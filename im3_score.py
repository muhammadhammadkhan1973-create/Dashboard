"""
IM3 162-Point Stock Scorer — re-threaded off Yahoo (v2.9.1-sourcing).
=================================================================
v2.9.1: fixes two v2.9 misses found on the live run + makes deploys self-applying.
      (1) div_yield derivation was gated on `dy is None`, but TV reports many PSX payers'
          yield as 0.0 (e.g. HUBC, which pays ~6.3%) -> gate skipped -> stayed NA. Now fires
          on falsy (0 or None). (2) The eq0s "Shareholders' Equity" alias (v2.9) never reached
          cached psx-sa names because psx_history_cache.json served pre-alias parses; added a
          cache schema-version tag (_SA_CACHE_VER) so a parse/label change invalidates stale
          entries and forces a re-fetch. (3) IM3_VERSION constant stamped into every record so
          the daily.yml gate can re-score on a version change (no more manual force_im3).
v2.9: PSX div_yield + altman_z denominator-recovery (both 5-pt metrics, ~17 and ~13 names).
      (1) div_yield: read only TV's dividend field, so PSX names without it went NA even when they
          pay (HUBC). Now falls back to the parsed dividends-paid line / market cap, PSX-only,
          ACTUAL payers only (div_paid>0; non-payers stay NA), capped <50% to reject artefacts.
      (2) altman_z: NA on ~13 PSX names because stockanalysis labels total equity "Shareholders'
          Equity" (or "Total Equity") while the SA map only matched "Total Common Equity" -> eq0s
          empty -> eq00 None -> Altman None. Added those equity aliases (SA/PSX map only; US FMP
          path untouched). Also: Altman X4 falls back to total liabilities (ta-eq) for debt-free
          PSX names so a clean balance sheet isn't lost to a divide-by-zero. US path byte-for-byte
          unchanged (both fixes gated to is_psx / the SA parser).
v2.8: PSX CAGR fix. cagr() required yrs+1 (=6) points for a 5-yr CAGR; PSX history
      (stockanalysis / psx_financials.json) supplies 5 fiscal years -> rev/op/np CAGR
      went NA on EVERY PSX name (holdings included), capping the PSX denominator ~7pts
      below 162. cagr() is now length-adaptive: a 6-point series keeps the exact strict
      5-yr computation (US path byte-for-byte UNCHANGED), while a shorter series computes
      the longest CAGR it supports (>=2 periods), shortening past a non-positive base year.
      Effect: PSX non-banks/holdings now score their 3 CAGRs -> denominator rises toward
      the full 162 (e.g. OGDC 155 -> 162). US scoring is provably untouched.
v2.7: PSX Tier-3 — GENERALIZED full-162 engine. fetch_psx_history(ticker) scrapes
      the stockanalysis.com / S&P Global Market Intelligence statement pages
      (income / balance-sheet / cash-flow) for ANY PSX non-bank, maps the stable
      S&P row labels onto _HKEYS (millions -> raw PKR), and returns a newest-first
      history (source 'psx-sa', >=3yr revenue). Wired as the Tier-3 fallback in
      fetch_history AFTER psx_financials.json and BEFORE psx-tv-only, so the ~25
      non-holding PSX names now reach the full /162 instead of the TV single-period
      reduced score — mirroring the US screen. Banks are excluded (gated on
      _PSX_FORCE_BANK + sector, plus the upstream psx_history bank guard) and stay
      System B. Cached to psx_history_cache.json (TTL 7d). Fully guarded: any fetch/
      parse failure -> None -> psx-tv-only; never breaks the scorer. NETWORK on the
      runner only (sandbox can't reach stockanalysis.com) — the runner run confirms
      live coverage; the log prints "psx-sa (... Nyr)" per name and the reason on a
      miss. DEPLOY: commit im3_score.py to the repo ROOT (optionally add
      psx_history_cache.json to the daily.yml commit so it persists between runs).
v2.5: PSX Tier-2 broker-history layer. psx_history() reads psx_financials.json
      (broker-model / annual-report multi-year statements, newest-first PKR) and
      feeds fetch_history's PSX branch. When a name is in the file (>=3yr revenue)
      it gets FULL history -> the previously-NA multi-year metrics compute (CAGRs,
      CFO/EPS/FCF trends, Altman-Z / Beneish-M / Piotroski-F, CROIC, CCC, DCF) and
      the reduced PSX denominator self-expands toward 162. Names not in the file
      fall back to the TV single-period reduced score (graceful). US path unchanged.
      DEPLOY: commit im3_score.py + psx_financials.json to the repo ROOT. The
      daily.yml PSX step auto-picks-up via scorer-hash change. NOTE: the OGDC entry
      in psx_financials.json is an ILLUSTRATIVE TEMPLATE — replace with AKD/Topline/
      JS Global / annual-report figures before the OGDC score is trusted; the
      template validates the MACHINERY only.
v2.4: PSX support added (US path unchanged). A "PSX:" ticker prefix routes
      fundamentals to TradingView pakistan/scan (57/61 single-period columns
      confirmed populated), returns empty statement history (no SEC/Yahoo PSX
      coverage — broker layer pending), scores on a REDUCED denominator that
      excludes the NA history metrics (same mechanic as the bank branch), and
      uses a PKR risk-free (PAK_BOND=11.5%) for earnings-yield & DCF-EPS so PSX
      valuation isn't judged against the US bond. Validated: OGDC 62/83 (B). Bank probe: TV exposes 1/32 System-B inputs -> PSX banks score generic-reduced; full System-B via broker.

DEPLOY: commit to the repo ROOT (next to scanner.py / index.html), overwrite.
  - No re-run needed to validate; the scorer is verified by execution.
  - US scoring is byte-for-byte unchanged (all PSX logic is gated by the "PSX:" prefix).
  - PSX scores DO NOT appear automatically. They show up only after daily.yml's IM3
    step is wired to pass "PSX:" tickers (e.g. PSX:OGDC) AND a PSX IM3 dashboard tab
    is added. That wiring is the next build — it is not in this file.
v2.3: ROOT-CAUSE FIX for the MU/AVGO/AMSC regression. _sec_annual now uses
      LAST-write-wins within each concept (the restated comparative value,
      matching proven v2.0) and preferred-concept-wins across synonyms (keeps
      the NVDA/AMD/AMAT fix). v2.1's first-write-wins picked un-restated values
      and broke CAGRs/margins. The v2.2 duration-guard removal was a misdiagnosis
      (kept, harmless). 
v2.2: removed the v2.1 annual-duration guard (300-400d).
v2.1: SEC coverage broadened — _sec_annual merges annual values across
      synonym us-gaap concepts (modern ASC-606 revenue tag + legacy
      Revenues/SalesRevenueNet), accepts 10-K/20-F/40-F, and applies an
      ~annual duration guard. Pulls tech/large-caps (NVDA/AMD/AMAT-class)
      off the Yahoo backstop and onto free SEC history.

Data sourcing (the change in this version):
  * SINGLE-PERIOD ratios/valuation/margins/quality  -> TradingView america/scan
    (62 columns probe-confirmed). Fixes the dividend-units bug (TV gives a percent
    number -> converted to decimal) and the EV/EBITDA "bug" (TV ttm value used
    directly), and makes every ratio reflect the LIVE price, not a stale sheet.
  * MULTI-YEAR statements (CAGRs, trend metrics, Piotroski/Beneish/Altman, the DCF
    series) -> FMP /stable/  ->  SEC EDGAR companyfacts  ->  Yahoo, in that order,
    each guarded. YAHOO IS THE FINAL BACKSTOP, so coverage can never regress below
    the prior all-Yahoo behaviour: worst case == today, best case the CAGR gap closes.
  * Bond yield -> BOND constant (live FRED handled in the scanner; not needed here).

Scoring is UNCHANGED — this is a re-source, not a methodology change. Each metric keeps
its existing threshold/verdict logic; only where the value comes from changed. The two
deferred methodology calls (peer-relative P/E, level-vs-momentum trends) are untouched.
Grade A>=80%. Points are absolute out of 162; each metric carries weightage (max) + earned (pts).

Intrinsic-value engine (DCF EPS/FCF/Cash, Projected, Peter Lynch, MoS) computed in-code from
the fetched series + live price (no Sarmaaya inputs).

Usage:
    python im3_score.py MU
    python im3_score.py --json MU RBB MCB ...

Deps: requests (primary), yfinance (fallback only). Both already in daily.yml.
"""

import sys, math, time, os, json
import requests
from datetime import date

try:
    import yfinance as yf
except ImportError:
    yf = None  # Yahoo is now FALLBACK-ONLY; its absence must not kill a run TV+FMP/SEC can cover.

# ── CONSTANTS ────────────────────────────────────────────────────────────────
BOND = 0.043  # US 10Y ~4.3%
HDRS = {"User-Agent": "Mozilla/5.0 (im3-score)"}
# SEC asks for a descriptive UA + contact; this works for low-volume per-ticker reads.
HDRS_SEC = {"User-Agent": "IM3-Score research hammad.khan@airproducts.com"}
TV_URL = "https://scanner.tradingview.com/america/scan"
PAK_TV_URL = "https://scanner.tradingview.com/pakistan/scan"  # PSX single-period fundamentals
PAK_BOND = 0.115  # PKR risk-free ~ SBP policy rate; used for PSX earnings-yield & DCF-EPS
BANK_ERP  = 0.06                          # equity risk premium added to the risk-free for bank cost-of-equity
BANK_G_LR = {'psx': 0.10, 'us': 0.04}     # long-run nominal growth for banks (kept below COE)
FMP_BASE = "https://financialmodelingprep.com/stable"
FMP_KEY = os.environ.get("FMP_API_KEY", "")

WEIGHTS = {
    'rev_cagr':5,'op_cagr':1,'op_margin':5,'np_cagr':1,'np_margin':5,
    'tax_rate':3,'int_coverage':2,'de_ratio':5,'total_debt':3,
    'current_ratio':5,'cfo_trend':5,'net_cash':3,'ccfo_cpat':5,
    'nfa_turn':3,'roe':3,'eps_trend':5,'pe_ratio':5,'peg_ratio':5,
    'earn_yield':3,'pb_ratio':3,'graham_val':3,'ps_ratio':3,
    'div_yield':5,'ev_ebitda':3,'mos':5,'val_shareholders':5,
    'inv_turn':3,'dro':3,'fat':3,'fcf_trend':5,'croic':5,
    'fcf_sale':5,'fcf_cfo':3,'ccc':3,'altman_z':5,'beneish_m':5,
    'piotroski_f':10,'roic_wacc':3,'cash_share':5,'cash_debt':5,
}
BANK_ZERO  = ('int_coverage','current_ratio','inv_turn','dro','fat','ccc','nfa_turn',
              'de_ratio','total_debt','op_cagr','op_margin','fcf_trend','croic',
              'fcf_sale','fcf_cfo','cash_share','cash_debt','ev_ebitda','ps_ratio',
              'peg_ratio','graham_val','mos','val_shareholders','piotroski_f',
              'altman_z','beneish_m','roic_wacc')
BANK_EXTRA = {'nim':4,'casa':3,'adr':3,'npl':5,'car':4}

LABELS = {
    'rev_cagr':'Revenue CAGR 5yr','op_cagr':'Op Profit CAGR','op_margin':'Op Margin',
    'np_cagr':'Net Profit CAGR','np_margin':'Net Margin','tax_rate':'Tax Rate',
    'int_coverage':'Interest Coverage','de_ratio':'D/E Ratio','total_debt':'Total Debt Trend',
    'current_ratio':'Current Ratio','cfo_trend':'CFO Trend','net_cash':'Net Change in Cash',
    'ccfo_cpat':'cCFO vs cPAT (5yr)','nfa_turn':'NFA Turnover','roe':'ROE',
    'eps_trend':'EPS Trend','pe_ratio':'P/E vs Peer','peg_ratio':'PEG Ratio',
    'earn_yield':'Earnings Yield vs Bond','pb_ratio':'P/B Ratio',
    'graham_val':'Graham P/E x P/B','ps_ratio':'P/S Ratio','div_yield':'Dividend Yield',
    'ev_ebitda':'EV/EBITDA','mos':'Margin of Safety (DCF EPS)',
    'val_shareholders':'Value for Shareholders','inv_turn':'Inventory Turnover',
    'dro':'Days Receivables','fat':'Fixed Asset Turnover','ccc':'Cash Conversion Cycle',
    'fcf_trend':'FCF Trend','croic':'CROIC','fcf_sale':'FCF/Sale',
    'fcf_cfo':'FCF/CFO','cash_debt':'Cash/Debt','cash_share':'Cash/Share',
    'altman_z':'Altman Z-Score','beneish_m':'Beneish M-Score',
    'piotroski_f':'Piotroski F-Score','roic_wacc':'ROIC vs WACC',
    'nim':'Net Interest Margin','casa':'CASA Ratio','adr':'Advance/Deposit Ratio',
    'npl':'NPL Ratio','car':'Capital Adequacy Ratio',
}

SECTIONS = [
    ('Growth',    ['rev_cagr','op_cagr','op_margin','np_cagr','np_margin']),
    ('Stability', ['tax_rate','int_coverage','de_ratio','total_debt','current_ratio',
                   'cfo_trend','net_cash','ccfo_cpat','nfa_turn','roe']),
    ('Valuation', ['eps_trend','pe_ratio','peg_ratio','earn_yield','pb_ratio',
                   'graham_val','ps_ratio','div_yield','ev_ebitda','mos','val_shareholders']),
    ('Inventory', ['inv_turn','dro','fat','ccc']),
    ('Cash Flow', ['fcf_trend','croic','fcf_sale','fcf_cfo','cash_debt','cash_share']),
    ('Risk',      ['altman_z','beneish_m','piotroski_f','roic_wacc']),
    ('Bank',      ['nim','casa','adr','npl','car']),
]

