"""
PARALLEL US screen via TradingView `america` — runs ALONGSIDE the Yahoo screen
to PROVE equivalence before any switch. Reuses scanner.py's exact gate constants
and large-cap set, so it's a true replica (not a guess).

Design (hybrid — TV lacks insider %):
  1. TV server-side filter: type=stock, mcap >= 300M, rev_growth >= 15%   (full universe, seconds, NO Yahoo)
  2. band gate (client): keep if mcap <= 2B  OR  ticker in large_cap_set   (exact current logic)
  3. insider gate: thin yfinance pass on SURVIVORS only (heldPercentInsiders >= 5%)
  4. diff TV survivors vs the 182 Yahoo survivors in data.json['explosive_us']

Run on the runner:  python us_tv_screen.py
"""
import requests, time, json, math
import scanner   # exact constants + large_cap_set + EXISTING; safe (no scan at import)

UA = "Mozilla/5.0"
SCAN_COLS = ['name','market_cap_basic','total_revenue_yoy_growth_ttm',
             'earnings_per_share_diluted_yoy_growth_ttm','close','sector','industry']

# ---------- pure logic (unit-tested in sandbox) ----------
def build_payload(start, end):
    return {
      "columns": SCAN_COLS,
      "filter": [
        {"left":"type","operation":"equal","right":"stock"},
        {"left":"market_cap_basic","operation":"egreater","right":scanner.US_SMALL_CAP_MIN},
        {"left":"total_revenue_yoy_growth_ttm","operation":"egreater",
         "right":scanner.US_REV_GROWTH_MIN*100},   # TV rev_growth is in %, Yahoo 0.15 -> 15
      ],
      "sort": {"sortBy":"market_cap_basic","sortOrder":"desc"},
      "range":[start,end], "markets":["america"],
    }

def bare(sym):                      # 'NASDAQ:NVDA' -> 'NVDA'
    return sym.split(':')[-1]

def passes_band(mcap, ticker, large_set):
    """Exact replica of screen_us_stock band logic."""
    if mcap is None or mcap <= 0: return False
    if ticker in large_set: return True            # large-cap set bypasses ceiling
    return scanner.US_SMALL_CAP_MIN <= mcap <= scanner.US_SMALL_CAP_MAX

def diff_sets(tv, yahoo):
    tv, yahoo = set(tv), set(yahoo)
    return {'overlap': sorted(tv & yahoo), 'tv_only': sorted(tv - yahoo),
            'yahoo_only': sorted(yahoo - tv),
            'n_tv': len(tv), 'n_yahoo': len(yahoo), 'n_overlap': len(tv & yahoo)}

# ---------- runner-only (network) ----------
def tv_fetch_all(page=500, cap=6000):
    rows, start = [], 0
    while start < cap:
        r = requests.post("https://scanner.tradingview.com/america/scan",
                          json=build_payload(start, start+page), headers={"User-Agent":UA}, timeout=40)
        if r.status_code != 200:
            print("  TV HTTP", r.status_code, r.text[:150]); break
        batch = r.json().get('data', [])
        for d in batch:
            rec = dict(zip(SCAN_COLS, d['d'])); rec['ticker'] = bare(d['s'])
            rows.append(rec)
        if len(batch) < page: break
        start += page
    return rows

def insider_confirm(tickers):
    import yfinance as yf
    kept, calls = [], 0
    for tk in tickers:
        calls += 1
        try:
            ins = yf.Ticker(tk).info.get('heldPercentInsiders', 0) or 0
            if ins >= 0.05: kept.append(tk)
        except Exception:
            pass
    return kept, calls

def main():
    large = scanner.us_large_cap_set()
    print("Pulling TV america universe (mcap>=300M, rev_growth>=15%)...")
    t=time.time(); rows = tv_fetch_all(); print(f"  TV returned {len(rows)} rows in {time.time()-t:.1f}s (server-filtered)")
    banded = [r['ticker'] for r in rows if passes_band(r.get('market_cap_basic'), r['ticker'], large)]
    print(f"  after band gate: {len(banded)} (small-caps in band + named large-caps)")
    print(f"  insider gate via yfinance on {len(banded)} survivors (was ~1467 full-universe calls)...")
    t=time.time(); tv_final, calls = insider_confirm(banded)
    print(f"  -> {len(tv_final)} TV survivors  |  {calls} yfinance calls in {time.time()-t:.1f}s")

    d = json.load(open('data.json'))
    yahoo = [c['ticker'] for c in d.get('explosive_us', [])]    # the 182 full Yahoo survivors
    res = diff_sets(tv_final, yahoo)
    print("\n=== TV vs Yahoo survivors ===")
    print(f"  TV {res['n_tv']}  |  Yahoo {res['n_yahoo']}  |  overlap {res['n_overlap']}")
    print(f"  Yahoo-only (TV missed): {len(res['yahoo_only'])} -> {res['yahoo_only'][:25]}")
    print(f"  TV-only (broader universe): {len(res['tv_only'])} -> {res['tv_only'][:25]}")
    print("\nGOAL: Yahoo-only should be small. Each Yahoo-only name = investigate (rev_growth")
    print("definition diff, or TV universe gap). TV-only = names the CSV universe missed (upside).")

if __name__ == '__main__':
    main()
