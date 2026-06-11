"""
PSX TradingView fundamental-column probe  —  Phase 0 of the PSX IM3 engine.
=========================================================================
Logging only; writes nothing. Run on GitHub Actions (TradingView is not
reachable from the build sandbox).

TWO sections, one run:
  (1) GENERIC  — the 61 IM3 single-period columns across non-bank + bank names.
  (2) BANK     — System-B bank inputs (NIM / CASA / ADR / NPL / CAR and the raw
                 loans/deposits/interest fields they derive from) across PSX
                 banks, to decide whether bank scoring can use TV or must wait
                 for broker research.

Paste the whole log back to lock the PSX source map.
"""
import requests, time

URL  = "https://scanner.tradingview.com/pakistan/scan"
HDRS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
        "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"}

# five holdings + a few large liquid names for breadth across sectors
TICKERS = ["PSX:OGDC", "PSX:PPL", "PSX:MCB", "PSX:FFC", "PSX:HUBC",
           "PSX:LUCK", "PSX:UBL"]

# PSX banks for the System-B section
BANK_TICKERS = ["PSX:MCB", "PSX:UBL", "PSX:HBL", "PSX:MEBL", "PSX:BAFL"]

# the 61 generic IM3 single-period columns (confirmed valid on america/scan)
COLS = [
    "name","description","sector","industry","market_cap_basic","close","currency",
    "price_earnings_ttm","price_earnings_current","price_book_ratio","price_book_fq",
    "price_sales_ratio","price_sales_current","enterprise_value_ebitda_ttm",
    "enterprise_value_fq","enterprise_value_current","gross_margin","gross_margin_ttm",
    "operating_margin","operating_margin_ttm","net_margin","net_margin_ttm",
    "pre_tax_margin_ttm","return_on_equity","return_on_invested_capital","return_on_assets",
    "debt_to_equity","debt_to_equity_fq","current_ratio","quick_ratio","dividends_yield",
    "dividends_yield_current","dividend_payout_ratio_ttm","dividends_per_share_fq",
    "total_debt","total_debt_fq","total_revenue","total_revenue_ttm","free_cash_flow",
    "free_cash_flow_ttm","free_cash_flow_margin_ttm","cash_n_short_term_invest_fq",
    "cash_n_equivalents_fq","ebitda","ebitda_ttm","ebit_ttm","earnings_per_share_basic_ttm",
    "earnings_per_share_diluted_ttm","earnings_per_share_fq","earnings_per_share_forecast_next_fq",
    "total_revenue_yoy_growth_ttm","earnings_per_share_diluted_yoy_growth_ttm","beta_1_year",
    "total_shares_outstanding_fundamental","number_of_shares_outstanding","interest_coverage",
    "total_current_assets_fq","total_current_liabilities_fq","invent_turnover_current",
    "total_assets_fq","retained_earnings_fq",
]

# candidate TV column names for the System-B bank inputs and their raw drivers.
# TV rejects unknown columns, so the per-field fallback flags the invalid ones.
BANK_COLS = [
    # net interest margin / income
    "net_interest_margin","net_interest_margin_fq","nim",
    "net_interest_income","net_interest_income_fy","total_interest_income",
    "interest_income","interest_income_fq","interest_expense","interest_expense_fq",
    # loans & deposits (ADR / advance-to-deposit)
    "loans_net_fq","loans_gross_fq","total_loans_fq","net_loans_fq",
    "total_deposits_fq","total_deposits_fy","deposits_fq",
    "demand_deposits_fq","savings_deposits_fq","time_deposits_fq",   # CASA decomposition
    # asset quality (NPL)
    "nonperf_loans_loans_fq","nonperforming_loans_fq","npl_ratio",
    "loan_loss_allowances_fq","loan_loss_provision_fq","loan_losses_fq",
    # capital adequacy
    "tier_1_capital_ratio","total_capital_ratio","capital_adequacy_ratio","tier1_ratio",
    # efficiency / book
    "efficiency_ratio","book_value_per_share_fq",
]

def scan(cols, tickers):
    """POST one column set for a ticker list; (data|None, status, err)."""
    body = {"symbols": {"tickers": tickers, "query": {"types": []}}, "columns": cols}
    try:
        r = requests.post(URL, json=body, headers=HDRS, timeout=30)
    except Exception as e:
        return None, "EXC", str(e)[:160]
    if r.status_code != 200:
        return None, r.status_code, r.text[:160]
    return r.json().get("data", []), 200, ""

def probe_columns(cols, tickers, label):
    """Per-column coverage with per-field fallback for TV-rejected columns."""
    print(f"=== {label} (n={len(tickers)} names) ===")
    base, code, err = scan(["name"], tickers)
    if base is None:
        print(f"  base scan failed (HTTP {code}): {err}"); return
    resolved = {row["s"]: row["d"][0] for row in base}
    print("  resolved:", ", ".join(f"{s.split(':')[1]}" for s in resolved) or "(none)")
    valid, invalid = {}, []
    B = 6
    for i in range(0, len(cols), B):
        batch = cols[i:i+B]
        data, code, err = scan(["name"] + batch, tickers)
        if data is not None:
            for row in data:
                for j, c in enumerate(batch):
                    valid.setdefault(c, {})[row["s"]] = row["d"][j+1]
        else:
            for c in batch:
                d2, _, _ = scan(["name", c], tickers)
                if d2 is not None:
                    for row in d2:
                        valid.setdefault(c, {})[row["s"]] = row["d"][1]
                else:
                    invalid.append(c)
                time.sleep(0.2)
        time.sleep(0.3)
    n = len(resolved); filled = 0
    for c in cols:
        if c in valid:
            nn = sum(1 for v in valid[c].values() if v is not None)
            if nn: filled += 1
            sample = next((v for v in valid[c].values() if v is not None), None)
            print(f"  {c:42} {nn}/{n}   e.g. {sample}")
        else:
            print(f"  {c:42} INVALID (rejected by TV)")
    print(f"  -> {filled}/{len(cols)} populated for >=1 name; INVALID: {invalid or '(none)'}")
    print()
    return filled, len(cols), invalid

def main():
    print("PSX TradingView pakistan/scan probe — generic + bank — logging only")
    print("=" * 70)
    probe_columns(COLS, TICKERS, "GENERIC IM3 single-period columns")
    probe_columns(BANK_COLS, BANK_TICKERS, "BANK System-B inputs (PSX banks)")
    print("VERDICT GUIDE:")
    print("  generic high + bank fields present -> PSX IM3 incl. banks = TV-automatable")
    print("  generic high + bank fields absent  -> non-bank PSX = TV; bank System-B = broker")
    print()
    print("Paste this whole log back to lock the PSX source map.")

if __name__ == "__main__":
    main()
