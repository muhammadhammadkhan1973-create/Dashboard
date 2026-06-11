"""
IM3 data-source probe  —  LOGGING ONLY, writes nothing.

Confirms the exact TradingView + FMP field names (and MU's live values) that will
re-source im3_score.py off Yahoo. Run once on the GitHub runner (TV/FMP are reachable
there, blocked in the build sandbox), read the log, and we lock the source map.

TV  : POST scanner.tradingview.com/america/scan for NASDAQ:MU, discovering which of a
      broad candidate column set are valid (per-field fallback on a 400) + MU's values.
FMP : GET the statement / ratio / growth endpoints with FMP_API_KEY and dump field names
      + a few values per endpoint.
FRED: already confirmed working in the scanner (us_10y) — not re-probed here.
"""
import os, json, time
import requests

TV_URL = "https://scanner.tradingview.com/america/scan"
HDRS   = {"User-Agent": "Mozilla/5.0 (im3-source-probe)"}
FMP_KEY = os.environ.get("FMP_API_KEY", "")

TV_SYMBOLS = ["NASDAQ:MU", "MU"]   # try qualified first, then bare

TV_CANDIDATES = [
    'name','description','exchange','sector','industry','market_cap_basic','close','currency',
    'price_earnings_ttm','price_earnings_current','price_book_ratio','price_book_fq',
    'price_sales_ratio','price_sales_current',
    'enterprise_value_ebitda_ttm','enterprise_value_fq','enterprise_value_current',
    'gross_margin','gross_margin_ttm','operating_margin','operating_margin_ttm',
    'net_margin','net_margin_ttm','pre_tax_margin_ttm',
    'return_on_equity','return_on_invested_capital','return_on_assets',
    'debt_to_equity','debt_to_equity_fq','current_ratio','quick_ratio',
    'dividends_yield','dividends_yield_current','dividend_payout_ratio_ttm','dividends_per_share_fq',
    'total_debt','total_debt_fq','total_revenue','total_revenue_ttm',
    'free_cash_flow','free_cash_flow_ttm','free_cash_flow_margin_ttm',
    'cash_n_short_term_invest_fq','cash_n_equivalents_fq',
    'ebitda','ebitda_ttm','ebit_ttm',
    'earnings_per_share_basic_ttm','earnings_per_share_diluted_ttm','earnings_per_share_fq',
    'earnings_per_share_forecast_next_fq',
    'total_revenue_yoy_growth_ttm','earnings_per_share_diluted_yoy_growth_ttm',
    'beta_1_year','total_shares_outstanding_fundamental','number_of_shares_outstanding',
    'interest_coverage','total_current_assets_fq','total_current_liabilities_fq',
    'invent_turnover_current','total_assets_fq','retained_earnings_fq',
]

def tv_fetch(symbol, columns):
    """Return (ok, row_values or error_text)."""
    body = {"symbols": {"tickers": [symbol]}, "columns": columns}
    try:
        r = requests.post(TV_URL, json=body, headers=HDRS, timeout=20)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:120]}"
        data = r.json().get("data") or []
        if not data:
            return False, "no rows"
        return True, data[0].get("d") or []
    except Exception as e:
        return False, f"EXC {e}"

def probe_tv():
    print("\n" + "="*72 + "\nTRADINGVIEW  america/scan  —  MU field discovery\n" + "="*72)
    # pick a symbol format that returns a row
    sym = None
    for s in TV_SYMBOLS:
        ok, res = tv_fetch(s, ['name', 'close'])
        print(f"  symbol test {s!r:14}: {'OK ' + str(res) if ok else 'FAIL ' + str(res)}")
        if ok:
            sym = s; break
    if not sym:
        print("  !! could not fetch MU from TV with any symbol format — stop here, report this.")
        return
    print(f"  using symbol: {sym}\n  probing {len(TV_CANDIDATES)} candidate columns (batches of 6, per-field fallback)...\n")
    valid, invalid = {}, []
    base = ['name']
    for i in range(0, len(TV_CANDIDATES), 6):
        chunk = TV_CANDIDATES[i:i+6]
        ok, res = tv_fetch(sym, base + chunk)
        if ok and isinstance(res, list) and len(res) == len(base) + len(chunk):
            for j, c in enumerate(chunk):
                valid[c] = res[len(base)+j]
        else:
            # isolate: probe each candidate alone
            for c in chunk:
                ok1, res1 = tv_fetch(sym, base + [c])
                if ok1 and isinstance(res1, list) and len(res1) == 2:
                    valid[c] = res1[1]
                else:
                    invalid.append(c)
                time.sleep(0.15)
        time.sleep(0.2)
    print(f"  --- VALID TV columns ({len(valid)}) : field = MU value ---")
    for c in TV_CANDIDATES:
        if c in valid:
            print(f"    {c:42} = {valid[c]}")
    print(f"\n  --- INVALID / unknown TV columns ({len(invalid)}) ---")
    print("    " + (", ".join(invalid) if invalid else "(none)"))

