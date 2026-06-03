"""
tce_backtest.py  —  point-in-time PRECISION backtest of the TCE engine's price core.

WHAT THIS TESTS (and what it does NOT):
  The audit showed the genuine 3-quarters-early signal for the 2025 AI-infra move was the price
  core — strong relative momentum + market leadership — with revisions confirming LATER. Historical
  estimate-revisions / short-interest / news as-of mid-2025 are not retrievable from free sources,
  so this backtest reconstructs ONLY the price-core streams (momentum, RS-vs-SPY guardrail, volume)
  point-in-time and measures how well THEY separate known winners from a control set.
  => This is a defensible LOWER BOUND on the engine, not a measurement of the full 9 streams.

NO LOOK-AHEAD: signals use only closes with date <= AS_OF; outcomes use only closes after AS_OF.

RUN (on a machine with internet — NOT the sandbox; Yahoo is blocked here):
    pip install yfinance pandas
    python tce_backtest.py
Outputs a metrics report to stdout and writes tce_backtest_results.csv.

Pure functions (signals_from_series, tier_pricecore, metrics) are unit-tested below with
`python tce_backtest.py --selftest` and require no network.
"""
import sys, csv, datetime as dt

AS_OF        = "2025-07-01"     # ~3 quarters before the April-2026 rally
FORWARD_END  = "2026-04-01"
WINNER_RET   = 40.0             # % forward return to count as a "winner" (tunable)
MOM_THRESH   = 15.0             # momentum cutoff for the headline tier (swept in the report)

# The 9 retrospective winners (the recall target)
WINNERS = ["MU", "WDC", "STX", "SNDK", "AMD", "DELL", "LITE", "BE", "INTC"]

# Broad control set — diversified large/mid-cap US names NOT selected on outcome. Mild survivorship
# (current tickers) is acknowledged in the report. Kept ~120 for a tractable run.
CONTROL = [
 "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","BRK-B","JPM","V","MA","UNH","HD","PG","KO","PEP",
 "COST","WMT","MCD","DIS","NFLX","CSCO","ORCL","CRM","ADBE","TXN","QCOM","AVGO","AMAT","LRCX","KLAC",
 "MRVL","NXPI","ADI","MCHP","XOM","CVX","COP","EOG","SLB","PSX","MPC","VLO","OXY","KMI","WMB","PXD",
 "JNJ","PFE","MRK","ABBV","LLY","TMO","ABT","DHR","BMY","AMGN","GILD","CVS","CI","HUM","ELV",
 "BAC","WFC","C","GS","MS","SCHW","BLK","AXP","USB","PNC","TFC","COF","BK","SPGI","CME","ICE",
 "CAT","DE","HON","GE","MMM","BA","LMT","RTX","NOC","GD","EMR","ETN","ITW","PH","ROK",
 "PM","MO","CL","KMB","GIS","K","HSY","MDLZ","STZ","KHC","SYY","KR","DG","DLTR","TGT","LOW",
 "T","VZ","TMUS","CMCSA","CHTR","SBUX","NKE","LULU","TJX","BKNG","MAR","HLT","F","GM","UPS","FDX",
 "LIN","APD","SHW","FCX","NEM","NUE","DOW","DD","PPG",
]

UNIVERSE = sorted(set(WINNERS + CONTROL))


# ----------------------------------------------------------------- pure logic (unit-tested)
def signals_from_series(closes_to_asof, vols_to_asof, spy_closes_to_asof):
    """All inputs are oldest->newest, ending ON OR BEFORE AS_OF. Returns dict of price-core signals.
       ~252 trading days = 1y; 63 = 3mo; 126 = 6mo."""
    s = {}
    c = closes_to_asof
    if c and len(c) >= 64 and c[-64]:
        s["mom_3mo"] = round((c[-1] - c[-64]) / c[-64] * 100, 1)
    if c and len(c) >= 127 and c[-127]:
        name6 = (c[-1] - c[-127]) / c[-127] * 100
        spy6 = None
        if spy_closes_to_asof and len(spy_closes_to_asof) >= 127 and spy_closes_to_asof[-127]:
            spy6 = (spy_closes_to_asof[-1] - spy_closes_to_asof[-127]) / spy_closes_to_asof[-127] * 100
        s["rs_vs_spy"] = round(name6 - spy6, 1) if spy6 is not None else None
        s["rs_ok"] = (spy6 is None) or (name6 >= spy6)
    if vols_to_asof and len(vols_to_asof) >= 60:
        vr = sum(vols_to_asof[-20:]) / 20.0
        vb = sum(vols_to_asof[-60:-20]) / 40.0
        if vb > 0:
            s["vol_ratio"] = round(vr / vb, 2)
    return s