# ── HELPERS (unchanged) ──────────────────────────────────────────────────────
def sdiv(a, b):
    try:
        if b is not None and b != 0:
            r = float(a) / float(b) if a is not None else None
            return None if r is not None and math.isnan(r) else r
    except: pass
    return None

def avg(lst, n=None):
    vals = [v for v in (lst[:n] if n else lst) if v is not None]
    return sum(vals)/len(vals) if vals else None

def cagr(s, yrs=5):
    """CAGR over up to `yrs` periods, adapting to the available history length.

    A strict `yrs`-year CAGR needs `yrs`+1 points. US history (FMP limit=6) supplies 6
    points, so the full 5-yr window is used and behaviour is UNCHANGED. PSX history from
    stockanalysis / psx_financials.json supplies 5 fiscal years (5 points), which the old
    `len(s) <= yrs` guard rejected -> rev/op/np CAGR went NA on every PSX name (the holdings
    too). Now, when the series is shorter than the full window, the longest CAGR the series
    supports (>= 2 periods) is computed instead, shortening the window past a non-positive
    base year. Returns None if no >= 2-period window with a positive base and latest value
    exists.

    US byte-for-byte guarantee: a 6-point series takes the first branch (s[yrs] vs s[0]),
    identical to the previous implementation; the adaptive branch only runs for < yrs+1 points.
    """
    if not s: return None
    b = s[0]
    if b is None or b <= 0: return None
    if len(s) > yrs:                         # full window available -> original strict 5-yr CAGR (US path)
        a = s[yrs]
        if a is None or a <= 0: return None
        return (b / a) ** (1.0 / yrs) - 1
    n = len(s) - 1                           # shorter series (PSX 5-yr): longest CAGR available
    while n >= 2:
        a = s[n]
        if a is not None and a > 0:
            return (b / a) ** (1.0 / n) - 1
        n -= 1
    return None

def trend(s3, s5, hi=True):
    if s3 is None or s5 is None: return 'NA'
    return 'GOOD' if (s3 > s5 if hi else s3 < s5) else 'WATCH'

def band(v, g, w, hi=True):
    if v is None: return 'NA'
    if hi:  return 'GOOD' if v >= g else ('WATCH' if v >= w else 'BAD')
    else:   return 'GOOD' if v <= g else ('WATCH' if v <= w else 'BAD')

def pts(verdict, max_p):
    return {'GOOD': max_p, 'WATCH': round(max_p*0.6), 'BAD': round(max_p*0.2)}.get(verdict, 0)

# ── Option C (peer-relative IM3) ───────────────────────────────────────────────
_SECTOR_MED_CACHE = None
def _sector_medians():
    """Per-GICS-sector medians {sector:{pe,op_margin,net_margin,roe}} written by the scanner
    (sector_medians.json). Absent -> {} -> every metric falls back to its absolute band, so the
    legacy /162 behaviour is byte-for-byte unchanged when the file is not present."""
    global _SECTOR_MED_CACHE
    if _SECTOR_MED_CACHE is None:
        try:    _SECTOR_MED_CACHE = json.load(open('sector_medians.json')) or {}
        except Exception: _SECTOR_MED_CACHE = {}
    return _SECTOR_MED_CACHE

def peer_band(v, med, hi=True, lo=0.7):
    """Peer-relative verdict vs a sector median. Returns None when there is no median or no value
    (the caller then uses the absolute band -> identical to legacy). hi=True (margins/ROE, higher
    better): GOOD >= median · WATCH >= median*lo · BAD below. hi=False (P/E, lower better):
    GOOD <= median · WATCH <= median*(2-lo) · BAD above."""
    if med is None or v is None or med <= 0:
        return None
    if hi:  return 'GOOD' if v >= med else ('WATCH' if v >= med*lo else 'BAD')
    else:   return 'GOOD' if v <= med else ('WATCH' if v <= med*(2-lo) else 'BAD')

def mk(key, verdict, W):
    mp = W.get(key, 0)
    return {'key': key, 'verdict': verdict, 'pts': pts(verdict, mp), 'max': mp}

def safe_nfat(rev, ppe):
    out = []
    for i in range(min(len(rev), len(ppe))):
        p0 = ppe[i]; p1 = ppe[i+1] if i+1 < len(ppe) else ppe[i]; r = rev[i]
        if p0 is not None and p1 is not None and r is not None:
            ap = (p0+p1)/2
            out.append(sdiv(r, ap) if ap else None)
        else: out.append(None)
    return out

def piotroski_f(ni, cfo, roa0, roa1, cfo_ta, d_lev, d_gm, d_at):
    s = 0
    checks = [
        (ni,    lambda v: v > 0),
        (cfo,   lambda v: v > 0),
        ((roa0,roa1), lambda v: v[0] is not None and v[1] is not None and v[0] > v[1]),
        ((cfo_ta,roa0), lambda v: v[0] is not None and v[1] is not None and v[0] > v[1]),
        (d_lev, lambda v: v <= 0),
        (d_gm,  lambda v: v >= 0),
        (d_at,  lambda v: v >= 0),
    ]
    for val, fn in checks:
        try:
            if val is not None and fn(val): s += 1
        except: pass
    return s

def beneish_m(r0,r1,ar0,ar1,gp0,gp1,ta0,ta1,pp0,pp1,sg0,sg1,dp0,dp1,ni,cfo,lt0,lt1):
    try:
        if any(v is None or v == 0 for v in [r0,r1,ta0,ta1]): return None
        if ni is None or cfo is None: return None
        dsri = ((ar0 or 0)/r0) / ((ar1 or 0.001)/r1)
        gmi  = ((gp1 or 0)/r1) / ((gp0 or 0.001)/r0) if gp0 and gp1 else None
        aqi  = (1-(((ar0 or 0)+(pp0 or 0))/ta0)) / (1-(((ar1 or 0)+(pp1 or 0))/ta1))
        sgi  = r0/r1
        depi = ((dp1 or 0)/((pp1 or 0)+(dp1 or 0.001))) / ((dp0 or 0.001)/((pp0 or 0)+(dp0 or 0.001))) if dp0 and dp1 and pp0 and pp1 else None
        sgai = ((sg0 or 0)/r0) / ((sg1 or 0.001)/r1)
        lvgi = ((lt0 or 0)/ta0) / ((lt1 or 0.001)/ta1)
        tata = (ni-cfo)/ta0
        coefs = [(0.920,dsri),(0.528,gmi),(0.404,aqi),(0.892,sgi),
                 (0.115,depi),(0.172,sgai),(4.679,lvgi),(-0.327,tata)]
        score = -4.84
        for c, v in coefs:
            if v is None: return None
            score += c*v
        return score
    except: return None

def altman_z(wc,re,ebit,eq,debt,ta):
    if any(v is None for v in [wc,re,ebit,eq,debt,ta]): return None
    if ta <= 0 or debt <= 0: return None
    return 6.56*(wc/ta)+3.26*(re/ta)+6.72*(ebit/ta)+1.05*(eq/debt)

def dcf_eps(eps, g_pct, bond=BOND):
    if eps is None or not bond: return None
    g = max(0.03, min(0.25, (g_pct or 5)/100))
    return eps * (8.5+2*g) * 4.4 / bond

def graham_iv(eps, bvps):
    if eps and bvps and eps > 0 and bvps > 0:
        return math.sqrt(22.5*eps*bvps)
    return None

def peter_lynch(peg, eg, eps):
    if peg is None or eps is None: return None
    return peg * max(0.05, min(0.20, (eg or 5)/100)) * eps

def dcf_2stage(base_ps, g_pct, n=10, r=0.12, g_term=0.04):
    """2-stage DCF on a per-share cash measure: n-year explicit growth stage discounted at
    r, then a Gordon terminal at g_term. Growth clamped 5-20% per the IM3 sheet note."""
    if not base_ps or base_ps <= 0: return None
    g = max(0.05, min(0.20, (g_pct or 5)/100))
    if r <= g_term: return None
    pv = 0.0; cf = base_ps
    for t in range(1, n+1):
        cf *= (1+g); pv += cf/(1+r)**t
    tv = cf*(1+g_term)/(r-g_term)
    return pv + tv/(1+r)**n

# ── DATA LAYER 1: TRADINGVIEW single-period fields ───────────────────────────
TV_FIELDS = [
    'description','sector','industry','market_cap_basic','close','currency',
    'price_earnings_ttm','price_book_ratio','price_sales_ratio','enterprise_value_ebitda_ttm',
    'gross_margin','operating_margin','net_margin','pre_tax_margin_ttm',
    'return_on_equity','return_on_invested_capital','return_on_assets',
    'debt_to_equity','current_ratio','quick_ratio',
    'dividends_yield','dividend_payout_ratio_ttm','dividends_per_share_fq',
    'total_debt','total_revenue_ttm','free_cash_flow_ttm','free_cash_flow_margin_ttm',
    'cash_n_short_term_invest_fq','ebitda_ttm','ebit_ttm',
    'earnings_per_share_diluted_ttm','earnings_per_share_basic_ttm','earnings_per_share_forecast_next_fq',
    'total_revenue_yoy_growth_ttm','earnings_per_share_diluted_yoy_growth_ttm',
    'beta_1_year','total_shares_outstanding_fundamental','interest_coverage',
    'total_current_assets_fq','total_current_liabilities_fq','total_assets_fq',
]
_TV_EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']

def _tv_post(symbol, columns, url=TV_URL):
    body = {"symbols": {"tickers": [symbol]}, "columns": columns}
    try:
        r = requests.post(url, json=body, headers=HDRS, timeout=20)
        if r.status_code != 200: return None
        data = r.json().get("data") or []
        return (data[0].get("d") or []) if data else None
    except Exception:
        return None

def tv_fetch(ticker):
    """One scan row -> {field: value}. PSX:* routes to pakistan/scan; else america/scan
    across the exchange prefixes. {} on miss."""
    tk = ticker.upper()
    if tk.startswith("PSX:"):
        d = _tv_post(tk, ['name'] + TV_FIELDS, url=PAK_TV_URL)
        if d and len(d) == len(TV_FIELDS) + 1:
            return dict(zip(TV_FIELDS, d[1:]))
        return {}
    for ex in _TV_EXCHANGES:
        d = _tv_post(f"{ex}:{tk}", ['name'] + TV_FIELDS)
        if d and len(d) == len(TV_FIELDS) + 1:
            return dict(zip(TV_FIELDS, d[1:]))
    d = _tv_post(tk, ['name'] + TV_FIELDS)  # bare fallback
    if d and len(d) == len(TV_FIELDS) + 1:
        return dict(zip(TV_FIELDS, d[1:]))
    return {}

def _tv_to_info(tv, ticker):
    """Adapt the TV row to the yfinance `info` keys the scorer reads, with unit fixes."""
    if not tv: return {}
    close = tv.get('close')
    pb    = tv.get('price_book_ratio')
    roe   = tv.get('return_on_equity')          # TV percent (39.82) -> decimal
    de    = tv.get('debt_to_equity')            # TV already decimal ratio (0.149)
    dy    = tv.get('dividends_yield')           # TV percent number (0.0555) -> decimal
    return {
        'longName': tv.get('description') or ticker,
        'shortName': tv.get('description') or ticker,
        'sector': tv.get('sector') or '—',
        'industry': tv.get('industry') or '',
        'currentPrice': close,
        'regularMarketPrice': close,
        'marketCap': tv.get('market_cap_basic'),
        'sharesOutstanding': tv.get('total_shares_outstanding_fundamental'),
        'trailingEps': tv.get('earnings_per_share_diluted_ttm') or tv.get('earnings_per_share_basic_ttm'),
        'trailingPE': tv.get('price_earnings_ttm'),
        'forwardPE': None,                       # TV exposes no clean ANNUAL forward PE -> pe_ratio uses the 25 default (peer-relative is the pending methodology upgrade)
        'pegRatio': None,                        # derived downstream as PE / avg-EPS-growth
        'priceToBook': pb,
        'priceToSalesTrailing12Months': tv.get('price_sales_ratio'),
        'dividendYield': (dy/100.0) if dy is not None else None,   # FIX: percent -> decimal (0.0555% -> 0.000555 -> WATCH, never GOOD)
        'enterpriseToEbitda': tv.get('enterprise_value_ebitda_ttm'),  # FIX: live ttm value used directly
        'returnOnEquity': (roe/100.0) if roe is not None else None,
        'returnOnInvestedCapital': tv.get('return_on_invested_capital'),
        'debtToEquity': de,                      # already decimal; the scorer's >10 guard won't trigger
        'currentRatio': tv.get('current_ratio'),
        'beta': tv.get('beta_1_year'),
        'bookValue': sdiv(close, pb),            # bvps = price / (price/book)
        'effectiveTaxRate': None,                # from history
        'interestCoverage': tv.get('interest_coverage'),  # often None on TV -> computed from history
        'netInterestMargin': None, 'casaRatio': None,
        'capitalAdequacyRatio': None, 'tier1CapitalRatio': None,
        '_tv': tv,
    }

# ── DATA LAYER 2: multi-year statements  FMP-stable -> SEC -> Yahoo ───────────
# Uniform history dict the scorer consumes. Series are newest-first, up to 6 entries.
_HKEYS = ['rev','op','np_','eps_s','cogs','sga','tax_exp','pbt','ebitda_s','int_exp','nii',
          'ppe','td','ltd','eq0s','ta_s','ca_s','cl_s','re_s','ar_s','ap_s','inv_s','cash_s',
          'sti_s','loans','deps','npl_s','cfo','fcf','ncc','dep','div_paid','buyback','issuance']

def _empty_hist():
    h = {k: [] for k in _HKEYS}; h['source'] = 'none'; return h

