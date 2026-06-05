"""
PARALLEL US screen v2 — diagnostic. Tests two fixes vs v1:
  (1) revenue-growth filter on total_revenue_yoy_growth_FQ (quarterly YoY) to
      match Yahoo's MRQ `revenueGrowth`, instead of the TTM field that dropped AMZN etc.
  (2) exclude OTC (foreign 'F' tickers) via the exchange column.
Cleanly isolates SCREEN from the noisy insider pass: tests whether TV's pre-insider
set CONTAINS your 182 Yahoo survivors (they already passed insider, so they must pass
rev_growth+universe). No yfinance, no insider pass -> no Yahoo 502 noise.
Then attributes every miss. Run:  python us_tv_screen.py
"""
import requests, time, json
import scanner   # exact constants + large_cap_set + data.json survivors

UA="Mozilla/5.0"
MAIN_EXCH = {'NASDAQ','NYSE','AMEX','NYSE ARCA','BATS','NYSE MKT','NYSEARCA'}
SCAN_COLS = ['name','market_cap_basic','exchange','sector',
             'total_revenue_yoy_growth_fq','total_revenue_yoy_growth_ttm']

def build_payload(start,end):
    return {
      "columns": SCAN_COLS,
      "filter": [
        {"left":"type","operation":"equal","right":"stock"},
        {"left":"market_cap_basic","operation":"egreater","right":scanner.US_SMALL_CAP_MIN},
        {"left":"total_revenue_yoy_growth_fq","operation":"egreater",
         "right":scanner.US_REV_GROWTH_MIN*100},   # QUARTERLY YoY, matches Yahoo MRQ
      ],
      "sort":{"sortBy":"market_cap_basic","sortOrder":"desc"},
      "range":[start,end], "markets":["america"],
    }
def bare(s): return s.split(':')[-1]
def passes_band(mcap,t,L):
    if not mcap or mcap<=0: return False
    if t in L: return True
    return scanner.US_SMALL_CAP_MIN <= mcap <= scanner.US_SMALL_CAP_MAX
def on_main_exch(exch): return (exch or '') in MAIN_EXCH

# ---- runner ----
def fetch_screen(page=500,cap=8000):
    rows,start=[],0
    while start<cap:
        r=requests.post("https://scanner.tradingview.com/america/scan",
                        json=build_payload(start,start+page),headers={"User-Agent":UA},timeout=40)
        if r.status_code!=200: print("  TV HTTP",r.status_code,r.text[:120]); break
        b=r.json().get('data',[])
        for d in b:
            rec=dict(zip(SCAN_COLS,d['d'])); rec['ticker']=bare(d['s']); rows.append(rec)
        if len(b)<page: break
        start+=page
    return rows

def fetch_named(tickers):
    """pull ttm+fq+exchange+sector for specific names to attribute misses"""
    cols=['total_revenue_yoy_growth_fq','total_revenue_yoy_growth_ttm','exchange','sector','market_cap_basic']
    p={"symbols":{"tickers":[],"query":{"types":["stock"]}},"columns":cols,
       "filter":[{"left":"name","operation":"in_range","right":tickers}],
       "range":[0,len(tickers)+10],"markets":["america"]}
    r=requests.post("https://scanner.tradingview.com/america/scan",json=p,headers={"User-Agent":UA},timeout=40)
    out={}
    if r.status_code==200:
        for d in r.json().get('data',[]): out[bare(d['s'])]=dict(zip(cols,d['d']))
    return out

def classify_miss(name, info, L):
    if info is None: return "not in TV america universe"
    fq=info.get('total_revenue_yoy_growth_fq'); ttm=info.get('total_revenue_yoy_growth_ttm')
    sec=(info.get('sector') or ''); exch=info.get('exchange')
    if not on_main_exch(exch): return f"OTC/other exch ({exch})"
    if fq is None:
        return "rev_growth_fq NULL" + (" [financial]" if 'Financ' in sec else "")
    if fq < scanner.US_REV_GROWTH_MIN*100:
        return f"fq below 15% (fq={fq:.0f}, ttm={ttm if ttm is None else round(ttm)})"
    return "SHOULD pass now (fq>=15, main exch) — was TTM/insider artifact"

def main():
    L=scanner.us_large_cap_set()
    print("v2 screen: rev_growth on QUARTERLY field, OTC excluded...")
    t=time.time(); rows=fetch_screen(); print(f"  TV returned {len(rows)} rows in {time.time()-t:.1f}s")
    pre=set(r['ticker'] for r in rows
            if passes_band(r.get('market_cap_basic'),r['ticker'],L) and on_main_exch(r.get('exchange')))
    print(f"  TV pre-insider set (band + main-exch): {len(pre)}")
    d=json.load(open('data.json')); yahoo=set(c['ticker'] for c in d.get('explosive_us',[]))
    contained=yahoo & pre; misses=sorted(yahoo - pre)
    print(f"\n=== Does TV (fq field) CONTAIN your {len(yahoo)} Yahoo survivors? ===")
    print(f"  contained: {len(contained)}/{len(yahoo)}  ({100*len(contained)//len(yahoo)}%)   misses: {len(misses)}")
    if misses:
        print("\n  attributing misses (pulling their TV ttm/fq/exchange)...")
        info=fetch_named(misses)
        from collections import Counter
        reasons=Counter()
        for m in misses:
            r=classify_miss(m, info.get(m), L); reasons[r.split(' [')[0].split(' (')[0]]+=1
            if len(misses)<=60: print(f"    {m:7s} {r}")
        print("\n  miss reasons:"); 
        for k,v in reasons.most_common(): print(f"    {v:3d}  {k}")
    print("\nIf contained ~ near 182 with fq field -> definition fix works, switchable (keep insider pass).")
if __name__=='__main__': main()
