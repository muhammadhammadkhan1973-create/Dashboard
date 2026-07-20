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

# A1 (DEN): a non-bank name whose measurable metrics fall below this fraction of its
# applicable scorecard is flagged 'partial' and cannot earn a top (A) grade — so a thin
# young name is scored on what we CAN see (NA excluded) yet a near-empty one can't show
# an inflated A on a handful of metrics. Banks are exempt (their IG2 model is validated).
COVERAGE_FLOOR = 0.60

# v2.16.0 (STRENGTH/VALUATION SPLIT): for NON-BANKS the headline grade is computed on business
# STRENGTH only (Growth/Stability/Inventory/Cashflow/Risk + the EPS-trend momentum signal). The
# cheapness / capital-return metrics below are still scored, but as a SEPARATE valuation INDICATOR
# (coloured on the dashboard) — they never drag the grade down or downgrade a strong business. A
# fast, strong, "expensive-looking" early name now reads strong, with its rich valuation shown as
# context beside it. Banks are EXEMPT (their validated IG2 / System-B grade is unchanged).
VALUATION_KEYS = ('pe_ratio','peg_ratio','earn_yield','pb_ratio','graham_val','ps_ratio',
                  'div_yield','ev_ebitda','mos','val_shareholders')

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
    # v2.20.0 (Fix A): 3-tier. GOOD = improving (3yr avg beats 5yr); WATCH = roughly flat;
    # BAD = clearly deteriorating (>10% the wrong way), so a declining cash-flow/EPS/turnover
    # trend can finally be marked down instead of getting the 60% WATCH floor. The BAD tier
    # fires ONLY on a positive 5yr base (magnitude is meaningful) — a negative/zero base stays
    # WATCH (sign-safe) and missing data stays NA (young names never penalised).
    if s3 is None or s5 is None: return 'NA'
    improving = (s3 > s5) if hi else (s3 < s5)
    if improving: return 'GOOD'
    if s5 is None or s5 <= 0: return 'WATCH'
    ratio = s3 / s5
    if hi:   return 'WATCH' if ratio >= 0.90 else 'BAD'   # >10% below the 5yr average
    else:    return 'WATCH' if ratio <= 1.10 else 'BAD'   # >10% worse (debt / debtor-days rising)

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
    """Graham revised intrinsic value: V = EPS x (8.5 + 2g) x 4.4 / Y, with g and Y BOTH in
    PERCENT (the 4.4 is the 1962 baseline AAA yield). g (expected annual EPS growth) is capped
    at 15 — Graham's own caution against extrapolating high growth — and Y is the AAA/risk-free
    yield in percent. Returns None for missing inputs or non-positive EPS (no earnings -> no
    earnings-power IV)."""
    if eps is None or eps <= 0 or not bond: return None
    g = max(0.0, min(15.0, g_pct if g_pct is not None else 5.0))   # percent, capped at 15
    Y = bond * 100.0 if bond < 1 else bond                          # yield in percent
    return eps * (8.5 + 2.0 * g) * 4.4 / Y

def graham_iv(eps, bvps):
    if eps and bvps and eps > 0 and bvps > 0:
        return math.sqrt(22.5*eps*bvps)
    return None

def peter_lynch(eg, eps):
    """Peter Lynch PEG=1 fair value: a fairly-priced grower trades at a P/E equal to its
    earnings-growth rate, so fair price = min(growth%, 25) x EPS. Lynch treats growth above
    ~25% as something you shouldn't pay a matching multiple for, so it's capped. Requires a
    positive EPS and positive growth; otherwise the method doesn't apply (None)."""
    if eps is None or eps <= 0 or eg is None or eg <= 0: return None
    return min(eg, 25.0) * eps

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

def _sec_ifrs(ifrs):
    """IFRS-taxonomy twin of the us-gaap statement builder, for FOREIGN private
    issuers (20-F / 40-F filed under IFRS — miners, ADRs like Barrick/GAU/ASM)
    whose companyfacts carry an 'ifrs-full' block instead of 'us-gaap'. Same
    _sec_annual machinery (annual forms, FY, newest-first, currency-unit
    fallback), only the element NAMES change to the IFRS taxonomy. Returns the
    same _HKEYS dict tagged source 'sec-ifrs', or None (<3yr revenue / empty) so
    the caller falls cleanly through to Yahoo — coverage can never regress.
    Ratios/margins/CAGRs are currency-invariant, so a name reporting in CAD/AUD
    still scores correctly (live price/valuation come from TV/info separately)."""
    if not ifrs: return None
    h = _empty_hist(); h['source'] = 'sec-ifrs'
    h['rev']    = _sec_annual(ifrs, ['Revenue','RevenueFromContractsWithCustomers'])
    if not h['rev'] or len([x for x in h['rev'] if x]) < 3:
        return None                            # no usable IFRS revenue -> SEC miss, fall to Yahoo
    h['op']     = _sec_annual(ifrs, ['ProfitLossFromOperatingActivities','OperatingIncomeLoss'])
    h['np_']    = _sec_annual(ifrs, ['ProfitLoss'])
    h['eps_s']  = _sec_annual(ifrs, ['DilutedEarningsLossPerShare','BasicEarningsLossPerShare'], want_per_share=True)
    h['cogs']   = _sec_annual(ifrs, ['CostOfSales'])
    h['sga']    = _sec_annual(ifrs, ['SellingGeneralAndAdministrativeExpense','AdministrativeExpense'])
    h['tax_exp']= _sec_annual(ifrs, ['IncomeTaxExpenseContinuingOperations','IncomeTaxExpenseBenefit'])
    h['pbt']    = _sec_annual(ifrs, ['ProfitLossBeforeTax'])
    h['int_exp']= _sec_annual(ifrs, ['FinanceCosts','InterestExpense'])
    h['dep']    = _sec_annual(ifrs, ['DepreciationAndAmortisationExpense',
                                     'DepreciationAmortisationAndImpairmentExpenseReversalRecognisedInProfitOrLoss'])
    h['ppe']    = _sec_annual(ifrs, ['PropertyPlantAndEquipment'])
    h['td']     = _sec_annual(ifrs, ['Borrowings','NoncurrentBorrowings'])
    h['ltd']    = _sec_annual(ifrs, ['NoncurrentBorrowings','LongtermBorrowings'])
    h['eq0s']   = _sec_annual(ifrs, ['Equity','EquityAttributableToOwnersOfParent'])
    h['ta_s']   = _sec_annual(ifrs, ['Assets'])
    h['ca_s']   = _sec_annual(ifrs, ['CurrentAssets'])
    h['cl_s']   = _sec_annual(ifrs, ['CurrentLiabilities'])
    h['re_s']   = _sec_annual(ifrs, ['RetainedEarnings'])
    h['ar_s']   = _sec_annual(ifrs, ['TradeAndOtherCurrentReceivables','CurrentTradeReceivables'])
    h['ap_s']   = _sec_annual(ifrs, ['TradeAndOtherCurrentPayables','CurrentTradePayables'])
    h['inv_s']  = _sec_annual(ifrs, ['Inventories'])
    h['cash_s'] = _sec_annual(ifrs, ['CashAndCashEquivalents'])
    h['cfo']    = _sec_annual(ifrs, ['CashFlowsFromUsedInOperatingActivities'])
    capex       = _sec_annual(ifrs, ['PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities',
                                     'PaymentsToAcquirePropertyPlantAndEquipment'])
    if h['cfo'] and capex:
        h['fcf'] = [(h['cfo'][i] - capex[i]) if i < len(capex) and h['cfo'][i] is not None and capex[i] is not None else None
                    for i in range(len(h['cfo']))]
    h['div_paid'] = [abs(v) if v is not None else None for v in _sec_annual(ifrs, ['DividendsPaidClassifiedAsFinancingActivities','DividendsPaid'])]
    h['buyback']  = [abs(v) if v is not None else None for v in _sec_annual(ifrs, ['PaymentsToAcquireOrRedeemEntitysShares'])]
    h['issuance'] = [abs(v) if v is not None else None for v in _sec_annual(ifrs, ['ProceedsFromIssuingShares'])]
    if h['op'] and h['dep']:                    # EBITDA approx op + dep (no IFRS EBITDA tag), same as the us-gaap path
        h['ebitda_s'] = [(h['op'][i] + (h['dep'][i] or 0)) if h['op'][i] is not None else None for i in range(len(h['op']))]
    return h

def sec_history(ticker):
    cik = _sec_cik(ticker)
    if not cik: return None
    try:
        r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                         headers=HDRS_SEC, timeout=45)
        if r.status_code != 200: return None
        _allfacts = r.json().get('facts', {})
        facts = _allfacts.get('us-gaap', {})
        ifrs  = _allfacts.get('ifrs-full', {})   # foreign filers (20-F/40-F under IFRS): miners, ADRs
    except Exception:
        return None
    if not facts: return _sec_ifrs(ifrs)          # no us-gaap block -> try the IFRS twin before Yahoo
    h = _empty_hist(); h['source'] = 'sec'
    h['rev']    = _sec_annual(facts, ['RevenueFromContractWithCustomerExcludingAssessedTax',
                                      'RevenueFromContractWithCustomerIncludingAssessedTax',
                                      'Revenues','SalesRevenueNet','SalesRevenueGoodsNet',
                                      'RevenuesNetOfInterestExpense'])
    if not h['rev'] or len([x for x in h['rev'] if x]) < 3:
        return _sec_ifrs(ifrs)                 # us-gaap present but no usable revenue -> try IFRS, else Yahoo
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
    h['ar_s']   = _sec_annual(facts, ['AccountsReceivableNetCurrent', 'ReceivablesNetCurrent', 'AccountsAndOtherReceivablesNetCurrent'])  # v2.27.0 variants
    h['ap_s']   = _sec_annual(facts, ['AccountsPayableCurrent', 'AccountsPayableTradeCurrent', 'AccountsPayableAndAccruedLiabilitiesCurrent'])  # v2.27.0 variants
    h['inv_s']  = _sec_annual(facts, ['InventoryNet', 'InventoryFinishedGoodsNetOfReserves', 'InventoryGross'])  # v2.27.0 variants
    h['cash_s'] = _sec_annual(facts, ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'])  # v2.27.0 variants
    h['sti_s']  = _sec_annual(facts, ['ShortTermInvestments'])
    h['cfo']    = _sec_annual(facts, ['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'])
    capex       = _sec_annual(facts, ['PaymentsToAcquirePropertyPlantAndEquipment'])
    if h['cfo'] and capex:
        h['fcf'] = [(h['cfo'][i] - capex[i]) if i < len(capex) and h['cfo'][i] is not None and capex[i] is not None else None
                    for i in range(len(h['cfo']))]
    h['div_paid'] = [abs(v) if v is not None else None for v in _sec_annual(facts, ['PaymentsOfDividendsCommonStock','PaymentsOfDividends'])]
    h['buyback']  = [abs(v) if v is not None else None for v in _sec_annual(facts, ['PaymentsForRepurchaseOfCommonStock'])]
    h['issuance'] = [abs(v) if v is not None else None for v in _sec_annual(facts, ['ProceedsFromIssuanceOfCommonStock'])]
    # v2.27.0: SEC net-change-in-cash (was NEVER fetched from SEC -> net_cash metric NA on ~70%% of
    # SEC-served names). Two standard ASC-230 concepts cover with/without the exchange-rate effect line.
    h['ncc']  = _sec_annual(facts, ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
                                    'CashAndCashEquivalentsPeriodIncreaseDecrease'])
    # EBITDA not a us-gaap tag -> approximate op + dep so peter-lynch growth has a base
    if h['op'] and h['dep']:
        h['ebitda_s'] = [(h['op'][i] + (h['dep'][i] or 0)) if h['op'][i] is not None else None for i in range(len(h['op']))]
    return h