def _flist(rows, field, n=6):
    out = []
    for r in (rows or [])[:n]:
        v = r.get(field)
        try: out.append(float(v) if v is not None else None)
        except Exception: out.append(None)
    return out

# --- FMP /stable/ ---
def _fmp_get(endpoint, ticker):
    if not FMP_KEY: return None
    try:
        url = f"{FMP_BASE}/{endpoint}?symbol={ticker}&limit=6&apikey={FMP_KEY}"
        r = requests.get(url, headers=HDRS, timeout=25)
        if r.status_code != 200: return None
        js = r.json()
        rows = js if isinstance(js, list) else None
        if not rows or not isinstance(rows[0], dict): return None
        # newest-first
        rows.sort(key=lambda d: str(d.get('date') or d.get('fiscalYear') or ''), reverse=True)
        return rows
    except Exception:
        return None

def fmp_history(ticker):
    inc = _fmp_get('income-statement', ticker)
    bal = _fmp_get('balance-sheet-statement', ticker)
    cfs = _fmp_get('cash-flow-statement', ticker)
    if not inc or len(inc) < 3:            # require a usable income series, else this source failed
        return None
    h = _empty_hist(); h['source'] = 'fmp'
    h['rev']     = _flist(inc, 'revenue')
    h['op']      = _flist(inc, 'operatingIncome')
    h['np_']     = _flist(inc, 'netIncome')
    h['eps_s']   = _flist(inc, 'epsDiluted') or _flist(inc, 'eps')
    h['cogs']    = _flist(inc, 'costOfRevenue')
    h['sga']     = _flist(inc, 'sellingGeneralAndAdministrativeExpenses') or _flist(inc, 'generalAndAdministrativeExpenses')
    h['tax_exp'] = _flist(inc, 'incomeTaxExpense')
    h['pbt']     = _flist(inc, 'incomeBeforeTax')
    h['ebitda_s']= _flist(inc, 'ebitda')
    h['int_exp'] = _flist(inc, 'interestExpense')
    h['dep']     = _flist(inc, 'depreciationAndAmortization') or _flist(cfs, 'depreciationAndAmortization')
    if bal:
        h['ppe']  = _flist(bal, 'propertyPlantEquipmentNet')
        h['td']   = _flist(bal, 'totalDebt') or _flist(bal, 'longTermDebt')
        h['ltd']  = _flist(bal, 'longTermDebt')
        h['eq0s'] = _flist(bal, 'totalStockholdersEquity') or _flist(bal, 'totalEquity')
        h['ta_s'] = _flist(bal, 'totalAssets')
        h['ca_s'] = _flist(bal, 'totalCurrentAssets')
        h['cl_s'] = _flist(bal, 'totalCurrentLiabilities')
        h['re_s'] = _flist(bal, 'retainedEarnings')
        h['ar_s'] = _flist(bal, 'netReceivables') or _flist(bal, 'accountsReceivables')
        h['ap_s'] = _flist(bal, 'accountPayables') or _flist(bal, 'accountsPayables')
        h['inv_s']= _flist(bal, 'inventory')
        h['cash_s']= _flist(bal, 'cashAndCashEquivalents')
        h['sti_s']= _flist(bal, 'shortTermInvestments')
    if cfs:
        h['cfo']  = _flist(cfs, 'operatingCashFlow') or _flist(cfs, 'netCashProvidedByOperatingActivities')
        h['fcf']  = _flist(cfs, 'freeCashFlow')
        h['ncc']  = _flist(cfs, 'netChangeInCash')
        h['div_paid'] = [abs(v) if v is not None else None for v in _flist(cfs, 'dividendsPaid') or _flist(cfs, 'commonDividendsPaid')]
        h['buyback']  = [abs(v) if v is not None else None for v in _flist(cfs, 'commonStockRepurchased') or _flist(cfs, 'netStockRepurchase')]
        h['issuance'] = [abs(v) if v is not None else None for v in _flist(cfs, 'commonStockIssued') or _flist(cfs, 'netStockIssuance')]
    return h

# --- SEC EDGAR companyfacts ---
_SEC_TICKER_MAP = None
def _sec_cik(ticker):
    global _SEC_TICKER_MAP
    if _SEC_TICKER_MAP is None:
        try:
            r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HDRS_SEC, timeout=25)
            j = r.json() if r.status_code == 200 else {}
            _SEC_TICKER_MAP = {row['ticker'].upper(): str(row['cik_str']).zfill(10) for row in j.values()}
        except Exception:
            _SEC_TICKER_MAP = {}
    return _SEC_TICKER_MAP.get(ticker.upper())

_ANNUAL_FORMS = ('10-K', '20-F', '40-F')   # annual filings (incl. 10-K/A; foreign 20-F/40-F)
def _sec_annual(facts, concepts, want_per_share=False):
    """Merged newest-first annual series across synonym us-gaap concepts.

    Earlier-listed concept wins per fiscal year; later synonyms fill the gaps.
    This is the fix for tech/large-caps that report only 1-2 years under the
    modern ASC-606 revenue tag while older years live under 'Revenues' /
    'SalesRevenueNet' — taking the first concept alone returned <3 years and
    dropped the name to Yahoo. Annual = 10-K/20-F/40-F, fp=FY, and (for flow
    items carrying start+end) an ~365-day period so stray YTD rows are excluded.
    """
    merged = {}
    for c in (concepts if isinstance(concepts, list) else [concepts]):
        node = facts.get(c)
        if not node: continue
        units = node.get('units', {})
        ukey = ('USD/shares' if want_per_share else 'USD')
        rows = units.get(ukey) or (units.get(next(iter(units), '')) if units else None)
        if not rows: continue
        this_concept = {}
        for r in rows:
            form = r.get('form', '')
            if not any(form.startswith(f) for f in _ANNUAL_FORMS): continue
            if r.get('fp') != 'FY' or not r.get('fy'): continue
            fr = r.get('frame', '')
            if fr and 'Q' in fr: continue          # reject quarterly frames
            if r.get('val') is None: continue
            # LAST-write-wins within a concept: companyfacts lists each fiscal
            # year first as originally filed, then as a restated comparative in
            # later 10-Ks — the later (restated) value is the one to keep. This
            # matches the proven v2.0 behaviour; v2.1's first-write-wins picked
            # the un-restated value and broke MU/AVGO/AMSC CAGRs & margins.
            this_concept[int(r['fy'])] = r.get('val')
        for fy, val in this_concept.items():
            if fy not in merged:                   # preferred concept wins ACROSS concepts; synonyms fill gaps
                merged[fy] = val
    if merged:
        return [merged[y] for y in sorted(merged, reverse=True)][:6]
    return []

def sec_history(ticker):
    cik = _sec_cik(ticker)
    if not cik: return None
    try:
        r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                         headers=HDRS_SEC, timeout=45)
        if r.status_code != 200: return None
        facts = r.json().get('facts', {}).get('us-gaap', {})
    except Exception:
        return None
    if not facts: return None
    h = _empty_hist(); h['source'] = 'sec'
    h['rev']    = _sec_annual(facts, ['RevenueFromContractWithCustomerExcludingAssessedTax',
                                      'RevenueFromContractWithCustomerIncludingAssessedTax',
                                      'Revenues','SalesRevenueNet','SalesRevenueGoodsNet',
                                      'RevenuesNetOfInterestExpense'])
    if not h['rev'] or len([x for x in h['rev'] if x]) < 3:
        return None                            # no usable revenue -> treat SEC as a miss, fall to Yahoo
    h['op']     = _sec_annual(facts, ['OperatingIncomeLoss'])
    h['np_']    = _sec_annual(facts, ['NetIncomeLoss','ProfitLoss'])
    h['eps_s']  = _sec_annual(facts, ['EarningsPerShareDiluted','EarningsPerShareBasicAndDiluted'], want_per_share=True)
    h['cogs']   = _sec_annual(facts, ['CostOfRevenue','CostOfGoodsAndServicesSold'])
    h['sga']    = _sec_annual(facts, ['SellingGeneralAndAdministrativeExpense','GeneralAndAdministrativeExpense'])
    h['tax_exp']= _sec_annual(facts, ['IncomeTaxExpenseBenefit'])
    h['pbt']    = _sec_annual(facts, ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
                                      'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments'])
    h['int_exp']= _sec_annual(facts, ['InterestExpense','InterestExpenseDebt'])
    h['dep']    = _sec_annual(facts, ['DepreciationDepletionAndAmortization','DepreciationAmortizationAndAccretionNet','DepreciationAndAmortization'])
    h['ppe']    = _sec_annual(facts, ['PropertyPlantAndEquipmentNet'])
    h['td']     = _sec_annual(facts, ['LongTermDebtNoncurrent','LongTermDebt','DebtLongtermAndShorttermCombinedAmount'])
    h['ltd']    = _sec_annual(facts, ['LongTermDebtNoncurrent','LongTermDebt'])
    h['eq0s']   = _sec_annual(facts, ['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'])
    h['ta_s']   = _sec_annual(facts, ['Assets'])
    h['ca_s']   = _sec_annual(facts, ['AssetsCurrent'])
    h['cl_s']   = _sec_annual(facts, ['LiabilitiesCurrent'])
    h['re_s']   = _sec_annual(facts, ['RetainedEarningsAccumulatedDeficit'])
    h['ar_s']   = _sec_annual(facts, ['AccountsReceivableNetCurrent'])
    h['ap_s']   = _sec_annual(facts, ['AccountsPayableCurrent'])
    h['inv_s']  = _sec_annual(facts, ['InventoryNet'])
    h['cash_s'] = _sec_annual(facts, ['CashAndCashEquivalentsAtCarryingValue'])
    h['sti_s']  = _sec_annual(facts, ['ShortTermInvestments'])
    h['cfo']    = _sec_annual(facts, ['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'])
    capex       = _sec_annual(facts, ['PaymentsToAcquirePropertyPlantAndEquipment'])
    if h['cfo'] and capex:
        h['fcf'] = [(h['cfo'][i] - capex[i]) if i < len(capex) and h['cfo'][i] is not None and capex[i] is not None else None
                    for i in range(len(h['cfo']))]
    h['div_paid'] = [abs(v) if v is not None else None for v in _sec_annual(facts, ['PaymentsOfDividendsCommonStock','PaymentsOfDividends'])]
    h['buyback']  = [abs(v) if v is not None else None for v in _sec_annual(facts, ['PaymentsForRepurchaseOfCommonStock'])]
    h['issuance'] = [abs(v) if v is not None else None for v in _sec_annual(facts, ['ProceedsFromIssuanceOfCommonStock'])]
    # EBITDA not a us-gaap tag -> approximate op + dep so peter-lynch growth has a base
    if h['op'] and h['dep']:
        h['ebitda_s'] = [(h['op'][i] + (h['dep'][i] or 0)) if h['op'][i] is not None else None for i in range(len(h['op']))]
    return h

# --- Yahoo (FINAL BACKSTOP) ---
def _gs(df, keys, n=6):
    if df is None or df.empty: return []
    for k in (keys if isinstance(keys, list) else [keys]):
        for idx in df.index:
            if k.lower() in str(idx).lower():
                vals = []
                for v in df.loc[idx].values[:n]:
                    try:
                        fv = float(v); vals.append(None if math.isnan(fv) else fv)
                    except: vals.append(None)
                if any(v is not None for v in vals): return vals
    return []

def yahoo_history(ticker):
    if yf is None: return _empty_hist()
    try:    t = yf.Ticker(ticker)
    except: return _empty_hist()
    def gd(attr):
        try:
            df = getattr(t, attr)
            if df is not None and not df.empty:
                df = df.copy(); df.index = df.index.astype(str).str.lower().str.strip(); return df
        except: pass
        return None
    inc, bal, cf = gd('income_stmt'), gd('balance_sheet'), gd('cashflow')
    h = _empty_hist(); h['source'] = 'yahoo'
    h['rev']    = _gs(inc,['total revenue','totalrevenue','revenue'])
    h['op']     = _gs(inc,['operating income','ebit','operatingincome'])
    h['np_']    = _gs(inc,['net income','netincome'])
    h['eps_s']  = _gs(inc,['diluted eps','basic eps','eps diluted'])
    h['cogs']   = _gs(inc,['cost of revenue','cost of goods sold','costofrevenue'])
    h['sga']    = _gs(inc,['selling general administrative','sga','operatingexpenses'])
    h['tax_exp']= _gs(inc,['tax provision','income tax expense','incometaxexpense'])
    h['pbt']    = _gs(inc,['pretax income','income before tax','incomebeforetax'])
    h['ebitda_s']= _gs(inc,['ebitda','normalized ebitda'])
    h['int_exp']= _gs(inc,['interest expense','interestexpense'])
    h['nii']    = _gs(inc,['net interest income','netinterestincome'])
    h['ppe']    = _gs(bal,['net ppe','property plant equipment net','netppe','property plant and equipment'])
    h['td']     = _gs(bal,['long term debt','total debt','longtermdebt','totaldebt'])
    h['ltd']    = _gs(bal,['long term debt','longtermdebt'])
    h['eq0s']   = _gs(bal,['stockholders equity','total stockholders equity','stockholdersequity'])
    h['ta_s']   = _gs(bal,['total assets','totalassets'])
    h['ca_s']   = _gs(bal,['current assets','total current assets','currentassets'])
    h['cl_s']   = _gs(bal,['current liabilities','total current liabilities','currentliabilities'])
    h['re_s']   = _gs(bal,['retained earnings','retainedearnings'])
    h['ar_s']   = _gs(bal,['accounts receivable','net receivables','accountsreceivable'])
    h['ap_s']   = _gs(bal,['accounts payable','accountspayable'])
    h['inv_s']  = _gs(bal,['inventory','inventories'])
    h['cash_s'] = _gs(bal,['cash and cash equivalents','cash','cashandcashequivalents'])
    h['sti_s']  = _gs(bal,['short term investments','other short term investments'])
    h['loans']  = _gs(bal,['net loans','loans','totalloans'])
    h['deps']   = _gs(bal,['total deposits','deposits','totaldeposits'])
    h['npl_s']  = _gs(bal,['nonperforming loans','allowance for loan losses','allowanceforloanlosses'])
    h['cfo']    = _gs(cf,['operating cash flow','total cash from operating activities','cashfromoperations','operatingcashflow'])
    h['fcf']    = _gs(cf,['free cash flow','freecashflow'])
    h['ncc']    = _gs(cf,['changes in cash','net change in cash','netchangeincash'])
    h['dep']    = _gs(cf,['depreciation','depreciation and amortization','depreciationandamortization'])
    h['div_paid']= [abs(v) if v is not None else None for v in _gs(cf,['common stock dividend paid','cash dividends paid','dividends paid'])]
    h['buyback'] = [abs(v) if v is not None else None for v in _gs(cf,['repurchase of capital stock','common stock payments'])]
    h['issuance']= [abs(v) if v is not None else None for v in _gs(cf,['issuance of capital stock','common stock issuance'])]
    return h

