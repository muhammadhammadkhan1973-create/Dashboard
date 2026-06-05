"""
RUNNER PROBE — run on GitHub Actions (reaches scanner.tradingview.com).
Answers, in ONE run, the things the sandbox can't reach:
  CHECK 1  Can the TradingView `america` scanner carry US screening?
           (full column set, per-column population %, count + timing)
  CHECK 2  Do US analyst fields populate for holdings + TCE watchlist?
  CHECK 3  Are commodities + FX available for metals/WTI/FX redundancy?
Drop in repo root, run once:  python tv_scan_probe.py
"""
import requests, time, json
H = {"User-Agent": "Mozilla/5.0"}

# ---- column set TCE + Explosive + analyst + IG would consume from TV ----
COLS = ['name','close','volume','relative_volume_10d_calc','market_cap_basic',
        'Perf.W','Perf.1M','Perf.3M','Perf.6M','Perf.Y','Perf.YTD',
        'total_revenue_yoy_growth_ttm','earnings_per_share_diluted_yoy_growth_ttm',
        'gross_margin_ttm','operating_margin_ttm','net_margin_ttm',
        'price_earnings_ttm','return_on_equity',
        'Recommend.All','RSI',
        'price_target_average','price_target_1y_delta',
        'recommendation_mark','recommendation_buy','recommendation_total',
        'earnings_per_share_forecast_next_fq','revenue_forecast_next_fq','sector']

def pct_pop(rows, cols):
    n=len(rows) or 1
    return {c: round(100*sum(1 for r in rows if r['d'][i] not in (None,'') )/n) for i,c in enumerate(cols)}

print("="*60,"\nCHECK 1: america universe pull (filtered, top 200 by volume)\n","="*60)
payload1 = {
  "columns": COLS,
  "filter": [
    {"left":"type","operation":"equal","right":"stock"},
    {"left":"market_cap_basic","operation":"egreater","right":2_000_000_000},
    {"left":"volume","operation":"egreater","right":500_000},
  ],
  "sort": {"sortBy":"volume","sortOrder":"desc"},
  "range":[0,200],
  "markets":["america"],
}
t=time.time()
r=requests.post("https://scanner.tradingview.com/america/scan",json=payload1,headers=H,timeout=40)
dt=time.time()-t
print("HTTP",r.status_code,"in %.1fs"%dt)
if r.status_code==200:
    j=r.json(); rows=j.get('data',[]); print("rows returned:",len(rows),"of totalCount",j.get('totalCount'))
    pop=pct_pop(rows,COLS)
    print("\nper-column population %:")
    for c in COLS: print(f"  {c:42s} {pop[c]:3d}%")
else:
    print("body:",r.text[:200])

print("\n"+"="*60,"\nCHECK 2: analyst coverage on YOUR US names\n","="*60)
US = ['XOM','CVX','COP','EOG','GOOGL','MSFT','META','UNH','GIS','KO',   # holdings
      'NVDA','AMD','KLAC','MU','AAPL']                                   # TCE watchlist
acols=['close','price_target_average','price_target_1y_delta','recommendation_mark',
       'recommendation_buy','recommendation_total','earnings_per_share_forecast_next_fq',
       'revenue_forecast_next_fq']
# america tickers need exchange prefix; query without prefix via symbol set 'query'
payload2={"symbols":{"tickers":[],"query":{"types":["stock"]}},
          "columns":acols,
          "filter":[{"left":"name","operation":"in_range","right":US}],
          "range":[0,50],"markets":["america"]}
r2=requests.post("https://scanner.tradingview.com/america/scan",json=payload2,headers=H,timeout=30)
print("HTTP",r2.status_code)
if r2.status_code==200:
    rows=r2.json().get('data',[])
    print(f"{'TICKER':8s}{'TARGET':>10s}{'1Y_DELTA':>10s}{'REC_MK':>8s}{'BUY/TOT':>9s}{'FWD_EPS':>9s}")
    cov=0
    for d in rows:
        v=dict(zip(acols,d['d'])); nm=d['s'].split(':')[-1]
        c=v['price_target_average'] not in (None,'') or (v['recommendation_total'] or 0)>0
        cov+=c
        print(f"{nm:8s}{str(v['price_target_average']):>10s}{str(v['price_target_1y_delta']):>10s}"
              f"{str(v['recommendation_mark']):>8s}{str(v['recommendation_buy'])+'/'+str(v['recommendation_total']):>9s}"
              f"{str(v['earnings_per_share_forecast_next_fq']):>9s}")
    print(f"covered {cov}/{len(rows)}  (expect ~all — FactSet covers US heavily)")

print("\n"+"="*60,"\nCHECK 3: commodities + FX redundancy\n","="*60)
def quote(market, tickers):
    p={"symbols":{"tickers":tickers},"columns":["close","change"]}
    rr=requests.post(f"https://scanner.tradingview.com/{market}/scan",json=p,headers=H,timeout=30)
    print(f"  /{market}/scan HTTP {rr.status_code}: ", end="")
    if rr.status_code==200:
        for d in rr.json().get('data',[]):
            print(f"{d['s']}={d['d'][0]}", end="  ")
    print()
quote("futures",["NYMEX:CL1!","ICEEUR:BRN1!","COMEX:GC1!","COMEX:SI1!","COMEX:HG1!"])  # WTI Brent gold silver copper
quote("forex",["TVC:DXY","FX_IDC:USDPKR"])                                              # dollar index, USD/PKR
print("\nIf CHECK1 cols ~100%, CHECK2 covered≈all, CHECK3 returns prices ->")
print("TV can carry US screening + analyst revisions + commodity/FX fallback.")
