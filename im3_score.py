"""
IM3 162-Point Stock Scorer — Free, uses yfinance only
======================================================
Usage:
    python im3_score.py RBB
    python im3_score.py RBB MCB LOB AROW WSBF BWB PCB KRNY WTBA AVAH

Install once:  pip install yfinance
"""

import sys, math, time

try:
    import yfinance as yf
except ImportError:
    print("ERROR: Run this first:  pip install yfinance")
    sys.exit(1)

# ── CONSTANTS ────────────────────────────────────────────────────────────────
BOND = 0.043  # US 10Y ~4.3%

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
BANK_ZERO  = ('int_coverage','current_ratio','inv_turn','dro','fat','ccc')
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

# ── HELPERS ──────────────────────────────────────────────────────────────────
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

def gs(df, keys, n=6):
    if df is None or df.empty: return []
    for k in (keys if isinstance(keys, list) else [keys]):
        for idx in df.index:
            if k.lower() in str(idx).lower():
                vals = []
                for v in df.loc[idx].values[:n]:
                    try:
                        fv = float(v)
                        vals.append(None if math.isnan(fv) else fv)
                    except: vals.append(None)
                if any(v is not None for v in vals): return vals
    return []

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

# ── MAIN SCORER ──────────────────────────────────────────────────────────────
def score_ticker(ticker):
    print(f"  Fetching {ticker}...", flush=True)
    t = yf.Ticker(ticker)

    try:    info = t.info or {}
    except: info = {}

    def get_df(attr):
        try:
            df = getattr(t, attr)
            if df is not None and not df.empty:
                df = df.copy()
                df.index = df.index.astype(str).str.lower().str.strip()
                return df
        except: pass
        return None

    inc = get_df('income_stmt')
    bal = get_df('balance_sheet')
    cf  = get_df('cashflow')

    # Bank detection — only actual deposit-taking banks, not all financials
    sec = (info.get('sector','') + ' ' + info.get('industry','')).lower()
    BANK_INDUSTRIES = ('banks—regional','banks—diversified','savings institutions',
                       'banks - regional','banks - diversified','savings institution',
                       'thrift','bancorp','bancshares','bancshare')
    NONBANK_OVERRIDE = ('software','technology','biotech','pharmaceutical',
                        'lending','marketplace','business development',
                        'asset management','investment','insurance','reit',
                        'capital corp','lending tree')
    is_bank = (any(k in sec for k in BANK_INDUSTRIES)
               and not any(k in sec for k in NONBANK_OVERRIDE))
    # Manual overrides — known non-bank financials that yfinance misclassifies
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

    # ── Fetch all series
    rev   = gs(inc,['total revenue','totalrevenue','revenue'])
    op    = gs(inc,['operating income','ebit','operatingincome'])
    np_   = gs(inc,['net income','netincome'])
    eps_s = gs(inc,['diluted eps','basic eps','eps diluted'])
    if not eps_s and info.get('trailingEps'): eps_s = [info['trailingEps']]
    cogs  = gs(inc,['cost of revenue','cost of goods sold','costofrevenue'])
    sga   = gs(inc,['selling general administrative','sga','operatingexpenses'])
    tax_exp = gs(inc,['tax provision','income tax expense','incometaxexpense'])
    pbt     = gs(inc,['pretax income','income before tax','incomebeforetax'])
    ebitda_s= gs(inc,['ebitda','normalized ebitda'])
    int_exp = gs(inc,['interest expense','interestexpense'])
    nii     = gs(inc,['net interest income','netinterestincome'])

    ppe   = gs(bal,['net ppe','property plant equipment net','netppe','property plant and equipment'])
    td    = gs(bal,['long term debt','total debt','longtermdebt','totaldebt'])
    ltd   = gs(bal,['long term debt','longtermdebt'])
    eq0s  = gs(bal,['stockholders equity','total stockholders equity','stockholdersequity'])
    ta_s  = gs(bal,['total assets','totalassets'])
    ca_s  = gs(bal,['current assets','total current assets','currentassets'])
    cl_s  = gs(bal,['current liabilities','total current liabilities','currentliabilities'])
    re_s  = gs(bal,['retained earnings','retainedearnings'])
    ar_s  = gs(bal,['accounts receivable','net receivables','accountsreceivable'])
    ap_s  = gs(bal,['accounts payable','accountspayable'])
    inv_s = gs(bal,['inventory','inventories'])
    cash_s= gs(bal,['cash and cash equivalents','cash','cashandcashequivalents'])
    sti_s = gs(bal,['short term investments','other short term investments'])
    loans = gs(bal,['net loans','loans','totalloans'])
    deps  = gs(bal,['total deposits','deposits','totaldeposits'])
    npl_s = gs(bal,['nonperforming loans','allowance for loan losses','allowanceforloanlosses'])

    cfo   = gs(cf,['operating cash flow','total cash from operating activities',
                   'cashfromoperations','operatingcashflow'])
    fcf   = gs(cf,['free cash flow','freecashflow'])
    ncc   = gs(cf,['changes in cash','net change in cash','netchangeincash'])
    dep   = gs(cf,['depreciation','depreciation and amortization','depreciationandamortization'])

    # ── Key scalars (all None-safe)
    def v0(s): return s[0] if s else None
    def v1(s): return s[1] if len(s) > 1 else None

    td0=v0(td); eq00=v0(eq0s); ta0=v0(ta_s); ta1=v1(ta_s)
    ca0=v0(ca_s); cl0=v0(cl_s); re0=v0(re_s); op0=v0(op)
    ni0=v0(np_); cfo0=v0(cfo); fcf0=v0(fcf); eps0=v0(eps_s) or info.get('trailingEps')
    tc0 = (v0(cash_s) or 0) + (v0(sti_s) or 0) if cash_s or sti_s else None
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
    peg = info.get('pegRatio') or info.get('trailingPegRatio')
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
    metrics.append(mk('val_shareholders', trend(avg(eps_s,3), avg(eps_s,5)), W))

    # ── INVENTORY
    if is_bank:
        for k in ('inv_turn','dro','fat','ccc'): metrics.append(mk(k,'NA',W))
    else:
        it = safe_nfat(rev, inv_s)  # reuse same safe pattern
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

    # ── INTRINSIC VALUES
    bvps    = info.get('bookValue')
    iv_eps  = dcf_eps(eps0, avg_eg)
    iv_gr   = graham_iv(eps0, bvps)
    iv_pl   = peter_lynch(peg, avg_eg2, eps0)
    ivs     = [v for v in [iv_eps,iv_gr,iv_pl] if v and v > 0]
    iv_comp = avg(ivs)
    mos_pct = sdiv((iv_comp-price), iv_comp)*100 if iv_comp and price else None

    total = sum(x['pts'] for x in metrics)
    pct   = round(total/162*100, 1)
    grade = 'A' if pct>=75 else 'B' if pct>=60 else 'C' if pct>=50 else 'FAIL'

    return {
        'ticker': ticker, 'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector','—'), 'is_bank': is_bank, 'price': price,
        'score': total, 'pct': pct, 'grade': grade, 'metrics': metrics,
        'piotroski': pf, 'altman_z': round(az,2) if az else None,
        'beneish_m': round(bm,2) if bm else None,
        'iv': {
            'dcf_eps':    round(iv_eps,2)  if iv_eps  else None,
            'graham':     round(iv_gr,2)   if iv_gr   else None,
            'peter_lynch':round(iv_pl,2)   if iv_pl   else None,
            'composite':  round(iv_comp,2) if iv_comp else None,
            'mos_pct':    round(mos_pct,1) if mos_pct is not None else None,
        },
    }

