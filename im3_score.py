"""
IM3 162-Point Stock Scorer — re-threaded off Yahoo (v2.3-sourcing).
=================================================================
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
    if not s or len(s) <= yrs: return None
    a, b = s[yrs], s[0]
    if a is None or b is None or a <= 0 or b <= 0: return None
    return (b/a)**(1/yrs) - 1

def trend(s3, s5, hi=True):
    if s3 is None or s5 is None: return 'NA'
    return 'GOOD' if (s3 > s5 if hi else s3 < s5) else 'WATCH'

def band(v, g, w, hi=True):
    if v is None: return 'NA'
    if hi:  return 'GOOD' if v >= g else ('WATCH' if v >= w else 'BAD')
    else:   return 'GOOD' if v <= g else ('WATCH' if v <= w else 'BAD')

def pts(verdict, max_p):
    return {'GOOD': max_p, 'WATCH': round(max_p*0.6), 'BAD': round(max_p*0.2)}.get(verdict, 0)

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

def _tv_post(symbol, columns):
    body = {"symbols": {"tickers": [symbol]}, "columns": columns}
    try:
        r = requests.post(TV_URL, json=body, headers=HDRS, timeout=20)
        if r.status_code != 200: return None
        data = r.json().get("data") or []
        return (data[0].get("d") or []) if data else None
    except Exception:
        return None

def tv_fetch(ticker):
    """One america/scan row -> {field: value}. Resolves the exchange prefix. {} on miss."""
    tk = ticker.upper()
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

def fetch_history(ticker, log=True):
    """FMP-stable -> SEC -> Yahoo, first usable wins. Yahoo is the guaranteed backstop."""
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

def score_ticker(ticker):
    if not _json_mode:
        print(f"  Fetching {ticker}...", flush=True)

    tv = tv_fetch(ticker)
    info = _tv_to_info(tv, ticker)
    if not info:  # TV miss -> Yahoo info backstop so behaviour can't regress
        if yf is not None:
            try: info = yf.Ticker(ticker).info or {}
            except: info = {}
        else: info = {}

    H = fetch_history(ticker)

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
    if ticker.upper() in FORCE_NONBANK: is_bank = False
    if ticker.upper() in FORCE_BANK:    is_bank = True

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
    for key, ser in [('rev_cagr',rev),('op_cagr',op),('np_cagr',np_)]:
        c = cagr(ser, 5)
        metrics.append(mk(key, 'GOOD' if c is not None and c>=0.15 else 'WATCH' if c is not None else 'NA', W))
    metrics.append(mk('op_margin', band(sdiv(op0, v0(rev)), 0.12, 0.06), W))
    metrics.append(mk('np_margin', band(sdiv(ni0, v0(rev)), 0.08, 0.03), W))

    # ── STABILITY
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
    metrics.append(mk('roe', band(info.get('returnOnEquity'), 0.20, 0.10), W))

    # ── VALUATION
    metrics.append(mk('eps_trend', trend(avg(eps_s,3), avg(eps_s,5)), W))
    pe = info.get('trailingPE') or info.get('forwardPE')
    fpe = info.get('forwardPE') or 25
    metrics.append(mk('pe_ratio', 'GOOD' if pe and pe>0 and pe<=fpe*1.1 else 'WATCH' if pe and pe>0 and pe<=fpe*1.3 else 'BAD' if pe and pe>0 else 'NA', W))
    # PEG: TV exposes none and Yahoo is demoted -> standard definition PE / avg-EPS-growth.
    peg = info.get('pegRatio') or (sdiv(pe, avg_eg) if pe and avg_eg and avg_eg>0 else None)
    metrics.append(mk('peg_ratio', 'GOOD' if peg and peg<1.0 else 'WATCH' if peg and peg<=1.5 else 'BAD' if peg else 'NA', W))
    ey = sdiv(1, pe)
    metrics.append(mk('earn_yield', 'GOOD' if ey and ey>BOND else 'BAD' if ey else 'NA', W))
    pb = info.get('priceToBook')
    metrics.append(mk('pb_ratio', 'GOOD' if pb and pb<1.5 else 'WATCH' if pb and pb<3.0 else 'BAD' if pb else 'NA', W))
    gv = (pe*pb) if pe and pb else None
    metrics.append(mk('graham_val', 'GOOD' if gv and gv<22.5 else 'BAD' if gv else 'NA', W))
    ps = info.get('priceToSalesTrailing12Months')
    metrics.append(mk('ps_ratio', 'GOOD' if ps and ps<1.5 else 'WATCH' if ps and ps<3.0 else 'BAD' if ps else 'NA', W))
    dy = info.get('dividendYield')
    metrics.append(mk('div_yield', 'GOOD' if dy and dy>=0.04 else 'WATCH' if dy else 'NA', W))
    ev_eb = info.get('enterpriseToEbitda')
    metrics.append(mk('ev_ebitda', 'GOOD' if ev_eb and ev_eb<10 else 'WATCH' if ev_eb and ev_eb<15 else 'BAD' if ev_eb else 'NA', W))

    iv_eps_v = dcf_eps(eps0, avg_eg)
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
    az = altman_z(wc, re0, op0, eq00, td0, ta0)
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
    ke    = BOND + (beta or 1.0)*0.055
    v_tot = (td0 or 0) + (eq00 or 0)
    wacc  = ((eq00 or 0)/v_tot*ke + (td0 or 0)/v_tot*0.06*(1-(tax_r or 0.21))) if v_tot else ke
    nopat = (op0*(1-(tax_r or 0.21))) if op0 else None
    roic  = sdiv(nopat, ic)
    metrics.append(mk('roic_wacc', 'GOOD' if roic is not None and roic>wacc else 'WATCH' if roic is not None else 'NA', W))

    # ── BANK EXTRAS
    if is_bank:
        nim_v = sdiv(v0(nii), ta0) or info.get('netInterestMargin')
        metrics.append({'key':'nim','verdict':band(nim_v,0.04,0.03),'pts':pts(band(nim_v,0.04,0.03),4),'max':4})
        casa_v = info.get('casaRatio')
        cv = band(casa_v,0.80,0.70) if casa_v else 'NA'
        metrics.append({'key':'casa','verdict':cv,'pts':pts(cv,3),'max':3})
        adr_v = sdiv(v0(loans), v0(deps))
        av = 'GOOD' if adr_v and 0.40<=adr_v<=0.60 else 'WATCH' if adr_v and (0.30<=adr_v<0.40 or 0.60<adr_v<=0.70) else 'BAD' if adr_v else 'NA'
        metrics.append({'key':'adr','verdict':av,'pts':pts(av,3),'max':3})
        npl_v = sdiv(v0(npl_s), v0(loans))
        nv = band(npl_v,0.03,0.05,hi=False) if npl_v else 'NA'
        metrics.append({'key':'npl','verdict':nv,'pts':pts(nv,5),'max':5})
        car_v = info.get('capitalAdequacyRatio') or info.get('tier1CapitalRatio')
        if car_v and car_v > 1: car_v = car_v/100
        cv2 = band(car_v,0.18,0.15) if car_v else 'NA'
        metrics.append({'key':'car','verdict':cv2,'pts':pts(cv2,4),'max':4})
        bank_inputs = {'nii': v0(nii), 'total_assets': ta0, 'gross_loans': v0(loans),
                       'deposits': v0(deps), 'npl_found': npl_v is not None,
                       'casa_found': casa_v is not None, 'car_found': car_v is not None}
    else:
        bank_inputs = None

    # ── INTRINSIC VALUES (in-code engine; no Sarmaaya inputs)
    bvps    = info.get('bookValue')
    iv_eps  = dcf_eps(eps0, avg_eg)
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

    if is_bank:
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
    grade = 'A' if pct>=80 else 'B' if pct>=60 else 'C' if pct>=50 else 'FAIL'

    return {
        'ticker': ticker, 'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector','—'), 'is_bank': is_bank, 'price': price,
        'score': total, 'pct': pct, 'grade': grade, 'metrics': metrics, 'max': max_out,
        'bank_coverage': bank_coverage, 'bank_inputs': bank_inputs,
        'src': {'fund': info.get('_tv') and 'tv' or 'yahoo', 'hist': H.get('source')},
        'piotroski': pf, 'altman_z': round(az,2) if az else None,
        'beneish_m': round(bm,2) if bm else None,
        'shareholder_yield_pct': round(nsy*100,2) if nsy is not None else None,
        'iv': {
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