# v2.27.0 US FIELD-LEVEL COMPLETION (owner-directed; NON-Yahoo). When the SEC history is served but
# individual balance-sheet series are empty (single-concept gaps), fill ONLY those empty series from
# the stockanalysis.com US standardized page -- the same S&P-template parser proven for PSX and
# validated live on MU (full FY2021-2025 + TTM, every row by name). Yahoo remains the untouched final
# backstop; this tier never runs for names SEC already fully covers.
_SA_US_BAL = "https://stockanalysis.com/stocks/{t}/financials/balance-sheet/"
_SA_US_INC = "https://stockanalysis.com/stocks/{t}/financials/"                       # v2.28.0
_SA_US_CF  = "https://stockanalysis.com/stocks/{t}/financials/cash-flow-statement/"   # v2.28.0
_SA_US_ROWMAP = {   # our history key -> stockanalysis standardized row label (balance sheet)
    'inv_s': 'Inventory', 'ar_s': 'Accounts Receivable', 'ap_s': 'Accounts Payable',
    'cash_s': 'Cash & Equivalents', 'sti_s': 'Short-Term Investments',
    'ca_s': 'Total Current Assets', 'cl_s': 'Total Current Liabilities', 'td': 'Total Debt',
    'ta_s': 'Total Assets', 're_s': 'Retained Earnings', 'eq0s': "Shareholders' Equity",
    'ppe': 'Property, Plant & Equipment', 'ltd': 'Long-Term Debt',
}
# v2.28.0 income-statement rows (fills int_exp/tax_exp/cogs/sga/eps/ebitda/pbt + deepens op/np/rev
# history to 5 FYs + TTM -- validated LIVE on ASM, the worst IFRS filer: every row present by name)
_SA_US_INC_ROWMAP = {
    'int_exp': 'Interest Expense', 'tax_exp': 'Provision for Income Taxes',
    'cogs': 'Cost of Revenue', 'sga': 'Selling, General & Admin',
    'eps_s': 'EPS (Diluted)', 'ebitda_s': 'EBITDA', 'pbt': 'Pretax Income',
    'op': 'Operating Income', 'np_': 'Net Income', 'rev': 'Revenue',
}
# v2.28.0 cash-flow rows (fills dep/fcf/cfo -> croic + the fcf family)
_SA_US_CF_ROWMAP = {
    'dep': 'Depreciation & Amortization', 'fcf': 'Free Cash Flow',
    'cfo': 'Operating Cash Flow', 'div_paid': 'Dividends Paid', 'buyback': 'Share Repurchases',
}
def _sa_us_complete(ticker, h):
    """v2.28.0 THREE-STATEMENT completion: fill ANY empty history series in h from the stockanalysis
    US pages (balance sheet + income statement + cash flow -- the same proven S&P-template parser).
    Only-empty series are filled; populated SEC series are never overwritten. Pages are fetched
    lazily: a page is hit only when at least one of its rows is actually missing. Returns count."""
    filled = 0
    bare = ticker.split(':')[-1].lower()
    for url, rowmap in ((_SA_US_BAL, _SA_US_ROWMAP), (_SA_US_INC, _SA_US_INC_ROWMAP), (_SA_US_CF, _SA_US_CF_ROWMAP)):
        needed = [k for k, lbl in rowmap.items() if not (h.get(k) and any(x is not None for x in h[k]))]
        if not needed:
            continue
        try:
            tbl = _sa_fetch_statement(url.format(t=bare))
        except Exception:
            tbl = None
        if not tbl:
            continue
        for k in needed:
            series = tbl.get(rowmap[k])
            if series and any(x is not None for x in series):
                # interest expense is served negative on SA ('-0.56'); the scorer expects magnitude
                h[k] = [abs(x) if (x is not None and k in ('int_exp', 'div_paid', 'buyback')) else x for x in series]
                filled += 1
                h.setdefault('sa_completed', []).append(k)
    return filled

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
    # DH-0.5: serve a fresh cached statement history (mirrors the PSX _SA_CACHE read). A hit
    # skips the income+balance+cashflow pulls entirely; the live price/valuation is fetched
    # separately in score_ticker (tv_fetch/info), so it still refreshes every run.
    bare = ticker.upper().split(':')[-1]
    try: _yhc = json.load(open(_YH_CACHE))
    except Exception: _yhc = {}
    _ent = _yhc.get(bare)
    if isinstance(_ent, dict) and _ent.get('h') and _ent.get('cv') == _YH_CACHE_VER:
        try:
            if (time.time() - float(_ent.get('ts', 0))) / 86400.0 < _YH_TTL_DAYS:
                return _ent['h']
        except Exception:
            pass
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
    # DH-0.5: cache ONLY a usable history (>=3yr revenue), so a transient Yahoo miss is never
    # stored as a hit -> coverage can't regress (a thin/empty fetch simply retries next run).
    try:
        if len([x for x in h.get('rev', []) if x]) >= 3:
            _yhc[bare] = {'ts': time.time(), 'cv': _YH_CACHE_VER, 'h': h}
            json.dump(_yhc, open(_YH_CACHE, 'w'))
    except Exception:
        pass
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
# DH-0.5: US multi-year statement cache (the exact mirror of _SA_CACHE for the Yahoo backstop).
# yahoo_history pulls income+balance+cashflow per US name (~1s each x the scored set ~= 143s/run);
# annual statements change quarterly, so a fresh cached history skips all three pulls. Side-file
# (must be committed by daily.yml, like psx_history_cache.json) -> persists across runs.
_YH_CACHE = "us_history_cache.json"
_YH_TTL_DAYS = 30        # statements are quarterly; 30d is safe and bounds the dict
_YH_CACHE_VER = "1"      # bump if yahoo_history's parse / _HKEYS map changes, to invalidate stale parses
IM3_VERSION = "2.28.0"  # 2.28.0: (FULL-SCORE COMPLETION, owner-directed: "calculate it but dont make it a gate -- the score should be full".) TWO changes, fetch/display layer only, NO gating-recipe change: (1) THREE-STATEMENT COMPLETION -- the proven v2.27.0 balance-only stockanalysis completion tier now also fills empty INCOME-STATEMENT series (Interest Expense, Tax Provision, COGS, SG&A, EPS diluted, EBITDA, Pretax, Operating Income, Net Income, Revenue -- validated LIVE on ASM, the worst IFRS filer, 5 FYs + TTM every row by name) and CASH-FLOW series (D&A, FCF, CFO, Dividends Paid, Share Repurchases), plus deeper balance rows (Total Assets, Retained Earnings, Equity, PP&E, LTD). Pages fetched lazily (only when a row is missing), only-empty filled, SEC never overwritten, Yahoo untouched. Un-blocks the fixable NA cascade concentrated on foreign/IFRS filers: int_coverage, tax_rate, beneish_m, np/op CAGR, ev_ebitda, altman_z, croic, fcf family, PE-family where earnings exist. (2) CALCULATE-DONT-GATE -- div_yield: a confirmed non-payer now SHOWS 0.0%% (reinvesting) instead of a blank (derived from div_paid/mktcap incl. zero); val_shareholders: the computed value (incl. 0.0%% reinvesting) is always displayed when inputs exist. Verdicts on zero stay NA -- displayed, never counted, never a penalty (Wave A preserved: growth names are not punished). Mathematically-impossible stays NA (PE on losses). Prior   # 2.27.0: (FETCH COMPLETION, owner-directed, non-Yahoo. NO scoring-recipe change.) The Explosive-tab audit proved ~half the metric NAs were a FETCH gap, not design: SEC-served names averaged 2.7/6 balance-sheet-class NAs vs Yahoo-served 1.8/6, and net_cash was NA on ~70% because sec_history NEVER set h[ncc]. Fixes, fetch-layer only: (a) SEC net-change-in-cash from two ASC-230 concepts; (b) variant tags for inventory/cash/receivables/payables single-concept lookups (the same single-label disease as the scanner revenue fix, one layer deeper); (c) US FIELD-LEVEL COMPLETION -- when SEC wins the history but leaves a balance series empty, that ONE series is filled from the stockanalysis.com US standardized page (the S&P-template parser already used for PSX, validated LIVE on MU: full FY2021-2025 + TTM, every row by name), Yahoo untouched as the pre-existing final backstop. Expected: net_cash NA ~70%->near-full, SEC-served names gain 1-5 scored metrics each. The adaptive per-stock maximum is BY DESIGN and unchanged (div_yield/peg/val_shareholders NAs stay -- growth names are not penalized). Prior   # 2.26.0: (M2 scoring-propagation audit — asset-light fat fairness, ported from scanner _score_standard v1.201.0) The final per-metric delta between the two IM3 engines: the scanner deep scorer EXCLUDES fixed-asset-turnover (fat) for an ULTRA-LIGHT non-bank (no meaningful inventory AND net PPE < 5% of total assets — software/services where fat is a meaningless ratio), but the canonical engine still graded it, so a handful of asset-light non-banks on the Explosive/TCE/PSX tabs carried an unfair fat verdict the M1 buy list would have dropped. FIX (non-bank INVENTORY block only): compute _light (no inventory / max inv < 1% of latest revenue) and _ultra (_light AND net PPE < 5% of first non-None total assets), both data-driven from the filings, never a sector label; when _ultra, fat is set verdict NA (the canonical exclusion mechanism — dropped from BOTH score and denominator by the existing `!= NA` filter, the SAME net effect as the scanner EXCL, since the canonical denominator does not recognise an EXCL label and pts(EXCL)=0 would have wrongly penalised) with an excl reason tag for card transparency. inv_turn/ccc already read NA naturally when inventory is absent, so only fat needed the explicit rule. BANKS byte-for-byte UNCHANGED (the whole branch is in the non-bank else-arm; banks still NA all four inventory metrics). Normal (non-ultra-light) non-banks byte-for-byte UNCHANGED (else-arm scores fat exactly as before). Only asset-light non-banks with tiny PPE shift — fat leaves their denominator, so their strength pct can only stay equal or RISE, per the never-penalise principle. Closes the two-engine scoring consistency ahead of the eventual port. FREEZE-SAFE: IM3 is a separate scorer from the TCE engine — no TCE tier/stream/the frozen ledger touched. # 2.25.0: (SEC IFRS fallback — foreign-filer statement coverage, FREEZE-SAFE) sec_history only read the 'us-gaap' companyfacts block, so FOREIGN private issuers that file 20-F/40-F under IFRS (miners/ADRs — Barrick/GAU/ASM-type names) returned None and dropped to the Yahoo backstop. NEW _sec_ifrs() is the IFRS-taxonomy twin of the us-gaap builder: same _sec_annual machinery (annual forms incl. 20-F/40-F, FY, newest-first, currency-unit fallback), only the element NAMES change to ifrs-full (Revenue/ProfitLossFromOperatingActivities/ProfitLoss/CostOfSales/FinanceCosts/Equity/CurrentAssets/Inventories/CashFlowsFromUsedInOperatingActivities/...). sec_history now captures BOTH blocks and routes to _sec_ifrs at its TWO existing miss-points — no us-gaap block, OR us-gaap present but <3yr usable revenue — so a foreign filer gets statements from SEC (free, authoritative, no API key) tagged source 'sec-ifrs' instead of Yahoo. The us-gaap success path is BYTE-FOR-BYTE UNCHANGED (only the two `return None` early-exits now try IFRS first; a name with neither block still returns None -> Yahoo, so coverage can NEVER regress). Ratios/margins/CAGRs are currency-invariant so a name reporting in CAD/AUD still scores correctly; live price/valuation come from TV/info separately. FREEZE NOTE: IM3 is a SEPARATE scorer from the TCE engine -> no TCE tier/stream/the frozen ledger touched -> respects the Sept freeze. Version bump re-scores the board on the next run (cold once, then the DH-0.5 cache warms); the names that move sec-ifrs gain full /162 multi-year coverage they previously got from Yahoo (or lacked).  # 2.24.0: (DH-0.5 — US statement-history cache; SPEED/PERSISTENCE only, no scoring change) yahoo_history (the Yahoo backstop for US multi-year statements) re-pulled income_stmt + balance_sheet + cashflow per US scored name every run (~1s/name -> ~143s over the ~127-name set; runner-benchmarked). Annual statements change quarterly, so the parsed history is now CACHED to us_history_cache.json — the EXACT mirror of the existing PSX _SA_CACHE (fetch_psx_history): version-tagged (_YH_CACHE_VER) + TTL'd (_YH_TTL_DAYS=30); a fresh hit returns the stored history dict and skips all three pulls. Cache is written ONLY for a usable history (>=3yr revenue), so a transient Yahoo miss is never stored as a hit -> coverage can NEVER regress (a thin/empty fetch retries next run). EQUIVALENCE: the cached value is the SAME statement bytes Yahoo would return within the 30d window (annual statements don't change), so grade/pct/metrics/valuation are byte-identical on a hit; the LIVE price + valuation are fetched separately in score_ticker (tv_fetch/info) and still refresh every run (only the quarterly statement legs are cached) — the same philosophy as the scanner's explosive-statement cache. REQUIRES daily.yml to commit us_history_cache.json (one git-add line, mirroring the psx_history_cache.json line) so the side file persists across runs — without it every run is a cold cache (the F2 side-file lesson). EXPECTED: the first 2.24.0 run is a cold full re-score (the version bump re-scores the board AND seeds the cache); subsequent runs skip the US statement pulls and the IM3 step drops ~100s+. FREEZE NOTE: IM3 is a SEPARATE scorer from the TCE engine — this touches NO TCE tier/stream/the frozen ledger -> respects the Sept freeze. Pure fetch-layer change; verdict/grade/valuation math byte-for-byte UNCHANGED.  # 2.23.0: (Fix D - surface EVERY metric value on the card, DISPLAY-ONLY) extends the v2.19.0 CAGR transparency to all ~40 metrics so each verdict is auditable from the card. The scorer now emits result['metric_values'] = {metric_key: {v, u[, dir/wacc]}} assembled from the SAME locals already used to score: scalar metrics carry their value+unit (margins/ROE/yields in %, PE/PEG/PB/PS/EV-EBITDA/coverage/current/cash-debt in x, Piotroski /9, Altman Z, Beneish M, ROIC vs WACC), and the pure TREND metrics (total_debt/cfo_trend/nfa_turn/eps_trend/inv_turn/dro/fat/ccc/fcf_trend/fcf_cfo) carry the % change of their 3yr-avg vs 5yr-avg = exactly what trend() tests, plus a higher/lower-better hint. PURELY ADDITIVE + wrapped in try/except so a display-value glitch can never break a score; verdict/pts/max/grade/valuation byte-for-byte UNCHANGED (validated: a synthetic non-bank reproduces grade/pct/score/n_metrics exactly, metric_values now populated). Inventory entries gated to non-banks (it/dro/ccc_s are non-bank-only locals). Pairs with index.html (renders the value beside each metric verdict). DISPLAY-ONLY -> never feeds the TCE engine/tier/ledger -> respects the Sept freeze.  # 2.22.0: (Fix C — valuation-indicator honesty; affects the VALUATION CHIP only, never the grade) Three calibration fixes from the complete metric audit: (1) PEG reads NA for names in an earnings inflection (op/np growth >100 or EXPLOSIVE) — PEG divides the rich P/E by a one-year 600%+ surge and reads absurdly cheap, falsely lifting the valuation score on ~11 expensive names (MU/AVGO/NVDA/LLY/WDC...); (2) the Attractive/Fair/Rich label now reads RICH whenever margin-of-safety < -50% regardless of the ratio-mix average, so a name at -83% MoS can no longer show 'Fair'; the Fair floor also moves 40->45; (3) the FCF- and cash-based margin-of-safety DISPLAY values are suppressed (None) when outside +-150% (capital-intensive cyclicals produced -714%/-506% noise). Grade/strength scoring byte-for-byte UNCHANGED — these touch only result['valuation'] and the iv display fields.  # 2.21.0: (Fix B — Altman-Z display clamp; NO grade change) the emitted altman_z display value is blanked (None) when outside the plausible -10..25 range (19 names showed scaling blow-ups: OGDC 473, GROY 7274, ABTC 495). The metric VERDICT is untouched (a high-Altman name is genuinely 'safe' and still scores GOOD) — only the nonsense NUMBER on the card is removed.  # 2.20.0: (Fix A — BAD tiers: the model can finally mark weakness down) The complete metric audit found ~17 strength metrics (≈59 of ~122 pts) could only score GOOD or WATCH, never BAD — so a failing company got the 60% WATCH floor instead of 20%, and weak names could not be marked down (53% of names sat artificially high). FIX adds a BAD tier where a CLEARLY-FAILING MEASURED value is unambiguously negative, never on missing data (which stays NA so young/early names are not penalised, per the multibagger principle): (a) trend() is now 3-tier — GOOD improving / WATCH roughly flat / BAD deteriorating >10% the wrong way on a POSITIVE base (sign-safe; negative base stays WATCH) — covering cfo_trend, eps_trend, fcf_trend, fixed-asset & inventory turnover, debtor-days, total-debt trend; (b) Revenue/Op/Net CAGR score BAD when the 5yr compound is NEGATIVE (business actually shrinking), GOOD>=15% / WATCH 0..15% / BAD<0; (c) ccfo_cpat scores BAD when cumulative operating cash is non-positive (earnings not cash-backed at all); (d) roic_wacc scores BAD when ROIC is non-positive (destroying capital). cash_share and tax_rate stay 2-tier (a low value there is not a red flag). This RE-GRADES weak names downward on the next run — by design — so the grades finally reflect measured weakness. Confirm the new grade distribution on the runner.  # 2.19.0: (CAGR transparency — additive, NO grade change) An audit-of-the-audit found the Growth-section CAGR metrics (Revenue/Op/Net-Profit CAGR) were scored on the real 5-year compound rate but the VALUE was computed and thrown away — the card showed only 'WATCH 3/5' with no number, so a moderate-but-correct read (e.g. MU's ~5yr revenue CAGR sitting just under the GOOD>=15% bar because the FY23 memory-cycle crash is inside the window) looked arbitrary or 'missed', when the +49% shown elsewhere is the LATEST-YEAR figure (a different window). FIX: the scorer now EMITS result['cagr_pct'] = {rev_cagr, op_cagr, np_cagr} (the actual 5yr CAGR %, or None) so the dashboard can show the number beside each verdict and beside the explosive latest-year growth — making every Growth score auditable. PURELY ADDITIVE: the verdict/pts/max/grade math is byte-for-byte UNCHANGED (validated); this only surfaces a value that was already computed. Pairs with index.html v5.84 (renders the CAGR % + latest-year growth + the GOOD>=15% bar on the Growth rows). NOTE (separate, not changed here): the CAGR tiering is currently binary (GOOD>=15% else WATCH, no BAD) so a declining-revenue name reads WATCH not BAD, and op/np CAGR are weighted 1pt each vs revenue's 5 — both are IM3-master calibration questions flagged for a deliberate decision, not silently re-tuned.  # 2.18.0: (Beneish-M reliability guard — audit fix) A dashboard-wide audit found Beneish-M scored BAD on 85% of non-bank names (93/110), 20 of them with outright broken values (billions/trillions, vs the real ~ -3..+3 range) — making it a near-universal false 4-pt penalty rather than a discriminating fraud signal. Two root causes: (a) names in an earnings INFLECTION (large operating/net-profit surge or turnaround — exactly the Explosive/Multibagger target profile) trip Beneish's accrual + margin + sales-growth terms and read as 'manipulation' purely because the business inflected; (b) the computation BLOWS UP on some feeds (near-zero denominator / unit error). FIX: the beneish_m metric now reads NA (EXCLUDED from the denominator, never a BAD penalty) when the name is in an inflection (reuses explosive_from_history: EXPLOSIVE verdict OR op_growth>100 OR np_growth>100) OR the value is out of range (|M|>8); a plausible value on a NON-inflecting name still scores GOOD/WATCH/BAD normally, preserving the genuine red-flag. The emitted beneish_m display value is suppressed (None) when |M|>8 so cards no longer show billion/trillion nonsense. Effect: removes the false drag from ~85% of names and lifts the ones it was wrongly penalising (8 cross a grade band); the explosive verdict is now computed once and reused (no behaviour change). Altman-Z display-clamp, PEG/FCF-IV suppression, valuation-band tighten and the bank provenance label are the queued follow-up fixes (separate version bumps). PSX + bank scoring and all other non-bank metrics byte-for-byte UNCHANGED.  # 2.17.1: (US scorecard crash fix — NALTOT-null) score_bank_us raised 'unsupported operand +: NoneType and float' for ALL 8 US banks (CARE/CCNE/COF/COFS/ISTR/MCBS/OSBC/PLBC) on the first v2.17.0 live run: FDIC returns the noncurrent-loans % (NPERFV) but a NULL $ field (NALTOT) for these banks, and the Texas-ratio numerator (naltot+ore) was evaluated unguarded when naltot was None. FIX: (a) when NALTOT($) is null, DERIVE the noncurrent dollar from NPERFV(%) x net loans (both FDIC-present) so reserve_coverage + Texas ratio still score; (b) if still unknown -> both read NA (excluded), never crash; (c) Texas denominator guarded >0. Hardened + verified None-safe across 53 variants (every field null, all-but-one null, zero/negative edges) — the all-None case returns 0/0 NA cleanly. The real-bank shape (NALTOT null) now scores ~36/42 with reserve_cov/texas GOOD off the derived figure. Only the scorer changed; scanner v1.93.0 (writes us_sc) is correct and unchanged. PSX + non-bank scoring byte-for-byte UNCHANGED.  # 2.17.0: (US BANK SCORECARD — purpose-built, CAMELS-aligned) NEW score_bank_us() replaces the re-banded Pakistani 24-ratio model for US banks, routed to ONLY when the scanner supplies a 'us_sc' input block (else US banks fall back to score_bank_ig2 calib='us', and PSX banks ALWAYS keep score_bank_ig2 calib='psx' — the workbook-validated model is byte-for-byte untouched, psx_bank can never reach score_bank_us). Built from the metrics US analysts/examiners actually use (FDIC Quarterly Banking Profile + Basel III well-capitalized + standard credit/funding screens), 21 ratios Good/Avg/Bad=2/1/0, NA excluded, max 42: CAPITAL(4) total risk-based capital>=12/10, tier-1 risk-based>=10/8, tier-1 leverage>=9/5, TCE/TA>=9/6; EARNINGS(5) ROA>=1.2/0.8, ROTCE>=12/8 (vs ~10-12 cost-of-equity), NIM>=3.5/3.0, efficiency<=55/65 INV, PPNR/assets>=2.0/1.0; ASSET QUALITY(4) noncurrent<=1/3 INV, net-charge-off<=0.5/1.0 INV, reserve-coverage>=150/80, Texas-ratio<=25/50 INV; LIQUIDITY/FUNDING(4) loan-to-deposit banded GOOD 75-92 / AVG 60-100, uninsured-deposit<=30/50 INV, core-deposit>=80/65, noninterest-bearing-deposit>=30/20; GROWTH(4) US-calibrated asset>=8/4, loan>=6/3, deposit>=6/3, PAT>=8/0 CAGR — fixing the audit finding that the IG2 'us' calib only re-banded 10 of 24 ratios and left the four growth bars on Pakistan's 15%/5% (PKR-inflation) thresholds, systematically under-scoring USD banks. NEW dimensions the Pakistani model lacked entirely: liquidity/funding (the 2023 SVB lessons — uninsured & core deposit mix, LDR), credit-stress (net charge-offs, reserve coverage, Texas ratio), tangible capital (TCE/TA, ROTCE), and pre-provision earning power (PPNR). All inputs are FDIC call-report data; price/market metrics (P/TBV) stay in the separate bank_valuation block, never the quality grade (consistent with the Wave A strength/valuation split). Returns the SAME dict shape as score_bank_ig2 -> drop-in via _ig2_result; grade bands A>=75/B>=60/C>=45/FAIL unchanged; bank_coverage/bank_inputs now read 'US scorecard (CAMELS)' for these banks. DEFERRED (no clean FDIC field for small banks): CRE concentration, AOCI/unrealized-loss burden, EVE/NII rate-sensitivity, LCR/NSFR — future field-probe candidates. Pairs with scanner v1.93.0 (writes the us_sc block); feature activates only when BOTH are deployed (order-independent — until then US banks keep the IG2 'us' score). Non-bank + PSX scoring byte-for-byte UNCHANGED.  # 2.16.0: (Wave A — STRENGTH/VALUATION SPLIT + 4 calibration fixes) The NON-BANK headline grade is now computed on business STRENGTH ONLY — Growth, Stability, Inventory, Cashflow, Risk, plus the EPS-trend momentum signal (strength bucket, ~122 applicable pts). The cheapness / capital-return block (pe_ratio, peg_ratio, earn_yield, pb_ratio, graham_val, ps_ratio, div_yield, ev_ebitda, mos, val_shareholders — VALUATION_KEYS, ~40 pts) is STILL scored but emitted as a SEPARATE valuation INDICATOR (result['valuation'] = {score, max, pct, label in Attractive/Fair/Rich, metrics[]}) and NEVER folded into the grade or used to downgrade. RATIONALE: a fast, strong, early 'expensive-looking' multibagger was losing ~15 pct-pts of grade purely for not being cheap — the value lens was burying the very names the Explosive/Multibagger tabs exist to surface. Now such a name reads STRONG, with its rich valuation shown beside it as context (coloured), per the standing principle 'separate is-it-strong from is-it-cheap'. Each metric carries a 'bucket' tag ('strength'|'valuation') so the dashboard can group/colour. result['blended_pct'] retains the old all-metric score for transparency/continuity only. Strength coverage (not all-metric) drives the partial flag + A->B cap, so valuation-data gaps no longer flag a name partial. Grade bands UNCHANGED (A>=80/B>=60/C>=50). BANKS EXEMPT — is_bank keeps the prior all-metric computation and the validated IG2/System-B grade is byte-for-byte unchanged (valuation=None for banks). FOUR calibration fixes (all now affect the INDICATOR only, not the grade): (1) val_shareholders no longer marks a reinvesting non-payer BAD — negligible/zero net shareholder yield reads NA (reinvestment is the value creation), real returns still GOOD/WATCH; (2) earn_yield is now 3-tier (GOOD>=bond / WATCH>=0.6*bond / BAD) instead of a brutal binary that failed almost every PSX grower at the 11.5% bond; (3) the scored 'mos' metric now uses the triangulated CENTRAL IV (mos_pct, percent units, GOOD>=25/WATCH>=0/BAD<0) — same basis as the displayed MoS — instead of a DCF-EPS-only value that understated high-growth IV; (4) PEG returns NA when there is no REAL EPS-growth series instead of fabricating 5% growth that wrongly flagged data-sparse fast growers expensive. Confirm on the runner: bank grades byte-for-byte unchanged; a strong expensive grower's grade RISES vs 2.15.0 while its valuation indicator reads 'Rich'; full-coverage cheap value names roughly unchanged on grade.  # 2.15.0: (Wave A / A1 — DEN: consistent NA-excluded denominator + coverage guard) the non-bank grade now uses ONE rule for both markets: NA metrics (data not yet available for a young name, or a metric that does not apply such as a growth non-payer's dividend yield) are EXCLUDED from the denominator rather than scored as zero. Previously only banks + PSX excluded NA; US non-banks divided by a FIXED 162, so data-sparse US names (small biotech ABCL, miner GAU) were penalised purely for being early. EFFECT: a full-coverage US name has max_s == 162 -> pct IDENTICAL to the old /162 (byte-for-byte); a US name carrying any NA metric now divides by its applicable weight, so its pct can only stay equal or RISE (the fix). Banks are UNCHANGED — IG2-scored banks are overridden by the IG2 block as before, and System-B banks already excluded NA. NEW coverage guard: coverage = measurable metrics / applicable metrics; a NON-BANK with coverage < COVERAGE_FLOOR (0.60) is flagged partial=True and, if it would grade A, is capped to B, so a near-empty name cannot show an inflated top grade on a handful of metrics. Output gains coverage + partial fields (additive). Banks exempt from the cap. Confirm on the runner: bank grades unchanged; full-data US large-caps unchanged; ABCL/GAU rise off the fixed /162 (quantify before/after); any name with <60%% coverage shows partial + is capped at B. # 2.14.4: (ABCL/GAU scorer crash FIXED — root cause) the gross-profit series gp_s subtracted COGS from revenue with the COGS term guarded for list-presence/index but NOT for a None ELEMENT: `(rev[i] or 0) - (cogs[i] if cogs and i<len(cogs) else 0)` threw `unsupported operand for -: float/int and NoneType` for names whose cogs series is present but has None values (biotech ABCL has no COGS line; miner GAU reports None some years). These two raised inside score_ticker every run and were dropped by the daily.yml merge (now surfaced). FIX: wrap the COGS element in `(... or 0)` so a missing COGS reads 0 (gross profit = revenue), matching how rev[i] is handled. Reproduced + validated in-sandbox (cogs=all-None now scores instead of crashing; the normal cogs-present path is byte-for-byte unchanged). # 2.14.3: 2.14.3: (bank_inputs echo honesty — cosmetic) when a bank is scored by the IG2 24-ratio model, the emitted bank_inputs no longer shows the legacy System-B raw-statement probe (nii/total_assets/gross_loans/deposits=null + npl/casa/car_found=false). That probe reads the live statement fetch, which is ABSENT for IG2-scored banks (their data is in bank_ig2_inputs.json), so it printed all-null/false for banks like AKBL that actually scored fine (37/48 A). It now echoes {source:'IG2 inputs (calib)', ratios_scored, ratios_na, ratios_total} from the IG2 metrics actually used. Gated to _ig2_result is not None, so System-B banks keep their raw probe and non-banks stay None. SCORE/GRADE/METRICS/PCT byte-for-byte UNCHANGED (validated). # 2.14.2: (MoS discrimination + anchor) two refinements after 2.14.1 went live: (a) the central IV anchor now drops the Graham NUMBER (sqrt(22.5*eps*bvps)) — it systematically lowballs asset-light high-ROE names and was dragging the median, pushing most expensive growth names to a flat -100% — so the anchor is the median of just the three growth-appropriate POWER methods [DCF·EPS (Graham-revised), DCF·FCF, Peter-Lynch]; Graham-number stays in the expand. (b) MoS is now SYMMETRIC & bounded [-100,+100] instead of clamped: cheap side = true Graham margin (IV-price)/IV (0..+100), expensive side = premium vs price (IV-price)/price (-100..0) so a name at 2.5x IV reads -60% and one at 5x reads -80% — it discriminates how-overvalued instead of a flat -100 wall. (NOTE: pair with index.html v5.42 which stops the IV display from falling back to the unguarded 'composite' average when 'central' is suppressed — that fallback was still surfacing TSM $14,966 etc.) # 2.14.1: peter_lynch PEG=1 fix + central median of 4 defensible methods + >10x data-sanity guard + MoS clamp. # 2.14.0: dcf_eps units fix (bond percent, g cap 15), triangulated central IV, iv emits central+peg. # 2.13.0: (Option C — peer-relative IM3) op_margin / net_margin / ROE / P/E are now scored PEER-RELATIVE against this name's GICS-sector MEDIAN (from sector_medians.json, written by scanner v1.58.0's fetch_sector_medians) instead of fixed absolute bars: peer_band() gives GOOD>=median / WATCH>=median*0.7 for margins+ROE, and the P/E reference fpe is the sector-median P/E (was a flat 25 default) — this closes the largest gap vs the IM3 master and resolves the standing P/E divergence. GATED TO NON-BANKS (med={} when is_bank) so the validated IG2 bank model is provably untouched; and FALLBACK-PRESERVING — when sector_medians.json is absent OR the name's sector has no median (Yahoo-fallback US names + every PSX name, different taxonomy), peer_band returns None and the prior ABSOLUTE thresholds apply, so PSX + bank scoring and the no-file path are byte-for-byte unchanged (validated). ev_ebitda confirmed already fixed (live TTM used directly, line 389) — no change. # 2.12.0: partial-bank SCS fallback — for banks with no audited equity/ADR series (BOP/AKBL/BIPL), score_bank_ig2 now fills roe/adr/roa_trend from the live SCS snapshot (rec roe_scs/adr_scs/roa_trend_scs as fractions/ratio, written by the scanner to bank_ig2_overrides.json), lifting them off the reduced /32 denominator. Fill-MISSING-ONLY: a curated value already in bank_ig2_inputs.json is never overwritten, so the nine full-data workbook banks reproduce EXACTLY (validated). Audited annual data (when sourced) takes precedence over SCS. Bank valuation + non-bank scoring byte-for-byte unchanged. # 2.11.0: bank valuation — banks now carry a bank-appropriate IV block (bank_valuation): justified P/B (ROE-driven, the anchor) + Graham + dividend-discount, blended to a fair value with MoS vs live price; capped DCF-EPS shown as optimistic bound; Peter-Lynch/PEG + P/E/P/B/earnings-yield/div-yield ratios; DCF-FCF/Cash suppressed for banks (no conventional FCF). PSX cost-of-equity = PKR risk-free 11.5% + 6% ERP; long-run g 10% (psx)/4% (us), held below COE. Inputs are real (eps/equity/pat from the IG2 series + live price); reported DPS lights up DDM/div-yield when the annual-report parse supplies it, else DDM uses an implied sustainable payout. Quality scoring (score_bank_ig2) and non-bank scoring byte-for-byte UNCHANGED. # 2.10.1: partial-bank fix — 7 IG2 ratios (spread_ratio/net_margin/nim/npl_gl/ccfo_cpat/adr/idr) returned a fake GOOD/BAD when a source line item was MISSING (defaulted to 0); they now return NA so partial-data banks (e.g. BOP/AKBL/BIPL with no NPL/CFO/equity) score honestly on their applicable ratios only. The 9 full-data workbook banks reproduce EXACTLY as before (validated).     # 2.10.0: (Banking InvestoGenie 2.0 — faithful 24-ratio/48-pt bank model) banks now score on the documented Banking IG 2.0 model (score_bank_ig2), VALIDATED to reproduce Banking_InvestoGenie_Score_v2.xlsx exactly — all 9 PSX banks' totals and all 216 per-ratio cells (MEBL 45, FABL 43, UBL 41, ABL 38, MCB/BAFL/BAHL 37, HBL 36, NBP 26). 24 ratios across Growth(5)/Stability(13)/Business(6), Good/Avg/Bad = 2/1/0, /48. Inputs from bank_ig2_inputs.json (the workbook's FY2019-24 series for the 9 banks; update annually). Dual calibration: 'psx' (SBP/Sarmaaya bands, workbook-faithful) for PSX banks, 'us' (US-bank norms) ready-but-dormant until US bank inputs are supplied — US banks without IG2 inputs keep the prior System-B subset. NA ratios excluded from the denominator (partial banks score on applicable max). Grade follows the IG2 scale (Excellent>=75 -> A, Good>=60 -> B, Average>=45 -> C, Weak -> FAIL). Replaces the partial System-B label that was an over-claim. Non-bank scoring byte-for-byte unchanged. 2.9.4: (MCB CASA/CAR + System-B bank-ratio slot) the bank model now reads rec['_bank_system_b']={nim,casa,adr,npl,car} from psx_financials.json (percent or fraction, normalised by _ratio_norm) as an OVERRIDE for NIM/CASA/ADR/NPL/CAR whenever the free feed leaves them empty — free feeds carry no CASA/CAR for PSX (or US community) banks, so without this those metrics always scored NA. No fabrication: values come ONLY from the disclosure you place in the file; absent -> {} -> NA = prior behaviour. Non-bank scoring byte-for-byte unchanged. 2.9.3: A1 OPNP ratio threshold 1.5 -> 1.0 (D4, deck literal definition; see scanner v1.51.2 note) — PSX finalisation re-scores. 2.9.2: adds explosive_from_history() -> result["explosive"] (canonical G1/G2/A1/A2/C1/C3 + verdict from the parsed statements) so the PSX IM3 step FINALISES the explosive verdict on real operating/net/cash growth (same conditions as US, no eps/rev proxy). Scoring/grade math UNCHANGED. // scorer version stamped into every record; the daily.yml gate re-scores when this changes
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
            # v2.27.0: complete empty balance series from stockanalysis (non-Yahoo) before returning
            if h.get('source') == 'sec':
                try:
                    _n = _sa_us_complete(ticker, h)
                    if _n and log and not _json_mode: print(f"    + sa-complete({_n}) balance series filled", flush=True)
                except Exception:
                    pass
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