# ── PSX generalized multi-year history (stockanalysis.com / S&P Global feed) ──
# v2.7: generalizes the broker-history layer to ANY PSX non-bank. Scrapes the three
# S&P-templated statement pages (income / balance-sheet / cash-flow), maps the stable
# row labels onto _HKEYS, scales millions -> raw PKR, and returns a newest-first
# history dict tagged 'psx-sa'. This lifts the ~25 non-holding PSX names from the
# TV single-period reduced score toward the full /162, exactly as the US screen does.
# Banks NEVER reach here (gated below + upstream bank guard). Fully guarded: any
# failure -> None -> caller falls back to psx-tv-only. Cached to psx_history_cache.json.
from html.parser import HTMLParser as _HTMLParser

_SA_BASE = "https://stockanalysis.com/quote/psx"
_SA_CACHE = "psx_history_cache.json"
_SA_TTL_DAYS = 7
_SA_CACHE_VER = "2.9.1"   # bump whenever the SA label maps / parse change, to invalidate stale cached parses
IM3_VERSION = "2.13.0"  # 2.13.0: (Option C — peer-relative IM3) op_margin / net_margin / ROE / P/E are now scored PEER-RELATIVE against this name's GICS-sector MEDIAN (from sector_medians.json, written by scanner v1.58.0's fetch_sector_medians) instead of fixed absolute bars: peer_band() gives GOOD>=median / WATCH>=median*0.7 for margins+ROE, and the P/E reference fpe is the sector-median P/E (was a flat 25 default) — this closes the largest gap vs the IM3 master and resolves the standing P/E divergence. GATED TO NON-BANKS (med={} when is_bank) so the validated IG2 bank model is provably untouched; and FALLBACK-PRESERVING — when sector_medians.json is absent OR the name's sector has no median (Yahoo-fallback US names + every PSX name, different taxonomy), peer_band returns None and the prior ABSOLUTE thresholds apply, so PSX + bank scoring and the no-file path are byte-for-byte unchanged (validated). ev_ebitda confirmed already fixed (live TTM used directly, line 389) — no change. # 2.12.0: partial-bank SCS fallback — for banks with no audited equity/ADR series (BOP/AKBL/BIPL), score_bank_ig2 now fills roe/adr/roa_trend from the live SCS snapshot (rec roe_scs/adr_scs/roa_trend_scs as fractions/ratio, written by the scanner to bank_ig2_overrides.json), lifting them off the reduced /32 denominator. Fill-MISSING-ONLY: a curated value already in bank_ig2_inputs.json is never overwritten, so the nine full-data workbook banks reproduce EXACTLY (validated). Audited annual data (when sourced) takes precedence over SCS. Bank valuation + non-bank scoring byte-for-byte unchanged. # 2.11.0: bank valuation — banks now carry a bank-appropriate IV block (bank_valuation): justified P/B (ROE-driven, the anchor) + Graham + dividend-discount, blended to a fair value with MoS vs live price; capped DCF-EPS shown as optimistic bound; Peter-Lynch/PEG + P/E/P/B/earnings-yield/div-yield ratios; DCF-FCF/Cash suppressed for banks (no conventional FCF). PSX cost-of-equity = PKR risk-free 11.5% + 6% ERP; long-run g 10% (psx)/4% (us), held below COE. Inputs are real (eps/equity/pat from the IG2 series + live price); reported DPS lights up DDM/div-yield when the annual-report parse supplies it, else DDM uses an implied sustainable payout. Quality scoring (score_bank_ig2) and non-bank scoring byte-for-byte UNCHANGED. # 2.10.1: partial-bank fix — 7 IG2 ratios (spread_ratio/net_margin/nim/npl_gl/ccfo_cpat/adr/idr) returned a fake GOOD/BAD when a source line item was MISSING (defaulted to 0); they now return NA so partial-data banks (e.g. BOP/AKBL/BIPL with no NPL/CFO/equity) score honestly on their applicable ratios only. The 9 full-data workbook banks reproduce EXACTLY as before (validated).     # 2.10.0: (Banking InvestoGenie 2.0 — faithful 24-ratio/48-pt bank model) banks now score on the documented Banking IG 2.0 model (score_bank_ig2), VALIDATED to reproduce Banking_InvestoGenie_Score_v2.xlsx exactly — all 9 PSX banks' totals and all 216 per-ratio cells (MEBL 45, FABL 43, UBL 41, ABL 38, MCB/BAFL/BAHL 37, HBL 36, NBP 26). 24 ratios across Growth(5)/Stability(13)/Business(6), Good/Avg/Bad = 2/1/0, /48. Inputs from bank_ig2_inputs.json (the workbook's FY2019-24 series for the 9 banks; update annually). Dual calibration: 'psx' (SBP/Sarmaaya bands, workbook-faithful) for PSX banks, 'us' (US-bank norms) ready-but-dormant until US bank inputs are supplied — US banks without IG2 inputs keep the prior System-B subset. NA ratios excluded from the denominator (partial banks score on applicable max). Grade follows the IG2 scale (Excellent>=75 -> A, Good>=60 -> B, Average>=45 -> C, Weak -> FAIL). Replaces the partial System-B label that was an over-claim. Non-bank scoring byte-for-byte unchanged. 2.9.4: (MCB CASA/CAR + System-B bank-ratio slot) the bank model now reads rec['_bank_system_b']={nim,casa,adr,npl,car} from psx_financials.json (percent or fraction, normalised by _ratio_norm) as an OVERRIDE for NIM/CASA/ADR/NPL/CAR whenever the free feed leaves them empty — free feeds carry no CASA/CAR for PSX (or US community) banks, so without this those metrics always scored NA. No fabrication: values come ONLY from the disclosure you place in the file; absent -> {} -> NA = prior behaviour. Non-bank scoring byte-for-byte unchanged. 2.9.3: A1 OPNP ratio threshold 1.5 -> 1.0 (D4, deck literal definition; see scanner v1.51.2 note) — PSX finalisation re-scores. 2.9.2: adds explosive_from_history() -> result["explosive"] (canonical G1/G2/A1/A2/C1/C3 + verdict from the parsed statements) so the PSX IM3 step FINALISES the explosive verdict on real operating/net/cash growth (same conditions as US, no eps/rev proxy). Scoring/grade math UNCHANGED. // scorer version stamped into every record; the daily.yml gate re-scores when this changes
# PSX banks -> System B only; never the non-bank multi-year engine (Altman/CCC/etc.).
_PSX_FORCE_BANK = ('MCB','UBL','HBL','NBP','MEBL','BAHL','BAFL','ABL','AKBL','FABL',
                   'HMB','BOP','SCBPL','BIPL','JSBL','SNBL','SBL','BOK','BML','SAMBA',
                   'AMBL','FCIBL','ESBL','ICIBL')
# SA row-label -> _HKEYS key. MONEY maps are scaled x1e6; RAW maps kept as-is (per-share).
_SA_INCOME_MONEY = {'Revenue':'rev','Cost of Revenue':'cogs','Selling, General & Admin':'sga',
                    'Operating Income':'op','Pretax Income':'pbt','Income Tax Expense':'tax_exp',
                    'Net Income':'np_','EBITDA':'ebitda_s','Interest Expense':'int_exp'}
_SA_INCOME_RAW   = {'EPS (Basic)':'eps_s'}
_SA_BAL_MONEY    = {'Property, Plant & Equipment':'ppe','Total Debt':'td','Long-Term Debt':'ltd',
                    'Total Common Equity':'eq0s',"Shareholders' Equity":'eq0s','Total Equity':'eq0s',
                    'Total Assets':'ta_s','Total Current Assets':'ca_s',
                    'Total Current Liabilities':'cl_s','Retained Earnings':'re_s','Receivables':'ar_s',
                    'Accounts Payable':'ap_s','Inventory':'inv_s','Cash & Equivalents':'cash_s',
                    'Trading Asset Securities':'sti_s'}
_SA_CF_MONEY     = {'Operating Cash Flow':'cfo','Free Cash Flow':'fcf',
                    'Depreciation & Amortization':'dep','Dividends Paid':'div_paid',
                    'Repurchase of Common Stock':'buyback','Issuance of Common Stock':'issuance'}

def _sa_num(s):
    """'63,524' -> 63524.0 ; '-'/'\u2014'/'' -> None ; '(1,234)' -> -1234.0"""
    if s is None: return None
    s = s.strip().replace(',', '').replace('\u2014', '').replace('\u2212', '-')
    if s in ('', '-', 'n/a', 'N/A'): return None
    neg = s.startswith('(') and s.endswith(')')
    if neg: s = s[1:-1]
    try:
        v = float(s); return -v if neg else v
    except Exception:
        return None

class _SATableParser(_HTMLParser):
    """Collect every <tr> as a list of cell texts (td/th), whitespace-collapsed."""
    def __init__(self):
        super().__init__(); self.rows = []; self._row = None; self._cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self._row = []
        elif tag in ('td', 'th') and self._row is not None: self._cell = []
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self._cell is not None:
            self._row.append(' '.join(''.join(self._cell).split())); self._cell = None
        elif tag == 'tr' and self._row is not None:
            if self._row: self.rows.append(self._row)
            self._row = None
    def handle_data(self, data):
        if self._cell is not None: self._cell.append(data)

def _sa_fetch_statement(url):
    """GET one statement page -> {row_label: [values aligned to ANNUAL FY columns]},
    newest-first, dropping any TTM/Current column. Returns None on any failure."""
    try:
        r = requests.get(url, headers=HDRS, timeout=25)
        if r.status_code != 200: return None
    except Exception:
        return None
    p = _SATableParser()
    try: p.feed(r.text)
    except Exception: return None
    hdr = next((row for row in p.rows if row and row[0].strip().lower().startswith('fiscal year')), None)
    if not hdr: return None
    periods = hdr[1:]
    keep = [i for i, lbl in enumerate(periods) if 'FY' in lbl.upper()]   # annual cols only (drop TTM)
    if not keep: return None
    out = {}
    for row in p.rows:
        if not row or len(row) < 2 or row[0].strip().lower().startswith('fiscal year'): continue
        label = row[0].strip(); vals = row[1:]
        if label in out: continue
        out[label] = [vals[i] if i < len(vals) else None for i in keep]
    return out

def fetch_psx_history(ticker, info=None):
    """Generalized PSX multi-year history from stockanalysis.com (the S&P Global
    Market Intelligence feed). Returns an _HKEYS dict (source 'psx-sa') for a PSX
    NON-BANK with >=3yr revenue, else None. Cached (TTL 7d). Never raises -> a miss
    degrades cleanly to the TV single-period score, never breaks the scorer."""
    bare = ticker.upper().split(':')[-1]
    if bare in _PSX_FORCE_BANK: return None
    sec = ((info or {}).get('sector', '') + ' ' + (info or {}).get('industry', '')).lower()
    if ('bank' in sec or 'bancorp' in sec) and not any(k in sec for k in ('insurance', 'asset management', 'investment', 'reit')):
        return None
    try: cache = json.load(open(_SA_CACHE))
    except Exception: cache = {}
    ent = cache.get(bare)
    if isinstance(ent, dict) and ent.get('h') and ent.get('cv') == _SA_CACHE_VER:
        try:
            if (time.time() - float(ent.get('ts', 0))) / 86400.0 < _SA_TTL_DAYS:
                return ent['h']
        except Exception:
            pass
    inc = _sa_fetch_statement(f"{_SA_BASE}/{bare}/financials/")
    if not inc: return None
    bal = _sa_fetch_statement(f"{_SA_BASE}/{bare}/financials/balance-sheet/") or {}
    cf  = _sa_fetch_statement(f"{_SA_BASE}/{bare}/financials/cash-flow-statement/") or {}
    h = _empty_hist()
    def put(table, mapping, money):
        for label, key in mapping.items():
            vals = table.get(label)
            if not vals: continue
            arr = [(None if (n := _sa_num(v)) is None else (n * 1e6 if money else n)) for v in vals]
            if key in ('int_exp', 'div_paid', 'buyback'):
                arr = [abs(x) if x is not None else None for x in arr]
            h[key] = arr
    put(inc, _SA_INCOME_MONEY, True); put(inc, _SA_INCOME_RAW, False)
    put(bal, _SA_BAL_MONEY, True); put(cf, _SA_CF_MONEY, True)
    if h.get('dep') and not h.get('ncc'): h['ncc'] = list(h['dep'])   # non-cash-charges proxy
    if len([x for x in h.get('rev', []) if x]) < 3:
        return None
    h['source'] = 'psx-sa'
    try:
        cache[bare] = {'ts': time.time(), 'cv': _SA_CACHE_VER, 'h': h}; json.dump(cache, open(_SA_CACHE, 'w'))
    except Exception:
        pass
    return h

