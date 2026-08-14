# CHANGELOG ADDITION — v1.347.0 → v1.430.0 (2026-08-14)

PASTE INSTRUCTIONS (purely additive — the existing file is not modified anywhere else):
Open the repo's CHANGELOG.md in the GitHub web editor. Find the line containing only `---`
(line 11, directly above `## 1.345.0`). Paste everything BELOW the marker line of this file
between that `---` line and the `## 1.345.0` heading. Save/commit. Nothing in the existing
file is deleted or changed; the new entries slot in at the top in the file's own
newest-first order, exactly per the v1.346.0 convention.

=================== PASTE EVERYTHING BELOW THIS LINE ===================

## Reconstruction note (2026-08-14)

Entries v1.347.0 - v1.430.0 below were appended in one owner-approved sweep on 2026-08-14: the per-version relocation convention had lapsed after v1.346.0, and each version's full docstring was overwritten in scanner.py by the next bump. v1.418-430 are taken from the audited Dashboard_Changelog_2026-08-14; v1.387-417 from the audited Dashboard_Changelog_2026-08-10 (v1.387-396 grouped, as documented there); v1.347-386 are reconstructed verbatim-where-possible from the archived session transcripts' delivered docstrings and may be truncated relative to the lost originals. Convention resumes: every new version adds its full rationale here at the top.

## 1.430.0

ECON ACTUALS FROM FRED (investigation closed with live proof: the faireconomy weekly export was fetched directly at 11:45 ET, 3h after the CPI release, and its schema carries NO actual field at all -- the old docstring was right, and the v1.429 assumption that actuals appear in-feed was wrong; MT tools with actual values read the FF site itself, which rate-limits exports to 2/5min since Aug-2024). FIX within proven infrastructure: _enrich_econ_actuals() computes actuals from FRED (existing key, existing library) for RELEASED events via a verified-id map only -- CPIAUCSL / CPILFESL (m/m + y/y), ICSA (claims -> 202K format), RSAFS (retail m/m), UMCSENT (sentiment level) -- formatted to match the feed's own strings, gated on release-time passed + observation freshness (45d monthly / 10d weekly). Unverified ids (PPI, core retail, UoM expectations) stay honestly blank rather than guessed. Enrichment mutates the calendar rows in place (the table column fills) then feeds merge_econ_announced (the 14-day log fills). Max ~5 tiny FRED calls/run, usually 0-2. PRIOR: see CHANGELOG.md.

## 1.429.0

ECON ANNOUNCED. Calendar filter carries 'actual'; _econ_num parser; merge_econ_announced persisted 14-day log (dedup title+date, surprise above/below/inline), wired at the recession call site (first in-function wire failed -- no 'data' in scope -- caught pre-delivery).

## 1.428.0

Trend Ladder frontier fix: moat absent from data at frontier-build time -> wanted-list reads data['moat'] OR EXISTING['moat']; ma_lines store 290 -> 410; moat trend coverage 211/317 = honest US-listed ceiling (rest are non-US ADR lines, honestly unstamped).

## 1.427.0

ma_lines AMEX third exchange fallback + 5-day miss-cache (store had grown +47/80; 33 silent failures were being retried forever -- failures now recorded once, not re-burned).

## 1.426.0

moat trend stamps ran BEFORE build_moat_universe's rebuild and were silently wiped (0/317) -> stamp_trend_moat_only zero-fetch re-stamp added AFTER the rebuild (live 0 -> 25). Stamp order is part of build correctness (D-123).

## 1.425.0

Trend Ladder noun param; METALS classified via proven COMEX/NYMEX/TVC symbols (6 GETs); HOLDINGS via row.sym (~9 GETs).

## 1.424.0

per-zone 'tech' sentence composed from the actual numbers (all six zones unit-tested with $ and %).

## 1.423.0

live audit proved TV batch /scan serves NULL for EMA10/EMA20/SMA100 on all 1,966 rows (alignment verified) -> ma_lines 5-day per-ticker store via the proven per-symbol GET, budget 80/run (D-122: never retry the broken path harder).

## 1.422.0

TREND LADDER. EMA10/EMA20/SMA100 added to _US_TV_COLS; _TL_TEXT six zones (buy+sell consequences; validation caught a missing SELL word -- fixed); _trend_ladder() boundaries; stamp_trend_ladder post-pass (explosive/recommended/moat via foundation); APD quote extended. Display-only, never scored (D-121).

## 1.421.0

