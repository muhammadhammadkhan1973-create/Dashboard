#!/usr/bin/env python3
"""
bench_dh0.py  —  Wave DH-0 price-history benchmark (runner-side, READ-ONLY)

Purpose: the sandbox can't reach Yahoo, so this standalone harness times the
real fetch paths ON YOUR GITHUB ACTIONS RUNNER to settle DH-0 with numbers.

It does NOT import or touch scanner.py / data.json / the TCE ledger. It only
times yfinance the way the scanner uses it, then prints seconds + coverage.

It answers three questions:
  Q1  How long does PER-NAME .history() take vs ONE yf.download() batch?
      (confirms the v1.111.0 batch is the right call, and by how much)
  Q2  Same for PSX .KA names (Yahoo PSX coverage is spotty — this shows it).
  Q3  How long do the per-name STATEMENT pulls cost (.info + income_stmt +
      balance_sheet + cashflow)? These CANNOT be batched by yf.download, so
      this is the number that decides DH-0.5 (cache them) vs DH-1 (swap source).

Run it once (see bench.yml), read the [DH-0] lines, paste them back.
"""
import time, random, sys

# Datacenter hygiene: realistic UA + small jitter between per-name calls.
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
JITTER = (0.15, 0.45)   # seconds between per-name calls

# Representative samples (no scanner import needed).
US = ['XOM','CVX','COP','EOG','GOOGL','MSFT','META','UNH','GIS','KO',
      'AMD','NVDA','MU','AVGO','AMAT','LRCX','WDC','KLAC','QCOM','INTC',
      'AAPL','CSCO','TXN','CAT','MRVL','STX','SNDK','COF','CCNE','OSBC']           # 30
PSX = ['OGDC','PPL','MCB','FFC','HUBC','UBL','MEBL','LUCK','ENGRO','PSO',
       'BAHL','MARI','FFBL','POL','SYS','HBL','BOP','EFERT','NBP','AKBL',
       'DGKC','PIOC','APL','ATRL','KOHC','TRG','SEARL','COLG','NESTLE','BAFL']     # 30
PSX_KA = [t + '.KA' for t in PSX]

def _hdr(t):  print('\n' + '='*60 + f'\n[DH-0] {t}\n' + '='*60)

def time_per_name(syms, period):
    import yfinance as yf
    ok = 0; t0 = time.time()
    for s in syms:
        try:
            h = yf.Ticker(s).history(period=period)
            if h is not None and len(h) > 0: ok += 1
        except Exception: pass
        time.sleep(random.uniform(*JITTER))
    return time.time() - t0, ok

def time_batch(syms, period):
    import yfinance as yf
    t0 = time.time(); ok = 0
    try:
        df = yf.download(syms, period=period, group_by='ticker',
                         progress=False, threads=True)
        for s in syms:
            try:
                sub = df[s] if s in df.columns.get_level_values(0) else None
                if sub is not None and sub['Close'].dropna().shape[0] > 0: ok += 1
            except Exception: pass
    except Exception as e:
        print(f'   batch error: {e}')
    return time.time() - t0, ok

def time_statements(syms):
    """The _fetch_im3_data shape: .info + income_stmt + balance_sheet + cashflow."""
    import yfinance as yf
    ok = 0; t0 = time.time()
    for s in syms:
        try:
            t = yf.Ticker(s)
            _ = t.info or {}
            _ = t.income_stmt
            _ = t.balance_sheet
            _ = t.cashflow
            ok += 1
        except Exception: pass
        time.sleep(random.uniform(*JITTER))
    return time.time() - t0, ok

def main():
    try:
        import yfinance as yf
        print('[DH-0] yfinance', getattr(yf, '__version__', '?'))
    except Exception as e:
        print('[DH-0] yfinance not importable:', e); sys.exit(1)

    _hdr('Q1  US 6-mo history: PER-NAME vs ONE BATCH  (30 names)')
    pn, pno = time_per_name(US, '6mo')
    print(f'   per-name : {pn:6.1f}s   ({pno}/{len(US)} returned data)')
    bt, bto = time_batch(US, '6mo')
    print(f'   batch    : {bt:6.1f}s   ({bto}/{len(US)} returned data)')
    if bt > 0: print(f'   speedup  : {pn/bt:5.1f}x faster via batch')

    _hdr('Q2  PSX .KA 1-mo history: PER-NAME vs ONE BATCH  (30 names)')
    pn2, pno2 = time_per_name(PSX_KA, '1mo')
    print(f'   per-name : {pn2:6.1f}s   ({pno2}/{len(PSX_KA)} returned data)')
    bt2, bto2 = time_batch(PSX_KA, '1mo')
    print(f'   batch    : {bt2:6.1f}s   ({bto2}/{len(PSX_KA)} returned data)')
    print('   NOTE: low coverage here = Yahoo has poor PSX .KA data ->')
    print('         confirms PSX history belongs on TV/PSX-portal (DH-2), not Yahoo.')

    _hdr('Q3  US per-name STATEMENT pulls (.info+income+balance+cashflow)  (10 names)')
    st, sto = time_statements(US[:10])
    print(f'   per-name : {st:6.1f}s   ({sto}/10 ok)   ~{(st/max(sto,1)):.1f}s/name')
    print(f'   PROJECTED over ~127 IM3-scored names: ~{st/max(sto,1)*127:5.0f}s')
    print('   These CANNOT be yf.download-batched -> the DH-0.5 (cache) vs')
    print('   DH-1 (source swap) decision rides on THIS number.')

    _hdr('READ-ME')
    print('   If Q1 batch < ~15s for 30 names, the v1.111.0 TCE batch already')
    print('   captures the history win -> no vendor change needed for history.')
    print('   The remaining cost is Q3 (statements). If Q3 projects to >60s,')
    print('   cache _fetch_im3_data like the explosive cache (DH-0.5, freeze-safe).')

if __name__ == '__main__':
    main()
