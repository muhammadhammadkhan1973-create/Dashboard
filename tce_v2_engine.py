"""
tce_v2_engine.py — Trend Convergence Engine v2 (universal six-stream, two-layer).

Reconstructed from the locked 2026-06-02 spec:
  START_PROMPT_next_session.txt  +  Dashboard_Architecture_Session_Summary_v1_11 §7.5–7.7.
STANDALONE — does NOT touch production scanner.py or the live 5-stream compute_tce_streams.
Pure logic, no network: fully testable in isolation (the June-2 discipline — prove, then wire).

TWO LAYERS
  Layer 1  sector adapters : map raw, sector-specific inputs -> 6 normalized signal values.
  Layer 2  universal scorer: 6 sector-agnostic streams; 4-of-6 = HIGH, 3-of-6 = WATCH.

THE SIX UNIVERSAL STREAMS (spec, verbatim intent)
  s1 sell-price momentum         unit economics turning up (commodity / ASP momentum)
  s2 supply / backlog            tightening supply or growing order backlog
  s3 estimate revisions          analyst EPS / target-price revisions clustering up
  s4 margin inflection           operating / gross margin turning up
  s5 external capital commitment capex / buyback / insider commitment; SHORT INTEREST = AMPLIFIER, not a gate
  s6 relative-strength guardrail stock RS vs its sector; GUARDRAIL — a HIGH label requires this to hold

NOTE ON THRESHOLDS: s1's ">=2 consecutive months >15%" is taken verbatim from the recovered
tce_v2_proto.py. The other per-stream cutoffs are sensible reconstructions matching the documented
intent and are exposed as named constants for easy tuning / reconciliation against the originals.
"""

from dataclasses import dataclass, field
from typing import Optional

# ---- tunable thresholds (reconstructed; s1 is verbatim from tce_v2_proto.py) ----
S1_MOM_PCT      = 15.0   # sell-price momentum % per month
S1_CONSEC       = 2      # consecutive months required
S2_BACKLOG_YOY  = 10.0   # backlog / order growth %% YoY to fire
S3_REV_BREADTH  = 5.0    # net upward revision breadth %% (raisers - cutters) to fire
S4_MARGIN_BPS   = 50.0   # margin inflection, bps YoY, to fire
S5_SHORT_AMP    = 15.0   # short interest %% that amplifies a borderline capital signal
S6_RS_MIN       = 0.0    # relative strength vs sector must be > this to hold the guardrail


# ----------------------------- the six streams -----------------------------
def s1_sellprice(mom_pct: Optional[float], consec_months: int = 0, thresh: Optional[float] = None):
    """Sell-price momentum: unit economics turning up. Fire on >=2 consecutive months above thresh.
    thresh defaults to the commodity scale (15%/mo); banks pass a NIM-appropriate value (~3%)."""
    if mom_pct is None:
        return False, "no sell-price feed"
    t = thresh if thresh is not None else S1_MOM_PCT
    fired = consec_months >= S1_CONSEC and mom_pct > t
    return fired, f"sell-price {mom_pct:+.1f}%/mo x{consec_months}mo (>{t:g}%)"


def s2_supply(backlog_yoy: Optional[float] = None, supply_tightening: Optional[bool] = None):
    """Supply / backlog: growing backlog OR tightening supply (e.g. falling rigs for crude)."""
    if backlog_yoy is None and supply_tightening is None:
        return False, "no supply/backlog feed"
    fired = bool(supply_tightening) or (backlog_yoy is not None and backlog_yoy > S2_BACKLOG_YOY)
    det = []
    if backlog_yoy is not None:
        det.append(f"backlog {backlog_yoy:+.1f}% YoY")
    if supply_tightening is not None:
        det.append("supply tightening" if supply_tightening else "supply loose")
    return fired, ", ".join(det)


def s3_revisions(rev_breadth_pct: Optional[float]):
    """Estimate revisions: net upward EPS/target revision breadth clustering positive."""
    if rev_breadth_pct is None:
        return False, "no revisions feed"
    fired = rev_breadth_pct > S3_REV_BREADTH
    return fired, f"rev breadth {rev_breadth_pct:+.1f}%"


def s4_margin(margin_delta_bps: Optional[float]):
    """Margin inflection: operating/gross margin turning up YoY."""
    if margin_delta_bps is None:
        return False, "no margin feed"
    fired = margin_delta_bps > S4_MARGIN_BPS
    return fired, f"margin {margin_delta_bps:+.0f}bps YoY"


def s5_capital(capital_committed: Optional[bool], short_interest_pct: float = 0.0):
    """External capital commitment (capex/buyback/insider). Short interest AMPLIFIES, never gates."""
    if capital_committed is None:
        return False, "no capital-event feed", False
    amp = short_interest_pct is not None and short_interest_pct > S5_SHORT_AMP
    det = f"capital {'committed' if capital_committed else 'none'}"
    if amp:
        det += f" (SI {short_interest_pct:.0f}% amplifier)"
    return bool(capital_committed), det, amp