APD permanently added to the TipRanks display-only pool.

## 1.420.0

NetBenefits Zacks forward layer deep-parsed from the repo report txt (11-05 earnings, Q 3.60 / most-acc 3.62 ESP+, FY26 13.43 / FY27 14.43, 9/9 revisions UP, +2.27/+2.65 trend) + 1,242-char plain_summary.

## 1.419.0

NetBenefits withholding relabelled (~30% NRA on dividends, arithmetic proof; NOT salary tax); gross+net dividend projections (net 4,216.58/yr; cumulative net 10,978.23).

## 1.418.0

NETBENEFITS. Six Fidelity statements (repo) reconciled into _NB_FACTS (grants/vesting/dividends/taxes/PSU outcomes; position 832 sh, basis 236,877.70); live APD via fetch_tv_symbol_quote('NYSE:APD'), fail-open to Zacks report px; dividend engine (7.24 x 832 = 6,023.68 = statement EAI, asserted in code).

## 1.417.0

STATEMENTS RECORDED, NOT REFETCHED: persisted sec_stmt_store (cfo_cpat + qrows, 45d quarterly-aligned); Multibagger 30 -> 0 SEC pulls with digit-identical scoring (21/16/2.848 confirmed in the owner's runner log); M2 Signal-T rows recorded (D-118).

## 1.416.0

REGRESSION-SAFE CARRY (supersedes staged v1.415): owner's runner log showed the SEC-filings stage stamps consumers (multibagger gate, explosive confirmation, sentinel); consumers extracted to sec_filings_consumers() (free-variable-checked) and run on BOTH fresh and carried paths; sec_meta added to the carry. Validated to exact reproduction (6/6 sentinel flags) (D-117).

## 1.415.0

SEC Form4/8-K crawl moved to a 20h TTL (sec_filings_as_of). (Superseded by v1.416 before deploy.)

## 1.414.0

EFFICIENCY: deep-holdings gate carries again. KSTR (UCITS) and XBI (top-25-only) removed from _DEEP_TARGETS -- both could never satisfy the gate, forcing a full 30-ETF refetch every run. EDGAR holdings now ~once per 5 days (proven in owner log) (D-119).

## 1.413.0

KSTR corrected to its UCITS reality (IE00BKPJY434, never in EDGAR; TV/ETF-Universe checked and ruled out); justETF with_weights=True branch serves KSTR/AINF/STOR; PHPM (physical metal) skips honestly. Live: exposure 60.5% coverage, TSM 8.29% top (D-116).

## 1.412.0

SERIES-DIRECT fetch for EWY/EWT by verified S-numbers (atom -> accession -> primary_doc.xml; ISIN -> local codes; ADR aliases 2330 -> TSM, 005930 -> Samsung); TSM overlap now flags via ITWN too.

## 1.411.0

N-PORT parse depth 150 (position-trap-tested with a plant at position 120).

## 1.410.0

EXISTING-weights fallback (build-order lag) + evidence instrumentation on the twin failing scans.

## 1.409.0

dropped-wire fix ('exposure' key computed but never written -- the edit script never saved; caught by payload audit, locked as D-120) + registrant-CIK routing (VanEck 1137360, iShares Inc 930667, KraneShares 1547576, all verified from SEC URLs).

## 1.408.0

THE FULL EDGAR-INTELLIGENCE WAVE (owner: build it all in one go): (1) N-PORT pct_value weights + cash sleeves (STIV) into moat_cover.deep_weights/deep_cash; (2) deep set +KSTR/EWY/EWT; (3) Tab 17 rb.exposure -- true underlying-company exposures with honest coverage + look-through diversification tags; (4) Tab 19 held_via overlap stamping against held funds' real constituents (D-114).

## 1.407.0

Tab 17 tilt switched to LOOK-THROUGH (_LIH_REGION_SPLIT): Asia-Tech 64 -> 34%, US-Tech 1.2 -> 21% -- owner's challenge confirmed correct.

## 1.406.0

ETF-holder post-pass extended to global_discovery.picks (intl listings honestly 0).

## 1.405.0

N-PORT guardrails: >=10-ticker plausibility gate (SPDR filings are CUSIP-only and parse to 1) + monotonic cache -- better data never overwritten by worse (D-113).

## 1.404.0

THE RESOLUTION FIX: deterministic series-NAME matching (_NPORT_NAME_KEYS vs general_info.series_name), diagnosed offline from edgartools source (its ticker maps lack 29/30 of our ETFs -- verified in the bundled parquet), trap-tested against an S&P-500 decoy; the Fund() path removed outright (D-112: a resolver that can return wrong data silently is removed, never gated).

## 1.403.0

Fund() resolution path tried and PROVEN WRONG live (19/30 misresolved; SOXX returned the S&P 500's portfolio).

## 1.402.0

largest-filing fallback restricted to _BROAD funds only; sector funds must name-match or return honestly empty.

## 1.401.0

carry-gate requires full deep-set coverage (the old 3-ETF cache had been blocking the widened 30-ETF fetch).

## 1.400.0

deep-holdings set widened 3 -> 30 sector/thematic ETFs.

## 1.399.0

UCITS -> US-equivalent bridge (_ucits_us_equiv) as the safety net under justETF.

## 1.398.0

post-pass annotates explosive/multibagger rows (etf_holders, etf_holder_count); build-order issue (index builds after those engines) solved by stamping late.

## 1.397.0

shared etf_holdings_index (stock -> ETFs) + etf_holders_for() accessor.

## 1.396.0 - 1.387.0 (grouped)

v1.387.0 - v1.396.0 -- N-PORT BREAKTHROUGH (grouped; see Dashboard_Changelog_2026-08-10). After proving every alternative dead (TV WebSocket session-auth via owner DevTools; API Ninjas + Finnhub premium walls; scraper repos consent-walled/paid-proxy), ETF holdings fetch built on SEC EDGAR N-PORT via edgartools: FundReport.from_filing() + investment_data(). First live truth: IVV/ITOT 1,748, VTI 3,462 real holdings; ETF-confirmed moat names 138 -> 209. Bug chain fixed en route: UA name collision, styled-HTML vs raw XML, namespace attribute prefixes, wrong trust CIK.

## 1.386.0

match the owner's secret NAME. Owner set the Finnhub key as ETF_FINNHUB_KEY (not FINNHUB_KEY), so the fetch read the wrong env var and got no_key. Fix: fetch_finnhub_etf_holdings reads os.environ['ETF_FINNHUB_KEY']. Also accepts a plaintext root file 'ETF_FINNHUB_KEY' as a fallback if present. daily.yml must pass ETF_FINNHUB_KEY. PRIOR: CHANGELOG.md.") s=s.replace(ov,nv,1) update the env read to try ETF_FINNHUB_KEY first, then FINNHUB_KEY, then a root file old=" _key = os.environ.get('FINNHUB_KEY', '').strip() if not _key: return [], {'src': 'finnhub', 'n': 0, 'err': 'no_key'}" new=(" _key = (os.environ.get('ETF_FINNHUB_KEY') or os.environ.get('FINNHUB_KEY') or '').strip() if not _key: try: with open('ETF_FINNHUB_KEY') as _kf:

## 1.385.0

add FINNHUB ETF holdings as the primary deep source (API Ninjas free tier paywalls holdings: 'premium users only'). Finnhub's /api/v1/etf/holdings?symbol= is documented to return constituents and its free tier may include them. fetch_finnhub_etf_holdings(ticker) pulls the 'holdings' array (symbol/share/weight). build_moat_cover now tries FINNHUB first, then falls back to API Ninjas -- whichever returns >=50 real holdings wins. Key from env FINNHUB_KEY (GitHub secret; never hardcoded). Junk-reject + n>=50 gate + diag-on-miss retained. Fail-open. PRIOR: see CHANGELOG.md.")

## 1.384.0

ETF deep holdings via API NINJAS REST (real solution to the WebSocket wall). TV serves holdings only over an authed websocket (proven); API Ninjas serves them as plain REST JSON with no wall: GET https://api.api-ninjas.com/v1/etf?ticker=<T> + X-Api-Key. New fetch_ninja_etf_holdings(ticker) pulls the full 'holdings' array (ticker/name/weight) for IVV/ITOT/VTI -- covering the moat mid-caps. Key read from env ETF_NINJA_KEY (GitHub Actions secret; NEVER hardcoded, the repo is public). Robust parser handles the documented {holdings:[{ticker,weight}]} shape and variants; junk-reject + n>=50 gate retained; diag captures the response on miss. Fail-open: no key or any error -> existing top-25 behavior unchanged. PRIOR: see CHANGELOG.md.")

## 1.383.0

TV holdings CONCLUDED unreachable (session-authed WebSocket, proven via owner DevTools). Deep-fetch disabled so it no longer consumes runtime. TV/parser functions retained for a future dedicated WebSocket client, which is the only way to reach TV's streamed constituents. deep_diag = {'_status': 'disabled_ws_only', 'note': 'TV serves ETF holdings via an authed websocket; not fetchable over HTTP'} ", "

## 1.382.0

exchange-qualified symbol (AMEX-IVV), confirmed from owner's DevTools capture. _TV_EXCH = {'IVV': 'AMEX', 'ITOT': 'AMEX', 'VTI': 'AMEX', 'IWM': 'AMEX', 'SPY': 'AMEX', 'VOO': 'AMEX'} _ex = _TV_EXCH.get(_sym, 'AMEX') _qs = '%s-%s' % (_ex, _sym) e.g. AMEX-IVV _hdrs = {'User-Agent': UA, 'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Origin': 'https://www.tradingview.com', 'Referer': 'https://www.tradingview.com/symbols/%s/holdings/' % _qs}

## 1.381.0

positively identify the constituent array anywhere in the JSON. " _arrays = _tv_all_arrays(obj) 1) prefer the array with the MOST rows that look like real holdings (symbol + weight) _best = None; _best_n = 0 for _arr in _arrays: _hits = [r for r in _arr if _looks_like_holding(r)] if len(_hits) > _best_n: _best_n = len(_hits); _best = _hits if _best and _best_n >= 5: return list(dict.fromkeys(t for t in (_tv_row_ticker(r) for r in _best) if t)) 2) fallback: largest array of symbol-bearing rows (no weight requirement) _best = None; _best_n = 0 for _arr in _arrays: _tks = [t for t in (_tv_row_ticker(r) for r in _arr) if t] if len(_tks) > _best_n: _best_n = len(_tks); _best = _tks return list(dict.fromkeys(_best or [])) ") io.open(p,'w',encoding='utf-8').write(s) print('OK edits=%d'%len(done),', '.join(done)) PYEOF python3 -c "import ast

## 1.380.0

real holdings, not 2 junk tokens if fresh and cache and _deep_ok: log(' [MOAT cover] carried (fresh <5d, TV deep present): %d ETFs' % len(cache)) return prev if not _is_tv: log(' [MOAT cover] cache lacks TV-sourced deep_diag -> refreshing to run TV fetch')", "

## 1.379.0

capture each candidate container so the TRUE holdings array is identified if isinstance(_j, dict): for _ck in ('results', 'render_results', 'extra_data', 'symbol_info'): _cv = _j.get(_ck) if _cv is not None: _diag['k_' + _ck] = str(_cv)[:220] return _tks, _diag ") io.open(p,'w',encoding='utf-8').write(s) print('OK edits=%d'%len(done),', '.join(done)) PYEOF python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" cp scanner.py /mnt/user-data/outputs/scanner.py grep -m1 -o "

## 1.378.0

TV holdings parser targets the 'results' key. The v1.377 diag proved TV's holdings live under top-level 'results' (not 'holdings'/'symbol'). _extract_tv_tickers now dives into results/render_results/extra_data first and recognises every plausible constituent row shape (symbol/ticker/s/name + nested 'd' arrays with a symbol string). Diag also widened to capture the real results[] slice as a safety net so if the row shape is unusual, one run shows it exactly. TV data is confirmed arriving (200/json), so this should populate the mid-caps. Changed: _extract_tv_tickers + diag results-capture. PRIOR: see CHANGELOG.md.")

## 1.377.0

JSON parsed but no tickers -> capture the shape so the parser can be finalised _diag = {'url': _u[:70], 'http': 200, 'n': 0, 'src': 'tv', 'top_keys': list(_j.keys())[:20] if isinstance(_j, dict) else 'not-dict'} _hi = _txt.find('holdings') if _hi < 0: _hi = _txt.find('symbol') if _hi < 0: _hi = _txt.find('"data"') if _hi >= 0: _diag['around'] = _txt[_hi:_hi+300] return [], _diag ") io.open(p,'w',encoding='utf-8').write(s) print('OK edits=%d'%len(done),', '.join(done)) PYEOF python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" cp scanner.py /mnt/user-data/outputs/scanner.py grep -m1 -o "

## 1.376.0

FIX the KeyError that froze moat_cover. Root cause (proven by replaying the real function): build_moat_cover's log line did {k: v['n'] ...} -- a hard key access -- but fetch_tv_etf_holdings' miss-path _diag dict has no 'n' key, so every run raised KeyError:'n', hit the except, and carried the stale 04:06 cache -> moat_cover frozen across 3 scans, TV fetch never persisted. FIX: v.get('n', 0) in the log, and the TV fetch always sets n in its diag. Now build_moat_cover completes, the src-tag gate fires, and the TV verdict actually writes. Changed: the log line + TV diag n-default. PRIOR: see CHANGELOG.md.")

## 1.375.0

tag so the gate can tell TV diag from the old iShares diag deep_diag[_bt] = _info if _tks: cache[_bt] = _tks except Exception as _be: deep_diag[_bt] = {'http': type(_be).__name__, 'n': 0} log(' [MOAT cover] fetched ","stderr":}

## 1.374.0

IBKR interest accruals -> NAV nav = holdings_usd + cash_usd + interest_usd ") assert s.count(old)==1, s.count(old) s=s.replace(old,new,1) also surface interest_usd in the emitted dict so it's visible old2="'as_of': today, 'nav_usd': round(nav, 2), 'holdings_usd': round(holdings_usd, 2)," new2="'as_of': today, 'nav_usd': round(nav, 2), 'holdings_usd': round(holdings_usd, 2), 'interest_usd': round(interest_usd, 2)," assert s.count(old2)==1, s.count(old2) s=s.replace(old2,new2,1) io.open(p,'w',encoding='utf-8').write(s) print('interest wired into NAV + emitted') PY python3 -c "import ast;ast.parse(open('/home/claude/scanner_work.py',encoding='utf-8').read());print('AST OK')"

## 1.373.0

carry only once TV deep holdings have succeeded; else refresh to retry the fetch. _deep_ok = any((v ","stderr":}

## 1.372.0

CONCLUDED unreachable from the runner (5 methods tried) -- disabled to stop the per-scan retry. Re-populate only with a source proven to serve automation.") also restore the freshness gate to not force-refresh on empty deep (since deep is now intentionally empty)

## 1.371.0

iShares CSV via the BUSINESS-RECORDER technique (owner's insight). BR serves the SPA/HTML shell to a plain GET but returns the real data when the request carries X-Requested-With: XMLHttpRequest (+ JSON/AJAX Accept + XHR fetch-metadata headers) -- signalling an in-page fetch, not a navigation. iShares' wall is the same shape (plain GET -> terms HTML; real CSV only for the browser's own fetch). So the broad-holdings request now sends the XHR header set on the session's CSV call. If it still returns HTML, html_wall stays True and we stop for good. One decisive run. Fail-open; UK pinned funds untouched. PRIOR: see CHANGELOG.md.")

## 1.370.0

iShares sets consent server-side -> use a SESSION. Step 1: hit the disclaimer-accept entry so the server drops the real consent cookie into the jar. Step 2: fetch the CSV reusing it. _sess = requests.Session() _sess.headers.update({'User-Agent': UA}) try: _sess.get('https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn' '?siteEntryPassthrough=true&dcrPath=/templatedata/config/product-screener-v3/data/en/us-one/product-screener', timeout=25, allow_redirects=True) _sess.get('https://www.ishares.com/us/products/%s?siteEntryPassthrough=true' % _pid, timeout=25, allow_redirects=True) except Exception: pass _hdrs = {'Accept': 'text/csv,application/csv,*/*', 'Referer': 'https://www.ishares.com/us/products/%s' % _pid} _r = _sess.get(_url, headers=_hdrs, timeout=35, allow_redirects=True) _txt = _r.text or '' ", ) io.open(p,'w',en

## 1.369.0

iShares CSVs carry a BOM _tks = [str(x.get('ticker') or '').upper() for x in _rows if x.get('ticker')] _tks = [t for t in _tks if (t and t.isalnum()) or ('.' in t)] _base_info['n'] = len(_tks)" assert s.count(old)==1, s.count(old) s=s.replace(old,new,1) io.open(p,'w',encoding='utf-8').write(s) print('BOM strip added') PY python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" python3 - <<'PY' import ast,datetime as dt b=open('scanner.py',encoding='utf-8').read();tree=ast.parse(b) picks={'_parse_ishares_csv':0,'fetch_ishares_broad_holdings':1,'build_moat_cover':2} nodes=sorted([n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in picks],key=lambda n:picks[n.name]) mce=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MOAT_COVER_ETFS' for t in

## 1.368.0

MOAT deep-holdings diag widened. v1.367 showed IVV/ITOT HTTP 200 but bytes=None -- the early 'not _r.text' return fired, so the body is EMPTY on a 200. That means the .ajax CSV endpoint returns nothing for our request (redirect to a landing page, or missing required params/headers). The diag now ALWAYS records regardless of empty body: http, bytes, content-type, final-url (after redirects), and the first 300 chars -- so one run shows whether it's an HTML redirect page, an empty 200, or a cookie/consent wall. Only then is the fix deterministic. Fetch still fail-open. PRIOR: see CHANGELOG.md.")

## 1.367.0

only carry once deep holdings actually succeeded log(' [MOAT cover] carried (fresh <5d, deep present): %d ETFs' % len(cache)) return prev", "

## 1.366.0

a pre-deep-holdings cache (no deep_diag) must refresh once so the broad CSV runs.

## 1.365.0

BROAD funds via issuer full-CSV -- deep holdings that reach the mid-caps. deep_diag = {} for _bt in _ISHARES_BROAD: try: _tks, _st = fetch_ishares_broad_holdings(_bt) deep_diag[_bt] = {'http': _st, 'n': len(_tks)} if _tks: cache[_bt] = _tks unioned into holders like any other ETF except Exception as _be: deep_diag[_bt] = {'http': type(_be).__name__, 'n': 0} log(' [MOAT cover] fetched %d/%d top-25 ETFs + broad deep: %s' % (got, len(MOAT_COVER_ETFS), {k: v['n'] for k, v in deep_diag.items()})) return {'by_etf': cache, 'as_of': dt.datetime.now(dt.timezone.utc).isoformat(), 'n_etfs': len(cache), 'deep_diag': deep_diag}") io.open(p,'w',encoding='utf-8').write(s) print('OK edits=%d'%len(done),', '.join(done)) PY python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" python3 - <<'PY' import ast,io b=io.op

## 1.364.0

MOAT turnaround flag fixed. The Turnaround membership flag read a non-existent 'tier' field, so it never fired (0 moat rows flagged). Real marker is the explosive_us 'verdict' string 'TURNAROUND -- quarterly inflection'. f_turn now derives from that. This makes the tab's new display rule (index v5.317: show returns >0, hide <=0, but ALWAYS show qualifying turnarounds) actually surface inflecting names. Changed: f_turn derivation only. PRIOR: see CHANGELOG.md.")

## 1.363.0

MOAT adds YTD alongside 1Y for every live-tracked name. Owner: 'add ytd also for all stocks'. The america/scan column request gains 'Perf.YTD'; each live row now carries ret_ytd_live beside ret_1y_live. Both figures render on the tab (index v5.316). Changed: the moat live-fetch columns + row assembly only. PRIOR: see CHANGELOG.md.")

## 1.362.0

MOAT -> ranked UCITS ETF list holding the top-return moat names. Owner: show the ETFs (with ISIN + all columns, World-ETF format) that concentrate the highest-return moat stocks. build_moat_universe now also assembles data['moat']['top_etfs']: pools every live UCITS ETF that carries ISIN + holdings (etf_momentum_watch + etf_emerging_themes_watch + hydrogen + metals ETC, ~101 funds, all with ter/ytd/live_ret_1y/estate_status), scores each by how many of the top-40 return leaders it holds (name-token match on the real holdings string), and emits the ranked list with FULL columns so the tab renders it exactly like Tab 16. No new fetch -- reuses ETF payloads already live. Changed: build_moat_universe tail only. PRIOR: see CHANGELOG.md.")

## 1.361.0

real ETF holdings coverage first (cached 5d), then MOAT reads it. try: data['moat_cover'] = build_moat_cover(EXISTING) except Exception as _mce: log('[MOAT cover] skipped: %s' % type(_mce).__name__) data['moat_cover'] = EXISTING.get('moat_cover', {}) or {}

## 1.360.0

MOAT TICKERS-FOR-ALL + ETF-HOLDER CONFIRMATION. Owner: non-US names had no ticker/return, and wanted the UCITS ETFs holding the top names shown. (1) ALL 317 names now carry a US-listed ticker/ADR (ASML, TSM, NVO, TD, HSBC, BESIY ... ADR map), so live returns resolve for every row through the same america/scan dual-exchange path -- no more blank non-US rows. (2) Each row now carries ucits_file (UCITS ETFs from the owner's ETF-Universe file that list it among their major holdings) AND etf_holders_live (US ETFs from wave_z.fund_cache that actually hold it, real top-25 data). Seed row is now 12-field (adds ucits_file). HONEST LIMIT stated in the tab: the file lists only each fund's top ~4 holdings, so file-matches are a floor not a census; true full UCITS holdings need a separate probe-first wave. Changed:

## 1.359.0

MOAT NYSE RESOLUTION -- v1.358 diag proved the prefix fix worked but resolved only 77/203 (the NASDAQ-listed names); the ~126 NYSE-listed moat names don't resolve under a NASDAQ: prefix. FIX: send BOTH NASDAQ:<t> and NYSE:<t> candidates per ticker (america/scan returns only what resolves -- the wrong-exchange twin is silently absent, no error, no cost), 100 per chunk. This is the mixed-exchange query the foundation-universe call proves. Expected n_live ~203. diag unchanged (still records match counts). Changed: the MOAT live-fetch loop only. PRIOR: see CHANGELOG.md.") s=s.replace(ov,nv,1) io.open('scanner.py','w',encoding='utf-8').write(s) print('applied') PY python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" python3 - <<'PY' prove: dual-candidate matching resolves both exchanges on a mixed stu

## 1.358.0

america/scan resolves EXCHANGE-PREFIXED symbols only. Prefix NASDAQ:<t> (this request resolves NYSE-listed names too, same as the foundation-universe call). Pull the ready 'Perf.Y' 1-year column alongside close/change. tickers = [r[2] for r in

## 1.357.0

WAVE MOAT -- a curated wide-moat global universe (317 names, owner-supplied justETF moat screen) as a new tab + auto-tracking engine. build_moat_universe(): live return tracking forward-from-first-seen for the 203 US large-caps (proven america/scan endpoint, chunked 50s, static file 1Y retained for the 114 non-US names -- NO fabricated live data), full every-engine cross-reference per stock (IM3 grade, Zacks, TipRanks, whale 13F, and Explosive/Turnaround/M1/Multibagger/TCE/WaveZ membership flags), and ETF-conviction confirmation (the file's own n_etfs breadth + which tracked funds actually hold each name, read from the existing wave_z.fund_cache). Emits data['moat'] = {rows, leader_isins (top-20 by best available return), n_total, n_live, as_of}. Call site at the tail after wave_z (reuses its fund_cache + all engine outputs; pipeline-orde

## 1.356.0

COT FRESHNESS GATE -- cot_futures cost 76.5s this run (vs its ~8-9s norm; CFTC's endpoint was crawling), and the fetch runs twice daily against data CFTC publishes ONCE A WEEK (Fridays, covering Tuesday positions). The stage now short-circuits when the carried cot_futures.as_of (stamped since v1.348.0) is younger than 72h: carry EXISTING, skip the fetch, log '[COT] carried (fresh <72h)'. A 3-day TTL loses nothing weekly-cadenced -- a Friday release is picked up by Saturday's runs at the latest -- and converts a 9-to-76-second twice-daily cost into at most two fetches a week. Fail-open: absent/undated prior -> fetch as before. Changed: the cot_futures call site in main only. PRIOR: see CHANGELOG.md.")

## 1.355.0

OIL LADDER FUTURES-FIRST -- the run log priced the polite TVC-first ordering at ~45s/run (fetch_us_macros 62.0s vs 16.5s on the prior run): TradingView's null responses for the dead TVC:USOIL/UKOIL symbols were slow before the proven futures rungs rescued the values. The try-lists now lead with the rungs that have resolved EVERY run since v1.347.0 (NYMEX:CL1!, ICEEUR:BRN1!) and keep the TVC symbols as the trailing rung, so the day TradingView restores them they resume automatically -- same ladder, same guard, reordered by evidence. Also silences the two chronic TVC warnings on normal runs (the dead rung is no longer attempted when futures succeed first). Changed: the cmap literal only. PRIOR: see CHANGELOG.md.")

## 1.354.0

MF holdings unavailable free -- intersection runs over the #1 ETFs; MF chips still shown. ") io.open(p,'w',encoding='utf-8').write(s) print('OK edits=%d %d->%d (%+d)'%(len(done),n0,len(s),len(s)-n0)); print(', '.join(done)) PY python3 -c "import ast;ast.parse(open('scanner.py',encoding='utf-8').read());print('AST OK')" cp scanner.py /mnt/user-data/outputs/scanner.py grep -m1 -o "

## 1.353.0

WAVE Z ENGINE -- Zacks #1-ETF x #1-mutual-fund COMMON-HOLDINGS intersection (the plan's research-first wave; research done THIS session: Zacks ETF quote pages serve the rank server-rendered ('1 - Strong Buy of 5', proven on XLK), MF quote pages likewise ('Zacks MF Rank ... 1-Strong Buy', proven on FSPTX/FSPSX incl. a NA case), and BOTH families expose /holding pages -- one source, the same fetch pattern as the proven stock-rank scrape, no stockanalysis dependency). Population note (honest): the full #1 list is premium-screener-gated, and our own ETF estate is UCITS (EURONEXT/IE ISINs Zacks does not rank), so the engine ranks curated US seed lists -- WAVE_Z_ETFS (~34 liquid sector/style/industry ETFs) + WAVE_Z_MFS (~16 major active funds) -- and intersects the top holdings of the rank-1s. Flatten-then-regex parsing (the tipranks lesson), T

## 1.352.0

TIPRANKS PARSE FIX -- v1.351.0's diagnostics delivered the verdict in one run exactly as designed: http={200:24, 404:1}, parse_fail=24, sample_head = a raw-HTML head. The runner is NOT IP-blocked; the pages serve fine. The anchors failed because they were validated against CONVERTED text while the runner receives raw HTML with tags/whitespace interleaved through the very same sentences (e.g. 'consensus rating of <b>Strong Buy</b>'). FIX: preprocess the body -- strip tags (re.sub <[^>]+> -> space), decode the few entities that touch our anchors (&amp; &nbsp; &#36;), collapse whitespace -- THEN apply the SAME already-validated sentence regexes. Belt-and-braces fallback: if sentences still miss, parse n_analysts from the meta-description ('based on N analysts'), which the diag PROVED serves in the raw head. Diagnostics stay. PRIOR: see CHANG

## 1.351.0

(SELF-CORRECTION) TipRanks overlay ran in production and stored ZERO of 25 tickers with ZERO warnings -- because v1.350.0's two skip paths (non-200 response; 200 page that misses the parse anchors) were both silent `continue`s, violating the failures-announce-themselves principle the chunked-scorer fix established. Cannot distinguish runner-IP blocking from anchor drift without evidence. FIX: per-run diagnostics recorded INTO the tipranks payload -- diag = {http: status-code counts, parse_fail count, sample_head: first 160 chars of one 200-but-unparseable body} -- plus one loud warn line whenever picks exist but zero fetches succeed. Next run's data.json names the exact failure mode self-serve. No behavior change on the success path. PRIOR: see CHANGELOG.md.")

## 1.350.0

TipRanks overlay -- AFTER recommended exists (it reads the list), before stamps/write. ", "

## 1.349.0

quarterly-aligned (was 7d): statements change quarterly; 7d meant churn names re-fetched weekly for no informational gain

## 1.348.0

self-serve freshness stamps at the FINAL write -- every stage has run and recorded its timing by this point (relocated from mid-main, where cot_futures had not yet run and its stamp could never fire -- placement caught by the pipeline-order rule). try: _asof_now = dt.datetime.now(dt.timezone.utc).isoformat() _tms = (data.get('meta') or {}).get('timings_ms') or {} if isinstance(data.get('cot_futures'), dict) and _tms.get('cot_futures'): data['cot_futures']['as_of'] = _asof_now if isinstance(data.get('metals_drivers'), dict) and _tms.get('metals'): data['metals_drivers']['as_of'] = _asof_now if isinstance((data.get('macros') or {}).get('metals'), dict) and _tms.get('metals'): data['macros']['metals']['as_of'] = _asof_now if isinstance(data.get('estimate_history'), dict): data['estimate_history']['as_of'] = _asof_now except Exception:

## 1.347.0

WTI/Brent futures fallback -- the owner's captured per-symbol GET (v1.327.0) now returns HTTP 200 body null for TVC:USOIL/UKOIL (upstream TV change; warning trail proves the fix itself runs and TV degraded beneath it), and the /scan CFD ladder was already rows=0. Added front-month futures NYMEX:CL1! (WTI) and ICEEUR:BRN1! (Brent) to each symbol's try-list -- same class, same /scan route the Arab Light ladder already resolves NYMEX:WS1!/ICEEUR:DUB1! through every run, so the pattern is proven in this file, not assumed. Symbol-GET still leads (cheap when TV restores it); futures fill when it nulls. Sane-band guard 10..400 unchanged. Changed fn: fetch_us_macros oil block only. PRIOR: see CHANGELOG.md.")

