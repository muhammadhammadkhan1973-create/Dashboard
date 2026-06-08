"""
PSX + US Active Macro Dashboard - Data Scanner v1.10.0
======================================================
Runs daily via GitHub Actions, scans US and PSX universes, runs TCE convergence,
fetches macro data, writes data.json for the HTML dashboard.

v1.10.0 adds:
- Full IM3 162-point scoring engine: score_im3()
  * Replicates every formula from IM3_0 Scoring Template Excel exactly
  * System A (Standard): 40 metrics, 162 pts — all non-bank stocks
  * System B (Bank): same template, 6 inventory/coverage metrics replaced
    with bank-specific ratios (NIM, ROE, CASA, ADR, NPL, CAR) → 162 pts
  * Bank detection via yfinance sector/industry fields
  * 7 intrinsic value methods: DCF EPS, DCF FCF, DCF Cash, Projected FCF,
    Projected Cash, Peter Lynch Value, Graham Value
  * Altman Z, Beneish M, Piotroski F — all computed from yfinance data
  * GOOD=100%, WATCH=60%, BAD=20% point conversion per weightage file
  * Runs as post-screen layer on explosive_us records only
  * im3 dict added to each explosive_us record

v1.9.0 adds:
- Tab 12 Gold & Metals data: fetch_metals()
  * Metal spot prices GC=F, SI=F, PL=F, PA=F from Yahoo Finance
  * DXY Dollar Index DX-Y.NYB from Yahoo Finance
  * Fed balance sheet WALCL from FRED (QE/QT signal)
  * COT non-commercial net positions from CFTC CMX page (Gold/Silver/Copper)
  * News RSS scoring for IMF Pakistan, Pakistan Default, GeoPolitical (feedparser)
  * All stored under data['macros']['metals']

v1.8.0 fixes:
- Baker Hughes timeout 30s → 5s, silent fallback
- PSX explosive: embedded FY2024 annual growth data
- IM3-correct explosive metrics using Operating Profit / Net Profit

v1.7.1 fixes: FMP enrichment moved to post-screen stage
"""

import os
import sys
import json
import math
import time
import csv
import traceback
import datetime as dt
from io import StringIO
from pathlib import Path

import requests
import pandas as pd
import numpy as np

# =============================================================
# CONFIG
# =============================================================
FRED_KEY = os.environ.get('FRED_API_KEY', '')
FMP_KEY  = os.environ.get('FMP_API_KEY', '')
OUTPUT_PATH  = Path(__file__).parent / 'data.json'
SCAN_VERSION = '1.28.0'  # 1.28.0: (Wave T2 daily-WoW trend) WoW/MoM/QoQ on the daily market series via 5/21/63-trading-day windows, all backfilled from the source series (live day-1): FRED us_10y/us_2y/hy_spread + dfii10/breakeven_10y/gvz, Yahoo gold/silver/platinum/palladium px + dxy (period widened 5d->6mo) and usd_pkr; plus a us_2s10s spread value. Dashboard M1 US-regime + M6 metals engine now fold real-yield/DXY/breakeven/GVZ/yield direction into their reads. 1.27.0: (Wave T1 weekly-native trend) generic {d,v} dedup-by-date history + WoW/MoM/QoQ trend helpers applied to the four weekly-native series: COT metals net-%OI (now dedup-by-report-date, fixes same-day duplicate appends -> cot_{m}_pct_wow/_mom/_qoq), COT futures net (backfilled from the DESC CFTC rows -> net_wow/_mom/_qoq, live day-1), WALCL (backfilled from the FRED weekly series -> walcl_wow/_mom/_qoq), and SBP reserves (value-change-dedup history -> sbp_reserves_wow/_mom/_qoq). Dashboard M6 metals engine now folds COT *direction* into the tactical score. 1.26.0: (Wave M5/M6 metals data) added FRED real-yield DFII10 + 10y breakeven T10YIE + Gold-VIX GVZCLS into macros.metals (dfii10/breakeven_10y/gvz), and 156-week COT net-%-OI history+percentile persistence (cot_{gold,silver,copper}_hist/_pctile) so the dashboard M6 engine swaps its real-yield proxy for true TIPS and its COT proxy for a percentile as history accrues. 1.25.0: (Wave D1 step 3) ROE>=ROE_FIN_MIN (8%) is now the PRIMARY financial screen gate (from the live diag: keeps 193/387, median 9.2%), with EPS-YoY>=0% as a not-deteriorating secondary; the Yahoo revenue gate is BYPASSED for financials (revenue meaningless for a spread/credit business) while non-financials still require revenueGrowth>=15%. Missing vendor field never drops a bank. Log line is now 'D1 bank gate: N in-band -> dropped R (ROE<8%) + E (EPS<0) -> M to Yahoo'. (Version bump re-scrapes ETF overlap once.) 1.24.0: (Track 1 — D1 step 2 gate) banks gated on a bank-appropriate metric: EPS-YoY>=0% active (drops deteriorating banks, no-data passes through), Yahoo revenue gate kept as backstop this run (monotonic, no candidate ballooning); ROE column+distribution diag added — ROE becomes primary financial gate next run once TV coverage/units confirmed. (Track 2 — IM3 System B refactor) score_im3_bank now zeroes ALL non-bank metrics (Piotroski/Altman/Beneish/ROIC-WACC, EV-EBITDA/PEG/PS/Graham/MoS, FCF/CROIC, D/E/total-debt, op-margin/turns) per the Sarmaaya Week-6 framework, and scores banks out of their APPLICABLE max (~70) instead of /162 — fixes the bug that capped every bank ~55% (grade C). Added bank_coverage + bank_inputs probe for the Phase-2 canonical-ratio additions. (Version bump re-scrapes ETF overlap once.) 1.23.0: Wave D1 step 1 instrumentation. 1.22.2: KSE-100 RESOLVED via diagnostics — the index lives on the dps.psx INT (intraday) timeseries (current; 171651.48 @ last session), NOT eod (frozen at 2021). int now primary with date-preference; dead market-watch(470KB)/indices/sarmaaya HTML + diag removed. Value was the last-session close, never stale. 1.22.0: (a) COT/CFTC timeout (8,12) to bound dead-endpoint cost; (b) KSE-100 fresh HTML sources (market-watch/indices) first, stale int demoted last; (c) NEW recession watch block (FRED Sahm/yield-curve/RECPRO/GDPNow/claims + ForexFactory faireconomy calendar). 1.21.3: also carry forward per-record im3 score dicts (not just the ticker list) so a skipped IM3 re-score doesn't wipe the scores from data.json. 1.21.2: preserve im3_explosive_tickers so the workflow's IM3 change-detection can skip re-scoring on stable days. 1.21.1: drop TV-leaked preferred-share tickers + demote micro-base rev-growth artifacts. 1.21.0: US screening migration Phase 1 (TV america pre-filter before Yahoo; financials pass straight to Yahoo; hard fallback to full Yahoo universe if TV unreachable)
# v1.19.0  TradingView futures fallback for live oil (WTI/Brent) — slots between Yahoo and stale-FRED

YF_DELAY          = 0.35
US_SMALL_CAP_MIN  = 300_000_000
US_SMALL_CAP_MAX  = 2_000_000_000
US_REV_GROWTH_MIN = 0.15
ROE_FIN_MIN       = 8.0   # %; D1 step 3 — the PRIMARY financial (bank) screen gate. From the
                          # live ROE diag (354/387 financials have ROE, median 9.2%): >=8% keeps
                          # 193 of 387, a sensible candidate floor (NOT the canonical 20% scoring
                          # bar). Replaces the revenue gate for financials (revenue is meaningless
                          # for a spread/credit business). Tunable.
US_REV_GROWTH_SANE_MAX = 500.0  # %; rev-growth above this is a micro-base artifact (near-zero prior-year
                                # revenue -> astronomical %). Such names are demoted in the candidate
                                # ranking so they can't grab a HIGH-CONVICTION slot (they still pass the screen).

US_CANDIDATE_POOL = 15    # top small-cap survivors fed to TCE (slow, network-heavy)
ETF_TCE_N         = 20    # ETF-consensus large-caps added to the US TCE pool (so quality large-caps are visible)
US_SCAN_WORKERS   = 2     # parallel Yahoo screen workers. 8 hard-throttled, 4 still capped survivors + poisoned the EPS session. 2 = balanced. Set to 1 for guaranteed-complete sequential (~18min).
US_EXPLOSIVE_POOL = 200   # survivors fed to explosive screen (fast, no network)

PSX_SWEET_SPOT_MIN = 5_000_000_000
PSX_SWEET_SPOT_MAX = 30_000_000_000
PSX_GROWTH_MIN     = 0.20

KSE_MIN, KSE_MAX = 50_000, 500_000

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

DEFAULT_DATA = {
    'meta': {'scan_version': SCAN_VERSION, 'last_scan_utc': None,
             'errors': [], 'warnings': []},
    'macros': {'us': {}, 'psx': {}, 'metals': {}},
    'universe_sizes': {'psx_total': 561, 'us_total': 5800},
    'psx_funnel': [], 'us_funnel': [],
    'psx_candidates': [], 'us_candidates': [],
    'tce_psx': [], 'tce_us': [],
    'tce_predictions': {},
    'explosive_psx': [], 'explosive_us': [],
    'rate_path': [],
    'recession': {},
}

WARNINGS = []


def load_existing():
    try:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_DATA.copy()


EXISTING = load_existing()


def log(msg):
    ts = dt.datetime.utcnow().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def warn(msg):
    WARNINGS.append(msg)
    log(f'  ⚠ {msg}')


def _series_trend(vals, w=(1,4,13)):
    """vals oldest->newest floats; returns {wow,mom,qoq (+_dir)} as window depth allows."""
    out={}
    vals=[v for v in (vals or []) if v is not None]
    if len(vals)<2: return out
    cur=vals[-1]
    for label,n in zip(('wow','mom','qoq'), w):
        if len(vals)>n:
            d=round(cur-vals[-1-n],4); out[label]=d
            out[label+'_dir']='up' if d>0 else ('down' if d<0 else 'flat')
    return out

def _push_hist(existing, date_str, value, cap=160):
    """Dedup-by-report-date {d,v} history (latest per date wins). Migrates old flat lists."""
    hist=[h if isinstance(h,dict) else {'d':None,'v':h} for h in (existing or [])]
    if value is not None:
        if hist and date_str is not None and hist[-1].get('d')==date_str:
            hist[-1]={'d':date_str,'v':value}
        else:
            hist.append({'d':date_str,'v':value})
    return hist[-cap:]

def _hist_trend(hist, w=(1,4,13)):
    return _series_trend([h['v'] for h in (hist or []) if isinstance(h,dict) and h.get('v') is not None], w)

def safe_get(d, *keys, default=None):
    try:
        for k in keys:
            d = d[k]
        return d
    except Exception:
        return default


# =============================================================
# 1. US MACRO via FRED  (+ live oil from Yahoo)
# =============================================================
def fetch_live_oil():
    out = {}
    try:
        import yfinance as yf
        for key, sym in (('wti', 'CL=F'), ('brent', 'BZ=F')):
            try:
                h = yf.Ticker(sym).history(period='5d')
                if len(h) > 0:
                    val = float(h['Close'].iloc[-1])
                    if 10 < val < 400:
                        out[key] = round(val, 2)
                        out[f'{key}_source'] = f'yahoo:{sym}'
                        try:
                            out[f'{key}_date'] = str(h.index[-1].date())
                        except Exception:
                            out[f'{key}_date'] = str(dt.date.today())
                        log(f'  ✓ {key} (live {sym}) = {out[key]} '
                            f'(as of {out.get(f"{key}_date")})')
            except Exception as e:
                log(f'  · oil {key} yahoo miss: {e}')
    except Exception as e:
        log(f'  · yfinance unavailable for oil: {e}')
    return out


def fetch_tv_oil(keys):
    """TradingView futures fallback for live oil — slots BETWEEN Yahoo and FRED.
    Live-delayed continuous front-month: WTI=NYMEX:CL1!, Brent=ICEEUR:BRN1!.
    Beats the stale FRED print when Yahoo rate-limits (proven reachable on runner)."""
    tmap = {'wti': 'NYMEX:CL1!', 'brent': 'ICEEUR:BRN1!'}
    want = {k: tmap[k] for k in keys if k in tmap}
    out = {}
    if not want:
        return out
    try:
        payload = {'symbols': {'tickers': list(want.values())}, 'columns': ['close']}
        r = requests.post('https://scanner.tradingview.com/futures/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=20)
        if r.status_code == 200:
            rows = {d['s']: d['d'][0] for d in r.json().get('data', [])}
            for k, sym in want.items():
                v = rows.get(sym)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    v = None
                if v is not None and 10 < v < 400:
                    out[k] = round(v, 2)
                    out[f'{k}_source'] = f'tradingview:{sym.split(":")[-1]}'
                    out[f'{k}_date'] = str(dt.date.today())
                    log(f'  ✓ {k} (TV fallback {sym}) = {out[k]}')
    except Exception as e:
        log(f'  · oil TV fallback miss: {e}')
    return out


def fetch_us_macros():
    import re
    log('Fetching US macros from FRED...')
    if not FRED_KEY:
        warn('FRED_API_KEY not set, using last-good US macros')
        return EXISTING.get('macros', {}).get('us', {})

    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_KEY)

        series = {
            'fed_rate':       'DFEDTARU',
            'core_pce':       'PCEPILFE',
            'cpi_yoy':        'CPIAUCSL',
            'us_10y':         'DGS10',
            'us_2y':          'DGS2',
            'unemployment':   'UNRATE',
            'umcsi':          'UMCSENT',
            'mfg_emp':        'MANEMP',
            'gdp_growth':     'A191RL1Q225SBEA',
            'industrial_prod':'INDPRO',
            'hy_spread':      'BAMLH0A0HYM2',
            'permits':        'PERMIT',
        }

        out = {}
        def _fred_series(sid):
            # v1.11: throttle + retry-with-backoff to avoid FRED 429 'Too Many Requests'.
            # No new source needed — same free API key, just paced (3 tries: 0/1.5/4s).
            last = None
            for attempt, backoff in enumerate((0, 1.5, 4.0)):
                if backoff:
                    time.sleep(backoff)
                try:
                    return fred.get_series(sid).dropna()
                except Exception as e:
                    last = e
                    if 'Too Many' in str(e) or '429' in str(e):
                        continue   # rate-limited — wait and retry
                    raise          # other errors: don't burn retries
            raise last
        for key, sid in series.items():
            try:
                time.sleep(0.6)    # gentle spacing between series (12 × 0.6s ≈ 7s)
                s = _fred_series(sid)
                if len(s) > 0:
                    val = float(s.iloc[-1])
                    if key in ('core_pce', 'cpi_yoy'):
                        if len(s) >= 13:
                            val = round(((s.iloc[-1] / s.iloc[-13]) - 1) * 100, 2)
                        else:
                            val = round(val, 2)
                    else:
                        val = round(val, 2)
                    out[key] = val
                    out[f'{key}_date'] = str(s.index[-1].date())
                    if key in ('us_10y','us_2y','hy_spread'):
                        for _tk,_tv in _series_trend([round(float(x),2) for x in s.values[-64:]], w=(5,21,63)).items():
                            out[f'{key}_{_tk}'] = _tv
                    log(f'  ✓ {key} = {out[key]}')
            except Exception as e:
                warn(f'FRED {key} ({sid}) failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'us', key)
                if lg is not None:
                    out[key] = lg
                    log(f'  · {key}: kept last-good = {lg}')

        if out.get('us_10y') is not None and out.get('us_2y') is not None:
            out['us_2s10s'] = round(out['us_10y'] - out['us_2y'], 2)
        # Live oil — Yahoo first, then TradingView futures, then FRED (last resort, may be stale)
        oil = fetch_live_oil()
        _oil_missing = [k for k in ('wti', 'brent') if k not in oil]
        if _oil_missing:
            oil.update(fetch_tv_oil(_oil_missing))
        for key, fred_id in (('wti', 'DCOILWTICO'), ('brent', 'DCOILBRENTEU')):
            if key in oil:
                out[key] = oil[key]
                out[f'{key}_source'] = oil[f'{key}_source']
                out[f'{key}_date']   = oil.get(f'{key}_date')
            else:
                try:
                    s = _fred_series(fred_id)   # F2: same retry/backoff as the main series loop
                    if len(s) > 0:
                        out[key] = round(float(s.iloc[-1]), 2)
                        out[f'{key}_source'] = f'fred:{fred_id} (may lag)'
                        out[f'{key}_date']   = str(s.index[-1].date())
                        warn(f'{key} live source missed; FRED value may be stale')
                except Exception as e:
                    warn(f'{key} FRED fallback failed: {e}')
                    lg = safe_get(EXISTING, 'macros', 'us', key)
                    if lg is not None:
                        out[key] = lg
                        out[f'{key}_source'] = 'last-good'

        try:
            if out.get('brent') and out.get('wti'):
                out['brent_wti_spread'] = round(out['brent'] - out['wti'], 2)
                log(f'  ✓ Brent-WTI spread = {out["brent_wti_spread"]}')
        except Exception:
            pass

        # US rotary rig count (F1) — third-party source: EIA (US gov) republishes the Baker Hughes
        # count as monthly "Crude Oil & Natural Gas Rotary Rigs in Operation" (TOTAL oil+gas; oil-only
        # is BH-proprietary & bot-blocked at TE/YCharts). Data is monthly + the page is heavy, so
        # cadence-gate to weekly (like ETF/Zacks): ~0 cost most runs, the rare fetch gets a real read window.
        _rig_prev = safe_get(EXISTING, 'macros', 'us', 'us_oil_rigs')
        _rig_utc = safe_get(EXISTING, 'macros', 'us', 'us_rigs_utc')
        _rig_age = None
        if _rig_utc:
            try:
                _rig_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_rig_utc).replace('Z', ''))).days
            except Exception:
                _rig_age = None
        if _rig_prev is not None and _rig_age is not None and _rig_age < 7:
            out['us_oil_rigs'] = _rig_prev
            out['us_rigs_utc'] = _rig_utc
            log(f'  → US rigs skipped (EIA fetch {_rig_age}d ago, <7d) — last-good {_rig_prev}')
        else:
            try:
                rr = requests.get('https://www.eia.gov/dnav/ng/hist/e_ertrr0_xr0_nus_cm.htm',
                                  headers={'User-Agent': UA}, timeout=(4, 12))
                if rr.status_code == 200:
                    t = re.sub(r'<[^>]+>', ' ', rr.text).replace('&nbsp;', ' ')
                    cut = t.find('No Data Reported')
                    if cut > 0:
                        t = t[:cut]
                    vals = [int(n.replace(',', '')) for n in re.findall(r'\d[\d,]{1,5}', t)]
                    for v in reversed(vals):           # most-recent plausible rig value; skip year tokens
                        if 100 <= v <= 6000 and not (1900 <= v <= 2100):
                            out['us_oil_rigs'] = v
                            out['us_rigs_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
                            log(f'  ✓ US rotary rigs (EIA, total oil+gas): {v}')
                            break
            except Exception as e:
                log(f'  · US rigs (EIA): {e}')
            if out.get('us_oil_rigs') is None and _rig_prev is not None:
                out['us_oil_rigs'] = _rig_prev
                log('  · US rigs: EIA unreachable; using last-good')

        # FOMC / Fed monetary-policy announcements (live — official Fed press-release RSS)
        try:
            import feedparser
            ffeed = feedparser.parse('https://www.federalreserve.gov/feeds/press_monetary.xml')
            items = []
            for e in ffeed.entries[:25]:
                pub = None
                if getattr(e, 'published_parsed', None):
                    pub = dt.datetime(*e.published_parsed[:6]).date().isoformat()
                items.append({'title': (getattr(e, 'title', '') or '').strip(),
                              'link':  getattr(e, 'link', '') or '',
                              'date':  pub})
            fomc = None
            for it in items:
                t = it['title'].lower()
                if 'fomc' in t or 'federal open market' in t or 'monetary policy' in t:
                    fomc = it; break
            if fomc is None and items:
                fomc = items[0]
            if fomc:
                tl = fomc['title'].lower()
                stance = ('QT' if any(w in tl for w in ('reduce', 'runoff', 'reducing', 'taper'))
                          else 'QE' if any(w in tl for w in ('purchase', 'expand its', 'increase its holdings'))
                          else None)
                days = None
                if fomc.get('date'):
                    try:
                        days = (dt.date.today() - dt.date.fromisoformat(fomc['date'])).days
                    except Exception:
                        days = None
                out['fomc'] = {'title': fomc['title'], 'link': fomc['link'], 'date': fomc['date'],
                               'days_ago': days, 'stance': stance, 'recent': items[:5]}
                log(f'  \u2713 FOMC: {fomc.get("date")} \u2014 {fomc["title"][:60]}')
        except Exception as e:
            log(f'  \u00b7 FOMC RSS (last-good): {e}')
            lg = safe_get(EXISTING, 'macros', 'us', 'fomc')
            if lg is not None:
                out['fomc'] = lg

        log(f'  Total US macros: '
            f'{len([k for k in out if not k.endswith(("_date","_source"))])}')
        return out

    except Exception as e:
        log(f'  US macros FAILED: {e}')
        traceback.print_exc()
        return EXISTING.get('macros', {}).get('us', {})


# =============================================================
# 2. PSX MACRO
# =============================================================
def _kse_sane(v):
    """Accept only index-magnitude numbers (rejects share prices and most volumes)."""
    try:
        v = float(v)
        return v if KSE_MIN < v < KSE_MAX else None
    except Exception:
        return None


def _kse_ts_to_date(ts):
    try:
        ts = float(ts)
        if ts > 1e12:
            ts /= 1000.0
        return str(dt.datetime.utcfromtimestamp(ts).date())
    except Exception:
        return None


def _kse_grab(text):
    """Find the KSE-100 index value in an HTML page. Prefers a decimal number
    (the index prints as 171651.48; share volumes are integers) to avoid
    false-matching a volume figure that happens to sit in the index range."""
    import re
    anchor = re.search(r'KSE\s*-?\s*100', text, re.I)
    if not anchor:
        return None
    window = text[anchor.end(): anchor.end() + 400]
    for pat in (r'[\d,]{5,}\.\d+', r'[\d,]{5,}'):   # decimal first, then integer fallback
        for num in re.findall(pat, window):
            v = _kse_sane(num.replace(',', ''))
            if v is not None:
                return round(v, 2)
    return None


def _kse_extract_ts(rows):
    """Pull (value, date_str) from a dps.psx timeseries 'data' array. Pure."""
    if not rows:
        return None, None
    last = rows[-1]
    val = None
    date_str = None
    if isinstance(last, (list, tuple)):
        if len(last) >= 1:
            date_str = _kse_ts_to_date(last[0])
        if len(last) >= 5:
            val = _kse_sane(last[4])
        if val is None and len(last) >= 2:
            val = _kse_sane(last[1])
    return (round(val, 2) if val is not None else None), date_str


def fetch_kse100():
    """KSE-100 index level. Resolved from v1.22.1 diagnostics:
      - The index lives on the dps.psx *intraday* (`int`) timeseries — it ends at the
        last trading session (171651.48 @ 2026-06-05) and is the CURRENT source.
      - The `eod` timeseries for the index symbol is frozen at 2021 (~48,300) — stale
        and below the sanity floor; never preferred.
      - market-watch/indices HTML only carry index *membership tags* / meta text, not
        the live level (JS-rendered), so they are not fetched (market-watch is ~470 KB).
    Strategy: read both timeseries, keep the one with the most recent row date (int in
    practice). The value reads identically across same-day runs because it is the last
    session close — that is correct, not stale."""
    headers = {'User-Agent': UA, 'Accept': 'application/json'}
    today = str(dt.date.today())
    best = None  # (val, date_str, src)
    for path, label in (('int', 'psx-dps:int (last session close)'),
                        ('eod', 'psx-dps:eod')):
        try:
            r = requests.get(f'https://dps.psx.com.pk/timeseries/{path}/KSE100',
                             headers=headers, timeout=12)
            if r.status_code == 200:
                j = r.json()
                rows = j.get('data') if isinstance(j, dict) else j
                v, d = _kse_extract_ts(rows)
                if v is not None:
                    if best is None or (d and best[1] and d > best[1]) or (d and not best[1]):
                        best = (v, d, label)
        except Exception as e:
            log(f'  · KSE-100 dps/{path} miss: {e}')

    if best is not None:
        return best[0], best[2], (best[1] or today)
    return None, None, None


def fetch_psx_macros():
    log('Fetching PSX macros...')
    out = EXISTING.get('macros', {}).get('psx', {}).copy()
    import re
    headers = {'User-Agent': UA}

    val, src, dstr = fetch_kse100()
    if val is not None:
        out['kse100'] = val
        out['kse100_source'] = src
        out['kse100_date'] = dstr
        log(f'  ✓ KSE-100 ({src}): {val} (as of {dstr})')
    else:
        lg = safe_get(EXISTING, 'macros', 'psx', 'kse100')
        if lg is not None:
            out['kse100'] = lg
            out['kse100_source'] = 'last-good (STALE)'
            out['kse100_date'] = safe_get(EXISTING, 'macros', 'psx', 'kse100_date')
            warn(f'KSE-100 all live sources failed; using STALE last-good {lg}')
        else:
            out['kse100'] = None
            warn('KSE-100 unavailable and no last-good value')

    try:
        import yfinance as yf
        h = yf.Ticker('USDPKR=X').history(period='6mo')
        if len(h) > 0:
            out['usd_pkr'] = round(float(h['Close'].iloc[-1]), 2)
            for _tk,_tv in _series_trend([round(float(x),2) for x in h['Close'].values[-64:]], w=(5,21,63)).items():
                out['usd_pkr_'+_tk] = _tv
            log(f'  ✓ USD/PKR: {out["usd_pkr"]}')
    except Exception as e:
        warn(f'USD/PKR failed: {e}')

    try:
        r = requests.get('https://www.sbp.org.pk/m_policy/index.asp',
                         headers=headers, timeout=15)
        if r.status_code == 200:
            m = re.search(r'(\d{1,2}\.\d{1,2})\s*(?:percent|%)', r.text, re.I)
            if m:
                out['sbp_rate'] = float(m.group(1))
                log(f'  ✓ SBP rate (SBP official): {out["sbp_rate"]}%')
    except Exception as e:
        log(f'  · SBP rate: {e}')
    if out.get('sbp_rate') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'sbp_rate')
        if lg is not None:
            out['sbp_rate'] = lg

    # CPI YoY — primary: TheGlobalEconomy (PBS-sourced, monthly, fetchable & parseable),
    # then PBS direct, then TE (below), then last-good. The _tge helper reads the most-recent
    # row of a TheGlobalEconomy per-indicator page and is reusable for other PSX macros.
    def _tge(slug, diag=False):
        try:
            rr = requests.get(f'https://www.theglobaleconomy.com/Pakistan/{slug}/',
                              headers={'User-Agent': UA}, timeout=15)
            if rr.status_code != 200:
                if diag: log(f'    · [diag] TGE {slug}: HTTP {rr.status_code}')
                return None
            txt = re.sub(r'<[^>]+>', ' ', rr.text)
            txt = txt.replace('&nbsp;', ' ').replace('&nbsp', ' ')  # entity survives tag-strip; year/month joined by it
            txt = re.sub(r'\s+', ' ', txt)            # collapse newlines/tabs so the row is contiguous
            i = txt.find('Recent values')
            seg = txt[i:i + 500] if i >= 0 else txt
            # accept "YYYY Mon <val>" or "Mon YYYY <val>"; values may carry commas
            m = re.search(r'(?:(?:19|20)\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|'
                          r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:19|20)\d{2})'
                          r'\s+(-?[\d,]+(?:\.\d+)?)', seg)
            if not m:
                if diag: log(f'    · [diag] TGE {slug}: 200 len={len(rr.text)} hasRecent={i>=0} seg={seg[:170]!r}')
                return None
            return float(m.group(1).replace(',', ''))
        except Exception as e:
            if diag: log(f'    · [diag] TGE {slug}: {type(e).__name__} {str(e)[:80]}')
            return None
    try:
        v = _tge('inflation_annual', diag=True)   # CPI YoY %, monthly (e.g. 7.30 for Mar 2026)
        if v is not None:
            out['pak_cpi'] = v
            log(f'  ✓ Pak CPI YoY (TheGlobalEconomy): {v}%')
        else:
            log('    · [diag] TheGlobalEconomy inflation_annual: no value parsed')
    except Exception as e:
        log(f'  · Pak CPI (TheGlobalEconomy): {e}')
    if out.get('pak_cpi') is None:
        try:
            r = requests.get('https://www.pbs.gov.pk/cpi', headers=headers, timeout=15)
            if r.status_code == 200:
                m = re.search(r'(\d{1,2}\.\d{1,2})\s*(?:percent|%)', r.text, re.I)
                if m:
                    out['pak_cpi'] = float(m.group(1)); log(f'  ✓ Pak CPI (PBS): {out["pak_cpi"]}%')
        except Exception as e:
            log(f'  · Pak CPI (PBS): {e}')
    if out.get('pak_cpi') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'pak_cpi')
        if lg is not None:
            out['pak_cpi'] = lg

    # F4 source resolution: CPI is now live-monthly via TheGlobalEconomy. REER / Current Account /
    # Fiscal have NO free monthly fetchable feed (SBP/PBS=PDF; FRED Pakistan=annual-only; TE blocks
    # bots; TheGlobalEconomy & World Bank carry these three only annually). They stay best-effort TE
    # → last-good → Tab-1 manual (update quarterly from the AKD/Topline economy report).

    # F4/F3: best-effort live fetch (free, Trading Economics) for the slow-moving Pakistan
    # macros that had no live source. Fully guarded — on ANY failure the last-good fallbacks
    # below apply, so this can never break the run. Validates on the live run (TE may block
    # bots; last-good remains the reliable backstop — spot-check against broker monthlies).
    def _te(slug, label):
        try:
            rr = requests.get('https://tradingeconomics.com/pakistan/' + slug,
                              headers={'User-Agent': UA}, timeout=12)
            if rr.status_code != 200:
                return None
            txt = re.sub(r'<[^>]+>', ' ', rr.text)
            m = re.search(label + r'[^0-9\-]{0,40}(-?\d{1,4}(?:\.\d{1,2})?)', txt, re.I)
            return float(m.group(1)) if m else None
        except Exception:
            return None
    try:
        if out.get('pak_cpi') is None:
            v = _te('inflation-cpi', 'Inflation Rate')
            if v is not None: out['pak_cpi'] = v; log(f'  ✓ Pak CPI (TE): {v}%')
        if out.get('reer') is None:
            v = _te('real-effective-exchange-rate', 'Real Effective')
            if v is not None: out['reer'] = v; log(f'  ✓ REER (TE): {v}')
        if out.get('pak_ca') is None:
            v = _te('current-account', 'Current Account')
            if v is not None: out['pak_ca'] = v; log(f'  ✓ Current account (TE): {v}')
        if out.get('pak_fiscal') is None:
            v = _te('government-budget', 'Government Budget')
            if v is not None: out['pak_fiscal'] = v; log(f'  ✓ Fiscal balance (TE): {v}% GDP')
        if out.get('sbp_reserves') is None:
            v = _te('foreign-exchange-reserves', 'Foreign Exchange Reserves')
            if v is not None: out['sbp_reserves'] = round(v/1000.0, 2) if v > 1000 else v; log(f'  ✓ SBP reserves (TE): {out["sbp_reserves"]}')
    except Exception as e:
        log(f'  · TE Pakistan macros (best-effort): {e}')

    log('  → SBP reserves: official page is PDF; keeping last-good if TE missed (manual override)')
    if out.get('sbp_reserves') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'sbp_reserves')
        if lg is not None:
            out['sbp_reserves'] = lg
    # T1: value-change-dedup reserves history + WoW/MoM/QoQ trend (SBP weekly data, daily runs)
    if out.get('sbp_reserves') is not None:
        _rh = [h if isinstance(h, dict) else {'d': None, 'v': h}
               for h in (safe_get(EXISTING, 'macros', 'psx', 'sbp_reserves_hist') or [])]
        if not _rh or _rh[-1].get('v') != out['sbp_reserves']:
            _rh.append({'d': None, 'v': out['sbp_reserves']})
        _rh = _rh[-160:]
        out['sbp_reserves_hist'] = _rh
        for _k, _v in _series_trend([h['v'] for h in _rh if isinstance(h, dict) and h.get('v') is not None]).items():
            out['sbp_reserves_'+_k] = _v

    if out.get('reer') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'reer')
        if lg is not None:
            out['reer'] = lg

    # v1.11: pak_ca and pak_fiscal have no live source yet — seed last-good so the
    # Gold tab's Pakistan factors don't silently fall back to Tab-1 manual values.
    for _k in ('pak_ca', 'pak_fiscal', 'neer'):
        if out.get(_k) is None:
            _lg = safe_get(EXISTING, 'macros', 'psx', _k)
            if _lg is not None:
                out[_k] = _lg

    _manual = [k for k in ('reer', 'pak_ca', 'pak_fiscal') if out.get(k) is not None]
    log(f'  → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: {_manual or "none"}')

    return out


