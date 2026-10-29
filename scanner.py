Run python scanner.py
  [existing] im3_detail: inline 0 + file 463 -> union 463 entries
  [existing] loaded 7,353,906 bytes / 158 top-level keys
[03:58:42] ============================================================
[03:58:42] Dashboard scanner v1.591.0 starting
[03:58:42] ============================================================
[03:58:42]   [SEC contract] all SEC-fed consumers receive every statement row they read (deep scorer 28 rows, explosive screen, multibagger CFO/CPAT, EPS gap-fill)
[03:58:42] Fetching US macros from FRED...
[03:58:42] Fetching PSX macros...
[03:58:42] Fetching metals data...
[03:58:42]   ⚠ [TV econ ok] universe=global serving core_pce, cpi_yoy, fed_rate, ppi_core_yoy, unemployment
[03:58:42]   [TV econ] global/scan served 5 level(s): core_pce=3.0, cpi_yoy=3.7, fed_rate=4.0, ppi_core_yoy=5.0, unemployment=4.2
[03:58:42]   [TV econ primary] serving levels for core_pce, fed_rate, ppi_core_yoy, unemployment
[03:58:42]   · KSE-100 TradingView index symbols -> {'PSX:KSE100': 165736.7555, 'PSX:KSE30': 48838.3814}
[03:58:42]   ✓ KSE-100 (tradingview:KSE100 (official close)): 165736.76 (as of 2026-10-29)
[03:58:42]   ✓ USD/PKR (TV FX_IDC:USDPKR): 276.46
[03:58:42]   ✓ gold_px (TV COMEX:GC1!): 4053.3 · SMA200 4524.07 · down death · RSI 37.7
[03:58:42]   ✓ silver_px (TV COMEX:SI1!): 53.28 · SMA200 71.4 · down death · RSI 29.2
[03:58:42]   ✓ platinum_px (TV NYMEX:PL1!): 1521.8 · SMA200 1903.67 · down death · RSI 28.3
[03:58:42]   ✓ palladium_px (TV NYMEX:PA1!): 1002.0 · SMA200 1429.14 · down death · RSI 21.2
[03:58:42]   ✓ copper_px (TV COMEX:HG1!): 6.65 · SMA200 6.24 · up golden · RSI 52.5
[03:58:42]   ✓ dxy (TV TVC:DXY): 102.17 · SMA200 99.63 · up golden · RSI 58.9
[03:58:42]   ✓ Gold:Silver ratio = 76.1
[03:58:43]   ✓ WALCL: $6.75T (+0.09%)
[03:58:44]   ✓ dfii10 (DFII10): 2.64
[03:58:44]   ✓ breakeven_10y (T10YIE): 2.38
[03:58:45]   ✓ gvz (GVZCLS): 22.58
[03:58:45]   ✓ COT gold: long=237,142 short=37,277 net=199,865 (49.7% OI)
[03:58:45]     COT gold percentile: 17th (24wk history)
[03:58:45]     COT gold trend: WoW -2.7 (down), MoM -5.0, QoQ +1.7
[03:58:45]   ✓ COT silver: long=34,575 short=14,780 net=19,795 (17.4% OI)
[03:58:45]     COT silver percentile: 4th (24wk history)
[03:58:45]     COT silver trend: WoW -3.5 (down), MoM -6.5, QoQ -4.7
[03:58:45]   ✓ COT copper: long=98,535 short=41,138 net=57,397 (17.5% OI)
[03:58:45]     COT copper percentile: 4th (24wk history)
[03:58:45]     COT copper trend: WoW -4.3 (down), MoM -12.5, QoQ -9.9
[03:58:47]   ✓ COT pctile gold: 80.0 (260w)
[03:58:47]   ✓ COT pctile silver: 30.0 (260w)
[03:58:47]   ✓ COT pctile copper: 75.0 (260w)
[03:58:47]   ✓ COT pctile platinum: 57.0 (260w)
[03:58:47]   ✓ COT pctile palladium: 67.0 (260w)
[03:58:47]   [COT×Seasonality] Oct: gold Conflicting (COT bullish/pctile 80.0, seas unfavorable +0.61%) | silver Headwind (COT bearish/pctile 30.0, seas unfavorable +0.23%) | copper Conflicting (COT bullish/pctile 75.0, seas unfavorable -0.07%)
[03:58:48]   ✓ imf_score: +1 (pos=0 neg=1)
[03:58:48]   [FRED] prefetched 12/16 series in parallel (5 workers, gate 2 req/s)
[03:58:48]   + fed_rate = 4.0 (TV primary; FRED skipped)
[03:58:48]   + core_pce = 3.0 (TV primary; FRED skipped)
[03:58:48]   ✓ cpi_yoy = 4.0
[03:58:48]   ✓ ppi_yoy = 6.35
[03:58:48]   + ppi_core_yoy = 5.0 (TV primary; FRED skipped)
[03:58:48]   ✓ us_10y = 4.99
[03:58:48]   ✓ us_30y = 5.3
[03:58:48]   ✓ us_real_10y = 2.64
[03:58:48]   ✓ us_2y = 4.7
[03:58:48]   + unemployment = 4.2 (TV primary; FRED skipped)
[03:58:48]   ✓ umcsi = 48.1
[03:58:48]   ✓ mfg_emp = 12652.0
[03:58:48]   ✓ gdp_growth = 2.2
[03:58:48]   ✓ industrial_prod = 103.95
[03:58:48]   ✓ hy_spread = 3.18
[03:58:48]   ✓ permits = 1398.0
[03:58:48]   [TE econ] rescued from TradingEconomics: umcsi=48.0
[03:58:48]   ✓ umcsi override: FRED print 58d old -> TE current 48.0 (was 48.1)
[03:58:49]   ⚠ [TV econ ok] universe=global serving cpi_yoy
[03:58:49]   [TV econ] global/scan served 1 level(s): cpi_yoy=3.7
[03:58:49]   [cpi] official headline override: 3.7 (FRED index-derived kept in cpi_diag)
[03:58:49]   ✓ default_score: +0 (pos=0 neg=0)
[03:58:49]   ✓ TIC Japan UST = $1185.5B (-17.2 m/m)
[03:58:49]   ✓ geo_score: +0 (pos=0 neg=0)
[03:58:49]   Metals complete: 217 fields
[03:58:49]   [stage] metals 7s
[03:58:50]   ✓ sp500 = 7743.98
[03:58:50]   ✓ wti (TV symbol GET NYMEX:CL1!) = 101.43
[03:58:50]   ✓ brent (TV symbol GET ICEEUR:BRN1!) = 110.23
[03:58:50]   ✓ Brent-WTI spread = 8.8
[03:58:51]   ✓ wti_spot (FRED roll-free) = 103.37 wow -4.19% mom 4.03%
[03:58:51]   ✓ SBP rate (SBP official): 12.0%
[03:58:51]   ✓ brent_spot (FRED roll-free) = 123.1 wow 6.84% mom 2.61%
[03:58:51]   [wti trends] history authority: filled ['wow', 'mom', 'qoq'] (91 days on file)
[03:58:51]   [brent trends] history authority: filled ['wow', 'mom'] (34 days on file)
[03:58:51]   ✓ Pak CPI YoY (TheGlobalEconomy): 10.42%
[03:58:52]   ✓ ndx (NASDAQ100) = 29813.16
[03:58:52]   ✓ dow (DJIA) = 52475.1
[03:58:52]   ✓ rut (AMEX:IWM) = 2812.9
[03:58:53]   ✓ Arab Light (Dubai proxy) = 93.3 $/bbl (2026-09)
[03:58:53]   ✓ Arab Light LIVE estimate = 108.23 $/bbl (Brent 110.23 - spread 2.0)
[03:58:53]   → US rigs skipped (EIA fetch 0d ago, <7d) — last-good 589
[03:58:53]   ✓ FOMC: 2026-10-28 — Federal Reserve issues FOMC statement
[03:58:53]   Total US macros: 130
[03:58:53]   [stage] fetch_us_macros 11s
[03:58:53]   · reer manual value 105.17 IGNORED: no "reer_as_of" date in psx_macros_manual.json (an undated hand-typed number cannot beat a dated live one)
[03:58:59]   ✓ REER (headline): 108.9 -- PKR’s REER Index rises to 108.9 in September - Mettis Global
[03:58:59]   ✓ Current account (Business Recorder): -356.0mn -- Current account deficit widens to $356m in September - The News Pakistan
[03:58:59]   ✓ Fiscal deficit (headline): 2.6% GDP -- Pakistan’s fiscal deficit narrows to 22-year low of 2.6% of GDP in FY26: Schehzad - Business Recorder
[03:58:59]   ✓ SBP reserves (Business Recorder weekly): 21.5bn, week ended 2026-10-17 -- SBP reserves rise $19m to $21.5b - The Express Tribune
[03:58:59]   ✓ Import cover: 3.31 months  (reserves $21.5bn / $6500.0mn a month; Sep-26 (PBS via Topline, 2 Oct 2026))
[03:58:59]   → REER/CA/Fiscal sources: live headline > dated seed (manual file only if dated). Values now: ['reer', 'pak_ca', 'pak_fiscal']
[03:58:59]   [stage] fetch_psx_macros 17s
[03:58:59] === US screening ===
[03:58:59]   [diag] Wave O L1 TV-US coverage (n=800/800): price_earnings_ttm=94%(27.226759032184663) price_book_ratio=100%(33.27925338772231) price_sales_ratio=100%(24.450653984013933) enterprise_value_ebitda_ttm=72%(25.48952376220406) gross_margin=75%(74.6746366790002) operating_margin=99%(65.2142628453736) net_margin=99%(63.6629490145856) return_on_invested_capital=97%(102.387442503643) debt_to_equity=95%(0.16970618034447799) current_ratio=96%(4.58894906901602) price_target_average=83%(334.448911) recommendation_mark=83%(1.104167) recommendation_buy=83%(62) recommendation_total=83%(72) earnings_per_share_forecast_next_fq=96%(2.47252) earnings_per_share_fq=98%(2.223888)
[03:58:59]   [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried insider_ownership,held_by_insiders,shares_insiders,institutional_ownership,held_by_institutions); the 5% insider gate stays Yahoo-only -> the L1 cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call
[03:59:09]   [universe] band 2181 + large-scan 3624 + curated/foreign 241 -> engine universe 5974
[03:59:09]   [universe] adopted 326 sentinel-blind names into the screen (self-heal; memory 326 + new 1)
[03:59:09]   TV prefilter: 2181 band names scanned -> Yahoo screens 4626 (large-cap 241 + financials 215 + growth 343 + ttm-fallback 14); replaces a ~2422-name full-universe Yahoo screen; dropped 29 preferred/baby-bond series
[03:59:09]   D1 bank gate: 421 in-band financials -> dropped 150 (ROE<8%) + 56 (EPS<0) -> 215 to Yahoo (revenue gate bypassed for financials)
[03:59:09]   [diag] financials EPS-growth: 421 financials, 322 with data (fq 303, ttm 287); min -604400.0% median 13.4% max 9780.0%; pass >=0% 203 | >=5% 190 | >=10% 168 | >=15% 156
[03:59:09]   [diag] financials ROE: 421 financials, 348 with data; min -4186.3% median 9.6% max 140.8%; pass >=8% 198 | >=10% 170 | >=12% 123 | >=15% 61 | >=20% 32
[03:59:10]   L1 large-cap fundamentals: matched 377/567 named large-caps (TV)
[03:59:10]   L1 symbol pass: asked TradingView for 190 missing names by symbol -> 127 found
[03:59:10]   Building screen from TV fundamentals (4563 recs) + TV second pass for gaps (v1.491.0: no Yahoo)...
[03:59:10]   L1 large-cap fundamentals: matched 0/64 named large-caps (TV)
[03:59:10]   [US screen] TV gap pass: 64 names -> 0 filled, 64 unavailable on TV (no Yahoo)
[03:59:10]   US scan (L1 TV-first): 0s, 678 candidates — 678 TV-sourced + 0 TV-gap-pass (of 64 gaps; 64 unavailable); insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)
[03:59:10]   Fetching income_stmt EPS for 14 survivors missing earningsGrowth...
[03:59:11]   [SEC] CIK map loaded: 10430 tickers (data.sec.gov reachable)
[03:59:14]     [SEC EPS] filled 6/14 from SEC EDGAR; 8 -> FMP/Yahoo fallback
[03:59:14]     [FMP EPS] FMP_API_KEY not set — using Yahoo income_stmt only
[03:59:14]   EPS enriched 6/14 previously-None survivors (SEC 6, FMP 0, TV batch 0; Yahoo retired v1.491.0)
[03:59:14]   [stage] screen_us 16s
[03:59:14]   [Multibagger US] pool 85 profitable small-caps (ROIC>0); 0 SEC CFO/CPAT pulls -> 20 with 3-yr cash data; 14 gate-passing; top CFO/CPAT=2.848
[03:59:19]   [Foundation Universe] TradingView america scan: 1881 US-listed names >= $2bn (seamless with the $300M-$2bn small-cap band -> continuous coverage); added top 150 accelerating large/mid-caps to Explosive pool (200 -> 350)
[03:59:19]   [M2 keystone] universe pre-score over 1881/1881 Foundation names -> 976 disciplined (>=50) / 905 speculative (<50); top score 100.0; giants list 130 gate-passing sector leaders below the top-250 cut
[03:59:19]   [Estimate clock] day 96: 623 names tracked; 156 revision signals live (30d + 90d acceleration)
[03:59:20]   [sector medians] 19 sectors -> sector_medians.json (19 with 200-DMA breadth; e.g. Electronic Technology PE~34.964/ROE~0.1795/1M~-5.73%/tgt~41.82%, Technology Services PE~24.2655/ROE~0.1634/1M~8.29%/tgt~24.42%, Retail Trade PE~21.0149/ROE~0.1998/1M~5.18%/tgt~16.95%)
[03:59:20]   [PSX sector breadth] 14 sectors >=5 names (e.g. Producer Manufacturing 36.0%, Process Industries 34.5%, Consumer Non-Durables 34.2%)
[03:59:23]   [PSX sector medians] 14 sectors (e.g. Process Industries PE~7.8989/ROE~0.0732/1M~-1.19%/tgt~56.96%, Finance PE~5.7326/ROE~0.1607/1M~3.66%/tgt~42.41%, Consumer Non-Durables PE~11.7583/ROE~0.1465/1M~-4.82%/tgt~None%)
[03:59:23]   [PSX Sector Booming] 14 sectors scored: Neutral=1 | Lagging=8 | Avoid=5
[03:59:23]   [Wave PK-D] devaluation: ELEVATED (score 3/13) -> rupee_slope=0, reserves_fall=0, reer_stretch=2, sbp_rate=1, ca_stress=0, pkr_wow=0, kerb_premium=0, gold_premium=0
[03:59:23] === PSX screening ===
[03:59:23] Fetching PSX universe...
[03:59:25]   · PSX endpoint returned 404
[03:59:25]   [F5 watchlist] 8 loaded ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; in top-500 scan -> force-include: ['MTL', 'POL', 'THCCL', 'DOL', 'CLOV', 'AHL', 'PAKT', 'HALEON']; absent from scan (skipped): []
[03:59:25]   ✓ PSX universe: 49 candidates from TradingView Pakistan scanner
[03:59:25]   ✓ GAL: price=525.45 (tv_scan)
[03:59:25]   ✓ PRL: price=94.16 (tv_scan)
[03:59:25]   ✓ TPL: price=23.88 (tv_scan)
[03:59:25]   ✓ GHNI: price=1167.28 (tv_scan)
[03:59:25]   ✓ NRL: price=554.85 (tv_scan)
[03:59:25]   ✓ TPLP: price=12.44 (tv_scan)
[03:59:25]   ✓ MACFL: price=51.77 (tv_scan)
[03:59:25]   ✓ NCPL: price=50.09 (tv_scan)
[03:59:25]   ✓ TPLT: price=43.58 (tv_scan)
[03:59:25]   ✓ TRG: price=53.62 (tv_scan)
[03:59:25]   ✓ AIRLINK: price=115.96 (tv_scan)
[03:59:25]   ✓ TREET: price=23.7 (tv_scan)
[03:59:25]   ✓ NPL: price=53.31 (tv_scan)
[03:59:25]   ✓ NRSL: price=32.56 (tv_scan)
[03:59:25]   ✓ CSAP: price=78.67 (tv_scan)
[03:59:25]   ✓ DNCC: price=25.98 (tv_scan)
[03:59:25]   ✓ PAEL: price=32.82 (tv_scan)
[03:59:25]   ✓ LOTCHEM: price=24.13 (tv_scan)
[03:59:25]   ✓ SLGL: price=15.01 (tv_scan)
[03:59:25]   ✓ SEARL: price=74.92 (tv_scan)
[03:59:25]   ✓ CTM: price=7.34 (tv_scan)
[03:59:25]   ✓ MUREB: price=895.94 (tv_scan)
[03:59:25]   ✓ GCIL: price=32.96 (tv_scan)
[03:59:25]   ✓ FCL: price=23.23 (tv_scan)
[03:59:25]   ✓ NML: price=121.13 (tv_scan)
[03:59:25]   ✓ OGDC: price=303.68 (tv_scan)
[03:59:25]   ✓ PPL: price=215.08 (tv_scan)
[03:59:25]   ✓ MCB: price=389.32 (tv_scan)
[03:59:25]   ✓ FFC: price=549.1 (tv_scan)
[03:59:25]   ✓ HUBC: price=193.18 (tv_scan)
[03:59:25]   ✓ MTL: price=282.99 (tv_scan)
[03:59:25]   ✓ POL: price=660.59 (tv_scan)
[03:59:25]   ✓ THCCL: price=69.18 (tv_scan)
[03:59:25]   ✓ DOL: price=30.42 (tv_scan)
[03:59:25]   ✓ CLOV: price=5.43 (tv_scan)
[03:59:25]   ✓ AHL: price=104.9 (tv_scan)
[03:59:25]   ✓ PAKT: price=1478.4 (tv_scan)
[03:59:25]   ✓ HALEON: price=658.64 (tv_scan)
[03:59:25]   ✓ UBL: price=410.36 (tv_scan)
[03:59:25]   ✓ MEBL: price=523.76 (tv_scan)
[03:59:25]   ✓ HBL: price=287.66 (tv_scan)
[03:59:25]   ✓ NBP: price=164.97 (tv_scan)
[03:59:25]   ✓ ABL: price=170.11 (tv_scan)
[03:59:25]   ✓ BAFL: price=57.88 (tv_scan)
[03:59:25]   ✓ BAHL: price=151.95 (tv_scan)
[03:59:25]   ✓ AKBL: price=108.91 (tv_scan)
[03:59:25]   ✓ FABL: price=91.19 (tv_scan)
[03:59:25]   ✓ BOP: price=28.65 (tv_scan)
[03:59:25]   ✓ BIPL: price=23.44 (tv_scan)
[03:59:25]   PSX scan done: 49 candidates
[03:59:27]   [Wave PSX-DPS] skip (HTTP 404) -> TV path unaffected
[03:59:27]   [Wave PSX-DPS] dps.psx refused -> 485 symbols from the TradingView Pakistan scan
[03:59:27]   [Wave PSX-PX] PSX price PRIMARY = dps.psx official close (49 names), TV fallback (0); fundamentals stay TradingView
[03:59:27]   [Wave Q snapshot] skipped (<24h since 2026-10-29T01:55:32.982850) — carrying last-good (13 banks)
[03:59:27]   [Wave Q sector] KPMG skipped (696h < 720h, newest edition) — carrying last-good
[03:59:27]   [Wave Q->IG2] SCS fallback overrides written for 12 bank(s): ['ABL', 'AKBL', 'BAFL', 'BAHL', 'BIPL', 'BOP', 'FABL', 'HBL', 'MCB', 'MEBL', 'NBP', 'UBL'] (im3_score fills these into missing roe/adr/roa-trend only)
[03:59:28]   [US-bank IG2] COF CERT 4297: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.4% ADR~80.9% CAR 15.184590431395431
[03:59:29]   [US-bank IG2] CCNE CERT 13876: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~9.7% ADR~83.2% CAR 13.585867849370054
[03:59:30]   [US-bank IG2] MCBS CERT 58181: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~15.5% ADR~113.8% CAR 19.927096960197737
[03:59:30]   [US-bank IG2] ISTR CERT 58316: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~8.6% ADR~89.4% CAR 12.92431526011692
[03:59:31]   [US-bank IG2] OSBC CERT 3603: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~13.7% ADR~81.3% CAR 13.82027793691253
[03:59:31]   [US-bank IG2] COFS CERT 1014: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~11.3% ADR~68.2% CAR 12.66748151792934
[03:59:32]   [US-bank IG2] PLBC CERT 23275: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~16.3% ADR~72.7% CAR 18.450058001627507
[03:59:33]   [US-bank IG2] CARE CERT 58596: 6 annual yr(s) [2019, 2020, 2021, 2022, 2023, 2024] -> FY24 ROE~7.2% ADR~85.4% CAR 11.983002042230364
[03:59:33]   [US-bank IG2] merged 8 US bank(s) into bank_ig2_overrides.json: ['CARE', 'CCNE', 'COF', 'COFS', 'ISTR', 'MCBS', 'OSBC', 'PLBC'] (im3_score v2.17.0+ scores these via score_bank_us — CAMELS scorecard, 21 ratios; pre-v2.17.0 falls back to score_bank_ig2 calib=us)
[03:59:33]   [Wave P FMR] fetch skipped (0d ago, <7d) — carrying last-good fund-ownership + flows
[03:59:33]   [Wave PSX-R valmatrix] fetch skipped (0d ago, <7d) — carrying last-good
[03:59:34]   [PSX-TV valuation] 391 PSX names; columns ok=['price_earnings_ttm', 'price_book_ratio', 'return_on_equity', 'dividends_yield', 'market_cap_basic', 'enterprise_value_ebitda_ttm', 'price_sales_ratio', 'earnings_per_share_basic_ttm', 'debt_to_equity'] rejected=[]; matrix names found 154/162; fill%={'pe': 75.3, 'pb': 86.4, 'roe': 84.6, 'div_yield': 61.7, 'mkt_cap': 88.3, 'ev_ebitda': 50.6, 'ps': 85.8, 'eps_ttm': 86.4, 'de': 81.5}
[03:59:34]   [PSX-TV valuation] overlaid on 154 matrix names; value lists re-ranked live
[03:59:34]   [Wave PSX-R valmatrix] broker file frozen at July 2, 2026 but replaced by the live TradingView feed -- no warning
[03:59:34]   [Wave PSX-R MTS] LIVE ajax: Rs 13,136.8mn as of 2026-10-27 (+MFS/FOI)
[03:59:35]   [BR kerb] kerb 278.66 vs interbank 276.46 -> premium +0.80%% (ajax/last_kerb_rates)
[03:59:36]   [BR flows] fipi rows 10 | lipi rows 11
[03:59:37]   [BR kibor] headline 11.16% -> defensive_mode=True (7 tenors)
[03:59:37]   [BR fx] official USD buy None / sell 276.22
[03:59:38]   [BR bullion] intl leg unavailable from Business Recorder -- gold premium retired as a metric (v1.492.0); local leg live
[03:59:38]   [BR bullion] local 364,914 PKR vs intl None USD -> premium None%
[03:59:38]   [Wave P breadth] adv=258 dec=184 unch=43 (top-485 mcap); vol leader=PASL; val leader=FFC
[03:59:39]   US TCE pool: 15 screen + 19 ETF-consensus + 11 whale new-position = 45  [Wave O injection: APLD, CBRS, AAL, AGX, ARES, AROC, BA, BIDU, BRKR, CIFR, CME]
[03:59:40]   US analyst overlay: matched 209/223 TCE-pool tickers (TV FactSet)
[03:59:40]   [TCE US] TradingView growth inputs filled for 31 pool names
[03:59:41]   ⚠ [FINRA short interest] file 2026-09-30 is 29 days old -- s8 is on stale short interest
[03:59:41]   [TCE US] FINRA short interest {'tried': ['2026-10-15:403', '2026-09-30:200'], 'file': '2026-09-30', 'names': 45, 'parse': {'delim': '|', 'header': ['accountingyearmonthnumber', 'symbolcode', 'issuename', 'issuerservicesgroupexchangecode', 'marketclasscode', 'currentshortpositionquantity', 'previousshortpositionquantity', 'stocksplitflag', 'averagedailyvolumequantity', 'daystocoverquantity', 'revisionflag', 'changepercent', 'changepreviousnumber', 'settlementdate'], 'cols': [1, 5, 9, 13]}, 'float_names': 44, 'pct_names': 44, 'asked': 45, 'age_days': 29, 'stale': True}
[03:59:41]   [TCE US] short-interest nowcast (shadow) for 44 names, would flip ['ARES']
[03:59:41]   [TCE US] FINRA short-volume share for 45 names (top-third cut-off 0.5270189531000627)
[03:59:42]   [TCE US] Yahoo residual (last resort): asked 24, answered 19, added 6 (ok)
[03:59:43]   [TCE US] revision bridge for 31 of 45 names (FMP http {}, Finnhub http {})
[03:59:43] === TCE on US (45 candidates) ===
[03:59:44]   TCE batch history: 45/45 names pre-fetched in one call (us)
[03:59:45]   [news diag us] SRZN -> google=9, bing=1
[03:59:56]   SHAZ: WATCH total=5 conv=3 streams=['s1_news', 's5_volume', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   HBNC: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   SRZN: WATCH total=7 conv=4 streams=['s1_news', 's3_insider', 's5_volume', 's6_momentum', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   RGNX: WATCH total=4 conv=3 streams=['s3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside']
[03:59:56]   MU: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   VMET: WATCH total=5 conv=3 streams=['s1_news', 's5_volume', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:59:56]   OGG: WATCH total=4 conv=3 streams=['s1_news', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   EOSE: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside']
[03:59:56]   ARQQ: IGNORE total=2 conv=1 streams=['s3_insider', 's8_capital']
[03:59:56]   XFOR: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   ASPI: WATCH total=4 conv=3 streams=['s3_insider', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   RHLD: IGNORE total=1 conv=1 streams=['s8_capital']
[03:59:56]   FUBO: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   GORO: WATCH total=4 conv=3 streams=['s5_volume', 's6_momentum', 's11_target_upside', 's12_recommendation']
[03:59:56]   BRUN: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   NVDA: HIGH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   AAPL: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[03:59:56]   INTC: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's9_eps_rev', 's9_eps_revision', 's11_target_upside']
[03:59:56]   MSFT: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's12_recommendation']
[03:59:56]   AMD: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[03:59:56]   TXN: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[03:59:56]   AVGO: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   LRCX: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   CSCO: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's10_rev_rev', 's11_target_upside']
[03:59:56]   XOM: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's9_eps_rev', 's9_eps_revision']
[03:59:56]   GOOGL: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   QCOM: IGNORE total=3 conv=1 streams=['s1_news', 's3_insider', 's9_eps_rev']
[03:59:56]   AMAT: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   MRVL: HIGH total=7 conv=5 streams=['s1_news', 's3_insider', 's6_momentum', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   CVX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's9_eps_revision']
[03:59:56]   ANET: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   ADI: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's12_recommendation']
[03:59:56]   KLAC: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's9_eps_rev', 's11_target_upside']
[03:59:56]   META: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   APLD: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   CBRS: WATCH total=6 conv=4 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside', 's12_recommendation']
[03:59:56]   AAL: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's8_capital', 's11_target_upside']
[03:59:56]   AGX: WATCH total=5 conv=3 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev', 's11_target_upside']
[03:59:56]   ARES: IGNORE total=3 conv=1 streams=['s1_news', 's3_insider', 's11_target_upside']
[03:59:56]   AROC: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[03:59:56]   BA: WATCH total=5 conv=2 streams=['s1_news', 's3_insider', 's5_volume', 's7_margin', 's11_target_upside']
[03:59:56]   BIDU: IGNORE total=2 conv=0 streams=['s1_news', 's3_insider']
[03:59:56]   BRKR: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's8_capital', 's9_eps_rev']
[03:59:56]   CIFR: WATCH total=6 conv=3 streams=['s1_news', 's3_insider', 's5_volume', 's8_capital', 's11_target_upside', 's12_recommendation']
[03:59:56]   CME: IGNORE total=4 conv=2 streams=['s1_news', 's3_insider', 's7_margin', 's9_eps_rev']
[03:59:56]   TCE: 3 HIGH, 29 WATCH out of 45 scanned
[03:59:56]   [stage] run_tce_us 13s
[03:59:56] === TCE on PSX (49 candidates) ===
[03:59:57]   TCE batch history: 48/49 names pre-fetched in one call (psx)
[03:59:57]   [news diag psx] GAL -> google_pk=11, brecorder=3
[04:00:05]   GAL: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   PRL: HIGH total=5 conv=3 streams=['s1_news', 's5_volume', 's6_momentum', 's11_target_upside', 's12_recommendation']
[04:00:05]   TPL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   GHNI: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   NRL: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[04:00:05]   TPLP: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   MACFL: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's7_margin']
[04:00:05]   NCPL: IGNORE total=2 conv=1 streams=['s1_news', 's11_target_upside']
[04:00:05]   TPLT: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's6_momentum', 's7_margin']
[04:00:05]   TRG: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   AIRLINK: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   TREET: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   NPL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   NRSL: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's7_margin']
[04:00:05]   CSAP: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   DNCC: IGNORE total=3 conv=1 streams=['s1_news', 's5_volume', 's6_momentum']
[04:00:05]   PAEL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   LOTCHEM: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   SLGL: IGNORE total=2 conv=0 streams=['s1_news', 's5_volume']
[04:00:05]   SEARL: IGNORE total=0 conv=0 streams=[]
[04:00:05]   CTM: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   MUREB: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   GCIL: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   FCL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   NML: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   OGDC: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   PPL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   MCB: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   FFC: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   HUBC: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   MTL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   POL: WATCH total=4 conv=2 streams=['s1_news', 's5_volume', 's7_margin', 's11_target_upside']
[04:00:05]   THCCL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   DOL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   CLOV: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   AHL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   PAKT: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   HALEON: IGNORE total=1 conv=1 streams=['s7_margin']
[04:00:05]   UBL: IGNORE total=2 conv=1 streams=['s1_news', 's11_target_upside']
[04:00:05]   MEBL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   HBL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   NBP: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   ABL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   BAFL: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   BAHL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   AKBL: WATCH total=3 conv=2 streams=['s1_news', 's11_target_upside', 's12_recommendation']
[04:00:05]   FABL: WATCH total=4 conv=3 streams=['s1_news', 's7_margin', 's11_target_upside', 's12_recommendation']
[04:00:05]   BOP: IGNORE total=2 conv=1 streams=['s1_news', 's7_margin']
[04:00:05]   BIPL: IGNORE total=1 conv=0 streams=['s1_news']
[04:00:05]   TCE: 1 HIGH, 15 WATCH out of 49 scanned
[04:00:05]   [stage] run_tce_psx 9s
[04:00:06] TCE predictions: 771 logged, 426 open (re-priced 140/231 off-pool); HIGH matured=38 hit=0.0 alpha=-8.4 lift=0.0; WATCH matured=131 hit=0.023; IGNORE matured=176 hit=0.045
[04:00:06] === EXPLOSIVE screen on US (350 candidates) ===
[04:00:06]   SHAZ: A=None B=None -> NOT EXPLOSIVE
[04:00:06]   HBNC: A=None B=None -> NOT EXPLOSIVE
[04:00:06]   SRZN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   RGNX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:07]   MU: A=True B=True -> EXPLOSIVE — both signals
[04:00:07]   VMET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:07]   OGG: A=False B=False -> NOT EXPLOSIVE
[04:00:07]   EOSE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   ARQQ: A=False B=False -> NOT EXPLOSIVE
[04:00:07]   XFOR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   ASPI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   RHLD: A=False B=False -> NOT EXPLOSIVE
[04:00:07]   FUBO: A=False B=False -> NOT EXPLOSIVE
[04:00:07]   GORO: A=False B=False -> TURNAROUND — quarterly inflection (3Q profit rising)
[04:00:07]   BRUN: A=None B=None -> NOT EXPLOSIVE
[04:00:07]   SATL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:07]   OABI: A=False B=False -> TURNAROUND — quarterly inflection (8Q profit rising)
[04:00:07]   EDIT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:07]   HYLN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   PRLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:07]   SGML: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   UNIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   URGN: A=False B=False -> TURNAROUND — quarterly inflection (2Q profit rising)
[04:00:07]   TXO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:07]   PCT: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   CEPU: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   ELE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   EQBK: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   CRMD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   TRX: A=True B=True -> EXPLOSIVE — both signals
[04:00:08]   RMIX: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   XTND: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   LAES: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   LZM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   AKTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   BW: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   INR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   EVC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   AMPX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   CMCO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   FOIL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   ACTG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   VOXR: A=True B=True -> EXPLOSIVE — both signals
[04:00:08]   SNDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   ABTC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   FBYD: A=False B=False -> NOT EXPLOSIVE
[04:00:08]   SENS: A=False B=False -> NOT EXPLOSIVE
[04:00:08]   AUTL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   SPRY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   CDNL: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   PFLT: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   POET: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   STAA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   PSEC: A=None B=None -> NOT EXPLOSIVE
[04:00:08]   NVDA: A=True B=True -> EXPLOSIVE — both signals
[04:00:08]   NRGV: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:08]   MTC: A=False B=False -> NOT EXPLOSIVE
[04:00:08]   AVEX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:08]   ETON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   IMTX: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   REPX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   WRD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   DCH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   SNDX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   AMBQ: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   DJT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   ATLC: A=None B=None -> TURNAROUND — quarterly inflection (2Q profit rising)
[04:00:09]   TE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   PHAT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   PICS: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   HAWK: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   AEBI: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   AVGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   FENC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   CHMG: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   ALOY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]     [EXPL SEC-diag] HSHP: rev_g=None op_g=3560.2 np_g=1006.3 | Total=[2025:1.32e+08,2024:0] Operating=[2025:6.82e+07,2024:-1.97e+06] Net=[2025:1.77e+07,2024:-1.95e+06]
[04:00:09]   HSHP: A=None B=False -> TURNAROUND — quarterly inflection (2Q profit rising)
[04:00:09]   FRD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   GROY: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   KDP: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:09]   USAS: A=False B=False -> TURNAROUND — quarterly inflection (3Q profit rising)
[04:00:09]   LPTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   DMLP: A=False B=False -> TURNAROUND — quarterly inflection (2Q profit rising)
[04:00:09]   DVN: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   WVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   TRC: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   RYZ: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   FTK: A=True B=True -> EXPLOSIVE — both signals
[04:00:09]   AAPG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   FEIM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   GNK: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   EBS: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   HIVE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   ROCK: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   MNR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   MCFT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   SVM: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   AVR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   TK: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:09]   ASC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   STX: A=False B=False -> TURNAROUND — quarterly inflection (10Q profit rising)
[04:00:09]   SRTA: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   CION: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   KMTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   COUR: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   WYFI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   OMC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   EOG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   INOD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   NAT: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   CARL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   DELL: A=False B=False -> TURNAROUND — quarterly inflection (8Q profit rising)
[04:00:09]   FIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   OKE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   LCID: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   SI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   WDC: A=True B=True -> EXPLOSIVE — both signals
[04:00:09]   LVWR: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   MAMA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   MAKO: A=True B=True -> EXPLOSIVE — both signals
[04:00:09]   KOS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   AII: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   BWMX: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   LRCX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   TEN: A=False B=False -> TURNAROUND — quarterly inflection
[04:00:09]   GAU: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   FDUS: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   NU: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   HLIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   ZVRA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   MPC: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   ASML: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   RUN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   CBNA: A=None B=None -> NOT EXPLOSIVE
[04:00:09]   CRON: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   LYTS: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   FANG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   CVX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   KOPN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   WKC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   AMD: A=True B=True -> EXPLOSIVE — both signals
[04:00:09]   BKSY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   MELI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   PPHC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   CRESY: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   SHIP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   AGRO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:09]   ASTH: A=False B=False -> TURNAROUND — quarterly inflection (2Q profit rising)
[04:00:09]   SCZM: A=False B=False -> NOT EXPLOSIVE
[04:00:09]   PAYS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   SE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   SD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:09]   MFA: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   MFAO: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   LLY: A=True B=True -> EXPLOSIVE — both signals
[04:00:10]   AADX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:10]   SHLS: A=False B=False -> NOT EXPLOSIVE
[04:00:10]   EVH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   GLP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   PSX: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:10]   AIP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   TWFG: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:10]   SOUN: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:10]   DDL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   VLO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   CARE: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:10]   INTR: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   KALU: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:10]   FMNB: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   BBDC: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   SHEL: A=None B=None -> NOT EXPLOSIVE
[04:00:10]   OMDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:10]   XOM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   MNKD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   MBUU: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:10]   QNST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   NBBK: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   OFRM: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   BFC: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   ECVT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   MRAM: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   HBT: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   TRIN: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   ISTR: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:11]   TSM: A=None B=None -> TURNAROUND — quarterly inflection (10Q profit rising)
[04:00:11]   GEL: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   RJET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   RERE: A=True B=True -> EXPLOSIVE — both signals
[04:00:11]   ASM: A=True B=True -> EXPLOSIVE — both signals
[04:00:11]   EGY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   SSII: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   ASMB: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   TH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   GFR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   YB: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   WELL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   AQST: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   ATEX: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   IVR: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   ANET: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   JOBY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   NRIX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   PTGX: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   IDYA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   ASTS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   BMNR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   BMNP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   LQDA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   ONDS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   CRSP: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   CGON: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   GLXY: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   FLY: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   KYMR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   NBIS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   ALM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   AGNC: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   SNDK: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   IOVA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   VRDN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   MRNA: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   HHH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   ECO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   APLD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   DNTH: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   INSM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   LUNR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   IONQ: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   SPCX: A=None B=None -> NOT EXPLOSIVE
[04:00:11]   RYN: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   STLA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   SM: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   LIFE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:11]   CDNA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:11]   SKHY: A=True B=True -> EXPLOSIVE — both signals
[04:00:11]   GRAL: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   TXG: A=False B=False -> NOT EXPLOSIVE
[04:00:11]   TGB: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   ARX: A=None B=None -> NOT EXPLOSIVE
[04:00:12]   TWST: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   AYA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   TEAM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   AXTI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   NTSK: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   HNGE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   INSW: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   RGTI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   SUN: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   AMLX: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   HTFL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   RBRK: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   WAT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   DHT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   CAI: A=None B=None -> NOT EXPLOSIVE
[04:00:12]   OKTA: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   EQX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   ARWR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   FRO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   PENG: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   PLTR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   HNI: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   GTLB: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   APPN: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   VIA: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   ALAB: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   BE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   HALO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   GMAB: A=None B=None -> NOT EXPLOSIVE
[04:00:12]   FPS: A=True B=True -> EXPLOSIVE — both signals
[04:00:12]   QLYS: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   P: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:12]   TRMD: A=None B=None -> NOT EXPLOSIVE
[04:00:12]   DNOW: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   PNFP: A=None B=None -> NOT EXPLOSIVE
[04:00:12]   KOD: A=None B=None -> INSUFFICIENT DATA
[04:00:12]   NTRA: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   VNOM: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   RGLD: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:12]   SNOW: A=False B=False -> NOT EXPLOSIVE
[04:00:12]   CRWD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:12]   ASND: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   SFNC: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   WBI: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   LITE: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   SMCI: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   CVI: A=False B=True -> INFLECTION (accelerating off low base — verify)
[04:00:13]   SAN: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:13]   SITM: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   ABCL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   GH: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   SIMO: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   IBRX: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   BBIO: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   TENB: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   TGTX: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   NSIT: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   BRZE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   ESTC: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   PANW: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   KLIC: A=False B=False -> NOT EXPLOSIVE
[04:00:13]     [EXPL SEC-diag] PLSE: rev_g=None op_g=-36.8 np_g=-35.8 | Total=[2025:3.5e+05,2024:0,2023:0,2022:7e+05,2021:1.42e+06] Operating=[2025:-7.69e+07,2024:-5.63e+07,2023:-4.36e+07,2022:-5.81e+07,2021:-6.3e+07,2020:-4.99e+07,2019:-4.7e+07,2018:-3.75e+07,2017:-2.56e+07,2016:-9.52e+06] Net=[2025:-7.28e+07,2024:-5.36e+07,2023:-4.22e+07,2022:-5.85e+07,2021:-6.37e+07,2020:-4.99e+07,2019:-4.7e+07,2018:-3.75e+07,2017:-2.56e+07,2016:-9.52e+06]
[04:00:13]   PLSE: A=None B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   COMP: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   KNSA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   CDE: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   CRDO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   HPE: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   OSCR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   ZETA: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   SQM: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   FROG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   ZS: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   MWH: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   TBBB: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   XMTR: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   ELF: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   DX: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   ATRC: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   PBF: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   NTAP: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   TPG: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   VIST: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   DINO: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   CMBT: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   HTGC: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   MP: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   ILMN: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   DDOG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   CRL: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   PAYC: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   CHRD: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   PTCT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   ADPT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   AUGO: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:13]   ERO: A=True B=True -> EXPLOSIVE — both signals
[04:00:13]   TNK: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   FIGS: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   LMND: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   VEEV: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   BLLN: A=None B=None -> NOT EXPLOSIVE
[04:00:13]   FTNT: A=False B=False -> NOT EXPLOSIVE
[04:00:13]   STNG: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:13]   TARS: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:14]   VEON: A=None B=None -> NOT EXPLOSIVE
[04:00:14]   RNG: A=False B=False -> NOT EXPLOSIVE
[04:00:14]   AVAH: A=True B=True -> EXPLOSIVE — both signals
[04:00:14]   RDN: A=False B=False -> NOT EXPLOSIVE
[04:00:14]   AUR: A=False B=False -> NOT EXPLOSIVE — OP declining
[04:00:14]   MRVL: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:14]   ARQT: A=True B=False -> QUALITY-GROWTH (growth, not accelerating)
[04:00:14]   SAIL: A=None B=None -> NOT EXPLOSIVE
[04:00:14]   [Explosive cache] 318 hit / 2 fetched (income_stmt cached 45d, persisted in data.json)
[04:00:14]   [Explosive src] 2 SEC-EDGAR / 0 Yahoo-fallback of 2 fetched; 0 verdict flip(s) vs last-good
[04:00:14]   [Explosive profile] stockanalysis fetches 8 (0.9s), SEC fetches 32 (7.0s), empty retries 8
[04:00:14]   EXPLOSIVE: 20 both-signal of 350 scored; 3 financials -> bank model; 1 insufficient-data
[04:00:14]   [stage] explosive_us 8s
[04:00:14]   [Signal T] quarterly data on 180/350 US names; 108 turnaround hook(s) fired (stockanalysis primary + SEC fallback)
[04:00:14]     [Signal T fail] no_matching_row: 8 ticker(s), e.g. ['HBNC', 'SRZN', 'RGNX', 'VMET', 'OGG', 'XFOR', 'BRUN', 'EDIT']
[04:00:14] === EXPLOSIVE screen on PSX (49 candidates) ===
[04:00:14]   GAL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   PRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   TPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   GHNI: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   NRL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   TPLP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   MACFL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   NCPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   TPLT: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   TRG: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   AIRLINK: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   TREET: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   NPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   NRSL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   CSAP: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   DNCC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   PAEL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   LOTCHEM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   SLGL: A=None B=None -> INSUFFICIENT DATA
[04:00:14]   SEARL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   CTM: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   MUREB: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   GCIL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   FCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   NML: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   OGDC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   PPL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   MCB: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   FFC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   HUBC: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   MTL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   POL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   THCCL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   DOL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   CLOV: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   AHL: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   PAKT: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   HALEON: A=None B=None -> PARTIAL — profit/cash data pending (IM3)
[04:00:14]   UBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   MEBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   HBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   NBP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   ABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   BAFL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   BAHL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   AKBL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   FABL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   BOP: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   BIPL: A=None B=None -> FINANCIAL — score via bank model (IM3 System B)
[04:00:14]   EXPLOSIVE: 0 both-signal of 49 scored; 12 financials -> bank model; 1 insufficient-data
[04:00:14]   [COT] carried (fresh <72h) -- CFTC publishes weekly; next fetch when the stamp ages out
[04:00:19]   [recession] prefetched 6/6 series in parallel (gate 2 req/s)
[04:00:19]   ✓ Recession calendar: 9 high-impact US releases (faireconomy)
[04:00:19]   ✓ Recession watch: LOW (score 0) — 6 FRED signals, 9 calendar events
[04:00:22]   [Econ announced] 1 actuals computed from FRED
[04:00:22]   [Econ announced] 6 released events on record (14d window)
[04:00:36]   [stage] us_growth 14s
[04:00:36]   → Zacks scrape skipped (last scrape 0d ago, <7d) — carrying forward last-good
[04:00:37]   [TE lei] Euro-area -> value not matched on page
[04:00:37]   [TE lei] Switzerland -> value not matched on page
[04:00:39]   [TE lei proxy] Euro-area = 97.9 (ESI (EC survey) proxy — OECD CLI discontinued)
[04:00:40]   [TE lei proxy] Switzerland = 109.1 (KOF Economic Barometer proxy — OECD CLI discontinued)
[04:00:40]   [TE lei] rescued from TradingEconomics (OECD CLI): Australia=99.95, Brazil=102.36, Canada=101.92, China=97.41, Euro-area=97.9, Germany=101.01, India=102.0, Japan=100.35, South Korea=102.53, Switzerland=109.1, UK=101.38, USA=101.0
[04:00:40]   [World LEI] TradingEconomics (PRIMARY): 12/12 countries
[04:00:40]   [World LEI] FRED skipped entirely -- TradingEconomics covered all 12
[04:00:40]   [Compass] recession_prob 0.62% wired through from data['recession'] -> the 16th indicator can finally be scored
[04:00:40]   [US Diffusion] net=+5  8/16 supportive  regime=Expansion  policy=hawkish  infl=re-accelerating
[04:00:40]   [Econ clock] US=REFLATION  PSX=STAGFLATION
[04:00:52]   [Country RS] Dollar direction: Neutral (DXY above200=True, currencies losing to USD: 3/12)
[04:00:52]   [Country RS] 13/9 countries ranked
[04:00:52]   [stage] country_rs 12s
[04:00:52]   [Bottom-up sectors] 11 sectors from 1881 stocks (mkt-median 7.2%, winner-cut 35.9%); Energy=100(Booming) | Health Care=73.9(Booming) | Information Technology=63.2(Favoured) | Industrials=48.4(Neutral)
[04:00:52]   [Sector Booming] 11 sectors scored: Avoid=1 | Booming=2 | Favoured=5 | Lagging=1 | Neutral=2
[04:00:52]   [Sector Selection] PSX zone=RED | US quadrant=REFLATION | triggers fired: B
[04:00:52]   [PSX narrative] RED | 5 lines
[04:00:52]   [Sector Booming delta] 11 sectors trended (rising=0 falling=0 flat=11)
[04:00:52]   [Global Theme] 4 themes scored: Developed-West=65.2(Favoured) | Commodity-Bloc=51.7(Neutral) | Asia-Tech=48.9(Neutral) | Emerging=19.9(Avoid)
[04:00:52]   [ETF recs gate] 2/5 macro-confirmed (dollar=Neutral, diffusion=Expansion)
[04:00:52]   [ETF Recommendations] 5 resolved: global_theme:Developed-West->UBS MSCI Switzerland 20/35 UCI, global_theme:Developed-West->iShares Core S&P 500 UCITS ETF, country:China->iShares MSCI China A UCITS ETF, sector:Energy->Xtrackers MSCI World Energy UC, sector:Industrials->State Street SPDR MSCI Europe 
[04:00:52]   [Bottom-up sectors] 11 sectors from 1881 stocks (mkt-median 7.2%, winner-cut 35.9%); Energy=100(Booming=TD✓) | Health Care=73.9(Booming=TD✓) | Information Technology=63.2(Favoured=TD✓) | Industrials=48.4(Neutral)
[04:00:53]   [ETF discovery] 60 genuine UCITS ETFs discovered live (kept 200 pre-dedup, dropped 283 leveraged/ETP + 26 below $50M floor; kept aum range $52M..$7.7bn); top: iShares MSCI UK UCITS ET 10178.1%, Ark Genomic Revolution U 96.3%, WisdomTree Cybersecurity 94.0%, iShares MSCI Global Semi 81.2%, Global X Cybersecurity U 81.2%
[04:00:53]   [ETF watch] 1 fund(s) flagged perf_suspect (implausible return rejected)
[04:00:53]     · [diag] iShares IE00BG0J4C88 pid=297843: HTTP 200 len 2257668 -> 0 holdings
[04:00:54]     · [diag] iShares IE00BG0J4841 pid=305642: HTTP 200 len 2266960 -> 0 holdings
[04:00:54]   [discovery holdings] 15 reuse (xlsx/watchlist) + 28 cache + 9 fetched (0 iShares + 9 justETF) / 60 discovery funds; 8 still —
[04:00:54]     · still —: Invesco Energy S&P US Select Sector UC [IE00B435CG94]; Global X Genomics & Biotechnology UCIT [IE00BM8R0N95]; FAM Series UCITS ICAV - Fineco AM MSCI [IE000C87OS21]; Market Access Rogers International Com [LU0249326488]; WisdomTree Enhanced Commodity UCITS ET [IE00BYMLZY74]; Invesco Bloomberg Commodity Carbon Til [IE000CYTPBT0]; iShares Diversified Commodity Swap UCI [DE000A0H0728]; Easy Energy & Metals Enhanced Roll -UC [LU1291109616]
[04:01:05]   [ETF live prices] 113 fund(s) priced via isin-filter resolver (recs + hydrogen + emerging-themes + metals + momentum watch) -- now incl. live YTD/1Y (v1.141.0)
[04:01:05]   [MA probe] ETFs 110/114 with SMA200, 113/114 with SMA50 (confirms TV 50/200-DMA coverage for the ETF live-price lists before the index MA columns are wired)
[04:01:05]     · [diag] sa-page CIBR: HTTP 200 len 99144
[04:01:05]     · [diag] sa-page CIBR: parsed 24 holdings
[04:01:06]   [Emerging holdings] verified-allowlist filled 4/4 funds (collision-safe; rest need justETF/issuer)
[04:01:06]     · [diag] iShares IE000X59ZHE2 pid=338777: HTTP 200 len 1594381 -> 0 holdings
[04:01:06]     · [diag] iShares IE00BG0J4C88 pid=297843: HTTP 200 len 2257668 -> 0 holdings
[04:01:06]     · [diag] iShares IE00BG0J4841 pid=305642: HTTP 200 len 2266960 -> 0 holdings
[04:01:06]     · [diag] iShares IE000C6ITGC8 pid=345953: HTTP 200 len 1169311 -> 0 holdings
[04:01:07]     · [diag] iShares IE000A9G9R73 pid=351117: HTTP 200 len 1398424 -> 0 holdings
[04:01:07]   [Emerging holdings] iShares issuer-file filled 0/5 funds (BlackRock authoritative CSV by ISIN)
[04:01:07]   [Emerging holdings] theme-fund real-name fill: 2 reuse + 19 cache + 0 justETF-fetched / 21 targeted
[04:01:07]   [Hydrogen notes] recomputed live: weakest=L&G Hydrogen Economy, smallest-AUM=49m
[04:01:08]   [ETF Results tracker] 20 pick(s) tracked vs ACWI ($122.86) -- 10/20 positive, 8/20 beating ACWI where alpha is computable
[04:01:08]   [Stock->UCITS bridge] 153 pick(s) matched to a UCITS proxy (US+PSX TCE HIGH+WATCH, US+PSX Explosive positive-verdict)
[04:01:08]   [Recommended->ETF trackers] priced 14/14 distinct UCITS proxy ETF(s); enriched ucits_proxy (ISIN+YTD+1Y) on 153 pick(s); explosive=8 group(s) / 20 name(s), tce=11 group(s) / 48 name(s)
[04:01:13]   [IBKR Flex] synced 11 positions (10 matched), cash ['AED', 'GBP', 'USD'], NAV 235907.085799459 @ 2026-10-28; changes: ['NEW GOO3 40.0']
[04:01:13]   [Live FX] GBPUSD 1.3300 (live) | EURUSD 1.1100 (live) | AED pegged 0.2723
[04:01:18]   [NetBenefits] APD 832.0 sh @ 307.20 (tv) -> MV 255590
[04:01:18]   [Statements] weekly 17 (16 complete) | monthly 4 (3 complete); from 113-day history since 2026-07-06
[04:01:18]   [Live Investment] NAV $235,725 (cost $255,184); P&L since inception -11.48% ($-29,287); 11 holdings 11 live/0 reuse-fallback/0 pending; day(IBKR-style) $+3,288; forward-covered 2 underlyings
[04:01:18]   [MA probe] holdings 11/11 with SMA200, 11/11 with SMA50 (TV serves 50/200-DMA for UCITS lines? -- confirms before the index MA columns are wired); e.g. SMH px=105.24 50=107.1516 200=95.4118, ITWN px=199.88 50=204.5971 200=175.3128, KSTR px=19.608 50=23.3413 200=24.1031
[04:01:18]   [stage] live_investment 10s
[04:01:19]     · [diag] iShares IE000X59ZHE2 pid=338777: HTTP 200 len 1594381 -> 0 holdings
[04:01:20]     · [diag] iShares IE000DR59CI3 pid=335844: HTTP 200 len 1575964 -> 0 holdings
[04:01:22]   US analyst overlay: matched 8/8 TCE-pool tickers (TV FactSet)
[04:01:24]   [look-through] news prefetched: 32 queries in parallel
[04:01:24]   [Live Lookthrough] 11 fund(s); holdings 4 ok/6 miss; rated 31/36; eps 31; trend 32; news 20; markets america 8/8, taiwan 7/7, china 7/7, korea 9/9
[04:01:24]     · [probe] SMH   NVIDIA Corp            w=11.3% america  NVDA           rating=Strong Buy  tgt=334     eps_nq=2.47
[04:01:24]     · [probe] SMH   Micron Technology      w=11.0% america  MU             rating=Strong Buy  tgt=1632    eps_nq=38.23
[04:01:24]     · [probe] SMH   AMD                    w=10.7% america  AMD            rating=Strong Buy  tgt=659     eps_nq=1.95
[04:01:24]     · [probe] SMH   Taiwan Semiconductor M w=10.4% taiwan   TWSE:2330      rating=Strong Buy  tgt=3412    eps_nq=33.00
[04:01:24]     · [probe] SMH   Broadcom Inc           w=10.2% america  AVGO           rating=Strong Buy  tgt=532     eps_nq=3.83
[04:01:24]     · [probe] SMH   Intel Corp             w=6.0%  america  INTC           rating=Buy         tgt=120     eps_nq=0.41
[04:01:24]     · [probe] SMH   Lam Research           w=5.1%  america  LRCX           rating=Strong Buy  tgt=368     eps_nq=2.35
[04:01:24]     · [probe] SMH   Applied Materials, Inc w=5.1%  america  AMAT           rating=Strong Buy  tgt=652     eps_nq=4.06
[04:01:24]     · [probe] SMH   Texas Instruments      w=3.3%  america  TXN            rating=Buy         tgt=339     eps_nq=2.62
[04:01:24]     · [probe] ITWN  Taiwan Semiconductor M w=31.1% taiwan   TWSE:2330      rating=Strong Buy  tgt=3412    eps_nq=33.00
[04:01:24]     · [probe] ITWN  MediaTek, Inc          w=7.9%  taiwan   TWSE:2454      rating=Strong Buy  tgt=6076    eps_nq=16.03
[04:01:24]     · [probe] ITWN  Delta Electronics, Inc w=5.0%  taiwan   TWSE:2308      rating=Strong Buy  tgt=2475    eps_nq=12.16
[04:01:24]     · [probe] ITWN  Hon Hai Precision Indu w=4.3%  taiwan   TWSE:2317      rating=Strong Buy  tgt=360     eps_nq=4.96
[04:01:24]     · [probe] ITWN  Elite Material Co., Lt w=2.2%  taiwan   TWSE:2383      rating=Strong Buy  tgt=8400    eps_nq=38.00
[04:01:24]     · [probe] ITWN  United Microelectronic w=2.0%  taiwan   TWSE:2303      rating=Strong Buy  tgt=150     eps_nq=1.39
[04:01:24]     · [probe] ITWN  Unimicron Technology C w=1.9%  taiwan   TWSE:3037      rating=Strong Buy  tgt=1460    eps_nq=6.63
[04:01:24]     · [probe] ITWN  Nan Ya Plastics Corp   w=1.6%  unresolved —              rating=—           tgt=—       eps_nq=—
[04:01:24]     · [probe] KSTR  Cambricon Technologies w=8.9%  china    SSE:688256     rating=Strong Buy  tgt=1615    eps_nq=2.77
[04:01:24]     · [probe] KSTR  Advanced Micro Fabrica w=8.7%  china    SSE:688012     rating=Strong Buy  tgt=445     eps_nq=0.97
[04:01:24]     · [probe] KSTR  Hygon Information Tech w=7.5%  china    SSE:688041     rating=Strong Buy  tgt=360     eps_nq=0.51
[04:01:24]     · [probe] KSTR  Montage Technology     w=7.5%  china    SSE:688008     rating=Strong Buy  tgt=323     eps_nq=0.90
[04:01:24]     · [probe] KSTR  Yuanjie Semicon Tech   w=5.6%  unresolved —              rating=—           tgt=—       eps_nq=—
[04:01:24]     · [probe] KSTR  Piotech                w=4.9%  china    SSE:688072     rating=Strong Buy  tgt=944     eps_nq=1.39
[04:01:24]     · [probe] KSTR  Hua Hong Grace         w=3.8%  unresolved —              rating=—           tgt=—       eps_nq=—
[04:01:24]     · [probe] KSTR  Hwatsing Technology    w=3.8%  china    SSE:688120     rating=Strong Buy  tgt=306     eps_nq=1.10
[04:01:24]     · [probe] KSTR  Skyverse Technology    w=3.3%  unresolved —              rating=—           tgt=—       eps_nq=—
[04:01:24]     · [probe] KSTR  Biwin Storage Technolo w=3.3%  china    SSE:688525     rating=—           tgt=—       eps_nq=—
[04:01:24]     · [probe] FLXK  Samsung Electronics Co w=25.9% korea    KRX:005930     rating=Strong Buy  tgt=490446  eps_nq=15034.12
[04:01:24]     · [probe] FLXK  SK hynix, Inc          w=16.7% korea    KRX:000660     rating=Strong Buy  tgt=3253393 eps_nq=110195.03
[04:01:24]     · [probe] FLXK  SK Square Co. Ltd      w=3.7%  korea    KRX:402340     rating=Strong Buy  tgt=1855000 eps_nq=84663.23
[04:01:24]     · [probe] FLXK  Samsung Electro-Mechan w=2.9%  korea    KRX:009150     rating=Strong Buy  tgt=2448800 eps_nq=8338.17
[04:01:24]     · [probe] FLXK  KB Financial Group, In w=2.2%  korea    KRX:105560     rating=Strong Buy  tgt=216043  eps_nq=4905.23
[04:01:24]     · [probe] FLXK  Hyundai Motor Co       w=2.2%  korea    KRX:005380     rating=Strong Buy  tgt=586226  eps_nq=8192.87
[04:01:24]     · [probe] FLXK  Shinhan Financial Grou w=1.8%  korea    KRX:055550     rating=Strong Buy  tgt=130759  eps_nq=1470.94
[04:01:24]     · [probe] FLXK  Doosan Enerbility Co., w=1.5%  korea    KRX:034020     rating=Strong Buy  tgt=126167  eps_nq=126.29
[04:01:24]     · [probe] FLXK  HANWHA AEROSPACE Co.,  w=1.4%  korea    KRX:012450     rating=Strong Buy  tgt=1576364 eps_nq=10737.34
[04:01:24]   [stage] live_lookthrough 6s
[04:01:24]   → ETF holdings overlap skipped (last attempt 4d ago, <7d; 25 consensus stocks) — carrying forward last-good
[04:01:24]   [Wave Z v2] consensus: 0 double-confirmed name(s) (0 funds x 57 whale-held tickers)
[04:01:24]   Carried forward 281 last-good IM3 score(s) onto rebuilt records
[04:01:24]   [IM3 guard] 3 score(s) dropped for >10% price-basis drift (corporate action) -> re-score: AMD, APLD, MU
[04:01:24]   Marked 1 stale-version IM3 score(s) (ver != 2.36.0) -> re-score/Pending
[04:01:24]   [ETF-X verified] 6 strict top-scorers -> 2 ETF(s) with VERIFIED holdings (0 fetched); tickers LLY, NVDA
[04:01:24]   [Zacks radar] carried 45 pink-tier IM3 grade(s) forward
[04:01:24]   [Zacks radar] price-joined 51 pink proxy(ies) from already-priced ISINs
[04:01:24]   [Zacks radar] 72 Strong-Buy name(s) off the main board -> 51 pink foundation-data rows + 21 screened rows lifted; 11 already on the board; 0 near-miss chip(s)
[04:01:24]   [Momentum] RSI×MA: us 29 cross / 45 scanned, psx 27/48, metals 1 cross; 200-DMA slope: live (day 60, needs 3+)
[04:01:24]   [Wave T history] 2026-10-29: 122 day(s) stored (kse100=165736.76, usd/pkr=276.46, diffusion_net=5, lei_exp=9, sector_top=Energy 82.4)
[04:01:24]   [Wave T trends] 141 field(s) in trend table, 122 with a live move (kse100=up, usd_pkr=down, sp500=up, gold_px=up)
[04:01:24]   [M1 override] Information Technology JOINS the pool (3/3 gates): 6M 5.548772032280363% vs mkt 0.9% | EPSg 29.7% vs mkt 16.1% | Zacks-heat 25.9% -- off-regime, same cash-conversion gate
[04:01:24]   [M1 referee] Sector Booming PROMOTED ['Consumer Staples', 'Health Care'] into the pool (band=Favoured)
[04:01:24]   [M1 referee] Step-2 sectors refereed by Sector Booming: Energy(regime,Booming#1), Industrials(regime,Booming#2), Information Technology(override,Favoured#3), Consumer Staples(scoreboard,Favoured#4), Financials(regime,Favoured#5), Materials(regime,Favoured#6), Health Care(scoreboard,Favoured#7), Consumer Discretionary(regime,Neutral#8)
[04:01:24]   [M1 discovery lane] 6 A-grade Zacks discovery(ies) join the pool: ['BKR', 'ADP', 'C', 'CRM', 'GOOGL', 'ISRG']
[04:01:24]   [M1 buylist] regime=REFLATION pool=153 fresh-scored=0 deep-scored=153 cash-chain(CFO/NP>=0.9)=105 pass + banks 14/14 | fail=25 no-cash-history=9 -> buys=8: ['MU', 'ISRG', 'LRCX', 'FOXA', 'ROST', 'VLO', 'COP', 'C']
[04:01:24]   [PSX topdown] E&P cash-unverified lane: ['POL'] join the buys (grade+trigger; no cash feed)
[04:01:24]   [PSX topdown] regime=DEFENSIVE (high-rate) +E&P-overweight favored=0 scored=47 cash-chain(CFO/PAT>=0.9)=2 pass + banks 10/12 | fail=2 no-data=30 -> buys=0: []
[04:01:24]   [M2 watch] scanned=630 turnaround-lane flagged=64 (evidence families >=2, own signal set) + quality-lane flagged=94 | shown 20+25 | calibration CRDO=FAIL GEV=PASS | 9-stock panel 4/9 (flagged or M1 buys) | top turnarounds: ['DT', 'BWIN', 'TALO', 'SMMT', 'SEI', 'NCLH', 'AXTI', 'TENB']
[04:01:24]   [M2 Signal T] 4/64 turnaround names carry a fired hook (native fetch: 7/62 had quarterly data)
[04:01:24]   [M2 watch] WARNING: D-127 calibration failed -- gates need review
[04:01:24]   [PSX M2 watch] scanned=49 turnaround flagged=10 (evidence families >=2, same process as US) | shown 10 | F1 sustained-uptrend(>=25%% vs 200DMA) legs=4 | top: ['PRL', 'TPLT', 'DNCC', 'NRL', 'POL', 'OGDC', 'GAL', 'GCIL']
[04:01:25]   [Wave ETF-M] M1 tracker 5 ETF(s)/8 names | M2 turnaround 10 ETF(s)/64 | M2 quality 11 ETF(s)/94 | 34/34 ISINs priced | GICS themes 7: ['Information Technology', 'Health Care', 'Financials', 'Consumer Discretionary', 'Industrials', 'Utilities', 'Energy']
[04:01:25]   [PB] paper book: us 8 names/5.0% cash, psx 0 names/None% cash; track day 107 (us nav 104.2262 vs spy 102.23, psx None vs kse 90.94)
[04:01:31]   [Narratives] skipped 7 feed(s) with 3+ consecutive empties: ai_infra:bloomberg, ai_infra:reuters, marketbeat_ratings, pakistan:bloomberg, pakistan:reuters, psx_brokers:bloomberg (retry on run %20)
[04:01:31]   [Narratives] 116 headlines across 13/13 themes; universe 478 names; top: Tariffs & Trade Policy
[04:01:31]   [stage] narratives 6s
[04:01:31]   [E&P trigger] Arab Light proxy $108.23 vs $60.0 -> FIRED (overweight E&P) (Brent $110.23)
[04:01:31]   [Metals drivers] real yield 2.61% | Gold -21.2 LEAN BEARISH | Silver +18.2 LEAN BULLISH | Copper +33.3 BULLISH | Platinum +19.0 LEAN BULLISH | Palladium +27.8 LEAN BULLISH
[04:01:31]   [Narratives] theme badge stamped on 163 record(s) across 8 pools (138 distinct tickers in live themes)
[04:01:32]   [Catalyst] earnings dates matched 409/443 pool tickers (TV)
[04:01:32]   [Catalyst] 409 names dated; 136 inside the 10-day window WITH a live signal
[04:01:32]   [Tab10] OP/NP blank reason stamped on 106 row(s)
[04:01:32]   [Whale 13F] SKIPPED -- 13F is quarterly; cached parse is 6d old, 29d past quarter-end (filing window is day 40-80). 15 whales, 3 crowded name(s) carried forward.
[04:01:32]   [Crowdedness] stamped onto M1 buy list: 0 crowded of 8 buys
[04:01:32]   [SEC filings] carried (fresh <20h; crawl skipped)
[04:01:32]   [Wave SEC] Multibagger insider-gate repaired: 4 names insider-tilted
[04:01:32]   [Wave SEC] Explosive: 10 names carry insider-buying confirmation
[04:01:32]   [Wave SEC] sentinel: 0 adverse-8K flag(s), 4 heavy-insider-selling flag(s) on held names
[04:01:32]   [Wave T shortlist] 1106 stock-rows tracked (262 live, 1106 conviction-stamped [1106 at true entry]) across 9 tabs; 41 sector baskets
[04:01:34]   [countryeconomy us] debt/GDP=124.38% (2025, flat) · Moody's Aa1 (Stable, 2025-05-16, flat)
[04:01:35]   [countryeconomy pakistan] debt/GDP=72.77% (2025, flat) · Moody's Caa1 (Stable, 2025-08-13, flat)
[04:01:38]   [Recommended tab] 24 engine-scored stocks + 5 thematic + 8 ETFs; top: ['C(4)', 'VLO(4)', 'ROST(3)', 'ISRG(3)', 'NVDA(3)']
[04:01:40]   [World stocks] filtered 2095 raw -> 1338 non-US -> 1026 unique companies
[04:01:40]   [World stocks] 1026 names across 13 region(s); fundamentals on 1011/1026
[04:01:41]   [Factor fund-lines] priced 4/4 funds
[04:01:41]   [Policy catalyst] 6 catalysts / 28 ticker-links / 4 categories
[04:01:42]   [policy px] prices+returns stamped: 38 from the US screen universe, 18 via per-symbol quotes
[04:01:42]   [Global discovery] status=live universe=1026 fund-cov=1011 picks=361
[04:01:43]     · [moat-set] moat: 25 holding rows parsed
[04:01:43]     · [moat-set] motg: 25 holding rows parsed
[04:01:45]   [Quarterly accel] backfill: 31 targets, 12 fetched, 19 cached, 12 no-history (forward-only); accelerating=10
[04:01:45]   [Quarterly accel] TIGHT full=26 nearmiss=199 moat=0 extra_scan=590 alarms=4
[04:01:45]   [universe sentinel] 1 holdings-visible names absent from engines: ['BRK.B']
[04:01:45]   [AMC FMR] fetch skipped (<7d) -- carrying last-good (2026-10-27)
[04:01:45]   [FMR probe] carried (probed 6d ago, weekly)
[04:01:45]   [Timing gaps] 5.6s after bank_snapshot, 5.0s after psx_market, 3.4s after sector_medians, 3.1s after recession
[04:01:45]   [Timing] total 182.9s  |  slowest: tail_builders 21.0s, fetch_psx_macros 16.6s, screen_us 15.5s, us_growth 13.9s, run_tce_us 12.7s, country_rs 12.5s
[04:01:45] [Estate flag] stamped 172 rows; [Canon ETF] normalised 161 rows (ytd_pct + n_holdings)
[04:01:45] [Recommended] 70 stocks (>=2 engines) + 12 ETFs consolidated
[04:01:45]   [entry timing] universe extended by 74 M1/M2/TCE/Explosive names (total 144)
[04:01:50]   [candle] stamped 144 rows with the confirmation-candle read
[04:01:50]   [trend playbook] BOTTOMING / BOTTOM RULES=68, BROKEN / TREND BROKEN - STAND ASIDE=38, TRENDING / TREND - WAIT FOR DIP=19, TRENDING / IN DIP ZONE - WAIT FOR REVERSAL=6, TRENDING / STRETCHED - DON'T CHASE=6, TRENDING / BREAKOUT BUY=5 | ATR for 144 names
[04:01:50]   [recommended] re-arbitrated on this run: 18 demoted
[04:01:50]   [entry timing] 144/144 names scored; verdicts {'WAIT': 73, 'NO DATA': 6, 'BUY': 27, 'HOLD OFF': 5, 'WAIT FOR DIP': 8, 'AVOID': 25}; charts 51
[04:01:50]   [stage] post.entry_timing 5s
[04:01:51]   [Bottoms] TradingView daily bars: 11 of 11 names (socket probe True)
[04:01:51]   [Exit rules] 19 positions: 7 EXIT, 0 TRIM
[04:01:51]   [sector positions] stamped 54 recommended/M1 rows from the keystone lookup
[04:01:52]   [market pulse] HEALTHY (ob 4% / os 9% / <200d 35%)
[04:01:52]   [Wave Z] rank-1: 10 ETFs ['XLK', 'XLE', 'XLV', 'XLI', 'XLB', 'DIA'] / 13 MFs ['FSPTX', 'FSELX', 'FBGRX', 'FDGRX'] | common holdings (>=2 funds): 24
[04:01:52]   [MOAT cover] carried (fresh <5d, all 11 deep ETFs present)
[04:01:52]   [Trend Ladder] ma_lines store: 636 tickers, 0 fetched this run (budget 80, 5d TTL)
[04:01:52]   [Trend Ladder] 213 rows stamped (display-only; foundation lines)
[04:01:55]   [Trend Ladder] +6 metals, +11 holdings classified (proven symbol GET)
[04:01:55]   [ETF index] 3831 stocks across 42 ETFs
[04:01:55]   [ETF index] annotated discovery rows
[04:01:56]   [MOAT] 317 names | 238 live-tracked (US) | 16 with engine grade | leaders top ret 84%
[04:01:56]   [Trend Ladder] moat re-stamp after rebuild: 234 rows (zero-fetch)
[04:01:56]   [TipRanks] overlay: 45 cached, 0 freshly fetched (top-25 recommended US)
[04:01:56]   [rebalance v2] late pass: 3 instructions; KSTR wait, TSM3 trim, AMD3 trim
[04:01:56]   [audit layer] acquired_fix=ok, benchmarks=ok, market_regime=ok, regime_gate=ok, regime_trend_reconcile=ok, cot_full=ok, discovery=ok, squeeze=ok, rs_momentum=ok, reconciliation=ok, vol_sizing=ok, signal_ledger=ok, account_relative=ok, leveraged_exposure=ok, content_age=ok, dual_values=ok, reference_fixes=ok, exit_rsi_fill=ok, watchlist_hygiene=ok, threshold_sensitivity=ok, results_summary=ok
[04:02:07]   [evidence layer] px_ctx=ok, ledger_hygiene=ok, psx_regime_fix=ok, gate_m1=ok, gate_explosive=ok, gate_zacks=ok, gate_m2=ok, gate_tce=ok, entry_timing_playbook=ok, bottoms_knife=ok, gate_psx=ok, gate_recommended=ok, gate_whale_discovery_etf=ok, m1_score_v2=ok, us_regime_sectors=ok, bottom_watch=ok, shadow_lanes=ok, ledger_attrs=ok, tce_snapshot=ok, tce_scorecard_verdict=ok, psx_tracker_fields=ok, pb_costs_and_bands=ok, exit_arbiter=ok, master_signal=ok, results_v2=ok
[04:02:07]   [stage] post.evidence_layer 11s
[04:02:08]   [side-state] split to side files: ['explosive_stmt_cache.json', 'sigt_quarterly_cache.json', 'justetf_cache.json', 'signal_ledger.json', 'bottom_watch_bars.json', 'px_ctx.json', 'ma_lines.json', 'fwd_eps_hist.json', 'estimate_history.json', 'world_stocks.json', 'foundation_cache.json (full) + slim inline']
[04:02:09]   [TV bars] us: 1326 symbols -> 442 bars; served ['close', 'high', 'low', 'open', 'volume']
[04:02:09]   [TV bars] psx: 49 symbols -> 49 bars; served ['close', 'high', 'low', 'open', 'volume']
[04:02:09]   [trading-rules] scope=trading | 6 blocks | bars 514 | graded 658 | VETOED 45 | patterns 12 | 3x 4 | risk 0
[04:02:14]   [Bottoms] TradingView daily bars: 202 of 202 names (socket probe True)
[04:02:44]   [Bottoms] 202 names, 202 with bars, 69 hourly; states {'CONFIRMED': 45, 'WATCHING': 77, 'NONE': 59, 'BROKEN': 13, 'AVOID': 8}; ADD gated none
[04:02:44]   [stage] bottoms 35s
[04:02:47]   [governor] TCE-HIGH=SUSPENDED (w=0.0, verdict FAIL) | ETF lapsed 5 | availability {'UNAVAILABLE': 6, 'DEGRADED': 1} | record drift 0
[04:02:48]   [size governor] 9.31 MB (saved -11 KB; im3_detail expired 0, aging orphans 0; growth vs prev 9 KB)
[04:02:48]   [serialize] data.json text built in 0.6s
[04:02:48]   [size sentinel] shipped ~7.36 MB after the workflow im3_detail split (9.18 MB as exported) -- under the 9.0 MB ceiling
[04:02:48] data.json written (9181946 bytes) -- 52.3s since the post-export phase began (bottoms, governors and serialising included; the file write itself is the last second or two)
[04:02:48] ============================================================
[04:02:48] Scanner completed
[04:02:48]   Hard errors: 0
[04:02:48]   Warnings (degraded data): 3
[04:02:48]       - [TV econ ok] universe=global serving core_pce, cpi_yoy, fed_rate, ppi_core_yoy, unemployment
[04:02:48]       - [TV econ ok] universe=global serving cpi_yoy
[04:02:48]       - [FINRA short interest] file 2026-09-30 is 29 days old -- s8 is on stale short interest
[04:02:48]   US macros: 133
[04:02:48]   PSX macros: 46
[04:02:48]   KSE-100: 165736.76 (tradingview:KSE100 (official close), as of 2026-10-29)
[04:02:48]   WTI/Brent: 101.43 / 110.23 (tradingview:CL1! (continuous, symbol GET), as of 2026-10-29)
[04:02:48]   US candidates: 15
[04:02:48]   PSX candidates: 49
[04:02:48]   US TCE HIGH: 3
[04:02:48]   PSX TCE HIGH: 1
[04:02:48]   Recession: LOW (score 0, 9 cal events)
[04:02:48] ============================================================