def psx_history(ticker):
    """Tier-2 PSX history layer. Reads multi-year statements from psx_financials.json
    (broker-model / annual-report sourced, newest-first PKR series) and returns the
    _HKEYS history dict. Returns None if the name isn't in the file or has < 3 years of
    revenue, so unlisted names fall back to the TV single-period reduced score. With a
    history present, the previously-NA multi-year metrics (CAGRs, CFO/EPS/FCF trends,
    Altman-Z / Beneish-M / Piotroski-F, CROIC, CCC, DCF-FCF/Cash) compute, and the
    reduced PSX denominator self-expands toward the full 162 as NA shrinks."""
    sym = ticker.upper().split(':')[-1]
    try:
        store = json.load(open('psx_financials.json'))
    except Exception:
        return None
    rec = store.get(sym)
    if not isinstance(rec, dict):
        return None
    # Bank guard: a bank-tagged record must NOT be scored on the non-bank metric
    # engine (Altman-Z, current ratio, cash-conversion cycle, inventory/receivable
    # turns, gross margin are meaningless for a bank). Until the bank metric subset
    # is wired (reads _bank_system_b: NIM/CASA/ADR/NPL/CAR), a bank stays on the
    # TV single-period reduced score. Setting _bank_model_ready:true activates it.
    if rec.get('_is_bank') and not rec.get('_bank_model_ready'):
        return None
    h = _empty_hist()
    for k in _HKEYS:
        v = rec.get(k)
        if isinstance(v, list):
            out = []
            for x in v:
                try: out.append(float(x) if x is not None else None)
                except Exception: out.append(None)
            h[k] = out
    if len([x for x in h.get('rev', []) if x]) < 3:
        return None
    h['source'] = 'psx-broker'
    return h

def _psx_bank_ratios(ticker):
    """v2.9.4 (MCB CASA/CAR slot): read broker-disclosed bank ratios from psx_financials.json —
    rec['_bank_system_b'] = {nim,casa,adr,npl,car} (percent or fraction). Free feeds carry no
    NIM/CASA/CAR/NPL/ADR for PSX (or US community) banks, so without this the System-B inputs
    score NA. Returns {} when the file / record / sub-dict is absent. No fabrication — values come
    only from the disclosure you place in the file."""
    try:
        sym = str(ticker).upper().split(':')[-1]
        rec = json.load(open('psx_financials.json')).get(sym) or {}
        b = rec.get('_bank_system_b') or {}
        return b if isinstance(b, dict) else {}
    except Exception:
        return {}

def _ratio_norm(x):
    """Normalise a disclosed bank ratio to a fraction: 78 -> 0.78, 4.5 -> 0.045, 0.78 -> 0.78."""
    try: x = float(x)
    except Exception: return None
    return x / 100.0 if abs(x) > 1.5 else x

def fetch_history(ticker, log=True, info=None):
    """FMP-stable -> SEC -> Yahoo, first usable wins. Yahoo is the guaranteed backstop.
    PSX:* has no free statement source (SEC/Yahoo do not cover PSX). Tier-2: psx_history
    reads psx_financials.json (broker / annual-report) -> full history when present;
    Tier-3 (v2.7): fetch_psx_history scrapes the stockanalysis.com / S&P Global feed for
    ANY PSX non-bank -> full history -> /162; otherwise empty -> multi-year metrics go NA
    and the reduced PSX denominator excludes them (TV single-period reduced score)."""
    if ticker.upper().startswith("PSX:"):
        h = psx_history(ticker)
        if h:
            if log and not _json_mode: print("    history source: psx-broker (psx_financials.json)", flush=True)
            return h
        h = fetch_psx_history(ticker, info=info)   # Tier-3: generalized S&P feed -> full /162 for non-banks
        if h:
            if log and not _json_mode: print(f"    history source: psx-sa (stockanalysis/S&P Global, {len([x for x in h.get('rev',[]) if x])}yr)", flush=True)
            return h
        h = _empty_hist(); h['source'] = 'psx-tv-only'
        if log and not _json_mode: print("    history source: psx-tv-only (no broker/S&P financials for this name)", flush=True)
        return h
    for fn in (fmp_history, sec_history):
        try:
            h = fn(ticker)
        except Exception:
            h = None
        if h and h.get('rev') and len([x for x in h['rev'] if x]) >= 3:
            if log and not _json_mode: print(f"    history source: {h['source']}", flush=True)
            return h
    h = yahoo_history(ticker)
    if log and not _json_mode: print(f"    history source: {h.get('source')}", flush=True)
    return h

# ── MAIN SCORER ──────────────────────────────────────────────────────────────
_json_mode = False

def _exp_yoy(s):
    """YoY% from a most-recent-first statement series (s[0]=latest, s[1]=prior)."""
    if not s or len(s) < 2: return None
    a, b = s[0], s[1]
    if a is None or b is None or b == 0: return None
    return round((a - b) / abs(b) * 100, 1)

# Canonical explosive thresholds (Explosive Screen Specification v1.1) — kept in sync
# with scanner.py. Used to FINALISE the PSX explosive verdict from the statements IM3
# already parses, so PSX runs the SAME conditions as US (no eps/rev proxy).
EXP_G1_REV = 20.0; EXP_G2_OP = 15.0; EXP_A1_OP = 20.0; EXP_A1_RATIO = 1.0; EXP_A2_PBT = 1.0

def explosive_from_history(H):
    """Compute the canonical explosive conditions + verdict from the multi-year
    statement series (rev/op/np_/pbt/cfo). Returns a dict the workflow merges onto
    the explosive record so PSX is judged on real operating/net/cash growth."""
    rev = H.get('rev') or []; op = H.get('op') or []; np_ = H.get('np_') or []
    pbt = H.get('pbt') or []; cfo = H.get('cfo') or []
    rev_g = _exp_yoy(rev); op_g = _exp_yoy(op); np_g = _exp_yoy(np_); pbt_g = _exp_yoy(pbt)
    prev_op = op[1] if len(op) >= 2 else None
    g1 = None if rev_g is None else bool(rev_g > EXP_G1_REV)
    g2 = None if op_g  is None else bool(op_g  >= EXP_G2_OP)
    ratio = None
    if op_g is None or np_g is None:
        a1 = None
    elif (prev_op is not None and prev_op <= 0) or op_g <= 0:
        a1 = False
    else:
        ratio = round(np_g / op_g, 2) if op_g != 0 else None
        a1 = bool(op_g > EXP_A1_OP and ratio is not None and ratio > EXP_A1_RATIO)
    a2 = None if (pbt_g is None or op_g is None or op_g <= 0) else bool((pbt_g / op_g) > EXP_A2_PBT)
    c1 = None; c3 = None
    if cfo and np_ and cfo[0] is not None and np_[0] is not None:
        c1 = bool(cfo[0] >= np_[0])
    cfo_v = [x for x in cfo[:5] if x is not None]; np_v = [x for x in np_[:5] if x is not None]
    if cfo_v and np_v:
        c3 = bool(sum(cfo_v) >= sum(np_v))
    if rev_g is None and op_g is None and np_g is None:
        verdict = 'INSUFFICIENT DATA'
    elif op_g is not None and op_g <= 0:
        verdict = 'NOT EXPLOSIVE — OP declining'
    else:
        growth = bool(g1) and bool(g2); accel = bool(a1)
        cash_fail = (c1 is False and c3 is False)
        if   growth and accel and not cash_fail: verdict = 'EXPLOSIVE — both signals'
        elif growth and accel and cash_fail:     verdict = 'QUALITY-GROWTH (growth + accel, cash flow does not back earnings)'
        elif growth:                             verdict = 'QUALITY-GROWTH (growth, not accelerating)'
        elif accel:                              verdict = 'INFLECTION (accelerating off low base — verify)'
        else:                                    verdict = 'NOT EXPLOSIVE'
    growth_known = (g1 is not None and g2 is not None)
    return {'verdict': verdict, 'rev_growth': rev_g, 'op_growth': op_g, 'np_growth': np_g,
            'pbt_growth': pbt_g, 'op_np_ratio': ratio,
            'signal_a': (bool(g1) and bool(g2)) if growth_known else None, 'signal_b': a1,
            'conditions': {'g1': g1, 'g2': g2, 'a1': a1, 'a2': a2, 'c1': c1, 'c3': c3},
            'source': 'im3_statements'}


# ── Banking InvestoGenie 2.0 — faithful 24-ratio / 48-pt bank model.
# Validated against Banking_InvestoGenie_Score_v2.xlsx: reproduces all 9 PSX banks' scores and
# all 216 per-ratio cells exactly. Dual calibration: 'psx' (SBP/Sarmaaya bands, workbook-faithful)
# and 'us' (US-bank norms; dormant until US bank inputs are supplied). Inputs from bank_ig2_inputs.json.
IG2_CALIB = {
 'psx': {'nim_g':0.045,'nim_a':0.040,'npl_g':0.05,'npl_a':0.08,'car_min':11.5,'casa_g':80,'casa_a':75,
         'loan_cagr':0.12,'dep_g':0.16,'dep_a':0.135,'idr_g':0.78,'idr_a':0.64,'adr_lo':0.40,'adr_hi':0.55,
         'tax_lo':0.45,'tax_hi':0.60,'roe_g':0.20,'roe_a':0.15},
 'us':  {'nim_g':0.035,'nim_a':0.030,'npl_g':0.01,'npl_a':0.03,'car_min':10.5,'casa_g':40,'casa_a':30,
         'loan_cagr':0.06,'dep_g':0.06,'dep_a':0.04,'idr_g':0.40,'idr_a':0.25,'adr_lo':0.70,'adr_hi':0.95,
         'tax_lo':0.15,'tax_hi':0.30,'roe_g':0.12,'roe_a':0.08}}
IG2_RATIOS = ['markup_cagr','net_spread_cagr','pbp_cagr','pat_cagr','eps_trend','spread_ratio','net_margin',
 'eff_tax','nim','npl_trend','npl_gl','prov_gl_trend','cfo_trend','net_change_cash','ccfo_cpat','roe',
 'roa_trend','car','loan_cagr','deposit_cagr','casa','adr','idr','branches']
_IG2_INPUTS_CACHE = None
def _load_ig2_inputs():
    global _IG2_INPUTS_CACHE
    if _IG2_INPUTS_CACHE is None:
        try: _IG2_INPUTS_CACHE = json.load(open('bank_ig2_inputs.json'))
        except Exception: _IG2_INPUTS_CACHE = {}
        # SCS fallback layer (scanner writes bank_ig2_overrides.json from the live SCS snapshot):
        # fills ONLY still-missing fields (e.g. roe_scs/adr_scs/roa_trend_scs on partial banks);
        # a curated value already present in bank_ig2_inputs.json is never overwritten, so the
        # nine full-data workbook banks are structurally untouched.
        try:
            _ov = json.load(open('bank_ig2_overrides.json')) or {}
            for _sym, _o in _ov.items():
                _tgt = _IG2_INPUTS_CACHE.setdefault(_sym, {})
                for _k, _v in (_o or {}).items():
                    if _v is not None and _tgt.get(_k) is None: _tgt[_k] = _v
        except Exception: pass
    return _IG2_INPUTS_CACHE
