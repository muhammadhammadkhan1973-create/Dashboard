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
SCAN_VERSION = '1.12.10'  # CPI parser: decode &nbsp; entity between year/month (TheGlobalEconomy) — pinned via raw-HTML diag

YF_DELAY          = 0.35
US_SMALL_CAP_MIN  = 300_000_000
US_SMALL_CAP_MAX  = 2_000_000_000
US_REV_GROWTH_MIN = 0.15

US_CANDIDATE_POOL = 15    # top survivors fed to TCE (slow, network-heavy)
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
    'explosive_psx': [], 'explosive_us': [],
    'rate_path': [],
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
                    log(f'  ✓ {key} = {out[key]}')
            except Exception as e:
                warn(f'FRED {key} ({sid}) failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'us', key)
                if lg is not None:
                    out[key] = lg
                    log(f'  · {key}: kept last-good = {lg}')

        # Live oil — Yahoo first, FRED fallback
        oil = fetch_live_oil()
        for key, fred_id in (('wti', 'DCOILWTICO'), ('brent', 'DCOILBRENTEU')):
            if key in oil:
                out[key] = oil[key]
                out[f'{key}_source'] = oil[f'{key}_source']
                out[f'{key}_date']   = oil.get(f'{key}_date')
            else:
                try:
                    s = fred.get_series(fred_id).dropna()
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

        # Baker Hughes rig count (F1) — single quick attempt. It reliably blocks the
        # GitHub runner, so don't burn ~80s retrying; fall straight through to last-good.
        try:
            import re as _re
            rr = requests.get('https://rigcount.bakerhughes.com/rig-count-overview',
                              headers={'User-Agent': UA}, timeout=8)
            if rr.status_code == 200:
                mm = _re.search(r'U\.?S\.?\s*Oil[^0-9]{0,40}(\d{3,4})', rr.text)
                if mm:
                    out['us_oil_rigs'] = int(mm.group(1))
                    log(f'  ✓ US oil rigs (Baker Hughes): {out["us_oil_rigs"]}')
        except Exception as e:
            log(f'  · Rig count (last-good): {e}')
        if out.get('us_oil_rigs') is None:
            lg = safe_get(EXISTING, 'macros', 'us', 'us_oil_rigs')
            if lg is not None:
                out['us_oil_rigs'] = lg
                log('  · Baker Hughes rig count unreachable; using last-good')

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
def fetch_kse100():
    import re
    headers = {'User-Agent': UA}
    today = str(dt.date.today())

    def sane(v):
        try:
            v = float(v)
            return v if KSE_MIN < v < KSE_MAX else None
        except Exception:
            return None

    def ts_to_date(ts):
        try:
            ts = float(ts)
            if ts > 1e12:
                ts /= 1000.0
            return str(dt.datetime.utcfromtimestamp(ts).date())
        except Exception:
            return None

    def grab(text):
        anchor = re.search(r'KSE\s*-?\s*100', text, re.I)
        if not anchor:
            return None
        window = text[anchor.end(): anchor.end() + 400]
        for num in re.findall(r'[\d,]{5,}(?:\.\d+)?', window):
            v = sane(num.replace(',', ''))
            if v is not None:
                return round(v, 2)
        return None

    for path in ('eod', 'int'):
        try:
            url = f'https://dps.psx.com.pk/timeseries/{path}/KSE100'
            r = requests.get(url, headers={**headers, 'Accept': 'application/json'},
                             timeout=15)
            if r.status_code == 200:
                j = r.json()
                rows = j.get('data') if isinstance(j, dict) else j
                if rows:
                    last = rows[-1]
                    val = None
                    date_str = None
                    if isinstance(last, (list, tuple)):
                        if len(last) >= 1:
                            date_str = ts_to_date(last[0])
                        if len(last) >= 5:
                            val = sane(last[4])
                        if val is None and len(last) >= 2:
                            val = sane(last[1])
                    if val is not None:
                        return round(val, 2), f'psx-dps:{path}', (date_str or today)
        except Exception as e:
            log(f'  · KSE-100 dps/{path} miss: {e}')

    try:
        r = requests.get('https://dps.psx.com.pk/indices', headers=headers, timeout=15)
        if r.status_code == 200:
            val = grab(r.text)
            if val is not None:
                return val, 'psx-dps:indices', today
    except Exception as e:
        log(f'  · KSE-100 dps/indices miss: {e}')

    for url in ('https://sarmaaya.pk/psx/market/KSE100',
                'https://sarmaaya.pk/indexes/KSE100'):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                val = grab(r.text)
                if val is not None:
                    return val, 'sarmaaya', today
        except Exception as e:
            log(f'  · KSE-100 sarmaaya miss: {e}')

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
        h = yf.Ticker('USDPKR=X').history(period='5d')
        if len(h) > 0:
            out['usd_pkr'] = round(float(h['Close'].iloc[-1]), 2)
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
        rows = requests.get(url, headers=headers, timeout=20).json()
        found = set()
        for rec in rows:
            name = str(rec.get('market_and_exchange_names', '')).upper()
            for key, kw in COT_KEYWORDS.items():
                if key in found:
                    continue
                if kw.upper() in name:
                    lng = float(rec.get('asset_mgr_positions_long', 0) or 0)
                    sht = float(rec.get('asset_mgr_positions_short', 0) or 0)
                    net = lng - sht
                    out[key] = {'long': int(lng), 'short': int(sht), 'net': int(net),
                                'signal': ('VERY BULLISH' if net > 500000 else 'BULLISH' if net > 0
                                           else 'BEARISH' if net > -500000 else 'VERY BEARISH'),
                                'date': rec.get('report_date_as_yyyy_mm_dd')}
                    found.add(key)
        log(f'  ✓ COT futures (TFF): {len(found)}/4 [{", ".join(sorted(found))}]')
    except Exception as e:
        warn(f'COT futures (TFF) failed: {e}')
    # --- Disaggregated: Crude (Managed Money) ---
    try:
        url = ('https://publicreporting.cftc.gov/resource/72hh-3qpy.json'
               '?$order=report_date_as_yyyy_mm_dd DESC&$limit=200')
        rows = requests.get(url, headers=headers, timeout=20).json()
        for rec in rows:
            name = str(rec.get('market_and_exchange_names', '')).upper()
            if 'WTI-PHYSICAL' in name and 'NEW YORK' in name:
                lng = float(rec.get('m_money_positions_long_all', 0) or 0)
                sht = float(rec.get('m_money_positions_short_all', 0) or 0)
                net = lng - sht
                out['Crude'] = {'long': int(lng), 'short': int(sht), 'net': int(net),
                                'signal': ('VERY BULLISH' if net > 200000 else 'BULLISH' if net > 0
                                           else 'BEARISH' if net > -200000 else 'VERY BEARISH'),
                                'date': rec.get('report_date_as_yyyy_mm_dd')}
                break
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
            h = yf.Ticker(sym).history(period='5d')
            if len(h) > 0:
                out[key] = round(float(h['Close'].iloc[-1]), 2)
                out[f'{key}_date'] = str(h.index[-1].date())
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
                log(f'  ✓ WALCL: ${out["walcl"]}T ({out["walcl_change"]:+.2f}%)')
        except Exception as e:
            warn(f'WALCL FRED failed: {e}')
            for k in ('walcl', 'walcl_change'):
                lg = safe_get(EXISTING, 'macros', 'metals', k)
                if lg is not None:
                    out[k] = lg

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

    except Exception as e:
        warn(f'COT CFTC fetch failed: {e}')
        for k in ('cot_gold_net','cot_gold_oi','cot_gold_pct','cot_gold_long','cot_gold_short','cot_gold_long_pct','cot_gold_short_pct',
                  'cot_silver_net','cot_silver_oi','cot_silver_pct','cot_silver_long','cot_silver_short','cot_silver_long_pct','cot_silver_short_pct',
                  'cot_copper_net','cot_copper_oi','cot_copper_pct','cot_copper_long','cot_copper_short','cot_copper_long_pct','cot_copper_short_pct','cot_date'):
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
        rev_growth = info.get('revenueGrowth')
        if rev_growth is None or rev_growth < US_REV_GROWTH_MIN:
            return None
        insider = info.get('heldPercentInsiders', 0) or 0
        if insider < 0.05:
            return None
        yf_rev = round(float(rev_growth) * 100, 1)
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

    tickers = fetch_us_universe()
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
    candidates.sort(key=lambda c: c.get('rev_growth', 0) or 0, reverse=True)

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

    # Fundamentals: (ticker, name, sector, rev_growth_pct, eps_growth_pct)
    # Source: PSX annual reports FY2024 vs FY2023. Update quarterly.
    return [
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


def screen_psx_stock(ticker_tuple):
    # Accepts (ticker, name, sector) or (ticker, name, sector, rev_growth, eps_growth)
    ticker, name, sector = ticker_tuple[0], ticker_tuple[1], ticker_tuple[2]
    rev_growth = ticker_tuple[3] if len(ticker_tuple) > 3 else None
    eps_growth = ticker_tuple[4] if len(ticker_tuple) > 4 else None
    out = {'ticker': ticker, 'name': name, 'sector': sector,
           'price': None, 'avg_volume': None,
           'rev_growth': rev_growth, 'eps_growth': eps_growth,
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
BINARY_STREAMS = ('s1_news','s2_sponsor','s3_insider','s4_revisions','s5_volume')


def compute_tce_streams(ticker, market='us'):
    streams = {k: 0 for k in BINARY_STREAMS}

    try:
        import feedparser
        query = f'{ticker}+stock+OR+earnings'
        url = (f'https://news.google.com/rss/search?q={query}'
               f'&hl=en-US&gl=US&ceid=US:en')
        feed = feedparser.parse(url)
        recent_count = 0
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=14)
        for entry in feed.entries[:30]:
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    if dt.datetime(*entry.published_parsed[:6]) > cutoff:
                        recent_count += 1
            except Exception:
                continue
        streams['s1_news_count'] = recent_count
        if recent_count >= 3:
            streams['s1_news'] = 1
    except Exception:
        pass

    try:
        import yfinance as yf
        sym = f'{ticker}.KA' if market == 'psx' else ticker
        t = yf.Ticker(sym)
        h = t.history(period='3mo')
        if len(h) >= 30:
            vol_recent   = h['Volume'].iloc[-20:].mean()
            vol_baseline = h['Volume'].iloc[:30].mean()
            if vol_baseline > 0:
                ratio = vol_recent / vol_baseline
                streams['s5_volume_ratio'] = round(ratio, 2)
                if ratio > 1.3:
                    streams['s5_volume'] = 1
        if market == 'us':
            info = t.info
            if info:
                fwd = info.get('forwardEps')
                tra = info.get('trailingEps')
                if fwd and tra and tra > 0:
                    growth = (fwd - tra) / abs(tra)
                    streams['s4_revisions_pct'] = round(growth * 100, 1)
                    if growth > 0.05:
                        streams['s4_revisions'] = 1
    except Exception:
        pass

    if market == 'us':
        try:
            today = dt.date.today()
            start_dt = (today - dt.timedelta(days=90)).isoformat()
            url = (f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22'
                   f'&forms=4&dateRange=custom&startdt={start_dt}'
                   f'&enddt={today.isoformat()}')
            r = requests.get(url, headers={
                'User-Agent': 'Dashboard Scanner dashboard@example.com',
                'Accept': 'application/json'}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                hits = safe_get(data, 'hits', 'total', 'value', default=0)
                streams['s3_insider_count'] = hits
                if hits >= 2:
                    streams['s3_insider'] = 1
        except Exception:
            pass

    if streams.get('s1_news_count', 0) >= 8:
        streams['s2_sponsor'] = 1

    streams['total'] = sum(streams[k] for k in BINARY_STREAMS)
    return streams


def run_tce(candidates, market='us', max_count=20):
    log(f'=== TCE on {market.upper()} ({len(candidates)} candidates) ===')
    tce_results = []
    for c in candidates[:max_count]:
        ticker = c['ticker']
        try:
            streams = compute_tce_streams(ticker, market)
            score = streams['total']
            tier = 'HIGH' if score >= 4 else ('WATCH' if score >= 3 else 'IGNORE')
            tce_results.append({
                'ticker': ticker,
                'name':   c.get('name', ticker),
                'sector': c.get('sector', ''),
                'tce_score': score,
                'tier':   tier,
                'streams': streams,
            })
            fired = [k for k in BINARY_STREAMS if streams.get(k) == 1]
            log(f'  {ticker}: score={score} tier={tier} streams={fired}')
            time.sleep(YF_DELAY)
        except Exception as e:
            log(f'  · TCE {ticker}: {e}')

    tce_results.sort(key=lambda r: r['tce_score'], reverse=True)
    high  = sum(1 for r in tce_results if r['tier'] == 'HIGH')
    watch = sum(1 for r in tce_results if r['tier'] == 'WATCH')
    log(f'  TCE: {high} HIGH, {watch} WATCH out of {len(tce_results)} scanned')
    return tce_results


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
# Bank replacement weights (same total 162 — 22 pts removed, 22 pts bank metrics)
IM3_BANK_WEIGHTS = {k: v for k, v in IM3_WEIGHTS.items()}
# Remove N/A metrics for banks
for _bk in ('int_coverage', 'current_ratio', 'inv_turn', 'dro', 'fat', 'ccc'):
    IM3_BANK_WEIGHTS[_bk] = 0
# Add bank-specific metrics
IM3_BANK_WEIGHTS.update({
    'nim':   4,   # Net Interest Margin      (replaces int_coverage 2 + partial)
    'casa':  3,   # CASA ratio               (replaces inv_turn 3)
    'adr':   3,   # Advance-to-Deposit Ratio (replaces dro 3)
    'npl':   5,   # Non-Performing Loans     (replaces current_ratio 5)
    'car':   4,   # Capital Adequacy Ratio   (replaces fat 3 + ccc 3 = 6, split)
    # Total added = 19, total removed = 19 → bank max = 162
})

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

    # Zero out N/A bank metrics (Int Coverage, Current Ratio, Inv, DRO, FAT, CCC)
    for key in ('int_coverage', 'current_ratio', 'inv_turn', 'dro', 'fat', 'ccc'):
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

    # Recompute totals with bank weights
    total = sum(_pts(m['verdict'], W.get(m['key'], m['max']))
                for m in result['metrics'])
    max_s = sum(W.get(m['key'], m['max']) for m in result['metrics']
                if m['verdict'] != 'NA' or W.get(m['key'], 0) > 0)
    pct   = (total / 162 * 100) if total else 0  # always /162 for consistency
    grade = 'A' if pct >= 75 else 'B' if pct >= 60 else 'C' if pct >= 50 else 'FAIL'

    result['score'] = total
    result['max']   = 162
    result['pct']   = round(pct, 1)
    result['grade'] = grade
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

    try:
        data['tce_us'] = run_tce(data['us_candidates'], market='us',
                                  max_count=US_CANDIDATE_POOL)
    except Exception as e:
        log(f'US TCE crashed: {e}')
        data['meta']['errors'].append(f'us_tce: {e}')
        data['tce_us'] = EXISTING.get('tce_us', [])

    try:
        data['tce_psx'] = run_tce(data['psx_candidates'], market='psx', max_count=10)
    except Exception as e:
        log(f'PSX TCE crashed: {e}')
        data['meta']['errors'].append(f'psx_tce: {e}')
        data['tce_psx'] = EXISTING.get('tce_psx', [])

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

    try:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(data, f, indent=2, default=str)
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
    log('=' * 60)


if __name__ == '__main__':
    main()
