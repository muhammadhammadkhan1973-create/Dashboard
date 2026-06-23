Run python scanner.py
[04:14:57] ============================================================
[04:14:57] Dashboard scanner v1.101.0 starting
[04:14:57] ============================================================
[04:14:57] Fetching US macros from FRED...
[04:14:58]   ✓ fed_rate = 3.75
[04:14:59]   ✓ core_pce = 3.29
[04:15:02]   ✓ cpi_yoy = 4.27
[04:15:04]   ✓ us_10y = 4.46
[04:15:07]   ✓ us_2y = 4.19
[04:15:08]   ✓ unemployment = 4.3
[04:15:09]   ✓ umcsi = 49.8
[04:15:09]   ✓ mfg_emp = 12605.0
[04:15:10]   ✓ gdp_growth = 1.6
[04:15:11]   ✓ industrial_prod = 102.65
[04:15:12]   ✓ hy_spread = 2.66
[04:15:13]   ✓ permits = 1413.0
[04:15:14]   ✓ sp500 = 7472.79
[04:15:14]   ✓ wti (live CL=F) = 73.68 (as of 2026-06-23)
[04:15:14]   ✓ brent (live BZ=F) = 77.58 (as of 2026-06-23)
[04:15:14]   ✓ Brent-WTI spread = 3.9
[04:15:16]   ✓ ndx (NASDAQ100) = 30347.08
[04:15:16]   ✓ dow (DJIA) = 51712.71
[04:15:16]   ✓ rut (TVC:RUT) = 3004.4
[04:15:17]   ✓ Arab Light (Dubai proxy) = 61.98 $/bbl (2025-12)
[04:15:17]   → US rigs skipped (EIA fetch 5d ago, <7d) — last-good 545
[04:15:17]   ✓ FOMC: 2026-06-17 — Federal Reserve issues FOMC statement
[04:15:17]   Total US macros: 102
[04:15:17] Fetching PSX macros...
[04:15:17]   · KSE-100 TradingView index symbols -> {'PSX:KSE100': 178471.8696, 'PSX:KSE30': 53200.2039}
[04:15:17]   ✓ KSE-100 (tradingview:KSE100 (official close)): 178471.87 (as of 2026-06-23)
[04:15:17]   ✓ USD/PKR: 278.08
[04:15:19]   ✓ SBP rate (SBP official): 11.5%
[04:15:19]   → Pak CPI: TheGlobalEconomy now JS-rendered (unparseable) — using manual/last-good
[04:15:21]   ✓ Pak CPI YoY (PBS live): 11.66% (index 294.34, MoM 0.52%, as of 2026-05; prior 11.66)
[04:15:21]   ✓ reer (manual override): 105.17
[04:15:22]   ✓ SBP reserves (ecodata, live): SBP 17.22bn / bank 5.52bn / total 22.74bn as on 12-June-2026 (prior 17.22)
[04:15:22]   → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: ['reer', 'pak_ca', 'pak_fiscal']
[04:15:22] Fetching metals data...
[04:15:22]   ✓ gold_px (GC=F): 4162.1
[04:15:22]   ✓ silver_px (SI=F): 63.16
[04:15:23]   ✓ platinum_px (PL=F): 1641.7
[04:15:23]   ✓ palladium_px (PA=F): 1249.5
[04:15:23]   ✓ dxy (DX-Y.NYB): 101.0
[04:15:23]   ✓ Gold:Silver ratio = 65.9
[04:15:23]   ✓ WALCL: $6.74T (+0.34%)
[04:15:24]   ✓ dfii10 (DFII10): 2.21
[04:15:25]   ✓ breakeven_10y (T10YIE): 2.23
[04:15:26]   ✓ gvz (GVZCLS): 27.9
[04:15:26]   ✓ COT gold: long=211,127 short=30,907 net=180,220 (53.1% OI)
[04:15:26]     COT gold trend: WoW +0.9 (up), MoM -0.9
[04:15:26]   ✓ COT silver: long=35,611 short=11,067 net=24,544 (22.8% OI)
[04:15:26]     COT silver trend: WoW +1.3 (up), MoM -0.5
[04:15:26]   ✓ COT copper: long=106,794 short=31,444 net=75,350 (27.8% OI)
[04:15:26]     COT copper trend: WoW +0.7 (up), MoM -0.7
[04:15:26]   ✓ imf_score: +0 (pos=0 neg=0)
[04:15:27]   ✓ default_score: +0 (pos=0 neg=0)
[04:15:27]   ✓ geo_score: +1 (pos=2 neg=1)
[04:15:27]   Metals complete: 104 fields
[04:15:27] === US screening ===
[04:15:28]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=95%(31.95350546724249) price_book_ratio=100%(32.23937329068743) price_sales_ratio=100%(23.686641999092334) enterprise_value_ebitda_ttm=72%(30.09776910883097) gross_margin=75%(74.1454331711974) operating_margin=99%(64.0200243795638) net_margin=99%(62.9659435640713) return_on_invested_capital=98%(106.17861300515598) debt_to_equity=97%(0.0655534751424742) current_ratio=99%(3.44077568134172) price_target_average=83%(310.622414) recommendation_mark=83%(1.126866) recommendation_buy=83%(56) recommendation_total=83%(67) earnings_per_share_forecast_next_fq=96%(2.075352) earnings_per_share_fq=98%(1.866323)
[04:15:28]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[04:15:31]   TV prefilter: 2065 band names scanned -> Yahoo screens 685 (large-cap 218 + financials 200 + growth 254 + ttm-fallback 13); replaces a ~2283-name full-universe Yahoo screen; dropped 31 preferred/baby-bond series
[04:15:31]   D1 bank gate: 407 in-band financials -> dropped 157 (ROE<8%) + 50 (EPS<0) -> 200 to Yahoo (revenue gate bypassed for financials)
[04:15:31]   [diag] financials EPS-growth: 407 financials, 303 with data (fq 282, ttm 279); min -61933.3% median 11.1% max 999.2%; pass >=0% 186 | >=5% 174 | >=10% 159 | >=15% 147
[04:15:31]   [diag] financials ROE: 407 financials, 334 with data; min -201.9% median 8.9% max 242.3%; pass >=8% 177 | >=10% 147 | >=12% 101 | >=15% 56 | >=20% 32
[04:15:31]   L1 large-cap fundamentals: matched 215/218 named large-caps (TV)
[04:15:31]   Building screen from TV fundamentals (682 recs) + Yahoo fallback for gaps...
[04:15:33]   US scan (L1 TV-first): 1s, 552 candidates — 550 TV-sourced + 2 Yahoo-fallback (of 3 gaps); insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)
[04:15:33]   Fetching income_stmt EPS for 14 survivors missing earningsGrowth...
[04:16:05]   EPS enriched 14/14 previously-None survivors (FMP 0, Yahoo 14)
[04:16:06]   [sector medians] 19 sectors -> sector_medians.json (19 with 200-DMA breadth; e.g. Electronic Technology PE~44.8864/ROE~0.1511/1M~10.99%/tgt~9.77%, Technology Services PE~24.6439/ROE~0.1423/1M~-5.32%/tgt~41.56%, Retail Trade PE~22.5596/ROE~0.2001/1M~0.73%/tgt~19.43%)
[04:16:06]   [PSX sector breadth] 13 sectors >=5 names (e.g. Process Industries 63.9%, Non-Energy Minerals 59.4%, Consumer Durables 58.8%)
[04:16:07]   [PSX sector medians] 14 sectors (e.g. Process Industries PE~9.2291/ROE~0.0789/1M~15.37%/tgt~26.0%, Finance PE~6.545/ROE~0.1813/1M~8.25%/tgt~30.93%, Consumer Non-Durables PE~13.2694/ROE~0.1859/1M~11.59%/tgt~None%)
[04:16:07]   [Wave PK-D] devaluation: ELEVATED (score 3/7) -> rupee_slope=1, reserves_fall=0, reer_stretch=1, sbp_rate=1, ca_stress=0
[04:16:07] === PSX screening ===
[04:16:07] Fetching PSX universe...
[04:16:09]   ✓ PSX endpoint reachable
[04:16:09]   [F5 watchlist] 8 loaded ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; in top-500 scan -> force-include: ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; absent from scan (skipped): []
[04:16:09]   ✓ PSX universe: 49 candidates from TradingView Pakistan scanner
[04:16:09]   ✓ TPL: price=16.52 (tv_scan)
[04:16:09]   ✓ SSGC: price=32.23 (tv_scan)
[04:16:09]   ✓ GCIL: price=34.38 (tv_scan)
[04:16:09]   ✓ TPLP: price=10.95 (tv_scan)
[04:16:09]   ✓ KPUS: price=2410.14 (tv_scan)
[04:16:09]   ✓ IGIHL: price=315.19 (tv_scan)
[04:16:09]   ✓ PAEL: price=43.08 (tv_scan)
[04:16:09]   ✓ TPLL: price=22.55 (tv_scan)
[04:16:09]   ✓ GGL: price=24.01 (tv_scan)
[04:16:09]   ✓ LOADS: price=14.8 (tv_scan)
[04:16:09]   ✓ TRG: price=65.95 (tv_scan)
[04:16:09]   ✓ LOTCHEM: price=28.55 (tv_scan)
[04:16:09]   ✓ NML: price=155.04 (tv_scan)
[04:16:09]   ✓ SEARL: price=93.58 (tv_scan)
[04:16:09]   ✓ AVN: price=37.92 (tv_scan)
[04:16:09]   ✓ GAL: price=522.85 (tv_scan)
[04:16:09]   ✓ KOHTM: price=175.86 (tv_scan)
[04:16:09]   ✓ PIBTL: price=17.84 (tv_scan)
[04:16:09]   ✓ NRL: price=372.59 (tv_scan)
[04:16:09]   ✓ PSX: price=49.62 (tv_scan)
[04:16:09]   ✓ QTECH: price=42.84 (tv_scan)
[04:16:09]   ✓ GATM: price=30.19 (tv_scan)
[04:16:09]   ✓ PRL: price=35.87 (tv_scan)
[04:16:09]   ✓ KOSM: price=6.67 (tv_scan)
[04:16:09]   ✓ NCPL: price=64.62 (tv_scan)
[04:16:09]   ✓ OGDC: price=334.25 (tv_scan)
[04:16:09]   ✓ PPL: price=242.63 (tv_scan)
[04:16:09]   ✓ MCB: price=400.1 (tv_scan)
[04:16:09]   ✓ FFC: price=557.94 (tv_scan)
[04:16:09]   ✓ HUBC: price=231.98 (tv_scan)
[04:16:09]   ✓ MTL: price=312.38 (tv_scan)
[04:16:09]   ✓ POL: price=687.08 (tv_scan)
[04:16:09]   ✓ THCCL: price=66.49 (tv_scan)
[04:16:09]   ✓ DOL: price=32.07 (tv_scan)
[04:16:09]   ✓ CLOV: price=8.26 (tv_scan)
[04:16:09]   ✓ AHL: price=113.64 (tv_scan)
[04:16:09]   ✓ PAKT: price=1420.1 (tv_scan)
[04:16:09]   ✓ HALEON: price=790.45 (tv_scan)
[04:16:09]   ✓ UBL: price=437.46 (tv_scan)
[04:16:09]   ✓ MEBL: price=512.17 (tv_scan)
[04:16:09]   ✓ HBL: price=294.98 (tv_scan)
[04:16:09]   ✓ NBP: price=203.0 (tv_scan)
[04:16:09]   ✓ ABL: price=183.72 (tv_scan)
[04:16:09]   ✓ BAFL: price=60.33 (tv_scan)
[04:16:09]   ✓ BAHL: price=170.71 (tv_scan)
[04:16:09]   ✓ AKBL: price=108.66 (tv_scan)
[04:16:09]   ✓ FABL: price=96.96 (tv_scan)
[04:16:09]   ✓ BOP: price=35.21 (tv_scan)
[04:16:09]   ✓ BIPL: price=26.81 (tv_scan)
[04:16:09]   PSX scan done: 49 candidates
[04:16:09]   [Wave Q snapshot] skipped (<24h since 2026-06-22T21:54:10.122681) — carrying last-good (13 banks)
[04:16:09]   [Wave Q sector] KPMG skipped (<30d) — carrying last-good
[04:16:09]   [Wave Q->IG2] SCS fallback overrides written for 12 bank(s): ['ABL', 'AKBL', 'BAFL', 'BAHL', 'BIPL', 'BOP', 'FABL', 'HBL', 'MCB', 'MEBL', 'NBP', 'UBL'] (im3_score fills these into missing roe/adr/roa-trend only)
[04:16:10]   [US-bank IG2] COF CERT 4297: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.4% ADR~80.9% CAR 15.184590431395431
[04:16:11]   [US-bank IG2] CCNE CERT 13876: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.7% ADR~83.2% CAR 13.585867849370054
[04:16:12]   [US-bank IG2] MCBS CERT 58181: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~15.5% ADR~113.8% CAR 19.927096960197737
[04:16:12]   [US-bank IG2] ISTR CERT 58316: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~8.6% ADR~89.4% CAR 12.92431526011692
[04:16:13]   [US-bank IG2] OSBC CERT 3603: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~13.7% ADR~81.3% CAR 13.82027793691253
[04:16:14]   [US-bank IG2] COFS CERT 1014: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~11.3% ADR~68.2% CAR 12.66748151792934
[04:16:15]   [US-bank IG2] PLBC CERT 23275: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~16.3% ADR~72.7% CAR 18.450058001627507
[04:16:15]   [US-bank IG2] CARE CERT 58596: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~7.2% ADR~85.4% CAR 11.983002042230364
[04:16:15]   [US-bank IG2] merged 8 US bank(s) into bank_ig2_overrides.json: ['CARE', 'CCNE', 'COF', 'COFS', 'ISTR', 'MCBS', 'OSBC', 'PLBC'] (im3_score v2.17.0+ scores these via score_bank_us — CAMELS scorecard, 21 ratios; pre-v2.17.0 falls back to score_bank_ig2 calib=us)
[04:16:15]   [Wave P FMR] fetch skipped (5d ago, <7d) — carrying last-good fund-ownership + flows
[04:16:15]   [Wave PSX-R valmatrix] fetch skipped (4d ago, <7d) — carrying last-good
[04:16:40]   [Wave PSX-R MTS] as-of February 6, 2026: total Rs 28747.6mn across 56 symbols (chg -0.06%, wavg rate 12.58%); top: ['NBP', 'BOP', 'PSO', 'HUBC', 'HBL', 'FFC', 'OGDC', 'SEARL']
[04:16:40]   [Wave PSX-R MTS] DIAG parsed mts_amount_mn (first 15): AGP=30.633, AICL=512.975, AIRLINK=169.315, AKBL=729.707, ATRL=658.431, BAFL=242.808, BAHL=227.036, BOP=2525.839, CHCC=10.254, CPHL=166.777, DCR=0.0, DGKC=690.488, EFERT=54.024, FABL=235.037, FATIMA=296.198
[04:16:40]   [Wave PSX-R MSCI] shelved (stale 2016 SCS source) -> psx_msci empty
[04:16:40]   [Wave P breadth] adv=206 dec=233 unch=38 (top-477 mcap); vol leader=WTL; val leader=OGDC
[04:16:40]   US TCE pool: 15 screen + 20 ETF-consensus = 35
[04:16:41]   US analyst overlay: matched 213/214 TCE-pool tickers (TV FactSet)
[04:16:41] === TCE on US (35 candidates) ===
[04:16:43]   VOXR: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:16:49]   HYLN: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum']
[04:16:52]   RJET: IGNORE total=3 conv=0 streams=['s1_news', 's3_insider', 's5_volume']
[04:16:55]   DVLT: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[04:16:57]   ABTC: IGNORE total=1 conv=0 streams=['s1_news']
[04:16:58]   VSTM: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[04:17:01]   BTGO: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[04:17:04]   ARQQ: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital']
[04:17:07]   WVE: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[04:17:09]   FWDI: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[04:17:11]   AVEX: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's11_target_upside', 's12_recommendation']
[04:17:13]   UMAC: HIGH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[04:17:15]   RHLD: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital']
[04:17:18]   ASPI: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[04:17:20]   FUBO: WATCH total=4 conv=3 streams=['s1_news', 's8_capital', 's11_target_upside', 's12_recommendation']
[04:17:22]   MU: HIGH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[04:17:28]   NVDA: HIGH total=5 conv=4 streams=['s3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[04:17:30]   AMD: WATCH total=4 conv=3 streams=['s1_news', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:17:36]   AMAT: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[04:17:40]   INTC: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's6_momentum', 's9_eps_rev']
[04:17:43]   LRCX: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[04:17:48]   AAPL: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[04:17:49]   AVGO: HIGH total=7 conv=5 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[04:17:53]   CSCO: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:17:54]   TXN: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:17:56]   QCOM: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin']
[04:17:59]   KLAC: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:18:04]   MRVL: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's9_eps_rev', 's12_recommendation']
[04:18:06]   WDC: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's8_capital', 's9_eps_rev']
[04:18:11]   STX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:18:14]   MSFT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:18:19]   SNDK: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's9_eps_rev']
[04:18:21]   GOOGL: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:18:25]   CAT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[04:18:30]   XOM: IGNORE total=3 conv=2 streams=['s1_news', 's9_eps_rev', 's11_target_upside']
[04:18:31]   TCE: 8 HIGH, 18 WATCH out of 35 scanned
[04:18:31] === TCE on PSX (49 candidates) ===
[04:18:32]   TPL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[04:18:33]   SSGC: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[04:18:34]   GCIL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[04:18:36]   TPLP: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:18:37]   KPUS: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:18:38]   IGIHL: WATCH total=3 conv=2 streams=['s5_volume', 's6_momentum', 's7_margin']
[04:18:39]   PAEL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
$TPLL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[04:18:41]   TPLL: IGNORE total=1 conv=1 streams=['s7_margin']
[04:18:42]   GGL: WATCH total=3 conv=2 streams=['s5_volume', 's6_momentum', 's7_margin']
[04:18:43]   LOADS: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[04:18:45]   TRG: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[04:18:46]   LOTCHEM: IGNORE total=1 conv=1 streams=['s6_momentum']
[04:18:47]   NML: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[04:18:48]   SEARL: IGNORE total=1 conv=1 streams=['s11_target_upside']
[04:18:50]   AVN: IGNORE total=1 conv=1 streams=['s6_momentum']
$GAL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[04:18:51]   GAL: WATCH total=3 conv=3 streams=['s6_momentum', 's11_target_upside', 's12_recommendation']
[04:18:52]   KOHTM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:18:53]   PIBTL: IGNORE total=1 conv=1 streams=['s6_momentum']
[04:18:55]   NRL: IGNORE total=1 conv=0 streams=['s1_news']
[04:18:56]   PSX: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
$QTECH.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[04:18:58]   QTECH: IGNORE total=0 conv=0 streams=[]
[04:18:59]   GATM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:19:00]   PRL: IGNORE total=0 conv=0 streams=[]
[04:19:02]   KOSM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:19:03]   NCPL: IGNORE total=1 conv=0 streams=['s1_news']
[04:19:04]   OGDC: WATCH total=4 conv=3 streams=['s1_news', 's6_momentum', 's11_target_upside', 's12_recommendation']
[04:19:06]   PPL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:19:07]   MCB: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:19:08]   FFC: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[04:19:10]   HUBC: IGNORE total=1 conv=0 streams=['s1_news']
[04:19:11]   MTL: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[04:19:13]   POL: WATCH total=2 conv=2 streams=['s7_margin', 's12_recommendation']
[04:19:14]   THCCL: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[04:19:15]   DOL: IGNORE total=1 conv=0 streams=['s1_news']
[04:19:17]   CLOV: IGNORE total=1 conv=0 streams=['s1_news']
[04:19:18]   AHL: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[04:19:19]   PAKT: IGNORE total=0 conv=0 streams=[]
[04:19:21]   HALEON: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:19:22]   UBL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[04:19:24]   MEBL: IGNORE total=1 conv=1 streams=['s12_recommendation']
[04:19:25]   HBL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[04:19:27]   NBP: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:19:28]   ABL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:19:29]   BAFL: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[04:19:30]   BAHL: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[04:19:32]   AKBL: WATCH total=2 conv=2 streams=['s6_momentum', 's12_recommendation']
[04:19:33]   FABL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[04:19:34]   BOP: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[04:19:36]   BIPL: IGNORE total=0 conv=0 streams=[]
[04:19:36]   TCE: 0 HIGH, 24 WATCH out of 49 scanned
[04:19:37] TCE predictions: 196 logged, 196 open (re-priced 18/68 off-pool); HIGH matured=0 hit=None alpha=None lift=None; WATCH matured=0 hit=None; IGNORE matured=0 hit=None
[04:19:37] === EXPLOSIVE screen on US (200 candidates) ===
[04:19:38]   VOXR: A=True B=True -> EXPLOSIVE — both signals
[04:19:38]   HYLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:39]   RJET: A=False B=False -> NOT EXPLOSIVE
[04:19:39]   DVLT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:40]   ABTC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:19:40]   VSTM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:41]   BTGO: A=None B=None -> NOT EXPLOSIVE
[04:19:41]   ARQQ: A=False B=False -> NOT EXPLOSIVE
[04:19:42]   WVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:42]   FWDI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:43]   AVEX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:43]   UMAC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:44]   RHLD: A=False B=False -> NOT EXPLOSIVE
[04:19:44]   ASPI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:45]   FUBO: A=False B=False -> NOT EXPLOSIVE
[04:19:45]   IAUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:46]   SSSS: A=None B=None -> NOT EXPLOSIVE
[04:19:46]   OABI: A=False B=False -> NOT EXPLOSIVE
[04:19:47]   GOLD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:47]   GLOO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:48]   MGRT: A=True B=True -> EXPLOSIVE — both signals
[04:19:49]   CRMD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:19:49]   SNDX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:19:50]   FBYD: A=False B=False -> NOT EXPLOSIVE
[04:19:50]   USAS: A=False B=False -> NOT EXPLOSIVE
[04:19:51]   MU: A=True B=True -> EXPLOSIVE — both signals
[04:19:51]   SPRY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:52]   MSIF: A=None B=None -> NOT EXPLOSIVE
[04:19:53]   ATOM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:53]   ASM: A=True B=True -> EXPLOSIVE — both signals
[04:19:54]   SKYT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:54]   PCT: A=None B=False -> NOT EXPLOSIVE — OP declining
[04:19:55]   IRWD: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:19:55]   NRGV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:19:56]   URGN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:56]   RILY: A=False B=False -> NOT EXPLOSIVE
[04:19:57]   NUAI: A=False B=False -> NOT EXPLOSIVE
[04:19:57]   AGCC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:58]   ANGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:19:58]   PRLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:19:59]   AEBI: A=False B=False -> NOT EXPLOSIVE
[04:19:59]   GROY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:00]   HIVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:00]   STAA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:01]   SSII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:01]   GAU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:02]   EVC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:03]   MAKO: A=True B=True -> EXPLOSIVE — both signals
[04:20:03]   LPTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:04]   TIC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:04]   MUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:05]   NEWT: A=None B=None -> NOT EXPLOSIVE
[04:20:05]   CARE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:20:06]   PDYN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:06]   ELE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:07]   PHAT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:07]   ELA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:08]   LIFE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:09]   LPG: A=True B=True -> EXPLOSIVE — both signals
[04:20:09]   AMLX: A=False B=False -> NOT EXPLOSIVE
[04:20:10]   AMN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:10]   IDR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:11]   ATLC: A=None B=None -> NOT EXPLOSIVE
[04:20:11]   ABCL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:12]   VRDN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:12]   FIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:13]   ASST: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:13]   SATA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:14]   LTC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:14]   CSWC: A=None B=None -> NOT EXPLOSIVE
[04:20:15]   BIOA: A=None B=False -> NOT EXPLOSIVE — OP declining
[04:20:15]   XZO: A=None B=None -> NOT EXPLOSIVE
[04:20:16]   JCAP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:16]   PICS: A=None B=None -> NOT EXPLOSIVE
[04:20:17]   DELL: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:20:17]   SRTA: A=False B=False -> NOT EXPLOSIVE
[04:20:18]   SENS: A=False B=False -> NOT EXPLOSIVE
[04:20:18]   AEVA: A=False B=False -> NOT EXPLOSIVE
[04:20:19]   NVDA: A=True B=True -> EXPLOSIVE — both signals
[04:20:20]   UPB: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:20]   INR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:21]   ZSQR: A=None B=False -> NOT EXPLOSIVE — OP declining
[04:20:21]   SATL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:22]   SCZM: A=False B=False -> NOT EXPLOSIVE
[04:20:22]   LAES: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:23]   ZVRA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:23]   CMCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:24]   SHIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:24]   SHLS: A=False B=False -> NOT EXPLOSIVE
[04:20:25]   FENC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:25]   MBI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:26]   ADAM: A=None B=None -> NOT EXPLOSIVE
[04:20:26]   OMC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:27]   DCH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:27]   AQST: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:28]   SI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:29]   NAT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:29]   KMTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:30]   GNK: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:30]   ROMA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:31]   AMBQ: A=False B=False -> NOT EXPLOSIVE
[04:20:31]   BBNX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:32]   SKYH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:32]   TLS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:33]   ASTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:33]   LLY: A=True B=True -> EXPLOSIVE — both signals
[04:20:34]   ASIC: A=True B=True -> EXPLOSIVE — both signals
[04:20:35]   OSS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:35]   GRRR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:36]   ISTR: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:20:36]   HSHP: A=False B=False -> NOT EXPLOSIVE
[04:20:37]   CGBD: A=None B=None -> NOT EXPLOSIVE
[04:20:37]   PAYS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:38]   SIDU: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:38]   ECVT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:39]   MAMA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:39]   GSBD: A=None B=None -> NOT EXPLOSIVE
[04:20:40]   ENVX: A=False B=False -> NOT EXPLOSIVE
[04:20:40]   VELO: A=False B=False -> NOT EXPLOSIVE
[04:20:41]   AVGO: A=True B=True -> EXPLOSIVE — both signals
[04:20:41]   GEVO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:42]   NEM: A=True B=True -> EXPLOSIVE — both signals
[04:20:43]   JANX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:43]   WYFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:44]   EZPW: A=False B=False -> NOT EXPLOSIVE
[04:20:44]   EVGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:45]   WDC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:45]   KOS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:46]   IOVA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:46]   EVLV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:47]   ROCK: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:47]   WEST: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:48]   STX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:48]   OFRM: A=None B=None -> NOT EXPLOSIVE
[04:20:49]   HLIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:49]   CLPT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:50]   PKE: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:20:50]   COF: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:20:51]   OMDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:51]   TOI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:52]   ATEX: A=False B=False -> NOT EXPLOSIVE
[04:20:53]   FLYW: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:53]   MRVI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:54]   ETON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:54]   NEXA: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:20:55]   CDNA: A=False B=False -> NOT EXPLOSIVE
[04:20:55]   PANL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:56]   CRON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:56]   XERS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:20:57]   SLDE: A=True B=True -> EXPLOSIVE — both signals
[04:20:57]   WELL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:58]   RYZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:20:59]   AMD: A=True B=True -> EXPLOSIVE — both signals
[04:20:59]   PRSU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:00]   ACRS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:00]   LWAY: A=False B=False -> NOT EXPLOSIVE
[04:21:01]   RES: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:01]   TREE: A=True B=True -> EXPLOSIVE — both signals
[04:21:02]   DMLP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:02]   PLBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:03]   PNTG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:04]   TWFG: A=True B=True -> EXPLOSIVE — both signals
[04:21:04]   ANET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:05]   TSM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:05]   ABX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:06]   CCNE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:06]   MCBS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:07]   CYD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:07]   KARO: A=False B=False -> NOT EXPLOSIVE
[04:21:08]   SNDA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:08]   DASH: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:09]   META: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:09]   ALB: A=False B=False -> NOT EXPLOSIVE
[04:21:10]   GCT: A=False B=False -> NOT EXPLOSIVE
[04:21:10]   OSBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:11]   CLMB: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:11]   COFS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:12]   REAX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:12]   ASYS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:13]   EFC: A=None B=None -> NOT EXPLOSIVE
[04:21:13]   GERN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:14]   GENI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:15]   VINP: A=True B=True -> EXPLOSIVE — both signals
[04:21:15]   BX: A=None B=None -> NOT EXPLOSIVE
[04:21:16]   KURA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:16]   CBLL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:17]   VIA: A=False B=False -> NOT EXPLOSIVE
[04:21:17]   ALKT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:18]   WLKP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:18]   TEN: A=False B=False -> NOT EXPLOSIVE
[04:21:19]   BALY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:19]   QNST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:20]   FIGS: A=False B=False -> NOT EXPLOSIVE
[04:21:20]   VEL: A=None B=None -> NOT EXPLOSIVE
[04:21:21]   TRIN: A=None B=None -> NOT EXPLOSIVE
[04:21:21]   ARDX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:21:22]   VMD: A=True B=True -> EXPLOSIVE — both signals
[04:21:22]   TXO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:21:23]   LWLG: A=False B=False -> NOT EXPLOSIVE
[04:21:23]   UTL: A=False B=False -> NOT EXPLOSIVE
[04:21:23]   EXPLOSIVE: 17 both-signal of 200 scored; 8 financials -> bank model; 0 insufficient-data
[04:21:23] === EXPLOSIVE screen on PSX (49 candidates) ===
[04:21:23]   TPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   SSGC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   GCIL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   TPLP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   KPUS: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   IGIHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PAEL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   TPLL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   GGL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   LOADS: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   TRG: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   LOTCHEM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   NML: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   SEARL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   AVN: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   GAL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   KOHTM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PIBTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   NRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PSX: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   QTECH: A=None B=None -> INSUFFICIENT DATA
[04:21:23]   GATM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   KOSM: A=None B=None -> INSUFFICIENT DATA
[04:21:23]   NCPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   OGDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   MCB: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   FFC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   HUBC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   MTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   POL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   THCCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   DOL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   CLOV: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   AHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   PAKT: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   HALEON: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:21:23]   UBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   MEBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   HBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   NBP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   ABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   BAFL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   BAHL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   AKBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   FABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   BOP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   BIPL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:21:23]   EXPLOSIVE: 0 both-signal of 49 scored; 12 financials -> bank model; 2 insufficient-data
[04:21:24]   ✓ COT futures (TFF): 4/4 [10yr, NASDAQ, SP500, VIX]
[04:21:25]   ✓ COT futures disaggregated (Managed Money): ['Crude', 'Agriculture']
[04:21:32]   ✓ Recession calendar: 8 high-impact US releases (faireconomy)
[04:21:32]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 8 calendar events
[04:21:32]   → Zacks scrape skipped (last scrape 1d ago, <7d) — carrying forward last-good
[04:21:32]     · [diag] stockanalysis FTXL: HTTP 200 body[:180]='{"status":200,"data":{"holdings":[{"no":1,"n":"Intel Corporation","s":"$INTC","as":"12.57%","sh":"2,712,001"},{"no":2,"n":"Micron Technology, Inc.","s":"$MU","as":"11.77%","sh":"29'
[04:21:32]     · [diag] stockanalysis FTXL: parsed 25 holdings
[04:21:59]   ETF overlap: 30/30 ETFs returned holdings -> top 25 consensus stocks
[04:21:59]   Carried forward 233 last-good IM3 score(s) onto rebuilt records
[04:21:59]   [Wave T history] 2026-06-23: 6 day(s) stored (kse100=178471.87, mts=28747.6mn, usd/pkr=278.08)
[04:21:59]   [Wave T shortlist] 222 stock-rows tracked (181 live) across 7 tabs; 31 sector baskets
[04:21:59] data.json written (2896061 bytes)
[04:21:59] ============================================================
[04:21:59] Scanner completed
[04:21:59]   Hard errors: 0
[04:21:59]   Warnings (degraded data): 0
[04:21:59]   US macros: 102
[04:21:59]   PSX macros: 26
[04:21:59]   KSE-100: 178471.87 (tradingview:KSE100 (official close), as of 2026-06-23)
[04:21:59]   WTI/Brent: 73.68 / 77.58 (yahoo:CL=F, as of 2026-06-23)
[04:21:59]   US candidates: 15
[04:21:59]   PSX candidates: 49
[04:21:59]   US TCE HIGH: 8
[04:21:59]   PSX TCE HIGH: 0
[04:21:59]   Recession: LOW (score 0, 8 cal events)
[04:21:59] ============================================================
