"""
probe_sources.py  —  ONE-SHOT runner probe (throwaway, logging-only, changes nothing).

Purpose: confirm three external unknowns on the ACTUAL GitHub runner before any scanner
code is built around them (per the standing 'probe-before-build' rule). Run this once,
upload the full log, and the real swaps get built against confirmed reality.

  1. SEC EDGAR  -> is data.sec.gov reachable from the runner's datacenter IP, and which
                  us-gaap concepts (Revenues / OperatingIncomeLoss / EPS) come back per
                  ticker?  (Target: replace the slow Yahoo income_stmt path for Explosive
                  OP-acceleration + the 14-survivor EPS enrichment.)
  2. TradingView forex -> which symbols actually return a live level for the Dollar Index
                  and USD/PKR, on the SAME proven scanner.tradingview.com primitive the
                  scanner already uses for oil/metals.  (Target: pull DXY + USD/PKR off Yahoo.)
  3. SBP reserves -> does ANY free endpoint return a current reserves number (the ecodata
                  path is dead; scanner is stuck on last-good 15.92).

Stdlib + requests only. Does NOT import scanner.py. Safe to run anytime.
"""
import json
import datetime as dt
import requests

# Browser UA (matches the scanner's working TradingView calls)
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
# SEC fair-access policy asks for a descriptive UA with contact; probe BOTH so we learn
# what the runner needs.
SEC_UA = 'PortfolioIntelDashboard probe contact@example.com'


def log(m):
    print(m, flush=True)


def line():
    log('=' * 70)


# ============================================================ 1. SEC EDGAR
def probe_sec():
    line()
    log('[PROBE 1] SEC EDGAR  (data.sec.gov reachability + concept availability)')
    line()

    # --- 1a. ticker -> CIK map ---
    cik_map = {}
    tk_url = 'https://www.sec.gov/files/company_tickers.json'
    for label, ua in (('SEC_UA', SEC_UA), ('browser_UA', UA)):
        try:
            r = requests.get(tk_url, headers={'User-Agent': ua}, timeout=25)
            log(f'  company_tickers.json  [{label}]  HTTP {r.status_code}  size={len(r.content)}')
            if r.status_code == 200 and not cik_map:
                data = r.json()
                for _, row in data.items():
                    cik_map[str(row['ticker']).upper()] = int(row['cik_str'])
                log(f'    -> parsed {len(cik_map)} ticker->CIK rows (e.g. AAPL={cik_map.get("AAPL")})')
        except Exception as e:
            log(f'  company_tickers.json  [{label}]  FAIL {str(e)[:90]}')

    if not cik_map:
        log('  !! could not build CIK map — SEC unreachable or blocked from this runner IP.')
        log('     (If HTTP 403: SEC is blocking the datacenter IP / UA — that decides the whole swap.)')
        return

    # --- 1b. companyfacts for a spread of names ---
    wanted_concepts = [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'OperatingIncomeLoss',
        'EarningsPerShareDiluted',
        'NetIncomeLoss',
    ]
    probe_tickers = ['MU', 'AMAT', 'UMAC', 'VSTM', 'COF']  # 2 large, 2 small-cap, 1 bank
    for tk in probe_tickers:
        cik = cik_map.get(tk)
        if not cik:
            log(f'\n  {tk}: not in CIK map (skipped)')
            continue
        url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'
        try:
            r = requests.get(url, headers={'User-Agent': SEC_UA}, timeout=25)
            log(f'\n  {tk} (CIK {cik:010d})  companyfacts HTTP {r.status_code}  size={len(r.content)}')
            if r.status_code != 200:
                continue
            facts = r.json().get('facts', {}).get('us-gaap', {})
            log(f'    us-gaap concepts present: {len(facts)}')
            for c in wanted_concepts:
                node = facts.get(c)
                if not node:
                    log(f'      {c:52} : ABSENT')
                    continue
                units = node.get('units', {})
                ukey = 'USD/shares' if 'USD/shares' in units else ('USD' if 'USD' in units else next(iter(units), None))
                arr = units.get(ukey, [])
                # last 3 quarterly (10-Q) entries, else last 3 of whatever exists
                q = [x for x in arr if x.get('form') == '10-Q']
                use = (q or arr)[-3:]
                tail = '; '.join(f"{x.get('end')}={x.get('val')}({x.get('fp')}/{x.get('form')})" for x in use)
                log(f'      {c:52} : {len(arr):>3} pts unit={ukey}  last3-> {tail}')
        except Exception as e:
            log(f'  {tk}: FAIL {str(e)[:90]}')

    log('\n  [verdict hint] Need Revenues (or RevenueFromContract...) + OperatingIncomeLoss')
    log('  quarterly to rebuild Explosive OP-acceleration; EarningsPerShareDiluted for EPS enrich.')


