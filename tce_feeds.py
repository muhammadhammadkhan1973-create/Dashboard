"""
tce_feeds.py — live, LABELED data feeds for the TCE v2 sector adapters.

Each of the six streams is assembled with an explicit (value, source, freshness) label so you
always know whether a signal is LIVE-fetched, read from a project file, or manual/last-good.
STANDALONE — pairs with tce_v2_engine.py; touches no production code.

Freshness tags:
  LIVE     fetched this run from a free source
  FILE     read from a project file (real data, but as-of the file's vintage)
  MANUAL   user-maintained / last-good (no free machine-readable feed yet)
  PENDING  needs the broker layer or a fetcher not yet built

Sandbox note: worldbank.org / yfinance / PSX are NOT reachable from the build sandbox (only
github/pypi/npm are). So the Pink Sheet read uses the project xlsx here and the live URL on your
GitHub run; RS (yfinance / PSX-EOD) is structured to fetch on your run. Same playbook as F4/ETF/rig.
"""

import os
import openpyxl
from tce_v2_engine import run, SOURCE_NOTES

# World Bank "Pink Sheet" (CMO). Tier-2 of the recovered 3-tier sell-price feed: column-by-header xlsx.
PINK_SHEET_PATH = "/mnt/project/CMOHistoricalDataMonthly.xlsx"   # production: workflow drops latest here
PINK_SHEET_URL  = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"


def _label(value, source, fresh):
    return {"value": value, "source": source, "fresh": fresh}