def tier_pricecore(sig, mom_thresh=MOM_THRESH):
    """Reconstructable analogue of the engine's HIGH-core: strong momentum that LEADS the market.
       STRONG = momentum>=thresh AND guardrail holds AND volume confirms.
       MODERATE = momentum>=thresh AND guardrail holds.  Else NONE. 'flagged' = STRONG or MODERATE."""
    mom = sig.get("mom_3mo"); rs_ok = sig.get("rs_ok", True); vol = sig.get("vol_ratio", 0) or 0
    if mom is None:
        return "NONE"
    if mom >= mom_thresh and rs_ok and vol > 1.3:
        return "STRONG"
    if mom >= mom_thresh and rs_ok:
        return "MODERATE"
    return "NONE"


def metrics(labeled):
    """labeled = list of (flagged_bool, winner_bool). Returns precision/recall/lift/confusion."""
    n = len(labeled)
    winners = sum(1 for _, w in labeled if w)
    flagged = sum(1 for f, _ in labeled if f)
    tp = sum(1 for f, w in labeled if f and w)
    fp = flagged - tp
    fn = winners - tp
    base = winners / n if n else 0
    precision = tp / flagged if flagged else 0
    recall = tp / winners if winners else 0
    lift = (precision / base) if base else 0
    return dict(n=n, winners=winners, flagged=flagged, tp=tp, fp=fp, fn=fn,
                base_rate=round(base, 3), precision=round(precision, 3),
                recall=round(recall, 3), lift=round(lift, 2))


# ----------------------------------------------------------------- data (network; runner only)
def _series(ticker, start, end):
    import yfinance as yf
    h = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    if len(h) == 0:
        return [], []
    return [float(x) for x in h["Close"].tolist()], [float(x) for x in h["Volume"].tolist()]


