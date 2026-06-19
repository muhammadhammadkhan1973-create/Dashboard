Run python scanner.py
[21:06:42] ============================================================
[21:06:42] Dashboard scanner v1.84.0 starting
[21:06:42] ============================================================
[21:06:42] Fetching US macros from FRED...
[21:06:43]   ✓ fed_rate = 3.75
[21:06:44]   ✓ core_pce = 3.29
[21:06:45]   ✓ cpi_yoy = 4.27
[21:06:47]   ✓ us_10y = 4.49
[21:06:49]   ✓ us_2y = 4.2
[21:06:50]   ✓ unemployment = 4.3
[21:06:51]   ✓ umcsi = 49.8
[21:06:52]   ✓ mfg_emp = 12605.0
[21:06:53]   ✓ gdp_growth = 1.6
[21:06:54]   ✓ industrial_prod = 102.65
[21:06:54]   ✓ hy_spread = 2.63
[21:06:55]   ✓ permits = 1413.0
[21:06:56]   ✓ sp500 = 7500.58
[21:06:56]   ✓ wti (live CL=F) = 76.54 (as of 2026-06-19)
[21:06:56]   ✓ brent (live BZ=F) = 80.59 (as of 2026-06-19)
[21:06:56]   ✓ Brent-WTI spread = 4.05
[21:06:56]   → US rigs skipped (EIA fetch 2d ago, <7d) — last-good 545
[21:06:56]   ✓ FOMC: 2026-06-17 — Federal Reserve issues FOMC statement
[21:06:56]   Total US macros: 97
[21:06:56] Fetching PSX macros...
[21:06:57]   · KSE-100 TradingView index symbols -> {'PSX:KSE100': 178922.7584, 'PSX:KSE30': 53308.9537}
[21:06:57]   ✓ KSE-100 (tradingview:KSE100 (official close)): 178922.76 (as of 2026-06-19)
[21:06:57]   ✓ USD/PKR: 277.98
[21:06:58]   ✓ SBP rate (SBP official): 11.5%
[21:06:59]   → Pak CPI: TheGlobalEconomy now JS-rendered (unparseable) — using manual/last-good
[21:06:59]   ✓ reer (manual override): 105.17
[21:06:59]   → SBP reserves: official page is PDF; keeping last-good if TE missed (manual override)
[21:06:59]   → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: ['reer', 'pak_ca', 'pak_fiscal']
[21:06:59] Fetching metals data...
[21:06:59]   ✓ gold_px (GC=F): 4172.9
[21:06:59]   ✓ silver_px (SI=F): 64.91
[21:06:59]   ✓ platinum_px (PL=F): 1668.2
[21:06:59]   ✓ palladium_px (PA=F): 1264.5
[21:06:59]   ✓ dxy (DX-Y.NYB): 100.85
[21:06:59]   ✓ Gold:Silver ratio = 64.3
[21:06:59]   ✓ WALCL: $6.74T (+0.34%)
[21:07:00]   ✓ dfii10 (DFII10): 2.23
[21:07:02]   ✓ breakeven_10y (T10YIE): 2.25
[21:07:02]   ✓ gvz (GVZCLS): 28.45
[21:07:02]   ✓ COT gold: long=207,984 short=34,147 net=173,837 (52.2% OI)
[21:07:02]     COT gold trend: WoW -1.8 (down), MoM -1.8
[21:07:02]   ✓ COT silver: long=32,487 short=10,273 net=22,214 (21.5% OI)
[21:07:02]     COT silver trend: WoW -1.8 (down), MoM -1.8
[21:07:02]   ✓ COT copper: long=108,035 short=33,585 net=74,450 (27.1% OI)
[21:07:02]     COT copper trend: WoW -1.4 (down), MoM -1.4
[21:07:03]   ✓ imf_score: -1 (pos=1 neg=0)
[21:07:03]   ✓ default_score: +0 (pos=0 neg=0)
[21:07:04]   ✓ geo_score: +0 (pos=2 neg=2)
[21:07:04]   Metals complete: 104 fields
[21:07:04] === US screening ===
[21:07:04]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=95%(32.265919323715885) price_book_ratio=100%(32.55458211653456) price_sales_ratio=100%(23.91822958441775) enterprise_value_ebitda_ttm=72%(30.396041755523736) gross_margin=75%(74.1454331711974) operating_margin=99%(64.0200243795638) net_margin=99%(62.9659435640713) return_on_invested_capital=98%(106.17861300515598) debt_to_equity=97%(0.0655534751424742) current_ratio=99%(3.44077568134172) price_target_average=84%(309.933898) recommendation_mark=84%(1.125) recommendation_buy=84%(57) recommendation_total=84%(68) earnings_per_share_forecast_next_fq=96%(2.075352) earnings_per_share_fq=98%(1.866323)
[21:07:04]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[21:07:07]   TV prefilter: 2073 band names scanned -> Yahoo screens 687 (large-cap 218 + financials 204 + growth 252 + ttm-fallback 13); replaces a ~2291-name full-universe Yahoo screen; dropped 31 preferred/baby-bond series
[21:07:07]   D1 bank gate: 413 in-band financials -> dropped 158 (ROE<8%) + 51 (EPS<0) -> 204 to Yahoo (revenue gate bypassed for financials)
[21:07:07]   [diag] financials EPS-growth: 413 financials, 307 with data (fq 285, ttm 283); min -61933.3% median 10.8% max 999.2%; pass >=0% 187 | >=5% 175 | >=10% 160 | >=15% 147
[21:07:07]   [diag] financials ROE: 413 financials, 337 with data; min -201.9% median 8.9% max 242.3%; pass >=8% 179 | >=10% 150 | >=12% 102 | >=15% 57 | >=20% 33
[21:07:08]   L1 large-cap fundamentals: matched 215/218 named large-caps (TV)
[21:07:08]   Building screen from TV fundamentals (684 recs) + Yahoo fallback for gaps...
[21:07:09]   US scan (L1 TV-first): 1s, 554 candidates — 552 TV-sourced + 2 Yahoo-fallback (of 3 gaps); insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)
[21:07:09]   Fetching income_stmt EPS for 13 survivors missing earningsGrowth...
[21:07:36]   EPS enriched 13/13 previously-None survivors
[21:07:37]   [sector medians] 19 sectors -> sector_medians.json (19 with 200-DMA breadth; e.g. Electronic Technology PE~44.5455/ROE~0.1466/breadth~78.5%, Technology Services PE~25.004/ROE~0.1423/breadth~32.9%, Retail Trade PE~22.438/ROE~0.2019/breadth~52.9%)
[21:07:37]   [PSX sector breadth] 13 sectors >=5 names (e.g. Transportation 66.7%, Process Industries 63.9%, Non-Energy Minerals 62.5%)
[21:07:37]   [Wave PK-D] devaluation: WATCH (score 2/7) -> rupee_slope=0, reserves_fall=0, reer_stretch=1, sbp_rate=1, ca_stress=0
[21:07:37] === PSX screening ===
[21:07:37]   [Wave R free-lever probe] remaining free PSX-macro feeds (logging-only):
[21:07:38]     - SBP FX reserves (weekly, replaces manual sbp_reserves) - sbp.org.pk/ecodata: HTTP 200 text/html 245kb -> HTML 245kb, 72 table(s) + 11019 digits, carries 'reserves' -> likely parseable
[21:07:41]     - SBP EasyData macro portal (rate / reserves / external series): HTTP 200 text/html 24kb -> HTML 24kb, 7 table(s) + 2055 digits, carries 'sbp' -> likely parseable
[21:07:44]     - PBS CPI (monthly inflation, replaces manual pak_cpi): HTTP 200 text/xml 74kb -> HTML 74kb, no <table> but 26745 digits -> maybe parseable (text/figures)
[21:07:46]     - PBS external trade (monthly trade gap -> current-account proxy): HTTP 404 text/html 203kb -> HTML 203kb, no <table> but 6004 digits -> maybe parseable (text/figures)
[21:07:46]     - Finance Division fiscal operations (fiscal deficit, replaces manual pak_fiscal): HTTP 403 text/html 5kb -> CLOUDFLARE challenge -> blocked from runner
[21:07:46]     - OGRA petroleum prices (sector-regulator board sample): HTTP 403 text/html 5kb -> CLOUDFLARE challenge -> blocked from runner
[21:07:46] Fetching PSX universe...
[21:07:49]   ✓ PSX endpoint reachable
[21:07:49]   [F5 watchlist] 8 loaded ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; in top-500 scan -> force-include: ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; absent from scan (skipped): []
[21:07:49]   ✓ PSX universe: 49 candidates from TradingView Pakistan scanner
[21:07:49]   ✓ SSGC: price=31.32 (tv_scan)
[21:07:49]   ✓ TPL: price=15.72 (tv_scan)
[21:07:49]   ✓ LOTCHEM: price=28.46 (tv_scan)
[21:07:49]   ✓ KPUS: price=2432.69 (tv_scan)
[21:07:49]   ✓ KOSM: price=6.96 (tv_scan)
[21:07:49]   ✓ TOMCL: price=41.5 (tv_scan)
[21:07:49]   ✓ TRG: price=66.68 (tv_scan)
[21:07:49]   ✓ PAEL: price=42.75 (tv_scan)
[21:07:49]   ✓ NML: price=156.42 (tv_scan)
[21:07:49]   ✓ PIBTL: price=17.94 (tv_scan)
[21:07:49]   ✓ TPLP: price=10.24 (tv_scan)
[21:07:49]   ✓ JVDC: price=145.18 (tv_scan)
[21:07:49]   ✓ PSX: price=51.56 (tv_scan)
[21:07:49]   ✓ GAL: price=531.99 (tv_scan)
[21:07:49]   ✓ CSAP: price=112.64 (tv_scan)
[21:07:49]   ✓ PREMA: price=35.59 (tv_scan)
[21:07:49]   ✓ NPL: price=76.04 (tv_scan)
[21:07:49]   ✓ GATM: price=29.01 (tv_scan)
[21:07:49]   ✓ SEARL: price=94.4 (tv_scan)
[21:07:49]   ✓ NRL: price=374.49 (tv_scan)
[21:07:49]   ✓ SPEL: price=52.22 (tv_scan)
[21:07:49]   ✓ OCTOPUS: price=38.26 (tv_scan)
[21:07:49]   ✓ NCPL: price=65.74 (tv_scan)
[21:07:49]   ✓ HASCOL: price=21.2 (tv_scan)
[21:07:49]   ✓ SPWL: price=10.0 (tv_scan)
[21:07:49]   ✓ OGDC: price=331.28 (tv_scan)
[21:07:49]   ✓ PPL: price=241.94 (tv_scan)
[21:07:49]   ✓ MCB: price=402.93 (tv_scan)
[21:07:49]   ✓ FFC: price=560.74 (tv_scan)
[21:07:49]   ✓ HUBC: price=231.3 (tv_scan)
[21:07:49]   ✓ MTL: price=607.26 (tv_scan)
[21:07:49]   ✓ POL: price=693.77 (tv_scan)
[21:07:49]   ✓ THCCL: price=67.62 (tv_scan)
[21:07:49]   ✓ DOL: price=32.01 (tv_scan)
[21:07:49]   ✓ CLOV: price=8.35 (tv_scan)
[21:07:49]   ✓ AHL: price=113.99 (tv_scan)
[21:07:49]   ✓ PAKT: price=1402.26 (tv_scan)
[21:07:49]   ✓ HALEON: price=798.84 (tv_scan)
[21:07:49]   ✓ UBL: price=438.18 (tv_scan)
[21:07:49]   ✓ MEBL: price=512.98 (tv_scan)
[21:07:49]   ✓ HBL: price=298.4 (tv_scan)
[21:07:49]   ✓ NBP: price=203.51 (tv_scan)
[21:07:49]   ✓ ABL: price=186.22 (tv_scan)
[21:07:49]   ✓ BAFL: price=61.1 (tv_scan)
[21:07:49]   ✓ BAHL: price=173.36 (tv_scan)
[21:07:49]   ✓ AKBL: price=107.65 (tv_scan)
[21:07:49]   ✓ FABL: price=97.08 (tv_scan)
[21:07:49]   ✓ BOP: price=35.2 (tv_scan)
[21:07:49]   ✓ BIPL: price=26.85 (tv_scan)
[21:07:49]   PSX scan done: 49 candidates
[21:07:49]   [Wave Q snapshot] skipped (<24h since 2026-06-19T13:58:20.309385) — carrying last-good (13 banks)
[21:07:49]   [Wave Q sector] KPMG skipped (<30d) — carrying last-good
[21:07:49]   [Wave Q->IG2] SCS fallback overrides written for 12 bank(s): ['ABL', 'AKBL', 'BAFL', 'BAHL', 'BIPL', 'BOP', 'FABL', 'HBL', 'MCB', 'MEBL', 'NBP', 'UBL'] (im3_score fills these into missing roe/adr/roa-trend only)
[21:07:49]   [Wave P FMR] fetch skipped (2d ago, <7d) — carrying last-good fund-ownership + flows
[21:07:49]   [Wave PSX-R valmatrix] fetch skipped (1d ago, <7d) — carrying last-good
[21:08:11]   [Wave PSX-R MTS] as-of February 6, 2026: total Rs 28747.6mn across 56 symbols (chg -0.06%, wavg rate 12.58%); top: ['NBP', 'BOP', 'PSO', 'HUBC', 'HBL', 'FFC', 'OGDC', 'SEARL']
[21:08:11]   [Wave PSX-R MTS] DIAG parsed mts_amount_mn (first 15): AGP=30.633, AICL=512.975, AIRLINK=169.315, AKBL=729.707, ATRL=658.431, BAFL=242.808, BAHL=227.036, BOP=2525.839, CHCC=10.254, CPHL=166.777, DCR=0.0, DGKC=690.488, EFERT=54.024, FABL=235.037, FATIMA=296.198
[21:08:11]   [Wave PSX-R MSCI] shelved (stale 2016 SCS source) -> psx_msci empty
[21:08:11]   [Wave P breadth] adv=141 dec=313 unch=23 (top-477 mcap); vol leader=SSGC; val leader=OGDC
[21:08:11]   US TCE pool: 15 screen + 20 ETF-consensus = 35
[21:08:12]   US analyst overlay: matched 213/214 TCE-pool tickers (TV FactSet)
[21:08:12] === TCE on US (35 candidates) ===
[21:08:14]   VOXR: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[21:08:16]   HYLN: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum']
[21:08:18]   RJET: IGNORE total=3 conv=0 streams=['s1_news', 's3_insider', 's5_volume']
[21:08:20]   DVLT: WATCH total=5 conv=4 streams=['s3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[21:08:22]   ABTC: IGNORE total=0 conv=0 streams=[]
[21:08:24]   VSTM: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[21:08:34]   BTGO: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[21:08:36]   ARQQ: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital']
[21:08:41]   WVE: WATCH total=5 conv=4 streams=['s3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[21:08:43]   FWDI: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's11_target_upside', 's12_recommendation']
[21:08:44]   UMAC: HIGH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[21:08:49]   RHLD: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital']
[21:08:54]   ASPI: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[21:08:57]   FUBO: WATCH total=4 conv=3 streams=['s1_news', 's8_capital', 's11_target_upside', 's12_recommendation']
[21:09:04]   IAUX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside', 's12_recommendation']
[21:09:06]   MU: HIGH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[21:09:12]   NVDA: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[21:09:17]   AMD: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:09:21]   AMAT: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[21:09:24]   INTC: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's6_momentum', 's9_eps_rev']
[21:09:26]   LRCX: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[21:09:27]   AAPL: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[21:09:31]   CSCO: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:09:36]   AVGO: HIGH total=7 conv=5 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[21:09:39]   TXN: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:09:43]   KLAC: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:09:45]   QCOM: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's7_margin']
[21:09:47]   MRVL: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's9_eps_rev', 's12_recommendation']
[21:09:50]   WDC: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's8_capital', 's9_eps_rev']
[21:09:52]   MSFT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[21:09:55]   STX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:09:58]   SNDK: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's8_capital', 's9_eps_rev']
[21:10:00]   GOOGL: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[21:10:01]   CAT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[21:10:03]   XOM: IGNORE total=3 conv=2 streams=['s1_news', 's9_eps_rev', 's11_target_upside']
[21:10:03]   TCE: 8 HIGH, 18 WATCH out of 35 scanned
[21:10:03] === TCE on PSX (49 candidates) ===
[21:10:04]   SSGC: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:06]   TPL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[21:10:07]   LOTCHEM: IGNORE total=1 conv=1 streams=['s6_momentum']
[21:10:09]   KPUS: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:10]   KOSM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:11]   TOMCL: IGNORE total=1 conv=1 streams=['s6_momentum']
[21:10:12]   TRG: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[21:10:14]   PAEL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[21:10:16]   NML: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[21:10:17]   PIBTL: IGNORE total=1 conv=1 streams=['s6_momentum']
[21:10:18]   TPLP: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:20]   JVDC: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[21:10:21]   PSX: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
$GAL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[21:10:23]   GAL: WATCH total=3 conv=3 streams=['s6_momentum', 's11_target_upside', 's12_recommendation']
[21:10:25]   CSAP: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[21:10:26]   PREMA: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[21:10:28]   NPL: IGNORE total=1 conv=1 streams=['s6_momentum']
[21:10:29]   GATM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:30]   SEARL: IGNORE total=1 conv=1 streams=['s11_target_upside']
[21:10:32]   NRL: IGNORE total=0 conv=0 streams=[]
[21:10:33]   SPEL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[21:10:35]   OCTOPUS: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[21:10:37]   NCPL: IGNORE total=1 conv=0 streams=['s1_news']
[21:10:38]   HASCOL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[21:10:39]   SPWL: IGNORE total=0 conv=0 streams=[]
[21:10:40]   OGDC: WATCH total=3 conv=3 streams=['s6_momentum', 's11_target_upside', 's12_recommendation']
[21:10:42]   PPL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[21:10:43]   MCB: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[21:10:45]   FFC: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[21:10:46]   HUBC: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[21:10:48]   MTL: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[21:10:49]   POL: WATCH total=2 conv=2 streams=['s7_margin', 's12_recommendation']
[21:10:51]   THCCL: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[21:10:52]   DOL: IGNORE total=1 conv=0 streams=['s1_news']
[21:10:54]   CLOV: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[21:10:55]   AHL: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[21:10:56]   PAKT: IGNORE total=0 conv=0 streams=[]
[21:10:58]   HALEON: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[21:11:00]   UBL: WATCH total=4 conv=4 streams=['s6_momentum', 's7_margin', 's11_target_upside', 's12_recommendation']
[21:11:01]   MEBL: IGNORE total=1 conv=1 streams=['s12_recommendation']
[21:11:03]   HBL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[21:11:04]   NBP: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[21:11:05]   ABL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[21:11:07]   BAFL: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[21:11:08]   BAHL: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[21:11:10]   AKBL: WATCH total=2 conv=2 streams=['s6_momentum', 's12_recommendation']
[21:11:11]   FABL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[21:11:13]   BOP: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[21:11:14]   BIPL: IGNORE total=0 conv=0 streams=[]
[21:11:15]   TCE: 0 HIGH, 25 WATCH out of 49 scanned
[21:11:16] TCE predictions: 189 logged, 189 open (re-priced 17/63 off-pool); HIGH matured=0 hit=None alpha=None lift=None; WATCH matured=0 hit=None; IGNORE matured=0 hit=None
[21:11:16] === EXPLOSIVE screen on US (200 candidates) ===
[21:11:16]   VOXR: A=True B=True -> EXPLOSIVE — both signals
[21:11:17]   HYLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:17]   RJET: A=False B=False -> NOT EXPLOSIVE
[21:11:18]   DVLT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:19]   ABTC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:19]   VSTM: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:20]   BTGO: A=None B=None -> NOT EXPLOSIVE
[21:11:20]   ARQQ: A=False B=False -> NOT EXPLOSIVE
[21:11:21]   WVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:21]   FWDI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:22]   UMAC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:22]   RHLD: A=False B=False -> NOT EXPLOSIVE
[21:11:23]   ASPI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:23]   FUBO: A=False B=False -> NOT EXPLOSIVE
[21:11:24]   IAUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:24]   SSSS: A=None B=None -> NOT EXPLOSIVE
[21:11:25]   OABI: A=False B=False -> NOT EXPLOSIVE
[21:11:25]   GOLD: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:26]   GLOO: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:26]   MGRT: A=True B=True -> EXPLOSIVE — both signals
[21:11:27]   CRMD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:27]   SNDX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:28]   FBYD: A=False B=False -> NOT EXPLOSIVE
[21:11:28]   USAS: A=False B=False -> NOT EXPLOSIVE
[21:11:29]   MU: A=True B=True -> EXPLOSIVE — both signals
[21:11:30]   SPRY: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:30]   MSIF: A=None B=None -> NOT EXPLOSIVE
[21:11:31]   ATOM: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:32]   ASM: A=True B=True -> EXPLOSIVE — both signals
[21:11:32]   SKYT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:33]   PCT: A=None B=False -> NOT EXPLOSIVE — OP declining
[21:11:33]   IRWD: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:11:34]   NRGV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:34]   URGN: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:35]   RILY: A=False B=False -> NOT EXPLOSIVE
[21:11:35]   NUAI: A=False B=False -> NOT EXPLOSIVE
[21:11:36]   AGCC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:36]   ANGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:37]   PRLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:37]   AEBI: A=False B=False -> NOT EXPLOSIVE
[21:11:38]   GROY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:38]   HIVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:39]   STAA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:39]   SSII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:40]   GAU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:40]   EVC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:41]   MAKO: A=True B=True -> EXPLOSIVE — both signals
[21:11:42]   LPTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:42]   TIC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:43]   MUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:43]   NEWT: A=None B=None -> NOT EXPLOSIVE
[21:11:44]   CARE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:11:44]   PDYN: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:45]   ELE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:45]   PHAT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:46]   ELA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:46]   LIFE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:47]   LPG: A=True B=True -> EXPLOSIVE — both signals
[21:11:47]   AMLX: A=False B=False -> NOT EXPLOSIVE
[21:11:48]   AMN: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:48]   IDR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:49]   ATLC: A=None B=None -> NOT EXPLOSIVE
[21:11:49]   ABCL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:50]   VRDN: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:51]   FIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:51]   ASST: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:52]   SATA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:52]   LTC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:53]   CSWC: A=None B=None -> NOT EXPLOSIVE
[21:11:53]   BIOA: A=None B=False -> NOT EXPLOSIVE — OP declining
[21:11:54]   XZO: A=None B=None -> NOT EXPLOSIVE
[21:11:54]   JCAP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:11:55]   PICS: A=None B=None -> NOT EXPLOSIVE
[21:11:55]   DELL: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:11:56]   SRTA: A=False B=False -> NOT EXPLOSIVE
[21:11:56]   SENS: A=False B=False -> NOT EXPLOSIVE
[21:11:57]   AEVA: A=False B=False -> NOT EXPLOSIVE
[21:11:57]   NVDA: A=True B=True -> EXPLOSIVE — both signals
[21:11:58]   UPB: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:58]   INR: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:11:59]   ZSQR: A=None B=False -> NOT EXPLOSIVE — OP declining
[21:11:59]   SATL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:00]   SCZM: A=False B=False -> NOT EXPLOSIVE
[21:12:00]   LAES: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:01]   ZVRA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:02]   CMCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:02]   SHIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:03]   SHLS: A=False B=False -> NOT EXPLOSIVE
[21:12:03]   FENC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:04]   MBI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:04]   ADAM: A=None B=None -> NOT EXPLOSIVE
[21:12:05]   OMC: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:05]   DCH: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:06]   AQST: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:06]   SI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:07]   NAT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:07]   KMTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:08]   GNK: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:08]   ROMA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:09]   AMBQ: A=False B=False -> NOT EXPLOSIVE
[21:12:09]   BBNX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:10]   SKYH: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:10]   TLS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:11]   ASTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:12]   LLY: A=True B=True -> EXPLOSIVE — both signals
[21:12:12]   ASIC: A=True B=True -> EXPLOSIVE — both signals
[21:12:13]   OSS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:13]   GRRR: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:14]   ISTR: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:14]   HSHP: A=False B=False -> NOT EXPLOSIVE
[21:12:15]   CGBD: A=None B=None -> NOT EXPLOSIVE
[21:12:15]   PAYS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:16]   SIDU: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:16]   ECVT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:17]   MAMA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:17]   GSBD: A=None B=None -> NOT EXPLOSIVE
[21:12:18]   ENVX: A=False B=False -> NOT EXPLOSIVE
[21:12:18]   VELO: A=False B=False -> NOT EXPLOSIVE
[21:12:19]   AVGO: A=True B=True -> EXPLOSIVE — both signals
[21:12:20]   GEVO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:20]   NEM: A=True B=True -> EXPLOSIVE — both signals
[21:12:21]   JANX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:21]   WYFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:22]   EZPW: A=False B=False -> NOT EXPLOSIVE
[21:12:22]   EVGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:23]   WDC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:23]   KOS: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:24]   IOVA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:25]   EVLV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:25]   ROCK: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:26]   WEST: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:26]   STX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:27]   OFRM: A=None B=None -> NOT EXPLOSIVE
[21:12:27]   HLIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:28]   CLPT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:28]   PKE: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:12:29]   COF: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:29]   OMDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:30]   TOI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:30]   ATEX: A=False B=False -> NOT EXPLOSIVE
[21:12:31]   FLYW: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:31]   MRVI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:32]   ETON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:32]   NEXA: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:12:33]   CDNA: A=False B=False -> NOT EXPLOSIVE
[21:12:33]   PANL: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:34]   CRON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:34]   XERS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:35]   SLDE: A=True B=True -> EXPLOSIVE — both signals
[21:12:36]   WELL: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:36]   RYZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:37]   AMD: A=True B=True -> EXPLOSIVE — both signals
[21:12:37]   PRSU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:38]   ACRS: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:38]   LWAY: A=False B=False -> NOT EXPLOSIVE
[21:12:39]   RES: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:39]   TREE: A=True B=True -> EXPLOSIVE — both signals
[21:12:40]   DMLP: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:41]   PLBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:41]   PNTG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:42]   TWFG: A=True B=True -> EXPLOSIVE — both signals
[21:12:42]   ANET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:43]   TSM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:43]   ABX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:44]   CCNE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:44]   MCBS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:45]   CYD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:45]   KARO: A=False B=False -> NOT EXPLOSIVE
[21:12:46]   SNDA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:46]   DASH: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:47]   META: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:48]   ALB: A=False B=False -> NOT EXPLOSIVE
[21:12:48]   GCT: A=False B=False -> NOT EXPLOSIVE
[21:12:49]   OSBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:49]   CLMB: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:50]   COFS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:12:50]   REAX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:51]   ASYS: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:51]   EFC: A=None B=None -> NOT EXPLOSIVE
[21:12:52]   GERN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:52]   GENI: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:53]   VINP: A=True B=True -> EXPLOSIVE — both signals
[21:12:53]   BX: A=None B=None -> NOT EXPLOSIVE
[21:12:54]   KURA: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:54]   CBLL: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:55]   VIA: A=False B=False -> NOT EXPLOSIVE
[21:12:55]   ALKT: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:56]   WLKP: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:56]   TEN: A=False B=False -> NOT EXPLOSIVE
[21:12:57]   BALY: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:12:57]   QNST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:12:58]   VEL: A=None B=None -> NOT EXPLOSIVE
[21:12:59]   TRIN: A=None B=None -> NOT EXPLOSIVE
[21:12:59]   ARDX: A=False B=False -> NOT EXPLOSIVE — OP declining
[21:13:00]   VMD: A=True B=True -> EXPLOSIVE — both signals
[21:13:00]   TXO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[21:13:01]   LWLG: A=False B=False -> NOT EXPLOSIVE
[21:13:01]   UTL: A=False B=False -> NOT EXPLOSIVE
[21:13:02]   MNST: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:13:02]   SWBI: A=False B=True -> INFLECTION (accelerating off low base — verify)
[21:13:02]   EXPLOSIVE: 17 both-signal of 200 scored; 8 financials -> bank model; 0 insufficient-data
[21:13:02] === EXPLOSIVE screen on PSX (49 candidates) ===
[21:13:02]   SSGC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   TPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   LOTCHEM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   KPUS: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   KOSM: A=None B=None -> INSUFFICIENT DATA
[21:13:02]   TOMCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   TRG: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PAEL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   NML: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PIBTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   TPLP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   JVDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PSX: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   GAL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   CSAP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PREMA: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   NPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   GATM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   SEARL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   NRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   SPEL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   OCTOPUS: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   NCPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   HASCOL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   SPWL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   OGDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   MCB: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   FFC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   HUBC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   MTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   POL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   THCCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   DOL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   CLOV: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   AHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   PAKT: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   HALEON: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[21:13:02]   UBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   MEBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   HBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   NBP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   ABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   BAFL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   BAHL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   AKBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   FABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   BOP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   BIPL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[21:13:02]   EXPLOSIVE: 0 both-signal of 49 scored; 12 financials -> bank model; 1 insufficient-data
[21:13:03]   ✓ COT futures (TFF): 4/4 [10yr, NASDAQ, SP500, VIX]
[21:13:04]   ✓ COT futures Crude: found
[21:13:10]   ✓ Recession calendar: 9 high-impact US releases (faireconomy)
[21:13:10]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 9 calendar events
[21:13:10]   → Zacks scrape skipped (last scrape 5d ago, <7d) — carrying forward last-good
[21:13:11]     · [diag] stockanalysis FTXL: HTTP 200 body[:180]='{"status":200,"data":{"holdings":[{"no":1,"n":"Intel Corporation","s":"$INTC","as":"12.13%","sh":"2,698,441"},{"no":2,"n":"Micron Technology, Inc.","s":"$MU","as":"11.56%","sh":"29'
[21:13:11]     · [diag] stockanalysis FTXL: parsed 25 holdings
[21:13:38]   ETF overlap: 30/30 ETFs returned holdings -> top 25 consensus stocks
[21:13:38]   Carried forward 238 last-good IM3 score(s) onto rebuilt records
[21:13:38]   [Wave T history] 2026-06-19: 2 day(s) stored (kse100=178922.76, mts=28747.6mn, usd/pkr=277.98)
[21:13:38]   [Wave T shortlist] 205 stock-rows tracked (184 live) across 7 tabs; 30 sector baskets
[21:13:38] data.json written (2938737 bytes)
[21:13:38] ============================================================
[21:13:38] Scanner completed
[21:13:38]   Hard errors: 0
[21:13:38]   Warnings (degraded data): 0
[21:13:38]   US macros: 97
[21:13:38]   PSX macros: 20
[21:13:38]   KSE-100: 178922.76 (tradingview:KSE100 (official close), as of 2026-06-19)
[21:13:38]   WTI/Brent: 76.54 / 80.59 (yahoo:CL=F, as of 2026-06-19)
[21:13:38]   US candidates: 15
[21:13:38]   PSX candidates: 49
[21:13:38]   US TCE HIGH: 8
[21:13:38]   PSX TCE HIGH: 0
[21:13:38]   Recession: LOW (score 0, 9 cal events)
[21:13:38] ============================================================