def score_bank_ig2(rec, calib='psx'):
    C = IG2_CALIB.get(calib, IG2_CALIB['psx'])
    def yr(d): return {int(k): float(v) for k, v in (d or {}).items() if v is not None}
    def cg(s):
        a, e = s.get(2019), s.get(2024)
        return ((e/a)**(1/5)-1) if (a and a > 0 and e is not None) else None
    def av(s, ys):
        v = [s[y] for y in ys if y in s]; return sum(v)/len(v) if v else None
    def tr(s):
        a = av(s, [2022,2023,2024]); b = av(s, [2020,2021,2022,2023,2024]); return (a/b) if (a and b) else None
    def bb(x, g, a, inv=False):
        if x is None: return None
        return (2 if x <= g else 1 if x <= a else 0) if inv else (2 if x >= g else 1 if x >= a else 0)
    def vv(p): return 'GOOD' if p == 2 else 'WATCH' if p == 1 else 'BAD' if p == 0 else 'NA'
    g = {k: yr(rec.get(k)) for k in ('markup','net_spread','pbp','pat','eps','total_assets','gross_loans',
         'deposits','investments','equity','npl','provisions','cfo','branches')}
    car=rec.get('car_2024'); casa=rec.get('casa_2024'); tax=rec.get('tax_2024'); pbt=rec.get('pbt_2024'); ncc=rec.get('net_change_cash_2024')
    P = {}
    P['markup_cagr']=bb(cg(g['markup']),0.15,0.05)
    P['net_spread_cagr']=bb(cg(g['net_spread']),0.15,0.05)
    P['pbp_cagr']=bb(cg(g['pbp']),0.15,0.05)
    pc=cg(g['pat']); P['pat_cagr']=(2 if pc>=0.15 else 1 if pc>=0 else 0) if pc is not None else None
    e3,e5=av(g['eps'],[2022,2023,2024]),av(g['eps'],[2020,2021,2022,2023,2024]); P['eps_trend']=(2 if e3>e5 else 0) if (e3 and e5) else None
    P['spread_ratio']=bb(g['net_spread'][2024]/g['markup'][2024],0.50,0.30) if (g['markup'].get(2024) and g['net_spread'].get(2024) is not None) else None
    P['net_margin']=bb(g['pat'][2024]/g['markup'][2024],0.10,0.05) if (g['markup'].get(2024) and g['pat'].get(2024) is not None) else None
    t=(tax/pbt) if (tax and pbt) else None; P['eff_tax']=(2 if C['tax_lo']<=t<=C['tax_hi'] else 1 if (0.30<=t<C['tax_lo'] or C['tax_hi']<t<=0.70) else 0) if t is not None else None
    P['nim']=bb(g['net_spread'][2024]/g['total_assets'][2024],C['nim_g'],C['nim_a']) if (g['total_assets'].get(2024) and g['net_spread'].get(2024) is not None) else None
    nt=tr(g['npl']); P['npl_trend']=(2 if nt<1.0 else 1 if nt<=1.10 else 0) if nt is not None else None
    P['npl_gl']=bb(g['npl'][2024]/g['gross_loans'][2024],C['npl_g'],C['npl_a'],inv=True) if (g['gross_loans'].get(2024) and g['npl'].get(2024) is not None) else None
    pvgl={y:g['provisions'][y]/g['gross_loans'][y] for y in g['provisions'] if g['gross_loans'].get(y)}; ptr=tr(pvgl); P['prov_gl_trend']=(2 if ptr<1.0 else 0) if ptr is not None else None
    ct=tr(g['cfo']); P['cfo_trend']=(2 if ct>1.0 else 0) if ct is not None else None
    P['net_change_cash']=(2 if ncc>0 else 0) if ncc is not None else None
    cc=sum(g['cfo'].get(y,0) for y in [2020,2021,2022,2023,2024]); cp=sum(g['pat'].get(y,0) for y in [2020,2021,2022,2023,2024]); P['ccfo_cpat']=(2 if cc>cp else 0) if (cp and any(y in g['cfo'] for y in [2020,2021,2022,2023,2024])) else None
    roe=(g['pat'].get(2024,0)/g['equity'][2024]) if g['equity'].get(2024) else None
    if roe is None and rec.get('roe_scs') is not None: roe=rec['roe_scs']
    P['roe']=(2 if roe>=C['roe_g'] else 1 if roe>=C['roe_a'] else 0) if roe is not None else None
    roa={y:g['pat'][y]/g['total_assets'][y] for y in g['pat'] if g['total_assets'].get(y)}; rt=tr(roa)
    if rt is None and rec.get('roa_trend_scs') is not None: rt=rec['roa_trend_scs']
    P['roa_trend']=(2 if rt>1.0 else 1 if rt>=0.90 else 0) if rt is not None else None
    P['car']=(2 if car>C['car_min'] else 0) if car is not None else None
    P['loan_cagr']=(2 if cg(g['gross_loans'])>C['loan_cagr'] else 0) if cg(g['gross_loans']) is not None else None
    dc=cg(g['deposits']); P['deposit_cagr']=(2 if dc>=C['dep_g'] else 1 if dc>=C['dep_a'] else 0) if dc is not None else None
    P['casa']=(2 if casa>=C['casa_g'] else 1 if casa>=C['casa_a'] else 0) if casa is not None else None
    adr=(g['gross_loans'][2024]/g['deposits'][2024]) if (g['deposits'].get(2024) and g['gross_loans'].get(2024) is not None) else None
    if adr is None and rec.get('adr_scs') is not None: adr=rec['adr_scs']
    P['adr']=(2 if C['adr_lo']<=adr<=C['adr_hi'] else 1 if (0.30<=adr<C['adr_lo'] or C['adr_hi']<adr<=0.70) else 0) if adr is not None else None
    idr=(g['investments'][2024]/g['deposits'][2024]) if (g['deposits'].get(2024) and g['investments'].get(2024) is not None) else None; P['idr']=(2 if idr>=C['idr_g'] else 1 if idr>=C['idr_a'] else 0) if idr is not None else None
    bt=tr(g['branches']); P['branches']=(2 if bt>1.0 else 1 if bt>=0.99 else 0) if bt is not None else None
    metrics=[{'key':k,'verdict':vv(P.get(k)),'pts':(P.get(k) or 0),'max':(2 if P.get(k) is not None else 0)} for k in IG2_RATIOS]
    score=sum(m['pts'] for m in metrics); mx=sum(m['max'] for m in metrics)
    pct=round(100*score/mx,1) if mx else None
    rating='Excellent' if pct and pct>=75 else 'Good' if pct and pct>=60 else 'Average' if pct and pct>=45 else 'Weak'
    return {'score':score,'max':mx,'pct':pct,'is_bank':True,'model':'ig2','calib':calib,'rating':rating,'metrics':metrics}

def bank_valuation(ig2_in, price, calib='psx'):
    """Bank-appropriate intrinsic value from the IM3 engine, adapted for banks.
    Anchor = justified P/B = (ROE - g)/(COE - g) x BVPS (a bank earning above its cost
    of equity is worth a premium to book). Graham and a dividend-discount read cross-check
    it; a capped DCF-EPS is the optimistic bound (shown, not blended). DCF-FCF / DCF-Cash
    are deliberately NOT computed for a bank (no conventional free cash flow). All inputs
    are real: eps/equity/pat from the IG2 series (shares = pat/eps) + the live price."""
    def yr(d): return {int(k): float(v) for k, v in (d or {}).items() if v is not None}
    eps_s, equity, pat = yr(ig2_in.get('eps')), yr(ig2_in.get('equity')), yr(ig2_in.get('pat'))
    e24, q24, p24 = eps_s.get(2024), equity.get(2024), pat.get(2024)
    if not (price and e24 and e24 > 0 and q24 and q24 > 0 and p24):
        return None
    shares = p24 / e24
    bvps   = q24 / shares
    roe    = p24 / q24
    ys = sorted(eps_s); n = len(ys) - 1
    cagr = ((eps_s[ys[-1]] / eps_s[ys[0]]) ** (1.0 / n) - 1.0) if (n > 0 and eps_s[ys[0]] > 0) else 0.0
    rf  = PAK_BOND if calib == 'psx' else BOND
    coe = rf + BANK_ERP
    g   = min(BANK_G_LR.get(calib, 0.04), coe - 0.02)            # long-run growth, held below COE
    # Graham number (uses EPS + book — valid for banks)
    graham = graham_iv(e24, bvps)
    # DCF-EPS: capped 2-stage (5y growth capped 15%, terminal g), discounted at the bank COE
    gh = min(max(cagr, 0.0), 0.15); e = e24; v = 0.0
    for i in range(1, 6): e *= (1 + gh); v += e / ((1 + coe) ** i)
    v += (e * (1 + g)) / (coe - g) / ((1 + coe) ** 5)
    dcf_eps_v = v
    # Justified P/B (ROE-driven) — the primary bank anchor
    just_pb = (roe - g) / (coe - g) if coe > g else None
    just_iv = just_pb * bvps if just_pb else None
    # Dividend discount: reported DPS if disclosed (annual report), else implied sustainable payout
    dps = ig2_in.get('dps_2024'); div_yield = None
    if dps:
        d1 = float(dps) * (1 + g); div_yield = float(dps) / price; dps_src = 'reported'
    else:
        payout = max(0.0, 1.0 - g / roe) if roe > 0 else 0.0
        d1 = e24 * payout * (1 + g); dps_src = 'implied'
    ddm = d1 / (coe - g) if coe > g else None
    # Peter Lynch / PEG fair ratio (~1 = fairly priced on growth; <1 cheap)
    peg = (price / e24) / (cagr * 100) if cagr > 0 else None
    # Fair value = blend of the bank-valid anchors (Graham + justified-P/B + DDM)
    anchors = [x for x in [graham, just_iv, ddm] if x and x > 0]
    fair = sum(anchors) / len(anchors) if anchors else None
    def _mos(x): return round((x - price) / x * 100, 1) if (x and price) else None
    return {
        'bank_method':    True,
        'dcf_eps':        round(dcf_eps_v, 2) if dcf_eps_v else None,
        'graham':         round(graham, 2) if graham else None,
        'justified_pb':   round(just_pb, 2) if just_pb else None,
        'justified_iv':   round(just_iv, 2) if just_iv else None,
        'ddm':            round(ddm, 2) if ddm else None,
        'ddm_src':        dps_src,
        'peter_lynch':    round(peg, 2) if peg else None,
        'composite':      round(fair, 2) if fair else None,
        'mos_pct':        _mos(fair),
        'roe_pct':        round(roe * 100, 1),
        'coe_pct':        round(coe * 100, 1),
        'g_pct':          round(g * 100, 1),
        'pe':             round(price / e24, 2),
        'pb':             round(price / bvps, 2),
        'peg':            round(peg, 2) if peg else None,
        'earn_yield_pct': round(e24 / price * 100, 2),
        'div_yield_pct':  round(div_yield * 100, 2) if div_yield else None,
        'dcf_fcf': None, 'dcf_cash': None,   # not meaningful for a bank
    }