# ============================================================ 2. TradingView forex
def probe_tv_forex():
    line()
    log('[PROBE 2] TradingView forex  (DXY + USD/PKR symbol resolution)')
    line()
    dxy_syms = ['TVC:DXY', 'CAPITALCOM:DXY', 'ICEUS:DX1!', 'INDEX:DXY', 'CBOE:DXY']
    pkr_syms = ['FX_IDC:USDPKR', 'FX:USDPKR', 'OANDA:USDPKR', 'SAXO:USDPKR']

    def try_scan(market, tickers, cols):
        url = f'https://scanner.tradingview.com/{market}/scan'
        try:
            r = requests.post(url, json={'symbols': {'tickers': tickers}, 'columns': cols},
                              headers={'User-Agent': UA}, timeout=20)
            log(f'  POST /{market}/scan  HTTP {r.status_code}')
            if r.status_code == 200:
                for d in r.json().get('data', []):
                    log(f'      {d.get("s"):22} -> {d.get("d")}')
            else:
                log(f'      body[:160]={r.text[:160]!r}')
        except Exception as e:
            log(f'  /{market}/scan FAIL {str(e)[:80]}')

    def try_symbol(tickers, cols):
        try:
            r = requests.post('https://scanner.tradingview.com/symbol',
                              json={'symbols': {'tickers': tickers}, 'columns': cols},
                              headers={'User-Agent': UA}, timeout=20)
            log(f'  POST /symbol  HTTP {r.status_code}')
            if r.status_code == 200:
                for d in r.json().get('data', []):
                    log(f'      {d.get("s"):22} -> {d.get("d")}')
            else:
                log(f'      body[:160]={r.text[:160]!r}')
        except Exception as e:
            log(f'  /symbol FAIL {str(e)[:80]}')

    cols = ['close', 'SMA200', 'RSI']  # same technicals the metal panel wants for DXY
    log('  -- DXY via /forex/scan --');  try_scan('forex', dxy_syms, cols)
    log('  -- DXY via /cfd/scan --');    try_scan('cfd', dxy_syms, cols)
    log('  -- DXY via /symbol --');      try_symbol(dxy_syms, cols)
    log('  -- USD/PKR via /forex/scan --'); try_scan('forex', pkr_syms, ['close'])
    log('  -- USD/PKR via /symbol --');     try_symbol(pkr_syms, ['close'])
    log('\n  [verdict hint] Pick the symbol that returns a sane level: DXY ~95-110, USDPKR ~275-285.')


# ============================================================ 3. SBP reserves
def probe_sbp():
    line()
    log('[PROBE 3] SBP FX reserves  (ecodata is dead; find any live number)')
    line()
    cands = [
        ('SBP easydata json',
         'https://easydata.sbp.org.pk/apex/rest/dataservice/TS_GP_BOP_LIABASSET_M'),
        ('TheGlobalEconomy reserves',
         'https://www.theglobaleconomy.com/Pakistan/foreign_exchange_reserves/'),
        ('tradingeconomics pk reserves',
         'https://tradingeconomics.com/pakistan/foreign-exchange-reserves'),
    ]
    for label, url in cands:
        try:
            r = requests.get(url, headers={'User-Agent': UA}, timeout=20)
            ct = r.headers.get('content-type', '')
            log(f'  {label:32} HTTP {r.status_code} ct={ct[:30]} size={len(r.content)}')
            log(f'      body[:160]={r.text[:160]!r}')
        except Exception as e:
            log(f'  {label:32} FAIL {str(e)[:80]}')
    log('\n  [verdict hint] low priority — if none return a clean number, we stay on last-good')
    log('  and just document it honestly (current behaviour).')


if __name__ == '__main__':
    log(f'probe_sources.py  run {dt.datetime.utcnow().isoformat()}Z')
    probe_sec()
    probe_tv_forex()
    probe_sbp()
    line()
    log('PROBE COMPLETE — upload this full log; real swaps get built against these results.')
    line()
