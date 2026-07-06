Run python scanner.py
[03:53:28] ============================================================
[03:53:28] Dashboard scanner v1.187.0 starting
[03:53:28] ============================================================
[03:53:28] Fetching US macros from FRED...
[03:53:29]   ✓ fed_rate = 3.75
[03:53:30]   ✓ core_pce = 3.41
[03:53:31]   ✓ cpi_yoy = 4.27
[03:53:33]   ✓ us_10y = 4.48
[03:53:34]   ✓ us_2y = 4.17
[03:53:35]   ✓ unemployment = 4.2
[03:53:36]   ✓ umcsi = 44.8
[03:53:37]   ✓ mfg_emp = 12598.0
[03:53:38]   ✓ gdp_growth = 2.1
[03:53:39]   ✓ industrial_prod = 102.65
[03:53:40]   ✓ hy_spread = 2.75
[03:53:41]   ✓ permits = 1410.0
[03:53:41]   ✓ sp500 = 7483.24
[03:53:41]   ✓ wti (TV fallback NYMEX:CL1!) = 68.42
[03:53:41]   ✓ brent (TV fallback ICEEUR:BRN1!) = 71.71
[03:53:41]   ✓ Brent-WTI spread = 3.29
[03:53:42]   ✓ ndx (NASDAQ100) = 29329.21
[03:53:43]   ✓ dow (DJIA) = 52900.07
[03:53:43]   ✓ rut (TVC:RUT) = 2996.11
[03:53:43]   ✓ Arab Light (Dubai proxy) = 61.98 $/bbl (2025-12)
[03:53:43]   → US rigs skipped (EIA fetch 1d ago, <7d) — last-good 553
[03:53:43]   ✓ FOMC: 2026-06-17 — Federal Reserve issues FOMC statement
[03:53:43]   Total US macros: 102
[03:53:43] Fetching PSX macros...
[03:53:44]   · KSE-100 TradingView index symbols -> {'PSX:KSE100': 185372.2072, 'PSX:KSE30': 55404.4894}
[03:53:44]   ✓ KSE-100 (tradingview:KSE100 (official close)): 185372.21 (as of 2026-07-06)
[03:53:44]   ✓ USD/PKR (TV FX_IDC:USDPKR): 277.87
[03:53:51]   ✓ SBP rate (SBP official): 11.5%
[03:53:52]   ✓ Pak CPI YoY (TheGlobalEconomy): 11.07%
[03:53:55]   ✓ Pak CPI YoY (PBS live): 11.66% (index 294.34, MoM 0.52%, as of 2026-05; prior 11.07)
[03:53:55]   ✓ reer (manual override): 105.17
[03:53:55]   ✓ SBP reserves (manual/FMR): 16.53bn as on 24-Jun-26 (update from any broker FMR / psx_macros_manual.json)
[03:53:55]   → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: ['reer', 'pak_ca', 'pak_fiscal']
[03:53:55] Fetching metals data...
[03:53:55]   ✓ gold_px (TV COMEX:GC1!): 4174.5 · SMA200 4477.61 · down death · RSI 44.5
[03:53:55]   ✓ silver_px (TV COMEX:SI1!): 62.3 · SMA200 69.03 · down golden · RSI 40.6
[03:53:55]   ✓ platinum_px (TV NYMEX:PL1!): 1644.4 · SMA200 1915.1 · down death · RSI 41.1
[03:53:55]   ✓ palladium_px (TV NYMEX:PA1!): 1271.0 · SMA200 1532.99 · down death · RSI 46.9
[03:53:55]   ✓ copper_px (TV COMEX:HG1!): 6.21 · SMA200 5.69 · up golden · RSI 47.5
[03:53:55]   ✓ dxy (TV TVC:DXY): 100.96 · SMA200 98.93 · up golden · RSI 58.4
[03:53:55]   ✓ Gold:Silver ratio = 67.0
[03:53:55]   ✓ WALCL: $6.72T (+0.19%)
[03:53:56]   ✓ dfii10 (DFII10): 2.25
[03:53:56]   ✓ breakeven_10y (T10YIE): 2.23
[03:53:57]   ✓ gvz (GVZCLS): 27.12
[03:53:57]   ✓ COT gold: long=217,028 short=35,689 net=181,339 (51.5% OI)
[03:53:57]     COT gold trend: WoW -1.6 (down), MoM -2.5
[03:53:57]   ✓ COT silver: long=35,139 short=11,388 net=23,751 (21.8% OI)
[03:53:57]     COT silver trend: WoW -1.0 (down), MoM -1.5
[03:53:57]   ✓ COT copper: long=104,205 short=32,585 net=71,620 (26.6% OI)
[03:53:57]     COT copper trend: WoW -1.2 (down), MoM -1.9
[03:53:57]   [COT×Seasonality] Jul: gold Conflicting (COT bullish/net-long 51.5% provisional, seas unfavorable +0.19%) | silver Lean bearish (COT neutral/net-long 21.8% provisional, seas unfavorable +0.77%) | copper Lean bullish (COT bullish/net-long 26.6% provisional, seas neutral +0.81%)
[03:53:58]   ✓ imf_score: +0 (pos=0 neg=0)
[03:53:58]   ✓ default_score: +0 (pos=0 neg=0)
[03:53:59]   ✓ geo_score: +1 (pos=1 neg=0)
[03:53:59]   Metals complete: 160 fields
[03:53:59] === US screening ===
[03:53:59]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=95%(29.837054733682503) price_book_ratio=100%(30.10398800970349) price_sales_ratio=100%(22.117749631838773) enterprise_value_ebitda_ttm=72%(28.077118077202396) gross_margin=75%(74.1454331711974) operating_margin=100%(64.0200243795638) net_margin=100%(62.9659435640713) return_on_invested_capital=99%(106.17861300515598) debt_to_equity=97%(0.0655534751424742) current_ratio=99%(3.44077568134172) price_target_average=84%(313.387719) recommendation_mark=84%(1.128788) recommendation_buy=84%(55) recommendation_total=84%(66) earnings_per_share_forecast_next_fq=96%(2.075352) earnings_per_share_fq=98%(1.866323)
[03:54:00]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[03:54:03]   TV prefilter: 2017 band names scanned -> Yahoo screens 671 (large-cap 218 + financials 196 + growth 246 + ttm-fallback 11); replaces a ~2235-name full-universe Yahoo screen; dropped 30 preferred/baby-bond series
[03:54:03]   D1 bank gate: 401 in-band financials -> dropped 153 (ROE<8%) + 52 (EPS<0) -> 196 to Yahoo (revenue gate bypassed for financials)
[03:54:03]   [diag] financials EPS-growth: 401 financials, 295 with data (fq 276, ttm 270); min -61933.3% median 10.5% max 999.2%; pass >=0% 177 | >=5% 165 | >=10% 152 | >=15% 140
[03:54:03]   [diag] financials ROE: 401 financials, 326 with data; min -132.1% median 8.8% max 242.3%; pass >=8% 173 | >=10% 142 | >=12% 97 | >=15% 54 | >=20% 32
[03:54:04]   L1 large-cap fundamentals: matched 215/218 named large-caps (TV)
[03:54:04]   Building screen from TV fundamentals (668 recs) + Yahoo fallback for gaps...
[03:54:05]   US scan (L1 TV-first): 1s, 538 candidates — 536 TV-sourced + 2 Yahoo-fallback (of 3 gaps); insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)
[03:54:05]   Fetching income_stmt EPS for 14 survivors missing earningsGrowth...
[03:54:05]   [SEC] CIK map loaded: 10415 tickers (data.sec.gov reachable)
[03:54:09]     [SEC EPS] filled 12/14 from SEC EDGAR; 2 -> FMP/Yahoo fallback
[03:54:09]     [FMP EPS] FMP gap-fill disabled (premium-gated for small-caps) — Yahoo income_stmt only
[03:54:15]   EPS enriched 14/14 previously-None survivors (SEC 12, FMP 0, Yahoo 2)
[03:54:20]   [Multibagger US] pool 84 profitable small-caps (ROIC>0); 30 SEC CFO/CPAT pulls -> 17 with 3-yr cash data; 11 gate-passing; top CFO/CPAT=6.408
[03:54:23]   [Foundation Universe] TradingView america scan: 1950 US-listed names >= $2bn (seamless with the $300M-$2bn small-cap band -> continuous coverage); added top 150 accelerating large/mid-caps to Explosive pool (200 -> 350)
[03:54:23]   [M2 keystone] universe pre-score over 1950/1950 Foundation names -> 1017 disciplined (>=50) / 933 speculative (<50); top score 100.0
[03:54:24]   [sector medians] 19 sectors -> sector_medians.json (19 with 200-DMA breadth; e.g. Electronic Technology PE~43.9678/ROE~0.1546/1M~-2.24%/tgt~19.46%, Technology Services PE~26.4865/ROE~0.1367/1M~-6.8%/tgt~35.8%, Retail Trade PE~25.0131/ROE~0.2062/1M~3.16%/tgt~15.96%)
[03:54:24]   [PSX sector breadth] 13 sectors >=5 names (e.g. Energy Minerals 77.8%, Process Industries 70.4%, Transportation 66.7%)
[03:54:24]   [PSX sector medians] 14 sectors (e.g. Process Industries PE~9.6389/ROE~0.0789/1M~21.64%/tgt~23.89%, Finance PE~6.759/ROE~0.1805/1M~11.1%/tgt~26.21%, Consumer Non-Durables PE~13.3392/ROE~0.1859/1M~13.58%/tgt~None%)
[03:54:24]   [PSX Sector Booming] 13 sectors scored: Favoured=11 | Neutral=2
[03:54:24]   [Wave PK-D] devaluation: WATCH (score 2/9) -> rupee_slope=0, reserves_fall=0, reer_stretch=1, sbp_rate=1, ca_stress=0, pkr_wow=0
[03:54:24] === PSX screening ===
[03:54:24] Fetching PSX universe...
[03:54:27]   ✓ PSX endpoint reachable
[03:54:27]   [F5 watchlist] 8 loaded ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; in top-500 scan -> force-include: ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; absent from scan (skipped): []
[03:54:27]   ✓ PSX universe: 49 candidates from TradingView Pakistan scanner
[03:54:27]   ✓ TPL: price=16.79 (tv_scan)
[03:54:27]   ✓ HCAR: price=251.78 (tv_scan)
[03:54:27]   ✓ GCIL: price=38.66 (tv_scan)
[03:54:27]   ✓ GAL: price=584.28 (tv_scan)
[03:54:27]   ✓ JVDC: price=157.29 (tv_scan)
[03:54:27]   ✓ TRG: price=67.62 (tv_scan)
[03:54:27]   ✓ LOTCHEM: price=29.38 (tv_scan)
[03:54:27]   ✓ TPLP: price=11.64 (tv_scan)
[03:54:27]   ✓ SLGL: price=18.43 (tv_scan)
[03:54:27]   ✓ GGL: price=26.62 (tv_scan)
[03:54:27]   ✓ NML: price=162.56 (tv_scan)
[03:54:27]   ✓ NRL: price=371.03 (tv_scan)
[03:54:27]   ✓ PAEL: price=45.39 (tv_scan)
[03:54:27]   ✓ PAKRI: price=18.1 (tv_scan)
[03:54:27]   ✓ GHNI: price=994.5 (tv_scan)
[03:54:27]   ✓ KOHTM: price=162.72 (tv_scan)
[03:54:27]   ✓ FFL: price=18.12 (tv_scan)
[03:54:27]   ✓ PSX: price=52.93 (tv_scan)
[03:54:27]   ✓ QTECH: price=51.87 (tv_scan)
[03:54:27]   ✓ SEARL: price=96.13 (tv_scan)
[03:54:27]   ✓ CEPB: price=31.38 (tv_scan)
[03:54:27]   ✓ PIBTL: price=18.87 (tv_scan)
[03:54:27]   ✓ IBLHL: price=55.32 (tv_scan)
[03:54:27]   ✓ PRL: price=36.29 (tv_scan)
[03:54:27]   ✓ PAKQATAR: price=23.49 (tv_scan)
[03:54:27]   ✓ OGDC: price=345.43 (tv_scan)
[03:54:27]   ✓ PPL: price=248.71 (tv_scan)
[03:54:27]   ✓ MCB: price=427.11 (tv_scan)
[03:54:27]   ✓ FFC: price=576.72 (tv_scan)
[03:54:27]   ✓ HUBC: price=233.61 (tv_scan)
[03:54:27]   ✓ MTL: price=302.52 (tv_scan)
[03:54:27]   ✓ POL: price=685.8 (tv_scan)
[03:54:27]   ✓ THCCL: price=68.04 (tv_scan)
[03:54:27]   ✓ DOL: price=32.9 (tv_scan)
[03:54:27]   ✓ CLOV: price=8.2 (tv_scan)
[03:54:27]   ✓ AHL: price=116.54 (tv_scan)
[03:54:27]   ✓ PAKT: price=1453.29 (tv_scan)
[03:54:27]   ✓ HALEON: price=803.01 (tv_scan)
[03:54:27]   ✓ UBL: price=490.77 (tv_scan)
[03:54:27]   ✓ MEBL: price=555.94 (tv_scan)
[03:54:27]   ✓ HBL: price=305.91 (tv_scan)
[03:54:27]   ✓ NBP: price=208.8 (tv_scan)
[03:54:27]   ✓ ABL: price=186.25 (tv_scan)
[03:54:27]   ✓ BAFL: price=61.64 (tv_scan)
[03:54:27]   ✓ BAHL: price=174.92 (tv_scan)
[03:54:27]   ✓ AKBL: price=117.32 (tv_scan)
[03:54:27]   ✓ FABL: price=101.56 (tv_scan)
[03:54:27]   ✓ BOP: price=36.85 (tv_scan)
[03:54:27]   ✓ BIPL: price=28.47 (tv_scan)
[03:54:27]   PSX scan done: 49 candidates
[03:54:27]   [Wave Q snapshot] skipped (<24h since 2026-07-05T06:57:04.279611) — carrying last-good (13 banks)
[03:54:27]   [Wave Q sector] KPMG skipped (<30d) — carrying last-good
[03:54:27]   [Wave Q->IG2] SCS fallback overrides written for 12 bank(s): ['ABL', 'AKBL', 'BAFL', 'BAHL', 'BIPL', 'BOP', 'FABL', 'HBL', 'MCB', 'MEBL', 'NBP', 'UBL'] (im3_score fills these into missing roe/adr/roa-trend only)
[03:54:28]   [US-bank IG2] COF CERT 4297: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.4% ADR~80.9% CAR 15.184590431395431
[03:54:28]   [US-bank IG2] CCNE CERT 13876: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.7% ADR~83.2% CAR 13.585867849370054
[03:54:29]   [US-bank IG2] MCBS CERT 58181: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~15.5% ADR~113.8% CAR 19.927096960197737
[03:54:30]   [US-bank IG2] ISTR CERT 58316: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~8.6% ADR~89.4% CAR 12.92431526011692
[03:54:31]   [US-bank IG2] OSBC CERT 3603: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~13.7% ADR~81.3% CAR 13.82027793691253
[03:54:31]   [US-bank IG2] COFS CERT 1014: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~11.3% ADR~68.2% CAR 12.66748151792934
[03:54:32]   [US-bank IG2] PLBC CERT 23275: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~16.3% ADR~72.7% CAR 18.450058001627507
[03:54:33]   [US-bank IG2] CARE CERT 58596: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~7.2% ADR~85.4% CAR 11.983002042230364
[03:54:33]   [US-bank IG2] merged 8 US bank(s) into bank_ig2_overrides.json: ['CARE', 'CCNE', 'COF', 'COFS', 'ISTR', 'MCBS', 'OSBC', 'PLBC'] (im3_score v2.17.0+ scores these via score_bank_us — CAMELS scorecard, 21 ratios; pre-v2.17.0 falls back to score_bank_ig2 calib=us)
[03:54:33]   [Wave P FMR] fetch skipped (1d ago, <7d) — carrying last-good fund-ownership + flows
[03:54:33]   [Wave PSX-R valmatrix] fetch skipped (1d ago, <7d) — carrying last-good
[03:54:55]   [Wave PSX-R MTS] as-of February 6, 2026: total Rs 28747.6mn across 56 symbols (chg -0.06%, wavg rate 12.58%); top: ['NBP', 'BOP', 'PSO', 'HUBC', 'HBL', 'FFC', 'OGDC', 'SEARL']
[03:54:55]   [Wave PSX-R MTS] DIAG parsed mts_amount_mn (first 15): AGP=30.633, AICL=512.975, AIRLINK=169.315, AKBL=729.707, ATRL=658.431, BAFL=242.808, BAHL=227.036, BOP=2525.839, CHCC=10.254, CPHL=166.777, DCR=0.0, DGKC=690.488, EFERT=54.024, FABL=235.037, FATIMA=296.198
[03:54:55]   [Wave PSX-R MTS] STALE: report as-of February 6, 2026 is 150d old (> 14d) — leverage gauge may not be current; flagged stale in data.json
[03:54:55]   [Wave PSX-R MSCI] shelved (stale 2016 SCS source) -> psx_msci empty
[03:54:55]   [Wave P breadth] adv=244 dec=208 unch=26 (top-478 mcap); vol leader=TPL; val leader=OGDC
[03:54:55]   US TCE pool: 15 screen + 19 ETF-consensus = 34
[03:54:56]   US analyst overlay: matched 212/213 TCE-pool tickers (TV FactSet)
[03:54:56] === TCE on US (34 candidates) ===
[03:54:58]   TCE batch history: 34/34 names pre-fetched in one call (us)
[03:54:58]   [news diag us] VOXR -> google=9, yahoo=6
[03:55:36]   VOXR: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:36]   HYLN: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's11_target_upside']
[03:55:36]   RJET: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum']
[03:55:36]   EOSE: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside']
[03:55:36]   DVLT: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   ABTC: IGNORE total=3 conv=0 streams=['s1_news', 's3_insider', 's5_volume']
[03:55:36]   VSTM: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   BTGO: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's11_target_upside', 's12_recommendation']
[03:55:36]   ARQQ: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital']
[03:55:36]   MU: HIGH total=8 conv=5 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   WVE: WATCH total=5 conv=4 streams=['s1_news', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   FWDI: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[03:55:36]   UMAC: HIGH total=6 conv=4 streams=['s1_news', 's5_volume', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:55:36]   RHLD: IGNORE total=1 conv=1 streams=['s8_capital']
[03:55:36]   ASPI: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:55:36]   NVDA: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   INTC: IGNORE total=3 conv=1 streams=['s1_news', 's3_insider', 's6_momentum']
[03:55:36]   AMAT: HIGH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[03:55:36]   AMD: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[03:55:36]   LRCX: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[03:55:36]   AAPL: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's7_margin', 's9_eps_rev']
[03:55:36]   AVGO: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   CSCO: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside']
[03:55:36]   KLAC: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev']
[03:55:36]   TXN: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[03:55:36]   GOOGL: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:36]   MSFT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:36]   MRVL: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's9_eps_rev', 's12_recommendation']
[03:55:36]   SNDK: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's9_eps_rev', 's11_target_upside']
[03:55:36]   QCOM: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside']
[03:55:36]   WDC: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's8_capital', 's9_eps_rev']
[03:55:36]   STX: HIGH total=5 conv=4 streams=['s1_news', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside']
[03:55:36]   XOM: IGNORE total=3 conv=1 streams=['s1_news', 's3_insider', 's11_target_upside']
[03:55:36]   META: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:55:36]   TCE: 8 HIGH, 18 WATCH out of 34 scanned
[03:55:36] === TCE on PSX (49 candidates) ===
$SLGL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
$PAKQATAR.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")

