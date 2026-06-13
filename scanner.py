Run python scanner.py
[07:56:58] ============================================================
[07:56:58] Dashboard scanner v1.51.0 starting
[07:56:58] ============================================================
[07:56:58] Fetching US macros from FRED...
[07:57:00]   ✓ fed_rate = 3.75
[07:57:01]   ✓ core_pce = 3.29
[07:57:02]   ✓ cpi_yoy = 4.27
[07:57:04]   ✓ us_10y = 4.45
[07:57:06]   ✓ us_2y = 4.05
[07:57:07]   ✓ unemployment = 4.3
[07:57:08]   ✓ umcsi = 49.8
[07:57:09]   ✓ mfg_emp = 12605.0
[07:57:10]   ✓ gdp_growth = 1.6
[07:57:11]   ✓ industrial_prod = 102.5
[07:57:12]   ✓ hy_spread = 2.78
[07:57:13]   ✓ permits = 1423.0
[07:57:14]   ✓ wti (live CL=F) = 84.88 (as of 2026-06-12)
[07:57:14]   ✓ brent (live BZ=F) = 87.33 (as of 2026-06-12)
[07:57:14]   ✓ Brent-WTI spread = 2.45
[07:57:14]   → US rigs skipped (EIA fetch 2d ago, <7d) — last-good 545
[07:57:14]   ✓ FOMC: 2026-05-20 — Minutes of the Federal Open Market Committee, April 28-29, 2
[07:57:14]   Total US macros: 95
[07:57:14] Fetching PSX macros...
[07:57:20]   ✓ KSE-100 (psx-dps:int (last session close)): 171562.22 (as of 2026-06-12)
[07:57:21]   ✓ USD/PKR: 278.03
[07:57:22]   ✓ SBP rate (SBP official): 11.5%
[07:57:23]   ✓ Pak CPI YoY (TheGlobalEconomy): 7.3%
[07:57:24]   → SBP reserves: official page is PDF; keeping last-good if TE missed (manual override)
[07:57:24]   → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: ['pak_ca', 'pak_fiscal']
[07:57:24] Fetching metals data...
[07:57:24]   ✓ gold_px (GC=F): 4215.0
[07:57:24]   ✓ silver_px (SI=F): 67.86
[07:57:24]   ✓ platinum_px (PL=F): 1709.2
[07:57:25]   ✓ palladium_px (PA=F): 1276.2
[07:57:25]   ✓ dxy (DX-Y.NYB): 99.75
[07:57:25]   ✓ Gold:Silver ratio = 62.1
[07:57:25]   ✓ WALCL: $6.73T (-0.05%)
[07:57:26]   ✓ dfii10 (DFII10): 2.16
[07:57:26]   ✓ breakeven_10y (T10YIE): 2.31
[07:57:27]   ✓ gvz (GVZCLS): 28.33
[07:57:27]   ✓ COT gold: long=207,984 short=34,147 net=173,837 (52.2% OI)
[07:57:27]     COT gold trend: WoW -1.8 (down), MoM -1.8
[07:57:27]   ✓ COT silver: long=32,487 short=10,273 net=22,214 (21.5% OI)
[07:57:27]     COT silver trend: WoW -1.8 (down), MoM -1.8
[07:57:27]   ✓ COT copper: long=108,035 short=33,585 net=74,450 (27.1% OI)
[07:57:27]     COT copper trend: WoW -1.4 (down), MoM -1.4
[07:57:28]   ✓ imf_score: -1 (pos=1 neg=0)
[07:57:29]   ✓ default_score: +0 (pos=0 neg=0)
[07:57:29]   ✓ geo_score: +1 (pos=3 neg=2)
[07:57:29]   Metals complete: 104 fields
[07:57:29] === US screening ===
[07:57:30]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=95%(31.42362706361604) price_book_ratio=99%(31.704754399789863) price_sales_ratio=100%(23.293851290648245) enterprise_value_ebitda_ttm=72%(29.591875315425373) gross_margin=76%(74.1454331711974) operating_margin=99%(64.0200243795638) net_margin=99%(62.9659435640713) return_on_invested_capital=98%(106.17861300515598) debt_to_equity=96%(0.0655534751424742) current_ratio=99%(3.44077568134172) price_target_average=84%(309.933898) recommendation_mark=84%(1.123188) recommendation_buy=84%(58) recommendation_total=84%(69) earnings_per_share_forecast_next_fq=95%(2.074852) earnings_per_share_fq=98%(1.866323)
[07:57:30]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[07:57:33]   TV prefilter: 2069 band names scanned -> Yahoo screens 689 (large-cap 223 + financials 196 + growth 258 + ttm-fallback 12); replaces a ~2292-name full-universe Yahoo screen; dropped 31 preferred/baby-bond series
[07:57:33]   D1 bank gate: 404 in-band financials -> dropped 157 (ROE<8%) + 51 (EPS<0) -> 196 to Yahoo (revenue gate bypassed for financials)
[07:57:33]   [diag] financials EPS-growth: 404 financials, 305 with data (fq 283, ttm 282); min -61933.3% median 10.7% max 999.2%; pass >=0% 185 | >=5% 173 | >=10% 158 | >=15% 145
[07:57:33]   [diag] financials ROE: 404 financials, 335 with data; min -201.9% median 8.9% max 242.3%; pass >=8% 178 | >=10% 147 | >=12% 100 | >=15% 55 | >=20% 33
[07:57:34]   L1 large-cap fundamentals: matched 215/223 named large-caps (TV)
[07:57:34]   Building screen from TV fundamentals (681 recs) + Yahoo fallback for gaps...
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: HES"}}}
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: IPG"}}}
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found","description":"Quote not found for symbol: PARA"}}}
[07:57:37]   US scan (L1 TV-first): 3s, 551 candidates — 549 TV-sourced + 2 Yahoo-fallback (of 8 gaps); insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)
[07:57:37]   Fetching income_stmt EPS for 13 survivors missing earningsGrowth...
[07:58:04]   EPS enriched 13/13 previously-None survivors
[07:58:04] === PSX screening ===
[07:58:04] Fetching PSX universe...
[07:58:07]   ✓ PSX endpoint reachable
[07:58:07]   ✓ PSX universe: 30 candidates from TradingView Pakistan scanner
[07:58:07]   ✓ JVDC: price=153.16 (tv_scan)
[07:58:07]   ✓ TPL: price=14.09 (tv_scan)
[07:58:07]   ✓ TRG: price=69.78 (tv_scan)
[07:58:07]   ✓ PAEL: price=41.07 (tv_scan)
[07:58:07]   ✓ GAL: price=485.33 (tv_scan)
[07:58:07]   ✓ SPEL: price=49.09 (tv_scan)
[07:58:07]   ✓ PIBTL: price=17.51 (tv_scan)
[07:58:07]   ✓ HCAR: price=270.28 (tv_scan)
[07:58:07]   ✓ GHNI: price=941.23 (tv_scan)
[07:58:07]   ✓ THCCL: price=69.16 (tv_scan)
[07:58:07]   ✓ MUGHAL: price=82.88 (tv_scan)
[07:58:07]   ✓ NCPL: price=64.56 (tv_scan)
[07:58:07]   ✓ TPLP: price=10.9 (tv_scan)
[07:58:07]   ✓ IGIHL: price=284.15 (tv_scan)
[07:58:07]   ✓ LOADS: price=15.05 (tv_scan)
[07:58:07]   ✓ NML: price=146.34 (tv_scan)
[07:58:07]   ✓ CHCC: price=296.17 (tv_scan)
[07:58:07]   ✓ POWER: price=21.5 (tv_scan)
[07:58:07]   ✓ TOMCL: price=38.08 (tv_scan)
[07:58:07]   ✓ KPUS: price=2420.59 (tv_scan)
[07:58:07]   ✓ HASCOL: price=21.51 (tv_scan)
[07:58:07]   ✓ NRL: price=358.32 (tv_scan)
[07:58:07]   ✓ SEARL: price=91.38 (tv_scan)
[07:58:07]   ✓ DCL: price=12.05 (tv_scan)
[07:58:07]   ✓ NETSOL: price=132.03 (tv_scan)
[07:58:07]   ✓ OGDC: price=317.99 (tv_scan)
[07:58:07]   ✓ PPL: price=225.84 (tv_scan)
[07:58:07]   ✓ MCB: price=399.95 (tv_scan)
[07:58:07]   ✓ FFC: price=556.45 (tv_scan)
[07:58:07]   ✓ HUBC: price=219.59 (tv_scan)
[07:58:07]   PSX scan done: 30 candidates
[07:58:07]   [Wave P FMR] fetch skipped (2d ago, <7d) — carrying last-good fund-ownership + flows
[07:58:07]   [Wave P breadth] adv=269 dec=164 unch=42 (top-475 mcap); vol leader=KOSM; val leader=MLCF
[07:58:08]   US TCE pool: 15 screen + 20 ETF-consensus = 35
[07:58:09]   US analyst overlay: matched 35/35 TCE-pool tickers (TV FactSet)
[07:58:09] === TCE on US (35 candidates) ===
[07:58:11]   VOXR: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[07:58:15]   HYLN: WATCH total=5 conv=1 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum']
[07:58:17]   RJET: IGNORE total=1 conv=0 streams=['s5_volume']
[07:58:20]   DVLT: WATCH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[07:58:23]   ABTC: IGNORE total=0 conv=0 streams=[]
[07:58:25]   VSTM: WATCH total=5 conv=4 streams=['s1_news', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[07:58:30]   BTGO: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[07:58:36]   WVE: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[07:58:40]   FWDI: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's11_target_upside', 's12_recommendation']
[07:58:45]   MRLN: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's11_target_upside', 's12_recommendation']
[07:58:48]   UMAC: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's8_capital', 's11_target_upside', 's12_recommendation']
[07:58:51]   RHLD: IGNORE total=3 conv=1 streams=['s3_insider', 's5_volume', 's8_capital']
[07:58:53]   TRX: IGNORE total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[07:58:56]   ASPI: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[07:58:58]   FUBO: WATCH total=5 conv=3 streams=['s1_news', 's2_sponsor', 's8_capital', 's11_target_upside', 's12_recommendation']
[07:59:03]   MU: HIGH total=8 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[07:59:05]   NVDA: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[07:59:08]   AMD: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[07:59:10]   INTC: WATCH total=5 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's9_eps_rev']
[07:59:13]   AMAT: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[07:59:15]   LRCX: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's12_recommendation']
[07:59:18]   AAPL: WATCH total=5 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's9_eps_rev']
[07:59:23]   AVGO: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[07:59:28]   CSCO: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[07:59:31]   QCOM: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin']
[07:59:36]   TXN: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[07:59:38]   KLAC: WATCH total=6 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's7_margin', 's9_eps_rev']
[07:59:44]   MRVL: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's9_eps_rev', 's12_recommendation']
[07:59:51]   MSFT: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[07:59:53]   GOOGL: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's7_margin', 's11_target_upside', 's12_recommendation']
[08:00:00]   CAT: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:00:02]   XOM: WATCH total=5 conv=2 streams=['s1_news', 's2_sponsor', 's3_insider', 's9_eps_rev', 's11_target_upside']
[08:00:08]   SNDK: WATCH total=6 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's8_capital', 's9_eps_rev']
[08:00:11]   ADI: WATCH total=7 conv=3 streams=['s1_news', 's2_sponsor', 's3_insider', 's5_volume', 's6_momentum', 's7_margin', 's9_eps_rev']
[08:00:13]   MPWR: HIGH total=7 conv=4 streams=['s1_news', 's2_sponsor', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside']
[08:00:13]   TCE: 7 HIGH, 22 WATCH out of 35 scanned
[08:00:13] === TCE on PSX (30 candidates) ===
[08:00:15]   JVDC: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:00:17]   TPL: WATCH total=4 conv=2 streams=['s1_news', 's2_sponsor', 's6_momentum', 's7_margin']
[08:00:19]   TRG: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[08:00:21]   PAEL: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
$GAL.KA: possibly delisted; no price data found  (period=6mo) (Yahoo error = "No data found, symbol may be delisted")
[08:00:23]   GAL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:25]   SPEL: WATCH total=3 conv=2 streams=['s1_news', 's6_momentum', 's7_margin']
[08:00:27]   PIBTL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:28]   HCAR: WATCH total=3 conv=2 streams=['s5_volume', 's6_momentum', 's11_target_upside']
[08:00:30]   GHNI: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:32]   THCCL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:34]   MUGHAL: WATCH total=2 conv=2 streams=['s7_margin', 's11_target_upside']
[08:00:36]   NCPL: IGNORE total=2 conv=0 streams=['s1_news', 's2_sponsor']
[08:00:38]   TPLP: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:39]   IGIHL: WATCH total=3 conv=2 streams=['s5_volume', 's6_momentum', 's7_margin']
[08:00:41]   LOADS: IGNORE total=3 conv=1 streams=['s1_news', 's2_sponsor', 's6_momentum']
[08:00:43]   NML: WATCH total=3 conv=3 streams=['s7_margin', 's11_target_upside', 's12_recommendation']
[08:00:45]   CHCC: WATCH total=3 conv=3 streams=['s6_momentum', 's11_target_upside', 's12_recommendation']
[08:00:47]   POWER: IGNORE total=3 conv=1 streams=['s1_news', 's2_sponsor', 's6_momentum']
[08:00:48]   TOMCL: IGNORE total=1 conv=1 streams=['s6_momentum']
[08:00:50]   KPUS: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[08:00:52]   HASCOL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:00:54]   NRL: IGNORE total=0 conv=0 streams=[]
[08:00:56]   SEARL: IGNORE total=1 conv=1 streams=['s11_target_upside']
[08:00:58]   DCL: IGNORE total=2 conv=1 streams=['s5_volume', 's6_momentum']
[08:01:00]   NETSOL: WATCH total=2 conv=2 streams=['s6_momentum', 's7_margin']
[08:01:02]   OGDC: WATCH total=3 conv=3 streams=['s6_momentum', 's11_target_upside', 's12_recommendation']
[08:01:04]   PPL: WATCH total=4 conv=2 streams=['s1_news', 's2_sponsor', 's11_target_upside', 's12_recommendation']
[08:01:06]   MCB: WATCH total=4 conv=2 streams=['s1_news', 's2_sponsor', 's11_target_upside', 's12_recommendation']
[08:01:08]   FFC: WATCH total=2 conv=2 streams=['s11_target_upside', 's12_recommendation']
[08:01:10]   HUBC: IGNORE total=2 conv=0 streams=['s1_news', 's2_sponsor']
[08:01:10]   TCE: 0 HIGH, 16 WATCH out of 30 scanned
[08:01:12] TCE predictions: 141 logged, 141 open (re-priced 14/44 off-pool); HIGH matured=0 hit=None alpha=None lift=None; WATCH matured=0 hit=None; IGNORE matured=0 hit=None
[08:01:12] === EXPLOSIVE screen on US (200 candidates) ===
[08:01:13]   VOXR: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:01:13]   HYLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:14]   RJET: A=False B=False -> NOT EXPLOSIVE
[08:01:14]   DVLT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:15]   ABTC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:16]   VSTM: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:16]   BTGO: A=None B=None -> NOT EXPLOSIVE
[08:01:17]   WVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:17]   FWDI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:18]   MRLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:18]   UMAC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:19]   RHLD: A=False B=False -> NOT EXPLOSIVE
[08:01:20]   TRX: A=True B=True -> EXPLOSIVE — both signals
[08:01:20]   ASPI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:21]   FUBO: A=False B=False -> NOT EXPLOSIVE
[08:01:22]   IAUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:22]   SSSS: A=None B=None -> NOT EXPLOSIVE
[08:01:23]   OABI: A=False B=False -> NOT EXPLOSIVE
[08:01:23]   GOLD: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:01:24]   GLOO: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:24]   MGRT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:25]   CRMD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:25]   SNDX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:26]   FBYD: A=False B=False -> NOT EXPLOSIVE
[08:01:26]   USAS: A=False B=False -> NOT EXPLOSIVE
[08:01:27]   MU: A=True B=True -> EXPLOSIVE — both signals
[08:01:28]   SPRY: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:28]   MSIF: A=None B=None -> NOT EXPLOSIVE
[08:01:29]   ATOM: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:30]   ASM: A=True B=True -> EXPLOSIVE — both signals
[08:01:30]   SKYT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:31]   PCT: A=None B=False -> NOT EXPLOSIVE — OP declining
[08:01:31]   IRWD: A=False B=True -> INFLECTION (accelerating off low base — verify)
[08:01:32]   NRGV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:32]   URGN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:33]   RILY: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:01:33]   NUAI: A=False B=False -> NOT EXPLOSIVE
[08:01:34]   AGCC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:34]   ANGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:35]   PRLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:36]   AGIO: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:36]   AEBI: A=False B=False -> NOT EXPLOSIVE
[08:01:37]   GROY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:37]   HIVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:38]   QURE: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:38]   STAA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:39]   SSII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:39]   GAU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:40]   EVC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:41]   MAKO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:41]   LPTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:42]   TIC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:42]   MUX: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:43]   NEWT: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:01:43]   CARE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:01:44]   PDYN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:44]   ELE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:45]   PHAT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:45]   ELA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:46]   LIFE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:47]   LPG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:47]   AMLX: A=False B=False -> NOT EXPLOSIVE
[08:01:48]   AMN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:48]   IDR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:49]   ATLC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:01:49]   ABCL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:50]   VRDN: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:51]   FIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:51]   ASST: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:52]   SATA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:52]   LTC: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:01:53]   CSWC: A=None B=None -> NOT EXPLOSIVE
[08:01:53]   BIOA: A=None B=False -> NOT EXPLOSIVE — OP declining
[08:01:54]   XZO: A=None B=None -> NOT EXPLOSIVE
[08:01:54]   JCAP: A=True B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:01:55]   PICS: A=None B=None -> NOT EXPLOSIVE
[08:01:56]   DELL: A=False B=False -> NOT EXPLOSIVE
[08:01:56]   SRTA: A=False B=False -> NOT EXPLOSIVE
[08:01:57]   SENS: A=False B=False -> NOT EXPLOSIVE
[08:01:57]   AEVA: A=False B=False -> NOT EXPLOSIVE
[08:01:58]   NVDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:01:58]   UPB: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:59]   INR: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:01:59]   ZSQR: A=None B=False -> NOT EXPLOSIVE — OP declining
[08:02:00]   SATL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:01]   LAES: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:01]   ZVRA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:02]   CMCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:02]   SHIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:03]   SHLS: A=False B=False -> NOT EXPLOSIVE
[08:02:03]   FENC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:04]   MBI: A=True B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:04]   ADAM: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:05]   OMC: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:06]   DCH: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:06]   AQST: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:07]   SI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:07]   NAT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:08]   KMTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:08]   GNK: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:09]   ROMA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:10]   AMBQ: A=False B=False -> NOT EXPLOSIVE
[08:02:10]   CARL: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:11]   BBNX: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:11]   SKYH: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:12]   TLS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:12]   ASTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:13]   LLY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:14]   ASIC: A=True B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:14]   OSS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:15]   GRRR: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:15]   ISTR: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:16]   HSHP: A=False B=False -> NOT EXPLOSIVE
[08:02:16]   CGBD: A=None B=None -> NOT EXPLOSIVE
[08:02:17]   PAYS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:17]   SIDU: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:18]   ECVT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:19]   MAMA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:19]   GSBD: A=None B=None -> NOT EXPLOSIVE
[08:02:20]   ENVX: A=False B=False -> NOT EXPLOSIVE
[08:02:20]   VELO: A=False B=False -> NOT EXPLOSIVE
[08:02:21]   AVGO: A=True B=True -> EXPLOSIVE — both signals
[08:02:22]   GEVO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:22]   NEM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:23]   JANX: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:23]   WYFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:24]   EZPW: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:24]   EVGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:25]   WDC: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:25]   KOS: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:26]   IOVA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:27]   EVLV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:27]   ROCK: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:28]   WEST: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:28]   STX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:29]   OFRM: A=None B=None -> NOT EXPLOSIVE
[08:02:29]   HLIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:30]   CLPT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:31]   PKE: A=False B=True -> INFLECTION (accelerating off low base — verify)
[08:02:31]   COF: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:32]   OMDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:32]   TOI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:33]   ATEX: A=False B=False -> NOT EXPLOSIVE
[08:02:34]   FLYW: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:34]   MRVI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:35]   ETON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:35]   NEXA: A=False B=True -> INFLECTION (accelerating off low base — verify)
[08:02:36]   CDNA: A=False B=False -> NOT EXPLOSIVE
[08:02:36]   PANL: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:37]   AIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:38]   CRON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:38]   XERS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:39]   SLDE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:39]   WELL: A=False B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:40]   RYZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:41]   AMD: A=True B=True -> EXPLOSIVE — both signals
[08:02:41]   PRSU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:42]   ACRS: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:42]   LWAY: A=False B=False -> NOT EXPLOSIVE
[08:02:43]   RES: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:44]   TREE: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:02:44]   DMLP: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:45]   PLBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:45]   PNTG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:46]   TWFG: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:02:47]   ANET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:47]   TSM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:48]   ABX: A=True B=False -> FINANCIAL — score via bank model (IM3 System B)
[08:02:48]   CCNE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:49]   MCBS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:49]   CYD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:50]   KARO: A=False B=False -> NOT EXPLOSIVE
[08:02:51]   SNDA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:51]   DASH: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:52]   META: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:52]   ALB: A=False B=False -> NOT EXPLOSIVE
[08:02:53]   GCT: A=False B=False -> NOT EXPLOSIVE
[08:02:53]   OSBC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:54]   CLMB: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:54]   COFS: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:55]   REAX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:56]   SCZM: A=False B=False -> NOT EXPLOSIVE
[08:02:56]   ASYS: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:57]   EFC: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:02:57]   GERN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:02:58]   GENI: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:02:59]   VINP: A=True B=True -> FINANCIAL — score via bank model (IM3 System B)
[08:02:59]   VCEL: A=False B=False -> NOT EXPLOSIVE
[08:03:00]   AMSC: A=True B=True -> QUALITY-GROWTH (growth + accel, cash unconfirmed)
[08:03:01]   BX: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:03:01]   KURA: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:03:02]   CBLL: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:03:02]   VIA: A=False B=False -> NOT EXPLOSIVE
[08:03:03]   ALKT: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:03:03]   WLKP: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:03:04]   TEN: A=False B=False -> NOT EXPLOSIVE
[08:03:04]   BALY: A=False B=False -> NOT EXPLOSIVE — OP declining
[08:03:05]   QNST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[08:03:06]   FIGS: A=False B=False -> NOT EXPLOSIVE
[08:03:06]   VEL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:03:06]   EXPLOSIVE: 5 both-signal of 200 scored; 28 financials -> bank model; 0 insufficient-data
[08:03:06] === EXPLOSIVE screen on PSX (30 candidates) ===
[08:03:06]   JVDC: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   TPL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   TRG: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   PAEL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   GAL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   SPEL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   PIBTL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   HCAR: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   GHNI: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   THCCL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   MUGHAL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   NCPL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   TPLP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:03:06]   IGIHL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:03:06]   LOADS: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   NML: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   CHCC: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   POWER: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   TOMCL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   KPUS: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   HASCOL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   NRL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   SEARL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   DCL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   NETSOL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   OGDC: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   PPL: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   MCB: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[08:03:06]   FFC: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   HUBC: A=None B=None -> NOT EXPLOSIVE
[08:03:06]   EXPLOSIVE: 0 both-signal of 30 scored; 3 financials -> bank model; 0 insufficient-data
[08:03:07]   ✓ COT futures (TFF): 4/4 [10yr, NASDAQ, SP500, VIX]
[08:03:08]   ✓ COT futures Crude: found
[08:03:15]   ✓ Recession calendar: 9 high-impact US releases (faireconomy)
[08:03:15]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 9 calendar events
[08:03:15]   → Zacks scrape skipped (last scrape 3d ago, <7d) — carrying forward last-good
[08:03:15]     · [diag] stockanalysis FTXL: HTTP 200 body[:180]='{"status":200,"data":{"holdings":[{"no":1,"n":"Intel Corporation","s":"$INTC","as":"11.89%","sh":"2,684,881"},{"no":2,"n":"Micron Technology, Inc.","s":"$MU","as":"10.96%","sh":"29'
[08:03:15]     · [diag] stockanalysis FTXL: parsed 25 holdings
[08:03:54]   ETF overlap: 30/30 ETFs returned holdings -> top 25 consensus stocks
[08:03:54]   Carried forward 129 last-good IM3 score(s) onto rebuilt records
[08:03:54] data.json written (1179840 bytes)
[08:03:54] ============================================================
[08:03:54] Scanner completed
[08:03:54]   Hard errors: 0
[08:03:54]   Warnings (degraded data): 0
[08:03:54]   US macros: 95
[08:03:54]   PSX macros: 17
[08:03:54]   KSE-100: 171562.22 (psx-dps:int (last session close), as of 2026-06-12)
[08:03:54]   WTI/Brent: 84.88 / 87.33 (yahoo:CL=F, as of 2026-06-12)
[08:03:54]   US candidates: 15
[08:03:54]   PSX candidates: 30
[08:03:54]   US TCE HIGH: 7
[08:03:54]   PSX TCE HIGH: 0
[08:03:54]   Recession: LOW (score 0, 9 cal events)
[08:03:54] ============================================================