# =============================================================
# 2c. COT FUTURES (sector gating) — CFTC Socrata, ported verbatim from M1 fetchCOT()
#     SP500/10yr/VIX/NASDAQ from TFF (Asset Manager net); Crude from Disaggregated (Managed Money).
# =============================================================
COT_KEYWORDS = {
    'SP500':  'S&P 500',
    '10yr':   'UST 10Y NOTE',
    'VIX':    'VIX FUTURES',
    'NASDAQ': 'NASDAQ-100',
}
COT_KEYWORDS_COMMODITIES = {'Crude': 'WTI-PHYSICAL'}

def fetch_cot_futures():
    """5 index/commodity COT contracts used to gate US sector selection.
    Returns {contract: {long, short, net, signal, date}}.  Never raises."""
    out = {}
    headers = {'User-Agent': UA}
    # --- TFF financial futures: SP500, 10yr, VIX, NASDAQ ---
    try:
        url = ('https://publicreporting.cftc.gov/resource/gpe5-46if.json'
               '?$order=report_date_as_yyyy_mm_dd DESC&$limit=100')
        rows = requests.get(url, headers=headers, timeout=(8, 12)).json()
        found = set()
        _ser = {k: [] for k in COT_KEYWORDS}   # newest->oldest net per contract (rows are DESC)
        for rec in rows:
            name = str(rec.get('market_and_exchange_names', '')).upper()
            for key, kw in COT_KEYWORDS.items():
                if kw.upper() in name:
                    lng = float(rec.get('asset_mgr_positions_long', 0) or 0)
                    sht = float(rec.get('asset_mgr_positions_short', 0) or 0)
                    net = lng - sht
                    _ser[key].append(net)
                    if key not in out:   # first (latest) row defines the headline
                        out[key] = {'long': int(lng), 'short': int(sht), 'net': int(net),
                                    'signal': ('VERY BULLISH' if net > 500000 else 'BULLISH' if net > 0
                                               else 'BEARISH' if net > -500000 else 'VERY BEARISH'),
                                    'date': rec.get('report_date_as_yyyy_mm_dd')}
                        found.add(key)
        for key in found:                  # T1: backfilled WoW/MoM/QoQ net trend from the DESC rows
            for _k, _v in _series_trend(list(reversed(_ser[key]))[-14:]).items():
                out[key]['net_'+_k] = _v
        log(f'  ✓ COT futures (TFF): {len(found)}/4 [{", ".join(sorted(found))}]')
    except Exception as e:
        warn(f'COT futures (TFF) failed: {e}')
    # --- Disaggregated: Crude (Managed Money) ---
    try:
        url = ('https://publicreporting.cftc.gov/resource/72hh-3qpy.json'
               '?$order=report_date_as_yyyy_mm_dd DESC&$limit=200')
        rows = requests.get(url, headers=headers, timeout=(8, 12)).json()
        _cser = []
        for rec in rows:
            name = str(rec.get('market_and_exchange_names', '')).upper()
            if 'WTI-PHYSICAL' in name and 'NEW YORK' in name:
                lng = float(rec.get('m_money_positions_long_all', 0) or 0)
                sht = float(rec.get('m_money_positions_short_all', 0) or 0)
                net = lng - sht
                _cser.append(net)
                if 'Crude' not in out:
                    out['Crude'] = {'long': int(lng), 'short': int(sht), 'net': int(net),
                                    'signal': ('VERY BULLISH' if net > 200000 else 'BULLISH' if net > 0
                                               else 'BEARISH' if net > -200000 else 'VERY BEARISH'),
                                    'date': rec.get('report_date_as_yyyy_mm_dd')}
        if 'Crude' in out:
            for _k, _v in _series_trend(list(reversed(_cser))[-14:]).items():
                out['Crude']['net_'+_k] = _v
        log(f'  ✓ COT futures Crude: {"found" if "Crude" in out else "not found"}')
    except Exception as e:
        warn(f'COT futures (Crude) failed: {e}')
    # last-good fallback
    if not out:
        lg = safe_get(EXISTING, 'cot_futures')
        if lg:
            out = lg
    return out

# =============================================================
# 2d. ZACKS SECTOR ENGINE — per-ticker rank scrape (M1 quote-feed method),
#     #1/#2 grouped by GICS sector to qualify sectors.  Never raises.
# =============================================================
ZACKS_SECTOR_UNIVERSE = {
    # Fixed S&P representative list across all 11 GICS sectors (large-cap sector read).
    'Information Technology': ['MSFT','NVDA','AVGO','AAPL','ORCL','CRM','AMD','ADBE','CSCO','ACN','TXN','QCOM','INTC','IBM','NOW','MU','AMAT','LRCX','ANET','DELL'],
    'Health Care':           ['LLY','UNH','JNJ','ABBV','MRK','TMO','ABT','ISRG','DHR','PFE','AMGN','BMY','CI','GILD','VRTX','CVS','MDT','ELV','REGN','HCA'],
    'Financials':            ['JPM','BAC','WFC','GS','MS','SPGI','AXP','BLK','C','SCHW','CB','PGR','MMC','BX','PNC','USB','TFC','AON','ICE','COF'],
    'Consumer Discretionary':['AMZN','TSLA','HD','MCD','NKE','LOW','BKNG','SBUX','TJX','ORLY','GM','F','MAR','CMG','ROST','HLT','YUM','DHI','LEN','AZO'],
    'Communication Services':['GOOGL','META','NFLX','DIS','TMUS','VZ','T','CMCSA','CHTR','EA','TTWO','WBD','OMC','LYV','MTCH','FOXA','PARA','NWSA','IPG','DASH'],
    'Industrials':           ['CAT','GE','RTX','UNP','HON','ETN','BA','LMT','DE','UPS','ADP','GD','NOC','EMR','CSX','ITW','MMM','FDX','WM','PH'],
    'Consumer Staples':      ['WMT','PG','KO','PEP','COST','MDLZ','PM','MO','CL','TGT','KMB','GIS','SYY','KHC','STZ','KR','HSY','KDP','MNST','ADM'],
    'Energy':                ['XOM','CVX','COP','EOG','SLB','MPC','PSX','OXY','WMB','VLO','PXD','HES','KMI','OKE','HAL','DVN','FANG','BKR','MRO','CTRA'],
    'Materials':             ['LIN','SHW','APD','ECL','FCX','NEM','NUE','DOW','DD','CTVA','PPG','VMC','MLM','ALB','IFF','LYB','STLD','CF','MOS','BALL'],
    'Utilities':             ['NEE','DUK','SO','D','AEP','SRE','EXC','XEL','PEG','ED','VST','WEC','EIX','AWK','DTE','PCG','AEE','CNP','CMS','ATO'],
    'Real Estate':           ['PLD','AMT','EQIX','WELL','CCI','PSA','O','SPG','DLR','VICI','CBRE','EXR','AVB','EQR','VTR','SBAC','WY','INVH','ARE','MAA'],
}
def _gics_from_yahoo(sec):
    if not sec: return None
    s = sec.lower()
    m = {'technology':'Information Technology','healthcare':'Health Care','financial':'Financials',
         'consumer cyclical':'Consumer Discretionary','communication':'Communication Services',
         'industrials':'Industrials','consumer defensive':'Consumer Staples','energy':'Energy',
         'basic materials':'Materials','utilities':'Utilities','real estate':'Real Estate'}
    for k,v in m.items():
        if k in s: return v
    return None

# ===================== Smart-Money ETF Holdings Overlap (Part D) =====================
# Screen a broad ETF candidate universe through Zacks Rank, keep #1/#2, fetch each
# survivor's holdings, aggregate by stock to find CONVICTION OVERLAP, flag Zacks-confirmed
# names. Weekly cadence (holdings barely move week-to-week). The Zacks rank screen reuses
# the same quote-feed endpoint the stock scrape uses (proven on the runner). The holdings
# fetch hits stockanalysis.com — that domain isn't on the sandbox allowlist, so it validates
# on the GitHub run; the aggregation/ranking below is pure logic and is unit-tested locally.
# Fixed universe: the user's top-30 Zacks Rank-#1, US, Equities ETFs by 1-Year performance
# (from the Zacks ETF screener, 2026-06-03). NO per-run rank screening — these are
# pre-confirmed #1; the scan only fetches their holdings and builds the overlap. Refresh
# this list quarterly when Zacks re-ranks. Holdings fetch (stockanalysis.com) validates on
# the GitHub run; the aggregation/ranking below is pure logic and is unit-tested locally.
TOP_ETFS = [
    'FTXL','PSI','SOXX','SOXQ','XSD','IGPT','PSCT','KNCT','VLUE','RSPT',
    'XNTK','XLK','QTEC','IDGT','IGM','FTEC','VGT','IYW','PWB','VDE',
    'XLE','QQQM','QQQ','VTWO','RPG','BIBL','SNPG','VB','VONV','IWD',
]
ETF_OVERLAP_TOP_N = 25     # number of consensus stocks to surface

# Authoritative per-ETF metrics from the user's Zacks ETF screen (2026-06-03): (name, YTD%, 1Y%).
# 3Y% and expense ratio aren't in the Zacks ETF export, so the scan fetches those two from
# Yahoo (validates on the GitHub run; shows None/'—' if Yahoo doesn't return them).
ETF_META = {
 'FTXL':('First Trust NASDAQ Semiconductor ETF',100.1,215.4),
 'PSI':('Invesco Semiconductors ETF',94.8,201.9),
 'SOXX':('iShares Semiconductor ETF',90.0,179.9),
 'SOXQ':('Invesco PHLX Semiconductor ETF',83.1,173.0),
 'XSD':('SPDR S&P Semiconductor ETF',87.0,172.2),
 'IGPT':('Invesco AI and Next Gen Software ETF',71.3,127.9),
 'PSCT':('Invesco S&P SmallCap Info Technology ETF',50.8,100.8),
 'KNCT':('Invesco Next Gen Connectivity ETF',60.8,99.2),
 'VLUE':('iShares MSCI USA Value Factor ETF',47.8,91.0),
 'RSPT':('Invesco S&P 500 Equal Weight Technology ETF',45.9,77.9),
 'XNTK':('SPDR NYSE Technology ETF',35.8,74.9),
 'XLK':('Technology Select Sector SPDR ETF',36.1,70.2),
 'QTEC':('First Trust NASDAQ-100 Technology ETF',42.7,70.0),
 'IDGT':('iShares U.S. Digital Infrastructure & RE ETF',53.3,66.0),
 'IGM':('iShares Expanded Tech Sector ETF',31.0,65.0),
 'FTEC':('Fidelity MSCI Info Technology Index ETF',32.1,65.0),
 'VGT':('Vanguard Information Technology ETF',31.9,64.4),
 'IYW':('iShares U.S. Technology ETF',29.2,63.2),
 'PWB':('Invesco Large Cap Growth ETF',27.8,47.1),
 'VDE':('Vanguard Energy ETF',29.3,45.1),
 'XLE':('Energy Select Sector SPDR ETF',29.0,44.2),
 'QQQM':('Invesco NASDAQ 100 ETF',21.0,43.7),
 'QQQ':('Invesco QQQ',21.0,43.6),
 'VTWO':('Vanguard Russell 2000 ETF',17.6,42.2),
 'RPG':('Invesco S&P 500 Pure Growth ETF',30.0,41.8),
 'BIBL':('Inspire 100 ETF',20.9,38.5),
 'SNPG':('Xtrackers S&P 500 Growth ETF',10.8,30.7),
 'VB':('Vanguard Small-Cap ETF',14.0,30.0),
 'VONV':('Vanguard Russell 1000 Value ETF',13.3,27.9),
 'IWD':('iShares Russell 1000 Value ETF',13.3,27.8),
}

def fetch_etf_meta(etf):
    """3Y return + expense ratio for an ETF via Yahoo. Guarded; returns {y3, expense} (None if missing)."""
    out = {'y3': None, 'expense': None}
    try:
        import yfinance as _yf
        t = _yf.Ticker(etf)
        try:
            h = t.history(period='3y')
            c = h['Close'].dropna() if (h is not None and not h.empty) else None
            if c is not None and len(c) > 2:
                out['y3'] = round((float(c.iloc[-1]) / float(c.iloc[0]) - 1) * 100, 1)
        except Exception:
            pass
        try:
            info = t.info or {}
            ne = info.get('netExpenseRatio')           # Yahoo: already in PERCENT (0.60 = 0.60%)
            ar = info.get('annualReportExpenseRatio')  # Yahoo: a FRACTION (0.006 = 0.60%)
            ex = float(ne) if ne is not None else (float(ar) * 100 if ar is not None else None)
            if ex is not None:
                if ex > 5:        # no ETF charges >5%; guard against any unit surprise
                    ex /= 100
                out['expense'] = round(ex, 2)
        except Exception:
            pass
    except Exception as e:
        log(f'    · meta fetch failed for {etf}: {e}')
    return out

_ETF_DIAG = {'done': False}
def _parse_holdings(rows):
    out = []
    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        sym = row.get('asset') or row.get('symbol') or row.get('s') or row.get('ticker')
        wt  = (row.get('weightPercentage') if row.get('weightPercentage') is not None else
               row.get('weight') if row.get('weight') is not None else
               row.get('w') if row.get('w') is not None else
               row.get('as') if row.get('as') is not None else
               row.get('assetsPercent') if row.get('assetsPercent') is not None else
               row.get('percent') if row.get('percent') is not None else row.get('assetPercent'))
        if sym and wt is not None:
            try:
                tk = str(sym).upper().strip().lstrip('$').strip()
                if tk:
                    out.append({'ticker': tk, 'weight': float(str(wt).replace('%','').replace(',','').strip())})
            except Exception:
                pass
    return out

def fetch_etf_holdings(etf):
    """ETF holdings -> [{ticker, weight}]. stockanalysis.com is the working free source (FMP
    holdings is premium-402 / v3 legacy-403 on the free key, so it's fallback-only).
    Logs a ONE-TIME diagnostic (status + body snippet + rows parsed) for the first ETF so a
    failure is debuggable from the run log instead of silently returning []."""
    diag = not _ETF_DIAG['done']
    sources = [('stockanalysis', f'https://stockanalysis.com/api/symbol/e/{etf}/holdings')]
    if FMP_KEY:
        sources += [
            ('fmp-stable', f'https://financialmodelingprep.com/stable/etf/holdings?symbol={etf}&apikey={FMP_KEY}'),
            ('fmp-v3',     f'https://financialmodelingprep.com/api/v3/etf-holder/{etf}?apikey={FMP_KEY}'),
        ]
    sources.append(('stockanalysis', f'https://stockanalysis.com/api/symbol/e/{etf}/holdings'))
    result = []
    for label, url in sources:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
            if diag:
                log(f'    · [diag] {label} {etf}: HTTP {r.status_code} body[:180]={r.text[:180]!r}')
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, list):
                    rows = j
                elif isinstance(j, dict):
                    dn = j.get('data')
                    rows = (dn.get('list') or dn.get('holdings') if isinstance(dn, dict) else dn) \
                           or j.get('holdings') or j.get('list') or []
                else:
                    rows = []
                parsed = _parse_holdings(rows)
                if diag:
                    log(f'    · [diag] {label} {etf}: parsed {len(parsed)} holdings')
                if parsed:
                    result = parsed
                    break
        except Exception as e:
            if diag:
                log(f'    · [diag] {label} {etf}: EXC {e}')
    if diag:
        _ETF_DIAG['done'] = True
    return result