# ===================== US BANK SCORECARD (CAMELS-aligned, US analyst standards) =====================
# A PURPOSE-BUILT US bank model — NOT the re-banded Pakistani 24-ratio IG2. Built from the metrics US
# analysts/examiners actually use (CAMELS: Capital, Asset quality, Earnings, Liquidity), with US
# benchmarks (FDIC Quarterly Banking Profile + Basel III well-capitalized + the standard credit/funding
# screens). 21 ratios, Good/Avg/Bad = 2/1/0, NA excluded from the denominator. PSX banks are untouched
# (they keep score_bank_ig2 calib='psx'); a US bank routes here only when the scanner supplies a 'us_sc'
# input block (else it falls back to the IG2 'us' calibration). Every input is FDIC call-report data so
# the scanner can feed it; price/market metrics (P/TBV) stay in the separate bank_valuation block, never
# the quality grade. NEW dimensions vs IG2: liquidity/funding (uninsured-deposit, core-deposit, LDR),
# credit-stress (net charge-offs, reserve coverage, Texas ratio), tangible capital (TCE/TA, ROTCE),
# pre-provision earning power (PPNR/assets), and US-calibrated growth (no PKR-inflation 15% bar).
US_SC = {  # (good, avg) bands; higher-is-better unless noted INV (lower-is-better) in score_bank_us
 'car_total':(12.0,10.0),'tier1_rbc':(10.0,8.0),'tier1_lev':(9.0,5.0),'tce_ta':(9.0,6.0),
 'roa':(1.2,0.8),'rotce':(12.0,8.0),'nim':(3.5,3.0),'eff':(55.0,65.0),'ppnr_roa':(2.0,1.0),
 'noncurrent':(1.0,3.0),'nco':(0.5,1.0),'reserve_cov':(150.0,80.0),'texas':(25.0,50.0),
 'uninsured':(30.0,50.0),'core_dep':(80.0,65.0),'nib_dep':(30.0,20.0),
 'asset_cagr':(8.0,4.0),'loan_cagr':(6.0,3.0),'deposit_cagr':(6.0,3.0),'pat_cagr':(8.0,0.0)}