def run():
    import time
    sig_start = (dt.date.fromisoformat(AS_OF) - dt.timedelta(days=420)).isoformat()  # ~14mo lookback
    spy_c, _ = _series("SPY", sig_start, AS_OF)
    rows, labeled = [], []
    caught = {}
    for i, tk in enumerate(UNIVERSE):
        try:
            c, v = _series(tk, sig_start, AS_OF)               # signals: up to AS_OF only
            fc, _ = _series(tk, AS_OF, FORWARD_END)            # outcome: after AS_OF only
            if len(c) < 127 or len(fc) < 2 or not fc[0]:
                continue
            sig = signals_from_series(c, v, spy_c)
            tier = tier_pricecore(sig)
            fwd = round((fc[-1] - fc[0]) / fc[0] * 100, 1)
            is_win = fwd >= WINNER_RET
            is_flag = tier in ("STRONG", "MODERATE")
            labeled.append((is_flag, is_win))
            if tk in WINNERS:
                caught[tk] = (tier, fwd)
            rows.append(dict(ticker=tk, group=("WINNER" if tk in WINNERS else "control"),
                             mom_3mo=sig.get("mom_3mo"), rs_vs_spy=sig.get("rs_vs_spy"),
                             rs_ok=sig.get("rs_ok"), vol_ratio=sig.get("vol_ratio"),
                             tier=tier, fwd_ret=fwd, winner=is_win))
            time.sleep(0.3)
        except Exception as e:
            print(f"  skip {tk}: {e}")

    with open("tce_backtest_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    print("="*64)
    print(f"TCE PRICE-CORE BACKTEST  as-of {AS_OF} -> {FORWARD_END}  winner>={WINNER_RET}%")
    print(f"universe scored: {len(rows)}  (sandbox cannot fetch; run on a machine with Yahoo)")
    print("="*64)
    m = metrics(labeled)
    print(f"base rate (winners/total): {m['base_rate']*100:.1f}%   winners={m['winners']}  flagged={m['flagged']}")
    print(f"precision: {m['precision']*100:.1f}%   recall: {m['recall']*100:.1f}%   LIFT: {m['lift']}x")
    print(f"confusion: TP={m['tp']} FP={m['fp']} FN={m['fn']}")
    print("\nthe 9 winners — where they landed:")
    for tk in WINNERS:
        t, fwd = caught.get(tk, ("(insufficient data)", None))
        print(f"  {tk:5s} {t:9s} fwd={fwd if fwd is not None else 'n/a'}")
    print("\nmomentum-threshold sweep (guardrail on):")
    print(f"  {'thresh':>7} {'flagged':>8} {'precision':>10} {'recall':>8} {'lift':>6}")
    for th in (5, 10, 15, 20, 30, 50):
        lab = []
        for r in rows:
            sig = dict(mom_3mo=r["mom_3mo"], rs_ok=r["rs_ok"], vol_ratio=r["vol_ratio"])
            t = tier_pricecore(sig, mom_thresh=th)
            lab.append((t in ("STRONG", "MODERATE"), r["winner"]))
        mm = metrics(lab)
        print(f"  {th:>6}% {mm['flagged']:>8} {mm['precision']*100:>9.1f}% {mm['recall']*100:>7.1f}% {mm['lift']:>5}x")
    print("\nCAVEATS: price-core only (revisions/capital/news not reconstructable point-in-time);")
    print("mild survivorship in control list; by mid-2025 several winners were already running")
    print("(this measures trend-confirmation as much as prediction).")


# ----------------------------------------------------------------- self-test (no network)
def selftest():
    def mkc(v127, v64, v1, n=130):      # set the exact 6mo / 3mo / now anchors the signal reads
        a = [v127]*n; a[-127] = v127; a[-64] = v64; a[-1] = v1; return a
    def mkv(recent, base, n=130):
        a = [base]*n
        for k in range(n-20, n): a[k] = recent
        return a
    spy = mkc(100, 104, 108)            # SPY +8% over 6mo
    # winner-like: 3mo +27%, leads SPY (name6 +40 vs +8), volume 2x
    sig = signals_from_series(mkc(100, 110, 140), mkv(2, 1), spy)
    assert sig["mom_3mo"] > 15 and sig["rs_ok"] and sig["vol_ratio"] > 1.3, sig
    assert tier_pricecore(sig) == "STRONG", sig
    # laggard: 3mo +1.4% -> below threshold
    sig2 = signals_from_series(mkc(100, 138, 140), mkv(1, 1), spy)
    assert tier_pricecore(sig2) == "NONE", sig2
    # guardrail veto: 3mo +27% (would qualify) BUT lags market (SPY +50% over 6mo) -> NONE
    spy_hot = mkc(100, 130, 150)
    sig3 = signals_from_series(mkc(100, 110, 140), mkv(2, 1), spy_hot)
    assert sig3["rs_ok"] is False and tier_pricecore(sig3) == "NONE", sig3
    # metrics math
    lab = [(True, True), (True, True), (True, False), (False, True), (False, False)]*4
    m = metrics(lab)
    assert m["tp"] == 8 and m["fp"] == 4 and m["fn"] == 4 and m["winners"] == 12 and m["flagged"] == 12, m
    assert m["precision"] == round(8/12, 3) and m["recall"] == round(8/12, 3), m
    assert m["base_rate"] == round(12/20, 3) and m["lift"] == round((8/12)/(12/20), 2), m
    print("selftest: all assertions passed")
    print(" STRONG signal:", sig, "-> tier", tier_pricecore(sig))
    print(" guardrail-veto signal:", sig3, "-> tier", tier_pricecore(sig3))
    print(" sample metrics:", m)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run()