def build_etf_overlap(rank12_etfs, holdings_map, zacks_top_tickers, top_n=ETF_OVERLAP_TOP_N):
    """Aggregate holdings across Zacks #1/#2 ETFs. conviction = blend(weight, breadth) with a
    Zacks-confirmed boost. Pure logic / unit-tested. Returns ranked top-N consensus stocks."""
    agg = {}
    for e in rank12_etfs:
        tk = e['etf']
        for h in holdings_map.get(tk, []):
            s = (h.get('ticker') or '').upper().strip()
            if not s or len(s) > 6 or s == tk:
                continue
            a = agg.setdefault(s, {'weight_sum':0.0, 'etfs':set()})
            a['weight_sum'] += float(h.get('weight') or 0)
            a['etfs'].add(tk)
    n_etf = max(len(rank12_etfs), 1)
    max_w = max((a['weight_sum'] for a in agg.values()), default=1.0) or 1.0
    zset = set(zacks_top_tickers or [])
    rows = []
    for s, a in agg.items():
        breadth = len(a['etfs'])
        w_norm = a['weight_sum'] / max_w
        b_norm = breadth / n_etf
        zc = s in zset
        conviction = round(100*(0.55*w_norm + 0.35*b_norm) + (10 if zc else 0), 1)
        rows.append({'ticker': s, 'etf_count': breadth, 'agg_weight': round(a['weight_sum'],2),
                     'conviction': conviction, 'zacks_confirmed': zc, 'in_etfs': sorted(a['etfs'])[:8]})
    rows.sort(key=lambda r: (-r['conviction'], -r['etf_count'], -r['agg_weight']))
    top = rows[:top_n]
    tot_w = sum(r['agg_weight'] for r in top) or 1.0
    for r in top:
        r['alloc_pct'] = round(r['agg_weight'] / tot_w * 100, 2)   # mirror-able weight across the shown names
    return top
# =====================================================================================

def fetch_zacks_sectors(survivors=None):
    """Scrape per-ticker Zacks rank for the fixed S&P universe + scan survivors (deduped),
    keep #1/#2, group by GICS sector. Returns {sector:{rank1,rank2,top,total,pct_top,top_tickers}}."""
    # Build universe: fixed list (with known sector) + survivors (sector from their record)
    uni = {}  # ticker -> gics sector
    for sec, tickers in ZACKS_SECTOR_UNIVERSE.items():
        for t in tickers:
            uni[t] = sec
    if survivors:
        for r in survivors:
            tk = r.get('ticker'); g = _gics_from_yahoo(r.get('sector'))
            if tk and g and tk not in uni:
                uni[tk] = g
    tickers = sorted(uni.keys())
    log(f'=== Zacks sector scrape: {len(tickers)} tickers (~{len(tickers)*2.5/60:.0f} min) ===')
    sectors = {s: {'rank1':0,'rank2':0,'top':0,'total':0,'pct_top':0.0,'top_tickers':[]}
               for s in ZACKS_SECTOR_UNIVERSE}
    fails = 0
    for i, tk in enumerate(tickers):
        sec = uni[tk]
        if sec not in sectors:
            sectors[sec] = {'rank1':0,'rank2':0,'top':0,'total':0,'pct_top':0.0,'top_tickers':[]}
        try:
            time.sleep(2.5)
            d = requests.get(f'https://quote-feed.zacks.com/index?t={tk}',
                             headers={'User-Agent':'Mozilla/5.0'}, timeout=15).json()
            rec = d.get(tk, {}) or {}
            rank = rec.get('zacks_rank')
            rank = int(rank) if rank not in (None,'','null') else None
            sectors[sec]['total'] += 1
            if rank == 1:
                sectors[sec]['rank1'] += 1; sectors[sec]['top'] += 1; sectors[sec]['top_tickers'].append(tk)
            elif rank == 2:
                sectors[sec]['rank2'] += 1; sectors[sec]['top'] += 1; sectors[sec]['top_tickers'].append(tk)
        except Exception:
            fails += 1
    for s, v in sectors.items():
        v['pct_top'] = round(v['top']/v['total']*100, 1) if v['total'] else 0.0
    log(f'  Zacks sector scrape done: {fails} failures of {len(tickers)}')
    return sectors

# =============================================================
# 2b. METALS DATA — Tab 12 Gold & Metals
# =============================================================
def fetch_metals():
    """
    Fetches all data for Tab 12:
    - Metal spot prices: GC=F, SI=F, PL=F, PA=F (Yahoo)
    - DXY Dollar Index: DX-Y.NYB (Yahoo)
    - Fed balance sheet QE/QT: WALCL (FRED)
    - COT positioning: CFTC CMX page (non-commercial net)
    - News RSS for IMF/Default/GeoPolitical scores
    Returns dict stored under data['macros']['metals']
    """
    import re
    import yfinance as yf

    out = EXISTING.get('macros', {}).get('metals', {}).copy()
    headers = {'User-Agent': UA}
    log('Fetching metals data...')

    # 1. Metal prices + DXY via Yahoo Finance
    yahoo_tickers = {
        'gold_px':      'GC=F',
        'silver_px':    'SI=F',
        'platinum_px':  'PL=F',
        'palladium_px': 'PA=F',
        'dxy':          'DX-Y.NYB',
    }
    for key, sym in yahoo_tickers.items():
        try:
            h = yf.Ticker(sym).history(period='6mo')
            if len(h) > 0:
                out[key] = round(float(h['Close'].iloc[-1]), 2)
                out[f'{key}_date'] = str(h.index[-1].date())
                for _tk,_tv in _series_trend([round(float(x),2) for x in h['Close'].values[-64:]], w=(5,21,63)).items():
                    out[f'{key}_{_tk}'] = _tv
                log(f'  ✓ {key} ({sym}): {out[key]}')
        except Exception as e:
            warn(f'{key} ({sym}) failed: {e}')
            lg = safe_get(EXISTING, 'macros', 'metals', key)
            if lg is not None:
                out[key] = lg

    if out.get('gold_px') and out.get('silver_px') and out['silver_px'] > 0:
        out['gs_ratio'] = round(out['gold_px'] / out['silver_px'], 1)
        log(f'  ✓ Gold:Silver ratio = {out["gs_ratio"]}')

    # 2. QE/QT — Fed balance sheet WALCL via FRED
    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            s = fred.get_series('WALCL').dropna()
            if len(s) >= 2:
                current = float(s.iloc[-1])
                prior   = float(s.iloc[-5]) if len(s) >= 5 else float(s.iloc[0])
                out['walcl']        = round(current / 1e6, 2)   # FRED WALCL is $millions -> store $trillions
                out['walcl_change'] = round((current - prior) / prior * 100, 2)
                out['walcl_date']   = str(s.index[-1].date())
                for _k, _v in _series_trend([float(x)/1e6 for x in s.values[-14:]]).items():
                    out['walcl_'+_k] = _v
                log(f'  ✓ WALCL: ${out["walcl"]}T ({out["walcl_change"]:+.2f}%)')
        except Exception as e:
            warn(f'WALCL FRED failed: {e}')
            for k in ('walcl', 'walcl_change', 'walcl_wow', 'walcl_mom', 'walcl_qoq'):
                lg = safe_get(EXISTING, 'macros', 'metals', k)
                if lg is not None:
                    out[k] = lg

    # 2b. WAVE M6 — true real yield (10y TIPS), 10y breakeven, Gold VIX via FRED (same proven Fred path)
    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            for key, sid in (('dfii10', 'DFII10'), ('breakeven_10y', 'T10YIE'), ('gvz', 'GVZCLS')):
                try:
                    s = fred.get_series(sid).dropna()
                    if len(s) > 0:
                        out[key] = round(float(s.iloc[-1]), 2)
                        out[f'{key}_date'] = str(s.index[-1].date())
                        for _tk,_tv in _series_trend([round(float(x),2) for x in s.values[-64:]], w=(5,21,63)).items():
                            out[f'{key}_{_tk}'] = _tv
                        log(f'  ✓ {key} ({sid}): {out[key]}')
                except Exception as e2:
                    warn(f'{key} ({sid}) FRED failed: {e2}')
                    lg = safe_get(EXISTING, 'macros', 'metals', key)
                    if lg is not None:
                        out[key] = lg
        except Exception as e:
            warn(f'M6 FRED block failed: {e}')

    # 3. COT positioning — CFTC CMX page
    try:
        r = requests.get('https://www.cftc.gov/dea/futures/deacmxsf.htm',
                         headers=headers, timeout=15)
        if r.status_code == 200:
            text = r.text
            dm = re.search(r'POSITIONS AS OF (\d{2}/\d{2}/\d{2})', text)
            if dm:
                out['cot_date'] = dm.group(1)

            def parse_cot_block(label_re):
                blk = re.search(label_re, text, re.S)
                if not blk:
                    return None, None, None
                chunk = text[blk.start(): blk.start() + 1500]
                oi_m = re.search(r'OPEN INTEREST:\s*([\d,]+)', chunk)
                oi = int(oi_m.group(1).replace(',', '')) if oi_m else None
                comm = re.search(r'COMMITMENTS\s*\n\s*([\d,]+)\s+([\d,]+)', chunk)
                if not comm:
                    return None, None, oi
                return int(comm.group(1).replace(',', '')), int(comm.group(2).replace(',', '')), oi

            for metal, pat, pfx in [
                ('gold',   r'GOLD - COMMODITY EXCHANGE INC\.',   'cot_gold'),
                ('silver', r'SILVER - COMMODITY EXCHANGE INC\.', 'cot_silver'),
                ('copper', r'COPPER- #1 - COMMODITY EXCHANGE INC\.', 'cot_copper'),
            ]:
                nc_l, nc_s, oi = parse_cot_block(pat)
                if nc_l is not None and oi:
                    out[f'{pfx}_net']  = nc_l - nc_s
                    out[f'{pfx}_oi']   = oi
                    out[f'{pfx}_pct']  = round((nc_l - nc_s) / oi * 100, 1)
                    # v1.11: keep the long/short legs so the dashboard can show longs vs shorts
                    out[f'{pfx}_long']      = nc_l
                    out[f'{pfx}_short']     = nc_s
                    out[f'{pfx}_long_pct']  = round(nc_l / oi * 100, 1)
                    out[f'{pfx}_short_pct'] = round(nc_s / oi * 100, 1)
                    log(f'  ✓ COT {metal}: long={nc_l:,} short={nc_s:,} net={out[f"{pfx}_net"]:,} ({out[f"{pfx}_pct"]}% OI)')
                    # WAVE M5/T1 — dedup-by-report-date {d,v} history (cap 160); percentile + WoW/MoM/QoQ trend
                    hist_key = f'{pfx}_hist'
                    hist = _push_hist(safe_get(EXISTING, 'macros', 'metals', hist_key),
                                      out.get('cot_date'), out[f'{pfx}_pct'], cap=160)
                    out[hist_key] = hist
                    _vals = [h['v'] for h in hist if isinstance(h, dict) and h.get('v') is not None]
                    if len(_vals) >= 20:
                        below = sum(1 for x in _vals if x <= out[f'{pfx}_pct'])
                        out[f'{pfx}_pctile'] = round(below / len(_vals) * 100)
                        log(f'    COT {metal} percentile: {out[f"{pfx}_pctile"]}th ({len(_vals)}wk history)')
                    _tr = _hist_trend(hist)
                    for _k, _v in _tr.items():
                        out[f'{pfx}_pct_{_k}'] = _v
                    if 'wow' in _tr:
                        log(f'    COT {metal} trend: WoW {_tr["wow"]:+} ({_tr.get("wow_dir")})'
                            + (f', MoM {_tr["mom"]:+}' if 'mom' in _tr else '')
                            + (f', QoQ {_tr["qoq"]:+}' if 'qoq' in _tr else ''))

    except Exception as e:
        warn(f'COT CFTC fetch failed: {e}')
        for k in ('cot_gold_net','cot_gold_oi','cot_gold_pct','cot_gold_long','cot_gold_short','cot_gold_long_pct','cot_gold_short_pct','cot_gold_hist','cot_gold_pctile',
                  'cot_silver_net','cot_silver_oi','cot_silver_pct','cot_silver_long','cot_silver_short','cot_silver_long_pct','cot_silver_short_pct','cot_silver_hist','cot_silver_pctile',
                  'cot_copper_net','cot_copper_oi','cot_copper_pct','cot_copper_long','cot_copper_short','cot_copper_long_pct','cot_copper_short_pct','cot_copper_hist','cot_copper_pctile','cot_gold_pct_wow','cot_gold_pct_mom','cot_gold_pct_qoq','cot_silver_pct_wow','cot_silver_pct_mom','cot_silver_pct_qoq','cot_copper_pct_wow','cot_copper_pct_mom','cot_copper_pct_qoq','cot_date'):
            lg = safe_get(EXISTING, 'macros', 'metals', k)
            if lg is not None:
                out[k] = lg

    # 4. News RSS — IMF Pakistan, Default risk, GeoPolitical
    try:
        import feedparser
        rss_targets = {
            'imf_score': (
                'https://news.google.com/rss/search?q=IMF+Pakistan&hl=en',
                ['disbursement','approved','agreement','on-track','success','review'],
                ['suspended','failed','exit','default','crisis','breach']),
            'default_score': (
                'https://news.google.com/rss/search?q=Pakistan+sovereign+default+risk&hl=en',
                ['falling','improved','stable','reduced','positive'],
                ['default','crisis','elevated','warning','risk','downgrade']),
            'geo_score': (
                'https://news.google.com/rss/search?q=gold+geopolitical+Middle+East+safe+haven&hl=en',
                ['conflict','tension','war','attack','safe haven','surge','unrest'],
                ['ceasefire','peace','calm','resolved','de-escalation']),
        }
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=14)
        for key, (url, pos_kw, neg_kw) in rss_targets.items():
            try:
                feed = feedparser.parse(url)
                pos = neg = 0
                for entry in feed.entries[:20]:
                    pub = dt.datetime(*entry.published_parsed[:6]) if hasattr(entry,'published_parsed') and entry.published_parsed else None
                    if pub and pub < cutoff:
                        continue
                    txt = (entry.get('title','') + ' ' + entry.get('summary','')).lower()
                    pos += sum(1 for kw in pos_kw if kw.lower() in txt)
                    neg += sum(1 for kw in neg_kw if kw.lower() in txt)
                if key == 'geo_score':
                    out[key] = +1 if pos > neg else (0 if pos == neg else -1)
                else:
                    out[key] = -1 if pos > neg else (0 if pos == neg else +1)
                log(f'  ✓ {key}: {out[key]:+d} (pos={pos} neg={neg})')
            except Exception as e:
                warn(f'{key} RSS failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'metals', key)
                if lg is not None:
                    out[key] = lg
    except ImportError:
        warn('feedparser not available; using last-good news scores')
        for k in ('imf_score', 'default_score', 'geo_score'):
            lg = safe_get(EXISTING, 'macros', 'metals', k)
            if lg is not None:
                out[k] = lg

    log(f'  Metals complete: {len([k for k in out if not k.endswith(("_date","_source"))])} fields')
    return out


# =============================================================
# 3. US UNIVERSE
# =============================================================
_LARGE_CAP_CACHE = None
def us_large_cap_set():
    """Decision 5: fixed S&P-200 large-caps (all 11 GICS) + holdings + thematic names,
    merged into the small-cap universe so the screen also covers large-cap sectors."""
    global _LARGE_CAP_CACHE
    if _LARGE_CAP_CACHE is None:
        s = set()
        for _tk in ZACKS_SECTOR_UNIVERSE.values():
            s.update(_tk)
        s.update(['XOM','CVX','COP','EOG','GOOGL','MSFT','META','UNH','GIS','KO',
                  'NVDA','TSM','ANET','MU','WDC','STX','DELL','AMD','LLY','AVGO'])
        _LARGE_CAP_CACHE = s
    return _LARGE_CAP_CACHE


def fetch_us_universe():
    log('Fetching US universe (NASDAQ-sourced top tickers)...')
    url = 'https://raw.githubusercontent.com/Ate329/top-us-stock-tickers/main/tickers/all.csv'
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=30)
        if r.status_code == 200:
            tickers = []
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                sym = (row.get('symbol') or '').strip().upper()
                mc = row.get('marketCap', '').strip()
                try:
                    mc_val = float(mc) if mc else 0
                except ValueError:
                    mc_val = 0
                if sym and sym.replace('.','').replace('-','').isalnum() and len(sym) <= 5:
                    if US_SMALL_CAP_MIN <= mc_val <= US_SMALL_CAP_MAX:
                        tickers.append(sym)
            large = us_large_cap_set()
            _scset = set(tickers)
            merged = tickers + [t for t in large if t not in _scset]
            log(f'  Got {len(tickers)} small-cap + {len(merged)-len(tickers)} large-cap = {len(merged)} merged US tickers (Decision 5)')
            if len(merged) > 0:
                return merged
    except Exception as e:
        warn(f'Primary US universe failed: {e}')

    try:
        url2 = 'https://raw.githubusercontent.com/Ate329/top-us-stock-tickers/main/tickers/sp500.csv'
        r = requests.get(url2, headers={'User-Agent': UA}, timeout=30)
        if r.status_code == 200:
            tickers = []
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                sym = (row.get('symbol') or '').strip().upper()
                if sym:
                    tickers.append(sym)
            if len(tickers) > 0:
                warn(f'US universe fell back to S&P 500 ({len(tickers)} tickers)')
                return tickers
    except Exception as e:
        warn(f'US universe fallback 1 failed: {e}')

    warn('US universe using hardcoded watchlist (final fallback)')
    return ['NVDA','META','TSM','AAPL','MSFT','GOOGL','AMZN',
            'PLPC','MGNI','SG','TOI','INMD','TRS','ADV','PKBK',
            'AXON','ENPH','MELI','PLTR','VRT','AVGO']


US_MAIN_EXCH = {'NASDAQ', 'NYSE', 'AMEX', 'NYSE ARCA', 'BATS', 'NYSE MKT', 'NYSEARCA'}
_US_TV_COLS = ['name', 'market_cap_basic', 'exchange', 'sector',
               'total_revenue_yoy_growth_fq', 'total_revenue_yoy_growth_ttm',
               # Wave D1 instrumentation: EPS-YoY-growth so the financial bucket
               # (which bypasses the revenue gate) can be measured for a future
               # bank-appropriate TV gate. Read for diagnostics only — gating unchanged.
               'earnings_per_share_diluted_yoy_growth_fq',
               'earnings_per_share_diluted_yoy_growth_ttm',
               # Wave D1 step 2: ROE is the bank-appropriate quality gate (canonical
               # Sarmaaya framework: ROE is the lead stability factor). Instrumented this
               # run (distribution + coverage); becomes the primary financial gate once
               # TV coverage/units are confirmed on a live run.
               'return_on_equity']


def is_common_us_ticker(tk):
    """PURE. True only for plain common-share tickers. TradingView's america `type=stock`
    feed leaks preferred-share series whose symbol carries a '/<class>' suffix (ABR/PE,
    GNL/PD, TWO/PA, ...). Those 502 on Yahoo and inflate the financials bucket (one REIT =
    many preferred series), so they're dropped before the universe is built. Conservative:
    only '/' (and stray whitespace) is rejected — '.'/'-' class shares are left alone,
    matching the existing Yahoo-universe guard. Unit-tested."""
    if not tk or not isinstance(tk, str):
        return False
    return '/' not in tk and ' ' not in tk


def classify_us_tv_row(rec, thr):
    """PURE. Decide whether a TradingView america row should be sent to the Yahoo screen.
    Returns 'financial' | 'growth' | 'ttm' | 'skip'. (The named large-cap set is unioned
    in by the caller; this only judges band names.)
      - financial: TV cannot measure bank revenue growth -> pass straight to Yahoo (screened as today)
      - growth:    non-financial, quarterly YoY rev-growth (fq) >= threshold (matches Yahoo MRQ)
      - ttm:       non-financial, fq is NULL but TTM YoY >= threshold (fallback recovers NULL-fq names)
      - skip:      OTC/foreign exch, out of band, or non-financial failing growth (Yahoo would reject too)
    thr is the growth threshold in PERCENT (e.g. 15.0)."""
    if (rec.get('exchange') or '') not in US_MAIN_EXCH:
        return 'skip'
    mc = rec.get('market_cap_basic') or 0
    if not (US_SMALL_CAP_MIN <= mc <= US_SMALL_CAP_MAX):
        return 'skip'
    if 'Financ' in (rec.get('sector') or ''):
        # Wave D1 step 3 gate. Banks are screened on bank-appropriate metrics, not revenue
        # growth (meaningless for a spread/credit business; the revenue gate is bypassed for
        # financials in screen_us_stock). PRIMARY gate = ROE >= ROE_FIN_MIN (the canonical lead
        # quality metric, unit-normalised); SECONDARY = drop clearly-DETERIORATING banks (EPS
        # YoY < 0). A missing vendor field is never a reason to drop a bank (pass through).
        roe = _roe_pct(rec.get('return_on_equity'))
        if roe is not None and roe < ROE_FIN_MIN:
            return 'skip'
        fq  = rec.get('earnings_per_share_diluted_yoy_growth_fq')
        ttm = rec.get('earnings_per_share_diluted_yoy_growth_ttm')
        eps = fq if fq is not None else ttm
        if eps is not None and eps < 0:
            return 'skip'
        return 'financial'
    fq = rec.get('total_revenue_yoy_growth_fq')
    ttm = rec.get('total_revenue_yoy_growth_ttm')
    if fq is not None and fq >= thr:
        return 'growth'
    if fq is None and ttm is not None and ttm >= thr:
        return 'ttm'
    return 'skip'


def _fin_eps_diag(pairs):
    """PURE. Wave D1 instrumentation. Given (eps_fq, eps_ttm) YoY-growth pairs for the TV
    financial bucket, summarise the distribution so a future bank-appropriate gate threshold
    can be chosen from real data instead of a blind guess. 'effective' growth = fq when
    present else ttm. Returns a one-line diagnostic string. Changes NO gating. Unit-tested."""
    n = len(pairs)
    n_fq = sum(1 for fq, _ in pairs if fq is not None)
    n_ttm = sum(1 for _, ttm in pairs if ttm is not None)
    eff = [(fq if fq is not None else ttm) for fq, ttm in pairs
           if (fq if fq is not None else ttm) is not None]
    if not eff:
        return (f'[diag] financials EPS-growth: {n} financials, 0 with TV EPS data '
                f'(fq {n_fq}, ttm {n_ttm}) — TV exposes no EPS growth for this bucket')
    s = sorted(eff)
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    p = {t: sum(1 for v in eff if v >= t) for t in (0, 5, 10, 15)}
    return (f'[diag] financials EPS-growth: {n} financials, {len(eff)} with data '
            f'(fq {n_fq}, ttm {n_ttm}); min {s[0]:.1f}% median {median:.1f}% max {s[-1]:.1f}%; '
            f'pass >=0% {p[0]} | >=5% {p[5]} | >=10% {p[10]} | >=15% {p[15]}')


def _roe_pct(roe):
    """PURE. Normalise a TradingView ROE value to PERCENT. TV may return either a percent
    (e.g. 12.5) or a fraction (0.125); a bank ROE is ~5-25%, so |v|<=1.5 is treated as a
    fraction and scaled x100. Guards the gate against silently dropping every bank if TV
    returns fractions. Returns None for None."""
    if roe is None:
        return None
    return roe * 100 if abs(roe) <= 1.5 else roe