US_SC_RATIOS = ['car_total','tier1_rbc','tier1_lev','tce_ta','roa','rotce','nim','eff','ppnr_roa',
 'noncurrent','nco','reserve_cov','texas','ldr','uninsured','core_dep','nib_dep',
 'asset_cagr','loan_cagr','deposit_cagr','pat_cagr']
def score_bank_us(sc):
    """sc = the scanner's 'us_sc' block (FDIC FY2024 scalars + 5yr series for the 4 CAGRs)."""
    C = US_SC
    def num(k):
        v = sc.get(k); return float(v) if isinstance(v, (int, float)) else None
    def b(x, g, a):    # higher is better
        return None if x is None else (2 if x >= g else 1 if x >= a else 0)
    def bi(x, g, a):   # INV: lower is better (good <= g, avg <= a)
        return None if x is None else (2 if x <= g else 1 if x <= a else 0)
    def cagr(key):
        s = {int(k): float(v) for k, v in ((sc.get('series') or {}).get(key) or {}).items() if v is not None}
        a, e = s.get(2019), s.get(2024)
        return ((e / a) ** 0.2 - 1) * 100 if (a and a > 0 and e is not None) else None
    eq = num('eq'); intan = num('intan') or 0.0; asset = num('asset'); netinc = num('netinc')
    tce = (eq - intan) if eq is not None else None
    P = {}
    # CAPITAL
    P['car_total'] = b(num('car_total'), *C['car_total'])
    P['tier1_rbc'] = b(num('tier1_rbc'), *C['tier1_rbc'])
    P['tier1_lev'] = b(num('tier1_lev'), *C['tier1_lev'])
    tce_ta = (100 * tce / (asset - intan)) if (tce is not None and asset and (asset - intan)) else None
    P['tce_ta'] = b(tce_ta, *C['tce_ta'])
    # EARNINGS
    P['roa'] = b(num('roa'), *C['roa'])
    rotce = (100 * netinc / tce) if (tce and netinc is not None) else None
    P['rotce'] = b(rotce, *C['rotce'])
    P['nim'] = b(num('nimy'), *C['nim'])
    P['eff'] = bi(num('eff'), *C['eff'])
    nim_d = num('nim_dollar')
    ppnr = (nim_d + (num('nonii') or 0.0) - (num('nonix') or 0.0)) if nim_d is not None else None
    ppnr_roa = (100 * ppnr / asset) if (ppnr is not None and asset) else None
    P['ppnr_roa'] = b(ppnr_roa, *C['ppnr_roa'])
    # ASSET QUALITY
    P['noncurrent'] = bi(num('noncurrent_pct'), *C['noncurrent'])
    P['nco'] = bi(num('nco_rate'), *C['nco'])
    allow = (num('allow_loans') / 100.0 * num('lnlsnet')) if (num('allow_loans') is not None and num('lnlsnet')) else None
    naltot = num('naltot')
    if naltot is None:        # FDIC's $ noncurrent field (NALTOT) can be null -> derive from NPERFV (%) x net loans
        ncp = num('noncurrent_pct'); lns = num('lnlsnet')
        naltot = (ncp / 100.0 * lns) if (ncp is not None and lns is not None) else None
    ore = num('ore') or 0.0
    if naltot is None:                            # still unknown -> reserve coverage + Texas ratio are NA
        P['reserve_cov'] = None; P['texas'] = None
    elif naltot <= 0:                             # no noncurrent loans -> fully covered / no credit stress
        P['reserve_cov'] = 2; P['texas'] = 2
    else:
        cov = (100 * allow / naltot) if (allow is not None) else None
        P['reserve_cov'] = b(cov, *C['reserve_cov'])
        texas = (100 * (naltot + ore) / (tce + allow)) if (tce is not None and allow is not None and (tce + allow) > 0) else None
        P['texas'] = bi(texas, *C['texas'])
    # LIQUIDITY / FUNDING
    ldr = num('ldr')
    P['ldr'] = None if ldr is None else (2 if 75 <= ldr <= 92 else 1 if (60 <= ldr < 75 or 92 < ldr <= 100) else 0)
    dep = num('dep')
    P['uninsured'] = bi((100 * num('depunins') / dep) if (num('depunins') is not None and dep) else None, *C['uninsured'])
    P['core_dep']  = b((100 * num('coredep') / dep) if (num('coredep') is not None and dep) else None, *C['core_dep'])
    P['nib_dep']   = b((100 * num('depnidom') / dep) if (num('depnidom') is not None and dep) else None, *C['nib_dep'])
    # GROWTH (US-calibrated)
    P['asset_cagr']   = b(cagr('asset'), *C['asset_cagr'])
    P['loan_cagr']    = b(cagr('loans'), *C['loan_cagr'])
    P['deposit_cagr'] = b(cagr('deposits'), *C['deposit_cagr'])
    P['pat_cagr']     = b(cagr('netinc'), *C['pat_cagr'])
    def vv(p): return 'GOOD' if p == 2 else 'WATCH' if p == 1 else 'BAD' if p == 0 else 'NA'
    metrics = [{'key': k, 'verdict': vv(P.get(k)), 'pts': (P.get(k) or 0),
                'max': (2 if P.get(k) is not None else 0)} for k in US_SC_RATIOS]
    score = sum(m['pts'] for m in metrics); mx = sum(m['max'] for m in metrics)
    pct = round(100 * score / mx, 1) if mx else None
    rating = 'Excellent' if pct and pct >= 75 else 'Good' if pct and pct >= 60 else 'Average' if pct and pct >= 45 else 'Weak'
    return {'score': score, 'max': mx, 'pct': pct, 'is_bank': True, 'model': 'us_scorecard',
            'calib': 'us', 'rating': rating, 'metrics': metrics}

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
            if (not psx_bank) and _ig2_in.get('us_sc'):
                # US bank with the FDIC scorecard feed -> purpose-built US (CAMELS) model.
                _ig2_result = score_bank_us(_ig2_in['us_sc'])
            else:
                # PSX bank (workbook-faithful) or US bank without the scorecard feed (legacy IG2 'us').
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

    _eps_eg = egrates(eps_s)
    avg_eg  = avg(_eps_eg) or 5.0
    _avg_eg_real = bool(_eps_eg)          # True only when a real EPS-growth series exists
    avg_eg2 = avg(egrates(ebitda_s)) or 5.0

    metrics = []
    # v2.18.0/v2.22.0: inflection flag computed ONCE here, reused by the Beneish guard (Risk) and the PEG guard (Valuation).
    _expv = explosive_from_history(H)
    _infl = (str(_expv.get('verdict','')).startswith('EXPLOSIVE')
             or (isinstance(_expv.get('op_growth'),(int,float)) and _expv.get('op_growth') > 100)
             or (isinstance(_expv.get('np_growth'),(int,float)) and _expv.get('np_growth') > 100))

    # ── GROWTH
    # Option C: this name's sector median for peer-relative P/E / margins / ROE. Gated to
    # NON-BANKS (banks score on the separate validated IG2 model — provably untouched). When no
    # median for the sector (e.g. Yahoo-fallback US names + all PSX names, different taxonomy) the
    # peer_band() calls below return None and the absolute thresholds apply -> legacy behaviour.
    med = {} if is_bank else (_sector_medians().get(info.get('sector')) or {})
    _cagr_vals = {}
    for key, ser in [('rev_cagr',rev),('op_cagr',op),('np_cagr',np_)]:
        c = cagr(ser, 5)
        _cagr_vals[key] = round(c*100,1) if c is not None else None   # v2.19.0: surface the actual 5yr CAGR %
        # v2.20.0 (Fix A): BAD when the 5yr compound is NEGATIVE (revenue/profit actually shrinking) —
        # GOOD >=15%, WATCH 0..15%, BAD <0%, NA when no series (young name never penalised).
        metrics.append(mk(key, 'GOOD' if c is not None and c>=0.15 else 'BAD' if c is not None and c<0 else 'WATCH' if c is not None else 'NA', W))
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
    # v2.20.0 (Fix A): GOOD = CFO covers PAT; BAD = non-positive cumulative operating cash (earnings not cash-backed at all); WATCH = positive but below PAT.
    metrics.append(mk('ccfo_cpat', 'GOOD' if cum_cfo and cum_np and cum_cfo>cum_np else 'BAD' if (cum_cfo is not None and cum_np and cum_cfo<=0) else 'WATCH' if cum_cfo and cum_np else 'NA', W))
    metrics.append(mk('nfa_turn', trend(avg(nfat,3), avg(nfat,5)), W))
    metrics.append(mk('roe', peer_band(info.get('returnOnEquity'), med.get('roe')) or band(info.get('returnOnEquity'), 0.20, 0.10), W))

    # ── VALUATION
    metrics.append(mk('eps_trend', trend(avg(eps_s,3), avg(eps_s,5)), W))
    pe = info.get('trailingPE') or info.get('forwardPE')
    fpe = med.get('pe') or info.get('forwardPE') or 25   # Option C: peer (sector-median) P/E is the reference; else forward/25
    metrics.append(mk('pe_ratio', 'GOOD' if pe and pe>0 and pe<=fpe*1.1 else 'WATCH' if pe and pe>0 and pe<=fpe*1.3 else 'BAD' if pe and pe>0 else 'NA', W))
    # PEG: TV exposes none and Yahoo is demoted -> standard definition PE / avg-EPS-growth.
    # Only computed when a REAL EPS-growth series exists; otherwise NA (no fabricated 5% growth
    # that would wrongly flag a data-sparse fast grower as expensive).
    peg = info.get('pegRatio') or (sdiv(pe, avg_eg) if pe and pe>0 and _avg_eg_real and avg_eg and avg_eg>0 else None)
    # v2.22.0 (Fix C): PEG is meaningless when 'growth' is a one-year earnings inflection (it divides the rich
    # P/E by a 600%+ surge and reads absurdly cheap) — so it reads NA for inflection names instead of a false GOOD.
    metrics.append(mk('peg_ratio', 'NA' if _infl else 'GOOD' if peg and peg<1.0 else 'WATCH' if peg and peg<=1.5 else 'BAD' if peg else 'NA', W))
    ey = sdiv(1, pe) if (pe and pe>0) else None
    # 3-tier indicator (was binary GOOD/BAD with no middle): GOOD when earnings yield beats the
    # local bond (cheap on earnings), WATCH within ~60% of it (reasonable), BAD well below. As an
    # indicator only — a high-P/E grower reading WATCH/BAD here no longer pulls its grade down.
    metrics.append(mk('earn_yield',
        'GOOD' if ey and ey>=eff_bond else 'WATCH' if ey and ey>=eff_bond*0.6 else 'BAD' if ey else 'NA', W))
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
    # v2.28.0 CALCULATE-DON'T-GATE (owner): a company that pays no dividend has a yield of 0%%
    # -- a fact worth SHOWING, not a blank. Derive 0.0 for confirmed non-payers (div_paid known,
    # market cap known); verdict stays NA on zero so it is displayed but never counted or penalised.
    if dy is None and mktcap and mktcap > 0 and v0(div_paid) is not None:
        dy = max(0.0, (v0(div_paid) or 0.0) / mktcap)
    metrics.append(mk('div_yield', 'GOOD' if dy and dy>=0.04 else 'WATCH' if dy else 'NA', W))
    ev_eb = info.get('enterpriseToEbitda')
    metrics.append(mk('ev_ebitda', 'GOOD' if ev_eb and ev_eb<10 else 'WATCH' if ev_eb and ev_eb<15 else 'BAD' if ev_eb else 'NA', W))

    # NOTE: the 'mos' metric is appended AFTER the intrinsic-value block below, so it scores off
    # the SAME triangulated central IV (mos_pct) that the dashboard displays — not a separate
    # DCF-EPS-only value (which understated high-growth IV and wrongly read BAD).

    # ── VALUE FOR SHAREHOLDERS = net shareholder yield (div + net buyback)/mktcap.
    # As an INDICATOR only: a real cash return reads GOOD/WATCH; a company returning little or
    # nothing because it REINVESTS is NOT penalised (reinvestment is the value creation for an
    # early compounder) — negligible/zero return reads NA, never BAD, and never drags the grade.
    nsy = None
    vsh_verdict = 'NA'
    if mktcap and mktcap > 0 and (v0(div_paid) is not None or v0(buyback) is not None):
        ret_cash = (v0(div_paid) or 0) + max(0.0, (v0(buyback) or 0) - (v0(issuance) or 0))
        nsy = sdiv(ret_cash, mktcap)
        if nsy is not None and nsy > 0:
            vsh_verdict = 'GOOD' if nsy >= 0.05 else 'WATCH' if nsy >= 0.02 else 'NA'
    metrics.append(mk('val_shareholders', vsh_verdict, W))

    # ── INVENTORY
    if is_bank:
        for k in ('inv_turn','dro','fat','ccc'): metrics.append(mk(k,'NA',W))
    else:
        # v2.26.0: ultra-light fixed-asset fairness — port of scanner _score_standard v1.201.0.
        # Fixed-asset turnover (fat) presupposes physical plant; it is meaningless for an asset-light
        # software/services company, so an ULTRA-LIGHT non-bank (no meaningful inventory AND net PPE
        # < 5% of total assets) has fat set 'NA' below (dropped from score AND denominator by the
        # existing `!= NA` filter — the same net effect as the scanner's EXCL) rather than graded on
        # an irrelevant ratio. Data-driven from the company's own filings, never a sector label.
        # inv_turn/ccc already read NA naturally when inventory is absent (empty series -> NA);
        # this closes the last per-metric delta between the two engines (M2 scoring-propagation audit).
        try:
            _inv_vals = [v for v in (inv_s or []) if v is not None]
            _rev0 = next((v for v in (rev or []) if v), None)
            _light = (not _inv_vals) or bool(_rev0 and max(_inv_vals) < 0.01 * _rev0)
            _ppe0  = next((v for v in (ppe or []) if v is not None), None)
            _ta0   = next((v for v in (ta_s or []) if v is not None), None)
            _ultra = bool(_light and _ppe0 is not None and _ta0 and (_ppe0 < 0.05 * _ta0))
        except Exception:
            _light = _ultra = False
        it = safe_nfat(rev, inv_s)
        metrics.append(mk('inv_turn', trend(avg(it,3), avg(it,5)), W))
        dro = [sdiv(ar_s[i] if i<len(ar_s) else None, rev[i])*365
               if rev and i<len(rev) and rev[i] and sdiv(ar_s[i] if i<len(ar_s) else None, rev[i]) is not None
               else None for i in range(min(len(rev),6))]
        metrics.append(mk('dro', trend(avg(dro,3), avg(dro,5), hi=False), W))
        if _ultra:
            # The canonical denominator excludes a metric via verdict 'NA' (the `!= 'NA'` filter below),
            # NOT via the scanner's 'EXCL' label — so fat is set 'NA' here to be dropped from BOTH the
            # score and the denominator (identical net effect to the scanner's EXCL). An 'excl' reason
            # tag distinguishes this deliberate fairness exclusion from plain missing data on the card.
            _fat_m = mk('fat', 'NA', W); _fat_m['excl'] = 'ultra-light (net PPE < 5% of assets)'
            metrics.append(_fat_m)
        else:
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

    gp_s = [((rev[i] or 0)-((cogs[i] if cogs and i<len(cogs) else 0) or 0)) for i in range(len(rev)) if rev[i] is not None] if rev else []
    bm = beneish_m(
        v0(rev),v1(rev), v0(ar_s) or 0,v1(ar_s) or 0,
        v0(gp_s) or 0,gp_s[1] if len(gp_s)>1 else 0,
        ta0,ta1, v0(ppe) or 0,v1(ppe) or 0,
        v0(sga) or 0,v1(sga) or 0, v0(dep) or 0,v1(dep) or 0,
        ni0,cfo0, v0(ltd) or 0,v1(ltd) or 0)
    # v2.18.0 — Beneish-M reliability guard. The M-score is structurally unreliable for the very
    # profile these tabs target: (a) a name in an earnings INFLECTION (large profit surge / turnaround)
    # trips the accrual + margin + sales-growth terms and reads as "manipulation" purely because the
    # business inflected — a false positive; and (b) the computation BLOWS UP for some feeds (values in
    # the billions/trillions, far outside the real ~ -3..+3 range) on a near-zero denominator / unit error.
    # In both cases the metric now reads NA (excluded from the denominator), never a 4-pt BAD penalty, so
    # name still scores normally, preserving the genuine red-flag signal. (_infl computed once above.)
    _bm_ok = (bm is not None) and (abs(bm) <= 8) and (not _infl)
    metrics.append(mk('beneish_m', 'GOOD' if (_bm_ok and bm < -2.22) else 'WATCH' if (_bm_ok and bm < -1.78) else 'BAD' if _bm_ok else 'NA', W))

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
    # v2.20.0 (Fix A): GOOD = ROIC beats WACC; BAD = non-positive ROIC (destroying capital); WATCH = positive but below WACC.
    metrics.append(mk('roic_wacc', 'GOOD' if roic is not None and roic>wacc else 'BAD' if (roic is not None and roic<=0) else 'WATCH' if roic is not None else 'NA', W))

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
    iv_pl   = peter_lynch(avg_eg2, eps0)
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
    # Triangulated central intrinsic value = MEDIAN of the three earnings/cash/growth POWER methods
    # appropriate to a growth name: DCF·EPS (Graham-revised earnings power), DCF·FCF (2-stage on free
    # cash flow), and Peter-Lynch (PEG=1 growth value). The Graham NUMBER and the total-cash DCF are
    # EXCLUDED from the anchor — Graham-number systematically lowballs asset-light high-ROE names and
    # the cash DCF is noisy — but both stay in the expand. Median is robust to any single method.
    _core = sorted(v for v in [iv_eps, iv_dcf_fcf, iv_pl] if v and v > 0)
    if _core:
        _m = len(_core)
        iv_central = _core[_m//2] if _m % 2 else (_core[_m//2 - 1] + _core[_m//2]) / 2.0
    else:
        iv_central = iv_eps if (iv_eps and iv_eps > 0) else None
    # Data-sanity guard: if the central IV diverges from price by >10x in either direction it is
    # almost always a feed scaling error (e.g. ADR vs ordinary shares, or local-currency per-share
    # figures like TSM in TWD), not a real valuation — suppress it rather than print a misleading
    # IV / MoS. Genuinely cheap or expensive names (within 10x) are kept and shown.
    if iv_central and price and (iv_central > price * 10 or iv_central < price / 10):
        iv_central = None
    # MoS vs the central IV — SYMMETRIC and bounded to [-100%, +100%], so it discriminates instead of
    # flooring every expensive name at -100%. Cheap side (price <= IV) is the true Graham margin
    # (IV-price)/IV in 0..+100; expensive side (price > IV) is the premium relative to price
    # (IV-price)/price in -100..0 (the drawdown to fair value), e.g. a name at 2.5x IV reads -60%,
    # at 5x IV reads -80% — bounded but still ordered by how overvalued.
    if iv_central and price:
        mos_pct = ((iv_central - price) / iv_central * 100.0) if price <= iv_central \
                  else ((iv_central - price) / price * 100.0)
    else:
        mos_pct = None

    # 'mos' metric (valuation indicator) scores off the triangulated central IV — same basis as the
    # displayed MoS — so the scored margin of safety matches what the dashboard shows (percent units).
    metrics.append(mk('mos',
        'GOOD' if mos_pct is not None and mos_pct >= 25 else
        'WATCH' if mos_pct is not None and mos_pct >= 0 else
        'BAD'  if mos_pct is not None else 'NA', W))

    # A1 (DEN): ONE consistent rule for BOTH markets. NA metrics — data the engine cannot
    # yet see (a young company's missing history) or a metric that does not apply (a growth
    # non-payer's dividend yield) — are EXCLUDED from the denominator rather than scored as
    # zero, so a name is never marked weak just for being early. (Previously only banks/PSX
    # excluded NA; US non-banks divided by a fixed 162, penalising data-sparse US names like
    # ABCL/GAU.) A full-coverage US name has max_s == 162 -> pct identical to the old /162;
    # only names carrying NA metrics shift (their pct can only stay equal or rise). The
    # coverage guard below caps a thin name so it cannot earn an inflated top grade.
    for x in metrics:
        x['bucket'] = 'valuation' if x['key'] in VALUATION_KEYS else 'strength'
    applicable = [x for x in metrics if W.get(x['key'], 0) > 0]

    valuation   = None
    blended_pct = None
    if is_bank:
        # BANK PATH UNCHANGED — validated IG2 / System-B grade; valuation stays in the bank grade.
        total    = sum(pts(x['verdict'], W.get(x['key'], 0)) for x in applicable)
        max_s    = sum(W.get(x['key'], 0) for x in applicable if x['verdict'] != 'NA')
        n_meas   = sum(1 for x in applicable if x['verdict'] != 'NA')
        pct      = round(total / max_s * 100, 1) if max_s else 0.0
        coverage = round(n_meas / len(applicable), 2) if applicable else 0.0
        partial  = False
        max_out  = max_s
        bank_coverage = coverage
        blended_pct   = pct
    else:
        # NON-BANK — grade on STRENGTH only; cheapness/capital-return reported as a separate
        # indicator and NEVER folded into the grade or used to downgrade a strong business.
        s_app = [x for x in applicable if x['bucket'] == 'strength']
        v_app = [x for x in applicable if x['bucket'] == 'valuation']
        total    = sum(pts(x['verdict'], W.get(x['key'], 0)) for x in s_app)
        max_s    = sum(W.get(x['key'], 0) for x in s_app if x['verdict'] != 'NA')
        n_meas   = sum(1 for x in s_app if x['verdict'] != 'NA')
        pct      = round(total / max_s * 100, 1) if max_s else 0.0
        coverage = round(n_meas / len(s_app), 2) if s_app else 0.0
        partial  = coverage < COVERAGE_FLOOR        # strength-coverage only; valuation gaps don't flag
        max_out  = max_s
        bank_coverage = coverage if is_psx else None
        # ── valuation indicator (independent; never affects grade). High pct = cheap = Attractive.
        v_total = sum(pts(x['verdict'], W.get(x['key'], 0)) for x in v_app)
        v_max   = sum(W.get(x['key'], 0) for x in v_app if x['verdict'] != 'NA')
        v_pct   = round(v_total / v_max * 100, 1) if v_max else None
        # v2.22.0 (Fix C): a deeply-overvalued name (margin-of-safety below -50%) reads Rich regardless of the
        # ratio-mix score — the band no longer lets an expensive name show 'Fair' on a lenient ratio average.
        v_label = (None if v_pct is None else
                   'Rich' if (mos_pct is not None and mos_pct < -50) else
                   'Attractive' if v_pct >= 70 else 'Fair' if v_pct >= 45 else 'Rich')
        valuation = {'score': v_total, 'max': v_max, 'pct': v_pct, 'label': v_label,
                     'metrics': [{'key': x['key'], 'verdict': x['verdict'],
                                  'pts': x['pts'], 'max': x['max']} for x in v_app]}
        # blended all-metric score retained for transparency / continuity ONLY — not the grade.
        b_total = total + v_total
        b_max   = max_s + (v_max or 0)
        blended_pct = round(b_total / b_max * 100, 1) if b_max else pct
    if _ig2_result is not None:        # Banking IG 2.0 overrides the generic bank score
        metrics       = _ig2_result['metrics']
        total         = _ig2_result['score']
        max_out       = _ig2_result['max']
        pct           = _ig2_result['pct'] or 0.0
        _mdl_lbl      = 'US scorecard (CAMELS)' if _ig2_result.get('model') == 'us_scorecard' else 'IG2 24-ratio'
        bank_coverage = '%s (%s)' % (_mdl_lbl, _ig2_result['calib'])
        # The legacy System-B bank_inputs probe reads RAW statement line items (nii / total
        # assets / gross loans / deposits via the live fetch) — which are absent for an
        # IG2-scored bank (its data lives in bank_ig2_inputs.json, NOT the statement fetch),
        # so it printed all-null + npl/casa/car_found=false for a bank that actually scored
        # fine (e.g. AKBL 37/48). Replace it with an honest coverage echo (works for both models).
        _ig2_m = _ig2_result['metrics']
        bank_inputs = {'source': '%s inputs (%s)' % (_mdl_lbl, _ig2_result['calib']),
                       'ratios_scored': sum(1 for x in _ig2_m if x.get('verdict') != 'NA'),
                       'ratios_na':     sum(1 for x in _ig2_m if x.get('verdict') == 'NA'),
                       'ratios_total':  len(_ig2_m)}
        grade = 'A' if pct>=75 else 'B' if pct>=60 else 'C' if pct>=45 else 'FAIL'
    else:
        grade = 'A' if pct>=80 else 'B' if pct>=60 else 'C' if pct>=50 else 'FAIL'
        if partial and grade == 'A':   # A1 coverage guard: thin data cannot earn a top grade
            grade = 'B'

    # v2.23.0 (Fix D): surface EVERY metric's underlying value so each verdict on the card is
    # auditable (extends the v2.19.0 CAGR transparency to all metrics). PURELY ADDITIVE — assembled
    # from the SAME locals already used to score; never touches a verdict/pts/max/grade/valuation.
    # Wrapped so any display-value glitch can never break a score (metric_values just stays partial).
    _mvals = {}
    try:
        def _mv(k, val, unit=''):
            if isinstance(val,(int,float)) and val==val and val not in (float('inf'),float('-inf')):
                _mvals[k] = {'v': round(float(val),2), 'u': unit}
        def _mvchg(k, s, hi=True):           # trend metrics: % change of 3yr-avg vs 5yr-avg (what trend() tests)
            a3, a5 = avg(s,3), avg(s,5)
            if a3 is not None and a5 not in (None,0):
                _mvals[k] = {'v': round((a3-a5)/abs(a5)*100,1), 'u': '% vs 5y avg', 'dir': ('higher better' if hi else 'lower better')}
        # GROWTH
        for _k in ('rev_cagr','op_cagr','np_cagr'):
            if _cagr_vals.get(_k) is not None: _mvals[_k] = {'v': _cagr_vals[_k], 'u': '%/yr'}
        if opm is not None: _mv('op_margin', opm*100, '%')
        if npm is not None: _mv('np_margin', npm*100, '%')
        # STABILITY
        if tax_r is not None: _mv('tax_rate', tax_r*100, '%')
        _mv('int_coverage', int_cov, 'x')
        if de is not None: _mv('de_ratio', de, 'x')
        _mvchg('total_debt', td, hi=False)
        if cr is not None: _mv('current_ratio', cr, 'x')
        _mvchg('cfo_trend', cfo, hi=True)
        if ncc0 is not None: _mv('net_cash', ncc0, '')
        if cum_cfo and cum_np: _mv('ccfo_cpat', cum_cfo/cum_np, 'x CFO/PAT')
        _mvchg('nfa_turn', nfat, hi=True)
        if info.get('returnOnEquity') is not None: _mv('roe', info['returnOnEquity']*100, '%')
        # VALUATION
        _mvchg('eps_trend', eps_s, hi=True)
        if pe is not None: _mv('pe_ratio', pe, 'x')
        if peg is not None: _mv('peg_ratio', peg, 'x')
        if ey is not None: _mv('earn_yield', ey*100, '%')
        if pb is not None: _mv('pb_ratio', pb, 'x')
        if gv is not None: _mv('graham_val', gv, 'x PE*PB')
        if ps is not None: _mv('ps_ratio', ps, 'x')
        if dy is not None: _mv('div_yield', dy*100, '%' + (' (reinvesting)' if dy == 0 else ''))
        if ev_eb is not None: _mv('ev_ebitda', ev_eb, 'x')
        if nsy is not None: _mv('val_shareholders', nsy*100, '%' + (' (reinvesting)' if nsy <= 0 else ''))
        # INVENTORY (non-bank only — it/dro/ccc_s undefined for banks)
        if not is_bank:
            _mvchg('inv_turn', it, hi=True)
            _mvchg('dro', dro, hi=False)
            _mvchg('fat', nfat, hi=True)
            _mvchg('ccc', ccc_s, hi=False)
        # CASHFLOW
        _mvchg('fcf_trend', fcf, hi=True)
        if croic_v is not None: _mv('croic', croic_v*100, '%')
        if fcf_m is not None: _mv('fcf_sale', fcf_m*100, '%')
        _mvchg('fcf_cfo', fcf_cfo_s, hi=True)
        if cd is not None: _mv('cash_debt', cd, 'x')
        if cps is not None: _mv('cash_share', cps, '/sh')
        # RISK
        if az is not None and -10 <= az <= 25: _mv('altman_z', az, 'Z')
        if bm is not None and abs(bm) <= 8: _mv('beneish_m', bm, 'M')
        _mv('piotroski_f', pf, '/9')
        if roic is not None:
            _mvals['roic_wacc'] = {'v': round(roic*100,1), 'u': '% ROIC',
                                   'wacc': (round(wacc*100,1) if isinstance(wacc,(int,float)) else None)}
    except Exception:
        pass

    _bank_iv = bank_valuation(_ig2_in, price, 'psx' if psx_bank else 'us') if (_ig2_result is not None) else None
    return {
        'ticker': ticker, 'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector','—'), 'is_bank': is_bank, 'is_psx': is_psx, 'price': price,
        'score': total, 'pct': pct, 'grade': grade, 'metrics': metrics, 'max': max_out, 'ver': IM3_VERSION,
        'bank_coverage': bank_coverage, 'bank_inputs': bank_inputs,
        'coverage': (None if is_bank else coverage), 'partial': partial,
        'valuation': valuation, 'blended_pct': blended_pct,
        'src': {'fund': info.get('_tv') and 'tv' or 'yahoo', 'hist': H.get('source')},
        'explosive': _expv,
        'cagr_pct': _cagr_vals,
        'metric_values': _mvals,
        'piotroski': pf, 'altman_z': round(az,2) if (az is not None and -10 <= az <= 25) else None,
        'beneish_m': round(bm,2) if (bm is not None and abs(bm) <= 8) else None,
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
            'central':       round(iv_central,2)   if iv_central   else None,
            'peg':           round(peg,2)          if peg          else None,
            'mos_pct':       round(mos_pct,1)      if mos_pct is not None else None,
            'mos_fcf_pct':   round(iv_fcf_mos,1)   if (iv_fcf_mos  is not None and -150 <= iv_fcf_mos  <= 150) else None,
            'mos_cash_pct':  round(iv_cash_mos,1)  if (iv_cash_mos is not None and -150 <= iv_cash_mos <= 150) else None,
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
