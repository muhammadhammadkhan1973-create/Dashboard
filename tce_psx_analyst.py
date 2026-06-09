"""
PSX analyst-conviction layer for TCE — pure, testable.
Consumes TradingView scanner analyst columns (FactSet-sourced) and derives
conviction streams that PSX otherwise CANNOT fire (no Pakistani feed for them).

Fields (confirmed in TradingView stocks field reference):
  close, price_target_average, recommendation_mark,
  recommendation_buy, recommendation_hold, recommendation_sell, recommendation_total,
  earnings_per_share_forecast_next_fq, earnings_per_share_forecast_fq, earnings_per_share_fq
"""
import math

# thresholds (tunable, mirror US TCE conviction discipline)
TGT_UPSIDE_THRESH = 0.15     # +15% analyst upside -> forward conviction
REC_BUY_RATIO     = 0.60     # >=60% of analysts buy -> consensus conviction
REC_MARK_BULLISH  = 2.0      # recommendation_mark is FactSet 1(strong buy)..5(strong sell); <=2.0 = buy-or-better
EPS_REV_THRESH    = 0.02     # +2% forward-estimate lift run-to-run -> upward revision (real s9)

def _num(x):
    """Coerce to float or None; reject NaN/Inf so logic never sees junk."""
    if x is None: return None
    try: v = float(x)
    except (TypeError, ValueError): return None
    return None if (math.isnan(v) or math.isinf(v)) else v

def derive_psx_analyst_streams(row, prev_fwd_eps=None):
    """row: dict of scanner analyst fields. prev_fwd_eps: last run's stored
    forward EPS estimate for this ticker (for revision detection). Returns dict."""
    close   = _num(row.get('close'))
    pt_avg  = _num(row.get('price_target_average'))
    rec_mk  = _num(row.get('recommendation_mark'))
    rec_buy = _num(row.get('recommendation_buy')) or 0.0
    rec_tot = _num(row.get('recommendation_total')) or 0.0
    fwd_eps = _num(row.get('earnings_per_share_forecast_next_fq'))
    est_fq  = _num(row.get('earnings_per_share_forecast_fq'))   # estimate for last reported q
    act_fq  = _num(row.get('earnings_per_share_fq'))            # actual reported last q

    # COVERAGE gate: no analyst follows this name -> emit nothing (no false signal)
    covered = (pt_avg is not None and pt_avg > 0) or rec_tot > 0
    out = {'analyst_covered': covered, 'streams': [], 'detail': {}}
    if not covered:
        return out

    # s11 — analyst target upside (forward-looking; addresses "confirmer misses pre-move")
    if pt_avg and close and close > 0:
        upside = (pt_avg - close) / close
        out['detail']['target_upside_pct'] = round(upside * 100, 1)
        if upside >= TGT_UPSIDE_THRESH:
            out['streams'].append('s11_target_upside')

    # s12 — buy consensus
    if rec_tot > 0:
        buy_ratio = rec_buy / rec_tot
        out['detail']['buy_ratio'] = round(buy_ratio, 2)
        out['detail']['rec_mark'] = rec_mk
        # recommendation_mark is the FactSet consensus on a 1(strong buy)..5(strong sell) scale
        # (probe-confirmed: sample 1.125, impossible on the previously-assumed -1..+1). Bullish
        # is LOW, so buy-or-better is rec_mk <= REC_MARK_BULLISH (the old >=0.5 was always-true
        # for any covered name -> s12 fired on coverage alone; this makes it discriminative).
        if buy_ratio >= REC_BUY_RATIO or (rec_mk is not None and rec_mk <= REC_MARK_BULLISH):
            out['streams'].append('s12_recommendation')

    # s9 — EPS revision (the real one PSX lacks): forward estimate rising vs last snapshot
    if fwd_eps is not None:
        out['detail']['fwd_eps'] = fwd_eps
        p = _num(prev_fwd_eps)
        if p is not None and p != 0:
            rev = (fwd_eps - p) / abs(p)
            out['detail']['eps_rev_pct'] = round(rev * 100, 1)
            if rev >= EPS_REV_THRESH:
                out['streams'].append('s9_eps_revision')
        else:
            out['detail']['eps_rev_pct'] = None  # day-1: store snapshot, can't fire yet

    # bonus context (not a stream): last-quarter EPS surprise
    if est_fq is not None and act_fq is not None and est_fq != 0:
        out['detail']['eps_surprise_pct'] = round((act_fq - est_fq) / abs(est_fq) * 100, 1)

    out['analyst_conv'] = len(out['streams'])
    return out