def s6_relstrength(rs_vs_sector: Optional[float]):
    """Relative-strength guardrail: stock RS vs its sector. Holds when RS is positive."""
    if rs_vs_sector is None:
        return False, "no RS feed"
    fired = rs_vs_sector > S6_RS_MIN
    return fired, f"RS vs sector {rs_vs_sector:+.1f}%"


# ----------------------------- convergence scorer -----------------------------
@dataclass
class Signals:
    sell_mom_pct: Optional[float] = None
    sell_consec: int = 0
    backlog_yoy: Optional[float] = None
    supply_tightening: Optional[bool] = None
    rev_breadth_pct: Optional[float] = None
    margin_delta_bps: Optional[float] = None
    capital_committed: Optional[bool] = None
    short_interest_pct: float = 0.0
    rs_vs_sector: Optional[float] = None
    sector: str = "generic"
    sell_thresh: Optional[float] = None   # per-sector s1 firing threshold (banks override for NIM)


def score(sig: Signals) -> dict:
    f1, d1 = s1_sellprice(sig.sell_mom_pct, sig.sell_consec, sig.sell_thresh)
    f2, d2 = s2_supply(sig.backlog_yoy, sig.supply_tightening)
    f3, d3 = s3_revisions(sig.rev_breadth_pct)
    f4, d4 = s4_margin(sig.margin_delta_bps)
    f5, d5, amp = s5_capital(sig.capital_committed, sig.short_interest_pct)
    f6, d6 = s6_relstrength(sig.rs_vs_sector)

    fired = {"s1_sellprice": f1, "s2_supply": f2, "s3_revisions": f3,
             "s4_margin": f4, "s5_capital": f5, "s6_relstrength": f6}
    n = sum(fired.values())
    guardrail_ok = f6  # s6 is the guardrail: required to hold for a HIGH

    if n >= 4 and guardrail_ok:
        tier = "HIGH"
    elif n >= 3:
        # short-interest amplifier can lift a guardrail-clean WATCH that's one stream shy
        tier = "WATCH"
        if n == 3 and amp and guardrail_ok:
            tier = "WATCH+"   # amplified — flag for attention, not promoted to HIGH (SI is not a gate)
    else:
        tier = "IGNORE"

    return {
        "sector": sig.sector, "tier": tier, "score": n, "guardrail_ok": guardrail_ok,
        "amplified": amp,
        "fired": [k for k, v in fired.items() if v],
        "detail": {"s1": d1, "s2": d2, "s3": d3, "s4": d4, "s5": d5, "s6": d6},
    }


# ----------------------------- Layer 1: sector adapters -----------------------------
# Each adapter maps raw, sector-specific inputs -> a Signals object for the universal scorer.

def _momentum(series, thresh_pct=None):
    """From a monthly series (oldest->newest) return (latest MoM %, # consecutive recent months > thresh)."""
    if not series or len(series) < 2:
        return None, 0
    moms = [(series[i] - series[i - 1]) / series[i - 1] * 100
            for i in range(1, len(series)) if series[i - 1]]
    if not moms:
        return None, 0
    t = thresh_pct if thresh_pct is not None else S1_MOM_PCT
    consec = 0
    for m in reversed(moms):
        if m > t:
            consec += 1
        else:
            break
    return moms[-1], consec


# Where each sector's six signals come from (free sources, per the recovered feasibility matrix):
SOURCE_NOTES = {
    "fertilizer": {
        "s1": "Urea + DAP price momentum — World Bank Pink Sheet (DAP intl; urea domestic/regulated)",
        "s2": "feed-gas curtailment to plants (SNGPL/SSGC notices) OR offtake growth — curtailment tightens",
        "s3": "broker EPS/TP revisions — AKD / Topline / AHL (cover FFC, EFERT, FATIMA)",
        "s4": "primary margin = urea price - feed-gas cost; gas-tariff hikes compress, price hikes expand",
        "s5": "BMR / expansion / debottlenecking capex + dividend commitment (FFC = high payout)",
        "s6": "relative strength vs KSE-100 (or a fertilizer basket)",
    },
    "bank": {
        "s1": "NIM trend (policy-rate driven; SBP 11.5% => fat NIMs). Momentum = is NIM still expanding?",
        "s2": "balance-sheet growth — deposits + advances (loan) growth = growing earning assets",
        "s3": "broker EPS revisions — AKD / Topline / AHL (PSX); sell-side (US banks)",
        "s4": "NIM delta / cost-of-funds spread (CASA-mix improvement)",
        "s5": "payout / buyback + CAR headroom (banks return capital)",
        "s6": "relative strength vs bank index (KSE banking index for MCB; bank ETF for US)",
    },
}