# ── DISPLAY ──────────────────────────────────────────────────────────────────
SYM = {'GOOD':'[OK]','WATCH':'[~~]','BAD':'[!!]','NA':'[--]'}

def print_result(r):
    fill = int(r['pct']/100*40)
    bar  = '#'*fill + '-'*(40-fill)
    print()
    print('='*65)
    print(f"  {r['ticker']}  {r['name']}")
    print(f"  {r['sector']}" + ('  [BANK]' if r['is_bank'] else ''))
    if r['price']: print(f"  Price: ${r['price']}")
    print('='*65)
    print(f"  SCORE : {r['score']} / 162  ({r['pct']}%)")
    print(f"  GRADE : {r['grade']}  [{bar}]")
    if r['altman_z']:  print(f"  Altman Z   : {r['altman_z']}  ({'SAFE' if r['altman_z']>2.6 else 'GREY' if r['altman_z']>1.1 else 'DISTRESS'})")
    if r['beneish_m']: print(f"  Beneish M  : {r['beneish_m']}  ({'CLEAN' if r['beneish_m']<-2.22 else 'GREY' if r['beneish_m']<-1.78 else 'MANIPULATOR'})")
    print(f"  Piotroski F: {r['piotroski']} / 7")

    iv = r['iv']
    print()
    print('  INTRINSIC VALUES:')
    if iv['dcf_eps']:    print(f"    DCF EPS     : ${iv['dcf_eps']}")
    if iv['graham']:     print(f"    Graham      : ${iv['graham']}")
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
        sp = sum(x['pts'] for x in sec_m)
        sm = sum(x['max'] for x in sec_m)
        print()
        print(f"  -- {sec_name}  {sp}/{sm} --")
        for mx in sec_m:
            sym = SYM.get(mx['verdict'],'[--]')
            lbl = LABELS.get(mx['key'], mx['key'])
            print(f"    {sym}  {lbl:<38}  {mx['pts']:2}/{mx['max']:2}")
    print()
    print('='*65)

# ── ENTRY POINT ──────────────────────────────────────────────────────────────
def main():
    import json as _json

    args = sys.argv[1:]
    json_mode = '--json' in args
    args = [a for a in args if a != '--json']

    if not args:
        if json_mode:
            print('[]')
            return
        print('\nIM3 162-Point Stock Scorer')
        print('Usage: python im3_score.py RBB MCB LOB')
        print('       python im3_score.py --json RBB MCB LOB  (outputs JSON)')
        print()
        inp = input('Enter ticker(s): ').strip().upper()
        args = inp.split()

    tickers = [a.upper() for a in args if not a.startswith('--')]

    if not json_mode:
        print(f"\nScoring: {', '.join(tickers)}")
        print("~15 seconds per stock\n")

    results = []
    for tk in tickers:
        try:
            r = score_ticker(tk)
            if json_mode:
                results.append(r)
            else:
                print_result(r)
                results.append(r)
        except Exception as e:
            if json_mode:
                results.append({'ticker': tk, 'error': str(e)})
            else:
                import traceback; traceback.print_exc()
                print(f"\n  ERROR {tk}: {e}")
        if len(tickers) > 1 and not json_mode:
            time.sleep(1)

    if json_mode:
        print(_json.dumps(results, default=str))
        return

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