def score_ticker(ticker):
    if not _json_mode:
        print(f"  Fetching {ticker}...", flush=True)

    is_psx = ticker.upper().startswith("PSX:")
    eff_bond = PAK_BOND if is_psx else BOND
    bare = ticker.upper().split(":")[-1]   # strip PSX: for force-list checks

    tv = tv_fetch(ticker)
    info = _tv_to_info(tv, ticker)
    if not info:  # TV miss -> Yahoo info backstop so behaviour can't regress
        if yf is not None:
            try: info = yf.Ticker(ticker).info or {}
            except: info = {}
        else: info = {}

    H = fetch_history(ticker, info=info)

    rev, op, np_, eps_s = H['rev'], H['op'], H['np_'], H['eps_s']
    if not eps_s and info.get('trailingEps'): eps_s = [info['trailingEps']]
    cogs, sga, tax_exp, pbt = H['cogs'], H['sga'], H['tax_exp'], H['pbt']
    ebitda_s, int_exp, nii  = H['ebitda_s'], H['int_exp'], H['nii']
    ppe, td, ltd, eq0s      = H['ppe'], H['td'], H['ltd'], H['eq0s']
    ta_s, ca_s, cl_s, re_s  = H['ta_s'], H['ca_s'], H['cl_s'], H['re_s']
    ar_s, ap_s, inv_s       = H['ar_s'], H['ap_s'], H['inv_s']
    cash_s, sti_s           = H['cash_s'], H['sti_s']
    loans, deps, npl_s      = H['loans'], H['deps'], H['npl_s']
    cfo, fcf, ncc, dep      = H['cfo'], H['fcf'], H['ncc'], H['dep']
    div_paid, buyback, issuance = H['div_paid'], H['buyback'], H['issuance']

    # Bank detection
    sec = (info.get('sector','') + ' ' + info.get('industry','')).lower()
    BANK_INDUSTRIES = ('banks—regional','banks—diversified','savings institutions',
                       'banks - regional','banks - diversified','savings institution',
                       'thrift','bancorp','bancshares','bancshare','banks')
    NONBANK_OVERRIDE = ('software','technology','biotech','pharmaceutical',
                        'lending','marketplace','business development',
                        'asset management','investment','insurance','reit',
                        'capital corp','lending tree')
    is_bank = (any(k in sec for k in BANK_INDUSTRIES)
               and not any(k in sec for k in NONBANK_OVERRIDE))
    FORCE_NONBANK = ('TREE','SSSS','AVAH','VITL','PAYS','WGS')
    FORCE_BANK    = ('RBB','MCB','LOB','AROW','WSBF','BWB','EGBN','BWFG','NBN',
                     'SFST','PGC','BMRC','NFBK','PCB','KRNY','WTBA','BCML',
                     'PDLB','FSBC','CHMG','ALRS')
    if bare in FORCE_NONBANK: is_bank = False
    if bare in FORCE_BANK:    is_bank = True
    # PSX banks use Banking Investo Genie 2.0 calibration (Sarmaaya Week-6 / SBP bands):
    # NIM 4.5%, NPL <=5%/<=8%, CAR >=11.5% (SBP req), tax 45-60% (statutory ~54%),
    # ADR contextual (low/moderate good when T-bills attractive, >70% bad). US banks
    # keep the generic System-B (US-tuned) bands.
    psx_bank = is_bank and is_psx
    # Banking IG 2.0: PSX banks with workbook inputs score on the faithful 24-ratio /48 model
    # (us calibration ready but dormant until US bank inputs are supplied).
    _ig2_result = None
    if is_bank:
        _ig2_in = _load_ig2_inputs().get(bare)
        if _ig2_in:
            _ig2_result = score_bank_ig2(_ig2_in, 'psx' if psx_bank else 'us')

    W = dict(WEIGHTS)
    if is_bank:
        for k in BANK_ZERO: W[k] = 0
        W.update(BANK_EXTRA)

    price  = info.get('currentPrice') or info.get('regularMarketPrice')
    shares = info.get('sharesOutstanding')
    mktcap = info.get('marketCap')

    # ── derived scalars (None-safe)
    def v0(s): return s[0] if s else None
    def v1(s): return s[1] if len(s) > 1 else None
    td0=v0(td); eq00=v0(eq0s); ta0=v0(ta_s); ta1=v1(ta_s)
    ca0=v0(ca_s); cl0=v0(cl_s); re0=v0(re_s); op0=v0(op)
    ni0=v0(np_); cfo0=v0(cfo); fcf0=v0(fcf); eps0=v0(eps_s) or info.get('trailingEps')
    tc0 = (v0(cash_s) or 0) + (v0(sti_s) or 0) if cash_s or sti_s else info.get('_tv',{}).get('cash_n_short_term_invest_fq')
    tax_r = sdiv(v0(tax_exp), v0(pbt)) or info.get('effectiveTaxRate')

    ic = None
    if td0 is not None or eq00 is not None:
        ic_val = (td0 or 0) + (eq00 or 0) - (tc0 or 0)
        ic = ic_val if ic_val != 0 else None

    nfat = safe_nfat(rev, ppe)

    def egrates(s):
        out = []
        for i in range(min(4, len(s)-1)):
            a,b = s[i], s[i+1]
            if a and b and b != 0: out.append((a-b)/abs(b)*100)
        return out

    avg_eg  = avg(egrates(eps_s))   or 5.0
    avg_eg2 = avg(egrates(ebitda_s)) or 5.0

    metrics = []

    # ── GROWTH
    # Option C: this name's sector median for peer-relative P/E / margins / ROE. Gated to
    # NON-BANKS (banks score on the separate validated IG2 model — provably untouched). When no
    # median for the sector (e.g. Yahoo-fallback US names + all PSX names, different taxonomy) the
    # peer_band() calls below return None and the absolute thresholds apply -> legacy behaviour.
    med = {} if is_bank else (_sector_medians().get(info.get('sector')) or {})
    for key, ser in [('rev_cagr',rev),('op_cagr',op),('np_cagr',np_)]:
        c = cagr(ser, 5)
        metrics.append(mk(key, 'GOOD' if c is not None and c>=0.15 else 'WATCH' if c is not None else 'NA', W))
    opm = sdiv(op0, v0(rev)); npm = sdiv(ni0, v0(rev))
    if is_psx and info.get('_tv'):   # use TV single-period margins (percent->decimal) when history is absent
        _tvr = info['_tv']
        if opm is None and _tvr.get('operating_margin') is not None: opm = _tvr['operating_margin']/100.0
        if npm is None and _tvr.get('net_margin') is not None:       npm = _tvr['net_margin']/100.0
    metrics.append(mk('op_margin', peer_band(opm, med.get('op_margin')) or band(opm, 0.12, 0.06), W))
    metrics.append(mk('np_margin', peer_band(npm, med.get('net_margin')) or band(npm, 0.08, 0.03), W))

    # ── STABILITY
    if psx_bank:
        # Pakistan bank statutory ~54%; 45-60% healthy, far-below flags aggressive planning.
        tax_v = ('GOOD'  if tax_r and 0.45 <= tax_r <= 0.60 else
                 'WATCH' if tax_r and (0.35 <= tax_r < 0.45 or 0.60 < tax_r <= 0.65) else
                 'BAD'   if tax_r else 'NA')
        metrics.append(mk('tax_rate', tax_v, W))
    else:
        thresh = 0.25 if is_bank else 0.21
        metrics.append(mk('tax_rate', 'GOOD' if tax_r and tax_r>=thresh else 'WATCH' if tax_r else 'NA', W))
    int_cov = info.get('interestCoverage') or sdiv(op0, abs(v0(int_exp)) if v0(int_exp) else None)
    metrics.append(mk('int_coverage', 'NA' if is_bank else band(int_cov, 5.0, 2.0), W))
    de = info.get('debtToEquity')
    if de: de = de/100 if de > 10 else de
    metrics.append(mk('de_ratio', 'GOOD' if de is not None and de<0.5 else 'WATCH' if de is not None and de<1.0 else 'BAD' if de is not None else 'NA', W))
    metrics.append(mk('total_debt', trend(avg(td,3), avg(td,5), hi=False), W))
    cr = info.get('currentRatio')
    metrics.append(mk('current_ratio', 'NA' if is_bank else ('GOOD' if cr and cr>=1.5 else 'WATCH' if cr and cr>=1.0 else 'BAD' if cr else 'NA'), W))
    metrics.append(mk('cfo_trend', trend(avg(cfo,3), avg(cfo,5)), W))
    ncc0=v0(ncc); ncc1=v1(ncc)
    metrics.append(mk('net_cash', 'GOOD' if ncc0 and ncc1 and ncc0>ncc1 else 'WATCH' if ncc0 and ncc0>0 else 'BAD' if ncc0 is not None else 'NA', W))
    cum_cfo = sum(v for v in cfo[:6] if v); cum_np = sum(v for v in np_[:6] if v)
    metrics.append(mk('ccfo_cpat', 'GOOD' if cum_cfo and cum_np and cum_cfo>cum_np else 'WATCH' if cum_cfo and cum_np else 'NA', W))
    metrics.append(mk('nfa_turn', trend(avg(nfat,3), avg(nfat,5)), W))
    metrics.append(mk('roe', peer_band(info.get('returnOnEquity'), med.get('roe')) or band(info.get('returnOnEquity'), 0.20, 0.10), W))

    # ── VALUATION
    metrics.append(mk('eps_trend', trend(avg(eps_s,3), avg(eps_s,5)), W))
    pe = info.get('trailingPE') or info.get('forwardPE')
    fpe = med.get('pe') or info.get('forwardPE') or 25   # Option C: peer (sector-median) P/E is the reference; else forward/25
    metrics.append(mk('pe_ratio', 'GOOD' if pe and pe>0 and pe<=fpe*1.1 else 'WATCH' if pe and pe>0 and pe<=fpe*1.3 else 'BAD' if pe and pe>0 else 'NA', W))
    # PEG: TV exposes none and Yahoo is demoted -> standard definition PE / avg-EPS-growth.
    peg = info.get('pegRatio') or (sdiv(pe, avg_eg) if pe and avg_eg and avg_eg>0 else None)
    metrics.append(mk('peg_ratio', 'GOOD' if peg and peg<1.0 else 'WATCH' if peg and peg<=1.5 else 'BAD' if peg else 'NA', W))
    ey = sdiv(1, pe)
    metrics.append(mk('earn_yield', 'GOOD' if ey and ey>eff_bond else 'BAD' if ey else 'NA', W))
    pb = info.get('priceToBook')
    metrics.append(mk('pb_ratio', 'GOOD' if pb and pb<1.5 else 'WATCH' if pb and pb<3.0 else 'BAD' if pb else 'NA', W))
    gv = (pe*pb) if pe and pb else None
    metrics.append(mk('graham_val', 'GOOD' if gv and gv<22.5 else 'BAD' if gv else 'NA', W))
    ps = info.get('priceToSalesTrailing12Months')
    metrics.append(mk('ps_ratio', 'GOOD' if ps and ps<1.5 else 'WATCH' if ps and ps<3.0 else 'BAD' if ps else 'NA', W))
    dy = info.get('dividendYield')
    if not dy and is_psx:
        # Derive from the parsed dividends-paid line (total dividends / market cap) when the TV
        # dividend field is absent OR reported as 0 (TV gives 0.0 for many PSX payers, e.g. HUBC).
        # Fills ACTUAL payers only (div_paid>0) — genuine non-payers stay NA, never fabricated.
        # Sanity-capped at 50% to reject statement data artefacts.
        dp0 = v0(div_paid)
        if dp0 and mktcap and mktcap > 0:
            _dyd = dp0 / mktcap
            if 0 < _dyd < 0.5: dy = _dyd
    metrics.append(mk('div_yield', 'GOOD' if dy and dy>=0.04 else 'WATCH' if dy else 'NA', W))
    ev_eb = info.get('enterpriseToEbitda')
    metrics.append(mk('ev_ebitda', 'GOOD' if ev_eb and ev_eb<10 else 'WATCH' if ev_eb and ev_eb<15 else 'BAD' if ev_eb else 'NA', W))

    iv_eps_v = dcf_eps(eps0, avg_eg, bond=eff_bond)
    mos = sdiv((iv_eps_v-price), iv_eps_v) if iv_eps_v and price else None
    metrics.append(mk('mos', 'GOOD' if mos and mos>=0.25 else 'WATCH' if mos and mos>=0 else 'BAD' if mos is not None else 'NA', W))

    # ── VALUE FOR SHAREHOLDERS = net shareholder yield (div + net buyback)/mktcap, else EPS-momentum proxy
    vsh_verdict = None
    nsy = None
    if mktcap and (v0(div_paid) is not None or v0(buyback) is not None):
        ret_cash = (v0(div_paid) or 0) + max(0.0, (v0(buyback) or 0) - (v0(issuance) or 0))
        nsy = sdiv(ret_cash, mktcap)
        if nsy is not None:
            vsh_verdict = 'GOOD' if nsy >= 0.05 else 'WATCH' if nsy >= 0.02 else 'BAD'
    if vsh_verdict is None:
        vsh_verdict = trend(avg(eps_s,3), avg(eps_s,5))   # fallback proxy
    metrics.append(mk('val_shareholders', vsh_verdict, W))

    # ── INVENTORY
    if is_bank:
        for k in ('inv_turn','dro','fat','ccc'): metrics.append(mk(k,'NA',W))
    else:
        it = safe_nfat(rev, inv_s)
        metrics.append(mk('inv_turn', trend(avg(it,3), avg(it,5)), W))
        dro = [sdiv(ar_s[i] if i<len(ar_s) else None, rev[i])*365
               if rev and i<len(rev) and rev[i] and sdiv(ar_s[i] if i<len(ar_s) else None, rev[i]) is not None
               else None for i in range(min(len(rev),6))]
        metrics.append(mk('dro', trend(avg(dro,3), avg(dro,5), hi=False), W))
        metrics.append(mk('fat', trend(avg(nfat,3), avg(nfat,5)), W))
        base = cogs if cogs else rev
        dsi = [sdiv(inv_s[i] if i<len(inv_s) else None, base[i] if i<len(base) and base[i] else None)*365
               if sdiv(inv_s[i] if i<len(inv_s) else None, base[i] if i<len(base) and base[i] else None) is not None
               else None for i in range(min(len(rev),6))]
        dpo = [sdiv(ap_s[i] if i<len(ap_s) else None, base[i] if i<len(base) and base[i] else None)*365
               if sdiv(ap_s[i] if i<len(ap_s) else None, base[i] if i<len(base) and base[i] else None) is not None
               else None for i in range(min(len(rev),6))]
        ccc_s = [(dro[i] or 0)+(dsi[i] or 0)-(dpo[i] or 0)
                 if i<len(dro) and i<len(dsi) and i<len(dpo)
                 and dro[i] is not None and dsi[i] is not None and dpo[i] is not None
                 else None for i in range(min(len(rev),6))]
        metrics.append(mk('ccc', trend(avg(ccc_s,3), avg(ccc_s,5), hi=False), W))

    # ── CASHFLOW
    metrics.append(mk('fcf_trend', trend(avg(fcf,3), avg(fcf,5)), W))
    croic_v = sdiv(fcf0, ic)
    metrics.append(mk('croic', 'GOOD' if croic_v and croic_v>0.15 else 'WATCH' if croic_v and croic_v>0.05 else 'BAD' if croic_v is not None else 'NA', W))
    fcf_m = sdiv(fcf0, v0(rev))
    metrics.append(mk('fcf_sale', 'GOOD' if fcf_m and fcf_m>0.20 else 'WATCH' if fcf_m and fcf_m>0.08 else 'BAD' if fcf_m is not None else 'NA', W))
    fcf_cfo_s = [sdiv(fcf[i], cfo[i]) for i in range(min(len(fcf),len(cfo),6)) if cfo and i<len(cfo) and cfo[i]]
    metrics.append(mk('fcf_cfo', trend(avg(fcf_cfo_s,3), avg(fcf_cfo_s,5)), W))
    cd = sdiv(tc0, td0)
    metrics.append(mk('cash_debt', 'GOOD' if cd and cd>1.0 else 'WATCH' if cd and cd>0.3 else 'BAD' if cd is not None else 'NA', W))
    cps = sdiv(tc0, shares)
    metrics.append(mk('cash_share', 'GOOD' if cps and price and cps>price*0.1 else 'WATCH' if cps else 'NA', W))

    # ── RISK
    wc = (ca0-cl0) if ca0 is not None and cl0 is not None else None
    # Altman Z'' X4 = equity / liabilities. Default to total debt (US path unchanged); for PSX names
    # that are effectively debt-free (td<=0/None) fall back to total liabilities (ta-eq) so a strong
    # balance sheet isn't lost to a divide-by-zero.
    _liab0 = (ta0 - eq00) if (ta0 is not None and eq00 is not None) else None
    _az_den = td0
    if is_psx and (td0 is None or td0 <= 0) and _liab0 and _liab0 > 0:
        _az_den = _liab0
    az = altman_z(wc, re0, op0, eq00, _az_den, ta0)
    metrics.append(mk('altman_z', 'GOOD' if az and az>2.6 else 'WATCH' if az and az>1.1 else 'BAD' if az is not None else 'NA', W))

    gp_s = [((rev[i] or 0)-(cogs[i] if cogs and i<len(cogs) else 0)) for i in range(len(rev)) if rev[i] is not None] if rev else []
    bm = beneish_m(
        v0(rev),v1(rev), v0(ar_s) or 0,v1(ar_s) or 0,
        v0(gp_s) or 0,gp_s[1] if len(gp_s)>1 else 0,
        ta0,ta1, v0(ppe) or 0,v1(ppe) or 0,
        v0(sga) or 0,v1(sga) or 0, v0(dep) or 0,v1(dep) or 0,
        ni0,cfo0, v0(ltd) or 0,v1(ltd) or 0)
    metrics.append(mk('beneish_m', 'GOOD' if bm and bm<-2.22 else 'WATCH' if bm and bm<-1.78 else 'BAD' if bm is not None else 'NA', W))

    roa0_v  = sdiv(ni0, ta0);  roa1_v = sdiv(v1(np_), ta1)
    cfo_ta  = sdiv(cfo0, ta0)
    lt0 = (v0(ltd) or td0); lt1 = (v1(ltd) or v1(td))
    d_lev_a = sdiv(lt0, ta0); d_lev_b = sdiv(lt1, ta1)
    d_lev = (d_lev_a - d_lev_b) if d_lev_a is not None and d_lev_b is not None else None
    gm0 = sdiv((v0(rev) or 0)-(v0(cogs) or 0), v0(rev)) if rev else None
    gm1 = sdiv((v1(rev) or 0)-(v1(cogs) or 0), v1(rev)) if len(rev)>1 else None
    at0 = sdiv(v0(rev), ta0) if rev else None; at1 = sdiv(v1(rev), ta1) if len(rev)>1 else None
    pf  = piotroski_f(ni0, cfo0, roa0_v, roa1_v, cfo_ta, d_lev,
                      (gm0-gm1) if gm0 is not None and gm1 is not None else None,
                      (at0-at1) if at0 is not None and at1 is not None else None)
    metrics.append(mk('piotroski_f', 'GOOD' if pf>=6 else 'WATCH' if pf>=3 else 'BAD', W))

    beta  = info.get('beta')
    ke    = eff_bond + (beta or 1.0)*0.055
    v_tot = (td0 or 0) + (eq00 or 0)
    wacc  = ((eq00 or 0)/v_tot*ke + (td0 or 0)/v_tot*0.06*(1-(tax_r or 0.21))) if v_tot else ke
    nopat = (op0*(1-(tax_r or 0.21))) if op0 else None
    roic  = sdiv(nopat, ic)
    metrics.append(mk('roic_wacc', 'GOOD' if roic is not None and roic>wacc else 'WATCH' if roic is not None else 'NA', W))

    # ── BANK EXTRAS
    if is_bank:
        _bank_ovr = _psx_bank_ratios(ticker)          # v2.9.4: broker disclosure (MCB CASA/CAR etc.)
        nim_v = sdiv(v0(nii), ta0) or info.get('netInterestMargin') or _ratio_norm(_bank_ovr.get('nim'))
        nim_vd = band(nim_v, 0.045, 0.035) if psx_bank else band(nim_v, 0.04, 0.03)
        metrics.append({'key':'nim','verdict':nim_vd,'pts':pts(nim_vd,4),'max':4})
        casa_v = info.get('casaRatio') or _ratio_norm(_bank_ovr.get('casa'))
        cv = band(casa_v,0.80,0.70) if casa_v else 'NA'
        metrics.append({'key':'casa','verdict':cv,'pts':pts(cv,3),'max':3})
        adr_v = sdiv(v0(loans), v0(deps))
        if adr_v is None: adr_v = _ratio_norm(_bank_ovr.get('adr'))
        if psx_bank:
            # Contextual (Banking IG 2.0 / SBP): when T-bills attractive (high-rate regime),
            # prudent banks park in govt paper -> low/moderate ADR is GOOD, very high is the risk.
            av = 'GOOD' if adr_v and adr_v<=0.60 else 'WATCH' if adr_v and adr_v<=0.70 else 'BAD' if adr_v else 'NA'
        else:
            av = 'GOOD' if adr_v and 0.40<=adr_v<=0.60 else 'WATCH' if adr_v and (0.30<=adr_v<0.40 or 0.60<adr_v<=0.70) else 'BAD' if adr_v else 'NA'
        metrics.append({'key':'adr','verdict':av,'pts':pts(av,3),'max':3})
        npl_v = sdiv(v0(npl_s), v0(loans))
        if npl_v is None: npl_v = _ratio_norm(_bank_ovr.get('npl'))
        if psx_bank:
            nv = band(npl_v,0.05,0.08,hi=False) if npl_v else 'NA'   # PSX structurally higher
        else:
            nv = band(npl_v,0.03,0.05,hi=False) if npl_v else 'NA'
        metrics.append({'key':'npl','verdict':nv,'pts':pts(nv,5),'max':5})
        car_v = info.get('capitalAdequacyRatio') or info.get('tier1CapitalRatio') or _ratio_norm(_bank_ovr.get('car'))
        if car_v and car_v > 1: car_v = car_v/100
        cv2 = ((band(car_v,0.13,0.115) if psx_bank else band(car_v,0.18,0.15)) if car_v else 'NA')  # SBP req 11.5%
        metrics.append({'key':'car','verdict':cv2,'pts':pts(cv2,4),'max':4})
        bank_inputs = {'nii': v0(nii), 'total_assets': ta0, 'gross_loans': v0(loans),
                       'deposits': v0(deps), 'npl_found': npl_v is not None,
                       'casa_found': casa_v is not None, 'car_found': car_v is not None}
    else:
        bank_inputs = None

    # ── INTRINSIC VALUES (in-code engine; no Sarmaaya inputs)
    bvps    = info.get('bookValue')
    iv_eps  = dcf_eps(eps0, avg_eg, bond=eff_bond)
    iv_gr   = graham_iv(eps0, bvps)
    iv_pl   = peter_lynch(peg, avg_eg2, eps0)
    fcf_ps      = sdiv(fcf0, shares)
    cash_ps     = sdiv(tc0,  shares)
    g_fcf       = avg(egrates(fcf))    or 5.0
    g_cash      = avg(egrates(cash_s)) or 5.0
    avg6_fcf_ps = sdiv(avg(fcf),    shares)
    avg6_cash_ps= sdiv(avg(cash_s), shares)
    iv_dcf_fcf  = dcf_2stage(fcf_ps,      g_fcf)
    iv_dcf_cash = dcf_2stage(cash_ps,     g_cash)
    iv_proj_fcf = dcf_2stage(avg6_fcf_ps, g_fcf)
    iv_proj_cash= dcf_2stage(avg6_cash_ps,g_cash)
    def _mos(v): return sdiv((v-price), v)*100 if v and price else None
    iv_fcf_val  = avg([v for v in [iv_dcf_fcf, iv_eps, iv_proj_fcf, iv_pl] if v and v>0])
    iv_cash_val = avg([v for v in [iv_dcf_cash,iv_eps, iv_proj_cash,iv_pl] if v and v>0])
    iv_fcf_mos  = _mos(iv_fcf_val)
    iv_cash_mos = _mos(iv_cash_val)
    ivs     = [v for v in [iv_eps,iv_gr,iv_pl,iv_dcf_fcf,iv_dcf_cash] if v and v > 0]
    iv_comp = avg(ivs)
    mos_pct = _mos(iv_eps)

    if is_bank or is_psx:
        # Reduced denominator: NA metrics (e.g. PSX multi-year history not yet sourced,
        # or bank-zeroed lines) are excluded from the max rather than scored as zero,
        # so a name isn't penalised for data the engine cannot yet see.
        applicable = [x for x in metrics if W.get(x['key'], 0) > 0]
        total   = sum(pts(x['verdict'], W.get(x['key'], 0)) for x in applicable)
        max_s   = sum(W.get(x['key'], 0) for x in applicable if x['verdict'] != 'NA')
        n_meas  = sum(1 for x in applicable if x['verdict'] != 'NA')
        pct     = round(total / max_s * 100, 1) if max_s else 0.0
        bank_coverage = round(n_meas / len(applicable), 2) if applicable else 0
        max_out = max_s
    else:
        total = sum(x['pts'] for x in metrics)
        pct   = round(total/162*100, 1)
        bank_coverage = None
        max_out = 162
    if _ig2_result is not None:        # Banking IG 2.0 overrides the generic bank score
        metrics       = _ig2_result['metrics']
        total         = _ig2_result['score']
        max_out       = _ig2_result['max']
        pct           = _ig2_result['pct'] or 0.0
        bank_coverage = 'IG2 24-ratio (%s)' % _ig2_result['calib']
        grade = 'A' if pct>=75 else 'B' if pct>=60 else 'C' if pct>=45 else 'FAIL'
    else:
        grade = 'A' if pct>=80 else 'B' if pct>=60 else 'C' if pct>=50 else 'FAIL'

    _bank_iv = bank_valuation(_ig2_in, price, 'psx' if psx_bank else 'us') if (_ig2_result is not None) else None
    return {
        'ticker': ticker, 'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector','—'), 'is_bank': is_bank, 'is_psx': is_psx, 'price': price,
        'score': total, 'pct': pct, 'grade': grade, 'metrics': metrics, 'max': max_out, 'ver': IM3_VERSION,
        'bank_coverage': bank_coverage, 'bank_inputs': bank_inputs,
        'src': {'fund': info.get('_tv') and 'tv' or 'yahoo', 'hist': H.get('source')},
        'explosive': explosive_from_history(H),
        'piotroski': pf, 'altman_z': round(az,2) if az else None,
        'beneish_m': round(bm,2) if bm else None,
        'shareholder_yield_pct': round(nsy*100,2) if nsy is not None else None,
        'iv': _bank_iv if _bank_iv else {
            'dcf_eps':       round(iv_eps,2)       if iv_eps       else None,
            'dcf_fcf':       round(iv_dcf_fcf,2)   if iv_dcf_fcf   else None,
            'dcf_cash':      round(iv_dcf_cash,2)  if iv_dcf_cash  else None,
            'proj_fcf':      round(iv_proj_fcf,2)  if iv_proj_fcf  else None,
            'proj_cash':     round(iv_proj_cash,2) if iv_proj_cash else None,
            'graham':        round(iv_gr,2)        if iv_gr        else None,
            'peter_lynch':   round(iv_pl,2)        if iv_pl        else None,
            'intrinsic_fcf': round(iv_fcf_val,2)   if iv_fcf_val   else None,
            'intrinsic_cash':round(iv_cash_val,2)  if iv_cash_val  else None,
            'composite':     round(iv_comp,2)      if iv_comp      else None,
            'mos_pct':       round(mos_pct,1)      if mos_pct is not None else None,
            'mos_fcf_pct':   round(iv_fcf_mos,1)   if iv_fcf_mos  is not None else None,
            'mos_cash_pct':  round(iv_cash_mos,1)  if iv_cash_mos is not None else None,
        },
    }