def adapt_ep(raw: dict) -> Signals:
    """E&P (XOM/CVX/COP/EOG, OGDC/PPL): sell-price = crude (Brent->Dubai/Arab-Light) momentum;
    supply = rig-count direction (falling rigs = tightening); margin from net-margin delta."""
    return Signals(
        sell_mom_pct=raw.get("crude_mom_pct"), sell_consec=raw.get("crude_consec", 0),
        sell_thresh=raw.get("crude_thresh"),
        supply_tightening=(raw["rigs_falling"] if "rigs_falling" in raw else None),
        backlog_yoy=raw.get("reserve_replacement_yoy"),
        rev_breadth_pct=raw.get("rev_breadth_pct"),
        margin_delta_bps=raw.get("net_margin_bps"),
        capital_committed=raw.get("capex_up"),
        short_interest_pct=raw.get("short_interest_pct", 0.0),
        rs_vs_sector=raw.get("rs_vs_xle"), sector="E&P",
    )


def adapt_fert(raw: dict) -> Signals:
    """Fertilizer (FFC, EFERT, FATIMA). See SOURCE_NOTES['fertilizer'].
    Accepts pre-computed fields OR raw series: urea_prices[]/dap_prices[] -> s1 momentum;
    urea_price/gas_cost (+ _prev) -> s4 primary-margin inflection."""
    mom = raw.get("urea_dap_mom_pct")
    consec = raw.get("urea_consec", 0)
    if mom is None and (raw.get("urea_prices") or raw.get("dap_prices")):
        res = [_momentum(s) for s in (raw.get("urea_prices"), raw.get("dap_prices")) if s]
        res = [r for r in res if r[0] is not None]
        if res:
            mom = sum(r[0] for r in res) / len(res)        # blended urea+DAP momentum
            consec = min(r[1] for r in res)                # require BOTH trending for the consec count
    margin = raw.get("primary_margin_bps")
    if margin is None and all(raw.get(k) is not None for k in
                              ("urea_price", "gas_cost", "urea_price_prev", "gas_cost_prev")):
        spread_now = raw["urea_price"] - raw["gas_cost"]
        spread_prev = raw["urea_price_prev"] - raw["gas_cost_prev"]
        if spread_prev:
            margin = (spread_now - spread_prev) / abs(spread_prev) * 10000  # bps change in primary margin
    return Signals(
        sell_mom_pct=mom, sell_consec=consec,
        supply_tightening=raw.get("gas_curtailment"),
        backlog_yoy=raw.get("offtake_yoy"),
        rev_breadth_pct=raw.get("rev_breadth_pct"),
        margin_delta_bps=margin,
        capital_committed=(raw.get("expansion_committed") or raw.get("dividend_up")),
        short_interest_pct=raw.get("short_interest_pct", 0.0),
        rs_vs_sector=raw.get("rs_vs_kse100", raw.get("rs_vs_sector")),
        sector="fertilizer",
    )


def adapt_bank(raw: dict) -> Signals:
    """Bank (MCB + US banks via the carve-out). See SOURCE_NOTES['bank'].
    Banks have no commodity sell-price — NIM is the price of money, so s1 uses a NIM-scaled threshold
    (default 3%/period, not the 15% commodity scale). Accepts nim_series[] -> s1 momentum, and
    deposit/advances growth -> s2 balance-sheet growth.
    Macro tie-in: SBP rate >=11% = the user's defensive trigger; for BANKS high rates are a NIM tailwind,
    so a bank firing here is a defensive-mode beneficiary, not a casualty."""
    nim_thresh = raw.get("nim_thresh", 3.0)
    mom = raw.get("nim_mom_pct")
    consec = raw.get("nim_consec", 0)
    if mom is None and raw.get("nim_series"):
        mom, consec = _momentum(raw["nim_series"], thresh_pct=nim_thresh)
    bsg = raw.get("loan_growth_yoy")
    if bsg is None and (raw.get("deposit_growth_yoy") is not None or raw.get("advances_growth_yoy") is not None):
        vals = [v for v in (raw.get("deposit_growth_yoy"), raw.get("advances_growth_yoy")) if v is not None]
        bsg = sum(vals) / len(vals) if vals else None
    return Signals(
        sell_mom_pct=mom, sell_consec=consec, sell_thresh=nim_thresh,
        backlog_yoy=bsg, supply_tightening=None,
        rev_breadth_pct=raw.get("rev_breadth_pct"),
        margin_delta_bps=raw.get("nim_delta_bps"),
        capital_committed=(raw.get("payout_up") or raw.get("buyback")),
        short_interest_pct=raw.get("short_interest_pct", 0.0),
        rs_vs_sector=raw.get("rs_vs_bank_idx", raw.get("rs_vs_sector")),
        sector="bank",
    )