2 Failed downloads:
['SLGL.KA', 'PAKQATAR.KA']: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[03:55:38]   TCE batch history: 47/49 names pre-fetched in one call (psx)
[03:55:39]   [news diag psx] TPL -> google_pk=7, brecorder=92
[03:55:47]   TPL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[03:55:47]   HCAR: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's11_target_upside']
[03:55:47]   GCIL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[03:55:47]   GAL: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[03:55:47]   JVDC: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[03:55:47]   TRG: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[03:55:47]   LOTCHEM: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[03:55:47]   TPLP: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[03:55:47]   SLGL: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[03:55:47]   GGL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[03:55:47]   NML: WATCH total=4 conv=4 streams=['s6_momentum', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:47]   NRL: IGNORE total=0 conv=0 streams=[]
[03:55:47]   PAEL: HIGH total=5 conv=4 streams=['s1_news', 's6_momentum', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:47]   PAKRI: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[03:55:47]   GHNI: IGNORE total=1 conv=1 streams=['s6_momentum']
[03:55:47]   KOHTM: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[03:55:47]   FFL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[03:55:47]   PSX: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[03:55:47]   QTECH: IGNORE total=1 conv=0 streams=['s1_news']
[03:55:47]   SEARL: IGNORE total=2 conv=1 streams=['s1_news', 's11_target_upside']
[03:55:47]   CEPB: IGNORE total=0 conv=0 streams=[]
[03:55:47]   PIBTL: WATCH total=4 conv=3 streams=['s1_news', 's6_momentum', 's11_target_upside', 's12_recommendation']
[03:55:47]   IBLHL: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[03:55:47]   PRL: IGNORE total=1 conv=0 streams=['s1_news']
[03:55:47]   PAKQATAR: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[03:55:47]   OGDC: WATCH total=4 conv=3 streams=['s1_news', 's6_momentum', 's11_target_upside', 's12_recommendation']
[03:55:47]   PPL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   MCB: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   FFC: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   HUBC: IGNORE total=1 conv=0 streams=['s1_news']
[03:55:47]   MTL: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[03:55:47]   POL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[03:55:47]   THCCL: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[03:55:47]   DOL: IGNORE total=0 conv=0 streams=[]
[03:55:47]   CLOV: IGNORE total=0 conv=0 streams=[]
[03:55:47]   AHL: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[03:55:47]   PAKT: IGNORE total=1 conv=1 streams=['s6_momentum']
[03:55:47]   HALEON: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[03:55:47]   UBL: HIGH total=5 conv=3 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin', 's12_recommendation']
[03:55:47]   MEBL: IGNORE total=2 conv=1 streams=['s1_news', 's12_recommendation']
[03:55:47]   HBL: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:47]   NBP: WATCH total=4 conv=3 streams=['s1_news', 's6_momentum', 's7_margin', 's12_recommendation']
[03:55:47]   ABL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   BAFL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   BAHL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[03:55:47]   AKBL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's12_recommendation']
[03:55:47]   FABL: HIGH total=5 conv=4 streams=['s1_news', 's6_momentum', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:55:47]   BOP: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[03:55:47]   BIPL: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[03:55:47]   TCE: 3 HIGH, 23 WATCH out of 49 scanned
[03:55:47] TCE predictions: 161 logged, 161 open (re-priced 6/50 off-pool); HIGH matured=0 hit=None alpha=None lift=None; WATCH matured=0 hit=None; IGNORE matured=0 hit=None
[03:55:47] === EXPLOSIVE screen on US (350 candidates) ===
[03:55:47]   VOXR: A=True B=True -> EXPLOSIVE — both signals
[03:55:47]   HYLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   RJET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   EOSE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   DVLT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   ABTC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   VSTM: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   BTGO: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   ARQQ: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   MU: A=True B=True -> EXPLOSIVE — both signals
[03:55:47]   WVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   FWDI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   UMAC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   RHLD: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   ASPI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   FUBO: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   IAUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   NSLR: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   OABI: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   GOLD: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   GLOO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   CRMD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   SNDX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   POET: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   USAS: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   SPRY: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   MSIF: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   ASM: A=True B=True -> EXPLOSIVE — both signals
[03:55:47]   SKYT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   PCT: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   IRWD: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   NRGV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   AMPX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   URGN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   RILY: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   NUAI: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   AGCC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   ANGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   PRLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   AEBI: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   GROY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   HIVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   STAA: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   SSII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   GAU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   EVC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   MAKO: A=True B=True -> EXPLOSIVE — both signals
[03:55:47]   LPTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   TIC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   MUX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   NEWT: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   CARE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:47]   ELE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   PHAT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   ELA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   LIFE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   LPG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   AMN: A=False B=False -> NOT EXPLOSIVE
[03:55:47]   IDR: A=True B=True -> EXPLOSIVE — both signals
[03:55:47]   ATLC: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   FIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:47]   ASST: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   SATA: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:47]   CSWC: A=None B=None -> NOT EXPLOSIVE
[03:55:47]   BIOA: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   XZO: A=None B=None -> NOT EXPLOSIVE
[03:55:48]   JCAP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   PICS: A=None B=None -> NOT EXPLOSIVE
[03:55:48]   DELL: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   SRTA: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   AEVA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   NVDA: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   UPB: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   INR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   ZSQR: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   SATL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   SCZM: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   LAES: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   ZVRA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   CMCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   SHLS: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   FENC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   MBI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   ADAM: A=None B=None -> NOT EXPLOSIVE
[03:55:48]   OMC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   DCH: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   AQST: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   SI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   NAT: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   KMTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   GNK: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   AMBQ: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   CARL: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   BBNX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   SKYH: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   TLS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   LLY: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   ASIC: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   OSS: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   GRRR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   ISTR: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:48]   HSHP: A=None B=False -> NOT EXPLOSIVE
[03:55:48]   CGBD: A=None B=None -> NOT EXPLOSIVE
[03:55:48]   PAYS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   ECVT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   MAMA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   GSBD: A=None B=None -> NOT EXPLOSIVE
[03:55:48]   ENVX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   VELO: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   AVGO: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   GEVO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   NEM: A=True B=True -> EXPLOSIVE — both signals
[03:55:48]   JANX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   WYFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   EVGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:48]   WDC: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   KOS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   IOVA: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   EVLV: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   ROCK: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   WEST: A=False B=False -> NOT EXPLOSIVE
[03:55:48]   BW: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:48]   STX: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   OFRM: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   HLIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CLPT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   PKE: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   COF: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   OMDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TOI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   MRVI: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ETON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   NEXA: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   CDNA: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   PANL: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CRON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   XERS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   WELL: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   RYZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AMD: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   PRSU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ACRS: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   LWAY: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   RES: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   TREE: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   DMLP: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   PLBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   PNTG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TWFG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ANET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TSM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ABX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   CCNE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   MCBS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   CYD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   KARO: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   SNDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   DASH: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   META: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ALB: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   GCT: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   OSBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   CLMB: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   COFS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   REAX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ASYS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   EFC: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   GERN: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   QMCO: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   GENI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   VINP: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   MFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AMSC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   BX: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   KURA: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CBLL: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   VIA: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   WLKP: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   TEN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   BALY: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   QNST: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   FIGS: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   VEL: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   TRIN: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   ARDX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   VMD: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   TXO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   LWLG: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   UTL: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   MNST: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   SWBI: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   XRX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   BOW: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   FTK: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   ARLO: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   DCTH: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   SVCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   UAN: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   WILC: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   JOBY: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   QXO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   QUBT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   LQDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   BSM: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   IDYA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   CRNX: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CGON: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ASTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   PGEN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   EBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:49]   CYTK: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ONDS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   NBIS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   IONQ: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   SNDK: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   BMNP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   BMNR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   MXL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   IBRX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   MRNA: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   BEAM: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ATEX: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   HUT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   XNDU: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ICHR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   BE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   ALAB: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ALM: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AYA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   AVEX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   UNIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CRDO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   CDNL: A=None B=False -> NOT EXPLOSIVE
[03:55:49]   FBYD: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   SLS: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ERAS: A=None B=False -> NOT EXPLOSIVE
[03:55:49]   BB: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   RYN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ABCL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   QURE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   SII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   CLOV: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   SEZL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   EXK: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   MANE: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   UCTT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AAOI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   LUNR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   VSH: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   BTDR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   PENG: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   INTC: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   RGTI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   OSCR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ASND: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   STRL: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   OUST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   INSM: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   MRVL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   EQX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   FPS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TWST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   AXTI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   DFTX: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   KLIC: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ACMR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   DX: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   APLD: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   WBI: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   MAAS: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   PTRN: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AGIO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   DBRG: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   IRDM: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   SITM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   SANM: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   COHU: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ASTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ECO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   VICR: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   TER: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   LGN: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   CMBT: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ELVN: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   LITE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   PNFP: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   AUGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   HNGE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CORT: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   DAVE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   DOCN: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   AMLX: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   COMP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TGTX: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   PTGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   SHAZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   MRP: A=None B=False -> NOT EXPLOSIVE
[03:55:49]   ORKA: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ORLA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   GLNG: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   DDOG: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AGX: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   HNI: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   FLEX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   TTMI: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   AEHR: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CDE: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   SYRE: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   MTRN: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   PANW: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   VIAV: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:49]   BLLN: A=None B=None -> NOT EXPLOSIVE
[03:55:49]   RGLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   SUN: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   SMCI: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   ARIS: A=True B=True -> EXPLOSIVE — both signals
[03:55:49]   MP: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   MDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   INSW: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   GH: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   AVAV: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   BFLY: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   CRWV: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   VSAT: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   PDFS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   MDGL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   CELH: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   RVMD: A=None B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   ALGM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   XMTR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:49]   FIX: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   AMAT: A=False B=False -> NOT EXPLOSIVE
[03:55:49]   WOLF: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:49]   TVTX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[03:55:50]   NAVN: A=None B=None -> NOT EXPLOSIVE
[03:55:51]   BETA: A=None B=None -> NOT EXPLOSIVE
[03:55:51]   FTNT: A=False B=False -> NOT EXPLOSIVE
[03:55:51]   MKSI: A=False B=False -> NOT EXPLOSIVE
[03:55:51]   TXG: A=False B=False -> NOT EXPLOSIVE
[03:55:51]   FRO: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   RKLB: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   HPE: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   FORM: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   VCTR: A=False B=False -> NOT EXPLOSIVE
[03:55:51]   OTF: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   LSCC: A=False B=False -> NOT EXPLOSIVE — OP declining
[03:55:51]   GLW: A=False B=True -> INFLECTION (accelerating off low base — verify)
[03:55:51]   EZPW: A=False B=False -> NOT EXPLOSIVE
[03:55:51]   [Explosive cache] 345 hit / 0 fetched (income_stmt cached 7d, persisted in data.json)
[03:55:51]   [Explosive src] 0 SEC-EDGAR / 0 Yahoo-fallback of 0 fetched; 0 verdict flip(s) vs last-good
[03:55:51]   EXPLOSIVE: 23 both-signal of 350 scored; 9 financials -> bank model; 0 insufficient-data
[03:55:51] === EXPLOSIVE screen on PSX (49 candidates) ===
[03:55:51]   TPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   HCAR: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   GCIL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   GAL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   JVDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   TRG: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   LOTCHEM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   TPLP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   SLGL: A=None B=None -> INSUFFICIENT DATA
[03:55:51]   GGL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   NML: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   NRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PAEL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PAKRI: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   GHNI: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   KOHTM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   FFL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PSX: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   QTECH: A=None B=None -> INSUFFICIENT DATA
[03:55:51]   SEARL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   CEPB: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PIBTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   IBLHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PAKQATAR: A=None B=None -> INSUFFICIENT DATA
[03:55:51]   OGDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   MCB: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   FFC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   HUBC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   MTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   POL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   THCCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   DOL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   CLOV: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   AHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   PAKT: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   HALEON: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[03:55:51]   UBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   MEBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   HBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   NBP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   ABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   BAFL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   BAHL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   AKBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   FABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   BOP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   BIPL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[03:55:51]   EXPLOSIVE: 0 both-signal of 49 scored; 12 financials -> bank model; 3 insufficient-data
[03:55:52]   ✓ COT SP500: net -35,448 BEARISH (-1.8% OI) "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"  [vs Sarmaaya -193,978: DRIFT]
[03:55:53]   ✓ COT NASDAQ: net -16,272 BEARISH (-5.9% OI) "NASDAQ-100 CONSOLIDATED - CHICAGO MERCANTILE EXCHANGE"  [vs Sarmaaya -20,866: DRIFT]
[03:55:54]   ✓ COT Russell: net -26,838 BEARISH (-6.9% OI) "RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE"
[03:55:55]   ✓ COT DJIA: net +9,474 VERY BULLISH (+12.0% OI) "DJIA CONSOLIDATED - CHICAGO BOARD OF TRADE"  [vs Sarmaaya +4,339: DRIFT]
[03:55:56]   ✓ COT 10yr: net -835,266 VERY BEARISH (-15.8% OI) "UST 10Y NOTE - CHICAGO BOARD OF TRADE"
[03:55:56]   ✓ COT VIX: net -66,774 VERY BEARISH (-18.9% OI) "VIX FUTURES - CBOE FUTURES EXCHANGE"
[03:55:57]   ✓ COT Crude: net +114,633 BULLISH (+6.0% OI) "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE"
[03:55:58]   ✓ COT NatGas: net -176,689 VERY BEARISH (-11.0% OI) "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE"
[03:55:58]   ✓ COT Agriculture: net +58,333 BULLISH (+3.0% OI) "CORN - CHICAGO BOARD OF TRADE"
[03:55:59]   ✓ COT futures (legacy Non-Commercial 6dca-aqww): 9/9 [SP500, NASDAQ, Russell, DJIA, 10yr, VIX, Crude, NatGas, Agriculture]
[03:56:07]   ✓ Recession calendar: 3 high-impact US releases (faireconomy)
[03:56:07]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 3 calendar events
[03:56:07]   → Zacks scrape skipped (last scrape 1d ago, <7d) — carrying forward last-good
[03:56:10]   [World LEI] 12/12 countries fetched (FRED)
[03:56:10]   [US Diffusion] net=+8  10/14 supportive  regime=Expansion
[03:56:13]   [Country RS] Dollar direction: Strong (DXY above200=True, currencies losing to USD: 6/12)
[03:56:13]   [Country RS] 13/9 countries ranked
[03:56:13]   [Sector Booming] 11 sectors scored: Lagging=8 | Neutral=3
[03:56:13]   [Sector Booming delta] 11 sectors trended (rising=0 falling=0 flat=11)
[03:56:13]   [Global Theme] 4 themes scored: Asia-Tech=72.8(Favoured) | Developed-West=71.3(Favoured) | Commodity-Bloc=68.0(Favoured) | Emerging=55.7(Neutral)
[03:56:13]   [ETF Recommendations] 5 resolved: country+global_theme:Taiwan & Asia-Tech->iShares MSCI Taiwan UCITS ETF (x2), global_theme:Asia-Tech->Franklin FTSE Korea UCITS ETF, global_theme:Semiconductors->VanEck Semiconductor UCITS ETF, global_theme:Developed-West->UBS MSCI Switzerland 20/35 UCI, global_theme:Developed-West->iShares Core S&P 500 UCITS ETF
[03:56:28]   [ETF live prices] 111 fund(s) priced via isin-filter resolver (recs + hydrogen + emerging-themes + metals + momentum watch) -- now incl. live YTD/1Y (v1.141.0)
[03:56:28]     · [diag] stockanalysis CIBR: HTTP 200 body[:180]='{"status":200,"data":{"holdings":[{"no":1,"n":"Palo Alto Networks, Inc.","s":"$PANW","as":"9.72%","sh":"3,902,373"},{"no":2,"n":"Fortinet, Inc.","s":"$FTNT","as":"8.90%","sh":"7,96'
[03:56:28]     · [diag] stockanalysis CIBR: parsed 25 holdings
[03:56:28]   [Emerging holdings] verified-allowlist filled 4/4 funds (collision-safe; rest need justETF/issuer)
[03:56:29]     · [diag] iShares IE000X59ZHE2 pid=338777: HTTP 200 len 12008 -> 51 holdings
[03:56:29]     · [diag] iShares IE00BG0J4C88 pid=297843: HTTP 200 len 21353 -> 116 holdings
[03:56:30]     · [diag] iShares IE00BG0J4841 pid=305642: HTTP 200 len 21353 -> 116 holdings
[03:56:30]     · [diag] iShares IE000C6ITGC8 pid=345953: HTTP 200 len 7105 -> 30 holdings
[03:56:30]     · [diag] iShares IE000A9G9R73 pid=351117: HTTP 200 len 14207 -> 85 holdings
[03:56:30]   [Emerging holdings] iShares issuer-file filled 5/5 funds (BlackRock authoritative CSV by ISIN)
[03:56:30]   [Hydrogen notes] recomputed live: weakest=Amundi Global Hydrog, smallest-AUM=49m
[03:56:30]   [ETF Results tracker] 7 pick(s) tracked vs ACWI ($121.53) -- 5/7 positive, 4/7 beating ACWI where alpha is computable
[03:56:30]   [Stock->UCITS bridge] 166 pick(s) matched to a UCITS proxy (US+PSX TCE HIGH+WATCH, US+PSX Explosive positive-verdict)
[03:56:31]   [Recommended->ETF trackers] priced 11/11 distinct UCITS proxy ETF(s); enriched ucits_proxy (ISIN+YTD+1Y) on 166 pick(s); explosive=6 group(s) / 23 name(s), tce=7 group(s) / 52 name(s)
[03:56:31]   → ETF holdings overlap skipped (last scrape 1d ago, <7d) — carrying forward last-good
[03:56:31]   → Wave Z inst_consensus skipped (last scrape 7d ago, <7d) — carrying forward last-good
[03:56:31]   Carried forward 306 last-good IM3 score(s) onto rebuilt records
[03:56:31]   [Wave T history] 2026-07-06: 10 day(s) stored (kse100=185372.21, usd/pkr=277.87, diffusion_net=8, lei_exp=4, sector_top=Industrials 55.6)
[03:56:31]   [Wave T trends] 95 field(s) in trend table, 31 with a live move (kse100=up, usd_pkr=down, sp500=up, gold_px=down)
[03:56:31]   [Wave T shortlist] 341 stock-rows tracked (230 live, 341 conviction-stamped [341 at true entry]) across 7 tabs; 35 sector baskets
[03:56:32]   [countryeconomy us] debt/GDP=122.27% (2024, flat) · Moody's Aa1 (Stable, 2025-05-16, flat)
[03:56:34]   [countryeconomy pakistan] debt/GDP=70.22% (2024, flat) · Moody's Caa1 (Stable, 2025-08-13, flat)
[03:56:34] data.json written (5859025 bytes)
[03:56:34] ============================================================
[03:56:34] Scanner completed
[03:56:34]   Hard errors: 0
[03:56:34]   Warnings (degraded data): 0
[03:56:34]   Swallowed (silent) exceptions: {'tce.fetch': 2}
[03:56:34]   US macros: 102
[03:56:34]   PSX macros: 31
[03:56:34]   KSE-100: 185372.21 (tradingview:KSE100 (official close), as of 2026-07-06)
[03:56:34]   WTI/Brent: 68.42 / 71.71 (tradingview:CL1!, as of 2026-07-06)
[03:56:34]   US candidates: 15
[03:56:34]   PSX candidates: 49
[03:56:34]   US TCE HIGH: 8
[03:56:34]   PSX TCE HIGH: 3
[03:56:34]   Recession: LOW (score 0, 3 cal events)
[03:56:34] ============================================================