FMP_ENDPOINTS = [
    ('profile',         'https://financialmodelingprep.com/api/v3/profile/MU?apikey={k}'),
    ('income-statement','https://financialmodelingprep.com/api/v3/income-statement/MU?limit=6&apikey={k}'),
    ('balance-sheet',   'https://financialmodelingprep.com/api/v3/balance-sheet-statement/MU?limit=6&apikey={k}'),
    ('cash-flow',       'https://financialmodelingprep.com/api/v3/cash-flow-statement/MU?limit=6&apikey={k}'),
    ('ratios',          'https://financialmodelingprep.com/api/v3/ratios/MU?limit=6&apikey={k}'),
    ('key-metrics',     'https://financialmodelingprep.com/api/v3/key-metrics/MU?limit=6&apikey={k}'),
    ('financial-growth','https://financialmodelingprep.com/api/v3/financial-growth/MU?limit=6&apikey={k}'),
    ('enterprise-values','https://financialmodelingprep.com/api/v3/enterprise-values/MU?limit=6&apikey={k}'),
]
# fields we care about per endpoint — printed if present
WATCH = ['date','calendarYear','revenue','operatingIncome','netIncome','eps','epsdiluted','ebitda',
         'grossProfit','incomeTaxExpense','incomeBeforeTax','interestExpense',
         'totalDebt','totalStockholdersEquity','totalCurrentAssets','totalCurrentLiabilities',
         'cashAndCashEquivalents','cashAndShortTermInvestments','inventory','netReceivables',
         'propertyPlantEquipmentNet','totalAssets','retainedEarnings','weightedAverageShsOut',
         'operatingCashFlow','freeCashFlow','netChangeInCash','capitalExpenditure',
         'dividendYield','priceEarningsRatio','priceToBookRatio','priceToSalesRatio',
         'enterpriseValueOverEBITDA','returnOnEquity','returnOnCapitalEmployed','currentRatio',
         'debtToEquity','revenueGrowth','epsgrowth','netIncomeGrowth','freeCashFlowGrowth',
         'sector','industry','price','beta','mktCap','enterpriseValue']

def probe_fmp():
    print("\n" + "="*72 + "\nFMP  —  MU endpoints (api/v3)\n" + "="*72)
    if not FMP_KEY:
        print("  !! FMP_API_KEY not in env — set it / pass the secret, then re-run.")
        return
    print(f"  FMP key present (…{FMP_KEY[-4:]})")
    for name, url in FMP_ENDPOINTS:
        try:
            r = requests.get(url.format(k=FMP_KEY), headers=HDRS, timeout=25)
            print(f"\n  [{name}] HTTP {r.status_code}")
            if r.status_code != 200:
                print(f"    body: {r.text[:160]}"); continue
            js = r.json()
            rows = js if isinstance(js, list) else [js]
            if not rows or not isinstance(rows[0], dict):
                print(f"    unexpected shape: {str(js)[:160]}"); continue
            r0 = rows[0]
            print(f"    records (years): {len(rows)}")
            print(f"    ALL field names ({len(r0)}): {', '.join(list(r0.keys()))}")
            present = {k: r0.get(k) for k in WATCH if k in r0}
            if present:
                print(f"    watched values (latest): " + json.dumps(present, default=str)[:600])
        except Exception as e:
            print(f"\n  [{name}] EXC {e}")

if __name__ == "__main__":
    print("IM3 DATA-SOURCE PROBE  (logging only; writes nothing)")
    probe_tv()
    probe_fmp()
    print("\n" + "="*72 + "\nPROBE DONE — paste this whole log back and I'll lock the source map.\n" + "="*72)