def _fin_roe_diag(values):
    """PURE. Wave D1 step 2 instrumentation. Given TV ROE values for the financial bucket,
    summarise the distribution and coverage so the ROE gate threshold (and unit handling)
    can be confirmed from real data before ROE becomes the primary gate. Unit-normalised
    via _roe_pct. Changes NO gating this run. Unit-tested."""
    n = len(values)
    pct = [_roe_pct(v) for v in values if v is not None]
    if not pct:
        return (f'[diag] financials ROE: {n} financials, 0 with TV ROE data '
                f'— no ROE gate applied (all pass through); EPS<0 gate still active')
    s = sorted(pct)
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    p = {t: sum(1 for v in pct if v >= t) for t in (8, 10, 12, 15, 20)}
    return (f'[diag] financials ROE: {n} financials, {len(pct)} with data; '
            f'min {s[0]:.1f}% median {median:.1f}% max {s[-1]:.1f}%; '
            f'pass >=8% {p[8]} | >=10% {p[10]} | >=12% {p[12]} | >=15% {p[15]} | >=20% {p[20]}')


def fetch_us_universe_tv():
    """v1.21.0 Phase 1 — pre-filter the US universe on the free TradingView america scanner
    so Yahoo only screens names that can plausibly survive. Validated 2026-06-05: the fq
    field reproduces 96% of non-financial Yahoo survivors; financials cannot be screened on
    TV revenue growth so they pass straight through to the Yahoo screen unchanged; the named
    large-cap set is always included. HARD fallback to the full Yahoo universe if TV is
    unreachable or returns nothing -> production can never break."""
    thr = US_REV_GROWTH_MIN * 100

    def _bare(s):
        return s.split(':')[-1]

    rows = []
    try:
        start, page, cap = 0, 500, 6000
        while start < cap:
            payload = {
                "columns": _US_TV_COLS,
                "filter": [
                    {"left": "type", "operation": "equal", "right": "stock"},
                    {"left": "market_cap_basic", "operation": "egreater", "right": US_SMALL_CAP_MIN},
                ],
                "sort": {"sortBy": "market_cap_basic", "sortOrder": "asc"},
                "range": [start, start + page], "markets": ["america"],
            }
            r = requests.post("https://scanner.tradingview.com/america/scan",
                              json=payload, headers={'User-Agent': UA}, timeout=40)
            if r.status_code != 200:
                warn(f'TV america prefilter HTTP {r.status_code}; falling back to Yahoo universe')
                rows = []
                break
            batch = r.json().get('data', [])
            stop = False
            for d in batch:
                rec = dict(zip(_US_TV_COLS, d['d']))
                rec['ticker'] = _bare(d['s'])
                if (rec.get('market_cap_basic') or 0) > US_SMALL_CAP_MAX:
                    stop = True   # ascending sort -> past the band ceiling, done
                    break
                if not is_common_us_ticker(rec['ticker']):
                    continue      # drop TV-leaked preferred-share series (ABR/PE, GNL/PD, ...) — they 502 on Yahoo
                rows.append(rec)
            if stop or len(batch) < page:
                break
            start += page
    except Exception as e:
        warn(f'TV america prefilter failed ({e}); falling back to Yahoo universe')
        rows = []

    if not rows:
        warn('TV prefilter empty -> using full Yahoo universe (no change vs prior behaviour)')
        return fetch_us_universe()

    large = us_large_cap_set()
    cands = set(large)   # named large-caps always reach the Yahoo screen (band bypass lives in screen_us_stock)
    buckets = {'financial': 0, 'growth': 0, 'ttm': 0}
    fin_eps_pairs = []   # D1: financial bucket EPS-growth (in-band financials, pre-gate)
    fin_roe_vals  = []   # D1 step 2: financial bucket ROE (for the ROE-gate decision)
    fin_dropped_roe = 0  # D1 step 3: financials the ROE>=ROE_FIN_MIN primary gate drops
    fin_dropped_eps = 0  # financials the EPS>=0 secondary gate drops (ROE-surviving only)
    for rec in rows:
        is_fin = ('Financ' in (rec.get('sector') or '')
                  and (rec.get('exchange') or '') in US_MAIN_EXCH
                  and US_SMALL_CAP_MIN <= (rec.get('market_cap_basic') or 0) <= US_SMALL_CAP_MAX)
        if is_fin:
            fq  = rec.get('earnings_per_share_diluted_yoy_growth_fq')
            ttm = rec.get('earnings_per_share_diluted_yoy_growth_ttm')
            fin_eps_pairs.append((fq, ttm))
            fin_roe_vals.append(rec.get('return_on_equity'))
            _roe = _roe_pct(rec.get('return_on_equity'))
            _eps = fq if fq is not None else ttm
            if _roe is not None and _roe < ROE_FIN_MIN:
                fin_dropped_roe += 1
            elif _eps is not None and _eps < 0:
                fin_dropped_eps += 1
        cls = classify_us_tv_row(rec, thr)
        if cls == 'skip':
            continue
        cands.add(rec['ticker'])
        buckets[cls] += 1
    out = sorted(cands)
    log(f'  TV prefilter: {len(rows)} band names scanned -> Yahoo screens {len(out)} '
        f'(large-cap {len(large)} + financials {buckets["financial"]} + '
        f'growth {buckets["growth"]} + ttm-fallback {buckets["ttm"]}); '
        f'replaces a ~{len(rows) + len(large)}-name full-universe Yahoo screen')
    log(f'  D1 bank gate: {len(fin_eps_pairs)} in-band financials -> dropped '
        f'{fin_dropped_roe} (ROE<{ROE_FIN_MIN:.0f}%) + {fin_dropped_eps} (EPS<0) '
        f'-> {buckets["financial"]} to Yahoo (revenue gate bypassed for financials)')
    log('  ' + _fin_eps_diag(fin_eps_pairs))
    log('  ' + _fin_roe_diag(fin_roe_vals))
    return out


def screen_us_stock(ticker, yf_module):
    """Screen one ticker via Yahoo info. Returns candidate dict or None."""
    try:
        t = yf_module.Ticker(ticker)
        info = t.info
        if not info or not isinstance(info, dict):
            return None
        market_cap = info.get('marketCap', 0) or 0
        if market_cap == 0:
            return None
        if ticker not in us_large_cap_set():
            if not (US_SMALL_CAP_MIN <= market_cap <= US_SMALL_CAP_MAX):
                return None  # small-cap path keeps the $300M-$2B band; large-cap set bypasses ceiling (Decision 5)
        sector = info.get('sector', 'Unknown') or 'Unknown'
        is_fin = 'Financ' in sector
        rev_growth = info.get('revenueGrowth')
        # D1 step 3: financials bypass the revenue-growth gate (revenue is meaningless for a
        # spread/credit business; they are gated on ROE>=ROE_FIN_MIN + EPS-YoY at the TV
        # prefilter). Non-financials still require revenueGrowth >= US_REV_GROWTH_MIN.
        if not is_fin:
            if rev_growth is None or rev_growth < US_REV_GROWTH_MIN:
                return None
        insider = info.get('heldPercentInsiders', 0) or 0
        if insider < 0.05:
            return None
        yf_rev = round(float(rev_growth) * 100, 1) if rev_growth is not None else None
        _eg = info.get('earningsGrowth')
        yf_eps = round(float(_eg) * 100, 1) if _eg is not None else None
        return {
            'ticker':       ticker,
            'name':         info.get('shortName') or info.get('longName') or ticker,
            'sector':       info.get('sector', 'Unknown'),
            'industry':     info.get('industry', ''),
            'market_cap':   market_cap,
            'market_cap_m': round(market_cap / 1e6, 0),
            'price':        info.get('currentPrice') or info.get('regularMarketPrice'),
            'rev_growth':   yf_rev,
            'eps_growth':   yf_eps,
            'growth_source':'yahoo',
            'roe':          round(float(info.get('returnOnEquity', 0) or 0) * 100, 1),
            'debt_equity':  round(float(info.get('debtToEquity', 0) or 0) / 100, 2),
            'pe':           info.get('trailingPE'),
            'forward_pe':   info.get('forwardPE'),
            'insider_pct':  round(float(insider) * 100, 1),
            'ocf_ni':       None,
        }
    except Exception:
        return None


def screen_us_universe():
    log('=== US screening ===')
    try:
        import yfinance as yf
    except ImportError:
        warn('yfinance not available for US screen')
        return {'funnel': EXISTING.get('us_funnel', []),
                'candidates': EXISTING.get('us_candidates', []),
                'all_survivors': EXISTING.get('us_candidates', [])}

    tickers = fetch_us_universe_tv()
    total = len(tickers)
    candidates = []

    log(f'  Screening {total} pre-filtered tickers via Yahoo Finance...')
    start = time.time()

    # Parallelized Yahoo screen (was ~16 min sequential). screen_us_stock is thread-safe
    # (each call builds its own yf.Ticker, no shared state). Tune US_SCAN_WORKERS down if
    # Yahoo rate-limits (watch the survived count). Validates on the live run.
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import random as _rand
    def _scan_one(tk):
        if US_SCAN_WORKERS > 1:
            time.sleep(_rand.uniform(0.2, 0.5))   # throttle only when parallel; workers=1 stays pure sequential
        try:
            return screen_us_stock(tk, yf)
        except Exception:
            return None
    done = 0
    ex = ThreadPoolExecutor(max_workers=US_SCAN_WORKERS)
    try:
        futures = [ex.submit(_scan_one, tk) for tk in tickers]
        for fut in as_completed(futures):
            done += 1
            result = fut.result()
            if result is not None:
                candidates.append(result)
            if done % 100 == 0:
                elapsed = time.time() - start
                rate = done / elapsed if elapsed > 0 else 0
                eta = (total - done) / rate / 60 if rate > 0 else 0
                log(f'  Progress: {done}/{total} ({done/total*100:.0f}%) — '
                    f'survived: {len(candidates)} — ETA: {eta:.1f}min')
            if time.time() - start > 2400:
                warn(f'US scan TIME CAP hit at {done}/{total}, stopping early')
                break
    finally:
        ex.shutdown(wait=False, cancel_futures=True)

    elapsed = time.time() - start
    log(f'  US scan: {elapsed/60:.1f}min, {len(candidates)} candidates passed all gates')

    survived = len(candidates)
    # Flag micro-base revenue-growth artifacts (near-zero prior-year revenue -> absurd %),
    # then rank with those artifacts demoted to the bottom so they can't seize a HIGH-CONVICTION
    # slot (UROY at 416,400% was doing exactly that). They still pass the screen and appear,
    # just not mis-ranked at the top. Raw rev_growth is preserved for display.
    for c in candidates:
        rg = c.get('rev_growth')
        c['rev_growth_artifact'] = (rg is not None and rg > US_REV_GROWTH_SANE_MAX)

    def _rank_key(c):
        rg = c.get('rev_growth', 0) or 0
        return -1e9 if c.get('rev_growth_artifact') else rg   # artifacts sort dead last
    candidates.sort(key=_rank_key, reverse=True)

    for i, c in enumerate(candidates):
        if i < 3:   c['status'] = 'HIGH-CONVICTION'
        elif i < 8: c['status'] = 'STRONG'
        else:       c['status'] = 'WATCH'

    # ---------------------------------------------------------------
    # FMP enrichment — on survivors ONLY (not 1259 raw tickers).
    # This is the v1.7.1 fix: calling fmp_growth() inside screen_us_stock
    # meant ~1259 FMP API calls per run, exhausting rate limits silently.
    # Here we call it on <=200 survivors after screening is complete.
    # ---------------------------------------------------------------
    # EPS enrichment — for survivors where Yahoo info.earningsGrowth is None,
    # fetch the actual annual income statement via yfinance and compute EPS growth.
    # Uses the same Yahoo connection already working in the scanner.
    eps_hits = 0
    eps_missing = [c for c in candidates[:US_EXPLOSIVE_POOL] if c.get('eps_growth') is None]
    if eps_missing:
        log(f'  Fetching income_stmt EPS for {len(eps_missing)} survivors missing earningsGrowth...')
        # The parallel screen can poison Yahoo's shared crumb, making every income_stmt call
        # fail (0/N). Recover: cooldown to let the throttle decay, then a fresh session + one
        # retry per ticker. (No-op cost when the screen was sequential.)
        if US_SCAN_WORKERS > 1:
            time.sleep(20)
        try:
            import requests as _rq
            _sess = _rq.Session(); _sess.headers.update({'User-Agent': UA})
        except Exception:
            _sess = None
        for c in eps_missing:
            for _att in range(2):
                try:
                    tk = yf.Ticker(c['ticker'], session=_sess) if _sess is not None else yf.Ticker(c['ticker'])
                    stmt = tk.income_stmt
                    if stmt is not None and not stmt.empty and stmt.shape[1] >= 2:
                        for label in ['Diluted EPS', 'Basic EPS']:
                            if label in stmt.index:
                                row = stmt.loc[label].dropna()
                                if len(row) >= 2:
                                    curr, prev = float(row.iloc[0]), float(row.iloc[1])
                                    if prev != 0:
                                        c['eps_growth'] = round((curr - prev) / abs(prev) * 100, 1)
                                        c['growth_source'] = 'yf_stmt'
                                        eps_hits += 1
                                break
                        break   # got a statement (with or without EPS row) — don't retry
                except Exception:
                    time.sleep(3)   # backoff, then one retry
            time.sleep(YF_DELAY)
        log(f'  EPS enriched {eps_hits}/{len(eps_missing)} previously-None survivors')
    else:
        log('  All survivors already have EPS growth from Yahoo info')

    funnel = [
        ['NYSE + NASDAQ + AMEX Listed Equities', 5800,
         'Total US-listed common stocks'],
        ['Active US universe (NASDAQ-sourced)', total + 4500,
         'After ETFs/funds removed'],
        ['Small-cap zone ($300M-$2bn) PRE-FILTERED', total,
         'Market cap filter at source'],
        ['+ Revenue Growth >15% YoY', survived,
         'Yahoo revenueGrowth + insider gate'],
        ['+ Insider Holding >5%', survived,
         'Sponsor/insider commitment'],
        [f'+ Top {US_CANDIDATE_POOL} to TCE', min(US_CANDIDATE_POOL, survived),
         f'Live scan: {dt.date.today()}'],
    ]

    return {'funnel': funnel,
            'candidates': candidates[:US_CANDIDATE_POOL],
            'all_survivors': candidates[:US_EXPLOSIVE_POOL]}