# ── DISPLAY ──────────────────────────────────────────────────────────────────
SYM = {'GOOD':'[OK]','WATCH':'[~~]','BAD':'[!!]','NA':'[--]'}

def print_result(r):
    fill = int(r['pct']/100*40); bar = '#'*fill + '-'*(40-fill)
    print(); print('='*65)
    print(f"  {r['ticker']}  {r['name']}")
    print(f"  {r['sector']}" + ('  [BANK]' if r['is_bank'] else '') + f"   (src: {r['src']['fund']}/{r['src']['hist']})")
    if r['price']: print(f"  Price: ${r['price']}")
    print('='*65)
    print(f"  SCORE : {r['score']} / {r['max']}  ({r['pct']}%)")
    print(f"  GRADE : {r['grade']}  [{bar}]")
    if r['altman_z']:  print(f"  Altman Z   : {r['altman_z']}")
    if r['beneish_m']: print(f"  Beneish M  : {r['beneish_m']}")
    print(f"  Piotroski F: {r['piotroski']} / 7")
    if r.get('shareholder_yield_pct') is not None: print(f"  Shareholder yield: {r['shareholder_yield_pct']}%")
    iv = r['iv']; print(); print('  INTRINSIC VALUES:')
    if iv['dcf_eps']:    print(f"    DCF EPS     : ${iv['dcf_eps']}")
    if iv['peter_lynch']:print(f"    Peter Lynch : ${iv['peter_lynch']}")
    if iv['composite']:  print(f"    Composite   : ${iv['composite']}")
    if iv['mos_pct'] is not None:
        lbl = 'SAFE' if iv['mos_pct']>=25 else 'SLIM' if iv['mos_pct']>=0 else 'OVERVALUED'
        print(f"    MoS         : {iv['mos_pct']}%  [{lbl}]")
    mdict = {mx['key']: mx for mx in r['metrics']}
    for sec_name, keys in SECTIONS:
        if sec_name == 'Bank' and not r['is_bank']: continue
        sec_m = [mdict[k] for k in keys if k in mdict]
        if not sec_m: continue
        sp = sum(x['pts'] for x in sec_m); sm = sum(x['max'] for x in sec_m)
        print(); print(f"  -- {sec_name}  {sp}/{sm} --")
        for mx in sec_m:
            print(f"    {SYM.get(mx['verdict'],'[--]')}  {LABELS.get(mx['key'], mx['key']):<38}  {mx['pts']:2}/{mx['max']:2}")
    print(); print('='*65)

# ── ENTRY POINT ──────────────────────────────────────────────────────────────
def main():
    import json as _json
    args = sys.argv[1:]
    json_mode = '--json' in args
    args = [a for a in args if a != '--json']
    global _json_mode
    _json_mode = json_mode
    if not args:
        if json_mode: print('[]'); return
        print('\nIM3 162-Point Stock Scorer (re-threaded: TV + FMP/SEC/Yahoo)')
        print('Usage: python im3_score.py MU   |   python im3_score.py --json MU RBB ...')
        inp = input('Enter ticker(s): ').strip().upper()
        args = inp.split()
    tickers = [a.upper() for a in args if not a.startswith('--')]
    if not json_mode:
        print(f"\nScoring: {', '.join(tickers)}\n")
    results = []
    for tk in tickers:
        try:
            r = score_ticker(tk)
            results.append(r)
            if not json_mode: print_result(r)
        except Exception as e:
            if json_mode: results.append({'ticker': tk, 'error': str(e)})
            else:
                import traceback; traceback.print_exc(); print(f"\n  ERROR {tk}: {e}")
        if len(tickers) > 1 and not json_mode: time.sleep(1)
    if json_mode:
        print(_json.dumps(results, default=str)); return
    if len(results) > 1:
        print('\nSUMMARY')
        print(f"{'#':<4}{'Ticker':<8}{'Score':<10}{'%':<8}{'Grade':<7}{'Bank':<6}MoS%")
        print('-'*50)
        for i, r in enumerate(sorted(results, key=lambda x: x.get('pct',0), reverse=True), 1):
            if r.get('error'): continue
            mos = r['iv']['mos_pct']
            print(f"{i:<4}{r['ticker']:<8}{r['score']:<10}{r['pct']:<8}{r['grade']:<7}{'Y' if r['is_bank'] else '':<6}{str(mos)+'%' if mos is not None else '—'}")
        print()

if __name__ == '__main__':
    main()
