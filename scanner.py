Run python scanner.py
[08:45:35] ============================================================
[08:45:35] Dashboard scanner v1.40.0 starting
[08:45:35] ============================================================
[08:45:35] Fetching US macros from FRED...
[08:45:37]   ✓ fed_rate = 3.75
[08:45:38]   ✓ core_pce = 3.29
[08:45:39]   ✓ cpi_yoy = 3.95
[08:45:42]   ✓ us_10y = 4.56
[08:45:44]   ✓ us_2y = 4.15
[08:45:45]   ✓ unemployment = 4.3
[08:45:46]   ✓ umcsi = 49.8
[08:45:47]   ✓ mfg_emp = 12605.0
[08:45:48]   ✓ gdp_growth = 1.6
[08:45:49]   ✓ industrial_prod = 102.5
[08:45:50]   ✓ hy_spread = 2.75
[08:45:51]   ✓ permits = 1423.0
[08:45:51]   ✓ wti (live CL=F) = 88.26 (as of 2026-06-10)
[08:45:51]   ✓ brent (live BZ=F) = 91.67 (as of 2026-06-10)
[08:45:51]   ✓ Brent-WTI spread = 3.41
[08:45:51]   → US rigs skipped (EIA fetch 6d ago, <7d) — last-good 545
[08:45:51]   ✓ FOMC: 2026-05-20 — Minutes of the Federal Open Market Committee, April 28-29, 2
[08:45:51]   Total US macros: 95
[08:45:51] Fetching PSX macros...
[08:45:56]   ✓ KSE-100 (psx-dps:int (last session close)): 169734.3 (as of 2026-06-10)
[08:45:56]   ✓ USD/PKR: 278.0
[08:45:57]   ✓ SBP rate (SBP official): 11.5%
[08:45:57]     · [diag] TGE inflation_annual: 200 len=392 hasRecent=False seg=' SuperJS check window.__SUPERJS_TARGET__ = "\\/Pakistan\\/inflation_annual\\/"; '
[08:45:57]     · [diag] TheGlobalEconomy inflation_annual: no value parsed
[08:45:58]   → SBP reserves: official page is PDF; keeping last-good if TE missed (manual override)
[08:45:58]   → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: ['pak_ca', 'pak_fiscal']
[08:45:58] Fetching metals data...
[08:45:58]   ✓ gold_px (GC=F): 4194.4
[08:45:58]   ✓ silver_px (SI=F): 64.04
[08:45:58]   ✓ platinum_px (PL=F): 1672.9
[08:45:58]   ✓ palladium_px (PA=F): 1219.0
[08:45:58]   ✓ dxy (DX-Y.NYB): 99.91
[08:45:58]   ✓ Gold:Silver ratio = 65.5
[08:45:58]   ✓ WALCL: $6.71T (+0.03%)
[08:45:59]   ✓ dfii10 (DFII10): 2.21
[08:46:00]   ✓ breakeven_10y (T10YIE): 2.33
[08:46:02]   ✓ gvz (GVZCLS): 27.17
[08:46:02]   ✓ COT gold: long=206,096 short=30,076 net=176,020 (54.0% OI)
[08:46:02]     COT gold trend: WoW +0.0 (flat)
[08:46:02]   ✓ COT silver: long=33,933 short=10,007 net=23,926 (23.3% OI)
[08:46:02]     COT silver trend: WoW +0.0 (flat)
[08:46:02]   ✓ COT copper: long=111,525 short=32,692 net=78,833 (28.5% OI)
[08:46:02]     COT copper trend: WoW +0.0 (flat)
[08:46:02]   ✓ imf_score: +0 (pos=0 neg=0)
[08:46:03]   ✓ default_score: +0 (pos=0 neg=0)
[08:46:04]   ✓ geo_score: +1 (pos=2 neg=1)
[08:46:04]   Metals complete: 98 fields
[08:46:04] === US screening ===
[08:46:04]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=95%(31.88305920548868) price_book_ratio=100%(32.168296790741515) price_sales_ratio=100%(23.634421269067975) enterprise_value_ebitda_ttm=72%(30.030511555479027) gross_margin=76%(74.1454331711974) operating_margin=100%(64.0200243795638) net_margin=100%(62.9659435640713) return_on_invested_capital=98%(106.17861300515598) debt_to_equity=96%(0.0655534751424742) current_ratio=99%(3.44077568134172) price_target_average=84%(309.933898) recommendation_mark=84%(1.125) recommendation_buy=84%(57) recommendation_total=84%(68) earnings_per_share_forecast_next_fq=96%(2.074852) earnings_per_share_fq=98%(1.866323)
[08:46:04]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[08:46:07]   TV prefilter: 1978 band names scanned -> Yahoo screens 664 (large-cap 223 + financials 173 + growth 257 + ttm-fallback 11); replaces a ~2201-name full-universe Yahoo screen
[08:46:07]   D1 bank gate: 381 in-band financials -> dropped 158 (ROE<8%) + 50 (EPS<0) -> 173 to Yahoo (revenue gate bypassed for financials)
[08:46:07]   [diag] financials EPS-growth: 381 financials, 314 with data (fq 294, ttm 285); min -5480.9% median 15.3% max 999.2%; pass >=0% 200 | >=5% 188 | >=10% 172 | >=15% 159
[08:46:07]   [diag] financials ROE: 381 financials, 347 with data; min -201.9% median 9.3% max 242.3%; pass >=8% 189 | >=10% 160 | >=12% 107 | >=15% 62 | >=20% 35
[08:46:07]   Screening 664 pre-filtered tickers via Yahoo Finance...
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: AGM.A"}}}
[08:46:32]   Progress: 100/664 (15%) — survived: 31 — ETA: 2.4min
[08:46:57]   Progress: 200/664 (30%) — survived: 58 — ETA: 1.9min
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: HES"}}}
[08:47:22]   Progress: 300/664 (45%) — survived: 97 — ETA: 1.5min
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: IPG"}}}
[08:47:47]   Progress: 400/664 (60%) — survived: 135 — ETA: 1.1min
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: PARA"}}}
[08:48:12]   Progress: 500/664 (75%) — survived: 175 — ETA: 0.7min
[08:48:37]   Progress: 600/664 (90%) — survived: 222 — ETA: 0.3min
[08:48:53]   US scan: 2.8min, 249 candidates passed all gates
[08:48:53]   Fetching income_stmt EPS for 100 survivors missing earningsGrowth...
[08:50:04]   EPS enriched 99/100 previously-None survivors
[08:50:04] === PSX screening ===
[08:50:04] Fetching PSX universe...
[08:50:07]   ✓ PSX endpoint reachable
[08:50:07]   ✓ PSX universe: 25 candidates from TradingView Pakistan scanner
[08:50:07]   ✓ TPLP: price=11.08 (tv_scan)
[08:50:07]   ✓ BBFL: price=47.06 (tv_scan)
[08:50:07]   ✓ TPL: price=13.91 (tv_scan)
[08:50:07]   ✓ LOADS: price=14.24 (tv_scan)
[08:50:07]   ✓ ASTL: price=16.97 (tv_scan)
[08:50:07]   ✓ TELE: price=9.2 (tv_scan)
[08:50:07]   ✓ PAEL: price=40.55 (tv_scan)
[08:50:07]   ✓ MUGHAL: price=80.91 (tv_scan)
[08:50:07]   ✓ TRG: price=70.69 (tv_scan)
[08:50:07]   ✓ GAL: price=473.0 (tv_scan)
[08:50:07]   ✓ JVDC: price=148.62 (tv_scan)
[08:50:07]   ✓ THCCL: price=67.82 (tv_scan)
[08:50:07]   ✓ HCAR: price=267.29 (tv_scan)
[08:50:07]   ✓ ASL: price=13.11 (tv_scan)
[08:50:07]   ✓ HASCOL: price=21.97 (tv_scan)
[08:50:07]   ✓ TOMCL: price=37.42 (tv_scan)
[08:50:07]   ✓ HTL: price=45.0 (tv_scan)
[08:50:07]   ✓ AGHA: price=8.35 (tv_scan)
[08:50:07]   ✓ INIL: price=166.03 (tv_scan)
[08:50:07]   ✓ KPUS: price=2452.0 (tv_scan)
[08:50:07]   ✓ ISL: price=84.75 (tv_scan)
[08:50:07]   ✓ MACFL: price=60.68 (tv_scan)
[08:50:07]   ✓ ADMM: price=70.49 (tv_scan)
[08:50:07]   ✓ PACE: price=11.68 (tv_scan)
[08:50:07]   ✓ TREET: price=24.69 (tv_scan)
[08:50:07]   PSX scan done: 25 candidates
[08:50:07]   US TCE pool: 15 screen + 20 ETF-consensus = 35
[08:50:08]   US analyst overlay: matched 35/35 TCE-pool tickers (TV FactSet)
[08:50:08] === TCE on US (35 candidates) ===
[08:50:10]   VOXR: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[08:50:11]   HYLN: IGNORE total=4 conv=1 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum']
[08:50:13]   DVLT: WATCH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:19]   GLOO: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[08:50:20]   WVE: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:24]   FWDI: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's11_target_upside', 's12_recommendation']
[08:50:25]   MGRT: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:50:28]   UMAC: HIGH total=8 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[08:50:30]   RHLD: IGNORE total=3 conv=1 streams=['s3_insider', 's5_volume', 's8_capital']
[08:50:31]   ASPI: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:32]   AGCC: IGNORE total=0 conv=0 streams=[]
[08:50:34]   IAUX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside', 's12_recommendation']
[08:50:38]   OABI: IGNORE total=4 conv=2 streams=['s3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[08:50:40]   GOLD: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:43]   CRMD: WATCH total=6 conv=5 streams=['s1_news', 's6_momentum', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:45]   MU: HIGH total=8 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[08:50:47]   NVDA: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[08:50:49]   AMD: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:50:51]   INTC: WATCH total=5 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's9_eps_rev']
[08:50:53]   AMAT: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[08:50:55]   LRCX: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[08:50:57]   AAPL: WATCH total=5 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's9_eps_rev']
[08:50:58]   AVGO: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[08:51:00]   CSCO: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:51:03]   QCOM: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin']
[08:51:05]   TXN: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:51:07]   KLAC: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:51:10]   MRVL: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's9_eps_rev', 's12_recommendation']
[08:51:15]   MSFT: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[08:51:17]   GOOGL: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[08:51:18]   CAT: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:51:21]   XOM: IGNORE total=4 conv=1 streams=['s1_news', 's2_sponsor', 's3_insider', 's9_eps_rev']
[08:51:23]   SNDK: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's8_capital', 's9_eps_rev']
[08:51:25]   ADI: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:51:28]   MPWR: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside']
[08:51:28]   TCE: 8 HIGH, 19 WATCH out of 35 scanned
[08:51:28] === TCE on PSX (25 candidates) ===
[08:51:29]   TPLP: IGNORE total=1 conv=1 streams=['s6_momentum']
$BBFL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[08:51:30]   BBFL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:51:32]   TPL: WATCH total=4 conv=2 streams=['s1_news', 's2_sponsor', 's6_momentum', 's7_margin']
[08:51:33]   LOADS: IGNORE total=2 conv=0 streams=['s1_news', 's2_sponsor']
[08:51:34]   ASTL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[08:51:36]   TELE: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:51:37]   PAEL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[08:51:38]   MUGHAL: WATCH total=2 conv=2 streams=['s7_margin', 's11_target_upside']
[08:51:40]   TRG: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
$GAL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[08:51:41]   GAL: IGNORE total=0 conv=0 streams=[]
[08:51:42]   JVDC: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:51:44]   THCCL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:51:45]   HCAR: WATCH total=3 conv=2 streams=['s5_volume', 's6_momentum', 's11_target_upside']
[08:51:46]   ASL: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[08:51:48]   HASCOL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:51:49]   TOMCL: IGNORE total=0 conv=0 streams=[]
[08:51:50]   HTL: IGNORE total=1 conv=1 streams=['s7_margin']
[08:51:52]   AGHA: IGNORE total=1 conv=1 streams=['s7_margin']
[08:51:53]   INIL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[08:51:54]   KPUS: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[08:51:56]   ISL: WATCH total=2 conv=2 streams=['s7_margin', 's11_target_upside']
[08:51:57]   MACFL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:51:58]   ADMM: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[08:51:59]   PACE: IGNORE total=2 conv=1 streams=['s1_news', 's6_momentum']
[08:52:01]   TREET: IGNORE total=3 conv=1 streams=['s1_news', 's2_sponsor', 's7_margin']
[08:52:01]   TCE: 0 HIGH, 9 WATCH out of 25 scanned
[08:52:02] TCE predictions: 115 logged, 115 open (re-priced 6/27 off-pool); HIGH matured=0 hit=None alpha=None lift=None; WATCH matured=0 hit=None; IGNORE matured=0 hit=None
[08:52:02] === EXPLOSIVE screen on US (200 candidates) ===
[08:52:02]   VOXR: A=True B=True -> EXPLOSIVE — both signals
[08:52:03]   HYLN: A=False B=None -> INSUFFICIENT DATA
[08:52:03]   DVLT: A=False B=None -> INSUFFICIENT DATA
[08:52:04]   GLOO: A=False B=None -> INSUFFICIENT DATA
[08:52:04]   WVE: A=False B=None -> INSUFFICIENT DATA
[08:52:05]   FWDI: A=False B=None -> INSUFFICIENT DATA
[08:52:05]   MGRT: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:06]   UMAC: A=False B=None -> INSUFFICIENT DATA
[08:52:06]   RHLD: A=False B=False -> NOT EXPLOSIVE
[08:52:07]   ASPI: A=False B=None -> INSUFFICIENT DATA
[08:52:07]   AGCC: A=False B=False -> NOT EXPLOSIVE
[08:52:08]   IAUX: A=False B=None -> INSUFFICIENT DATA
[08:52:09]   OABI: A=False B=None -> INSUFFICIENT DATA
[08:52:09]   GOLD: A=False B=False -> NOT EXPLOSIVE
[08:52:10]   CRMD: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:10]   FBYD: A=False B=None -> INSUFFICIENT DATA
[08:52:11]   USAS: A=False B=None -> INSUFFICIENT DATA
[08:52:11]   SPRY: A=False B=None -> INSUFFICIENT DATA
[08:52:12]   SKYT: A=False B=False -> NOT EXPLOSIVE
[08:52:12]   NRGV: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:13]   NUAI: A=False B=None -> INSUFFICIENT DATA
[08:52:13]   COFS: A=False B=False -> NOT EXPLOSIVE
[08:52:14]   GROY: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:14]   QURE: A=False B=None -> INSUFFICIENT DATA
[08:52:15]   SSII: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:15]   EVC: A=False B=False -> NOT EXPLOSIVE
[08:52:16]   RILY: A=False B=None -> INSUFFICIENT DATA
[08:52:16]   BTGO: A=False B=False -> NOT EXPLOSIVE
[08:52:17]   ECO: A=False B=False -> NOT EXPLOSIVE
[08:52:17]   ASM: A=True B=True -> EXPLOSIVE — both signals
[08:52:18]   ELE: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:18]   TIC: A=False B=False -> NOT EXPLOSIVE
[08:52:19]   MUX: A=False B=None -> INSUFFICIENT DATA
[08:52:19]   PDYN: A=False B=None -> INSUFFICIENT DATA
[08:52:20]   LPG: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:20]   NAT: A=False B=False -> NOT EXPLOSIVE
[08:52:21]   ELA: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:21]   IDR: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:22]   ABCL: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:23]   FIP: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:23]   DELL: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:24]   SRTA: A=False B=None -> INSUFFICIENT DATA
[08:52:24]   AEVA: A=False B=None -> INSUFFICIENT DATA
[08:52:25]   AEBI: A=False B=False -> NOT EXPLOSIVE
[08:52:25]   UPB: A=False B=None -> INSUFFICIENT DATA
[08:52:26]   SCZM: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:26]   SATL: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:27]   SHIP: A=False B=False -> NOT EXPLOSIVE
[08:52:27]   FENC: A=False B=False -> NOT EXPLOSIVE
[08:52:28]   SENS: A=False B=None -> INSUFFICIENT DATA
[08:52:28]   PICS: A=False B=False -> NOT EXPLOSIVE
[08:52:29]   KMTS: A=False B=None -> INSUFFICIENT DATA
[08:52:29]   ATLC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:30]   GNK: A=False B=False -> NOT EXPLOSIVE
[08:52:30]   AMBQ: A=False B=None -> INSUFFICIENT DATA
[08:52:31]   CARL: A=False B=None -> INSUFFICIENT DATA
[08:52:31]   ISTR: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:32]   SKYH: A=False B=None -> INSUFFICIENT DATA
[08:52:32]   TLS: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:33]   ASTH: A=False B=False -> NOT EXPLOSIVE
[08:52:33]   ASIC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:34]   OSS: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:34]   GRRR: A=False B=False -> NOT EXPLOSIVE
[08:52:35]   HSHP: A=False B=False -> NOT EXPLOSIVE
[08:52:35]   PAYS: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:36]   ENVX: A=False B=None -> INSUFFICIENT DATA
[08:52:36]   VELO: A=False B=None -> INSUFFICIENT DATA
[08:52:37]   SSSS: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:37]   BWB: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:38]   EVGO: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:39]   SKWD: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:39]   WEST: A=False B=None -> INSUFFICIENT DATA
[08:52:40]   MCBS: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:40]   CLPT: A=False B=None -> INSUFFICIENT DATA
[08:52:41]   PKE: A=True B=True -> EXPLOSIVE — both signals
[08:52:41]   GEMI: A=False B=None -> INSUFFICIENT DATA
[08:52:42]   NEXA: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:52:42]   TOI: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:43]   MRVI: A=False B=None -> INSUFFICIENT DATA
[08:52:43]   CRON: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:44]   PANL: A=False B=False -> NOT EXPLOSIVE
[08:52:44]   AIP: A=False B=None -> INSUFFICIENT DATA
[08:52:45]   SNDA: A=False B=None -> INSUFFICIENT DATA
[08:52:46]   SLDE: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:46]   RYZ: A=False B=False -> NOT EXPLOSIVE
[08:52:47]   MCB: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:47]   LWAY: A=False B=False -> NOT EXPLOSIVE
[08:52:48]   RES: A=False B=False -> NOT EXPLOSIVE
[08:52:48]   TREE: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:49]   DMLP: A=False B=False -> NOT EXPLOSIVE
[08:52:49]   PNTG: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:50]   BWFG: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:50]   PKBK: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:51]   ANET: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:51]   ABX: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:52]   NBN: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:52]   RJET: A=False B=False -> NOT EXPLOSIVE
[08:52:53]   LOB: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:53]   PLBC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:52:54]   GCT: A=False B=False -> NOT EXPLOSIVE
[08:52:54]   CLMB: A=False B=False -> NOT EXPLOSIVE
[08:52:55]   REAX: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:52:55]   ASYS: A=False B=None -> INSUFFICIENT DATA
[08:52:56]   WYFI: A=False B=False -> NOT EXPLOSIVE
[08:52:56]   GENI: A=False B=None -> INSUFFICIENT DATA
[08:52:57]   AROW: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:52:57]   CBLL: A=False B=None -> INSUFFICIENT DATA
[08:52:58]   VIA: A=False B=None -> INSUFFICIENT DATA
[08:52:58]   ALKT: A=False B=None -> INSUFFICIENT DATA
[08:52:59]   WLKP: A=False B=False -> NOT EXPLOSIVE
[08:52:59]   TEN: A=False B=False -> NOT EXPLOSIVE
[08:53:00]   BALY: A=False B=False -> NOT EXPLOSIVE
[08:53:00]   NPB: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:01]   VMD: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:01]   FSBC: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:02]   MNST: A=False B=False -> NOT EXPLOSIVE
[08:53:02]   XRX: A=False B=False -> NOT EXPLOSIVE
[08:53:03]   FTK: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:03]   DCTH: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:04]   BLDP: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:05]   SFST: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:05]   SVCO: A=False B=None -> INSUFFICIENT DATA
[08:53:06]   TCBX: A=False B=False -> NOT EXPLOSIVE
[08:53:06]   BFLY: A=False B=None -> INSUFFICIENT DATA
[08:53:07]   OOMA: A=False B=None -> INSUFFICIENT DATA
[08:53:07]   WLFC: A=False B=False -> NOT EXPLOSIVE
[08:53:08]   NFBK: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:08]   KDK: A=False B=None -> INSUFFICIENT DATA
[08:53:09]   FSTR: A=False B=False -> NOT EXPLOSIVE
[08:53:09]   TK: A=False B=False -> NOT EXPLOSIVE
[08:53:10]   GCBC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:10]   KRUS: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:11]   LINC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:11]   PAX: A=False B=False -> NOT EXPLOSIVE
[08:53:12]   SOPH: A=False B=None -> INSUFFICIENT DATA
[08:53:12]   ORCL: A=False B=False -> NOT EXPLOSIVE
[08:53:13]   DAKT: A=False B=False -> NOT EXPLOSIVE
[08:53:13]   APPN: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:14]   ANIP: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:14]   ELVA: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:15]   GILT: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:15]   CVEO: A=False B=False -> NOT EXPLOSIVE
[08:53:16]   APPS: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:16]   CDRE: A=False B=False -> NOT EXPLOSIVE
[08:53:17]   MQ: A=False B=None -> INSUFFICIENT DATA
[08:53:17]   STLD: A=False B=False -> NOT EXPLOSIVE
[08:53:18]   ASC: A=False B=False -> NOT EXPLOSIVE
[08:53:18]   ITRN: A=False B=False -> NOT EXPLOSIVE
[08:53:19]   KARO: A=False B=False -> NOT EXPLOSIVE
[08:53:20]   PLPC: A=False B=False -> NOT EXPLOSIVE
[08:53:20]   REAL: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:21]   COSO: A=False B=False -> NOT EXPLOSIVE
[08:53:21]   ELMD: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:22]   LXU: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:22]   TALK: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:23]   GOOS: A=False B=False -> NOT EXPLOSIVE
[08:53:23]   RNGR: A=False B=False -> NOT EXPLOSIVE
[08:53:24]   PCB: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:24]   ROMA: A=False B=None -> INSUFFICIENT DATA
[08:53:25]   RDVT: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:25]   WEAV: A=False B=None -> INSUFFICIENT DATA
[08:53:26]   WGS: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:26]   MAX: A=False B=False -> NOT EXPLOSIVE
[08:53:27]   WSBF: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:27]   VINP: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:28]   CCB: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:28]   ESQ: A=False B=False -> NOT EXPLOSIVE
[08:53:29]   OBT: A=False B=False -> NOT EXPLOSIVE
[08:53:29]   AMPL: A=False B=None -> INSUFFICIENT DATA
[08:53:30]   IBEX: A=False B=False -> NOT EXPLOSIVE
[08:53:30]   QUIK: A=False B=None -> INSUFFICIENT DATA
[08:53:31]   IE: A=False B=None -> INSUFFICIENT DATA
[08:53:31]   AMZN: A=False B=False -> NOT EXPLOSIVE
[08:53:32]   HRMY: A=False B=False -> NOT EXPLOSIVE
[08:53:32]   WTBA: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:33]   MS: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:34]   JMSB: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:34]   PBT: A=False B=False -> NOT EXPLOSIVE
[08:53:35]   UNTY: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:35]   AVAH: A=True B=True -> EXPLOSIVE — both signals
[08:53:36]   GLP: A=False B=False -> NOT EXPLOSIVE
[08:53:36]   BSVN: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:37]   SCHW: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:53:37]   SES: A=True B=None -> QUALITY-GROWTH (Signal A only)
[08:53:38]   TSLA: A=False B=False -> NOT EXPLOSIVE
[08:53:38]   LIND: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:39]   INNV: A=False B=None -> INSUFFICIENT DATA
[08:53:39]   JOUT: A=False B=None -> INSUFFICIENT DATA
[08:53:40]   WTI: A=False B=None -> INSUFFICIENT DATA
[08:53:40]   MRLN: A=False B=None -> INSUFFICIENT DATA
[08:53:41]   VITL: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:41]   MPTI: A=False B=False -> NOT EXPLOSIVE
[08:53:42]   BFST: A=False B=False -> NOT EXPLOSIVE
[08:53:42]   SHBI: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:43]   USCB: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:43]   FMBH: A=False B=False -> NOT EXPLOSIVE
[08:53:44]   BY: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:44]   ISBA: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:45]   CZFS: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   ITIC: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   EXPLOSIVE: 4 both-signal (non-financial) of 200 scored; 50 financials flagged for bank model
[08:53:46] === EXPLOSIVE screen on PSX (25 candidates) ===
[08:53:46]   TPLP: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   BBFL: A=None B=None -> INSUFFICIENT DATA
[08:53:46]   TPL: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   LOADS: A=False B=False -> NOT EXPLOSIVE
[08:53:46]   ASTL: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   TELE: A=None B=None -> INSUFFICIENT DATA
[08:53:46]   PAEL: A=True B=True -> EXPLOSIVE — both signals
[08:53:46]   MUGHAL: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   TRG: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   GAL: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:46]   JVDC: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:46]   THCCL: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:46]   HCAR: A=True B=False -> QUALITY-GROWTH (Signal A only)
[08:53:46]   ASL: A=None B=None -> INSUFFICIENT DATA
[08:53:46]   HASCOL: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   TOMCL: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   HTL: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   AGHA: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   INIL: A=True B=True -> EXPLOSIVE — both signals
[08:53:46]   KPUS: A=None B=None -> INSUFFICIENT DATA
[08:53:46]   ISL: A=True B=True -> EXPLOSIVE — both signals
[08:53:46]   MACFL: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   ADMM: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   PACE: A=False B=None -> INSUFFICIENT DATA
[08:53:46]   TREET: A=False B=True -> INFLECTION (Signal B only — verify quality)
[08:53:46]   EXPLOSIVE: 3 both-signal (non-financial) of 25 scored; 0 financials flagged for bank model
[08:53:46]   ✓ COT futures (TFF): 4/4 [10yr, NASDAQ, SP500, VIX]
[08:53:47]   ✓ COT futures Crude: found
[08:53:54]   ✓ Recession calendar: 9 high-impact US releases (faireconomy)
[08:53:54]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 9 calendar events
[08:53:54]   → Zacks scrape skipped (last scrape 0d ago, <7d) — carrying forward last-good
[08:53:54]   → ETF holdings overlap skipped (last scrape 0d ago, <7d) — carrying forward last-good
[08:53:54]   Carried forward 41 last-good IM3 score(s) onto rebuilt records
[08:53:54] data.json written (528468 bytes)
[08:53:54] ============================================================
[08:53:54] Scanner completed
[08:53:54]   Hard errors: 0
[08:53:54]   Warnings (degraded data): 0
[08:53:54]   US macros: 95
[08:53:54]   PSX macros: 17
[08:53:54]   KSE-100: 169734.3 (psx-dps:int (last session close), as of 2026-06-10)
[08:53:54]   WTI/Brent: 88.26 / 91.67 (yahoo:CL=F, as of 2026-06-10)
[08:53:54]   US candidates: 15
[08:53:54]   PSX candidates: 25
[08:53:54]   US TCE HIGH: 8
[08:53:54]   PSX TCE HIGH: 0
[08:53:54]   Recession: LOW (score 0, 9 cal events)
[08:53:54] ============================================================