# =============================================================
# 4. PSX
# =============================================================
def fetch_psx_universe():
    log('Fetching PSX universe...')
    test_url = 'https://dps.psx.com.pk/timeseries/eod/MUGHAL'
    try:
        r = requests.get(test_url, headers={
            'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
        log(f'  {"✓ PSX endpoint reachable" if r.status_code==200 else f"· PSX endpoint returned {r.status_code}"}')
    except Exception as e:
        log(f'  · PSX endpoint test: {e}')

    # F5: real candidate universe from the TradingView Pakistan scanner (the one reliable free PSX
    # path; same source the Apps Script bot uses). Falls back to the curated list on any failure so
    # PSX TCE never goes empty.
    try:
        live = fetch_psx_universe_live()
        if len(live) >= 8:
            log(f'  ✓ PSX universe: {len(live)} candidates from TradingView Pakistan scanner')
            return live
        log(f'  · TV scan returned {len(live)} (<8) — using fallback watchlist')
    except Exception as e:
        log(f'  · TV scan failed ({e}) — using fallback watchlist')
    return _PSX_FALLBACK


# Curated fallback only (used if the live scan fails). (ticker, name, sector, rev_growth, eps_growth)
_PSX_FALLBACK = [
    ('MUGHAL', 'Mughal Iron & Steel',         'Steel',     18.2,  32.5),
    ('ECOP',   'EcoPack Limited',             'Packaging', 22.1,  28.3),
    ('PIBTL',  'Pakistan Intl Bulk Terminal', 'Transport', 15.8,  12.1),
    ('GHGL',   'Ghani Glass',                 'Glass',     19.4,  22.7),
    ('PABC',   'Pak Alum Beverage Cans',      'Packaging', 24.6,  31.2),
    ('ACPL',   'Attock Cement',               'Cement',    11.2,   8.4),
    ('SAZEW',  'Sazgar Engineering',          'Auto',      35.8,  48.2),
    ('NCPL',   'Nishat Chunian Power',        'Utilities',  9.1,  14.3),
    ('SYM',    'Symmetry Group',              'IT',        42.3,  55.1),
    ('IML',    'Ismail Industries',           'Food',      16.7,  21.4),
]

# --- F5 live universe via TradingView Pakistan scanner (pure parse/derive + thin network wrapper) ---
PSX_SCAN_COLS = ['name', 'close', 'volume', 'market_cap_basic', 'Perf.3M', 'sector',
                 'total_revenue_yoy_growth_ttm', 'earnings_per_share_diluted_yoy_growth_ttm']
PSX_MCAP_MIN  = 3e9     # exclude micro-caps (PKR)
PSX_MCAP_MAX  = 60e9    # exclude KSE-30 mega-caps; keep the small/mid "sweet spot"
PSX_TOP_N     = 25


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_tv_scan(payload, columns):
    """TradingView scanner JSON -> list of row dicts keyed by column. Symbol 'PSX:OGDC' -> 'OGDC'.
    Maps defensively: if the response has fewer values than requested columns (e.g. a column TV
    couldn't compute), the missing ones become None rather than dropping the row. Pure + unit-tested."""
    rows = []
    for item in ((payload or {}).get('data') or []):
        sym = item.get('s', '') if isinstance(item, dict) else ''
        ticker = sym.split(':')[-1] if ':' in sym else sym
        d = item.get('d') or [] if isinstance(item, dict) else []
        if not ticker or len(d) < 4:        # need at least the core price/volume/mcap fields
            continue
        rec = {'ticker': ticker}
        for i, c in enumerate(columns):
            rec[c] = d[i] if i < len(d) else None
        rows.append(rec)
    return rows


def derive_psx_candidates(rows, mcap_min=PSX_MCAP_MIN, mcap_max=PSX_MCAP_MAX, top_n=PSX_TOP_N):
    """Filter to the sweet-spot market-cap band with real liquidity, rank by traded value scaled by
    positive 3-month momentum, return top_n as (ticker, name, sector, rev_growth_pct, eps_growth_pct,
    perf_3m_pct). perf_3m is the 3-month performance % carried for the s6 momentum fallback."""
    scored = []
    for r in rows:
        mc = _f(r.get('market_cap_basic')); px = _f(r.get('close')); vol = _f(r.get('volume'))
        if mc is None or px is None or vol is None:
            continue
        if not (mcap_min <= mc <= mcap_max) or px <= 0 or vol <= 0:
            continue
        chg3m = _f(r.get('Perf.3M')) or 0.0
        score = (px * vol) * (1 + max(chg3m, 0) / 100.0)
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    return [(r['ticker'], r.get('name') or r['ticker'], r.get('sector') or '',
             _f(r.get('total_revenue_yoy_growth_ttm')),
             _f(r.get('earnings_per_share_diluted_yoy_growth_ttm')),
             _f(r.get('Perf.3M')))
            for _, r in scored[:top_n]]


def fetch_psx_universe_live(top_n=PSX_TOP_N):
    body = {'columns': PSX_SCAN_COLS, 'range': [0, 500],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'}, 'markets': ['pakistan']}
    r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                      headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f'TV scan HTTP {r.status_code}')
    return derive_psx_candidates(parse_tv_scan(r.json(), PSX_SCAN_COLS), top_n=top_n)


def screen_psx_stock(ticker_tuple):
    # Accepts (ticker, name, sector) or (...rev_growth, eps_growth) or (...rev_growth, eps_growth, perf_3m)
    ticker, name, sector = ticker_tuple[0], ticker_tuple[1], ticker_tuple[2]
    rev_growth = ticker_tuple[3] if len(ticker_tuple) > 3 else None
    eps_growth = ticker_tuple[4] if len(ticker_tuple) > 4 else None
    perf_3m    = ticker_tuple[5] if len(ticker_tuple) > 5 else None
    out = {'ticker': ticker, 'name': name, 'sector': sector,
           'price': None, 'avg_volume': None,
           'rev_growth': rev_growth, 'eps_growth': eps_growth, 'perf_3m': perf_3m,
           'growth_source': 'psx_annual' if rev_growth is not None else None,
           'data_source': 'cached', 'status': 'STRONG'}

    try:
        r = requests.get(f'https://dps.psx.com.pk/timeseries/eod/{ticker}',
                         headers={'User-Agent': UA, 'Accept': 'application/json'},
                         timeout=12)
        if r.status_code == 200:
            data = r.json()
            rows = data.get('data') if isinstance(data, dict) else data
            if isinstance(rows, list) and rows:
                last = rows[-1]
                if isinstance(last, (list, tuple)):
                    if len(last) >= 5:
                        out['price'] = float(last[4])
                        out['avg_volume'] = int(last[5]) if len(last) > 5 else None
                    elif len(last) >= 2:
                        out['price'] = float(last[1])
                        out['avg_volume'] = int(last[2]) if len(last) > 2 else None
                    if out['price'] is not None:
                        out['data_source'] = 'psx_eod'
    except Exception:
        pass

    if out['price'] is None:
        try:
            import yfinance as yf
            t = yf.Ticker(f'{ticker}.KA')
            h = t.history(period='1mo')
            if len(h) > 0:
                out['price'] = round(float(h['Close'].iloc[-1]), 2)
                out['avg_volume'] = int(h['Volume'].iloc[-5:].mean())
                out['data_source'] = 'yahoo:.KA'
        except Exception:
            pass

    return out


def screen_psx_universe():
    log('=== PSX screening ===')
    try:
        tickers = fetch_psx_universe()
        candidates = []
        for tup in tickers:
            try:
                result = screen_psx_stock(tup)
                if result:
                    candidates.append(result)
                    log(f'  ✓ {result["ticker"]}: price={result["price"]} '
                        f'({result["data_source"]})')
                time.sleep(YF_DELAY)
            except Exception:
                continue

        if len(candidates) >= 3:
            candidates[0]['status'] = 'HIGH-CONVICTION'
            candidates[1]['status'] = 'HIGH-CONVICTION'
            candidates[2]['status'] = 'HIGH-CONVICTION'
            for c in candidates[3:7]:
                c['status'] = 'STRONG'
            for c in candidates[7:]:
                c['status'] = 'WATCH'

        funnel = [
            ['PSX Total Listed Companies', 561, 'Source: PSX official listings'],
            ['Outside KSE-30 (excl. large caps)', 480, 'Removed KSE-30 large caps'],
            ['Sweet Spot Tier (PKR 5-30bn)', 150, 'Informal PSX small-cap zone'],
            ['+ Growth Filter (Fwd >20%)', 30, 'Forecast earnings growth ≥20%'],
            ['+ Moat OR Insider Gate', 18, 'Sponsor ≥40% + clear moat'],
            ['+ Multibagger Fit Assessment', len(candidates), 'Final candidates'],
        ]

        log(f'  PSX scan done: {len(candidates)} candidates')
        return {'funnel': funnel, 'candidates': candidates}
    except Exception as e:
        log(f'  PSX FAILED: {e}')
        traceback.print_exc()
        return {'funnel': EXISTING.get('psx_funnel', []),
                'candidates': EXISTING.get('psx_candidates', [])}


# =============================================================
# 5. TCE
# =============================================================
# --- Augmented TCE: old attention streams + fundamentals + forward revisions + RS guardrail ---
ATTENTION   = ('s1_news', 's2_sponsor', 's3_insider', 's5_volume')
FUNDAMENTAL = ('s6_momentum', 's7_margin', 's8_capital')
REVISION    = ('s9_eps_rev', 's10_rev_rev')
CONVICTION  = FUNDAMENTAL + REVISION            # streams that must converge for HIGH (the discriminators)
COUNTED     = ATTENTION + FUNDAMENTAL + REVISION
BINARY_STREAMS = COUNTED                        # back-compat alias

# Tuning (precision backtest, 2026-06-03): the price core is a real-but-modest trend-confirmer whose
# edge sharpens with a tighter momentum bar (lift 1.36x@15% -> 1.46x@20% -> 2.0x@30%). s6 raised
# 15 -> 22; and HIGH now requires conviction>=4 (the conv-3+attention path is dropped to WATCH).
TCE_MOM_THRESH     = 22      # s6 momentum %, 3mo
PRED_HORIZON_DAYS  = 90      # forward-validation maturation window
PRED_WINNER_THRESH = 40.0    # forward return % that counts a logged pick a "winner"


def derive_streams(info, closes, eps_up30, eps_down30, rev_est, spy_6mo_ret, prev_rev_est,
                   eps_growth_pct=None, rev_growth_pct=None, perf_3m=None):
    """Yahoo-derived stream flags from already-fetched primitives. Any input may be None; a stream
    that can't be computed simply stays 0 (never errors, never vetoes). eps_growth_pct/rev_growth_pct
    are an optional percent-units fallback for s7 when Yahoo .info lacks growth (PSX, where yfinance
    has no fundamentals). perf_3m is the TradingView 3-month performance %, used as the s6 momentum
    fallback when there's no .KA price history (PSX names yfinance can't serve). Pure + unit-tested."""
    s = {}
    if closes:
        s['price'] = round(closes[-1], 4)                                    # entry price for forward-validation
    if closes and len(closes) >= 64 and closes[-64]:                         # s6 momentum (3mo)
        mom = (closes[-1] - closes[-64]) / closes[-64] * 100
        s['s6_momentum_pct'] = round(mom, 1)
        s['s6_momentum'] = 1 if mom >= TCE_MOM_THRESH else 0
    elif perf_3m is not None:                                                # s6 fallback: TV 3-month perf
        s['s6_momentum_pct'] = round(perf_3m, 1)
        s['s6_momentum'] = 1 if perf_3m >= TCE_MOM_THRESH else 0
        s['s6_momentum_src'] = 'tv_perf3m'
    if closes and len(closes) >= 2 and closes[0]:                            # RS guardrail (6mo vs SPY)
        name_6mo = (closes[-1] - closes[0]) / closes[0] * 100
        s['rs_vs_spy'] = round(name_6mo - spy_6mo_ret, 1) if spy_6mo_ret is not None else None
        s['rs_ok'] = (spy_6mo_ret is None) or (name_6mo >= spy_6mo_ret)
    else:
        s['rs_ok'] = True
    eg = info.get('earningsGrowth') if info else None                        # s7 margin inflection
    rg = info.get('revenueGrowth') if info else None
    if eg is not None and rg is not None:
        s['s7_margin_spread_pct'] = round((eg - rg) * 100, 1)
        s['s7_margin'] = 1 if (eg > rg and eg > 0) else 0
    elif eps_growth_pct is not None and rev_growth_pct is not None:           # PSX fallback (percent units)
        s['s7_margin_spread_pct'] = round(eps_growth_pct - rev_growth_pct, 1)
        s['s7_margin'] = 1 if (eps_growth_pct > rev_growth_pct and eps_growth_pct > 0) else 0
    sp = info.get('shortPercentOfFloat') if info else None                   # s8 external capital
    if sp is not None:
        s['s8_capital_short_pct'] = round(sp * 100, 1)
        s['s8_capital'] = 1 if sp >= 0.08 else 0
    if eps_up30 is not None and eps_down30 is not None:                       # s9 EPS revision direction
        s['s9_eps_rev_net'] = eps_up30 - eps_down30
        s['s9_eps_rev'] = 1 if (eps_up30 > eps_down30 and eps_up30 > 0) else 0
    if rev_est is not None:                                                  # s10 revenue revision (snapshot)
        s['rev_est'] = rev_est
        if prev_rev_est:
            s['s10_rev_rev_pct'] = round((rev_est - prev_rev_est) / prev_rev_est * 100, 2)
            s['s10_rev_rev'] = 1 if rev_est > prev_rev_est else 0
    return s


def tce_tier(streams, market='us'):
    """Conviction (fundamentals+revisions) carries the tier. HIGH requires conviction>=4 (backtest:
    the conv-3+attention path didn't earn its keep — it now tops out at WATCH). A name converging on
    fundamentals BEFORE news/volume — the 3-quarters-early setup — still reaches HIGH on conviction
    alone; pure attention can only ever reach WATCH. RS guardrail caps a market-laggard to WATCH.

    PSX uses a market-specific bar: PSX can structurally fire only 5 of 9 streams (no Pakistani feed
    for s3 insider, s8 short-interest, s9/s10 revisions), so conviction caps at ~2. The US bar is
    therefore unreachable. PSX: HIGH = conv>=2 AND total>=5; WATCH = conv>=2 OR total>=4."""
    total = sum(int(streams.get(k, 0)) for k in COUNTED)
    conv  = sum(int(streams.get(k, 0)) for k in CONVICTION)
    rs_ok = bool(streams.get('rs_ok', True))
    if market == 'psx':
        if conv >= 2 and total >= 5:
            return 'HIGH', total, conv
        if conv >= 2 or total >= 4:
            return 'WATCH', total, conv
        return 'IGNORE', total, conv
    strong = (conv >= 4)
    if strong and rs_ok:
        return 'HIGH', total, conv
    if (conv >= 3) or (total >= 5 and conv >= 1) or (strong and not rs_ok):
        return 'WATCH', total, conv
    return 'IGNORE', total, conv


def _spy_6mo_return():
    try:
        import yfinance as yf
        h = yf.Ticker('SPY').history(period='6mo')
        if len(h) >= 2:
            c = h['Close']
            return round((c.iloc[-1] - c.iloc[0]) / c.iloc[0] * 100, 1)
    except Exception:
        pass
    return None


def _pred_days(d0, d1):
    try:
        return (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)).days
    except Exception:
        return 0


def update_tce_predictions(prev, today_iso, rows,
                           horizon_days=PRED_HORIZON_DAYS, winner_thresh=PRED_WINNER_THRESH):
    """Forward-validation ledger (the automated replacement for the impossible historical revision
    backtest). Logs each run's HIGH/WATCH picks with entry price, then on every later run marks the
    latest forward return and freezes it once the pick matures (>= horizon). Summarises per-tier
    hit-rate / avg forward / avg peak over matured picks. Pure + unit-tested (no I/O, no clock —
    `today_iso` and `rows` are passed in, so date math is deterministic).
      prev: prior {'predictions':[...]} dict (or None)
      rows: this run's picks as [{'ticker','tier','market','price'}] (price required)"""
    prev = prev or {}
    preds = [dict(p) for p in prev.get('predictions', [])]
    price = {r['ticker']: r['price'] for r in rows if r.get('price')}
    open_tickers = set()
    for p in preds:                                            # update + freeze at maturity
        d = _pred_days(p.get('date', ''), today_iso)
        p['days_open'] = d
        cur = price.get(p['ticker'])
        if cur and p.get('entry') and not p.get('resolved'):
            ret = round((cur - p['entry']) / p['entry'] * 100, 1)
            p['last_price'] = round(cur, 4); p['last_date'] = today_iso
            p['fwd_ret_pct'] = ret
            p['peak_ret_pct'] = round(max(p.get('peak_ret_pct', ret), ret), 1)
        if d >= horizon_days and not p.get('resolved'):
            p['resolved'] = True
        if d < horizon_days:
            open_tickers.add(p['ticker'])
    for r in rows:                                             # log new picks not already open
        tk = r['ticker']; cur = price.get(tk)
        if cur and tk not in open_tickers:
            preds.append({'ticker': tk, 'tier': r.get('tier'), 'market': r.get('market', 'us'),
                          'date': today_iso, 'entry': round(cur, 4), 'last_price': round(cur, 4),
                          'last_date': today_iso, 'fwd_ret_pct': 0.0, 'peak_ret_pct': 0.0,
                          'days_open': 0, 'resolved': False})
            open_tickers.add(tk)
    summary = {'horizon_days': horizon_days, 'winner_thresh': winner_thresh,
               'total_logged': len(preds),
               'open': sum(1 for p in preds if p.get('days_open', 0) < horizon_days)}
    for tier in ('HIGH', 'WATCH'):
        matured = [p for p in preds if p.get('tier') == tier and p.get('days_open', 0) >= horizon_days]
        n = len(matured)
        if n:
            hits = sum(1 for p in matured if p.get('fwd_ret_pct', 0) >= winner_thresh)
            summary[tier] = {'matured': n, 'hit_rate': round(hits / n, 3),
                             'avg_fwd_pct': round(sum(p.get('fwd_ret_pct', 0) for p in matured) / n, 1),
                             'avg_peak_pct': round(sum(p.get('peak_ret_pct', 0) for p in matured) / n, 1)}
        else:
            summary[tier] = {'matured': 0, 'hit_rate': None, 'avg_fwd_pct': None, 'avg_peak_pct': None}
    return {'predictions': preds, 'summary': summary, 'updated': today_iso}


def compute_tce_streams(ticker, market='us', spy_6mo_ret=None, prev_rev_est=None,
                        eps_growth_pct=None, rev_growth_pct=None, perf_3m=None):
    streams = {k: 0 for k in COUNTED}

    # s1_news / s2_sponsor — Google News RSS recent count (last 14 days)
    try:
        import feedparser
        url = (f'https://news.google.com/rss/search?q={ticker}+stock+OR+earnings'
               f'&hl=en-US&gl=US&ceid=US:en')
        feed = feedparser.parse(url)
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=14)
        recent = 0
        for entry in feed.entries[:30]:
            try:
                if getattr(entry, 'published_parsed', None) and dt.datetime(*entry.published_parsed[:6]) > cutoff:
                    recent += 1
            except Exception:
                continue
        streams['s1_news_count'] = recent
        if recent >= 3:
            streams['s1_news'] = 1
        if recent >= 8:
            streams['s2_sponsor'] = 1
    except Exception:
        pass

    # ONE yfinance fetch -> volume(s5) + momentum/RS(s6) + margin(s7) + capital(s8) + revisions(s9/s10)
    try:
        import yfinance as yf
        sym = f'{ticker}.KA' if market == 'psx' else ticker
        t = yf.Ticker(sym)
        h = t.history(period='6mo')
        try:
            info = t.info or {}
        except Exception:
            info = {}
        closes = [float(x) for x in h['Close'].tolist()] if len(h) else []

        if len(h) >= 60:                                            # s5_volume
            vr = h['Volume'].iloc[-20:].mean(); vb = h['Volume'].iloc[:40].mean()
            if vb > 0:
                ratio = vr / vb
                streams['s5_volume_ratio'] = round(ratio, 2)
                if ratio > 1.3:
                    streams['s5_volume'] = 1

        eps_up30 = eps_down30 = None                                # s9 forward EPS revision breadth
        try:
            er = t.get_eps_revisions() if hasattr(t, 'get_eps_revisions') else getattr(t, 'eps_revisions', None)
            if er is not None and hasattr(er, 'columns'):
                cols = {str(c).lower(): c for c in er.columns}
                up_c = next((cols[k] for k in cols if 'up' in k and '30' in k), None)
                dn_c = next((cols[k] for k in cols if 'down' in k and '30' in k), None)
                if up_c is not None and dn_c is not None:
                    eps_up30 = int(er[up_c].fillna(0).iloc[0]); eps_down30 = int(er[dn_c].fillna(0).iloc[0])
        except Exception:
            pass

        rev_est = None                                              # s10 consensus revenue estimate (snapshot)
        try:
            re_df = t.get_revenue_estimate() if hasattr(t, 'get_revenue_estimate') else getattr(t, 'revenue_estimate', None)
            if re_df is not None and hasattr(re_df, 'columns'):
                avg_c = next((c for c in re_df.columns if str(c).lower() in ('avg', 'average')), None)
                if avg_c is not None:
                    rev_est = float(re_df[avg_c].iloc[0])
        except Exception:
            pass

        streams.update(derive_streams(info, closes, eps_up30, eps_down30, rev_est, spy_6mo_ret, prev_rev_est,
                                       eps_growth_pct=eps_growth_pct, rev_growth_pct=rev_growth_pct,
                                       perf_3m=perf_3m))
    except Exception:
        streams.setdefault('rs_ok', True)

    # s3_insider — SEC Form 4 count (US only)
    if market == 'us':
        try:
            today = dt.date.today()
            start_dt = (today - dt.timedelta(days=90)).isoformat()
            url = (f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22'
                   f'&forms=4&dateRange=custom&startdt={start_dt}&enddt={today.isoformat()}')
            r = requests.get(url, headers={'User-Agent': 'Dashboard Scanner dashboard@example.com',
                                           'Accept': 'application/json'}, timeout=10)
            if r.status_code == 200:
                hits = safe_get(r.json(), 'hits', 'total', 'value', default=0)
                streams['s3_insider_count'] = hits
                if hits >= 2:
                    streams['s3_insider'] = 1
        except Exception:
            pass

    streams.setdefault('rs_ok', True)
    streams['total'] = sum(streams.get(k, 0) for k in COUNTED)
    return streams


def run_tce(candidates, market='us', max_count=20, spy_6mo_ret=None, prev_rev=None):
    log(f'=== TCE on {market.upper()} ({len(candidates)} candidates) ===')
    prev_rev = prev_rev or {}
    tce_results = []
    for c in candidates[:max_count]:
        ticker = c['ticker']
        try:
            # PSX has no yfinance fundamentals; feed the scanner's TTM growth so s7 can fire. US: None.
            _eg = c.get('eps_growth') if market == 'psx' else None
            _rg = c.get('rev_growth') if market == 'psx' else None
            _p3m = c.get('perf_3m') if market == 'psx' else None    # TV 3M perf -> s6 fallback when no .KA history
            streams = compute_tce_streams(ticker, market, spy_6mo_ret=spy_6mo_ret,
                                          prev_rev_est=prev_rev.get(ticker),
                                          eps_growth_pct=_eg, rev_growth_pct=_rg, perf_3m=_p3m)
            tier_label, total, conv = tce_tier(streams, market)
            tce_results.append({
                'ticker': ticker, 'name': c.get('name', ticker), 'sector': c.get('sector', ''),
                'src': c.get('src', 'screen'),
                'tce_score': total, 'conviction': conv, 'tier': tier_label, 'streams': streams,
            })
            fired = [k for k in COUNTED if streams.get(k) == 1]
            log(f'  {ticker}: {tier_label} total={total} conv={conv} streams={fired}')
            time.sleep(YF_DELAY)
        except Exception as e:
            log(f'  · TCE {ticker}: {e}')

    tce_results.sort(key=lambda r: (r['tce_score'], r.get('conviction', 0)), reverse=True)
    high  = sum(1 for r in tce_results if r['tier'] == 'HIGH')
    watch = sum(1 for r in tce_results if r['tier'] == 'WATCH')
    log(f'  TCE: {high} HIGH, {watch} WATCH out of {len(tce_results)} scanned')
    return tce_results


def merge_tce_pool(small_caps, etf_stocks, cap_small=US_CANDIDATE_POOL, cap_etf=ETF_TCE_N):
    """Build the US TCE pool: small-cap screen survivors PLUS the ETF-consensus large-caps (so quality
    names like MU/INTC are visible to the engine). Dedup by ticker (screen survivor wins). The ETF
    names are sourced from the prior run's overlap, which is fine because Zacks ETF ranks update
    quarterly, not daily. Pure + unit-tested."""
    seen, out = set(), []
    for c in (small_caps or [])[:cap_small]:
        tk = c.get('ticker')
        if tk and tk not in seen:
            seen.add(tk); d = dict(c); d.setdefault('src', 'screen'); out.append(d)
    for s in (etf_stocks or [])[:cap_etf]:
        tk = s.get('ticker')
        if tk and tk not in seen:
            seen.add(tk)
            out.append({'ticker': tk, 'name': tk, 'sector': '', 'src': 'etf',
                        'etf_conviction': s.get('conviction')})
    return out


# =============================================================
# 5b. EXPLOSIVE STAGE
# =============================================================
SIG_A_REV_MIN    = 15.0   # Revenue growth threshold for Signal A
SIG_A_OP_MIN     = 15.0   # Operating profit growth threshold for Signal A
SIG_B_OP_MIN     = 20.0   # OP growth threshold for Signal B
SIG_B_RATIO_MIN  = 1.5    # NP/OP growth ratio threshold for Signal B


def im3_score_from_stmt(income_stmt):
    """Compute IM3-correct Signal A/B from yfinance income_stmt DataFrame.
    Signal A: Rev growth >=15% AND Op growth >=15%
    Signal B: Op growth >20% AND (NP_growth/OP_growth) > 1.5
    Returns (sig_a, sig_b, rev_g, op_g, np_g, ratio) — all None on failure.
    """
    if income_stmt is None or income_stmt.empty or income_stmt.shape[1] < 2:
        return None, None, None, None, None, None

    def yoy(stmt, *labels):
        for label in labels:
            if label in stmt.index:
                row = stmt.loc[label].dropna()
                if len(row) >= 2:
                    curr, prev = float(row.iloc[0]), float(row.iloc[1])
                    if prev != 0:
                        return round((curr - prev) / abs(prev) * 100, 1)
        return None

    rev_g = yoy(income_stmt, 'Total Revenue', 'Revenue')
    op_g  = yoy(income_stmt, 'Operating Income', 'EBIT')
    np_g  = yoy(income_stmt, 'Net Income', 'Net Income Common Stockholders')

    sig_a = None if (rev_g is None or op_g is None) else bool(
        rev_g >= SIG_A_REV_MIN and op_g >= SIG_A_OP_MIN)

    if op_g is None or np_g is None:
        sig_b, ratio = None, None
    else:
        try:
            prev_op = float(income_stmt.loc['Operating Income'].dropna().iloc[1])
        except Exception:
            prev_op = 1  # assume positive if can't retrieve
        if prev_op <= 0:
            sig_b, ratio = None, None
        else:
            ratio = round(np_g / op_g, 2) if op_g != 0 else None
            sig_b = bool(op_g > SIG_B_OP_MIN and ratio is not None and ratio > SIG_B_RATIO_MIN)

    return sig_a, sig_b, rev_g, op_g, np_g, ratio


def score_explosive_candidate(c):
    """Score using pre-fetched growth fields (PSX path or fallback).
    US stocks use im3_score_from_stmt in run_explosive for IM3-correct scoring.
    """
    rev = c.get('rev_growth')
    eps = c.get('eps_growth')

    if rev is None or eps is None:
        sig_a = None
    else:
        sig_a = bool(rev >= SIG_A_REV_MIN and eps >= SIG_A_OP_MIN)

    if rev is None or eps is None:
        sig_b, ratio = None, None
    elif rev <= 0:
        sig_b, ratio = None, None
    else:
        ratio = round(eps / rev, 2)
        sig_b = bool(eps > SIG_B_OP_MIN and ratio > SIG_B_RATIO_MIN)

    if sig_a and sig_b:   verdict = 'EXPLOSIVE — both signals'
    elif sig_a:           verdict = 'QUALITY-GROWTH (Signal A only)'
    elif sig_b:           verdict = 'INFLECTION (Signal B only — verify quality)'
    elif sig_a is None or sig_b is None: verdict = 'INSUFFICIENT DATA'
    else:                 verdict = 'NOT EXPLOSIVE'

    return {
        'ticker':          c.get('ticker'),
        'name':            c.get('name', c.get('ticker')),
        'sector':          c.get('sector', ''),
        'rev_growth':      rev,
        'op_growth':       c.get('op_growth'),
        'np_growth':       c.get('np_growth'),
        'eps_growth':      eps,
        'op_np_ratio':     ratio,
        'signal_a':        sig_a,
        'signal_b':        sig_b,
        'verdict':         verdict,
        'cash_guardrails': 'na_confirm_im3',
        'growth_source':   c.get('growth_source', 'yahoo'),
        'fidelity':        'im3_screen',
    }


def run_explosive(candidates, market='us'):
    log(f'=== EXPLOSIVE screen on {market.upper()} '
        f'({len(candidates)} candidates) ===')

    # For US: fetch income_stmt to get Operating Profit and Net Profit
    # for IM3-correct Signal B scoring. PSX uses pre-embedded growth fields.
    if market == 'us':
        try:
            import yfinance as yf
        except ImportError:
            yf = None
    else:
        yf = None

    out = []
    for c in candidates:
        try:
            ticker = c.get('ticker')
            rec = None

            # US path: try IM3-correct income_stmt scoring first
            if market == 'us' and yf is not None:
                try:
                    stmt = yf.Ticker(ticker).income_stmt
                    sig_a, sig_b, rev_g, op_g, np_g, ratio = im3_score_from_stmt(stmt)
                    if sig_a is not None or sig_b is not None:
                        if sig_a and sig_b:   verdict = 'EXPLOSIVE — both signals'
                        elif sig_a:           verdict = 'QUALITY-GROWTH (Signal A only)'
                        elif sig_b:           verdict = 'INFLECTION (Signal B only — verify quality)'
                        elif sig_a is None or sig_b is None: verdict = 'INSUFFICIENT DATA'
                        else:                 verdict = 'NOT EXPLOSIVE'
                        rec = {
                            'ticker':          ticker,
                            'name':            c.get('name', ticker),
                            'sector':          c.get('sector', ''),
                            'rev_growth':      rev_g,
                            'op_growth':       op_g,
                            'np_growth':       np_g,
                            'eps_growth':      c.get('eps_growth'),
                            'op_np_ratio':     ratio,
                            'signal_a':        sig_a,
                            'signal_b':        sig_b,
                            'verdict':         verdict,
                            'cash_guardrails': 'na_confirm_im3',
                            'growth_source':   'yf_stmt_im3',
                            'fidelity':        'im3_screen',
                        }
                except Exception:
                    pass
                time.sleep(YF_DELAY)

            # Fallback: use pre-fetched rev/eps growth fields
            if rec is None:
                rec = score_explosive_candidate(c)

            # Bank/financial carve-out: OP/NP explosive conditions are invalid for
            # banks & financials (no operating-profit / CFO>NP semantics), so they
            # mechanically pass and flood the list. Flag them so they don't count as
            # EXPLOSIVE; score via IM3 System B (bank-adjusted) downstream instead.
            if rec is not None:
                _sec = (rec.get('sector') or '')
                rec['is_financial'] = _sec in ('Financial Services', 'Financials')
                if rec['is_financial'] and str(rec.get('verdict','')).startswith('EXPLOSIVE'):
                    rec['verdict'] = 'FINANCIAL — score via bank model (IM3 System B)'

            if rec:
                out.append(rec)
                log(f'  {rec["ticker"]}: A={rec["signal_a"]} '
                    f'B={rec["signal_b"]} -> {rec["verdict"]}')
        except Exception as e:
            log(f'  · explosive {c.get("ticker")}: {e}')

    out.sort(key=lambda r: (r.get('signal_a') is True and r.get('signal_b') is True,
                             r.get('signal_a') is True,
                             r.get('op_growth') or r.get('eps_growth') or -999), reverse=True)
    both = sum(1 for r in out if r['verdict'].startswith('EXPLOSIVE'))
    fin  = sum(1 for r in out if r.get('is_financial'))
    log(f'  EXPLOSIVE: {both} both-signal (non-financial) of {len(out)} scored; {fin} financials flagged for bank model')
    return out


# =============================================================
# 6. IM3 162-POINT SCORING ENGINE
# Replicates every formula from IM3_0 Scoring Template Excel.
# Two scoring paths:
#   score_im3_standard() — non-bank stocks (full 40 metrics)
#   score_im3_bank()     — bank/financial stocks (6 metrics replaced)
# Entry point: score_im3(ticker) → dict with score, grade, details
# =============================================================

