"""
PSX TradingView fundamental-column probe  —  Phase 0 of the PSX IM3 engine.
=========================================================================
Logging only; writes nothing. Run on GitHub Actions (TradingView is not
reachable from the build sandbox).

Mirrors the MU america/scan probe, but points at
scanner.tradingview.com/pakistan/scan. It answers the one question that
decides the whole PSX IM3 build:

    Which of the 62 IM3 single-period fundamental columns does TradingView
    actually populate for PSX names?

  * If TV fills most of them  -> the single-period half of PSX IM3 is free /
    automatable (same as US `fund:tv`); only the multi-year history needs
    broker research.
  * If TV fills few/none      -> single-period must also come from broker
    research, and PSX IM3 is a broker-data build end to end.

Paste the whole log back to lock the PSX source map.
"""
import requests, time

URL  = "https://scanner.tradingview.com/pakistan/scan"
HDRS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
        "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"}

# five holdings + a few large liquid names for breadth across sectors
TICKERS = ["PSX:OGDC", "PSX:PPL", "PSX:MCB", "PSX:FFC", "PSX:HUBC",
           "PSX:ENGRO", "PSX:LUCK", "PSX:UBL"]

# the 62 columns confirmed valid on america/scan for MU — the IM3 single-period inputs
COLS = [
    "name","description","sector","industry","market_cap_basic","close","currency",
    "price_earnings_ttm","price_earnings_current","price_book_ratio","price_book_fq",
    "price_sales_ratio","price_sales_current","enterprise_value_ebitda_ttm",
    "enterprise_value_fq","enterprise_value_current","gross_margin","gross_margin_ttm",
    "operating_margin","operating_margin_ttm","net_margin","net_margin_ttm",
    "pre_tax_margin_ttm","return_on_equity","return_on_invested_capital","return_on_assets",
    "debt_to_equity","debt_to_equity_fq","current_ratio","quick_ratio","dividends_yield",
    "dividends_yield_current","dividend_payout_ratio_ttm","dividends_per_share_fq",
    "total_debt","total_debt_fq","total_revenue","total_revenue_ttm","free_cash_flow",
    "free_cash_flow_ttm","free_cash_flow_margin_ttm","cash_n_short_term_invest_fq",
    "cash_n_equivalents_fq","ebitda","ebitda_ttm","ebit_ttm","earnings_per_share_basic_ttm",
    "earnings_per_share_diluted_ttm","earnings_per_share_fq","earnings_per_share_forecast_next_fq",
    "total_revenue_yoy_growth_ttm","earnings_per_share_diluted_yoy_growth_ttm","beta_1_year",
    "total_shares_outstanding_fundamental","number_of_shares_outstanding","interest_coverage",
    "total_current_assets_fq","total_current_liabilities_fq","invent_turnover_current",
    "total_assets_fq","retained_earnings_fq",
]

def scan(cols):
    """POST one column set; returns (data_list | None, status, err). TV rejects the
    whole request if ANY column is unknown, so callers fall back to per-field probing."""
    body = {"symbols": {"tickers": TICKERS, "query": {"types": []}}, "columns": cols}
    try:
        r = requests.post(URL, json=body, headers=HDRS, timeout=30)
    except Exception as e:
        return None, "EXC", str(e)[:160]
    if r.status_code != 200:
        return None, r.status_code, r.text[:160]
    return r.json().get("data", []), 200, ""

def main():
    print("PSX TradingView pakistan/scan fundamental probe — logging only")
    print("=" * 70)

    # 1) reachability + which tickers resolve
    data, code, err = scan(["name", "close"])
    if data is None:
        print(f"BASE SCAN FAILED (HTTP {code}): {err}")
        print("If this 404s/blocks, the pakistan/scan fundamental path is unavailable "
              "and PSX single-period must come from broker research.")
        return
    resolved = {row["s"]: row["d"] for row in data}
    print(f"tickers resolved: {len(resolved)}/{len(TICKERS)}")
    for s, d in resolved.items():
        print(f"  {s:12} name={d[0]!r} close={d[1]}")
    print()

    # 2) per-column coverage (batches of 6, per-field fallback for rejected columns)
    valid, invalid = {}, []
    B = 6
    for i in range(0, len(COLS), B):
        batch = COLS[i:i + B]
        data, code, err = scan(["name"] + batch)
        if data is not None:
            for row in data:
                for j, c in enumerate(batch):
                    valid.setdefault(c, {})[row["s"]] = row["d"][j + 1]
        else:
            for c in batch:                      # narrow down the offending column(s)
                d2, code2, err2 = scan(["name", c])
                if d2 is not None:
                    for row in d2:
                        valid.setdefault(c, {})[row["s"]] = row["d"][1]
                else:
                    invalid.append(c)
                time.sleep(0.2)
        time.sleep(0.3)

    # 3) coverage report
    n = len(resolved)
    filled = 0
    print(f"=== COLUMN COVERAGE (non-null across {n} PSX names) ===")
    for c in COLS:
        if c in valid:
            vals = valid[c]
            nonnull = sum(1 for v in vals.values() if v is not None)
            if nonnull:
                filled += 1
            sample = next((v for v in vals.values() if v is not None), None)
            print(f"  {c:42} {nonnull}/{n}   e.g. {sample}")
        else:
            print(f"  {c:42} INVALID (column rejected by TV)")
    print()
    print(f"SUMMARY: {filled}/{len(COLS)} columns populated for at least one PSX name.")
    print(f"INVALID columns: {invalid or '(none)'}")
    print()
    print("VERDICT GUIDE:")
    print("  high coverage  -> PSX single-period IM3 = TV (free, automatable); broker only for history")
    print("  low coverage   -> PSX single-period must come from broker research too")
    print()
    print("Paste this whole log back to lock the PSX source map.")

if __name__ == "__main__":
    main()
