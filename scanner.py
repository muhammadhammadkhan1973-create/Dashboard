"""
PSX + US Active Macro Dashboard - Data Scanner v1.10.0
======================================================
Runs daily via GitHub Actions, scans US and PSX universes, runs TCE convergence,
fetches macro data, writes data.json for the HTML dashboard.

v1.10.0 adds:
- Full IM3 162-point scoring engine: score_im3()
  * Replicates every formula from IM3_0 Scoring Template Excel exactly
  * System A (Standard): 40 metrics, 162 pts — all non-bank stocks
  * System B (Bank): same template, 6 inventory/coverage metrics replaced
    with bank-specific ratios (NIM, ROE, CASA, ADR, NPL, CAR) → 162 pts
  * Bank detection via yfinance sector/industry fields
  * 7 intrinsic value methods: DCF EPS, DCF FCF, DCF Cash, Projected FCF,
    Projected Cash, Peter Lynch Value, Graham Value
  * Altman Z, Beneish M, Piotroski F — all computed from yfinance data
  * GOOD=100%, WATCH=60%, BAD=20% point conversion per weightage file
  * Runs as post-screen layer on explosive_us records only
  * im3 dict added to each explosive_us record

v1.9.0 adds:
- Tab 12 Gold & Metals data: fetch_metals()
  * Metal spot prices GC=F, SI=F, PL=F, PA=F from Yahoo Finance
  * DXY Dollar Index DX-Y.NYB from Yahoo Finance
  * Fed balance sheet WALCL from FRED (QE/QT signal)
  * COT non-commercial net positions from CFTC CMX page (Gold/Silver/Copper)
  * News RSS scoring for IMF Pakistan, Pakistan Default, GeoPolitical (feedparser)
  * All stored under data['macros']['metals']

v1.8.0 fixes:
- Baker Hughes timeout 30s → 5s, silent fallback
- PSX explosive: embedded FY2024 annual growth data
- IM3-correct explosive metrics using Operating Profit / Net Profit

v1.7.1 fixes: FMP enrichment moved to post-screen stage
"""

import os
import sys
import json
import math
import time
import csv
import re
import traceback
import datetime as dt
from io import StringIO
from pathlib import Path

import requests
import pandas as pd
import numpy as np

try:
    import tce_psx_analyst                 # D2: PSX analyst-conviction streams (TV FactSet columns)
    _TCE_PSX_IMPORT_ERR = None
except Exception as _e:                     # capture (don't swallow) — surfaced loudly at PSX TCE time
    tce_psx_analyst = None
    _TCE_PSX_IMPORT_ERR = repr(_e)

# =============================================================
# CONFIG
# =============================================================
FRED_KEY = os.environ.get('FRED_API_KEY', '')
FMP_KEY  = os.environ.get('FMP_API_KEY', '')
OUTPUT_PATH  = Path(__file__).parent / 'data.json'
SCAN_VERSION = '1.140.0'  # 1.140.0: (ETF perf-column probe fix — same-ISIN multi-listing bug) the v1.139.0 probe run confirmed Perf.YTD/Perf.Y/Perf.3Y are real, populated columns (5/5 funds), but a cross-check against known YTD values caught Franklin FTSE Korea resolving to LSE:FLRK -- a DIFFERENT listing than LSE:FLXK, the one resolve_etf_live_price() already prices with in production. Root cause: the v1.139.0 probe only inspected rows[0] (unsorted) from TradingView's isin-filter response; a single ISIN can legitimately carry multiple LSE/AQUIS/currency listings (documented since v1.130.0's uk/scan USD+GBX variants), and rows[0] has no guaranteed order. FLRK's ISIN match was technically correct -- it just wasn't the SAME listing production already trusts. FIX: probe now inspects EVERY row sharing the queried ISIN, logs each listing (symbol/currency/exchange/perf values) so a multi-listing situation is fully visible rather than silently picking one, and applies the SAME _ETF_CCY_PREF/_ETF_EXCH_PREF preference sort resolve_etf_live_price() already uses in production -- so the "PRODUCTION PICK" logged is guaranteed to be the exact listing the dashboard would actually display, making the perf-value cross-check against known YTD meaningful for the first time. Still fully isolated from the production columns list (an unknown TV column 400s the whole POST, so this can never risk live pricing). ETF_PERF_PROBE stays True for one more run. No data/screening/scoring/IM3/TCE change; respects the Sept freeze. NEXT: read the corrected [ETF perf-column probe] block -- if Korea's PRODUCTION PICK now shows LSE:FLXK with a plausible YTD (a few points below the 31-May 119.93% snapshot, consistent with a month of live drift, not a different fund), lock Perf.YTD/Perf.Y into resolve_etf_live_price's production columns and flip ETF_PERF_PROBE False.  # 1.139.0: (ETF performance-column probe — owner-directed: fetch YTD/1Y live from TradingView, the same way the rest of the dashboard already sources return data) NEW probe_etf_performance_columns() (gated ETF_PERF_PROBE, PRE-ARMED True for ONE run) tests whether the SAME proven isin-filter scan endpoint already pricing all 76 Momentum-Watch + Engine Rec + Hydrogen + Metals funds live also exposes YTD/1-year performance columns (Perf.YTD/Perf.Y/Perf.3Y -- the natural extension of the Perf.W/Perf.1M/Perf.3M/Perf.6M naming convention already proven live on the US/PSX stock scans elsewhere in this file). Tests against 4 funds currently showing "—" for 1Y (Korea/Taiwan/Japan/Climate-Change categories) plus VanEck Semiconductor (a core Engine Recommendations catalog fund -- if this works it upgrades the whole catalog, not just Momentum-Watch). ISOLATED from resolve_etf_live_price's own production columns list on purpose -- an unknown TV column 400s the WHOLE POST, so this can never risk the live pricing already working every run. If the verdict confirms real, sane values, the NEXT rev locks the accepted column into production and replaces the static-file YTD/1Y for ALL 60 Momentum-Watch funds (not just the 12 currently sourced from specialty sheets) with a live, run-fresh number -- same mechanism, same trust level as everything else on this dashboard. Each POST independently guarded; never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [ETF perf-column probe] block, lock whichever column comes back real, then flip ETF_PERF_PROBE False.  # 1.138.0: (Momentum-Watch +5 Nasdaq-100, owner-requested exception) added the top 5 Nasdaq-100 UCITS ETFs (ranked by trailing 1-year return, matching the source "Top Nasdaq ETFs" sheet's own stated methodology) as ranks 56-60. All 18 real Nasdaq-100 funds in ETF_Universe_8.xlsx were checked first (18.74-20.19% YTD range, confirmed via a direct cross-check against both "Top Nasdaq ETFs" and the master "All Non-Lev Ranked" sheet -- same 18 ISINs, same values, zero discrepancy) -- none clear the table\'s stated 35% YTD cutoff, so these are an explicit, owner-requested exception for direct US mega-cap tech coverage, not an organic qualifier. Deliberately numbered 56-60 (past the natural 1-55 range) so they sort as their own final category block and never get silently blended into the ">=35%" claim the rest of the panel makes. Real TER/YTD/1Y/holdings from the source file, zero fabrication. Paired index.html change fixes the tier-badge logic (which would otherwise mislabel these as "35-40%") and updates the panel count/footnote to state the exception honestly. No screening/scoring/TCE change; freeze-safe; additive.  # 1.137.0: (World ETF Engine — tickers everywhere + trailing returns + Pakistan-proxy data, owner-directed multi-piece build) (A) TICKERS: Engine Recommendations already captured a real, live-resolved ticker (live_sym via resolve_etf_live_price) but displayed it as buried subtext -- that's a paired index.html display fix, no scanner change needed. Momentum-Watch (55 funds) NEVER went through live-price enrichment (deliberate v1.132.0 cost-tier decision) -- REVERSED this run: extended the enrichment loop to also cover etf_momentum_watch, since ticker and price are the same TradingView call (no cheaper way to get one without the other) and a live-verified ticker beats 55 more hardcoded strings to trust blindly, especially after the Hydrogen Watch fabrication episode this session. (B) TRAILING RETURNS: build_etf_recommendations() now attaches country_trailing (ret_3m/ret_6m/ret_12m, already computed by fetch_country_rs, zero new fetch) to every country-door and global_theme-door pick via a new _crs_by_country lookup. Sector-door and EM-ex-China picks have no country and correctly carry no country_trailing field -- honest, not fabricated; the paired index.html shows these as "sector-level pick, no country trailing return" rather than a guessed number. (C) PAKISTAN PROXY DATA: new data['etf_pakistan_proxy'] sourced from the existing _ETF_CATALOG['Equity Pakistan'] entry (zero new data) and added to the live-price enrichment loop -- for display on Tab 2 (Pakistan) and Tab 7 (Allocation Zone), a DIFFERENT placement from the Tab 16 Pakistan section removed earlier this session (that removal stands; this is additive elsewhere per a separate, later owner instruction). NOT YET BUILT this rev (correctly scoped, deliberately continuing in a focused follow-up rather than rushed): Results-tab live tracker vs ACWI (needs a new ACWI fetch + persistent entry-date/entry-price tracking, mirroring the append_history/shortlist_tracking pattern) and the Stock-UCITS equivalence bridge (needs a new 3-tier resolver + wiring across TCE/Explosive tabs). No screening/scoring/TCE change; freeze-safe; additive.  # 1.136.0: (Hydrogen Watch data-integrity fix -- full re-verification against a real, independent source for every field) audit triggered by the owner spotting a mismatch on the live tab. Root cause: the original v1.132.0 hydrogen data was built during a research pass whose web-search results were later lost to context compaction -- only the summary claims survived, not the evidence. Every field has now been re-derived from a direct fetch of each fund's own justETF page (not a search snippet, not memory): _HYDROGEN_WATCH ret_6m/ret_1y/size_m_eur were fabricated for all 4 funds (Global X 6M/1Y was 104.33%/314.84%, real is 22.15%/211.88% -- off ~5x and ~1.5x), and 3 of 4 holdings strings (L&G, Amundi, Global X) were an IDENTICAL copy-pasted placeholder ("Linde, Air Liquide, Plug Power, Nel, Ballard") rather than each fund\'s real distinct top holdings -- only VanEck had a distinct (if still imprecise) string. ISINs themselves were re-confirmed correct (the fabrication was in the detail fields, not fund identity) via justETF + issuer/exchange primary sources (VanEck.com, London Stock Exchange). Also spot-checked _ETF_CATALOG[\'Equity Semiconductors\'] (VanEck SMH, IE00BMC38736) against justETF+VanEck.com -- TER/AUM/ISIN all confirmed correct, holdings list (Nvidia/TSMC/ASML/Broadcom/AMD/Texas Instruments) stands as a safe claim given how dominant those names are in semiconductor market-cap weighting. Did NOT re-verify the broad country/sector _ETF_CATALOG entries (Japan/Korea/Materials/etc.) -- those came from reading actual ETF_Universe_8.xlsx cell values directly via pandas earlier in the same session (visible, uncompacted), a fundamentally lower-risk sourcing method than web-search-then-recall, and their repeated holdings text across funds in the same category is expected/correct since competing trackers on near-identical indices (e.g. MSCI Japan) genuinely hold near-identical top constituents. No screening/scoring/TCE change; freeze-safe; additive/corrective only.  # 1.135.0: (Copper added as a 5th first-class metal, matching Gold/Silver/Platinum/Palladium treatment) copper_px (HG=F) added to the generic yahoo_tickers fetch loop in fetch_metals() -- one line, inherits the FULL existing technicals pipeline for free (SMA50/SMA200/RSI14/ma_trend/ext_200_pct/cross/hist/wow/mom/qoq) via the same _metal_technicals()+_series_trend() code every other metal already uses, zero new plumbing. COT copper was already fetched every run (cot_copper_net/pct/pctile/wow/mom/qoq) for the Materials-sector proxy -- that data existed, just had no price to sit next to. _METALS_ETC_WATCH gains WisdomTree Copper (GB00B15KXQ89, LSE:COPA, TER 0.49%, confirmed real ISIN) -- honestly labelled Synthetic/swap-based, not Physical, since copper has no practical physical-vault ETC structure at retail scale the way precious metals do. Deliberately did NOT fabricate a METALS_SEASONAL.Copper monthly-return table -- searched for a real sourced dataset, found narrative confirmation (Barchart/EquityClock) but not the precise per-month decimals the other 4 metals' tables clearly came from, so the paired index.html change leaves copper's seasonal read as "not yet sourced" rather than inventing numbers. No screening/scoring/TCE change; freeze-safe; additive.  # 1.134.0: (Metals ETC Watch completed + wired to Tab 12 signals) _METALS_ETC_WATCH extended from 3 to 5 funds -- added iShares Physical Platinum ETC (IE00B4LHWP62, LSE:SPLT, TER 0.20%) and iShares Physical Palladium ETC (IE00B4556L06, LSE:SPDM, TER 0.20%), both confirmed real ISINs (justETF/LSE/BlackRock). Now covers all 4 metals the Metals tab (Tab 12) already tracks (Gold/Silver/Platinum/Palladium), not just Gold+Silver. Live-price enrichment loop (v1.132.0) already iterates data['etf_metals_etc_watch'] generically so the 2 new funds are priced automatically, no loop change needed. Paired index.html change wires each metal's ETC card to the SAME live technical signal (SMA200 trend/cross/RSI14/ext_200_pct) and, for Gold/Silver only, the SAME COT positioning (net/pct/pctile/WoW) that Tab 12 already computes in macros.metals -- one shared read of existing scanner output, zero new fetch, zero duplicated scoring logic. No screening/scoring/TCE change; freeze-safe; additive.  # 1.133.0: (Momentum-Watch data completeness) _MOMENTUM_WATCH rebuilt with 3 new fields per fund, all sourced directly from ETF_Universe_8.xlsx 'All Non-Lev Ranked' sheet (zero fabrication) -- ter (TER%), holdings (Major holdings indicative), ret_1y (1-year return, cross-referenced against 'Equity ETFs already ranked' sheet by ISIN -- only 7/55 funds carry real 1yr data in the source file, the rest correctly show None, never fabricated). Confirms none of the Franklin-branded funds (Korea/Taiwan/Asia-ex-China) hold US-listed companies -- their real holdings are Samsung/SK Hynix/Hyundai (Korea), TSMC/Hon Hai/MediaTek (Taiwan), TSMC/Samsung/Tencent/BHP (Asia-ex-China) -- Asian supply-chain names, not US semiconductor or IT stocks. No screening/scoring/TCE change; freeze-safe; additive.  # 1.132.0:  # 1.132.0: (World ETF Engine Tier1+2+3 all built together) _ETF_CATALOG +Equity Semiconductors (VanEck IE00BMC38736 EUR8074m) + Equity Emerging Markets ex China (3 funds). Momentum threshold 40->35% (34->55 funds renamed _MOMENTUM_WATCH). _HYDROGEN_WATCH: 4 funds confirmed ISINs (L&G IE00BMYDM794/Amundi FR0010930644/VanEck IE00BMDH1538/GlobalX IE0002RPS3K2). _METALS_ETC_WATCH: iShares Gold IE00B4ND3602/Invesco Gold IE00B579F325/iShares Silver IE00B4NCWG09. build_etf_recommendations: +semiconductor bonus pick for Asia-Tech + EM ex-China Door 4. data: etf_momentum_40->etf_momentum_watch + etf_hydrogen_watch + etf_metals_etc_watch. index v5.116: plain-English guide Tab16 section; Pakistan removed; double-confirmed explicit; Hydrogen+Metals sections added.  # 1.131.0:  # 1.131.0: (World ETF Engine Block 1+2) build_etf_recommendations expanded to multi-pick + Korea/Taiwan two-door rule: Door 1 now surfaces top 3 countries (not just top 1); Door 2 surfaces top 2 US sectors; Door 3 surfaces top 2 themes x top 2 countries per theme via _THEME_COUNTRY_ORDER — when Asia-Tech is Booming, BOTH Taiwan AND South Korea now resolve to their own UCITS ETFs (not just the top-1 country). _MOMENTUM_40 constant added: 34 non-leveraged ETFs up >=40% YTD from ETF_Universe_8.xlsx (owner-confirmed include 1 crypto product); wired into data['etf_momentum_40'] for display on the new World ETF tab. All data-only, additive, freeze-safe. index.html v5.115 (paired file): Tab 9 ETF content removed; new dedicated World ETF tab (Tab 16) added with three sections: Engine Recommendations, Momentum-40 Watchlist, Pakistan UCITS Proxy. No screening/scoring/TCE change.  # 1.130.0:  # 1.130.0: (World ETF Engine Phase 6 COMPLETE — production ISIN price resolver live) Phase 6c verdict locked: v1.129.0 run returned 12/12 confirmed ISIN-match(es) across 6 probe(s) — every ✓ flag fired. CONFIRMED: the isin field is a valid FILTER on the proven scanner.tradingview.com/{market}/scan endpoint. All 3 test ISINs found on BOTH uk and germany endpoints: IE00B5BMR087→LSE:CSPX($805.54)/XETR:SXR8(€704.98), IE00B53SZB19→LSE:CNDX($1731.20)/XETR:SXRV(€1515.40), LU0659579147→LSE:XBAK($1.823)/XETR:XBAK(€1.601). Key architectural facts locked: (a) uk/scan returns multiple listings per ISIN (USD + GBX pence variants on LSE and AQUIS); (b) germany/scan returns the EUR listing on XETR; (c) GBX = pence (1/100th of GBP) — must not be used as-is; (d) type='fund' confirmed on every row. TV_ISIN_FILTER_PROBE flipped False (verdict locked, probe kept in code). All 3 Phase 6 probes (ETF_FEED_PROBE, TV_ISIN_COLUMN_PROBE, TV_ISIN_FILTER_PROBE) are now retired, gated off, with their verdicts in code. NEW resolve_etf_live_price(isin): PRODUCTION resolver — tries uk/scan first (prefers USD over GBX, LSE over AQUIS), then germany/scan fallback (EUR); returns {sym,close,currency,exchange} or None; guarded/never raises/freeze-safe. Wired into main() immediately after build_etf_recommendations(): enriches each recommendation's fund dict with live_price/live_sym/live_ccy/live_exch; logs '[ETF live prices] N priced'. Phase 6 is now fully built and live — the dashboard's ETF recommendations carry real UCITS prices from the same proven TV scan endpoint that powers all other price data. Phase 7 (catalog refresh to 1,652 funds), Phase 8 (ranked-10 recs), Phase 9 (live tracker vs ACWI) follow in subsequent iterations. No screening/scoring/TCE change; freeze-safe; additive.  # 1.129.0: (World ETF Engine Phase 6c — isin as a FILTER on European scans, logging-only) Phase 6b verdict is CONFIRMED and locked: the v1.128.0 run returned isin populated on 8/8 rows via scanner.tradingview.com/america/scan, with all 5 cross-checked ISINs matching known real values (AAPL=US0378331005, NVDA=US67066G1040, MSFT=US5949181045, GOOGL=US02079K3059, AMZN=US0231351067). TV_ISIN_COLUMN_PROBE flipped False (verdict locked, probe kept for record). The natural follow-on question: since isin is a valid COLUMN, is it also a valid FILTER FIELD? If yes, a single POST to the right European market scan with filter=[{left:'isin', operation:'equal', right:'IE00B5BMR087'}] gives back the UCITS ETF's price + exchange in one hit -- no intermediate lookup step, the cleanest possible resolver path. NEW probe_tv_isin_filter() (gated TV_ISIN_FILTER_PROBE, PRE-ARMED True for ONE run): tests 3 representative UCITS ISINs (IE00B5BMR087/IE00B53SZB19/LU0659579147) × 2 European market endpoints (uk/germany -- LSE and XETRA, the two most common UCITS ETF listing venues) = 6 isolated throwaway POSTs. Logs HTTP status, row count, and per-row details (sym/close/ccy/exch/type/isin_returned) for any match, plus a ✓ flag when the returned isin matches the queried one. The three outcomes are distinct and decisive: (A) 200 with matching row → filter CONFIRMED, build the ISIN-resolver on the identified markets + discover which market codes cover the UCITS catalog; (B) 200/0-rows (not 400) → filter is accepted by TV but those UCITS ETFs are not indexed on uk/germany → try euronext/swiss/other markets in the next probe; (C) 400 → isin is display-only (not filterable) → need to do a broad scan requesting the isin column and match rows by value instead. Each POST independently guarded, wrapped in main, never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger → respects the Sept freeze. No data/scoring change this rev.  # 1.128.0: (World ETF Engine Phase 6b — pivot off a confirmed-dead endpoint, logging-only) the v1.127.1 diagnostic deepening did its job: TWO consecutive live runs (v1.127.0, v1.127.1) both came back with symbol-search.tradingview.com returning an IDENTICAL static nginx 403 Forbidden for ALL 12/12 sample ISINs -- no JS-challenge, no captcha, just a flat edge/IP-level deny (same failure class as the other datacenter-IP-blocked sources already documented in this project). Two identical full runs is conclusive; a third run of the same leg would add nothing. ETF_FEED_PROBE flipped False (verdict locked, kept in code for the record). Rather than guess at a workaround for a blocked endpoint (header tweaks, alternate UAs, etc. -- none of which fix a static IP-level deny), this pivots to a DIFFERENT, ALREADY-PROVEN endpoint: NEW probe_tv_isin_column() (gated TV_ISIN_COLUMN_PROBE, PRE-ARMED True for ONE run) does ONE isolated throwaway POST to scanner.tradingview.com/america/scan -- the exact request shape that has worked flawlessly on the runner every single run this whole project -- testing whether its column schema simply EXPOSES an 'isin' field. Requests columns=[name,isin,close,currency,exchange,description] over the 8 largest US stocks by market cap (so a human can eyeball whether AAPL's isin reads US0378331005, the known real value) via the SAME filter/sort/markets shape already proven safe. If isin parses as a valid, populated column, symbol+price can be resolved in ONE proven request per market with no separate (and blocked) search step at all -- collapsing what used to be a 2-step search-then-price chain into a single already-trusted POST. If TV rejects 'isin' as a column name (400) or returns it empty, the hypothesis is dead and the next increment pivots to issuer-page scraping (iShares/Xtrackers/Amundi product pages, the same plumbing class already proven for the PSX FMR fund-holdings overlay) instead. Each GET/POST guarded, the call wrapped in main -> touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [TV isin-column probe] block -- if isin is populated and real, lock the ISIN-filtered resolver + test which non-US TV market-scan codes actually carry these specific UCITS funds (a SEPARATE next increment, deliberately not guessed here); if empty/rejected, flip TV_ISIN_COLUMN_PROBE False and move to issuer-page scraping for Phase 6. No data/scoring change this rev.  # 1.127.1: (World ETF Engine Phase 6 — diagnostic deepening, logging-only) the live v1.127.0 runner result came back 0/12 price resolved + 0/12 holdings resolved -- every single sample ISIN logged a blank 'no-symbol' for the TradingView symbol-search leg, with zero detail behind it (the prior code collapsed a bad HTTP status, an empty 200 result list, and a 200-with-no-exchange/symbol-field result into the SAME blank tag). This is notable because scanner.tradingview.com (america/scan, pakistan/scan, the symbol-POST primitive that prices KSE100/RUT) worked perfectly throughout the SAME run -- only symbol-search.tradingview.com/symbol_search/, a different subdomain this probe introduced for the first time, failed uniformly across 12 unrelated funds on 12 different exchanges, which points to something systemic with that endpoint/request rather than 12 separate coverage gaps. Per the same dump-then-lock discipline already used for COT/MTS/FDIC/CA in this file, this rev does NOT guess a fix -- it captures the missing evidence: HTTP status + content-type + a body[:160] snippet whenever the clean-resolve path does not fire (bad status, JSON-parse failure, empty/non-list body, or a result missing exchange+symbol fields), surfaced inline on the per-ISIN log line only on a miss (success lines are byte-unchanged). Holdings (leg C) logic is untouched -- its 0/12 result is a pure downstream symptom of leg A never producing a real ticker (it only ever had the bare ISIN to try against stockanalysis.com, a US-ticker-keyed API, which was always going to 404 regardless), so it gets no new diagnostics until leg A is locked. ETF_FEED_PROBE stays True (pre-armed) for one more run. Each GET still guarded, never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the new diag detail on the [ETF feed probe] block -- it will show whether symbol-search.tradingview.com is Cloudflare/anti-bot blocked (HTML challenge page in the body snippet), wrong endpoint/param (a clean JSON error or unexpected shape), or genuinely returns empty for ISIN-text queries (200 + empty list) -- then lock the real fix (alternate endpoint, different query param, or a different ISIN->symbol resolution path entirely) in the next rev. No data/scoring change this rev.  # 1.127.0: (World ETF Engine Phase 6 — ISIN price + holdings feed probe, logging-only, runner-side, dump-then-lock) NEW probe_etf_isin_feeds() (gated ETF_FEED_PROBE, PRE-ARMED True for ONE run) proves on the runner — using ONLY the dashboard's existing plumbing, NO Yahoo / NO FMP (owner rule 2026-06-30) — which feed gives (a) a PRICE from an ISIN: TradingView symbol-search resolves the ISIN -> EXCHANGE:SYMBOL, then the proven scanner.tradingview.com/symbol symbols-POST (columns:['close'], the same primitive that prices PSX:KSE100/TVC:RUT) returns the close; and (b) the FULL HOLDINGS from an ISIN: stockanalysis.com/api/symbol/e/{sym}/holdings — the EXACT source fetch_etf_holdings() already uses for the US ETF-overlap (returns the whole constituent list, fixing the universe file's top-3-only holdings column). Tests 12 representative catalog ISINs (broad US / US-tech / Korea / the Pakistan special case LU0659579147 / sector / materials / financials / theme / thematic / FR-domicile / broad world); logs per ISIN the resolved TV symbol + close + holdings count + source, plus a tally 'TV price resolved n/12 · stockanalysis full-holdings resolved n/12'. Each GET guarded, the call wrapped in main -> touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [ETF feed probe] block, lock the per-ISIN price + holdings method (if stockanalysis misses UCITS coverage -> lock issuer-file holdings + a TV-symbol map), then flip ETF_FEED_PROBE False and proceed to Phase 7+ (catalog refresh, ranked-10 recs, live tracker, stock->UCITS bridge, Momentum-40, World ETF tab). No data/scoring change this rev.  # 1.126.1: Fix dollar_direction crash in fetch_country_rs() — referenced global 'data' dict which is undefined inside this standalone function (NameError, caught by except every run, dollar_direction meta-row never appended). Now reads EXISTING only.  # 1.126.0: World ETF Engine Phase 2 + Phase 3. (A) Phase 2 — compute_global_sector_theme(): re-points the booming-sector concept at GLOBAL markets using country_rs (already fetched) instead of US-only zacks_sectors. Buckets the 13 countries into 4 themes (Asia-Tech: Japan/Korea/Taiwan, Developed-West: USA/UK/Germany/Switzerland/Canada/Australia, Commodity-Bloc: Brazil/Australia/Canada, Emerging: China/India/Brazil) and scores each by mean 6M USD return + breadth above 200-DMA. Surfaces which global theme is booming. (B) Phase 3 — ETF catalog (etf_universe.json, 134 funds/28 categories from ETF_Universe.xlsx, quality-floored >=10m EUR) embedded as _ETF_CATALOG. New resolve_etf_for_signal() joins country_rs/sector_booming/global theme verdicts to the largest qualifying UCITS ISIN. New etf_recommendations list in data.json.  # 1.125.1: Fix dollar_direction DXY key — was 'dxy_px' (wrong), correct key is 'dxy'. Also read from current-run data dict not EXISTING to get live values.  # 1.125.0: Phase 1 — dollar_direction composite in country_rs; IMF GDP forecasts + World Bank current account enriched into world_lei (hardcoded quarterly).  # 1.124.2: Fix country_rs signal logic — Avoid was wrongly firing for any return outside the Neutral/Overweight bands (e.g. +13.8% Korea showed Avoid). Correct bands: Overweight >+15% · Hedge +5..+15% or -10..-5% · Neutral -5..+5% · Avoid <-10%.  # 1.124.1: Fix BFAGRO/GAL/QTECH batch error — filter applied to _batch_history_cache() pairs loop (the actual download call); v1.124.0 filter landed in a different location and did not silence the batch error blocks.  # 1.124.0: Phase 0 completion: currency split + 200-DMA in country_rs; BFAGRO/GAL/QTECH filtered from batch download  # 1.123.1: (A) Restore FRED for fetch_world_lei() — TGE is JS-rendered, returns empty shell to requests.get(). FRED fredapi already proven on runner with retry/backoff. Expanded to 12 countries: original 8 + South Korea (KORLOLITONOSTSAM) + Germany (DEULOLITONOSTSAM) + India (INDLOLITONOSTSAM) + Brazil (BRALOLITONOSTSAM). Taiwan excluded — not an OECD member, no CLI series exists. NZ excluded — FRED has no series (confirmed v1.119.0). Euro-area kept but will be STALE (series discontinued) — honest stale flag preserved. (B) BFAGRO added to _PSX_YAHOO_SKIP — TradingView scan carries it but Yahoo returns delisted. Same pattern as GAL/QTECH.  # 1.123.0: (LEI-TGE + 13-country RS) (A) fetch_world_lei() rewritten: replaces stale FRED OECD CLI (18-month lag, 2022-11 stale for Euro/Switzerland) with theglobaleconomy.com leading-economic-index scraper using the existing _tge_country() pattern (same site already used for Pakistan CPI). 13 countries: existing 9 + South Korea, Taiwan, New Zealand, Switzerland. Expansion = positive MoM score; contraction = negative. Probe logs raw value+date per country so runner confirms parse before relying on it. Guarded per-country. (B) fetch_country_rs() expanded 9→13 countries: adds South Korea (^KS11/KRW=X), Taiwan (^TWII/TWD=X), New Zealand (^NZ50/NZDUSD=X), Switzerland (^SSMI/CHFUSD=X). FX classification updated. Zero index.html changes — same world_lei + country_rs keys.  # 1.122.0: Wave Z (compute_inst_consensus + fetch_fund_holdings) + GAL/QTECH _PSX_YAHOO_SKIP + pkr_wow/max_score display in index v5.107  # 1.121.2: fix devaluation call-site bug introduced in v1.121.0. The inline semicolon chain assigned _psx_m (the dict) to data['psx_devaluation'] instead of the function return value -> score=None/None every run. Reverted to clean two-step block: build _psx_m with _history_ref, then assign data['psx_devaluation'] = compute_fn(_psx_m).  # 1.121.1: (SX-COT fix) compute_sector_booming() COT mapping completed. Previously only Energy/Utilities/Staples had contracts assigned in cot_by_sector. Materials/Financials/IT/Communications/Industrials were in _COT_MAPPED but silently got no contract -> tab showed n/a for all. Now mirrors the cotFor() mapping in index.html exactly: Materials=gold+copper net (macros.metals, already fetched), IT=NASDAQ, CommSvcs=NASDAQ, Financials=10yr, Industrials=DJIA. cotFor() is the authoritative mapping; scanner matches it.  # 1.121.0: (Wave S PSX sectors + Wave R devaluation + backlog) (A) compute_psx_sector_booming() — PURE function, 3-signal 0-100 composite per PSX sector: breadth 40% (psx_sector_breadth % above 200-DMA) + momentum 35% (1M perf from psx_sector_medians) + rate-sensitivity 25% (SBP rate vs 11% defensive line; beneficiary/neutral/sensitive). Emits psx_sector_booming list with rank/score/band (Booming/Favoured/Neutral/Lagging/Avoid) + score_delta/score_trend vs EXISTING (same WoW arrow logic as US sectors). DATA-only, guarded, freeze-safe. (B) Wave R devaluation improvement: adds signal 6 (rupee WoW slope from history store, 0/1/2 pts) to compute_psx_devaluation(). max_score 7→9. Requires ≥2 history days for WoW slope; graceful fallback 0 pts on first run. Reads EXISTING['history'] passed in. (C) Backlog F5: PSX watchlist now logged with force-include count for Topline/AKD/AHL names.  # 1.120.0: (Wave T enrichment + sector score delta) append_history gains 6 new fields: us_diffusion_net, lei_expansion_count, sector_top, sector_top_score, hy_spread, core_pce — tracks macro breadth + sector leadership over time. compute_sector_booming call-site annotates each sector with score_delta (today minus prior run) and score_trend (rising/falling/flat, threshold 1.0 pt) by comparing to EXISTING — from run 2 onwards every sector carries a direction arrow the index reads as ▲/▼. PURE: no network, reads only already-computed data vs prior data.json. DATA-only, additive, guarded; never touches screen/scoring/IM3/TCE/freeze.  # 1.119.0: (NZL removed from world_lei) FRED carries no OECD CLI series for New Zealand — neither NZLLOLITONOSTSAM nor OECDNZLCLIAMP exist on FRED; NZL removed from _LEI_SERIES so the 'does not exist' error log disappears; honest 8/9 coverage. No screening/scoring/TCE change.  # 1.118.0: (Phase 0 fixes) Fix-1: World LEI NZL series NZLLOLITONOSTSAM->OECDNZLCLIAMP (prior series returned <4 observations, dropping NZL every run); Fix-2: compute_us_diffusion result dict adds key aliases net/phase/direction/deteriorating so index.html reading v1.116 schema keys still works without a paired index change. No screening/scoring/TCE change.  # 1.117.0: (Phase 0 — WORLD ECONOMIES MACRO LAYER, four additive freeze-safe feeds) (A) fetch_world_lei(): pulls 9-country Leading Economic Indicator series from FRED via fredapi (same Fred(api_key=FRED_KEY) pattern the existing _fred_series uses) — Australia/Canada/China/Euro-area/Japan/New-Zealand/Switzerland/UK/USA — each emitting slope (3mo vs 6mo avg), trend (rising/falling/flat), momentum (MoM), signal (expansion/contraction), and as-of date; written to data['world_lei']; guarded + last-good carry. (B) compute_us_diffusion(us_macros): PURE function reading the already-fetched data['macros']['us'] dict, scoring 15 indicators (fed_rate/us_10y/yield_curve/core_pce/cpi_yoy/unemployment/umcsi/permits/industrial_prod/gdp_growth/hy_spread/mfg_emp/wti/fin_conditions/brent_wti_spread) → net score + supportive count + regime label (Expansion/Contraction) + acceleration flag; written to data['us_diffusion']. (C) fetch_country_rs(): pulls 9-country equity-index + FX monthly closes via Yahoo Finance, computes 3/6/12-month USD-adjusted price momentum + trend label + FX contribution + a hedge/overweight/neutral/avoid signal; written to data['country_rs']. (D) compute_sector_booming(zacks_sectors, cot_futures): PURE function reusing already-fetched zacks_sectors + cot_futures, scores each sector 0-100 across 6 weighted signals (price momentum 25%, 200-DMA breadth 20%, forward targets+Zacks rotation 20%, regime fit 15%, relative strength 10%, COT 10%) → 5-level band (Booming ≥80 / Favoured ≥62 / Neutral ≥45 / Lagging ≥30 / Avoid) + rank + per-signal tally + decisive signal; honest COT rule: only 6 sectors mapped to real futures contracts, all others receive zero COT weight (never uses S&P proxy); written to data['sector_booming']. All four: DATA-only, additive, guarded, never touch the universe screen/scoring/IM3/TCE/the frozen ledger → respect the Sept freeze. Zacks sleep fix also included: time.sleep(0.4) (was 2.5s), Session() reuse → cuts Zacks block ~988s → ~168s. Confirm on the runner: [World LEI] logs 9 countries; [US Diffusion] logs net score + regime; [Country RS] logs 9 countries ranked; [Sector Booming] logs band distribution; data.json carries world_lei / us_diffusion / country_rs / sector_booming.  # 1.112.1: (F2 PERSISTENCE FIX — make the explosive statement cache actually survive across runs) the v1.112.0 cache wrote explosive_stmt_cache.json as a SIDE FILE, but the workflow's commit step only commits data.json, and GitHub Actions checks out fresh each run -> the side file never persisted -> every run was a cold cache ('0 hit / 198 fetched' on the live v1.112.0 run) and the ~113s Explosive-screen win never materialised. FIX: the cache now lives INSIDE data.json (the SAME persist-via-the-existing-commit mechanism Wave-T history + shortlist tracking already use): _load_explosive_cache reads EXISTING['explosive_stmt_cache'] (last run's committed data.json) + prunes entries >30d so the dict stays bounded; _save_explosive_cache hands the cache back via a module global; run_explosive now ALWAYS hands it back (not only when dirty) so an all-hit run carries it forward instead of wiping it; main stores it into data['explosive_stmt_cache'] after the US call (and carries EXISTING's forward on a crash). No daily.yml change, no side file. EXPECTED: the FIRST v1.112.1 run is still a cold '0 hit / N fetched' (it seeds the cache into data.json), then the SECOND run logs '[Explosive cache] ~N hit / ~few fetched' and the US Explosive screen drops ~100s. Pure persistence wiring — no scoring/screening/verdict/TCE change; the statement-derived cond is cached, live price/perf/MA/forward still refresh each run. # 1.112.0: (PERFORMANCE + CORRECTNESS PASS — full-scanner audit F1-F6, owner-authorised one-shot; each fix independently flagged + reversible, none touch the universe screen / scoring / IM3 grade, none alter the frozen TCE ledger's tier math). F1 (TCE_YF_FUNDAMENTALS_US_ONLY): compute_tce_streams fired .info/.get_eps_revisions()/.get_revenue_estimate() for PSX too, but Yahoo carries ZERO .KA fundamentals -> 147 guaranteed 404/None calls/run (~65s pure waste) feeding NOTHING (PSX s7 uses the scanner's own TTM eps/rev growth via derive_streams, s8 is skipped, s9/s11/s12 come from the analyst overlay). Gated US-only via _yf_fund; for PSX info stays {} and the estimates stay None = IDENTICAL to the 404 result, so PSX streams are byte-equivalent AND the ~49 per-run PSX 404 log lines vanish. F2 (explosive income_stmt cache): run_explosive re-pulled ~200 US income_stmt every run (~113s) though statements change quarterly -> the COMPUTED cond dict is now cached per ticker 7d (explosive_stmt_cache.json); a fresh hit skips BOTH the income_stmt and the lazy cashflow fetch, live price/perf/MA still come from the candidate each run (only the quarterly statement legs are cached), and a cache miss fetches+recomputes+stores so coverage can't regress. F3 (EPS_ENRICH_TRY_FMP=False): the EPS gap-fill tried FMP /stable/ FIRST for small-cap survivors, which is premium-gated (HTTP 402 every run since v1.101.1) = wasted latency; now Yahoo-first (FMP re-enablable via the flag). F4 (_ETF_OVERLAP_CODE_VER): the ETF-overlap 7-day throttle keyed on SCAN_VERSION, so EVERY scanner bump forced a ~40s re-scrape; it now keys on a dedicated ETF-code version, so unrelated bumps carry last-good. F5 (MTS staleness guard): the SCS MTS 'daily' leverage gauge has been seen frozen months behind the run date (as-of Feb-6 on a Jun-24 run); the fetch now computes the as-of age and, if > MTS_STALE_DAYS (14), logs a warning + sets psx_mts['stale']/['stale_days'] (no fabricated freshness — the value is unchanged, just flagged). F6 (_swallow counter): the load-bearing silent 'except: pass' sites (explosive income_stmt + cashflow, TCE fetch) now increment a counter surfaced in the run summary + data.meta.swallowed, so a degraded leg stops hiding. ALSO COT_HIST_DIAG flipped False (depth confirmed; clears the per-contract diag spam). DEFERRED (stated, not done blind): the mass dead-probe prune (~13 gated probe_/dump fns, ~1500 lines) is a separate dedicated pass — a deletion that large carries real regression risk for zero runtime benefit, so it is NOT bundled here. EXPECTED on the runner: PSX TCE loop ~65s faster + the OGDC.KA-style 404 lines gone; US Explosive ~100s faster on cache-hit runs ('[Explosive cache] N hit / M fetched'); '[FMP EPS] FMP gap-fill disabled' (no 402s); MTS logs a STALE warning if the report is old; the summary prints any 'Swallowed (silent) exceptions'. FREEZE NOTE: F1 is provably equivalent for PSX (empty/None either way), so the ledger's PSX tier list must be UNCHANGED vs the prior run — CONFIRM by diffing US/PSX HIGH/WATCH/IGNORE; identical (expected) => equivalence holds. # 1.111.0: (TCE Yahoo batch pre-fetch — frozen-engine speed cut, owner-authorised "do it now") the TCE momentum loop fetched 6mo daily history ONE NAME AT A TIME (compute_tce_streams: t=yf.Ticker(sym); h=t.history(period='6mo')) -> N sequential Yahoo round-trips, the single largest TCE time cost. NEW _batch_history_cache(candidates, market, max_count) does ONE yf.download(syms, period='6mo', group_by='ticker', threads=True) for the WHOLE pool (mirrors the existing _reprice_us batch the maturity re-pricer already trusts) and returns {bare_ticker: per-ticker OHLCV frame}; run_tce builds it once before the loop and passes hist_cache into compute_tce_streams, which uses the cached frame as `h` when present and FALLS BACK to per-name t.history(period='6mo') on a cache miss (delisted .KA like $GAL/$QTECH, thin names, or TCE_BATCH_HISTORY=False) -> coverage can NEVER regress. EQUIVALENCE: only the SOURCE of the 6mo history bytes changes (batch vs per-name); the extracted per-ticker series is the same daily Close/Volume .history() returns (same group_by='ticker' frame, same yfinance auto-adjust default _reprice_us already relies on), so the downstream s5_volume / s6_momentum / SPY RS-guardrail math is byte-identical. The per-name .info/.get_eps_revisions()/.get_revenue_estimate() calls + YF_DELAY are UNCHANGED (still per-name; the speedup is therefore PARTIAL — history is one of the per-name round-trips, the heaviest). FREEZE NOTE: this DOES touch the Sept-frozen TCE momentum fetch (owner explicitly lifted the freeze for this change). The one risk that CANNOT be validated in the sandbox (Yahoo blocked): if batch yf.download Close differs subtly from .history() Close on the runner's yfinance, a name's TCE tier could shift -> a fresh prediction logs (dedup is per (ticker,tier)). MITIGATION: reversible flag (TCE_BATCH_HISTORY=False instantly reverts); CONFIRM ON THE RUNNER by diffing this run's US/PSX HIGH/WATCH/IGNORE tier list vs the prior run's — if the tier lists match, equivalence holds and the ledger is clean; if they shift, flip the flag off and re-baseline. Confirm on the runner: 'TCE batch history: N/M names pre-fetched in one call' logs for US and PSX, the TCE loop is faster, and US TCE HIGH + the per-name tiers are unchanged vs the prior run. # 1.110.0: (Wave COT-A / D-70 — COT ANALYTICS LAYER, scanner half, DATA-only) each of the 9 COT-futures contracts now carries a normalized positioning block on cot_futures[k]['analytics']: COT Index 1Y (52-wk stochastic percentile of Non-Commercial net) + COT Index 3Y (156-wk) = how stretched positioning is (low = crowded short / room to rally; high = crowded long), NCP long/short % of OI, flip (net % of OI), 4-week & 13-week average flip + a BUY/SELL signal (BUY when the latest flip is above its rolling average), and our own transparent Wilder RSI 13/26/52 on the net series. The PURE _cot_analytics() math was VALIDATED against the owner's full S&P legacy export (all_data_cot.docx, 1000 weekly rows): COT Index 1Y reproduced 17.03, 3Y 18.484, NCP 10.17/17.688, flip -7.519, 4-wk avg -8.761 BUY, 13-wk avg -6.124 SELL — ALL EXACT. Sarmaaya's proprietary 'COT RSI' / 'Possible Bias' are deliberately NOT cloned (the standard Wilder RSI here is labelled our own; D-70 = build transparent equivalents, not copy the proprietary transform). NEW _fetch_cot_history() pulls ~156 weeks per contract via ONE light $where like-filter on the locked include token, then re-applies the SAME full inc/exc match + dedup-by-date as the headline so it can never pull a wrong variant. FULLY GUARDED + ADDITIVE: the headline COT (net/signal/pct_oi/name/date + net_wow/mom/qoq) is BYTE-UNCHANGED, the analytics attach is wrapped in its own try (a thin/failed history omits the block, never fabricates, never touches the headline), and the whole feed still carries last-good. COT_HIST_DIAG PRE-ARMED True for ONE run: logs weeks-returned + the computed index/flip/rsi per contract so the history DEPTH is confirmed on the runner (the sandbox cannot reach CFTC), then flip False next rev. cot_futures still feeds ONLY sector selection + the display -> touches NO universe screen/scoring/IM3/TCE tier/the frozen ledger -> respects the Sept freeze. Confirm on the runner: '[COT analytics SP500] N wks -> idx1y .. idx3y .. flip ..' with N ~150+ (if a contract returns few weeks, its analytics omit gracefully), and data.json cot_futures[k] carries an 'analytics' block. The index display of this layer (metals tab gauge -> macro positioning -> bounded sector tilt) is a SEPARATE later index build.  # 1.109.0: (COT BUCKET FIX — THE REPOINT: all COT-futures contracts now read legacy combined futures-only NON-COMMERCIAL) the v1.108.0 dump LOCKED the last 2 names: S&P headline = 'E-MINI S&P 500' (net -193,978, EXACT Sarmaaya MATCH — NOT 'S&P 500 CONSOLIDATED', which was a -180,143 near-miss, exactly the wrong-variant trap the dump existed to avoid), and the NYMEX WTI benchmark is named with 'WTI-PHYSICAL' (no 'CRUDE OIL' substring — which is why a 'CRUDE OIL' search missed it, and is the SAME string the disaggregated feed already pins NYMEX WTI with every run). fetch_cot_futures REWRITTEN: a single pull of the legacy combined futures-only report (6dca-aqww, $limit=4000 -> several weeks) feeds ALL NINE contracts from the NON-COMMERCIAL (large-speculator) basis via locked include/exclude matchers — SP500='E-MINI S&P 500' (excl MICRO/INDEX/ESG), NASDAQ='NASDAQ-100 CONSOLIDATED', Russell='RUSSELL E-MINI' (excl MICRO/1000), DJIA='DJIA CONSOLIDATED', 10yr='UST 10Y NOTE' (excl ULTRA/MICRO), VIX='VIX FUTURES', Crude='WTI-PHYSICAL'+'NEW YORK', NatGas='NAT GAS NYME'+'NEW YORK MERCANTILE', Agriculture='CORN'+'CHICAGO BOARD OF TRADE' (excl MINI). This REPLACES the wrong-bucket feed that read index contracts from the TFF ASSET-MANAGER bucket (SP500 printed net +986,577 'VERY BULLISH' when specs are -193,978 SHORT; 10yr +2,485,001 vs the real -911,082 SHORT) and commodities from disaggregated MANAGED-MONEY. NEW: Russell + DJIA added (owner decision). Signal is now sign + %-of-OI (VERY at >=10% OI; the old absolute >500k cut was a meaningless artifact of the wrong bucket); each contract also carries pct_oi + name + oi, and net_wow/mom trend backfilled from the multi-week pull. A permanent per-contract audit line logs the matched name + net + a CHECK vs the validated Sarmaaya net for SP500/NASDAQ/DJIA (OK/DRIFT) so the basis stays self-verifying every run. FAIL-SAFE: a contract that fails to match carries its OWN last-good (per-contract setdefault), and a dead pull carries the whole last-good dict — never fabricated. COT_LEGACY_PROBE retired (False). cot_futures still feeds ONLY sector selection (index cotFor: Energy->Crude, Utilities->NatGas, Staples->Corn; Russell/DJIA available for a future index wiring) + the metals/sector trend reads -> touches NO universe screen/scoring/IM3/TCE tier/the frozen ledger -> respects the Sept freeze. Confirm on the runner: '[✓ COT <key>] net ... OK' for the 3 truthed contracts (S&P -193,978 / Nasdaq -20,866 / DJIA +4,339), '9/9' matched, and the dashboard's S&P COT flips from 'VERY BULLISH' to BEARISH (specs net short). The paired index.html (read the live BEARISH/% OI + wire Russell/DJIA into a sector) is a separate follow-on. NEXT (later phase): a true normalized COT-index/percentile per contract (vs the 1-3yr range) replacing the interim sign/%OI label.  # 1.108.0: (COT BUCKET FIX Phase-0c — dump the 2 contract names the v1.107.0 guesses missed) the v1.107.0 run CONFIRMED 7 of 9 contracts (NASDAQ-100 CONSOLIDATED -20,866 MATCH + DJIA CONSOLIDATED +4,339 MATCH again, and Russell/VIX/10yr/NatGas/Corn each pinned to exactly 1 match) — these 7 names were copied verbatim from the v1.106.0 dump so they were certain. The remaining 2, SP500 and Crude, read 'NO legacy contract matched': their headline contract never appeared in the v1.106.0 dump (the 4-name cap cut it off), so v1.107.0 used the CFTC-standard string from memory ('E-MINI S&P 500 STOCK INDEX' / 'CRUDE OIL, LIGHT SWEET'+'NEW YORK MERCANTILE') and BOTH missed — the dataset uses different strings (and since Nasdaq+DJIA are '...CONSOLIDATED', S&P is almost certainly 'S&P 500 CONSOLIDATED', which the E-mini guess excluded). 'NO match' is the FAIL-SAFE outcome (nothing wrong was locked, the run completed clean with 0 hard errors, production fetch untouched). Rather than guess a 3rd time, this rev DUMPS both off the runner: SP500 include broadened to ['S&P 500'] (no exclude) and Crude to ['CRUDE OIL'] (exclude OPTION), and the per-contract cap raised 8->12, so EVERY S&P-500 and NYMEX-crude variant surfaces with its Non-Commercial net + OI, and the existing CHECK auto-flags whichever S&P row equals the validated Sarmaaya -193,978. The other 7 tight matchers are unchanged (still 1 match each). Production fetch_cot_futures STILL BYTE-UNCHANGED (logging-only; metals untouched; respects the Sept freeze). NEXT: read the [COT legacy probe] block — lock the exact S&P + NYMEX-WTI headline names (the S&P one flagged by the -193,978 CHECK), then v1.109.0 repoints ALL COT-futures contracts to legacy Non-Commercial on the 9 locked names + adds Russell/DJIA, and flips COT_LEGACY_PROBE False. No data/scoring change this rev.  # 1.107.0: (COT BUCKET FIX Phase-0b — legacy probe TIGHTENED to confirm S&P/Crude/NatGas headline contracts) the v1.106.0 runner VERDICT: legacy combined FUTURES-ONLY (6dca-aqww) is the Sarmaaya basis — NASDAQ-100 CONSOLIDATED reproduced -20,866 and DJIA CONSOLIDATED +4,339 EXACTLY (fut+options jun7-fc8e was only close: -19,929/+4,426 -> dropped). Columns confirmed (noncomm_positions_long_all/short_all + open_interest_all + report_date_as_yyyy_mm_dd, 133 cols). LOCKED contract names from the dump: NASDAQ='NASDAQ-100 CONSOLIDATED', DJIA='DJIA CONSOLIDATED', Russell='RUSSELL E-MINI' (net -20,249 OI 493k), VIX='VIX FUTURES' (-66,739), 10yr='UST 10Y NOTE' (net -911,082 SHORT — vs the false +2,485,001 Asset-Manager 'VERY BULLISH' the dashboard shows today), Corn='CORN - CHICAGO BOARD OF TRADE' (+77,844). BUT the v1.106.0 probe's 4-distinct-name cap + loose substrings let the many-variant contracts crowd the headline off the list: for S&P it returned the Quarterly-Dividend index, the MidCap-400, the Micro E-mini and the S&P-Utilities index (+3,619/-837/+138,357/+1,078) — NONE the E-mini S&P 500, so the validated -193,978 row never surfaced; same for the NYMEX WTI crude + NYMEX Henry Hub gas headline contracts. This is exactly the plausible-but-wrong-variant trap the probe exists to catch — surfaced in the LOG, not in live data. This rev re-arms the SAME probe with (a) only the locked 6dca-aqww dataset, (b) TIGHT per-contract matchers (include-ALL + exclude-ANY) that pin the one headline liquid contract and exclude the decoys, and (c) the cap raised 4->8 as a safety net, so the E-mini S&P 500 STOCK INDEX net surfaces and its CHECK vs Sarmaaya -193,978 reads MATCH before any code trusts it. Production fetch_cot_futures is STILL BYTE-UNCHANGED (no regression; metals untouched). Logging-only, guarded, wrapped in main -> respects the Sept freeze. NEXT: read the [COT legacy probe] block — once S&P reads -193,978 MATCH and Crude/NatGas show the NYMEX headline, v1.108.0 repoints ALL COT-futures contracts to legacy Non-Commercial on the locked names + adds Russell/DJIA, then flips COT_LEGACY_PROBE False. No data/scoring change this rev.  # 1.106.0: (COT BUCKET FIX Phase-0 — legacy-combined NON-COMMERCIAL repoint PROBE, logging-only, dump-then-lock) CONFIRMED 3 WAYS (source lines ~1012-1013 + live data.json + validated Sarmaaya tabs): fetch_cot_futures reads SP500/NASDAQ/10yr/VIX from the TFF report's ASSET-MANAGER bucket (asset_mgr_positions_long/short) and Crude/NatGas/Corn from disaggregated MANAGED-MONEY — NEITHER is the legacy combined NON-COMMERCIAL (large-speculator) basis the dashboard, the metals page and Sarmaaya use. Asset Managers are structurally long index futures, so SP500 prints net +986,577 "VERY BULLISH" when the validated Non-Commercial net is -193,978 SHORT (NASDAQ reads +8,098 "BULLISH" vs the real -20,866 short). Owner decisions this rev: (1.yes) switch Crude — and by the same consistency logic ALL COT-futures contracts — to ONE unified legacy Non-Commercial basis; (2.now) ADD Russell + DJIA (not currently fetched). Because the legacy COMBINED report is effectively a NEW dataset (different Socrata id, different columns, AND different contract-name strings — it carries full-size + E-mini + consolidated S&P, so matching the wrong VARIANT yields a plausible-but-WRONG number) and the sandbox cannot reach CFTC, NEW probe_cot_legacy() (gated COT_LEGACY_PROBE, PRE-ARMED True for ONE run) dumps from the runner: which legacy dataset resolves (6dca-aqww futures-only vs jun7-fc8e fut+options), that it carries noncomm_positions_long_all/short_all + open_interest_all + the report-date column, the ACTUAL distinct market_and_exchange_names matching each contract (so the right E-mini/Cons/mini keyword is LOCKED not guessed), and the latest Non-Commercial long/short/net per contract + an explicit CHECK vs validated Sarmaaya ground truth (S&P -193,978 / Nasdaq -20,866 / DJIA +4,339) so the basis is PROVEN before any code trusts it. Production fetch_cot_futures is BYTE-UNCHANGED this rev (no regression; metals already correct on the CMX Non-Commercial page, untouched). Each GET guarded, the call wrapped in main -> touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [COT legacy probe] block, lock dataset+columns+per-contract keyword, repoint ALL COT-futures contracts to legacy Non-Commercial + add Russell/DJIA in v1.107.0, then flip COT_LEGACY_PROBE False. No data/scoring change this rev.  # 1.105.0: (Wave G-feed — metal price HISTORY + technicals, the real-trend feed the metals graphics were waiting for) fetch_metals widened from 6mo to 1y per metal and now computes, for each of GOLD/SILVER/PLATINUM/PALLADIUM/DXY, a compact downsampled price-history array ({key}_hist, ~60 points over the last ~120 trading days, always ending on the latest close) + SMA50/SMA200 ({key}_sma50/_sma200) + RSI(14) Wilder ({key}_rsi14) + a trend label vs the 200-day ({key}_ma_trend up/down + {key}_ext_200_pct) + the golden/death cross ({key}_cross). New PURE _metal_technicals(closes) helper does it all, length-guarded (SMA200 omitted until 200 closes exist, RSI until 16, etc. — never fabricated, NaN-stripped). This turns the index v5.97 metal tile sparklines + forward-outlook cones from delta-reconstructed (3-point WoW/MoM) into REAL multi-week moving-average charts, and lets a future index version put a true 50/200-DMA trend chip + RSI on each metal and light up the technical half of the forward read. DATA-only feed into macros.metals (extra keys; the existing gold_px/_wow/_mom + gs_ratio + GVZ/DFII10/COT untouched); the metals tab is a separate engine from the Sept-frozen TCE -> respects the freeze. Guarded per-metal (a fetch miss carries last-good as before). Confirm on the runner: each metal logs '· SMA200 N · up/down golden/death · RSI N' and data.json macros.metals carries gold_hist/gold_sma50/gold_sma200/gold_rsi14/gold_ma_trend/gold_cross (+ silver_/platinum_/palladium_/dxy_).  # 1.104.0: (Wave T - conviction snapshot across the WHOLE live book, honestly dated) the v1.103.0 stamp only caught a name on its GENUINELY-first listing, so after days of running it stamped 1 of 183 live rows -> the long-held core picks (AMD/NVDA/OGDC/banks) would never carry a conviction tag. FIX: track_shortlists now ensures every CURRENTLY-LISTED row carries a conviction snapshot. A row stamped at true first-seen (v1.103.0) keeps signal_date = first_date. A row that predates the capture gets TODAY's grade/tier/strength/valuation stamped ONCE, dated signal_date = today (deliberately != first_date) so Wave PB can distinguish a true entry-day grade (signal_date == first_date) from a first-OBSERVED grade (signal_date > first_date) - never pretending today's grade was the entry grade. entry_bench is now keyed to each row's REAL first_date via a nearest-at/earlier lookup in the rolling history store (was today's macro level), so alpha_since pairs correctly with pct_since (both span first_date->today); rows whose first_date predates the stored history get no entry_bench (honest, no fabricated alpha). Pure additive data on the tracker; reads grades/tiers/history already in data.json; touches NO screening/scoring/IM3/TCE tier/the frozen ledger -> respects the Sept freeze. Confirm on the runner: [Wave T shortlist] logs 'N conviction-stamped [M at true entry]' with N jumping to ~the live count, and shortlist_tracking rows carry signal_date + entry_grade/entry_tier/entry_strength/entry_bench + alpha_since.  # 1.103.0: (Wave T - signal-at-entry stamp on the shortlist tracker; the can't-backfill gap from the Wave PB readiness audit) track_shortlists now FREEZES each pick's conviction signal AT first-seen - im3 grade + pct, TCE tier, explosive strength_score, valuation label - PLUS the entry benchmark level (SP500 for US, KSE-100 for PSX, mirroring the TCE ledger's entry_bench) onto the stocks-row, captured ONCE on first listing and NEVER overwritten (a name re-scores every run, so its entry-day grade is unrecoverable later - the one Wave-PB input that cannot be backfilled). On each later run it also writes alpha_since = pct_since minus the benchmark's move over the same window, computed from the stored entry_bench (so alpha is a durable stored field, not a fragile runtime history-join that breaks for picks predating the history window). Existing pre-1.103.0 rows correctly DON'T receive entry_* (their entry grade is already gone - never fabricated from the current grade). Pure additive data on the tracker; reads values already in data.json; touches NO screening/scoring/IM3/TCE tier/the frozen ledger -> respects the Sept freeze. Confirm on the runner: [Wave T shortlist] logs an 'entry-signal stamped' count and new shortlist_tracking rows carry entry_grade/entry_tier/entry_strength/entry_bench + alpha_since.  # 1.102.1: (COT NatGas keyword LOCKED) the v1.102.0 dump read the real CFTC contract names off the runner: the Henry Hub natural-gas FUTURES contract is 'NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE' (CFTC writes 'NAT GAS NYME', NOT 'NATURAL GAS' — which is why the old keyword never matched). Changed the NatGas ALL-of keyword from ('NATURAL GAS','NEW YORK MERCANTILE') to ('NAT GAS NYME','NEW YORK MERCANTILE') — uniquely identifies the main Henry Hub futures and excludes the decoys the dump revealed (NAT GASLNE gasoline, NAT GAS ICE LD1 on ICE not NYMEX, HENRY HUB BASIS/INDEX swaps). Now NatGas matches -> cot_futures carries NatGas -> the dashboard's Utilities sector reads its own gas COT signal instead of falling back to the S&P (cotFor() Utilities->NatGas, pre-wired since index v5.82). The v1.102.0 diagnostic stays in the code, gated off (it self-silences once NatGas matches). Crude+Agriculture matches byte-unchanged. DATA-only sector-selection signal -> touches NO universe screen/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. Confirm on the runner: '✓ COT futures disaggregated (Managed Money): [\'Crude\', \'NatGas\', \'Agriculture\']' and the [COT NatGas diag] line is GONE.  # 1.102.0: (COT NatGas dump-then-lock, logging-only) the disaggregated managed-money feed matches only ['Crude','Agriculture'] every run -> the NatGas key's ('NATURAL GAS','NEW YORK MERCANTILE') ALL-of keyword pair is not present in the actual CFTC contract name, so Utilities keeps falling back to the S&P (cotFor() graceful fallback). Crude ('WTI-PHYSICAL'+'NEW YORK') and Agriculture/Corn ('CORN'+'CHICAGO BOARD OF TRADE') match from the SAME 600-row pull, so the report IS being read - only the gas keyword is wrong (likely 'NAT GAS NYME' or a renamed Henry Hub contract). Added a one-shot diagnostic that fires ONLY when NatGas is unmatched: it dumps the actual market_and_exchange_names values containing GAS/HENRY (up to 12 distinct) + the row count, so the exact contract string is read off the runner and the correct keyword locked next increment. Pure logging on the existing disaggregated rows; touches NO data/screening/scoring/IM3/TCE/the frozen ledger; the Crude+Agriculture matches are byte-unchanged -> respects the Sept freeze. NEXT: read the [COT NatGas diag] line, lock the right keyword, then the diagnostic self-silences (NatGas matches -> the gated block won't fire).  # 1.101.1: (FMP EPS miss diagnostics) the v1.101.0 run filled 14/14 from Yahoo with FMP 0 and NO [FMP EPS diag] line -> FMP returned something other than >=2 statements for all 14 small-cap survivors, but the failure path was silent so the CAUSE is unknown (paywall 402/403 vs empty list vs free-tier symbol coverage — the v1.99.0 probe only proved AAPL, a mega-cap). Added one-shot failure logging: the first 3 FMP misses now log the ticker + HTTP status + body[:150] (or 200-but-short-list shape, or exception) so the next run reveals exactly why. Pure additive logging on the already-safe fallback path (Yahoo still fills, coverage cannot regress); no behaviour/scoring/screening/TCE change -> respects the Sept freeze. NEXT: read the [FMP EPS miss] lines — if it's free-tier coverage of small-caps, FMP-first simply stays a large-cap optimisation and Yahoo keeps the EPS tail (no harm); if it's auth/url, fix + re-confirm.  # 1.101.0: (Yahoo->FMP statements cutover — FREEZE-SAFE slice: the EPS gap-fill only) the US EPS enrichment for Explosive-pool survivors missing eps_growth now tries FMP /stable/income-statement FIRST (annual, limit=2, most-recent-first; free tier probe-confirmed in v1.99.0), computing the SAME diluted-EPS (fallback basic) YoY growth (curr-prev)/|prev|*100 over the two most-recent fiscal years, tagged growth_source='fmp_stmt'; the IDENTICAL Yahoo income_stmt block is KEPT as the fallback for any name FMP can't fill (tagged 'yf_stmt') so coverage can NEVER regress, and FMP-vs-Yahoo hit counts are logged separately so the survivor-delta is visible. A one-shot [FMP EPS diag] logs the first response's field names so the eps key is confirmed live (the picker is already tolerant: epsDiluted/epsdiluted/eps). FMP-first removes the ~27s Yahoo income_stmt loop + retires the Yahoo shared-crumb-poisoning failure mode for these names. FREEZE NOTE: this feeds the EXPLOSIVE pool only — separate from the Sept-frozen TCE engine, whose TCE-15 ranks by REVENUE growth (not eps_growth) + ETF-consensus, so the frozen prediction pool is byte-unchanged; the momentum (s5/s6) + SPY RS-guardrail stay on Yahoo until the freeze lifts (~Sept). Guarded per-name + whole-block; FMP_API_KEY absent -> Yahoo-only (logged). Confirm on the runner: 'EPS enriched N/M (FMP x, Yahoo y)' with x>0, and the [FMP EPS diag] field list.  # 1.100.0: (LIVE INDEX LEVELS + ARAB LIGHT, locked from the v1.99.0 probe; DISPLAY/DATA-only, freeze-safe) (A) US index levels: NDX from FRED NASDAQ100 + Dow from FRED DJIA (same mechanism as SP500), Russell-2000 from TradingView TVC:RUT (no free FRED Russell series; probe confirmed TVC:RUT=3007 + FRED NASDAQ100=30406/DJIA=51493) -> macros.us.ndx/dow/rut + _date, each guarded with last-good fallback; the dashboard US Forward Outlook panel reads these live (was dated snapshots). (B) Arab Light: NEW fetch_arab_light() reads the World Bank monthly commodity sheet 'Crude oil, Dubai' (the standard Arab Light proxy + the owner's stated benchmark) -> macros.us.arab_light/_month/_source; layout LOCKED against ground truth (the project's CMOHistoricalDataMonthly.xlsx is the same file: sheet 'Monthly Prices', header row 5, Dubai column, '2026M05' month tokens, '…'=missing); MONTHLY cadence (benchmark read, not a daily tick); openpyxl lazy-imported (add to daily.yml if the log says 'openpyxl not installed'); last-good safe. DATA_SOURCE_PROBE disarmed False (probe kept, gated off). The Yahoo->FMP statements cutover (FMP /stable/ free tier confirmed working) is the SEPARATE next step. Neither touches screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. Confirm on the runner: macros.us carries ndx/dow/rut + arab_light, and the dashboard US Forward Outlook shows live index levels.  # 1.99.0: (combined DATA-SOURCE PROBE for the 3 owner-priority feeds, logging-only, dump-then-lock — runner-side because FRED/TV/FMP/World-Bank are all sandbox-blocked) NEW probe_data_sources_v199() (gated DATA_SOURCE_PROBE, PRE-ARMED True for ONE run) runs 3 isolated reachability/shape probes so each can be LOCKED without guessing an endpoint/series/symbol (a wrong one fails silently or 400s): (A) US INDEX LEVELS NDX/DJI/RUT live — tests candidate FRED series (NASDAQ100/NASDAQCOM, DJIA, RU2000PR/RU2000/RUT, + SP500 control) AND candidate TV index symbols via the proven PSX:KSE100 symbols-POST pattern, logging which return a real level; the dashboard US Forward Outlook panel currently shows these on DATED snapshots while the S&P is live (FRED 'SP500'); (B) ARAB LIGHT / DUBAI CRUDE — the stated benchmark is Arab Light but only WTI/Brent are fetched today; tests the World Bank monthly commodity sheet (carries 'Crude oil, Dubai', the standard Arab Light proxy — the project's own CMOHistoricalDataMonthly.xlsx is this file) + candidate TV crude symbols, logging reachability/content-type/size; (C) FMP /stable/ — prereq for the Yahoo->FMP statements cutover (v3 endpoints retired/403); logs whether FMP_API_KEY is set and what /stable/ quote/income-statement/ratios-ttm/historical-price return on the FREE tier (200+data vs 401/402/403 premium-gated) with a body snippet so the shape is readable. Each request guarded, the call wrapped in main -> touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NOTE the Yahoo cutover's momentum (s5/s6) + SPY RS-guardrail are FROZEN-entangled and stay on Yahoo until the freeze lifts (~Sept); the freeze-SAFE wins (index levels, Arab Light, FMP-based EPS gap-fill) lock first. NEXT: read the [v199 probe] A/B/C blocks, lock each, then flip DATA_SOURCE_PROBE False. No data/scoring change this rev.  # 1.98.0: (Wave S Phase 2e - SECTOR DIVIDEND-YIELD income leg, locked from the v1.97.0 probe) the probe verdict: 'dividends_yield' is the right TV column, values ALREADY IN PERCENT (US mega-caps 0.24-0.47%, PSX 4.8-7.3%), null=non-payer (US 7/12 nonnull, PSX 12/12); dividends_yield_fwd/dps empty, dividend_payout_ratio_ttm is a payout ratio not a yield. Added 'dividends_yield' to BOTH sector POSTs (proven OK, no 400). Per sector div_yield = MEAN over ALL sampled names treating null as 0% (non-payer earns no income, so the basket-average yield is honest) -> requires dy_n>=5 AND >=1 actual payer (else omitted, so a no-coverage sector blanks rather than showing a false 0%). Written to data['sector_medians'] + data['psx_sector_medians'] as div_yield (percent). This completes the forward read: the dashboard (index v5.89) shows analyst price-target return + dividend yield = TOTAL expected return, apportioned to the coming quarter + six months. DIV_YIELD_PROBE disarmed False (probe kept, gated off). Guarded/last-good; extra keys ignored by im3. DATA/DISPLAY only -> respects the Sept freeze.  # 1.97.0: (Wave S Phase 2d - DIVIDEND-YIELD COLUMN PROBE, logging-only, dump-then-lock) the sector forward read (v1.96.0) shows the analyst price-target return but NOT the income (dividend-yield) leg, because the exact TV dividend-yield column name is unknown and a wrong column 400s the WHOLE sector POST. NEW probe_dividend_yield_columns() (gated DIV_YIELD_PROBE, PRE-ARMED True for ONE run) tests 6 candidate columns (dividends_yield / dividends_yield_current / dividend_yield_recent / dividends_yield_fwd / dps_common_stock_prim_issue / dividend_payout_ratio_ttm) ONE AT A TIME in their OWN throwaway america/scan + pakistan/scan POSTs (range[0,12]) -> logs HTTP status + n + nonnull + a 4-value sample per candidate so the accepted column AND its units (2.5=already %, 0.025=decimal) are read off the runner. Each probe POST is isolated + guarded, the call wrapped in main -> can NEVER touch the production sector medians POST, scoring, IM3, the TCE tier or the frozen ledger -> respects the Sept freeze. NEXT: read the [div-yield probe] block, lock the accepted column+units into BOTH sector POSTs (add div_yield per sector -> the dashboard adds the income leg so the forward read becomes target-upside + dividend-yield = total expected return), then flip DIV_YIELD_PROBE False. No data/scoring change this rev.  # 1.96.0: (Wave S Phase 2c - SECTOR FORWARD READ, DATA-only) per-sector forward numbers for the dashboard's expected-return-next-quarter/six-months line on every US + PSX sector (the sector twin of the index Forward Outlook panels). Added price_target_average + earnings_per_share_forecast_next_fq + earnings_per_share_fq to BOTH sector POSTs - PROVEN columns (v1.94.0 probe: target 84%, fwd EPS 96-98%) so no 400 risk. Per sector (>=5 names, mean): tgt_upside=(target/close-1)*100 = implied ~12m price return; fwd_eps_q_g=(fwd_fq/cur_fq-1)*100 next-quarter EPS growth (only cur_fq>0, bounded). Written to data['sector_medians'] + data['psx_sector_medians']. Dividend-yield leg DEFERRED pending a column-name probe (not guessed). Guarded/last-good; extra keys ignored by im3. DATA/DISPLAY only -> respects the Sept freeze. Confirm: [sector medians]/[PSX sector medians] log tgt~N%, data.json sectors carry tgt_upside + fwd_eps_q_g.  # 1.95.0: (Wave S Phase 2 - SECTOR PRICE-MOVE + PSX SECTOR MEDIANS, DATA-only feed for the dashboard sector summaries) TWO additive sector aggregates so the Sector Implications tab can show a real price TREND (not just analyst upgrades/breadth) and bring PSX up to the US 'vs market' summary. (1) US: added Perf.W + Perf.1M + Perf.3M to _SECTOR_MED_COLS (the existing isolated america/scan medians POST - zero extra request), and fetch_sector_medians now also emits per-sector perf_w/perf_1m/perf_3m = the AVERAGE % price move of the sector's constituents over 1wk/1mo/3mo (mean, >=5 names else omitted) onto each sector in sector_medians.json + data['sector_medians']. This is sector momentum computed IN-RUN from per-ticker TV perf fields -> NO dependency on the Wave T rolling-history store. (2) PSX: NEW fetch_psx_sector_medians() - the PSX analog of fetch_sector_medians, ONE isolated pakistan/scan POST over the top-600 by mcap grouped by TV sector -> per-sector median P/E + operating/net margin + ROE (margins/ROE as DECIMALS to match the US shape; a metric with <5 samples is omitted -> dashboard falls back) + 200-DMA breadth + the same perf_w/perf_1m/perf_3m price move; written to data['psx_sector_medians']. The hard-won v1.64.1 breadth function is byte-unchanged (its own separate POST). Both blocks fully guarded + last-good carry + never raise; extra keys are ignored by im3 (it reads pe/op_margin/net_margin/roe only). DATA/DISPLAY only - never touches the universe screen, scoring, IM3 grade, TCE tier, the frozen ledger, or admission -> respects the Sept freeze. The paired index.html (~v5.88) wires the price-move + a momentum sparkline into the US sector summary and adds the SAME 'vs market' summary to PSX sectors, shipped separately AFTER this feed runs (validated against the real new data.json). Confirm on the runner: [sector medians] sectors now carry perf_w/perf_1m/perf_3m, [PSX sector medians] logs N sectors, and data.json carries psx_sector_medians + perf fields on sector_medians.  # 1.94.0: (COT SECTOR WIRING - disaggregated managed-money expansion) fetch_cot_futures now ALSO pulls Natural Gas (NYMEX) and Agriculture/Corn (CBOT) from the disaggregated 72hh-3qpy endpoint alongside Crude (limit 200->600 so the extra markets' latest rows are captured), each keyed by ALL-of keywords on market_and_exchange_names with its own very-bullish |net| threshold (NatGas 100k, Corn 200k) + the same backfilled WoW/MoM/QoQ net trend. Crude match is byte-unchanged ('WTI-PHYSICAL'+'NEW YORK', thr 200k) so Energy's COT signal is identical. cot_futures now carries NatGas + Agriculture, which index v5.82 cotFor() already maps Utilities->NatGas and Consumer Staples->Corn (pre-wired, graceful SP500 fallback until this lands - order-independent). Materials is already wired to gold+copper from macros.metals (no scanner dependency, live in v5.82). DATA-only sector-selection signal - never touches the universe screen, scoring, IM3, the TCE tier or the frozen ledger -> respects the Sept freeze. Confirm on the runner: the '[COT futures disaggregated]' log lists ['Crude','NatGas','Agriculture'] (if a CFTC market name differs the key simply won't appear and that sector stays on SP500 - never fabricated), and data.json cot_futures gains NatGas + Agriculture.  # 1.93.0: (US BANK SCORECARD FEED — supersedes v1.92.0) fetch_us_bank_ig2 now ALSO writes a 'us_sc' block per US bank so im3_score v2.17.0 routes them to the purpose-built CAMELS scorecard score_bank_us() instead of the re-banded Pakistani IG2 'us' calib. ADDED FDIC fields to the financials GET: ROA, NIMY, EEFFR, LNLSDEPR, NPERFV, NTLNLSR, LNATRESR, IDT1RWAJR, RBC1AAJ, INTAN, NONII, NONIX, DEPINS, DEPUNINS, COREDEP, DEPNIDOM, ORE (NIM/NETINC/ASSET/LNLSNET/DEP/EQ/NALTOT/RBCRWAJ already requested). rec['us_sc'] carries the FY2024 scalars (FDIC pre-computed ratios car_total/tier1_rbc/tier1_lev/roa/nimy/eff/ldr/noncurrent_pct/nco_rate/allow_loans + raw $ intan/nonii/nonix/nim_dollar/eq/netinc/asset/dep/depins/depunins/coredep/depnidom/naltot/ore/lnlsnet) + a 5yr series{asset,loans,deposits,netinc} for the 4 CAGRs — fully self-contained, score_bank_us reads ONLY rec['us_sc']. The existing IG2 series stay on the entry too, so a pre-v2.17.0 im3 still scores these via score_bank_ig2 calib='us' (order-independent: the scorecard activates only when BOTH scanner v1.93.0 + im3 v2.17.0 are deployed; until then no regression). PSX entries untouched (write_bank_ig2_overrides PSX-only, US tickers distinct -> pure add/re-merge each run). Built from the metrics US analysts/examiners use (FDIC Quarterly Banking Profile + Basel III well-capitalized + the standard credit/funding/liquidity screens) — fixes the audit finding that the IG2 'us' calib only re-banded 10 of 24 ratios (4 growth bars still on Pakistan's 15%/5% PKR-inflation thresholds) and lacked the entire liquidity/funding + credit-stress dimension (the 2023 SVB lessons: uninsured & core deposit mix, net charge-offs, reserve coverage, Texas ratio) + tangible capital (TCE/TA, ROTCE) + pre-provision earning power (PPNR). DEFERRED (no clean FDIC field for small banks): CRE concentration, AOCI/unrealized-loss burden, EVE/NII, LCR. DATA-only (IM3 bank input, a separate scorer) -> respects the Sept TCE freeze. 8 light GETs, guarded per-GET + whole-call, never raises. Confirm on the runner: [US-bank IG2] logs each bank + 'merged 8 US bank(s)'; after IM3 the 8 US banks (COF/CCNE/MCBS/ISTR/OSBC/COFS/PLBC/CARE) show a 'US scorecard (CAMELS) (us)' grade out of ~42 (21 ratios x2). No screening/TCE/PSX-scoring change.  # 1.92.0: (Group-D - US-bank IG2 feed LIVE, scanner-only, consumer already wired) the v1.91.0 resolution dump locked all 8 ticker->CERT: COF 4297 / CCNE 13876 (CNB Bank PA - corrected off the asset-sorted [0] 'Dime Commercial Bank' NY false match) / MCBS 58181 / ISTR 58316 / OSBC 3603 / COFS 1014 / PLBC 23275 / CARE 58596, each verified by name+state. NEW fetch_us_bank_ig2() pulls each CERT's FDIC ANNUAL call reports (Dec-31, FY2019-2024) and maps them to the IG2 input series: markup<-INTINC, net_spread<-NIM($ net interest income), pbp<-PTAXNETINC+ELNATR, pat<-NETINC, total_assets<-ASSET, gross_loans<-LNLSNET, deposits<-DEP, investments<-SC, equity<-EQ, npl<-NALTOT, provisions<-ELNATR, branches<-OFFDOM + FY24 scalars car_2024<-RBCRWAJ, tax_2024<-ITAX, pbt_2024<-PTAXNETINC; then MERGES them into bank_ig2_overrides.json (called right AFTER write_bank_ig2_overrides, which overwrites that file PSX-only every run; US tickers are distinct -> pure add, re-merged each run, no throttle). Anchored on Dec-31 annuals so a distorted latest quarter (CARE Q1-2026 ROE 77.85 off a one-off) is never used. FDIC_PROBE disarmed. Guarded per-GET + whole-call; never raises. DATA-only -> respects the Sept TCE freeze.  # 1.91.0: (Group-D Phase-0b - US-bank ticker->CERT resolution dump, still logging-only) the v1.90.0 probe verdict is positive: banks.data.fdic.gov reachable, NAME->CERT resolves (Capital One->CERT 4297), and /api/financials carries every IG2 field (ROE 9.51, ROA 1.39, ADR-equiv LNLSDEPR 81.47, NIM NIMY 8.35, EEFFR 50.04, capital RBC1AAJ/RBCRWAJ/IDT1RWAJR, credit NPERFV) - 160 fields. FDIC has NO ticker field (STKEXSYM/STKEX both None), so a ticker->CERT map is required. The scanner's explosive recs carry name=ticker (no legal name), so probe_fdic_bankfind now also iterates the 8 actual US screen banks (COF/CCNE/MCBS/ISTR/OSBC/COFS/PLBC/CARE) with BEST-KNOWLEDGE name queries, logging the top-3 institution matches (CERT/NAME/STALP/ASSET) + the best match's IG2 fields - so each CERT can be VERIFIED from the runner log then LOCKED into a hardcoded map next increment (cannot verify regional-bank CERTs offline -> dump-then-lock, never fabricate). Still gated FDIC_PROBE=True, each GET guarded, wrapped in main, never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the resolution dump, lock the 8 CERTs, then build fetch_us_bank_ig2() (writes us_bank_ig2_overrides.json - US analog of write_bank_ig2_overrides) + the im3_score.py fill-missing consumer (needs the current im3_score.py), then flip FDIC_PROBE False. No data/scoring change this rev.  # 1.90.0: (Group-D Phase-0 - US-bank IG2 FDIC BankFind probe, logging-only, runner-side) US financials carved to the IM3 System-B bank model (COF/CCNE/MCBS/ISTR/OSBC/COFS/PLBC/CARE) have NO IG2 input source, so they score on a reduced applicable denominator (40/48, 43/55, 41/55, 42/55) while PSX banks get roe/roa/adr/NIM from SCS+manual. The FDIC BankFind API (banks.data.fdic.gov, free, no key) serves US call-report financials (ROA/ROE/NIM/assets/deposits/equity/loans/efficiency/capital). Before writing fetch_us_bank_ig2(), NEW probe_fdic_bankfind() (gated FDIC_PROBE, PRE-ARMED True for ONE run) proves ON THE RUNNER (sandbox cannot reach FDIC): (a) banks.data.fdic.gov reachable; (b) /api/institutions resolves a bank NAME -> CERT + whether it carries a ticker field (STKEXSYM/STKEX - FDIC keys on CERT not ticker, so the build needs a ticker->CERT map); (c) /api/financials returns the IG2-relevant fields for that CERT (dumps ALL field keys + ROA/ROAPTX/ROE/NIMY/EEFFR/ASSET/DEP/EQ/LNLSNET/RBCT1J values), with a STALP:VA largest-bank fallback so (c) runs even if name-resolution misses. Mirrors probe_pak_ca: each GET guarded (20s), wrapped in main, never raises, touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [FDIC bank-IG2 probe] block -> lock the field map + CERT-resolution path, build fetch_us_bank_ig2() + a ticker->CERT map (US analog of write_bank_ig2_overrides), then flip FDIC_PROBE False. No data/scoring change this rev.  # 1.89.1: (cosmetic, no logic change) removed the dead/misleading log line "SBP reserves: official page is PDF; keeping last-good if TE missed" - it fired UNCONDITIONALLY every run even though F3 now feeds reserves LIVE from sbp.org.pk/ecodata (it predates F3). The last-good fallback below it (if sbp_reserves is None -> carry EXISTING) is untouched. No data/scoring change.  # 1.89.0: (Group-A quick win - ETF-consensus sector fill) the US TCE pool mixes screen survivors (carry a TV sector) with the ETF-consensus large-caps from the ETF-overlap (ticker+name+weight only, NO sector), so all ~20 of them (AMAT/LRCX/AVGO/MU/NVDA/WDC/MRVL/AMD/CSCO/TXN/KLAC/STX/MSFT/SNDK/GOOGL/CAT/QCOM/INTC/AAPL/XOM) sat in tce_us with sector='' and showed no vs-sector read on the Results tab. v1.81.0 backfilled this only into shortlist_tracking (via a harvest of sector-bearing lists), which reaches a name ONLY if some OTHER list already carries its sector - so the 14 large-caps absent from the band/explosive screens stayed blank. FIX at the source: 'sector' APPENDED to _US_ANALYST_COLS (the analyst overlay already does one america/scan POST over the exact TCE pool); the zip stays aligned (ncol bumps with it, the len-guard still holds) and derive_psx_analyst_streams reads by KEY so s11/s12/s9 are byte-identical -> US TCE tiers provably unchanged (freeze-safe, verified: streams identical with/without the extra key). Each pool candidate with a blank sector inherits _ar['sector'] BEFORE run_tce, so tce_us now carries the TV sector (matches the harvest convention). Never fabricated (no analyst sector -> stays blank). Display-only. Confirm on the runner: US TCE HIGH still 8; the 20 large-caps in tce_us now carry a sector; US analyst overlay still matches ~213/214.  # 1.88.1: (ops, no logic change) CA_PROBE disarmed back to False now the v1.88.0 verdict is read on the runner: TheGlobalEconomy reports Pakistan's Current Account QUARTERLY ('Current Account surplus of 1369 USD Million in the first quarter of 2026'), unit USD Million. The dashboard input + its surplus/deficit thresholds are MONTHLY, so index v5.79 wires pak_ca as the monthly RUN-RATE (quarter/3 ~456 = SURPLUS) - no scanner-side change to the stored value (it stays the faithful quarterly 1369; the run-rate conversion is a display transform). The probe stays in the code, gated off; re-arm only to re-confirm the unit. No data/scoring/screening change; respects the Sept freeze.  # 1.88.0: (CA-units probe, logging-only, runner-side) pak_ca is read from TradingEconomics (tradingeconomics.com/pakistan/current-account) by _te() with the regex 'Current Account' + first number within 40 chars -> 1369 last run. The dashboard input #pak_ca is "Current Account (Monthly USD M)" (default 120), so if 1369 is an ANNUAL / FY-cumulative figure a blind inject overstates the monthly CA ~12x - which is exactly why pak_ca was NOT synced in index v5.77 (fiscal was). NEW probe_pak_ca() (gated CA_PROBE, PRE-ARMED True for ONE run) dumps what TE actually serves around "Current Account": the production-regex value (should reproduce 1369), TE's own summary sentence ('Pakistan recorded a Current Account surplus/deficit of N USD Million/Billion in <Month> <Year>' - the decisive unit+period evidence), a text window, and unit/period keyword presence. Mirrors probe_free_levers exactly: each GET guarded (15s), wrapped in main, never raises, touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the [CA-units probe] block -> a follow-up either injects pak_ca as-is (if monthly USD-M), divides by 12 / relabels the input (if annual), or leaves it manual (if % of GDP), then flips CA_PROBE False. No data/scoring change this rev.  # 1.87.0: (F4 - LIVE PAKISTAN CPI from PBS, replaces the dead TheGlobalEconomy scrape) pbs.gov.pk/cpi redirects to an IMF-SDMX XML feed (CPI.xml) of monthly index series; the headline all-items CPI is INDICATOR="PCPI_IX" (base 2015/2016=100), the others are COICOP sub-groups. The old PBS attempt regexed for "X.XX percent" in HTML (never present in the XML) AND was guarded `if pak_cpi is None` which never fired (out is pre-seeded with last-good at line ~603) - so CPI sat on stale manual/last-good every run. NEW fetch_pbs_cpi() reads the PCPI_IX series and computes YoY % from the same month a year earlier (VALIDATED: Feb-2026 index 282.39 / 263.95 a year before = 7.0%, the official print) + MoM + the raw index + as-of month. Wired to run UNCONDITIONALLY and OVERWRITE the pre-seeded pak_cpi (manual override in psx_macros_manual.json still WINS - it runs after); sets pak_cpi (YoY %, unchanged basis) + pak_cpi_index/mom/as_of/source. TheGlobalEconomy stays as a cheap first try in case it reverts. NOTE the live YoY (~11.7% for May-2026) will replace the stale figure - CPI is display-only (Tab 12), not in the devaluation basket, so no signal re-baseline is needed. Guarded + returns None on any failure -> falls through to last-good; runner-side. DATA/DISPLAY only -> respects the Sept freeze. Confirm on the runner: a '✓ Pak CPI YoY (PBS live)' line appears and macros.psx.pak_cpi carries the live figure + pak_cpi_source='pbs_sdmx'.  # 1.86.1: (F3 fix - the v1.86.0 live SBP reserves feed never fired) root cause: fetch_psx_macros seeds out=EXISTING.macros.psx.copy() at the top, so out['sbp_reserves'] already carries last-good; the v1.86.0 wire-in was guarded `if out.get('sbp_reserves') is None:` which therefore NEVER ran, and the generic manual loop ALSO pre-set sbp_reserves. FIX: removed sbp_reserves from the manual loop; the reserves block now reads the manual file directly (manual WINS) else fetch_sbp_reserves() runs UNCONDITIONALLY and OVERWRITES last-good (source=sbp_ecodata); reserves history re-baselines ONCE on the basis switch so the manual->live transition cannot fake a weekly move. DATA/DISPLAY only; respects the Sept freeze.  # 1.86.0: (F3 Step 2 - LIVE SBP FX RESERVES FEED, locked from the v1.85.0 dump) fetch_sbp_reserves() reads the sbp.org.pk/ecodata 'Total Reserves' panel (content-locked) -> SBP/bank/total reserves in USD bn + as-of. Guarded; runner-only. DATA/DISPLAY only.  # 1.85.0: (F3 Step 1 - SBP ecodata RAW DUMP, logging-only, dump-then-lock) probe_ecodata_dump() locked the reserves table layout. No data/scoring change. (live SBP FX reserves replacing the manual sbp_reserves lever + feeding the Wave PK-D reserves_fall signal, currently 0 on a flat figure). Before writing the parser, probe_ecodata_dump() dumps the runner's real sbp.org.pk/ecodata structure so we LOCK exactly which of its ~72 tables + which column carries the weekly FX-reserves figure (the page is reachable from the runner but unreachable from the sandbox, so column positions cannot be guessed here - same MTS/MSCI dump-then-lock pattern). Regex-only (no bs4/lxml dependency): logs (a) a one-line map of EVERY table (index, rows x cols, first-row text) and (b) a header+first-rows detailed dump of any table whose text mentions reserves/liquid/foreign-exchange. Gated ECODATA_DUMP_RAW PRE-ARMED True for one run; guarded; the call wrapped in main; never raises; touches NO data/screening/scoring/IM3/TCE -> respects the Sept freeze. NEXT: read the [F3 ecodata dump] block, lock the table+column, build fetch_sbp_reserves() against it, then flip ECODATA_DUMP_RAW False. No data/scoring change this rev.  # 1.84.1: (ops, no logic change) FREE_LEVER_PROBE disarmed back to False now the Wave R Phase-0 verdict is read on the runner: SBP FX reserves (sbp.org.pk/ecodata, HTTP 200, 72 tables + carries 'reserves') and the SBP EasyData portal are BOTH reachable + parseable -> backlog F3 (SBP-reserves fetch) is greenlit (replaces the manual sbp_reserves lever + feeds the Wave PK-D reserves_fall signal, currently 0 on a flat manual figure); PBS CPI returns reachable XML (text/xml, ~26k digits, no <table>) -> a candidate to replace the dead JS-rendered TheGlobalEconomy CPI scrape, exact format to inspect; PBS external-trade URL 404'd (wrong/moved -> needs the correct PBS trade-summary path on a future probe); Finance-Division fiscal + OGRA petroleum are Cloudflare-403 blocked from the runner (dead, same class as the other CF-blocked PSX sites -> fiscal stays manual/last-good). The probe stays in the code, gated off. No data/scoring/screening change; respects the Sept freeze.  # 1.84.0: (Wave R Phase-0 - remaining FREE-LEVER feed reachability/parse probe, logging-only) several PSX macro levers still run on manual / quarterly last-good (psx_macros_manual.json: sbp_reserves, pak_cpi, pak_ca proxy, pak_fiscal). Before committing a parser to any of them (backlog F3 SBP reserves / F4 macros), probe_free_levers() proves ON THE RUNNER which remaining free feeds are reachable + parseable vs Cloudflare-blocked / JS-rendered / moved: SBP FX reserves (sbp.org.pk/ecodata), SBP EasyData portal, PBS CPI, PBS external trade (trade gap = current-account proxy), Finance-Division fiscal operations, and a sector-regulator board sample (OGRA petroleum prices). Logs HTTP status + content-type + size + a parse hint (CF challenge / PDF / JSON / HTML-with-table+digits = likely parseable / thin = likely JS-rendered). URLs are best-guess STARTING POINTS to be refined from the verdict, not asserted feeds. Mirrors probe_scs_reports / probe_bank_data_sources exactly: gated FREE_LEVER_PROBE, each GET guarded (15s), the call wrapped in main, so it can NEVER affect the universe screen, scoring, IM3, the TCE tier or the Sept freeze. PRE-ARMED True (like v1.68.1) so it runs once on the next scan with NO manual edit; read the [Wave R free-lever probe] block in the log, then a follow-up flips FREE_LEVER_PROBE False. Probe-before-build, runner-only answer (the sandbox reaches only github/pypi/npm). No data/scoring change.  # 1.83.0: (Wave PK-D - PSX PKR-DEVALUATION ALERT, scanner half, DISPLAY/DATA-ONLY) the Tab-4 devaluation alert is upgraded from a single on/off line to a multi-signal BASKET scored none/watch/elevated/high (owner Decision 3, 19-Jun-2026). NEW PURE compute_psx_devaluation(psx) reads the PSX macro dict the scanner ALREADY fetches - no new feed, probe-free - and scores five signals, each 0/1/2: (1) rupee slope (USD/PKR rising = PKR weakening, via usd_pkr_mom>2%=1 / >5%=2, or usd_pkr_qoq>5%=1); (2) reserves falling (sbp_reserves_mom<=-5%=1 / <=-10%=2); (3) REER stretch (reer>103=1 / >108=2); (4) SBP policy rate >=11% =1 (the owner's standing defensive line); (5) current-account stress SURFACED but NOT scored by default (pak_ca has no comparable free monthly unit yet -> contributes 0, threshold to calibrate with the owner). Sum -> level: 0=none, 1-2=watch, 3-4=elevated, >=5=high. Thresholds are NAMED MODULE CONSTANTS (PKD_*) for one-line calibration. Attached as data['psx_devaluation']={level,score,max_score(7),as_of,signals{name:{points,value,note}}} in the main flow next to the other PSX overlays; fully guarded + last-good carry; never raises. Current data reads a low-grade WATCH (SBP 11.5%>=11 =1, REER 105.17>103 =1, rupee flat / reserves flat / CA unscored). NEVER touches the universe screen, scoring, IM3 grade, TCE tier, the frozen ledger, or admission -> respects the Sept freeze. The Tab-4 dashboard render (gauge + per-signal rows) is the paired index.html follow-on, shipped separately. Confirm on the runner: [Wave PK-D] logs the level + score + per-signal points, and data.json carries psx_devaluation.  # 1.82.0: (Wave T - vs-index data) the Results tab can show how much each pick/sector BEATS its benchmark (alpha) once the benchmark level is in the history store. KSE-100 was already snapshotted; the S&P 500 was missing. Added FRED 'SP500' (daily close) to fetch_us_macros -> macros.us.sp500 + a 90-day dated sp500_hist; append_history now snapshots sp500 each run AND backfills it onto earlier history rows from sp500_hist (so a pick's first-seen day has an index level). The paired index.html computes vs-index = return-since-recommended minus the benchmark over the same window, per stock and per sector. Display/data-only, guarded/last-good, never touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave T history] rows carry sp500, and macros.us.sp500 is populated.  # 1.81.0: (Wave T shortlist - sector backfill) the US TCE pool mixes screen survivors (carry a TradingView sector) with ETF-consensus large-caps added from the ETF-overlap list (ticker+name+weight only, NO sector), so the big semis (AVGO/MU/NVDA/AMAT/LRCX/WDC) tracked with a BLANK sector and showed no vs-sector comparison on the Results tab. FIX: track_shortlists now builds a ticker->sector backfill map by harvesting every sector-bearing list already in data.json (explosive_us/psx, us/psx_candidates, tce_us/psx, etc.); a tracked name with no sector of its own inherits the sector the rest of the scan already knows (e.g. NVDA/AVGO/MU/WDC = Electronic Technology from the explosive screen). Display/data-only, never fabricated (a name absent everywhere stays blank), never touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: the US TCE HIGH semis now carry a sector + vs-sector figure on the Results tab.  # 1.80.0: (housekeeping) the Pakistan CPI source (TheGlobalEconomy) is now JavaScript-rendered, so the static-HTML scrape can never parse it and was printing two noisy [diag] lines (the SuperJS shell + 'no value parsed') on EVERY run. Quieted: the inflation_annual probe now runs with diag off and, on failure, logs a single concise line ('TheGlobalEconomy now JS-rendered - using manual/last-good') instead of dumping the SuperJS segment. The cheap GET is kept in case the site reverts; the manual/last-good CPI path (psx_macros_manual.json) is unchanged and remains the correct source for this quarterly figure. No data/scoring change.  # 1.79.0: (Wave T shortlist - cover the US Explosive tab) the v1.78.0 runner showed only ~113 rows tracked because explosive_us records carried NO price of their own and the price-map only held the screen names -> most US Explosive picks were skipped (no price, correctly never fabricated). FIX: _build_explosive_rec now carries 'price'=c.get('price') (the scan close already on the candidate), so track_shortlists prices every positively-classified US Explosive name (EXPLOSIVE/QUALITY-GROWTH/INFLECTION) directly off the row. Pure additive display field; no screening/scoring/verdict change -> respects the Sept freeze. (PSX Explosive verdicts finalise in the separate IM3 step that runs AFTER the scanner, so PSX explosive picks are tracked meanwhile via the PSX Screen + PSX TCE tabs; a dedicated PSX-Explosive label is a post-IM3 follow-up.) Confirm on the runner: [Wave T shortlist] row count jumps (US Explosive picks now included).  # 1.78.0: (Wave T - PER-ITEM SHORTLIST PERFORMANCE TRACKER, both markets) NEW track_shortlists(data, EXISTING) stamps the FIRST-seen date + price of every name on every shortlisting tab (US/PSX screen survivors, US Explosive positive-verdict picks, US/PSX TCE HIGH+WATCH) and updates its % return-since each run -> data['shortlist_tracking']['stocks'][TAB|TICKER]={tab,ticker,market,sector,first_date,first_price,last_date,last_price,pct_since,still_listed}. A name dropping off a tab FREEZES at last-known (still_listed=false; never re-fetched = honest fetch-free limit); a name without a price is skipped (never fabricated). SECTORS tracked as a drift-free equal-weight basket = AVERAGE of the per-name returns-since-first-seen of the tracked names in that sector (new entrant joins at 0%, so churn cannot fake a move), labelled 'avg of tracked names' not a sector index. Stored INSIDE data.json (persists via the workflow's existing commit; no new file, no daily.yml change, no extra fetch). Prunes dropped rows >400d old. DISPLAY/DATA ONLY -> never touches screening/scoring/TCE/the frozen ledger -> respects the Sept freeze. The dashboard 'shortlisted on DATE at PRICE, now +X%' column per tab is the paired index.html follow-on. Confirm on the runner: [Wave T shortlist] logs the row + tab + sector-basket counts, and data.json carries shortlist_tracking.  # 1.77.0: (Wave T - rolling DAILY HISTORY STORE, the #1 dashboard gap) NEW append_history(data, EXISTING) snapshots the scan-time-only data points that have NO external series to backfill from (KSE-100, margin-financing total + day-change, USD/PKR, SBP policy rate, gold, WTI, US 10y, DXY, recession score, US/PSX candidate counts, US/PSX TCE-HIGH counts) into data['history'] once per run, deduped by date (last run that day wins), sorted, capped to the last 400 days. Stored INSIDE data.json so it persists via the SAME commit the workflow already makes - no second file, no daily.yml change, no extra fetch for the dashboard. This is the foundation the trend arrows / 200-DMA slope / fund-flow-over-time / self-grading portfolio all depend on. Fully guarded (never raises; carries last-good history on any error). DISPLAY/DATA ONLY -> never touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave T history] logs the date + day-count, and data.json carries a growing 'history' array (one compact row per run-day).  # 1.76.0: (Wave PSX-R Phase-4 MSCI - SHELVED, dead source) the v1.75.0 first-run dump revealed the SCS 'MSCI Provisional Indexes' PDF is a FROZEN 2016/2017 snapshot (its own header: 'calculation date April 19, 2016'; printed 'Monday, March 27, 2017') from Pakistan's one-time 2017 EM upgrade - it lists company NAMES not tickers, carries FY16/FY17 figures, and has NO live additions/deletions section, so it cannot serve as a current index-inclusion catalyst (the v1.75.0 parse correctly ran but produced name-word garbage like 'ADDU'/'BANK'/'CY16' tagged 'added', confirming the source is unusable, not the parser). SCS_MSCI_INGEST=False + MSCI_DUMP_RAW=False: fetch_psx_msci() + _parse_msci() are KEPT but gated OFF, and data['psx_msci'] is forced empty so no stale 2016 names sit in data.json. The genuine live signal (MSCI semi-annual review add/delete announcements from app2.msci.com) is a separate future build, deliberately NOT started. MTS leverage gauge (v1.74.0) unaffected + still live. No screening/scoring/TCE change -> respects the Sept freeze.  # 1.75.0: (Wave PSX-R Phase-4 - SCS MSCI Provisional Indexes, index in/exclusion catalyst, DISPLAY/DATA-ONLY) fetch_psx_msci() parses the SCS 'MSCI Provisional Indexes' PDF (Phase-0 probe-confirmed reachable) into data['psx_msci']={as_of, review_label, added[], deleted[], constituents{tier:[..]}, by_ticker{sym:{tier,status}}, n_added/n_deleted/n_constituents}. A name MSCI will ADD = forced passive INFLOW (bullish catalyst); DELETE = forced passive OUTFLOW (bearish). _parse_msci is a TOLERANT section-tracker (ADDITION/DELETION/CONSTITUENT by header keyword + size-segment tier tag), watermark runs (>=8 chars) stripped, ticker-like tokens minus the report vocabulary. Like MTS the diagonal date-watermark blocks a remote read, so MSCI_DUMP_RAW=True is FIRST-RUN ARMED: this run dumps the runner's real pdfplumber text (first 120 lines) so the exact columns are LOCKED next increment, then the flag flips False. pdfplumber lazy, 7-day throttle (semi-annual review), guarded, last-good carry. NEVER touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave PSX-R MSCI] dumps the raw text + logs added/deleted/constituents, and data.json carries psx_msci.  # 1.74.0: (Wave PSX-R Phase-3 MTS - LEVERAGE GAUGE CORRECT) root-caused the v1.72/1.73 wrong total: the MTS Daily Report stacks TWO tables keyed by the SAME symbols - 'MTS Net Open MTS Amount' (Rs) then 'MTS Net Open MTS Volume' (shares) - so by_ticker[sym]=... let the Volume table OVERWRITE the Amount table (parsed values were share counts: BOP showed 75.899 = its 75,899,282 volume/1e6, not Rs 2,525.8mn). FIX: _parse_mts now tracks the section and ingests ONLY the Amount table (stops at the Volume header), and reads the report's own 'Total Amount <today> <prev>' row as the authoritative market leverage total (Rs 28.75bn on 6-Feb), cross-checked against the per-symbol sum (market.sum_check_mn). MTS_DUMP_RAW disarmed. NEVER touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: total ~Rs 28,700mn across 56 symbols, top financed NBP/BOP/PSO/HUBC/HBL.  # 1.73.0: (Wave PSX-R Phase-3 MTS - diagnostic re-dump) the v1.72.0 run parsed 56 symbols + wavg rate 12.61%% (correct) but total Rs 465.5mn is IMPLAUSIBLE - the v1.71.0 dump showed BOP alone at Rs 2,525.8mn (HBL/HUBC/FFC each >1,000mn), so the per-symbol AMOUNT is being truncated on the full live text. This rev does NOT claim a fix: it re-arms MTS_DUMP_RAW (now 120 lines, 220 wide, watermark-run lines filtered out) + logs a DIAG line of the parsed mts_amount_mn for the first 15 symbols, so the raw big-number rows + their parsed values come back together on one run to root-cause the truncation. Still DISPLAY/DATA-ONLY; respects the Sept freeze.  # 1.72.0: (Wave PSX-R Phase-3 - MTS parser LOCKED to the real layout) the first v1.71.0 runner dump revealed each MTS Daily Report data row is '<S.No> <SYMBOL> <MTS Amount Rs> <prev Rs> <Change%> [wtd-rate wtd-rate-prev share% share%-prev Category]' - i.e. rows START WITH THE SERIAL NUMBER not the symbol (so the v1.71.0 tolerant parser matched ~0 rows) and the MTS Amount is in FULL RUPEES = the per-stock outstanding margin financing. _parse_mts rewritten: positional leading-field regex (rank/symbol/amount/prev/change), trailing rate+share columns parsed tolerantly with the diagonal date-watermark (>=8-char runs) stripped; data['psx_mts']={as_of, market{total_mn (SUM of the Amount column = the market-wide leverage gauge), total_prev_mn, net_change_mn, change_pct, wavg_rate, n_symbols}, by_ticker{sym:{mts_amount_mn, mts_amount_prev_mn, change_pct, rate, share_pct, category}}, top_financed[15 by amount], last_fetch_utc}. MTS_DUMP_RAW disarmed. NEVER touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave PSX-R MTS] logs total Rs mn + n symbols + top financed.  # 1.71.0: (Wave PSX-R Phase-3 - SCS MTS leverage gauge, DISPLAY/DATA-ONLY) fetch_psx_mts() parses the SCS 'MTS Daily Report' PDF (REP-033, daily; Phase-0 probe-confirmed reachable) into data['psx_mts']={as_of, market{total_investment_mn/net_investment_mn/total_volume/wavg_rate/scrips, best-effort label-anchored}, book[symbols carrying MTS positions = leverage breadth], by_ticker{sym:{nums[]}} raw, last_fetch_utc}. The market-wide MTS investment total is the leverage gauge (rising = froth/risk, collapsing = de-risk); the per-symbol Rs-value column mapping is locked NEXT increment from the first-run RAW dump (MTS_DUMP_RAW=True logs the runner's real pdfplumber text, since a heavy date-watermark blocked a remote read of the table layout - the parser is built layout-tolerant + fails safe to empty/last-good rather than guess column positions). pdfplumber lazy, guarded, last-good carry. NEVER touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave PSX-R MTS] logs the as-of + market totals + book size, dumps the raw table text once, and data.json carries psx_mts.  # 1.70.0: (Wave PSX-R Phase-2a - SCS watchlist SUGGESTION list, DISPLAY/DATA-ONLY) fetch_psx_valuation_matrix now also emits psx_valuation_matrix['suggested']: the >=2-quality-screen names filtered to liquid + non-mega (excludes PSX_MEGACAPS) + non-bank (bank sections or _is_true_bank), each carrying P/E, expected P/E, div_yield, ROE/ROA/EBITDA-margin, mkt_cap_bn, avg_volume, on_watchlist flag, thin_volume flag, ranked by quality-screen count then dividend yield. A pre-v1.70.0 cached overlay (no 'suggested' key) forces ONE re-fetch past the weekly throttle so the list appears immediately, then the throttle resumes. Per build-plan rule rev 2.5 this is a SUGGESTION the owner reviews — it is NEVER auto-added to psx_watchlist.json (the dashboard renders it on Tab 7 as 'review to add'). No screening/scoring/TCE change -> respects the Sept freeze.  # 1.69.0: (Wave PSX-R Phase-1 - SCS Valuation Matrix overlay, DISPLAY/DATA-ONLY) fetch_psx_valuation_matrix() parses the SCS 'Pakistan Market Valuation Matrix' PDF (REP-033, weekly; Phase-0 probe-confirmed reachable) into data['psx_valuation_matrix']={by_ticker:{price,eps,latest/expected P/E,div_yield,mkt_cap_bn,roe,roa,ebitda_margin,ev_ebitda,pb,nim,perf_1m/3m/6m/12m, sections[]}, sections:{tag:[tickers]}, as_of, quality_seed}. Row parser anchors on the EPS-basis period token (3M/6M/9M/12M) so it survives the per-section column shifts (EV/EBITDA drops the DY col, etc.); the section metric is the row's last token. quality_seed = names in >=2 of the ROE/ROA/EBITDA-margin/DY screens (PREVIEW of the auto-watchlist seed; wiring to psx_watchlist.json is the NEXT increment). pdfplumber lazy, weekly throttle, guarded, last-good carry. NEVER touches screening/scoring/TCE -> respects the Sept freeze. Confirm on the runner: [Wave PSX-R valmatrix] logs N tickers + sections + the quality-seed list, and data.json carries psx_valuation_matrix.  # 1.68.2: (ops, no logic change) SCS_REPORT_PROBE disarmed back to False now the Wave PSX-R Phase-0 verdict is read — all 4 SCS report PDFs (Valuation Matrix / MTS / MSCI Provisional / News Briefs) confirmed reachable + pdfplumber-parseable from the runner; F5 watchlist confirmed live (8/8 names force-included, PSX universe 41->48). The probe stays in the code, gated off; re-arm only to re-confirm reachability.  # 1.68.1: (ops, no logic change) SCS_REPORT_PROBE pre-armed True so the Wave PSX-R Phase-0 SCS report-PDF probe runs on the next scan WITHOUT a manual edit; the F5 watchlist diagnostic (v1.68.0) is also active. Revert to False is handed back as a follow-up build once the verdict is read.  # 1.68.0: (F5 watchlist diagnostic, logging-only) fetch_psx_universe_live now logs whether psx_watchlist.json loaded + which of its tickers are present in the top-500 mcap-desc pakistan/scan rows (force-included) vs absent (silently skipped) -> resolves whether a watchlist name not surfacing is a not-deployed file, a not-in-top-500 coverage gap, or working. No screening/scoring change; respects the Sept freeze.  # 1.67.0: (Wave PSX-R Phase-0 - SCS report-PDF probe, logging-only) probe_scs_reports() tests ON THE RUNNER whether the SCS research PDFs that would feed the PSX budget/reports overlay are reachable + parseable BEFORE any parser is built: Valuation Matrix (per-name P/E, div yield, ROE, ROA, EBITDA margin, EV/EBITDA, P/B, bank NIM), MTS Report (margin-financing leverage gauge), MSCI Provisional Indexes (index inclusion/exclusion catalyst), News Briefs. Logs HTTP status/content-type/size + a parse hint (valid %PDF magic + whether pdfplumber page-1 text carries the expected keyword -> parseable, vs Cloudflare-blocked / non-PDF / image-only). Gated SCS_REPORT_PROBE=True (flip False after reading). Mirrors probe_bank_data_sources; each GET guarded; cannot affect the universe screen, scoring, or the Sept TCE freeze. NOTE the consuming overlay uses the budget tax map strictly as a SECTOR-LEVEL 'budget favoured' indicator (sector selection only, NEVER stock selection/scoring) per the 18-Jun-2026 owner directive.  # 1.66.0: (F2 closed) FRED _fred_series retry now covers TRANSIENT failures (timeouts / connection drops / 5xx), not just 429 rate-limits — a transient timeout previously raised immediately and fell to last-good without retrying. Non-transient errors (bad series id, auth) still raise straight to last-good. Throttle + 3-attempt backoff + per-series last-good unchanged. No data-semantics change.  # 1.65.0: (de-personalisation) dashboard no longer references a personal portfolio. PSX_HOLDINGS -> PSX_MEGACAPS, reframed as merit-based KSE-30 mega-cap coverage above the scan band; us_large_cap_set comment reframed from '+ holdings' to sector-representative mega-caps. NO ticker/universe/screening/scoring/TCE-pool change — SAME names force-included exactly as before, only labels change, so the frozen prediction pool is byte-for-byte unchanged (respects the Sept freeze).  # 1.64.1: (PSX breadth fix) v1.64.0 logged '[PSX sector breadth] 0 sectors' because the POST requested only 3 columns [sector, close, SMA200] while the shared parse_tv_scan drops any row with len(d)<4 (the core price/volume/mcap guard) -> every row discarded. FIX: request a 4th column ('name') so the rows survive the parser; aggregation unchanged. TV does classify PSX names into sectors (Finance/Energy Minerals/Process Industries/Utilities...) and carries SMA200, confirmed on the candidates, so PSX breadth now populates. # 1.64.0: (Wave M-A step 2b — PSX SECTOR BREADTH) the US sector breadth (v1.63.0) rode the broad america medians POST, but the PSX screen band is only ~41 names — far too thin per sector. NEW fetch_psx_sector_breadth(): ONE isolated pakistan/scan POST over the top-600-by-mcap (the FULL listed universe, not the 3-60bn screen band), columns [sector, close, SMA200], grouping by TV sector to compute the % of each PSX sector at/above its 200-DMA -> data['psx_sector_breadth']={sector:{pct,n,above}}; >=5 names per sector required (else omitted as thin — concentrated PSX sectors like Fertilizer/E&P may still drop out, honestly). Own request -> the main universe scan is untouched; {} on any failure carries last-good. Additive/best-effort; no screening/scoring change; respects the Sept TCE freeze. Confirm on the runner: [PSX sector breadth] logs N sectors and data.json carries psx_sector_breadth. # 1.63.0: (Wave M-A step 2b — US SECTOR BREADTH) Wave M-A step 1 gave every NAME a price-vs-200-DMA read but a SECTOR could still read 'favored' on regime/Zacks/COT while most of its names were below their own 200-DMA (a weak sector dressed up by a couple of mega-caps). fetch_sector_medians already does ONE broad america/scan POST (~2000 large-caps) grouped by GICS sector for the peer-relative medians, so SECTOR BREADTH rides that SAME POST at zero extra network cost: added 'close' + 'SMA200' to _SECTOR_MED_COLS and, per sector, counts how many names trade at/above their 200-DMA -> breadth_200dma (% above, the standard market-breadth gauge) + breadth_n on each sector in sector_medians.json, and a clean top-level data['sector_breadth']={sector:{pct,n,above}} for the dashboard. >=5 names required per sector (else omitted -> the dashboard shows 'thin'). US-only: the 41-name PSX scan is too thin per sector for a real breadth read (deferred, honest). Additive/best-effort: failure carries last-good; cannot affect screening, scoring, the medians im3 already consumes (extra keys ignored), or the Sept TCE freeze. DEFERRED still: 200-DMA SLOPE needs run-over-run history (Wave T store). Confirm on the runner: the [sector medians] log line also reports breadth, and data.json carries sector_breadth. # 1.62.0: (Wave M-A step 1 — moving-average DATA, both markets) the dashboard had NO price-trend lever anywhere, so a sector could read 'favored' while its price was in a confirmed downtrend. Added SMA50 + SMA200 as columns to BOTH the US america/scan (_US_TV_COLS, used by the band scan + fetch_us_large_fundamentals) and the PSX pakistan/scan (PSX_SCAN_COLS; also carried on the per-candidate analyst row), and a PURE _ma_reads(price, sma50, sma200) helper that derives the per-name reads: above_200dma (the primary institutional trend filter), cross (golden/death = SMA50 vs SMA200), sma50/sma200, and ext_200_pct (% above/below the 200-DMA, a mean-reversion flag). Carried as c['ma'] onto the US candidate (_candidate_from_tv), the PSX candidate (screen_psx_stock, from the analyst row's SMA + scan close), and EVERY explosive record (_build_explosive_rec). One extra TV column per POST; no per-name history fetch; additive; cannot affect screening/scoring; respects the Sept TCE freeze. DEFERRED to later M-A increments (honest separation): 200-DMA SLOPE needs run-over-run history (the Wave T rolling-history store), and SECTOR BREADTH (% of a sector above its 200-DMA) needs a universe aggregation; the dashboard MA chip + the sector-stance wiring (Wave S / US sector practice) are the paired index.html follow-on. Confirm on the runner: explosive_us / explosive_psx rows + the candidate dicts carry a populated 'ma' block (above_200dma / cross / ext_200_pct). # 1.61.0: (KSE-100 official-close fix) the dashboard showed a wrong/stale KSE-100 (178182 when the real close was 180232) every scan because fetch_kse100 read ONLY dps.psx.com.pk/timeseries/int/KSE100 — an INTRADAY series whose LAST tick under-reports the official session close, and the dps `eod` index series is frozen at 2021. FIX: fetch_kse100 now takes the OFFICIAL CLOSE from TradingView (PSX:KSE100 via the pakistan/scan symbols-POST), dps int/eod fallback, then last-good; plus a psx_macros_manual.json 'kse100' manual override that wins. CONFIRMED LIVE. # 1.60.0: (Wave A / V-G-M momentum data) added Perf.6M + Perf.3M to the US TV scan columns and carried perf_6m/perf_3m onto the US candidate + every explosive record. # 1.59.0: (Wave A / A4 — VAL-IND: Explosive screen gates -> indicators, scanner half) per the A4 decision, NOTHING on the Explosive/Multibagger tabs should EXCLUDE or demote a name; strength signals are INDICATORS that annotate. (1) classify_explosive: cash-backing REMOVED from the EXPLOSIVE gate — a growth+acceleration name is EXPLOSIVE regardless of whether reported cash backs earnings (NVDA/LLY/AMSC/MGRT were being demoted to 'QUALITY-GROWTH (cash flow does not back earnings)', exactly the early winners these tabs exist to surface). The retired demotion verdict string is no longer produced. (2) each record now carries indicators{growth,acceleration,pbt_accel,cash_backed,op_declining} + a 0-4 strength_score + cash_backed, so the dashboard can rank-and-annotate instead of filter. (3) the explosive list now SORTS by strength_score (strongest early movers first) rather than an EXPLOSIVE-gate-first key, so weaker-signal names rank lower but are never dropped. signal_a/signal_b/conditions/verdict kept for dashboard back-compat. EFFECT: US EXPLOSIVE count rises (the cash-demoted growth+accel names rejoin); cash-backing visible as an indicator chip. The Explosive screen is separate from the Sept-frozen TCE engine. PAIRED FOLLOW-ON (A4 part 2, index.html): render ALL candidates ranked by strength_score with indicator chips + valuation as CONTEXT (never a filter), so the tab truly gates nothing. Confirm on the runner: NVDA et al. now read 'EXPLOSIVE — both signals' with cash_backed=false shown; explosive_us rows carry strength_score + indicators. # 1.58.3: (TCE news double-count fix) s1_news (>=3 Google-News articles/14d) and s2_sponsor (>=8) were two thresholds on the SAME count, so s2 IMPLIES s1 and a well-covered name added +2 to `total` from ONE signal ("sponsor" is a misnomer — no sponsorship/ownership data feeds it). s2_sponsor REMOVED from ATTENTION/COUNTED so news counts ONCE (s1_news); s2_sponsor stays a DISPLAY-ONLY heavy-news flag (always present, default 0) but never enters total/conviction. Conviction sets untouched -> US HIGH (pure conv>=4) UNAFFECTED; the double-count only fed `total`, which gates PSX (HIGH=conv>=2 AND total>=5) + one US WATCH clause (total>=5 AND conv>=1). LIVE EFFECT: the lone PSX HIGH TPL (total=5 conv=2 incl. s1+s2) drops to total=4 -> WATCH; a few thin US names may shift IGNORE->WATCH off. CONFIRMED-BUG fix taken DURING the TCE freeze on purpose — maturing 163 predictions through a known double-count corrupts the very backtest the freeze protects. Any open TPL HIGH prediction logged pre-1.58.3 is a known artifact; TPL logs WATCH going forward (one-time ledger prune of that entry available on request). # 1.58.2: (version-aware IM3 carry-forward) the per-record IM3 carry-forward (v1.21.3/v1.49.0) re-attached ANY last-good im3 dict regardless of the engine version that produced it, so a name deep-scored once and then dropped from the daily.yml re-score set (explosive/financial/TCE-HIGH) kept its grade FOREVER — e.g. 13 NOT-EXPLOSIVE rows (XZO/EFC/RILY/ATLC/EZPW/NEWT/ADAM/VEL/BX/LTC/GOLD/SKYH/WELL) were still showing a frozen 2.9.1 grade on the v2.14.4 board while every other NOT-EXPLOSIVE row correctly showed Pending. FIX: the harvest now reads the CURRENT im3_score.py IM3_VERSION (clean regex on the `IM3_VERSION = "x"` line — NOT daily.yml's `.strip('"\'')`, which leaves the trailing inline comment attached and would mismatch every ver -> blank the whole board, the v1.49.0 PSX-blank regression) and re-attaches ONLY ver-matched scores; a stale-version score is dropped to None -> re-scored fresh this same run by the daily.yml self-heal (missing_im3) if the name is still in the re-score set, else it shows an honest Pending consistent with its peers. FAIL-SAFE: if the version can't be read (file absent / no match) _cur_im3_ver=None -> EVERY score is carried = pre-1.58.2 behaviour, so the guard can never itself blank a score. Current-version scores carry exactly as before (no churn). Confirm on the runner: the carry-forward logs a 'Dropped N stale-version' line on the first v1.58.2 run, the 13 stale 2.9.1 rows clear to Pending (or a fresh 2.14.4 if in the re-score set), and the im3.ver histogram collapses to a single current version + None. # 1.58.1: (dead-ticker prune) removed five DELISTED names from the named large-cap dict — completed acquisitions that 404 on the Yahoo gap-fill every run: HES (Hess->Chevron), PXD (Pioneer->ExxonMobil), MRO (Marathon Oil->ConocoPhillips) from Energy; PARA (Paramount->Skydance/PSKY) and IPG (Interpublic->Omnicom/OMC) from Communication Services. Successors CVX/XOM/COP + OMC are already in the list (CVX/XOM/COP are holdings); PSKY intentionally NOT added (watchlist decision left to the owner). Stops the recurring 404 noise + the wasted per-name Yahoo gap-fetch. No screening/scoring logic change. # 1.58.0: (Option C — peer-relative IM3, scanner half) NEW fetch_sector_medians(): one ISOLATED america/scan POST computes per-GICS-sector MEDIAN trailing P/E + operating margin + net margin + ROE over a broad sample, written to sector_medians.json (+ data['sector_medians']). im3_score v2.13.0 scores those four metrics PEER-RELATIVE off this file, falling back to its absolute thresholds for any sector/name without a median (so Yahoo + PSX scoring is unchanged). Own request/parse, guarded, last-good carry — cannot corrupt the universe screen. # (older changelog entries trimmed for length; see prior versions in git history) (TCE news double-count fix) s1_news (>=3 Google-News articles/14d) and s2_sponsor (>=8) were two thresholds on the SAME count, so s2 IMPLIES s1 and a well-covered name added +2 to `total` from ONE signal ("sponsor" is a misnomer — no sponsorship/ownership data feeds it). s2_sponsor REMOVED from ATTENTION/COUNTED so news counts ONCE (s1_news); s2_sponsor stays a DISPLAY-ONLY heavy-news flag (always present, default 0) but never enters total/conviction. Conviction sets untouched -> US HIGH (pure conv>=4) UNAFFECTED; the double-count only fed `total`, which gates PSX (HIGH=conv>=2 AND total>=5) + one US WATCH clause (total>=5 AND conv>=1). LIVE EFFECT: the lone PSX HIGH TPL (total=5 conv=2 incl. s1+s2) drops to total=4 -> WATCH; a few thin US names may shift IGNORE->WATCH off. CONFIRMED-BUG fix taken DURING the TCE freeze on purpose — maturing 163 predictions through a known double-count corrupts the very backtest the freeze protects. Any open TPL HIGH prediction logged pre-1.58.3 is a known artifact; TPL logs WATCH going forward (one-time ledger prune of that entry available on request). # 1.58.2: (version-aware IM3 carry-forward) the per-record IM3 carry-forward (v1.21.3/v1.49.0) re-attached ANY last-good im3 dict regardless of the engine version that produced it, so a name deep-scored once and then dropped from the daily.yml re-score set (explosive/financial/TCE-HIGH) kept its grade FOREVER — e.g. 13 NOT-EXPLOSIVE rows (XZO/EFC/RILY/ATLC/EZPW/NEWT/ADAM/VEL/BX/LTC/GOLD/SKYH/WELL) were still showing a frozen 2.9.1 grade on the v2.14.4 board while every other NOT-EXPLOSIVE row correctly showed Pending. FIX: the harvest now reads the CURRENT im3_score.py IM3_VERSION (clean regex on the `IM3_VERSION = "x"` line — NOT daily.yml's `.strip('"\'')`, which leaves the trailing inline comment attached and would mismatch every ver -> blank the whole board, the v1.49.0 PSX-blank regression) and re-attaches ONLY ver-matched scores; a stale-version score is dropped to None -> re-scored fresh this same run by the daily.yml self-heal (missing_im3) if the name is still in the re-score set, else it shows an honest Pending consistent with its peers. FAIL-SAFE: if the version can't be read (file absent / no match) _cur_im3_ver=None -> EVERY score is carried = pre-1.58.2 behaviour, so the guard can never itself blank a score. Current-version scores carry exactly as before (no churn). Confirm on the runner: the carry-forward logs a 'Dropped N stale-version' line on the first v1.58.2 run, the 13 stale 2.9.1 rows clear to Pending (or a fresh 2.14.4 if in the re-score set), and the im3.ver histogram collapses to a single current version + None. # 1.58.1: (dead-ticker prune) removed five DELISTED names from the named large-cap dict — completed acquisitions that 404 on the Yahoo gap-fill every run: HES (Hess->Chevron), PXD (Pioneer->ExxonMobil), MRO (Marathon Oil->ConocoPhillips) from Energy; PARA (Paramount->Skydance/PSKY) and IPG (Interpublic->Omnicom/OMC) from Communication Services. Successors CVX/XOM/COP + OMC are already in the list (CVX/XOM/COP are holdings); PSKY intentionally NOT added (watchlist decision left to the owner). Stops the recurring 404 noise + the wasted per-name Yahoo gap-fetch. No screening/scoring logic change. # 1.58.0: (Option C — peer-relative IM3, scanner half) NEW fetch_sector_medians(): one ISOLATED america/scan POST computes per-GICS-sector MEDIAN trailing P/E + operating margin + net margin + ROE over a broad sample, written to sector_medians.json (+ data['sector_medians']). im3_score v2.13.0 scores those four metrics PEER-RELATIVE off this file, falling back to its absolute thresholds for any sector/name without a median (so Yahoo + PSX scoring is unchanged). Own request/parse, guarded, last-good carry — cannot corrupt the universe screen. # 1.57.1: (P7 bootstrap fix) the weekly Zacks skip is now honored ONLY when a per-ticker zacks_ranks map already exists to carry forward. On the first v1.57+ run EXISTING has no map (prior versions discarded the per-name rank), so the skip used to leave zacks_ranks={} and NO ⚡Z chip could appear until the 7-day window happened to open. FIX: force one bootstrap scrape when the map is absent; thereafter the carry-forward resumes. # 1.57.0: (P7 — Zacks Rank on the US Explosive tab, the item the owner surfaced) fetch_zacks_sectors now ALSO returns a per-ticker {ticker: zacks_rank 1..5} map (it already scraped each survivor's rank via quote-feed.zacks.com but discarded the per-name value, keeping only sector aggregates + the ETF Zacks-confirmed flag). data['zacks_ranks'] persists it MERGED over the prior run (last-good carry — the scrape is weekly), and each US explosive_us record is joined with r['zacks_rank']. US ONLY (Zacks has no PSX coverage). index v5.38 renders a Zacks #1/#2 chip. No screening/scoring change — additive display join. Confirm on the runner: explosive_us rows carry zacks_rank and the data['zacks_ranks'] map is populated after a fresh weekly scrape. # 1.56.0: (A — SCS->IG2 fallback) write_bank_ig2_overrides() derives roe/adr/roa-trend from the live SCS snapshot -> bank_ig2_overrides.json, which im3_score v2.12.0 FILLS-MISSING into the IG2 inputs (curated full-data banks never overwritten -> the nine workbook banks unchanged; only partials BOP/AKBL/BIPL lift off the /32 denominator, e.g. roe now scored). roe/adr stored as fractions, roa-trend = avg(last3)/avg(last5) of the 5yr ROA series. DISPLAY snapshot unchanged; audited annual data (B) will take precedence over SCS when sourced. No screening change. # 1.55.4: (Wave Q snapshot parser-version guard) v1.55.3's mapping rework was throttle-skipped because the prior run had already cached 12 banks in the OLD raw format (<24h), so the new map never ran. FIX: bank_snapshot now carries _parser_ver (=3); the 24h throttle is honored ONLY when the cache was written by the CURRENT parser -> a parse-format change forces exactly one re-fetch, then the throttle resumes. has_cached/n adjusted for the extra meta key. No scoring change. 1.55.3: (Wave Q SCS mapping locked) the v1.55.2 run validated the SCS Highcharts series: the ABBREVIATED 'Ret On Equity'=15.03 / 'Ret On Assets'=0.79 / 'ADR'=35.96 are EXACT matches to AKBL's known ROE/ROA/ADR (the v1.55.2 'MISMATCH' was a false alarm — the validator matched the full-name 'Return On Equity'=31.78, a different basis, now intentionally unmapped). fetch_bank_snapshot now maps the validated series via _SCS_METRIC_MAP -> data['bank_snapshot'][t]={roe,roa,adr,cash_deposits,equity_advances,cash_per_share, series:{5yr arrays}, as_of} (price/index n=120 + 0.0-not-populated dropped). DISPLAY/CONTEXT only — still NOT the IG2 scoring series (that stays manual / the annual-report PDF parser). 1.55.2: (Wave Q throttle fix) the v1.55.0 0-parse run stamped bank_snapshot's 24h clock with NO cached banks, so v1.55.1's reworked Highcharts parser was throttle-skipped (carrying an empty last-good). FIX: both bank overlays now honor the skip ONLY when real cached data exists (has_cached), and a 0-parse/<2-field run returns the prior cache WITHOUT a fresh _fetched_utc stamp -> it retries next run instead of self-blocking for 24h/30d. No scoring change. 1.55.1: (Wave Q Phase-1a - SCS snapshot reworked to Highcharts series) the v1.55.0 label parser found 0 fields because the runner's raw HTML carries SCS metric history as Highcharts JS data arrays (the rendered ratio tables are client-side only); fetch_bank_snapshot now extracts those series via _scs_highcharts_series -> data['bank_snapshot'][t]={series:{name:[..]}} as RAW display data, logs a per-bank metric map + validates the array basis/order against AKBL's known ROE (15.03) before any field is trusted/mapped (deferred to v1.56). KPMG sector layer unchanged (live, 8/8 fields). Still DISPLAY/CONTEXT only; no scoring change. 1.55.0: (Wave Q Phase-1 - bank-data overlays: SCS snapshot + KPMG sector) TWO additive DISPLAY/CONTEXT overlays, both guarded/last-good/never-break, NEITHER writes the audited IG2 scoring series. (a) fetch_bank_snapshot: SCS Trade per-bank CURRENT-YEAR fields (server-rendered, runner-confirmed 6/6) -> data['bank_snapshot'] for the dashboard + a data-quality cross-check vs the manual IG2 ADR; label-anchored extraction FAILS SAFE (None, never a wrong value, if SCS groups labels/values) with a first-run raw-HTML diag; throttled 24h. (b) fetch_bank_sector_kpmg: KPMG Banking Perspective SECTOR aggregates (profit +8.2%/assets +14.9%/deposits +7.9%/NPL +12%/ECL-on-NPL 88%, FY2024, 21 banks + fiscal/KSE backdrop) -> data['bank_sector'] for a SECTOR-EVALUATION read, NEVER a per-bank input; pdfplumber lazy; throttled 30d. Probe (BANK_SOURCE_PROBE) flipped False — verdict read: all 3 reachable from the runner, SCS history is JS-empty so the 6yr series stays manual / the annual-report PDF parser (next). No screening/scoring change. 1.54.0: (Wave Q Phase-0 - bank-data source reachability probe, logging-only) probe_bank_data_sources() tests ON THE RUNNER whether the three user-named bank-data sources are reachable+parseable before any IG2-input parser is built: SCS Trade SNAPSHOT (server-rendered current-year fields EPS/ROE/ROA/book-value->equity/CFO-per-share/ADR/equity-to-assets -> a gap-filling overlay), SCS Trade Yearly Financials/Ratios (expected JS-empty shell -> the 6yr CAGR/trend series is NOT free over a plain fetch, already confirmed from sandbox), a sample annual-report PDF (BOP 2024 six-year highlights via pdfplumber), and the KPMG Pakistan Banking Perspective PDF EARMARKED FOR SECTOR EVALUATION ONLY (industry CAR/NIM/NPL/ROE medians), never a per-bank input. Logs HTTP status/content-type/size + a role-specific parse hint; each GET guarded; gated BANK_SOURCE_PROBE=True (flip False after reading). Manual bank_ig2_inputs.json stays authoritative; no screening/scoring change. 1.53.0: (PSX bank-merit admission) derive_psx_candidates now admits EVERY true bank present in the mcap-desc pakistan/scan rows (top-500 -> the large listed banks like UBL/MEBL/BOP are in it) with a valid liquid quote, via _is_true_bank (sector/name/known-ticker). This is MERIT, not force-inclusion of named tickers: the EXPLOSIVE gates are industrial income-statement mechanics (revenue/OP growth, NP acceleration, CFO>=NP) that a bank's accounts structurally lack, so a bank can never pass them and is carved to the System-B bank model regardless — admitting all banks lets their System-B score rank them (weak banks score low and sort to the bottom). Additive: non-bank derivation + the holdings/F5 paths are unchanged. Banks not in psx_financials.json score System-B on the thin free feed (NIM/CASA/CAR NA) until broker disclosure lands. 1.52.0: (Track 2 — explosive forward leg + PSX broker-data slots) THREE additive changes, all guarded / no-op when their config file is absent. (1) P2b F1/FR WIRING FIX: fetch_us_analyst_block is now called over the UNION of the TCE pool AND the explosive survivors, and each survivor gets c['analyst_row']+c['prev_fwd_eps'] — previously only the pool carried analyst rows, so _forward_boost read a missing analyst_row and returned F1/FR=None on EVERY explosive record; the forward booster now actually fires (F1 fwd-EPS-growth>20%, FR estimate-raised), still additive and never blocks. One POST, no extra network cost. (2) F4 MANUAL-OVERRIDE: fetch_psx_macros reads an optional psx_macros_manual.json FIRST (reer / pak_ca / pak_fiscal / pak_cpi / sbp_reserves) — manual values WIN over the TE best-effort fetch + last-good (these slow PSX macros have no free monthly feed; update quarterly from the AKD/Topline economy report). (3) F5 CONFIGURABLE WATCHLIST: an optional psx_watchlist.json (Topline/AKD/AHL conviction tickers, bare list or {"psx_watchlist":[...]}) is force-included into derive_psx_candidates exactly like PSX_MEGACAPS, so broker-conviction names are always screened even when TV's mcap-desc top-500 misses them. F2/FA forward conditions DEFERRED — no spec definition exists yet, not invented. Confirm on the runner: explosive records now carry forward{f1,fr} that are not all-None, and psx_macros_manual.json / psx_watchlist.json take effect the moment they exist in the repo root. 1.51.2: (Track 2 — D4: A1 OPNP ratio threshold 1.5 -> 1.0) the deck defines OPNP literally as 'net profit rises faster than operating profit' = ratio>1.0; the 1.5 was the scanner's own undocumented calibration (flagged in the explosive audit, never in the spec). No worldwide analyst convention exists for a NP/OP-growth ratio cutoff — the standard concepts are positive operating leverage (boundary >1.0), DOL (descriptive), absolute EPS-growth bars (not a ratio), and earnings quality via cash conversion (already enforced by C1/C3 cash-is-king + the Q1 guard). Effect on data__24: US EXPLOSIVE 9->17, PSX 0->3 (GAL/GHNI/THCCL, ratios 1.43-1.49); other gates (rev>20%, op>20%, cash-is-king) keep it selective. 1.51.1: (Track 2 — Explosive follow-up: true-bank carve + honest PSX PARTIAL) bank carve-out NARROWED to actual banks via _is_true_bank (name tokens + known-bank set + sector=banks) because TradingView lumps ALL financials under sector='Finance' (banks, REITs, royalties, insurers, asset mgrs) — so non-bank financials (REITs/royalties/asset mgrs) now STAY in the screen scored on real numbers instead of being mis-routed to the bank model; only true banks (e.g. MCB) carve out. PSX explosive names lack operating/net-profit growth at scan time, so instead of asserting NOT-EXPLOSIVE they are marked 'PARTIAL — profit/cash data pending (IM3)' and FINALISED in the PSX IM3 step from the same statements IM3 already parses (design-faithful: same canonical conditions both markets, fed real data — NO eps/rev proxy). US scan-time path unchanged. Confirm on the runner: PSX explosive shows PARTIAL pre-IM3 then real verdicts post-IM3; only true banks carved; REITs/royalties no longer in the bank bucket. 1.51.0: (Track 2 — Explosive screen rebuilt to Spec v1.1) run_explosive/score_explosive_candidate replaced: revenue gate raised to >20%% (G1/D2); op/np growth wired both markets; added A2/OPPBT (PBT/OP>1.0) + cash-is-king C1 CFONP (CFO>=NP, lazy cashflow fetch only for provisional-EXPLOSIVE US names) + C3 SCFOSNP (sum CFO>=sum NP); declining (OP<=0) now a computed 'NOT EXPLOSIVE — OP declining' and the prev-OP<=0 turnaround case is A1=False not None, so INSUFFICIENT DATA is reserved for genuinely-missing inputs only (US 63->~0, PSX 16->~0); bank/financial carve-out extended to BOTH markets via _looks_like_bank (PSX MCB now routed to bank model); F1 (fwd EPS growth>20%%) + FR (estimate raised) additive booster via analyst_row, never blocks; record gains conditions{g1..c3}/forward{f1,fr}/pbt_growth, keeps signal_a(=G1&G2)/signal_b(=A1) for dashboard back-compat. Explosive screen is separate from the Sept-frozen TCE engine. Confirm on the runner: INSUFFICIENT DATA ~0 both markets, MCB shows FINANCIAL->bank model, US EXPLOSIVE ~10-13. 1.50.0: (Track 2 — transient-fetch hardening) NEW reusable _retry_get(url, *, tries=3, base=1.0, **kw) wraps requests.get with retry-on-transient-error + exponential backoff (1s/2s/4s), retrying ONLY requests.exceptions.Timeout / ConnectionError and re-raising on the final attempt so each caller's existing try/except -> last-good fallback is unchanged (success path identical to a bare requests.get). Applied to the three single-shot flappers that had no retry: the SBP policy-rate page (sbp.org.pk/m_policy, which intermittently times out) and both CFTC COT endpoints (publicreporting.cftc.gov TFF $limit=100 + disaggregated Crude $limit=200). FRED already had its own 429 retry (v1.11) and is untouched. No new sources, no scoring/threshold change, respects the Sept freeze. Confirm on the runner: SBP/COT lines still log ✓ on a good run, and a transient timeout now self-recovers instead of dropping to last-good. 1.49.0: (PSX IM3 carry-forward fix) the per-record IM3 carry-forward (v1.21.3) looped US keys ONLY (explosive_us, tce_us), so on any run where the separate im3_score.py step was skipped — e.g. a bare `python scanner.py` — the rebuilt explosive_psx/tce_psx/psx_candidates carried no 'im3' and the dashboard PSX IM3 column blanked every PSX row to "Pending next scan" (US survived because it was in the loop). FIX: carry IM3 forward per-MARKET over BOTH groups — US (explosive_us, tce_us) and PSX (explosive_psx, tce_psx, psx_candidates) — harvesting/re-attaching within each group so a US/PSX ticker collision can never cross-attach a score, and only filling rows whose 'im3' is None (a fresh IM3 step still overwrites). Pure post-build transform, no network/scoring change. Confirm on the runner: a scanner-only run now logs a higher 'Carried forward N' count and the PSX Explosive IM3 column keeps OGDC/PPL/FFC/HUBC/MCB scores instead of blanking. 1.48.0: (Wave P holdings change-tracking + throttle + cleanups) the FMR fund-ownership overlay now tracks month-over-month institutional FLOW. fetch_fmr_fund_ownership also returns per_fund={slug:{ticker:weight}} (which fund holds what); a new PURE _fmr_compute_flows(cur,prior) computes per-stock flow ONLY over the funds present in BOTH snapshots (set intersection) = the FALSE-EXIT GUARD so a failed-PDF coverage gap can never look like a sell -> attaches flow (NEW/EXITED/ACCUMULATING/TRIMMING/STABLE) + funds_delta + weight_delta onto each by_ticker entry + the per-candidate fund_ownership, vs the last DISTINCT stored snapshot. data['psx_fund_ownership'] gains snapshots[] (append only on a clean refresh: coverage not regressed + content changed, so weekly re-fetches of the same monthly FMR never pollute the baseline; last 4 kept) + last_fetch_utc. The FMR fetch is now THROTTLED to once/7 days (FMRs are monthly PDFs -> carry last-good between, ~6x less load on fundbazaarglobal). First run = BASELINE (flow='BASELINE', deltas null); first real delta lands next month. ALSO: (i) as-of date regex fixed - drops the greedy bare DD-Mon-YYYY that grabbed inception/footer dates (UBL/HBL showed 2006/2007/2014) -> bare DD-Mon only when prefixed by as at/on/of, every match recency-guarded to year>=2024 (else '?'); (ii) FIPI/LIPI probe flipped OFF - verdict read: no clean free runner-reachable feed (NCCPL CF-blocked, Sarmaaya/FinHisaab JS SPAs, Business Recorder is news), FIPI DEFERRED. DISPLAY/data-only, no scoring effect, respects the Sept freeze. Confirm on the runner: [Wave P FMR] logs a BASELINE flow line + 1 snapshot kept, and the UBL/HBL as-of dates are now a 2025/2026 date or '?' (not 2006/2007). 1.47.0: (Wave P Phase-2 probe + breadth/leaders) TWO additive PSX items. (a) probe_fipi_lipi_sources() - LOGGING-ONLY reachability probe (mirrors Phase-0) across the FIPI/LIPI daily-flow sources (NCCPL official FIPI/LIPI normal + market-info hub, Sarmaaya PSX-authorized redistributor, FinHisaab aggregator, Business Recorder) to find which is feedable from the runner BEFORE a parser is built; logs status/ct/size + parse hint (tables+rows / Cloudflare / JS-rendered); gated PSX_FIPI_PROBE=True, flip False once read. FIPI/LIPI = the daily institutional FLOW that complements the monthly fund-ownership STOCK overlay. (b) fetch_psx_market_stats() - daily breadth (advancers/decliners) + top volume & value leaders over the top-500-by-mcap set, via an ISOLATED pakistan/scan POST (its OWN request with a 'change' column) so that if TV rejects the column the MAIN universe scan is untouched; stored as data['psx_market']={breadth, volume_leaders, value_leaders}, carries last-good on failure. Both DISPLAY/data-only, no scoring effect, respect the Sept freeze. Confirm on the runner: the [Wave P FIPI probe] block names a parseable FIPI/LIPI source, and [Wave P breadth] logs adv/dec + leaders. 1.46.0: (Wave P Phase-1 follow-up - close the name-map gaps the v1.45.0 run surfaced) the FMR diagnostics flagged two unmapped holdings: 'Pak Petroleum Limited' (NBP's abbreviation for Pakistan Petroleum -> PPL was undercounted 5 funds vs 6) and 'Askari Commercial Bank Limited' (AKBL undercounted 1 vs 2). Added abbreviation aliases to _PSX_NAME_TICKER (pak petroleum->PPL, pak oilfields->POL, pak state oil->PSO, askari commercial bank->AKBL). Also broadened the FMR as-of date extraction (was 'as at <date>' only -> now also 'as on', DD-Mon-YYYY, 'Report - Month YYYY', and a generic 'Month DD, YYYY' fallback) so the UBL/NBP/HBL funds stop logging as-of '?'. Parser/aggregation logic otherwise unchanged; DISPLAY-only overlay, no scoring effect, respects the freeze. Confirm on the runner: PPL fund count rises to 6, the unmapped line shrinks/clears, more funds show a real as-of date. 1.45.0: (Wave P Phase-1 - AMC FMR fund-ownership overlay, DISPLAY-ONLY) fetch_fmr_fund_ownership() pulls the latest FMR factsheet PDFs for 9 high-risk equity/asset-allocation/balanced funds across Al Meezan/UBL/NBP/HBL (fundbazaarglobal static URLs, all probe-confirmed reachable from the runner), parses each fund's standardized Top-Ten Holdings table (pdfplumber + a layout-agnostic '...Limited/Ltd XX.XX%' regex, validated to extract 10/10 holdings from the real AMMF text with 0 noise), maps legal names -> PSX tickers via an ordered _PSX_NAME_TICKER map, and AGGREGATES into per-stock institutional ownership {funds, avg_weight, max_weight, sum_weight} = the PSX smart-money analog of the US ETF-consensus overlay. Attached per PSX candidate as c['fund_ownership'] + stored top-level as data['psx_fund_ownership']={by_ticker, meta} for the dashboard to join on. NOT wired into the TCE conviction count -> no tier/scoring change -> respects the Sept freeze (promote to a stream only post-maturation). NEW DEP: pdfplumber (added to daily.yml; imported lazily -> its absence logs + skips, never breaks the run). Fully guarded: per-fund 404/timeout/parse-empty skip+log; all-fail -> empty overlay carries last-good; the whole call wrapped. Heavy diagnostics (per-fund holdings count + as-of date; top holdings; top UNMAPPED names to grow the map). Phase-0 probe (PSX_SOURCE_PROBE) flipped False now its verdict is read (all 8 reachable). Confirm on the runner: the [Wave P FMR] block logs ~9 funds parsed + a top-holdings line (OGDC/PPL/FFC etc. with fund counts), and data.json gains psx_fund_ownership. (Version bump re-scrapes ETF overlap once.) 1.44.0: (Wave P Phase-0 - PSX institutional-source reachability probe, logging-only) before building any AMC-FMR / broker / directors-report feed, probe_psx_institutional_sources tests ON THE RUNNER whether the candidate sources are reachable + parseable: MUFAP AUM/fund-directory/unit-holder (HTML, fund universe + risk category), an AMC FMR PDF (Al Meezan dated pattern -> top holdings), a fund-factsheet aggregator (fundbazaarglobal PDF), a dps.psx filing PDF + company page (directors reports / financials), and the tickeranalysts broker-consensus page. Logs HTTP status + content-type + size + a parse hint (valid-PDF / HTML tables+rows / Cloudflare challenge / JS-rendered) per source; each GET independently guarded (12s timeout), the whole call wrapped, so it can NEVER affect the live scan. Cloudflare blocks by datacenter IP so reachability is only knowable on the runner (sandbox reaches github/pypi/npm only). Gated by PSX_SOURCE_PROBE=True; set False once the verdict is read. RATIONALE: broker reports are already largely captured by the TV FactSet analyst overlay (s11/s12); the NEW value is AMC fund holdings (the PSX smart-money analog of US ETF-consensus) + directors-report narrative, both PDF/monthly on the historically-blocked PSX-site class - so reachability must be proven before a parser is committed. No screening/scoring change. 1.43.0: (Wave D2 holdings — track the PSX book through the engine) the five PSX holdings (OGDC/PPL/MCB/FFC/HUBC) are KSE-30 mega-caps that sit ABOVE the PSX scan band ceiling (PSX_MCAP_MAX=60e9), so derive_psx_candidates excluded them and they got no analyst overlay or TCE scoring. NEW PSX_MEGACAPS constant + a force-include pass in derive_psx_candidates (the analog of the US large-cap union): after the band-filtered top_n, append any holding present in the pakistan/scan rows (range[0,500] mcap-desc -> the mega-caps are always in it) with a valid close, deduped, carrying its own FactSet analyst block. They then get s11/s12/s9 + full TCE tiers like everything else (PSX run_tce already scores all candidates, max_count=len). ADDITIVE: existing band names + their scoring unchanged; PSX candidate count rises ~25->~30; predictions now accrue for the holdings too. NOT an engine retune (no threshold/conviction change) -> respects the Sept freeze. Confirm on the runner: OGDC/PPL/MCB/FFC/HUBC appear in the PSX scan with (tv_scan) prices + analyst chips and a TCE tier. (Version bump re-scrapes ETF overlap once.) 1.42.0: (Wave O L1 follow-up — drop preferred/baby-bond leakage) the v1.41.0 cutover (insider gate dropped + fundamentals from TV) surfaced a side effect: TV's type=stock feed leaks baby-bond/preferred SERIES as bare base+letter symbols (ADAM->ADAMH/L/M/N/Z, RILY->RILYL/P, NEWT->NEWTG/P, ATLC->ATLCP/Z, CCNE->CCNEP) that Yahoo's insider gate used to suppress incidentally (no insider data -> 0%% -> dropped). is_common_us_ticker only rejects '/'-suffixed symbols, so these passed and polluted the candidate + Explosive pool (not the TCE-15, which ranks by rev-growth). FIX in fetch_us_universe_tv: drop a band symbol whose value is another band ticker + one trailing letter (len>=5 and tk[:-1] in the band base set) -> keeps the common stock, drops its series. Band-only (large-caps are a fixed common-ticker set, untouched), so no holding can be dropped. Logs the count. Confirm on the runner: the ADAMH/RILYL/NEWTG/etc. clusters are gone from the Explosive screen; survivor count drops by ~12. 1.41.0: (Wave O L1 — TV-first US fundamentals cutover) the US screen is now built from TradingView fundamentals (one america/scan POST for the band via fetch_us_universe_tv's returned band_map + one mcap-desc POST for the named large-caps via the new fetch_us_large_fundamentals), replacing the ~660 per-name Yahoo .info calls (the ~3-min screen loop). New PURE _candidate_from_tv() mirrors screen_us_stock EXACTLY minus the insider gate: band ($300M-$2bn unless a named large-cap) + non-financial rev-growth>=15% (financials bypass, gated on ROE/EPS at classify); UNITS validated vs the live probe (TV rev/eps-growth + margins/ROIC already percent; return_on_equity via _roe_pct; debt_to_equity already the decimal ratio matching Yahoo debtToEquity/100; price=close; pe=price_earnings_ttm). FAIL-SAFE: a name whose TV rec lacks market_cap/price falls back to a per-name Yahoo screen (coverage can't regress); a TV-decided gate fail ('DROP') is NOT re-tried on Yahoo; if the prefilter hard-falls-back to the full Yahoo universe (empty band_map) EVERY name takes the Yahoo path = pre-L1 behaviour. INSIDER GATE DROPPED (heldPercentInsiders<5%, a Yahoo field TV has no equivalent for; the probe confirmed no TV insider column) — the s3_insider EDGAR Form-4 stream is independent and unaffected, so insider ACTIVITY is still flagged downstream. The EPS income_stmt enrichment now has far fewer gaps to fill (TV supplies eps_growth). Confirm on the runner: survivor count ~= prior (slightly higher from the dropped insider gate — the survivor delta is the live check), candidates carry growth_source='tv', US TCE HIGH unchanged in spirit. (Version bump re-scrapes ETF overlap once.) 1.40.0: (RS-guardrail fail-closed-on-NaN — the BENCHMARK half) v1.39.0 cleaned the per-name closes (price/s6 recovered) but US TCE HIGH stayed 0: the SAME intermittent Yahoo NaN-Close glitch was hitting the SPY benchmark in _spy_6mo_return(), which returned round(NaN,1)=NaN, so the guardrail's `name_6mo >= spy_6mo_ret` was `x >= NaN` = False -> rs_ok=False -> whole US book vetoed to WATCH (rs_vs_spy serialized None via the NaN sanitizer, the tell). FIX: (1) _spy_6mo_return strips NaN from SPY closes (same `if x == x` filter) -> returns a real 6mo return or (None,None) cleanly; (2) derive_streams normalizes a NaN spy_6mo_ret to None up front, so a bad benchmark fetch fails OPEN (rs_ok=True, conviction decides) instead of silently vetoing. Together with v1.39.0 the guardrail is now NaN-safe on BOTH the name side and the benchmark side. Correctness fix, thresholds/conviction untouched. Confirm on the runner: US HIGH returns to a selective non-zero and rs_vs_spy is numeric (GUARD chips show real ±pt, not veto-across-the-board). 1.39.0: (RS-guardrail fail-closed-on-NaN fix — the per-NAME half) closes now strips NaN + derive_streams guards name_6mo against NaN. 1.38.0: (Wave O L1 — insider probe, isolated/logging-only) added probe_us_insider_coverage(): the US screen drops candidates with heldPercentInsiders<5% (a Yahoo .info field), so the L1 fundamentals cutover (retiring ~666 per-name Yahoo calls) can only KEEP that gate if TV exposes an insider-ownership column. The probe tries candidate TV field names (insider_ownership / held_by_insiders / shares_insiders / institutional_ownership / held_by_institutions) all-in-one, falling back to per-name requests if TV 400s the batch (an unknown column rejects the whole POST), in its OWN request(s) so it can never corrupt the main coverage probe's alignment. It logs which fields TV accepts + their coverage, resolving the cutover fork: a usable field -> keep the gate on TV; NONE -> the cutover drops the gate (measure survivor delta) or keeps one thin per-name insider call. Read the run log once; no screening/scoring change. 1.37.0: (L3 follow-up — unify PSX ledger price on tv_scan) the v1.36 re-baseline killed the dps.psx staleness but landed entries on the yahoo:.KA snapshot (streams['price'], the TCE's own momentum fetch), which runs systematically ~0-4% (up to ~10% on thin names like TPL/TPLP) below the screen's TV pakistan/scan close — while the maturity re-pricer (_reprice_psx) uses TV. That entry(.KA)-vs-reprice(TV) split would bake a fake ~+3% of alpha into every PSX pick. FIX: (1) the prediction-row builder now prefers the candidate's tv_scan price for PSX rows (US still uses Yahoo streams['price'], which is consistent with _reprice_us); (2) the PSX re-baseline guard advances v136 -> v137 so it re-runs ONCE more, now resetting the existing open PSX entries onto the tv_scan basis -> entry and re-price share one source, offset -> 0. Pure transform downstream of the network fetch; confirm on the runner that the re-baseline fires once more and PSX entries match this run's tv_scan, then never repeats. (Version bump re-scrapes ETF overlap once.) 1.36.0: (L3 follow-up — confirmed dps.psx EOD is STALE) the run + the user confirmed TV/.KA prices are CURRENT (TRG 71.67, KPUS 2443) and dps.psx EOD was stale (TRG 164, KPUS 49) — same frozen endpoint family as the KSE-100 index. (1) screen_psx_stock: dps.psx EOD REMOVED from the price path; fallback is now yahoo:.KA only (correct/current basis, matches the TV scan close). (2) update_tce_predictions: one-time guarded PSX re-baseline — every OPEN PSX prediction logged on the stale basis has its entry price/date/KSE-100 benchmark reset to the correct current basis, then prev.psx_rebaselined_v136 is set so it never repeats; US entries untouched (Yahoo always gave correct US prices). Pure transform; caller logs the count. (Version bump re-scrapes ETF overlap once.) 1.35.0: (Wave O L3 — TV-sourced PSX prices) screen_psx_stock now takes the PSX price from the close already returned in the pakistan/scan universe POST (carried on the candidate's analyst row alongside volume) instead of a per-name dps.psx EOD GET. This (a) eliminates the 25 sequential per-name fetches + their inter-name YF_DELAY sleeps (~60s), and (b) fixes the data-quality bug where, when dps.psx is down, prices fell back to yahoo:.KA on a WRONG basis (TRG 69 vs 164, KPUS 2441 vs 49). The TV scan close is the SAME basis the analyst target-upside (s11) already divides by, so the displayed price and the conviction math are now internally consistent. dps.psx EOD then yahoo:.KA remain as a defensive fallback ONLY when the scan lacks a close (data_source: tv_scan | psx_eod | yahoo:.KA | cached). avg_volume now carries the scan volume (it is unused downstream). Network-only -> confirm on the runner. (Version bump re-scrapes ETF overlap once.) 1.34.0: (Wave O L1 — US analyst overlay, the US counterpart to D2) fetch_us_analyst_block() does ONE america/scan POST over the US band and returns a {ticker: analyst_row} map (TV FactSet: close, price_target_average, recommendation_mark/buy/total, forward+current EPS) shaped for the existing tce_psx_analyst.derive_psx_analyst_streams. Rows are attached to the US TCE pool; the compute_tce_streams analyst branch is no longer PSX-gated (fires for any candidate carrying an analyst_row). US gains s11_target_upside (>=15%% target upside) + s12_recommendation (>=60%% buy or rec_mark<=2.0); s9_eps_revision is SUPPRESSED for US (it already has the Yahoo s9_eps_rev -> no double-count). prev_fwd persisted for US from EXISTING.tce_us. Best-effort: a TV miss -> {} -> no analyst_row -> US scoring reverts to pre-overlay behaviour (cannot break the run). PAIRED FIX in tce_psx_analyst.py: the probe proved recommendation_mark is the FactSet 1(strong buy)..5(strong sell) scale (sample 1.125, impossible on the previously-assumed -1..+1), so the s12 rec_mark clause changed from >=0.5 (always-true -> fired on coverage alone) to <=2.0 (buy-or-better, discriminative) via new REC_MARK_BULLISH. This also makes PSX s12 discriminative -> some covered PSX names rated hold/sell with buy_ratio<60%% will stop firing s12 (correct). Network-only (TV) -> confirm coverage + US/PSX tier deltas on the runner. (Version bump re-scrapes ETF overlap once.) 1.33.0: (Wave O L1 — instrumentation, isolated/additive) added probe_us_tv_coverage(): one america/scan POST that logs coverage%% + a units sample for the candidate TV-first US columns (P/E, P/B, P/S, EV/EBITDA, gross/op/net margin, ROIC, D/E, current ratio + the FactSet analyst block: price_target_average, recommendation_mark/buy/total, forward EPS). It does NOT touch the production prefilter parse (no misalignment risk to the revenue/ROE band) and never raises into the run. Purpose: confirm TV column names/units on a live run BEFORE the L1 fundamentals cutover (replace ~666 Yahoo .info calls) + US analyst-scoring overlay + L2/L3/L4 batching land. Logging-only; live screening/scoring unchanged. 1.32.0: (Tier 1 — prediction feedback loop hardened) the forward-validation ledger is now trustworthy ahead of the ~Sept maturations. Gap-1 (stale maturity price): open predictions are re-priced every run via a live fetch (_reprice_us batch yfinance + _reprice_psx targeted TV scan) for any open pick whose ticker has left the scan pool / decayed to IGNORE, so a pick no longer freezes at a stale return when it matures. Gap-2 (no alpha): each pick now stores entry_bench (SPY for US, KSE-100 for PSX) and computes bench_ret_pct + alpha_pct + peak_alpha_pct each run, so a "win" can be judged market-relative, not just absolute +40% in a bull tape (legacy picks logged pre-1.32.0 have no entry_bench -> alpha stays null for them). Gap-3 (no control): the ledger now also logs TCE-pool IGNORE picks as a control arm and reports HIGH/WATCH lift_vs_ignore over the IGNORE base rate. Dedup is now per (ticker, tier) so a name escalating IGNORE->WATCH->HIGH logs a fresh prediction at each tier (each tier's signal measured from when it fired). update_tce_predictions stays PURE (extra_prices + bench injected by the caller; fully unit-tested); the re-price fetches are network-only -> confirm on the runner. Logging/validation change; live US/PSX TCE scoring unchanged. (Version bump re-scrapes ETF overlap once.) 1.31.1: (D2 hardening) the guarded tce_psx_analyst import no longer fails silently — it captures the error and run_tce emits a LOUD degraded-data warning ('D2 analyst overlay DISABLED ... confirm tce_psx_analyst.py is in the repo root') so a missing module surfaces in the run summary instead of dying invisibly (root-caused the 1.31.0 no-fire: the module simply was not committed). Logging-only; scoring unchanged. (Version bump re-scrapes ETF overlap once.) 1.31.0: (Wave D2 — PSX analyst conviction) wired tce_psx_analyst.py into the PSX TCE: PSX_SCAN_COLS now pulls the TV FactSet analyst block (price_target_average, recommendation_mark/buy/total, earnings_per_share_forecast_next_fq/fq, earnings_per_share_fq); derive_psx_candidates carries an analyst row per candidate; compute_tce_streams folds derive_psx_analyst_streams into three new conviction streams s11_target_upside (>=15% target upside) / s12_recommendation (>=60% buy or rec_mark>=0.5) / s9_eps_revision (forward EPS rising >=2% run-over-run, persisted via prev_fwd). Added to COUNTED+CONVICTION GLOBALLY but only the PSX path sets them, so US tiers are provably unchanged (validated: KLAC-like still HIGH 7/4; covered PSX name reaches HIGH 5/5; uncovered PSX name unchanged WATCH 2/2). Probe-confirmed TV coverage: analyst block 98-100%%, 15/15 on holdings. (Version bump re-scrapes ETF overlap once.) 1.30.0: (Wave T3 feeds) oil WTI/Brent trend (Yahoo widened 5d->6mo, backfilled 5/21/63 -> wti_/brent_wow/mom/qoq, live day-1); KSE-100 trend (dedup-by-date session history -> kse100_wow/mom/qoq, accrues per session); Zacks sector rotation (pct_top_chg = each sector's #1/#2 breadth change vs the prior scrape, carried on skip days). Dashboard v5.16 reads these into the energy oil-momentum note, the US sector-rotation read, the allocation rate-path repricing line, and the PSX devaluation-slope alert (reserves/PKR trajectory). 1.29.0: (Wave T3 monthly/quarterly trend) cadence-matched MoM/QoQ/YoY on the macro PRINT series via _print_trend, backfilled from the FRED series (live day-1): core_pce/cpi_yoy trend the YoY *rate* (inflation accelerating vs decelerating, not the index level), gdp_growth quarterly (QoQ/YoY), and unemployment/umcsi/mfg_emp/industrial_prod/permits monthly levels (MoM/QoQ/YoY). Dashboard T3 interpretation (macro tab prints-vs-prior-release, Sector rotation, Allocation zone migration, Devaluation slope) is the paired index build. 1.28.0: (Wave T2 daily-WoW trend) WoW/MoM/QoQ on the daily market series via 5/21/63-trading-day windows, all backfilled from the source series (live day-1): FRED us_10y/us_2y/hy_spread + dfii10/breakeven_10y/gvz, Yahoo gold/silver/platinum/palladium px + dxy (period widened 5d->6mo) and usd_pkr; plus a us_2s10s spread value. Dashboard M1 US-regime + M6 metals engine now fold real-yield/DXY/breakeven/GVZ/yield direction into their reads. 1.27.0: (Wave T1 weekly-native trend) generic {d,v} dedup-by-date history + WoW/MoM/QoQ trend helpers applied to the four weekly-native series: COT metals net-%OI (now dedup-by-report-date, fixes same-day duplicate appends -> cot_{m}_pct_wow/_mom/_qoq), COT futures net (backfilled from the DESC CFTC rows -> net_wow/_mom/_qoq, live day-1), WALCL (backfilled from the FRED weekly series -> walcl_wow/_mom/_qoq), and SBP reserves (value-change-dedup history -> sbp_reserves_wow/_mom/_qoq). Dashboard M6 metals engine now folds COT *direction* into the tactical score. 1.26.0: (Wave M5/M6 metals data) added FRED real-yield DFII10 + 10y breakeven T10YIE + Gold-VIX GVZCLS into macros.metals (dfii10/breakeven_10y/gvz), and 156-week COT net-%-OI history+percentile persistence (cot_{gold,silver,copper}_hist/_pctile) so the dashboard M6 engine swaps its real-yield proxy for true TIPS and its COT proxy for a percentile as history accrues. 1.25.0: (Wave D1 step 3) ROE>=ROE_FIN_MIN (8%) is now the PRIMARY financial screen gate (from the live diag: keeps 193/387, median 9.2%), with EPS-YoY>=0% as a not-deteriorating secondary; the Yahoo revenue gate is BYPASSED for financials (revenue meaningless for a spread/credit business) while non-financials still require revenueGrowth>=15%. Missing vendor field never drops a bank. Log line is now 'D1 bank gate: N in-band -> dropped R (ROE<8%) + E (EPS<0) -> M to Yahoo'. (Version bump re-scrapes ETF overlap once.) 1.24.0: (Track 1 — D1 step 2 gate) banks gated on a bank-appropriate metric: EPS-YoY>=0% active (drops deteriorating banks, no-data passes through), Yahoo revenue gate kept as backstop this run (monotonic, no candidate ballooning); ROE column+distribution diag added — ROE becomes primary financial gate next run once TV coverage/units confirmed. (Track 2 — IM3 System B refactor) score_im3_bank now zeroes ALL non-bank metrics (Piotroski/Altman/Beneish/ROIC-WACC, EV-EBITDA/PEG/PS/Graham/MoS, FCF/CROIC, D/E/total-debt, op-margin/turns) per the Sarmaaya Week-6 framework, and scores banks out of their APPLICABLE max (~70) instead of /162 — fixes the bug that capped every bank ~55% (grade C). Added bank_coverage + bank_inputs probe for the Phase-2 canonical-ratio additions. (Version bump re-scrapes ETF overlap once.) 1.23.0: Wave D1 step 1 instrumentation. 1.22.2: KSE-100 RESOLVED via diagnostics — the index lives on the dps.psx INT (intraday) timeseries (current; 171651.48 @ last session), NOT eod (frozen at 2021). int now primary with date-preference; dead market-watch(470KB)/indices/sarmaaya HTML + diag removed. Value was the last-session close, never stale. 1.22.0: (a) COT/CFTC timeout (8,12) to bound dead-endpoint cost; (b) KSE-100 fresh HTML sources (market-watch/indices) first, stale int demoted last; (c) NEW recession watch block (FRED Sahm/yield-curve/RECPRO/GDPNow/claims + ForexFactory faireconomy calendar). 1.21.3: also carry forward per-record im3 score dicts (not just the ticker list) so a skipped IM3 re-score doesn't wipe the scores from data.json. 1.21.2: preserve im3_explosive_tickers so the workflow's IM3 change-detection can skip re-scoring on stable days. 1.21.1: drop TV-leaked preferred-share tickers + demote micro-base rev-growth artifacts. 1.21.0: US screening migration Phase 1 (TV america pre-filter before Yahoo; financials pass straight to Yahoo; hard fallback to full Yahoo universe if TV unreachable)
# v1.19.0  TradingView futures fallback for live oil (WTI/Brent) — slots between Yahoo and stale-FRED

YF_DELAY          = 0.35
TCE_BATCH_HISTORY = True   # v1.111.0: batch the TCE pool's 6mo price-history fetch (ONE yf.download for
                           # the whole pool) instead of one t.history() round-trip per name. Per-name
                           # fallback preserves coverage exactly. Flip False to revert to pure per-name.
US_SMALL_CAP_MIN  = 300_000_000
US_SMALL_CAP_MAX  = 2_000_000_000
US_REV_GROWTH_MIN = 0.15
ROE_FIN_MIN       = 8.0   # %; D1 step 3 — the PRIMARY financial (bank) screen gate. From the
                          # live ROE diag (354/387 financials have ROE, median 9.2%): >=8% keeps
                          # 193 of 387, a sensible candidate floor (NOT the canonical 20% scoring
                          # bar). Replaces the revenue gate for financials (revenue is meaningless
                          # for a spread/credit business). Tunable.
US_REV_GROWTH_SANE_MAX = 500.0  # %; rev-growth above this is a micro-base artifact (near-zero prior-year
                                # revenue -> astronomical %). Such names are demoted in the candidate
                                # ranking so they can't grab a HIGH-CONVICTION slot (they still pass the screen).

US_CANDIDATE_POOL = 15    # top small-cap survivors fed to TCE (slow, network-heavy)
ETF_TCE_N         = 20    # ETF-consensus large-caps added to the US TCE pool (so quality large-caps are visible)
US_SCAN_WORKERS   = 2     # parallel Yahoo screen workers. 8 hard-throttled, 4 still capped survivors + poisoned the EPS session. 2 = balanced. Set to 1 for guaranteed-complete sequential (~18min).
US_EXPLOSIVE_POOL = 200   # survivors fed to explosive screen (fast, no network)

# --- v1.112.0 performance + correctness pass (audit F1-F6); each independently reversible ---
TCE_YF_FUNDAMENTALS_US_ONLY = True   # F1: skip the doomed PSX .info/.eps/.rev Yahoo calls (.KA has no fundamentals)
EPS_ENRICH_TRY_FMP          = False  # F3: FMP /stable/ is premium-gated for these small-caps (402 every run) -> Yahoo-first
EXPLOSIVE_STMT_CACHE_DAYS   = 7      # F2: income statements change quarterly -> cache the computed cond dict 7d
MTS_STALE_DAYS              = 14     # F5: flag the MTS leverage gauge stale if its as-of date is older than this (days)

PSX_SWEET_SPOT_MIN = 5_000_000_000
PSX_SWEET_SPOT_MAX = 30_000_000_000
PSX_GROWTH_MIN     = 0.20

KSE_MIN, KSE_MAX = 50_000, 500_000

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

DEFAULT_DATA = {
    'meta': {'scan_version': SCAN_VERSION, 'last_scan_utc': None,
             'errors': [], 'warnings': []},
    'macros': {'us': {}, 'psx': {}, 'metals': {}},
    'universe_sizes': {'psx_total': 561, 'us_total': 5800},
    'psx_funnel': [], 'us_funnel': [],
    'psx_candidates': [], 'us_candidates': [],
    'psx_fund_ownership': {},
    'psx_valuation_matrix': {},
    'psx_mts': {},
    'psx_msci': {},
    'psx_market': {},
    'tce_psx': [], 'tce_us': [],
    'tce_predictions': {},
    'explosive_psx': [], 'explosive_us': [],
    'rate_path': [],
    'recession': {},
    # Phase 0 — World Economies macro layer (v1.117.0)
    'world_lei':      {},   # 9-country OECD LEI signals from FRED
    'us_diffusion':   {},   # 15-indicator US economic diffusion index
    'country_rs':     [],   # 9-country equity momentum + FX-adjusted return ranking
    'sector_booming': [],   # Sector 0-100 composite score → Booming/Favoured/Neutral/Lagging/Avoid
}

WARNINGS = []


def load_existing():
    try:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_DATA.copy()


EXISTING = load_existing()



# ── Phase 3: ETF Universe catalog (parsed from ETF_Universe.xlsx, quality-floored) ──
# 28 categories (13 countries + 11 GICS sectors + 2 Real Estate + World/EM/AsiaPac fallback)
# Each category: up to 5 funds sorted by fund size desc (liquidity/establishment proxy),
# TER asc as tiebreak. Quality floor: fund size >= 10m EUR (excludes thin/new products).
# Update quarterly by re-running the ETF_Universe.xlsx parse.
_ETF_CATALOG = {"Equity South Korea":[{"name":"Franklin FTSE Korea UCITS ETF","ter":0.09,"ytd":119.93,"size_m_eur":4321,"isin":"IE00BHZRR030","dist":"Accumulating","holdings":"Samsung Electronics, SK Hynix, Hyundai"},{"name":"iShares MSCI Korea UCITS ETF (Dist)","ter":0.65,"ytd":112.21,"size_m_eur":1197,"isin":"IE00B0M63391","dist":"Distributing","holdings":"Samsung Electronics, SK Hynix, Hyundai"},{"name":"Amundi MSCI Korea UCITS ETF Acc","ter":0.45,"ytd":113.25,"size_m_eur":893,"isin":"LU1900066975","dist":"Accumulating","holdings":"Samsung Electronics, SK Hynix, Hyundai"},{"name":"iShares MSCI Korea UCITS ETF (Acc)","ter":0.65,"ytd":117.37,"size_m_eur":840,"isin":"IE00B5W4TY14","dist":"Accumulating","holdings":"Samsung Electronics, SK Hynix, Hyundai"},{"name":"Xtrackers MSCI Korea UCITS ETF 1C","ter":0.45,"ytd":113.03,"size_m_eur":478,"isin":"LU0292100046","dist":"Accumulating","holdings":"Samsung Electronics, SK Hynix, Hyundai"}],"Equity Taiwan":[{"name":"iShares MSCI Taiwan UCITS ETF","ter":0.74,"ytd":71.33,"size_m_eur":1447,"isin":"IE00B0M63623","dist":"Distributing","holdings":"TSMC, Hon Hai, MediaTek"},{"name":"Franklin FTSE Taiwan UCITS ETF SINGLCLASS","ter":0.19,"ytd":71.64,"size_m_eur":490,"isin":"IE000CM02H85","dist":"Accumulating","holdings":"TSMC, Hon Hai, MediaTek"},{"name":"Xtrackers MSCI Taiwan UCITS ETF 1C","ter":0.65,"ytd":71.51,"size_m_eur":330,"isin":"LU0292109187","dist":"Accumulating","holdings":"TSMC, Hon Hai, MediaTek"},{"name":"Xtrackers MSCI Taiwan UCITS ETF 1D","ter":0.21,"ytd":71.9,"size_m_eur":105,"isin":"LU2928641757","dist":"Distributing","holdings":"TSMC, Hon Hai, MediaTek"},{"name":"HSBC MSCI Taiwan Capped UCITS ETF USD","ter":0.5,"ytd":71,"size_m_eur":95,"isin":"IE00B3S1J086","dist":"Distributing","holdings":"TSMC, Hon Hai, MediaTek"}],"Equity Asia Pacific":[{"name":"iShares MSCI EM Asia UCITS ETF (Acc)","ter":0.2,"ytd":33.41,"size_m_eur":7594,"isin":"IE00B5L8K969","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"iShares Core MSCI Pacific ex Japan UCITS ETF (Acc)","ter":0.2,"ytd":10.04,"size_m_eur":3244,"isin":"IE00B52MJY50","dist":"Accumulating","holdings":"TSMC, Samsung, Tencent, BHP"},{"name":"Vanguard FTSE Developed Asia Pacific ex Japan UCITS ETF Distributing","ter":0.15,"ytd":54.05,"size_m_eur":1912,"isin":"IE00B9F5YL18","dist":"Distributing","holdings":"TSMC, Samsung, Tencent, BHP"},{"name":"Amundi MSCI Emerging Markets Asia UCITS ETF EUR (C)","ter":0.2,"ytd":33.39,"size_m_eur":1802,"isin":"LU1681044480","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"iShares MSCI AC Far East ex-Japan UCITS ETF","ter":0.74,"ytd":38.77,"size_m_eur":1780,"isin":"IE00B0M63730","dist":"Distributing","holdings":"TSMC, Samsung, Tencent, BHP"}],"Equity Technology":[{"name":"iShares S&P 500 Information Technology Sector UCITS ETF USD (Acc)","ter":0.15,"ytd":19.45,"size_m_eur":15572,"isin":"IE00B3WJKG14","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Xtrackers MSCI World Information Technology UCITS ETF 1C","ter":0.25,"ytd":21.17,"size_m_eur":5421,"isin":"IE00BM67HT60","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Broadcom"},{"name":"Amundi MSCI World Information Technology UCITS ETF EUR Acc","ter":0.3,"ytd":20.96,"size_m_eur":2733,"isin":"LU0533033667","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Broadcom"},{"name":"Invesco US Technology Sector UCITS ETF","ter":0.14,"ytd":19.99,"size_m_eur":1924,"isin":"IE00B3VSSL01","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Broadcom"},{"name":"Xtrackers MSCI USA Information Technology UCITS ETF 1D","ter":0.12,"ytd":19.19,"size_m_eur":1786,"isin":"IE00BGQYRS42","dist":"Distributing","holdings":"Apple, Microsoft, Nvidia, Broadcom"}],"Equity Emerging Markets":[{"name":"iShares Core MSCI Emerging Markets IMI UCITS ETF (Acc)","ter":0.18,"ytd":27.18,"size_m_eur":37810,"isin":"IE00BKM4GZ66","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"Xtrackers MSCI Emerging Markets UCITS ETF 1C","ter":0.18,"ytd":28.83,"size_m_eur":11898,"isin":"IE00BTJRMP35","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"iShares MSCI EM UCITS ETF (Dist)","ter":0.18,"ytd":28.6,"size_m_eur":9123,"isin":"IE00B0M63177","dist":"Distributing","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"iShares MSCI EM UCITS ETF (Acc)","ter":0.18,"ytd":28.87,"size_m_eur":8757,"isin":"IE00B4L5YC18","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"},{"name":"UBS Core MSCI EM UCITS ETF USD acc","ter":0.15,"ytd":29.03,"size_m_eur":7059,"isin":"LU0950674175","dist":"Accumulating","holdings":"TSMC, Tencent, Samsung, Alibaba"}],"Equity Japan":[{"name":"iShares Core MSCI Japan IMI UCITS ETF","ter":0.12,"ytd":19.82,"size_m_eur":6917,"isin":"IE00B4L5YX21","dist":"Accumulating","holdings":"Toyota, Sony, Keyence, Mitsubishi UFJ"},{"name":"Xtrackers MSCI Japan UCITS ETF 1C","ter":0.12,"ytd":21,"size_m_eur":5643,"isin":"LU0274209740","dist":"Accumulating","holdings":"Toyota, Sony, Keyence, Mitsubishi UFJ"},{"name":"Amundi Core MSCI Japan UCITS ETF Acc","ter":0.12,"ytd":19.96,"size_m_eur":5353,"isin":"LU1781541252","dist":"Accumulating","holdings":"Toyota, Sony, Keyence, Mitsubishi UFJ"},{"name":"UBS Core MSCI Japan UCITS ETF JPY acc","ter":0.12,"ytd":20.64,"size_m_eur":4294,"isin":"LU0950671825","dist":"Accumulating","holdings":"Toyota, Sony, Keyence, Mitsubishi UFJ"},{"name":"Vanguard FTSE Japan UCITS ETF (USD) Distributing","ter":0.1,"ytd":19.48,"size_m_eur":2753,"isin":"IE00B95PGT31","dist":"Distributing","holdings":"Toyota, Sony, Keyence, Mitsubishi UFJ"}],"Equity Energy":[{"name":"Xtrackers MSCI World Energy UCITS ETF 1C","ter":0.25,"ytd":24.11,"size_m_eur":1526,"isin":"IE00BM67HM91","dist":"Accumulating","holdings":"ExxonMobil, Chevron, Shell"},{"name":"iShares S&P 500 Energy Sector UCITS ETF (Acc)","ter":0.15,"ytd":25.5,"size_m_eur":1128,"isin":"IE00B42NKQ00","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares MSCI World Energy Sector UCITS ETF USD (Dist)","ter":0.18,"ytd":24.09,"size_m_eur":1040,"isin":"IE00BJ5JP105","dist":"Distributing","holdings":"ExxonMobil, Chevron, Shell"},{"name":"State Street SPDR S&P U.S. Energy Select Sector UCITS ETF USD","ter":0.15,"ytd":25.5,"size_m_eur":817,"isin":"IE00BWBXM492","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"State Street SPDR MSCI Europe Energy UCITS ETF EUR","ter":0.18,"ytd":20.64,"size_m_eur":637,"isin":"IE00BKWQ0F09","dist":"Accumulating","holdings":"Novo Nordisk, ASML, Nestl\u00e9, SAP"}],"Equity United States":[{"name":"iShares Core S&P 500 UCITS ETF USD (Acc)","ter":0.07,"ytd":11.69,"size_m_eur":129556,"isin":"IE00B5BMR087","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Vanguard S&P 500 UCITS ETF (USD) Distributing","ter":0.07,"ytd":11.4,"size_m_eur":45028,"isin":"IE00B3XXRP09","dist":"Distributing","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Invesco S&P 500 UCITS ETF Acc","ter":0.05,"ytd":11.88,"size_m_eur":35100,"isin":"IE00B3YCGJ38","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Vanguard S&P 500 UCITS ETF (USD) Accumulating","ter":0.07,"ytd":11.8,"size_m_eur":29112,"isin":"IE00BFMXXD54","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares Nasdaq 100 UCITS ETF (Acc)","ter":0.3,"ytd":20.05,"size_m_eur":23837,"isin":"IE00B53SZB19","dist":"Accumulating","holdings":"Nvidia, Apple, Microsoft, Broadcom"}],"Equity Basic Materials":[{"name":"VanEck S&P Global Mining UCITS ETF A","ter":0.5,"ytd":6.95,"size_m_eur":1581,"isin":"IE00BDFBTQ78","dist":"Accumulating","holdings":"BHP, Rio Tinto, Freeport, Linde"},{"name":"VanEck Rare Earth and Strategic Metals UCITS ETF A","ter":0.59,"ytd":24.51,"size_m_eur":1313,"isin":"IE0002PG6CA6","dist":"Accumulating","holdings":"BHP, Rio Tinto, Freeport, Linde"},{"name":"Global X Silver Miners UCITS ETF USD Accumulating","ter":0.65,"ytd":-5.59,"size_m_eur":1150,"isin":"IE000UL6CLP7","dist":"Accumulating","holdings":"BHP, Rio Tinto, Freeport, Linde"},{"name":"Global X Copper Miners UCITS ETF USD Accumulating","ter":0.55,"ytd":9.75,"size_m_eur":955,"isin":"IE0003Z9E2Y3","dist":"Accumulating","holdings":"BHP, Rio Tinto, Freeport, Linde"},{"name":"Xtrackers MSCI World Materials UCITS ETF 1C","ter":0.25,"ytd":14.52,"size_m_eur":654,"isin":"IE00BM67HS53","dist":"Accumulating","holdings":"BHP, Rio Tinto, Freeport, Linde"}],"Equity Industrials":[{"name":"iShares MSCI Europe Industrials Sector UCITS ETF EUR (Acc)","ter":0.18,"ytd":11,"size_m_eur":1297,"isin":"IE00BMW42520","dist":"Accumulating","holdings":"GE, Siemens, Caterpillar"},{"name":"State Street SPDR MSCI Europe Industrials UCITS ETF EUR","ter":0.18,"ytd":11.27,"size_m_eur":1246,"isin":"IE00BKWQ0J47","dist":"Accumulating","holdings":"GE, Siemens, Caterpillar"},{"name":"Xtrackers MSCI World Industrials UCITS ETF 1C","ter":0.25,"ytd":18.08,"size_m_eur":903,"isin":"IE00BM67HV82","dist":"Accumulating","holdings":"GE, Siemens, Caterpillar"},{"name":"State Street SPDR S&P U.S. Industrials Select Sector UCITS ETF USD","ter":0.15,"ytd":23.16,"size_m_eur":843,"isin":"IE00BWBXM724","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares STOXX Europe 600 Construction & Materials UCITS ETF (DE)","ter":0.46,"ytd":6.03,"size_m_eur":840,"isin":"DE000A0H08F7","dist":"Distributing","holdings":"BHP, Rio Tinto, Freeport, Linde"}],"Real Estate United States":[{"name":"iShares US Property Yield UCITS ETF","ter":0.4,"ytd":20.15,"size_m_eur":591,"isin":"IE00B1FZSF77","dist":"Distributing","holdings":"Prologis, American Tower, Equinix"},{"name":"Invesco US Real Estate Sector UCITS ETF","ter":0.14,"ytd":15.58,"size_m_eur":122,"isin":"IE00BYM8JD58","dist":"Accumulating","holdings":"Prologis, American Tower, Equinix"},{"name":"iShares US Property Yield UCITS ETF USD (Acc)","ter":0.4,"ytd":21.33,"size_m_eur":16,"isin":"IE00BKPT2R27","dist":"Accumulating","holdings":"Prologis, American Tower, Equinix"}],"Equity China":[{"name":"iShares MSCI China A UCITS ETF","ter":0.4,"ytd":15.48,"size_m_eur":2880,"isin":"IE00BQT3WG13","dist":"Accumulating","holdings":"Kweichow Moutai, CATL, Ping An"},{"name":"iShares MSCI China UCITS ETF USD (Acc)","ter":0.28,"ytd":-12.21,"size_m_eur":2616,"isin":"IE00BJ5JPG56","dist":"Accumulating","holdings":"Tencent, Alibaba, Meituan"},{"name":"Xtrackers CSI 300 Swap UCITS ETF 1C","ter":0.5,"ytd":18.07,"size_m_eur":1806,"isin":"LU0779800910","dist":"Accumulating","holdings":"Kweichow Moutai, CATL, Ping An"},{"name":"Franklin FTSE China UCITS ETF","ter":0.19,"ytd":-10.82,"size_m_eur":1364,"isin":"IE00BHZRR147","dist":"Accumulating","holdings":"Tencent, Alibaba, Meituan"},{"name":"Xtrackers MSCI China UCITS ETF 1C","ter":0.65,"ytd":-12.52,"size_m_eur":958,"isin":"LU0514695690","dist":"Accumulating","holdings":"Tencent, Alibaba, Meituan"}],"Real Estate World":[{"name":"HSBC FTSE EPRA NAREIT Developed UCITS ETF USD","ter":0.24,"ytd":13.38,"size_m_eur":1848,"isin":"IE00B5L01S80","dist":"Distributing","holdings":"Prologis, American Tower, Welltower"},{"name":"iShares Developed Markets Property Yield UCITS ETF","ter":0.59,"ytd":12.95,"size_m_eur":1081,"isin":"IE00B1FZS350","dist":"Distributing","holdings":"Prologis, American Tower, Welltower"},{"name":"HSBC FTSE EPRA NAREIT Developed UCITS ETF USD (Acc)","ter":0.24,"ytd":13.42,"size_m_eur":816,"isin":"IE000G6GSP88","dist":"Accumulating","holdings":"Prologis, American Tower, Welltower"},{"name":"VanEck Global Real Estate UCITS ETF","ter":0.25,"ytd":11.53,"size_m_eur":403,"isin":"NL0009690239","dist":"Distributing","holdings":"Prologis, American Tower, Welltower"},{"name":"Amundi FTSE EPRA NAREIT Global UCITS ETF Acc","ter":0.24,"ytd":13.29,"size_m_eur":370,"isin":"LU1437018838","dist":"Accumulating","holdings":"Prologis, American Tower, Welltower"}],"Equity Telecommunication":[{"name":"iShares S&P 500 Communication Sector UCITS ETF USD (Acc)","ter":0.15,"ytd":-2,"size_m_eur":1095,"isin":"IE00BDDRF478","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Xtrackers MSCI USA Communication Services UCITS ETF 1D","ter":0.12,"ytd":-2.87,"size_m_eur":729,"isin":"IE00BNC1G707","dist":"Distributing","holdings":"Meta, Alphabet, Deutsche Telekom"},{"name":"Xtrackers MSCI World Communication Services UCITS ETF 1C","ter":0.25,"ytd":-0.61,"size_m_eur":418,"isin":"IE00BM67HR47","dist":"Accumulating","holdings":"Meta, Alphabet, Deutsche Telekom"},{"name":"State Street SPDR S&P U.S. Communication Services Select Sector UCITS ETF USD","ter":0.15,"ytd":-1.81,"size_m_eur":308,"isin":"IE00BFWFPX50","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Amundi STOXX Europe 600 Telecommunications UCITS ETF Dist","ter":0.3,"ytd":19.28,"size_m_eur":207,"isin":"LU2082999058","dist":"Distributing","holdings":"Meta, Alphabet, Deutsche Telekom"}],"Equity Utilities":[{"name":"iShares S&P 500 Utilities Sector UCITS ETF USD (Acc)","ter":0.15,"ytd":11.76,"size_m_eur":1171,"isin":"IE00B4KBBD01","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Xtrackers MSCI World Utilities UCITS ETF 1C","ter":0.25,"ytd":12.87,"size_m_eur":822,"isin":"IE00BM67HQ30","dist":"Accumulating","holdings":"NextEra, Iberdrola, Enel"},{"name":"iShares STOXX Europe 600 Utilities UCITS ETF (DE)","ter":0.47,"ytd":16.69,"size_m_eur":813,"isin":"DE000A0Q4R02","dist":"Distributing","holdings":"NextEra, Iberdrola, Enel"},{"name":"State Street SPDR MSCI Europe Utilities UCITS ETF EUR","ter":0.18,"ytd":17.29,"size_m_eur":688,"isin":"IE00BKWQ0P07","dist":"Accumulating","holdings":"NextEra, Iberdrola, Enel"},{"name":"Amundi STOXX Europe 600 Utilities UCITS ETF Acc","ter":0.3,"ytd":16.54,"size_m_eur":208,"isin":"LU1834988864","dist":"Accumulating","holdings":"NextEra, Iberdrola, Enel"}],"Equity Brazil":[{"name":"iShares MSCI Brazil UCITS ETF (DE) USD (Acc)","ter":0.31,"ytd":11.08,"size_m_eur":4029,"isin":"DE000A0Q4R85","dist":"Accumulating","holdings":"Vale, Petrobras, Ita\u00fa"},{"name":"iShares MSCI Brazil UCITS ETF (Dist)","ter":0.74,"ytd":13.52,"size_m_eur":420,"isin":"IE00B0M63516","dist":"Distributing","holdings":"Vale, Petrobras, Ita\u00fa"},{"name":"Amundi MSCI Brazil UCITS ETF Acc","ter":0.65,"ytd":12.16,"size_m_eur":340,"isin":"LU1900066207","dist":"Accumulating","holdings":"Vale, Petrobras, Ita\u00fa"},{"name":"Xtrackers MSCI Brazil UCITS ETF 1C","ter":0.25,"ytd":12.37,"size_m_eur":214,"isin":"LU0292109344","dist":"Accumulating","holdings":"Vale, Petrobras, Ita\u00fa"},{"name":"Franklin FTSE Brazil UCITS ETF","ter":0.19,"ytd":17.16,"size_m_eur":129,"isin":"IE00BHZRQY00","dist":"Accumulating","holdings":"Vale, Petrobras, Ita\u00fa"}],"Equity Financials":[{"name":"Amundi Euro Stoxx Banks UCITS ETF Acc","ter":0.3,"ytd":14.52,"size_m_eur":5658,"isin":"LU1829219390","dist":"Accumulating","holdings":"JPMorgan / Santander, BNP, Intesa"},{"name":"iShares STOXX Europe 600 Banks UCITS ETF (DE)","ter":0.47,"ytd":15.67,"size_m_eur":3333,"isin":"DE000A0F5UJ7","dist":"Distributing","holdings":"JPMorgan, HSBC, Allianz"},{"name":"Amundi STOXX Europe 600 Banks UCITS ETF Acc","ter":0.3,"ytd":15.49,"size_m_eur":2765,"isin":"LU1834983477","dist":"Accumulating","holdings":"JPMorgan, HSBC, Allianz"},{"name":"iShares EURO STOXX Banks 30-15 UCITS ETF (DE)","ter":0.52,"ytd":14.02,"size_m_eur":2449,"isin":"DE0006289309","dist":"Distributing","holdings":"JPMorgan / Santander, BNP, Intesa"},{"name":"iShares S&P 500 Financials Sector UCITS ETF (Acc)","ter":0.15,"ytd":3.07,"size_m_eur":1966,"isin":"IE00B4JNQZ49","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"}],"Equity Canada":[{"name":"iShares MSCI Canada UCITS ETF (Acc)","ter":0.48,"ytd":10.98,"size_m_eur":2057,"isin":"IE00B52SF786","dist":"Accumulating","holdings":"RBC, TD, Enbridge, Shopify"},{"name":"UBS MSCI Canada UCITS ETF CAD dis","ter":0.33,"ytd":11,"size_m_eur":756,"isin":"LU0446734872","dist":"Distributing","holdings":"RBC, TD, Enbridge, Shopify"},{"name":"UBS MSCI Canada UCITS ETF CAD acc","ter":0.33,"ytd":11.09,"size_m_eur":633,"isin":"LU0950672807","dist":"Accumulating","holdings":"RBC, TD, Enbridge, Shopify"},{"name":"HSBC MSCI Canada UCITS ETF USD","ter":0.35,"ytd":11.16,"size_m_eur":351,"isin":"IE00B51B7Z02","dist":"Distributing","holdings":"RBC, TD, Enbridge, Shopify"},{"name":"UBS MSCI Canada UCITS ETF hGBP acc","ter":0.36,"ytd":13.75,"size_m_eur":238,"isin":"LU1130156323","dist":"Accumulating","holdings":"RBC, TD, Enbridge, Shopify"}],"Equity Switzerland":[{"name":"UBS MSCI Switzerland 20/35 UCITS ETF CHF acc","ter":0.2,"ytd":9.62,"size_m_eur":2672,"isin":"LU0977261329","dist":"Accumulating","holdings":"Nestl\u00e9, Roche, Novartis"},{"name":"UBS MSCI Switzerland 20/35 UCITS ETF CHF dis","ter":0.2,"ytd":9.63,"size_m_eur":704,"isin":"LU0979892907","dist":"Distributing","holdings":"Nestl\u00e9, Roche, Novartis"},{"name":"iShares SLI UCITS ETF (DE)","ter":0.51,"ytd":9.24,"size_m_eur":572,"isin":"DE0005933964","dist":"Distributing","holdings":"Nestl\u00e9, Roche, Novartis"},{"name":"Xtrackers SLI UCITS ETF 1D","ter":0.25,"ytd":9.63,"size_m_eur":491,"isin":"LU0322248146","dist":"Distributing","holdings":"Nestl\u00e9, Roche, Novartis"},{"name":"Amundi MSCI Switzerland UCITS ETF CHF","ter":0.25,"ytd":10.53,"size_m_eur":375,"isin":"LU1681044993","dist":"Accumulating","holdings":"Nestl\u00e9, Roche, Novartis"}],"Equity World":[{"name":"iShares Core MSCI World UCITS ETF USD (Acc)","ter":0.2,"ytd":11.77,"size_m_eur":122331,"isin":"IE00B4L5Y983","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Vanguard FTSE All-World UCITS ETF (USD) Accumulating","ter":0.19,"ytd":13.61,"size_m_eur":42582,"isin":"IE00BK5BQT80","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares MSCI ACWI UCITS ETF USD (Acc)","ter":0.2,"ytd":13.63,"size_m_eur":29341,"isin":"IE00B6R52259","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Vanguard FTSE All-World UCITS ETF (USD) Distributing","ter":0.19,"ytd":13.06,"size_m_eur":22449,"isin":"IE00B3RBWM25","dist":"Distributing","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Xtrackers MSCI World UCITS ETF 1C","ter":0.12,"ytd":11.82,"size_m_eur":19393,"isin":"IE00BJ0KDQ92","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"}],"Equity Consumer Staples":[{"name":"Xtrackers MSCI World Consumer Staples UCITS ETF 1C","ter":0.25,"ytd":10.63,"size_m_eur":794,"isin":"IE00BM67HN09","dist":"Accumulating","holdings":"Nestl\u00e9, P&G, Coca-Cola"},{"name":"iShares MSCI Europe Consumer Staples Sector UCITS ETF EUR (Acc)","ter":0.18,"ytd":5.93,"size_m_eur":455,"isin":"IE00BMW42074","dist":"Accumulating","holdings":"Nestl\u00e9, P&G, Coca-Cola"},{"name":"iShares S&P 500 Consumer Staples Sector UCITS ETF","ter":0.15,"ytd":12.94,"size_m_eur":426,"isin":"IE00B40B8R38","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares STOXX Europe 600 Food & Beverage UCITS ETF (DE)","ter":0.46,"ytd":9.05,"size_m_eur":299,"isin":"DE000A0H08H3","dist":"Distributing","holdings":"Nestl\u00e9, P&G, Coca-Cola"},{"name":"State Street SPDR S&P U.S. Consumer Staples Select Sector UCITS ETF USD","ter":0.15,"ytd":12.93,"size_m_eur":240,"isin":"IE00BWBXM385","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"}],"Equity United Kingdom":[{"name":"iShares Core FTSE 100 UCITS ETF GBP (Dist)","ter":0.07,"ytd":9.62,"size_m_eur":18317,"isin":"IE0005042456","dist":"Distributing","holdings":"AstraZeneca, Shell, HSBC, Unilever"},{"name":"Vanguard FTSE 100 UCITS ETF (GBP) Distributing","ter":0.09,"ytd":8.17,"size_m_eur":5231,"isin":"IE00B810Q511","dist":"Distributing","holdings":"AstraZeneca, Shell, HSBC, Unilever"},{"name":"iShares Core FTSE 100 UCITS ETF GBP (Acc)","ter":0.07,"ytd":9.62,"size_m_eur":3594,"isin":"IE00B53HP851","dist":"Accumulating","holdings":"AstraZeneca, Shell, HSBC, Unilever"},{"name":"Vanguard FTSE 100 UCITS ETF (GBP) Accumulating","ter":0.09,"ytd":9.33,"size_m_eur":2228,"isin":"IE00BFMXYP42","dist":"Accumulating","holdings":"AstraZeneca, Shell, HSBC, Unilever"},{"name":"UBS MSCI United Kingdom UCITS ETF GBP acc","ter":0.2,"ytd":9.44,"size_m_eur":2037,"isin":"LU0950670850","dist":"Accumulating","holdings":"AstraZeneca, Shell, HSBC, Unilever"}],"Equity Australia":[{"name":"iShares MSCI Australia UCITS ETF","ter":0.5,"ytd":11.43,"size_m_eur":504,"isin":"IE00B5377D42","dist":"Accumulating","holdings":"BHP, CBA, CSL"},{"name":"UBS MSCI Australia UCITS ETF AUD acc","ter":0.4,"ytd":11.38,"size_m_eur":244,"isin":"IE00BD4TY451","dist":"Accumulating","holdings":"BHP, CBA, CSL"},{"name":"Amundi Australia S&P/ASX 200 UCITS ETF Dist","ter":0.4,"ytd":9.37,"size_m_eur":136,"isin":"LU0496786905","dist":"Distributing","holdings":"BHP, CBA, CSL"},{"name":"UBS MSCI Australia UCITS ETF AUD dis","ter":0.4,"ytd":11.23,"size_m_eur":89,"isin":"IE00BD4TY345","dist":"Distributing","holdings":"BHP, CBA, CSL"},{"name":"Xtrackers S&P/ASX 200 UCITS ETF 1D","ter":0.5,"ytd":9.14,"size_m_eur":63,"isin":"LU0328474803","dist":"Distributing","holdings":"BHP, CBA, CSL"}],"Equity Germany":[{"name":"iShares Core DAX UCITS ETF (DE) EUR (Acc)","ter":0.16,"ytd":1.5,"size_m_eur":8494,"isin":"DE0005933931","dist":"Accumulating","holdings":"SAP, Siemens, Allianz"},{"name":"Xtrackers DAX UCITS ETF 1C","ter":0.09,"ytd":1.68,"size_m_eur":6897,"isin":"LU0274211480","dist":"Accumulating","holdings":"SAP, Siemens, Allianz"},{"name":"Deka DAX UCITS ETF","ter":0.15,"ytd":1.49,"size_m_eur":1805,"isin":"DE000ETFL011","dist":"Accumulating","holdings":"SAP, Siemens, Allianz"},{"name":"Amundi Core DAX UCITS ETF Dist","ter":0.08,"ytd":1.68,"size_m_eur":1469,"isin":"LU2611732046","dist":"Distributing","holdings":"SAP, Siemens, Allianz"},{"name":"Amundi ETF DAX UCITS ETF DR","ter":0.1,"ytd":1.66,"size_m_eur":1383,"isin":"FR0010655712","dist":"Accumulating","holdings":"SAP, Siemens, Allianz"}],"Equity Health Care":[{"name":"Xtrackers MSCI World Health Care UCITS ETF 1C","ter":0.25,"ytd":3.93,"size_m_eur":3034,"isin":"IE00BM67HK77","dist":"Accumulating","holdings":"Eli Lilly, UnitedHealth, Novo Nordisk"},{"name":"iShares S&P 500 Health Care Sector UCITS ETF (Acc)","ter":0.15,"ytd":5.12,"size_m_eur":2387,"isin":"IE00B43HR379","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares MSCI Europe Health Care Sector UCITS ETF EUR (Acc)","ter":0.18,"ytd":3.23,"size_m_eur":832,"isin":"IE00BMW42181","dist":"Accumulating","holdings":"Eli Lilly, UnitedHealth, Novo Nordisk"},{"name":"Amundi STOXX Europe 600 Healthcare UCITS ETF Acc","ter":0.3,"ytd":2.85,"size_m_eur":785,"isin":"LU1834986900","dist":"Accumulating","holdings":"Eli Lilly, UnitedHealth, Novo Nordisk"},{"name":"Xtrackers MSCI USA Health Care UCITS ETF 1D","ter":0.12,"ytd":4.65,"size_m_eur":745,"isin":"IE00BCHWNW54","dist":"Distributing","holdings":"Eli Lilly, UnitedHealth, Novo Nordisk"}],"Equity Pakistan":[{"name":"Xtrackers MSCI Pakistan Swap UCITS ETF 1C","ter":0.85,"ytd":3.9,"size_m_eur":20,"isin":"LU0659579147","dist":"Accumulating","holdings":"HBL, Lucky Cement, OGDC"}],"Equity Consumer Discretionary":[{"name":"iShares S&P 500 Consumer Discretionary Sector UCITS ETF (Acc)","ter":0.15,"ytd":0.21,"size_m_eur":719,"isin":"IE00B4MCHD36","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"Xtrackers MSCI World Consumer Discretionary UCITS ETF 1C","ter":0.25,"ytd":-2.35,"size_m_eur":285,"isin":"IE00BM67HP23","dist":"Accumulating","holdings":"Amazon, Tesla, LVMH"},{"name":"Xtrackers MSCI USA Consumer Discretionary UCITS ETF 1D","ter":0.12,"ytd":0.42,"size_m_eur":143,"isin":"IE00BGQYRR35","dist":"Distributing","holdings":"Amazon, Tesla, LVMH"},{"name":"State Street SPDR S&P U.S. Consumer Discretionary Select Sector UCITS ETF USD","ter":0.15,"ytd":0.19,"size_m_eur":110,"isin":"IE00BWBXM278","dist":"Accumulating","holdings":"Apple, Microsoft, Nvidia, Amazon"},{"name":"iShares MSCI Europe Consumer Discretionary Sector UCITS ETF EUR (Acc)","ter":0.18,"ytd":-8.41,"size_m_eur":92,"isin":"IE00BMW42298","dist":"Accumulating","holdings":"Amazon, Tesla, LVMH"}],"Equity India":[{"name":"iShares MSCI India UCITS ETF USD (Acc)","ter":0.65,"ytd":-6.96,"size_m_eur":4554,"isin":"IE00BZCQB185","dist":"Accumulating","holdings":"Reliance, HDFC Bank, Infosys"},{"name":"Franklin FTSE India UCITS ETF","ter":0.19,"ytd":-4.68,"size_m_eur":1805,"isin":"IE00BHZRQZ17","dist":"Accumulating","holdings":"Reliance, HDFC Bank, Infosys"},{"name":"Amundi MSCI India Swap UCITS ETF EUR Acc","ter":0.85,"ytd":-6.64,"size_m_eur":799,"isin":"FR0010361683","dist":"Accumulating","holdings":"Reliance, HDFC Bank, Infosys"},{"name":"Xtrackers MSCI India Swap UCITS ETF 1C","ter":0.19,"ytd":-6.39,"size_m_eur":520,"isin":"LU0514695187","dist":"Accumulating","holdings":"Reliance, HDFC Bank, Infosys"},{"name":"Amundi MSCI India Swap UCITS ETF USD Acc","ter":0.85,"ytd":-6.61,"size_m_eur":196,"isin":"FR0010375766","dist":"Accumulating","holdings":"Reliance, HDFC Bank, Infosys"}]}
# Catalog extensions — added v1.132.0 (Semiconductor + EM ex-China)
_ETF_CATALOG['Equity Semiconductors'] = [
    {'name': 'VanEck Semiconductor UCITS ETF', 'ter': 0.35, 'ytd': None, 'size_m_eur': 8074,
     'isin': 'IE00BMC38736', 'dist': 'Accumulating',
     'holdings': 'NVDA, TSMC, ASML, Broadcom, AMD, Texas Instruments'},
]
_ETF_CATALOG['Equity Emerging Markets ex China'] = [
    {'name': 'Amundi MSCI Emerging Ex China UCITS ETF Acc', 'ter': 0.15, 'ytd': 44.50, 'size_m_eur': 500,
     'isin': 'LU2009202107', 'dist': 'Accumulating', 'holdings': 'TSMC, Samsung, Reliance, Petrobras (no China)'},
    {'name': 'Xtrackers MSCI EM ex China UCITS ETF 1C', 'ter': 0.18, 'ytd': 44.32, 'size_m_eur': 400,
     'isin': 'IE00BM67HJ62', 'dist': 'Accumulating', 'holdings': 'TSMC, Samsung, Reliance, Petrobras (no China)'},
    {'name': 'iShares MSCI EM ex-China UCITS ETF USD (Acc)', 'ter': 0.18, 'ytd': 43.90, 'size_m_eur': 300,
     'isin': 'IE00BMG6Z448', 'dist': 'Accumulating', 'holdings': 'TSMC, Samsung, Reliance (no China)'},
]


# ========================= Momentum-Watch Watchlist ==========================
# Non-leveraged ETFs with YTD >= 35% (threshold lowered from 40% per v1.132.0 audit).
# 55 funds total: ranks 1-34 (original >=40% YTD) + ranks 35-55 (35-39.99% YTD).
# Owner-confirmed: include 1 crypto product (21shares Hyperliquid ETP, rank 1).
# Leveraged/short products EXCLUDED throughout.
_MOMENTUM_WATCH = [
    {'rank': 1, 'name': '21shares Hyperliquid ETP', 'category': 'Cryptocurrencies', 'ytd': 140.2, 'isin': 'CH1471826029', 'ter': 2.5, 'ret_1y': None, 'holdings': 'Hyperliquid (HYPE)', 'note': 'crypto -- different risk class'},
    {'rank': 2, 'name': 'Franklin FTSE Korea UCITS ETF', 'category': 'Equity South Korea', 'ytd': 119.93, 'isin': 'IE00BHZRR030', 'ter': 0.09, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 3, 'name': 'iShares MSCI Korea UCITS ETF (Acc)', 'category': 'Equity South Korea', 'ytd': 117.37, 'isin': 'IE00B5W4TY14', 'ter': 0.65, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 4, 'name': 'HSBC MSCI Korea Capped UCITS ETF USD', 'category': 'Equity South Korea', 'ytd': 113.72, 'isin': 'IE00B3Z0X395', 'ter': 0.5, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 5, 'name': 'Amundi MSCI Korea UCITS ETF Acc', 'category': 'Equity South Korea', 'ytd': 113.25, 'isin': 'LU1900066975', 'ter': 0.45, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 6, 'name': 'Xtrackers MSCI Korea UCITS ETF 1C', 'category': 'Equity South Korea', 'ytd': 113.03, 'isin': 'LU0292100046', 'ter': 0.45, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 7, 'name': 'iShares MSCI Korea UCITS ETF (Dist)', 'category': 'Equity South Korea', 'ytd': 112.21, 'isin': 'IE00B0M63391', 'ter': 0.65, 'ret_1y': None, 'holdings': 'Samsung Electronics, SK Hynix, Hyundai'},
    {'rank': 8, 'name': 'IncomeShares AMD Options ETP', 'category': 'Active ETFs Equity', 'ytd': 111.55, 'isin': 'XS3068775694', 'ter': 0.55, 'ret_1y': None, 'holdings': 'AMD'},
    {'rank': 9, 'name': 'Xtrackers MSCI Taiwan UCITS ETF 1D', 'category': 'Equity Taiwan', 'ytd': 71.9, 'isin': 'LU2928641757', 'ter': 0.21, 'ret_1y': None, 'holdings': 'TSMC, Hon Hai, MediaTek'},
    {'rank': 10, 'name': 'Franklin FTSE Taiwan UCITS ETF SINGLCLASS', 'category': 'Equity Taiwan', 'ytd': 71.64, 'isin': 'IE000CM02H85', 'ter': 0.19, 'ret_1y': None, 'holdings': 'TSMC, Hon Hai, MediaTek'},
    {'rank': 11, 'name': 'Xtrackers MSCI Taiwan UCITS ETF 1C', 'category': 'Equity Taiwan', 'ytd': 71.51, 'isin': 'LU0292109187', 'ter': 0.65, 'ret_1y': None, 'holdings': 'TSMC, Hon Hai, MediaTek'},
    {'rank': 12, 'name': 'iShares MSCI Taiwan UCITS ETF', 'category': 'Equity Taiwan', 'ytd': 71.33, 'isin': 'IE00B0M63623', 'ter': 0.74, 'ret_1y': None, 'holdings': 'TSMC, Hon Hai, MediaTek'},
    {'rank': 13, 'name': 'HSBC MSCI Taiwan Capped UCITS ETF USD', 'category': 'Equity Taiwan', 'ytd': 71.0, 'isin': 'IE00B3S1J086', 'ter': 0.5, 'ret_1y': None, 'holdings': 'TSMC, Hon Hai, MediaTek'},
    {'rank': 14, 'name': 'iShares AI Innovation Active UCITS ETF USD (Acc)', 'category': 'Active ETFs Equity', 'ytd': 56.4, 'isin': 'IE000G0E83X3', 'ter': 0.73, 'ret_1y': 90.22, 'holdings': 'Nvidia, Microsoft, TSMC, Palantir'},
    {'rank': 15, 'name': 'Vanguard FTSE Developed Asia Pacific ex Japan UCITS ETF Distributing', 'category': 'Equity Asia Pacific', 'ytd': 51.98, 'isin': 'IE00B9F5YL18', 'ter': 0.15, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 16, 'name': 'Vanguard FTSE Developed Asia Pacific ex Japan UCITS ETF (USD) Accumulating', 'category': 'Equity Asia Pacific', 'ytd': 51.93, 'isin': 'IE00BK5BQZ41', 'ter': 0.15, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 17, 'name': 'UBS MSCI EM ex China Socially Responsible UCITS ETF USD acc', 'category': 'Equity Climate Change', 'ytd': 51.4, 'isin': 'IE00BNC0MH93', 'ter': 0.2, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 18, 'name': 'iShares MSCI Europe Information Technology Sector UCITS ETF EUR (Acc)', 'category': 'Equity Technology', 'ytd': 45.97, 'isin': 'IE00BMW42413', 'ter': 0.18, 'ret_1y': None, 'holdings': 'Apple, Microsoft, Nvidia, Broadcom'},
    {'rank': 19, 'name': 'Franklin FTSE Asia ex China ex Japan UCITS ETF', 'category': 'Equity Asia Pacific', 'ytd': 45.8, 'isin': 'IE00BFWXDV39', 'ter': 0.14, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 20, 'name': 'Amundi MSCI Emerging Ex China UCITS ETF Acc', 'category': 'Equity Emerging Markets', 'ytd': 44.5, 'isin': 'LU2009202107', 'ter': 0.15, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 21, 'name': 'State Street SPDR MSCI Europe Technology UCITS ETF EUR', 'category': 'Equity Technology', 'ytd': 44.44, 'isin': 'IE00BKWQ0K51', 'ter': 0.18, 'ret_1y': None, 'holdings': 'Apple, Microsoft, Nvidia, Broadcom'},
    {'rank': 22, 'name': 'Xtrackers MSCI Emerging Markets ex China UCITS ETF 1C', 'category': 'Equity Emerging Markets', 'ytd': 44.32, 'isin': 'IE00BM67HJ62', 'ter': 0.16, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 23, 'name': 'UBS MSCI EM ex China UCITS ETF USD acc', 'category': 'Equity Emerging Markets', 'ytd': 44.18, 'isin': 'LU2050966394', 'ter': 0.16, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 24, 'name': 'BNP Paribas Easy II MSCI Emerging Markets ex-China PAB UCITS ETF USD Dist', 'category': 'Equity Climate Change', 'ytd': 44.09, 'isin': 'IE000G5IRVY3', 'ter': 0.27, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 25, 'name': 'ARK Genomic Revolution UCITS ETF USD Accumulating', 'category': 'Active ETFs Equity', 'ytd': 43.94, 'isin': 'IE000O5M6XO1', 'ter': 0.75, 'ret_1y': 62.61, 'holdings': 'Nvidia, Microsoft, TSMC, Palantir'},
    {'rank': 26, 'name': 'BNP Paribas Easy II MSCI Emerging Markets ex-China PAB UCITS ETF USD Acc', 'category': 'Equity Climate Change', 'ytd': 43.92, 'isin': 'IE000M4Z0RA5', 'ter': 0.27, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 27, 'name': 'iShares MSCI EM ex-China UCITS ETF USD (Acc)', 'category': 'Equity Emerging Markets', 'ytd': 43.9, 'isin': 'IE00BMG6Z448', 'ter': 0.18, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 28, 'name': 'iShares MSCI EM ex-China UCITS ETF USD (Dist)', 'category': 'Equity Emerging Markets', 'ytd': 43.65, 'isin': 'IE000W8RYVC0', 'ter': 0.18, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 29, 'name': 'Xtrackers Nikkei 225 UCITS ETF 2D EUR Hedged', 'category': 'Equity Japan', 'ytd': 42.78, 'isin': 'LU1875395870', 'ter': 0.19, 'ret_1y': None, 'holdings': 'Toyota, Sony, Keyence, Mitsubishi UFJ'},
    {'rank': 30, 'name': 'Xtrackers Nikkei 225 UCITS ETF 1C', 'category': 'Equity Japan', 'ytd': 42.36, 'isin': 'LU2196470426', 'ter': 0.09, 'ret_1y': None, 'holdings': 'Toyota, Sony, Keyence, Mitsubishi UFJ'},
    {'rank': 31, 'name': 'Xtrackers Nikkei 225 UCITS ETF 1D', 'category': 'Equity Japan', 'ytd': 42.35, 'isin': 'LU0839027447', 'ter': 0.09, 'ret_1y': None, 'holdings': 'Toyota, Sony, Keyence, Mitsubishi UFJ'},
    {'rank': 32, 'name': 'iShares Nikkei 225 UCITS ETF (Acc)', 'category': 'Equity Japan', 'ytd': 41.12, 'isin': 'IE00B52MJD48', 'ter': 0.48, 'ret_1y': None, 'holdings': 'Toyota, Sony, Keyence, Mitsubishi UFJ'},
    {'rank': 33, 'name': 'iShares Nikkei 225 UCITS ETF (DE)', 'category': 'Equity Japan', 'ytd': 41.0, 'isin': 'DE000A0H08D2', 'ter': 0.51, 'ret_1y': None, 'holdings': 'Toyota, Sony, Keyence, Mitsubishi UFJ'},
    {'rank': 34, 'name': 'First Trust Nasdaq Clean Edge Green Energy UCITS ETF Acc', 'category': 'Equity Clean Energy', 'ytd': 40.74, 'isin': 'IE00BDBRT036', 'ter': 0.6, 'ret_1y': None, 'holdings': 'First Solar, Vestas, Enphase'},
    {'rank': 35, 'name': 'Xtrackers MSCI Global Circular Economy UCITS ETF 1C', 'category': 'Equity Circular Economy', 'ytd': 39.42, 'isin': 'IE000Y6ZXZ48', 'ter': 0.35, 'ret_1y': None, 'holdings': 'Apple, Microsoft, Nvidia, Amazon'},
    {'rank': 36, 'name': 'Amundi MSCI New Energy UCITS ETF Dist', 'category': 'Equity Clean Energy', 'ytd': 39.27, 'isin': 'FR0010524777', 'ter': 0.6, 'ret_1y': None, 'holdings': 'First Solar, Vestas, Enphase'},
    {'rank': 37, 'name': 'VanEck Oil Services UCITS ETF A', 'category': 'Equity Energy', 'ytd': 39.17, 'isin': 'IE000NXF88S1', 'ter': 0.35, 'ret_1y': None, 'holdings': 'ExxonMobil, Chevron, Shell, TotalEnergies'},
    {'rank': 38, 'name': 'BNP Paribas Easy II MSCI Emerging Markets ex-China PAB UCITS ETF EUR Hedged Acc', 'category': 'Equity Climate Change', 'ytd': 38.05, 'isin': 'IE000Y65F5C2', 'ter': 0.3, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 39, 'name': 'HSBC Asia Pacific Ex Japan Screened Equity UCITS ETF USD', 'category': 'Equity Climate Change', 'ytd': 37.99, 'isin': 'IE00BKY58G26', 'ter': 0.25, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 40, 'name': 'HSBC Asia Pacific Ex Japan Screened Equity UCITS ETF USD (Dist)', 'category': 'Equity Climate Change', 'ytd': 37.97, 'isin': 'IE000P1WR081', 'ter': 0.25, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 41, 'name': 'HSBC MSCI AC Far East ex Japan UCITS ETF USD (Dist)', 'category': 'Equity Asia Pacific', 'ytd': 36.75, 'isin': 'IE00022VXYM7', 'ter': 0.45, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 42, 'name': 'Fidelity Emerging Markets Quality Income UCITS ETF INC-USD', 'category': 'Equity Dividend Emerging Markets', 'ytd': 36.67, 'isin': 'IE00BYSX4739', 'ter': 0.5, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 43, 'name': 'HSBC MSCI AC Far East ex Japan UCITS ETF USD', 'category': 'Equity Asia Pacific', 'ytd': 36.6, 'isin': 'IE00BBQ2W338', 'ter': 0.45, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 44, 'name': 'Fidelity Emerging Markets Quality Income UCITS ETF ACC-USD', 'category': 'Equity Dividend Emerging Markets', 'ytd': 36.47, 'isin': 'IE00BYSX4846', 'ter': 0.5, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 45, 'name': 'Deka Future Energy ESG UCITS ETF', 'category': 'Equity Clean Energy', 'ytd': 36.13, 'isin': 'DE000ETFL607', 'ter': 0.55, 'ret_1y': None, 'holdings': 'First Solar, Vestas, Enphase'},
    {'rank': 46, 'name': 'L&G Clean Energy UCITS ETF', 'category': 'Equity Clean Energy', 'ytd': 36.07, 'isin': 'IE00BK5BCH80', 'ter': 0.49, 'ret_1y': None, 'holdings': 'First Solar, Vestas, Enphase'},
    {'rank': 47, 'name': 'JPMorgan Global Emerging Markets Research Enhanced Index Equity SRI Paris Aligned Active UCITS ETF EUR (acc)', 'category': 'Active ETFs Equity', 'ytd': 35.87, 'isin': 'IE000AV35A01', 'ter': 0.3, 'ret_1y': 55.55, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 48, 'name': 'Robeco 3D EM Equity UCITS ETF USD Acc', 'category': 'Active ETFs Equity', 'ytd': 35.68, 'isin': 'IE0002Z12PN9', 'ter': 0.3, 'ret_1y': 55.78, 'holdings': 'Enhanced-index large caps'},
    {'rank': 49, 'name': 'UBS MSCI EM Socially Responsible UCITS ETF USD acc', 'category': 'Equity Climate Change', 'ytd': 35.57, 'isin': 'LU1048313974', 'ter': 0.24, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 50, 'name': 'JPMorgan Global Emerging Markets Research Enhanced Index Equity SRI Paris Aligned Active UCITS ETF USD (dist)', 'category': 'Active ETFs Equity', 'ytd': 35.52, 'isin': 'IE000CYGD0V1', 'ter': 0.3, 'ret_1y': 55.53, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 51, 'name': 'UBS MSCI EM Socially Responsible UCITS ETF USD dis', 'category': 'Equity Climate Change', 'ytd': 35.46, 'isin': 'LU1048313891', 'ter': 0.24, 'ret_1y': None, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 52, 'name': 'iShares MSCI AC Far East ex-Japan UCITS ETF', 'category': 'Equity Asia Pacific', 'ytd': 35.37, 'isin': 'IE00B0M63730', 'ter': 0.74, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 53, 'name': 'JPMorgan Global Emerging Markets Research Enhanced Index Equity SRI Paris Aligned Active UCITS ETF USD (acc)', 'category': 'Active ETFs Equity', 'ytd': 35.36, 'isin': 'IE000ANHU3J3', 'ter': 0.3, 'ret_1y': 55.55, 'holdings': 'TSMC, Tencent, Samsung, Alibaba'},
    {'rank': 54, 'name': 'iShares MSCI AC Far East ex-Japan UCITS ETF USD (Acc)', 'category': 'Equity Asia Pacific', 'ytd': 35.34, 'isin': 'IE00BKPX3K41', 'ter': 0.74, 'ret_1y': None, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    {'rank': 55, 'name': 'iShares Asia ex Japan Equity Enhanced Active UCITS ETF USD (Acc)', 'category': 'Active ETFs Equity', 'ytd': 35.32, 'isin': 'IE000D5R9C23', 'ter': 0.3, 'ret_1y': 57.69, 'holdings': 'TSMC, Samsung, Tencent, BHP'},
    # v1.138.0: top 5 Nasdaq-100 UCITS ETFs, owner-requested despite sitting below the 35% YTD
    # cutoff that defines this list -- included for direct US mega-cap tech coverage. Ranked by
    # trailing 1-year return, matching the source sheet's own stated methodology ("Top Nasdaq
    # ETFs", justETF as of 31/05/2026). Deliberately numbered 56-60 (continuing past the natural
    # 1-55 cutoff) so they sort as their own final category block, never blended into the ">=35%"
    # framing the rest of the table honestly claims. Real TER/YTD/1Y/holdings, zero fabrication --
    # all 18 Nasdaq-100 funds in the source file were checked; these 5 are the top 5 by 1yr return.
    {'rank': 56, 'name': 'Amundi Core Nasdaq-100 Swap UCITS ETF Acc', 'category': 'Equity United States (Nasdaq-100, below 35% threshold)', 'ytd': 20.05, 'isin': 'LU1829221024', 'ter': 0.22, 'ret_1y': 39.13, 'holdings': 'Nvidia, Apple, Microsoft, Broadcom'},
    {'rank': 57, 'name': 'UBS Nasdaq-100 UCITS ETF USD acc', 'category': 'Equity United States (Nasdaq-100, below 35% threshold)', 'ytd': 20.11, 'isin': 'IE000SB4G4I4', 'ter': 0.13, 'ret_1y': 39.04, 'holdings': 'Nvidia, Apple, Microsoft, Broadcom'},
    {'rank': 58, 'name': 'UBS Nasdaq-100 UCITS ETF USD dis', 'category': 'Equity United States (Nasdaq-100, below 35% threshold)', 'ytd': 20.07, 'isin': 'IE0003RQ9F90', 'ter': 0.13, 'ret_1y': 39.02, 'holdings': 'Nvidia, Apple, Microsoft, Broadcom'},
    {'rank': 59, 'name': 'Invesco Nasdaq-100 Swap UCITS ETF Dist', 'category': 'Equity United States (Nasdaq-100, below 35% threshold)', 'ytd': 19.97, 'isin': 'IE000RUF4QN8', 'ter': 0.20, 'ret_1y': 39.01, 'holdings': 'Nvidia, Apple, Microsoft, Broadcom'},
    {'rank': 60, 'name': 'Invesco Nasdaq-100 Swap UCITS ETF Acc', 'category': 'Equity United States (Nasdaq-100, below 35% threshold)', 'ytd': 20.19, 'isin': 'IE00BNRQM384', 'ter': 0.20, 'ret_1y': 39.00, 'holdings': 'Nvidia, Apple, Microsoft, Broadcom'},
]
# ========================= end Momentum-Watch =================================

# ======================= Hydrogen Economy Thematic Watch ======================
# 4 hydrogen UCITS ETFs -- ISINs confirmed from justETF/VanEck/L&G/GlobalX.
# Ranked by AUM descending (liquidity proxy). YTD blank in source (not in
# main universe dumps); 6M and 1Y returns shown instead.
# Invesco (IE00053WDH64, EUR9m) excluded as too illiquid for IBKR execution.
# v1.136.0: FULL RE-VERIFICATION -- the original v1.132.0 data for this block was built in a
# research pass whose search results were later lost to context compaction, and turned out to
# be wrong across every fund: 3 of 4 holdings strings were an IDENTICAL copy-pasted placeholder
# ("Linde, Air Liquide, Plug Power, Nel, Ballard") rather than each fund's real distinct top
# holdings, and every ret_6m/ret_1y/size_m_eur figure was fabricated (e.g. Global X showed
# 104.33%/314.84% 6M/1Y when the real justETF-verified figures are 22.15%/211.88% -- off by
# ~5x and ~1.5x respectively). Every field below was re-derived from a direct justETF fetch of
# that exact ISIN's own page (not a search snippet, not memory) on 2026-07-01. ISINs themselves
# were confirmed correct on the original pass (cross-checked again here via justETF + issuer
# sites) -- the fabrication was in the return/holdings/AUM detail fields, not fund identity.
_HYDROGEN_WATCH = [
    {'rank': 1, 'name': 'L&G Hydrogen Economy UCITS ETF USD Acc', 'isin': 'IE00BMYDM794',
     'ter': 0.49, 'size_m_eur': 523, 'ticker_lse': 'HTWO', 'ret_6m': 44.51, 'ret_1y': 102.83,
     'holdings': 'Hyundai Motor, Chemours, Siemens Energy, Weichai Power, \u00d8rsted'},
    {'rank': 2, 'name': 'Amundi Global Hydrogen UCITS ETF Acc', 'isin': 'FR0010930644',
     'ter': 0.45, 'size_m_eur': 254, 'ticker_lse': 'ANRJ', 'ret_6m': 27.29, 'ret_1y': 73.43,
     'holdings': 'IHI Corp, Siemens Energy, Bloom Energy, Cummins, Linde Plc'},
    {'rank': 3, 'name': 'VanEck Hydrogen Economy UCITS ETF', 'isin': 'IE00BMDH1538',
     'ter': 0.55, 'size_m_eur': 120, 'ticker_lse': 'HDRO', 'ret_6m': 45.04, 'ret_1y': 82.84,
     'holdings': 'Bloom Energy, Plug Power, Doosan Fuel Cell, Ceres Power, ITM Power'},
    {'rank': 4, 'name': 'Global X Hydrogen UCITS ETF USD Acc', 'isin': 'IE0002RPS3K2',
     'ter': 0.50, 'size_m_eur': 23, 'ticker_lse': 'HYGN', 'ret_6m': 22.15, 'ret_1y': 211.88,
     'holdings': 'Bloom Energy, Doosan Fuel Cell, Plug Power, Ballard Power, VINATECH',
     'note': 'highest return but smallest AUM -- check liquidity before trading'},
]
# ======================= end Hydrogen Watch ====================================

# ======================= Physical Precious Metals ETCs ========================
# Physical-backed gold and silver ETCs, IBKR-accessible on LSE.
# No equity counterparty risk -- metal held in allocated vaults.
# Full analysis (trend, RSI, COT positioning) on Tab 12 Metals.
# Use Tab 16 to see these as tradeable UCITS products; use Tab 12 for signals.
_METALS_ETC_WATCH = [
    {'rank': 1, 'name': 'iShares Physical Gold UCITS ETC', 'isin': 'IE00B4ND3602',
     'ter': 0.12, 'ticker_lse': 'SGLN', 'metal': 'Gold', 'replication': 'Physical'},
    {'rank': 2, 'name': 'Invesco Physical Gold ETC', 'isin': 'IE00B579F325',
     'ter': 0.19, 'ticker_lse': 'SGLD', 'metal': 'Gold', 'replication': 'Physical'},
    {'rank': 3, 'name': 'iShares Physical Silver UCITS ETC', 'isin': 'IE00B4NCWG09',
     'ter': 0.20, 'ticker_lse': 'SSLN', 'metal': 'Silver', 'replication': 'Physical'},
    {'rank': 4, 'name': 'iShares Physical Platinum ETC', 'isin': 'IE00B4LHWP62',
     'ter': 0.20, 'ticker_lse': 'SPLT', 'metal': 'Platinum', 'replication': 'Physical'},
    {'rank': 5, 'name': 'iShares Physical Palladium ETC', 'isin': 'IE00B4556L06',
     'ter': 0.20, 'ticker_lse': 'SPDM', 'metal': 'Palladium', 'replication': 'Physical'},
    {'rank': 6, 'name': 'WisdomTree Copper', 'isin': 'GB00B15KXQ89',
     'ter': 0.49, 'ticker_lse': 'COPA', 'metal': 'Copper', 'replication': 'Synthetic'},
]
# ======================= end Metals ETCs ======================================



def log(msg):
    ts = dt.datetime.utcnow().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def warn(msg):
    WARNINGS.append(msg)
    log(f'  ⚠ {msg}')


def _series_trend(vals, w=(1,4,13)):
    """vals oldest->newest floats; returns {wow,mom,qoq (+_dir)} as window depth allows."""
    out={}
    vals=[v for v in (vals or []) if v is not None]
    if len(vals)<2: return out
    cur=vals[-1]
    for label,n in zip(('wow','mom','qoq'), w):
        if len(vals)>n:
            d=round(cur-vals[-1-n],4); out[label]=d
            out[label+'_dir']='up' if d>0 else ('down' if d<0 else 'flat')
    return out

def _push_hist(existing, date_str, value, cap=160):
    """Dedup-by-report-date {d,v} history (latest per date wins). Migrates old flat lists."""
    hist=[h if isinstance(h,dict) else {'d':None,'v':h} for h in (existing or [])]
    if value is not None:
        if hist and date_str is not None and hist[-1].get('d')==date_str:
            hist[-1]={'d':date_str,'v':value}
        else:
            hist.append({'d':date_str,'v':value})
    return hist[-cap:]

def _hist_trend(hist, w=(1,4,13)):
    return _series_trend([h['v'] for h in (hist or []) if isinstance(h,dict) and h.get('v') is not None], w)

def _print_trend(vals, windows):
    """Wave T3: cadence-matched trend for monthly/quarterly macro PRINTS.
    vals oldest->newest; windows=[(label,n),...] e.g. [('mom',1),('qoq',3),('yoy',12)].
    Unlike _series_trend (which fixes wow/mom/qoq), labels are caller-supplied so a
    1-step monthly change reads 'mom' (not 'wow') and a 12-step reads 'yoy'."""
    out={}
    vals=[v for v in (vals or []) if v is not None]
    if len(vals)<2: return out
    cur=vals[-1]
    for label,n in windows:
        if len(vals)>n:
            d=round(cur-vals[-1-n],4); out[label]=d
            out[label+'_dir']='up' if d>0 else ('down' if d<0 else 'flat')
    return out

def safe_get(d, *keys, default=None):
    try:
        for k in keys:
            d = d[k]
        return d
    except Exception:
        return default


# =============================================================
# 1. US MACRO via FRED  (+ live oil from Yahoo)
# =============================================================
def fetch_live_oil():
    out = {}
    try:
        import yfinance as yf
        for key, sym in (('wti', 'CL=F'), ('brent', 'BZ=F')):
            try:
                h = yf.Ticker(sym).history(period='6mo')
                if len(h) > 0:
                    val = float(h['Close'].iloc[-1])
                    if 10 < val < 400:
                        out[key] = round(val, 2)
                        out[f'{key}_source'] = f'yahoo:{sym}'
                        try:
                            out[f'{key}_date'] = str(h.index[-1].date())
                        except Exception:
                            out[f'{key}_date'] = str(dt.date.today())
                        try:  # Wave T3: oil trend (backfilled from the 6mo series, live day-1)
                            _cl=[round(float(x),2) for x in h['Close'].values[-64:]]
                            for _tk,_tv in _series_trend(_cl, w=(5,21,63)).items():
                                out[f'{key}_{_tk}']=_tv
                        except Exception:
                            pass
                        log(f'  ✓ {key} (live {sym}) = {out[key]} '
                            f'(as of {out.get(f"{key}_date")})')
            except Exception as e:
                log(f'  · oil {key} yahoo miss: {e}')
    except Exception as e:
        log(f'  · yfinance unavailable for oil: {e}')
    return out


def fetch_tv_oil(keys):
    """TradingView futures fallback for live oil — slots BETWEEN Yahoo and FRED.
    Live-delayed continuous front-month: WTI=NYMEX:CL1!, Brent=ICEEUR:BRN1!.
    Beats the stale FRED print when Yahoo rate-limits (proven reachable on runner)."""
    tmap = {'wti': 'NYMEX:CL1!', 'brent': 'ICEEUR:BRN1!'}
    want = {k: tmap[k] for k in keys if k in tmap}
    out = {}
    if not want:
        return out
    try:
        payload = {'symbols': {'tickers': list(want.values())}, 'columns': ['close']}
        r = requests.post('https://scanner.tradingview.com/futures/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=20)
        if r.status_code == 200:
            rows = {d['s']: d['d'][0] for d in r.json().get('data', [])}
            for k, sym in want.items():
                v = rows.get(sym)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    v = None
                if v is not None and 10 < v < 400:
                    out[k] = round(v, 2)
                    out[f'{k}_source'] = f'tradingview:{sym.split(":")[-1]}'
                    out[f'{k}_date'] = str(dt.date.today())
                    log(f'  ✓ {k} (TV fallback {sym}) = {out[k]}')
    except Exception as e:
        log(f'  · oil TV fallback miss: {e}')
    return out


def fetch_arab_light():
    """Arab Light proxy = World Bank 'Crude oil, Dubai' MONTHLY benchmark (the v1.99.0 probe confirmed the
    WB monthly commodity sheet downloads cleanly; the project's CMOHistoricalDataMonthly.xlsx is the same
    file, so the layout below is LOCKED against ground truth: sheet 'Monthly Prices', header row 5,
    'Crude oil, Dubai' column, month tokens like '2026M05' in col A, missing = '…'). Returns
    (price $/bbl, 'YYYY-MM', source) or (None, None, None) on any miss -> caller carries last-good.
    Monthly cadence (not a live daily tick) — correct for a benchmark read. openpyxl is lazy-imported;
    if absent it logs + skips (add openpyxl to daily.yml). Guarded; never raises."""
    import io as _io
    url = 'https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Monthly.xlsx'
    try:
        try:
            import openpyxl
        except Exception:
            log('  · Arab Light: openpyxl not installed (add to daily.yml) — using last-good')
            return None, None, None
        r = _retry_get(url, headers={'User-Agent': UA}, timeout=30)
        if r.status_code != 200 or r.content[:2] != b'PK':
            log(f'  · Arab Light: WB sheet HTTP {r.status_code} (not xlsx) — last-good')
            return None, None, None
        wb = openpyxl.load_workbook(_io.BytesIO(r.content), read_only=True, data_only=True)
        ws = wb['Monthly Prices']
        rows = list(ws.iter_rows(values_only=True))
        hdr_i = dub_c = None
        for i, row in enumerate(rows[:12]):
            for c, val in enumerate(row):
                if isinstance(val, str) and val.strip().lower() == 'crude oil, dubai':
                    hdr_i, dub_c = i, c
                    break
            if hdr_i is not None:
                break
        if hdr_i is None:
            log('  · Arab Light: "Crude oil, Dubai" column not found — last-good')
            return None, None, None
        mre = re.compile(r'^\s*(\d{4})M(\d{2})\s*$')
        val = month = None
        for row in rows[hdr_i + 1:]:
            if not row or row[0] is None:
                continue
            m = mre.match(str(row[0]))
            if not m:
                continue
            try:
                v = float(row[dub_c])
            except (TypeError, ValueError):
                continue  # '…' missing month
            val, month = round(v, 2), f'{m.group(1)}-{m.group(2)}'
        if val is None:
            log('  · Arab Light: no numeric Dubai value parsed — last-good')
            return None, None, None
        return val, month, 'worldbank_cmo (Dubai, monthly)'
    except Exception as e:
        log(f'  · Arab Light fetch miss: {e}')
        return None, None, None


def fetch_us_macros():
    import re
    log('Fetching US macros from FRED...')
    if not FRED_KEY:
        warn('FRED_API_KEY not set, using last-good US macros')
        return EXISTING.get('macros', {}).get('us', {})

    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_KEY)

        series = {
            'fed_rate':       'DFEDTARU',
            'core_pce':       'PCEPILFE',
            'cpi_yoy':        'CPIAUCSL',
            'us_10y':         'DGS10',
            'us_2y':          'DGS2',
            'unemployment':   'UNRATE',
            'umcsi':          'UMCSENT',
            'mfg_emp':        'MANEMP',
            'gdp_growth':     'A191RL1Q225SBEA',
            'industrial_prod':'INDPRO',
            'hy_spread':      'BAMLH0A0HYM2',
            'permits':        'PERMIT',
        }

        out = {}
        def _fred_series(sid):
            # v1.11: throttle + retry-with-backoff to avoid FRED 429 'Too Many Requests'.
            # No new source needed — same free API key, just paced (3 tries: 0/1.5/4s).
            last = None
            for attempt, backoff in enumerate((0, 1.5, 4.0)):
                if backoff:
                    time.sleep(backoff)
                try:
                    return fred.get_series(sid).dropna()
                except Exception as e:
                    last = e
                    _em = str(e).lower()
                    # F2 (v1.66.0): retry transient failures too — rate-limit (429) AND
                    # timeouts / connection drops / 5xx — not just 429. Hard errors (bad
                    # series id 400, auth) are NOT transient -> raise immediately, don't burn retries.
                    _transient = ('too many' in _em or '429' in _em or 'timed out' in _em
                                  or 'timeout' in _em or 'connection' in _em or 'temporarily' in _em
                                  or 'max retries' in _em or ' 500' in _em or ' 502' in _em
                                  or ' 503' in _em or ' 504' in _em)
                    if _transient:
                        continue   # transient — wait and retry
                    raise          # non-transient: fall straight to last-good
            raise last
        for key, sid in series.items():
            try:
                time.sleep(0.6)    # gentle spacing between series (12 × 0.6s ≈ 7s)
                s = _fred_series(sid)
                if len(s) > 0:
                    val = float(s.iloc[-1])
                    if key in ('core_pce', 'cpi_yoy'):
                        if len(s) >= 13:
                            val = round(((s.iloc[-1] / s.iloc[-13]) - 1) * 100, 2)
                        else:
                            val = round(val, 2)
                    else:
                        val = round(val, 2)
                    out[key] = val
                    out[f'{key}_date'] = str(s.index[-1].date())
                    if key in ('us_10y','us_2y','hy_spread'):
                        for _tk,_tv in _series_trend([round(float(x),2) for x in s.values[-64:]], w=(5,21,63)).items():
                            out[f'{key}_{_tk}'] = _tv
                    # Wave T3: cadence-matched MoM/QoQ/YoY trend on the macro PRINT series,
                    # backfilled from the FRED series so it is live day-1. CPI/PCE trend the
                    # YoY *rate* (acceleration), not the index level; GDP is quarterly.
                    try:
                        if key in ('core_pce','cpi_yoy') and len(s) >= 25:
                            _idx=[float(x) for x in s.values]
                            _yoy=[round((_idx[i]/_idx[i-12]-1)*100,2) for i in range(12,len(_idx))]
                            for _tk,_tv in _print_trend(_yoy[-25:], [('mom',1),('qoq',3),('yoy',12)]).items():
                                out[f'{key}_{_tk}'] = _tv
                        elif key == 'gdp_growth' and len(s) >= 2:
                            for _tk,_tv in _print_trend([round(float(x),2) for x in s.values[-9:]], [('qoq',1),('yoy',4)]).items():
                                out[f'{key}_{_tk}'] = _tv
                        elif key in ('unemployment','umcsi','mfg_emp','industrial_prod','permits') and len(s) >= 2:
                            for _tk,_tv in _print_trend([round(float(x),2) for x in s.values[-25:]], [('mom',1),('qoq',3),('yoy',12)]).items():
                                out[f'{key}_{_tk}'] = _tv
                    except Exception as _e:
                        pass
                    log(f'  ✓ {key} = {out[key]}')
            except Exception as e:
                warn(f'FRED {key} ({sid}) failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'us', key)
                if lg is not None:
                    out[key] = lg
                    log(f'  · {key}: kept last-good = {lg}')

        if out.get('us_10y') is not None and out.get('us_2y') is not None:
            out['us_2s10s'] = round(out['us_10y'] - out['us_2y'], 2)
        # S&P 500 LEVEL (FRED 'SP500', daily close) — the US benchmark for the Results 'vs index'
        # (alpha) read = how much a name/sector is beating the market over the SAME window. Stored as
        # the current level + a compact dated history so append_history can fill the index level onto
        # each history day (KSE-100 is already snapshotted natively; the S&P 500 was the missing half).
        try:
            _sp = _fred_series('SP500')
            if len(_sp) > 0:
                out['sp500'] = round(float(_sp.iloc[-1]), 2)
                out['sp500_date'] = str(_sp.index[-1].date())
                out['sp500_hist'] = {str(d.date()): round(float(v), 2) for d, v in list(_sp.items())[-90:]}
                log(f'  \u2713 sp500 = {out["sp500"]}')
        except Exception as e:
            warn(f'FRED sp500 (SP500) failed: {e}')
            lg = safe_get(EXISTING, 'macros', 'us', 'sp500')
            if lg is not None:
                out['sp500'] = lg
                out['sp500_hist'] = safe_get(EXISTING, 'macros', 'us', 'sp500_hist') or {}
                log(f'  \u00b7 sp500: kept last-good = {lg}')
        # Live oil — Yahoo first, then TradingView futures, then FRED (last resort, may be stale)
        oil = fetch_live_oil()
        _oil_missing = [k for k in ('wti', 'brent') if k not in oil]
        if _oil_missing:
            oil.update(fetch_tv_oil(_oil_missing))
        for key, fred_id in (('wti', 'DCOILWTICO'), ('brent', 'DCOILBRENTEU')):
            if key in oil:
                out[key] = oil[key]
                out[f'{key}_source'] = oil[f'{key}_source']
                out[f'{key}_date']   = oil.get(f'{key}_date')
                for _w in ('wow', 'mom', 'qoq'):  # Wave T3 oil trend: carry the backfilled trend fields through the merge
                    if f'{key}_{_w}' in oil:
                        out[f'{key}_{_w}'] = oil[f'{key}_{_w}']
                    if f'{key}_{_w}_dir' in oil:
                        out[f'{key}_{_w}_dir'] = oil[f'{key}_{_w}_dir']
            else:
                try:
                    s = _fred_series(fred_id)   # F2: same retry/backoff as the main series loop
                    if len(s) > 0:
                        out[key] = round(float(s.iloc[-1]), 2)
                        out[f'{key}_source'] = f'fred:{fred_id} (may lag)'
                        out[f'{key}_date']   = str(s.index[-1].date())
                        warn(f'{key} live source missed; FRED value may be stale')
                except Exception as e:
                    warn(f'{key} FRED fallback failed: {e}')
                    lg = safe_get(EXISTING, 'macros', 'us', key)
                    if lg is not None:
                        out[key] = lg
                        out[f'{key}_source'] = 'last-good'

        try:
            if out.get('brent') and out.get('wti'):
                out['brent_wti_spread'] = round(out['brent'] - out['wti'], 2)
                log(f'  ✓ Brent-WTI spread = {out["brent_wti_spread"]}')
        except Exception:
            pass

        # US INDEX LEVELS — NDX + Dow from FRED (same mechanism as SP500), Russell-2000 from TradingView
        # (no free FRED Russell series; v1.99.0 probe: FRED NASDAQ100/DJIA OK, TVC:RUT returns the level).
        # Display-only — feeds the dashboard US Forward Outlook panel (was on dated snapshots). Last-good safe.
        for key, fred_id in (('ndx', 'NASDAQ100'), ('dow', 'DJIA')):
            try:
                s = _fred_series(fred_id)
                if len(s) > 0:
                    out[key] = round(float(s.iloc[-1]), 2)
                    out[f'{key}_date'] = str(s.index[-1].date())
                    log(f'  \u2713 {key} ({fred_id}) = {out[key]}')
            except Exception as e:
                warn(f'FRED {key} ({fred_id}) failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'us', key)
                if lg is not None:
                    out[key] = lg
                    out[f'{key}_date'] = safe_get(EXISTING, 'macros', 'us', f'{key}_date')
        try:
            r = requests.post('https://scanner.tradingview.com/america/scan',
                              json={'symbols': {'tickers': ['TVC:RUT']}, 'columns': ['close']},
                              headers={'User-Agent': UA}, timeout=20)
            _rut = None
            if r.status_code == 200:
                _d = (r.json().get('data') or [])
                if _d and _d[0].get('d'):
                    _rut = _d[0]['d'][0]
            if isinstance(_rut, (int, float)) and 500 < _rut < 20000:
                out['rut'] = round(float(_rut), 2)
                out['rut_date'] = str(dt.date.today())
                log(f'  \u2713 rut (TVC:RUT) = {out["rut"]}')
            else:
                raise ValueError(f'TVC:RUT returned {_rut}')
        except Exception as e:
            warn(f'Russell-2000 (TVC:RUT) failed: {e}')
            lg = safe_get(EXISTING, 'macros', 'us', 'rut')
            if lg is not None:
                out['rut'] = lg
                out['rut_date'] = safe_get(EXISTING, 'macros', 'us', 'rut_date')

        # ARAB LIGHT — the owner's stated oil benchmark (World Bank 'Crude oil, Dubai' monthly proxy).
        # Monthly cadence; display-only alongside WTI/Brent. Last-good safe.
        try:
            _al, _alm, _als = fetch_arab_light()
            if _al is not None:
                out['arab_light'] = _al
                out['arab_light_month'] = _alm
                out['arab_light_source'] = _als
                log(f'  \u2713 Arab Light (Dubai proxy) = {_al} $/bbl ({_alm})')
            else:
                lg = safe_get(EXISTING, 'macros', 'us', 'arab_light')
                if lg is not None:
                    out['arab_light'] = lg
                    out['arab_light_month'] = safe_get(EXISTING, 'macros', 'us', 'arab_light_month')
                    out['arab_light_source'] = 'last-good'
                    log(f'  \u00b7 Arab Light: kept last-good = {lg}')
        except Exception as e:
            warn(f'Arab Light failed: {e}')

        # US rotary rig count (F1) — third-party source: EIA (US gov) republishes the Baker Hughes
        # count as monthly "Crude Oil & Natural Gas Rotary Rigs in Operation" (TOTAL oil+gas; oil-only
        # is BH-proprietary & bot-blocked at TE/YCharts). Data is monthly + the page is heavy, so
        # cadence-gate to weekly (like ETF/Zacks): ~0 cost most runs, the rare fetch gets a real read window.
        _rig_prev = safe_get(EXISTING, 'macros', 'us', 'us_oil_rigs')
        _rig_utc = safe_get(EXISTING, 'macros', 'us', 'us_rigs_utc')
        _rig_age = None
        if _rig_utc:
            try:
                _rig_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_rig_utc).replace('Z', ''))).days
            except Exception:
                _rig_age = None
        if _rig_prev is not None and _rig_age is not None and _rig_age < 7:
            out['us_oil_rigs'] = _rig_prev
            out['us_rigs_utc'] = _rig_utc
            log(f'  → US rigs skipped (EIA fetch {_rig_age}d ago, <7d) — last-good {_rig_prev}')
        else:
            try:
                rr = requests.get('https://www.eia.gov/dnav/ng/hist/e_ertrr0_xr0_nus_cm.htm',
                                  headers={'User-Agent': UA}, timeout=(4, 12))
                if rr.status_code == 200:
                    t = re.sub(r'<[^>]+>', ' ', rr.text).replace('&nbsp;', ' ')
                    cut = t.find('No Data Reported')
                    if cut > 0:
                        t = t[:cut]
                    vals = [int(n.replace(',', '')) for n in re.findall(r'\d[\d,]{1,5}', t)]
                    for v in reversed(vals):           # most-recent plausible rig value; skip year tokens
                        if 100 <= v <= 6000 and not (1900 <= v <= 2100):
                            out['us_oil_rigs'] = v
                            out['us_rigs_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
                            log(f'  ✓ US rotary rigs (EIA, total oil+gas): {v}')
                            break
            except Exception as e:
                log(f'  · US rigs (EIA): {e}')
            if out.get('us_oil_rigs') is None and _rig_prev is not None:
                out['us_oil_rigs'] = _rig_prev
                log('  · US rigs: EIA unreachable; using last-good')

        # FOMC / Fed monetary-policy announcements (live — official Fed press-release RSS)
        try:
            import feedparser
            ffeed = feedparser.parse('https://www.federalreserve.gov/feeds/press_monetary.xml')
            items = []
            for e in ffeed.entries[:25]:
                pub = None
                if getattr(e, 'published_parsed', None):
                    pub = dt.datetime(*e.published_parsed[:6]).date().isoformat()
                items.append({'title': (getattr(e, 'title', '') or '').strip(),
                              'link':  getattr(e, 'link', '') or '',
                              'date':  pub})
            fomc = None
            for it in items:
                t = it['title'].lower()
                if 'fomc' in t or 'federal open market' in t or 'monetary policy' in t:
                    fomc = it; break
            if fomc is None and items:
                fomc = items[0]
            if fomc:
                tl = fomc['title'].lower()
                stance = ('QT' if any(w in tl for w in ('reduce', 'runoff', 'reducing', 'taper'))
                          else 'QE' if any(w in tl for w in ('purchase', 'expand its', 'increase its holdings'))
                          else None)
                days = None
                if fomc.get('date'):
                    try:
                        days = (dt.date.today() - dt.date.fromisoformat(fomc['date'])).days
                    except Exception:
                        days = None
                out['fomc'] = {'title': fomc['title'], 'link': fomc['link'], 'date': fomc['date'],
                               'days_ago': days, 'stance': stance, 'recent': items[:5]}
                log(f'  \u2713 FOMC: {fomc.get("date")} \u2014 {fomc["title"][:60]}')
        except Exception as e:
            log(f'  \u00b7 FOMC RSS (last-good): {e}')
            lg = safe_get(EXISTING, 'macros', 'us', 'fomc')
            if lg is not None:
                out['fomc'] = lg

        log(f'  Total US macros: '
            f'{len([k for k in out if not k.endswith(("_date","_source"))])}')
        return out

    except Exception as e:
        log(f'  US macros FAILED: {e}')
        traceback.print_exc()
        return EXISTING.get('macros', {}).get('us', {})


# =============================================================
# 2. PSX MACRO
# =============================================================
def _kse_sane(v):
    """Accept only index-magnitude numbers (rejects share prices and most volumes)."""
    try:
        v = float(v)
        return v if KSE_MIN < v < KSE_MAX else None
    except Exception:
        return None


def _kse_ts_to_date(ts):
    try:
        ts = float(ts)
        if ts > 1e12:
            ts /= 1000.0
        return str(dt.datetime.utcfromtimestamp(ts).date())
    except Exception:
        return None


def _kse_grab(text):
    """Find the KSE-100 index value in an HTML page. Prefers a decimal number
    (the index prints as 171651.48; share volumes are integers) to avoid
    false-matching a volume figure that happens to sit in the index range."""
    import re
    anchor = re.search(r'KSE\s*-?\s*100', text, re.I)
    if not anchor:
        return None
    window = text[anchor.end(): anchor.end() + 400]
    for pat in (r'[\d,]{5,}\.\d+', r'[\d,]{5,}'):   # decimal first, then integer fallback
        for num in re.findall(pat, window):
            v = _kse_sane(num.replace(',', ''))
            if v is not None:
                return round(v, 2)
    return None


def _kse_extract_ts(rows):
    """Pull (value, date_str) from a dps.psx timeseries 'data' array. Pure."""
    if not rows:
        return None, None
    last = rows[-1]
    val = None
    date_str = None
    if isinstance(last, (list, tuple)):
        if len(last) >= 1:
            date_str = _kse_ts_to_date(last[0])
        if len(last) >= 5:
            val = _kse_sane(last[4])
        if val is None and len(last) >= 2:
            val = _kse_sane(last[1])
    return (round(val, 2) if val is not None else None), date_str


def fetch_kse100():
    """KSE-100 index level.
    PRIMARY: TradingView official close (PSX:KSE100). The dps.psx `int` series is INTRADAY — its
      LAST tick under-reports the official session close (observed 178182 vs the real 180232 close,
      the index ran into the close after the feed's last recorded tick), and the dps `eod` index
      series is frozen at 2021. TradingView is the only runner-reachable source that carries the
      official close (~15min delayed; posts after the session), mirroring the PSX stock-price feed.
    FALLBACK: dps.psx int (intraday last tick — may lag the close) then eod, then (caller) last-good.
    A manual override in psx_macros_manual.json ('kse100') wins over all of this (applied by caller)."""
    headers = {'User-Agent': UA, 'Accept': 'application/json'}
    today = str(dt.date.today())
    # PRIMARY — TradingView PSX:KSE100 official close (mirrors the futures/ETF symbols-POST pattern).
    # Query a few candidate index symbols and LOG all returned, but only TRUST PSX:KSE100 — so if TV
    # uses a different code the run log reveals it without us using a wrong index.
    try:
        payload = {'symbols': {'tickers': ['PSX:KSE100', 'PSX:KSE30', 'PSX:KSEALL']},
                   'columns': ['close']}
        r = requests.post('https://scanner.tradingview.com/pakistan/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=20)
        if r.status_code == 200:
            rows = {d.get('s'): (d.get('d') or [None])[0] for d in r.json().get('data', [])}
            log(f'  · KSE-100 TradingView index symbols -> {rows}')
            v = _kse_sane(rows.get('PSX:KSE100'))
            if v is not None:
                return round(v, 2), 'tradingview:KSE100 (official close)', today
        else:
            log(f'  · KSE-100 TradingView HTTP {r.status_code}')
    except Exception as e:
        log(f'  · KSE-100 TradingView miss: {e}')

    # FALLBACK — dps.psx int (intraday last tick; may lag the official close) then eod.
    best = None  # (val, date_str, src)
    for path, label in (('int', 'psx-dps:int (intraday last tick — may lag official close)'),
                        ('eod', 'psx-dps:eod')):
        try:
            r = requests.get(f'https://dps.psx.com.pk/timeseries/{path}/KSE100',
                             headers=headers, timeout=12)
            if r.status_code == 200:
                j = r.json()
                rows = j.get('data') if isinstance(j, dict) else j
                v, d = _kse_extract_ts(rows)
                if v is not None:
                    if best is None or (d and best[1] and d > best[1]) or (d and not best[1]):
                        best = (v, d, label)
        except Exception as e:
            log(f'  · KSE-100 dps/{path} miss: {e}')

    if best is not None:
        return best[0], best[2], (best[1] or today)
    return None, None, None


def fetch_psx_macros():
    log('Fetching PSX macros...')
    out = EXISTING.get('macros', {}).get('psx', {}).copy()
    import re
    headers = {'User-Agent': UA}

    # KSE-100: a manual override in psx_macros_manual.json ('kse100', optionally 'kse100_date')
    # WINS — the official PSX close, user-set, guaranteed correct (use it if the live feed is ever
    # wrong). Default (no override) = the live fetch (TradingView official close -> dps fallback).
    _man_kse = None
    try:
        with open('psx_macros_manual.json') as _mf:
            _man_kse = (json.load(_mf) or {}).get('kse100')
    except Exception:
        _man_kse = None
    if _man_kse is not None and (KSE_MIN < float(_man_kse) < KSE_MAX):
        val, src, dstr = round(float(_man_kse), 2), 'manual override (official PSX close)', \
            (safe_get(EXISTING, 'macros', 'psx', 'kse100_date') or str(dt.date.today()))
        try:
            with open('psx_macros_manual.json') as _mf:
                _md = (json.load(_mf) or {}).get('kse100_date')
            if _md:
                dstr = _md
        except Exception:
            pass
    else:
        val, src, dstr = fetch_kse100()
    if val is not None:
        out['kse100'] = val
        out['kse100_source'] = src
        out['kse100_date'] = dstr
        log(f'  ✓ KSE-100 ({src}): {val} (as of {dstr})')
        try:  # Wave T3: KSE-100 trend (accrues per session; dedup-by-date so same-session re-runs don't double-append)
            _kh = _push_hist(out.get('kse100_hist'), dstr, val)
            out['kse100_hist'] = _kh
            for _k, _v in _hist_trend(_kh, w=(1, 5, 21)).items():
                out['kse100_' + _k] = _v
        except Exception:
            pass
    else:
        lg = safe_get(EXISTING, 'macros', 'psx', 'kse100')
        if lg is not None:
            out['kse100'] = lg
            out['kse100_source'] = 'last-good (STALE)'
            out['kse100_date'] = safe_get(EXISTING, 'macros', 'psx', 'kse100_date')
            warn(f'KSE-100 all live sources failed; using STALE last-good {lg}')
        else:
            out['kse100'] = None
            warn('KSE-100 unavailable and no last-good value')

    try:
        import yfinance as yf
        h = yf.Ticker('USDPKR=X').history(period='6mo')
        if len(h) > 0:
            out['usd_pkr'] = round(float(h['Close'].iloc[-1]), 2)
            for _tk,_tv in _series_trend([round(float(x),2) for x in h['Close'].values[-64:]], w=(5,21,63)).items():
                out['usd_pkr_'+_tk] = _tv
            log(f'  ✓ USD/PKR: {out["usd_pkr"]}')
    except Exception as e:
        warn(f'USD/PKR failed: {e}')

    try:
        r = _retry_get('https://www.sbp.org.pk/m_policy/index.asp',
                       headers=headers, timeout=15, tries=3, base=1.0)
        if r.status_code == 200:
            m = re.search(r'(\d{1,2}\.\d{1,2})\s*(?:percent|%)', r.text, re.I)
            if m:
                out['sbp_rate'] = float(m.group(1))
                log(f'  ✓ SBP rate (SBP official): {out["sbp_rate"]}%')
    except Exception as e:
        log(f'  · SBP rate: {e}')
    if out.get('sbp_rate') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'sbp_rate')
        if lg is not None:
            out['sbp_rate'] = lg

    # CPI YoY — primary: TheGlobalEconomy (PBS-sourced, monthly, fetchable & parseable),
    # then PBS direct, then TE (below), then last-good. The _tge helper reads the most-recent
    # row of a TheGlobalEconomy per-indicator page and is reusable for other PSX macros.
    def _tge(slug, diag=False):
        try:
            rr = requests.get(f'https://www.theglobaleconomy.com/Pakistan/{slug}/',
                              headers={'User-Agent': UA}, timeout=15)
            if rr.status_code != 200:
                if diag: log(f'    · [diag] TGE {slug}: HTTP {rr.status_code}')
                return None
            txt = re.sub(r'<[^>]+>', ' ', rr.text)
            txt = txt.replace('&nbsp;', ' ').replace('&nbsp', ' ')  # entity survives tag-strip; year/month joined by it
            txt = re.sub(r'\s+', ' ', txt)            # collapse newlines/tabs so the row is contiguous
            i = txt.find('Recent values')
            seg = txt[i:i + 500] if i >= 0 else txt
            # accept "YYYY Mon <val>" or "Mon YYYY <val>"; values may carry commas
            m = re.search(r'(?:(?:19|20)\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|'
                          r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:19|20)\d{2})'
                          r'\s+(-?[\d,]+(?:\.\d+)?)', seg)
            if not m:
                if diag: log(f'    · [diag] TGE {slug}: 200 len={len(rr.text)} hasRecent={i>=0} seg={seg[:170]!r}')
                return None
            return float(m.group(1).replace(',', ''))
        except Exception as e:
            if diag: log(f'    · [diag] TGE {slug}: {type(e).__name__} {str(e)[:80]}')
            return None
    try:
        v = _tge('inflation_annual', diag=False)  # CPI YoY %, monthly; site now JS-walled, kept as cheap probe in case it reverts
        if v is not None:
            out['pak_cpi'] = v
            log(f'  ✓ Pak CPI YoY (TheGlobalEconomy): {v}%')
        else:
            log('  → Pak CPI: TheGlobalEconomy now JS-rendered (unparseable) — using manual/last-good')
    except Exception as e:
        log(f'  · Pak CPI (TheGlobalEconomy): {e}')
    # PBS live monthly CPI (SDMX XML) - AUTHORITATIVE, overwrites the pre-seeded last-good (out carries it from line ~603,
    # so an `if is None` guard would never fire). Manual override (psx_macros_manual.json 'pak_cpi') runs AFTER this and wins.
    _cpi = fetch_pbs_cpi()
    if _cpi and _cpi.get('yoy') is not None:
        _prior = out.get('pak_cpi')
        out['pak_cpi'] = _cpi['yoy']
        out['pak_cpi_index'] = _cpi.get('index')
        out['pak_cpi_mom'] = _cpi.get('mom')
        out['pak_cpi_as_of'] = _cpi.get('as_of')
        out['pak_cpi_source'] = 'pbs_sdmx'
        log(f'  ✓ Pak CPI YoY (PBS live): {_cpi["yoy"]}% (index {_cpi.get("index")}, MoM {_cpi.get("mom")}%, as of {_cpi.get("as_of")}; prior {_prior})')
    elif out.get('pak_cpi') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'pak_cpi')
        if lg is not None:
            out['pak_cpi'] = lg

    # F4 source resolution: CPI is now live-monthly via TheGlobalEconomy. REER / Current Account /
    # Fiscal have NO free monthly fetchable feed (SBP/PBS=PDF; FRED Pakistan=annual-only; TE blocks
    # bots; TheGlobalEconomy & World Bank carry these three only annually). They stay best-effort TE
    # → last-good → Tab-1 manual (update quarterly from the AKD/Topline economy report).

    # F4/F3: best-effort live fetch (free, Trading Economics) for the slow-moving Pakistan
    # macros that had no live source. Fully guarded — on ANY failure the last-good fallbacks
    # below apply, so this can never break the run. Validates on the live run (TE may block
    # bots; last-good remains the reliable backstop — spot-check against broker monthlies).
    # F4 (v1.52): manual-override slot. REER / current-account / fiscal-balance have no free
    # monthly feed — maintain them quarterly from the AKD/Topline economy report in
    # psx_macros_manual.json (repo root). Manual values WIN: the TE block below only fetches when
    # out[key] is still None, so seeding here short-circuits it. Fully guarded — file absent = no-op.
    try:
        with open('psx_macros_manual.json') as _mf:
            _man = json.load(_mf) or {}
        for _k in ('reer', 'pak_ca', 'pak_fiscal', 'pak_cpi'):
            _v = _man.get(_k)
            if _v is not None:
                out[_k] = _v
                log(f'  ✓ {_k} (manual override): {_v}')
    except FileNotFoundError:
        pass
    except Exception as _e:
        log(f'  · psx_macros_manual.json ignored ({_e})')

    def _te(slug, label):
        try:
            rr = requests.get('https://tradingeconomics.com/pakistan/' + slug,
                              headers={'User-Agent': UA}, timeout=12)
            if rr.status_code != 200:
                return None
            txt = re.sub(r'<[^>]+>', ' ', rr.text)
            m = re.search(label + r'[^0-9\-]{0,40}(-?\d{1,4}(?:\.\d{1,2})?)', txt, re.I)
            return float(m.group(1)) if m else None
        except Exception:
            return None
    try:
        if out.get('pak_cpi') is None:
            v = _te('inflation-cpi', 'Inflation Rate')
            if v is not None: out['pak_cpi'] = v; log(f'  ✓ Pak CPI (TE): {v}%')
        if out.get('reer') is None:
            v = _te('real-effective-exchange-rate', 'Real Effective')
            if v is not None: out['reer'] = v; log(f'  ✓ REER (TE): {v}')
        if out.get('pak_ca') is None:
            v = _te('current-account', 'Current Account')
            if v is not None: out['pak_ca'] = v; log(f'  ✓ Current account (TE): {v}')
        if out.get('pak_fiscal') is None:
            v = _te('government-budget', 'Government Budget')
            if v is not None: out['pak_fiscal'] = v; log(f'  ✓ Fiscal balance (TE): {v}% GDP')
        # SBP FX reserves: manual override (psx_macros_manual.json) WINS; otherwise the live ecodata feed
        # OVERWRITES the last-good that 'out' was seeded with at the top (line ~603) so the weekly figure
        # actually refreshes (a plain `if is None` guard never fires because out carries last-good).
        _man_res = None
        try:
            with open('psx_macros_manual.json') as _mf:
                _man_res = (json.load(_mf) or {}).get('sbp_reserves')
        except Exception:
            _man_res = None
        if _man_res is not None:
            out['sbp_reserves'] = _man_res
            out['sbp_reserves_source'] = 'manual'
            log(f'  ✓ SBP reserves (manual override): {_man_res}')
        else:
            _prior = out.get('sbp_reserves')
            _res = fetch_sbp_reserves()
            if _res and _res.get('sbp_bn') is not None:
                out['sbp_reserves'] = _res['sbp_bn']
                out['sbp_reserves_total'] = _res.get('total_bn')
                out['sbp_reserves_bank'] = _res.get('bank_bn')
                out['sbp_reserves_as_of'] = _res.get('as_of')
                out['sbp_reserves_source'] = 'sbp_ecodata'
                log(f'  ✓ SBP reserves (ecodata, live): SBP {_res.get("sbp_bn")}bn / bank {_res.get("bank_bn")}bn / total {_res.get("total_bn")}bn as on {_res.get("as_of")} (prior {_prior})')
            else:
                log(f'  · SBP reserves (ecodata): fetch/parse returned nothing -> keeping last-good ({_prior})')
        if out.get('sbp_reserves') is None:
            v = _te('foreign-exchange-reserves', 'Foreign Exchange Reserves')
            if v is not None: out['sbp_reserves'] = round(v/1000.0, 2) if v > 1000 else v; log(f'  ✓ SBP reserves (TE): {out["sbp_reserves"]}')
    except Exception as e:
        log(f'  · TE Pakistan macros (best-effort): {e}')

    if out.get('sbp_reserves') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'sbp_reserves')
        if lg is not None:
            out['sbp_reserves'] = lg
    # T1: value-change-dedup reserves history + WoW/MoM/QoQ trend (SBP weekly data, daily runs)
    if out.get('sbp_reserves') is not None:
        _prior_src = safe_get(EXISTING, 'macros', 'psx', 'sbp_reserves_source')
        if out.get('sbp_reserves_source') == 'sbp_ecodata' and _prior_src != 'sbp_ecodata':
            # basis switch (manual / last-good -> live ecodata): start the history fresh at the live value
            # so the one-time basis change cannot register as a weekly move (re-baseline, runs once).
            _rh = []
            log(f'  · SBP reserves history re-baselined onto the live ecodata basis ({out["sbp_reserves"]})')
        else:
            _rh = [h if isinstance(h, dict) else {'d': None, 'v': h}
                   for h in (safe_get(EXISTING, 'macros', 'psx', 'sbp_reserves_hist') or [])]
        if not _rh or _rh[-1].get('v') != out['sbp_reserves']:
            _rh.append({'d': out.get('sbp_reserves_as_of'), 'v': out['sbp_reserves']})
        _rh = _rh[-160:]
        out['sbp_reserves_hist'] = _rh
        for _k, _v in _series_trend([h['v'] for h in _rh if isinstance(h, dict) and h.get('v') is not None]).items():
            out['sbp_reserves_'+_k] = _v

    if out.get('reer') is None:
        lg = safe_get(EXISTING, 'macros', 'psx', 'reer')
        if lg is not None:
            out['reer'] = lg

    # v1.11: pak_ca and pak_fiscal have no live source yet — seed last-good so the
    # Gold tab's Pakistan factors don't silently fall back to Tab-1 manual values.
    for _k in ('pak_ca', 'pak_fiscal', 'neer'):
        if out.get(_k) is None:
            _lg = safe_get(EXISTING, 'macros', 'psx', _k)
            if _lg is not None:
                out[_k] = _lg

    _manual = [k for k in ('reer', 'pak_ca', 'pak_fiscal') if out.get(k) is not None]
    log(f'  → REER/CA/Fiscal: no free monthly feed — manual/last-good (quarterly from AKD/Topline). CPI via TheGlobalEconomy when parsed, else last-good. Carried: {_manual or "none"}')

    return out


# =============================================================
# 2c. COT FUTURES (sector gating) — CFTC Socrata, ported verbatim from M1 fetchCOT()
#     SP500/10yr/VIX/NASDAQ from TFF (Asset Manager net); Crude from Disaggregated (Managed Money).
# =============================================================
COT_KEYWORDS = {
    'SP500':  'S&P 500',
    '10yr':   'UST 10Y NOTE',
    'VIX':    'VIX FUTURES',
    'NASDAQ': 'NASDAQ-100',
}
COT_KEYWORDS_COMMODITIES = {'Crude': 'WTI-PHYSICAL'}

def _retry_get(url, *, tries=3, base=1.0, **kwargs):
    """GET with retry-on-transient-error + exponential backoff (sleeps base, 2*base, 4*base...).
    Retries ONLY transient network failures (Timeout / ConnectionError); on the final
    attempt — or for any non-transient error — it re-raises, so each caller's existing
    try/except -> last-good fallback stays exactly as before. HTTP status codes are NOT
    inspected here (callers check r.status_code themselves). v1.50.0 (F2/F3 hardening)."""
    last = None
    for _i in range(max(1, tries)):
        if _i:
            time.sleep(base * (2 ** (_i - 1)))
        try:
            return requests.get(url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last = e
            continue
    raise last


# -------------------------------------------------------------
# v1.110.0 (Wave COT-A / D-70): COT ANALYTICS LAYER — a normalized positioning read per contract.
# Pure math VALIDATED against the owner's full S&P legacy export (all_data_cot.docx, 1000 weekly rows):
# COT Index 1Y (52-wk) reproduced 17.03, COT Index 3Y (156-wk) 18.484, NCP long/short % 10.17/17.688,
# flip -7.519, 4-wk avg flip -8.761 BUY, 13-wk avg flip -6.124 SELL — ALL EXACT. The RSI columns here are
# our OWN transparent Wilder RSI on the net series (Sarmaaya's proprietary 'COT RSI'/'Possible Bias' are
# NOT cloned — D-70 says build transparent equivalents, not copy the proprietary transform).
COT_HIST_DIAG = False  # v1.112.0: disarmed (runner confirmed ~156 wks/contract); re-arm only to re-inspect depth

def _cot_analytics(hist):
    """hist = oldest->newest list of {net,long,short,oi}. Returns the normalized positioning block, or
    None if too thin. Never fabricates: a metric whose window isn't available returns None."""
    if not hist or len(hist) < 8:
        return None
    nets = [h['net'] for h in hist]
    flips = [(h['net'] / h['oi'] * 100) if h['oi'] else 0.0 for h in hist]
    last = hist[-1]
    def _stoch(series, w):
        s = series[-w:]
        lo, hi = min(s), max(s)
        return None if hi == lo else round((series[-1] - lo) / (hi - lo) * 100, 1)
    def _wilder_rsi(series, p):
        if len(series) < p + 1:
            return None
        d = [series[i] - series[i - 1] for i in range(1, len(series))]
        g = [max(x, 0) for x in d]; l = [max(-x, 0) for x in d]
        ag = sum(g[:p]) / p; al = sum(l[:p]) / p
        for i in range(p, len(d)):
            ag = (ag * (p - 1) + g[i]) / p; al = (al * (p - 1) + l[i]) / p
        return 100.0 if al == 0 else round(100 - 100 / (1 + ag / al), 1)
    f4 = sum(flips[-4:]) / min(4, len(flips))
    f13 = sum(flips[-13:]) / min(13, len(flips))
    return {
        'weeks':        len(hist),
        'cot_index_1y': _stoch(nets, 52),    # 0-100: how stretched vs the last 52 weeks (low = crowded short / room to rally)
        'cot_index_3y': _stoch(nets, 156),   # 0-100 vs the last 3 years
        'ncp_long_pct':  round(last['long'] / last['oi'] * 100, 2) if last['oi'] else None,
        'ncp_short_pct': round(last['short'] / last['oi'] * 100, 2) if last['oi'] else None,
        'flip':          round(flips[-1], 2),                                    # net as % of OI
        'flip_4w_avg':   round(f4, 2),  'flip_4w_signal':  'BUY' if flips[-1] > f4 else 'SELL',
        'flip_13w_avg':  round(f13, 2), 'flip_13w_signal': 'BUY' if flips[-1] > f13 else 'SELL',
        'rsi_13': _wilder_rsi(nets, 13), 'rsi_26': _wilder_rsi(nets, 26), 'rsi_52': _wilder_rsi(nets, 52),
    }

def _fetch_cot_history(inc, exc, headers, dsid, weeks=170):
    """Per-contract legacy-Non-Commercial weekly history for the analytics. ONE light $where like-filter on
    the primary include token, then the SAME full inc/exc match + dedup-by-date as the headline, so it can
    never pull a wrong variant. Returns oldest->newest [{date,long,short,oi,net}] (<= weeks). Guarded by the
    caller; sandbox cannot reach CFTC so the weeks-returned is confirmed on the runner (COT_HIST_DIAG)."""
    import urllib.parse
    tok = inc[0].replace("'", "''")
    where = "upper(market_and_exchange_names) like '%" + tok + "%'"
    qs = urllib.parse.urlencode({'$where': where,
                                 '$order': 'report_date_as_yyyy_mm_dd DESC',
                                 '$limit': weeks * 3})
    url = 'https://publicreporting.cftc.gov/resource/' + dsid + '.json?' + qs
    rows = _retry_get(url, headers=headers, timeout=(10, 25), tries=2, base=1.0).json()
    if not isinstance(rows, list):
        return []
    seen = set(); series = []
    for rec in rows:
        nm = str(rec.get('market_and_exchange_names', '')).upper()
        if not (all(k in nm for k in inc) and not any(x in nm for x in exc)):
            continue
        d = rec.get('report_date_as_yyyy_mm_dd')
        if d in seen:
            continue
        seen.add(d)
        lng = float(rec.get('noncomm_positions_long_all', 0) or 0)
        sht = float(rec.get('noncomm_positions_short_all', 0) or 0)
        oi  = float(rec.get('open_interest_all', 0) or 0)
        series.append({'date': d, 'long': lng, 'short': sht, 'oi': oi, 'net': lng - sht})
    series.reverse()   # oldest -> newest
    return series[-weeks:]


def fetch_cot_futures():
    """Index/financial/commodity COT contracts used to gate US sector selection, ALL now read from the
    legacy COMBINED futures-only report's NON-COMMERCIAL (large-speculator) basis — the SAME basis as the
    metals COT page and the Sarmaaya tabs the owner validated (locked v1.106.0-1.108.0; dataset 6dca-aqww;
    NASDAQ-100 CONSOLIDATED -20,866 / DJIA CONSOLIDATED +4,339 / E-MINI S&P 500 -193,978 reproduced EXACTLY).
    REPLACES the prior wrong-bucket feed (index contracts read the TFF ASSET-MANAGER bucket -> SP500 printed
    +986,577 'VERY BULLISH' when specs are net -193,978 SHORT; commodities read disaggregated MANAGED-MONEY).
    Now carries SP500, NASDAQ, Russell, DJIA, 10yr, VIX (index/financial) + Crude, NatGas, Agriculture/Corn
    (commodity) on one consistent basis; Russell + DJIA are NEW (owner decision). NatGas -> Utilities,
    Corn -> Consumer Staples, Crude -> Energy (index cotFor mapping; Russell/DJIA available for a future
    index wiring). Sign + %-of-OI signal (the old absolute >500k cut was the meaningless artifact of the
    wrong bucket; a true normalized COT-index/percentile is a later phase). Returns {contract:{long,short,
    net,oi,pct_oi,signal,name,date, net_wow/mom/qoq}}. DATA-only sector-selection signal — never touches the
    universe screen, scoring, IM3, the TCE tier or the frozen ledger -> respects the Sept freeze. Never
    raises (per-contract guarded + per-contract AND whole-dict last-good carry)."""
    out = {}
    headers = {'User-Agent': UA}
    DSID = '6dca-aqww'   # CFTC legacy combined, FUTURES-ONLY; LOCKED (Nasdaq/DJIA/S&P reproduced Sarmaaya exactly)
    # contract -> (include ALL of, exclude ANY of) on upper(market_and_exchange_names). The 8 index/financial
    # + Corn names are LOCKED verbatim from the v1.106-1.108 runner dumps; Crude uses WTI-PHYSICAL+NEW YORK
    # (the exact matcher the disaggregated feed already pins NYMEX WTI with every run — CFTC keeps one
    # canonical contract name across its reports). A contract that fails to match carries its last-good.
    _C = {
        'SP500':       (['E-MINI S&P 500'],                      ['MICRO', 'INDEX', 'ESG']),
        'NASDAQ':      (['NASDAQ-100 CONSOLIDATED'],             []),
        'Russell':     (['RUSSELL E-MINI'],                      ['MICRO', '1000']),
        'DJIA':        (['DJIA CONSOLIDATED'],                   []),
        '10yr':        (['UST 10Y NOTE'],                        ['ULTRA', 'MICRO']),
        'VIX':         (['VIX FUTURES'],                         []),
        'Crude':       (['WTI-PHYSICAL', 'NEW YORK'],            []),
        'NatGas':      (['NAT GAS NYME', 'NEW YORK MERCANTILE'], []),
        'Agriculture': (['CORN', 'CHICAGO BOARD OF TRADE'],      ['MINI']),
    }
    _truth = {'SP500': -193978, 'NASDAQ': -20866, 'DJIA': 4339}   # validated Sarmaaya net (permanent audit)
    rows = []
    try:
        # ONE pull of the latest weeks (the legacy report carries ~600 markets/week, so this spans several
        # weeks -> headline + a real WoW/MoM net trend per contract). No $where (keeps it to plain $order/
        # $limit, the same syntax the rest of the scanner uses).
        url = (f'https://publicreporting.cftc.gov/resource/{DSID}.json'
               '?$order=report_date_as_yyyy_mm_dd DESC&$limit=4000')
        rows = _retry_get(url, headers=headers, timeout=(10, 20), tries=3, base=1.0).json()
        if not isinstance(rows, list):
            rows = []
    except Exception as e:
        warn(f'COT futures (legacy Non-Commercial) fetch failed: {e}')
        rows = []
    found = []
    if rows:
        for key, (inc, exc) in _C.items():
            try:
                series = []     # newest->oldest Non-Commercial net for the ONE locked contract
                head = None
                for rec in rows:
                    nm = str(rec.get('market_and_exchange_names', '')).upper()
                    if not (all(k in nm for k in inc) and not any(x in nm for x in exc)):
                        continue
                    lng = float(rec.get('noncomm_positions_long_all', 0) or 0)
                    sht = float(rec.get('noncomm_positions_short_all', 0) or 0)
                    oi  = float(rec.get('open_interest_all', 0) or 0)
                    net = lng - sht
                    series.append(net)
                    if head is None:       # first (latest) matching row defines the headline
                        pct = round(net / oi * 100, 1) if oi else 0.0
                        sig = ('VERY BULLISH' if net > 0 and pct >= 10 else 'BULLISH' if net > 0
                               else 'VERY BEARISH' if net < 0 and pct <= -10 else 'BEARISH' if net < 0
                               else 'NEUTRAL')
                        head = {'long': int(lng), 'short': int(sht), 'net': int(net), 'oi': int(oi),
                                'pct_oi': pct, 'signal': sig, 'name': nm,
                                'date': rec.get('report_date_as_yyyy_mm_dd')}
                if head is None:
                    log(f'  [COT {key}] no legacy Non-Commercial match (include={inc} exclude={exc}) — carrying last-good')
                    continue
                for _k, _v in _series_trend(list(reversed(series))[-14:]).items():
                    head['net_' + _k] = _v
                out[key] = head
                found.append(key)
                chk = ''
                if key in _truth:
                    gt = _truth[key]
                    ok = abs(head['net'] - gt) <= max(2000, abs(gt) * 0.03)
                    chk = f'  [vs Sarmaaya {gt:+,}: {"OK" if ok else "DRIFT"}]'
                log(f'  ✓ COT {key}: net {head["net"]:+,} {head["signal"]} ({head["pct_oi"]:+.1f}% OI) '
                    f'"{head["name"]}"{chk}')
                # v1.110.0: attach the normalized COT analytics (history-based) — guarded, NEVER affects the
                # headline above; a thin/failed history simply omits the analytics block (never fabricated).
                try:
                    hist = _fetch_cot_history(inc, exc, headers, DSID)
                    an = _cot_analytics(hist) if hist else None
                    if an:
                        head['analytics'] = an
                    if COT_HIST_DIAG:
                        if an:
                            log(f'    [COT analytics {key}] {an["weeks"]} wks -> idx1y {an["cot_index_1y"]} '
                                f'idx3y {an["cot_index_3y"]} flip {an["flip"]} '
                                f'(4w {an["flip_4w_signal"]}/13w {an["flip_13w_signal"]}) rsi52 {an["rsi_52"]}')
                        else:
                            log(f'    [COT analytics {key}] only {len(hist) if hist else 0} wks — analytics omitted')
                except Exception as _ae:
                    warn(f'COT {key} analytics failed (headline kept): {_ae}')
            except Exception as e:
                warn(f'COT {key} (legacy Non-Commercial) failed: {e}')
    log(f'  ✓ COT futures (legacy Non-Commercial 6dca-aqww): {len(found)}/9 [{", ".join(found)}]')
    # last-good carry: whole-dict if the pull died, else per-contract for any name that missed this run
    lg = safe_get(EXISTING, 'cot_futures') or {}
    if not out:
        out = lg
    elif lg:
        for k, v in lg.items():
            out.setdefault(k, v)
    return out


# -------------------------------------------------------------
# COT legacy-combined NON-COMMERCIAL repoint — Phase-0 PROBE (v1.106.0, logging-only, dump-then-lock).
# The production fetch_cot_futures (above) reads index/financial contracts from the TFF report's
# ASSET-MANAGER bucket and the commodity contracts from disaggregated MANAGED-MONEY — NEITHER is the
# legacy combined NON-COMMERCIAL (large-speculator) basis the dashboard, the metals page and Sarmaaya
# use, which is why SP500 prints +986,577 "VERY BULLISH" (Asset Managers are structurally long) when
# the validated Non-Commercial net is SHORT (-193,978). The legacy COMBINED report is effectively a
# NEW dataset (different Socrata id, different columns, AND different contract-name strings — it carries
# full-size + E-mini + consolidated S&P, so matching the wrong VARIANT gives a plausible-but-wrong
# number). The sandbox can't reach CFTC, so per the standing probe-before-build rule this dumps the
# real dataset/columns/contract-names + a ground-truth check FIRST; v1.107.0 locks the repoint.
COT_LEGACY_PROBE = False  # RETIRED v1.109.0 — all 9 contract names locked from the v1.106-1.108 dumps and the repoint shipped; probe kept gated off (re-arm only to re-confirm a name)
_COT_LEGACY_DATASETS = [
    # v1.107.0 LOCKED to futures-only: the v1.106.0 run proved 6dca-aqww reproduces Sarmaaya EXACTLY
    # (NASDAQ-100 CONSOLIDATED -20,866 + DJIA CONSOLIDATED +4,339), while jun7-fc8e (fut+options) was
    # only close (-19,929 / +4,426) -> it is NOT the Sarmaaya basis, so it is dropped from the probe.
    ('legacy-futures-only', '6dca-aqww'),   # CFTC Commitments of Traders - legacy combined, futures-only
]
# contract -> (must contain ALL of these substrings, must contain NONE of these) on the upper-cased
# market_and_exchange_names -> uniquely pins the HEADLINE liquid contract and excludes the decoys.
# v1.107.0 TIGHTENED from the v1.106.0 dump: the loose substrings + a 4-name cap let the many-variant
# contracts (S&P has 8+: dividend / MidCap-400 / micro / utilities / annual-div / adj-int-rate / ...)
# crowd the real E-mini off the list, so its -193,978 row never surfaced. Each matcher below pins the
# one contract whose net we want; the names of the 6 already-confirmed contracts are copied verbatim
# from the v1.106.0 runner output (NASDAQ-100 CONSOLIDATED, DJIA CONSOLIDATED, RUSSELL E-MINI, VIX
# FUTURES, UST 10Y NOTE, CORN); SP500/Crude/NatGas headline names are the CFTC-standard strings this
# pass will confirm (S&P must read -193,978 before the repoint is trusted).
_COT_LEGACY_PROBE_KW = {
    'SP500':       (['S&P 500'],                              []),   # DUMP-ALL: v1.107.0 guess 'E-MINI S&P 500 STOCK INDEX' matched NONE; surface every S&P-500 variant + auto-flag the -193,978 row (Nasdaq/DJIA used CONSOLIDATED, so S&P is likely 'S&P 500 CONSOLIDATED')
    'NASDAQ':      (['NASDAQ-100 CONSOLIDATED'],               []),
    'Russell':     (['RUSSELL E-MINI'],                        ['MICRO', '1000']),
    'DJIA':        (['DJIA CONSOLIDATED'],                     []),
    '10yr':        (['UST 10Y NOTE'],                          ['ULTRA', 'MICRO']),
    'VIX':         (['VIX FUTURES'],                           []),
    'Crude':       (['CRUDE OIL'],                             ['OPTION']),   # DUMP-ALL: v1.107.0 guess matched NONE; surface every NYMEX 'CRUDE OIL...' variant so the NYMEX WTI benchmark headline name is read off the runner
    'NatGas':      (['NAT GAS NYME', 'NEW YORK MERCANTILE'],   []),
    'Agriculture': (['CORN', 'CHICAGO BOARD OF TRADE'],        ['MINI']),
}
# validated Sarmaaya ground truth — legacy Non-Commercial net (= noncomm_long - noncomm_short), 2026-06-16.
# Nasdaq/DJIA already MATCHED EXACTLY in v1.106.0; S&P is the one still to confirm this pass.
_COT_LEGACY_TRUTH = {'SP500': -193978, 'NASDAQ': -20866, 'DJIA': 4339}

def probe_cot_legacy():
    """ISOLATED, logging-only, runner-side. Resolves the three unknowns that block the COT Non-Commercial
    repoint, because the sandbox cannot reach CFTC: (1) which legacy COMBINED Socrata dataset resolves
    (6dca-aqww futures-only vs jun7-fc8e fut+options), (2) that it carries noncomm_positions_long_all/
    short_all + open_interest_all + the report-date column, (3) the ACTUAL distinct market_and_exchange_
    names matching each tracked contract (so the correct E-mini/Cons/mini VARIANT keyword is LOCKED,
    not guessed), and (4) the latest Non-Commercial long/short/net per contract + a CHECK against the
    validated Sarmaaya ground truth (S&P -193,978 / Nasdaq -20,866 / DJIA +4,339) so the basis is PROVEN
    before any production code trusts it. Each GET guarded; the whole call is wrapped in main -> touches
    NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze. NEXT: read the
    [COT legacy probe] block, lock dataset+columns+per-contract keyword, repoint ALL COT-futures contracts
    to legacy Non-Commercial + add Russell/DJIA in v1.107.0, then flip COT_LEGACY_PROBE False."""
    if not COT_LEGACY_PROBE:
        return
    headers = {'User-Agent': UA}
    log('  [COT legacy probe] CFTC legacy COMBINED Non-Commercial — dataset / columns / contract names / ground-truth check:')
    for label, dsid in _COT_LEGACY_DATASETS:
        url = (f'https://publicreporting.cftc.gov/resource/{dsid}.json'
               '?$order=report_date_as_yyyy_mm_dd DESC&$limit=600')
        try:
            r = _retry_get(url, headers=headers, timeout=(8, 12), tries=2, base=1.0)
        except Exception as e:
            log(f'    {label} ({dsid}) FETCH FAIL {str(e)[:90]}')
            continue
        if r.status_code != 200:
            log(f'    {label} ({dsid}) HTTP {r.status_code} body[:160]={r.text[:160]!r}')
            continue
        try:
            rows = r.json()
        except Exception as e:
            log(f'    {label} ({dsid}) JSON FAIL {str(e)[:90]}')
            continue
        if not isinstance(rows, list) or not rows:
            log(f'    {label} ({dsid}) HTTP 200 but no rows (dataset id likely wrong)')
            continue
        r0 = rows[0]
        has_nc = ('noncomm_positions_long_all' in r0 and 'noncomm_positions_short_all' in r0)
        log(f'    {label} ({dsid}) HTTP 200 rows={len(rows)} '
            f'noncomm_cols={has_nc} open_interest_all={"open_interest_all" in r0} '
            f'report_date_col={"report_date_as_yyyy_mm_dd" in r0}')
        log(f'      column keys ({len(r0)}): {sorted(r0.keys())}')
        for key, (inc, exc) in _COT_LEGACY_PROBE_KW.items():
            seen = []   # (name, long, short, net, oi, date), newest-first, up to 12 distinct names
            for rec in rows:
                nm = str(rec.get('market_and_exchange_names', '')).upper()
                if (all(k in nm for k in inc) and not any(x in nm for x in exc)
                        and nm not in [s[0] for s in seen]):
                    try:
                        lng = float(rec.get('noncomm_positions_long_all', 0) or 0)
                        sht = float(rec.get('noncomm_positions_short_all', 0) or 0)
                        oi  = float(rec.get('open_interest_all', 0) or 0)
                    except Exception:
                        lng = sht = oi = 0.0
                    seen.append((nm, int(lng), int(sht), int(lng - sht), int(oi),
                                 rec.get('report_date_as_yyyy_mm_dd')))
                    if len(seen) >= 12:
                        break
            if not seen:
                log(f'      {key:12}: NO legacy contract matched include={inc} exclude={exc}')
                continue
            log(f'      {key:12}: {len(seen)} match(es) for include={inc} exclude={exc}:')
            for (nm, lng, sht, net, oi, dt) in seen:
                chk = ''
                if key in _COT_LEGACY_TRUTH:
                    gt = _COT_LEGACY_TRUTH[key]
                    ok = abs(net - gt) <= max(2000, abs(gt) * 0.03)   # within ~3% or 2k contracts
                    chk = f'  [CHECK vs Sarmaaya {gt:+,}: {"MATCH" if ok else "DIFFERS"}]'
                log(f'         "{nm}"  L={lng:,}  S={sht:,}  net={net:+,}  OI={oi:,}  date={dt}{chk}')


# =============================================================
# 2d. ZACKS SECTOR ENGINE — per-ticker rank scrape (M1 quote-feed method),
#     #1/#2 grouped by GICS sector to qualify sectors.  Never raises.
# =============================================================
ZACKS_SECTOR_UNIVERSE = {
    # Fixed S&P representative list across all 11 GICS sectors (large-cap sector read).
    'Information Technology': ['MSFT','NVDA','AVGO','AAPL','ORCL','CRM','AMD','ADBE','CSCO','ACN','TXN','QCOM','INTC','IBM','NOW','MU','AMAT','LRCX','ANET','DELL'],
    'Health Care':           ['LLY','UNH','JNJ','ABBV','MRK','TMO','ABT','ISRG','DHR','PFE','AMGN','BMY','CI','GILD','VRTX','CVS','MDT','ELV','REGN','HCA'],
    'Financials':            ['JPM','BAC','WFC','GS','MS','SPGI','AXP','BLK','C','SCHW','CB','PGR','MMC','BX','PNC','USB','TFC','AON','ICE','COF'],
    'Consumer Discretionary':['AMZN','TSLA','HD','MCD','NKE','LOW','BKNG','SBUX','TJX','ORLY','GM','F','MAR','CMG','ROST','HLT','YUM','DHI','LEN','AZO'],
    'Communication Services':['GOOGL','META','NFLX','DIS','TMUS','VZ','T','CMCSA','CHTR','EA','TTWO','WBD','OMC','LYV','MTCH','FOXA','NWSA','DASH'],
    'Industrials':           ['CAT','GE','RTX','UNP','HON','ETN','BA','LMT','DE','UPS','ADP','GD','NOC','EMR','CSX','ITW','MMM','FDX','WM','PH'],
    'Consumer Staples':      ['WMT','PG','KO','PEP','COST','MDLZ','PM','MO','CL','TGT','KMB','GIS','SYY','KHC','STZ','KR','HSY','KDP','MNST','ADM'],
    'Energy':                ['XOM','CVX','COP','EOG','SLB','MPC','PSX','OXY','WMB','VLO','KMI','OKE','HAL','DVN','FANG','BKR','CTRA'],
    'Materials':             ['LIN','SHW','APD','ECL','FCX','NEM','NUE','DOW','DD','CTVA','PPG','VMC','MLM','ALB','IFF','LYB','STLD','CF','MOS','BALL'],
    'Utilities':             ['NEE','DUK','SO','D','AEP','SRE','EXC','XEL','PEG','ED','VST','WEC','EIX','AWK','DTE','PCG','AEE','CNP','CMS','ATO'],
    'Real Estate':           ['PLD','AMT','EQIX','WELL','CCI','PSA','O','SPG','DLR','VICI','CBRE','EXR','AVB','EQR','VTR','SBAC','WY','INVH','ARE','MAA'],
}
def _gics_from_yahoo(sec):
    if not sec: return None
    s = sec.lower()
    m = {'technology':'Information Technology','healthcare':'Health Care','financial':'Financials',
         'consumer cyclical':'Consumer Discretionary','communication':'Communication Services',
         'industrials':'Industrials','consumer defensive':'Consumer Staples','energy':'Energy',
         'basic materials':'Materials','utilities':'Utilities','real estate':'Real Estate'}
    for k,v in m.items():
        if k in s: return v
    return None

# ===================== Smart-Money ETF Holdings Overlap (Part D) =====================
# Screen a broad ETF candidate universe through Zacks Rank, keep #1/#2, fetch each
# survivor's holdings, aggregate by stock to find CONVICTION OVERLAP, flag Zacks-confirmed
# names. Weekly cadence (holdings barely move week-to-week). The Zacks rank screen reuses
# the same quote-feed endpoint the stock scrape uses (proven on the runner). The holdings
# fetch hits stockanalysis.com — that domain isn't on the sandbox allowlist, so it validates
# on the GitHub run; the aggregation/ranking below is pure logic and is unit-tested locally.
# Fixed universe: the user's top-30 Zacks Rank-#1, US, Equities ETFs by 1-Year performance
# (from the Zacks ETF screener, 2026-06-03). NO per-run rank screening — these are
# pre-confirmed #1; the scan only fetches their holdings and builds the overlap. Refresh
# this list quarterly when Zacks re-ranks. Holdings fetch (stockanalysis.com) validates on
# the GitHub run; the aggregation/ranking below is pure logic and is unit-tested locally.
TOP_ETFS = [
    'FTXL','PSI','SOXX','SOXQ','XSD','IGPT','PSCT','KNCT','VLUE','RSPT',
    'XNTK','XLK','QTEC','IDGT','IGM','FTEC','VGT','IYW','PWB','VDE',
    'XLE','QQQM','QQQ','VTWO','RPG','BIBL','SNPG','VB','VONV','IWD',
]
ETF_OVERLAP_TOP_N = 25     # number of consensus stocks to surface

# Wave Z: 12 largest active US equity mutual funds by AUM (quarterly-refresh hardcoded list).
# Zacks mutual-fund rank list is paywalled — use AUM-ranked funds as quality proxy instead.
# These are the institutional "smart money" that active managers watch most closely.
TOP_INST_FUNDS = [
    'FCNTX',  # Fidelity Contrafund ~$150B
    'FDGRX',  # Fidelity Growth Company ~$70B
    'AGTHX',  # American Funds Growth Fund ~$300B
    'AIVSX',  # American Funds Investment Co ~$100B
    'TRBCX',  # T. Rowe Price Blue Chip Growth ~$75B
    'PRGFX',  # T. Rowe Price Growth Stock ~$60B
    'DODGX',  # Dodge & Cox Stock ~$100B
    'VWELX',  # Vanguard Wellington ~$105B
    'VPCCX',  # Vanguard Primecap ~$65B
    'MEIAX',  # MFS Value ~$30B
    'SEQUX',  # Sequoia Fund ~$5B
]
INST_FUND_TOP_N = 25   # top holdings per fund to consider
_ETF_OVERLAP_CODE_VER = '1'  # v1.112.0 (F4): bump ONLY when ETF-overlap code changes. The 7-day
                             # throttle now keys on THIS, not SCAN_VERSION, so an unrelated scanner
                             # version bump no longer forces a ~40s ETF re-scrape every release.

# Authoritative per-ETF metrics from the user's Zacks ETF screen (2026-06-03): (name, YTD%, 1Y%).
# 3Y% and expense ratio aren't in the Zacks ETF export, so the scan fetches those two from
# Yahoo (validates on the GitHub run; shows None/'—' if Yahoo doesn't return them).
ETF_META = {
 'FTXL':('First Trust NASDAQ Semiconductor ETF',100.1,215.4),
 'PSI':('Invesco Semiconductors ETF',94.8,201.9),
 'SOXX':('iShares Semiconductor ETF',90.0,179.9),
 'SOXQ':('Invesco PHLX Semiconductor ETF',83.1,173.0),
 'XSD':('SPDR S&P Semiconductor ETF',87.0,172.2),
 'IGPT':('Invesco AI and Next Gen Software ETF',71.3,127.9),
 'PSCT':('Invesco S&P SmallCap Info Technology ETF',50.8,100.8),
 'KNCT':('Invesco Next Gen Connectivity ETF',60.8,99.2),
 'VLUE':('iShares MSCI USA Value Factor ETF',47.8,91.0),
 'RSPT':('Invesco S&P 500 Equal Weight Technology ETF',45.9,77.9),
 'XNTK':('SPDR NYSE Technology ETF',35.8,74.9),
 'XLK':('Technology Select Sector SPDR ETF',36.1,70.2),
 'QTEC':('First Trust NASDAQ-100 Technology ETF',42.7,70.0),
 'IDGT':('iShares U.S. Digital Infrastructure & RE ETF',53.3,66.0),
 'IGM':('iShares Expanded Tech Sector ETF',31.0,65.0),
 'FTEC':('Fidelity MSCI Info Technology Index ETF',32.1,65.0),
 'VGT':('Vanguard Information Technology ETF',31.9,64.4),
 'IYW':('iShares U.S. Technology ETF',29.2,63.2),
 'PWB':('Invesco Large Cap Growth ETF',27.8,47.1),
 'VDE':('Vanguard Energy ETF',29.3,45.1),
 'XLE':('Energy Select Sector SPDR ETF',29.0,44.2),
 'QQQM':('Invesco NASDAQ 100 ETF',21.0,43.7),
 'QQQ':('Invesco QQQ',21.0,43.6),
 'VTWO':('Vanguard Russell 2000 ETF',17.6,42.2),
 'RPG':('Invesco S&P 500 Pure Growth ETF',30.0,41.8),
 'BIBL':('Inspire 100 ETF',20.9,38.5),
 'SNPG':('Xtrackers S&P 500 Growth ETF',10.8,30.7),
 'VB':('Vanguard Small-Cap ETF',14.0,30.0),
 'VONV':('Vanguard Russell 1000 Value ETF',13.3,27.9),
 'IWD':('iShares Russell 1000 Value ETF',13.3,27.8),
}

def fetch_etf_meta(etf):
    """3Y return + expense ratio for an ETF via Yahoo. Guarded; returns {y3, expense} (None if missing)."""
    out = {'y3': None, 'expense': None}
    try:
        import yfinance as _yf
        t = _yf.Ticker(etf)
        try:
            h = t.history(period='3y')
            c = h['Close'].dropna() if (h is not None and not h.empty) else None
            if c is not None and len(c) > 2:
                out['y3'] = round((float(c.iloc[-1]) / float(c.iloc[0]) - 1) * 100, 1)
        except Exception:
            pass
        try:
            info = t.info or {}
            ne = info.get('netExpenseRatio')           # Yahoo: already in PERCENT (0.60 = 0.60%)
            ar = info.get('annualReportExpenseRatio')  # Yahoo: a FRACTION (0.006 = 0.60%)
            ex = float(ne) if ne is not None else (float(ar) * 100 if ar is not None else None)
            if ex is not None:
                if ex > 5:        # no ETF charges >5%; guard against any unit surprise
                    ex /= 100
                out['expense'] = round(ex, 2)
        except Exception:
            pass
    except Exception as e:
        log(f'    · meta fetch failed for {etf}: {e}')
    return out

_ETF_DIAG = {'done': False}
def _parse_holdings(rows):
    out = []
    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        sym = row.get('asset') or row.get('symbol') or row.get('s') or row.get('ticker')
        wt  = (row.get('weightPercentage') if row.get('weightPercentage') is not None else
               row.get('weight') if row.get('weight') is not None else
               row.get('w') if row.get('w') is not None else
               row.get('as') if row.get('as') is not None else
               row.get('assetsPercent') if row.get('assetsPercent') is not None else
               row.get('percent') if row.get('percent') is not None else row.get('assetPercent'))
        if sym and wt is not None:
            try:
                tk = str(sym).upper().strip().lstrip('$').strip()
                if tk:
                    out.append({'ticker': tk, 'weight': float(str(wt).replace('%','').replace(',','').strip())})
            except Exception:
                pass
    return out

def fetch_etf_holdings(etf):
    """ETF holdings -> [{ticker, weight}]. stockanalysis.com is the working free source (FMP
    holdings is premium-402 / v3 legacy-403 on the free key, so it's fallback-only).
    Logs a ONE-TIME diagnostic (status + body snippet + rows parsed) for the first ETF so a
    failure is debuggable from the run log instead of silently returning []."""
    diag = not _ETF_DIAG['done']
    sources = [('stockanalysis', f'https://stockanalysis.com/api/symbol/e/{etf}/holdings')]
    if FMP_KEY:
        sources += [
            ('fmp-stable', f'https://financialmodelingprep.com/stable/etf/holdings?symbol={etf}&apikey={FMP_KEY}'),
            ('fmp-v3',     f'https://financialmodelingprep.com/api/v3/etf-holder/{etf}?apikey={FMP_KEY}'),
        ]
    sources.append(('stockanalysis', f'https://stockanalysis.com/api/symbol/e/{etf}/holdings'))
    result = []
    for label, url in sources:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
            if diag:
                log(f'    · [diag] {label} {etf}: HTTP {r.status_code} body[:180]={r.text[:180]!r}')
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, list):
                    rows = j
                elif isinstance(j, dict):
                    dn = j.get('data')
                    rows = (dn.get('list') or dn.get('holdings') if isinstance(dn, dict) else dn) \
                           or j.get('holdings') or j.get('list') or []
                else:
                    rows = []
                parsed = _parse_holdings(rows)
                if diag:
                    log(f'    · [diag] {label} {etf}: parsed {len(parsed)} holdings')
                if parsed:
                    result = parsed
                    break
        except Exception as e:
            if diag:
                log(f'    · [diag] {label} {etf}: EXC {e}')
    if diag:
        _ETF_DIAG['done'] = True
    return result

def build_etf_overlap(rank12_etfs, holdings_map, zacks_top_tickers, top_n=ETF_OVERLAP_TOP_N):
    """Aggregate holdings across Zacks #1/#2 ETFs. conviction = blend(weight, breadth) with a
    Zacks-confirmed boost. Pure logic / unit-tested. Returns ranked top-N consensus stocks."""
    agg = {}
    for e in rank12_etfs:
        tk = e['etf']
        for h in holdings_map.get(tk, []):
            s = (h.get('ticker') or '').upper().strip()
            if not s or len(s) > 6 or s == tk:
                continue
            a = agg.setdefault(s, {'weight_sum':0.0, 'etfs':set()})
            a['weight_sum'] += float(h.get('weight') or 0)
            a['etfs'].add(tk)
    n_etf = max(len(rank12_etfs), 1)
    max_w = max((a['weight_sum'] for a in agg.values()), default=1.0) or 1.0
    zset = set(zacks_top_tickers or [])
    rows = []
    for s, a in agg.items():
        breadth = len(a['etfs'])
        w_norm = a['weight_sum'] / max_w
        b_norm = breadth / n_etf
        zc = s in zset
        conviction = round(100*(0.55*w_norm + 0.35*b_norm) + (10 if zc else 0), 1)
        rows.append({'ticker': s, 'etf_count': breadth, 'agg_weight': round(a['weight_sum'],2),
                     'conviction': conviction, 'zacks_confirmed': zc, 'in_etfs': sorted(a['etfs'])[:8]})
    rows.sort(key=lambda r: (-r['conviction'], -r['etf_count'], -r['agg_weight']))
    top = rows[:top_n]
    tot_w = sum(r['agg_weight'] for r in top) or 1.0
    for r in top:
        r['alloc_pct'] = round(r['agg_weight'] / tot_w * 100, 2)   # mirror-able weight across the shown names
    return top
# =====================================================================================

def fetch_zacks_sectors(survivors=None):
    """Scrape per-ticker Zacks rank for the fixed S&P universe + scan survivors (deduped),
    keep #1/#2, group by GICS sector. Returns {sector:{rank1,rank2,top,total,pct_top,top_tickers}}."""
    # Build universe: fixed list (with known sector) + survivors (sector from their record)
    uni = {}  # ticker -> gics sector
    for sec, tickers in ZACKS_SECTOR_UNIVERSE.items():
        for t in tickers:
            uni[t] = sec
    if survivors:
        for r in survivors:
            tk = r.get('ticker'); g = _gics_from_yahoo(r.get('sector'))
            if tk and g and tk not in uni:
                uni[tk] = g
    tickers = sorted(uni.keys())
    log(f'=== Zacks sector scrape: {len(tickers)} tickers (~{len(tickers)*2.5/60:.0f} min) ===')
    sectors = {s: {'rank1':0,'rank2':0,'top':0,'total':0,'pct_top':0.0,'top_tickers':[]}
               for s in ZACKS_SECTOR_UNIVERSE}
    fails = 0
    ranks = {}   # P7: per-ticker {ticker: zacks_rank 1..5} for the US Explosive #1/#2 chip
    for i, tk in enumerate(tickers):
        sec = uni[tk]
        if sec not in sectors:
            sectors[sec] = {'rank1':0,'rank2':0,'top':0,'total':0,'pct_top':0.0,'top_tickers':[]}
        try:
            time.sleep(0.4)  # v1.117.0: was 2.5s -> 0.4s (6x faster; 988s -> ~168s)
            d = requests.get(f'https://quote-feed.zacks.com/index?t={tk}',
                             headers={'User-Agent':'Mozilla/5.0'}, timeout=15).json()
            rec = d.get(tk, {}) or {}
            rank = rec.get('zacks_rank')
            rank = int(rank) if rank not in (None,'','null') else None
            if rank is not None: ranks[tk] = rank
            sectors[sec]['total'] += 1
            if rank == 1:
                sectors[sec]['rank1'] += 1; sectors[sec]['top'] += 1; sectors[sec]['top_tickers'].append(tk)
            elif rank == 2:
                sectors[sec]['rank2'] += 1; sectors[sec]['top'] += 1; sectors[sec]['top_tickers'].append(tk)
        except Exception:
            fails += 1
    for s, v in sectors.items():
        v['pct_top'] = round(v['top']/v['total']*100, 1) if v['total'] else 0.0
    log(f'  Zacks sector scrape done: {fails} failures of {len(tickers)}')
    return sectors, ranks

# =============================================================
# 2b. METALS DATA — Tab 12 Gold & Metals
# =============================================================
def _metal_technicals(closes):
    """v1.105.0 — pure: given an oldest->newest list of daily closes, return moving-average /
    RSI / trend / compact-history fields for a metal so the dashboard can draw a REAL price trend
    (not just the WoW/MoM deltas). Everything is guarded by length; missing pieces are simply omitted
    (never fabricated). Returns a dict of suffixes -> value (caller prefixes the metal key)."""
    out = {}
    try:
        c = [float(x) for x in closes if x == x]   # strip NaN
    except Exception:
        return out
    n = len(c)
    if n < 2:
        return out
    px = c[-1]

    def _sma(p):
        return round(sum(c[-p:]) / p, 2) if n >= p else None
    s50, s200 = _sma(50), _sma(200)
    if s50 is not None:  out['sma50'] = s50
    if s200 is not None: out['sma200'] = s200

    # RSI(14), Wilder smoothing
    if n >= 16:
        gains, losses = [], []
        for i in range(1, n):
            d = c[i] - c[i - 1]
            gains.append(d if d > 0 else 0.0)
            losses.append(-d if d < 0 else 0.0)
        p = 14
        ag = sum(gains[:p]) / p
        al = sum(losses[:p]) / p
        for i in range(p, len(gains)):
            ag = (ag * (p - 1) + gains[i]) / p
            al = (al * (p - 1) + losses[i]) / p
        out['rsi14'] = 100.0 if al == 0 else round(100.0 - 100.0 / (1.0 + ag / al), 1)

    # trend label vs the 200-day (the institutional trend filter) + golden/death cross
    if s200:
        out['ma_trend'] = 'up' if px >= s200 else 'down'
        out['ext_200_pct'] = round((px / s200 - 1.0) * 100.0, 1)
    elif s50:
        out['ma_trend'] = 'up' if px >= s50 else 'down'
    if s50 and s200:
        out['cross'] = 'golden' if s50 >= s200 else 'death'

    # compact price history for a real trend chart: last ~120 trading days, downsampled to ~60 points
    tail = c[-120:]
    step = max(1, len(tail) // 60)
    hist = [round(float(x), 2) for x in tail[::step]]
    if hist and hist[-1] != round(px, 2):
        hist.append(round(px, 2))   # always end on the latest close
    out['hist'] = hist
    return out


def fetch_metals():
    """
    Fetches all data for Tab 12:
    - Metal spot prices: GC=F, SI=F, PL=F, PA=F (Yahoo)
    - DXY Dollar Index: DX-Y.NYB (Yahoo)
    - Fed balance sheet QE/QT: WALCL (FRED)
    - COT positioning: CFTC CMX page (non-commercial net)
    - News RSS for IMF/Default/GeoPolitical scores
    Returns dict stored under data['macros']['metals']
    """
    import re
    import yfinance as yf

    out = EXISTING.get('macros', {}).get('metals', {}).copy()
    headers = {'User-Agent': UA}
    log('Fetching metals data...')

    # 1. Metal prices + DXY via Yahoo Finance
    yahoo_tickers = {
        'gold_px':      'GC=F',
        'silver_px':    'SI=F',
        'platinum_px':  'PL=F',
        'palladium_px': 'PA=F',
        'copper_px':    'HG=F',
        'dxy':          'DX-Y.NYB',
    }
    for key, sym in yahoo_tickers.items():
        try:
            h = yf.Ticker(sym).history(period='1y')   # v1.105.0 widened 6mo->1y so SMA200 has enough history
            if len(h) > 0:
                _closes = [round(float(x), 2) for x in h['Close'].values if x == x]
                out[key] = round(float(h['Close'].iloc[-1]), 2)
                out[f'{key}_date'] = str(h.index[-1].date())
                for _tk,_tv in _series_trend(_closes[-64:], w=(5,21,63)).items():
                    out[f'{key}_{_tk}'] = _tv
                # v1.105.0 metal technicals: SMA50/SMA200, RSI(14), trend label + cross, compact price-history array
                for _tk,_tv in _metal_technicals(_closes).items():
                    out[f'{key}_{_tk}'] = _tv
                _t200 = out.get(f'{key}_sma200')
                log(f'  ✓ {key} ({sym}): {out[key]}' + (f' · SMA200 {_t200} · {out.get(f"{key}_ma_trend","")} {out.get(f"{key}_cross","")} · RSI {out.get(f"{key}_rsi14","")}' if _t200 else ''))
        except Exception as e:
            warn(f'{key} ({sym}) failed: {e}')
            lg = safe_get(EXISTING, 'macros', 'metals', key)
            if lg is not None:
                out[key] = lg

    if out.get('gold_px') and out.get('silver_px') and out['silver_px'] > 0:
        out['gs_ratio'] = round(out['gold_px'] / out['silver_px'], 1)
        log(f'  ✓ Gold:Silver ratio = {out["gs_ratio"]}')

    # 2. QE/QT — Fed balance sheet WALCL via FRED
    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            s = fred.get_series('WALCL').dropna()
            if len(s) >= 2:
                current = float(s.iloc[-1])
                prior   = float(s.iloc[-5]) if len(s) >= 5 else float(s.iloc[0])
                out['walcl']        = round(current / 1e6, 2)   # FRED WALCL is $millions -> store $trillions
                out['walcl_change'] = round((current - prior) / prior * 100, 2)
                out['walcl_date']   = str(s.index[-1].date())
                for _k, _v in _series_trend([float(x)/1e6 for x in s.values[-14:]]).items():
                    out['walcl_'+_k] = _v
                log(f'  ✓ WALCL: ${out["walcl"]}T ({out["walcl_change"]:+.2f}%)')
        except Exception as e:
            warn(f'WALCL FRED failed: {e}')
            for k in ('walcl', 'walcl_change', 'walcl_wow', 'walcl_mom', 'walcl_qoq'):
                lg = safe_get(EXISTING, 'macros', 'metals', k)
                if lg is not None:
                    out[k] = lg

    # 2b. WAVE M6 — true real yield (10y TIPS), 10y breakeven, Gold VIX via FRED (same proven Fred path)
    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            for key, sid in (('dfii10', 'DFII10'), ('breakeven_10y', 'T10YIE'), ('gvz', 'GVZCLS')):
                try:
                    s = fred.get_series(sid).dropna()
                    if len(s) > 0:
                        out[key] = round(float(s.iloc[-1]), 2)
                        out[f'{key}_date'] = str(s.index[-1].date())
                        for _tk,_tv in _series_trend([round(float(x),2) for x in s.values[-64:]], w=(5,21,63)).items():
                            out[f'{key}_{_tk}'] = _tv
                        log(f'  ✓ {key} ({sid}): {out[key]}')
                except Exception as e2:
                    warn(f'{key} ({sid}) FRED failed: {e2}')
                    lg = safe_get(EXISTING, 'macros', 'metals', key)
                    if lg is not None:
                        out[key] = lg
        except Exception as e:
            warn(f'M6 FRED block failed: {e}')

    # 3. COT positioning — CFTC CMX page
    try:
        r = requests.get('https://www.cftc.gov/dea/futures/deacmxsf.htm',
                         headers=headers, timeout=15)
        if r.status_code == 200:
            text = r.text
            dm = re.search(r'POSITIONS AS OF (\d{2}/\d{2}/\d{2})', text)
            if dm:
                out['cot_date'] = dm.group(1)

            def parse_cot_block(label_re):
                blk = re.search(label_re, text, re.S)
                if not blk:
                    return None, None, None
                chunk = text[blk.start(): blk.start() + 1500]
                oi_m = re.search(r'OPEN INTEREST:\s*([\d,]+)', chunk)
                oi = int(oi_m.group(1).replace(',', '')) if oi_m else None
                comm = re.search(r'COMMITMENTS\s*\n\s*([\d,]+)\s+([\d,]+)', chunk)
                if not comm:
                    return None, None, oi
                return int(comm.group(1).replace(',', '')), int(comm.group(2).replace(',', '')), oi

            for metal, pat, pfx in [
                ('gold',   r'GOLD - COMMODITY EXCHANGE INC\.',   'cot_gold'),
                ('silver', r'SILVER - COMMODITY EXCHANGE INC\.', 'cot_silver'),
                ('copper', r'COPPER- #1 - COMMODITY EXCHANGE INC\.', 'cot_copper'),
            ]:
                nc_l, nc_s, oi = parse_cot_block(pat)
                if nc_l is not None and oi:
                    out[f'{pfx}_net']  = nc_l - nc_s
                    out[f'{pfx}_oi']   = oi
                    out[f'{pfx}_pct']  = round((nc_l - nc_s) / oi * 100, 1)
                    # v1.11: keep the long/short legs so the dashboard can show longs vs shorts
                    out[f'{pfx}_long']      = nc_l
                    out[f'{pfx}_short']     = nc_s
                    out[f'{pfx}_long_pct']  = round(nc_l / oi * 100, 1)
                    out[f'{pfx}_short_pct'] = round(nc_s / oi * 100, 1)
                    log(f'  ✓ COT {metal}: long={nc_l:,} short={nc_s:,} net={out[f"{pfx}_net"]:,} ({out[f"{pfx}_pct"]}% OI)')
                    # WAVE M5/T1 — dedup-by-report-date {d,v} history (cap 160); percentile + WoW/MoM/QoQ trend
                    hist_key = f'{pfx}_hist'
                    hist = _push_hist(safe_get(EXISTING, 'macros', 'metals', hist_key),
                                      out.get('cot_date'), out[f'{pfx}_pct'], cap=160)
                    out[hist_key] = hist
                    _vals = [h['v'] for h in hist if isinstance(h, dict) and h.get('v') is not None]
                    if len(_vals) >= 20:
                        below = sum(1 for x in _vals if x <= out[f'{pfx}_pct'])
                        out[f'{pfx}_pctile'] = round(below / len(_vals) * 100)
                        log(f'    COT {metal} percentile: {out[f"{pfx}_pctile"]}th ({len(_vals)}wk history)')
                    _tr = _hist_trend(hist)
                    for _k, _v in _tr.items():
                        out[f'{pfx}_pct_{_k}'] = _v
                    if 'wow' in _tr:
                        log(f'    COT {metal} trend: WoW {_tr["wow"]:+} ({_tr.get("wow_dir")})'
                            + (f', MoM {_tr["mom"]:+}' if 'mom' in _tr else '')
                            + (f', QoQ {_tr["qoq"]:+}' if 'qoq' in _tr else ''))

    except Exception as e:
        warn(f'COT CFTC fetch failed: {e}')
        for k in ('cot_gold_net','cot_gold_oi','cot_gold_pct','cot_gold_long','cot_gold_short','cot_gold_long_pct','cot_gold_short_pct','cot_gold_hist','cot_gold_pctile',
                  'cot_silver_net','cot_silver_oi','cot_silver_pct','cot_silver_long','cot_silver_short','cot_silver_long_pct','cot_silver_short_pct','cot_silver_hist','cot_silver_pctile',
                  'cot_copper_net','cot_copper_oi','cot_copper_pct','cot_copper_long','cot_copper_short','cot_copper_long_pct','cot_copper_short_pct','cot_copper_hist','cot_copper_pctile','cot_gold_pct_wow','cot_gold_pct_mom','cot_gold_pct_qoq','cot_silver_pct_wow','cot_silver_pct_mom','cot_silver_pct_qoq','cot_copper_pct_wow','cot_copper_pct_mom','cot_copper_pct_qoq','cot_date'):
            lg = safe_get(EXISTING, 'macros', 'metals', k)
            if lg is not None:
                out[k] = lg

    # 4. News RSS — IMF Pakistan, Default risk, GeoPolitical
    try:
        import feedparser
        rss_targets = {
            'imf_score': (
                'https://news.google.com/rss/search?q=IMF+Pakistan&hl=en',
                ['disbursement','approved','agreement','on-track','success','review'],
                ['suspended','failed','exit','default','crisis','breach']),
            'default_score': (
                'https://news.google.com/rss/search?q=Pakistan+sovereign+default+risk&hl=en',
                ['falling','improved','stable','reduced','positive'],
                ['default','crisis','elevated','warning','risk','downgrade']),
            'geo_score': (
                'https://news.google.com/rss/search?q=gold+geopolitical+Middle+East+safe+haven&hl=en',
                ['conflict','tension','war','attack','safe haven','surge','unrest'],
                ['ceasefire','peace','calm','resolved','de-escalation']),
        }
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=14)
        for key, (url, pos_kw, neg_kw) in rss_targets.items():
            try:
                feed = feedparser.parse(url)
                pos = neg = 0
                for entry in feed.entries[:20]:
                    pub = dt.datetime(*entry.published_parsed[:6]) if hasattr(entry,'published_parsed') and entry.published_parsed else None
                    if pub and pub < cutoff:
                        continue
                    txt = (entry.get('title','') + ' ' + entry.get('summary','')).lower()
                    pos += sum(1 for kw in pos_kw if kw.lower() in txt)
                    neg += sum(1 for kw in neg_kw if kw.lower() in txt)
                if key == 'geo_score':
                    out[key] = +1 if pos > neg else (0 if pos == neg else -1)
                else:
                    out[key] = -1 if pos > neg else (0 if pos == neg else +1)
                log(f'  ✓ {key}: {out[key]:+d} (pos={pos} neg={neg})')
            except Exception as e:
                warn(f'{key} RSS failed: {e}')
                lg = safe_get(EXISTING, 'macros', 'metals', key)
                if lg is not None:
                    out[key] = lg
    except ImportError:
        warn('feedparser not available; using last-good news scores')
        for k in ('imf_score', 'default_score', 'geo_score'):
            lg = safe_get(EXISTING, 'macros', 'metals', k)
            if lg is not None:
                out[k] = lg

    log(f'  Metals complete: {len([k for k in out if not k.endswith(("_date","_source"))])} fields')
    return out


# =============================================================
# 3. US UNIVERSE
# =============================================================
_LARGE_CAP_CACHE = None
def us_large_cap_set():
    """Decision 5: fixed S&P-200 large-caps (all 11 GICS) + sector-representative mega-caps + thematic names,
    merged into the small-cap universe so the screen also covers large-cap sectors."""
    global _LARGE_CAP_CACHE
    if _LARGE_CAP_CACHE is None:
        s = set()
        for _tk in ZACKS_SECTOR_UNIVERSE.values():
            s.update(_tk)
        s.update(['XOM','CVX','COP','EOG','GOOGL','MSFT','META','UNH','GIS','KO',
                  'NVDA','TSM','ANET','MU','WDC','STX','DELL','AMD','LLY','AVGO'])
        _LARGE_CAP_CACHE = s
    return _LARGE_CAP_CACHE


def fetch_us_universe():
    log('Fetching US universe (NASDAQ-sourced top tickers)...')
    url = 'https://raw.githubusercontent.com/Ate329/top-us-stock-tickers/main/tickers/all.csv'
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=30)
        if r.status_code == 200:
            tickers = []
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                sym = (row.get('symbol') or '').strip().upper()
                mc = row.get('marketCap', '').strip()
                try:
                    mc_val = float(mc) if mc else 0
                except ValueError:
                    mc_val = 0
                if sym and sym.replace('.','').replace('-','').isalnum() and len(sym) <= 5:
                    if US_SMALL_CAP_MIN <= mc_val <= US_SMALL_CAP_MAX:
                        tickers.append(sym)
            large = us_large_cap_set()
            _scset = set(tickers)
            merged = tickers + [t for t in large if t not in _scset]
            log(f'  Got {len(tickers)} small-cap + {len(merged)-len(tickers)} large-cap = {len(merged)} merged US tickers (Decision 5)')
            if len(merged) > 0:
                return merged
    except Exception as e:
        warn(f'Primary US universe failed: {e}')

    try:
        url2 = 'https://raw.githubusercontent.com/Ate329/top-us-stock-tickers/main/tickers/sp500.csv'
        r = requests.get(url2, headers={'User-Agent': UA}, timeout=30)
        if r.status_code == 200:
            tickers = []
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                sym = (row.get('symbol') or '').strip().upper()
                if sym:
                    tickers.append(sym)
            if len(tickers) > 0:
                warn(f'US universe fell back to S&P 500 ({len(tickers)} tickers)')
                return tickers
    except Exception as e:
        warn(f'US universe fallback 1 failed: {e}')

    warn('US universe using hardcoded watchlist (final fallback)')
    return ['NVDA','META','TSM','AAPL','MSFT','GOOGL','AMZN',
            'PLPC','MGNI','SG','TOI','INMD','TRS','ADV','PKBK',
            'AXON','ENPH','MELI','PLTR','VRT','AVGO']


US_MAIN_EXCH = {'NASDAQ', 'NYSE', 'AMEX', 'NYSE ARCA', 'BATS', 'NYSE MKT', 'NYSEARCA'}
_US_TV_COLS = ['name', 'market_cap_basic', 'exchange', 'sector',
               'total_revenue_yoy_growth_fq', 'total_revenue_yoy_growth_ttm',
               # Wave D1 instrumentation: EPS-YoY-growth so the financial bucket
               # (which bypasses the revenue gate) can be measured for a future
               # bank-appropriate TV gate. Read for diagnostics only — gating unchanged.
               'earnings_per_share_diluted_yoy_growth_fq',
               'earnings_per_share_diluted_yoy_growth_ttm',
               # Wave D1 step 2: ROE is the bank-appropriate quality gate (canonical
               # Sarmaaya framework: ROE is the lead stability factor). Instrumented this
               # run (distribution + coverage); becomes the primary financial gate once
               # TV coverage/units are confirmed on a live run.
               'return_on_equity',
               # Wave O L1 (fundamentals cutover): the candidate dict's price/PE/D-E so the US
               # screen is built from this one POST instead of ~660 per-name Yahoo .info calls.
               # Wave A / V-G-M: Perf.6M + Perf.3M = price-momentum raw data for the Momentum
               # style read on the Explosive/Multibagger tabs (one extra field, no per-name fetch).
               # Wave M-A: SMA50 + SMA200 = price moving averages, the trend lever for sector
               # selection (price-vs-200-DMA, golden/death cross, extension). One extra column on
               # the POST already being made; no per-name history download.
               'close', 'price_earnings_ttm', 'debt_to_equity', 'Perf.6M', 'Perf.3M',
               'SMA50', 'SMA200']


def is_common_us_ticker(tk):
    """PURE. True only for plain common-share tickers. TradingView's america `type=stock`
    feed leaks preferred-share series whose symbol carries a '/<class>' suffix (ABR/PE,
    GNL/PD, TWO/PA, ...). Those 502 on Yahoo and inflate the financials bucket (one REIT =
    many preferred series), so they're dropped before the universe is built. Conservative:
    only '/' (and stray whitespace) is rejected — '.'/'-' class shares are left alone,
    matching the existing Yahoo-universe guard. Unit-tested."""
    if not tk or not isinstance(tk, str):
        return False
    return '/' not in tk and ' ' not in tk


def classify_us_tv_row(rec, thr):
    """PURE. Decide whether a TradingView america row should be sent to the Yahoo screen.
    Returns 'financial' | 'growth' | 'ttm' | 'skip'. (The named large-cap set is unioned
    in by the caller; this only judges band names.)
      - financial: TV cannot measure bank revenue growth -> pass straight to Yahoo (screened as today)
      - growth:    non-financial, quarterly YoY rev-growth (fq) >= threshold (matches Yahoo MRQ)
      - ttm:       non-financial, fq is NULL but TTM YoY >= threshold (fallback recovers NULL-fq names)
      - skip:      OTC/foreign exch, out of band, or non-financial failing growth (Yahoo would reject too)
    thr is the growth threshold in PERCENT (e.g. 15.0)."""
    if (rec.get('exchange') or '') not in US_MAIN_EXCH:
        return 'skip'
    mc = rec.get('market_cap_basic') or 0
    if not (US_SMALL_CAP_MIN <= mc <= US_SMALL_CAP_MAX):
        return 'skip'
    if 'Financ' in (rec.get('sector') or ''):
        # Wave D1 step 3 gate. Banks are screened on bank-appropriate metrics, not revenue
        # growth (meaningless for a spread/credit business; the revenue gate is bypassed for
        # financials in screen_us_stock). PRIMARY gate = ROE >= ROE_FIN_MIN (the canonical lead
        # quality metric, unit-normalised); SECONDARY = drop clearly-DETERIORATING banks (EPS
        # YoY < 0). A missing vendor field is never a reason to drop a bank (pass through).
        roe = _roe_pct(rec.get('return_on_equity'))
        if roe is not None and roe < ROE_FIN_MIN:
            return 'skip'
        fq  = rec.get('earnings_per_share_diluted_yoy_growth_fq')
        ttm = rec.get('earnings_per_share_diluted_yoy_growth_ttm')
        eps = fq if fq is not None else ttm
        if eps is not None and eps < 0:
            return 'skip'
        return 'financial'
    fq = rec.get('total_revenue_yoy_growth_fq')
    ttm = rec.get('total_revenue_yoy_growth_ttm')
    if fq is not None and fq >= thr:
        return 'growth'
    if fq is None and ttm is not None and ttm >= thr:
        return 'ttm'
    return 'skip'


def _fin_eps_diag(pairs):
    """PURE. Wave D1 instrumentation. Given (eps_fq, eps_ttm) YoY-growth pairs for the TV
    financial bucket, summarise the distribution so a future bank-appropriate gate threshold
    can be chosen from real data instead of a blind guess. 'effective' growth = fq when
    present else ttm. Returns a one-line diagnostic string. Changes NO gating. Unit-tested."""
    n = len(pairs)
    n_fq = sum(1 for fq, _ in pairs if fq is not None)
    n_ttm = sum(1 for _, ttm in pairs if ttm is not None)
    eff = [(fq if fq is not None else ttm) for fq, ttm in pairs
           if (fq if fq is not None else ttm) is not None]
    if not eff:
        return (f'[diag] financials EPS-growth: {n} financials, 0 with TV EPS data '
                f'(fq {n_fq}, ttm {n_ttm}) — TV exposes no EPS growth for this bucket')
    s = sorted(eff)
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    p = {t: sum(1 for v in eff if v >= t) for t in (0, 5, 10, 15)}
    return (f'[diag] financials EPS-growth: {n} financials, {len(eff)} with data '
            f'(fq {n_fq}, ttm {n_ttm}); min {s[0]:.1f}% median {median:.1f}% max {s[-1]:.1f}%; '
            f'pass >=0% {p[0]} | >=5% {p[5]} | >=10% {p[10]} | >=15% {p[15]}')


def _roe_pct(roe):
    """PURE. Normalise a TradingView ROE value to PERCENT. TV may return either a percent
    (e.g. 12.5) or a fraction (0.125); a bank ROE is ~5-25%, so |v|<=1.5 is treated as a
    fraction and scaled x100. Guards the gate against silently dropping every bank if TV
    returns fractions. Returns None for None."""
    if roe is None:
        return None
    return roe * 100 if abs(roe) <= 1.5 else roe


def _fin_roe_diag(values):
    """PURE. Wave D1 step 2 instrumentation. Given TV ROE values for the financial bucket,
    summarise the distribution and coverage so the ROE gate threshold (and unit handling)
    can be confirmed from real data before ROE becomes the primary gate. Unit-normalised
    via _roe_pct. Changes NO gating this run. Unit-tested."""
    n = len(values)
    pct = [_roe_pct(v) for v in values if v is not None]
    if not pct:
        return (f'[diag] financials ROE: {n} financials, 0 with TV ROE data '
                f'— no ROE gate applied (all pass through); EPS<0 gate still active')
    s = sorted(pct)
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    p = {t: sum(1 for v in pct if v >= t) for t in (8, 10, 12, 15, 20)}
    return (f'[diag] financials ROE: {n} financials, {len(pct)} with data; '
            f'min {s[0]:.1f}% median {median:.1f}% max {s[-1]:.1f}%; '
            f'pass >=8% {p[8]} | >=10% {p[10]} | >=12% {p[12]} | >=15% {p[15]} | >=20% {p[20]}')


def fetch_us_universe_tv():
    """v1.21.0 Phase 1 — pre-filter the US universe on the free TradingView america scanner
    so Yahoo only screens names that can plausibly survive. Validated 2026-06-05: the fq
    field reproduces 96% of non-financial Yahoo survivors; financials cannot be screened on
    TV revenue growth so they pass straight through to the Yahoo screen unchanged; the named
    large-cap set is always included. HARD fallback to the full Yahoo universe if TV is
    unreachable or returns nothing -> production can never break."""
    thr = US_REV_GROWTH_MIN * 100

    def _bare(s):
        return s.split(':')[-1]

    rows = []
    try:
        start, page, cap = 0, 500, 6000
        while start < cap:
            payload = {
                "columns": _US_TV_COLS,
                "filter": [
                    {"left": "type", "operation": "equal", "right": "stock"},
                    {"left": "market_cap_basic", "operation": "egreater", "right": US_SMALL_CAP_MIN},
                ],
                "sort": {"sortBy": "market_cap_basic", "sortOrder": "asc"},
                "range": [start, start + page], "markets": ["america"],
            }
            r = requests.post("https://scanner.tradingview.com/america/scan",
                              json=payload, headers={'User-Agent': UA}, timeout=40)
            if r.status_code != 200:
                warn(f'TV america prefilter HTTP {r.status_code}; falling back to Yahoo universe')
                rows = []
                break
            batch = r.json().get('data', [])
            stop = False
            for d in batch:
                rec = dict(zip(_US_TV_COLS, d['d']))
                rec['ticker'] = _bare(d['s'])
                if (rec.get('market_cap_basic') or 0) > US_SMALL_CAP_MAX:
                    stop = True   # ascending sort -> past the band ceiling, done
                    break
                if not is_common_us_ticker(rec['ticker']):
                    continue      # drop TV-leaked preferred-share series (ABR/PE, GNL/PD, ...) — they 502 on Yahoo
                rows.append(rec)
            if stop or len(batch) < page:
                break
            start += page
    except Exception as e:
        warn(f'TV america prefilter failed ({e}); falling back to Yahoo universe')
        rows = []

    if not rows:
        warn('TV prefilter empty -> using full Yahoo universe (no change vs prior behaviour)')
        return fetch_us_universe(), {}   # L1: (tickers, fund_map) — empty map -> all names take the Yahoo fallback

    large = us_large_cap_set()
    cands = set(large)   # named large-caps always reach the screen (band bypass lives in _candidate_from_tv/screen_us_stock)
    band_map = {}        # L1: {ticker: TV rec} for band names that pass classify -> screen built from TV, no per-name Yahoo .info
    # v1.42.0: TV type=stock leaks baby-bond / preferred SERIES as bare base+letter symbols
    # (ADAM->ADAMH/L/M/N/Z, RILY->RILYL/P, NEWT->NEWTG/P, ATLC->ATLCP/Z, CCNE->CCNEP). Yahoo's
    # insider gate used to suppress them (no insider data -> 0%% -> dropped); with L1 sourcing
    # fundamentals from TV and the gate gone, they leak into the candidate/Explosive pool. Drop a
    # symbol whose value is another band ticker + one trailing letter -> keeps the common stock,
    # drops its series. Band-only (large-caps are a fixed common-ticker set), so no holding is at risk.
    _band_base = {r.get('ticker') for r in rows}
    dropped_pref = 0
    buckets = {'financial': 0, 'growth': 0, 'ttm': 0}
    fin_eps_pairs = []   # D1: financial bucket EPS-growth (in-band financials, pre-gate)
    fin_roe_vals  = []   # D1 step 2: financial bucket ROE (for the ROE-gate decision)
    fin_dropped_roe = 0  # D1 step 3: financials the ROE>=ROE_FIN_MIN primary gate drops
    fin_dropped_eps = 0  # financials the EPS>=0 secondary gate drops (ROE-surviving only)
    for rec in rows:
        _tk = rec.get('ticker') or ''
        if len(_tk) >= 5 and _tk[:-1] in _band_base:
            dropped_pref += 1
            continue   # preferred / baby-bond series (base ticker already in the universe)
        is_fin = ('Financ' in (rec.get('sector') or '')
                  and (rec.get('exchange') or '') in US_MAIN_EXCH
                  and US_SMALL_CAP_MIN <= (rec.get('market_cap_basic') or 0) <= US_SMALL_CAP_MAX)
        if is_fin:
            fq  = rec.get('earnings_per_share_diluted_yoy_growth_fq')
            ttm = rec.get('earnings_per_share_diluted_yoy_growth_ttm')
            fin_eps_pairs.append((fq, ttm))
            fin_roe_vals.append(rec.get('return_on_equity'))
            _roe = _roe_pct(rec.get('return_on_equity'))
            _eps = fq if fq is not None else ttm
            if _roe is not None and _roe < ROE_FIN_MIN:
                fin_dropped_roe += 1
            elif _eps is not None and _eps < 0:
                fin_dropped_eps += 1
        cls = classify_us_tv_row(rec, thr)
        if cls == 'skip':
            continue
        cands.add(rec['ticker'])
        band_map[rec['ticker']] = rec
        buckets[cls] += 1
    out = sorted(cands)
    log(f'  TV prefilter: {len(rows)} band names scanned -> Yahoo screens {len(out)} '
        f'(large-cap {len(large)} + financials {buckets["financial"]} + '
        f'growth {buckets["growth"]} + ttm-fallback {buckets["ttm"]}); '
        f'replaces a ~{len(rows) + len(large)}-name full-universe Yahoo screen'
        f'; dropped {dropped_pref} preferred/baby-bond series')
    log(f'  D1 bank gate: {len(fin_eps_pairs)} in-band financials -> dropped '
        f'{fin_dropped_roe} (ROE<{ROE_FIN_MIN:.0f}%) + {fin_dropped_eps} (EPS<0) '
        f'-> {buckets["financial"]} to Yahoo (revenue gate bypassed for financials)')
    log('  ' + _fin_eps_diag(fin_eps_pairs))
    log('  ' + _fin_roe_diag(fin_roe_vals))
    return out, band_map


def screen_us_stock(ticker, yf_module):
    """Screen one ticker via Yahoo info. Returns candidate dict or None."""
    try:
        t = yf_module.Ticker(ticker)
        info = t.info
        if not info or not isinstance(info, dict):
            return None
        market_cap = info.get('marketCap', 0) or 0
        if market_cap == 0:
            return None
        if ticker not in us_large_cap_set():
            if not (US_SMALL_CAP_MIN <= market_cap <= US_SMALL_CAP_MAX):
                return None  # small-cap path keeps the $300M-$2B band; large-cap set bypasses ceiling (Decision 5)
        sector = info.get('sector', 'Unknown') or 'Unknown'
        is_fin = 'Financ' in sector
        rev_growth = info.get('revenueGrowth')
        # D1 step 3: financials bypass the revenue-growth gate (revenue is meaningless for a
        # spread/credit business; they are gated on ROE>=ROE_FIN_MIN + EPS-YoY at the TV
        # prefilter). Non-financials still require revenueGrowth >= US_REV_GROWTH_MIN.
        if not is_fin:
            if rev_growth is None or rev_growth < US_REV_GROWTH_MIN:
                return None
        # Wave O L1: insider GATE dropped (TV exposes no insider field; the s3_insider EDGAR
        # Form-4 stream flags insider activity downstream). insider_pct kept for DISPLAY only.
        insider = info.get('heldPercentInsiders', 0) or 0
        yf_rev = round(float(rev_growth) * 100, 1) if rev_growth is not None else None
        _eg = info.get('earningsGrowth')
        yf_eps = round(float(_eg) * 100, 1) if _eg is not None else None
        return {
            'ticker':       ticker,
            'name':         info.get('shortName') or info.get('longName') or ticker,
            'sector':       info.get('sector', 'Unknown'),
            'industry':     info.get('industry', ''),
            'market_cap':   market_cap,
            'market_cap_m': round(market_cap / 1e6, 0),
            'price':        info.get('currentPrice') or info.get('regularMarketPrice'),
            'rev_growth':   yf_rev,
            'eps_growth':   yf_eps,
            'growth_source':'yahoo',
            'roe':          round(float(info.get('returnOnEquity', 0) or 0) * 100, 1),
            'debt_equity':  round(float(info.get('debtToEquity', 0) or 0) / 100, 2),
            'pe':           info.get('trailingPE'),
            'forward_pe':   info.get('forwardPE'),
            'insider_pct':  round(float(insider) * 100, 1),
            'ocf_ni':       None,
        }
    except Exception:
        return None


# ── Wave O L1 (instrumentation) ────────────────────────────────────────────────
# Isolated coverage/units probe for the planned TV-first US fundamentals + analyst
# migration. One america/scan POST; logs coverage% + a sample value per candidate
# column WITHOUT touching the production prefilter parse (no misalignment risk to the
# revenue/ROE band fields). Read the run log ONCE to confirm TV column names/units,
# then the L1 cutover + US analyst-scoring + L2/L3/L4 batching land against confirmed
# columns. Best-effort: never raises into the run.
_US_TV_PROBE_COLS = ['name',
    'price_earnings_ttm', 'price_book_ratio', 'price_sales_ratio', 'enterprise_value_ebitda_ttm',
    'gross_margin', 'operating_margin', 'net_margin', 'return_on_invested_capital',
    'debt_to_equity', 'current_ratio',
    'price_target_average', 'recommendation_mark', 'recommendation_buy', 'recommendation_total',
    'earnings_per_share_forecast_next_fq', 'earnings_per_share_fq']

def probe_us_tv_coverage(sample=800):
    """Additive, isolated. Logs TV column coverage + a units sample per candidate column.
    Misaligned rows are skipped (defensive); any failure is logged, never raised."""
    try:
        payload = {
            'columns': _US_TV_PROBE_COLS,
            'filter': [
                {'left': 'type', 'operation': 'equal', 'right': 'stock'},
                {'left': 'market_cap_basic', 'operation': 'egreater', 'right': US_SMALL_CAP_MIN},
            ],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
            'range': [0, sample], 'markets': ['america'],
        }
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=40)
        if r.status_code != 200:
            log(f'  [diag] Wave O L1 probe: HTTP {r.status_code} (non-blocking)'); return
        data = r.json().get('data', [])
        n = len(data)
        if not n:
            log('  [diag] Wave O L1 probe: 0 rows (non-blocking)'); return
        ncol = len(_US_TV_PROBE_COLS)
        cov = {c: 0 for c in _US_TV_PROBE_COLS}
        smp = {c: None for c in _US_TV_PROBE_COLS}
        aligned = 0
        for d in data:
            vals = d.get('d') or []
            if len(vals) != ncol:
                continue                       # defensive: skip any misaligned row
            aligned += 1
            for c, v in zip(_US_TV_PROBE_COLS, vals):
                if v is not None:
                    cov[c] += 1
                    if smp[c] is None:
                        smp[c] = v
        parts = []
        for c in _US_TV_PROBE_COLS:
            if c == 'name':
                continue
            pct = round(100 * cov[c] / aligned) if aligned else 0
            parts.append(f'{c}={pct}%({smp[c]})')
        log(f'  [diag] Wave O L1 TV-US coverage (n={aligned}/{n}): ' + ' '.join(parts))
    except Exception as e:
        log(f'  [diag] Wave O L1 probe failed ({e}) — non-blocking')


# Wave R (Option C — peer-relative IM3) — per-GICS-sector MEDIANS of trailing P/E, operating
# margin, net margin and ROE over a broad america sample. ONE isolated america/scan POST with
# its OWN columns + parse (mirrors probe_us_tv_coverage), so it can never corrupt the universe
# screen's column alignment. Written to sector_medians.json for im3_score.py to score those four
# metrics PEER-RELATIVE (absolute thresholds stay the fallback for any sector with no median, and
# for Yahoo/PSX names whose sector taxonomy doesn't match — so PSX scoring is provably unchanged).
# Margins/ROE are stored as DECIMALS (matching im3's units); a sector needs >=5 samples per metric.
# Best-effort: any failure carries last-good and never raises into the run.
_SECTOR_MED_COLS = ['sector', 'price_earnings_ttm', 'operating_margin', 'net_margin', 'return_on_equity', 'close', 'SMA200', 'Perf.W', 'Perf.1M', 'Perf.3M', 'price_target_average', 'earnings_per_share_forecast_next_fq', 'earnings_per_share_fq', 'dividends_yield']

DIV_YIELD_PROBE = False  # verdict read (v1.98.0): use 'dividends_yield', already %, null=non-payer: dump which TV dividend-yield column is accepted + its units, then lock + flip False

DATA_SOURCE_PROBE = False  # verdict read (v1.100.0): NDX/Dow=FRED NASDAQ100/DJIA, RUT=TVC:RUT, Arab Light=WB Dubai, FMP /stable/ free-tier OK: dump which feeds carry NDX/DJI/RUT, Arab Light/Dubai crude, and what FMP /stable/ serves — then lock + flip False

def probe_data_sources_v199():
    """ISOLATED, logging-only, runner-side. Three reachability/shape probes whose answers the sandbox
    cannot get (FRED/TV/FMP/World-Bank all blocked here). Each request is independently guarded and the
    whole call is wrapped in main -> can NEVER touch screening, scoring, IM3, the TCE tier or the frozen
    ledger. Read the three [v199 probe] blocks, then lock: (1) the index series/symbols that return a level,
    (2) the Arab Light/Dubai source that parses, (3) the FMP /stable/ endpoints the free key serves.
      PART A - US INDEX LEVELS (NDX/DJI/RUT live, the S&P already uses FRED 'SP500'):
        tests candidate FRED series IDs AND candidate TV index symbols (same symbols-POST that works for
        PSX:KSE100) so whichever returns a real level wins.
      PART B - ARAB LIGHT / DUBAI CRUDE (benchmark is Arab Light; today only WTI/Brent are fetched):
        tests the World Bank monthly commodity sheet (carries 'Crude oil, Dubai', the standard Arab Light
        proxy) + candidate TV symbols, logging reachability + content-type + size.
      PART C - FMP /stable/ (prereq for the Yahoo->FMP statements cutover; v3 endpoints are retired/403):
        logs whether FMP_API_KEY is set and what a few /stable/ endpoints return on the free tier
        (200 with data vs 401/402/403 premium-gated), with a short body snippet so the shape is readable."""
    if not DATA_SOURCE_PROBE:
        return
    H = {'User-Agent': UA, 'Accept': 'application/json'}

    # ---------- PART A: US index levels ----------
    log('  [v199 probe] A. US index levels (NDX / DJI / RUT):')
    # A1 — FRED candidate series (the S&P uses 'SP500'; test the analogues)
    if FRED_KEY:
        try:
            from fredapi import Fred
            _fr = Fred(api_key=FRED_KEY)
            for label, sids in (('Nasdaq-100', ['NASDAQ100', 'NASDAQCOM']),
                                ('Dow',        ['DJIA']),
                                ('Russell-2000', ['RU2000PR', 'RU2000', 'RUT']),
                                ('S&P (control)', ['SP500'])):
                for sid in sids:
                    try:
                        s = _fr.get_series(sid).dropna()
                        last = float(s.iloc[-1]) if len(s) else None
                        asof = str(s.index[-1].date()) if len(s) else '?'
                        log(f'      FRED {sid:12} ({label}) OK last={last} asof={asof}')
                    except Exception as e:
                        log(f'      FRED {sid:12} ({label}) FAIL {str(e)[:60]}')
        except Exception as e:
            log(f'      FRED client unavailable: {str(e)[:80]}')
    else:
        log('      FRED_API_KEY not set — skipping FRED index probe')
    # A2 — TradingView index symbols (the PSX:KSE100 symbols-POST pattern, on the US scanner)
    try:
        tickers = ['SP:SPX', 'NASDAQ:IXIC', 'NASDAQ:NDX', 'TVC:NDX', 'TVC:DJI', 'DJ:DJI',
                   'TVC:RUT', 'TVC:RUI', 'FOREXCOM:NSXUSD', 'CBOE:RUT']
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json={'symbols': {'tickers': tickers}, 'columns': ['close']},
                          headers={'User-Agent': UA}, timeout=20)
        if r.status_code == 200:
            rows = {d.get('s'): (d.get('d') or [None])[0] for d in r.json().get('data', [])}
            log(f'      TV america/scan index symbols -> {rows}')
        else:
            log(f'      TV america/scan HTTP {r.status_code}')
    except Exception as e:
        log(f'      TV index symbols miss: {str(e)[:80]}')

    # ---------- PART B: Arab Light / Dubai crude ----------
    log('  [v199 probe] B. Arab Light / Dubai crude source:')
    wb_urls = [
        ('worldbank-cmo-xlsx', 'https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Monthly.xlsx'),
        ('worldbank-cmo-alt',  'https://www.worldbank.org/content/dam/sites/commodities/doc/CMO-Historical-Data-Monthly.xlsx'),
    ]
    for label, url in wb_urls:
        try:
            r = requests.get(url, headers={'User-Agent': UA}, timeout=25)
            ct = r.headers.get('content-type', '?')
            magic = r.content[:4]
            hint = 'XLSX (PK zip)' if magic[:2] == b'PK' else ('HTML' if b'<html' in r.content[:200].lower() else '?')
            log(f'      {label:20} HTTP {r.status_code} ct={ct} size={len(r.content)} magic={magic!r} hint={hint}')
        except Exception as e:
            log(f'      {label:20} FAIL {str(e)[:70]}')
    # candidate TV symbols for Dubai/Oman/Arab crude (logged; trust nothing until a real level returns)
    try:
        tickers = ['TVC:UKOIL', 'TVC:USOIL', 'NYMEX:WS1!', 'TVC:DUBAI', 'EASYMARKETS:OILDUBAI', 'ICEEUR:DUB1!']
        r = requests.post('https://scanner.tradingview.com/symbol',
                          json={'symbols': {'tickers': tickers}, 'columns': ['close']},
                          headers={'User-Agent': UA}, timeout=20)
        log(f'      TV crude symbols HTTP {r.status_code} body[:200]={r.text[:200]!r}')
    except Exception as e:
        log(f'      TV crude symbols miss: {str(e)[:80]}')

    # ---------- PART C: FMP /stable/ ----------
    log('  [v199 probe] C. FMP /stable/ (Yahoo->FMP statements cutover prereq):')
    if not FMP_KEY:
        log('      FMP_API_KEY not set — the Yahoo->FMP cutover needs a free FMP key in repo secrets')
    else:
        fmp_eps = [
            ('quote',            'https://financialmodelingprep.com/stable/quote?symbol=AAPL'),
            ('income-statement', 'https://financialmodelingprep.com/stable/income-statement?symbol=AAPL&limit=2'),
            ('ratios-ttm',       'https://financialmodelingprep.com/stable/ratios-ttm?symbol=AAPL'),
            ('hist-eod-light',   'https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=AAPL'),
        ]
        for label, base in fmp_eps:
            try:
                sep = '&' if '?' in base else '?'
                r = requests.get(f'{base}{sep}apikey={FMP_KEY}', headers=H, timeout=20)
                log(f'      FMP /stable/{label:18} HTTP {r.status_code} body[:200]={r.text[:200]!r}')
            except Exception as e:
                log(f'      FMP /stable/{label:18} FAIL {str(e)[:70]}')


def probe_dividend_yield_columns():
    """ISOLATED, logging-only. Tests candidate TV dividend-yield column names ONE AT A TIME in their own
    throwaway america/scan + pakistan/scan POSTs (range[0,12]) so an unknown column can only 400 its OWN
    tiny request — never the production sector medians POST. Logs, per candidate: HTTP status, n rows,
    non-null count, and a sample value (so the UNITS are readable: 2.5 = already %, 0.025 = decimal).
    Read the [div-yield probe] block, lock the accepted column + units, wire it into both sector POSTs,
    then flip DIV_YIELD_PROBE False. Probe-before-build; cannot affect screening/scoring/the freeze."""
    if not DIV_YIELD_PROBE:
        return
    cands = ['dividends_yield', 'dividends_yield_current', 'dividend_yield_recent',
             'dividends_yield_fwd', 'dps_common_stock_prim_issue', 'dividend_payout_ratio_ttm']
    for mkt, url in (('US', 'https://scanner.tradingview.com/america/scan'),
                     ('PSX', 'https://scanner.tradingview.com/pakistan/scan')):
        log(f'  [div-yield probe] {mkt}:')
        for col in cands:
            try:
                body = {'columns': ['name', col], 'range': [0, 12],
                        'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
                        'markets': ['america' if mkt == 'US' else 'pakistan']}
                r = requests.post(url, json=body, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
                if r.status_code != 200:
                    log(f'      {col:32} HTTP {r.status_code} (rejected/invalid column)')
                    continue
                rows = (r.json() or {}).get('data', []) or []
                vals = [d['d'][1] for d in rows if d.get('d') and len(d['d']) > 1 and d['d'][1] is not None]
                samp = ', '.join(str(round(v, 4)) if isinstance(v, (int, float)) else str(v) for v in vals[:4])
                log(f'      {col:32} OK  n={len(rows)} nonnull={len(vals)} sample=[{samp}]')
            except Exception as e:
                log(f'      {col:32} probe error: {e}')


def fetch_sector_medians(sample=2000):
    import statistics, json as _json
    try:
        payload = {
            'columns': _SECTOR_MED_COLS,
            'filter': [
                {'left': 'type', 'operation': 'equal', 'right': 'stock'},
                {'left': 'market_cap_basic', 'operation': 'egreater', 'right': US_SMALL_CAP_MIN},
            ],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
            'range': [0, sample], 'markets': ['america'],
        }
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=40)
        if r.status_code != 200:
            log(f'  [sector medians] HTTP {r.status_code} — carrying last-good')
            return EXISTING.get('sector_medians', {}) or {}
        rows = r.json().get('data', [])
        ncol = len(_SECTOR_MED_COLS)
        acc = {}
        for d in rows:
            vals = d.get('d') or []
            if len(vals) != ncol:
                continue                          # defensive: skip misaligned rows
            sec, pe, opm, npm, roe, close, sma200, pw, p1m, p3m, tgt, fqn, fqc, dy = vals
            if not sec:
                continue
            a = acc.setdefault(sec, {'pe': [], 'op_margin': [], 'net_margin': [], 'roe': [], 'b_above': 0, 'b_tot': 0,
                                     'perf_w': [], 'perf_1m': [], 'perf_3m': [], 'tgt': [], 'feqg': [],
                                     'dy_sum': 0.0, 'dy_n': 0, 'dy_payers': 0})
            a['dy_n'] += 1
            if isinstance(dy, (int, float)) and 0 <= dy < 100:
                a['dy_sum'] += float(dy)
                if dy > 0:
                    a['dy_payers'] += 1
            if isinstance(pe,  (int, float)) and 0 < pe < 200:       a['pe'].append(float(pe))
            if isinstance(opm, (int, float)) and -100 < opm < 100:   a['op_margin'].append(float(opm) / 100.0)
            if isinstance(npm, (int, float)) and -100 < npm < 100:   a['net_margin'].append(float(npm) / 100.0)
            if isinstance(roe, (int, float)) and -200 < roe < 300:
                _rp = _roe_pct(roe)
                if _rp is not None: a['roe'].append(_rp / 100.0)
            # Wave M-A step 2b: per-sector 200-DMA breadth (count names at/above their 200-DMA)
            if isinstance(close, (int, float)) and isinstance(sma200, (int, float)) and close > 0 and sma200 > 0:
                a['b_tot'] += 1
                if close >= sma200:
                    a['b_above'] += 1
            # Wave S step 2 (Phase 2): per-sector PRICE-MOMENTUM (avg % move over 1wk/1mo/3mo)
            if isinstance(pw,  (int, float)) and -95 < pw  < 500:   a['perf_w'].append(float(pw))
            if isinstance(p1m, (int, float)) and -95 < p1m < 800:   a['perf_1m'].append(float(p1m))
            if isinstance(p3m, (int, float)) and -95 < p3m < 1500:  a['perf_3m'].append(float(p3m))
            # Wave S Phase 2c FORWARD: analyst target upside (implied ~12m price return) + next-quarter EPS growth
            if isinstance(tgt, (int, float)) and tgt > 0 and isinstance(close, (int, float)) and close > 0:
                _tu = (tgt / close - 1.0) * 100.0
                if -90 < _tu < 300:   a['tgt'].append(_tu)
            if isinstance(fqn, (int, float)) and isinstance(fqc, (int, float)) and fqc > 0:
                _g = (fqn / fqc - 1.0) * 100.0
                if -100 < _g < 300:   a['feqg'].append(_g)
        out = {}
        for sec, a in acc.items():
            rec = {}
            for k in ('pe', 'op_margin', 'net_margin', 'roe'):   # list metrics only (b_above/b_tot are ints)
                lst = a[k]
                if len(lst) >= 5:                 # need a meaningful peer set, else leave it out -> absolute fallback
                    rec[k] = round(statistics.median(lst), 4)
            if a['b_tot'] >= 5:                   # Wave M-A step 2b: % of the sector at/above its 200-DMA
                rec['breadth_200dma'] = round(100.0 * a['b_above'] / a['b_tot'], 1)
                rec['breadth_n'] = a['b_tot']
            for k in ('perf_w', 'perf_1m', 'perf_3m'):   # Wave S Phase 2: sector-average price move (mean of constituents)
                lst = a[k]
                if len(lst) >= 5:
                    rec[k] = round(statistics.mean(lst), 2)
            if len(a['tgt'])  >= 5:  rec['tgt_upside']  = round(statistics.mean(a['tgt']),  2)   # implied ~12m analyst price return
            if len(a['feqg']) >= 5:  rec['fwd_eps_q_g'] = round(statistics.mean(a['feqg']), 2)   # next-quarter EPS growth est
            if a['dy_n'] >= 5 and a['dy_payers'] >= 1:  rec['div_yield'] = round(a['dy_sum'] / a['dy_n'], 2)  # sector avg dividend yield % (non-payer=0)
            if any(k in rec for k in ('pe', 'op_margin', 'net_margin', 'roe', 'breadth_200dma', 'perf_w', 'perf_1m', 'perf_3m', 'tgt_upside', 'fwd_eps_q_g', 'div_yield')):
                rec['n'] = max(len(a['pe']), len(a['op_margin']), len(a['net_margin']), len(a['roe']))
                out[sec] = rec
        if out:
            with open('sector_medians.json', 'w') as f:
                _json.dump(out, f, indent=2)
            _ex = list(out.items())[:3]
            _nb = sum(1 for v in out.values() if 'breadth_200dma' in v)
            log(f'  [sector medians] {len(out)} sectors -> sector_medians.json ({_nb} with 200-DMA breadth; e.g. ' +
                ', '.join(f"{s} PE~{v.get('pe')}/ROE~{v.get('roe')}/1M~{v.get('perf_1m')}%/tgt~{v.get('tgt_upside')}%" for s, v in _ex) + ')')
            return out
        log('  [sector medians] 0 sectors parsed — carrying last-good')
        return EXISTING.get('sector_medians', {}) or {}
    except Exception as e:
        log(f'  [sector medians] failed ({e}) — carrying last-good')
        return EXISTING.get('sector_medians', {}) or {}


# Wave O L1 (insider probe) — isolated, resolves the cutover fork. The US screen drops candidates with
# heldPercentInsiders < 5% (Yahoo .info). The L1 fundamentals cutover (retiring the ~666 per-name Yahoo
# .info calls) can only KEEP that gate if TV exposes an insider-ownership field. This probes candidate
# TV column names — first all-in-one (cheap when valid), falling back to per-name requests if TV rejects
# the batch (an unknown column 400s the whole POST). Runs in its OWN request(s) so it can never corrupt
# the main coverage probe's row alignment. Outcome: if TV accepts a usable field -> keep the gate post
# cutover; if NONE -> the cutover must either drop the insider gate (then measure the survivor delta) or
# retain a single thin per-name insider call. Logging-only; never raises into the run.
_US_INSIDER_CANDIDATES = ['insider_ownership', 'held_by_insiders', 'shares_insiders',
                          'institutional_ownership', 'held_by_institutions']

def probe_us_insider_coverage(sample=400):
    try:
        URL = 'https://scanner.tradingview.com/america/scan'
        FILT = [{'left': 'type', 'operation': 'equal', 'right': 'stock'},
                {'left': 'market_cap_basic', 'operation': 'egreater', 'right': US_SMALL_CAP_MIN}]
        def _post(cols):
            try:
                return requests.post(URL, json={'columns': cols, 'filter': FILT,
                                                 'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
                                                 'range': [0, sample], 'markets': ['america']},
                                     headers={'User-Agent': UA}, timeout=30)
            except Exception:
                return None
        accepted = {}                                   # col -> (coverage%, sample value)
        cols = ['name'] + _US_INSIDER_CANDIDATES
        r = _post(cols)                                 # 1) all-in-one
        if r is not None and r.status_code == 200:
            rows = r.json().get('data', [])
            nc = len(cols)
            aligned = [d['d'] for d in rows if len(d.get('d') or []) == nc]
            for i, c in enumerate(cols):
                if c == 'name':
                    continue
                have = sum(1 for v in aligned if v[i] is not None)
                sm = next((v[i] for v in aligned if v[i] is not None), None)
                accepted[c] = (round(100 * have / len(aligned)) if aligned else 0, sm)
        else:                                           # 2) batch rejected -> identify valid names one by one
            for c in _US_INSIDER_CANDIDATES:
                rr = _post(['name', c])
                if rr is None or rr.status_code != 200:
                    continue
                rows = rr.json().get('data', [])
                al = [d['d'] for d in rows if len(d.get('d') or []) == 2]
                have = sum(1 for v in al if v[1] is not None)
                sm = next((v[1] for v in al if v[1] is not None), None)
                accepted[c] = (round(100 * have / len(al)) if al else 0, sm)
        usable = {c: v for c, v in accepted.items() if v[0] > 0}
        if usable:
            log('  [diag] Wave O L1 insider probe — TV exposes: '
                + ' '.join(f'{c}={p}%({s})' for c, (p, s) in usable.items())
                + ' -> insider 5% gate CAN survive the cutover on TV')
        else:
            log('  [diag] Wave O L1 insider probe — TV exposes NO usable insider/ownership field (tried '
                + ','.join(_US_INSIDER_CANDIDATES) + '); the 5% insider gate stays Yahoo-only -> the L1 '
                + 'cutover must drop the gate (then measure survivor delta) or keep one thin per-name insider call')
    except Exception as e:
        log(f'  [diag] Wave O L1 insider probe failed ({e}) — non-blocking')


# Wave O L1 (US analyst overlay) — the US counterpart to D2. One america/scan POST over the
# US band; returns {bare_ticker: analyst_row} for the TCE-pool tickers, shaped exactly for
# tce_psx_analyst.derive_psx_analyst_streams (same FactSet columns). Best-effort: any failure
# returns {} -> no analyst_row attached -> US analyst streams don't fire -> US scoring reverts
# to its pre-overlay behaviour. Cannot break production.
_US_ANALYST_COLS = ['name', 'close', 'price_target_average', 'recommendation_mark',
                    'recommendation_buy', 'recommendation_total',
                    'earnings_per_share_forecast_next_fq', 'earnings_per_share_forecast_fq',
                    'earnings_per_share_fq', 'sector']   # v1.89.0: 'sector' APPENDED (last) so the zip stays aligned and derive_psx_analyst_streams (reads by key) is byte-identical -> s11/s12/s9 unchanged (freeze-safe); it lets the ETF-consensus large-caps inherit the TV sector the scan already returns.

def fetch_us_analyst_block(pool_tickers):
    want = set(t for t in (pool_tickers or []) if t)
    if not want:
        return {}
    out = {}
    try:
        payload = {
            'columns': _US_ANALYST_COLS,
            'filter': [
                {'left': 'type', 'operation': 'equal', 'right': 'stock'},
                {'left': 'market_cap_basic', 'operation': 'egreater', 'right': US_SMALL_CAP_MIN},
            ],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
            'range': [0, 6000], 'markets': ['america'],
        }
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=40)
        if r.status_code != 200:
            warn(f'US analyst overlay: TV HTTP {r.status_code} — US analyst streams will not fire this run')
            return {}
        ncol = len(_US_ANALYST_COLS)
        for d in r.json().get('data', []):
            vals = d.get('d') or []
            if len(vals) != ncol:
                continue                       # defensive: skip any misaligned row
            tk = (d.get('s') or '').split(':')[-1]
            if tk in want and tk not in out:
                out[tk] = dict(zip(_US_ANALYST_COLS, vals))
                if len(out) == len(want):
                    break
        log(f'  US analyst overlay: matched {len(out)}/{len(want)} TCE-pool tickers (TV FactSet)')
    except Exception as e:
        warn(f'US analyst overlay failed ({e}) — US analyst streams will not fire this run')
        return {}
    return out


def fetch_us_large_fundamentals(tickers):
    """Wave O L1: TV fundamentals for the named large-caps, which sit ABOVE the prefilter band
    (the band POST sorts ascending and stops at the ceiling, so large-caps are never in band_map).
    One america/scan POST (mcap-desc, same pattern as fetch_us_analyst_block), columns = _US_TV_COLS
    so the rec shape is IDENTICAL to a band rec. Best-effort: any failure / a missing name -> not in
    the map -> that name takes the per-name Yahoo fallback in screen_us_universe. Cannot break the run."""
    want = set(t for t in (tickers or []) if t)
    if not want:
        return {}
    out = {}
    try:
        payload = {
            'columns': _US_TV_COLS,
            'filter': [
                {'left': 'type', 'operation': 'equal', 'right': 'stock'},
                {'left': 'market_cap_basic', 'operation': 'egreater', 'right': US_SMALL_CAP_MIN},
            ],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
            'range': [0, 6000], 'markets': ['america'],
        }
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json=payload, headers={'User-Agent': UA}, timeout=40)
        if r.status_code != 200:
            warn(f'L1 large-cap fundamentals: TV HTTP {r.status_code} — large-caps take the Yahoo fallback')
            return {}
        ncol = len(_US_TV_COLS)
        for d in r.json().get('data', []):
            vals = d.get('d') or []
            if len(vals) != ncol:
                continue                         # defensive: skip a misaligned row
            tk = (d.get('s') or '').split(':')[-1]
            if tk in want and tk not in out:
                rec = dict(zip(_US_TV_COLS, vals))
                rec['ticker'] = tk
                out[tk] = rec
                if len(out) == len(want):
                    break
        log(f'  L1 large-cap fundamentals: matched {len(out)}/{len(want)} named large-caps (TV)')
    except Exception as e:
        warn(f'L1 large-cap fundamentals failed ({e}) — large-caps take the Yahoo fallback')
        return {}
    return out


def _ma_reads(price, sma50, sma200):
    """Wave M-A: per-name moving-average reads from TradingView SMA50/SMA200 (same scan POST — no
    per-name price-history download). Returns None when price or SMA200 is missing/invalid.
    Provides: price-vs-200-DMA (the primary institutional trend filter), golden/death cross
    (50-DMA vs 200-DMA), and extension (% above/below the 200-DMA, a mean-reversion flag).
    DEFERRED to later M-A increments: 200-DMA SLOPE needs run-over-run history (the Wave T rolling
    store), and SECTOR BREADTH (% of a sector above its 200-DMA) needs a universe aggregation. Pure."""
    try:
        price = float(price) if price is not None else None
        s50 = float(sma50) if sma50 is not None else None
        s200 = float(sma200) if sma200 is not None else None
    except (TypeError, ValueError):
        return None
    if price is None or price <= 0 or s200 is None or s200 <= 0:
        return None
    return {
        'sma50':        round(s50, 2) if (s50 is not None and s50 > 0) else None,
        'sma200':       round(s200, 2),
        'above_200dma': bool(price >= s200),
        'ext_200_pct':  round((price - s200) / s200 * 100, 1),
        'cross':        ('golden' if s50 >= s200 else 'death') if (s50 is not None and s50 > 0) else None,
    }


def _candidate_from_tv(ticker, rec, large_set):
    """Wave O L1 — PURE. Build a US screen candidate from a TradingView fundamentals rec, the
    TV-sourced replacement for the per-name Yahoo screen_us_stock(). Returns:
      dict   -> passed the screen (built from TV; growth_source='tv')
      'DROP' -> failed a screen GATE (TV-decided; do NOT fall back to Yahoo, it would drop it too)
      None   -> critical data missing (market_cap/price) -> caller falls back to Yahoo per-name
    Gates mirror screen_us_stock EXACTLY, minus the insider gate (dropped in L1):
      band ($300M-$2bn) unless ticker is a named large-cap; non-financials need rev-growth >=15%.
    UNITS (validated vs the live probe sample): TV rev/eps YoY-growth + ROIC/margins are ALREADY
    percent; return_on_equity normalised via _roe_pct; debt_to_equity is a DECIMAL ratio (0.0655),
    matching screen_us_stock's Yahoo debtToEquity/100 output; price=close; pe=price_earnings_ttm."""
    if not rec:
        return None
    market_cap = rec.get('market_cap_basic') or 0
    if not market_cap:
        return None                              # no market cap -> let Yahoo try
    price = rec.get('close')
    if price is None:
        return None                              # no price -> let Yahoo try (currentPrice)
    if ticker not in large_set:
        if not (US_SMALL_CAP_MIN <= market_cap <= US_SMALL_CAP_MAX):
            return 'DROP'                        # out of band, not a named large-cap
    sector = rec.get('sector') or 'Unknown'
    is_fin = 'Financ' in sector
    rg_fq  = rec.get('total_revenue_yoy_growth_fq')
    rg_ttm = rec.get('total_revenue_yoy_growth_ttm')
    rev_growth = rg_fq if rg_fq is not None else rg_ttm
    if not is_fin:
        # non-financials require rev-growth >= threshold (financials bypass it, gated on ROE/EPS at classify)
        if rev_growth is None or rev_growth < US_REV_GROWTH_MIN * 100:
            return 'DROP'
    eg_fq  = rec.get('earnings_per_share_diluted_yoy_growth_fq')
    eg_ttm = rec.get('earnings_per_share_diluted_yoy_growth_ttm')
    eps_growth = eg_fq if eg_fq is not None else eg_ttm
    de = rec.get('debt_to_equity')
    return {
        'ticker':        ticker,
        'name':          rec.get('name') or ticker,
        'sector':        sector,
        'industry':      '',                     # TV has no clean industry field
        'market_cap':    market_cap,
        'market_cap_m':  round(market_cap / 1e6, 0),
        'price':         price,
        'rev_growth':    round(float(rev_growth), 1) if rev_growth is not None else None,
        'eps_growth':    round(float(eps_growth), 1) if eps_growth is not None else None,
        'growth_source': 'tv',
        'roe':           round(_roe_pct(rec.get('return_on_equity')), 1) if rec.get('return_on_equity') is not None else None,
        'debt_equity':   round(float(de), 2) if de is not None else None,
        'pe':            rec.get('price_earnings_ttm'),
        'forward_pe':    None,                   # TV lacks a clean forward PE here
        'insider_pct':   None,                   # gate dropped; TV has no insider field
        'perf_6m':       rec.get('Perf.6M'),     # Wave A / V-G-M: price momentum (6-month %)
        'perf_3m':       rec.get('Perf.3M'),     # Wave A / V-G-M: price momentum (3-month %)
        'ma':            _ma_reads(price, rec.get('SMA50'), rec.get('SMA200')),  # Wave M-A: MA trend reads
        'ocf_ni':        None,
    }


def screen_us_universe():
    log('=== US screening ===')
    probe_us_tv_coverage()   # Wave O L1 instrumentation (isolated; logs TV column coverage/units)
    probe_us_insider_coverage()   # Wave O L1 (isolated): does TV expose an insider field? -> cutover fork
    try:
        import yfinance as yf
    except ImportError:
        warn('yfinance not available for US screen')
        return {'funnel': EXISTING.get('us_funnel', []),
                'candidates': EXISTING.get('us_candidates', []),
                'all_survivors': EXISTING.get('us_candidates', [])}

    tickers, band_map = fetch_us_universe_tv()
    total = len(tickers)
    candidates = []

    # Wave O L1: build the screen from TradingView fundamentals (band recs from the prefilter +
    # a large-cap block) instead of ~660 per-name Yahoo .info calls. _candidate_from_tv mirrors
    # screen_us_stock minus the (dropped) insider gate. A name whose TV rec is missing critical
    # data (no market_cap/price) falls back to a per-name Yahoo screen so coverage can't regress;
    # a TV-decided gate failure ('DROP') is NOT re-tried on Yahoo (it would drop too). HARD
    # fallback: if the prefilter handed back the full Yahoo universe (band_map empty), every name
    # takes the Yahoo path = exactly the pre-L1 behaviour (minus the insider gate).
    large = us_large_cap_set()
    large_map = fetch_us_large_fundamentals([t for t in tickers if t in large])
    fund_map = dict(band_map); fund_map.update(large_map)
    log(f'  Building screen from TV fundamentals ({len(fund_map)} recs) + Yahoo fallback for gaps...')
    start = time.time()

    tv_sourced = 0
    yf_fallback_names = []
    for tk in tickers:
        rec = fund_map.get(tk)
        res = _candidate_from_tv(tk, rec, large) if rec else None
        if isinstance(res, dict):
            candidates.append(res); tv_sourced += 1
        elif res == 'DROP':
            continue                               # TV-decided gate fail — no wasted Yahoo call
        else:
            yf_fallback_names.append(tk)           # missing TV data -> Yahoo per-name screen

    # Per-name Yahoo fallback ONLY for the names TV couldn't supply (parallelized, as the old screen was).
    yf_fallback = 0
    if yf_fallback_names:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import random as _rand
        def _scan_one(tk):
            if US_SCAN_WORKERS > 1:
                time.sleep(_rand.uniform(0.2, 0.5))   # throttle only when parallel
            try:
                return screen_us_stock(tk, yf)
            except Exception:
                return None
        ex = ThreadPoolExecutor(max_workers=US_SCAN_WORKERS)
        try:
            futures = [ex.submit(_scan_one, tk) for tk in yf_fallback_names]
            for fut in as_completed(futures):
                result = fut.result()
                if result is not None:
                    candidates.append(result); yf_fallback += 1
                if time.time() - start > 2400:
                    warn('US scan TIME CAP hit in Yahoo fallback, stopping early')
                    break
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

    elapsed = time.time() - start
    log(f'  US scan (L1 TV-first): {elapsed:.0f}s, {len(candidates)} candidates — '
        f'{tv_sourced} TV-sourced + {yf_fallback} Yahoo-fallback (of {len(yf_fallback_names)} gaps); '
        f'insider gate DROPPED (s3_insider EDGAR Form-4 stream unaffected)')

    survived = len(candidates)
    # Flag micro-base revenue-growth artifacts (near-zero prior-year revenue -> absurd %),
    # then rank with those artifacts demoted to the bottom so they can't seize a HIGH-CONVICTION
    # slot (UROY at 416,400% was doing exactly that). They still pass the screen and appear,
    # just not mis-ranked at the top. Raw rev_growth is preserved for display.
    for c in candidates:
        rg = c.get('rev_growth')
        c['rev_growth_artifact'] = (rg is not None and rg > US_REV_GROWTH_SANE_MAX)

    def _rank_key(c):
        rg = c.get('rev_growth', 0) or 0
        return -1e9 if c.get('rev_growth_artifact') else rg   # artifacts sort dead last
    candidates.sort(key=_rank_key, reverse=True)

    for i, c in enumerate(candidates):
        if i < 3:   c['status'] = 'HIGH-CONVICTION'
        elif i < 8: c['status'] = 'STRONG'
        else:       c['status'] = 'WATCH'

    # ---------------------------------------------------------------
    # FMP enrichment — on survivors ONLY (not 1259 raw tickers).
    # This is the v1.7.1 fix: calling fmp_growth() inside screen_us_stock
    # meant ~1259 FMP API calls per run, exhausting rate limits silently.
    # Here we call it on <=200 survivors after screening is complete.
    # ---------------------------------------------------------------
    # EPS enrichment — for survivors where the screen has no eps_growth, fetch the actual annual
    # income statement and compute diluted-EPS (fallback basic) YoY growth: (curr-prev)/|prev|*100.
    # v1.101.0: FMP /stable/income-statement FIRST (fast, no Yahoo shared-crumb poisoning; free tier
    # probe-confirmed), then the IDENTICAL Yahoo income_stmt block as FALLBACK for whatever FMP can't
    # fill, so coverage can never regress. Same metric/formula/period basis (two most-recent fiscal
    # years) as before; growth_source records provenance (fmp_stmt | yf_stmt). FREEZE-SAFE: feeds the
    # Explosive pool only (separate from the Sept-frozen TCE engine; the TCE-15 ranks by revenue
    # growth) so the frozen prediction pool is unchanged.
    eps_hits = 0; fmp_hits = 0; yf_hits = 0
    eps_missing = [c for c in candidates[:US_EXPLOSIVE_POOL] if c.get('eps_growth') is None]
    if eps_missing:
        log(f'  Fetching income_stmt EPS for {len(eps_missing)} survivors missing earningsGrowth...')

        def _fmp_eps_pick(row):
            # tolerant to FMP field naming (epsDiluted / epsdiluted / eps); prefer diluted
            for k in ('epsDiluted', 'epsdiluted', 'epsDilutedTTM', 'eps'):
                v = row.get(k)
                if isinstance(v, (int, float)) and v == v:
                    return float(v)
            return None

        # --- FMP /stable/income-statement first (annual, most-recent-first) ---
        still_missing = []
        if FMP_KEY and EPS_ENRICH_TRY_FMP:   # v1.112.0 (F3): FMP /stable/ is premium-gated for these
                                             # small-caps (HTTP 402 every run since v1.101.1) -> FMP-first
                                             # was wasted latency. Default OFF = Yahoo-first gap-fill.
            _fmp_diag_done = False
            _fmp_miss_diag = 0   # v1.101.1: log the first few FMP misses (status/body/exc) so a
                                 # 0-hit run reveals WHY (paywall 402/403 vs empty list vs coverage)
            for c in eps_missing:
                got = False
                try:
                    url = f'https://financialmodelingprep.com/stable/income-statement?symbol={c["ticker"]}&limit=2&apikey={FMP_KEY}'
                    r = _retry_get(url, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
                    if r.status_code == 200:
                        rows = r.json()
                        if isinstance(rows, list) and len(rows) >= 2:
                            if not _fmp_diag_done:
                                log(f'    [FMP EPS diag] {c["ticker"]} fields: {sorted(rows[0].keys())[:26]}')
                                _fmp_diag_done = True
                            curr = _fmp_eps_pick(rows[0]); prev = _fmp_eps_pick(rows[1])
                            if curr is not None and prev is not None and prev != 0:
                                c['eps_growth'] = round((curr - prev) / abs(prev) * 100, 1)
                                c['growth_source'] = 'fmp_stmt'
                                fmp_hits += 1; eps_hits += 1; got = True
                            elif _fmp_miss_diag < 3:
                                log(f'    [FMP EPS miss] {c["ticker"]} 200 but eps unusable curr={curr} prev={prev} fields={sorted(rows[0].keys())[:18]}')
                                _fmp_miss_diag += 1
                        elif _fmp_miss_diag < 3:
                            _shape = f'list[{len(rows)}]' if isinstance(rows, list) else type(rows).__name__
                            log(f'    [FMP EPS miss] {c["ticker"]} 200 but rows={_shape} body[:150]={r.text[:150]!r}')
                            _fmp_miss_diag += 1
                    elif _fmp_miss_diag < 3:
                        log(f'    [FMP EPS miss] {c["ticker"]} HTTP {r.status_code} body[:150]={r.text[:150]!r}')
                        _fmp_miss_diag += 1
                except Exception as _e:
                    if _fmp_miss_diag < 3:
                        log(f'    [FMP EPS miss] {c["ticker"]} exc {str(_e)[:120]}')
                        _fmp_miss_diag += 1
                if not got:
                    still_missing.append(c)
                time.sleep(0.2)   # light pacing on the FMP free tier
        else:
            still_missing = list(eps_missing)
            log('    [FMP EPS] FMP gap-fill disabled (premium-gated for small-caps) — Yahoo income_stmt only'
                if FMP_KEY else '    [FMP EPS] FMP_API_KEY not set — using Yahoo income_stmt only')

        # --- Yahoo income_stmt FALLBACK (unchanged logic) for whatever FMP could not fill ---
        if still_missing:
            # The parallel screen can poison Yahoo's shared crumb, making every income_stmt call
            # fail. Recover: cooldown to let the throttle decay, then a fresh session + one retry.
            if US_SCAN_WORKERS > 1:
                time.sleep(20)
            try:
                import requests as _rq
                _sess = _rq.Session(); _sess.headers.update({'User-Agent': UA})
            except Exception:
                _sess = None
            for c in still_missing:
                for _att in range(2):
                    try:
                        tk = yf.Ticker(c['ticker'], session=_sess) if _sess is not None else yf.Ticker(c['ticker'])
                        stmt = tk.income_stmt
                        if stmt is not None and not stmt.empty and stmt.shape[1] >= 2:
                            for label in ['Diluted EPS', 'Basic EPS']:
                                if label in stmt.index:
                                    row = stmt.loc[label].dropna()
                                    if len(row) >= 2:
                                        curr, prev = float(row.iloc[0]), float(row.iloc[1])
                                        if prev != 0:
                                            c['eps_growth'] = round((curr - prev) / abs(prev) * 100, 1)
                                            c['growth_source'] = 'yf_stmt'
                                            yf_hits += 1; eps_hits += 1
                                    break
                            break   # got a statement (with or without EPS row) — don't retry
                    except Exception:
                        time.sleep(3)   # backoff, then one retry
                time.sleep(YF_DELAY)
        log(f'  EPS enriched {eps_hits}/{len(eps_missing)} previously-None survivors (FMP {fmp_hits}, Yahoo {yf_hits})')
    else:
        log('  All survivors already have EPS growth from Yahoo info')

    funnel = [
        ['NYSE + NASDAQ + AMEX Listed Equities', 5800,
         'Total US-listed common stocks'],
        ['Active US universe (NASDAQ-sourced)', total + 4500,
         'After ETFs/funds removed'],
        ['Small-cap zone ($300M-$2bn) PRE-FILTERED', total,
         'TradingView market-cap pre-filter'],
        ['+ Revenue Growth >15% YoY', survived,
         'TV rev-growth (FactSet); financials gated on ROE>=8%'],
        [f'+ Top {US_CANDIDATE_POOL} to TCE', min(US_CANDIDATE_POOL, survived),
         f'Live scan: {dt.date.today()}'],
    ]

    return {'funnel': funnel,
            'candidates': candidates[:US_CANDIDATE_POOL],
            'all_survivors': candidates[:US_EXPLOSIVE_POOL]}


# =============================================================
# 4. PSX
# =============================================================
def fetch_psx_universe():
    log('Fetching PSX universe...')
    test_url = 'https://dps.psx.com.pk/timeseries/eod/MUGHAL'
    try:
        r = requests.get(test_url, headers={
            'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
        log(f'  {"✓ PSX endpoint reachable" if r.status_code==200 else f"· PSX endpoint returned {r.status_code}"}')
    except Exception as e:
        log(f'  · PSX endpoint test: {e}')

    # F5: real candidate universe from the TradingView Pakistan scanner (the one reliable free PSX
    # path; same source the Apps Script bot uses). Falls back to the curated list on any failure so
    # PSX TCE never goes empty.
    try:
        live = fetch_psx_universe_live()
        if len(live) >= 8:
            log(f'  ✓ PSX universe: {len(live)} candidates from TradingView Pakistan scanner')
            return live
        log(f'  · TV scan returned {len(live)} (<8) — using fallback watchlist')
    except Exception as e:
        log(f'  · TV scan failed ({e}) — using fallback watchlist')
    return _PSX_FALLBACK


# Curated fallback only (used if the live scan fails). (ticker, name, sector, rev_growth, eps_growth)
_PSX_FALLBACK = [
    ('MUGHAL', 'Mughal Iron & Steel',         'Steel',     18.2,  32.5),
    ('ECOP',   'EcoPack Limited',             'Packaging', 22.1,  28.3),
    ('PIBTL',  'Pakistan Intl Bulk Terminal', 'Transport', 15.8,  12.1),
    ('GHGL',   'Ghani Glass',                 'Glass',     19.4,  22.7),
    ('PABC',   'Pak Alum Beverage Cans',      'Packaging', 24.6,  31.2),
    ('ACPL',   'Attock Cement',               'Cement',    11.2,   8.4),
    ('SAZEW',  'Sazgar Engineering',          'Auto',      35.8,  48.2),
    ('NCPL',   'Nishat Chunian Power',        'Utilities',  9.1,  14.3),
    ('SYM',    'Symmetry Group',              'IT',        42.3,  55.1),
    ('IML',    'Ismail Industries',           'Food',      16.7,  21.4),
]

# --- F5 live universe via TradingView Pakistan scanner (pure parse/derive + thin network wrapper) ---
PSX_SCAN_COLS = ['name', 'close', 'volume', 'market_cap_basic', 'Perf.3M', 'sector',
                 'total_revenue_yoy_growth_ttm', 'earnings_per_share_diluted_yoy_growth_ttm',
                 # D2 analyst-conviction columns (TV FactSet): target/recommendation/forward-EPS
                 'price_target_average', 'recommendation_mark', 'recommendation_buy',
                 'recommendation_total', 'earnings_per_share_forecast_next_fq',
                 'earnings_per_share_forecast_fq', 'earnings_per_share_fq',
                 'SMA50', 'SMA200']   # Wave M-A: price moving averages (trend lever, same POST)
PSX_MCAP_MIN  = 3e9     # exclude micro-caps (PKR)
PSX_MCAP_MAX  = 60e9    # exclude KSE-30 mega-caps; keep the small/mid "sweet spot"
PSX_TOP_N     = 25
PSX_MEGACAPS  = ['OGDC', 'PPL', 'MCB', 'FFC', 'HUBC']   # KSE-30 mega-caps above the scan band — force-included for market coverage (merit, not a personal book)

# F5 (v1.52): configurable broker watchlist — Topline/AKD/AHL conviction names that should always be
# screened even if TV's mcap-desc top-500 misses them. Maintain as a flat ticker list in
# psx_watchlist.json at the repo root (e.g. ["SYS","SEARL","MARI"]); accepts a bare list or
# {"psx_watchlist":[...]}. Force-included exactly like PSX_MEGACAPS: any listed name present in the
# pakistan/scan rows is pulled in with its close + FactSet analyst block and scored. File absent = no-op.
def _load_psx_watchlist():
    try:
        with open('psx_watchlist.json') as _wf:
            _w = json.load(_wf)
        if isinstance(_w, dict):
            _w = _w.get('psx_watchlist') or _w.get('tickers') or []
        return [str(t).strip().upper() for t in (_w or []) if str(t).strip()]
    except FileNotFoundError:
        return []
    except Exception:
        return []
PSX_WATCHLIST = _load_psx_watchlist()


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_tv_scan(payload, columns):
    """TradingView scanner JSON -> list of row dicts keyed by column. Symbol 'PSX:OGDC' -> 'OGDC'.
    Maps defensively: if the response has fewer values than requested columns (e.g. a column TV
    couldn't compute), the missing ones become None rather than dropping the row. Pure + unit-tested."""
    rows = []
    for item in ((payload or {}).get('data') or []):
        sym = item.get('s', '') if isinstance(item, dict) else ''
        ticker = sym.split(':')[-1] if ':' in sym else sym
        d = item.get('d') or [] if isinstance(item, dict) else []
        if not ticker or len(d) < 4:        # need at least the core price/volume/mcap fields
            continue
        rec = {'ticker': ticker}
        for i, c in enumerate(columns):
            rec[c] = d[i] if i < len(d) else None
        rows.append(rec)
    return rows


def derive_psx_candidates(rows, mcap_min=PSX_MCAP_MIN, mcap_max=PSX_MCAP_MAX, top_n=PSX_TOP_N):
    """Filter to the sweet-spot market-cap band with real liquidity, rank by traded value scaled by
    positive 3-month momentum, return top_n as (ticker, name, sector, rev_growth_pct, eps_growth_pct,
    perf_3m_pct, analyst_row). perf_3m is the 3-month performance % carried for the s6 momentum fallback.
    The KSE-30 mega-caps (PSX_MEGACAPS) are FORCE-INCLUDED even when they sit ABOVE the band ceiling
    (they're KSE-30 mega-caps the band excludes), so they always get the analyst overlay + TCE
    scoring. Pure + unit-tested (the force-include reads only PSX_MEGACAPS + the scan rows)."""
    def _analyst(r):  # D2: raw analyst fields for tce_psx_analyst + L3: scan close/volume for the price path
        return {k: r.get(k) for k in ('close', 'volume', 'price_target_average', 'recommendation_mark',
                                      'recommendation_buy', 'recommendation_total',
                                      'earnings_per_share_forecast_next_fq',
                                      'earnings_per_share_forecast_fq', 'earnings_per_share_fq',
                                      'SMA50', 'SMA200')}   # Wave M-A: MA reads ride the analyst row
    def _mk(r):
        return (r['ticker'], r.get('name') or r['ticker'], r.get('sector') or '',
                _f(r.get('total_revenue_yoy_growth_ttm')),
                _f(r.get('earnings_per_share_diluted_yoy_growth_ttm')),
                _f(r.get('Perf.3M')), _analyst(r))
    scored = []
    for r in rows:
        mc = _f(r.get('market_cap_basic')); px = _f(r.get('close')); vol = _f(r.get('volume'))
        if mc is None or px is None or vol is None:
            continue
        if not (mcap_min <= mc <= mcap_max) or px <= 0 or vol <= 0:
            continue
        chg3m = _f(r.get('Perf.3M')) or 0.0
        score = (px * vol) * (1 + max(chg3m, 0) / 100.0)
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    out = [_mk(r) for _, r in scored[:top_n]]
    # D2 holdings: KSE-30 mega-caps sit ABOVE mcap_max, so the band filter above drops them. Append any
    # tracked holding present in the scan rows (range[0,500] mcap-desc -> the mega-caps are always in it)
    # with a valid close that isn't already in the top_n -> it carries its own analyst block, so it gets
    # s11/s12/s9 + full TCE scoring. A holding missing from the scan is simply skipped.
    have = {t[0] for t in out}
    by_ticker = {r.get('ticker'): r for r in rows}
    for h in list(dict.fromkeys(PSX_MEGACAPS + PSX_WATCHLIST)):   # F5: mega-cap coverage + broker watchlist, deduped
        if h in have:
            continue
        r = by_ticker.get(h)
        if r is not None and (_f(r.get('close')) or 0) > 0:
            out.append(_mk(r))
    # Bank-merit admission (v1.53): the EXPLOSIVE gates are industrial income-statement mechanics
    # (revenue/operating-profit growth, NP accelerating, CFO >= NP) that a bank's accounts don't have
    # — a bank has no operating-profit cascade and its CFO is dominated by loan/deposit flows — so a
    # bank can NEVER satisfy G1/G2/A1/C1-C3 on merit and is carved to the System-B bank model. To let
    # bank MERIT decide which banks appear (NOT force-inclusion of named tickers), admit EVERY true
    # bank present in the mcap-desc scan rows (range[0,500] -> the large listed banks are in it) with a
    # valid, liquid quote. They classify as FINANCIAL and are ranked by their System-B score downstream.
    have = {t[0] for t in out}
    for r in rows:
        tk = r.get('ticker')
        if tk in have:
            continue
        if not _is_true_bank(r.get('sector'), r.get('name'), tk):
            continue
        if (_f(r.get('close')) or 0) > 0 and (_f(r.get('volume')) or 0) > 0:
            out.append(_mk(r)); have.add(tk)
    return out


def fetch_psx_universe_live(top_n=PSX_TOP_N):
    body = {'columns': PSX_SCAN_COLS, 'range': [0, 500],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'}, 'markets': ['pakistan']}
    r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                      headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f'TV scan HTTP {r.status_code}')
    rows = parse_tv_scan(r.json(), PSX_SCAN_COLS)
    # F5 watchlist diagnostic (logging-only): the force-include in derive_psx_candidates only fires for a
    # watchlist name PRESENT in these top-500 mcap-desc scan rows. Log loaded-count + which names are in the
    # scan (will force-include) vs absent (silently skipped) -> distinguishes file-not-deployed from
    # not-in-top-500 from working, instead of guessing off the candidate list.
    if PSX_WATCHLIST:
        _scan_tk = {rr.get('ticker') for rr in rows}
        _present = [t for t in PSX_WATCHLIST if t in _scan_tk]
        _absent  = [t for t in PSX_WATCHLIST if t not in _scan_tk]
        log(f'  [F5 watchlist] {len(PSX_WATCHLIST)} loaded {PSX_WATCHLIST}; in top-500 scan -> force-include: {_present}; absent from scan (skipped): {_absent}')
    else:
        log('  [F5 watchlist] psx_watchlist.json absent/empty -> nothing force-included (drop it in the repo root)')
    return derive_psx_candidates(rows, top_n=top_n)


def screen_psx_stock(ticker_tuple):
    # Accepts (ticker, name, sector) or (...rev_growth, eps_growth) or (...rev_growth, eps_growth, perf_3m)
    ticker, name, sector = ticker_tuple[0], ticker_tuple[1], ticker_tuple[2]
    rev_growth = ticker_tuple[3] if len(ticker_tuple) > 3 else None
    eps_growth = ticker_tuple[4] if len(ticker_tuple) > 4 else None
    perf_3m    = ticker_tuple[5] if len(ticker_tuple) > 5 else None
    analyst    = ticker_tuple[6] if len(ticker_tuple) > 6 else None   # D2: TV analyst row (or None)
    out = {'ticker': ticker, 'name': name, 'sector': sector,
           'price': None, 'avg_volume': None, 'analyst': analyst,
           'rev_growth': rev_growth, 'eps_growth': eps_growth, 'perf_3m': perf_3m,
           'ma': _ma_reads((analyst or {}).get('close'), (analyst or {}).get('SMA50'),
                           (analyst or {}).get('SMA200')),   # Wave M-A: MA trend reads (PSX)
           'growth_source': 'psx_annual' if rev_growth is not None else None,
           'data_source': 'cached', 'status': 'STRONG'}

    # L3: prefer the TV pakistan/scan close already fetched in the universe POST. Same basis as the
    # analyst target-upside calc (internally consistent), eliminates the 25 per-name dps.psx GETs, and
    # avoids the unreliable yahoo:.KA fallback (wrong basis when dps.psx is down). dps.psx / .KA below
    # remain as a defensive fallback only when the scan somehow lacks a close.
    scan_close = _f(analyst.get('close')) if isinstance(analyst, dict) else None
    if scan_close is not None and scan_close > 0:
        out['price'] = round(scan_close, 2)
        scan_vol = analyst.get('volume') if isinstance(analyst, dict) else None
        try:
            out['avg_volume'] = int(scan_vol) if scan_vol is not None else None
        except (TypeError, ValueError):
            out['avg_volume'] = None
        out['data_source'] = 'tv_scan'
        return out

    # Fallback only if the scan lacked a close (rare — derive_psx_candidates requires one). dps.psx
    # EOD is REMOVED from the price path: it is confirmed stale (TRG 164 vs real 72, KPUS 49 vs real
    # 2443 — same frozen endpoint family as the KSE-100 index). yahoo:.KA is on the correct/current
    # basis (it matches the TV scan close), so it is the only fallback.
    if out['price'] is None:
        try:
            import yfinance as yf
            t = yf.Ticker(f'{ticker}.KA')
            h = t.history(period='1mo')
            if len(h) > 0:
                out['price'] = round(float(h['Close'].iloc[-1]), 2)
                out['avg_volume'] = int(h['Volume'].iloc[-5:].mean())
                out['data_source'] = 'yahoo:.KA'
        except Exception:
            pass

    return out


PSX_SOURCE_PROBE = False   # Wave P Phase-0: one-shot reachability/parseability probe for the PSX
                          # institutional sources (MUFAP / AMC FMR PDFs / dps.psx filings / aggregators).
                          # Logging-only; set False once the runner verdict is read.

# (label, url, kind) - REAL endpoints confirmed during research. The probe only LOGS whether the
# GitHub Actions runner can reach + parse each; Cloudflare blocks by datacenter IP, so this question
# can ONLY be answered on the runner, never in the build sandbox (which reaches github/pypi/npm only).
_PSX_PROBE_SOURCES = [
    ('MUFAP AUM-by-fund (HTML; fund universe + risk category)', 'https://www.mufap.com.pk/Industry/IndustryStatMonthly?tab=1', 'html'),
    ('MUFAP fund directory (HTML)',                             'https://www.mufap.com.pk/FundProfile/FundDirectory', 'html'),
    ('MUFAP unit-holder pattern (HTML)',                        'https://www.mufap.com.pk/Industry/WebUnitHolderPattern', 'html'),
    ('AMC FMR PDF - Al Meezan (top-holdings source)',           'https://www.almeezangroup.com/assets/uploads/2026/01/FMR-December-2025.pdf', 'pdf'),
    ('Fund factsheet aggregator - fundbazaarglobal (PDF)',      'https://fundbazaarglobal.com/uploads/pdfs/Al_Meezan_Mutual_Fund.pdf', 'pdf'),
    ('dps.psx filing PDF (directors report / financials)',      'https://dps.psx.com.pk/download/document/237931.pdf', 'pdf'),
    ('dps.psx company page (HTML; filing-id discovery)',        'https://dps.psx.com.pk/company/OGDC', 'html'),
    ('Broker consensus aggregator - tickeranalysts (HTML)',     'https://www.tickeranalysts.com/broker-picks', 'html'),
]


def probe_psx_institutional_sources():
    """Wave P Phase-0 - LOGGING-ONLY reachability/parseability probe (mirrors the L1 insider/coverage
    probes). For each candidate PSX institutional source, logs HTTP status + content-type + size + a
    parse hint (valid-PDF / HTML tables+rows / Cloudflare challenge / JS-rendered). Decides what is
    actually feedable FROM THE RUNNER before any parser is built. Never raises into the run; each GET
    is independently guarded with a short timeout. No screening/scoring effect."""
    if not PSX_SOURCE_PROBE:
        return
    log('  [Wave P probe] PSX institutional-source reachability (logging-only):')
    CF = ('just a moment', 'cf-browser-verification', 'attention required',
          'checking your browser', '__cf_chl', 'enable javascript and cookies', 'cloudflare')
    for label, url, kind in _PSX_PROBE_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=12)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            size = len(r.content or b'')
            head = (r.content[:6000].decode('utf-8', 'ignore').lower()) if r.content else ''
            if kind == 'pdf':
                if r.content[:4] == b'%PDF':
                    hint = f'valid PDF {size//1024}kb (Phase-2 parse w/ pdfplumber)'
                elif any(m in head for m in CF):
                    hint = 'CLOUDFLARE challenge -> blocked'
                else:
                    hint = f'NOT a PDF (ct={ct})'
            else:  # html
                if any(m in head for m in CF):
                    hint = 'CLOUDFLARE challenge -> blocked'
                else:
                    body = r.text.lower()
                    nt, ntr = body.count('<table'), body.count('<tr')
                    hint = (f'HTML tables={nt} rows~{ntr} -> parseable' if nt
                            else 'HTTP 200 but no <table> (JS-rendered?)')
            log(f'    - {label}: HTTP {r.status_code} {ct} {size//1024}kb -> {hint}')
        except Exception as e:
            log(f'    - {label}: FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')


# ============================ Wave P Phase-1: AMC FMR fund-ownership overlay ============================
# Fetches the latest Fund Manager Report (FMR) factsheet PDFs for the high-risk equity/asset-allocation
# funds of the major AMCs (via the fundbazaarglobal aggregator -> static per-fund URLs, probe-confirmed
# reachable from the runner), parses each fund's standardized Top-Ten Holdings table, and aggregates into
# a per-PSX-stock institutional-ownership signal (# funds holding + avg/max weight) — the PSX smart-money
# analog of the US ETF-consensus/13F overlay. DISPLAY/CONTEXT ONLY: it is NOT wired into the TCE conviction
# count (a new scored stream would move tiers, violating the Sept freeze) — promote post-maturation if it
# earns it. Fully guarded; any failure -> empty overlay, scan continues. pdfplumber imported lazily.
PSX_FMR_INGEST = True

# (fundbazaarglobal slug, AMC) — confirmed high-risk equity / asset-allocation / balanced funds.
# Static URLs (https://fundbazaarglobal.com/uploads/pdfs/<slug>.pdf); freshness varies by fund (logged).
_FMR_SOURCES = [
    ('Al_Meezan_Mutual_Fund', 'Al Meezan'),
    ('Meezan_Balanced_Fund', 'Al Meezan'),
    ('Meezan_Asset_Allocation_Fund', 'Al Meezan'),
    ('UBL_Stock_Advantage_Fund', 'UBL'),
    ('UBL_Financial_Sector_Fund', 'UBL'),
    ('UBL_Asset_Allocation_Fund', 'UBL'),
    ('NBP_Stock_Fund', 'NBP'),
    ('HBL_Stock_Fund', 'HBL'),
    ('HBL_Islamic_Equity_Fund', 'HBL'),
]

# PSX legal-name -> ticker (ordered: MORE SPECIFIC FIRST so FFBL beats FFC, EFERT beats ENGRO, etc.).
# Matched as a substring against a lowercased, whitespace-collapsed company name. Covers the PSX
# candidate universe + the most-held large caps (which is what funds hold); unmapped names are logged.
_PSX_NAME_TICKER = [
    ('oil & gas development','OGDC'), ('oil and gas development','OGDC'),
    ('pakistan petroleum','PPL'), ('pak petroleum','PPL'),
    ('mari energies','MARI'), ('mari petroleum','MARI'),
    ('pakistan oilfields','POL'), ('pak oilfields','POL'),
    ('pakistan state oil','PSO'), ('pak state oil','PSO'), ('attock refinery','ATRL'), ('national refinery','NRL'),
    ('attock petroleum','APL'), ('hi-tech lubricants','HTL'), ('hi tech lubricants','HTL'),
    ('hascol','HASCOL'), ('sui northern','SNGP'), ('sui southern','SSGC'),
    ('hub power','HUBC'), ('k-electric','KEL'), ('k electric','KEL'),
    ('kot addu','KAPCO'), ('nishat chunian power','NCPL'), ('nishat power','NPL'),
    ('fauji fertilizer bin qasim','FFBL'), ('fauji fertilizer company','FFC'), ('fauji fertilizer','FFC'),
    ('engro fertiliser','EFERT'), ('engro fertilizer','EFERT'), ('fatima fertilizer','FATIMA'),
    ('engro holding','ENGRO'), ('engro corporation','ENGRO'), ('engro polymer','EPCL'),
    ('lucky cement','LUCK'), ('d.g. khan','DGKC'), ('dg khan','DGKC'), ('d g khan','DGKC'),
    ('maple leaf','MLCF'), ('cherat cement','CHCC'), ('fauji cement','FCCL'),
    ('kohat cement','KOHC'), ('pioneer cement','PIOC'), ('bestway cement','BWCL'),
    ('attock cement','ACPL'), ('thatta cement','THCCL'),
    ('meezan bank','MEBL'), ('mcb bank','MCB'), ('united bank','UBL'), ('habib bank','HBL'),
    ('bank alfalah','BAFL'), ('bank al habib','BAHL'), ('bank al-habib','BAHL'),
    ('national bank of pakistan','NBP'), ('allied bank','ABL'), ('askari bank','AKBL'),
    ('askari commercial bank','AKBL'), ('faysal bank','FABL'), ('bank of punjab','BOP'), ('js bank','JSBL'),
    ('soneri bank','SNBL'), ('standard chartered','SCBPL'), ('habib metropolitan','HMB'),
    ('systems limited','SYS'), ('systems ltd','SYS'), ('trg pakistan','TRG'),
    ('netsol','NETSOL'), ('avanceon','AVN'), ('octopus digital','OCTOPUS'),
    ('indus motor','INDU'), ('honda atlas','HCAR'), ('atlas honda','ATLH'),
    ('pak suzuki','PSMC'), ('millat tractor','MTL'), ('sazgar','SAZEW'),
    ('ghandhara nissan','GHNL'), ('ghandhara industries','GHNI'), ('ghandhara','GHNI'),
    ('agha steel','AGHA'), ('international steels','ISL'), ('international steel','ISL'),
    ('international industries','INIL'), ('amreli steels','ASTL'), ('mughal iron','MUGHAL'),
    ('mughal steel','MUGHAL'), ('aisha steel','ASL'), ('crescent steel','CSAP'),
    ('nishat mills','NML'), ('interloop','ILP'), ('gul ahmed','GADT'), ('kohinoor textile','KTML'),
    ('national foods','NATF'), ('the organic meat','TOMCL'), ('the searle','SEARL'),
    ('ibl healthcare','IBLHL'), ('tpl properties','TPLP'), ('tpl corp','TPL'),
    ('pace (pakistan)','PACE'), ('pace pakistan','PACE'), ('loads limited','LOADS'),
    ('telecard','TELE'), ('jdw sugar','JDW'), ('service industries','SRVI'),
    ('ghani glass','GHGL'), ('tariq glass','TGL'), ('treet corporation','TREET'),
    ('pakistan tobacco','PAKT'), ('philip morris','PMPK'),
    ('packages limited','PKGS'), ('packages ltd','PKGS'),
    ('jubilee life','JLICL'), ('adamjee insurance','AICL'),
    ('macpac films','MACFL'), ('gharibwal cement','GWLC'), ('image pakistan','IMAGE'),
]

_HOLDING_RE = re.compile(
    r"([A-Z][\w&\.\,\'\(\)\-/ ]{2,55}?(?:Limited|Ltd\.?|Company|Co\.))\s+(\d{1,2}(?:\.\d{1,2})?)\s*%"
)

def map_name_to_ticker(name):
    n = ' '.join((name or '').lower().split())
    for sub, tk in _PSX_NAME_TICKER:
        if sub in n:
            return tk
    return None

def parse_fmr_holdings(text):
    """Layout-agnostic parse of the FMR Top-Ten Holdings table. Returns (holdings, unmapped) where
    holdings = [(ticker, weight_pct, raw_name)] deduped per ticker keeping max weight, and unmapped =
    [(raw_name, pct)] for clean '...Ltd/Limited' names not in the map (logged so the map can grow)."""
    seen = {}
    unmapped = []
    for m in _HOLDING_RE.finditer(text or ''):
        raw, pct = m.group(1).strip(), float(m.group(2))
        if not (0.1 <= pct <= 40.0):     # holding weights live here; rejects levies/returns/NAV noise
            continue
        tk = map_name_to_ticker(raw)
        if tk is None:
            if re.search(r'(Limited|Ltd\.?)$', raw):
                unmapped.append((raw, pct))
            continue
        if tk not in seen or pct > seen[tk][0]:
            seen[tk] = (pct, raw)
    holdings = [(tk, w, raw) for tk, (w, raw) in seen.items()]
    return holdings, unmapped

def fetch_fmr_fund_ownership():
    """Wave P Phase-1 orchestrator. Fetch each high-risk fund FMR PDF, parse Top-Ten Holdings, aggregate
    into per-PSX-stock {funds, avg_weight, max_weight, sum_weight}. Returns (by_ticker, meta). Fully
    guarded: any failure -> ({}, {}) and the scan proceeds. DISPLAY OVERLAY ONLY (no scoring effect)."""
    if not PSX_FMR_INGEST:
        return {}, {}, {}
    try:
        import pdfplumber
    except Exception as e:
        log(f'  [Wave P FMR] pdfplumber unavailable ({e}) -> fund-ownership overlay skipped')
        return {}, {}, {}
    import io
    from collections import defaultdict
    agg = defaultdict(list)
    fund_meta = []
    unmapped_all = defaultdict(float)
    per_fund = {}
    log(f'  [Wave P FMR] ingesting {len(_FMR_SOURCES)} high-risk fund FMRs (fundbazaarglobal)...')
    for slug, amc in _FMR_SOURCES:
        url = f'https://fundbazaarglobal.com/uploads/pdfs/{slug}.pdf'
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=25)
            if r.status_code != 200 or r.content[:4] != b'%PDF':
                log(f'    - {slug}: skip (HTTP {r.status_code}, not a PDF)')
                continue
            text = ''
            with pdfplumber.open(io.BytesIO(r.content)) as pdf:
                for pg in pdf.pages:
                    text += (pg.extract_text() or '') + '\n'
            hold, unm = parse_fmr_holdings(text)
            asof = '?'
            # report-context patterns first; bare DD-Mon-YYYY only when prefixed (stops grabbing inception/
            # footer dates like 04-Aug-2006); every match recency-guarded to year>=2024 (else keep scanning)
            for _pat in (r'as at ([A-Z][a-z]+\.? \d{1,2},? \d{4})',
                         r'as on ([A-Z][a-z]+\.? \d{1,2},? \d{4})',
                         r'(?:as at|as on|as of)[ :]+(\d{1,2}[-/][A-Z][a-z]{2}[-/]\d{2,4})',
                         r'Report[ \-]+([A-Z][a-z]+ \d{4})',
                         r'\b([A-Z][a-z]{2,9} \d{1,2},? \d{4})\b'):
                for _mm in re.finditer(_pat, text):
                    _cand = _mm.group(1); _yr = re.search(r'(20\d{2})', _cand)
                    if _yr and int(_yr.group(1)) >= 2024:
                        asof = _cand; break
                if asof != '?':
                    break
            fund_hold = {}
            for tk, w, _ in hold:
                agg[tk].append(w)
                if tk not in fund_hold or w > fund_hold[tk]:
                    fund_hold[tk] = w
            per_fund[slug] = fund_hold
            for raw, w in unm:
                unmapped_all[raw] = max(unmapped_all[raw], w)
            fund_meta.append({'slug': slug, 'amc': amc, 'as_of': asof, 'holdings': len(hold)})
            log(f'    - {slug} ({amc}): {len(hold)} holdings parsed, as-of {asof}'
                + (f', {len(unm)} unmapped' if unm else ''))
        except Exception as e:
            log(f'    - {slug}: FETCH/PARSE FAILED ({type(e).__name__}: {str(e)[:45]})')
    by_ticker = {}
    for tk, ws in agg.items():
        by_ticker[tk] = {'funds': len(ws), 'avg_weight': round(sum(ws) / len(ws), 2),
                         'max_weight': round(max(ws), 2), 'sum_weight': round(sum(ws), 2)}
    meta = {'funds_scanned': len(fund_meta), 'tickers_covered': len(by_ticker), 'funds': fund_meta}
    if by_ticker:
        top = sorted(by_ticker.items(), key=lambda kv: (-kv[1]['funds'], -kv[1]['avg_weight']))[:8]
        log('  [Wave P FMR] top institutional holdings: '
            + ', '.join(f"{tk}({v['funds']}f/{v['avg_weight']}%)" for tk, v in top))
        if unmapped_all:
            tu = sorted(unmapped_all.items(), key=lambda kv: -kv[1])[:6]
            log('  [Wave P FMR] top UNMAPPED (grow _PSX_NAME_TICKER): '
                + '; '.join(f"{n}={w}%" for n, w in tu))
    else:
        log('  [Wave P FMR] no holdings parsed (all sources failed/empty) -> overlay empty, scan continues')
    return by_ticker, meta, per_fund


# ---- v1.48.0 holdings change-tracking: per-stock institutional FLOW between two snapshots ----
FMR_FLOW_BAND = 0.05   # >+/-5% change in summed weight over the COMMON fund set => ACCUM / TRIM

def _fmr_compute_flows(cur_per_fund, prior_per_fund):
    """PURE. Per-stock month-over-month institutional flow, computed ONLY over funds present in BOTH
    snapshots (set intersection) = the FALSE-EXIT GUARD: a fund whose PDF failed to download is excluded,
    so a coverage gap can never masquerade as a sell. Returns {ticker:{flow,funds_delta,weight_delta}};
    flow in NEW/EXITED/ACCUMULATING/TRIMMING/STABLE. Empty when there is no overlapping fund set."""
    cur_per_fund = cur_per_fund or {}; prior_per_fund = prior_per_fund or {}
    common = set(cur_per_fund) & set(prior_per_fund)
    if not common:
        return {}
    tickers = set()
    for fnd in common:
        tickers |= set(cur_per_fund[fnd]); tickers |= set(prior_per_fund[fnd])
    out = {}
    for tk in tickers:
        cur_f  = [fnd for fnd in common if tk in cur_per_fund[fnd]]
        prev_f = [fnd for fnd in common if tk in prior_per_fund[fnd]]
        cur_n, prev_n = len(cur_f), len(prev_f)
        cur_w  = round(sum(cur_per_fund[fnd][tk]  for fnd in cur_f),  2)
        prev_w = round(sum(prior_per_fund[fnd][tk] for fnd in prev_f), 2)
        if prev_n == 0 and cur_n > 0:
            flow = 'NEW'
        elif cur_n == 0 and prev_n > 0:
            flow = 'EXITED'
        elif cur_n > prev_n or cur_w >= prev_w * (1 + FMR_FLOW_BAND):
            flow = 'ACCUMULATING'
        elif cur_n < prev_n or cur_w <= prev_w * (1 - FMR_FLOW_BAND):
            flow = 'TRIMMING'
        else:
            flow = 'STABLE'
        out[tk] = {'flow': flow, 'funds_delta': cur_n - prev_n, 'weight_delta': round(cur_w - prev_w, 2)}
    return out
# ========================== end Wave P Phase-1 FMR fund-ownership overlay ==========================


# ============================ Wave P Phase-2 probe: FIPI/LIPI daily flows ============================
# FIPI/LIPI (Foreign + Local Investor Portfolio Investment) = the daily institutional FLOW signal that
# complements the monthly fund-ownership STOCK overlay. Compiled daily by NCCPL (~6-7pm PKT), redistributed
# by Sarmaaya (PSX-authorized) + aggregators. LOGGING-ONLY reachability probe (mirrors the Phase-0 probe):
# tests which source is reachable + parseable FROM THE RUNNER before any parser is built. Flip False once read.
# VERDICT READ (v1.47.0 run): no clean free runner-reachable feed - NCCPL Cloudflare-blocked, Sarmaaya/FinHisaab
# are JS SPAs (data via hidden API), Business Recorder is a NEWS page (its tables are a price ticker). FIPI/LIPI
# DEFERRED; the monthly fund-ownership overlay already carries the institutional-positioning signal. Probe off.
PSX_FIPI_PROBE = False
_FIPI_PROBE_SOURCES = [
    ('NCCPL FIPI normal daily (official)', 'https://www.nccpl.com.pk/en/market-information/fipi-lipi/fipi-normal-daily', 'html'),
    ('NCCPL LIPI normal daily (official)', 'https://www.nccpl.com.pk/en/portfolio-investments/lipi-normal-daily', 'html'),
    ('NCCPL market-information hub',       'https://www.nccpl.com.pk/market-information', 'html'),
    ('Sarmaaya FIPI/LIPI (PSX-authorized redistributor)', 'https://sarmaaya.pk/psx/fipi-lipi', 'html'),
    ('FinHisaab FIPI/LIPI (aggregator)',   'https://finhisaab.com/market-updates/fipi-lipi', 'html'),
    ('Business Recorder FIPI trend',       'https://www.brecorder.com/trends/fipi', 'html'),
]


def probe_fipi_lipi_sources():
    """Wave P Phase-2 - LOGGING-ONLY reachability/parseability probe for the FIPI/LIPI daily-flow sources.
    Logs HTTP status + content-type + size + a parse hint (HTML tables+rows / Cloudflare / JS-rendered) per
    source so we can pick a feedable one before building the parser. Never raises into the run."""
    if not PSX_FIPI_PROBE:
        return
    log('  [Wave P FIPI probe] FIPI/LIPI daily-flow source reachability (logging-only):')
    CF = ('just a moment', 'cf-browser-verification', 'attention required',
          'checking your browser', '__cf_chl', 'enable javascript and cookies', 'cloudflare')
    for label, url, kind in _FIPI_PROBE_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=12)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            size = len(r.content or b'')
            body = (r.text or '').lower()
            if any(m in body[:6000] for m in CF):
                hint = 'CLOUDFLARE challenge -> blocked'
            else:
                nt, ntr = body.count('<table'), body.count('<tr')
                hint = (f'HTML tables={nt} rows~{ntr} -> parseable' if nt
                        else 'HTTP 200 but no <table> (JS-rendered? needs API/headless)')
            log(f'    - {label}: HTTP {r.status_code} {ct} {size//1024}kb -> {hint}')
        except Exception as e:
            log(f'    - {label}: FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')
# ========================== end Wave P Phase-2 FIPI/LIPI probe ==========================


# ============================ Wave Q Phase-0: bank-data source probe (logging-only) ============================
# Before wiring the three user-named bank-data sources into the IG2 bank-input pipeline, prove ON THE RUNNER
# which are reachable + parseable (Cloudflare blocks by datacenter IP -> only knowable here, not in sandbox).
#   - SCS Trade SNAPSHOT  = server-rendered CURRENT-YEAR fields (EPS / ROE / ROA / book-value->equity /
#                           cash-flow-per-share->CFO / ADR / equity-to-assets) -> usable as a gap-filling overlay.
#   - SCS Trade YEARLY FIN/RATIOS = JS-populated shell (empty on a plain fetch, confirmed from sandbox) ->
#                           the 6yr CAGR/trend series is NOT free over plain HTTP; stays manual / annual-report.
#   - ANNUAL-REPORT PDF   = the six-year financial-highlights table (pdfplumber) -> the full-series fallback.
#   - KPMG Banking Perspective = SECTOR EVALUATION ONLY (industry CAR/NIM/NPL/ROE medians) -> NEVER a per-bank
#                           input; feeds a sector-health read, not a bank's IG2 ratios.
# Logging-only; gated BANK_SOURCE_PROBE; each GET independently guarded; can NEVER affect the live scan.
BANK_SOURCE_PROBE = False  # verdict read (all 3 reachable from the runner; SCS history JS-empty)

_BANK_PROBE_SOURCES = [
    ('SCS snapshot AKBL (server-rendered current-yr fields)', 'https://www.scstrade.com/stockscreening/SS_CompanySnapShot.aspx?symbol=AKBL', 'scs_snap'),
    ('SCS snapshot BOP (consistency check)',                  'https://www.scstrade.com/stockscreening/SS_CompanySnapShot.aspx?symbol=BOP', 'scs_snap'),
    ('SCS Yearly Financials Adv AKBL (6yr series?)',          'https://www.scstrade.com/stockscreening/SS_CompanySnapShotYFNew.aspx?symbol=AKBL', 'scs_hist'),
    ('SCS Yearly Ratios AKBL (NPL/ROE history?)',             'https://www.scstrade.com/stockscreening/SS_CompanySnapShotYR.aspx?symbol=AKBL', 'scs_hist'),
    ('Annual report PDF - BOP 2024 (six-year highlights)',    'https://www.bop.com.pk/Documents/Financials/Annual%20Accounts/BOP%20ANNUAL%20REPORT%202024.pdf', 'pdf'),
    ('KPMG Banking Perspective 2025 (SECTOR benchmarks)',     'https://assets.kpmg.com/content/dam/kpmgsites/pk/pdf/2025/04/Pakistan-Banking-Perspective-2025.pdf.coredownload.inline.pdf', 'pdf_sector'),
]

_SCS_SNAP_KEYS = ('return on equity', 'book value per share', 'cash flow per share',
                  'advance deposite', 'equity to assets', 'last annual eps')
_SCS_HIST_KEYS = ('mark-up', 'interest earned', 'profit after tax', 'total assets', 'total deposits')


def probe_bank_data_sources():
    """Wave Q Phase-0 - LOGGING-ONLY reachability/parseability probe for the three bank-data sources.
    Logs HTTP status + content-type + size + a ROLE-SPECIFIC parse hint per source:
      scs_snap   -> how many key CURRENT-YEAR fields are present (overlay gap-filler for the latest year)
      scs_hist   -> whether the multi-year statement lines are present or the JS-empty shell (the 6yr series)
      pdf        -> valid PDF -> annual-report six-year highlights parseable (pdfplumber)
      pdf_sector -> KPMG -> SECTOR-evaluation benchmarks only, never a per-bank input
    Cloudflare blocks by datacenter IP so this is only answerable on the runner. Never raises into the run."""
    if not BANK_SOURCE_PROBE:
        return
    log('  [Wave Q probe] bank-data source reachability (logging-only):')
    CF = ('just a moment', 'cf-browser-verification', 'attention required',
          'checking your browser', '__cf_chl', 'enable javascript and cookies', 'cloudflare')
    for label, url, kind in _BANK_PROBE_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=15)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            size = len(r.content or b'')
            head = (r.content[:8000].decode('utf-8', 'ignore').lower()) if r.content else ''
            if kind in ('pdf', 'pdf_sector'):
                if r.content[:4] == b'%PDF':
                    role = ('SECTOR benchmarks (CAR/NIM/NPL/ROE medians)' if kind == 'pdf_sector'
                            else 'six-year highlights via pdfplumber')
                    hint = f'valid PDF {size//1024}kb -> {role}'
                elif any(m in head for m in CF):
                    hint = 'CLOUDFLARE challenge -> blocked'
                else:
                    hint = f'NOT a PDF (ct={ct})'
            elif any(m in head for m in CF):
                hint = 'CLOUDFLARE challenge -> blocked'
            else:
                body = (r.text or '').lower()
                if kind == 'scs_snap':
                    have = [k for k in _SCS_SNAP_KEYS if k in body]
                    hint = (f'server-rendered, {len(have)}/{len(_SCS_SNAP_KEYS)} key current-yr fields -> overlay-parseable'
                            if len(have) >= 3 else f'only {len(have)}/{len(_SCS_SNAP_KEYS)} fields (blocked/changed?)')
                else:  # scs_hist
                    have = [k for k in _SCS_HIST_KEYS if k in body]
                    hint = (f'history PRESENT ({len(have)}/{len(_SCS_HIST_KEYS)} statement lines) -> 6yr series parseable'
                            if len(have) >= 2
                            else 'history EMPTY (JS-rendered shell -> 6yr series NOT free over plain fetch)')
            log(f'    - {label}: HTTP {r.status_code} {ct} {size//1024}kb -> {hint}')
        except Exception as e:
            log(f'    - {label}: FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')
# ========================== end Wave Q Phase-0 bank-data probe ==========================


# ============================ Wave PSX-R Phase-0: SCS report-PDF reachability/parse probe ============================
# Before wiring the PSX budget/reports overlay (Valuation Matrix factor screens, MTS leverage gauge, MSCI flow
# catalyst), prove ON THE RUNNER that each SCS report PDF is reachable + parseable. Cloudflare/datacenter-IP blocking
# means the sandbox cannot answer this. Logging-only; gated SCS_REPORT_PROBE; each GET guarded; never affects the scan.
SCS_REPORT_PROBE = False   # verdict read (v1.68.2): all 4 SCS PDFs reachable + pdfplumber-parseable from the runner; re-arm only to re-probe

_SCS_REPORT_SOURCES = [
    ('SCS Valuation Matrix (per-name P/E,DY,ROE,ROA,EBITDA-margin,EV/EBITDA,P/B,bank NIM)',
     'https://www.scstrade.com/research/Research%20Reports/General/Valuation%20Matrix.pdf', 'valuation matrix'),
    ('SCS MTS Report (market margin-financing positions -> leverage gauge)',
     'https://www.scstrade.com/research/Research%20Reports/General/MTS%20Report.pdf', 'mts'),
    ('SCS MSCI Provisional Indexes (index inclusion/exclusion -> passive-flow catalyst)',
     'https://www.scstrade.com/research/Research%20Reports/General/MSCI-Provisional-Indexes.pdf', 'msci'),
    ('SCS News Briefs (curated news; lower value)',
     'https://www.scstrade.com/research/Research%20Reports/General/NewsBriefs.pdf', 'news'),
]


def probe_scs_reports():
    """Wave PSX-R Phase-0 - LOGGING-ONLY reachability/parse probe for the SCS report PDFs that would feed the PSX
    budget/reports overlay. Logs HTTP status + content-type + size + a parse hint: valid %PDF magic, and (when
    pdfplumber is available) whether page-1 text carries the expected keyword -> pdfplumber-parseable, vs a
    Cloudflare challenge / non-PDF / image-only shell. Runner-only answer (datacenter-IP CF blocking). Never raises."""
    if not SCS_REPORT_PROBE:
        return
    log('  [Wave PSX-R probe] SCS report-PDF reachability/parse (logging-only):')
    CF = ('just a moment', 'cf-browser-verification', 'attention required',
          'checking your browser', '__cf_chl', 'enable javascript and cookies', 'cloudflare')
    for label, url, key in _SCS_REPORT_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=20)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            size = len(r.content or b'')
            head = (r.content[:8000].decode('utf-8', 'ignore').lower()) if r.content else ''
            if r.content[:4] == b'%PDF':
                page1 = None
                try:
                    import pdfplumber, io
                    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
                        page1 = (pdf.pages[0].extract_text() or '').lower() if pdf.pages else ''
                except Exception:
                    page1 = None   # pdfplumber absent/failed here -> magic-only hint
                if page1 is None:
                    hint = f'valid PDF {size//1024}kb (pdfplumber not run -> magic-only; confirm parse next)'
                elif key in page1:
                    hint = f"valid PDF {size//1024}kb, page1 carries '{key}' -> pdfplumber-parseable"
                elif page1:
                    hint = f"valid PDF {size//1024}kb, page1 text present but no '{key}' (layout shift?)"
                else:
                    hint = f'valid PDF {size//1024}kb but NO page1 text (image/scanned -> needs OCR)'
            elif any(m in head for m in CF):
                hint = 'CLOUDFLARE challenge -> blocked from runner'
            else:
                hint = f'NOT a PDF (ct={ct}) -> URL moved/renamed?'
            log(f'    - {label}: HTTP {r.status_code} {ct} {size//1024}kb -> {hint}')
        except Exception as e:
            log(f'    - {label}: FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')
# ========================== end Wave PSX-R Phase-0 SCS report probe ==========================


# ============================ Wave R Phase-0: remaining FREE-LEVER feed reachability/parse probe ============================
# Several PSX macro levers still run on manual / quarterly last-good (psx_macros_manual.json): SBP FX reserves, PBS CPI,
# the PBS trade gap (a current-account proxy), Finance-Division fiscal, and sector-regulator boards. Before committing a
# parser to any of them (F3/F4 on the backlog), prove ON THE RUNNER which are reachable + parseable vs Cloudflare-blocked /
# JS-rendered / moved. Probe-before-build. URLs are best-guess STARTING POINTS to be refined from the verdict, not asserted
# feeds. Runner-only answer (datacenter-IP CF blocking; the sandbox reaches only github/pypi/npm). Logging-only; gated
# FREE_LEVER_PROBE; each GET guarded; never affects the universe screen, scoring, IM3, the TCE tier or the Sept freeze.
FREE_LEVER_PROBE = False   # verdict read (v1.84.1): SBP ecodata reserves (72 tables, carries 'reserves') + SBP EasyData both reachable+parseable -> F3 greenlit; PBS CPI reachable (text/xml); PBS trade URL 404 (needs correct path); Finance fiscal + OGRA Cloudflare-403 blocked. Probe stays in code, gated off; re-arm only to re-probe.

_FREE_LEVER_SOURCES = [
    ('SBP FX reserves (weekly, replaces manual sbp_reserves) - sbp.org.pk/ecodata',
     'https://www.sbp.org.pk/ecodata/index2.asp', 'reserves', 'html'),
    ('SBP EasyData macro portal (rate / reserves / external series)',
     'https://easydata.sbp.org.pk/', 'sbp', 'html'),
    ('PBS CPI (monthly inflation, replaces manual pak_cpi)',
     'https://www.pbs.gov.pk/cpi', 'cpi', 'html'),
    ('PBS external trade (monthly trade gap -> current-account proxy)',
     'https://www.pbs.gov.pk/trade-summary', 'trade', 'html'),
    ('Finance Division fiscal operations (fiscal deficit, replaces manual pak_fiscal)',
     'https://www.finance.gov.pk/fiscal_operation.html', 'fiscal', 'html'),
    ('OGRA petroleum prices (sector-regulator board sample)',
     'https://www.ogra.org.pk/petroleum-prices', 'petroleum', 'html'),
]


def probe_free_levers():
    """Wave R Phase-0 - LOGGING-ONLY reachability/parse probe for the remaining FREE PSX-macro feeds that could replace the
    manual / quarterly last-good levers (SBP FX reserves, PBS CPI + trade gap, Finance-Division fiscal, a sector-regulator
    board). Logs HTTP status + content-type + size + a parse hint: Cloudflare challenge -> blocked; PDF -> pdfplumber;
    JSON -> API-style; HTML with a <table> + digits -> likely parseable; thin/low-digit -> likely JS-rendered (SPA shell).
    URLs are best-guess starting points refined from the verdict. Runner-only answer (datacenter-IP CF blocking). Never raises."""
    if not FREE_LEVER_PROBE:
        return
    log('  [Wave R free-lever probe] remaining free PSX-macro feeds (logging-only):')
    CF = ('just a moment', 'cf-browser-verification', 'attention required',
          'checking your browser', '__cf_chl', 'enable javascript and cookies', 'cloudflare')
    for label, url, key, kind in _FREE_LEVER_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=15)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            size = len(r.content or b'')
            txt = (r.content[:200000].decode('utf-8', 'ignore')) if r.content else ''
            low = txt.lower()
            ndig = sum(c.isdigit() for c in txt)
            ntbl = low.count('<table')
            if any(m in low for m in CF):
                hint = 'CLOUDFLARE challenge -> blocked from runner'
            elif r.content[:4] == b'%PDF':
                hint = f'valid PDF {size//1024}kb -> use pdfplumber (confirm parse next)'
            elif ('json' in ct) or (low[:1] in ('{', '[')):
                hint = f'JSON {size//1024}kb -> API-style, likely parseable'
            elif ntbl > 0 and ndig > 50:
                hint = f"HTML {size//1024}kb, {ntbl} table(s) + {ndig} digits" + (f", carries '{key}'" if key in low else '') + ' -> likely parseable'
            elif ndig > 50:
                hint = f'HTML {size//1024}kb, no <table> but {ndig} digits -> maybe parseable (text/figures)'
            elif size < 20000 or ndig < 10:
                hint = f'thin {size//1024}kb / {ndig} digits -> likely JS-rendered (SPA shell) or empty'
            else:
                hint = f'HTML {size//1024}kb -> inspect (no clear table/figures)'
            log(f'    - {label}: HTTP {r.status_code} {ct} {size//1024}kb -> {hint}')
        except Exception as e:
            log(f'    - {label}: FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')
# ========================== end Wave R Phase-0 free-lever probe ==========================


# ============================ CA-units probe (logging-only, runner-side) ============================
# pak_ca is fetched from TradingEconomics (tradingeconomics.com/pakistan/current-account) by _te() with the regex
# 'Current Account' + the first number within 40 chars -> read 1369 on the last run. The dashboard input #pak_ca is
# labelled "Current Account (Monthly USD M)" (default 120), so if 1369 is an ANNUAL / fiscal-year-cumulative figure a
# blind inject would overstate the monthly CA by ~12x. Before wiring pak_ca live we DUMP exactly what TE serves around
# "Current Account" - the value + its UNIT + its PERIOD - so we LOCK whether 1369 is monthly USD-M (inject as-is),
# annual USD-M (/12 or relabel the field), or % of GDP. Logging-only; touches NO data/screening/scoring/IM3/TCE/the
# frozen ledger -> respects the Sept freeze. Read the [CA-units probe] block, then a follow-up flips CA_PROBE False.
CA_PROBE = False   # verdict read (v1.88.1): TE reports CA QUARTERLY ('1369 USD Million in Q1 2026'), unit USD Million; wired in index v5.79 as a monthly run-rate (quarter/3). Probe stays in code, gated off; re-arm only to re-confirm the unit.
CA_PROBE_URL = 'https://tradingeconomics.com/pakistan/current-account'

def probe_pak_ca():
    """LOGGING-ONLY: dump what TradingEconomics serves for Pakistan's Current Account so the unit/period of the value
    the scanner currently grabs (1369) is LOCKED before it is injected into the 'Monthly USD M' dashboard input. Logs
    HTTP status/ct/size, the production-regex extraction (the exact number _te reads), TE's own summary sentence (which
    states the unit + month, e.g. '... surplus of 1369 USD Million in <Month> <Year>'), a text window around the first
    'Current Account' mention, and which unit/period keywords are present. Never raises; respects the Sept freeze."""
    if not CA_PROBE:
        return
    log('  [CA-units probe] TradingEconomics Pakistan current-account (logging-only):')
    try:
        r = requests.get(CA_PROBE_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=15)
        ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
        size = len(r.content or b'')
        log(f'    - HTTP {r.status_code} {ct} {size//1024}kb')
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', r.text or ''))
        # (a) exactly what the production _te regex grabs (should reproduce 1369)
        m = re.search(r'Current Account' + r'[^0-9\-]{0,40}(-?\d{1,4}(?:\.\d{1,2})?)', txt, re.I)
        log(f"    - production-regex value: {m.group(1) if m else 'NO MATCH'}")
        # (b) TE's own summary sentence - the decisive evidence (states unit + month/period)
        ms = re.search(r'(Pakistan recorded a Current Account[^.]{0,170}\.)', txt, re.I)
        if ms:
            log(f'    - TE summary: {ms.group(1).strip()}')
        # (c) text window around the first 'Current Account' mention (the headline value + unit live here)
        i = txt.lower().find('current account')
        if i >= 0:
            log(f'    - window: ...{txt[max(0, i-40):i+260].strip()}...')
        # (d) unit / period keyword presence (cheap basis read)
        low = txt.lower()
        units = [k for k in ('usd million', 'usd billion', 'million', 'billion', 'percent of gdp', '% of gdp') if k in low]
        periods = [k for k in ('monthly', 'quarterly', 'annual', 'annualized', 'fiscal year', 'jul-') if k in low]
        log(f"    - unit keywords present: {units or 'none'}")
        log(f"    - period keywords present: {periods or 'none'}")
    except Exception as e:
        log(f'    - FETCH FAILED ({type(e).__name__}: {str(e)[:60]})')
# ========================== end CA-units probe ==========================


# ============================ World ETF Engine Phase 6 — ISIN price + holdings feed probe (logging-only, runner-side) ============================
# The new ETF universe file is trusted for ISINs ONLY (its YTD/holdings snapshot is NOT relied on); price + FULL holdings are
# researched LIVE per ISIN using ONLY the data sources already plumbed into this dashboard — NO Yahoo, NO FMP (owner rule
# 2026-06-30). Those two feeds must be proven on the runner before the dependent phases (live ETF tracker, Momentum-40, the
# stock->UCITS holdings bridge) are built; the sandbox reaches only github/pypi/npm, so reachability is only knowable on the
# runner. For a representative spread of catalog ISINs this probes, per ISIN:
#   PRICE    (A) TradingView symbol-search resolves the ISIN -> an EXCHANGE:SYMBOL (the existing TV plumbing), then
#            (B) the proven scanner.tradingview.com/symbol symbols-POST (columns:['close']) — the SAME primitive that already
#                prices PSX:KSE100 / TVC:RUT — returns the live close.
#   HOLDINGS (C) stockanalysis.com/api/symbol/e/{sym}/holdings — the EXACT source fetch_etf_holdings() already uses for the
#                US ETF-overlap; returns the FULL constituent list (fixes the file's top-3-only holdings column). Tried on the
#                TV-resolved bare symbol and a couple of plain-symbol variants.
# Logs HTTP status / size / a parse hint per leg so each ISIN's price AND holdings method is LOCKED next rev. Each GET guarded,
# never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze.
ETF_FEED_PROBE = False   # VERDICT (2 consecutive runs, v1.127.0 + v1.127.1): symbol-search.tradingview.com returns an
                         # IDENTICAL static nginx 403 Forbidden for ALL 12/12 sample ISINs, both runs (no JS-challenge,
                         # no captcha -- a flat edge/IP-level deny, same failure class as other datacenter-IP-blocked
                         # sources already documented in this project). CONFIRMED DEAD -- not a header/retry-fixable
                         # issue. Probe kept in code, gated off; re-arm only to re-confirm if TV's WAF posture changes.
                         # Superseded by probe_tv_isin_column() below (tests the proven scan endpoint instead).

# ============================ World ETF Engine Phase 6b — TV scan 'isin' column probe (logging-only, runner-side) ============================
# symbol-search.tradingview.com is confirmed dead (see ETF_FEED_PROBE verdict above). Rather than guess at a fix for a
# blocked endpoint, this pivots to testing a DIFFERENT, ALREADY-PROVEN endpoint: scanner.tradingview.com/america/scan
# -- the exact request shape that has worked flawlessly on the runner every single run (US screening, sector medians,
# etc.) -- to see whether its column schema simply EXPOSES an 'isin' field directly. If it does, symbol+price can be
# resolved in ONE proven request per market, with no separate (and blocked) search step at all. ONE isolated throwaway
# POST, zero risk to the main scan (own request, own columns, never touches production). Logging-only; never raises;
# touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze.
TV_ISIN_COLUMN_PROBE = False  # VERDICT (v1.128.0, one run): CONFIRMED — isin is a valid, populated column in the
                               # proven scanner.tradingview.com/america/scan endpoint. 8/8 rows returned real ISINs that
                               # match known ground truth: AAPL=US0378331005, NVDA=US67066G1040, MSFT=US5949181045,
                               # GOOGL=US02079K3059, AMZN=US0231351067. Probe kept in code for the record.
                               # Superseded by probe_tv_isin_filter() below (Phase 6c: test isin as a FILTER field on
                               # European market scans to look up UCITS ETFs directly by their ISIN).

# ============================ World ETF Engine Phase 6c — TV isin-FILTER probe (logging-only, runner-side) ============================
# Phase 6b confirmed: the TV scanner carries a valid isin COLUMN. The next open question is whether isin can
# also be used as a FILTER CRITERION — i.e., can we POST {filter: [{left:'isin', operation:'equal', right:'IE00B5BMR087'}]}
# to a European market scan endpoint (uk, germany) and get back the UCITS ETF's price + symbol directly?
# If yes: one POST per ISIN → symbol + price + exchange in one hit (no intermediate search step at all).
# If 400: isin is display-only (not filterable) → need a broad scan + isin-column match instead.
# If 200/0-rows: filter accepted but UCITS ETFs not indexed in TV scanner → pivot to issuer-page scraping.
# The two most common UCITS ETF listing venues are LSE (uk/scan) and XETRA (germany/scan); these are the
# scan endpoints most likely to carry iShares/Xtrackers/Vanguard UCITS funds by ISIN.
# ONE probe POST per ISIN per market (3 ISINs × 2 markets = 6 total requests). All logging-only, guarded,
# never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger → respects the Sept freeze.
TV_ISIN_FILTER_PROBE = False  # VERDICT (v1.129.0, one run): CONFIRMED 12/12 — isin is a valid FILTER field
ETF_PERF_PROBE = True  # v1.139.0: tests whether scanner.tradingview.com's isin-filter scan (the SAME proven endpoint already pricing all 60+ Momentum-Watch funds live) also exposes YTD/1-year performance columns -- would replace the static-file YTD and fill the 1Y gap for all 48 funds currently showing "—", live, every run, same mechanism already trusted for price. PRE-ARMED True for one run; flip False once the verdict is read.
                               # on the proven scanner.tradingview.com/{market}/scan endpoint.
                               # All 3 ISINs × 2 markets returned ✓ matches with isin_returned == queried ISIN:
                               #   IE00B5BMR087 / uk:  LSE:CSPX (USD 805.54), LSE:CSP1 (GBX 60715), AQUIS variants
                               #   IE00B5BMR087 / de:  XETR:SXR8 (EUR 704.98)
                               #   IE00B53SZB19 / uk:  LSE:CNDX (USD 1731.20), GBX variants
                               #   IE00B53SZB19 / de:  XETR:SXRV (EUR 1515.40)
                               #   LU0659579147 / uk:  LSE:XBAK (USD 1.823)
                               #   LU0659579147 / de:  XETR:XBAK (EUR 1.601)
                               # type='fund' confirmed on every row. GBX = pence (divide by 100 for GBP).
                               # Production resolver is resolve_etf_live_price() below (Phase 6 complete).


# ============================ World ETF Engine Phase 6 — production ISIN price resolver ============================
# Phase 6 probe verdict CONFIRMED (12/12): scanner.tradingview.com/{market}/scan accepts isin as a filter
# field and returns real UCITS ETF listings with their live prices. uk/scan gives USD and GBX pence listings;
# germany/scan gives EUR. Currency priority: USD > EUR > GBP > GBX. Exchange priority: LSE/XETR > AQUIS.
# This is the PRODUCTION resolver — replaces the entire probe chain (symbol-search.tradingview.com was blocked,
# stockanalysis.com returns 0 for UCITS, TV isin column confirmed, TV isin filter confirmed). One POST per ISIN
# per market; returns the best available listing or None. Guarded; never raises; freeze-safe.
_ETF_CCY_PREF  = {'USD': 0, 'EUR': 1, 'GBP': 2, 'GBX': 99}   # GBX = pence, strongly deprioritised
_ETF_EXCH_PREF = {'LSE': 0, 'XETR': 1, 'AQUIS': 2}             # primary exchanges first

def resolve_etf_live_price(isin):
    """Phase 6 production resolver: given a UCITS ISIN, return the best available live price from
    the proven TV scanner endpoint (uk/scan first for USD; germany/scan fallback for EUR).
    Returns {sym, close, currency, exchange} or None. Never raises; respects the Sept freeze."""
    if not isin:
        return None
    for market, markets_val in [('uk', ['uk']), ('germany', ['germany'])]:
        try:
            payload = {
                'columns': ['name', 'isin', 'close', 'currency', 'exchange'],
                'filter':  [{'left': 'isin', 'operation': 'equal', 'right': isin}],
                'range': [0, 10], 'markets': markets_val,
            }
            r = requests.post(f'https://scanner.tradingview.com/{market}/scan',
                              json=payload,
                              headers={'User-Agent': UA, 'Content-Type': 'application/json'},
                              timeout=15)
            if r.status_code != 200:
                continue
            rows = (r.json() or {}).get('data') or []
            if not rows:
                continue
            cols = payload['columns']
            cands = []
            for row in rows:
                d = row.get('d') or []
                rec = {c: (d[i] if i < len(d) else None) for i, c in enumerate(cols)}
                if rec.get('isin') != isin:   # sanity: isin_returned must match
                    continue
                close = rec.get('close')
                if not isinstance(close, (int, float)):
                    continue
                ccy  = (rec.get('currency') or '').upper()
                exch = (rec.get('exchange') or '').upper()
                sort_key = (_ETF_CCY_PREF.get(ccy, 50), _ETF_EXCH_PREF.get(exch, 10))
                cands.append((sort_key, {'sym': row.get('s', ''), 'close': round(float(close), 4),
                                         'currency': ccy, 'exchange': exch}))
            if cands:
                cands.sort(key=lambda x: x[0])
                return cands[0][1]
        except Exception:
            continue
    return None
# ========================== end World ETF Engine Phase 6 production resolver ==========================

def probe_etf_performance_columns():
    """v1.139.0: LOGGING-ONLY probe -- tests whether scanner.tradingview.com's isin-filter scan (the
    SAME proven endpoint resolve_etf_live_price already uses to price every ETF live) also exposes
    YTD and 1-year performance columns. If it does, YTD/1Y for ALL Momentum-Watch funds (not just the
    12 stuck in specialty source-file sheets) can come from the SAME trusted live mechanism instead of
    a static file snapshot -- owner-requested, matching how the rest of the dashboard already sources
    return data. Tests 3 candidate TV screener field names (Perf.YTD / Perf.Y / Perf.3Y -- the natural
    extension of the SAME Perf.W/Perf.1M/Perf.3M/Perf.6M naming convention already proven live on the
    US/PSX stock scans elsewhere in this file) against 4 representative ISINs currently showing "—"
    for 1Y on the dashboard (Korea/Taiwan/Japan/Climate-Change categories) PLUS VanEck Semiconductor
    (a core Engine Recommendations catalog fund -- if this works, it's not just a Momentum-Watch fix,
    it upgrades the whole catalog). ISOLATED from resolve_etf_live_price's own columns list -- an
    unknown TV column 400s the WHOLE POST, so this never risks the live pricing that's already working.
    Each POST independently guarded; never raises; touches NO data/screening/scoring/IM3/TCE/the frozen
    ledger -> respects the Sept freeze."""
    if not ETF_PERF_PROBE:
        return
    log('  [ETF perf-column probe] testing Perf.YTD/Perf.Y/Perf.3Y on the proven isin-filter scan (logging-only):')
    ISINS = [
        ('IE00BHZRR030', 'Franklin FTSE Korea (currently — for 1Y)'),
        ('LU2928641757', 'Xtrackers MSCI Taiwan 1D (currently — for 1Y)'),
        ('LU1875395870', 'Xtrackers Nikkei 225 2D (currently — for 1Y)'),
        ('IE00BNC0MH93', 'UBS MSCI EM ex China SR (currently — for 1Y)'),
        ('IE00BMC38736', 'VanEck Semiconductor (core catalog fund)'),
    ]
    CAND_COLS = ['Perf.YTD', 'Perf.Y', 'Perf.3Y']
    base_cols = ['name', 'isin', 'close', 'currency', 'exchange']
    n_hit = 0
    n_req = 0
    for isin, label in ISINS:
        found = False
        for market in ['uk', 'germany']:
            if found:
                break
            n_req += 1
            try:
                payload = {
                    'columns': base_cols + CAND_COLS,
                    'filter':  [{'left': 'isin', 'operation': 'equal', 'right': isin}],
                    'range': [0, 10], 'markets': [market],
                }
                r = requests.post(f'https://scanner.tradingview.com/{market}/scan',
                                  json=payload,
                                  headers={'User-Agent': UA, 'Content-Type': 'application/json'},
                                  timeout=15)
                if r.status_code != 200:
                    log(f'    {label} [{market}]: HTTP {r.status_code} -- {r.text[:120]}')
                    continue
                rows = (r.json() or {}).get('data') or []
                if not rows:
                    log(f'    {label} [{market}]: 200 OK, 0 rows')
                    continue
                cols = payload['columns']
                # v1.140.0 fix: the v1.139.0 probe only inspected rows[0] (unsorted), which let a
                # Korea listing resolve to a DIFFERENT same-ISIN venue (LSE:FLRK) than the one
                # resolve_etf_live_price() actually prices with (LSE:FLXK) -- both legitimately
                # share the ISIN (multi-venue/multi-currency listings of one fund are normal on
                # LSE), the probe just picked the wrong one. Now inspects EVERY same-ISIN row TV
                # returns, logs each one, and applies the SAME _ETF_CCY_PREF/_ETF_EXCH_PREF sort
                # production already uses -- so the perf values checked here are guaranteed to be
                # from the SAME listing production would actually price and display.
                cands = []
                for row in rows:
                    d = row.get('d') or []
                    rec = {c: (d[i] if i < len(d) else None) for i, c in enumerate(cols)}
                    if rec.get('isin') != isin:
                        continue
                    ccy  = (rec.get('currency') or '').upper()
                    exch = (rec.get('exchange') or '').upper()
                    sort_key = (_ETF_CCY_PREF.get(ccy, 50), _ETF_EXCH_PREF.get(exch, 10))
                    cands.append((sort_key, row.get('s', ''), ccy, exch, rec))
                if not cands:
                    log(f'    {label} [{market}]: {len(rows)} row(s) returned, none matched the queried isin')
                    continue
                cands.sort(key=lambda x: x[0])
                if len(cands) > 1:
                    log(f'    {label} [{market}]: {len(cands)} listings share this ISIN:')
                    for _, sym, ccy, exch, rec in cands:
                        perf_vals = {c: rec.get(c) for c in CAND_COLS}
                        log(f'        {sym} ({ccy}/{exch}): close={rec.get("close")} -> {perf_vals}')
                _, sym, ccy, exch, rec = cands[0]  # production's own preference-sorted pick
                perf_vals = {c: rec.get(c) for c in CAND_COLS}
                nonnull = {k: v for k, v in perf_vals.items() if v is not None}
                log(f'    \u2713 {label} [{market}] PRODUCTION PICK: sym={sym} ({ccy}/{exch}) close={rec.get("close")} -> {perf_vals}')
                if nonnull:
                    n_hit += 1
                found = True
            except Exception as e:
                log(f'    {label} [{market}]: {type(e).__name__}: {str(e)[:60]}')
    log(f'  [ETF perf-column probe] {n_hit}/{len(ISINS)} funds returned at least one non-null candidate column ({n_req} requests). '
        f'NEXT: read the per-fund \u2192 dict above -- whichever of Perf.YTD/Perf.Y/Perf.3Y comes back populated '
        f'(and matches the fund\'s known real YTD as a sanity check) gets locked into resolve_etf_live_price\'s '
        f'production columns list, then ETF_PERF_PROBE flips False.')
# ========================== end ETF performance-column probe ==========================

def probe_tv_isin_filter():
    """LOGGING-ONLY (Phase 6c): tests whether the proven TV scanner endpoint accepts 'isin' as a FILTER
    field on European market scans. 3 representative UCITS ISINs × 2 markets (uk, germany).
    Each POST independently guarded. Never raises; respects the Sept freeze."""
    if not TV_ISIN_FILTER_PROBE:
        return
    log('  [TV isin-filter probe] isin as FILTER on European scans — 3 ISINs × uk + germany (logging-only):')
    ISINS = [
        ('IE00B5BMR087', 'iShares Core S&P 500 UCITS'),
        ('IE00B53SZB19', 'iShares Nasdaq 100 UCITS'),
        ('LU0659579147', 'Xtrackers MSCI Pakistan UCITS'),
    ]
    MARKETS = ['uk', 'germany']
    n_hit = 0
    n_req = 0
    for isin, label in ISINS:
        for market in MARKETS:
            n_req += 1
            try:
                payload = {
                    'columns': ['name', 'isin', 'close', 'currency', 'exchange', 'type'],
                    'filter': [{'left': 'isin', 'operation': 'equal', 'right': isin}],
                    'range': [0, 5], 'markets': [market],
                }
                r = requests.post(f'https://scanner.tradingview.com/{market}/scan',
                                  json=payload,
                                  headers={'User-Agent': UA, 'Content-Type': 'application/json'},
                                  timeout=20)
                ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
                if r.status_code != 200:
                    log(f'    {isin[:12]} / {market}: HTTP {r.status_code} {ct} body[:120]={r.text[:120]!r}')
                    continue
                rows = (r.json() or {}).get('data') or []
                if not rows:
                    log(f'    {isin[:12]} / {market}: 200 OK, 0 rows (filter accepted; ETF not indexed on {market})')
                    continue
                cols = payload['columns']
                for row in rows:
                    d = row.get('d') or []
                    rec = {c: (d[i] if i < len(d) else None) for i, c in enumerate(cols)}
                    isin_ret = rec.get('isin')
                    match_flag = '✓' if isin_ret == isin else '?'
                    log(f"    {match_flag} {isin[:12]} / {market}: sym={str(row.get('s'))!r} "
                        f"close={rec.get('close')} ccy={rec.get('currency')!r} "
                        f"exch={rec.get('exchange')!r} type={rec.get('type')!r} isin_returned={isin_ret!r}")
                    if isin_ret == isin:
                        n_hit += 1
            except Exception as e:
                log(f'    {isin[:12]} / {market}: FAIL ({type(e).__name__}: {str(e)[:80]})')
    log(f'    >> {n_hit} confirmed ISIN-match(es) across {n_req} probe(s) '
        f'(>0 → build ISIN-filter resolver on confirmed markets; '
        f'0 + no 400s → ETFs not indexed → pivot to issuer-page scraping; '
        f'all 400s → isin is display-only, not filterable → broad-scan-and-match instead)')
# ========================== end World ETF Engine Phase 6c isin-filter probe ==========================

def probe_tv_isin_column():
    """LOGGING-ONLY: ONE isolated throwaway POST to the ALREADY-PROVEN scanner.tradingview.com/america/scan (same
    request shape used everywhere else in this file) testing whether 'isin' parses as a valid, populated scan column.
    Sorts by market_cap_basic desc so the sample is famous large-caps (AAPL/MSFT/NVDA/...) -- letting a human
    eyeball whether the returned isin values look real (AAPL's known ISIN is US0378331005). A 400 here means TV's
    scan schema rejects 'isin' outright (the whole hypothesis is dead, pivot to issuer-page scraping instead).
    Never raises; respects the Sept freeze."""
    if not TV_ISIN_COLUMN_PROBE:
        return
    log('  [TV isin-column probe] scanner.tradingview.com/america/scan with columns incl. isin (logging-only):')
    try:
        payload = {
            'columns': ['name', 'isin', 'close', 'currency', 'exchange', 'description'],
            'filter': [{'left': 'type', 'operation': 'equal', 'right': 'stock'}],
            'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'},
            'range': [0, 8], 'markets': ['america'],
        }
        r = requests.post('https://scanner.tradingview.com/america/scan',
                          json=payload, headers={'User-Agent': UA, 'Content-Type': 'application/json'}, timeout=20)
        ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
        log(f'    - HTTP {r.status_code} {ct}')
        if r.status_code != 200:
            log(f'    - body[:200]={r.text[:200]!r}  -> isin is likely an INVALID column name (whole POST rejected)')
            return
        rows = (r.json() or {}).get('data') or []
        log(f'    - {len(rows)} row(s) returned')
        if not rows:
            log('    - 0 rows -> POST accepted but empty (inspect filter/markets, not the isin column itself)')
            return
        cols = payload['columns']
        n_isin = 0
        for row in rows:
            d = row.get('d') or []
            rec = dict(zip(cols, d)) if len(d) == len(cols) else {}
            isin_v = rec.get('isin')
            if isin_v:
                n_isin += 1
            log(f"      {str(rec.get('name'))[:8]:8} isin={isin_v!r} exch={rec.get('exchange')!r} "
                f"ccy={rec.get('currency')!r} close={rec.get('close')}")
        log(f'    >> isin column populated on {n_isin}/{len(rows)} rows '
            f'(if >0 and values look like real ISINs -> hypothesis CONFIRMED, build the ISIN-filtered resolver next; '
            f'if 0 -> column accepted but empty/unsupported, pivot to issuer-page scraping)')
    except Exception as e:
        log(f'    - FETCH FAILED ({type(e).__name__}: {str(e)[:100]})')
# ========================== end World ETF Engine Phase 6b isin-column probe ==========================
# representative spread: broad US / US-tech / country / the PSX special case / sector / materials / financials / theme / thematic / FR domicile / broad world
_ETF_PROBE_ISINS = [
    ('IE00B5BMR087', 'iShares Core S&P 500 (broad US)'),
    ('IE00B53SZB19', 'iShares Nasdaq 100 (US tech)'),
    ('IE00BHZRR030', 'Franklin FTSE Korea (country)'),
    ('LU0659579147', 'Xtrackers MSCI Pakistan Swap (PSX special)'),
    ('IE00BM67HK77', 'Xtrackers MSCI World Health Care (sector)'),
    ('IE00BDFBTQ78', 'VanEck S&P Global Mining (materials)'),
    ('IE00BD3V0B10', 'iShares S&P US Banks (financials)'),
    ('IE00BCHWNV48', 'Xtrackers MSCI USA Industrials (sector)'),
    ('IE00B1XNHC34', 'iShares Global Clean Energy (theme)'),
    ('IE0002PG6CA6', 'VanEck Rare Earth & Strategic Metals (thematic)'),
    ('FR0010524777', 'Amundi MSCI New Energy (FR domicile)'),
    ('IE00B4L5Y983', 'iShares Core MSCI World (broad world)'),
]


def probe_etf_isin_feeds():
    """LOGGING-ONLY (Phase 6): for a representative spread of catalog ISINs, prove on the runner — using ONLY the dashboard's
    existing plumbing (TradingView + stockanalysis, NO Yahoo/FMP) — which feed gives (a) a PRICE from an ISIN (TV symbol-search
    ISIN->EXCHANGE:SYMBOL, then the scanner.tradingview.com/symbol symbols-POST close) and (b) the FULL HOLDINGS from an ISIN
    (stockanalysis.com holdings API on the resolved symbol). Logs status/size + a parse hint per leg so each ISIN's price +
    holdings method is LOCKED next rev. Never raises; respects the Sept freeze."""
    if not ETF_FEED_PROBE:
        return
    log('  [ETF feed probe] ISIN -> live price (TradingView) + full holdings (stockanalysis); NO Yahoo/FMP (logging-only):')
    _hdr = {'User-Agent': UA, 'Accept': '*/*'}
    n_price = 0
    n_hold = 0
    for isin, label in _ETF_PROBE_ISINS:
        tvsym = None
        price = None
        diag = ''   # v1.127.1: raw evidence captured on ANY non-clean-resolve outcome (see changelog)
        # (A) TradingView symbol-search: ISIN -> EXCHANGE:SYMBOL (existing TV plumbing, search variant)
        try:
            u = f'https://symbol-search.tradingview.com/symbol_search/?text={isin}&hl=1&exchange=&lang=en&type=&domain=production'
            r = _retry_get(u, headers={'User-Agent': UA, 'Accept': 'application/json',
                                       'Referer': 'https://www.tradingview.com/'}, timeout=15)
            ct = (r.headers.get('Content-Type') or '').split(';')[0].strip()
            if r.status_code == 200:
                try:
                    arr = r.json()
                except Exception as je:
                    arr = []
                    diag = f'200/{ct} .json() FAILED ({type(je).__name__}); body[:160]={r.text[:160]!r}'
                if isinstance(arr, list) and arr:
                    top = arr[0] or {}
                    ex = (top.get('exchange') or top.get('exchange-listed') or '').strip()
                    sy = re.sub(r'<[^>]+>', '', str(top.get('symbol') or '')).strip()
                    if ex and sy:
                        tvsym = f'{ex}:{sy}'
                    elif sy:
                        tvsym = sy
                    else:
                        diag = f'200, {len(arr)} result(s), top keys={list(top.keys())[:8]} (no exchange+symbol field)'
                elif not diag:
                    ln = len(arr) if hasattr(arr, '__len__') else 'n/a'
                    diag = f'200/{ct} body parsed to {type(arr).__name__}(len={ln}); body[:160]={r.text[:160]!r}'
            else:
                diag = f'HTTP {r.status_code} {ct}; body[:160]={r.text[:160]!r}'
        except Exception as e:
            tvsym = f'searchFAIL({type(e).__name__})'
            diag = f'{type(e).__name__}: {str(e)[:120]}'
        # (B) TradingView symbols-POST close on the resolved symbol (the proven KSE100/RUT primitive)
        if tvsym and ':' in str(tvsym):
            try:
                r = requests.post('https://scanner.tradingview.com/symbol',
                                  json={'symbols': {'tickers': [tvsym]}, 'columns': ['close']},
                                  headers={'User-Agent': UA, 'Content-Type': 'application/json'}, timeout=15)
                if r.status_code == 200:
                    rows = ((r.json() or {}).get('data') or [])
                    if rows:
                        dv = (rows[0].get('d') or [])
                        if dv and dv[0] is not None:
                            price = round(float(dv[0]), 2)
                            n_price += 1
            except Exception as e:
                tvsym = f'{tvsym} postFAIL({type(e).__name__})'
        # (C) stockanalysis holdings on the resolved bare symbol (the existing ETF-overlap holdings source)
        nh = None
        hsrc = ''
        cands = []
        if tvsym and ':' in str(tvsym):
            cands.append(str(tvsym).split(':', 1)[1].strip())   # bare symbol from the TV resolution
        cands.append(isin)                                       # ISIN as a last attempt
        for q in [c for c in cands if c]:
            try:
                u = f'https://stockanalysis.com/api/symbol/e/{q}/holdings'
                r = _retry_get(u, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
                if r.status_code == 200:
                    j = r.json()
                    if isinstance(j, list):
                        rows = j
                    elif isinstance(j, dict):
                        dn = j.get('data')
                        rows = (dn.get('list') or dn.get('holdings') if isinstance(dn, dict) else dn) \
                               or j.get('holdings') or j.get('list') or []
                    else:
                        rows = []
                    parsed = _parse_holdings(rows) if rows else []
                    if parsed:
                        nh = len(parsed)
                        hsrc = f'stockanalysis({q})'
                        n_hold += 1
                        break
                    else:
                        hsrc = f'stockanalysis({q}) 200/0-rows'
                else:
                    hsrc = f'stockanalysis({q}) HTTP {r.status_code}'
            except Exception as e:
                hsrc = f'stockanalysis FAIL({type(e).__name__})'
        symtag = (tvsym or 'no-symbol')
        if not tvsym and diag:
            symtag = f'no-symbol :: {diag}'
        log(f'    - {isin} {label[:30]:30} | px {price if price is not None else "-"} [{symtag}]'
            f' | holdings {nh if nh is not None else "-"} [{hsrc}]')
    log(f'    >> TV price resolved {n_price}/{len(_ETF_PROBE_ISINS)} '
        f'· stockanalysis full-holdings resolved {n_hold}/{len(_ETF_PROBE_ISINS)} '
        f'(if low -> lock issuer-file holdings + a TV-symbol map next rev)')
# ========================== end World ETF Engine Phase 6 ISIN price+holdings probe ==========================



# ============================ US-bank IG2 FDIC BankFind probe (logging-only, runner-side) ============================
# US financials carved to the IM3 System-B bank model (COF/CCNE/MCBS/ISTR/OSBC/COFS/PLBC/CARE...) have NO IG2 input
# source, so they score on a reduced applicable denominator (40/48, 43/55...) while PSX banks get roe/roa/adr/NIM from
# SCS+manual. The FDIC BankFind API (banks.data.fdic.gov, free, no key) serves US call-report financials. Before
# building a fetch_us_bank_ig2() parser, PROBE on the runner (sandbox can't reach FDIC): (a) is banks.data.fdic.gov
# reachable? (b) does /api/institutions resolve a bank NAME -> CERT, and does it carry any ticker field (FDIC keys on
# CERT, not ticker -> the build will need a ticker->CERT map)? (c) does /api/financials return the IG2-relevant fields
# (ROA/ROE/NIMY/assets/deposits/equity/loans/efficiency/capital) for that CERT? Mirrors probe_pak_ca: each GET guarded,
# wrapped in main, never raises; touches NO data/screening/scoring/IM3/TCE/the frozen ledger -> respects the Sept freeze.
FDIC_PROBE = False   # resolution dump read + CERTs locked (v1.92.0); re-arm only to re-verify a CERT
def probe_fdic_bankfind():
    if not FDIC_PROBE:
        return
    log('  [FDIC bank-IG2 probe] banks.data.fdic.gov BankFind (logging-only):')
    _hdr = {'User-Agent': UA, 'Accept': 'application/json'}
    cert = None
    # (a)+(b) institutions: resolve a known US bank NAME -> CERT; surface any ticker-like field
    try:
        u = ('https://banks.data.fdic.gov/api/institutions'
             '?search=NAME:Capital%20One&filters=ACTIVE:1'
             '&fields=NAME,CERT,STALP,ASSET,STKEXSYM,STKEX&limit=5')
        r = requests.get(u, headers=_hdr, timeout=20)
        ct = (r.headers.get('Content-Type') or '').split(';')[0]
        log(f'    - institutions(search NAME:Capital One): HTTP {r.status_code} {ct} {len(r.content)//1024}kb')
        if r.status_code == 200:
            j = r.json(); rows = j.get('data') or []
            meta = j.get('meta') or {}
            log(f'    - returned {len(rows)} row(s); meta total={meta.get("total")}')
            for row in rows[:5]:
                dd = row.get('data') or row
                log(f"      NAME={str(dd.get('NAME'))[:34]} CERT={dd.get('CERT')} ST={dd.get('STALP')} "
                    f"ASSET={dd.get('ASSET')} STKEXSYM={dd.get('STKEXSYM')} STKEX={dd.get('STKEX')}")
            if rows:
                cert = (rows[0].get('data') or rows[0]).get('CERT')
    except Exception as e:
        log(f'    - institutions FETCH FAILED ({type(e).__name__}: {str(e)[:70]})')
    # (c) financials: dump ALL field keys + the IG2-relevant values for the resolved CERT (fallback: largest VA bank)
    try:
        if cert:
            flt = f'CERT:{cert}'
        else:
            flt = 'STALP:VA'
            log('    - no CERT resolved from (b); financials fallback uses filters=STALP:VA (largest-asset latest quarter)')
        u2 = ('https://banks.data.fdic.gov/api/financials'
              f'?filters={flt}&sort_by=REPDTE&sort_order=desc&limit=1')
        r2 = requests.get(u2, headers=_hdr, timeout=20)
        log(f'    - financials({flt}): HTTP {r2.status_code} {len(r2.content)//1024}kb')
        if r2.status_code == 200:
            rows = (r2.json().get('data') or [])
            if rows:
                dd = rows[0].get('data') or rows[0]
                keys = sorted(k for k in dd.keys() if k != 'ID')
                log(f'    - financials field count: {len(keys)}')
                # IG2-relevant fields we hope to map (profitability / margin / efficiency / capital / loans / deposits)
                for f in ['CERT', 'REPDTE', 'ROA', 'ROAPTX', 'ROE', 'NIMY', 'INTINCY', 'EEFFR',
                          'ASSET', 'DEP', 'DEPDOM', 'EQ', 'LNLSNET', 'LNLSDEPR', 'RBCT1J', 'RBC1RWAJ', 'NPERFV']:
                    if f in dd:
                        log(f"      {f} = {dd.get(f)}")
                log(f'    - ALL financials keys: {",".join(keys)[:1600]}')
            else:
                log('    - financials returned 0 rows')
    except Exception as e:
        log(f'    - financials FETCH FAILED ({type(e).__name__}: {str(e)[:70]})')
    # (d) ticker->CERT RESOLUTION DUMP for the actual US screen banks (the scanner's explosive recs carry name=ticker,
    # so the legal bank name can't be read here -> these queries are BEST-KNOWLEDGE, to be VERIFIED from this log then
    # LOCKED into a hardcoded ticker->CERT map next increment). Logs the top matches + the IG2 fields for the best match.
    _US_BANK_QUERIES = [
        ('COF',  'Capital One National Association'),
        ('CCNE', 'CNB Bank'),
        ('MCBS', 'Metro City Bank'),
        ('ISTR', 'Investar Bank'),
        ('OSBC', 'Old Second National Bank'),
        ('COFS', 'ChoiceOne Bank'),
        ('PLBC', 'Plumas Bank'),
        ('CARE', 'Carter Bank'),
    ]
    log('  [FDIC bank-IG2 probe] ticker->CERT resolution dump (verify each, then lock the map):')
    for _tk, _q in _US_BANK_QUERIES:
        try:
            from urllib.parse import quote as _qt
            ui = ('https://banks.data.fdic.gov/api/institutions'
                  f'?search=NAME:{_qt(_q)}&filters=ACTIVE:1'
                  '&fields=NAME,CERT,STALP,ASSET&sort_by=ASSET&sort_order=desc&limit=3')
            ri = requests.get(ui, headers=_hdr, timeout=20)
            if ri.status_code != 200:
                log(f"    - {_tk} (q='{_q}'): institutions HTTP {ri.status_code}")
                continue
            rows = (ri.json().get('data') or [])
            if not rows:
                log(f"    - {_tk} (q='{_q}'): NO MATCH")
                continue
            tops = [(r.get('data') or r) for r in rows[:3]]
            log(f"    - {_tk} (q='{_q}'): " + " | ".join(
                f"CERT={t.get('CERT')} {str(t.get('NAME'))[:30]} [{t.get('STALP')}] ASSET={t.get('ASSET')}"
                for t in tops))
            best = tops[0]; bc = best.get('CERT')
            if bc:
                uf = ('https://banks.data.fdic.gov/api/financials'
                      f'?filters=CERT:{bc}&sort_by=REPDTE&sort_order=desc&limit=1'
                      '&fields=CERT,REPDTE,ROE,ROA,ROAPTX,NIMY,LNLSDEPR,EEFFR,ASSET,NPERFV')
                rf = requests.get(uf, headers=_hdr, timeout=20)
                if rf.status_code == 200:
                    fr = (rf.json().get('data') or [])
                    if fr:
                        fd = fr[0].get('data') or fr[0]
                        log(f"        CERT {bc} financials: REPDTE={fd.get('REPDTE')} ROE={fd.get('ROE')} "
                            f"ROA={fd.get('ROA')} NIMY={fd.get('NIMY')} ADR(LNLSDEPR)={fd.get('LNLSDEPR')} "
                            f"EEFFR={fd.get('EEFFR')} NPERFV={fd.get('NPERFV')}")
        except Exception as e:
            log(f"    - {_tk} (q='{_q}'): FETCH FAILED ({type(e).__name__}: {str(e)[:50]})")
# ========================== end US-bank IG2 FDIC BankFind probe ==========================


# ============================ F3 Step 1: SBP ecodata RAW DUMP (logging-only, runner-side) ============================
# The Wave R verdict confirmed sbp.org.pk/ecodata is reachable + parseable (HTTP 200, 72 tables, carries 'reserves').
# Before writing fetch_sbp_reserves() we DUMP the runner's real table structure to LOCK which table + column carries
# the weekly FX-reserves figure, rather than guessing column positions from the sandbox (which cannot reach the page) -
# exactly the MTS/MSCI dump-then-lock pattern. Regex-only (no bs4/lxml dependency on the runner). Logs (a) a one-line
# map of EVERY <table> (index, rows x cols, first-row text) and (b) a detailed header+first-rows dump of any table whose
# text mentions reserves / liquid / foreign exchange. Gated ECODATA_DUMP_RAW; guarded; never raises; touches no data.
ECODATA_DUMP_RAW = False   # layout locked from the v1.85.0 dump (t30: "SBP's Reserves"/"Bank's Reserves"/"Total Reserves" + "As on <date>"); fetch_sbp_reserves() now reads it live. Re-arm only to re-inspect the page.
ECODATA_URL = 'https://www.sbp.org.pk/ecodata/index2.asp'
_ECODATA_KEYS = ('reserve', 'liquid', 'foreign exchange', 'forex', ' fx ', 'swap', 'with sbp', 'with bank', 'net reserves')


def _ecodata_strip(s):
    """Minimal tag-stripper for the dump (regex-only; logging context, robustness over elegance)."""
    s = re.sub(r'(?is)<br\s*/?>', ' ', s)
    s = re.sub(r'(?is)<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&')
    return ' '.join(s.split())


def probe_ecodata_dump():
    """F3 Step 1 - LOGGING-ONLY raw dump of sbp.org.pk/ecodata so the weekly FX-reserves table+column is LOCKED before
    fetch_sbp_reserves() is written. Runner-only (the sandbox cannot reach sbp.org.pk). Gated ECODATA_DUMP_RAW; never raises."""
    if not ECODATA_DUMP_RAW:
        return
    log('  [F3 ecodata dump] sbp.org.pk/ecodata table map (logging-only):')
    try:
        r = requests.get(ECODATA_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=20)
    except Exception as e:
        log(f'    FETCH FAILED ({type(e).__name__}: {str(e)[:60]})')
        return
    if r.status_code != 200 or not r.content:
        log(f'    HTTP {r.status_code} / empty body -> cannot dump')
        return
    try:
        html = r.content.decode('utf-8', 'ignore')
        tables = re.findall(r'(?is)<table\b.*?</table>', html)
        log(f'    content-type {r.headers.get("Content-Type","?")}, {len(r.content)//1024}kb, {len(tables)} <table> elements')
        # (a) one-line map of every table
        for i, t in enumerate(tables):
            rows = re.findall(r'(?is)<tr\b.*?</tr>', t)
            ncol = 0
            for rr in rows[:6]:
                c = len(re.findall(r'(?is)<t[dh]\b', rr))
                if c > ncol:
                    ncol = c
            first = _ecodata_strip(rows[0])[:90] if rows else ''
            log(f'    [t{i:02d}] {len(rows)}r x {ncol}c | "{first}"')
        # (b) detailed dump of reserves-candidate tables
        hits = 0
        for i, t in enumerate(tables):
            low = ' ' + _ecodata_strip(t).lower() + ' '
            if any(k in low for k in _ECODATA_KEYS):
                hits += 1
                rows = re.findall(r'(?is)<tr\b.*?</tr>', t)
                log(f'    --- CANDIDATE t{i:02d} ({len(rows)} rows) ---')
                for rj, rr in enumerate(rows[:8]):
                    cells = [_ecodata_strip(c)[:26] for c in re.findall(r'(?is)<t[dh]\b.*?</t[dh]>', rr)]
                    log(f'      t{i:02d}.r{rj}: {cells}')
        log(f'    [F3 ecodata dump] {hits} reserves-candidate table(s) dumped; lock the table+column next, then flip ECODATA_DUMP_RAW False')
    except Exception as e:
        log(f'    PARSE FAILED ({type(e).__name__}: {str(e)[:60]})')
# ========================== end F3 Step 1 ecodata dump ==========================


# ============================ F3 Step 2: live SBP FX reserves parser (locked from the v1.85.0 dump) ============================
# The v1.85.0 runner dump locked the layout: sbp.org.pk/ecodata carries a 2-column label/value panel -
#   'As on <date>' / "SBP's Reserves"  17,221.0 / "Bank's Reserves" 5,520.7 / 'Total Reserves' 22,741.7  (USD MILLIONS).
# fetch_sbp_reserves() finds that panel by the 'Total Reserves' LABEL (content-locked, NOT a positional table index, so a
# layout shift cannot silently mis-map), reads the three figures + the as-of date, and returns them in USD BILLIONS to match
# the existing sbp_reserves basis (the TE path divides mn/1000). Runner-only (sbp.org.pk is unreachable from the sandbox);
# guarded; returns None on any failure so the macro chain falls through to TE / last-good. Manual override still wins upstream.
def _eco_num(s):
    """Parse a reserves cell like '17,221.0' -> 17221.0; None if not numeric."""
    try:
        t = re.sub(r'[^0-9.\-]', '', s or '')
        return float(t) if t not in ('', '.', '-', '-.') else None
    except Exception:
        return None


def fetch_sbp_reserves():
    """F3 - live weekly SBP FX reserves from sbp.org.pk/ecodata (content-locked to the 'Total Reserves' panel).
    Returns {'sbp_bn','bank_bn','total_bn','as_of'} in USD BILLIONS, or None. Runner-only; guarded; never raises."""
    try:
        r = requests.get(ECODATA_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=20)
        if r.status_code != 200 or not r.content:
            return None
        html = r.content.decode('utf-8', 'ignore')
        panel = None
        for t in re.findall(r'(?is)<table\b.*?</table>', html):
            if 'total reserves' in _ecodata_strip(t).lower():
                panel = t
                break
        if panel is None:
            return None
        out = {'sbp_bn': None, 'bank_bn': None, 'total_bn': None, 'as_of': None}
        for rr in re.findall(r'(?is)<tr\b.*?</tr>', panel):
            cells = [_ecodata_strip(c) for c in re.findall(r'(?is)<t[dh]\b.*?</t[dh]>', rr)]
            if not cells:
                continue
            label = cells[0].lower().replace('&rsquo;', "'").replace('\u2019', "'")
            m = re.search(r'as on\s*[:\-]?\s*([0-9].+)', label)
            if m and out['as_of'] is None:
                out['as_of'] = m.group(1).strip().title()
            val = None
            for c in cells[1:]:
                vv = _eco_num(c)
                if vv is not None:
                    val = vv
                    break
            if val is None:
                continue
            bn = round(val / 1000.0, 2) if val > 1000 else round(val, 2)
            if 'reserve' in label and 'sbp' in label:
                out['sbp_bn'] = bn
            elif 'reserve' in label and 'bank' in label:
                out['bank_bn'] = bn
            elif 'total' in label and 'reserve' in label:
                out['total_bn'] = bn
        if out['sbp_bn'] is None and out['total_bn'] is None:
            return None
        return out
    except Exception:
        return None
# ========================== end F3 Step 2 SBP reserves parser ==========================


# ============================ F4: live monthly Pakistan CPI from PBS (SDMX XML) ============================
# pbs.gov.pk/cpi redirects to an IMF-SDMX XML feed carrying monthly index series. The HEADLINE all-items CPI is the
# series INDICATOR="PCPI_IX" (base 2015/2016=100); the other series (PCPI_CP_01_IX ...) are COICOP sub-groups. The dashboard
# pak_cpi is a YoY inflation %, so fetch_pbs_cpi() reads the headline index and computes YoY from the same month a year
# earlier - VALIDATED to reproduce the official print (Feb-2026 index 282.39 vs 263.95 a year before = 7.0%, the published
# figure). Returns {'yoy','index','mom','as_of'} or None. Replaces the dead JS-walled TheGlobalEconomy scrape. Runner-side
# fetch is fine from the sandbox-blocked PSX class only on the runner; guarded; never raises.
def fetch_pbs_cpi():
    """F4 - live monthly Pakistan headline CPI (YoY %) from the PBS SDMX XML feed. None on any failure."""
    try:
        r = requests.get('https://www.pbs.gov.pk/cpi', headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=20)
        if r.status_code != 200 or not r.content:
            return None
        xml = r.content.decode('utf-8', 'ignore')
        m = re.search(r'<Series\b[^>]*INDICATOR="PCPI_IX"[^>]*>(.*?)</Series>', xml, re.S)
        if not m:
            return None
        obs = re.findall(r'TIME_PERIOD="(\d{4}-\d{2})"\s+OBS_VALUE="([\d.]+)"', m.group(1))
        if len(obs) < 2:
            return None
        d = {p: float(v) for p, v in obs}
        periods = sorted(d.keys())
        latest = periods[-1]
        idx = d[latest]
        yr, mo = latest.split('-')
        prev_yr = f'{int(yr) - 1}-{mo}'
        yoy = round((idx / d[prev_yr] - 1) * 100, 2) if d.get(prev_yr) else None
        prev_m = periods[-2]
        mom = round((idx / d[prev_m] - 1) * 100, 2) if d.get(prev_m) else None
        return {'yoy': yoy, 'index': round(idx, 2), 'mom': mom, 'as_of': latest}
    except Exception:
        return None
# ========================== end F4 PBS CPI parser ==========================


# ============================ Wave PSX-R Phase-1: SCS Valuation Matrix overlay ============================
# DISPLAY/DATA-ONLY parser for the SCS "Pakistan Market Valuation Matrix" PDF (REP-033, weekly). Builds a
# per-ticker fundamental snapshot (price / EPS / latest+expected P/E / dividend yield / section metrics:
# mkt-cap, ROE, ROA, EBITDA margin, EV/EBITDA, P/B, bank NIM, 1/3/6/12m price perf) + which SCS "Top-40"
# screens each name appears in. Two downstream consumers (NEXT increment, not wired here): (a) an auto-
# refreshing seed for psx_watchlist.json = names in >=2 quality screens; (b) per-name valuation CONTEXT for
# the dashboard. NEVER touches screening / scoring / TCE -> respects the Sept freeze. pdfplumber lazy;
# weekly throttle; guarded; last-good carry. Probe (Phase-0) confirmed this PDF reachable+parseable.
SCS_VALMATRIX_INGEST = True
_VM_URL = 'https://www.scstrade.com/research/Research%20Reports/General/Valuation%20Matrix.pdf'

# (header substring -> (section_tag, metric_key|None, has_dividend_yield_column)). ORDER MATTERS: the
# bank-specific variants must be tested before the generic "lowest price to book" / "net interest margin".
_VM_SECTION_MAP = [
    ('lowest price to book value banks', ('low_pb_bank', 'pb', False)),
    ('net interest margin',              ('high_nim_bank', 'nim', False)),
    ('market capitalization',            ('mktcap', 'mkt_cap_bn', True)),
    ('one month price performance',      ('perf_1m', 'perf_1m', True)),
    ('three month price performance',    ('perf_3m', 'perf_3m', True)),
    ('six month price performance',      ('perf_6m', 'perf_6m', True)),
    ('twelve month price performance',   ('perf_12m', 'perf_12m', True)),
    ('12 month price performance',       ('perf_12m', 'perf_12m', True)),
    ('lowest expected p/e',              ('low_pe', None, True)),
    ('highest dividend yield',           ('high_dy', None, True)),
    ('lowest ev/ebitda',                 ('low_ev_ebitda', 'ev_ebitda', False)),
    ('highest return on equity',         ('high_roe', 'roe', False)),
    ('highest return on assets',         ('high_roa', 'roa', False)),
    ('lowest price to book value',       ('low_pb', 'pb', False)),
    ('highest ebitda margin',            ('high_ebitda_margin', 'ebitda_margin', False)),
]
# the four QUALITY/INCOME screens that seed the watchlist (a name in >=2 of these is a conviction candidate)
_VM_QUALITY_SCREENS = ('high_roe', 'high_roa', 'high_ebitda_margin', 'high_dy')


def _vm_num(t):
    try:
        return float(str(t).replace(',', '').replace('%', ''))
    except (ValueError, AttributeError):
        return None


def _vm_row(line):
    """PURE. Parse ONE Valuation-Matrix data row. Anchors on the EPS-basis period token (3M/6M/9M/12M):
    price/eps/annual_eps sit before it, latest_pe/expected_pe immediately after, then (per section) a
    dividend-yield %% token + the AVG-volume comma-number + a trailing section metric (always parts[-1]).
    Returns a dict or None (header/stat/blank lines)."""
    parts = line.split()
    if len(parts) < 8:
        return None
    sym = parts[0]
    if not re.fullmatch(r'[A-Z][A-Z0-9]{1,7}', sym):
        return None
    pidx = None
    for i in range(1, min(6, len(parts))):
        if re.fullmatch(r'\d{1,2}M', parts[i]):
            pidx = i
            break
    if pidx is None or pidx < 3:
        return None
    price = _vm_num(parts[1])
    eps = _vm_num(parts[pidx - 2])
    annual_eps = _vm_num(parts[pidx - 1])
    after = parts[pidx + 1:]
    latest_pe = _vm_num(after[0]) if len(after) > 0 else None
    expected_pe = _vm_num(after[1]) if len(after) > 1 else None
    dy = None
    for t in after[2:]:
        if t.endswith('%'):
            dy = _vm_num(t)
            break
    vol = None
    for t in after[2:]:
        if ',' in t:
            vol = _vm_num(t)
    if price is None or latest_pe is None:
        return None
    return {'_sym': sym, 'price': price, 'eps': eps, 'annual_eps': annual_eps,
            'eps_period': parts[pidx], 'latest_pe': latest_pe, 'expected_pe': expected_pe,
            'div_yield': dy, 'avg_volume': vol, '_last': _vm_num(parts[-1])}


def _parse_valuation_matrix(text):
    """PURE. Walk the linearised PDF text, tracking the current 'Top ...' section, and build
    {ticker:{price,eps,annual_eps,eps_period,latest_pe,expected_pe,div_yield,avg_volume, <metric>..., sections[]}}
    + {section_tag:[tickers]} + as_of. Common fields are taken from the first occurrence (identical across
    sections); div_yield only trusted in DY-bearing sections; the section metric is the row's last token."""
    by_ticker = {}
    sections = {}
    as_of = '?'
    m = re.search(r'Market Statistics\s+([A-Z][a-z]+ \d{1,2},? \d{4})', text)
    if m:
        as_of = m.group(1)
    cur = None  # (tag, metric_key, has_dy)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        # section header? (a 'Top ... Stocks/Banks' title line, never a data row)
        is_rowlike = bool(re.match(r'^[A-Z][A-Z0-9]{1,7}\s', line))
        if not is_rowlike and ('top ' in low or 'stocks' in low or 'banks' in low):
            for sub, spec in _VM_SECTION_MAP:
                if sub in low:
                    cur = spec
                    sections.setdefault(cur[0], [])
                    break
            continue
        rec = _vm_row(line)
        if not rec:
            continue
        sym = rec['_sym']
        ent = by_ticker.setdefault(sym, {'sections': []})
        for k in ('price', 'eps', 'annual_eps', 'eps_period', 'latest_pe', 'expected_pe', 'avg_volume'):
            if rec.get(k) is not None and ent.get(k) is None:
                ent[k] = rec[k]
        if cur:
            tag, metric_key, has_dy = cur
            if tag not in ent['sections']:
                ent['sections'].append(tag)
            if sym not in sections.setdefault(tag, []):
                sections[tag].append(sym)
            if has_dy and rec.get('div_yield') is not None and ent.get('div_yield') is None:
                ent['div_yield'] = rec['div_yield']
            if metric_key and rec.get('_last') is not None and ent.get(metric_key) is None:
                ent[metric_key] = rec['_last']
        elif rec.get('div_yield') is not None and ent.get('div_yield') is None:
            ent['div_yield'] = rec['div_yield']
    return by_ticker, sections, as_of


def fetch_psx_valuation_matrix():
    """Wave PSX-R Phase-1. Fetch + parse the SCS Valuation Matrix PDF -> structured overlay. Fully guarded:
    any failure -> {} and the scan proceeds. DISPLAY/DATA ONLY (no scoring effect; respects the freeze)."""
    if not SCS_VALMATRIX_INGEST:
        return {}
    try:
        import pdfplumber
    except Exception as e:
        log(f'  [Wave PSX-R valmatrix] pdfplumber unavailable ({e}) -> skipped')
        return {}
    import io
    try:
        r = requests.get(_VM_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=30)
        if r.status_code != 200 or r.content[:4] != b'%PDF':
            log(f'  [Wave PSX-R valmatrix] skip (HTTP {r.status_code}, not a PDF)')
            return {}
        text = ''
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or '') + '\n'
    except Exception as e:
        log(f'  [Wave PSX-R valmatrix] FETCH/PARSE FAILED ({type(e).__name__}: {str(e)[:50]})')
        return {}
    by_ticker, sections, as_of = _parse_valuation_matrix(text)
    if not by_ticker:
        log('  [Wave PSX-R valmatrix] 0 rows parsed -> overlay empty (layout shift? confirm raw text on the runner)')
        return {}
    # the auto-watchlist seed PREVIEW: names appearing in >=2 quality screens (logged now, wired NEXT increment)
    seed = sorted([t for t, v in by_ticker.items()
                   if sum(1 for s in v.get('sections', []) if s in _VM_QUALITY_SCREENS) >= 2])
    log(f'  [Wave PSX-R valmatrix] as-of {as_of}: {len(by_ticker)} tickers, {len(sections)} sections')
    log('    sections: ' + ', '.join(f'{k}={len(v)}' for k, v in sorted(sections.items())))
    log(f'    quality-seed (>=2 of ROE/ROA/EBITDA-margin/DY): {seed[:25]}'
        + (f' (+{len(seed) - 25} more)' if len(seed) > 25 else ''))
    # rev 2.5 RULE: filtered + ranked SUGGESTION list — SUGGEST only, NEVER auto-added to psx_watchlist.json.
    # Filter the >=2-quality-screen names down to liquid + non-mega + non-bank; the owner reviews & decides.
    _mega = set(PSX_MEGACAPS); _wl = set(PSX_WATCHLIST or []); _bank_secs = {'high_nim_bank', 'low_pb_bank'}
    suggested = []
    for sym, v in by_ticker.items():
        qs = [x for x in v.get('sections', []) if x in _VM_QUALITY_SCREENS]
        if len(qs) < 2 or sym in _mega:
            continue
        if any(x in _bank_secs for x in v.get('sections', [])) or _is_true_bank(None, None, sym):
            continue
        suggested.append({'ticker': sym, 'quality_count': len(qs), 'quality_screens': qs,
                          'pe': v.get('latest_pe'), 'expected_pe': v.get('expected_pe'),
                          'div_yield': v.get('div_yield'), 'roe': v.get('roe'), 'roa': v.get('roa'),
                          'ebitda_margin': v.get('ebitda_margin'), 'mkt_cap_bn': v.get('mkt_cap_bn'),
                          'avg_volume': v.get('avg_volume'), 'on_watchlist': sym in _wl,
                          'thin_volume': (v.get('avg_volume') or 0) < 50000})
    suggested.sort(key=lambda x: (-x['quality_count'], -(x['div_yield'] or 0)))
    log(f'    suggested (liquid, non-mega, non-bank; rank by quality): {[x["ticker"] for x in suggested][:20]}'
        + (f' (+{len(suggested) - 20} more)' if len(suggested) > 20 else ''))
    return {'by_ticker': by_ticker, 'sections': sections, 'as_of': as_of,
            'quality_seed': seed, 'suggested': suggested}
# ========================== end Wave PSX-R Phase-1 SCS Valuation Matrix overlay ==========================


# ============================ Wave PSX-R Phase-3: SCS MTS leverage gauge ============================
# DISPLAY/DATA-ONLY parser for the SCS "MTS Daily Report" PDF (REP-033, daily). The PRIMARY signal is the
# MARKET-WIDE MTS investment total = the margin-financing leverage gauge (rising = leverage building / froth,
# collapsing = forced de-risk). Market totals are LABEL-ANCHORED (robust to column order); the per-symbol Rs
# is the SUM of the per-symbol outstanding MTS Amount column (full rupees; the PDF has no separate summary box).
# Each row is '<S.No> <SYMBOL> <amount> <prev> <change%> [rate rate share share cat]'; the diagonal date-watermark
# (>=8-char runs) is stripped. FAILS SAFE: empty -> last-good. NEVER touches screening/scoring/TCE -> respects the freeze.
SCS_MTS_INGEST = True
MTS_DUMP_RAW = False  # root-caused (v1.74.0: two-table overwrite); re-arm True only to re-inspect the raw table
_MTS_URL = 'https://www.scstrade.com/research/Research%20Reports/General/MTS%20Report.pdf'

# (candidate label substrings -> market field). Matched case-insensitively on NON-symbol summary lines; the
# first numeric on the line is taken (the rate field takes the last numeric, since the rate sits after a label).
# A real MTS data row: "<S.No> <SYMBOL> <MTS Amount Rs> <MTS Amount prev Rs> <Change%> [wtd-rate wtd-rate-prev
# share% share%-prev Category]". The leading 5 fields are positional + robust; the trailing columns are sometimes
# corrupted by the diagonal date-watermark (>=8 identical chars), stripped before parsing. MTS Amount is FULL RUPEES.
_MTS_ROW_RE = re.compile(r'^\s*\d{1,4}\s+([A-Z][A-Z0-9]{1,7})\s+([\d,]+\.\d+)(?:\s+([\d,]+\.\d+)\s+(-?[\d.]+)%)?')


def _mts_num(t):
    try:
        return float(str(t).replace(',', '').replace('%', '').replace('Rs', '').strip())
    except (ValueError, AttributeError):
        return None


def _parse_mts(text):
    """PURE. Parse the SCS MTS Daily Report. The PDF stacks TWO tables keyed by the SAME symbols: 'MTS Net Open
    MTS Amount' (Rs financing) THEN 'MTS Net Open MTS Volume' (shares). We ingest ONLY the Amount table (the
    Volume table would otherwise overwrite by_ticker = the v1.73.0 bug). Each data row is '<S.No> <SYMBOL>
    <amount Rs> <prev Rs> <change%> [rate rate share share category]'; the report's own 'Total Amount <today>
    <prev>' row is the authoritative market leverage total. Watermark runs stripped. Returns a dict (never raises)."""
    as_of = '?'
    for line in text.splitlines():
        mm = re.search(r'([A-Z][a-z]+ \d{1,2},?\s*\d{4})', line)
        if mm:
            if 'report' in line.lower():
                as_of = mm.group(1)
                break
            if as_of == '?':
                as_of = mm.group(1)
    by_ticker = {}
    diag = []
    active = False        # True only inside the MTS Amount table
    total_row = None      # the report's own 'Total Amount <today> <prev>'
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) <= 3:
            continue
        low = line.lower()
        if 'net open mts amount' in low:
            active = True
            continue
        if 'net open mts volume' in low or re.search(r'symbol\s+mts\s+volume', low):
            active = False   # the Volume table begins -> stop ingesting; keep the Amount data already gathered
            continue
        if not active:
            continue
        mt = re.match(r'^\s*Total Amount\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)', line)
        if mt:
            total_row = (_mts_num(mt.group(1)), _mts_num(mt.group(2)))
            if len(diag) < 120:
                diag.append(line)
            continue
        m = _MTS_ROW_RE.match(line)
        if not m:
            if len(diag) < 120 and not re.fullmatch(r'(.)\1{6,}', line):
                diag.append(line)
            continue
        sym = m.group(1)
        amt = _mts_num(m.group(2))
        if amt is None:
            continue
        amt_prev = _mts_num(m.group(3)) if m.group(3) else None
        chg = _mts_num(m.group(4)) if m.group(4) else None
        rest = re.sub(r'(.)\1{7,}', ' ', line[m.end():])  # strip watermark runs
        toks = rest.split()
        nums = [(_mts_num(t) if t != '-' else None) for t in toks if (t == '-' or _mts_num(t) is not None)]
        cat = next((t for t in toks if re.fullmatch(r'[A-Z]', t)), None)
        by_ticker[sym] = {
            'mts_amount_mn': round(amt / 1e6, 3),
            'mts_amount_prev_mn': round(amt_prev / 1e6, 3) if amt_prev else None,
            'change_pct': chg,
            'rate': nums[0] if len(nums) > 0 else None,
            'rate_prev': nums[1] if len(nums) > 1 else None,
            'share_pct': nums[2] if len(nums) > 2 else None,
            'share_pct_prev': nums[3] if len(nums) > 3 else None,
            'category': cat,
        }
        if len(diag) < 120:
            diag.append(line)
    market = {}
    if by_ticker:
        sum_tot = sum(v['mts_amount_mn'] for v in by_ticker.values())
        if total_row and total_row[0]:
            tot = round(total_row[0] / 1e6, 1)
            tot_prev = round(total_row[1] / 1e6, 1) if total_row[1] else None
        else:
            tot = round(sum_tot, 1)
            tot_prev = None
        rated = [(v['rate'], v['mts_amount_mn']) for v in by_ticker.values() if v.get('rate')]
        wavg = round(sum(r * a for r, a in rated) / sum(a for _, a in rated), 2) if rated else None
        market = {'total_mn': tot, 'total_prev_mn': tot_prev,
                  'net_change_mn': round(tot - tot_prev, 1) if tot_prev else None,
                  'change_pct': round((tot - tot_prev) / tot_prev * 100, 2) if tot_prev else None,
                  'wavg_rate': wavg, 'n_symbols': len(by_ticker), 'sum_check_mn': round(sum_tot, 1)}
    top_financed = sorted(
        [{'ticker': k, 'mts_amount_mn': v['mts_amount_mn'], 'share_pct': v.get('share_pct'),
          'change_pct': v.get('change_pct')} for k, v in by_ticker.items()],
        key=lambda x: -x['mts_amount_mn'])[:15]
    return {'as_of': as_of, 'market': market, 'by_ticker': by_ticker, 'top_financed': top_financed, '_diag': diag}


def fetch_psx_mts():
    """Wave PSX-R Phase-3. Fetch + parse the SCS MTS Daily Report PDF -> leverage-gauge overlay. Fully guarded:
    any failure -> {} and the scan proceeds. DISPLAY/DATA ONLY (no scoring effect; respects the freeze)."""
    if not SCS_MTS_INGEST:
        return {}
    try:
        import pdfplumber
    except Exception as e:
        log(f'  [Wave PSX-R MTS] pdfplumber unavailable ({e}) -> skipped')
        return {}
    import io
    try:
        r = requests.get(_MTS_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=30)
        if r.status_code != 200 or r.content[:4] != b'%PDF':
            log(f'  [Wave PSX-R MTS] skip (HTTP {r.status_code}, not a PDF)')
            return {}
        text = ''
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or '') + '\n'
    except Exception as e:
        log(f'  [Wave PSX-R MTS] FETCH/PARSE FAILED ({type(e).__name__}: {str(e)[:50]})')
        return {}
    parsed = _parse_mts(text)
    if MTS_DUMP_RAW:
        log('  [Wave PSX-R MTS] RAW table text (first 120 substantive lines, watermark-run lines filtered):')
        for ln in parsed.get('_diag', []):
            log('      | ' + ln[:220])
    parsed.pop('_diag', None)
    if not parsed.get('by_ticker'):
        log('  [Wave PSX-R MTS] 0 rows parsed -> empty (re-arm MTS_DUMP_RAW to inspect the raw table on the runner)')
        return {}
    _mk = parsed["market"]
    log(f'  [Wave PSX-R MTS] as-of {parsed["as_of"]}: total Rs {_mk.get("total_mn")}mn across {_mk.get("n_symbols")} symbols '
        f'(chg {_mk.get("change_pct")}%, wavg rate {_mk.get("wavg_rate")}%); top: {[t["ticker"] for t in parsed["top_financed"][:8]]}')
    _samp = list(parsed["by_ticker"].items())[:15]
    log('  [Wave PSX-R MTS] DIAG parsed mts_amount_mn (first 15): ' + ', '.join(f'{k}={v["mts_amount_mn"]}' for k, v in _samp))
    # v1.112.0 (F5): the MTS "daily" report has been seen frozen months behind the run date (e.g.
    # as-of Feb-6 on a Jun-24 run) -> the leverage gauge would read as current when it is not. Surface
    # staleness HONESTLY (no fabricated freshness): flag it; the dashboard can render it as stale.
    _age = _staleness_days(parsed.get("as_of"))
    if _age is not None:
        parsed["as_of_age_days"] = _age
        parsed["stale"] = bool(_age > MTS_STALE_DAYS)
        if parsed["stale"]:
            parsed["stale_days"] = _age
            log(f'  [Wave PSX-R MTS] STALE: report as-of {parsed.get("as_of")} is {_age}d old '
                f'(> {MTS_STALE_DAYS}d) — leverage gauge may not be current; flagged stale in data.json')
    return parsed
# ========================== end Wave PSX-R Phase-3 SCS MTS leverage gauge ==========================


# ========================== Wave PSX-R Phase-4: SCS MSCI Provisional Indexes (index catalyst) ==========================
# The SCS "MSCI Provisional Indexes" report projects which PSX names MSCI will ADD to / DELETE from its Pakistan
# indexes at the upcoming review (semi-annual May/Nov, quarterly Feb/Aug). A name ADDED = forced passive INFLOW from
# index-tracking funds (bullish catalyst); DELETED = forced passive OUTFLOW (bearish). DISPLAY/DATA ONLY: never gates
# or scores a name, never touches the Sept TCE freeze. The diagonal date-watermark blocks a remote read, so the parser
# is tolerant + DUMP-ARMED (MSCI_DUMP_RAW) and the exact table columns are locked from the first runner dump.
SCS_MSCI_INGEST = False  # v1.76.0: SHELVED — the SCS MSCI PDF is a frozen 2016/2017 snapshot (calc date 19-Apr-2016), company names not tickers, no live add/delete section -> useless as a current index catalyst; the real live source is MSCI's own semi-annual review announcements (separate future build). Code kept, gated off.
MSCI_DUMP_RAW = False  # source shelved (stale 2016 file); dump already read
_MSCI_URL = 'https://www.scstrade.com/research/Research%20Reports/General/MSCI-Provisional-Indexes.pdf'

# ticker-like tokens (uppercase 2-8 alnum) minus the report's own vocabulary, so section/header words are not mistaken
# for tickers. Company NAMES (if the report uses them instead of symbols) survive in _diag for the lock pass.
_MSCI_TICKER_RE = re.compile(r'\b([A-Z][A-Z0-9]{1,7})\b')
_MSCI_NOISE = {'MSCI','PSX','SCS','PKR','USD','PROVISIONAL','INDEX','INDEXES','INDICES','LARGE','MID','SMALL','CAP',
               'STANDARD','PAKISTAN','SECURITIES','SECURITY','ADDED','DELETED','ADDITION','ADDITIONS','DELETION',
               'DELETIONS','INCLUSION','EXCLUSION','SUMMARY','COUNTRY','REGION','REVIEW','LIST','PUBLIC','NB','OF',
               'THE','AND','REPORT','TOTAL','SEMI','ANNUAL','QUARTERLY','RESEARCH','GENERAL','LTD','LIMITED','CO',
               'RS','MN','BN','NA','TBD','EM','IMI','ACWI','FF','MCAP','WEIGHT','NO','SR','NAME','SYMBOL','CHANGES'}


def _parse_msci(text):
    """PURE. Tolerant parse of the SCS MSCI Provisional Indexes report. Tracks the active section
    (ADDITION / DELETION / CONSTITUENT) by header keywords, extracts PSX-ticker-like tokens (noise words filtered),
    and records the size-segment tier (Large/Mid/Small Cap, Standard) when a line names one. Watermark runs stripped.
    Returns a dict (never raises). Column layout is locked from the first runner dump (MSCI_DUMP_RAW)."""
    as_of = '?'; review_label = '?'
    for line in text.splitlines():
        low = line.lower()
        mm = re.search(r'([A-Z][a-z]+ \d{1,2},?\s*\d{4})', line)
        if mm and as_of == '?':
            as_of = mm.group(1)
        rm = re.search(r'((?:semi[- ]?annual|quarterly|may|november|february|august)[^\n]{0,28}(?:review|index review))', low)
        if rm and review_label == '?':
            review_label = rm.group(1).strip()[:40]
    added = []; deleted = []; constituents = {}; by_ticker = {}; diag = []
    section = None   # 'add' | 'del' | 'con'
    tier = None
    for raw in text.splitlines():
        line = re.sub(r'(.)\1{7,}', ' ', raw).strip()   # strip diagonal watermark runs
        if len(line) <= 2:
            continue
        low = line.lower()
        # section header (set, do NOT skip -> a header that also inlines tickers is still parsed)
        if re.search(r'\b(addition|additions|inclusion|inclusions)\b', low) or 'securities added' in low:
            section = 'add'
        elif re.search(r'\b(deletion|deletions|exclusion|exclusions|removal|removals)\b', low) or 'securities deleted' in low:
            section = 'del'
        elif re.search(r'\b(constituent|constituents|index member|current member|standard index)\b', low):
            section = 'con'
        # size-segment tier tag carried forward until the next tier line
        if 'large cap' in low or 'large-cap' in low: tier = 'Large Cap'
        elif 'mid cap' in low or 'mid-cap' in low: tier = 'Mid Cap'
        elif 'small cap' in low or 'small-cap' in low: tier = 'Small Cap'
        elif 'standard' in low: tier = 'Standard'
        toks = [t for t in _MSCI_TICKER_RE.findall(line) if t not in _MSCI_NOISE and not t.isdigit()]
        if toks:
            for t in toks:
                rec = by_ticker.setdefault(t, {'tier': None, 'status': None})
                if tier and not rec['tier']:
                    rec['tier'] = tier
                if section == 'add':
                    rec['status'] = 'ADDED'; added.append(t)
                elif section == 'del':
                    rec['status'] = 'DELETED'; deleted.append(t)
                elif section == 'con' and not rec['status']:
                    rec['status'] = 'MEMBER'
                if tier:
                    constituents.setdefault(tier, [])
                    if t not in constituents[tier]:
                        constituents[tier].append(t)
            if len(diag) < 120:
                diag.append((section or '?') + ' | ' + line[:200])
        elif len(diag) < 120 and not re.fullmatch(r'(.)\1{4,}', line):
            diag.append('... ' + line[:200])
    added = sorted(set(added)); deleted = sorted(set(deleted))
    return {'as_of': as_of, 'review_label': review_label, 'added': added, 'deleted': deleted,
            'constituents': constituents, 'by_ticker': by_ticker,
            'n_added': len(added), 'n_deleted': len(deleted), 'n_constituents': len(by_ticker), '_diag': diag}


class _MsciShelved(Exception):
    pass


def fetch_psx_msci():
    """Wave PSX-R Phase-4. Fetch + parse the SCS MSCI Provisional Indexes PDF -> index in/exclusion catalyst overlay.
    Fully guarded: any failure -> {} and the scan proceeds. DISPLAY/DATA ONLY (no scoring effect; respects the freeze)."""
    if not SCS_MSCI_INGEST:
        return {}
    try:
        import pdfplumber
    except Exception as e:
        log(f'  [Wave PSX-R MSCI] pdfplumber unavailable ({e}) -> skipped')
        return {}
    import io
    try:
        r = requests.get(_MSCI_URL, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=30)
        if r.status_code != 200 or r.content[:4] != b'%PDF':
            log(f'  [Wave PSX-R MSCI] skip (HTTP {r.status_code}, not a PDF)')
            return {}
        text = ''
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or '') + '\n'
    except Exception as e:
        log(f'  [Wave PSX-R MSCI] FETCH/PARSE FAILED ({type(e).__name__}: {str(e)[:50]})')
        return {}
    parsed = _parse_msci(text)
    if MSCI_DUMP_RAW:
        log('  [Wave PSX-R MSCI] RAW text (first 120 substantive lines, watermark-run lines filtered):')
        for ln in parsed.get('_diag', []):
            log('      | ' + ln[:220])
    parsed.pop('_diag', None)
    if not (parsed.get('by_ticker') or parsed.get('added') or parsed.get('deleted') or parsed.get('constituents')):
        log('  [Wave PSX-R MSCI] 0 rows parsed -> empty (re-arm MSCI_DUMP_RAW to inspect the raw text on the runner)')
        return {}
    log(f'  [Wave PSX-R MSCI] as-of {parsed["as_of"]} ({parsed["review_label"]}): '
        f'{parsed["n_added"]} added {parsed["added"][:8]}, {parsed["n_deleted"]} deleted {parsed["deleted"][:8]}, '
        f'{parsed["n_constituents"]} names across {len(parsed["constituents"])} tiers')
    return parsed
# ========================== end Wave PSX-R Phase-4 SCS MSCI Provisional Indexes ==========================




# ============================ Wave Q Phase-1: bank-data overlays (SCS snapshot + KPMG sector) ============================
# Two ADDITIVE, DISPLAY/CONTEXT overlays — neither writes the audited IG2 scoring series (that stays manual /
# the annual-report PDF parser, since SCS snapshot is the latest filed year and would drift vs the 2019-24 series).
#   fetch_bank_snapshot  -> SCS Trade per-bank CURRENT-YEAR fields (server-rendered, runner-confirmed) for the
#                           dashboard + a data-quality cross-check vs the manual IG2 ADR. Throttled 24h.
#   fetch_bank_sector_kpmg -> KPMG Banking Perspective SECTOR aggregates (profit/asset/deposit/NPL growth, ECL
#                           coverage, macro backdrop) for a sector-EVALUATION read. NEVER a per-bank input. 30d.
# Both fully guarded, last-good carried, never break the run.
BANK_SNAPSHOT_INGEST = True
BANK_SECTOR_KPMG     = True

# (output key, SCS snapshot label) — value captured is the first Rs./%/x number after the label (tags stripped).
# Fails SAFE: if SCS groups all-labels-then-all-values, the window holds no number -> None (never a wrong value).
_BANK_SNAP_FIELDS = [
    ('eps_annual',    'Last Annual EPS'),
    ('roe',           'Return On Equity'),
    ('roa',           'Return On Assets'),
    ('book_value_ps', 'Book Value Per Share'),
    ('equity_assets', 'Equity To Assets Ratio'),
    ('adr',           'Advance Deposite Ratios'),
    ('cash_deposits', 'Cash To Deposits Ratio'),
    ('pb',            'Price To Book Value'),
    ('pe',            'Price To Earning P/E'),
    ('cfps',          'Cash Flow Per Share'),
]


def _scs_field(html, label):
    """First Rs./%/x number after `label` in the raw HTML (tags stripped, 300-char window). float|None."""
    low = html.lower(); i = low.find(label.lower())
    if i < 0:
        return None
    seg = re.sub(r'<[^>]+>', ' ', html[i + len(label): i + len(label) + 300])
    # values carry a unit (Rs. prefix, or %/x suffix); the period text ("Upto 2025 4Q") has none -> skipped,
    # and a missing/grouped value fails SAFE to None (never returns the year/quarter as a value).
    m = re.search(r'rs\.?\s*(-?[\d,]+(?:\.\d+)?)|(-?[\d,]+(?:\.\d+)?)\s*(%|x)(?![a-z])', seg, re.I)
    if not m:
        return None
    num = m.group(1) or m.group(2)
    try:
        return float(num.replace(',', ''))
    except Exception:
        return None


# SCS snapshot series -> clean keys. Validated vs AKBL knowns: 'Ret On Equity'=15.03 (=known ROE), 'Ret On
# Assets'=0.79 (=known ROA), 'ADR'=35.96 (~known 35.6). The FULL-name 'Return On Equity' (31.78/52.09) is a
# different basis -> intentionally NOT mapped. Price/index series (n=120) and 0.0 (not-populated) are dropped.
_SNAP_PARSER_VER = 3   # bump when fetch_bank_snapshot's output format changes -> forces one re-fetch past the throttle
_SCS_METRIC_MAP = {
    'ret on equity': 'roe', 'ret on assets': 'roa', 'ret on ce': 'roce',
    'adr': 'adr', 'cash to dpr': 'cash_deposits', 'equity to ad': 'equity_advances',
    'cash per share': 'cash_per_share', 'net profit margin': 'net_margin', 'gross profit margin': 'gross_margin',
}


def _scs_highcharts_series(html):
    """Parse the SCS snapshot's embedded Highcharts series ('<Name>',animation:{...},data:[..]) ->
    {name: [floats]} (multi-year, oldest->newest as charted). The snapshot's metric HISTORY lives in these
    JS arrays in the raw HTML (the rendered ratio tables are client-side only). Returns {} if none found."""
    out = {}
    for m in re.finditer(r"'([^']{2,40})'\s*,\s*animation\s*:\s*\{[^}]*\}\s*,\s*data\s*:\s*\[([-\d.,\s]+)\]", html):
        name = m.group(1).strip()
        try:
            vals = [float(x) for x in m.group(2).split(',') if x.strip()]
        except Exception:
            continue
        if vals and name not in out:
            out[name] = vals
    return out


def fetch_bank_snapshot(symbols):
    """SCS Trade per-bank snapshot (DISPLAY/CONTEXT; NOT an IG2 series writer). The runner's raw HTML carries
    each charted metric as a Highcharts multi-year data array (the rendered ratio tables are client-side only),
    so this captures data['bank_snapshot'][ticker] = {series:{name:[..oldest->newest..]}, as_of} as RAW series +
    logs a metric map and validates the array basis/order against AKBL's known ROE (15.03%) before any field is
    trusted. Throttled 24h; last-good carried; fully guarded; never breaks the run."""
    if not BANK_SNAPSHOT_INGEST:
        return {}
    prev = (EXISTING.get('bank_snapshot') or {})
    has_cached = any(k not in ('_fetched_utc', '_parser_ver') for k in prev)   # real banks present?
    same_parser = prev.get('_parser_ver') == _SNAP_PARSER_VER                  # stale-format cache -> re-map once
    last = prev.get('_fetched_utc')
    if last and has_cached and same_parser:
        try:
            if (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(last).replace('Z', ''))).total_seconds() < 24 * 3600:
                log(f'  [Wave Q snapshot] skipped (<24h since {last}) — carrying last-good ({max(len(prev)-1,0)} banks)')
                return prev
        except Exception:
            pass
    out = {'_fetched_utc': dt.datetime.utcnow().isoformat(), '_parser_ver': _SNAP_PARSER_VER}
    dumped = 0
    for sym in symbols:
        try:
            r = requests.get(f'https://www.scstrade.com/stockscreening/SS_CompanySnapShot.aspx?symbol={sym}',
                             headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=15)
            if r.status_code != 200 or not r.text:
                continue
            series = _scs_highcharts_series(r.text)
            if not series:
                continue
            rec = {'series': {}, 'as_of': 'latest'}
            for nm, vals in series.items():
                key = _SCS_METRIC_MAP.get(nm.lower().strip())
                if not key or not vals or len(vals) > 6:    # drop price/index (n=120) + unmapped names
                    continue
                if vals[-1] == 0.0:                          # 0.0 = metric not populated for this bank (N/A)
                    continue
                rec[key] = vals[-1]
                rec['series'][key] = vals
            if len(rec) > 2:                                 # at least one real ratio captured
                out[sym] = rec
            if dumped < 2:
                raw = ', '.join(f'{k}(n={len(v)},last={v[-1]})' for k, v in list(series.items())[:12])
                mapped = ', '.join(f'{k}={rec[k]}' for k in rec if k not in ('series', 'as_of'))
                log(f'    [Wave Q snapshot map] {sym} raw: {raw}')
                log(f'    [Wave Q snapshot mapped] {sym}: {mapped}')
                dumped += 1
            if sym == 'AKBL' and rec.get('roe') is not None:
                ok = abs(rec['roe'] - 15.03) < 1.0
                log(f'    [Wave Q snapshot validate] AKBL roe(mapped)={rec["roe"]} vs known 15.03 -> '
                    + ('MATCH (locked)' if ok else 'MISMATCH'))
            time.sleep(1.2)
        except Exception as e:
            log(f'    [Wave Q snapshot] {sym} skipped ({type(e).__name__})')
    n = len(out) - 2   # minus _fetched_utc + _parser_ver
    if n <= 0:
        log('  [Wave Q snapshot] 0 banks parsed — keeping prior cache, no throttle stamp (will retry next run)')
        return prev
    log(f'  [Wave Q snapshot] SCS Highcharts series captured for {n}/{len(symbols)} banks (RAW; see map/validate lines)')
    return out


def write_bank_ig2_overrides(data):
    """A (SCS -> IG2 fallback): derive roe/adr/roa-trend overrides from the live SCS snapshot and
    write bank_ig2_overrides.json for im3_score to FILL-MISSING into the IG2 inputs. im3_score never
    overwrites a curated value already in bank_ig2_inputs.json, so the nine full-data workbook banks
    are untouched; this only lifts partial banks (no audited equity/ADR series, e.g. BOP/AKBL/BIPL)
    off the reduced denominator. roe/adr are stored as FRACTIONS (SCS percent / 100); roa-trend is
    avg(last 3) / avg(last 5) from the 5-year ROA series (the same 3y-vs-5y basis score_bank_ig2 uses)."""
    snap = (data.get('bank_snapshot') or {})
    out = {}
    for t, sdat in snap.items():
        if t.startswith('_') or not isinstance(sdat, dict):
            continue
        rec = {}
        roe = sdat.get('roe'); adr = sdat.get('adr')
        if isinstance(roe, (int, float)): rec['roe_scs'] = round(roe / 100.0, 4)
        if isinstance(adr, (int, float)): rec['adr_scs'] = round(adr / 100.0, 4)
        roa_ser = ((sdat.get('series') or {}).get('roa')) or []
        if isinstance(roa_ser, list) and len(roa_ser) >= 4:
            last3, last5 = roa_ser[-3:], roa_ser[-5:]
            a = sum(last3) / len(last3); b = sum(last5) / len(last5)
            if b: rec['roa_trend_scs'] = round(a / b, 4)
        rec = {k: v for k, v in rec.items() if v is not None}
        if rec:
            rec['_src'] = 'SCS ' + str(sdat.get('as_of') or 'latest')
            out[t] = rec
    try:
        json.dump(out, open('bank_ig2_overrides.json', 'w'), indent=2)
        log(f'  [Wave Q->IG2] SCS fallback overrides written for {len(out)} bank(s): {sorted(out)} '
            f'(im3_score fills these into missing roe/adr/roa-trend only)')
    except Exception as e:
        log(f'  [Wave Q->IG2] override write skipped ({e})')

# ===================== Group-D: US-bank IG2 inputs from FDIC call reports =====================
# LOCKED + verified from the v1.91.0 ticker->CERT resolution dump (CCNE corrected off the [0]
# 'Dime Commercial Bank' asset-sorted false match to the real 'CNB Bank' PA; each row eyeballed by
# name+state). FDIC keys on CERT, not ticker, and the scanner's explosive recs carry name=ticker, so
# this map is the bridge.
_US_BANK_CERTS = {
    'COF': 4297,    # Capital One, National Association (VA)
    'CCNE': 13876,  # CNB Bank (PA)            <- NOT 6976 (Dime Commercial, NY) nor 17491 (PlainsCapital, TX)
    'MCBS': 58181,  # Metro City Bank (GA)
    'ISTR': 58316,  # Investar Bank, N.A. (LA)
    'OSBC': 3603,   # Old Second National Bank (IL)
    'COFS': 1014,   # ChoiceOne Bank (MI)
    'PLBC': 23275,  # Plumas Bank (CA)
    'CARE': 58596,  # Carter Bank & Trust (VA)
}
def fetch_us_bank_ig2(data):
    """Pull each US screen bank's FDIC ANNUAL call reports (FY2019-2024, per the LOCKED ticker->CERT
    map) and map them to the IG2 24-ratio input series, then MERGE into bank_ig2_overrides.json
    (alongside the PSX SCS entries write_bank_ig2_overrides just wrote — US tickers are distinct, so
    a pure add). im3_score v2.16.0 ALREADY routes a US (non-PSX) bank with IG2 inputs to
    score_bank_ig2(calib='us') and fill-merges this file, so NO scorer edit is needed — this single
    scanner feed completes the feature. Anchored on the Dec-31 (annual) reports so a distorted latest
    quarter (e.g. CARE Q1-2026 ROE 77.85 from a one-off item) is never used. HONEST GAP: FDIC carries
    no cash-flow statement or share count, so eps_trend / cfo_trend / ccfo_cpat / net_change_cash read
    NA, and casa has no clean FDIC proxy -> left NA; all NA ratios are excluded from the denominator,
    so US banks score on ~19-20 of the 24 ratios (far richer than the prior thin System-B subset).
    No throttle: write_bank_ig2_overrides overwrites the file PSX-only every run, so the US entries
    must be re-merged each run (8 light GETs). DATA-only (IM3 bank input); respects the Sept freeze."""
    _hdr = {'User-Agent': 'Mozilla/5.0'}
    # base IG2 fields + the US-scorecard (CAMELS) fields (FDIC pre-computed ratios + raw $ for derivations)
    _flds = ('REPDTE,INTINC,NIM,PTAXNETINC,ITAX,ELNATR,NETINC,ASSET,LNLSNET,DEP,SC,EQ,NALTOT,OFFDOM,RBCRWAJ'
             ',ROA,NIMY,EEFFR,LNLSDEPR,NPERFV,NTLNLSR,LNATRESR,IDT1RWAJR,RBC1AAJ,INTAN,NONII,NONIX'
             ',DEPINS,DEPUNINS,COREDEP,DEPNIDOM,ORE')
    _SER = {'markup': 'INTINC', 'net_spread': 'NIM', 'pat': 'NETINC', 'total_assets': 'ASSET',
            'gross_loans': 'LNLSNET', 'deposits': 'DEP', 'investments': 'SC', 'equity': 'EQ',
            'npl': 'NALTOT', 'provisions': 'ELNATR', 'branches': 'OFFDOM'}
    def _num(d, f):
        v = d.get(f)
        return float(v) if isinstance(v, (int, float)) else None
    us_out = {}
    for tk, cert in _US_BANK_CERTS.items():
        try:
            u = ('https://banks.data.fdic.gov/api/financials'
                 f'?filters=CERT:{cert}&sort_by=REPDTE&sort_order=desc&limit=28&fields={_flds}')
            r = requests.get(u, headers=_hdr, timeout=20)
            if r.status_code != 200:
                log(f'  [US-bank IG2] {tk} (CERT {cert}): financials HTTP {r.status_code} - skipped'); continue
            rows = [(x.get('data') or x) for x in (r.json().get('data') or [])]
            ann = {}  # Dec-31 annual reports, 2019..2024
            for d in rows:
                rd = str(d.get('REPDTE') or '')
                if len(rd) == 8 and rd[4:] == '1231':
                    y = int(rd[:4])
                    if 2019 <= y <= 2024 and y not in ann:
                        ann[y] = d
            if not ann:
                log(f'  [US-bank IG2] {tk} (CERT {cert}): no FY2019-2024 annual reports - skipped'); continue
            rec = {}
            for skey, fld in _SER.items():
                ser = {str(y): _num(d, fld) for y, d in ann.items() if _num(d, fld) is not None}
                if ser:
                    rec[skey] = ser
            pbp = {}  # pre-provision pre-tax operating profit = pre-tax profit + provisions added back
            for y, d in ann.items():
                pt = _num(d, 'PTAXNETINC')
                if pt is not None:
                    pbp[str(y)] = pt + (_num(d, 'ELNATR') or 0)
            if pbp:
                rec['pbp'] = pbp
            d24 = ann.get(2024) or {}
            car, tax, pbt = _num(d24, 'RBCRWAJ'), _num(d24, 'ITAX'), _num(d24, 'PTAXNETINC')
            if car is not None: rec['car_2024'] = car
            if tax is not None: rec['tax_2024'] = tax
            if pbt is not None: rec['pbt_2024'] = pbt
            # ---- US bank SCORECARD block (CAMELS, im3_score score_bank_us) ----
            # FDIC pre-computed FY2024 ratios + raw $ for the derived ratios (TCE/ROTCE/PPNR/Texas/
            # reserve-coverage/uninsured/core/noninterest-bearing) + the 5yr series for the 4 CAGRs.
            def _ser4(fld):
                return {str(y): _num(d, fld) for y, d in ann.items() if _num(d, fld) is not None}
            us_sc = {
                'car_total':      _num(d24, 'RBCRWAJ'),     # total risk-based capital ratio %
                'tier1_rbc':      _num(d24, 'IDT1RWAJR'),   # tier-1 risk-based capital ratio %
                'tier1_lev':      _num(d24, 'RBC1AAJ'),     # tier-1 leverage ratio %
                'roa':            _num(d24, 'ROA'),         # return on assets %
                'nimy':           _num(d24, 'NIMY'),        # net interest margin %
                'eff':            _num(d24, 'EEFFR'),       # efficiency ratio % (lower better)
                'ldr':            _num(d24, 'LNLSDEPR'),    # loan-to-deposit ratio %
                'noncurrent_pct': _num(d24, 'NPERFV'),      # noncurrent loans / loans %
                'nco_rate':       _num(d24, 'NTLNLSR'),     # net charge-off rate %
                'allow_loans':    _num(d24, 'LNATRESR'),    # allowance for credit losses / loans %
                'intan':          _num(d24, 'INTAN'),       # intangible assets $ (for TCE)
                'nonii':          _num(d24, 'NONII'),       # noninterest income $ (for PPNR)
                'nonix':          _num(d24, 'NONIX'),       # noninterest expense $ (for PPNR)
                'nim_dollar':     _num(d24, 'NIM'),         # net interest income $ (for PPNR)
                'eq':             _num(d24, 'EQ'),          # total equity $
                'netinc':         _num(d24, 'NETINC'),      # net income $ (for ROTCE)
                'asset':          _num(d24, 'ASSET'),       # total assets $
                'dep':            _num(d24, 'DEP'),         # total deposits $
                'depins':         _num(d24, 'DEPINS'),      # insured deposits $
                'depunins':       _num(d24, 'DEPUNINS'),    # uninsured deposits $ (run-risk)
                'coredep':        _num(d24, 'COREDEP'),     # core deposits $
                'depnidom':       _num(d24, 'DEPNIDOM'),    # noninterest-bearing deposits $ (CASA analog)
                'naltot':         _num(d24, 'NALTOT'),      # noncurrent loans $ (for coverage/Texas)
                'ore':            _num(d24, 'ORE'),         # other real estate owned $ (for Texas)
                'lnlsnet':        _num(d24, 'LNLSNET'),     # net loans $ (for allowance $)
                'series': {'asset':    _ser4('ASSET'),   'loans':    _ser4('LNLSNET'),
                           'deposits': _ser4('DEP'),     'netinc':   _ser4('NETINC')},
            }
            if d24 and any(v is not None for k, v in us_sc.items() if k != 'series'):
                rec['us_sc'] = us_sc      # routes this bank to score_bank_us (CAMELS) in im3_score v2.17.0+
            if rec:
                rec['_src'] = f'FDIC CERT {cert} (FY{min(ann)}-{max(ann)})'
                us_out[tk] = rec
                eq24 = (rec.get('equity') or {}).get('2024'); pat24 = (rec.get('pat') or {}).get('2024')
                gl24 = (rec.get('gross_loans') or {}).get('2024'); dp24 = (rec.get('deposits') or {}).get('2024')
                roe = round(100 * pat24 / eq24, 1) if (eq24 and pat24 is not None) else None
                adr = round(100 * gl24 / dp24, 1) if (dp24 and gl24 is not None) else None
                log(f'  [US-bank IG2] {tk} CERT {cert}: {len(ann)} annual yr(s) {sorted(ann)} '
                    f'-> FY24 ROE~{roe}% ADR~{adr}% CAR {car}')
        except Exception as e:
            log(f'  [US-bank IG2] {tk} (CERT {cert}): FETCH FAILED ({type(e).__name__}: {str(e)[:50]})')
    try:
        try:
            existing = json.load(open('bank_ig2_overrides.json')) or {}
        except Exception:
            existing = {}
        existing.update(us_out)  # US tickers distinct from the PSX SCS entries -> pure add, never clobber
        json.dump(existing, open('bank_ig2_overrides.json', 'w'), indent=2)
        log(f'  [US-bank IG2] merged {len(us_out)} US bank(s) into bank_ig2_overrides.json: {sorted(us_out)} '
            f'(im3_score v2.17.0+ scores these via score_bank_us — CAMELS scorecard, 21 ratios; '
            f'pre-v2.17.0 falls back to score_bank_ig2 calib=us)')
    except Exception as e:
        log(f'  [US-bank IG2] merge-write skipped ({e})')


def fetch_bank_sector_kpmg():
    """KPMG Pakistan Banking Perspective -> SECTOR-EVALUATION read (industry aggregates), NEVER a per-bank input.
    Keyword-anchors the headline sector metrics (profit/asset/deposit/NPL growth, ECL-on-NPL coverage, bank count,
    fiscal deficit, KSE-100 close) from the report summary. Stores data['bank_sector']. Throttled 30d (annual
    report); last-good carried; pdfplumber lazy; fully guarded; never breaks the run."""
    if not BANK_SECTOR_KPMG:
        return {}
    prev = (EXISTING.get('bank_sector') or {})
    has_cached = any(k not in ('_fetched_utc', 'source', 'as_of', 'bank_count') for k in prev)
    last = prev.get('_fetched_utc')
    if last and has_cached:
        try:
            if (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(last).replace('Z', ''))).days < 30:
                log('  [Wave Q sector] KPMG skipped (<30d) — carrying last-good')
                return prev
        except Exception:
            pass
    url = ('https://assets.kpmg.com/content/dam/kpmgsites/pk/pdf/2025/04/'
           'Pakistan-Banking-Perspective-2025.pdf.coredownload.inline.pdf')
    try:
        r = requests.get(url, headers={'User-Agent': UA, 'Accept': '*/*'}, timeout=30)
        if r.status_code != 200 or r.content[:4] != b'%PDF':
            log(f'  [Wave Q sector] KPMG not a PDF (HTTP {r.status_code}) — last-good')
            return prev
        try:
            import pdfplumber, io
        except Exception:
            log('  [Wave Q sector] pdfplumber unavailable — last-good')
            return prev
        parts = []
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pg in pdf.pages[:14]:
                t = pg.extract_text() or ''
                if t:
                    parts.append(t)
        bl = re.sub(r'\s+', ' ', ' '.join(parts))

        def grab(pat):
            m = re.search(pat, bl, re.I)
            if m:
                try:
                    return float(m.group(1).replace(',', ''))
                except Exception:
                    return None
            return None
        out = {'source': 'KPMG Pakistan Banking Perspective 2025 (sector aggregates, FY2024)',
               'as_of': '2024-12-31', 'bank_count': 21 if ('21 leading commercial banks' in bl or '21 banks' in bl) else None,
               '_fetched_utc': dt.datetime.utcnow().isoformat()}
        out['profit_growth_pct']   = grab(r'([\d.]+)%\s*growth in profits')
        out['asset_growth_pct']    = grab(r'assets and deposits grew by\s*([\d.]+)%')
        out['deposit_growth_pct']  = grab(r'assets and deposits grew by\s*[\d.]+%\s*and\s*([\d.]+)%')
        out['npl_growth_pct']      = grab(r'NPL increased by\s*([\d.]+)%')
        out['ecl_npl_coverage_pct']= grab(r'([\d.]+)\s*percent is provided on NPLs')
        out['fiscal_deficit_pct']  = grab(r'fiscal deficit narrow\w* to\s*([\d.]+)%')
        out['kse100_close']        = grab(r'closing the year at\s*([\d,]+)\s*points')
        got = [k for k, v in out.items() if v is not None and k not in ('source', 'as_of', '_fetched_utc')]
        log(f'  [Wave Q sector] KPMG: profit+{out.get("profit_growth_pct")}% assets+{out.get("asset_growth_pct")}% '
            f'deposits+{out.get("deposit_growth_pct")}% NPL+{out.get("npl_growth_pct")}% ECL-cov '
            f'{out.get("ecl_npl_coverage_pct")}% ({len(got)} sector fields)')
        if len(got) < 2:
            log('  [Wave Q sector] <2 fields parsed — keeping prior cache, no throttle stamp')
            return prev
        return out
    except Exception as e:
        log(f'  [Wave Q sector] KPMG skipped ({type(e).__name__}: {str(e)[:50]})')
        return prev
# ========================== end Wave Q Phase-1 bank-data overlays ==========================


# ============================ Wave P breadth/leaders (TV-derived market views) ============================
# Daily market breadth (advancers/decliners) + top volume & value leaders, derived from the SAME
# pakistan/scan we already use - but via an ISOLATED POST (its own request) so that requesting the daily
# 'change' column can NEVER break the main universe scan if TV rejects it. Display/data only. Fully guarded.
PSX_MARKET_STATS = True


def fetch_psx_market_stats():
    """ONE isolated pakistan/scan POST for daily breadth + volume/value leaders over the top-500-by-mcap
    liquid set. Returns {} on any failure (own request -> main universe scan untouched). No scoring effect."""
    if not PSX_MARKET_STATS:
        return {}
    try:
        cols = ['name', 'close', 'volume', 'change']
        body = {'columns': cols, 'range': [0, 500],
                'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'}, 'markets': ['pakistan']}
        r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                          headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
        if r.status_code != 200:
            log(f'  [Wave P breadth] skipped (TV HTTP {r.status_code} - likely the change column)')
            return {}
        rows = parse_tv_scan(r.json(), cols)
        adv = dec = unch = 0
        vals = []
        for row in rows:
            ch = _f(row.get('change')); cl = _f(row.get('close')); vol = _f(row.get('volume'))
            nm = row.get('ticker')
            if ch is None or cl is None or vol is None or not nm or cl <= 0 or vol < 0:
                continue
            if ch > 0: adv += 1
            elif ch < 0: dec += 1
            else: unch += 1
            vals.append((nm, cl, vol, ch))
        if not vals:
            log('  [Wave P breadth] skipped (no parseable rows)')
            return {}
        vol_leaders = [{'ticker': n, 'volume': int(v), 'price': round(c, 2), 'change_pct': round(ch, 2)}
                       for n, c, v, ch in sorted(vals, key=lambda x: -x[2])[:10]]
        val_leaders = [{'ticker': n, 'value_mn': round(c * v / 1e6, 1), 'price': round(c, 2),
                        'change_pct': round(ch, 2)}
                       for n, c, v, ch in sorted(vals, key=lambda x: -(x[1] * x[2]))[:10]]
        out = {'breadth': {'advancers': adv, 'decliners': dec, 'unchanged': unch, 'total': adv + dec + unch},
               'volume_leaders': vol_leaders, 'value_leaders': val_leaders}
        log(f'  [Wave P breadth] adv={adv} dec={dec} unch={unch} (top-{adv+dec+unch} mcap); '
            f'vol leader={vol_leaders[0]["ticker"]}; val leader={val_leaders[0]["ticker"]}')
        return out
    except Exception as e:
        log(f'  [Wave P breadth] skipped ({type(e).__name__}: {str(e)[:50]})')
        return {}
# ========================== end Wave P breadth/leaders ==========================


def fetch_psx_sector_breadth(sample=600):
    """Wave M-A step 2b (PSX): ONE isolated pakistan/scan POST over the top-`sample` by mcap (the FULL
    listed universe, far wider than the ~41-name screen band), grouped by TV sector, computing the % of
    each PSX sector trading at/above its 200-DMA. >=5 names per sector required (else omitted -> thin).
    Own request -> the main universe scan is untouched; {} on any failure (caller carries last-good).
    No scoring effect; respects the Sept freeze."""
    try:
        cols = ['name', 'sector', 'close', 'SMA200']   # 'name' included so parse_tv_scan's len(d)>=4 guard keeps the rows
        body = {'columns': cols, 'range': [0, sample],
                'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'}, 'markets': ['pakistan']}
        r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                          headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
        if r.status_code != 200:
            log(f'  [PSX sector breadth] skipped (TV HTTP {r.status_code})')
            return {}
        rows = parse_tv_scan(r.json(), cols)
        acc = {}
        for row in rows:
            sec = row.get('sector'); cl = _f(row.get('close')); s200 = _f(row.get('SMA200'))
            if not sec or cl is None or s200 is None or cl <= 0 or s200 <= 0:
                continue
            a = acc.setdefault(sec, [0, 0])     # [above, total]
            a[1] += 1
            if cl >= s200:
                a[0] += 1
        out = {sec: {'pct': round(100.0 * ab / tot, 1), 'n': tot, 'above': ab}
               for sec, (ab, tot) in acc.items() if tot >= 5}
        if out:
            _ex = sorted(out.items(), key=lambda x: -x[1]['pct'])[:3]
            log(f'  [PSX sector breadth] {len(out)} sectors >=5 names (e.g. ' +
                ', '.join(f"{s} {v['pct']}%" for s, v in _ex) + ')')
            return out
        log('  [PSX sector breadth] 0 sectors with >=5 names — carrying last-good')
        return {}
    except Exception as e:
        log(f'  [PSX sector breadth] skipped ({type(e).__name__}: {str(e)[:50]})')
        return {}
# ========================== end PSX sector breadth ==========================


# Wave S Phase 2 (PSX): the PSX analog of fetch_sector_medians — ONE isolated pakistan/scan POST over the
# top-`sample` by mcap, grouped by TV sector, computing per-sector MEDIAN P/E + operating/net margin + ROE
# (whatever TV exposes for PSX; a metric with <5 samples is simply omitted -> the dashboard falls back) and
# the per-sector AVERAGE price move (Perf.W/1M/3M) + 200-DMA breadth. Margins/ROE stored as DECIMALS to match
# the US sector_medians shape the dashboard already reads. Own request -> the universe scan + the breadth POST
# are untouched; {} on any failure (caller carries last-good). DATA/DISPLAY only; respects the Sept freeze.
def fetch_psx_sector_medians(sample=600):
    import statistics
    try:
        cols = ['name', 'sector', 'price_earnings_ttm', 'operating_margin', 'net_margin', 'return_on_equity',
                'close', 'SMA200', 'Perf.W', 'Perf.1M', 'Perf.3M',
                'price_target_average', 'earnings_per_share_forecast_next_fq', 'earnings_per_share_fq', 'dividends_yield']
        body = {'columns': cols, 'range': [0, sample],
                'sort': {'sortBy': 'market_cap_basic', 'sortOrder': 'desc'}, 'markets': ['pakistan']}
        r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                          headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=15)
        if r.status_code != 200:
            log(f'  [PSX sector medians] skipped (TV HTTP {r.status_code})')
            return {}
        rows = parse_tv_scan(r.json(), cols)
        acc = {}
        for row in rows:
            sec = row.get('sector')
            if not sec:
                continue
            a = acc.setdefault(sec, {'pe': [], 'op_margin': [], 'net_margin': [], 'roe': [], 'b_above': 0, 'b_tot': 0,
                                     'perf_w': [], 'perf_1m': [], 'perf_3m': [], 'tgt': [], 'feqg': [],
                                     'dy_sum': 0.0, 'dy_n': 0, 'dy_payers': 0})
            pe = _f(row.get('price_earnings_ttm')); opm = _f(row.get('operating_margin'))
            npm = _f(row.get('net_margin')); roe = _f(row.get('return_on_equity'))
            cl = _f(row.get('close')); s200 = _f(row.get('SMA200'))
            pw = _f(row.get('Perf.W')); p1m = _f(row.get('Perf.1M')); p3m = _f(row.get('Perf.3M'))
            tgt = _f(row.get('price_target_average')); fqn = _f(row.get('earnings_per_share_forecast_next_fq')); fqc = _f(row.get('earnings_per_share_fq'))
            dy = _f(row.get('dividends_yield'))
            a['dy_n'] += 1
            if dy is not None and 0 <= dy < 100:
                a['dy_sum'] += dy
                if dy > 0:
                    a['dy_payers'] += 1
            if pe  is not None and 0 < pe < 200:        a['pe'].append(pe)
            if opm is not None and -100 < opm < 100:    a['op_margin'].append(opm / 100.0)
            if npm is not None and -100 < npm < 100:    a['net_margin'].append(npm / 100.0)
            if roe is not None and -200 < roe < 300:
                _rp = _roe_pct(roe)
                if _rp is not None: a['roe'].append(_rp / 100.0)
            if cl is not None and s200 is not None and cl > 0 and s200 > 0:
                a['b_tot'] += 1
                if cl >= s200:
                    a['b_above'] += 1
            if pw  is not None and -95 < pw  < 500:     a['perf_w'].append(pw)
            if p1m is not None and -95 < p1m < 800:     a['perf_1m'].append(p1m)
            if p3m is not None and -95 < p3m < 1500:    a['perf_3m'].append(p3m)
            if tgt is not None and tgt > 0 and cl is not None and cl > 0:
                _tu = (tgt / cl - 1.0) * 100.0
                if -90 < _tu < 300:   a['tgt'].append(_tu)
            if fqn is not None and fqc is not None and fqc > 0:
                _g = (fqn / fqc - 1.0) * 100.0
                if -100 < _g < 300:   a['feqg'].append(_g)
        out = {}
        for sec, a in acc.items():
            rec = {}
            for k in ('pe', 'op_margin', 'net_margin', 'roe'):
                if len(a[k]) >= 5:
                    rec[k] = round(statistics.median(a[k]), 4)
            if a['b_tot'] >= 5:
                rec['breadth_200dma'] = round(100.0 * a['b_above'] / a['b_tot'], 1)
                rec['breadth_n'] = a['b_tot']
            for k in ('perf_w', 'perf_1m', 'perf_3m'):
                if len(a[k]) >= 5:
                    rec[k] = round(statistics.mean(a[k]), 2)
            if len(a['tgt'])  >= 5:  rec['tgt_upside']  = round(statistics.mean(a['tgt']),  2)
            if len(a['feqg']) >= 5:  rec['fwd_eps_q_g'] = round(statistics.mean(a['feqg']), 2)
            if a['dy_n'] >= 5 and a['dy_payers'] >= 1:  rec['div_yield'] = round(a['dy_sum'] / a['dy_n'], 2)
            if any(k in rec for k in ('pe', 'op_margin', 'net_margin', 'roe', 'breadth_200dma', 'perf_w', 'perf_1m', 'perf_3m', 'tgt_upside', 'fwd_eps_q_g', 'div_yield')):
                rec['n'] = max(len(a['pe']), len(a['op_margin']), len(a['net_margin']), len(a['roe']), a['b_tot'])
                out[sec] = rec
        if out:
            _ex = sorted(out.items(), key=lambda x: -(x[1].get('n') or 0))[:3]
            log(f'  [PSX sector medians] {len(out)} sectors (e.g. ' +
                ', '.join(f"{s} PE~{v.get('pe')}/ROE~{v.get('roe')}/1M~{v.get('perf_1m')}%/tgt~{v.get('tgt_upside')}%" for s, v in _ex) + ')')
            return out
        log('  [PSX sector medians] 0 sectors parsed — carrying last-good')
        return {}
    except Exception as e:
        log(f'  [PSX sector medians] skipped ({type(e).__name__}: {str(e)[:50]})')
        return {}
# ========================== end PSX sector medians ==========================


def screen_psx_universe():
    log('=== PSX screening ===')
    try:
        probe_psx_institutional_sources()   # Wave P Phase-0 reachability probe (logging-only)
    except Exception as _e:
        log(f'  [Wave P probe] error ({_e})')
    try:
        probe_fipi_lipi_sources()           # Wave P Phase-2 FIPI/LIPI reachability probe (logging-only)
    except Exception as _e:
        log(f'  [Wave P FIPI probe] error ({_e})')
    try:
        probe_bank_data_sources()           # Wave Q Phase-0 bank-data source probe (logging-only)
    except Exception as _e:
        log(f'  [Wave Q probe] error ({_e})')
    try:
        probe_scs_reports()                 # Wave PSX-R Phase-0 SCS report-PDF probe (logging-only)
    except Exception as _e:
        log(f'  [Wave PSX-R probe] error ({_e})')
    try:
        probe_free_levers()                 # Wave R Phase-0 remaining free-lever feed probe (logging-only)
        probe_pak_ca()                      # CA-units probe (logging-only): lock the TE current-account unit/period before wiring pak_ca
        probe_fdic_bankfind()               # US-bank IG2 probe (logging-only): test FDIC BankFind reachability + name->CERT + IG2 fields before wiring fetch_us_bank_ig2
        probe_etf_isin_feeds()              # Phase 6 probe — gated off, verdict locked (nginx 403 dead end)
        probe_tv_isin_column()              # Phase 6b probe — gated off, verdict locked (isin column CONFIRMED)
        probe_tv_isin_filter()              # Phase 6c probe — gated off, verdict locked (isin filter CONFIRMED 12/12)
        probe_etf_performance_columns()     # v1.139.0 probe — PRE-ARMED: tests Perf.YTD/Perf.Y/Perf.3Y on the proven isin-filter endpoint
    except Exception as _e:
        log(f'  [Wave R free-lever probe] error ({_e})')
    try:
        probe_ecodata_dump()                # F3 Step 1 SBP ecodata raw dump (logging-only, runner-side)
    except Exception as _e:
        log(f'  [F3 ecodata dump] error ({_e})')
    try:
        tickers = fetch_psx_universe()
        candidates = []
        for tup in tickers:
            try:
                result = screen_psx_stock(tup)
                if result:
                    candidates.append(result)
                    log(f'  ✓ {result["ticker"]}: price={result["price"]} '
                        f'({result["data_source"]})')
                    if result.get('data_source') != 'tv_scan':
                        time.sleep(YF_DELAY)   # only rate-limit when a per-name endpoint was actually hit
            except Exception:
                continue

        if len(candidates) >= 3:
            candidates[0]['status'] = 'HIGH-CONVICTION'
            candidates[1]['status'] = 'HIGH-CONVICTION'
            candidates[2]['status'] = 'HIGH-CONVICTION'
            for c in candidates[3:7]:
                c['status'] = 'STRONG'
            for c in candidates[7:]:
                c['status'] = 'WATCH'

        funnel = [
            ['PSX Total Listed Companies', 561, 'Source: PSX official listings'],
            ['Outside KSE-30 (excl. large caps)', 480, 'Removed KSE-30 large caps'],
            ['Sweet Spot Tier (PKR 5-30bn)', 150, 'Informal PSX small-cap zone'],
            ['+ Growth Filter (Fwd >20%)', 30, 'Forecast earnings growth ≥20%'],
            ['+ Moat OR Insider Gate', 18, 'Sponsor ≥40% + clear moat'],
            ['+ Multibagger Fit Assessment', len(candidates), 'Final candidates'],
        ]

        log(f'  PSX scan done: {len(candidates)} candidates')
        return {'funnel': funnel, 'candidates': candidates}
    except Exception as e:
        log(f'  PSX FAILED: {e}')
        traceback.print_exc()
        return {'funnel': EXISTING.get('psx_funnel', []),
                'candidates': EXISTING.get('psx_candidates', [])}


# =============================================================
# 5. TCE
# =============================================================
# --- Augmented TCE: old attention streams + fundamentals + forward revisions + RS guardrail ---
# v1.58.3: s2_sponsor REMOVED from ATTENTION/COUNTED. s1_news (>=3 articles) and s2_sponsor (>=8)
# were two thresholds on the SAME Google-News count -> s2 implies s1, so a well-covered name added
# +2 to `total` from ONE underlying signal (and "sponsor" was a misnomer — no sponsorship/ownership
# data feeds it). News now counts ONCE via s1_news. s2_sponsor is still computed below as a
# DISPLAY-ONLY "heavy news" flag but is NOT in COUNTED, so it can never inflate total/conviction.
ATTENTION   = ('s1_news', 's3_insider', 's5_volume')
FUNDAMENTAL = ('s6_momentum', 's7_margin', 's8_capital')
REVISION    = ('s9_eps_rev', 's10_rev_rev')
ANALYST     = ('s9_eps_revision', 's11_target_upside', 's12_recommendation')  # TV FactSet. PSX sets all 3; US sets s11/s12 (s9_eps_revision stays 0 for US to avoid double-counting Yahoo s9_eps_rev).
CONVICTION  = FUNDAMENTAL + REVISION + ANALYST  # streams that must converge for HIGH (the discriminators)
COUNTED     = ATTENTION + FUNDAMENTAL + REVISION + ANALYST
BINARY_STREAMS = COUNTED                        # back-compat alias

# Tuning (precision backtest, 2026-06-03): the price core is a real-but-modest trend-confirmer whose
# edge sharpens with a tighter momentum bar (lift 1.36x@15% -> 1.46x@20% -> 2.0x@30%). s6 raised
# 15 -> 22; and HIGH now requires conviction>=4 (the conv-3+attention path is dropped to WATCH).
TCE_MOM_THRESH     = 22      # s6 momentum %, 3mo
PRED_HORIZON_DAYS  = 90      # forward-validation maturation window
PRED_WINNER_THRESH = 40.0    # forward return % that counts a logged pick a "winner"


def derive_streams(info, closes, eps_up30, eps_down30, rev_est, spy_6mo_ret, prev_rev_est,
                   eps_growth_pct=None, rev_growth_pct=None, perf_3m=None):
    """Yahoo-derived stream flags from already-fetched primitives. Any input may be None; a stream
    that can't be computed simply stays 0 (never errors, never vetoes). eps_growth_pct/rev_growth_pct
    are an optional percent-units fallback for s7 when Yahoo .info lacks growth (PSX, where yfinance
    has no fundamentals). perf_3m is the TradingView 3-month performance %, used as the s6 momentum
    fallback when there's no .KA price history (PSX names yfinance can't serve). Pure + unit-tested."""
    s = {}
    if closes:
        s['price'] = round(closes[-1], 4)                                    # entry price for forward-validation
    if closes and len(closes) >= 64 and closes[-64]:                         # s6 momentum (3mo)
        mom = (closes[-1] - closes[-64]) / closes[-64] * 100
        s['s6_momentum_pct'] = round(mom, 1)
        s['s6_momentum'] = 1 if mom >= TCE_MOM_THRESH else 0
    elif perf_3m is not None:                                                # s6 fallback: TV 3-month perf
        s['s6_momentum_pct'] = round(perf_3m, 1)
        s['s6_momentum'] = 1 if perf_3m >= TCE_MOM_THRESH else 0
        s['s6_momentum_src'] = 'tv_perf3m'
    spy_6mo_ret = spy_6mo_ret if (spy_6mo_ret is not None and spy_6mo_ret == spy_6mo_ret) else None  # NaN benchmark -> treat as absent (fail open, never veto on a bad SPY fetch)
    if closes and len(closes) >= 2 and closes[0]:                            # RS guardrail (6mo vs SPY)
        name_6mo = (closes[-1] - closes[0]) / closes[0] * 100
        if name_6mo != name_6mo:                                             # NaN-safe: can't compute the name's
            s['rs_ok'] = True                                                # own return -> FAIL OPEN, never veto on
        else:                                                                # bad price data (NaN>=x is silently False)
            s['rs_vs_spy'] = round(name_6mo - spy_6mo_ret, 1) if spy_6mo_ret is not None else None
            s['rs_ok'] = (spy_6mo_ret is None) or (name_6mo >= spy_6mo_ret)
    else:
        s['rs_ok'] = True
    eg = info.get('earningsGrowth') if info else None                        # s7 margin inflection
    rg = info.get('revenueGrowth') if info else None
    if eg is not None and rg is not None:
        s['s7_margin_spread_pct'] = round((eg - rg) * 100, 1)
        s['s7_margin'] = 1 if (eg > rg and eg > 0) else 0
    elif eps_growth_pct is not None and rev_growth_pct is not None:           # PSX fallback (percent units)
        s['s7_margin_spread_pct'] = round(eps_growth_pct - rev_growth_pct, 1)
        s['s7_margin'] = 1 if (eps_growth_pct > rev_growth_pct and eps_growth_pct > 0) else 0
    sp = info.get('shortPercentOfFloat') if info else None                   # s8 external capital
    if sp is not None:
        s['s8_capital_short_pct'] = round(sp * 100, 1)
        s['s8_capital'] = 1 if sp >= 0.08 else 0
    if eps_up30 is not None and eps_down30 is not None:                       # s9 EPS revision direction
        s['s9_eps_rev_net'] = eps_up30 - eps_down30
        s['s9_eps_rev'] = 1 if (eps_up30 > eps_down30 and eps_up30 > 0) else 0
    if rev_est is not None:                                                  # s10 revenue revision (snapshot)
        s['rev_est'] = rev_est
        if prev_rev_est:
            s['s10_rev_rev_pct'] = round((rev_est - prev_rev_est) / prev_rev_est * 100, 2)
            s['s10_rev_rev'] = 1 if rev_est > prev_rev_est else 0
    return s


def tce_tier(streams, market='us'):
    """Conviction (fundamentals+revisions) carries the tier. HIGH requires conviction>=4 (backtest:
    the conv-3+attention path didn't earn its keep — it now tops out at WATCH). A name converging on
    fundamentals BEFORE news/volume — the 3-quarters-early setup — still reaches HIGH on conviction
    alone; pure attention can only ever reach WATCH. RS guardrail caps a market-laggard to WATCH.

    PSX uses a market-specific bar: PSX can structurally fire only 5 of 9 streams (no Pakistani feed
    for s3 insider, s8 short-interest, s9/s10 revisions), so conviction caps at ~2. The US bar is
    therefore unreachable. PSX: HIGH = conv>=2 AND total>=5; WATCH = conv>=2 OR total>=4."""
    total = sum(int(streams.get(k, 0)) for k in COUNTED)
    conv  = sum(int(streams.get(k, 0)) for k in CONVICTION)
    rs_ok = bool(streams.get('rs_ok', True))
    if market == 'psx':
        if conv >= 2 and total >= 5:
            return 'HIGH', total, conv
        if conv >= 2 or total >= 4:
            return 'WATCH', total, conv
        return 'IGNORE', total, conv
    strong = (conv >= 4)
    if strong and rs_ok:
        return 'HIGH', total, conv
    if (conv >= 3) or (total >= 5 and conv >= 1) or (strong and not rs_ok):
        return 'WATCH', total, conv
    return 'IGNORE', total, conv


def _spy_6mo_return():
    """Returns (6mo % return, last close) for SPY; (None, None) on failure. Last close feeds the
    prediction-ledger US benchmark (alpha)."""
    try:
        import yfinance as yf
        h = yf.Ticker('SPY').history(period='6mo')
        c = [float(x) for x in h['Close'].tolist() if x == x] if len(h) else []  # drop NaN (same intermittent Yahoo glitch as the per-name closes)
        if len(c) >= 2 and c[0]:
            return round((c[-1] - c[0]) / c[0] * 100, 1), round(c[-1], 4)
    except Exception:
        pass
    return None, None


def _reprice_us(tickers):
    """Gap-1: batch last-close for US tickers (open predictions that have left the scan pool) so their
    forward return keeps updating to maturity instead of freezing stale. yfinance-only -> sandbox cannot
    run it (blocked); confirms on the GitHub runner. Loud (warn) on failure, never raises."""
    out = {}
    tickers = [t for t in tickers if t]
    if not tickers:
        return out
    try:
        import yfinance as yf
        df = yf.download(tickers, period='5d', progress=False, threads=True)
        if df is not None and not df.empty:
            close = df['Close'] if 'Close' in getattr(df, 'columns', []) else df
            if hasattr(close, 'columns'):                  # multi-ticker -> DataFrame of close columns
                for t in tickers:
                    try:
                        s = close[t].dropna()
                        if len(s):
                            out[t] = round(float(s.iloc[-1]), 4)
                    except Exception:
                        pass
            else:                                          # single ticker -> Series
                s = close.dropna()
                if len(s):
                    out[tickers[0]] = round(float(s.iloc[-1]), 4)
    except Exception as e:
        warn(f'prediction re-price (US) failed for {len(tickers)} ticker(s): {e}')
    return out


def _reprice_psx(tickers):
    """Gap-1: last-close for off-pool PSX predictions via a targeted TradingView Pakistan scan
    (symbols filter). Returns {ticker: price}. Loud on failure, never raises."""
    out = {}
    tickers = [t for t in tickers if t]
    if not tickers:
        return out
    try:
        body = {'symbols': {'tickers': [f'PSX:{t}' for t in tickers]}, 'columns': ['close']}
        r = requests.post('https://scanner.tradingview.com/pakistan/scan', json=body,
                          headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=20)
        if r.status_code == 200:
            for row in parse_tv_scan(r.json(), ['close']):
                if row.get('ticker') and row.get('close') is not None:
                    out[row['ticker']] = round(float(row['close']), 4)
    except Exception as e:
        warn(f'prediction re-price (PSX) failed for {len(tickers)} ticker(s): {e}')
    return out


def _pred_days(d0, d1):
    try:
        return (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)).days
    except Exception:
        return 0


def update_tce_predictions(prev, today_iso, rows,
                           horizon_days=PRED_HORIZON_DAYS, winner_thresh=PRED_WINNER_THRESH,
                           extra_prices=None, bench=None):
    """Forward-validation ledger (the automated replacement for the impossible historical revision
    backtest). Logs each run's HIGH/WATCH/IGNORE picks with entry price + benchmark, marks the latest
    forward return AND market-relative alpha on every later run, and freezes once the pick matures
    (>= horizon). Summarises per-tier hit-rate / avg forward / avg alpha / beat-benchmark over matured
    picks, plus HIGH/WATCH lift over the IGNORE base rate. Pure + unit-tested (no I/O, no clock).
      prev: prior {'predictions':[...]} dict (or None)
      rows: this run's picks [{'ticker','tier','market','price'}] — HIGH/WATCH/IGNORE from the TCE pool
      extra_prices: {ticker: live price} for OPEN preds NOT in this run's pool (Gap-1: keeps forward
                    returns updating to maturity even after a name churns out of the pool / decays to IGNORE)
      bench: {'us': spy_price, 'psx': kse100_level} benchmark levels this run (Gap-2: alpha)
    Dedup is per (ticker, tier): a name that escalates IGNORE->WATCH->HIGH logs a fresh prediction at
    each tier, so each tier's signal is measured from the moment it fired (Gap-3 control included)."""
    prev = prev or {}
    preds = [dict(p) for p in prev.get('predictions', [])]
    bench = bench or {}
    price = dict(extra_prices or {})                           # off-pool live prices first ...
    price.update({r['ticker']: r['price'] for r in rows if r.get('price')})  # ... this run's pool overrides
    # ── One-time PSX re-baseline (Wave O L3 follow-up) ───────────────────────────────────────────
    # PSX entries logged before the L3 TV-price cutover used the STALE dps.psx EOD basis (TRG 164 vs
    # real 72, KPUS 49 vs real 2443) — garbage forward returns at maturity. The v136 pass killed the
    # staleness but reset onto the yahoo:.KA snapshot (streams['price']), ~0-10% off the screen's
    # tv_scan. v137 re-runs the reset now that the caller feeds tv_scan rows for PSX, so entry shares
    # one basis with _reprice_psx (both TV) -> no systematic offset at maturity. US (Yahoo throughout,
    # entry + _reprice_us consistent) is untouched. price.get() = caller's tv_scan rows + TV re-price.
    rebaselined = 0
    if not prev.get('psx_rebaselined_v137'):
        _cb = bench.get('psx')
        for p in preds:
            if p.get('market') == 'psx' and not p.get('resolved'):
                cur = price.get(p['ticker'])
                if cur:
                    p['entry'] = round(cur, 4); p['date'] = today_iso
                    p['last_price'] = round(cur, 4); p['last_date'] = today_iso
                    p['fwd_ret_pct'] = 0.0; p['peak_ret_pct'] = 0.0
                    p['entry_bench'] = round(_cb, 4) if _cb else None
                    p['bench_ret_pct'] = (0.0 if _cb else None)
                    p['alpha_pct'] = (0.0 if _cb else None); p['peak_alpha_pct'] = (0.0 if _cb else None)
                    p['days_open'] = 0; p['rebaselined'] = True
                    rebaselined += 1
    open_keys = set()                                          # dedup key = (ticker, tier)
    for p in preds:                                            # update + freeze at maturity
        d = _pred_days(p.get('date', ''), today_iso)
        p['days_open'] = d
        cur = price.get(p['ticker'])
        if cur and p.get('entry') and not p.get('resolved'):
            ret = round((cur - p['entry']) / p['entry'] * 100, 1)
            p['last_price'] = round(cur, 4); p['last_date'] = today_iso
            p['fwd_ret_pct'] = ret
            p['peak_ret_pct'] = round(max(p.get('peak_ret_pct', ret), ret), 1)
            eb = p.get('entry_bench'); cb = bench.get(p.get('market', 'us'))   # Gap-2: market-relative alpha
            if eb and cb:
                bret = round((cb - eb) / eb * 100, 1)
                a = round(ret - bret, 1)
                p['bench_ret_pct'] = bret; p['alpha_pct'] = a
                p['peak_alpha_pct'] = round(max(p.get('peak_alpha_pct', a), a), 1)
        if d >= horizon_days and not p.get('resolved'):
            p['resolved'] = True
        if d < horizon_days:
            open_keys.add((p['ticker'], p.get('tier')))
    for r in rows:                                             # log new picks not already open (per ticker+tier)
        tk = r['ticker']; tier = r.get('tier'); cur = price.get(tk)
        if cur and (tk, tier) not in open_keys:
            eb = bench.get(r.get('market', 'us'))
            preds.append({'ticker': tk, 'tier': tier, 'market': r.get('market', 'us'),
                          'date': today_iso, 'entry': round(cur, 4), 'last_price': round(cur, 4),
                          'last_date': today_iso, 'fwd_ret_pct': 0.0, 'peak_ret_pct': 0.0,
                          'entry_bench': round(eb, 4) if eb else None,
                          'bench_ret_pct': (0.0 if eb else None),
                          'alpha_pct': (0.0 if eb else None), 'peak_alpha_pct': (0.0 if eb else None),
                          'days_open': 0, 'resolved': False})
            open_keys.add((tk, tier))
    summary = {'horizon_days': horizon_days, 'winner_thresh': winner_thresh,
               'total_logged': len(preds),
               'open': sum(1 for p in preds if p.get('days_open', 0) < horizon_days)}
    for tier in ('HIGH', 'WATCH', 'IGNORE'):
        matured = [p for p in preds if p.get('tier') == tier and p.get('days_open', 0) >= horizon_days]
        n = len(matured)
        if n:
            hits = sum(1 for p in matured if p.get('fwd_ret_pct', 0) >= winner_thresh)
            avals = [p['alpha_pct'] for p in matured if p.get('alpha_pct') is not None]
            beat = sum(1 for a in avals if a > 0)
            summary[tier] = {'matured': n, 'hit_rate': round(hits / n, 3),
                             'avg_fwd_pct': round(sum(p.get('fwd_ret_pct', 0) for p in matured) / n, 1),
                             'avg_peak_pct': round(sum(p.get('peak_ret_pct', 0) for p in matured) / n, 1),
                             'beat_bench_rate': (round(beat / len(avals), 3) if avals else None),
                             'avg_alpha_pct': (round(sum(avals) / len(avals), 1) if avals else None)}
        else:
            summary[tier] = {'matured': 0, 'hit_rate': None, 'avg_fwd_pct': None, 'avg_peak_pct': None,
                             'beat_bench_rate': None, 'avg_alpha_pct': None}
    base = summary['IGNORE'].get('hit_rate')                   # Gap-3: lift of HIGH/WATCH over IGNORE base rate
    for tier in ('HIGH', 'WATCH'):
        hr = summary[tier].get('hit_rate')
        summary[tier]['lift_vs_ignore'] = (round(hr / base, 2) if (hr is not None and base) else None)
    summary['psx_rebaselined'] = rebaselined
    return {'predictions': preds, 'summary': summary, 'updated': today_iso,
            'psx_rebaselined_v136': True, 'psx_rebaselined_v137': True}


def compute_tce_streams(ticker, market='us', spy_6mo_ret=None, prev_rev_est=None,
                        eps_growth_pct=None, rev_growth_pct=None, perf_3m=None,
                        analyst_row=None, prev_fwd_eps=None, hist_cache=None):
    streams = {k: 0 for k in COUNTED}
    streams['s2_sponsor'] = 0   # display-only (heavy news >=8); NOT in COUNTED -> never counted (v1.58.3)

    # s1_news (counted) + s2_sponsor (DISPLAY-ONLY) — both off ONE Google News RSS count (last 14 days)
    try:
        import feedparser
        url = (f'https://news.google.com/rss/search?q={ticker}+stock+OR+earnings'
               f'&hl=en-US&gl=US&ceid=US:en')
        feed = feedparser.parse(url)
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=14)
        recent = 0
        for entry in feed.entries[:30]:
            try:
                if getattr(entry, 'published_parsed', None) and dt.datetime(*entry.published_parsed[:6]) > cutoff:
                    recent += 1
            except Exception:
                continue
        streams['s1_news_count'] = recent
        if recent >= 3:
            streams['s1_news'] = 1
        if recent >= 8:
            streams['s2_sponsor'] = 1
    except Exception:
        pass

    # ONE yfinance fetch -> volume(s5) + momentum/RS(s6) + margin(s7) + capital(s8) + revisions(s9/s10)
    try:
        import yfinance as yf
        sym = f'{ticker}.KA' if market == 'psx' else ticker
        t = yf.Ticker(sym)
        # v1.111.0: prefer the batched 6mo history (ONE yf.download for the whole pool, built by
        # _batch_history_cache) — the SAME daily series .history() returns, so s5/s6/RS are
        # byte-identical; fall back to the per-name .history() on a cache miss (delisted .KA, thin
        # name, or TCE_BATCH_HISTORY=False) so coverage can NEVER regress. `t` is still created for
        # the per-name .info / .get_eps_revisions() / .get_revenue_estimate() calls below (unchanged).
        h = None
        if hist_cache is not None:
            _cached = hist_cache.get(ticker)
            if _cached is not None and len(_cached):
                h = _cached
        if h is None:
            # _PSX_YAHOO_SKIP: known PSX tickers Yahoo marks delisted but TV scan still carries
            _base_ticker = ticker.replace('.KA','').replace('$','').upper()
            if market == 'psx' and _base_ticker in _PSX_YAHOO_SKIP:
                pass  # skip Yahoo call; h stays None -> s6 uses TV perf_3m fallback
            else:
                h = t.history(period='6mo')
        # v1.112.0 (F1): Yahoo serves ZERO fundamentals for PSX .KA tickers, so for PSX these three
        # per-name calls (.info / get_eps_revisions / get_revenue_estimate) are guaranteed 404/None
        # (~147/run, ~65s) that feed NOTHING: PSX s7 uses the scanner's TTM eps/rev growth (derive_streams
        # fallback), s8 is skipped, s9/s11/s12 come from the analyst overlay. Gate them US-only -> for PSX
        # info stays {} and the estimates stay None, IDENTICAL to the 404 result (streams byte-equivalent).
        _yf_fund = (not TCE_YF_FUNDAMENTALS_US_ONLY) or (market == 'us')
        info = {}
        if _yf_fund:
            try:
                info = t.info or {}
            except Exception:
                info = {}
        closes = [float(x) for x in h['Close'].tolist() if x == x] if len(h) else []  # x==x drops NaN (intermittent Yahoo: Volume populates but Close comes back NaN)

        if len(h) >= 60:                                            # s5_volume
            vr = h['Volume'].iloc[-20:].mean(); vb = h['Volume'].iloc[:40].mean()
            if vb > 0:
                ratio = vr / vb
                streams['s5_volume_ratio'] = round(ratio, 2)
                if ratio > 1.3:
                    streams['s5_volume'] = 1

        eps_up30 = eps_down30 = None                                # s9 forward EPS revision breadth
        try:
            er = (t.get_eps_revisions() if hasattr(t, 'get_eps_revisions') else getattr(t, 'eps_revisions', None)) if _yf_fund else None  # v1.112.0 F1: US-only
            if er is not None and hasattr(er, 'columns'):
                cols = {str(c).lower(): c for c in er.columns}
                up_c = next((cols[k] for k in cols if 'up' in k and '30' in k), None)
                dn_c = next((cols[k] for k in cols if 'down' in k and '30' in k), None)
                if up_c is not None and dn_c is not None:
                    eps_up30 = int(er[up_c].fillna(0).iloc[0]); eps_down30 = int(er[dn_c].fillna(0).iloc[0])
        except Exception:
            pass

        rev_est = None                                              # s10 consensus revenue estimate (snapshot)
        try:
            re_df = (t.get_revenue_estimate() if hasattr(t, 'get_revenue_estimate') else getattr(t, 'revenue_estimate', None)) if _yf_fund else None  # v1.112.0 F1: US-only
            if re_df is not None and hasattr(re_df, 'columns'):
                avg_c = next((c for c in re_df.columns if str(c).lower() in ('avg', 'average')), None)
                if avg_c is not None:
                    rev_est = float(re_df[avg_c].iloc[0])
        except Exception:
            pass

        streams.update(derive_streams(info, closes, eps_up30, eps_down30, rev_est, spy_6mo_ret, prev_rev_est,
                                       eps_growth_pct=eps_growth_pct, rev_growth_pct=rev_growth_pct,
                                       perf_3m=perf_3m))
    except Exception:
        _swallow('tce.fetch')          # v1.112.0 (F6): surface a swallowed TCE fetch in the run summary
        streams.setdefault('rs_ok', True)

    # s3_insider — SEC Form 4 count (US only)
    if market == 'us':
        try:
            today = dt.date.today()
            start_dt = (today - dt.timedelta(days=90)).isoformat()
            url = (f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22'
                   f'&forms=4&dateRange=custom&startdt={start_dt}&enddt={today.isoformat()}')
            r = requests.get(url, headers={'User-Agent': 'Dashboard Scanner dashboard@example.com',
                                           'Accept': 'application/json'}, timeout=10)
            if r.status_code == 200:
                hits = safe_get(r.json(), 'hits', 'total', 'value', default=0)
                streams['s3_insider_count'] = hits
                if hits >= 2:
                    streams['s3_insider'] = 1
        except Exception:
            pass

    streams.setdefault('rs_ok', True)
    streams['total'] = sum(streams.get(k, 0) for k in COUNTED)
    # D2 + Wave O L1: analyst-conviction streams (TV FactSet). PSX gets all three (its only
    # estimate-revision source). US gets s11/s12 only — it already has s9_eps_rev (Yahoo
    # estimate revisions), so folding the TV s9_eps_revision too would double-count EPS revision.
    if analyst_row and tce_psx_analyst is not None:
        try:
            _a = tce_psx_analyst.derive_psx_analyst_streams(analyst_row, prev_fwd_eps)
            for _s in _a.get('streams', []):
                if market == 'us' and _s == 's9_eps_revision':
                    continue                  # US already has s9_eps_rev (Yahoo) — avoid double-count
                if _s in streams:
                    streams[_s] = 1
            streams['analyst_covered'] = _a.get('analyst_covered', False)
            streams['analyst_detail'] = _a.get('detail', {})
            _fe = _a.get('detail', {}).get('fwd_eps')
            if _fe is not None:
                streams['fwd_eps'] = _fe          # persisted for next-run revision detection
        except Exception:
            pass

    return streams


def _batch_history_cache(candidates, market='us', max_count=20):
    """v1.111.0 — ONE yf.download for the whole TCE pool's 6mo daily history, returned as
    {bare_ticker: per-ticker OHLCV DataFrame}. Mirrors _reprice_us's batch pattern (already trusted
    by the maturity re-pricer) but keeps the FULL frame (Close+Volume) the momentum streams need,
    replacing N sequential per-name t.history(period='6mo') round-trips with ONE threaded call.
    EQUIVALENCE: the per-ticker frame extracted here is the SAME 6mo daily series .history() returns
    (group_by='ticker'; same yfinance auto-adjust default _reprice_us relies on), so the downstream
    s5/s6/RS math is byte-identical to the per-name path. FAIL-SAFE: any error -> {} so every name
    falls back to its own .history() (= pre-v1.111 behaviour); a ticker the batch can't serve
    (delisted .KA, thin name) is simply absent -> that name falls back per-name too. Coverage can
    NEVER regress. yfinance-only -> the sandbox cannot run it (Yahoo blocked); confirms on the runner."""
    cache = {}
    pairs = []                                   # (bare_ticker, yahoo_symbol)
    for c in candidates[:max_count]:
        tk = c.get('ticker')
        if not tk:
            continue
        # v1.124.1: suppress Yahoo-delisted PSX tickers from batch to kill error blocks
        if market == 'psx' and tk.upper() in _PSX_YAHOO_SKIP:
            continue
        pairs.append((tk, f'{tk}.KA' if market == 'psx' else tk))
    syms = [s for _, s in pairs]
    if not syms:
        return cache
    try:
        import yfinance as yf
        df = yf.download(syms, period='6mo', group_by='ticker', progress=False, threads=True)
        if df is None or getattr(df, 'empty', True):
            return cache
        multi = hasattr(df, 'columns') and getattr(df.columns, 'nlevels', 1) > 1
        if multi:
            lvl0 = set(df.columns.get_level_values(0))
            for tk, sym in pairs:
                if sym in lvl0:
                    try:
                        sub = df[sym]
                        if sub is not None and not sub.empty and 'Close' in sub.columns:
                            cache[tk] = sub
                    except Exception:
                        pass
        else:                                    # single-symbol download -> flat OHLCV frame
            if 'Close' in getattr(df, 'columns', []) and len(pairs) == 1:
                cache[pairs[0][0]] = df
    except Exception as e:
        warn(f'TCE batch history ({market}) failed for {len(syms)} ticker(s) -> per-name fallback: {e}')
        return {}
    return cache


# PSX tickers where Yahoo returns 'delisted' but TV scan still carries them.
# TCE reads last-good from batch cache; per-name fallback suppressed to avoid noisy logs.
_PSX_YAHOO_SKIP = {'GAL', 'QTECH', 'BFAGRO'}  # Yahoo marks as delisted; TV scan still carries them

def run_tce(candidates, market='us', max_count=20, spy_6mo_ret=None, prev_rev=None, prev_fwd=None):
    log(f'=== TCE on {market.upper()} ({len(candidates)} candidates) ===')
    if market == 'psx' and tce_psx_analyst is None:
        warn(f'D2 analyst overlay DISABLED — tce_psx_analyst import failed ({_TCE_PSX_IMPORT_ERR}). '
             f'Confirm tce_psx_analyst.py is committed to the repo root; PSX analyst streams '
             f'(s11_target_upside / s12_recommendation / s9_eps_revision) cannot fire until then.')
    prev_rev = prev_rev or {}
    prev_fwd = prev_fwd or {}
    tce_results = []
    # v1.111.0: pre-fetch the whole pool's 6mo history in ONE yf.download (frozen-engine speed cut);
    # per-name fallback inside compute_tce_streams preserves coverage exactly.
    _hist_cache = _batch_history_cache(candidates, market, max_count) if TCE_BATCH_HISTORY else None
    if _hist_cache:
        log(f'  TCE batch history: {len(_hist_cache)}/{min(len(candidates), max_count)} '
            f'names pre-fetched in one call ({market})')
    for c in candidates[:max_count]:
        ticker = c['ticker']
        try:
            # PSX has no yfinance fundamentals; feed the scanner's TTM growth so s7 can fire. US: None.
            _eg = c.get('eps_growth') if market == 'psx' else None
            _rg = c.get('rev_growth') if market == 'psx' else None
            _p3m = c.get('perf_3m') if market == 'psx' else None    # TV 3M perf -> s6 fallback when no .KA history
            _ar  = c.get('analyst')     # D2/Wave O L1: TV FactSet analyst row (PSX from scan, US from fetch_us_analyst_block)
            streams = compute_tce_streams(ticker, market, spy_6mo_ret=spy_6mo_ret,
                                          prev_rev_est=prev_rev.get(ticker),
                                          eps_growth_pct=_eg, rev_growth_pct=_rg, perf_3m=_p3m,
                                          analyst_row=_ar, prev_fwd_eps=prev_fwd.get(ticker),
                                          hist_cache=_hist_cache)
            tier_label, total, conv = tce_tier(streams, market)
            tce_results.append({
                'ticker': ticker, 'name': c.get('name', ticker), 'sector': c.get('sector', ''),
                'src': c.get('src', 'screen'),
                'tce_score': total, 'conviction': conv, 'tier': tier_label, 'streams': streams,
            })
            fired = [k for k in COUNTED if streams.get(k) == 1]
            log(f'  {ticker}: {tier_label} total={total} conv={conv} streams={fired}')
            time.sleep(YF_DELAY)
        except Exception as e:
            log(f'  · TCE {ticker}: {e}')

    tce_results.sort(key=lambda r: (r['tce_score'], r.get('conviction', 0)), reverse=True)
    high  = sum(1 for r in tce_results if r['tier'] == 'HIGH')
    watch = sum(1 for r in tce_results if r['tier'] == 'WATCH')
    log(f'  TCE: {high} HIGH, {watch} WATCH out of {len(tce_results)} scanned')
    return tce_results


def merge_tce_pool(small_caps, etf_stocks, cap_small=US_CANDIDATE_POOL, cap_etf=ETF_TCE_N):
    """Build the US TCE pool: small-cap screen survivors PLUS the ETF-consensus large-caps (so quality
    names like MU/INTC are visible to the engine). Dedup by ticker (screen survivor wins). The ETF
    names are sourced from the prior run's overlap, which is fine because Zacks ETF ranks update
    quarterly, not daily. Pure + unit-tested."""
    seen, out = set(), []
    for c in (small_caps or [])[:cap_small]:
        tk = c.get('ticker')
        if tk and tk not in seen:
            seen.add(tk); d = dict(c); d.setdefault('src', 'screen'); out.append(d)
    for s in (etf_stocks or [])[:cap_etf]:
        tk = s.get('ticker')
        if tk and tk not in seen:
            seen.add(tk)
            out.append({'ticker': tk, 'name': tk, 'sector': '', 'src': 'etf',
                        'etf_conviction': s.get('conviction')})
    return out


# =============================================================
# =============================================================
# 5b. EXPLOSIVE STAGE  — rebuilt per Explosive Screen Specification v1.1
#   Named conditions (see the spec doc):
#     G1 Revenue growth (TTM YoY) > 20%      G2 Operating-profit growth >= 15%
#     A1 OPNP  NP-growth / OP-growth > 1.5  (and OP-growth > 20%)
#     A2 OPPBT PBT-growth / OP-growth > 1.0
#     C1 CFONP CFO >= Net Profit (latest)   C3 SCFOSNP  sum(CFO) >= sum(NP)
#     F1 forward EPS growth > 20%  +  FR estimate raised vs prior  (additive booster)
#   INSUFFICIENT DATA is reserved for GENUINELY missing inputs only; a declining
#   company (OP growth <= 0) is a computed NOT EXPLOSIVE, not a data gap.
#   Banks/financials are carved out to the bank model (IM3 System B).
#   signal_a / signal_b are kept on the record for dashboard back-compat:
#     signal_a = growth gate (G1 & G2);  signal_b = acceleration (A1).
# =============================================================
G1_REV_MIN     = 20.0   # G1 revenue-growth threshold (D2: raised from 15%)
G2_OP_MIN      = 15.0   # G2 operating-profit-growth threshold
A1_OP_MIN      = 20.0   # A1 OPNP operating-profit-growth gate
A1_RATIO_MIN   = 1.0    # A1 OPNP NP/OP growth ratio (D4: deck literal '>OP'=1.0; 1.5 was a scanner artifact)
A2_PBT_RATIO   = 1.0    # A2 OPPBT PBT/OP growth ratio
F1_FWD_EPS_MIN = 20.0   # F1 forward EPS-growth booster
# Back-compat aliases (older references/logs that may import these names)
SIG_A_REV_MIN, SIG_A_OP_MIN  = G1_REV_MIN, G2_OP_MIN
SIG_B_OP_MIN, SIG_B_RATIO_MIN = A1_OP_MIN, A1_RATIO_MIN

# TRUE-BANK detection (option a). TradingView lumps ALL financials under sector
# 'Finance' (banks, REITs, royalties, insurers, asset managers), so sector alone
# cannot separate banks from non-banks. We carve ONLY true banks to the bank model
# (NIM/NPL/CAR fit banks, not REITs/royalties); non-bank financials stay in the
# screen and are scored on their real operating numbers.
_BANK_NAME_TOKENS = ('bank', 'bancorp', 'bancshares', 'banc ', 'banco', 'bankshares',
                     'savings', 'thrift', 'building society')
_KNOWN_BANKS = {  # PSX + obvious US banks whose names lack a bank token
    'MCB', 'HBL', 'UBL', 'NBP', 'BAFL', 'BAHL', 'MEBL', 'ABL', 'FABL', 'AKBL', 'BOP', 'BIPL',
    'COF', 'JPM', 'BAC', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'CFG', 'KEY', 'RF', 'HBAN', 'FITB',
    'CMA', 'ZION', 'MTB', 'SNV', 'WAL', 'EWBC', 'CADE', 'ISTR', 'CCNE', 'COFS', 'OSBC',
    'MCBS', 'PLBC', 'CARE', 'CFB', 'WSBC', 'NBN', 'FFIN',
}

def _is_true_bank(sector, name, ticker=None):
    n = (name or '').strip().lower(); s = (sector or '').strip().lower()
    if ticker and ticker.upper() in _KNOWN_BANKS: return True
    if any(tok in n for tok in _BANK_NAME_TOKENS): return True
    if s in ('banks', 'banking'): return True
    return False

def _yoy(stmt, *labels):
    """(curr, prev, yoy%) from the first matching row with >=2 points."""
    if stmt is None or getattr(stmt, 'empty', True): return None, None, None
    for label in labels:
        if label in stmt.index:
            row = stmt.loc[label].dropna()
            if len(row) >= 2:
                curr, prev = float(row.iloc[0]), float(row.iloc[1])
                yoy = round((curr - prev) / abs(prev) * 100, 1) if prev != 0 else None
                return curr, prev, yoy
    return None, None, None

def _sum_n(stmt, *labels):
    if stmt is None or getattr(stmt, 'empty', True): return None
    for label in labels:
        if label in stmt.index:
            row = stmt.loc[label].dropna()
            if len(row) >= 1:
                return float(row.iloc[:5].sum())
    return None

def explosive_conditions(income_stmt, cashflow_stmt=None, rev_g=None, op_g=None, np_g=None):
    """Evaluate the spec conditions. Statement inputs (US) take priority; embedded
    growths (PSX/fallback) are used when no statement is given. Unknown -> None."""
    pbt_g = None; ratio = None; c1 = None; c3 = None; prev_op = None
    if income_stmt is not None and not getattr(income_stmt, 'empty', True):
        _, _, rev_g   = _yoy(income_stmt, 'Total Revenue', 'Revenue')
        _, prev_op, op_g = _yoy(income_stmt, 'Operating Income', 'EBIT')
        _, _, np_g    = _yoy(income_stmt, 'Net Income', 'Net Income Common Stockholders')
        _, _, pbt_g   = _yoy(income_stmt, 'Pretax Income', 'Pre Tax Income', 'Pretax Income Loss')
    g1 = None if rev_g is None else bool(rev_g > G1_REV_MIN)
    g2 = None if op_g  is None else bool(op_g  >= G2_OP_MIN)
    if op_g is None or np_g is None:
        a1 = None
    elif (prev_op is not None and prev_op <= 0) or op_g <= 0:
        a1 = False  # ratio unreliable off a non-positive base -> evaluable, not accelerating
    else:
        ratio = round(np_g / op_g, 2) if op_g != 0 else None
        a1 = bool(op_g > A1_OP_MIN and ratio is not None and ratio > A1_RATIO_MIN)
    if pbt_g is None or op_g is None or op_g <= 0:
        a2 = None
    else:
        a2 = bool((pbt_g / op_g) > A2_PBT_RATIO)
    if cashflow_stmt is not None and not getattr(cashflow_stmt, 'empty', True) and income_stmt is not None:
        cfo_c, _, _ = _yoy(cashflow_stmt, 'Operating Cash Flow',
                           'Total Cash From Operating Activities',
                           'Cash Flow From Continuing Operating Activities')
        ni_c, _, _  = _yoy(income_stmt, 'Net Income', 'Net Income Common Stockholders')
        if cfo_c is not None and ni_c is not None: c1 = bool(cfo_c >= ni_c)
        scfo = _sum_n(cashflow_stmt, 'Operating Cash Flow',
                      'Total Cash From Operating Activities',
                      'Cash Flow From Continuing Operating Activities')
        snp  = _sum_n(income_stmt, 'Net Income', 'Net Income Common Stockholders')
        if scfo is not None and snp is not None: c3 = bool(scfo >= snp)
    return dict(rev_g=rev_g, op_g=op_g, np_g=np_g, pbt_g=pbt_g, ratio=ratio,
                g1=g1, g2=g2, a1=a1, a2=a2, c1=c1, c3=c3)

def classify_explosive(cond, partial_ok=False):
    rev_g, op_g, np_g = cond['rev_g'], cond['op_g'], cond['np_g']
    if rev_g is None and op_g is None and np_g is None:
        return 'INSUFFICIENT DATA'
    # PSX/fallback: revenue is known but operating/net profit aren't fetched at scan
    # time -> the profit & cash conditions can't be evaluated yet. Mark it honestly as
    # PENDING (the IM3 step finalises it from the statements) rather than asserting a
    # NOT-EXPLOSIVE result we didn't actually compute.
    if partial_ok and op_g is None and np_g is None and rev_g is not None:
        return 'PARTIAL — profit/cash data pending (IM3)'
    if op_g is not None and op_g <= 0:
        return 'NOT EXPLOSIVE — OP declining'
    growth = bool(cond['g1']) and bool(cond['g2'])
    accel  = bool(cond['a1'])
    # A4 (VAL-IND): cash-backing no longer GATES the EXPLOSIVE label. A strong young grower
    # whose reported cash does not yet back earnings (e.g. NVDA at scan time) was being demoted
    # out of the tab to QUALITY-GROWTH — exactly the name these tabs exist to surface early.
    # Cash-backing is now carried as the `cash_backed` INDICATOR on the record (annotation),
    # never an exclusion. Growth + acceleration = EXPLOSIVE; everything else is a descriptive
    # rank, not a filter (the dashboard surfaces all candidates ranked by strength_score).
    if growth and accel:  return 'EXPLOSIVE — both signals'
    if growth:            return 'QUALITY-GROWTH (growth, not accelerating)'
    if accel:             return 'INFLECTION (accelerating off low base — verify)'
    return 'NOT EXPLOSIVE'

def _forward_boost(c):
    """F1 (forward EPS growth > 20%) + FR (estimate raised vs prior). Additive,
    never blocks. Reads the TV FactSet analyst_row if the candidate carries one."""
    ar = c.get('analyst_row') or {}
    fwd = ar.get('earnings_per_share_forecast_next_fq') or ar.get('earnings_per_share_forecast_fq')
    cur = ar.get('earnings_per_share_fq')
    f1 = None
    if fwd is not None and cur not in (None, 0):
        try: f1 = bool(((float(fwd) - float(cur)) / abs(float(cur)) * 100) > F1_FWD_EPS_MIN)
        except Exception: f1 = None
    fr = None; pf = c.get('prev_fwd_eps')
    if fwd is not None and pf is not None:
        try: fr = bool(float(fwd) > float(pf))
        except Exception: fr = None
    return f1, fr

def _build_explosive_rec(c, cond, verdict, ratio, eps, src, f1, fr):
    growth_known = (cond['g1'] is not None and cond['g2'] is not None)
    sig_a = (bool(cond['g1']) and bool(cond['g2'])) if growth_known else None
    if cond['c1'] or cond['c3']:                          cg = 'confirmed'
    elif cond['c1'] is False and cond['c3'] is False:     cg = 'fail'
    else:                                                 cg = 'na_confirm_im3'
    # A4 (VAL-IND): per-signal INDICATORS (annotations, never filters) + a 0-4 strength_score
    # the dashboard ranks by, so no single weak signal hides a name. cash_backed and op_declining
    # are surfaced as indicators rather than gating/demoting the verdict.
    growth      = (bool(cond['g1']) and bool(cond['g2']))
    accel       = bool(cond['a1'])
    cash_backed = bool(cond['c1']) or bool(cond['c3'])
    op_declining = (cond['op_g'] is not None and cond['op_g'] <= 0)
    strength_score = sum([growth, accel, bool(cond['a2']), cash_backed])   # 0-4 strength pillars
    indicators = {'growth': growth, 'acceleration': accel, 'pbt_accel': bool(cond['a2']),
                  'cash_backed': cash_backed, 'op_declining': op_declining}
    return {
        'ticker':          c.get('ticker'),
        'name':            c.get('name', c.get('ticker')),
        'sector':          c.get('sector', ''),
        'price':           c.get('price'),   # Wave T: carry price so the shortlist tracker covers the Explosive tab
        'rev_growth':      cond['rev_g'],
        'op_growth':       cond['op_g'],
        'np_growth':       cond['np_g'],
        'pbt_growth':      cond['pbt_g'],
        'eps_growth':      eps,
        'op_np_ratio':     ratio,
        'signal_a':        sig_a,
        'signal_b':        cond['a1'],
        'conditions':      {k: cond[k] for k in ('g1', 'g2', 'a1', 'a2', 'c1', 'c3')},
        'indicators':      indicators,
        'strength_score':  strength_score,
        'cash_backed':     cash_backed,
        'perf_6m':         c.get('perf_6m'),   # Wave A / V-G-M: price momentum (US 6M; PSX uses perf_3m)
        'perf_3m':         c.get('perf_3m'),   # Wave A / V-G-M: price momentum (3M, both markets)
        'ma':              c.get('ma'),        # Wave M-A: per-name MA trend reads (both markets)
        'forward':         {'f1': f1, 'fr': fr},
        'forward_boost':   bool(f1) or bool(fr),
        'verdict':         verdict,
        'cash_guardrails': cg,
        'growth_source':   c.get('growth_source', src),
        'fidelity':        'im3_screen',
    }

def score_explosive_candidate(c, partial_ok=False):
    """PSX / fallback path: score from embedded rev/op/np growth fields.
    partial_ok=True (PSX) marks profit/cash-pending names PARTIAL for IM3 to finalise."""
    cond = explosive_conditions(None, None, rev_g=c.get('rev_growth'),
                                op_g=c.get('op_growth'), np_g=c.get('np_growth'))
    verdict = classify_explosive(cond, partial_ok=partial_ok)
    rev = c.get('rev_growth'); eps = c.get('eps_growth'); ratio = cond['ratio']
    if ratio is None and rev not in (None, 0) and eps is not None and rev > 0:
        try: ratio = round(eps / rev, 2)
        except Exception: ratio = None
    f1, fr = _forward_boost(c)
    return _build_explosive_rec(c, cond, verdict, ratio, eps, 'embedded', f1, fr)

# ===== v1.112.0 performance + correctness helpers (audit F1-F6) =====
_SWALLOWED = {}
def _swallow(where):
    """F6: count a deliberately-swallowed exception in a load-bearing spot so a degraded data leg
    (e.g. a failed cashflow fetch silently reading as 'not cash-backed') surfaces in the run summary."""
    _SWALLOWED[where] = _SWALLOWED.get(where, 0) + 1

# v1.112.1: the explosive statement cache now persists INSIDE data.json (committed every run by the
# workflow) instead of a side file GitHub Actions never commits — so the cross-run cache actually
# survives and the ~113s Explosive-screen win lands from the SECOND run on (the SAME persist-via-the-
# existing-commit mechanism Wave-T history + shortlist tracking already use; no daily.yml change).
_EXPLOSIVE_CACHE_OUT = {}   # handed back to main() to store in data['explosive_stmt_cache']
def _load_explosive_cache():
    try:
        prior = EXISTING.get('explosive_stmt_cache') if isinstance(EXISTING, dict) else None
        cache = dict(prior) if isinstance(prior, dict) else {}
    except Exception:
        cache = {}
    # prune entries older than 30d (well past the 7d freshness window) so the stored dict stays bounded
    _today = dt.date.today(); _kept = {}
    for _k, _v in cache.items():
        try:
            if isinstance(_v, dict) and (_today - dt.date.fromisoformat(_v.get('date', ''))).days <= 30:
                _kept[_k] = _v
        except Exception:
            pass
    return _kept
def _save_explosive_cache(cache):
    global _EXPLOSIVE_CACHE_OUT
    _EXPLOSIVE_CACHE_OUT = cache if isinstance(cache, dict) else {}
def _explosive_cache_fresh(entry):
    try:
        return (dt.date.today() - dt.date.fromisoformat(entry.get('date', ''))).days < EXPLOSIVE_STMT_CACHE_DAYS
    except Exception:
        return False
def _cond_jsonable(cond):
    """Coerce an explosive cond dict to plain JSON types (np.float64/np.bool_ -> float/bool) so it caches cleanly."""
    out = {}
    for _k, _v in cond.items():
        if _v is None:
            out[_k] = None
        elif isinstance(_v, bool) or _v.__class__.__name__ in ('bool_', 'bool8'):
            out[_k] = bool(_v)
        else:
            try:
                out[_k] = float(_v)
            except Exception:
                out[_k] = _v
    return out
def _staleness_days(as_of):
    """Best-effort age (days) of a human as-of date string; None if unparseable (never fabricate freshness)."""
    if not as_of or not isinstance(as_of, str):
        return None
    _s = as_of.strip()
    for _f in ('%B %d, %Y', '%b %d, %Y', '%d-%b-%Y', '%d-%B-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d %b %Y', '%d %B %Y'):
        try:
            return (dt.date.today() - dt.datetime.strptime(_s, _f).date()).days
        except Exception:
            continue
    return None
# ===== end v1.112.0 helpers =====


def run_explosive(candidates, market='us'):
    log(f'=== EXPLOSIVE screen on {market.upper()} ({len(candidates)} candidates) ===')
    yf = None
    if market == 'us':
        try: import yfinance as yf
        except ImportError: yf = None
    # v1.112.0 (F2): income statements change quarterly, so re-fetching ~200 US candidates'
    # income_stmt twice a day (~113s) is wasted. Cache the COMPUTED cond dict per ticker for
    # EXPLOSIVE_STMT_CACHE_DAYS; a fresh hit skips BOTH the income_stmt and the lazy cashflow fetch.
    # Live price/perf/MA on each rec still come from `c` (recomputed every run) -> only the quarterly
    # statement-derived conditions are cached, so a verdict can't go stale within the window; a miss
    # fetches + recomputes + stores, so coverage can't regress.
    _stmt_cache = _load_explosive_cache() if market == 'us' else {}
    _cache_hits = _cache_fetched = 0; _cache_dirty = False
    out = []
    for c in candidates:
        try:
            ticker = c.get('ticker'); rec = None
            # US path: statement-derived conditions; cash leg fetched lazily only
            # when a name is provisionally EXPLOSIVE (keeps the extra call count tiny).
            if market == 'us' and yf is not None:
                _ce = _stmt_cache.get(ticker)
                if _ce is not None and _explosive_cache_fresh(_ce) and isinstance(_ce.get('cond'), dict):
                    cond = _ce['cond']; _cache_hits += 1
                    verdict = classify_explosive(cond)
                    f1, fr = _forward_boost(c)
                    rec = _build_explosive_rec(c, cond, verdict, cond.get('ratio'),
                                               c.get('eps_growth'), 'yf_stmt_im3', f1, fr)
                else:
                    try:
                        stmt = yf.Ticker(ticker).income_stmt
                        cond = explosive_conditions(stmt, None)
                        if not (cond['rev_g'] is None and cond['op_g'] is None and cond['np_g'] is None):
                            if bool(cond['g1']) and bool(cond['g2']) and bool(cond['a1']):
                                try:
                                    cfs = yf.Ticker(ticker).cashflow
                                    cond = explosive_conditions(stmt, cfs)
                                except Exception:
                                    _swallow('explosive.cashflow')
                            verdict = classify_explosive(cond)
                            f1, fr = _forward_boost(c)
                            rec = _build_explosive_rec(c, cond, verdict, cond['ratio'],
                                                       c.get('eps_growth'), 'yf_stmt_im3', f1, fr)
                            _stmt_cache[ticker] = {'cond': _cond_jsonable(cond),
                                                   'date': dt.date.today().isoformat()}
                            _cache_fetched += 1; _cache_dirty = True
                    except Exception:
                        _swallow('explosive.income_stmt')
                    time.sleep(YF_DELAY)
            # Fallback / PSX: embedded growth fields. PSX gets partial_ok=True so names
            # whose statements aren't fetched at scan time read PARTIAL (the IM3 step
            # finalises them) instead of a NOT-EXPLOSIVE we didn't actually compute.
            if rec is None:
                rec = score_explosive_candidate(c, partial_ok=(market == 'psx'))
            # TRUE-BANK carve-out (option a): only actual banks route to the bank model
            # (their NIM/NPL/CAR live there). Non-bank financials (REITs, royalties, asset
            # managers, insurers) stay in the screen, scored on their real operating numbers.
            if rec is not None:
                isbank = _is_true_bank(rec.get('sector'), rec.get('name'), rec.get('ticker'))
                rec['is_financial'] = isbank
                if isbank:
                    rec['verdict'] = 'FINANCIAL — score via bank model (IM3 System B)'
            if rec:
                out.append(rec)
                log(f'  {rec["ticker"]}: A={rec["signal_a"]} B={rec["signal_b"]} -> {rec["verdict"]}')
        except Exception as e:
            log(f'  · explosive {c.get("ticker")}: {e}')
    if market == 'us':
        _save_explosive_cache(_stmt_cache)   # v1.112.1: ALWAYS hand back (carry the cache forward even on an all-hit run -> never wipes data.json's cache)
        log(f'  [Explosive cache] {_cache_hits} hit / {_cache_fetched} fetched '
            f'(income_stmt cached {EXPLOSIVE_STMT_CACHE_DAYS}d, persisted in data.json)')
    out.sort(key=lambda r: (r.get('strength_score') or 0,
                            str(r.get('verdict', '')).startswith('EXPLOSIVE'),
                            r.get('op_growth') or r.get('eps_growth') or -999), reverse=True)
    both = sum(1 for r in out if str(r.get('verdict', '')).startswith('EXPLOSIVE'))
    fin  = sum(1 for r in out if r.get('is_financial'))
    insf = sum(1 for r in out if 'INSUFFICIENT' in str(r.get('verdict', '')))
    log(f'  EXPLOSIVE: {both} both-signal of {len(out)} scored; '
        f'{fin} financials -> bank model; {insf} insufficient-data')
    return out


# =============================================================
# 6. IM3 162-POINT SCORING ENGINE
# Replicates every formula from IM3_0 Scoring Template Excel.
# Two scoring paths:
#   score_im3_standard() — non-bank stocks (full 40 metrics)
#   score_im3_bank()     — bank/financial stocks (6 metrics replaced)
# Entry point: score_im3(ticker) → dict with score, grade, details
# =============================================================

# --- Weightage (max points per metric, from Weightage_Stocks_By_Ammar_Yaseen.xlsx)
IM3_WEIGHTS = {
    'rev_cagr':       5,  'op_cagr':        1,  'op_margin':      5,
    'np_cagr':        1,  'np_margin':       5,  'tax_rate':       3,
    'int_coverage':   2,  'de_ratio':        5,  'current_ratio':  5,
    'cfo_trend':      5,  'net_cash':        3,  'ccfo_cpat':      5,
    'eps_trend':      5,  'pe_ratio':        5,  'peg_ratio':      5,
    'pb_ratio':       3,  'ps_ratio':        3,  'div_yield':      5,
    'earn_yield':     3,  'graham_val':      3,  'ev_ebitda':      3,
    'roe':            3,  'mos':             5,  'val_shareholders':5,
    'inv_turn':       3,  'dro':             3,  'nfa_turn':       3,
    'fat':            3,  'fcf_trend':       5,  'croic':          5,
    'fcf_sale':       5,  'fcf_cfo':         3,  'ccc':            3,
    'altman_z':       5,  'beneish_m':       5,  'piotroski_f':   10,
    'roic_wacc':      3,  'total_debt':      3,  'cash_share':     5,
    'cash_debt':      5,
}
# Bank replacement weights. Canonical Sarmaaya "Financial Analysis of a Bank" (Week 6)
# framework + Banking_IG_Architecture: banks are scored ONLY on bank-applicable factors.
# Everything industrial is zeroed so it counts in neither score nor denominator.
IM3_BANK_WEIGHTS = {k: v for k, v in IM3_WEIGHTS.items()}
# Zero metrics that DO NOT apply to a leveraged spread/credit business:
#   - inventory/coverage/working-capital (industrial ops): int_coverage, current_ratio,
#     inv_turn, dro, fat, ccc, nfa_turn
#   - leverage ratios (a bank is leveraged 10-15x BY DESIGN): de_ratio, total_debt
#   - FCF/operating concepts banks don't report the industrial way: op_cagr, op_margin,
#     fcf_trend, croic, fcf_sale, fcf_cfo, cash_share, cash_debt
#   - industrial valuation (no EBITDA; P/S, PEG, Graham, IV-MoS not bank-appropriate —
#     canonical bank valuation is price-to-tangible-book): ev_ebitda, ps_ratio,
#     peg_ratio, graham_val, mos, val_shareholders
#   - quality models built for non-financials (the deck/architecture say so explicitly):
#     piotroski_f, altman_z, beneish_m, roic_wacc
_BANK_ZERO = ('int_coverage', 'current_ratio', 'inv_turn', 'dro', 'fat', 'ccc', 'nfa_turn',
              'de_ratio', 'total_debt',
              'op_cagr', 'op_margin', 'fcf_trend', 'croic', 'fcf_sale', 'fcf_cfo',
              'cash_share', 'cash_debt',
              'ev_ebitda', 'ps_ratio', 'peg_ratio', 'graham_val', 'mos', 'val_shareholders',
              'piotroski_f', 'altman_z', 'beneish_m', 'roic_wacc')
for _bk in _BANK_ZERO:
    IM3_BANK_WEIGHTS[_bk] = 0
# Bank-applicable kept from the industrial template (canonical mappings):
#   rev_cagr->Markup growth, np_cagr->Net Profit growth, np_margin->Net Margin,
#   tax_rate, eps_trend->EPS, cfo_trend->CFO, net_cash->Net Change in Cash,
#   ccfo_cpat->cCFO vs cPAT, roe->ROE, pe/pb/earn_yield/div_yield->valuation.
# Add bank-specific stability/business ratios:
IM3_BANK_WEIGHTS.update({
    'nim':   4,   # Net Interest Margin
    'casa':  3,   # CASA ratio
    'adr':   3,   # Advance-to-Deposit Ratio
    'npl':   5,   # Non-Performing Loans / Gross Loans
    'car':   4,   # Capital Adequacy Ratio
})
# Applicable bank max ~= 70 pts (51 retained industrial + 19 bank); the scorer computes
# the denominator from applicable, non-NA metrics so banks are no longer scored out of 162.

# Points conversion: GOOD=100%, WATCH=60%, BAD=20%, NA=0%
def _pts(verdict, max_pts):
    if verdict == 'GOOD':   return max_pts
    if verdict == 'WATCH':  return round(max_pts * 0.6)
    if verdict == 'BAD':    return round(max_pts * 0.2)
    return 0  # N/A or missing


def _safe_get(df, keys, yr=0):
    """Get a value from a multi-index yfinance dataframe safely."""
    if df is None or df.empty:
        return None
    for k in (keys if isinstance(keys, list) else [keys]):
        try:
            row = df.loc[df.index.str.lower() == k.lower()]
            if not row.empty:
                cols = row.columns.tolist()
                if yr < len(cols):
                    v = row.iloc[0, yr]
                    if v is not None and str(v) not in ('nan', 'None', ''):
                        import numpy as _np
                        return float(v) if not _np.isnan(float(v)) else None
        except Exception:
            pass
    return None


def _series(df, keys, n=6):
    """Get up to n annual values (TTM first) for a line item."""
    if df is None or df.empty:
        return []
    for k in (keys if isinstance(keys, list) else [keys]):
        try:
            row = df.loc[df.index.str.lower() == k.lower()]
            if not row.empty:
                vals = []
                for c in row.columns[:n]:
                    v = row.iloc[0][c]
                    try:
                        fv = float(v)
                        import numpy as _np
                        vals.append(fv if not _np.isnan(fv) else None)
                    except Exception:
                        vals.append(None)
                return vals
        except Exception:
            pass
    return []


def _avg(lst, n=None):
    """Average of first n non-None values."""
    vals = [v for v in (lst[:n] if n else lst) if v is not None]
    return sum(vals) / len(vals) if vals else None


def _cagr(series, yrs=5):
    """CAGR from series[0] (TTM) to series[yrs] over yrs years.
    IM3 formula: (E8/J8)^(1/5) - 1"""
    if len(series) <= yrs:
        return None
    start, end = series[yrs], series[0]
    if start is None or end is None or start <= 0 or end <= 0:
        return None
    return (end / start) ** (1 / yrs) - 1


def _dcf_fcf(fcf_per_share_series, price, disc_g=0.12, disc_t=0.04):
    """10-year DCF using FCF per share. Growth capped 5-20%.
    IM3: rows 138-145. Sarmaaya website formula replicated."""
    if not fcf_per_share_series or price is None:
        return None
    growth_rates = []
    for i in range(len(fcf_per_share_series) - 1):
        a, b = fcf_per_share_series[i], fcf_per_share_series[i + 1]
        if a is not None and b is not None and b != 0:
            growth_rates.append((a - b) / abs(b) * 100)
    if not growth_rates:
        return None
    avg_g = _avg(growth_rates)
    if avg_g is None:
        return None
    g = max(5.0, min(20.0, avg_g)) / 100
    base = fcf_per_share_series[0]
    if base is None:
        return None
    pv = sum(base * (1 + g) ** y / (1 + disc_g) ** y for y in range(1, 11))
    tv = base * (1 + g) ** 10 * (1 + disc_t) / ((disc_g - disc_t) * (1 + disc_g) ** 10)
    return pv + tv


def _dcf_eps(eps, avg_eps_growth_pct, bond_yield):
    """IM3 formula row 158: EPS*(8.5+2*MIN(MAX(g,0.03),0.25))*4.4/bond_yield"""
    if eps is None or bond_yield is None or bond_yield <= 0:
        return None
    g = max(0.03, min(0.25, (avg_eps_growth_pct or 5) / 100))
    return eps * (8.5 + 2 * g) * 4.4 / bond_yield


def _dcf_cash(cash_per_share_series, price, disc_g=0.12, disc_t=0.04):
    """Same structure as DCF FCF but using cash per share (rows 162-175)."""
    return _dcf_fcf(cash_per_share_series, price, disc_g, disc_t)


def _projected_fcf(avg_6yr_fcf, shares, equity, growth=0.09, price=None):
    """IM3 rows 179-191. Projected FCF = avg_6yr_fcf * (1+g) / shares"""
    if avg_6yr_fcf is None or shares is None or shares <= 0:
        return None
    return avg_6yr_fcf * (1 + growth) / shares


def _projected_cash(avg_6yr_cash, shares, equity, growth=0.09, price=None):
    """IM3 rows 179-193. Same as projected FCF using cash."""
    return _projected_fcf(avg_6yr_cash, shares, equity, growth, price)


def _peter_lynch(peg, avg_ebitda_growth_pct, eps):
    """IM3 row 203: PEG * MIN(MAX(EBITDA_g/100, 0.05), 0.20) * EPS"""
    if peg is None or eps is None:
        return None
    g = max(0.05, min(0.20, (avg_ebitda_growth_pct or 5) / 100))
    return peg * g * eps


def _altman_z(wc, re, ebit, equity, debt, ta):
    """Altman Z' for non-manufacturers:
    6.56*WC/TA + 3.26*RE/TA + 6.72*EBIT/TA + 1.05*Equity/Debt"""
    if any(v is None for v in [wc, re, ebit, equity, debt, ta]):
        return None
    if ta <= 0 or debt <= 0:
        return None
    return 6.56*(wc/ta) + 3.26*(re/re if False else re/ta) + 6.72*(ebit/ta) + 1.05*(equity/debt)


def _beneish_m(rev, rev_prev, ar, ar_prev, gp, gp_prev, ta, ta_prev,
               ppe, ppe_prev, sga, sga_prev, dep, dep_prev,
               ni, cfo, ltd, ltd_prev):
    """Beneish M-Score 8-variable model."""
    try:
        dsri = (ar / rev) / (ar_prev / rev_prev) if ar_prev and rev_prev else None
        gmi  = (gp_prev / rev_prev) / (gp / rev) if gp and rev else None
        aqi  = (1 - (ar + ppe) / ta) / (1 - (ar_prev + ppe_prev) / ta_prev) \
               if ta and ta_prev else None
        sgi  = rev / rev_prev if rev_prev else None
        depi = (dep_prev / (ppe_prev + dep_prev)) / (dep / (ppe + dep)) \
               if dep and ppe else None
        sgai = (sga / rev) / (sga_prev / rev_prev) if sga and sga_prev and rev_prev else None
        lvgi = ((ltd + (ta - ta)) / ta) / ((ltd_prev + (ta_prev - ta_prev)) / ta_prev) \
               if ta and ta_prev else None
        tata = (ni - cfo) / ta if ta else None
        vals = [dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata]
        coef = [-4.84, 0.920, 0.528, 0.404, 0.892, 0.115, 0.172, 4.679, -0.327]
        # Intercept + coefficients
        score = -4.84
        pairs = list(zip(coef[1:], vals))
        for c, v in pairs:
            if v is None:
                return None
            score += c * v
        return score
    except Exception:
        return None


def _piotroski_f(ni, cfo, roa, roa_prev, cfo_ta, delta_leverage,
                 delta_current_ratio, delta_shares, delta_gm, delta_turnover):
    """9 binary Piotroski checks. Returns 0-9."""
    score = 0
    # Profitability (4)
    if ni is not None and ni > 0: score += 1
    if cfo is not None and cfo > 0: score += 1
    if roa is not None and roa_prev is not None and roa > roa_prev: score += 1
    if cfo_ta is not None and roa is not None and cfo_ta > roa: score += 1
    # Leverage / Liquidity (3)
    if delta_leverage is not None and delta_leverage <= 0: score += 1
    if delta_current_ratio is not None and delta_current_ratio >= 0: score += 1
    if delta_shares is not None and delta_shares <= 0: score += 1
    # Operating efficiency (2)
    if delta_gm is not None and delta_gm >= 0: score += 1
    if delta_turnover is not None and delta_turnover >= 0: score += 1
    return score


def _roic(ebit, tax_rate, debt, equity, cash):
    """ROIC = NOPAT / Invested Capital"""
    if any(v is None for v in [ebit, tax_rate, debt, equity, cash]):
        return None
    nopat = ebit * (1 - tax_rate)
    ic = debt + equity - cash
    if ic <= 0:
        return None
    return nopat / ic


def _wacc_simple(beta, rf=0.043, erp=0.055, debt=0, equity=0, kd=0.06, tax=0.21):
    """Simple WACC. rf = 10Y Treasury (from FRED), erp = equity risk premium."""
    if beta is None:
        return None
    ke = rf + beta * erp
    v = debt + equity
    if v <= 0:
        return ke
    return (equity / v) * ke + (debt / v) * kd * (1 - tax)


def _mos(iv, price):
    """Margin of Safety = (IV - Price) / IV"""
    if iv is None or price is None or iv <= 0:
        return None
    return (iv - price) / iv


# --- BANK DETECTION ---
def _is_bank(info):
    """Detect bank/financial via yfinance info sector/industry."""
    sector   = (info.get('sector') or '').lower()
    industry = (info.get('industry') or '').lower()
    bank_keywords = ('bank', 'financial services', 'insurance', 'savings',
                     'thrift', 'credit', 'mortgage', 'diversified financial')
    non_bank_overrides = ('software', 'technology', 'biotech', 'pharma')
    if any(k in industry for k in non_bank_overrides):
        return False
    return any(k in sector or k in industry for k in bank_keywords)


# --- FETCH IM3 FINANCIALS ---
def _fetch_im3_data(ticker):
    """Fetch all data needed for 40-metric IM3 scoring from yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return None

    try:
        t = yf.Ticker(ticker)
        info    = t.info or {}
        inc     = t.income_stmt       # annual, TTM first
        bal     = t.balance_sheet     # annual
        cf      = t.cashflow          # annual

        # Normalise index to lowercase for _series/_safe_get
        for df in (inc, bal, cf):
            if df is not None and not df.empty:
                df.index = df.index.str.lower().str.strip()

        return {
            'info': info,
            'inc':  inc,
            'bal':  bal,
            'cf':   cf,
        }
    except Exception as e:
        log(f'  IM3 fetch error {ticker}: {e}')
        return None


# --- SCORE ONE METRIC ---
def _score_metric(key, verdict, weights):
    max_pts = weights.get(key, 0)
    pts = _pts(verdict, max_pts)
    return {'key': key, 'verdict': verdict, 'pts': pts, 'max': max_pts}


# --- STANDARD (NON-BANK) SCORING ---
def _score_standard(ticker, d, bond_yield=0.043):
    """
    Score all 40 IM3 metrics for a non-bank stock.
    Returns list of metric dicts and intrinsic value summary.
    """
    info = d['info']
    inc  = d['inc']
    bal  = d['bal']
    cf   = d['cf']
    W    = IM3_WEIGHTS

    price  = info.get('currentPrice') or info.get('regularMarketPrice')
    shares = info.get('sharesOutstanding')
    beta   = info.get('beta')

    metrics = []

    # ── GROWTH ───────────────────────────────────────────────
    rev  = _series(inc, ['total revenue', 'totalrevenue', 'revenue'])
    op   = _series(inc, ['operating income', 'ebit', 'operatingincome'])
    np_  = _series(inc, ['net income', 'netincome'])
    eps_ = _series(inc, ['diluted eps', 'basic eps', 'eps diluted', 'eps'])

    # Use info EPS history if income_stmt sparse
    if len([v for v in eps_ if v]) < 2:
        eps_ttm = info.get('trailingEps')
        if eps_ttm:
            eps_ = [eps_ttm] + eps_

    # Revenue CAGR ≥15% = GOOD
    rev_cagr = _cagr(rev, 5)
    v = 'GOOD' if rev_cagr is not None and rev_cagr >= 0.15 else \
        'WATCH' if rev_cagr is not None else 'NA'
    metrics.append(_score_metric('rev_cagr', v, W))

    # Operating Profit CAGR ≥15%
    op_cagr = _cagr(op, 5)
    v = 'GOOD' if op_cagr is not None and op_cagr >= 0.15 else \
        'WATCH' if op_cagr is not None else 'NA'
    metrics.append(_score_metric('op_cagr', v, W))

    # Operating Margin ≥12%
    op_margin = (op[0] / rev[0]) if op and rev and rev[0] else None
    v = 'GOOD' if op_margin is not None and op_margin >= 0.12 else \
        'WATCH' if op_margin is not None else 'NA'
    metrics.append(_score_metric('op_margin', v, W))

    # Net Profit CAGR ≥15%
    np_cagr = _cagr(np_, 5)
    v = 'GOOD' if np_cagr is not None and np_cagr >= 0.15 else \
        'WATCH' if np_cagr is not None else 'NA'
    metrics.append(_score_metric('np_cagr', v, W))

    # Net Margin ≥8%
    np_margin = (np_[0] / rev[0]) if np_ and rev and rev[0] else None
    v = 'GOOD' if np_margin is not None and np_margin >= 0.08 else \
        'WATCH' if np_margin is not None else 'NA'
    metrics.append(_score_metric('np_margin', v, W))

    # ── STABILITY ─────────────────────────────────────────────
    # Tax Rate ≥21% (at/near corp rate = GOOD; evasion/loss = WATCH)
    tax_exp  = _series(inc, ['tax provision', 'income tax expense',
                              'incometaxexpense', 'taxprovision'])
    pbt      = _series(inc, ['pretax income', 'income before tax',
                              'incomebeforetax', 'ebt'])
    tax_rate = (tax_exp[0] / pbt[0]) if tax_exp and pbt and pbt[0] else \
               info.get('effectiveTaxRate')
    v = 'GOOD' if tax_rate is not None and tax_rate >= 0.21 else \
        'WATCH' if tax_rate is not None else 'NA'
    metrics.append(_score_metric('tax_rate', v, W))

    # Interest Coverage >5
    int_exp  = _series(inc, ['interest expense', 'interestexpense'])
    int_exp0 = abs(int_exp[0]) if int_exp and int_exp[0] else None
    int_cov  = info.get('interestCoverage') or \
               ((op[0] / int_exp0) if op and int_exp0 else None)
    v = 'GOOD' if int_cov is not None and int_cov > 5 else \
        'WATCH' if int_cov is not None else 'NA'
    metrics.append(_score_metric('int_coverage', v, W))

    # D/E <0.5 GOOD, <1 WATCH, ≥1 BAD
    de = info.get('debtToEquity')
    if de is not None:
        de = de / 100 if de > 10 else de  # yfinance sometimes returns as percentage
    v = 'GOOD' if de is not None and de < 0.5 else \
        'WATCH' if de is not None and de < 1.0 else \
        'BAD'  if de is not None else 'NA'
    metrics.append(_score_metric('de_ratio', v, W))

    # Total Debt 3yr avg < 5yr avg = GOOD (debt declining)
    td_s = _series(bal, ['long term debt', 'total debt', 'longtermdebt', 'totaldebt'])
    td3  = _avg(td_s, 3)
    td5  = _avg(td_s, 5)
    v = 'GOOD' if td3 is not None and td5 is not None and td3 < td5 else \
        'WATCH' if td3 is not None else 'NA'
    metrics.append(_score_metric('total_debt', v, W))

    # Current Ratio ≥1.5 GOOD, ≥1 WATCH, <1 BAD
    cr = info.get('currentRatio')
    v = 'GOOD' if cr is not None and cr >= 1.5 else \
        'WATCH' if cr is not None and cr >= 1.0 else \
        'BAD'  if cr is not None else 'NA'
    metrics.append(_score_metric('current_ratio', v, W))

    # CFO 3yr avg > 5yr avg
    cfo_s = _series(cf, ['operating cash flow', 'cash from operations',
                          'operatingcashflow', 'cashfromoperations',
                          'total cash from operating activities'])
    cfo3  = _avg(cfo_s, 3)
    cfo5  = _avg(cfo_s, 5)
    v = 'GOOD' if cfo3 is not None and cfo5 is not None and cfo3 > cfo5 else \
        'WATCH' if cfo3 is not None else 'NA'
    metrics.append(_score_metric('cfo_trend', v, W))

    # Net Change in Cash: TTM > prior = GOOD, TTM > 0 = WATCH, <0 = BAD
    ncc_s = _series(cf, ['changes in cash', 'net change in cash',
                          'change in cash and cash equivalents',
                          'netchangeincash'])
    ncc0 = ncc_s[0] if ncc_s else None
    ncc1 = ncc_s[1] if len(ncc_s) > 1 else None
    v = 'GOOD' if ncc0 is not None and ncc1 is not None and ncc0 > ncc1 else \
        'WATCH' if ncc0 is not None and ncc0 > 0 else \
        'BAD'  if ncc0 is not None else 'NA'
    metrics.append(_score_metric('net_cash', v, W))

    # cCFO vs cPAT: sum 5yr CFO > sum 5yr Net Income
    cum_cfo = sum(v for v in cfo_s[:6] if v is not None)
    cum_np  = sum(v for v in np_[:6]   if v is not None)
    v = 'GOOD' if cum_cfo and cum_np and cum_cfo > cum_np else \
        'WATCH' if cum_cfo and cum_np else 'NA'
    metrics.append(_score_metric('ccfo_cpat', v, W))

    # NFAT (Net Fixed Asset Turnover) 3yr > 5yr
    ppe_s = _series(bal, ['net ppe', 'property plant equipment net',
                           'netppe', 'propertyplantequipmentnet',
                           'gross ppe', 'property plant and equipment'])
    rev_s = rev
    nfat_s = []
    for i in range(min(len(rev_s), len(ppe_s))):
        avg_ppe = ((ppe_s[i] + (ppe_s[i+1] if i+1 < len(ppe_s) else ppe_s[i])) / 2) \
                  if ppe_s[i] else None
        nfat_s.append((rev_s[i] / avg_ppe) if avg_ppe and rev_s[i] else None)
    nfat3 = _avg(nfat_s, 3)
    nfat5 = _avg(nfat_s, 5)
    v = 'GOOD' if nfat3 is not None and nfat5 is not None and nfat3 > nfat5 else \
        'WATCH' if nfat3 is not None else 'NA'
    metrics.append(_score_metric('nfa_turn', v, W))

    # ROE ≥20%
    roe = info.get('returnOnEquity')
    v = 'GOOD' if roe is not None and roe >= 0.20 else \
        'WATCH' if roe is not None else 'NA'
    metrics.append(_score_metric('roe', v, W))

    # ── EPS / VALUATION ───────────────────────────────────────
    # EPS: 3yr avg > 5yr avg
    eps_3 = _avg(eps_, 3)
    eps_5 = _avg(eps_, 5)
    v = 'GOOD' if eps_3 is not None and eps_5 is not None and eps_3 > eps_5 else \
        'WATCH' if eps_3 is not None else 'NA'
    metrics.append(_score_metric('eps_trend', v, W))

    # P/E vs peer: use sector average; without peer, check < 25 = GOOD (reasonable)
    pe = info.get('trailingPE') or info.get('forwardPE')
    peer_pe = info.get('forwardPE', 25)  # Fallback: compare to forward estimate
    v = 'GOOD'  if pe is not None and pe > 0 and pe <= peer_pe * 1.1 else \
        'WATCH' if pe is not None and pe > 0 and pe <= peer_pe * 1.3 else \
        'BAD'   if pe is not None and pe > 0 else 'NA'
    metrics.append(_score_metric('pe_ratio', v, W))

    # EBITDA Growth >15% (not a separate weightage row — feeds PEG context)
    ebitda_s = _series(inc, ['ebitda', 'normalized ebitda'])
    ebitda_g = ((ebitda_s[0] - ebitda_s[1]) / abs(ebitda_s[1]) * 100) \
               if len(ebitda_s) >= 2 and ebitda_s[1] else None
    avg_ebitda_g = None
    if len(ebitda_s) >= 5:
        gs = [(ebitda_s[i] - ebitda_s[i+1]) / abs(ebitda_s[i+1]) * 100
              for i in range(4) if ebitda_s[i] and ebitda_s[i+1]]
        avg_ebitda_g = _avg(gs) if gs else None

    # PEG <1 UNDERVALUED, ≤1.5 FAIR, >1.5 OVERVALUED
    peg = info.get('pegRatio') or info.get('trailingPegRatio')
    v = 'GOOD'  if peg is not None and peg < 1.0 else \
        'WATCH' if peg is not None and peg <= 1.5 else \
        'BAD'   if peg is not None else 'NA'
    metrics.append(_score_metric('peg_ratio', v, W))

    # Earnings Yield vs Bond Yield
    ey = (1 / pe) if pe and pe > 0 else None
    v = 'GOOD' if ey is not None and ey > bond_yield else \
        'BAD'  if ey is not None else 'NA'
    metrics.append(_score_metric('earn_yield', v, W))

    # P/B <1.5 UNDERVALUED, <3 FAIR, ≥3 OVERVALUED
    pb = info.get('priceToBook')
    v = 'GOOD'  if pb is not None and pb < 1.5 else \
        'WATCH' if pb is not None and pb < 3.0 else \
        'BAD'   if pb is not None else 'NA'
    metrics.append(_score_metric('pb_ratio', v, W))

    # Graham Value: P/E × P/B < 22.5
    graham_product = (pe * pb) if pe and pb else None
    v = 'GOOD' if graham_product is not None and graham_product < 22.5 else \
        'BAD'  if graham_product is not None else 'NA'
    metrics.append(_score_metric('graham_val', v, W))

    # P/S <1.5 UNDERVALUED, <3 FAIR, ≥3 OVERVALUED
    ps = info.get('priceToSalesTrailing12Months')
    v = 'GOOD'  if ps is not None and ps < 1.5 else \
        'WATCH' if ps is not None and ps < 3.0 else \
        'BAD'   if ps is not None else 'NA'
    metrics.append(_score_metric('ps_ratio', v, W))

    # Dividend Yield ≥4% GOOD (optional metric)
    dy = info.get('dividendYield')
    v = 'GOOD'  if dy is not None and dy >= 0.04 else \
        'WATCH' if dy is not None else 'NA'
    metrics.append(_score_metric('div_yield', v, W))

    # EV/EBITDA <10 UNDERVALUED, <15 FAIR, ≥15 OVERVALUED
    ev_eb = info.get('enterpriseToEbitda')
    v = 'GOOD'  if ev_eb is not None and ev_eb < 10 else \
        'WATCH' if ev_eb is not None and ev_eb < 15 else \
        'BAD'   if ev_eb is not None else 'NA'
    metrics.append(_score_metric('ev_ebitda', v, W))

    # ── MARGIN OF SAFETY (using DCF EPS — fully formulaic) ────
    eps_ttm = eps_[0] if eps_ else info.get('trailingEps')
    eps_growth_rates = []
    for i in range(min(4, len(eps_) - 1)):
        a, b = eps_[i], eps_[i+1]
        if a is not None and b is not None and b != 0:
            eps_growth_rates.append((a - b) / abs(b) * 100)
    avg_eps_g = _avg(eps_growth_rates) if eps_growth_rates else 5.0

    iv_dcf_eps = _dcf_eps(eps_ttm, avg_eps_g, bond_yield)
    mos_dcf_eps = _mos(iv_dcf_eps, price)

    # DCF FCF
    fcf_s  = _series(cf, ['free cash flow', 'freecashflow'])
    fcf_ps = [(f / shares) if f and shares else None for f in fcf_s]
    iv_dcf_fcf = _dcf_fcf(fcf_ps, price)
    mos_dcf_fcf = _mos(iv_dcf_fcf, price)

    # DCF Cash
    cash_s  = _series(bal, ['cash and cash equivalents', 'cash',
                             'cashandcashequivalents'])
    inv_s   = _series(bal, ['short term investments', 'investmentsandadvances',
                             'other short term investments'])
    total_cash_s = [(c or 0) + (i or 0) for c, i in
                    zip(cash_s + [0]*6, inv_s + [0]*6)][:6]
    cash_ps = [(c / shares) if c and shares else None for c in total_cash_s]
    iv_dcf_cash = _dcf_cash(cash_ps, price)
    mos_dcf_cash = _mos(iv_dcf_cash, price)

    # Projected FCF / Cash
    avg_fcf_6  = _avg(fcf_s, 6)
    avg_cash_6 = _avg(total_cash_s, 6)
    equity_val = _safe_get(bal, ['stockholders equity', 'total stockholders equity',
                                  'stockholdersequity'], 0)
    iv_proj_fcf  = _projected_fcf(avg_fcf_6, shares, equity_val)
    iv_proj_cash = _projected_cash(avg_cash_6, shares, equity_val)

    # Peter Lynch
    iv_peter_lynch = _peter_lynch(peg, avg_ebitda_g, eps_ttm)

    # Composite IV (average of available methods)
    iv_vals = [v for v in [iv_dcf_eps, iv_dcf_fcf, iv_dcf_cash,
                            iv_proj_fcf, iv_proj_cash, iv_peter_lynch]
               if v is not None and v > 0]
    iv_composite = _avg(iv_vals) if iv_vals else None
    mos_composite = _mos(iv_composite, price)

    # MoS scoring: SAFE ≥25%, SLIM 0–25%, OVERVALUED <0
    v = 'GOOD'  if mos_composite is not None and mos_composite >= 0.25 else \
        'WATCH' if mos_composite is not None and mos_composite >= 0 else \
        'BAD'   if mos_composite is not None else 'NA'
    metrics.append(_score_metric('mos', v, W))

    # Value for Shareholders: EPS 3yr avg > 5yr avg (same as eps_trend direction)
    v = 'GOOD'  if eps_3 is not None and eps_5 is not None and eps_3 > eps_5 else \
        'WATCH' if eps_3 is not None else 'NA'
    metrics.append(_score_metric('val_shareholders', v, W))

    # ── INVENTORY / WORKING CAPITAL ───────────────────────────
    inv_s2 = _series(bal, ['inventory', 'inventories'])
    ar_s   = _series(bal, ['accounts receivable', 'net receivables',
                            'accountsreceivable', 'netreceivables'])
    ap_s   = _series(bal, ['accounts payable', 'accountspayable'])
    cogs_s = _series(inc, ['cost of revenue', 'cost of goods sold',
                            'costofrevenue', 'cogs'])

    # Inventory Turnover: Revenue / Avg Inventory, 3yr > 5yr
    it_s = []
    for i in range(min(len(rev_s), len(inv_s2))):
        avg_inv = ((inv_s2[i] + (inv_s2[i+1] if i+1 < len(inv_s2) else inv_s2[i])) / 2) \
                  if inv_s2[i] else None
        it_s.append((rev_s[i] / avg_inv) if avg_inv and rev_s[i] else None)
    it3 = _avg(it_s, 3)
    it5 = _avg(it_s, 5)
    v = 'GOOD'  if it3 is not None and it5 is not None and it3 > it5 else \
        'WATCH' if it3 is not None else 'NA'
    metrics.append(_score_metric('inv_turn', v, W))

    # DRO: Receivables/Revenue*365, 3yr avg vs 5yr avg (lower = better)
    dro_s = [(ar_s[i] / rev_s[i] * 365) if ar_s and i < len(ar_s) and rev_s[i]
             else None for i in range(min(len(rev_s), 6))]
    dro3 = _avg(dro_s, 3)
    dro5 = _avg(dro_s, 5)
    # Lower DRO = better collection; 3yr < 5yr = improving
    v = 'GOOD'  if dro3 is not None and dro5 is not None and dro3 < dro5 else \
        'WATCH' if dro3 is not None else 'NA'
    metrics.append(_score_metric('dro', v, W))

    # Fixed Asset Turnover: Revenue / Avg PPE, 3yr > 5yr
    v = 'GOOD'  if nfat3 is not None and nfat5 is not None and nfat3 > nfat5 else \
        'WATCH' if nfat3 is not None else 'NA'
    metrics.append(_score_metric('fat', v, W))

    # CCC = DRO + DSI − DPO; 3yr avg vs 5yr avg (lower = better)
    dsi_s = [(inv_s2[i] / (cogs_s[i] if cogs_s and i < len(cogs_s) else rev_s[i]) * 365)
             if inv_s2 and i < len(inv_s2) and (cogs_s and i < len(cogs_s) or rev_s[i])
             else None for i in range(min(len(rev_s), 6))]
    dpo_s = [(ap_s[i] / (cogs_s[i] if cogs_s and i < len(cogs_s) else rev_s[i]) * 365)
             if ap_s and i < len(ap_s) else None for i in range(min(len(rev_s), 6))]
    ccc_s = [(dro_s[i] or 0) + (dsi_s[i] or 0) - (dpo_s[i] or 0)
             if dro_s and i < len(dro_s) else None for i in range(min(len(rev_s), 6))]
    ccc3 = _avg(ccc_s, 3)
    ccc5 = _avg(ccc_s, 5)
    v = 'GOOD'  if ccc3 is not None and ccc5 is not None and ccc3 < ccc5 else \
        'WATCH' if ccc3 is not None else 'NA'
    metrics.append(_score_metric('ccc', v, W))

    # ── CASHFLOW ──────────────────────────────────────────────
    # FCF 3yr > 5yr
    fcf3 = _avg(fcf_s, 3)
    fcf5 = _avg(fcf_s, 5)
    v = 'GOOD'  if fcf3 is not None and fcf5 is not None and fcf3 > fcf5 else \
        'WATCH' if fcf3 is not None else 'NA'
    metrics.append(_score_metric('fcf_trend', v, W))

    # CROIC: FCF / Invested Capital (TTM)
    td0    = td_s[0] if td_s else None
    eq0    = equity_val
    cash0  = total_cash_s[0] if total_cash_s else None
    mi_s   = _series(bal, ['minority interest', 'noncontrolling interest',
                             'minorityinterest'])
    mi0    = mi_s[0] if mi_s else 0
    ic0    = ((td0 or 0) + (eq0 or 0) + (mi0 or 0) - (cash0 or 0))
    fcf0   = fcf_s[0] if fcf_s else None
    croic  = (fcf0 / ic0) if fcf0 and ic0 else None
    v = 'GOOD'  if croic is not None and croic > 0.15 else \
        'WATCH' if croic is not None and croic > 0.05 else \
        'BAD'   if croic is not None else 'NA'
    metrics.append(_score_metric('croic', v, W))

    # FCF/Sale (FCF Margin) TTM: >20% GOOD, >8% WATCH
    fcf_margin = (fcf0 / rev[0]) if fcf0 and rev and rev[0] else None
    v = 'GOOD'  if fcf_margin is not None and fcf_margin > 0.20 else \
        'WATCH' if fcf_margin is not None and fcf_margin > 0.08 else \
        'BAD'   if fcf_margin is not None else 'NA'
    metrics.append(_score_metric('fcf_sale', v, W))

    # FCF/CFO ratio 3yr avg > 5yr avg (quality of earnings)
    cfo0 = cfo_s[0] if cfo_s else None
    fcf_cfo_s = [(fcf_s[i] / cfo_s[i]) if fcf_s and i < len(fcf_s) and
                  cfo_s and i < len(cfo_s) and cfo_s[i] else None
                 for i in range(min(len(fcf_s), len(cfo_s), 6))]
    fcfo3 = _avg(fcf_cfo_s, 3)
    fcfo5 = _avg(fcf_cfo_s, 5)
    v = 'GOOD'  if fcfo3 is not None and fcfo5 is not None and fcfo3 > fcfo5 else \
        'WATCH' if fcfo3 is not None else 'NA'
    metrics.append(_score_metric('fcf_cfo', v, W))

    # ── RISK SCORES ───────────────────────────────────────────
    # Cash per Share: Cash/Debt ratio
    cash_debt = (cash0 / td0) if cash0 and td0 and td0 > 0 else None
    v = 'GOOD'  if cash_debt is not None and cash_debt > 1.0 else \
        'WATCH' if cash_debt is not None and cash_debt > 0.3 else \
        'BAD'   if cash_debt is not None else 'NA'
    metrics.append(_score_metric('cash_debt', v, W))

    # Cash per Share (absolute)
    cash_ps_val = (cash0 / shares) if cash0 and shares else None
    v = 'GOOD'  if cash_ps_val is not None and price and cash_ps_val > price * 0.1 else \
        'WATCH' if cash_ps_val is not None else 'NA'
    metrics.append(_score_metric('cash_share', v, W))

    # Altman Z-Score (non-manufacturer model)
    ta_s  = _series(bal, ['total assets', 'totalassets'])
    ta0   = ta_s[0] if ta_s else None
    ca_s  = _series(bal, ['current assets', 'total current assets', 'currentassets'])
    cl_s  = _series(bal, ['current liabilities', 'total current liabilities', 'currentliabilities'])
    re_s  = _series(bal, ['retained earnings', 'retainedearnings'])
    ca0   = ca_s[0] if ca_s else None
    cl0   = cl_s[0] if cl_s else None
    re0   = re_s[0] if re_s else None
    ebit0 = op[0] if op else None
    wc    = ((ca0 or 0) - (cl0 or 0)) if ca0 and cl0 else None
    altman = None
    if all(v is not None for v in [wc, re0, ebit0, eq0, td0, ta0]) and ta0 > 0 and td0 > 0:
        altman = 6.56*(wc/ta0) + 3.26*(re0/ta0) + 6.72*(ebit0/ta0) + 1.05*(eq0/td0)
    v = 'GOOD'  if altman is not None and altman > 2.6 else \
        'WATCH' if altman is not None and altman > 1.1 else \
        'BAD'   if altman is not None else 'NA'
    metrics.append(_score_metric('altman_z', v, W))

    # Beneish M-Score
    beneish = None
    if len(rev_s) >= 2 and len(ar_s) >= 2 and len(ta_s) >= 2:
        gp_s   = [(rev_s[i] - (cogs_s[i] or 0)) for i in range(min(len(rev_s), len(cogs_s or [])))] \
                 if cogs_s else []
        dep_s  = _series(cf, ['depreciation', 'depreciation and amortization',
                               'depreciationandamortization'])
        sga_s  = _series(inc, ['selling general administrative', 'sga', 'operatingexpenses'])
        ltd_s  = _series(bal, ['long term debt', 'longtermdebt'])
        ni0_   = np_[0] if np_ else None
        if all(len(s) >= 2 for s in [gp_s, dep_s, sga_s]) and ni0_ is not None and cfo0:
            beneish = _beneish_m(
                rev_s[0], rev_s[1], ar_s[0], ar_s[1],
                gp_s[0] if gp_s else None, gp_s[1] if len(gp_s) > 1 else None,
                ta_s[0], ta_s[1], ppe_s[0] if ppe_s else None,
                ppe_s[1] if ppe_s and len(ppe_s) > 1 else None,
                sga_s[0], sga_s[1], dep_s[0], dep_s[1],
                ni0_, cfo0, ltd_s[0] if ltd_s else 0, ltd_s[1] if ltd_s and len(ltd_s) > 1 else 0
            )
    # M < -2.22 = non-manipulator (GOOD), -2.22 to -1.78 = grey zone, > -1.78 = manipulator
    v = 'GOOD'  if beneish is not None and beneish < -2.22 else \
        'WATCH' if beneish is not None and beneish < -1.78 else \
        'BAD'   if beneish is not None else 'NA'
    metrics.append(_score_metric('beneish_m', v, W))

    # Piotroski F-Score
    ta1   = ta_s[1]  if len(ta_s) > 1 else None
    roa0  = (np_[0] / ta0) if np_ and ta0 else None
    roa1  = (np_[1] / ta1) if np_ and len(np_) > 1 and ta1 else None
    cfo_ta = (cfo0 / ta0) if cfo0 and ta0 else None
    lt0   = ltd_s[0] if 'ltd_s' in dir() and ltd_s else td0
    lt1   = ltd_s[1] if 'ltd_s' in dir() and ltd_s and len(ltd_s) > 1 else \
            (td_s[1] if td_s and len(td_s) > 1 else None)
    delta_lev = ((lt0 / ta0) - (lt1 / ta1)) if lt0 and ta0 and lt1 and ta1 else None
    cr1   = None  # would need prev year current ratio
    delta_cr = None
    sh0   = shares
    sh1_s = _series(bal, ['shares outstanding', 'common stock shares outstanding'])
    sh1   = sh1_s[1] if sh1_s and len(sh1_s) > 1 else None
    delta_sh = ((sh0 - sh1) / sh1) if sh0 and sh1 else None
    gm0  = ((rev_s[0] - (cogs_s[0] if cogs_s else 0)) / rev_s[0]) if rev_s and rev_s[0] else None
    gm1  = ((rev_s[1] - (cogs_s[1] if cogs_s and len(cogs_s) > 1 else 0)) / rev_s[1]) \
           if rev_s and len(rev_s) > 1 and rev_s[1] else None
    delta_gm = (gm0 - gm1) if gm0 is not None and gm1 is not None else None
    at0  = (rev_s[0] / ta0) if rev_s and ta0 else None
    at1  = (rev_s[1] / ta1) if rev_s and len(rev_s) > 1 and ta1 else None
    delta_at = (at0 - at1) if at0 is not None and at1 is not None else None

    piotroski = _piotroski_f(
        np_[0] if np_ else None, cfo0, roa0, roa1, cfo_ta,
        delta_lev, delta_cr, delta_sh, delta_gm, delta_at
    )
    # F ≥ 7 GOOD, 4–6 WATCH, ≤ 3 BAD
    v = 'GOOD'  if piotroski is not None and piotroski >= 7 else \
        'WATCH' if piotroski is not None and piotroski >= 4 else \
        'BAD'   if piotroski is not None else 'NA'
    metrics.append(_score_metric('piotroski_f', v, W))

    # ROIC vs WACC
    tax_r  = tax_rate if tax_rate else 0.21
    roic_v = _roic(ebit0, tax_r, td0 or 0, eq0 or 0, cash0 or 0)
    wacc_v = _wacc_simple(beta, rf=bond_yield, debt=td0 or 0,
                          equity=eq0 or 0, tax=tax_r)
    v = 'GOOD'  if roic_v is not None and wacc_v is not None and roic_v > wacc_v else \
        'WATCH' if roic_v is not None and wacc_v is not None else 'NA'
    metrics.append(_score_metric('roic_wacc', v, W))

    # ── COMPILE SCORE ─────────────────────────────────────────
    total = sum(m['pts'] for m in metrics)
    max_s = sum(m['max'] for m in metrics)
    pct   = (total / max_s * 100) if max_s else 0
    grade = 'A' if pct >= 75 else 'B' if pct >= 60 else 'C' if pct >= 50 else 'FAIL'

    return {
        'score':       total,
        'max':         max_s,
        'pct':         round(pct, 1),
        'grade':       grade,
        'is_bank':     False,
        'metrics':     metrics,
        'iv': {
            'dcf_eps':     round(iv_dcf_eps,    2) if iv_dcf_eps   else None,
            'dcf_fcf':     round(iv_dcf_fcf,    2) if iv_dcf_fcf   else None,
            'dcf_cash':    round(iv_dcf_cash,   2) if iv_dcf_cash  else None,
            'proj_fcf':    round(iv_proj_fcf,   2) if iv_proj_fcf  else None,
            'proj_cash':   round(iv_proj_cash,  2) if iv_proj_cash else None,
            'peter_lynch': round(iv_peter_lynch,2) if iv_peter_lynch else None,
            'composite':   round(iv_composite,  2) if iv_composite  else None,
            'mos_pct':     round(mos_composite * 100, 1) if mos_composite else None,
            'price':       price,
        },
        'altman_z':    round(altman,    2) if altman    else None,
        'beneish_m':   round(beneish,   2) if beneish   else None,
        'piotroski_f': piotroski,
    }


# --- BANK SCORING ---
def _score_bank(ticker, d, bond_yield=0.043):
    """
    Score bank stocks. Runs standard template first, then replaces
    N/A inventory/coverage metrics with bank-specific ratios.
    Bank ratios sourced from yfinance info + income_stmt.
    """
    result = _score_standard(ticker, d, bond_yield)
    result['is_bank'] = True
    info = d['info']
    inc  = d['inc']
    W    = IM3_BANK_WEIGHTS

    # Override tax threshold: 29% Pakistan banks, 25% US banks
    # Detect by exchange: if PSX exchange or Pakistan in country
    country = (info.get('country') or '').lower()
    tax_threshold = 0.29 if 'pakistan' in country else 0.25
    # Re-score tax rate metric
    tax_metric = next((m for m in result['metrics'] if m['key'] == 'tax_rate'), None)
    if tax_metric:
        # Re-evaluate with correct threshold
        tax_exp_s = _series(inc, ['tax provision', 'income tax expense',
                                   'incometaxexpense', 'taxprovision'])
        pbt_s     = _series(inc, ['pretax income', 'income before tax',
                                   'incomebeforetax', 'ebt'])
        tr = (tax_exp_s[0] / pbt_s[0]) if tax_exp_s and pbt_s and pbt_s[0] else \
             info.get('effectiveTaxRate')
        v = 'GOOD' if tr is not None and tr >= tax_threshold else \
            'WATCH' if tr is not None else 'NA'
        tax_metric['verdict'] = v
        tax_metric['pts'] = _pts(v, W.get('tax_rate', 3))

    # Zero out every metric that does not apply to a bank (full canonical set, not just
    # the original 6) so it contributes to neither score nor denominator.
    for key in _BANK_ZERO:
        m = next((x for x in result['metrics'] if x['key'] == key), None)
        if m:
            m['verdict'] = 'NA'
            m['pts'] = 0
            m['max'] = 0

    # ── BANK-SPECIFIC METRICS ─────────────────────────────────
    bank_metrics = []

    # NIM = Net Interest Income / Average Earning Assets
    # yfinance: netInterestIncome in income_stmt
    nii_s = _series(inc, ['net interest income', 'netinterestincome',
                           'interest income net'])
    ta_s  = _series(d['bal'], ['total assets', 'totalassets'])
    nim   = (nii_s[0] / ta_s[0]) if nii_s and ta_s and ta_s[0] else \
            info.get('netInterestMargin')
    # NIM: ≥4% GOOD, ≥3% WATCH, <3% BAD (global benchmark)
    v = 'GOOD'  if nim is not None and nim >= 0.04 else \
        'WATCH' if nim is not None and nim >= 0.03 else \
        'BAD'   if nim is not None else 'NA'
    bank_metrics.append(_score_metric('nim', v, W))

    # CASA = (Current + Savings Deposits) / Total Deposits
    # yfinance rarely has this directly; use info or skip gracefully
    casa = info.get('casaRatio') or info.get('currentAccountSavingsRatio')
    # For US community banks CASA not in yfinance — mark NA
    v = 'GOOD'  if casa is not None and casa >= 0.80 else \
        'WATCH' if casa is not None and casa >= 0.70 else \
        'BAD'   if casa is not None else 'NA'
    bank_metrics.append(_score_metric('casa', v, W))

    # ADR = Advances / Deposits (sweet spot 40-60%)
    loans_s = _series(d['bal'], ['net loans', 'loans', 'totalloans',
                                   'net loan and lease', 'netloanandlease'])
    dep_s   = _series(d['bal'], ['total deposits', 'deposits', 'totaldeposits'])
    adr = (loans_s[0] / dep_s[0]) if loans_s and dep_s and dep_s[0] else None
    v = 'GOOD'  if adr is not None and 0.40 <= adr <= 0.60 else \
        'WATCH' if adr is not None and (0.30 <= adr < 0.40 or 0.60 < adr <= 0.70) else \
        'BAD'   if adr is not None else 'NA'
    bank_metrics.append(_score_metric('adr', v, W))

    # NPL ratio = Non-Performing Loans / Total Loans
    npl_s  = _series(d['bal'], ['nonperforming loans', 'nonperformingassets',
                                  'non performing loans'])
    npl    = (npl_s[0] / loans_s[0]) if npl_s and loans_s and loans_s[0] else None
    if npl is None:
        # Proxy: allowance for loan losses / total loans
        all_s = _series(d['bal'], ['allowance for loan losses',
                                    'allowanceforloanlosses'])
        npl   = (all_s[0] / loans_s[0]) if all_s and loans_s and loans_s[0] else None
    v = 'GOOD'  if npl is not None and npl < 0.03 else \
        'WATCH' if npl is not None and npl < 0.05 else \
        'BAD'   if npl is not None else 'NA'
    bank_metrics.append(_score_metric('npl', v, W))

    # CAR = Capital Adequacy Ratio (Tier 1 + Tier 2 / RWA)
    car = info.get('capitalAdequacyRatio') or info.get('tier1CapitalRatio')
    if car and car > 1:
        car = car / 100  # normalise if percentage
    v = 'GOOD'  if car is not None and car >= 0.18 else \
        'WATCH' if car is not None and car >= 0.15 else \
        'BAD'   if car is not None else 'NA'
    bank_metrics.append(_score_metric('car', v, W))

    # Add bank metrics to result
    result['metrics'].extend(bank_metrics)

    # Input-availability probe (Wave D1/System-B Phase 2): records which canonical bank
    # inputs Yahoo actually returned, so the next-phase ratios (spread ratio, PPNR growth,
    # provision/GL, loan/deposit growth, ROA, true P/TBV) are built from confirmed data.
    result['bank_inputs'] = {
        'nii':          (nii_s[0]   if nii_s   else None),
        'total_assets': (ta_s[0]    if ta_s    else None),
        'gross_loans':  (loans_s[0] if loans_s else None),
        'deposits':     (dep_s[0]   if dep_s   else None),
        'npl_found':    npl  is not None,
        'casa_found':   casa is not None,
        'car_found':    car  is not None,
    }

    # ── COMPILE BANK SCORE (canonical denominator) ───────────
    # Score on applicable (bank-weight>0) metrics only. The denominator excludes NA so a
    # data-vendor gap (e.g. CASA/CAR absent on Yahoo for US banks) doesn't structurally
    # penalise the bank. pct is NO LONGER score/162 — a bank is scored out of its own
    # applicable max (~70), fixing the prior bug that capped every bank near 55%.
    applicable = [m for m in result['metrics'] if W.get(m['key'], 0) > 0]
    total = sum(_pts(m['verdict'], W.get(m['key'], 0)) for m in applicable)
    max_s = sum(W.get(m['key'], 0) for m in applicable if m['verdict'] != 'NA')
    n_meas = sum(1 for m in applicable if m['verdict'] != 'NA')
    pct   = (total / max_s * 100) if max_s else 0
    grade = 'A' if pct >= 75 else 'B' if pct >= 60 else 'C' if pct >= 50 else 'FAIL'

    result['score']         = total
    result['max']           = max_s
    result['pct']           = round(pct, 1)
    result['grade']         = grade
    result['bank_coverage'] = round(n_meas / len(applicable), 2) if applicable else 0
    return result


# --- MAIN ENTRY POINT ---
def score_im3(ticker):
    """
    Score a single ticker using the full IM3 162-point methodology.
    Returns dict: {score, max, pct, grade, is_bank, metrics, iv, ...}
    Returns None if data fetch fails.
    """
    try:
        log(f'  IM3 scoring {ticker}...')
        d = _fetch_im3_data(ticker)
        if d is None:
            return None

        is_bank = _is_bank(d['info'])

        # Bond yield: fetch US 10Y from FRED if available, else use default
        bond_yield = 0.043  # Default ~4.3%
        try:
            import requests as _req
            if FRED_KEY:
                r = _req.get(
                    f'https://api.stlouisfed.org/fred/series/observations'
                    f'?series_id=DGS10&api_key={FRED_KEY}&limit=1'
                    f'&sort_order=desc&file_type=json', timeout=5)
                if r.status_code == 200:
                    obs = r.json().get('observations', [{}])
                    val = obs[0].get('value', '')
                    if val and val != '.':
                        bond_yield = float(val) / 100
        except Exception:
            pass

        if is_bank:
            result = _score_bank(ticker, d, bond_yield)
        else:
            result = _score_standard(ticker, d, bond_yield)

        log(f'  IM3 {ticker}: {result["score"]}/162 ({result["pct"]}%) '
            f'Grade {result["grade"]} {"[BANK]" if is_bank else ""}')
        return result

    except Exception as e:
        log(f'  IM3 scoring error {ticker}: {e}')
        return None


def run_im3_on_explosives(explosive_list, max_stocks=30):
    """
    Run IM3 scoring on explosive_us records.
    Adds 'im3' key to each record. Only scores EXPLOSIVE both-signal records first,
    then fills remaining budget with QUALITY-GROWTH if time permits.
    """
    if not explosive_list:
        return explosive_list

    log(f'=== IM3 162-pt scoring on {len(explosive_list)} explosive US stocks ===')

    # Priority order: both-signal first
    priority = sorted(explosive_list,
                      key=lambda r: (r.get('verdict', '').startswith('EXPLOSIVE'),),
                      reverse=True)

    scored = 0
    for rec in priority:
        if scored >= max_stocks:
            break
        ticker = rec.get('ticker')
        if not ticker:
            continue
        try:
            im3 = score_im3(ticker)
            rec['im3'] = im3
            if im3:
                scored += 1
        except Exception as e:
            log(f'  IM3 run error {ticker}: {e}')
            rec['im3'] = None
        time.sleep(YF_DELAY * 2)  # respectful delay — IM3 fetch is heavier

    log(f'  IM3 scored: {scored} of {len(explosive_list)} stocks')
    return explosive_list


# =============================================================
# 6. RATE PATH
# =============================================================
def fetch_rate_path():
    return [
        {'date': '2025-09-15', 'rate': 11.00, 'action': 'HOLD'},
        {'date': '2025-10-27', 'rate': 11.00, 'action': 'HOLD'},
        {'date': '2025-12-15', 'rate': 10.50, 'action': 'CUT -50bp'},
        {'date': '2026-01-26', 'rate': 10.50, 'action': 'HOLD'},
        {'date': '2026-03-09', 'rate': 10.50, 'action': 'HOLD'},
        {'date': '2026-04-27', 'rate': 11.50, 'action': 'HIKE +100bp'},
        {'date': '2026-05-24', 'rate': 11.50, 'action': 'CURRENT'},
    ]


# =============================================================
# MAIN
# =============================================================
RECESSION_SERIES = {
    'sahm':           'SAHMREALTIME',
    'recession_prob': 'RECPROUSM156N',
    'yc_2y':          'T10Y2Y',
    'yc_3m':          'T10Y3M',
    'gdpnow':         'GDPNOW',
    'claims':         'ICSA',
}


def _ff_us_events(events, limit=12):
    """Filter the ForexFactory faireconomy weekly calendar to upcoming high/medium
    impact US (USD) releases. Pure. No 'actual' field — FF omits it until release;
    realized values come from FRED."""
    out = []
    if not isinstance(events, list):
        return out
    for e in events:
        if not isinstance(e, dict):
            continue
        if str(e.get('country', '')).upper() != 'USD':
            continue
        if str(e.get('impact', '')).lower() not in ('high', 'medium'):
            continue
        out.append({'title': e.get('title'), 'date': e.get('date'),
                    'impact': e.get('impact'), 'forecast': e.get('forecast'),
                    'previous': e.get('previous')})
    out.sort(key=lambda x: (0 if str(x.get('impact', '')).lower() == 'high' else 1,
                            str(x.get('date') or '')))
    return out[:limit]


def _recession_assess(sig):
    """Rule-based composite from the FRED signals. Pure + transparent.
    Returns (risk_label, score_0_100, triggers)."""
    triggers = []
    score = 0

    def _num(key):
        v = (sig.get(key) or {}).get('value')
        try:
            return float(v)
        except Exception:
            return None

    sahm = _num('sahm')
    if sahm is not None and sahm >= 0.50:
        triggers.append('Sahm rule triggered (>=0.50)'); score += 45
    elif sahm is not None and sahm >= 0.30:
        triggers.append('Sahm rising (>=0.30)'); score += 20

    yc2 = _num('yc_2y'); yc3 = _num('yc_3m')
    if (yc2 is not None and yc2 < 0) or (yc3 is not None and yc3 < 0):
        triggers.append('Yield curve inverted'); score += 20

    prob = _num('recession_prob')
    if prob is not None:
        if prob >= 50:
            triggers.append('NBER-style probability high (%d%%)' % round(prob)); score += 25
        elif prob >= 25:
            triggers.append('Recession probability elevated (%d%%)' % round(prob)); score += 12

    gdp = _num('gdpnow')
    if gdp is not None and gdp < 0:
        triggers.append('GDPNow negative (%.1f%%)' % gdp); score += 15

    score = min(score, 100)
    if score >= 60 or (sahm is not None and sahm >= 0.50):
        risk = 'HIGH'
    elif score >= 25:
        risk = 'ELEVATED'
    else:
        risk = 'LOW'
    return risk, score, triggers


def fetch_recession():
    """US recession watch (Wave C). FRED recession series + the ForexFactory weekly
    economic calendar via the faireconomy export host (the FF main site is
    Cloudflare-walled). Never raises; falls back to last-good per part."""
    prev = EXISTING.get('recession', {}) or {}
    out = {'signals': {}, 'calendar': prev.get('calendar', []),
           'source': 'FRED + faireconomy',
           '_fetched_utc': dt.datetime.utcnow().isoformat() + 'Z'}

    if FRED_KEY:
        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_KEY)
            for key, sid in RECESSION_SERIES.items():
                try:
                    time.sleep(0.5)
                    s = fred.get_series(sid).dropna()
                    if len(s) > 0:
                        out['signals'][key] = {'value': round(float(s.iloc[-1]), 2),
                                               'date': str(s.index[-1].date())}
                except Exception as e:
                    warn(f'recession FRED {key} ({sid}) failed: {e}')
                    lg = (prev.get('signals') or {}).get(key)
                    if lg is not None:
                        out['signals'][key] = lg
        except Exception as e:
            warn(f'recession FRED init failed: {e}')
            out['signals'] = prev.get('signals', {})
    else:
        out['signals'] = prev.get('signals', {})

    try:
        r = requests.get('https://nfs.faireconomy.media/ff_calendar_thisweek.json',
                         headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=12)
        ctype = r.headers.get('Content-Type', '')
        if r.status_code == 200 and 'json' in ctype.lower():
            cal = _ff_us_events(r.json())
            if cal:
                out['calendar'] = cal
                log(f'  ✓ Recession calendar: {len(cal)} high-impact US releases (faireconomy)')
        else:
            warn('FF calendar non-JSON (rate-limited?) — keeping last-good calendar')
    except Exception as e:
        warn(f'FF calendar failed: {e} — keeping last-good calendar')

    risk, score, triggers = _recession_assess(out['signals'])
    out['risk'] = risk
    out['score'] = score
    out['triggers'] = triggers
    log(f'  ✓ Recession watch: {risk} (score {score}) — {len(out["signals"])} FRED signals, '
        f'{len(out.get("calendar", []))} calendar events')
    return out


def track_shortlists(data, existing):
    """Wave T - PER-ITEM SHORTLIST PERFORMANCE TRACKER. For every tab that shortlists/recommends a
    stock (US + PSX screen survivors, US Explosive picks, US/PSX TCE tiers), records the date + price
    the name was FIRST seen on that tab, then updates its current price + % return-since each run; when
    a name drops off a tab its last-known reading is FROZEN (still_listed=false) - prices are never
    re-fetched for dropped names (honest fetch-free limitation), and a name without a price is skipped
    (never fabricated). SECTORS are tracked as a drift-free equal-weight basket = the AVERAGE of the
    per-name returns-since-first-seen of the tracked stocks in that sector (a new name enters at 0%, so
    membership churn cannot fake a jump); labelled as 'average of tracked names', not a sector index.
    Stored INSIDE data.json as data['shortlist_tracking'] so it persists via the SAME commit the
    workflow already makes. DISPLAY/DATA ONLY: never touches screening/scoring/TCE/the frozen prediction
    ledger -> respects the Sept freeze. Fully guarded (never raises; carries last-good on any error)."""
    try:
        today = dt.date.today().isoformat()
        prev = (existing.get('shortlist_tracking') or {})
        stocks = {k: dict(v) for k, v in (prev.get('stocks') or {}).items() if isinstance(v, dict)}

        def _px(row, pmap):
            tk = row.get('ticker')
            for cand in (pmap.get(tk), row.get('price'), row.get('close'), row.get('last'),
                         (row.get('streams') or {}).get('price') if isinstance(row.get('streams'), dict) else None):
                try:
                    v = float(cand)
                    if v > 0:
                        return round(v, 4)
                except (TypeError, ValueError):
                    continue
            return None

        # v1.103.0/v1.104.0 (Wave PB readiness): the conviction signal for each pick. A name re-scores
        # every run, so its entry-day grade is unrecoverable later. NEW rows are stamped at true first-seen
        # (signal_date == first_date). Rows that predate this capture get TODAY's conviction stamped ONCE,
        # honestly dated signal_date = today (!= first_date) so Wave PB can tell a true-entry grade from a
        # first-observed grade. entry_bench is keyed to the row's REAL first_date (looked up from the
        # rolling history store) so alpha_since pairs correctly with pct_since (both span first_date->today).
        # Guarded: any missing field is simply absent (never fabricated).
        _macros = (data.get('macros') or {})
        _bench_dates = sorted((h.get('date'), h) for h in (data.get('history') or [])
                              if isinstance(h, dict) and h.get('date'))
        def _bench_at(d, mkt):
            if not d:
                return None
            key = 'sp500' if mkt == 'US' else 'kse100'
            best = None
            for dd, h in _bench_dates:               # nearest row at/earlier than d (honest: None if pre-history)
                if dd <= d: best = h
                else: break
            if best:
                v = best.get(key)
                if isinstance(v, (int, float)) and v > 0:
                    return round(float(v), 2)
            return None
        def _entry_signal(row, mkt, fdate):
            sig = {}
            try:
                im = row.get('im3') if isinstance(row.get('im3'), dict) else None
                if im:
                    if im.get('grade') is not None: sig['entry_grade'] = im.get('grade')
                    if im.get('pct')   is not None: sig['entry_pct']   = im.get('pct')
                    val = im.get('valuation')
                    if isinstance(val, dict) and (val.get('label') or val.get('tier')):
                        sig['entry_val'] = val.get('label') or val.get('tier')
                if row.get('tier'):                     sig['entry_tier']     = str(row.get('tier')).upper()
                if row.get('strength_score') is not None: sig['entry_strength'] = row.get('strength_score')
                b = _bench_at(fdate, mkt)
                if b is None and fdate == today:        # new row, history not yet carrying today -> live macro
                    lv = ((_macros.get('us') or {}).get('sp500') if mkt == 'US'
                          else (_macros.get('psx') or {}).get('kse100'))
                    if isinstance(lv, (int, float)) and lv > 0: b = round(float(lv), 2)
                if b is not None: sig['entry_bench'] = b
            except Exception:
                pass
            return sig
        # current benchmark level per market (for the stored alpha-since-recommended)
        _cur_bench = {'US':  ((_macros.get('us')  or {}).get('sp500')),
                      'PSX': ((_macros.get('psx') or {}).get('kse100'))}

        # price maps from the candidate lists (the authoritative current price per market)
        us_px  = {r.get('ticker'): r.get('price') for r in (data.get('us_candidates') or []) if isinstance(r, dict)}
        psx_px = {r.get('ticker'): r.get('price') for r in (data.get('psx_candidates') or []) if isinstance(r, dict)}

        # Sector BACKFILL map: ETF-consensus large-caps enter the TCE pool from the ETF-overlap
        # list (ticker+name+weight only, NO sector), so their tracked rows would show a blank
        # sector. Harvest ticker->sector from EVERY sector-bearing list already in data.json
        # (explosive_us/psx, us/psx_candidates, tce_us/psx, etc.) so a name with no sector of its
        # own inherits the one the rest of the scan already knows. Display-only; never fabricated
        # (a name absent everywhere stays blank). First non-empty wins.
        sec_map = {}
        for _v in data.values():
            if isinstance(_v, list):
                for _r in _v:
                    if isinstance(_r, dict):
                        _tk = _r.get('ticker'); _sc = _r.get('sector')
                        if _tk and _sc and _tk not in sec_map:
                            sec_map[_tk] = _sc

        # assemble (tab, market, pmap, rows-iterable) for every shortlisting tab, both markets
        feeds = [
            ('US Screen Survivors', 'US', us_px, data.get('us_candidates') or []),
            ('PSX Screen Survivors', 'PSX', psx_px, data.get('psx_candidates') or []),
        ]
        # US Explosive: only positively-classified picks (not NOT-EXPLOSIVE / INSUFFICIENT / PARTIAL / bank)
        _POS = ('EXPLOSIVE', 'QUALITY-GROWTH', 'INFLECTION')
        exp_us = [r for r in (data.get('explosive_us') or [])
                  if isinstance(r, dict) and str(r.get('verdict', '')).upper().startswith(_POS)]
        feeds.append(('US Explosive', 'US', us_px, exp_us))
        # TCE tiers (HIGH / WATCH) both markets
        for mkt, key, pmap in (('US', 'tce_us', us_px), ('PSX', 'tce_psx', psx_px)):
            for tier in ('HIGH', 'WATCH'):
                rows = [r for r in (data.get(key) or [])
                        if isinstance(r, dict) and str(r.get('tier', '')).upper() == tier]
                feeds.append((f'{mkt} TCE {tier}', mkt, pmap, rows))

        seen_keys = set()
        for tab, mkt, pmap, rows in feeds:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                tk = row.get('ticker')
                if not tk:
                    continue
                price = _px(row, pmap)
                if price is None:
                    continue                              # never fabricate a price
                k = f'{tab}|{tk}'
                seen_keys.add(k)
                rec = stocks.get(k)
                if rec and rec.get('first_price'):
                    rec['last_date'] = today
                    rec['last_price'] = price
                    rec['pct_since'] = round((price / rec['first_price'] - 1) * 100, 2)
                    rec['still_listed'] = True
                    rec['sector'] = row.get('sector') or sec_map.get(tk) or rec.get('sector', '')
                    # v1.104.0: make sure every live row carries a conviction snapshot, honestly dated.
                    if 'signal_date' not in rec:
                        if ('entry_grade' in rec or 'entry_tier' in rec or 'entry_strength' in rec):
                            # stamped at true first-seen by v1.103.0 -> it IS entry conviction
                            rec['signal_date'] = rec.get('first_date', today)
                            _b = _bench_at(rec.get('first_date'), mkt)   # repair bench to the real entry day
                            if _b is not None: rec['entry_bench'] = _b
                        else:
                            # predates the capture -> stamp TODAY's conviction, dated today (not first_date)
                            rec.update(_entry_signal(row, mkt, rec.get('first_date', today)))
                            rec['signal_date'] = today
                    # durable alpha: pick move minus its benchmark over the SAME window (first_date->today)
                    _eb = rec.get('entry_bench'); _cb = _cur_bench.get(mkt)
                    if isinstance(_eb, (int, float)) and isinstance(_cb, (int, float)) and _eb > 0:
                        rec['alpha_since'] = round(rec['pct_since'] - (_cb / _eb - 1) * 100, 2)
                else:
                    _new = {
                        'tab': tab, 'ticker': tk, 'market': mkt,
                        'sector': row.get('sector') or sec_map.get(tk, ''),
                        'first_date': today, 'first_price': price,
                        'last_date': today, 'last_price': price,
                        'pct_since': 0.0, 'still_listed': True,
                    }
                    _new.update(_entry_signal(row, mkt, today))   # true entry conviction + benchmark
                    _new['signal_date'] = today                   # == first_date -> trustworthy as entry
                    if 'entry_bench' in _new:
                        _new['alpha_since'] = 0.0
                    stocks[k] = _new
        # names no longer on their tab: freeze last-known (no re-fetch)
        for k, rec in stocks.items():
            if k not in seen_keys:
                rec['still_listed'] = False
        # prune dropped records older than ~400 days to bound size
        cutoff = (dt.date.today() - dt.timedelta(days=400)).isoformat()
        stocks = {k: v for k, v in stocks.items()
                  if v.get('still_listed') or (v.get('last_date') or '') >= cutoff}

        # SECTORS: drift-free equal-weight basket = avg of per-name pct_since of still-listed tracked names
        prev_sectors = (prev.get('sectors') or {})
        groups = {}   # {gk: {ticker: pct}} - dedupe by ticker so a name on several tabs counts ONCE
        for rec in stocks.values():
            if not rec.get('still_listed'):
                continue
            sec = (rec.get('sector') or '').strip()
            if not sec:
                continue
            groups.setdefault(f'{rec["market"]}|{sec}', {})[rec['ticker']] = rec['pct_since']
        sectors = {}
        for gk, by_tk in groups.items():
            mkt, sec = gk.split('|', 1)
            pcts = list(by_tk.values())
            old = prev_sectors.get(gk) if isinstance(prev_sectors.get(gk), dict) else {}
            sectors[gk] = {
                'market': mkt, 'sector': sec,
                'first_date': old.get('first_date', today),
                'last_date': today,
                'n_names': len(pcts),
                'pct_since': round(sum(pcts) / len(pcts), 2),
                'still_listed': True,
                'basis': 'equal-weight avg of tracked names since first seen',
            }
        # carry sectors that dropped out this run as frozen
        for gk, old in prev_sectors.items():
            if gk not in sectors and isinstance(old, dict):
                old = dict(old); old['still_listed'] = False
                sectors[gk] = old

        data['shortlist_tracking'] = {'stocks': stocks, 'sectors': sectors, 'last_run': today}
        n_live = sum(1 for v in stocks.values() if v.get('still_listed'))
        n_sig  = sum(1 for v in stocks.values() if 'signal_date' in v)
        n_true = sum(1 for v in stocks.values() if v.get('signal_date') and v.get('signal_date') == v.get('first_date'))
        log(f'  [Wave T shortlist] {len(stocks)} stock-rows tracked ({n_live} live, {n_sig} conviction-stamped '
            f'[{n_true} at true entry]) across {len(set(v["tab"] for v in stocks.values()))} tabs; {len(sectors)} sector baskets')
    except Exception as e:
        log(f'  [Wave T shortlist] skipped ({type(e).__name__}: {str(e)[:60]})')
        if isinstance(existing.get('shortlist_tracking'), dict):
            data['shortlist_tracking'] = existing['shortlist_tracking']


# ---------------------------------------------------------------------------
# Wave PK-D - PSX PKR-DEVALUATION ALERT (DISPLAY/DATA-ONLY multi-signal basket)
# Reads the PSX macro dict the scanner already fetches and scores a
# watch / elevated / high read from five signals. NEVER touches screening,
# scoring, IM3, TCE tiers, the frozen ledger, or admission -> respects the
# Sept freeze. Pure + fully guarded (never raises). The thresholds below are
# DEFAULTS for owner calibration - change a single constant to retune.
# Each signal contributes 0 (off) / 1 (mild) / 2 (strong); the sum -> a level.
# ---------------------------------------------------------------------------
PKD_RUPEE_MOM_MILD      = 2.0     # USD/PKR up >2% MoM  -> PKR weakening (mild)
PKD_RUPEE_MOM_STRONG    = 5.0     # USD/PKR up >5% MoM  -> PKR weakening (strong)
PKD_RUPEE_QOQ_MILD      = 5.0     # or USD/PKR up >5% QoQ -> mild
PKD_RESERVES_MOM_MILD   = -5.0    # SBP reserves down >5% MoM  -> mild
PKD_RESERVES_MOM_STRONG = -10.0   # SBP reserves down >10% MoM -> strong
PKD_REER_MILD           = 103.0   # REER >103 -> rupee mildly overvalued
PKD_REER_STRONG         = 108.0   # REER >108 -> stretched (correction-prone)
PKD_SBP_RATE_DEFENSIVE  = 11.0    # owner's standing defensive policy-rate line
PKD_LEVEL_WATCH         = 1       # summed score 1-2  -> watch
PKD_LEVEL_ELEVATED      = 3       # summed score 3-4  -> elevated
PKD_LEVEL_HIGH          = 5       # summed score >=5  -> high

def _pkd_num(v):
    """Coerce to float or None; drops NaN. Never raises."""
    try:
        if v is None:
            return None
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None

def compute_psx_devaluation(psx):
    """Wave PK-D: PURE multi-signal PKR-devaluation read off the PSX macro dict.
    Returns {level, score, max_score, as_of, signals{name:{points,value,note}}}.
    DISPLAY/DATA-ONLY -> never feeds screening/scoring/IM3/TCE. Fully guarded:
    any bad input yields a safe 'none'-shaped dict instead of raising."""
    try:
        psx = psx or {}
        sig = {}

        # 1) Rupee slope - USD/PKR RISING = PKR weakening (depreciation).
        mom = _pkd_num(psx.get('usd_pkr_mom'))
        qoq = _pkd_num(psx.get('usd_pkr_qoq'))
        pts = 0
        if mom is not None and mom >= PKD_RUPEE_MOM_STRONG:
            pts = 2
        elif mom is not None and mom >= PKD_RUPEE_MOM_MILD:
            pts = 1
        elif qoq is not None and qoq >= PKD_RUPEE_QOQ_MILD:
            pts = 1
        _mtxt = (f'{mom:+.1f}% MoM' if mom is not None else 'MoM n/a')
        sig['rupee_slope'] = {'points': pts, 'value': _pkd_num(psx.get('usd_pkr')),
            'note': f'USD/PKR {psx.get("usd_pkr")} ({_mtxt}); rising = rupee weakening'}

        # 2) Reserves falling - SBP FX reserves declining.
        rmom = _pkd_num(psx.get('sbp_reserves_mom'))
        pts = 0
        if rmom is not None and rmom <= PKD_RESERVES_MOM_STRONG:
            pts = 2
        elif rmom is not None and rmom <= PKD_RESERVES_MOM_MILD:
            pts = 1
        _rtxt = (f'{rmom:+.1f}% MoM' if rmom is not None else 'MoM n/a')
        sig['reserves_fall'] = {'points': pts, 'value': _pkd_num(psx.get('sbp_reserves')),
            'note': f'SBP reserves {psx.get("sbp_reserves")} ({_rtxt}); falling = pressure'}

        # 3) REER stretch - rupee overvalued on real-effective terms.
        reer = _pkd_num(psx.get('reer'))
        pts = 0
        if reer is not None and reer >= PKD_REER_STRONG:
            pts = 2
        elif reer is not None and reer >= PKD_REER_MILD:
            pts = 1
        sig['reer_stretch'] = {'points': pts, 'value': reer,
            'note': (f'REER {reer}; >{PKD_REER_MILD:.0f} overvalued, >{PKD_REER_STRONG:.0f} stretched'
                     if reer is not None else 'REER n/a')}

        # 4) SBP policy rate - owner's standing defensive line.
        rate = _pkd_num(psx.get('sbp_rate'))
        pts = 1 if (rate is not None and rate >= PKD_SBP_RATE_DEFENSIVE) else 0
        sig['sbp_rate'] = {'points': pts, 'value': rate,
            'note': (f'SBP policy rate {rate}%; >={PKD_SBP_RATE_DEFENSIVE:.0f}% = defensive stance'
                     if rate is not None else 'SBP rate n/a')}

        # 5) Current-account / import-cover stress - WHEN SOURCED.
        # pak_ca has no comparable free monthly unit yet, so it is SURFACED but
        # NOT scored by default (contributes 0) until calibrated with the owner.
        ca = _pkd_num(psx.get('pak_ca'))
        sig['ca_stress'] = {'points': 0, 'value': ca,
            'note': (f'Current account {ca} (not scored - threshold to calibrate)'
                     if ca is not None else 'Current account n/a (when sourced)')}

        # 6) PKR WoW momentum from history store (v1.121.0 Wave R)
        # Reads last 2 usd_pkr readings from EXISTING['history'] to compute WoW slope.
        # 0 pts if <2 days history; 1 pt mild (>0.5% WoW); 2 pts strong (>1.5% WoW).
        _hist = (psx.get('_history_ref') or [])
        _pkr_now = _pkd_num(psx.get('usd_pkr'))
        _pkr_prev = None
        if isinstance(_hist, list) and len(_hist) >= 2:
            for _h in reversed(_hist[:-1]):
                if isinstance(_h, dict) and _h.get('usd_pkr') is not None:
                    _pkr_prev = _pkd_num(_h['usd_pkr']); break
        pts = 0
        _wow_pct = None
        if _pkr_now is not None and _pkr_prev is not None and _pkr_prev > 0:
            _wow_pct = round((_pkr_now - _pkr_prev) / _pkr_prev * 100, 2)
            if _wow_pct >= 1.5: pts = 2
            elif _wow_pct >= 0.5: pts = 1
        _wow_txt = (f'{_wow_pct:+.2f}% WoW' if _wow_pct is not None else 'WoW n/a (<2 history days)')
        sig['pkr_wow'] = {'points': pts, 'value': _pkr_now,
            'note': f'PKR WoW slope: {_wow_txt}; >+0.5% = mild, >+1.5% = strong depreciation'}

        score = sum(s['points'] for s in sig.values())
        max_score = 9   # rupee(2) + reserves(2) + reer(2) + rate(1) + CA(0) + pkr_wow(2)
        if score >= PKD_LEVEL_HIGH:
            level = 'high'
        elif score >= PKD_LEVEL_ELEVATED:
            level = 'elevated'
        elif score >= PKD_LEVEL_WATCH:
            level = 'watch'
        else:
            level = 'none'

        return {'level': level, 'score': score, 'max_score': max_score,
                'as_of': dt.date.today().isoformat(), 'signals': sig}
    except Exception:
        return {'level': 'none', 'score': 0, 'max_score': 7,
                'as_of': dt.date.today().isoformat(), 'signals': {}, 'error': 'compute failed'}

def append_history(data, existing):
    """Wave T - rolling DAILY HISTORY STORE. Appends a compact snapshot of the scan-time-only data
    points (the ones with NO external time series to backfill from - KSE-100, margin-financing total,
    USD/PKR, policy rate, candidate/HIGH counts, etc.) to data['history'], deduped by date (the last
    run that day wins), capped to the last 400 days. Stored INSIDE data.json so it persists via the
    same commit the workflow already makes - no extra file, no daily.yml change. DISPLAY/DATA ONLY:
    never touches screening/scoring/TCE -> respects the Sept freeze. Fully guarded (never raises)."""
    try:
        psx = (data.get('macros') or {}).get('psx') or {}
        us  = (data.get('macros') or {}).get('us') or {}
        met = (data.get('macros') or {}).get('metals') or {}
        mts = (data.get('psx_mts') or {}).get('market') or {}
        def _len(key):
            v = data.get(key); return len(v) if isinstance(v, list) else None
        def _tier(key, tier):
            v = data.get(key)
            return sum(1 for r in v if isinstance(r, dict) and r.get('tier') == tier) if isinstance(v, list) else None
        snap = {
            'date': dt.date.today().isoformat(),
            'kse100': psx.get('kse100'),
            'sp500': us.get('sp500'),
            'usd_pkr': psx.get('usd_pkr'),
            'sbp_rate': psx.get('sbp_rate'),
            'mts_total_mn': mts.get('total_mn'),
            'mts_change_pct': mts.get('change_pct'),
            'gold_px': met.get('gold_px'),
            'dxy': met.get('dxy'),
            'wti': us.get('wti'),
            'us_10y': us.get('us_10y'),
            'recession_score': (data.get('recession') or {}).get('score'),
            'us_candidates_n': _len('us_candidates'),
            'psx_candidates_n': _len('psx_candidates'),
            'us_tce_high_n': _tier('tce_us', 'HIGH'),
            'psx_tce_high_n': _tier('tce_psx', 'HIGH'),
            # Wave T enrichment v1.120.0 — macro breadth + sector leadership
            'us_diffusion_net': (data.get('us_diffusion') or {}).get('net'),
            'lei_expansion_count': sum(
                1 for v in (data.get('world_lei') or {}).values()
                if isinstance(v, dict) and v.get('signal') == 'expansion'
            ) or None,
            'sector_top': ((data.get('sector_booming') or [{}])[0].get('sector')
                           if data.get('sector_booming') else None),
            'sector_top_score': ((data.get('sector_booming') or [{}])[0].get('score')
                                 if data.get('sector_booming') else None),
            'hy_spread': us.get('hy_spread'),
            'core_pce': us.get('core_pce'),
        }
        hist = existing.get('history')
        if not isinstance(hist, list):
            hist = []
        hist = [h for h in hist if isinstance(h, dict) and h.get('date') != snap['date']]
        hist.append(snap)
        hist.sort(key=lambda h: h.get('date') or '')
        data['history'] = hist[-400:]
        # Backfill the S&P 500 level onto any earlier history row that predates the sp500 field,
        # from the FRED SP500 dated series, so the US 'vs index' read has a benchmark level at each
        # pick's first-seen date (KSE-100 is snapshotted natively). Display/data-only.
        _sp_hist = us.get('sp500_hist') or {}
        if isinstance(_sp_hist, dict) and _sp_hist:
            for _h in data['history']:
                if isinstance(_h, dict) and _h.get('sp500') is None and _h.get('date') in _sp_hist:
                    _h['sp500'] = _sp_hist[_h['date']]
        log(f'  [Wave T history] {snap["date"]}: {len(data["history"])} day(s) stored '
            f'(kse100={snap["kse100"]}, usd/pkr={snap["usd_pkr"]}'
            f', diffusion_net={snap["us_diffusion_net"]}'
            f', lei_exp={snap["lei_expansion_count"]}'
            f', sector_top={snap["sector_top"]} {snap["sector_top_score"]})')
    except Exception as e:
        log(f'  [Wave T history] skipped ({type(e).__name__}: {str(e)[:50]})')
        if isinstance(existing.get('history'), list):
            data['history'] = existing['history']


# =====================================================================================
# Phase 0 — WORLD ECONOMIES MACRO LAYER (v1.117.0)
# Four freeze-safe, additive functions. None touch the universe screen / scoring /
# IM3 / TCE tier / the frozen ledger. Pure DATA-only, guarded, last-good carry.
# =====================================================================================

def _tge_lei(country_slug, indicator='leading-economic-index', diag=True):
    """Fetch a single leading economic indicator value from theglobaleconomy.com.
    Same scraping pattern as the Pakistan CPI _tge() already proven on the runner.
    Returns (value_float, date_str) or (None, None) on failure.
    country_slug examples: 'Japan', 'South-Korea', 'United-States', 'United-Kingdom',
    'China', 'Canada', 'Australia', 'Germany', 'Brazil', 'Taiwan', 'New-Zealand',
    'Switzerland', 'India'."""
    try:
        import requests as _req
        _UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        url = f'https://www.theglobaleconomy.com/{country_slug}/{indicator}/'
        rr = _req.get(url, headers={'User-Agent': _UA}, timeout=20)
        if rr.status_code != 200:
            if diag:
                log(f'  [LEI-TGE] {country_slug}/{indicator}: HTTP {rr.status_code}')
            return None, None
        import re as _re
        txt = _re.sub(r'<[^>]+>', ' ', rr.text)
        txt = txt.replace('&nbsp;', ' ').replace('&nbsp', ' ')
        txt = _re.sub(r'\s+', ' ', txt)
        i = txt.find('Recent values')
        seg = txt[i:i+600] if i >= 0 else txt[:600]
        # Extract date: "YYYY Mon" or "Mon YYYY"
        dm = _re.search(
            r'((?:(?:19|20)\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))|'
            r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:19|20)\d{2}))',
            seg)
        # Extract value after date
        vm = _re.search(
            r'(?:(?:19|20)\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|'
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:19|20)\d{2})'
            r'\s+(-?[\d,]+(?:\.\d+)?)',
            seg)
        val  = float(vm.group(1).replace(',', '')) if vm else None
        date = dm.group(1).strip() if dm else None
        if diag:
            log(f'  [LEI-TGE] {country_slug}: val={val} date={date} hasRecent={i>=0}')
        return val, date
    except Exception as _e:
        if diag:
            log(f'  [LEI-TGE] {country_slug}: {type(_e).__name__}: {str(_e)[:60]}')
        return None, None


def fetch_world_lei():
    """v1.123.1: Restored FRED fredapi for OECD CLI. TGE was JS-rendered — returns
    empty HTML shell to requests.get(); 0/13 fetched on runner (confirmed 2026-06-29).
    FRED fredapi already proven + has retry/backoff (_fred_series pattern).
    12 countries: original 8 + South Korea + Germany + India + Brazil.
    Taiwan excluded (not OECD member — no CLI series). NZ excluded (no FRED series).
    Guarded per-country; miss omits entry; full crash returns {}.
    DATA-only; never touches screen / scoring / TCE / frozen ledger."""
    _LEI_SERIES = {
        'Australia':   'AUSLOLITONOSTSAM',
        'Canada':      'CANLOLITONOSTSAM',
        'China':       'CHNLOLITONOSTSAM',
        'Euro-area':   'EA19LOLITONOSTSAM',  # may be stale — series discontinued; kept + flagged
        'Japan':       'JPNLOLITONOSTSAM',
        'Switzerland': 'CHELOLITONOSTSAM',
        'UK':          'GBRLOLITONOSTSAM',
        'USA':         'USALOLITONOSTSAM',
        # v1.123.1: 4 new OECD members added
        'South Korea': 'KORLOLITONOSTSAM',
        'Germany':     'DEULOLITONOSTSAM',
        'India':       'INDLOLITONOSTSAM',
        'Brazil':      'BRALOLITONOSTSAM',
        # Taiwan: not an OECD member — no CLI series
        # New Zealand: no FRED series (confirmed v1.119.0)
    }
    out = {}
    try:
        from fredapi import Fred as _Fred
        _fred = _Fred(api_key=FRED_KEY)
        for country, series_id in _LEI_SERIES.items():
            try:
                s = _fred.get_series(series_id, observation_start='2020-01-01')
                s = s.dropna()
                if len(s) < 4:
                    log(f'  [World LEI] {country}: insufficient data ({len(s)} obs) — skip')
                    continue
                vals  = list(s.values)
                dates = [str(d)[:10] for d in s.index]
                latest = vals[-1]
                prev1  = vals[-2]
                avg3   = sum(vals[-3:]) / 3
                avg6   = sum(vals[-6:]) / 6 if len(vals) >= 6 else sum(vals) / len(vals)
                slope  = round(avg3 - avg6, 4)
                mom    = round(latest - prev1, 4)
                trend  = 'rising' if slope > 0 else ('falling' if slope < 0 else 'flat')
                signal = 'expansion' if latest > 100 else 'contraction'
                out[country] = {
                    'lei':      round(latest, 3),
                    'slope':    slope,
                    'trend':    trend,
                    'momentum': mom,
                    'signal':   signal,
                    'as_of':    dates[-1],
                }
            except Exception as _e:
                log(f'  [World LEI] {country} skip: {type(_e).__name__}: {str(_e)[:50]}')
        log(f'  [World LEI] {len(out)}/{len(_LEI_SERIES)} countries fetched (FRED)')
    except Exception as e:
        log(f'  [World LEI] fetch failed: {type(e).__name__}: {str(e)[:60]}')
    # Phase 1: enrich with IMF 2026 GDP forecast + World Bank 2024 current account
    # Hardcoded quarterly — update from imf.org/en/Publications/WEO each quarter
    _IMF_GDP = {'Australia':1.6,'Canada':1.4,'China':4.6,'Euro-area':0.8,
                'Japan':0.6,'Switzerland':1.2,'UK':1.1,'USA':1.8,
                'South Korea':2.3,'Germany':0.1,'India':6.5,'Brazil':2.2}
    _WB_CA   = {'Australia':-1.4,'Canada':-0.7,'China':2.1,'Euro-area':2.8,
                'Japan':3.5,'Switzerland':8.2,'UK':-3.1,'USA':-3.3,
                'South Korea':3.9,'Germany':5.8,'India':-1.2,'Brazil':-2.4}
    for _c in list(out):
        out[_c]['gdp_forecast']       = _IMF_GDP.get(_c)
        out[_c]['current_account_pct'] = _WB_CA.get(_c)
    return out


def compute_us_diffusion(us_macros):
    """Phase 0-B: PURE function — reads the already-fetched data['macros']['us'] dict and
    scores 15 indicators into a diffusion index (supportive=+1, not=0, harmful=-1).
    Returns {net_score, supportive, neutral, harmful, total, regime, acceleration, as_of}.
    DATA-only, PURE (no network calls), never touches screening / scoring / TCE."""
    if not us_macros or not isinstance(us_macros, dict):
        return {}
    def _v(k):
        return us_macros.get(k)

    scores = []

    # 1. Fed rate: <=4.0 supportive (accommodative), >5.5 harmful (restrictive)
    fed = _v('fed_rate')
    if fed is not None:
        scores.append(1 if fed <= 4.0 else (-1 if fed > 5.5 else 0))

    # 2. 10y yield: <4.5 supportive, >5.5 harmful
    y10 = _v('us_10y')
    if y10 is not None:
        scores.append(1 if y10 < 4.5 else (-1 if y10 > 5.5 else 0))

    # 3. Yield curve (2s10s): positive = supportive (not inverted)
    yc = _v('yield_curve')
    if yc is None:
        us2 = _v('us_2y'); us10 = _v('us_10y')
        yc = (us10 - us2) if (us2 is not None and us10 is not None) else None
    if yc is not None:
        scores.append(1 if yc > 0 else (-1 if yc < -0.5 else 0))

    # 4. Core PCE: <2.5 supportive, >3.5 harmful
    pce = _v('core_pce')
    if pce is not None:
        scores.append(1 if pce < 2.5 else (-1 if pce > 3.5 else 0))

    # 5. CPI YoY: <3 supportive, >5 harmful
    cpi = _v('cpi_yoy')
    if cpi is not None:
        scores.append(1 if cpi < 3 else (-1 if cpi > 5 else 0))

    # 6. Unemployment: <4.5 supportive (low), >6 harmful (high)
    unemp = _v('unemployment')
    if unemp is not None:
        scores.append(1 if unemp < 4.5 else (-1 if unemp > 6 else 0))

    # 7. UMCSI consumer sentiment: >80 supportive, <60 harmful
    umcsi = _v('umcsi')
    if umcsi is not None:
        scores.append(1 if umcsi > 80 else (-1 if umcsi < 60 else 0))

    # 8. Building permits MoM trend: positive supportive
    permits = _v('permits')
    permits_mom = _v('permits_mom')
    if permits_mom is not None:
        scores.append(1 if permits_mom > 0 else (-1 if permits_mom < -5 else 0))
    elif permits is not None:
        scores.append(0)  # no trend data

    # 9. Industrial production MoM: positive supportive
    ip_mom = _v('industrial_prod_mom')
    if ip_mom is not None:
        scores.append(1 if ip_mom > 0 else (-1 if ip_mom < -1 else 0))

    # 10. GDP growth: >2 supportive, <0 harmful (recession)
    gdp = _v('gdp_growth')
    if gdp is not None:
        scores.append(1 if gdp > 2 else (-1 if gdp < 0 else 0))

    # 11. HY spread: <400bp supportive (risk-on), >700 harmful (stress)
    hy = _v('hy_spread')
    if hy is not None:
        scores.append(1 if hy < 400 else (-1 if hy > 700 else 0))

    # 12. Mfg employment MoM: positive supportive
    mfg = _v('mfg_emp')
    mfg_mom = _v('mfg_emp_mom')
    if mfg_mom is not None:
        scores.append(1 if mfg_mom > 0 else (-1 if mfg_mom < -20 else 0))

    # 13. WTI oil: <80 supportive (not stagflationary), >100 harmful
    wti = _v('wti')
    if wti is not None:
        scores.append(1 if wti < 80 else (-1 if wti > 100 else 0))

    # 14. Financial conditions: proxy via HY already done; use recession score if available
    rec = _v('recession_prob')
    if rec is not None:
        scores.append(1 if rec < 20 else (-1 if rec > 50 else 0))

    # 15. Brent-WTI spread: <$5 supportive (normal), >$10 harmful (supply stress)
    brent = _v('brent') or _v('arab_light')
    if brent is not None and wti is not None:
        bw = brent - wti
        scores.append(1 if bw < 5 else (-1 if bw > 10 else 0))

    if not scores:
        return {}

    supportive = sum(1 for s in scores if s > 0)
    harmful    = sum(1 for s in scores if s < 0)
    neutral    = sum(1 for s in scores if s == 0)
    net        = supportive - harmful
    total      = len(scores)
    regime     = 'Expansion' if net > 0 else ('Contraction' if net < 0 else 'Neutral')
    accel      = supportive > (total * 0.6)

    result = {
        'net_score':   net,
        'net':         net,         # v1.118.0: alias for index.html compatibility
        'supportive':  supportive,
        'neutral':     neutral,
        'harmful':     harmful,
        'deteriorating': harmful,   # v1.118.0: alias matching v1.116 schema
        'total':       total,
        'regime':      regime,
        'phase':       regime,      # v1.118.0: alias for index.html compatibility
        'direction':   'Accelerating' if accel else 'Decelerating',  # v1.118.0: alias
        'acceleration': accel,
        'as_of':       us_macros.get('last_updated') or us_macros.get('_fetched_utc', ''),
    }
    log(f"  [US Diffusion] net={net:+d}  {supportive}/{total} supportive  regime={regime}")
    return result


def compute_global_sector_theme(country_rs):
    """Phase 2: World ETF Engine — re-points the booming-sector concept at GLOBAL markets.
    Reuses country_rs (already fetched, no new network call). Buckets the 13 countries into
    4 regional/thematic groups and scores each by composite momentum + 200-DMA breadth:
      Asia-Tech:       Japan, South Korea, Taiwan        (semiconductor/tech supply chain)
      Developed-West:  USA, UK, Germany, Switzerland, Canada, Australia
      Commodity-Bloc:  Brazil, Australia, Canada          (resource exporters; overlaps West)
      Emerging:        China, India, Brazil
    Score = mean(6M USD return) * 0.6 + (pct above 200-DMA) * 0.4, on a 0-100 scale.
    Returns a list of dicts sorted by score desc: theme, score, band, countries, top_country,
    avg_ret_6m, pct_above_200dma. PURE function — no network call, reuses fetched data.
    DATA-only; never touches screening / scoring / TCE / the frozen ledger."""
    _THEMES = {
        'Asia-Tech':      ['Japan', 'South Korea', 'Taiwan'],
        'Developed-West': ['USA', 'UK', 'Germany', 'Switzerland', 'Canada', 'Australia'],
        'Commodity-Bloc': ['Brazil', 'Australia', 'Canada'],
        'Emerging':       ['China', 'India', 'Brazil'],
    }
    if not country_rs:
        return []
    by_country = {r.get('country'): r for r in country_rs if r.get('country')}
    results = []
    for theme, countries in _THEMES.items():
        rows = [by_country[c] for c in countries if c in by_country]
        if not rows:
            continue
        rets = [r.get('ret_6m') for r in rows if r.get('ret_6m') is not None]
        above = [r.get('above_200dma') for r in rows if r.get('above_200dma') is not None]
        if not rets:
            continue
        avg_ret = sum(rets) / len(rets)
        pct_above = (sum(1 for a in above if a) / len(above) * 100) if above else 50.0
        # Normalise: avg_ret of +15% -> ~100 on the momentum leg; clamp 0-100
        mom_score = max(0, min(100, 50 + avg_ret * 2.5))
        score = round(mom_score * 0.6 + pct_above * 0.4, 1)
        band = ('Booming'  if score >= 75 else
                'Favoured' if score >= 60 else
                'Neutral'  if score >= 40 else
                'Lagging'  if score >= 25 else 'Avoid')
        top_country = max(rows, key=lambda r: r.get('ret_6m') or -999)
        results.append({
            'theme':            theme,
            'score':            score,
            'band':             band,
            'countries':        countries,
            'top_country':      top_country.get('country'),
            'top_country_ret6m': top_country.get('ret_6m'),
            'avg_ret_6m':       round(avg_ret, 1),
            'pct_above_200dma': round(pct_above, 1),
        })
    results.sort(key=lambda r: r['score'], reverse=True)
    log(f"  [Global Theme] {len(results)} themes scored: " +
        ' | '.join(f"{r['theme']}={r['score']}({r['band']})" for r in results))
    return results


def resolve_etf_for_signal(category_key, fallback_keys=None):
    """Phase 3: World ETF Engine — resolve a country/sector signal to a buyable UCITS ETF.
    category_key: an _ETF_CATALOG key (e.g. 'Equity South Korea', 'Equity Technology').
    fallback_keys: optional list of broader categories to try if category_key has no match
    (e.g. ['Equity Asia Pacific', 'Equity World']).
    Returns the largest-by-size qualifying fund dict {name,ter,ytd,size_m_eur,isin,dist} or
    None if no category matches. PURE function — reads only the embedded _ETF_CATALOG.
    DATA-only; never touches screening / scoring / TCE / the frozen ledger."""
    funds = _ETF_CATALOG.get(category_key)
    if funds:
        return dict(funds[0])
    for fb in (fallback_keys or []):
        funds = _ETF_CATALOG.get(fb)
        if funds:
            r = dict(funds[0])
            r['_fallback_from'] = category_key
            r['_resolved_via'] = fb
            return r
    return None


def build_etf_recommendations(country_rs, sector_booming, global_theme):
    """Joins World ETF Engine signals to buyable UCITS ISINs via resolve_etf_for_signal().
    v1.132.0 -- four doors + semiconductor bonus pick:
      Door 1 (country):      top 3 eligible countries by 6M USD return (Overweight/Hedge signal)
      Door 2 (sector):       top 2 US sectors (Booming then Favoured)
      Door 3 (theme):        top 2 themes x top 2 countries per theme; Asia-Tech also fires
                             a semiconductor bonus pick (VanEck SMGB IE00BMC38736)
      Door 4 (em_ex_china):  fires when Emerging Favoured/Booming but China Neutral/Avoid
    Korea/Taiwan two-door: both surface independently when Asia-Tech is Booming.
    Same-ISIN picks from multiple doors merge into one double-confirmed entry.
    PURE function -- no network call. DATA-only; never touches screening / scoring / TCE."""
    _COUNTRY_ETF_CAT = {
        'Japan': 'Equity Japan', 'India': 'Equity India', 'USA': 'Equity United States',
        'UK': 'Equity United Kingdom', 'China': 'Equity China', 'Canada': 'Equity Canada',
        'Australia': 'Equity Australia', 'Germany': 'Equity Germany', 'Brazil': 'Equity Brazil',
        'South Korea': 'Equity South Korea', 'Taiwan': 'Equity Taiwan',
        'Switzerland': 'Equity Switzerland',
    }
    _SECTOR_ETF_CAT = {
        'Materials': 'Equity Basic Materials', 'Information Technology': 'Equity Technology',
        'Energy': 'Equity Energy', 'Industrials': 'Equity Industrials',
        'Consumer Staples': 'Equity Consumer Staples', 'Health Care': 'Equity Health Care',
        'Financials': 'Equity Financials', 'Real Estate': 'Real Estate United States',
        'Consumer Discretionary': 'Equity Consumer Discretionary', 'Utilities': 'Equity Utilities',
        'Communication Services': 'Equity Telecommunication',
    }
    _THEME_COUNTRY_ORDER = {
        'Asia-Tech':      ['Taiwan', 'South Korea', 'Japan'],
        'Developed-West': ['USA', 'UK', 'Germany', 'Switzerland', 'Canada', 'Australia'],
        'Commodity-Bloc': ['Australia', 'Brazil', 'Canada'],
        'Emerging':       ['India', 'Brazil'],
    }
    recs = []
    # v1.137.0: lookup for attaching country trailing returns (3M/6M/12M, already computed by
    # fetch_country_rs -- zero new fetch) onto country-attached picks. Sector-door picks have
    # no country and correctly carry no trailing-return field (honest, not fabricated).
    _crs_by_country = {r['country']: r for r in (country_rs or []) if r.get('country')}
    try:
        # Door 1: top 3 countries by 6M USD return (Overweight/Hedge signal)
        eligible_countries = [r for r in (country_rs or [])
                               if r.get('country') and r.get('signal') in ('Overweight', 'Hedge')]
        for top_c in sorted(eligible_countries, key=lambda r: r.get('ret_6m') or -999, reverse=True)[:3]:
            cat = _COUNTRY_ETF_CAT.get(top_c['country'])
            if cat:
                fund = resolve_etf_for_signal(cat, fallback_keys=['Equity World'])
                if fund:
                    recs.append({
                        'door': 'country', 'signal': top_c['country'],
                        'reason': f"6M USD {top_c.get('ret_6m','--')}% . {top_c.get('signal','--')}",
                        'fund': fund,
                        'country_trailing': {'country': top_c['country'], 'ret_3m': top_c.get('ret_3m'),
                                              'ret_6m': top_c.get('ret_6m'), 'ret_12m': top_c.get('ret_12m')},
                    })

        # Door 2: top 2 US sectors (Booming scores highest then Favoured)
        eligible_sectors = [r for r in (sector_booming or [])
                             if r.get('band') in ('Booming', 'Favoured')]
        for top_s in sorted(eligible_sectors, key=lambda r: r.get('score') or 0, reverse=True)[:2]:
            cat = _SECTOR_ETF_CAT.get(top_s['sector'])
            if cat:
                fund = resolve_etf_for_signal(cat, fallback_keys=['Equity World'])
                if fund:
                    recs.append({
                        'door': 'sector', 'signal': top_s['sector'],
                        'reason': f"score {top_s.get('score','--')} . {top_s.get('band','--')}",
                        'fund': fund,
                    })

        # Door 3: top 2 global themes x top 2 countries (Korea/Taiwan two-door rule)
        # + semiconductor bonus pick when Asia-Tech fires (founding instruction: Korea/Taiwan semis)
        eligible_themes = [r for r in (global_theme or []) if r.get('band') in ('Booming', 'Favoured')]
        for top_t in sorted(eligible_themes, key=lambda r: r.get('score') or 0, reverse=True)[:2]:
            theme_name = top_t.get('theme', '')
            data_top = top_t.get('top_country')
            ordered = ([data_top] if data_top else []) + [
                c for c in _THEME_COUNTRY_ORDER.get(theme_name, []) if c != data_top
            ]
            n_theme = 0
            for country_name in ordered:
                if n_theme >= 2:
                    break
                cat = _COUNTRY_ETF_CAT.get(country_name)
                if cat:
                    fund = resolve_etf_for_signal(cat, fallback_keys=['Equity Asia Pacific', 'Equity World'])
                    if fund:
                        _crow = _crs_by_country.get(country_name) or {}
                        recs.append({
                            'door': 'global_theme', 'signal': theme_name,
                            'reason': (f"score {top_t.get('score','--')} . {theme_name} . "
                                       f"{country_name} {top_t.get('top_country_ret6m','--')}%"),
                            'fund': fund,
                            'country_trailing': {'country': country_name, 'ret_3m': _crow.get('ret_3m'),
                                                  'ret_6m': _crow.get('ret_6m'), 'ret_12m': _crow.get('ret_12m')},
                        })
                        n_theme += 1
            # Semiconductor bonus: VanEck SMGB surfaces when Asia-Tech is Booming/Favoured
            if theme_name == 'Asia-Tech' and n_theme > 0:
                semi_fund = resolve_etf_for_signal('Equity Semiconductors', fallback_keys=['Equity Technology'])
                if semi_fund:
                    recs.append({
                        'door': 'global_theme', 'signal': 'Semiconductors',
                        'reason': (f"score {top_t.get('score','--')} . Asia-Tech booming . "
                                   f"semiconductor pure-play UCITS (founding instruction)"),
                        'fund': semi_fund,
                    })

        # Door 4: EM ex-China -- fires when Emerging is Favoured/Booming but China is weak
        china_rs = next((r for r in (country_rs or []) if r.get('country') == 'China'), None)
        china_sig = china_rs.get('signal') if china_rs else None
        em_theme = next((t for t in (global_theme or [])
                         if t.get('theme') == 'Emerging' and t.get('band') in ('Booming', 'Favoured')), None)
        if em_theme and china_sig in ('Neutral', 'Avoid', None):
            em_ex_fund = resolve_etf_for_signal('Equity Emerging Markets ex China',
                                                fallback_keys=['Equity Emerging Markets'])
            if em_ex_fund:
                recs.append({
                    'door': 'em_ex_china', 'signal': 'EM ex-China',
                    'reason': (f"Emerging {em_theme.get('band')} but China {china_sig or 'not Overweight'} "
                               f"-- ex-China ETF preferred over broad EM"),
                    'fund': em_ex_fund,
                })

        # Merge identical ISINs -- same fund from multiple doors = genuine double-confirmation
        _by_isin = {}
        for r in recs:
            isin = r['fund']['isin']
            if isin in _by_isin:
                _by_isin[isin]['door'] = _by_isin[isin]['door'] + '+' + r['door']
                _by_isin[isin]['signal'] = _by_isin[isin]['signal'] + ' & ' + r['signal']
                _by_isin[isin]['reason'] = _by_isin[isin]['reason'] + ' . also: ' + r['reason']
                _by_isin[isin]['confirmed_count'] = _by_isin[isin].get('confirmed_count', 1) + 1
            else:
                r['confirmed_count'] = 1
                _by_isin[isin] = r
        recs = list(_by_isin.values())
        log(f"  [ETF Recommendations] {len(recs)} resolved: " +
            ', '.join(f"{r['door']}:{r['signal']}->{r['fund']['name'][:30]}"
                      + (f" (x{r['confirmed_count']})" if r.get('confirmed_count',1)>1 else '')
                      for r in recs))
    except Exception as _e:
        log(f"  [ETF Recommendations] skip: {type(_e).__name__}: {str(_e)[:60]}")
    return recs



def fetch_country_rs():
    """v1.123.0: 9→13 countries. Pulls equity-index + FX daily closes via Yahoo Finance and
    computes 3/6/12-month USD-adjusted price momentum + trend label + FX contribution.
    Returns a list of dicts sorted by 6-month USD return (descending).
    Country universe: USA, Japan, Germany, UK, India, Brazil, China, Australia, Canada,
    South Korea (^KS11), Taiwan (^TWII), New Zealand (^NZ50), Switzerland (^SSMI).
    Guarded per-country; a crash returns [].
    DATA-only; never touches the universe screen / scoring / TCE / the frozen ledger."""
    import datetime as _dt
    _COUNTRIES = [
        ('USA',         '^GSPC',    None),
        ('Japan',       '^N225',    'JPY=X'),
        ('Germany',     '^GDAXI',   'EURUSD=X'),
        ('UK',          '^FTSE',    'GBPUSD=X'),
        ('India',       '^BSESN',   'INR=X'),
        ('Brazil',      '^BVSP',    'BRL=X'),
        ('China',       '000001.SS','CNY=X'),
        ('Australia',   '^AXJO',    'AUDUSD=X'),
        ('Canada',      '^GSPTSE',  'CAD=X'),
        # v1.123.0: 4 new countries added — Korea, Taiwan, NZ, Switzerland
        ('South Korea', '^KS11',    'KRW=X'),      # KOSPI; KRW=X = KRW per USD (invert)
        ('Taiwan',      '^TWII',    'TWD=X'),       # Taiwan Weighted; TWD=X = TWD per USD (invert)
        ('New Zealand', '^NZ50',    'NZDUSD=X'),    # NZX50; NZDUSD=X = USD per NZD (direct)
        ('Switzerland', '^SSMI',    'CHFUSD=X'),    # SMI; CHFUSD=X = USD per CHF (direct)
    ]
    # FX tickers that are quote UNITS (USD per 1 FX unit) vs inverted (units per 1 USD)
    _USD_PER_UNIT = {'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'CHFUSD=X'}

    try:
        import yfinance as _yf
    except ImportError:
        log('  [Country RS] yfinance not available')
        return []

    results = []
    end_dt   = _dt.datetime.utcnow()
    start_dt = end_dt - _dt.timedelta(days=400)

    for country, idx_sym, fx_sym in _COUNTRIES:
        try:
            idx = _yf.download(idx_sym, start=start_dt, end=end_dt, auto_adjust=True,
                               progress=False, threads=False)
            if idx.empty or len(idx) < 4:
                continue
            # Get Close column (handle multi-level or single-level)
            if hasattr(idx.columns, 'levels'):
                closes = idx['Close'].iloc[:, 0] if idx['Close'].ndim > 1 else idx['Close']
            else:
                closes = idx['Close']
            closes = closes.dropna()
            if len(closes) < 4:
                continue

            # FX rate: convert local-currency index to USD
            if fx_sym:
                try:
                    fx = _yf.download(fx_sym, start=start_dt, end=end_dt, auto_adjust=True,
                                      progress=False, threads=False)
                    if not fx.empty:
                        if hasattr(fx.columns, 'levels'):
                            fx_close = fx['Close'].iloc[:, 0] if fx['Close'].ndim > 1 else fx['Close']
                        else:
                            fx_close = fx['Close']
                        fx_close = fx_close.dropna().reindex(closes.index, method='ffill').dropna()
                        # Convert: if FX ticker is NOT USD-per-unit, it's units-per-USD (invert)
                        if fx_sym not in _USD_PER_UNIT:
                            fx_close = 1.0 / fx_close
                        # Align
                        common = closes.index.intersection(fx_close.index)
                        if len(common) >= 4:
                            closes_usd = closes.loc[common] * fx_close.loc[common]
                        else:
                            closes_usd = closes
                    else:
                        closes_usd = closes
                except Exception:
                    closes_usd = closes
            else:
                closes_usd = closes  # USA: already in USD

            # 200-DMA: use closes_usd for trend (Phase 0 Wave T index level)
            _sma200 = None; _above_200 = None; _ma_trend = 'unknown'
            if len(closes_usd) >= 200:
                _sma200 = round(float(closes_usd.iloc[-200:].mean()), 2)
                _above_200 = float(closes_usd.iloc[-1]) >= _sma200
                _slope = float(closes_usd.iloc[-200:].mean()) - float(closes_usd.iloc[-220:-20].mean()) if len(closes_usd) >= 220 else 0
                _ma_trend = 'up' if _slope > 0 else ('down' if _slope < 0 else 'flat')
            elif len(closes_usd) >= 50:
                _sma200 = round(float(closes_usd.iloc[-50:].mean()), 2)
                _above_200 = float(closes_usd.iloc[-1]) >= _sma200
                _ma_trend = 'partial'  # <200 days available

            # Local return (index in local currency, no FX conversion)
            _loc3 = _loc6 = _loc12 = None
            if fx_sym and len(closes) >= 4:
                _l_latest = float(closes.iloc[-1])
                _l3 = float(closes.iloc[-min(13,len(closes))])
                _l6 = float(closes.iloc[-min(26,len(closes))])
                _l12 = float(closes.iloc[-min(52,len(closes))])
                _loc3  = round((_l_latest/_l3  - 1)*100, 1) if _l3  else None
                _loc6  = round((_l_latest/_l6  - 1)*100, 1) if _l6  else None
                _loc12 = round((_l_latest/_l12 - 1)*100, 1) if _l12 else None

            latest = float(closes_usd.iloc[-1])
            m3_ago = float(closes_usd.iloc[-min(13, len(closes_usd))])
            m6_ago = float(closes_usd.iloc[-min(26, len(closes_usd))])
            m12_ago= float(closes_usd.iloc[-min(52, len(closes_usd))])

            ret3  = round((latest / m3_ago  - 1) * 100, 1) if m3_ago  else None
            ret6  = round((latest / m6_ago  - 1) * 100, 1) if m6_ago  else None
            ret12 = round((latest / m12_ago - 1) * 100, 1) if m12_ago else None

            # Trend
            if ret3 is not None and ret6 is not None:
                trend = 'rising' if ret3 > ret6 * 0.5 else ('falling' if ret3 < 0 else 'flat')
            else:
                trend = 'unknown'

            # Signal: Overweight >+15% · Hedge ±5–15% or -5–-10% · Neutral -5%..+5% · Avoid <-10%
            if ret6 is not None:
                if ret6 > 15:              signal = 'Overweight'
                elif ret6 < -10:           signal = 'Avoid'
                elif -5 <= ret6 <= 5:      signal = 'Neutral'
                else:                      signal = 'Hedge'  # +5..+15 or -10..-5
            else:
                signal = 'Neutral'

            # FX drag = USD return minus local return (negative = currency hurt you)
            _fx3  = round(ret3  - _loc3,  1) if ret3  is not None and _loc3  is not None else None
            _fx6  = round(ret6  - _loc6,  1) if ret6  is not None and _loc6  is not None else None
            _fx12 = round(ret12 - _loc12, 1) if ret12 is not None and _loc12 is not None else None
            results.append({
                'country':     country,
                'ret_3m':      ret3,
                'ret_6m':      ret6,
                'ret_12m':     ret12,
                'local_ret_3m':  _loc3,
                'local_ret_6m':  _loc6,
                'local_ret_12m': _loc12,
                'fx_drag_3m':    _fx3,
                'fx_drag_6m':    _fx6,
                'fx_drag_12m':   _fx12,
                'above_200dma':  _above_200,
                'sma200':        _sma200,
                'ma_trend':      _ma_trend,
                'trend':         trend,
                'signal':        signal,
            })
        except Exception as _e:
            log(f'  [Country RS] {country} skip: {type(_e).__name__}: {str(_e)[:40]}')

    results.sort(key=lambda r: (r.get('ret_6m') or -999), reverse=True)
    # Phase 1: dollar_direction composite (DXY trend + FX drag breadth)
    try:
        # v1.126.1 fix: fetch_country_rs() has no access to the global 'data' dict (it's
        # called as a standalone function, metals aren't a parameter) — 'data' is undefined
        # here, which crashed every run silently into the except. Read from EXISTING only
        # (last committed data.json); DXY trend moves slowly so one-run-behind is fine.
        _dxy_trend  = safe_get(EXISTING, 'macros', 'metals', 'dxy_ma_trend') or 'unknown'
        _dxy_sma200 = safe_get(EXISTING, 'macros', 'metals', 'dxy_sma200')
        _dxy_px     = safe_get(EXISTING, 'macros', 'metals', 'dxy')
        _rs = [r for r in results if r.get('fx_drag_6m') is not None]
        _fx_neg = sum(1 for r in _rs if r['fx_drag_6m'] < -2)  # USD strong vs country
        _fx_pos = sum(1 for r in _rs if r['fx_drag_6m'] >  2)  # USD weak vs country
        _dxy_above = bool(_dxy_px and _dxy_sma200 and _dxy_px > _dxy_sma200)
        if _dxy_above and _fx_neg >= 4:       _dd = 'Strong'
        elif not _dxy_above and _fx_pos >= 4: _dd = 'Weakening'
        else:                                  _dd = 'Neutral'
        results.append({'__meta__': 'dollar_direction', 'dollar_direction': _dd,
                         'fx_neg_count': _fx_neg, 'fx_pos_count': _fx_pos,
                         'dxy_above_200': _dxy_above})
        log(f'  [Country RS] Dollar direction: {_dd} '
            f'(DXY above200={_dxy_above}, currencies losing to USD: {_fx_neg}/{len(_rs)})')
    except Exception as _dde:
        log(f'  [Country RS] dollar_direction skip: {_dde}')
    log(f'  [Country RS] {len([r for r in results if "country" in r])}/9 countries ranked')
    return results


def fetch_fund_holdings(fund_ticker):
    """Wave Z: fetch top holdings for a mutual fund ticker via yfinance.
    Returns list of tickers (strings). Gracefully returns [] on any error."""
    try:
        import yfinance as yf
        tk = yf.Ticker(fund_ticker)
        # get_funds_data() returns a dict with 'top_holdings' key
        fd = tk.get_funds_data()
        if fd and hasattr(fd, 'top_holdings') and fd.top_holdings is not None:
            holdings = list(fd.top_holdings.index)[:INST_FUND_TOP_N]
            return [str(h).upper() for h in holdings if h]
        # fallback: .info['holdings'] on some fund tickers
        info = tk.info or {}
        held = info.get('holdings', [])
        return [h.get('symbol','').upper() for h in held if h.get('symbol')][:INST_FUND_TOP_N]
    except Exception as e:
        log(f'  [Wave Z] fund {fund_ticker} fetch failed: {type(e).__name__}: {str(e)[:40]}')
        return []


def compute_inst_consensus(etf_overlap, fund_holdings_map):
    """Wave Z: intersect ETF top-25 consensus stocks with institutional fund holdings.
    A stock is 'double-confirmed' if it appears in:
      - ETF top-25 consensus (etf_overlap['stocks'])  AND
      - holdings of ≥2 institutional funds in fund_holdings_map
    Combined score = ETF_conviction×0.6 + fund_count×10×0.4 (capped at 100).
    Returns list of dicts sorted by combined_score desc."""
    try:
        etf_stocks = (etf_overlap or {}).get('stocks', [])
        if not etf_stocks or not fund_holdings_map:
            return []
        # Build ETF conviction map: ticker -> conviction score (0-100 from etf_overlap)
        etf_map = {}
        for s in etf_stocks:
            tk = (s.get('ticker') or '').upper()
            if tk:
                etf_map[tk] = s.get('score', 50) or 50
        # Build fund count map: ticker -> set of funds holding it
        fund_map = {}
        for fund, holdings in fund_holdings_map.items():
            for tk in holdings:
                tk = tk.upper()
                if tk not in fund_map:
                    fund_map[tk] = set()
                fund_map[tk].add(fund)
        # Intersect: must be in ETF top-25 AND in ≥2 funds
        results = []
        for tk, etf_score in etf_map.items():
            funds = fund_map.get(tk, set())
            fund_count = len(funds)
            if fund_count >= 2:
                combined = round(etf_score * 0.6 + min(fund_count * 10, 40) * 1.0, 1)
                results.append({
                    'ticker': tk,
                    'etf_score': etf_score,
                    'fund_count': fund_count,
                    'funds': sorted(list(funds)),
                    'combined_score': combined,
                })
        results.sort(key=lambda r: r['combined_score'], reverse=True)
        log(f'  [Wave Z] inst_consensus: {len(results)} double-confirmed stocks '
            f'(ETF∩≥2 funds) from {len(fund_holdings_map)} funds / {len(etf_map)} ETF names')
        return results
    except Exception as e:
        log(f'  [Wave Z] compute_inst_consensus crashed: {type(e).__name__}: {str(e)[:60]}')
        return []


def compute_psx_sector_booming(psx_sector_breadth, psx_sector_medians, psx_macros):
    """Wave S (PSX): PURE function — 3-signal 0-100 composite per PSX sector.
    Signals:
      breadth     40% — % names above 200-DMA (psx_sector_breadth)
      momentum    35% — 1-month price performance (psx_sector_medians Perf.1M)
      rate_sens   25% — SBP rate vs 11% line * sector sensitivity (beneficiary/neutral/sensitive)
    Band: Booming >=80 / Favoured >=62 / Neutral >=45 / Lagging >=30 / Avoid <30.
    DATA-only, freeze-safe, no network calls. Returns [] on bad input (guarded)."""
    try:
        PSX_RATE_SENS = {
            # PSX TV sector name -> (sensitivity, direction at high rate)
            'Finance':              ('beneficiary', +1),   # banks earn more on spread
            'Process Industries':  ('beneficiary', +1),   # fertilizer (pricing power)
            'Energy Minerals':     ('neutral',      0),   # E&P (oil-driven not rate)
            'Health Technology':   ('neutral',      0),   # pharma (defensive)
            'Technology Services': ('neutral',      0),   # IT (FX-driven)
            'Electronic Technology': ('neutral',    0),
            'Distribution Services': ('neutral',   0),   # OMC
            'Utilities':           ('neutral',      0),   # power (govt-contracted)
            'Energy':              ('neutral',      0),
            'Non-Energy Minerals': ('sensitive',   -1),   # cement (construction slows)
            'Consumer Durables':   ('sensitive',   -1),   # autos
            'Consumer Non-Durables': ('sensitive', -1),   # textile
            'Producer Manufacturing': ('sensitive',-1),
            'Retail Trade':        ('sensitive',   -1),
        }
        sbp_rate = (psx_macros or {}).get('sbp_rate') or 0
        rate_above_def = max(0, sbp_rate - 11.0)  # pts above 11% defensive line
        results = []
        sectors_scored = set()
        # Merge breadth and medians
        for sec, bdata in (psx_sector_breadth or {}).items():
            if not isinstance(bdata, dict):
                continue
            if sec in sectors_scored:
                continue
            sectors_scored.add(sec)
            breadth_pct = bdata.get('pct', 0) or 0          # 0-100
            mdata = (psx_sector_medians or {}).get(sec, {}) or {}
            perf1m = mdata.get('perf_1m') or mdata.get('Perf.1M') or 0  # %
            # --- signal 1: breadth (0-100) ──────────────────────────────────
            s_breadth = max(0.0, min(100.0, breadth_pct))
            # --- signal 2: momentum (normalise perf_1m to 0-100) ───────────
            # Map -10% to +10% onto 0-100; clip outside
            norm_mom = max(0.0, min(100.0, (perf1m + 10.0) * 5.0))
            # --- signal 3: rate sensitivity (0-100) ─────────────────────────
            sens, direction = PSX_RATE_SENS.get(sec, ('neutral', 0))
            if direction == +1:
                # beneficiary: higher rate = better; score 50 + rate_above_def*5 (capped 100)
                s_rate = min(100.0, 50.0 + rate_above_def * 5.0)
            elif direction == -1:
                # sensitive: higher rate = worse; score 50 - rate_above_def*5 (floor 0)
                s_rate = max(0.0, 50.0 - rate_above_def * 5.0)
            else:
                s_rate = 50.0   # neutral
            # --- composite ───────────────────────────────────────────────────
            composite = round(s_breadth*0.40 + norm_mom*0.35 + s_rate*0.25, 1)
            if composite >= 80:   band = 'Booming'
            elif composite >= 62: band = 'Favoured'
            elif composite >= 45: band = 'Neutral'
            elif composite >= 30: band = 'Lagging'
            else:                 band = 'Avoid'
            results.append({
                'sector': sec, 'score': composite, 'band': band,
                'rate_sensitivity': sens,
                'signals': {
                    'breadth_200dma': round(s_breadth, 1),
                    'momentum_1m': round(norm_mom, 1),
                    'rate_sens_score': round(s_rate, 1),
                    'perf_1m_raw': round(perf1m, 2),
                    'sbp_rate': sbp_rate,
                },
                'score_delta': None, 'score_trend': None,
            })
        results.sort(key=lambda r: r['score'], reverse=True)
        for i, r in enumerate(results):
            r['rank'] = i + 1
        log(f'  [PSX Sector Booming] {len(results)} sectors scored: '
            + ' | '.join(f'{b}={sum(1 for r in results if r["band"]==b)}'
                         for b in ["Booming","Favoured","Neutral","Lagging","Avoid"] if
                         any(r["band"]==b for r in results)))
        return results
    except Exception as e:
        log(f'  [PSX Sector Booming] crashed: {type(e).__name__}: {str(e)[:60]}')
        return []


def compute_sector_booming(zacks_sectors, cot_futures, metals_data=None):
    """Phase 0-D: PURE function — reuses already-fetched zacks_sectors + cot_futures dicts,
    scores each sector 0-100 across 6 weighted signals:
      price momentum 25% | 200-DMA breadth 20% | forward targets+Zacks rotation 20%
      regime fit 15%     | relative strength 10% | COT 10% (honest: only 6 sectors mapped)
    Returns a list of dicts sorted by score (descending), each carrying:
      sector, score, band (Booming/Favoured/Neutral/Lagging/Avoid), rank, signals, decisive.
    COT honesty rule (SX-5): only Energy/Utilities/Staples/Materials/Financials/Tech mapped
    to real futures contracts; all others get zero COT weight rather than S&P proxy.
    DATA-only, PURE (no network calls), never touches screening / scoring / TCE."""

    # Sectors with a genuine COT futures contract mapped in the scanner
    # Matches cotFor() in index.html; Health Care / Consumer Discretionary / Real Estate
    # have no genuine tradeable proxy and correctly stay excluded (no SP500 stand-in).
    _COT_MAPPED = {'Energy', 'Utilities', 'Consumer Staples', 'Materials',
                   'Financials', 'Information Technology', 'Communication Services',
                   'Industrials'}

    results = []
    if not zacks_sectors or not isinstance(zacks_sectors, dict):
        return results

    # Extract COT signals — mirrors cotFor() mapping in index.html (single source of truth).
    # SX-5 honesty rule: only map sectors where a real futures contract exists.
    # Materials uses gold+copper net from macros.metals (already fetched every run).
    # SP500 is NEVER used as a proxy for unlisted sectors.
    cot = cot_futures or {}
    cot_by_sector = {}

    def _cot_sig(contract_key):
        """Return signal string for a contract key, or None if unavailable."""
        c = cot.get(contract_key, {})
        if c and isinstance(c, dict):
            sig = c.get('signal', '')
            return sig if sig else None
        return None

    # Direct contract mappings (matching cotFor() in index.html exactly)
    for sec, keys in [
        ('Energy',               ['Crude', 'NatGas']),       # crude oil primary
        ('Utilities',            ['NatGas']),                 # natural gas
        ('Consumer Staples',     ['Agriculture']),            # corn/agriculturals
        ('Information Technology', ['NASDAQ']),              # NASDAQ-100
        ('Communication Services', ['NASDAQ']),              # NASDAQ-100 (tech-adjacent)
        ('Financials',           ['10yr']),                  # 10yr Treasury (bank curve)
        ('Industrials',          ['DJIA']),                  # Dow Jones blue-chip
    ]:
        for k in keys:
            sig = _cot_sig(k)
            if sig:
                cot_by_sector[sec] = sig
                break

    # Materials: gold + copper combined net (same logic as metalsCot() in cotFor())
    # Both are already fetched into data['macros']['metals'] every run
    try:
        _met = metals_data if isinstance(metals_data, dict) else {}
        _g_net = _met.get('cot_gold_net')
        _c_net = _met.get('cot_copper_net')
        if _g_net is not None or _c_net is not None:
            _mat_net = (_g_net or 0) + (_c_net or 0)
            if _mat_net > 250000:   cot_by_sector['Materials'] = 'VERY BULLISH'
            elif _mat_net > 0:      cot_by_sector['Materials'] = 'BULLISH'
            elif _mat_net > -250000: cot_by_sector['Materials'] = 'BEARISH'
            else:                   cot_by_sector['Materials'] = 'VERY BEARISH'
    except Exception:
        pass  # Materials COT stays absent — honest, never fabricated

    rank = 0
    scores_raw = []
    for sec, sv in zacks_sectors.items():
        if not isinstance(sv, dict) or sec.startswith('_'):
            continue

        sig_scores = {}

        # Signal 1: Price momentum (Zacks pct_top = % of sector at rank #1/#2)
        pct_top = sv.get('pct_top', 0) or 0
        sig_scores['zacks_pct_top'] = min(100, pct_top * 2.5)  # 40% -> 100

        # Signal 2: 200-DMA breadth
        breadth = sv.get('breadth_200dma')
        sig_scores['breadth_200dma'] = (breadth if breadth is not None else 50)

        # Signal 3: Forward targets + Zacks rotation
        tgt_upside = sv.get('tgt_upside')
        zacks_rot  = sv.get('pct_top_chg', 0) or 0
        tgt_score  = min(100, max(0, (tgt_upside or 0) * 3))  # 33% upside -> 100
        rot_score  = min(100, max(0, 50 + zacks_rot * 5))
        sig_scores['forward'] = (tgt_score + rot_score) / 2

        # Signal 4: Regime fit — placeholder (50 = neutral; would improve with macro context)
        sig_scores['regime_fit'] = 50

        # Signal 5: Relative strength (perf vs market) — use 1M perf if available
        perf1m = sv.get('perf_1m')
        if perf1m is not None:
            rs_score = min(100, max(0, 50 + float(perf1m) * 2))
        else:
            rs_score = 50
        sig_scores['rel_strength'] = rs_score

        # Signal 6: COT — ONLY for genuinely mapped sectors (SX-5 honesty rule)
        if sec in _COT_MAPPED and sec in cot_by_sector:
            cot_sig = cot_by_sector[sec]
            cot_score = 75 if 'BULLISH' in cot_sig.upper() else (
                        25 if 'BEARISH' in cot_sig.upper() else 50)
            sig_scores['cot'] = cot_score
        else:
            sig_scores['cot'] = None  # Excluded — no real contract; weight goes to others

        # Weighted composite (renormalise if COT excluded)
        weights = {
            'zacks_pct_top':  0.25,
            'breadth_200dma': 0.20,
            'forward':        0.20,
            'regime_fit':     0.15,
            'rel_strength':   0.10,
            'cot':            0.10,
        }
        total_w = sum(w for k, w in weights.items() if sig_scores.get(k) is not None)
        if total_w <= 0:
            continue
        composite = sum(
            sig_scores[k] * w / total_w
            for k, w in weights.items()
            if sig_scores.get(k) is not None
        )
        scores_raw.append((sec, round(composite, 1), sig_scores))

    scores_raw.sort(key=lambda x: x[1], reverse=True)

    for rank_idx, (sec, score, sig_scores) in enumerate(scores_raw, 1):
        band = ('Booming'  if score >= 80 else
                'Favoured' if score >= 62 else
                'Neutral'  if score >= 45 else
                'Lagging'  if score >= 30 else 'Avoid')

        # Decisive signal = the highest-weight non-None signal
        decisive = max(
            ((k, v) for k, v in sig_scores.items() if v is not None),
            key=lambda kv: weights.get(kv[0], 0) * kv[1],
            default=('—', 0)
        )[0]

        results.append({
            'sector':   sec,
            'score':    score,
            'band':     band,
            'rank':     rank_idx,
            'signals':  {k: round(v, 1) if v is not None else None
                         for k, v in sig_scores.items()},
            'decisive': decisive,
        })

    # Summary log
    bands = {}
    for r in results:
        bands[r['band']] = bands.get(r['band'], 0) + 1
    log(f"  [Sector Booming] {len(results)} sectors scored: " +
        ' | '.join(f"{b}={n}" for b, n in sorted(bands.items())))
    return results



def main():
    log('=' * 60)
    log(f'Dashboard scanner v{SCAN_VERSION} starting')
    log('=' * 60)

    data = DEFAULT_DATA.copy()
    data['meta'] = {
        'scan_version':  SCAN_VERSION,
        'last_scan_utc': dt.datetime.utcnow().isoformat() + 'Z',
        'errors':        [],
        'warnings':      [],
    }

    try:
        data['macros']['us'] = fetch_us_macros()
    except Exception as e:
        log(f'US macros crashed: {e}')
        data['meta']['errors'].append(f'us_macros: {e}')
        data['macros']['us'] = EXISTING.get('macros', {}).get('us', {})

    try:
        data['macros']['psx'] = fetch_psx_macros()
    except Exception as e:
        log(f'PSX macros crashed: {e}')
        data['meta']['errors'].append(f'psx_macros: {e}')
        data['macros']['psx'] = EXISTING.get('macros', {}).get('psx', {})

    try:
        data['macros']['metals'] = fetch_metals()
    except Exception as e:
        log(f'Metals macros crashed: {e}')
        data['meta']['errors'].append(f'metals_macros: {e}')
        data['macros']['metals'] = EXISTING.get('macros', {}).get('metals', {})

    us_all_survivors = []
    try:
        us_result = screen_us_universe()
        data['us_funnel']    = us_result['funnel']
        data['us_candidates'] = us_result['candidates']
        us_all_survivors     = us_result.get('all_survivors', us_result['candidates'])
    except Exception as e:
        log(f'US screening crashed: {e}')
        data['meta']['errors'].append(f'us_screen: {e}')
        data['us_funnel']    = EXISTING.get('us_funnel', [])
        data['us_candidates'] = EXISTING.get('us_candidates', [])
        us_all_survivors     = data['us_candidates']

    # Wave R (Option C): per-sector medians for peer-relative IM3 (P/E, margins, ROE).
    # Isolated POST; failure carries last-good. Writes sector_medians.json for im3_score.py.
    try:
        data['sector_medians'] = fetch_sector_medians()
        try:
            probe_dividend_yield_columns()
        except Exception as _e:
            log(f'  [div-yield probe] skipped ({_e})')
        try:
            probe_data_sources_v199()
        except Exception as _e:
            log(f'  [v199 probe] skipped ({_e})')
        try:
            probe_cot_legacy()
        except Exception as _e:
            log(f'  [COT legacy probe] skipped ({_e})')
    except Exception as e:
        log(f'sector medians crashed: {e}')
        data['sector_medians'] = EXISTING.get('sector_medians', {}) or {}

    # Wave M-A step 2b: surface a clean top-level US sector-breadth block (% of each sector
    # at/above its 200-DMA) for the dashboard, derived from the same medians POST above.
    try:
        _sm = data.get('sector_medians') or {}
        data['sector_breadth'] = {
            sec: {'pct': v['breadth_200dma'], 'n': v.get('breadth_n', v.get('n')),
                  'above': round(v['breadth_200dma'] * v.get('breadth_n', v.get('n', 0)) / 100.0)}
            for sec, v in _sm.items() if isinstance(v, dict) and v.get('breadth_200dma') is not None
        }
        if not data['sector_breadth']:
            data['sector_breadth'] = EXISTING.get('sector_breadth', {}) or {}
    except Exception as e:
        log(f'sector breadth derive crashed: {e}')
        data['sector_breadth'] = EXISTING.get('sector_breadth', {}) or {}

    # Wave M-A step 2b (PSX): wide-universe PSX sector breadth (% above 200-DMA), own isolated POST.
    try:
        data['psx_sector_breadth'] = fetch_psx_sector_breadth() or (EXISTING.get('psx_sector_breadth', {}) or {})
    except Exception as e:
        log(f'psx sector breadth crashed: {e}')
        data['psx_sector_breadth'] = EXISTING.get('psx_sector_breadth', {}) or {}

    # Wave S Phase 2 (PSX): PSX sector MEDIANS (P/E, margins, ROE) + price-move (Perf.W/1M/3M), own isolated POST.
    try:
        data['psx_sector_medians'] = fetch_psx_sector_medians() or (EXISTING.get('psx_sector_medians', {}) or {})
    except Exception as e:
        log(f'psx sector medians crashed: {e}')
        data['psx_sector_medians'] = EXISTING.get('psx_sector_medians', {}) or {}

    # Wave S (PSX): PSX sector composite scores (v1.121.0)
    try:
        _psb = compute_psx_sector_booming(
            data.get('psx_sector_breadth', {}),
            data.get('psx_sector_medians', {}),
            (data.get('macros') or {}).get('psx') or {}
        )
        # WoW delta vs EXISTING (same pattern as US sector_booming)
        _prior_psb = {r['sector']: r['score'] for r in (EXISTING.get('psx_sector_booming') or [])
                      if isinstance(r, dict) and r.get('sector') and r.get('score') is not None}
        for _r in _psb:
            _sec = _r.get('sector'); _now = _r.get('score')
            _prev = _prior_psb.get(_sec)
            if _now is not None and _prev is not None:
                _d = round(_now - _prev, 1)
                _r['score_delta'] = _d
                _r['score_trend'] = 'rising' if _d >= 1.0 else ('falling' if _d <= -1.0 else 'flat')
        data['psx_sector_booming'] = _psb or EXISTING.get('psx_sector_booming', []) or []
    except Exception as _e:
        log(f'  [PSX Sector Booming] skipped: {type(_e).__name__}: {str(_e)[:50]}')
        data['psx_sector_booming'] = EXISTING.get('psx_sector_booming', []) or []

        # Wave PK-D: PSX PKR-devaluation alert (display/data-only multi-signal basket).
    try:
        _psx_m = dict((data.get('macros') or {}).get('psx') or {})
        _psx_m['_history_ref'] = data.get('history') or []
        data['psx_devaluation'] = compute_psx_devaluation(_psx_m)
        _pkd = data['psx_devaluation']
        log(f'  [Wave PK-D] devaluation: {str(_pkd.get("level", "?")).upper()} '
            f'(score {_pkd.get("score")}/{_pkd.get("max_score")}) -> '
            + ', '.join(f'{k}={v.get("points")}' for k, v in (_pkd.get('signals') or {}).items()))
    except Exception as e:
        log(f'psx devaluation crashed: {e}')
        data['psx_devaluation'] = EXISTING.get('psx_devaluation', {}) or {}

    try:
        psx_result = screen_psx_universe()
        data['psx_funnel']    = psx_result['funnel']
        data['psx_candidates'] = psx_result['candidates']
        # Wave Q Phase-1: bank-data overlays (display/context + sector evaluation; never the IG2 scoring series)
        try:
            _bank_syms = sorted({c.get('ticker') for c in data['psx_candidates']
                                 if c.get('ticker') and _is_true_bank(c.get('sector'), c.get('name'), c.get('ticker'))})
            data['bank_snapshot'] = fetch_bank_snapshot(_bank_syms)
        except Exception as _e:
            log(f'  [Wave Q snapshot] error ({_e})'); data['bank_snapshot'] = EXISTING.get('bank_snapshot', {})
        try:
            data['bank_sector'] = fetch_bank_sector_kpmg()
        except Exception as _e:
            log(f'  [Wave Q sector] error ({_e})'); data['bank_sector'] = EXISTING.get('bank_sector', {})
        # A (SCS -> IG2 fallback): write roe/adr/roa-trend overrides for partial banks (fill-missing only downstream)
        try:
            write_bank_ig2_overrides(data)
        except Exception as _e:
            log(f'  [Wave Q->IG2] override write error ({_e})')
        try:
            fetch_us_bank_ig2(data)   # Group-D: FDIC US-bank IG2 inputs -> MERGE into bank_ig2_overrides.json (consumer already wired, calib=us)
        except Exception as _e:
            log(f'  [US-bank IG2] error ({_e})')
    except Exception as e:
        log(f'PSX screening crashed: {e}')
        data['meta']['errors'].append(f'psx_screen: {e}')
        data['psx_funnel']    = EXISTING.get('psx_funnel', [])
        data['psx_candidates'] = EXISTING.get('psx_candidates', [])

    # Wave P Phase-1 + v1.48.0 change-tracking: AMC fund-ownership overlay + month-over-month FLOW
    # (DISPLAY ONLY; not a scored stream -> respects freeze). FMRs are MONTHLY PDFs, so the fetch is
    # throttled to once / 7 days (carry last-good between -> ~6x less load on fundbazaarglobal).
    try:
        _prev_fo = EXISTING.get('psx_fund_ownership', {}) or {}
        _last_fetch = _prev_fo.get('last_fetch_utc'); _age = None
        if _last_fetch:
            try:
                _age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_last_fetch).replace('Z', ''))).days
            except Exception:
                _age = None
        if _age is not None and _age < 7 and _prev_fo.get('by_ticker'):
            log(f'  [Wave P FMR] fetch skipped ({_age}d ago, <7d) — carrying last-good fund-ownership + flows')
            data['psx_fund_ownership'] = _prev_fo
            _carry = _prev_fo.get('by_ticker', {})
            for _c in data['psx_candidates']:
                _o = _carry.get(_c.get('ticker'))
                if _o:
                    _c['fund_ownership'] = _o
        else:
            _fmr_by_ticker, _fmr_meta, _cur_per_fund = fetch_fmr_fund_ownership()
            if _fmr_by_ticker:
                _snaps = _prev_fo.get('snapshots') or []
                _prior_pf = _snaps[-1].get('per_fund') if _snaps else None
                _flows = _fmr_compute_flows(_cur_per_fund, _prior_pf) if _prior_pf else {}
                for _tk, _v in _fmr_by_ticker.items():
                    _fl = _flows.get(_tk)
                    if _fl:
                        _v.update(_fl)
                    else:
                        _v['flow'] = 'BASELINE'; _v['funds_delta'] = None; _v['weight_delta'] = None
                for _c in data['psx_candidates']:
                    _o = _fmr_by_ticker.get(_c.get('ticker'))
                    if _o:
                        _c['fund_ownership'] = _o
                # snapshot history: append current ONLY on a clean refresh (coverage not regressed +
                # content changed) so weekly re-fetches of the SAME monthly FMR never pollute the baseline
                def _sig(pf):
                    return frozenset((t, round(w, 1)) for fnd in pf for t, w in pf[fnd].items())
                _changed = (not _prior_pf) or (_sig(_cur_per_fund) != _sig(_prior_pf))
                _new_snaps = list(_snaps)
                if _changed and set(_cur_per_fund) >= (set(_prior_pf) if _prior_pf else set()):
                    _new_snaps.append({'ts': dt.datetime.utcnow().isoformat() + 'Z', 'per_fund': _cur_per_fund})
                    _new_snaps = _new_snaps[-4:]
                _n_mv = sum(1 for _v in _fmr_by_ticker.values()
                            if _v.get('flow') in ('ACCUMULATING', 'TRIMMING', 'NEW', 'EXITED'))
                log('  [Wave P FMR] flow: ' + ('BASELINE run (first deltas land next month)' if not _prior_pf
                    else f'{_n_mv} names moved vs prior snapshot; {len(_new_snaps)} snapshot(s) kept'))
                data['psx_fund_ownership'] = {'by_ticker': _fmr_by_ticker, 'meta': _fmr_meta,
                                              'snapshots': _new_snaps,
                                              'last_fetch_utc': dt.datetime.utcnow().isoformat() + 'Z'}
            else:
                data['psx_fund_ownership'] = _prev_fo
    except Exception as e:
        log(f'  [Wave P FMR] overlay error ({e}) -> skipped')
        data['psx_fund_ownership'] = EXISTING.get('psx_fund_ownership', {})

    # Wave PSX-R Phase-1: SCS Valuation Matrix overlay (DISPLAY/data only; weekly PDF -> throttle 7d,
    # carry last-good between). Never touches screening/scoring/TCE -> respects the Sept freeze.
    try:
        _prev_vm = EXISTING.get('psx_valuation_matrix', {}) or {}
        _vm_last = _prev_vm.get('last_fetch_utc'); _vm_age = None
        if _vm_last:
            try:
                _vm_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_vm_last).replace('Z', ''))).days
            except Exception:
                _vm_age = None
        if _vm_age is not None and _vm_age < 7 and _prev_vm.get('by_ticker') and ('suggested' in _prev_vm):
            log(f'  [Wave PSX-R valmatrix] fetch skipped ({_vm_age}d ago, <7d) — carrying last-good')
            data['psx_valuation_matrix'] = _prev_vm
        else:
            _vm = fetch_psx_valuation_matrix()
            if _vm.get('by_ticker'):
                _vm['last_fetch_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
                data['psx_valuation_matrix'] = _vm
            else:
                data['psx_valuation_matrix'] = _prev_vm
    except Exception as e:
        log(f'  [Wave PSX-R valmatrix] overlay error ({e}) -> skipped')
        data['psx_valuation_matrix'] = EXISTING.get('psx_valuation_matrix', {})

    # Wave PSX-R Phase-3: SCS MTS leverage gauge (DISPLAY/data only; daily PDF; guarded, last-good).
    # Never touches screening/scoring/TCE -> respects the Sept freeze.
    try:
        _mts = fetch_psx_mts()
        if _mts.get('market') or _mts.get('book'):
            _mts['last_fetch_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
            data['psx_mts'] = _mts
        else:
            data['psx_mts'] = EXISTING.get('psx_mts', {})
    except Exception as e:
        log(f'  [Wave PSX-R MTS] overlay error ({e}) -> skipped')
        data['psx_mts'] = EXISTING.get('psx_mts', {})

    # Wave PSX-R Phase-4: SCS MSCI Provisional Indexes (index in/exclusion catalyst; DISPLAY/data only; guarded,
    # last-good, 7-day throttle since the review is semi-annual). Never touches screening/scoring/TCE -> Sept freeze.
    try:
        if not SCS_MSCI_INGEST:
            data['psx_msci'] = {}
            raise _MsciShelved()
        _prev_msci = EXISTING.get('psx_msci', {}) or {}
        _ms_age = None; _ms_last = _prev_msci.get('last_fetch_utc')
        if _ms_last:
            try:
                _ms_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_ms_last).replace('Z', ''))).days
            except Exception:
                _ms_age = None
        if _ms_age is not None and _ms_age < 7 and (_prev_msci.get('by_ticker') or _prev_msci.get('added') or _prev_msci.get('deleted')):
            log(f'  [Wave PSX-R MSCI] fetch skipped ({_ms_age}d ago, <7d) — carrying last-good')
            data['psx_msci'] = _prev_msci
        else:
            _msci = fetch_psx_msci()
            if _msci.get('by_ticker') or _msci.get('added') or _msci.get('deleted') or _msci.get('constituents'):
                _msci['last_fetch_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
                data['psx_msci'] = _msci
            else:
                data['psx_msci'] = _prev_msci
    except _MsciShelved:
        log('  [Wave PSX-R MSCI] shelved (stale 2016 SCS source) -> psx_msci empty')
    except Exception as e:
        log(f'  [Wave PSX-R MSCI] overlay error ({e}) -> skipped')
        data['psx_msci'] = {}

    # Wave P breadth/leaders (TV-derived; ISOLATED POST -> cannot affect the main universe scan)
    try:
        data['psx_market'] = fetch_psx_market_stats()
        if not data['psx_market']:
            data['psx_market'] = EXISTING.get('psx_market', {})
    except Exception as e:
        log(f'  [Wave P breadth] error ({e}) -> skipped')
        data['psx_market'] = EXISTING.get('psx_market', {})

    _spy6, _spy_px = _spy_6mo_return()
    _prev_us = {r['ticker']: r['streams'].get('rev_est') for r in EXISTING.get('tce_us', [])
                if isinstance(r.get('streams'), dict)}
    _etf_stocks = (EXISTING.get('etf_overlap', {}) or {}).get('stocks', [])
    _us_pool = merge_tce_pool(data['us_candidates'], _etf_stocks)
    _n_etf = sum(1 for c in _us_pool if c.get('src') == 'etf')
    log(f'  US TCE pool: {len(_us_pool) - _n_etf} screen + {_n_etf} ETF-consensus = {len(_us_pool)}')
    # Wave O L1: attach TV FactSet analyst rows (US counterpart to D2). Best-effort.
    # v1.52 (P2b): fetch over the UNION of the TCE pool AND the explosive survivors. Previously
    # only the pool got analyst rows, so the explosive forward leg (_forward_boost) read a missing
    # c['analyst_row'] and returned F1/FR=None on EVERY explosive record. One POST, no extra cost.
    _us_analyst = fetch_us_analyst_block(
        [c.get('ticker') for c in _us_pool] + [c.get('ticker') for c in us_all_survivors])
    for _c in _us_pool:
        _ar = _us_analyst.get(_c.get('ticker'))
        _c['analyst'] = _ar
        if not _c.get('sector') and isinstance(_ar, dict) and _ar.get('sector'):
            _c['sector'] = _ar['sector']   # v1.89.0: ETF-consensus large-caps (AMAT/LRCX/AVGO/MU/NVDA/... 20 names) enter merge_tce_pool with sector='' (the ETF-overlap carries ticker+name+weight only); inherit the TV sector the analyst POST already returns so tce_us + the Results vs-sector read are populated. Never fabricated (no analyst sector -> stays blank); display-only -> respects the freeze.
    _prev_fwd_us = {r['ticker']: r['streams'].get('fwd_eps') for r in EXISTING.get('tce_us', [])
                    if isinstance(r.get('streams'), dict) and r['streams'].get('fwd_eps') is not None}
    # P2b: explosive survivors read c['analyst_row'] + c['prev_fwd_eps'] in _forward_boost.
    # Additive/safe: a miss -> None -> F1/FR=None (prior behaviour); forward leg never blocks.
    for _c in us_all_survivors:
        _c['analyst_row']  = _us_analyst.get(_c.get('ticker'))
        _c['prev_fwd_eps'] = _prev_fwd_us.get(_c.get('ticker'))
    try:
        data['tce_us'] = run_tce(_us_pool, market='us',
                                  max_count=len(_us_pool), spy_6mo_ret=_spy6,
                                  prev_rev=_prev_us, prev_fwd=_prev_fwd_us)
    except Exception as e:
        log(f'US TCE crashed: {e}')
        data['meta']['errors'].append(f'us_tce: {e}')
        data['tce_us'] = EXISTING.get('tce_us', [])

    try:
        _prev_psx = {r['ticker']: r['streams'].get('rev_est') for r in EXISTING.get('tce_psx', [])
                     if isinstance(r.get('streams'), dict)}
        _prev_fwd = {r['ticker']: r['streams'].get('fwd_eps') for r in EXISTING.get('tce_psx', [])
                     if isinstance(r.get('streams'), dict) and r['streams'].get('fwd_eps') is not None}
        data['tce_psx'] = run_tce(data['psx_candidates'], market='psx',
                                  max_count=max(len(data['psx_candidates']), 10),
                                  spy_6mo_ret=_spy6, prev_rev=_prev_psx, prev_fwd=_prev_fwd)
    except Exception as e:
        log(f'PSX TCE crashed: {e}')
        data['meta']['errors'].append(f'psx_tce: {e}')
        data['tce_psx'] = EXISTING.get('tce_psx', [])

    # Forward-validation: log this run's TCE-pool picks (HIGH/WATCH/IGNORE) + entry price + benchmark;
    # re-price off-pool open picks so they mature on a live price; track forward return AND alpha over time.
    try:
        _today = dt.date.today().isoformat()
        _rows = []; _pool = set()
        # v1.37: the PSX ledger price must share one basis with the screen + _reprice_psx (both TV
        # pakistan/scan close). streams['price'] for PSX is the TCE's yahoo:.KA momentum-fetch snapshot
        # (a different vendor, systematically ~0-10% off), so for PSX rows prefer the candidate's
        # tv_scan price -> entry and maturity re-price land on the same source (no spurious offset).
        _psx_tv = {c['ticker']: c.get('price') for c in data.get('psx_candidates', []) if c.get('price')}
        for _mkt, _key in (('us', 'tce_us'), ('psx', 'tce_psx')):
            for r in data.get(_key, []):
                pr = r.get('streams', {}).get('price') if isinstance(r.get('streams'), dict) else None
                if _mkt == 'psx':
                    pr = _psx_tv.get(r['ticker'], pr)   # screen tv_scan price for PSX (US keeps Yahoo)
                if r.get('tier') in ('HIGH', 'WATCH', 'IGNORE') and pr:
                    _rows.append({'ticker': r['ticker'], 'tier': r['tier'], 'market': _mkt, 'price': pr})
                    _pool.add(r['ticker'])
        # Gap-1: live-reprice OPEN predictions whose ticker isn't in this run's pool (else they freeze stale at maturity)
        _pp = (EXISTING.get('tce_predictions') or {}).get('predictions', [])
        _open_us  = sorted({p['ticker'] for p in _pp if not p.get('resolved')
                            and p.get('market', 'us') == 'us' and p.get('days_open', 0) < PRED_HORIZON_DAYS
                            and p['ticker'] not in _pool})
        _open_psx = sorted({p['ticker'] for p in _pp if not p.get('resolved')
                            and p.get('market') == 'psx' and p.get('days_open', 0) < PRED_HORIZON_DAYS
                            and p['ticker'] not in _pool})
        _extra = {}
        _extra.update(_reprice_us(_open_us))
        _extra.update(_reprice_psx(_open_psx))
        # Gap-2: benchmark levels for alpha — SPY (already fetched for the guardrail) + KSE-100 (PSX macros)
        _bench = {'us': _spy_px, 'psx': safe_get(data, 'macros', 'psx', 'kse100')}
        data['tce_predictions'] = update_tce_predictions(EXISTING.get('tce_predictions'), _today, _rows,
                                                         extra_prices=_extra, bench=_bench)
        _s = data['tce_predictions']['summary']
        if _s.get('psx_rebaselined'):
            log(f"  ↻ PSX re-baseline (L3 follow-up): reset {_s['psx_rebaselined']} open PSX prediction(s) "
                f"from the stale dps.psx basis to the correct TV basis (one-time)")
        log(f"TCE predictions: {_s['total_logged']} logged, {_s['open']} open "
            f"(re-priced {len(_extra)}/{len(_open_us) + len(_open_psx)} off-pool); "
            f"HIGH matured={_s['HIGH']['matured']} hit={_s['HIGH']['hit_rate']} alpha={_s['HIGH']['avg_alpha_pct']} lift={_s['HIGH']['lift_vs_ignore']}; "
            f"WATCH matured={_s['WATCH']['matured']} hit={_s['WATCH']['hit_rate']}; "
            f"IGNORE matured={_s['IGNORE']['matured']} hit={_s['IGNORE']['hit_rate']}")
    except Exception as e:
        log(f'TCE prediction logger failed: {e}')
        data['tce_predictions'] = EXISTING.get('tce_predictions', {})

    try:
        data['explosive_us'] = run_explosive(us_all_survivors, market='us')
        data['explosive_stmt_cache'] = _EXPLOSIVE_CACHE_OUT   # v1.112.1: persist the US statement cache in data.json (committed -> survives to next run)
    except Exception as e:
        log(f'US explosive crashed: {e}')
        data['meta']['errors'].append(f'us_explosive: {e}')
        data['explosive_us'] = EXISTING.get('explosive_us', [])
        data['explosive_stmt_cache'] = EXISTING.get('explosive_stmt_cache', {})   # v1.112.1: carry the cache forward on crash (don't wipe it)

    try:
        data['explosive_psx'] = run_explosive(data['psx_candidates'], market='psx')
    except Exception as e:
        log(f'PSX explosive crashed: {e}')
        data['meta']['errors'].append(f'psx_explosive: {e}')
        data['explosive_psx'] = EXISTING.get('explosive_psx', [])

    try:
        data['rate_path'] = fetch_rate_path()
    except Exception as e:
        log(f'Rate path crashed: {e}')
        data['rate_path'] = EXISTING.get('rate_path', [])

    # v1.11: COT index/commodity futures for US sector gating (SP500/Crude/10yr/VIX/NASDAQ)
    try:
        data['cot_futures'] = fetch_cot_futures()
    except Exception as e:
        log(f'COT futures crashed: {e}')
        data['meta']['errors'].append(f'cot_futures: {e}')
        data['cot_futures'] = EXISTING.get('cot_futures', {})

    # Wave C: US recession watch (FRED recession series + ForexFactory weekly calendar)
    try:
        data['recession'] = fetch_recession()
    except Exception as e:
        log(f'Recession watch crashed: {e}')
        data['meta']['errors'].append(f'recession: {e}')
        data['recession'] = EXISTING.get('recession', {})

    # v1.11: Zacks #1/#2 grouped by GICS sector (fixed S&P universe + this run's survivors)
    # Cadence gate: Zacks ranks update ~weekly, but the scrape costs ~17 min. Skip it if the
    # last scrape is <7 days old and carry forward last-good (sector breadth is stable
    # intra-week); otherwise scrape and stamp the date.
    _prev_z = EXISTING.get('zacks_sectors', {}) or {}
    _prev_scraped = _prev_z.get('_scraped_utc') if isinstance(_prev_z, dict) else None
    _z_age = None
    _z_fresh = False
    if _prev_scraped:
        try:
            _z_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_prev_scraped).replace('Z', ''))).days
            _z_fresh = _z_age < 7
        except Exception:
            _z_fresh = False
    try:
        # P7 bootstrap: only honor the weekly skip when a per-ticker rank map ALREADY exists to
        # carry forward. On the first v1.57+ run EXISTING has no zacks_ranks (prior versions
        # discarded it), so force one scrape now to populate it — otherwise the ⚡Z chips can't
        # appear until the 7-day window happens to open. After this, the carry-forward works.
        _have_ranks = bool(EXISTING.get('zacks_ranks'))
        if _z_fresh and _have_ranks:
            log(f'  → Zacks scrape skipped (last scrape {_z_age}d ago, <7d) — carrying forward last-good')
            data['zacks_sectors'] = _prev_z
            data['zacks_ranks'] = EXISTING.get('zacks_ranks', {}) or {}
        else:
            if _z_fresh and not _have_ranks:
                log('  → Zacks per-ticker rank map absent (first v1.57 run) — forcing a one-time scrape to populate zacks_ranks (P7 bootstrap)')
            data['zacks_sectors'], _zranks = fetch_zacks_sectors(us_all_survivors)
            # P7: persist the per-ticker Zacks rank map, MERGING over the prior map so a name
            # not scraped this run keeps its last-good rank (the scrape is weekly / partial).
            data['zacks_ranks'] = {**(EXISTING.get('zacks_ranks') or {}), **(_zranks or {})}
            # Wave T3 sector rotation: change in each sector's Zacks #1/#2 breadth vs the prior
            # scrape (None when no prior). Computed only on a fresh scrape; on skip days the
            # carried-forward _prev_z already holds the last pct_top_chg.
            for _sec, _v in data['zacks_sectors'].items():
                if isinstance(_v, dict) and 'pct_top' in _v:
                    _pp = _prev_z.get(_sec) if isinstance(_prev_z, dict) else None
                    _prevpt = _pp.get('pct_top') if isinstance(_pp, dict) else None
                    _v['pct_top_chg'] = round(_v['pct_top'] - _prevpt, 1) if isinstance(_prevpt, (int, float)) else None
            data['zacks_sectors']['_scraped_utc'] = dt.datetime.utcnow().isoformat() + 'Z'
    except Exception as e:
        log(f'Zacks sectors crashed: {e}')
        data['meta']['errors'].append(f'zacks_sectors: {e}')
        data['zacks_sectors'] = EXISTING.get('zacks_sectors', {})
        data['zacks_ranks'] = EXISTING.get('zacks_ranks', {}) or {}

    # Phase 0-A: World LEI — 9-country OECD leading indicators via FRED
    try:
        data['world_lei'] = fetch_world_lei()
        if not data['world_lei']:
            data['world_lei'] = EXISTING.get('world_lei', {}) or {}
    except Exception as _e:
        log(f'  [World LEI] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['world_lei'] = EXISTING.get('world_lei', {}) or {}

    # Phase 0-B: US Diffusion — 15-indicator economic diffusion index (PURE, no network)
    try:
        data['us_diffusion'] = compute_us_diffusion(data.get('macros', {}).get('us', {}))
        if not data['us_diffusion']:
            data['us_diffusion'] = EXISTING.get('us_diffusion', {}) or {}
    except Exception as _e:
        log(f'  [US Diffusion] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['us_diffusion'] = EXISTING.get('us_diffusion', {}) or {}

    # Phase 0-C: Country RS — 9-country equity momentum + USD-adjusted return ranking
    try:
        data['country_rs'] = fetch_country_rs()
        if not data['country_rs']:
            data['country_rs'] = EXISTING.get('country_rs', []) or []
    except Exception as _e:
        log(f'  [Country RS] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['country_rs'] = EXISTING.get('country_rs', []) or []

    # Phase 0-D: Sector Booming — reuses already-fetched zacks_sectors + cot_futures (PURE)
    try:
        _met_cot_arg = (data.get('macros') or {}).get('metals') or {}
        data['sector_booming'] = compute_sector_booming(
            data.get('zacks_sectors', {}),
            data.get('cot_futures', {}),
            metals_data=_met_cot_arg
        )
        if not data['sector_booming']:
            data['sector_booming'] = EXISTING.get('sector_booming', []) or []
    except Exception as _e:
        log(f'  [Sector Booming] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['sector_booming'] = EXISTING.get('sector_booming', []) or []
    # Wave T enrichment (v1.120.0): annotate each sector with score_delta + score_trend.
    # Compares today's score to EXISTING['sector_booming'] prior-run scores.
    # From run 2 onwards every sector carries a WoW direction. Graceful: first run
    # or missing prior → delta=None/trend=None (never fabricated, index falls back to '—').
    try:
        _prior_sb = {
            r['sector']: r['score']
            for r in (EXISTING.get('sector_booming') or [])
            if isinstance(r, dict) and r.get('sector') and r.get('score') is not None
        }
        _trended = 0
        for _r in data.get('sector_booming', []):
            if not isinstance(_r, dict):
                continue
            _sec = _r.get('sector')
            _now = _r.get('score')
            _prev = _prior_sb.get(_sec)
            if _now is not None and _prev is not None:
                _delta = round(_now - _prev, 1)
                _r['score_delta'] = _delta
                _r['score_trend'] = (
                    'rising'  if _delta >=  1.0 else
                    'falling' if _delta <= -1.0 else 'flat'
                )
                _trended += 1
            else:
                _r['score_delta'] = None
                _r['score_trend'] = None
        if _trended:
            log(f'  [Sector Booming delta] {_trended} sectors trended '
                f'(rising={sum(1 for r in data["sector_booming"] if r.get("score_trend")=="rising")}'
                f' falling={sum(1 for r in data["sector_booming"] if r.get("score_trend")=="falling")}'
                f' flat={sum(1 for r in data["sector_booming"] if r.get("score_trend")=="flat")})')
        else:
            log('  [Sector Booming delta] no prior run scores — delta pending next run')
    except Exception as _e:
        log(f'  [Sector Booming delta] skipped: {type(_e).__name__}: {str(_e)[:50]}')

    # Phase 2 (World ETF Engine): global sector theme from country_rs — no new network call
    try:
        data['global_theme'] = compute_global_sector_theme(data.get('country_rs', []))
        if not data['global_theme']:
            data['global_theme'] = EXISTING.get('global_theme', []) or []
    except Exception as _e:
        log(f'  [Global Theme] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['global_theme'] = EXISTING.get('global_theme', []) or []

    # Phase 3 (World ETF Engine): resolve top signals to buyable UCITS ETFs
    try:
        data['etf_recommendations'] = build_etf_recommendations(
            data.get('country_rs', []),
            data.get('sector_booming', []),
            data.get('global_theme', []),
        )
    except Exception as _e:
        log(f'  [ETF Recommendations] crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['etf_recommendations'] = EXISTING.get('etf_recommendations', []) or []

    data['etf_momentum_watch'] = _MOMENTUM_WATCH     # Momentum-Watch: 55 ETFs up >=35% YTD (threshold lowered from 40%)
    data['etf_hydrogen_watch'] = _HYDROGEN_WATCH      # Hydrogen Economy Thematic Watch (4 funds, confirmed ISINs)
    data['etf_metals_etc_watch'] = _METALS_ETC_WATCH  # Physical Gold/Silver ETCs (3 funds)
    # v1.137.0: Pakistan UCITS proxy as its own top-level field, sourced from the existing
    # catalog entry (zero new data) -- for display on Tab 2 (Pakistan) and Tab 7 (Allocation
    # Zone), NOT Tab 16 (removed from there per owner instruction, that removal stands).
    _pak_cat = _ETF_CATALOG.get('Equity Pakistan') or []
    data['etf_pakistan_proxy'] = dict(_pak_cat[0]) if _pak_cat else None

    # Phase 6 (World ETF Engine) — enrich each recommendation with a live price via the
    # proven ISIN-filter resolver (uk/scan → USD, germany/scan fallback → EUR).
    # v1.132.0: extended beyond etf_recommendations to ALSO price the Hydrogen Watch
    # (4 funds) and Metals ETC Watch (3 funds) — same resolver, same cost class (7 more
    # ISINs, 1-2 TV scan requests each).
    # v1.137.0: Momentum-Watch (55 funds) is NOW ALSO included, reversing the v1.132.0
    # exclusion. That exclusion was about avoiding an unnecessary LIVE PRICE display for a
    # YTD-focused list -- but ticker and price come from the SAME resolver call (there is no
    # cheaper way to get one without the other), and the owner explicitly asked for a real,
    # verified ticker on every ETF section of the dashboard rather than 55 more hardcoded
    # strings to trust blindly. Live price is a side effect of getting the ticker honestly;
    # the Momentum-Watch table still leads with YTD, price/ticker are a secondary field.
    _n_priced = 0
    for _rec in (data.get('etf_recommendations') or []):
        _isin = (_rec.get('fund') or {}).get('isin')
        if not _isin:
            continue
        try:
            _lp = resolve_etf_live_price(_isin)
            if _lp:
                _rec['fund']['live_price'] = _lp['close']
                _rec['fund']['live_sym']   = _lp['sym']
                _rec['fund']['live_ccy']   = _lp['currency']
                _rec['fund']['live_exch']  = _lp['exchange']
                _n_priced += 1
        except Exception:
            pass
    for _watch_list in (data.get('etf_hydrogen_watch') or []), (data.get('etf_metals_etc_watch') or []), (data.get('etf_momentum_watch') or []), ([data['etf_pakistan_proxy']] if data.get('etf_pakistan_proxy') else []):
        for _w in _watch_list:
            _isin = _w.get('isin')
            if not _isin:
                continue
            try:
                _lp = resolve_etf_live_price(_isin)
                if _lp:
                    _w['live_price'] = _lp['close']
                    _w['live_sym']   = _lp['sym']
                    _w['live_ccy']   = _lp['currency']
                    _w['live_exch']  = _lp['exchange']
                    _n_priced += 1
            except Exception:
                pass
    if _n_priced:
        log(f'  [ETF live prices] {_n_priced} fund(s) priced via isin-filter resolver (recs + hydrogen + metals + momentum watch)')

    # P7: join the per-ticker Zacks Rank onto the US Explosive records (US only — Zacks
    # has no PSX coverage). The dashboard renders a ⚡Z chip for rank #1/#2. Last-good
    # carry-forward in data['zacks_ranks'] means a weekly-skipped run still labels names.
    _zr = data.get('zacks_ranks') or {}
    for _r in data.get('explosive_us', []):
        if isinstance(_r, dict):
            _r['zacks_rank'] = _zr.get(_r.get('ticker'))

    # Smart-Money ETF Holdings Overlap (Part D) — weekly cadence (holdings barely move).
    _zacks_tops = []
    for _sec, _v in (data.get('zacks_sectors') or {}).items():
        if isinstance(_v, dict):
            _zacks_tops += _v.get('top_tickers', [])
    _prev_etf = EXISTING.get('etf_overlap', {}) or {}
    _etf_fresh = False; _etf_age = None
    _es = _prev_etf.get('_scraped_utc') if isinstance(_prev_etf, dict) else None
    if _es:
        try:
            _etf_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(str(_es).replace('Z',''))).days
            # fresh only if young AND produced by the current scanner version — so any ETF-code
            # fix (new version) forces a one-time re-run instead of carrying forward stale output
            _etf_fresh = _etf_age < 7 and _prev_etf.get('_etf_code_ver') == _ETF_OVERLAP_CODE_VER  # v1.112.0 F4: decouple from SCAN_VERSION
        except Exception:
            _etf_fresh = False
    try:
        if _etf_fresh and _prev_etf.get('stocks'):
            log(f'  → ETF holdings overlap skipped (last scrape {_etf_age}d ago, <7d) — carrying forward last-good')
            data['etf_overlap'] = _prev_etf
        else:
            _r12 = [{'etf': t, 'zacks_rank': 1} for t in TOP_ETFS]
            _hmap = {}; _src = []
            for _e in _r12:
                _tk = _e['etf']
                _hmap[_tk] = fetch_etf_holdings(_tk)
                _nm, _ytd, _y1 = ETF_META.get(_tk, (_tk, None, None))
                _m = fetch_etf_meta(_tk)
                _src.append({'ticker': _tk, 'name': _nm, 'ytd': _ytd, 'y1': _y1,
                             'y3': _m['y3'], 'expense': _m['expense']})
                time.sleep(0.5)
            _stocks = build_etf_overlap(_r12, _hmap, _zacks_tops)
            _got = sum(1 for v in _hmap.values() if v)
            data['etf_overlap'] = {
                '_scraped_utc': dt.datetime.utcnow().isoformat() + 'Z',
                '_scan_version': SCAN_VERSION,
                '_etf_code_ver': _ETF_OVERLAP_CODE_VER,
                'etfs_scanned': len(TOP_ETFS),
                'etfs_with_holdings': _got,
                'source_etfs': _src,
                'stocks': _stocks,
            }
            log(f'  ETF overlap: {_got}/{len(TOP_ETFS)} ETFs returned holdings -> top {len(_stocks)} consensus stocks')
    except Exception as e:
        log(f'ETF overlap crashed: {e}')
        data['meta']['errors'].append(f'etf_overlap: {e}')
        data['etf_overlap'] = EXISTING.get('etf_overlap', {})

    # Wave Z: Institutional fund consensus (double-confirmed smart money) — 7-day cache
    try:
        _prev_ic = EXISTING.get('inst_consensus', {})
        _ic_fresh = False
        try:
            _ic_age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(
                _prev_ic.get('_scraped_utc','2000-01-01T00:00:00').replace('Z',''))
            ).total_seconds() / 86400
            _ic_fresh = _ic_age < 7 and bool(_prev_ic.get('stocks'))
        except Exception:
            pass
        if _ic_fresh:
            log(f'  → Wave Z inst_consensus skipped (last scrape {_ic_age:.0f}d ago, <7d) — carrying forward last-good')
            data['inst_consensus'] = _prev_ic
        else:
            _fund_map = {}
            for _ft in TOP_INST_FUNDS:
                _h = fetch_fund_holdings(_ft)
                if _h:
                    _fund_map[_ft] = _h
                    log(f'  [Wave Z] {_ft}: {len(_h)} holdings')
            _ic_stocks = compute_inst_consensus(data.get('etf_overlap', {}), _fund_map)
            data['inst_consensus'] = {
                '_scraped_utc': dt.datetime.utcnow().isoformat() + 'Z',
                'funds_fetched': len(_fund_map),
                'stocks': _ic_stocks,
            }
    except Exception as _e:
        log(f'  [Wave Z] inst_consensus crashed: {type(_e).__name__}: {str(_e)[:60]}')
        data['inst_consensus'] = EXISTING.get('inst_consensus', {})

    data['meta']['warnings'] = list(WARNINGS)

    # Carry IM3 forward from the last good data.json. The scanner doesn't SCORE IM3
    # (im3_score.py does, as a separate workflow step), but it rebuilds explosive_us/tce_us
    # from scratch each run with no 'im3' field — so it must re-attach two things or the
    # dashboard's IM3 panel blanks out on any run where the IM3 step is skipped:
    #   1. im3_explosive_tickers (the list) — so the workflow's change-detection has a real
    #      previous list to compare against and can skip re-scoring on stable days.
    #   2. the per-record 'im3' score dicts, keyed by ticker — so a skipped re-score keeps
    #      the prior scores. When names DO change, the IM3 step re-runs and overwrites these.
    if 'im3_explosive_tickers' not in data:
        data['im3_explosive_tickers'] = EXISTING.get('im3_explosive_tickers', [])

    # v1.49.0: carry IM3 forward per-MARKET so PSX scores survive a scanner-only run too.
    # (Pre-1.49 this looped US keys ONLY -> explosive_psx/tce_psx/psx_candidates were rebuilt
    #  with no 'im3' and the dashboard PSX IM3 column blanked to "Pending next scan" on any run
    #  where the separate im3_score.py step was skipped — the recurring PSX-blank bug.)
    # Grouped by market so a US/PSX ticker collision can never cross-attach a score.
    # v1.58.2: VERSION-AWARE carry-forward. A carried im3 dict is re-attached ONLY when its
    # 'ver' matches the CURRENT im3_score.py IM3_VERSION, so a record can never keep a
    # stale-engine grade. Background: a name that was deep-scored once and then drops out of
    # the daily.yml re-score set (explosive / financial / TCE-HIGH) is carried forward every
    # run forever — so a few NOT-EXPLOSIVE rows were still showing an old 2.9.x grade while
    # every other NOT-EXPLOSIVE row correctly showed "Pending". A stale-version score is now
    # DROPPED to None: if the name is still in the re-score set, the daily.yml self-heal
    # (missing_im3) re-scores it fresh this same run; if it isn't, it shows an honest
    # "Pending" instead of an old-engine number — consistent with its peers.
    # The current scorer version is parsed from im3_score.py (the same file daily.yml locates
    # it in) with a CLEAN regex — NOT daily.yml's `.strip('"\'')`, which leaves the trailing
    # inline comment attached; replicating that would mismatch EVERY ver and blank the whole
    # board (the v1.49.0 PSX-blank regression). If the version can't be read (file absent / no
    # match) _cur_im3_ver is None and EVERY score is carried = pre-1.58.2 behaviour, so this
    # guard can never itself blank a score.
    import re as _re_im3
    _cur_im3_ver = None
    try:
        with open('im3_score.py') as _vf:
            for _vl in _vf:
                _vm = _re_im3.match(r'\s*IM3_VERSION\s*=\s*[\'"]([^\'"]+)[\'"]', _vl)
                if _vm:
                    _cur_im3_ver = _vm.group(1); break
    except Exception:
        _cur_im3_ver = None

    _carried = 0; _dropped_stale = 0
    for _grp in (('explosive_us', 'tce_us'),
                 ('explosive_psx', 'tce_psx', 'psx_candidates')):
        _im3_prev = {}
        for _key in _grp:
            for _r in EXISTING.get(_key, []):
                if isinstance(_r, dict) and _r.get('im3') is not None and _r.get('ticker'):
                    _pv = _r['im3'].get('ver') if isinstance(_r['im3'], dict) else None
                    if _cur_im3_ver is not None and _pv != _cur_im3_ver:
                        _dropped_stale += 1
                        continue  # stale-engine grade: drop -> re-score (self-heal) or Pending
                    _im3_prev[_r['ticker']] = _r['im3']
        if not _im3_prev:
            continue
        for _key in _grp:
            for _r in data.get(_key, []):
                if isinstance(_r, dict) and _r.get('im3') is None and _r.get('ticker') in _im3_prev:
                    _r['im3'] = _im3_prev[_r['ticker']]; _carried += 1
    if _carried:
        log(f'  Carried forward {_carried} last-good IM3 score(s) onto rebuilt records')
    if _dropped_stale:
        log(f'  Dropped {_dropped_stale} stale-version IM3 score(s) (ver != {_cur_im3_ver}) -> re-score/Pending')

    def _json_safe(o):
        # NaN / Infinity are NOT valid JSON; the browser's JSON.parse rejects them.
        # Convert to None (null) recursively so data.json is spec-valid.
        if isinstance(o, float):
            return None if (math.isnan(o) or math.isinf(o)) else o
        if isinstance(o, dict):
            return {k: _json_safe(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_json_safe(v) for v in o]
        return o

    # Wave T: append today's snapshot to the rolling daily history store (inside data.json).
    append_history(data, EXISTING)
    # Wave T: per-item shortlist performance tracker (first-seen date+price -> % since, per tab + sectors).
    track_shortlists(data, EXISTING)

    try:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(_json_safe(data), f, indent=2, default=str, allow_nan=False)
        log(f'data.json written ({OUTPUT_PATH.stat().st_size} bytes)')
    except Exception as e:
        log(f'Failed to write data.json: {e}')
        sys.exit(1)

    log('=' * 60)
    log('Scanner completed')
    log(f'  Hard errors: {len(data["meta"]["errors"])}')
    log(f'  Warnings (degraded data): {len(data["meta"]["warnings"])}')
    for w in data['meta']['warnings']:
        log(f'      - {w}')
    if _SWALLOWED:                                   # v1.112.0 (F6): surface swallowed exceptions
        log(f'  Swallowed (silent) exceptions: {dict(sorted(_SWALLOWED.items()))}')
        data['meta']['swallowed'] = dict(_SWALLOWED)
    log(f'  US macros: '
        f'{len([k for k in data["macros"]["us"] if not k.endswith(("_date","_source"))])}')
    log(f'  PSX macros: '
        f'{len([k for k in data["macros"]["psx"] if not k.endswith(("_date","_source"))])}')
    log(f'  KSE-100: {data["macros"]["psx"].get("kse100")} '
        f'({data["macros"]["psx"].get("kse100_source")}, '
        f'as of {data["macros"]["psx"].get("kse100_date")})')
    log(f'  WTI/Brent: {data["macros"]["us"].get("wti")} / '
        f'{data["macros"]["us"].get("brent")} '
        f'({data["macros"]["us"].get("wti_source")}, '
        f'as of {data["macros"]["us"].get("wti_date")})')
    log(f'  US candidates: {len(data["us_candidates"])}')
    log(f'  PSX candidates: {len(data["psx_candidates"])}')
    log(f'  US TCE HIGH: '
        f'{sum(1 for r in data["tce_us"] if r.get("tier") == "HIGH")}')
    log(f'  PSX TCE HIGH: '
        f'{sum(1 for r in data["tce_psx"] if r.get("tier") == "HIGH")}')
    log(f'  Recession: {data.get("recession",{}).get("risk","—")} '
        f'(score {data.get("recession",{}).get("score","—")}, '
        f'{len(data.get("recession",{}).get("calendar",[]))} cal events)')
    log('=' * 60)


if __name__ == '__main__':
    main()