# --- Weightage (max points per metric, from Weightage_Stocks_By_Ammar_Yaseen.xlsx)
IM3_WEIGHTS = {
    'rev_cagr':       5,  'op_cagr':        1,  'op_margin':      5,
    'np_cagr':        1,  'np_margin':       5,  'tax_rate':       3,
    'int_coverage':   2,  'de_ratio':        5,  'current_ratio':  5,
    'cfo_trend':      5,  'net_cash':        3,  'ccfo_cpat':      5,
    'eps_trend':      5,  'pe_ratio':        5,  'peg_ratio':      5,
    'pb_ratio':       3,  'ps_ratio':        3,  'div_yield':      5,
    'earn_yield':     3,  'graham_val':      3,  'ev_ebitda':      3,
    'roe':            3,  'mos':             5,  'val_shareholders':5,
    'inv_turn':       3,  'dro':             3,  'nfa_turn':       3,
    'fat':            3,  'fcf_trend':       5,  'croic':          5,
    'fcf_sale':       5,  'fcf_cfo':         3,  'ccc':            3,
    'altman_z':       5,  'beneish_m':       5,  'piotroski_f':   10,
    'roic_wacc':      3,  'total_debt':      3,  'cash_share':     5,
    'cash_debt':      5,
}
# Bank replacement weights. Canonical Sarmaaya "Financial Analysis of a Bank" (Week 6)
# framework + Banking_IG_Architecture: banks are scored ONLY on bank-applicable factors.
# Everything industrial is zeroed so it counts in neither score nor denominator.
IM3_BANK_WEIGHTS = {k: v for k, v in IM3_WEIGHTS.items()}
# Zero metrics that DO NOT apply to a leveraged spread/credit business:
#   - inventory/coverage/working-capital (industrial ops): int_coverage, current_ratio,
#     inv_turn, dro, fat, ccc, nfa_turn
#   - leverage ratios (a bank is leveraged 10-15x BY DESIGN): de_ratio, total_debt
#   - FCF/operating concepts banks don't report the industrial way: op_cagr, op_margin,
#     fcf_trend, croic, fcf_sale, fcf_cfo, cash_share, cash_debt
#   - industrial valuation (no EBITDA; P/S, PEG, Graham, IV-MoS not bank-appropriate —
#     canonical bank valuation is price-to-tangible-book): ev_ebitda, ps_ratio,
#     peg_ratio, graham_val, mos, val_shareholders
#   - quality models built for non-financials (the deck/architecture say so explicitly):
#     piotroski_f, altman_z, beneish_m, roic_wacc
_BANK_ZERO = ('int_coverage', 'current_ratio', 'inv_turn', 'dro', 'fat', 'ccc', 'nfa_turn',
              'de_ratio', 'total_debt',
              'op_cagr', 'op_margin', 'fcf_trend', 'croic', 'fcf_sale', 'fcf_cfo',
              'cash_share', 'cash_debt',
              'ev_ebitda', 'ps_ratio', 'peg_ratio', 'graham_val', 'mos', 'val_shareholders',
              'piotroski_f', 'altman_z', 'beneish_m', 'roic_wacc')
for _bk in _BANK_ZERO:
    IM3_BANK_WEIGHTS[_bk] = 0
# Bank-applicable kept from the industrial template (canonical mappings):
#   rev_cagr->Markup growth, np_cagr->Net Profit growth, np_margin->Net Margin,
#   tax_rate, eps_trend->EPS, cfo_trend->CFO, net_cash->Net Change in Cash,
#   ccfo_cpat->cCFO vs cPAT, roe->ROE, pe/pb/earn_yield/div_yield->valuation.
# Add bank-specific stability/business ratios:
IM3_BANK_WEIGHTS.update({
    'nim':   4,   # Net Interest Margin
    'casa':  3,   # CASA ratio
    'adr':   3,   # Advance-to-Deposit Ratio
    'npl':   5,   # Non-Performing Loans / Gross Loans
    'car':   4,   # Capital Adequacy Ratio
})
# Applicable bank max ~= 70 pts (51 retained industrial + 19 bank); the scorer computes
# the denominator from applicable, non-NA metrics so banks are no longer scored out of 162.

# Points conversion: GOOD=100%, WATCH=60%, BAD=20%, NA=0%
def _pts(verdict, max_pts):
    if verdict == 'GOOD':   return max_pts
    if verdict == 'WATCH':  return round(max_pts * 0.6)
    if verdict == 'BAD':    return round(max_pts * 0.2)
    return 0  # N/A or missing


def _safe_get(df, keys, yr=0):
    """Get a value from a multi-index yfinance dataframe safely."""
    if df is None or df.empty:
        return None
    for k in (keys if isinstance(keys, list) else [keys]):
        try:
            row = df.loc[df.index.str.lower() == k.lower()]
            if not row.empty:
                cols = row.columns.tolist()
                if yr < len(cols):
                    v = row.iloc[0, yr]
                    if v is not None and str(v) not in ('nan', 'None', ''):
                        import numpy as _np
                        return float(v) if not _np.isnan(float(v)) else None
        except Exception:
            pass
    return None


def _series(df, keys, n=6):
    """Get up to n annual values (TTM first) for a line item."""
    if df is None or df.empty:
        return []
    for k in (keys if isinstance(keys, list) else [keys]):
        try:
            row = df.loc[df.index.str.lower() == k.lower()]
            if not row.empty:
                vals = []
                for c in row.columns[:n]:
                    v = row.iloc[0][c]
                    try:
                        fv = float(v)
                        import numpy as _np
                        vals.append(fv if not _np.isnan(fv) else None)
                    except Exception:
                        vals.append(None)
                return vals
        except Exception:
            pass
    return []


def _avg(lst, n=None):
    """Average of first n non-None values."""
    vals = [v for v in (lst[:n] if n else lst) if v is not None]
    return sum(vals) / len(vals) if vals else None


def _cagr(series, yrs=5):
    """CAGR from series[0] (TTM) to series[yrs] over yrs years.
    IM3 formula: (E8/J8)^(1/5) - 1"""
    if len(series) <= yrs:
        return None
    start, end = series[yrs], series[0]
    if start is None or end is None or start <= 0 or end <= 0:
        return None
    return (end / start) ** (1 / yrs) - 1


def _dcf_fcf(fcf_per_share_series, price, disc_g=0.12, disc_t=0.04):
    """10-year DCF using FCF per share. Growth capped 5-20%.
    IM3: rows 138-145. Sarmaaya website formula replicated."""
    if not fcf_per_share_series or price is None:
        return None
    growth_rates = []
    for i in range(len(fcf_per_share_series) - 1):
        a, b = fcf_per_share_series[i], fcf_per_share_series[i + 1]
        if a is not None and b is not None and b != 0:
            growth_rates.append((a - b) / abs(b) * 100)
    if not growth_rates:
        return None
    avg_g = _avg(growth_rates)
    if avg_g is None:
        return None
    g = max(5.0, min(20.0, avg_g)) / 100
    base = fcf_per_share_series[0]
    if base is None:
        return None
    pv = sum(base * (1 + g) ** y / (1 + disc_g) ** y for y in range(1, 11))
    tv = base * (1 + g) ** 10 * (1 + disc_t) / ((disc_g - disc_t) * (1 + disc_g) ** 10)
    return pv + tv


def _dcf_eps(eps, avg_eps_growth_pct, bond_yield):
    """IM3 formula row 158: EPS*(8.5+2*MIN(MAX(g,0.03),0.25))*4.4/bond_yield"""
    if eps is None or bond_yield is None or bond_yield <= 0:
        return None
    g = max(0.03, min(0.25, (avg_eps_growth_pct or 5) / 100))
    return eps * (8.5 + 2 * g) * 4.4 / bond_yield


def _dcf_cash(cash_per_share_series, price, disc_g=0.12, disc_t=0.04):
    """Same structure as DCF FCF but using cash per share (rows 162-175)."""
    return _dcf_fcf(cash_per_share_series, price, disc_g, disc_t)


def _projected_fcf(avg_6yr_fcf, shares, equity, growth=0.09, price=None):
    """IM3 rows 179-191. Projected FCF = avg_6yr_fcf * (1+g) / shares"""
    if avg_6yr_fcf is None or shares is None or shares <= 0:
        return None
    return avg_6yr_fcf * (1 + growth) / shares


def _projected_cash(avg_6yr_cash, shares, equity, growth=0.09, price=None):
    """IM3 rows 179-193. Same as projected FCF using cash."""
    return _projected_fcf(avg_6yr_cash, shares, equity, growth, price)


def _peter_lynch(peg, avg_ebitda_growth_pct, eps):
    """IM3 row 203: PEG * MIN(MAX(EBITDA_g/100, 0.05), 0.20) * EPS"""
    if peg is None or eps is None:
        return None
    g = max(0.05, min(0.20, (avg_ebitda_growth_pct or 5) / 100))
    return peg * g * eps


def _altman_z(wc, re, ebit, equity, debt, ta):
    """Altman Z' for non-manufacturers:
    6.56*WC/TA + 3.26*RE/TA + 6.72*EBIT/TA + 1.05*Equity/Debt"""
    if any(v is None for v in [wc, re, ebit, equity, debt, ta]):
        return None
    if ta <= 0 or debt <= 0:
        return None
    return 6.56*(wc/ta) + 3.26*(re/re if False else re/ta) + 6.72*(ebit/ta) + 1.05*(equity/debt)


def _beneish_m(rev, rev_prev, ar, ar_prev, gp, gp_prev, ta, ta_prev,
               ppe, ppe_prev, sga, sga_prev, dep, dep_prev,
               ni, cfo, ltd, ltd_prev):
    """Beneish M-Score 8-variable model."""
    try:
        dsri = (ar / rev) / (ar_prev / rev_prev) if ar_prev and rev_prev else None
        gmi  = (gp_prev / rev_prev) / (gp / rev) if gp and rev else None
        aqi  = (1 - (ar + ppe) / ta) / (1 - (ar_prev + ppe_prev) / ta_prev) \
               if ta and ta_prev else None
        sgi  = rev / rev_prev if rev_prev else None
        depi = (dep_prev / (ppe_prev + dep_prev)) / (dep / (ppe + dep)) \
               if dep and ppe else None
        sgai = (sga / rev) / (sga_prev / rev_prev) if sga and sga_prev and rev_prev else None
        lvgi = ((ltd + (ta - ta)) / ta) / ((ltd_prev + (ta_prev - ta_prev)) / ta_prev) \
               if ta and ta_prev else None
        tata = (ni - cfo) / ta if ta else None
        vals = [dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata]
        coef = [-4.84, 0.920, 0.528, 0.404, 0.892, 0.115, 0.172, 4.679, -0.327]
        # Intercept + coefficients
        score = -4.84
        pairs = list(zip(coef[1:], vals))
        for c, v in pairs:
            if v is None:
                return None
            score += c * v
        return score
    except Exception:
        return None


def _piotroski_f(ni, cfo, roa, roa_prev, cfo_ta, delta_leverage,
                 delta_current_ratio, delta_shares, delta_gm, delta_turnover):
    """9 binary Piotroski checks. Returns 0-9."""
    score = 0
    # Profitability (4)
    if ni is not None and ni > 0: score += 1
    if cfo is not None and cfo > 0: score += 1
    if roa is not None and roa_prev is not None and roa > roa_prev: score += 1
    if cfo_ta is not None and roa is not None and cfo_ta > roa: score += 1
    # Leverage / Liquidity (3)
    if delta_leverage is not None and delta_leverage <= 0: score += 1
    if delta_current_ratio is not None and delta_current_ratio >= 0: score += 1
    if delta_shares is not None and delta_shares <= 0: score += 1
    # Operating efficiency (2)
    if delta_gm is not None and delta_gm >= 0: score += 1
    if delta_turnover is not None and delta_turnover >= 0: score += 1
    return score


def _roic(ebit, tax_rate, debt, equity, cash):
    """ROIC = NOPAT / Invested Capital"""
    if any(v is None for v in [ebit, tax_rate, debt, equity, cash]):
        return None
    nopat = ebit * (1 - tax_rate)
    ic = debt + equity - cash
    if ic <= 0:
        return None
    return nopat / ic


def _wacc_simple(beta, rf=0.043, erp=0.055, debt=0, equity=0, kd=0.06, tax=0.21):
    """Simple WACC. rf = 10Y Treasury (from FRED), erp = equity risk premium."""
    if beta is None:
        return None
    ke = rf + beta * erp
    v = debt + equity
    if v <= 0:
        return ke
    return (equity / v) * ke + (debt / v) * kd * (1 - tax)


def _mos(iv, price):
    """Margin of Safety = (IV - Price) / IV"""
    if iv is None or price is None or iv <= 0:
        return None
    return (iv - price) / iv


# --- BANK DETECTION ---
def _is_bank(info):
    """Detect bank/financial via yfinance info sector/industry."""
    sector   = (info.get('sector') or '').lower()
    industry = (info.get('industry') or '').lower()
    bank_keywords = ('bank', 'financial services', 'insurance', 'savings',
                     'thrift', 'credit', 'mortgage', 'diversified financial')
    non_bank_overrides = ('software', 'technology', 'biotech', 'pharma')
    if any(k in industry for k in non_bank_overrides):
        return False
    return any(k in sector or k in industry for k in bank_keywords)