ADAPTERS = {"ep": adapt_ep, "fert": adapt_fert, "bank": adapt_bank}


def run(sector_key: str, raw: dict) -> dict:
    """Top-level: pick adapter by sector, adapt raw inputs, score convergence."""
    adapter = ADAPTERS.get(sector_key)
    if adapter is None:
        raise ValueError(f"unknown sector '{sector_key}' (have {list(ADAPTERS)})")
    return score(adapter(raw))


if __name__ == "__main__":
    # ---- mechanics validation (illustrative inputs, clearly labeled — NOT the original 9-stock audit) ----
    cases = [
        ("E&P  — full convergence (should be HIGH)", "ep", dict(
            crude_mom_pct=18, crude_consec=3, rigs_falling=True, rev_breadth_pct=12,
            net_margin_bps=120, capex_up=True, short_interest_pct=4, rs_vs_xle=8)),
        ("E&P  — 3 streams, guardrail holds (WATCH)", "ep", dict(
            crude_mom_pct=18, crude_consec=3, rigs_falling=True, rev_breadth_pct=2,
            net_margin_bps=10, capex_up=False, short_interest_pct=2, rs_vs_xle=5)),
        ("E&P  — 4 streams but RS guardrail FAILS (capped to WATCH)", "ep", dict(
            crude_mom_pct=18, crude_consec=3, rigs_falling=True, rev_breadth_pct=12,
            net_margin_bps=120, capex_up=True, short_interest_pct=4, rs_vs_xle=-3)),
        ("E&P  — 3 streams + high short interest (WATCH+ amplified)", "ep", dict(
            crude_mom_pct=18, crude_consec=3, rigs_falling=True, rev_breadth_pct=2,
            net_margin_bps=10, capex_up=False, short_interest_pct=22, rs_vs_xle=6)),
        ("Fert — convergence (HIGH)", "fert", dict(
            urea_dap_mom_pct=20, urea_consec=2, gas_curtailment=True, rev_breadth_pct=9,
            primary_margin_bps=80, expansion_committed=True, rs_vs_sector=4)),
        ("Bank — NIM + loan growth + payout (HIGH)", "bank", dict(
            nim_mom_pct=16, nim_consec=2, loan_growth_yoy=14, nim_delta_bps=70,
            payout_up=True, rev_breadth_pct=8, rs_vs_bank_idx=3)),
        ("Generic — nothing fires (IGNORE)", "ep", dict(
            crude_mom_pct=2, crude_consec=0, rigs_falling=False, rev_breadth_pct=-1,
            net_margin_bps=-20, capex_up=False, rs_vs_xle=-5)),
        ("Fert (FFC-like) — DERIVED from urea/DAP series + margin spread (HIGH)", "fert", dict(
            urea_prices=[100, 119, 140], dap_prices=[100, 118, 138],   # ~18%/mo, 2 consec
            gas_curtailment=True, rev_breadth_pct=9,
            urea_price=140, gas_cost=40, urea_price_prev=119, gas_cost_prev=39,  # spread 79->100 = +margin
            dividend_up=True, rs_vs_kse100=4)),
        ("Bank (MCB-like) — DERIVED NIM series + deposit/advances growth (HIGH)", "bank", dict(
            nim_series=[5.0, 5.25, 5.5],                # ~5%/period NIM expansion, 2 consec (>3% thresh)
            deposit_growth_yoy=16, advances_growth_yoy=12,  # blended ~14% -> s2 fires
            nim_delta_bps=60, payout_up=True, rev_breadth_pct=7, rs_vs_bank_idx=3)),
        ("Bank — NIM rolling over (s1 dead), only growth+payout (WATCH)", "bank", dict(
            nim_series=[5.5, 5.5, 5.45],                # NIM flat/down -> s1 will NOT fire
            deposit_growth_yoy=16, advances_growth_yoy=12, payout_up=True, rs_vs_bank_idx=3)),
    ]
    print("TCE v2 engine — mechanics validation\n" + "=" * 60)
    ok = True
    expect = ["HIGH", "WATCH", "WATCH", "WATCH+", "HIGH", "HIGH", "IGNORE", "HIGH", "HIGH", "WATCH"]
    for (label, sec, raw), exp in zip(cases, expect):
        r = run(sec, raw)
        flag = "OK " if r["tier"] == exp else "!! "
        if r["tier"] != exp:
            ok = False
        print(f"{flag}{label}")
        print(f"      -> {r['tier']}  (score {r['score']}/6, guardrail={'ok' if r['guardrail_ok'] else 'FAIL'})"
              f"  fired={r['fired']}")
    print("=" * 60)
    print("ALL MECHANICS PASS" if ok else "SOME CASES OFF — review thresholds")