def _pink_sheet_series(headers=("Urea", "DAP", "Dubai"), n=6, path=PINK_SHEET_PATH):
    """Read the last n monthly values per commodity from the WB Pink Sheet 'Monthly Prices' sheet,
    matching by header substring. Uses the local project xlsx if present, else downloads the live
    World Bank file (reachable on the GitHub runner; not in the build sandbox)."""
    try:
        if not os.path.exists(path):
            import urllib.request, tempfile
            tmp = os.path.join(tempfile.gettempdir(), "wb_pinksheet.xlsx")
            urllib.request.urlretrieve(PINK_SHEET_URL, tmp)
            path = tmp
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception:
        return None, None
    ws = wb["Monthly Prices"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[4]
    cols = {}
    for want in headers:
        for j, h in enumerate(hdr):
            if h and want.lower() in str(h).lower() and want not in cols:
                cols[want] = j
                break
    data = [r for r in rows[6:] if r[0]]
    asof = data[-1][0] if data else None
    out = {}
    for want, j in cols.items():
        vals = [r[j] for r in data[-n:] if isinstance(r[j], (int, float))]
        out[want] = vals
    return out, asof


def _mom(series):
    if not series or len(series) < 2 or not series[-2]:
        return None
    return (series[-1] - series[-2]) / series[-2] * 100


def fert_feed(ticker, *, gas_cost=None, gas_cost_prev=None, manual=None):
    """Assemble a LABELED fertilizer feed. s1 from the real Pink Sheet; s4 = urea - gas (gas manual);
    s2/s3/s5 manual/last-good (pending gas-notice + broker layers); s6 RS fetches on your run."""
    manual = manual or {}
    series, asof = _pink_sheet_series()
    labels = {}
    raw = {}

    # --- s1: blended Urea + DAP price momentum (World Bank Pink Sheet) ---
    if series:
        urea_mom, dap_mom = _mom(series.get("Urea")), _mom(series.get("DAP"))
        moms = [m for m in (urea_mom, dap_mom) if m is not None]
        blend = sum(moms) / len(moms) if moms else None
        raw["urea_prices"] = series.get("Urea")
        raw["dap_prices"] = series.get("DAP")
        labels["s1"] = _label(
            f"urea {urea_mom:+.1f}%/mo, DAP {dap_mom:+.1f}%/mo (blend {blend:+.1f}%)" if blend is not None else "n/a",
            f"World Bank Pink Sheet (CMO), thru {asof}", "FILE")
        if series.get("Urea"):
            raw["urea_price"] = series["Urea"][-1]
            raw["urea_price_prev"] = series["Urea"][-2] if len(series["Urea"]) > 1 else None
    else:
        labels["s1"] = _label("Pink Sheet unavailable", PINK_SHEET_URL, "LIVE-on-run")

    # --- s4: primary margin = urea price - feed-gas cost (urea LIVE from Pink Sheet, gas MANUAL) ---
    if gas_cost is not None and gas_cost_prev is not None and raw.get("urea_price_prev"):
        raw["gas_cost"], raw["gas_cost_prev"] = gas_cost, gas_cost_prev
        spread_now = raw["urea_price"] - gas_cost
        spread_prev = raw["urea_price_prev"] - gas_cost_prev
        labels["s4"] = _label(f"primary spread {spread_prev:.0f}->{spread_now:.0f}",
                              "urea: Pink Sheet | feed-gas: SNGPL notified tariff (manual)", "FILE+MANUAL")
    else:
        labels["s4"] = _label("need gas_cost (SNGPL feed tariff)", "manual", "MANUAL")

    # --- s2 supply, s3 revisions, s5 capital: manual / last-good until fetchers + broker layer exist ---
    raw["gas_curtailment"] = manual.get("gas_curtailment")
    labels["s2"] = _label(manual.get("gas_curtailment"), "SNGPL/SSGC curtailment notices (manual/news)", "MANUAL")
    raw["rev_breadth_pct"] = manual.get("rev_breadth_pct")
    labels["s3"] = _label(manual.get("rev_breadth_pct"), "broker EPS/TP — AKD/Topline/AHL", "PENDING(broker layer)")
    raw["expansion_committed"] = manual.get("expansion_committed")
    raw["dividend_up"] = manual.get("dividend_up")
    labels["s5"] = _label(manual.get("expansion_committed") or manual.get("dividend_up"),
                          "PSX filings / payout announcements (manual)", "MANUAL")

    # --- s6: relative strength vs KSE-100 (PSX-EOD for FFC; yfinance for US fert) — fetches on your run ---
    raw["rs_vs_kse100"] = manual.get("rs_vs_kse100")
    labels["s6"] = _label(manual.get("rs_vs_kse100"),
                          "FFC.KA 13wk vs KSE-100 (PSX-EOD via scanner)", "LIVE-on-run")

    result = run("fert", raw)
    return result, labels, raw


def _print(ticker, result, labels):
    print(f"\n{ticker} — fertilizer   (TCE v2 live feed)")
    print("-" * 78)
    fired = set(result["fired"])
    for s in ("s1", "s2", "s3", "s4", "s5", "s6"):
        L = labels[s]
        mark = "FIRED" if {"s1": "s1_sellprice", "s2": "s2_supply", "s3": "s3_revisions",
                            "s4": "s4_margin", "s5": "s5_capital", "s6": "s6_relstrength"}[s] in fired else "  -  "
        val = L["value"]
        val = "(none)" if val is None else (val if isinstance(val, str) else str(val))
        print(f"  [{mark}] {s}: {val}")
        print(f"          src: {L['source']}  [{L['fresh']}]")
    print("-" * 78)
    print(f"  => TIER: {result['tier']}   (score {result['score']}/6, "
          f"guardrail={'ok' if result['guardrail_ok'] else 'FAIL'})  fired={result['fired']}")


if __name__ == "__main__":
    # FFC live feed: s1 from the REAL Pink Sheet in the project; gas tariff + the manual/pending signals
    # supplied as illustrative current values (replace with your maintained inputs).
    res, labels, raw = fert_feed(
        "FFC",
        gas_cost=300, gas_cost_prev=300,          # SNGPL feed-gas tariff (PKR-normalized, manual)
        manual=dict(gas_curtailment=False, rev_breadth_pct=None,
                    expansion_committed=False, dividend_up=True, rs_vs_kse100=None),
    )
    _print("FFC", res, labels)
    print("\nNote: s1 is the live Pink Sheet read (real, file-vintage). s6 RS + the live Pink Sheet URL")
    print("fetch on your GitHub run; s2/s3/s5 are manual/last-good until the gas-notice + broker layers land.")