# --- FETCH IM3 FINANCIALS ---
def _fetch_im3_data(ticker):
    """Fetch all data needed for 40-metric IM3 scoring from yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return None

    try:
        t = yf.Ticker(ticker)
        info    = t.info or {}
        inc     = t.income_stmt       # annual, TTM first
        bal     = t.balance_sheet     # annual
        cf      = t.cashflow          # annual

        # Normalise index to lowercase for _series/_safe_get
        for df in (inc, bal, cf):
            if df is not None and not df.empty:
                df.index = df.index.str.lower().str.strip()

        return {
            'info': info,
            'inc':  inc,
            'bal':  bal,
            'cf':   cf,
        }
    except Exception as e:
        log(f'  IM3 fetch error {ticker}: {e}')
        return None


# --- SCORE ONE METRIC ---
def _score_metric(key, verdict, weights):
    max_pts = weights.get(key, 0)
    pts = _pts(verdict, max_pts)
    return {'key': key, 'verdict': verdict, 'pts': pts, 'max': max_pts}


# --- STANDARD (NON-BANK) SCORING ---
def _score_standard(ticker, d, bond_yield=0.043):
    """
    Score all 40 IM3 metrics for a non-bank stock.
    Returns list of metric dicts and intrinsic value summary.
    """
    info = d['info']
    inc  = d['inc']
    bal  = d['bal']
    cf   = d['cf']
    W    = IM3_WEIGHTS

    price  = info.get('currentPrice') or info.get('regularMarketPrice')
    shares = info.get('sharesOutstanding')
    beta   = info.get('beta')

    metrics = []

    # ── GROWTH ───────────────────────────────────────────────
    rev  = _series(inc, ['total revenue', 'totalrevenue', 'revenue'])
    op   = _series(inc, ['operating income', 'ebit', 'operatingincome'])
    np_  = _series(inc, ['net income', 'netincome'])
    eps_ = _series(inc, ['diluted eps', 'basic eps', 'eps diluted', 'eps'])

    # Use info EPS history if income_stmt sparse
    if len([v for v in eps_ if v]) < 2:
        eps_ttm = info.get('trailingEps')
        if eps_ttm:
            eps_ = [eps_ttm] + eps_

    # Revenue CAGR ≥15% = GOOD
    rev_cagr = _cagr(rev, 5)
    v = 'GOOD' if rev_cagr is not None and rev_cagr >= 0.15 else \
        'WATCH' if rev_cagr is not None else 'NA'
    metrics.append(_score_metric('rev_cagr', v, W))

    # Operating Profit CAGR ≥15%
    op_cagr = _cagr(op, 5)
    v = 'GOOD' if op_cagr is not None and op_cagr >= 0.15 else \
        'WATCH' if op_cagr is not None else 'NA'
    metrics.append(_score_metric('op_cagr', v, W))

    # Operating Margin ≥12%
    op_margin = (op[0] / rev[0]) if op and rev and rev[0] else None
    v = 'GOOD' if op_margin is not None and op_margin >= 0.12 else \
        'WATCH' if op_margin is not None else 'NA'
    metrics.append(_score_metric('op_margin', v, W))

    # Net Profit CAGR ≥15%
    np_cagr = _cagr(np_, 5)
    v = 'GOOD' if np_cagr is not None and np_cagr >= 0.15 else \
        'WATCH' if np_cagr is not None else 'NA'
    metrics.append(_score_metric('np_cagr', v, W))

    # Net Margin ≥8%
    np_margin = (np_[0] / rev[0]) if np_ and rev and rev[0] else None
    v = 'GOOD' if np_margin is not None and np_margin >= 0.08 else \
        'WATCH' if np_margin is not None else 'NA'
    metrics.append(_score_metric('np_margin', v, W))

    # ── STABILITY ─────────────────────────────────────────────
    # Tax Rate ≥21% (at/near corp rate = GOOD; evasion/loss = WATCH)
    tax_exp  = _series(inc, ['tax provision', 'income tax expense',
                              'incometaxexpense', 'taxprovision'])
    pbt      = _series(inc, ['pretax income', 'income before tax',
                              'incomebeforetax', 'ebt'])
    tax_rate = (tax_exp[0] / pbt[0]) if tax_exp and pbt and pbt[0] else \
               info.get('effectiveTaxRate')
    v = 'GOOD' if tax_rate is not None and tax_rate >= 0.21 else \
        'WATCH' if tax_rate is not None else 'NA'
    metrics.append(_score_metric('tax_rate', v, W))

    # Interest Coverage >5
    int_exp  = _series(inc, ['interest expense', 'interestexpense'])
    int_exp0 = abs(int_exp[0]) if int_exp and int_exp[0] else None
    int_cov  = info.get('interestCoverage') or \
               ((op[0] / int_exp0) if op and int_exp0 else None)
    v = 'GOOD' if int_cov is not None and int_cov > 5 else \
        'WATCH' if int_cov is not None else 'NA'
    metrics.append(_score_metric('int_coverage', v, W))

    # D/E <0.5 GOOD, <1 WATCH, ≥1 BAD
    de = info.get('debtToEquity')
    if de is not None:
        de = de / 100 if de > 10 else de  # yfinance sometimes returns as percentage
    v = 'GOOD' if de is not None and de < 0.5 else \
        'WATCH' if de is not None and de < 1.0 else \
        'BAD'  if de is not None else 'NA'
    metrics.append(_score_metric('de_ratio', v, W))

    # Total Debt 3yr avg < 5yr avg = GOOD (debt declining)
    td_s = _series(bal, ['long term debt', 'total debt', 'longtermdebt', 'totaldebt'])
    td3  = _avg(td_s, 3)
    td5  = _avg(td_s, 5)
    v = 'GOOD' if td3 is not None and td5 is not None and td3 < td5 else \
        'WATCH' if td3 is not None else 'NA'
    metrics.append(_score_metric('total_debt', v, W))

    # Current Ratio ≥1.5 GOOD, ≥1 WATCH, <1 BAD
    cr = info.get('currentRatio')
    v = 'GOOD' if cr is not None and cr >= 1.5 else \
        'WATCH' if cr is not None and cr >= 1.0 else \
        'BAD'  if cr is not None else 'NA'
    metrics.append(_score_metric('current_ratio', v, W))

    # CFO 3yr avg > 5yr avg
    cfo_s = _series(cf, ['operating cash flow', 'cash from operations',
                          'operatingcashflow', 'cashfromoperations',
                          'total cash from operating activities'])
    cfo3  = _avg(cfo_s, 3)
    cfo5  = _avg(cfo_s, 5)
    v = 'GOOD' if cfo3 is not None and cfo5 is not None and cfo3 > cfo5 else \
        'WATCH' if cfo3 is not None else 'NA'
    metrics.append(_score_metric('cfo_trend', v, W))

    # Net Change in Cash: TTM > prior = GOOD, TTM > 0 = WATCH, <0 = BAD
    ncc_s = _series(cf, ['changes in cash', 'net change in cash',
                          'change in cash and cash equivalents',
                          'netchangeincash'])
    ncc0 = ncc_s[0] if ncc_s else None
    ncc1 = ncc_s[1] if len(ncc_s) > 1 else None
    v = 'GOOD' if ncc0 is not None and ncc1 is not None and ncc0 > ncc1 else \
        'WATCH' if ncc0 is not None and ncc0 > 0 else \
        'BAD'  if ncc0 is not None else 'NA'
    metrics.append(_score_metric('net_cash', v, W))

    # cCFO vs cPAT: sum 5yr CFO > sum 5yr Net Income
    cum_cfo = sum(v for v in cfo_s[:6] if v is not None)
    cum_np  = sum(v for v in np_[:6]   if v is not None)
    v = 'GOOD' if cum_cfo and cum_np and cum_cfo > cum_np else \
        'WATCH' if cum_cfo and cum_np else 'NA'
    metrics.append(_score_metric('ccfo_cpat', v, W))

    # NFAT (Net Fixed Asset Turnover) 3yr > 5yr
    ppe_s = _series(bal, ['net ppe', 'property plant equipment net',
                           'netppe', 'propertyplantequipmentnet',
                           'gross ppe', 'property plant and equipment'])
    rev_s = rev
    nfat_s = []
    for i in range(min(len(rev_s), len(ppe_s))):
        avg_ppe = ((ppe_s[i] + (ppe_s[i+1] if i+1 < len(ppe_s) else ppe_s[i])) / 2) \
                  if ppe_s[i] else None
        nfat_s.append((rev_s[i] / avg_ppe) if avg_ppe and rev_s[i] else None)
    nfat3 = _avg(nfat_s, 3)
    nfat5 = _avg(nfat_s, 5)
    v = 'GOOD' if nfat3 is not None and nfat5 is not None and nfat3 > nfat5 else \
        'WATCH' if nfat3 is not None else 'NA'
    metrics.append(_score_metric('nfa_turn', v, W))

    # ROE ≥20%
    roe = info.get('returnOnEquity')
    v = 'GOOD' if roe is not None and roe >= 0.20 else \
        'WATCH' if roe is not None else 'NA'
    metrics.append(_score_metric('roe', v, W))

    # ── EPS / VALUATION ───────────────────────────────────────
    # EPS: 3yr avg > 5yr avg
    eps_3 = _avg(eps_, 3)
    eps_5 = _avg(eps_, 5)
    v = 'GOOD' if eps_3 is not None and eps_5 is not None and eps_3 > eps_5 else \
        'WATCH' if eps_3 is not None else 'NA'
    metrics.append(_score_metric('eps_trend', v, W))

    # P/E vs peer: use sector average; without peer, check < 25 = GOOD (reasonable)
    pe = info.get('trailingPE') or info.get('forwardPE')
    peer_pe = info.get('forwardPE', 25)  # Fallback: compare to forward estimate
    v = 'GOOD'  if pe is not None and pe > 0 and pe <= peer_pe * 1.1 else \
        'WATCH' if pe is not None and pe > 0 and pe <= peer_pe * 1.3 else \
        'BAD'   if pe is not None and pe > 0 else 'NA'
    metrics.append(_score_metric('pe_ratio', v, W))

    # EBITDA Growth >15% (not a separate weightage row — feeds PEG context)
    ebitda_s = _series(inc, ['ebitda', 'normalized ebitda'])
    ebitda_g = ((ebitda_s[0] - ebitda_s[1]) / abs(ebitda_s[1]) * 100) \
               if len(ebitda_s) >= 2 and ebitda_s[1] else None
    avg_ebitda_g = None
    if len(ebitda_s) >= 5:
        gs = [(ebitda_s[i] - ebitda_s[i+1]) / abs(ebitda_s[i+1]) * 100
              for i in range(4) if ebitda_s[i] and ebitda_s[i+1]]
        avg_ebitda_g = _avg(gs) if gs else None

    # PEG <1 UNDERVALUED, ≤1.5 FAIR, >1.5 OVERVALUED
    peg = info.get('pegRatio') or info.get('trailingPegRatio')
    v = 'GOOD'  if peg is not None and peg < 1.0 else \
        'WATCH' if peg is not None and peg <= 1.5 else \
        'BAD'   if peg is not None else 'NA'
    metrics.append(_score_metric('peg_ratio', v, W))

    # Earnings Yield vs Bond Yield
    ey = (1 / pe) if pe and pe > 0 else None
    v = 'GOOD' if ey is not None and ey > bond_yield else \
        'BAD'  if ey is not None else 'NA'
    metrics.append(_score_metric('earn_yield', v, W))

    # P/B <1.5 UNDERVALUED, <3 FAIR, ≥3 OVERVALUED
    pb = info.get('priceToBook')
    v = 'GOOD'  if pb is not None and pb < 1.5 else \
        'WATCH' if pb is not None and pb < 3.0 else \
        'BAD'   if pb is not None else 'NA'
    metrics.append(_score_metric('pb_ratio', v, W))

    # Graham Value: P/E × P/B < 22.5
    graham_product = (pe * pb) if pe and pb else None
    v = 'GOOD' if graham_product is not None and graham_product < 22.5 else \
        'BAD'  if graham_product is not None else 'NA'
    metrics.append(_score_metric('graham_val', v, W))

    # P/S <1.5 UNDERVALUED, <3 FAIR, ≥3 OVERVALUED
    ps = info.get('priceToSalesTrailing12Months')
    v = 'GOOD'  if ps is not None and ps < 1.5 else \
        'WATCH' if ps is not None and ps < 3.0 else \
        'BAD'   if ps is not None else 'NA'
    metrics.append(_score_metric('ps_ratio', v, W))

    # Dividend Yield ≥4% GOOD (optional metric)
    dy = info.get('dividendYield')
    v = 'GOOD'  if dy is not None and dy >= 0.04 else \
        'WATCH' if dy is not None else 'NA'
    metrics.append(_score_metric('div_yield', v, W))

    # EV/EBITDA <10 UNDERVALUED, <15 FAIR, ≥15 OVERVALUED
    ev_eb = info.get('enterpriseToEbitda')
    v = 'GOOD'  if ev_eb is not None and ev_eb < 10 else \
        'WATCH' if ev_eb is not None and ev_eb < 15 else \
        'BAD'   if ev_eb is not None else 'NA'
    metrics.append(_score_metric('ev_ebitda', v, W))

    # ── MARGIN OF SAFETY (using DCF EPS — fully formulaic) ────
    eps_ttm = eps_[0] if eps_ else info.get('trailingEps')
    eps_growth_rates = []
    for i in range(min(4, len(eps_) - 1)):
        a, b = eps_[i], eps_[i+1]
        if a is not None and b is not None and b != 0:
            eps_growth_rates.append((a - b) / abs(b) * 100)
    avg_eps_g = _avg(eps_growth_rates) if eps_growth_rates else 5.0

    iv_dcf_eps = _dcf_eps(eps_ttm, avg_eps_g, bond_yield)
    mos_dcf_eps = _mos(iv_dcf_eps, price)

    # DCF FCF
    fcf_s  = _series(cf, ['free cash flow', 'freecashflow'])
    fcf_ps = [(f / shares) if f and shares else None for f in fcf_s]
    iv_dcf_fcf = _dcf_fcf(fcf_ps, price)
    mos_dcf_fcf = _mos(iv_dcf_fcf, price)

    # DCF Cash
    cash_s  = _series(bal, ['cash and cash equivalents', 'cash',
                             'cashandcashequivalents'])
    inv_s   = _series(bal, ['short term investments', 'investmentsandadvances',
                             'other short term investments'])
    total_cash_s = [(c or 0) + (i or 0) for c, i in
                    zip(cash_s + [0]*6, inv_s + [0]*6)][:6]
    cash_ps = [(c / shares) if c and shares else None for c in total_cash_s]
    iv_dcf_cash = _dcf_cash(cash_ps, price)
    mos_dcf_cash = _mos(iv_dcf_cash, price)

    # Projected FCF / Cash
    avg_fcf_6  = _avg(fcf_s, 6)
    avg_cash_6 = _avg(total_cash_s, 6)
    equity_val = _safe_get(bal, ['stockholders equity', 'total stockholders equity',
                                  'stockholdersequity'], 0)
    iv_proj_fcf  = _projected_fcf(avg_fcf_6, shares, equity_val)
    iv_proj_cash = _projected_cash(avg_cash_6, shares, equity_val)

    # Peter Lynch
    iv_peter_lynch = _peter_lynch(peg, avg_ebitda_g, eps_ttm)

    # Composite IV (average of available methods)
    iv_vals = [v for v in [iv_dcf_eps, iv_dcf_fcf, iv_dcf_cash,
                            iv_proj_fcf, iv_proj_cash, iv_peter_lynch]
               if v is not None and v > 0]
    iv_composite = _avg(iv_vals) if iv_vals else None
    mos_composite = _mos(iv_composite, price)

    # MoS scoring: SAFE ≥25%, SLIM 0–25%, OVERVALUED <0
    v = 'GOOD'  if mos_composite is not None and mos_composite >= 0.25 else \
        'WATCH' if mos_composite is not None and mos_composite >= 0 else \
        'BAD'   if mos_composite is not None else 'NA'
    metrics.append(_score_metric('mos', v, W))

    # Value for Shareholders: EPS 3yr avg > 5yr avg (same as eps_trend direction)
    v = 'GOOD'  if eps_3 is not None and eps_5 is not None and eps_3 > eps_5 else \
        'WATCH' if eps_3 is not None else 'NA'
    metrics.append(_score_metric('val_shareholders', v, W))

    # ── INVENTORY / WORKING CAPITAL ───────────────────────────
    inv_s2 = _series(bal, ['inventory', 'inventories'])
    ar_s   = _series(bal, ['accounts receivable', 'net receivables',
                            'accountsreceivable', 'netreceivables'])
    ap_s   = _series(bal, ['accounts payable', 'accountspayable'])
    cogs_s = _series(inc, ['cost of revenue', 'cost of goods sold',
                            'costofrevenue', 'cogs'])

    # Inventory Turnover: Revenue / Avg Inventory, 3yr > 5yr
    it_s = []
    for i in range(min(len(rev_s), len(inv_s2))):
        avg_inv = ((inv_s2[i] + (inv_s2[i+1] if i+1 < len(inv_s2) else inv_s2[i])) / 2) \
                  if inv_s2[i] else None
        it_s.append((rev_s[i] / avg_inv) if avg_inv and rev_s[i] else None)
    it3 = _avg(it_s, 3)
    it5 = _avg(it_s, 5)
    v = 'GOOD'  if it3 is not None and it5 is not None and it3 > it5 else \
        'WATCH' if it3 is not None else 'NA'
    metrics.append(_score_metric('inv_turn', v, W))

    # DRO: Receivables/Revenue*365, 3yr avg vs 5yr avg (lower = better)
    dro_s = [(ar_s[i] / rev_s[i] * 365) if ar_s and i < len(ar_s) and rev_s[i]
             else None for i in range(min(len(rev_s), 6))]
    dro3 = _avg(dro_s, 3)
    dro5 = _avg(dro_s, 5)
    # Lower DRO = better collection; 3yr < 5yr = improving
    v = 'GOOD'  if dro3 is not None and dro5 is not None and dro3 < dro5 else \
        'WATCH' if dro3 is not None else 'NA'
    metrics.append(_score_metric('dro', v, W))

    # Fixed Asset Turnover: Revenue / Avg PPE, 3yr > 5yr
    v = 'GOOD'  if nfat3 is not None and nfat5 is not None and nfat3 > nfat5 else \
        'WATCH' if nfat3 is not None else 'NA'
    metrics.append(_score_metric('fat', v, W))

    # CCC = DRO + DSI − DPO; 3yr avg vs 5yr avg (lower = better)
    dsi_s = [(inv_s2[i] / (cogs_s[i] if cogs_s and i < len(cogs_s) else rev_s[i]) * 365)
             if inv_s2 and i < len(inv_s2) and (cogs_s and i < len(cogs_s) or rev_s[i])
             else None for i in range(min(len(rev_s), 6))]
    dpo_s = [(ap_s[i] / (cogs_s[i] if cogs_s and i < len(cogs_s) else rev_s[i]) * 365)
             if ap_s and i < len(ap_s) else None for i in range(min(len(rev_s), 6))]
    ccc_s = [(dro_s[i] or 0) + (dsi_s[i] or 0) - (dpo_s[i] or 0)
             if dro_s and i < len(dro_s) else None for i in range(min(len(rev_s), 6))]
    ccc3 = _avg(ccc_s, 3)
    ccc5 = _avg(ccc_s, 5)
    v = 'GOOD'  if ccc3 is not None and ccc5 is not None and ccc3 < ccc5 else \
        'WATCH' if ccc3 is not None else 'NA'
    metrics.append(_score_metric('ccc', v, W))

    # ── CASHFLOW ──────────────────────────────────────────────
    # FCF 3yr > 5yr
    fcf3 = _avg(fcf_s, 3)
    fcf5 = _avg(fcf_s, 5)
    v = 'GOOD'  if fcf3 is not None and fcf5 is not None and fcf3 > fcf5 else \
        'WATCH' if fcf3 is not None else 'NA'
    metrics.append(_score_metric('fcf_trend', v, W))

    # CROIC: FCF / Invested Capital (TTM)
    td0    = td_s[0] if td_s else None
    eq0    = equity_val
    cash0  = total_cash_s[0] if total_cash_s else None
    mi_s   = _series(bal, ['minority interest', 'noncontrolling interest',
                             'minorityinterest'])
    mi0    = mi_s[0] if mi_s else 0
    ic0    = ((td0 or 0) + (eq0 or 0) + (mi0 or 0) - (cash0 or 0))
    fcf0   = fcf_s[0] if fcf_s else None
    croic  = (fcf0 / ic0) if fcf0 and ic0 else None
    v = 'GOOD'  if croic is not None and croic > 0.15 else \
        'WATCH' if croic is not None and croic > 0.05 else \
        'BAD'   if croic is not None else 'NA'
    metrics.append(_score_metric('croic', v, W))

    # FCF/Sale (FCF Margin) TTM: >20% GOOD, >8% WATCH
    fcf_margin = (fcf0 / rev[0]) if fcf0 and rev and rev[0] else None
    v = 'GOOD'  if fcf_margin is not None and fcf_margin > 0.20 else \
        'WATCH' if fcf_margin is not None and fcf_margin > 0.08 else \
        'BAD'   if fcf_margin is not None else 'NA'
    metrics.append(_score_metric('fcf_sale', v, W))

    # FCF/CFO ratio 3yr avg > 5yr avg (quality of earnings)
    cfo0 = cfo_s[0] if cfo_s else None
    fcf_cfo_s = [(fcf_s[i] / cfo_s[i]) if fcf_s and i < len(fcf_s) and
                  cfo_s and i < len(cfo_s) and cfo_s[i] else None
                 for i in range(min(len(fcf_s), len(cfo_s), 6))]
    fcfo3 = _avg(fcf_cfo_s, 3)
    fcfo5 = _avg(fcf_cfo_s, 5)
    v = 'GOOD'  if fcfo3 is not None and fcfo5 is not None and fcfo3 > fcfo5 else \
        'WATCH' if fcfo3 is not None else 'NA'
    metrics.append(_score_metric('fcf_cfo', v, W))

    # ── RISK SCORES ───────────────────────────────────────────
    # Cash per Share: Cash/Debt ratio
    cash_debt = (cash0 / td0) if cash0 and td0 and td0 > 0 else None
    v = 'GOOD'  if cash_debt is not None and cash_debt > 1.0 else \
        'WATCH' if cash_debt is not None and cash_debt > 0.3 else \
        'BAD'   if cash_debt is not None else 'NA'
    metrics.append(_score_metric('cash_debt', v, W))

    # Cash per Share (absolute)
    cash_ps_val = (cash0 / shares) if cash0 and shares else None
    v = 'GOOD'  if cash_ps_val is not None and price and cash_ps_val > price * 0.1 else \
        'WATCH' if cash_ps_val is not None else 'NA'
    metrics.append(_score_metric('cash_share', v, W))

    # Altman Z-Score (non-manufacturer model)
    ta_s  = _series(bal, ['total assets', 'totalassets'])
    ta0   = ta_s[0] if ta_s else None
    ca_s  = _series(bal, ['current assets', 'total current assets', 'currentassets'])
    cl_s  = _series(bal, ['current liabilities', 'total current liabilities', 'currentliabilities'])
    re_s  = _series(bal, ['retained earnings', 'retainedearnings'])
    ca0   = ca_s[0] if ca_s else None
    cl0   = cl_s[0] if cl_s else None
    re0   = re_s[0] if re_s else None
    ebit0 = op[0] if op else None
    wc    = ((ca0 or 0) - (cl0 or 0)) if ca0 and cl0 else None
    altman = None
    if all(v is not None for v in [wc, re0, ebit0, eq0, td0, ta0]) and ta0 > 0 and td0 > 0:
        altman = 6.56*(wc/ta0) + 3.26*(re0/ta0) + 6.72*(ebit0/ta0) + 1.05*(eq0/td0)
    v = 'GOOD'  if altman is not None and altman > 2.6 else \
        'WATCH' if altman is not None and altman > 1.1 else \
        'BAD'   if altman is not None else 'NA'
    metrics.append(_score_metric('altman_z', v, W))

    # Beneish M-Score
    beneish = None
    if len(rev_s) >= 2 and len(ar_s) >= 2 and len(ta_s) >= 2:
        gp_s   = [(rev_s[i] - (cogs_s[i] or 0)) for i in range(min(len(rev_s), len(cogs_s or [])))] \
                 if cogs_s else []
        dep_s  = _series(cf, ['depreciation', 'depreciation and amortization',
                               'depreciationandamortization'])
        sga_s  = _series(inc, ['selling general administrative', 'sga', 'operatingexpenses'])
        ltd_s  = _series(bal, ['long term debt', 'longtermdebt'])
        ni0_   = np_[0] if np_ else None
        if all(len(s) >= 2 for s in [gp_s, dep_s, sga_s]) and ni0_ is not None and cfo0:
            beneish = _beneish_m(
                rev_s[0], rev_s[1], ar_s[0], ar_s[1],
                gp_s[0] if gp_s else None, gp_s[1] if len(gp_s) > 1 else None,
                ta_s[0], ta_s[1], ppe_s[0] if ppe_s else None,
                ppe_s[1] if ppe_s and len(ppe_s) > 1 else None,
                sga_s[0], sga_s[1], dep_s[0], dep_s[1],
                ni0_, cfo0, ltd_s[0] if ltd_s else 0, ltd_s[1] if ltd_s and len(ltd_s) > 1 else 0
            )
    # M < -2.22 = non-manipulator (GOOD), -2.22 to -1.78 = grey zone, > -1.78 = manipulator
    v = 'GOOD'  if beneish is not None and beneish < -2.22 else \
        'WATCH' if beneish is not None and beneish < -1.78 else \
        'BAD'   if beneish is not None else 'NA'
    metrics.append(_score_metric('beneish_m', v, W))

    # Piotroski F-Score
    ta1   = ta_s[1]  if len(ta_s) > 1 else None
    roa0  = (np_[0] / ta0) if np_ and ta0 else None
    roa1  = (np_[1] / ta1) if np_ and len(np_) > 1 and ta1 else None
    cfo_ta = (cfo0 / ta0) if cfo0 and ta0 else None
    lt0   = ltd_s[0] if 'ltd_s' in dir() and ltd_s else td0
    lt1   = ltd_s[1] if 'ltd_s' in dir() and ltd_s and len(ltd_s) > 1 else \
            (td_s[1] if td_s and len(td_s) > 1 else None)
    delta_lev = ((lt0 / ta0) - (lt1 / ta1)) if lt0 and ta0 and lt1 and ta1 else None
    cr1   = None  # would need prev year current ratio
    delta_cr = None
    sh0   = shares
    sh1_s = _series(bal, ['shares outstanding', 'common stock shares outstanding'])
    sh1   = sh1_s[1] if sh1_s and len(sh1_s) > 1 else None
    delta_sh = ((sh0 - sh1) / sh1) if sh0 and sh1 else None
    gm0  = ((rev_s[0] - (cogs_s[0] if cogs_s else 0)) / rev_s[0]) if rev_s and rev_s[0] else None
    gm1  = ((rev_s[1] - (cogs_s[1] if cogs_s and len(cogs_s) > 1 else 0)) / rev_s[1]) \
           if rev_s and len(rev_s) > 1 and rev_s[1] else None
    delta_gm = (gm0 - gm1) if gm0 is not None and gm1 is not None else None
    at0  = (rev_s[0] / ta0) if rev_s and ta0 else None
    at1  = (rev_s[1] / ta1) if rev_s and len(rev_s) > 1 and ta1 else None
    delta_at = (at0 - at1) if at0 is not None and at1 is not None else None

    piotroski = _piotroski_f(
        np_[0] if np_ else None, cfo0, roa0, roa1, cfo_ta,
        delta_lev, delta_cr, delta_sh, delta_gm, delta_at
    )
    # F ≥ 7 GOOD, 4–6 WATCH, ≤ 3 BAD
    v = 'GOOD'  if piotroski is not None and piotroski >= 7 else \
        'WATCH' if piotroski is not None and piotroski >= 4 else \
        'BAD'   if piotroski is not None else 'NA'
    metrics.append(_score_metric('piotroski_f', v, W))

    # ROIC vs WACC
    tax_r  = tax_rate if tax_rate else 0.21
    roic_v = _roic(ebit0, tax_r, td0 or 0, eq0 or 0, cash0 or 0)
    wacc_v = _wacc_simple(beta, rf=bond_yield, debt=td0 or 0,
                          equity=eq0 or 0, tax=tax_r)
    v = 'GOOD'  if roic_v is not None and wacc_v is not None and roic_v > wacc_v else \
        'WATCH' if roic_v is not None and wacc_v is not None else 'NA'
    metrics.append(_score_metric('roic_wacc', v, W))

    # ── COMPILE SCORE ─────────────────────────────────────────
    total = sum(m['pts'] for m in metrics)
    max_s = sum(m['max'] for m in metrics)
    pct   = (total / max_s * 100) if max_s else 0
    grade = 'A' if pct >= 75 else 'B' if pct >= 60 else 'C' if pct >= 50 else 'FAIL'

    return {
        'score':       total,
        'max':         max_s,
        'pct':         round(pct, 1),
        'grade':       grade,
        'is_bank':     False,
        'metrics':     metrics,
        'iv': {
            'dcf_eps':     round(iv_dcf_eps,    2) if iv_dcf_eps   else None,
            'dcf_fcf':     round(iv_dcf_fcf,    2) if iv_dcf_fcf   else None,
            'dcf_cash':    round(iv_dcf_cash,   2) if iv_dcf_cash  else None,
            'proj_fcf':    round(iv_proj_fcf,   2) if iv_proj_fcf  else None,
            'proj_cash':   round(iv_proj_cash,  2) if iv_proj_cash else None,
            'peter_lynch': round(iv_peter_lynch,2) if iv_peter_lynch else None,
            'composite':   round(iv_composite,  2) if iv_composite  else None,
            'mos_pct':     round(mos_composite * 100, 1) if mos_composite else None,
            'price':       price,
        },
        'altman_z':    round(altman,    2) if altman    else None,
        'beneish_m':   round(beneish,   2) if beneish   else None,
        'piotroski_f': piotroski,
    }


# --- BANK SCORING ---
def _score_bank(ticker, d, bond_yield=0.043):
    """
    Score bank stocks. Runs standard template first, then replaces
    N/A inventory/coverage metrics with bank-specific ratios.
    Bank ratios sourced from yfinance info + income_stmt.
    """
    result = _score_standard(ticker, d, bond_yield)
    result['is_bank'] = True
    info = d['info']
    inc  = d['inc']
    W    = IM3_BANK_WEIGHTS

    # Override tax threshold: 29% Pakistan banks, 25% US banks
    # Detect by exchange: if PSX exchange or Pakistan in country
    country = (info.get('country') or '').lower()
    tax_threshold = 0.29 if 'pakistan' in country else 0.25
    # Re-score tax rate metric
    tax_metric = next((m for m in result['metrics'] if m['key'] == 'tax_rate'), None)
    if tax_metric:
        # Re-evaluate with correct threshold
        tax_exp_s = _series(inc, ['tax provision', 'income tax expense',
                                   'incometaxexpense', 'taxprovision'])
        pbt_s     = _series(inc, ['pretax income', 'income before tax',
                                   'incomebeforetax', 'ebt'])
        tr = (tax_exp_s[0] / pbt_s[0]) if tax_exp_s and pbt_s and pbt_s[0] else \
             info.get('effectiveTaxRate')
        v = 'GOOD' if tr is not None and tr >= tax_threshold else \
            'WATCH' if tr is not None else 'NA'
        tax_metric['verdict'] = v
        tax_metric['pts'] = _pts(v, W.get('tax_rate', 3))

    # Zero out every metric that does not apply to a bank (full canonical set, not just
    # the original 6) so it contributes to neither score nor denominator.
    for key in _BANK_ZERO:
        m = next((x for x in result['metrics'] if x['key'] == key), None)
        if m:
            m['verdict'] = 'NA'
            m['pts'] = 0
            m['max'] = 0

    # ── BANK-SPECIFIC METRICS ─────────────────────────────────
    bank_metrics = []

    # NIM = Net Interest Income / Average Earning Assets
    # yfinance: netInterestIncome in income_stmt
    nii_s = _series(inc, ['net interest income', 'netinterestincome',
                           'interest income net'])
    ta_s  = _series(d['bal'], ['total assets', 'totalassets'])
    nim   = (nii_s[0] / ta_s[0]) if nii_s and ta_s and ta_s[0] else \
            info.get('netInterestMargin')
    # NIM: ≥4% GOOD, ≥3% WATCH, <3% BAD (global benchmark)
    v = 'GOOD'  if nim is not None and nim >= 0.04 else \
        'WATCH' if nim is not None and nim >= 0.03 else \
        'BAD'   if nim is not None else 'NA'
    bank_metrics.append(_score_metric('nim', v, W))

    # CASA = (Current + Savings Deposits) / Total Deposits
    # yfinance rarely has this directly; use info or skip gracefully
    casa = info.get('casaRatio') or info.get('currentAccountSavingsRatio')
    # For US community banks CASA not in yfinance — mark NA
    v = 'GOOD'  if casa is not None and casa >= 0.80 else \
        'WATCH' if casa is not None and casa >= 0.70 else \
        'BAD'   if casa is not None else 'NA'
    bank_metrics.append(_score_metric('casa', v, W))

    # ADR = Advances / Deposits (sweet spot 40-60%)
    loans_s = _series(d['bal'], ['net loans', 'loans', 'totalloans',
                                   'net loan and lease', 'netloanandlease'])
    dep_s   = _series(d['bal'], ['total deposits', 'deposits', 'totaldeposits'])
    adr = (loans_s[0] / dep_s[0]) if loans_s and dep_s and dep_s[0] else None
    v = 'GOOD'  if adr is not None and 0.40 <= adr <= 0.60 else \
        'WATCH' if adr is not None and (0.30 <= adr < 0.40 or 0.60 < adr <= 0.70) else \
        'BAD'   if adr is not None else 'NA'
    bank_metrics.append(_score_metric('adr', v, W))

    # NPL ratio = Non-Performing Loans / Total Loans
    npl_s  = _series(d['bal'], ['nonperforming loans', 'nonperformingassets',
                                  'non performing loans'])
    npl    = (npl_s[0] / loans_s[0]) if npl_s and loans_s and loans_s[0] else None
    if npl is None:
        # Proxy: allowance for loan losses / total loans
        all_s = _series(d['bal'], ['allowance for loan losses',
                                    'allowanceforloanlosses'])
        npl   = (all_s[0] / loans_s[0]) if all_s and loans_s and loans_s[0] else None
    v = 'GOOD'  if npl is not None and npl < 0.03 else \
        'WATCH' if npl is not None and npl < 0.05 else \
        'BAD'   if npl is not None else 'NA'
    bank_metrics.append(_score_metric('npl', v, W))

    # CAR = Capital Adequacy Ratio (Tier 1 + Tier 2 / RWA)
    car = info.get('capitalAdequacyRatio') or info.get('tier1CapitalRatio')
    if car and car > 1:
        car = car / 100  # normalise if percentage
    v = 'GOOD'  if car is not None and car >= 0.18 else \
        'WATCH' if car is not None and car >= 0.15 else \
        'BAD'   if car is not None else 'NA'
    bank_metrics.append(_score_metric('car', v, W))

    # Add bank metrics to result
    result['metrics'].extend(bank_metrics)

    # Input-availability probe (Wave D1/System-B Phase 2): records which canonical bank
    # inputs Yahoo actually returned, so the next-phase ratios (spread ratio, PPNR growth,
    # provision/GL, loan/deposit growth, ROA, true P/TBV) are built from confirmed data.
    result['bank_inputs'] = {
        'nii':          (nii_s[0]   if nii_s   else None),
        'total_assets': (ta_s[0]    if ta_s    else None),
        'gross_loans':  (loans_s[0] if loans_s else None),
        'deposits':     (dep_s[0]   if dep_s   else None),
        'npl_found':    npl  is not None,
        'casa_found':   casa is not None,
        'car_found':    car  is not None,
    }

    # ── COMPILE BANK SCORE (canonical denominator) ───────────
    # Score on applicable (bank-weight>0) metrics only. The denominator excludes NA so a
    # data-vendor gap (e.g. CASA/CAR absent on Yahoo for US banks) doesn't structurally
    # penalise the bank. pct is NO LONGER score/162 — a bank is scored out of its own
    # applicable max (~70), fixing the prior bug that capped every bank near 55%.
    applicable = [m for m in result['metrics'] if W.get(m['key'], 0) > 0]
    total = sum(_pts(m['verdict'], W.get(m['key'], 0)) for m in applicable)
    max_s = sum(W.get(m['key'], 0) for m in applicable if m['verdict'] != 'NA')
    n_meas = sum(1 for m in applicable if m['verdict'] != 'NA')
    pct   = (total / max_s * 100) if max_s else 0
    grade = 'A' if pct >= 75 else 'B' if pct >= 60 else 'C' if pct >= 50 else 'FAIL'

    result['score']         = total
    result['max']           = max_s
    result['pct']           = round(pct, 1)
    result['grade']         = grade
    result['bank_coverage'] = round(n_meas / len(applicable), 2) if applicable else 0
    return result


# --- MAIN ENTRY POINT ---
def score_im3(ticker):
    """
    Score a single ticker using the full IM3 162-point methodology.
    Returns dict: {score, max, pct, grade, is_bank, metrics, iv, ...}
    Returns None if data fetch fails.
    """
    try:
        log(f'  IM3 scoring {ticker}...')
        d = _fetch_im3_data(ticker)
        if d is None:
            return None

        is_bank = _is_bank(d['info'])

        # Bond yield: fetch US 10Y from FRED if available, else use default
        bond_yield = 0.043  # Default ~4.3%
        try:
            import requests as _req
            if FRED_KEY:
                r = _req.get(
                    f'https://api.stlouisfed.org/fred/series/observations'
                    f'?series_id=DGS10&api_key={FRED_KEY}&limit=1'
                    f'&sort_order=desc&file_type=json', timeout=5)
                if r.status_code == 200:
                    obs = r.json().get('observations', [{}])
                    val = obs[0].get('value', '')
                    if val and val != '.':
                        bond_yield = float(val) / 100
        except Exception:
            pass

        if is_bank:
            result = _score_bank(ticker, d, bond_yield)
        else:
            result = _score_standard(ticker, d, bond_yield)

        log(f'  IM3 {ticker}: {result["score"]}/162 ({result["pct"]}%) '
            f'Grade {result["grade"]} {"[BANK]" if is_bank else ""}')
        return result

    except Exception as e:
        log(f'  IM3 scoring error {ticker}: {e}')
        return None


def run_im3_on_explosives(explosive_list, max_stocks=30):
    """
    Run IM3 scoring on explosive_us records.
    Adds 'im3' key to each record. Only scores EXPLOSIVE both-signal records first,
    then fills remaining budget with QUALITY-GROWTH if time permits.
    """
    if not explosive_list:
        return explosive_list

    log(f'=== IM3 162-pt scoring on {len(explosive_list)} explosive US stocks ===')

    # Priority order: both-signal first
    priority = sorted(explosive_list,
                      key=lambda r: (r.get('verdict', '').startswith('EXPLOSIVE'),),
                      reverse=True)

    scored = 0
    for rec in priority:
        if scored >= max_stocks:
            break
        ticker = rec.get('ticker')
        if not ticker:
            continue
        try:
            im3 = score_im3(ticker)
            rec['im3'] = im3
            if im3:
                scored += 1
        except Exception as e:
            log(f'  IM3 run error {ticker}: {e}')
            rec['im3'] = None
        time.sleep(YF_DELAY * 2)  # respectful delay — IM3 fetch is heavier

    log(f'  IM3 scored: {scored} of {len(explosive_list)} stocks')
    return explosive_list


# =============================================================
# 6. RATE PATH
# =============================================================
def fetch_rate_path():
    return [
        {'date': '2025-09-15', 'rate': 11.00, 'action': 'HOLD'},
        {'date': '2025-10-27', 'rate': 11.00, 'action': 'HOLD'},
        {'date': '2025-12-15', 'rate': 10.50, 'action': 'CUT -50bp'},
        {'date': '2026-01-26', 'rate': 10.50, 'action': 'HOLD'},
        {'date': '2026-03-09', 'rate': 10.50, 'action': 'HOLD'},
        {'date': '2026-04-27', 'rate': 11.50, 'action': 'HIKE +100bp'},
        {'date': '2026-05-24', 'rate': 11.50, 'action': 'CURRENT'},
    ]


# =============================================================
# MAIN
# =============================================================
RECESSION_SERIES = {
    'sahm':           'SAHMREALTIME',
    'recession_prob': 'RECPROUSM156N',
    'yc_2y':          'T10Y2Y',
    'yc_3m':          'T10Y3M',
    'gdpnow':         'GDPNOW',
    'claims':         'ICSA',
}


def _ff_us_events(events, limit=12):
    """Filter the ForexFactory faireconomy weekly calendar to upcoming high/medium
    impact US (USD) releases. Pure. No 'actual' field — FF omits it until release;
    realized values come from FRED."""
    out = []
    if not isinstance(events, list):
        return out
    for e in events:
        if not isinstance(e, dict):
            continue
        if str(e.get('country', '')).upper() != 'USD':
            continue
        if str(e.get('impact', '')).lower() not in ('high', 'medium'):
            continue
        out.append({'title': e.get('title'), 'date': e.get('date'),
                    'impact': e.get('impact'), 'forecast': e.get('forecast'),
                    'previous': e.get('previous')})
    out.sort(key=lambda x: (0 if str(x.get('impact', '')).lower() == 'high' else 1,
                            str(x.get('date') or '')))
    return out[:limit]


def _recession_assess(sig):
    """Rule-based composite from the FRED signals. Pure + transparent.
    Returns (risk_label, score_0_100, triggers)."""
    triggers = []
    score = 0

    def _num(key):
        v = (sig.get(key) or {}).get('value')
        try:
            return float(v)
        except Exception:
            return None

    sahm = _num('sahm')
    if sahm is not None and sahm >= 0.50:
        triggers.append('Sahm rule triggered (>=0.50)'); score += 45
    elif sahm is not None and sahm >= 0.30:
        triggers.append('Sahm rising (>=0.30)'); score += 20

    yc2 = _num('yc_2y'); yc3 = _num('yc_3m')
    if (yc2 is not None and yc2 < 0) or (yc3 is not None and yc3 < 0):
        triggers.append('Yield curve inverted'); score += 20

    prob = _num('recession_prob')
    if prob is not None:
        if prob >= 50:
            triggers.append('NBER-style probability high (%d%%)' % round(prob)); score += 25
        elif prob >= 25:
            triggers.append('Recession probability elevated (%d%%)' % round(prob)); score += 12

    gdp = _num('gdpnow')
    if gdp is not None and gdp < 0:
        triggers.append('GDPNow negative (%.1f%%)' % gdp); score += 15

    score = min(score, 100)
    if score >= 60 or (sahm is not None and sahm >= 0.50):
        risk = 'HIGH'
    elif score >= 25:
        risk = 'ELEVATED'
    else:
        risk = 'LOW'
    return risk, score, triggers


def fetch_recession():
    """US recession watch (Wave C). FRED recession series + the ForexFactory weekly
    economic calendar via the faireconomy export host (the FF main site is
    Cloudflare-walled). Never raises; falls back to last-good per part."""
    prev = EXISTING.get('recession', {}) or {}
    out = {'signals': {}, 'calendar': prev.get('calendar', []),
           'source': 'FRED + faireconomy',
           '_fetched_utc': dt.datetime.utcnow().isoformat() + 'Z'}

    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            for key, sid in RECESSION_SERIES.items():
                try:
                    time.sleep(0.5)
                    s = fred.get_series(sid).dropna()
                    if len(s) > 0:
                        out['signals'][key] = {'value': round(float(s.iloc[-1]), 2),
                                               'date': str(s.index[-1].date())}
                except Exception as e:
                    warn(f'recession FRED {key} ({sid}) failed: {e}')
                    lg = (prev.get('signals') or {}).get(key)
                    if lg is not None:
                        out['signals'][key] = lg
        except Exception as e:
            warn(f'recession FRED init failed: {e}')
            out['signals'] = prev.get('signals', {})
    else:
        out['signals'] = prev.get('signals', {})

    try:
        r = requests.get('https://nfs.faireconomy.media/ff_calendar_thisweek.json',
                         headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=12)
        ctype = r.headers.get('Content-Type', '')
        if r.status_code == 200 and 'json' in ctype.lower():
            cal = _ff_us_events(r.json())
            if cal:
                out['calendar'] = cal
                log(f'  ✓ Recession calendar: {len(cal)} high-impact US releases (faireconomy)')
        else:
            warn('FF calendar non-JSON (rate-limited?) — keeping last-good calendar')
    except Exception as e:
        warn(f'FF calendar failed: {e} — keeping last-good calendar')

    risk, score, triggers = _recession_assess(out['signals'])
    out['risk'] = risk
    out['score'] = score
    out['triggers'] = triggers
    log(f'  ✓ Recession watch: {risk} (score {score}) — {len(out["signals"])} FRED signals, '
        f'{len(out.get("calendar", []))} calendar events')
    return out


def main():
    log('=' * 60)
    log(f'Dashboard scanner v{SCAN_VERSION} starting')
    log('=' * 60)

    data = DEFAULT_DATA.copy()
    data['meta'] = {
        'scan_version':  SCAN_VERSION,
        'last_scan_utc': dt.datetime.utcnow().isoformat() + 'Z',
        'errors':        [],
        'warnings':      [],
    }

    try:
        data['macros']['us'] = fetch_us_macros()
    except Exception as e:
        log(f'US macros crashed: {e}')
        data['meta']['errors'].append(f'us_macros: {e}')
        data['macros']['us'] = EXISTING.get('macros', {}).get('us', {})

    try:
        data['macros']['psx'] = fetch_psx_macros()
    except Exception as e:
        log(f'PSX macros crashed: {e}')
        data['meta']['errors'].append(f'psx_macros: {e}')
        data['macros']['psx'] = EXISTING.get('macros', {}).get('psx', {})

    try:
        data['macros']['metals'] = fetch_metals()
    except Exception as e:
        log(f'Metals macros crashed: {e}')
        data['meta']['errors'].append(f'metals_macros: {e}')
        data['macros']['metals'] = EXISTING.get('macros', {}).get('metals', {})

    us_all_survivors = []
    try:
        us_result = screen_us_universe()
        data['us_funnel']    = us_result['funnel']
        data['us_candidates'] = us_result['candidates']
        us_all_survivors     = us_result.get('all_survivors', us_result['candidates'])
    except Exception as e:
        log(f'US screening crashed: {e}')
        data['meta']['errors'].append(f'us_screen: {e}')
        data['us_funnel']    = EXISTING.get('us_funnel', [])
        data['us_candidates'] = EXISTING.get('us_candidates', [])
        us_all_survivors     = data['us_candidates']

    try:
        psx_result = screen_psx_universe()
        data['psx_funnel']    = psx_result['funnel']
        data['psx_candidates'] = psx_result['candidates']
    except Exception as e:
        log(f'PSX screening crashed: {e}')
        data['meta']['errors'].append(f'psx_screen: {e}')
        data['psx_funnel']    = EXISTING.get('psx_funnel', [])
        data['psx_candidates'] = EXISTING.get('psx_candidates', [])

    _spy6 = _spy_6mo_return()
    _prev_us = {r['ticker']: r['streams'].get('rev_est') for r in EXISTING.get('tce_us', [])
                if isinstance(r.get('streams'), dict)}
    _etf_stocks = (EXISTING.get('etf_overlap', {}) or {}).get('stocks', [])
    _us_pool = merge_tce_pool(data['us_candidates'], _etf_stocks)
    _n_etf = sum(1 for c in _us_pool if c.get('src') == 'etf')
    log(f'  US TCE pool: {len(_us_pool) - _n_etf} screen + {_n_etf} ETF-consensus = {len(_us_pool)}')
    try:
        data['tce_us'] = run_tce(_us_pool, market='us',
                                  max_count=len(_us_pool), spy_6mo_ret=_spy6, prev_rev=_prev_us)
    except Exception as e:
        log(f'US TCE crashed: {e}')
        data['meta']['errors'].append(f'us_tce: {e}')
        data['tce_us'] = EXISTING.get('tce_us', [])

    try:
        _prev_psx = {r['ticker']: r['streams'].get('rev_est') for r in EXISTING.get('tce_psx', [])
                     if isinstance(r.get('streams'), dict)}
        data['tce_psx'] = run_tce(data['psx_candidates'], market='psx',
                                  max_count=max(len(data['psx_candidates']), 10),
                                  spy_6mo_ret=_spy6, prev_rev=_prev_psx)
    except Exception as e:
        log(f'PSX TCE crashed: {e}')
        data['meta']['errors'].append(f'psx_tce: {e}')
        data['tce_psx'] = EXISTING.get('tce_psx', [])

    # Forward-validation: log this run's HIGH/WATCH picks + entry price; track forward returns over time.
    try:
        _today = dt.date.today().isoformat()
        _rows = []
        for _mkt, _key in (('us', 'tce_us'), ('psx', 'tce_psx')):
            for r in data.get(_key, []):
                pr = r.get('streams', {}).get('price') if isinstance(r.get('streams'), dict) else None
                if r.get('tier') in ('HIGH', 'WATCH') and pr:
                    _rows.append({'ticker': r['ticker'], 'tier': r['tier'], 'market': _mkt, 'price': pr})
        data['tce_predictions'] = update_tce_predictions(EXISTING.get('tce_predictions'), _today, _rows)
        _s = data['tce_predictions']['summary']
        log(f"TCE predictions: {_s['total_logged']} logged, {_s['open']} open; "
            f"HIGH matured={_s['HIGH']['matured']} hit_rate={_s['HIGH']['hit_rate']}; "
            f"WATCH matured={_s['WATCH']['matured']} hit_rate={_s['WATCH']['hit_rate']}")
    except Exception as e:
        log(f'TCE prediction logger failed: {e}')
        data['tce_predictions'] = EXISTING.get('tce_predictions', {})

    try:
        data['explosive_us'] = run_explosive(us_all_survivors, market='us')
    except Exception as e:
        log(f'US explosive crashed: {e}')
        data['meta']['errors'].append(f'us_explosive: {e}')
        data['explosive_us'] = EXISTING.get('explosive_us', [])

    try:
        data['explosive_psx'] = run_explosive(data['psx_candidates'], market='psx')
    except Exception as e:
        log(f'PSX explosive crashed: {e}')
        data['meta']['errors'].append(f'psx_explosive: {e}')
        data['explosive_psx'] = EXISTING.get('explosive_psx', [])

    try:
        data['rate_path'] = fetch_rate_path()
    except Exception as e:
        log(f'Rate path crashed: {e}')
        data['rate_path'] = EXISTING.get('rate_path', [])

    # v1.11: COT index/commodity futures for US sector gating (SP500/Crude/10yr/VIX/NASDAQ)
    try:
        data['cot_futures'] = fetch_cot_futures()
    except Exception as e:
        log(f'COT futures crashed: {e}')
        data['meta']['errors'].append(f'cot_futures: {e}')
        data['cot_futures'] = EXISTING.get('cot_futures', {})

    # Wave C: US recession watch (FRED recession series + ForexFactory weekly calendar)
    try:
        data['recession'] = fetch_recession()
    except Exception as e:
        log(f'Recession watch crashed: {e}')
        data['meta']['errors'].append(f'recession: {e}')
        data['recession'] = EXISTING.get('recession', {})

    # v1.11: Zacks #1/#2 grouped by GICS sector (fixed S&P universe + this run's survivors)
    # Cadence gate: Zacks ranks update ~weekly, but the scrape costs ~17 min. Skip it if the
    # last scrape is <7 days old and carry forward last-good (sector breadth is stable
    # intra-week); otherwise scrape and stamp the date.
    _prev_z = EXISTING.get('zacks_sectors', {}) or {}
    _prev_scraped = _prev_z.get('_scraped_utc') if isinstance(_prev_z, dict) else None
    _z_age = None
    _z_fresh = False
    if _prev_scraped:
        try:
            _z_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_prev_scraped).replace('Z', ''))).days
            _z_fresh = _z_age < 7
        except Exception:
            _z_fresh = False
    try:
        if _z_fresh:
            log(f'  → Zacks scrape skipped (last scrape {_z_age}d ago, <7d) — carrying forward last-good')
            data['zacks_sectors'] = _prev_z
        else:
            data['zacks_sectors'] = fetch_zacks_sectors(us_all_survivors)
            data['zacks_sectors']['_scraped_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
    except Exception as e:
        log(f'Zacks sectors crashed: {e}')
        data['meta']['errors'].append(f'zacks_sectors: {e}')
        data['zacks_sectors'] = EXISTING.get('zacks_sectors', {})

    # Smart-Money ETF Holdings Overlap (Part D) — weekly cadence (holdings barely move).
    _zacks_tops = []
    for _sec, _v in (data.get('zacks_sectors') or {}).items():
        if isinstance(_v, dict):
            _zacks_tops += _v.get('top_tickers', [])
    _prev_etf = EXISTING.get('etf_overlap', {}) or {}
    _etf_fresh = False; _etf_age = None
    _es = _prev_etf.get('_scraped_utc') if isinstance(_prev_etf, dict) else None
    if _es:
        try:
            _etf_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_es).replace('Z',''))).days
            # fresh only if young AND produced by the current scanner version — so any ETF-code
            # fix (new version) forces a one-time re-run instead of carrying forward stale output
            _etf_fresh = _etf_age < 7 and _prev_etf.get('_scan_version') == SCAN_VERSION
        except Exception:
            _etf_fresh = False
    try:
        if _etf_fresh and _prev_etf.get('stocks'):
            log(f'  → ETF holdings overlap skipped (last scrape {_etf_age}d ago, <7d) — carrying forward last-good')
            data['etf_overlap'] = _prev_etf
        else:
            _r12 = [{'etf': t, 'zacks_rank': 1} for t in TOP_ETFS]
            _hmap = {}; _src = []
            for _e in _r12:
                _tk = _e['etf']
                _hmap[_tk] = fetch_etf_holdings(_tk)
                _nm, _ytd, _y1 = ETF_META.get(_tk, (_tk, None, None))
                _m = fetch_etf_meta(_tk)
                _src.append({'ticker': _tk, 'name': _nm, 'ytd': _ytd, 'y1': _y1,
                             'y3': _m['y3'], 'expense': _m['expense']})
                time.sleep(0.5)
            _stocks = build_etf_overlap(_r12, _hmap, _zacks_tops)
            _got = sum(1 for v in _hmap.values() if v)
            data['etf_overlap'] = {
                '_scraped_utc': dt.datetime.utcnow().isoformat() + 'Z',
                '_scan_version': SCAN_VERSION,
                'etfs_scanned': len(TOP_ETFS),
                'etfs_with_holdings': _got,
                'source_etfs': _src,
                'stocks': _stocks,
            }
            log(f'  ETF overlap: {_got}/{len(TOP_ETFS)} ETFs returned holdings -> top {len(_stocks)} consensus stocks')
    except Exception as e:
        log(f'ETF overlap crashed: {e}')
        data['meta']['errors'].append(f'etf_overlap: {e}')
        data['etf_overlap'] = EXISTING.get('etf_overlap', {})

    data['meta']['warnings'] = list(WARNINGS)

    # Carry IM3 forward from the last good data.json. The scanner doesn't SCORE IM3
    # (im3_score.py does, as a separate workflow step), but it rebuilds explosive_us/tce_us
    # from scratch each run with no 'im3' field — so it must re-attach two things or the
    # dashboard's IM3 panel blanks out on any run where the IM3 step is skipped:
    #   1. im3_explosive_tickers (the list) — so the workflow's change-detection has a real
    #      previous list to compare against and can skip re-scoring on stable days.
    #   2. the per-record 'im3' score dicts, keyed by ticker — so a skipped re-score keeps
    #      the prior scores. When names DO change, the IM3 step re-runs and overwrites these.
    if 'im3_explosive_tickers' not in data:
        data['im3_explosive_tickers'] = EXISTING.get('im3_explosive_tickers', [])

    _im3_prev = {}
    for _key in ('explosive_us', 'tce_us'):
        for _r in EXISTING.get(_key, []):
            if isinstance(_r, dict) and _r.get('im3') is not None and _r.get('ticker'):
                _im3_prev[_r['ticker']] = _r['im3']
    if _im3_prev:
        _carried = 0
        for _key in ('explosive_us', 'tce_us'):
            for _r in data.get(_key, []):
                if isinstance(_r, dict) and _r.get('im3') is None and _r.get('ticker') in _im3_prev:
                    _r['im3'] = _im3_prev[_r['ticker']]; _carried += 1
        if _carried:
            log(f'  Carried forward {_carried} last-good IM3 score(s) onto rebuilt records')

    def _json_safe(o):
        # NaN / Infinity are NOT valid JSON; the browser's JSON.parse rejects them.
        # Convert to None (null) recursively so data.json is spec-valid.
        if isinstance(o, float):
            return None if (math.isnan(o) or math.isinf(o)) else o
        if isinstance(o, dict):
            return {k: _json_safe(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_json_safe(v) for v in o]
        return o

    try:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(_json_safe(data), f, indent=2, default=str, allow_nan=False)
        log(f'data.json written ({OUTPUT_PATH.stat().st_size} bytes)')
    except Exception as e:
        log(f'Failed to write data.json: {e}')
        sys.exit(1)

    log('=' * 60)
    log('Scanner completed')
    log(f'  Hard errors: {len(data["meta"]["errors"])}')
    log(f'  Warnings (degraded data): {len(data["meta"]["warnings"])}')
    for w in data['meta']['warnings']:
        log(f'      - {w}')
    log(f'  US macros: '
        f'{len([k for k in data["macros"]["us"] if not k.endswith(("_date","_source"))])}')
    log(f'  PSX macros: '
        f'{len([k for k in data["macros"]["psx"] if not k.endswith(("_date","_source"))])}')
    log(f'  KSE-100: {data["macros"]["psx"].get("kse100")} '
        f'({data["macros"]["psx"].get("kse100_source")}, '
        f'as of {data["macros"]["psx"].get("kse100_date")})')
    log(f'  WTI/Brent: {data["macros"]["us"].get("wti")} / '
        f'{data["macros"]["us"].get("brent")} '
        f'({data["macros"]["us"].get("wti_source")}, '
        f'as of {data["macros"]["us"].get("wti_date")})')
    log(f'  US candidates: {len(data["us_candidates"])}')
    log(f'  PSX candidates: {len(data["psx_candidates"])}')
    log(f'  US TCE HIGH: '
        f'{sum(1 for r in data["tce_us"] if r.get("tier") == "HIGH")}')
    log(f'  PSX TCE HIGH: '
        f'{sum(1 for r in data["tce_psx"] if r.get("tier") == "HIGH")}')
    log(f'  Recession: {data.get("recession",{}).get("risk","—")} '
        f'(score {data.get("recession",{}).get("score","—")}, '
        f'{len(data.get("recession",{}).get("calendar",[]))} cal events)')
    log('=' * 60)


if __name__ == '__main__':
    main()
