## v1.587.2 - FIX: current account headline was read before it existed (NameError swallowed) so a crude scrape gave +1369; live Business Recorder value now wins unless the manual file sets it. Import-bill queries widened.

## v1.587.1 - every hand-fed macro input now shows its age on the dashboard (cards + Data-age panel; unknown date = STALE)

## v1.587.0 - Pakistan macro inputs now update themselves
- SBP reserves, monthly import bill and current account are read from Business Recorder headlines (Google News RSS), with plausibility clamps. Priority: explicit psx_macros_manual.json value > live headline > old constant (logged as stale).
- Fixes the 125-day-old reserves (dashboard showed 16.53bn; real SBP-held is 21.45bn, total liquid 26.80bn, week ended 2 Oct) that understated import cover.
- Content-age rows show the real source and date. Parsers unit-tested offline; live fetch verifies on the next GitHub run (sandbox cannot reach Google News).

## v1.586.0 / index v5.446 - audit actions 1-5
1. PSX SIGNAL: new ev_psx_signal. Every Pakistani candidate and your five holdings get BUY / BUY SMALL / ADD / WAIT FOR PRICE / HOLD / AVOID, fair value and buying zones (strong buy 75%, buy 90%, rich 110% of fair value), chart support zone and stop; merged into the master signal as 'PSX:<ticker>' so chips work on the Pakistan tabs; section on tab 23. Holdings only read HOLD or ADD (no validated PSX exit rule). Weak KSE-100 phase = new money only at a confirmed bottom.
2. TIGHTER BOTTOMS: a CONFIRMED name below its 200-day that was never armed (Bottom Rule v2 sequence) is moved back to WATCHING and loses tranche_ok (state_loose keeps the old state; TIGHTEN_BOTTOMS=0 reverts). State counts recomputed.
3. ONE EXIT VOICE: the exit arbiter table says it is the instruction to follow; older sections are named only where they disagree ('All sections agree' otherwise).
4. LOG: every stage of 5 s or more prints its own line; serialise time logged; the old 'data.json written in 57 s' was the whole post-export phase (bottoms, governors, serialising), not the file write - label corrected.
5. HEADROOM: fwd_eps_hist, estimate_history and world_stocks (about 1.3 MB, never read by index.html) moved to committed side files with slim inline pointers; carry-forward reads them first (_prev_block). daily.yml commits the three files.

## v1.585.4
- Replaced the deprecated pd.Timestamp.utcnow() (3 Pandas4Warning per run; removed in pandas 4) with pd.Timestamp.now('UTC'). Same value, no behaviour change.

## v1.585.3 / index v5.445
- Hover on every signal chip, trend chip, signal pill and zone-table ticker shows the full company name; hover on a pill (6 to SELL, 5 to TRIM, 14 to BUY ...) lists every ticker with its name. Pills now show the true count (they were capped at 12).
- A held note whose bottom check has fired but is unconfirmed now says so (AMD3: 'a possible turn is forming, not confirmed, does not cancel the stop instruction'); 3x notes with earnings within 10 days carry the gap warning. The Bottom Watch text no longer says 'nothing fires' when a rule has fired.

## index v5.444 - NEW TAB 23 'Fundamental & Technical Buy'
- Where to enter, the buying-zones table, the buy-the-dip map, the plain-words chart guide and the engine roster moved out of the first-page banner into their own tab. The first page keeps only the compact one-message banner (headline, markets, signal counts) plus a button to the new tab. No scanner change.

## v1.585.2 - AUDIT FIXES (live run of 27 Oct, v1.585.1)
- Master signal now takes 'growing + cheap' (entry points) as a business vote: DVN and RERE no longer read TREND ONLY / AVOID on one tab and 'buy' on another.
- BUY SMALL from a confirmed bottom says so ('chart shows a CONFIRMED BOTTOM - small first piece') instead of 'the price says wait'; headline separates 'buy where business and price agree' from 'small first piece at a confirmed bottom'.
- Results tab summary rebuilt after the evidence layer (it still showed VLO / FOXA / ROST as BUY after entry timing had turned them to WAIT (bottom rules)).
- A BUY SMALL backed only by Zacks or Explosive carries a caution (neither has beaten the market in the live ledger yet).

## v1.585.1 / index v5.443 - fundamental buying zones: per growing stock fair value (average of the two valuation models), strong-buy (75%), buy-below (90%), rich (110%) lines, status and plain business-view sentence; M1 'Attractive' no longer counts as cheap when price is >10% above fair value. Banner table of all growing stocks.

## v1.585.0 / index v5.442 - WHERE TO ENTER (fundamentals + price)
- New `ev_entry_points` (runs in `ev_post_bottoms` after master signal and trend dips). A stock qualifies when this quarter's EPS is up 15%+ and sales 10%+ on a year ago (Explosive US or the acceleration screen) AND it is cheap (M1 Attractive / cheap vs peers / 15%+ margin of safety / P/E <= 18). The price must then give one entry: BUY ON RETRACEMENT, BUY AT A CONFIRMED BOTTOM (small), BUY THE BREAKOUT (close above ceiling on volume), BASE FORMING (quiet 8+ day base, buy only on the breakout close), else WAIT / STAND ASIDE / DON'T CHASE.
- Banner section "Where to enter" with entry zone and stop per name. Offline test on 27 Oct data: 45 growing names, 17 cheap, 1 buy-now, 2 base-forming.

## v1.584.1 — 2026-10-27 — trend-and-dip map (index v5.441)
- `ev_trend_dips`: from the trend playbook on each entry-timing row, every trending stock is classed RETRACEMENT HAS ARRIVED (inside the 20-50 day buy zone), RETRACEMENT CLOSE (within 3% above it), BREAKING OUT, RETRACEMENT COMING, STRETCHED (do not chase) or BROKEN, with zone, stop, gap to zone and a plain sentence; business votes from master_signal. Weekly hidden divergence (trend-continuation) is now stored on the 70 per-stock arming rows. Live 27 Oct (offline): 2 arrived (BWIN, BMNP), 10 close (EXPD, TMO, AMG, KO, ELV, KMI...), 7 breaking out, 13 coming, 14 stretched, 49 broken.
- INDEX: the banner above the tabs gains the buy-the-dip map and a plain-words guide to trend, retracement, breakout, stretched, RSI, divergence, hidden divergence, bottom and stop. Ticker chips no longer decorate the banner's own pills.
## v1.584.0 — 2026-10-27 — THE ONE MESSAGE: master signal across every engine (index v5.439 + v5.440)
- `ev_master_signal` (+ `MASTER_ENGINES` roster: 24 engines, 13 judge the business, 11 judge the price): collapses all engines into one plain signal per ticker: BUY, BUY SMALL, BUY ON A DIP, WAIT FOR PRICE, TREND ONLY, HOLD, ADD, TRIM, SELL, AVOID. Business votes (M1, Recommended v2, Explosive confirmed, M2 quality/turnaround, Zacks rank <= 2, whale consensus, Global discovery) say whether the company is attractive; price votes (entry-timing verdict, trend playbook, bottom rules) say whether the moment is right; a held name takes the exit arbiter's instruction first; a broken trend never gets a buy. Published as `data.master_signal` {headline, markets, rows, lists, engines, rule}; ~24 KB. Recomputed after the bottoms stage so it reads the fresh bottoms rows.
- INDEX: a one-message banner above the tabs (what to do first, buy candidates, buy-on-a-dip, good businesses waiting, market phases, counts, expandable roster of the 24 engines) and the signal word next to every ticker on every tab (hover = the reason in plain words). Every evidence box leads with what it is / how it helps / what to do (v5.439); Tab 17 starts with the APD NetBenefits section.
- Live 27 Oct payload (offline): 169 names signalled: 6 SELL, 5 TRIM, 1 BUY, 8 BUY SMALL, 4 BUY ON A DIP, 77 WAIT FOR PRICE, 12 TREND ONLY, 56 AVOID. Not yet run live.
- NOT done: the pre-v1.580 sections (metals engine text, factor framework, seasonality tables, macro panels) keep their original wording.
## v1.583.1 — 2026-10-27 — FIX: the bottoms gates were being overwritten (found in the audit of the first v1.583.0 live run)
- FINDING: `build_bottoms` runs AFTER the evidence layer and assigns a fresh `data['bottoms']`, so everything the evidence layer wrote to bottoms rows never reached the published file: the falling-knife gate (item 28), the Bottom Rule v2 per-stock sequence gate (v1.582.0), and the v1.583.0 per-stock arming. Live 27 Oct 06:08 UTC payload: v2_gate 0, knife_gate 0, no knife_gate_count, no arming. The replays (which start from a stored payload) could not show it.
- FIX: `ev_post_bottoms` re-applies `ev_bottoms_knife` and `ev_stock_arming` immediately after the bottoms stage (`post.bottoms_gates`); arming now always publishes `arming_summary` (a skip reason when it cannot run). Applied to the live 27 Oct payload offline: first tranches 32 -> 20 (12 held back: 6 by the v2 sequence, 6 by the knife gate), 11 CONFIRMED-below-200-day names never armed.
- NOT changed: the advisor ADD gate inside build_bottoms is computed before these gates; the audit-layer ledger lanes still read the bottoms of the previous scan (one-scan lag).
## v1.583.0 — 2026-10-27 — COT release-aware cache + freshness, metals COT-extreme score, per-stock Bottom Rule v2 arming (index v5.437; daily.yml schedule)
- COT CACHE: disaggregated and TFF pulls now happen once per CFTC release (Friday ~19:30 UTC for the Tuesday before) instead of every run on Sat/Sun/Mon; a block that already holds the newest expected report is carried, a stale block is retried at most every 6 hours. The legacy futures carry is release-aware the same way. Tested: current block = 0 fetches, stale block = 2 fetches.
- COT FRESHNESS: `data.cot_freshness` {expected_report_date, per-source report_date / lag_days / FRESH-LAGGING-STALE}; `metals.cot_freshness`. Checked on the live 26 Oct payload: all four feeds FRESH at 2026-10-20. Shown in a new COT box on the Metals tab.
- METALS COT-EXTREME SCORE (item 43 remainder): `metals.cot_extreme_score` -2..+2 per metal from managed-money index, legacy percentile and producer leg; information only, never a veto. Live 26 Oct: Gold +1, Silver +1, Platinum +1 (producers at a 3-year long extreme), Copper 0, Palladium 0.
- K11 PER-STOCK ARMING (shadow): `ev_stock_arming` runs the SAME evaluator as the index watch on up to 70 names (holdings, CONFIRMED, WATCHING with a >=10% decline) from ~300 daily and ~160 weekly bars; writes bottoms.rows[t].arming and bottoms.arming_summary. It does not change tranche_ok; `arming_would_withhold` marks CONFIRMED names below their 200-day that were never armed. Replay: 70 evaluated, 23 armed, 9 CONFIRMED-bear-never-armed. Live fetch time unmeasured until the first scan (expect +15-40 s).
- INDEX v5.437: COT box (Metals), per-stock arming box (Live Investment), plain-English hovers on ~60 legacy column headers (any <th> without its own tooltip).
- daily.yml: crons now `30 22 * * *` and `0 11 * * *` (03:30 / 16:00 PKT; GitHub's 3-5.5 h delay lands them ~09:00 PKT and 16:00-21:30 PKT).
- Item 52 was already largely built (feeds with 3 empty runs are skipped and retried every 20th run); recency weighting still not done. Items 12, 17, 21, 31, 33, 34, 41, 48, 51 unchanged (external feeds or calibration needed).
## v1.582.2 — 2026-10-26 — exit arbiter: execution sequence (index v5.436)

Caps confirmed as policy after the research (UCITS 5/10/40, US 75-5-10, FINRA 09-31, adviser rules of thumb): theme cluster 25%, single line 15%, 3x sleeve 5%, core >= 40%.
The arbiter now publishes `actions.sequence`: (1) EXIT 3x notes past the -20% hard stop or on a bear underlying, (2) TRIM the remaining 3x to the 5% sleeve, (3) EXIT bear-regime lines with a broken 50-day (worst P&L first), (4) TRIM the over-cap theme cluster largest line first, in tranches on up-days, (5) ADD a World/ACWI UCITS core up to 40%, keeping the cash floor. Each step carries approximate dollars from NAV. Shown at the top of the arbiter box.

## v1.582.1 — 2026-10-26 — exit arbiter made regime-first; moved to the bottom of the Live Investment tab (index v5.435)

Audit of the owner's complaint ("EXIT on every holding makes no sense"): the arbiter was faithfully repeating the pre-existing 50-day exit rule (COARSE: 8% under the 50-day = EXIT), which already read EXIT / SELL on 9 of 11 lines elsewhere on the tab, while the rebalance advisor said HOLD on the same lines and the validated Bottom Rule v2 put 8 of 11 instruments in a BULL regime (above their 200-day). Three engines, three answers; the arbiter had picked the harshest.
Fix: regime first, per the validated book. Above its own 200-day, a 50-day break is RULE 6 (hold, no averaging) and is shown as a flag, not an exit; below the 200-day the 50-day exit rule stands. 3x notes exit only on the -20% hard stop or a bear underlying; "held > 21 sessions" and "underlying below its 20-day" are review flags. The time stop is a flag. Policy caps (theme 25%, single line 15%, 3x sleeve 5%) still say TRIM. Each line now shows the 50-day rule, the sizing verdict and the advisor beside the arbiter's instruction.
Today's book under the corrected arbiter: EXIT 6 (PHPM, FLXK, KSTR, STOR -- bear regime and broken 50-day; AMD3 -43%, GOO3 -26% -- past the hard stop), TRIM 5 (ITWN, AINF, SMH -- Asia-Tech cluster 59% vs the 25% cap, ITWN also over the 15% single-line cap; TSM3, MSF3 -- 3x sleeve 12.3% vs 5%), no line HOLD because the caps bind. Section moved to the bottom of the tab.

## v1.582.0 — 2026-10-26 — BOTTOM RULE v2 (the validated rule book) across the dashboard (index v5.433)

Replaces v1.581's same-day gate framework with the rule book validated on IBKR daily bars Oct-2021..Oct-2026 (AMD/GOOGL/MSFT/TSM/NVDA/APD/SPY; ~20 confirmed events, one real bear):
- **Step 0 regime** = close vs the 200-day SMA on the underlying (never the ETP). Bull: the daily trigger alone confirms at a higher low into the EMA20/50 band (dip-buy). Bear: nothing confirms without the sequence.
- **Step 1 arm (bear, weekly)** = score >= 25 at ANY point in the last 14 days (the same-day gate never fired in five years): A-D divergence 25, RSI divergence with first low <= 40 25 (<= 30 never occurs), capitulation (vol >= 2x 50-day, close in the lower third near the low) WITH an up-day follow-through within 5 sessions 20, support touched AND weekly close back above 15, post-climax volume contraction on the retest (indices only) 15, daily RSI/Chaikin divergence 0 (worst input tested). A 14-day score history is kept per instrument in the payload.
- **Step 2 trigger (daily)** = reversal candle at the 20-day low (low within 2%, close above the prior midpoint, upper third of range), undercut-and-reclaim of the 20-day low, or close above the divergence swing high with RSI > 50. CONFIRMED only armed-then-triggered; PARTIAL = armed, no trigger (watch only). Rule 6 unchanged (close below EMA50 = falling knife).
- **3x notes** (TSM3/AMD3/MSF3/GOO3): never on PARTIAL; the test figures are printed beside each note.
- **Trend-continuation playbook regime-gated:** BREAKOUT BUY / BUY DIP become WAIT - BEAR REGIME below the 200-day; weekly hidden divergence is a continuation confirmer there only.
- **Per-stock bottom engine (230 names):** a daily divergence (rule 5) never confirms; capitulation (rule 4) only with a reversal candle (rule 1); undercut-reclaim (2) or hourly structure (3) stand. tranche_ok withdrawn otherwise (`v2_gate`).
- **KSE-100:** LIP band as the support input, reclaim ladder 164,000 -> 167,000 -> 168,000, rotation flag (CONFIRMED + fundamental green light, act at month-end), marked provisional until a PSX price history is tested.
- Dropped versus this morning: same-day gate + score >= 40, daily divergences in the score, weekly RSI <= 30, capitulation and support touch as standalones, hidden divergence and wave counts in bottom logic.

Tested: synthetic bear sequence (armed 5 days earlier, capitulation + follow-through, reversal at the 20-day low -> CONFIRMED; same bars without the arming history -> EVIDENCE BUILDING); live KSE-100 and S&P bars; full replay of the 07:55 payload (24/24 steps); jsdom render of the new card and instrument table. Live reading today: **KSE-100 BEAR, score 0, not armed, no trigger, below the EMA50 (rule 6)** -- the index is 2.8% above the band, no capitulation day, no weekly divergence; nothing in the validated rule book calls this a bottom yet. **S&P BULL: undercut-and-reclaim of the 20-day low fired, but not at a higher low into the EMA band -> no dip-buy yet.**

## v1.581.0 — 2026-10-26 — Bottom Watch v2: the evidence-graded rule set (index v5.432)

Replaces this morning's four-vote Bottom Watch with the owner's graded framework, word for word:
- **Hidden divergence out of the bottom score** — it is continuation evidence; reported as `hidden_divergence_continuation` on the weekly layer and written into the trend playbook row (`trend_pb.hidden_divergence_weekly`) as dip-buy confirmation. Wave counts removed.
- **Timeframe roles:** monthly = regime, go/no-go only (RSI <= 40 washed out +10; a monthly downtrend that is not washed out -> `MONTHLY DOWNTREND - BUYS IGNORED`); weekly = structure (RSI divergence 30, Chaikin/A-D divergence 25, higher low 15, close above 10-week 10, 40-week flat/rising 5); daily = timing (RSI divergence 10, Chaikin 5).
- **Rule 5 tightened:** the first RSI low must be <= 30; the divergence counts only after price reclaims the swing high between the lows AND RSI > 50 (`_ev_div2`). Rule 6 invalidation unchanged.
- **Volume in Wyckoff order, index only, only after a climax** (a month at 2x its 24-month median within 6 months): low-volume retest +10, expansion on the rally +10 (the trigger). Single stocks get no volume vote.
- **Zone, not a trigger:** a touch of the owner band or a monthly swing low = +10; a zone touch needs a reversal candle AND a weekly close back above the zone before G2 opens; the "first test" flag is gone (no evidence it is more reliable).
- **Gates:** G0 at least 10% off the 12-month high (no decline, no bottom); G1 weekly not in freefall (three closes under the prior week's low with the gauge falling); G2 daily price trigger (reversal candle / undercut-and-reclaim of the 10-day low / reclaim of the divergence swing high). CONFIRMED = score >= 40 (>= 50 PSX) AND G1 AND G2. States: NO DECLINE / NO SETUP / SETUP / SCORED - WAITING FOR GATES / CONFIRMED / MONTHLY DOWNTREND - BUYS IGNORED. Tranche: CONFIRMED 1.0, SCORED 0.33, else 0.
- **Instrument map:** AMD, GOOGL, TSM, APD, MSFT and the KSE-100 judged monthly -> weekly -> daily on their own bars (15 extra chart-socket calls, parallel); TSM3 / AMD3 / MSF3 / GOO3 read the SAME underlying bars (Chaikin never on the ETP), monthly/weekly as a filter only, timed on the daily trigger.
- Backtest is now a monthly-layer replay (washed-out, monthly divergence under rule 5, zone touch) and says so; weekly/daily gates cannot be replayed from monthly bars.
- Index v5.432: the card shows the five layers with points and plain-English hovers, the three gates, the score vs threshold, the drawdown pill, the sparklines (RSI 30-40 washed-out band) and the instrument table.

Tested: unit tests of rule 5 (first-low and reclaim conditions), hidden divergence, the Wyckoff volume logic on the S&P series (which has volume); live-bar run on the real KSE-100 and S&P bars; full replay of the 07:55 payload through the layer (24/24 steps); jsdom render + screenshot. Live reading on today's bars: **KSE-100 NO SETUP, score 10/50** (15% off the 12-month high so G0 is open; monthly RSI 59.7 not washed out; weekly: no regular divergence, below the 10-week, RSI 39; daily RSI divergence 10 pts, no trigger; band 2.8% below the index, not touched). **S&P: NO DECLINE** (2.8% off its high -- the 45 structure points it scores mean nothing without a fall first, which is why G0 exists).

## v1.580.1 — 2026-10-26 — first live-run fixes (index v5.431)

First live run of v1.580.0 (06:26 UTC, 6 min 07 s, all 24 evidence steps ok, KSE-100 monthly bars live: 166 months) showed three things to correct:
- **Item 36 reverted from the live M1 sort.** Demoting Zacks in the live order re-ranked the 8-name list (gold miners with IM3 95 moved ahead of ISRG/FOXA/TJX/CRM) and the trend veto then left one name (GFI). The live order is restored so the `m1_buy` ledger lane stays comparable; Zacks-as-a-tilt lives in the v2 shadow lane as designed.
- **fund_ok 13F fallback** read a field that does not exist (`n_holders` on by_ticker); it now reads `n_whales` / `n_holders` from both whale maps.
- **Bottom Watch:** the KSE-100 index carries no volume on TradingView, so the volume tile now says "no volume feed" and the state is judged on the three available votes (KSEALL volume is tried as a substitute); the RSI vote compares the gauge with its own 5-year median instead of a fixed 50 (live: hidden bullish divergence present, RSI 59.7 vs median 69.6 -> vote); the owner's 26 Oct call is seeded as ledger row one whatever the state.
Live reading after the fix: 1 of 3 available votes (RSI divergence); the index sits 2.8% above the LIP band, so the support vote fires only on a close within 2% of it.

## v1.580.0 — 2026-10-26 — EVIDENCE LAYER: the 53-item engine build plan + the 12-item KSE-100 Bottom Watch, in one scanner version (index v5.430)

One new post-processing layer (`build_evidence_layer`, 24 guarded steps, runs after the audit layer and before the side split) plus surgical fixes inside
the engines. Every new selection rule is a **shadow lane**: the old rule keeps running and keeps writing its ledger lane; the v2 rule writes a parallel
lane; promotion only when a v2 lane has >= 60 matured 63-session marks with a better median and beat rate on the cleaned ledger.
Tested by replaying the 26 Oct live payload through the audit + evidence layers with network stubs (`/tmp/r22/t1580.py`: 24/24 steps ok), unit tests of the
Bottom Watch maths (both divergence kinds, volume dry-up, support band) and of the ledger benchmark/collision fix, and a jsdom render test of the ten index
panels (`domtest1580.js`). Live sources (TradingView monthly/weekly bars, the price-context scan) are verified on the first live run.

| # | Item | Status | Where |
|---|---|---|---|
| 1 | Ledger benchmark leg from the same series; impossible marks voided (`alpha_void`, `mark_suspect`) | BUILT (113 marks voided on the live ledger) | build_signal_ledger + ev_ledger_hygiene |
| 2 | PSX lanes priced only from PSX sources; US/PSX ticker collisions voided | BUILT (3 rows) | build_signal_ledger + ev_ledger_hygiene |
| 3 | At-entry attributes stamped on every new ledger row | BUILT (175 rows today) | ev_ledger_attrs |
| 4 | TCE predictions store streams/conviction/momentum/RS/short interest/regime; shadow 2xATR exit column | BUILT | ev_tce_prediction_snapshot |
| 5 | New lanes: global_discovery (now priced), world_etf by door, bottoms:CONFIRMED_all, kse100_bottom_watch, PSX value/momentum | BUILT | ev_shadow_lanes |
| 6 | Medians only, n + horizon on every figure, 63-session at n>=20, no horizon-1; TCE edge verdict replaces the 40% winner threshold | BUILT | ev_results_v2, ev_tce_scorecard_verdict |
| 7 | PSX tracker entry_grade/pct/tier on new rows; frozen PSX rows re-priced | BUILT (new rows only; old rows keep no entry grade) | ev_psx_tracker_fields |
| 8 | Paper book charged 10 bps/side; turnover and net alpha published | BUILT (US: 198%/month one-way, gross +0.55 -> net -1.39 pts) | ev_pb_costs_and_bands |
| 9 | PSX cash gate reads metric_values from im3_detail.json | BUILT (OGDC/PPL now fail, FFC/HUBC pass; no-data 33 -> 31) | build_psx_topdown |
| 10 | Favoured filter accepts Booming; set() over dicts fixed | BUILT (unit-tested with a forced favoured list: 7 buys, no exception) | build_psx_topdown |
| 11 | SBP >= 11% trigger (A-SBP) beside the CPI trigger; 90-day rate history; 6M KIBOR - policy spread as the bank signal | BUILT (KIBOR is a dated manual constant until a feed exists) | ev_psx_regime_fix |
| 12 | Macro constants age-flagged (>45 days = placeholder) | PARTIAL: flags built; reserves/import bill still June constants (no reachable feed from the runner yet) | ev_psx_regime_fix |
| 13 | fund_ok wired to the 13F holders when the institutional consensus is empty | BUILT | build_m1_buylist |
| 14 | TCE streams.total recomputed after the analyst overlay | BUILT | derive_streams |
| 15 | M2 F6 counts only when the 30-day revision > 0 | BUILT | build_m2_watch |
| 16 | ETF tracker: perf_suspect rows cannot rank; lapsed string carries the threshold; +5% promote flag | BUILT (rank_v2 / lapsed_reason_v2 / promote_candidate; the lapse governor itself unchanged) | ev_gate_whale_discovery_etf |
| 17 | One regime table; funnel from the live pool | PARTIAL: favored_effective logged per run (meta.favored_effective_log); tables not merged | ev_psx_regime_fix |
| 18 | M1 v2: trend gate at selection, RS tie-breaker, shadow lane | BUILT (12 names; 3 of the 4 old buys fail the gate today) | ev_gate_m1 |
| 19 | Explosive CONFIRMED only above a rising 200-day and <= 25% extended; 300% base-effect flag | BUILT (7 confirmed / 13 not yet) | ev_gate_explosive |
| 20 | Zacks radar v2: rank 1 only + trend; EXIT mark on rank >= 3 | BUILT | ev_gate_zacks |
| 21 | M2 Turnaround v2: stage 1->2 base; distress vetoes | PARTIAL: base + price < $5 veto built; CFO/net-debt vetoes need statement fields not on the rows | ev_gate_m2 |
| 22 | M2 Quality v2: RS pct >= 70, within 15% of the 52-week high, Zacks < 3 | BUILT | ev_gate_m2 |
| 23 | TCE HIGH_v2 = gated intersection; attention streams display-only | BUILT (shadow tier_v2 on every row) | ev_gate_tce |
| 24 | Short interest as a cap, never a positive | BUILT in v2 (old conviction unchanged by design) | ev_gate_tce |
| 25 | Max 3 HIGH per sector; 90-day cooling-off after a HIGH loss | BUILT | ev_gate_tce |
| 26 | HIGH demoted to WATCH on MIXED / RISK OFF / broken S&P trend | BUILT (fired today) | ev_gate_tce |
| 27 | Entry verdict consumes the playbook (BOTTOM TRANCHE / WAIT FOR DIP); RS and 6-1 momentum filled for all names | BUILT (6 verdicts changed, 246 fields filled) | ev_entry_timing_playbook |
| 28 | Falling-knife bottoms need rule 1/2 plus one of 3/4/5 for a tranche | BUILT (9 confirmations held back today) | ev_bottoms_knife |
| 29 | PSX M2 / Explosive-PSX price gate; banks out of M2 | BUILT | ev_gate_psx, ev_gate_explosive |
| 30 | Recommended v2: two independent engines, modifiers only break ties, sector cap 3 | BUILT (119 -> 2 names today) | ev_gate_recommended |
| 31 | Whale: crowded demoted; filing age shown | PARTIAL: crowded flag + filing age + v2; "top-3 position for a whale" needs position weights the 13F parse does not keep | ev_gate_whale_discovery_etf |
| 32 | Discovery valuation guard + trend gate | BUILT (lane starts today) | ev_gate_whale_discovery_etf |
| 33 | World ETF door v2: value + momentum | PARTIAL: momentum leg (6- and 12-month both positive) built; country value leg needs a CAPE/P-B feed | ev_gate_whale_discovery_etf |
| 34 | Sector-relative scorecard (shadow score v2) | PARTIAL: built on the stored metric values (margins, cash conversion, FCF/sales, ROE, F-score, turnover, cover, debt, Beneish); gross profitability and asset growth not in the stored set | ev_m1_score_v2 |
| 35 | Market-multiple valuation label (P/E, EV/EBITDA percentile within sector) | BUILT (shadow, valuation_v2) | ev_m1_score_v2 |
| 36 | Zacks demoted from first sort key to a tilt | BUILT (live rule; the rank-4/5 veto unchanged) | build_m1_buylist |
| 37 | Forward-weighted Explosive score (strength_v2) | BUILT (shadow) | ev_gate_explosive |
| 38 | PSX value sleeve (earnings yield vs KIBOR, P/B, dividend; grade >= C) | BUILT (shadow lane psx_value) | ev_gate_psx |
| 39 | PSX 6-1 momentum lane, on only when breadth >= 40% | BUILT (off today: breadth 18.8%) | ev_gate_psx |
| 40 | Relative sector gate replaces "Favoured >= 62"; banks capped in buys_v2 | BUILT (shadow favored_v2 / buys_v2) | ev_gate_psx |
| 41 | Bank IG v2 PSX-relative percentiles with the NIM direction | PARTIAL: percentiles + KIBOR note built; sector-structure weights not calibrated | ev_gate_psx |
| 42 | Sector eligibility on 6-month relative return and breadth; regime table a tie-breaker | BUILT (meta.sector_gate_v2) | ev_us_regime_sectors |
| 43 | Metals: central-bank buying constant dated | PARTIAL: WGC_CB_TONNES = 690 (H1-2026 annualised, dated); ETF-holdings weekly and COT-extreme scoring not added | constant |
| 44 | Banded paper book: monthly re-rank, top-8 in / top-16 out, 25% drift bands, 10 bps | BUILT (pb_v2, NAV chain from today) | ev_pb_costs_and_bands |
| 45 | M1 sector cap 2, list of 10-12 | BUILT in v2 | ev_gate_m1 |
| 46 | One exit arbiter; candle veto never blocks an exit | BUILT (live_investment.actions) | ev_exit_arbiter |
| 47 | Time stop (under water after 42 sessions); TRIM at +25% | BUILT | ev_exit_arbiter |
| 48 | Policy targets and caps (theme 25%, line 15%, stock 5%, 3x 5%, core >= 40%) | PARTIAL: caps on the holding-level theme labels; holdings-level look-through not built | ev_exit_arbiter |
| 49 | 3x rules: 21-session max hold, -20% stop, underlying below 20-day, re-entry lockout | BUILT (lockout is advisory text; no order flow exists) | ev_exit_arbiter |
| 50 | Drawdown de-risking at -10% / -20% from peak NAV | BUILT (fires today at -17.6%) | ev_exit_arbiter |
| 51 | PSX cash-flow statements (CapitalStake / TV probe) | NOT BUILT (external key) | — |
| 52 | Narrative feed hygiene | NOT BUILT | — |
| 53 | Every tile shows n and horizon; shadow label | BUILT on the Results scoreboard; FACT/JUDGEMENT labels elsewhere not added | index v5.430 |
| K1 | KSE-100 monthly/weekly/daily bars via the chart socket, side file bottom_watch_bars.json, resample fallback | BUILT (live source verified on first run) | build_bottom_watch |
| K2 | Monthly RSI waves, hidden and regular bullish divergence | BUILT (unit-tested) | _ev_rsi, _ev_divergence |
| K3 | Monthly volume month-to-date projection vs 24-month 20th percentile | BUILT | _ev_bottom_watch_eval |
| K4 | Owner LIP band (dated) + auto swing lows + first-test flag | BUILT | _ev_bottom_watch_eval |
| K5 | Chaikin oscillator monthly + weekly divergence | BUILT | _ev_chaikin |
| K6 | Four votes -> state with a price trigger; tranche factor | BUILT | _ev_bottom_watch_eval |
| K7 | PSX market regime (KSE-100 vs 200-day, breadth) with the Bottom Watch state | BUILT (meta.market_regime_psx) | build_bottom_watch |
| K8 | Ledger lane kse100_bottom_watch, one row per state change, owner's call logged | BUILT | build_bottom_watch |
| K9 | Backtest over the monthly history (every 3+-vote month, forward 3/6/12 months, new-low rate) | BUILT | _ev_bottom_watch_backtest |
| K10 | PSX tab card: four tiles, state pill, sparkline with the band, RSI panel, history table, plain hovers; S&P twin on the US tab | BUILT | index v5.430 |
| K11 | Stock-level bottom rules 7/8 (weekly divergence, volume dry-up) | NOT BUILT (needs per-stock bars inside _bt_eval; next version) | — |
| K12 | Tranche factor on PSX buy lists | BUILT | build_bottom_watch |

Totals: 65 items — 53 BUILT, 9 PARTIAL (built with a stated limit: 12, 17, 21, 31, 33, 34, 41, 43, 48), 3 NOT BUILT (51 PSX statements, 52 narrative feeds, K11 stock-level bottom rules). Live-run verification still owed for the
two new network calls (TradingView monthly bars; the price-context scan) and for the shadow lanes' first marks.

## v1.575.0 (scanner) + signal_ledger.json (M2 seed): M2 now tested like every other engine. The signal ledger gains M2 Quality, M2 Turnaround (Tab 8b) and PSX M2 watch (Tab 3); back-filled from the dashboard git history (373 rows). First 21-session reading: M2 Quality median +1.3pp beat 53% (n=100), M2 Turnaround -1.0pp 45% (n=33), PSX M2 +0.1pp 51% (n=49). Replaces the weaker "return while listed" shortlist-tracker measure for M2 with the same fixed 5/21/63/90-session test M1 gets. COMMIT signal_ledger.json with scanner.py.

## v1.574.0 (scanner) / index v5.424 / signal_ledger.json (seed): M1 AND EVERY RECOMMENDATION ENGINE TESTED AGAINST ITS INDEX. The signal ledger is back-filled from the dashboard's own daily history in git (every second day, 1 Jul - 25 Oct 2026, 59 snapshots): 450 historical rows for the M1 buy list, Recommended top 10, PSX top-down buys, TCE HIGH, Explosive US and Zacks radar, each marked 5/21/63/90 sessions later against the S&P 500 or KSE-100 from the same snapshots. Marks are now taken only inside a 10-session window after each horizon. Results chart shows each engine with its tab and a fixed 21-session test; "PB" rows renamed "M1 buy list held as a paper portfolio (Tab 2)" / "PSX top-down buys held as a paper portfolio (Tab 3)". First reading, 21 sessions: M1 buy list median +1.7pp, beat 58% (n=36); Recommended top 10 +1.7pp, 55% (n=40); TCE HIGH +0.6pp, 51% (n=37); Explosive -0.3pp, 48% (n=62); PSX top-down -0.7pp, 41% (n=32); Zacks radar -2.5pp, 39% (n=41). COMMIT signal_ledger.json alongside scanner.py.

## v1.573.0 (scanner) / index v5.423: RESULTS TAB HEAD. Scanner publishes `results_summary`: (a) buy candidates where a fundamental engine (M1 buy list / Recommended / PSX top-down) AND the price rules (entry timing, trend playbook, held bottom) agree, with vetoes, grade, valuation, Zacks, relative strength, dip zone, breakout, exit and suggested size; (b) estate-safe UCITS funds with >= 5 engines agreeing; (c) every engine ranked by the realised alpha of what it recommended (shortlist tracker rows held >= 5 days, TCE 90-day scorecard, PB paper books, World-ETF tracker, the new ledger when it has >= 8 marks) with a 0-100 reliability score; (d) the account vs its indices. Index renders it as stat tiles, cards, an SVG reliability bar chart and an account-vs-S&P sparkline, plain-English hovers throughout. Live reading today: 0 of 5 candidates ready (all WATCH: fundamentals like ISRG/FOXA/TJX/CRM/CVX, price not confirmed); PB paper books and PSX TCE WATCH are the only engines beating their index; TCE HIGH, US Explosive, US TCE WATCH lag badly.

## index v5.422: plain-English hover text. Every technical chip and pill (market RISK ON/OFF, parity PASS/FAIL, trend chips, bottom pills, VETOED tags, trend-playbook button) now opens with a sentence a non-technical reader can act on, followed by the numbers and the engine detail.

## v1.572.0 (scanner): (1) bar_history split FIX -- trading_rules writes bar_history AFTER the side-state split, so v1.571.0 never removed it from data.json (served headroom hit 0.05 MB); it is now split right after trading_rules and carried back via the side file. (2) COT Disaggregated/TFF: live fetch worked on the first scan (CFTC columns confirmed: m_money_*, prod_merc_positions_long/short, swap_positions_long_all / swap__positions_short_all), but one shared pull reached only ~10 weeks so commodity COT indexes were null; now one server-side-filtered query per contract (700 rows each) so every leg reaches 156 weeks.

## v1.571.0 (scanner) / index v5.421 / daily.yml -- AUDIT BUILD, second batch (the rest of the 30-item plan that can be built offline) + the three issues from the 25 Oct audit.
- ISSUE 1 / ITEM 5: a holding's acquired date is the first BUY trade in the IBKR feed (GOO3 23 Oct -> 14 Oct; the decay figure moves from a meaningless -25.5pp to -1.9pp); new positions from the Flex statement take their first trade date, not the statement end. PHPM estate label: NON-US ETC (not UCITS).
- ISSUE 2: bar_history (0.47 MB, scanner-only state) moved to the side file bar_history.json; served payload headroom rises from ~0.3 MB to ~0.75 MB.
- ISSUE 3: meta.market_regime.horizon_note reconciles the 200-day regime with SPY's 50-day trend state; when RISK ON but SPY trend BROKEN, bottom tranches are marked first-tranche-only.
- ITEMS 16-17 COT Disaggregated (72hh-3qpy: managed money, producers/merchants, swap dealers for WTI, Brent, NatGas, gold, silver, copper, Pt, Pd) and TFF (gpe5-46if: asset managers, leveraged funds, dealers for ES, NQ, RTY, YM, 10yr, VIX, USD Index): net, % OI, 156-week COT index and percentile per leg, extremes flags; refetched Sat/Sun/Mon or when older than 3 days, carried otherwise; column names matched from candidate lists and the ones seen are published (`columns_seen`) so a mismatch is visible. Decision hooks as flags: psx_topdown.ep_cot_check (E&P overweight flagged when WTI producers <=10 and managed money >=90), macros.metals.cot_flags. Strip line added.
- ITEM 18 meta.discovery: dropped TradingView-gap names by name, and the foundation names that reached neither the M1 pool nor the Explosive screen.
- ITEM 20 PSX engine names (48) enter the bottoms universe via TradingView PSX daily bars (BT_PSX=0 disables); coverage note updated.
- ITEM 25 meta.threshold_sensitivity: publishes hit rate and alpha by entry RSI band once the ledger has 100 rows marked at 21 sessions; says 'collecting' until then.
- ITEM 30 Bollinger-width squeeze flag on the chart names (informational).
- NOT BUILT: item 24 (Explosive-PSX statements for the 33 no-data names needs a PSX financials source), AINF/STOR issuer holdings and TSM3 NAV backfill (item 5 remainder). Live sources untested from the sandbox: the two CFTC datasets (column names verified against the published API at first live fetch), TradingView PSX bars.
## v1.570.0 (scanner) / index v5.420 / daily.yml -- AUDIT BUILD (research report 2026-10-24, master plan items). Built, tested offline against the live 23 Oct payload (every step ok), regression suite green.
- ITEM 1/11/29 Universal signal ledger `signal_ledger` (+ side file signal_ledger.json): every BUY/BUY NOW, BREAKOUT BUY/BUY DIP, bottom CONFIRMED (tranche ok), M1 buy, recommended top-10, Zacks radar, Explosive US/PSX, PSX top-down buy, TCE HIGH/WATCH, whale consensus buy, global discovery pick; one row per (engine, ticker) per 30 days, append-only, forward return and alpha vs SPY/KSE-100 at 1/5/21/63/90 sessions, per-engine summary. 164 rows on day one from the live payload.
- ITEM 2 `benchmarks` daily series (SPY, QQQ, ACWI, SOXX, EWT, EWY, GLD, KWEB, IWM + KSE100) from the TradingView scanner, same day as the pick prices; carried 400 days.
- ITEM 3 Reconciliation (`meta.reconciliation`): M1 buys vetoed when exit says EXIT, trend_pb BROKEN or bottoms AVOID (live payload: TSM, MU, GOOGL, LRCX vetoed; ISRG, FOXA, TJX, CRM kept, originals in buys_vetoed/buys_before_veto); recommended rows with trend zone broken/stand flagged (56 live); every Tab-17 holding gets ONE verdict (exit rule governs hold/sell).
- ITEM 4 `live_investment.relative`: ONE flow-adjusted since-inception return (Modified Dietz on IBKR flows; live -13.93% from 2 Jul) vs SPY/QQQ/ACWI over the same window, 1w/1m/3m windows; shown on Tab 19 and the strip.
- ITEM 5 (part) SMH N-PORT no longer matches the VanEck FABLESS fund (`_NPORT_NAME_EXCL`). Not done: AINF/STOR issuer holdings, GOO3 acquired date, TSM3 NAV backfill, PHPM estate label.
- ITEM 6 `live_investment.leveraged`: per 3x note product return since entry vs 3x underlying (TSM/AMD now in the chart set so all four fill from the next scan; live: GOO3 -26.9% vs 3x GOOGL -1.3% = -25.5pp decay), notional exposure 1.25x market value, cluster shares of notional.
- ITEM 7 `plan.size_vol_usd` on timing rows: 0.5% of NAV per ATR14 move, capped at the plan size (fills where ATR present).
- ITEM 8 `meta.market_regime` (SPY vs 200-day from its own timing row, breadth = % of timing names above the 50-day; live RISK ON at 50.3%); RISK OFF halves bottom tranches and downgrades BUY NOW to BUY (annotated, never silent). Header chip "market RISK ON/OFF".
- ITEM 9 Bottom engine strict (BT_STRICT=1): CONFIRMED needs rule 2, 3 or 4; a lone reversal candle or RSI divergence is WATCHING with the flag.
- ITEM 10/27 `meta.content_age`: manual constants (SBP reserves, import bill, CMO Arab Light month, OSP differential) and the superseded psx_valuation_matrix carry their own age rows (live: 2 late).
- ITEM 12 PSX top-down strict (PSX_TOPDOWN_STRICT=1): buys only from favored sectors; empty favored -> buys withheld (candidates kept in buys_all_candidates); bank buys get a FIPI outflow warning.
- ITEM 13 Narrative-tab / News votes weigh 0.25 in the recommended conviction count.
- ITEM 14 COT: commercial leg (comm_long/short/net/pct_oi) from the same Socrata rows, 156-week COT index + percentile on both legs, `extreme` flag at >=90 / <=10. Not done: release-aware gate, Disaggregated/TFF feeds (items 16-17; column names need a live probe).
- ITEM 15 Mansfield RS vs S&P (60-session) and 6-1 momentum on the 47 chart names; BUY NOW with RS<0 downgraded to BUY.
- ITEM 19 watch-list seeded ytd/ret_1y moved to *_seed when no live figure (22 rows live).
- ITEM 21 `meta.regime_history` (market, M1 regime, PSX regime, breadth) per scan.
- ITEM 22 Reference fixes (GOOGL/GOOG names, LRCX sector, XOM name) + `meta.reference_check` mismatch list.
- ITEM 23 exit_rules RSI filled from the bottoms engine when null (11 live).
- ITEM 26 `macros.us.arab_light_dual` and `cpi_dual` with basis and which value the trigger reads.
- ITEM 28 theme benchmark per holding (`theme_bench`, return since entry fills as the benchmark series accrues).
- NOT BUILT (needs live sources or a decision): 16-17 COT Disaggregated/TFF + decision hooks; 18 discovery repair (ADR path); 20 PSX OHLC via TV socket; 24 Explosive-PSX statements; 25 walk-forward thresholds (needs the ledger to accrue); 30 squeeze/VWAP/ML. Dashboard rendering of the ledger per tab is a summary line on the run-health strip for now.
## v1.568.0 (scanner) / daily.yml / index v5.416 -- DASHBOARD-WIDE AUDIT BUILD. (1) Size governor judged the 9 MB ceiling on the payload BEFORE im3_detail (1.7 MB) is split out, so it reported "ceiling breached" every run while the served data.json is 8.7 MB; now judged on the served size, `served_total` and `headroom_mb` published. (2) "Changes since last scan" never showed buy-list changes made by the scoring step restamp (the 23 Oct forced rescore swapped 3 of 8 buys and the line said none): the scanner records `prev_buys`, the scoring step finalises added/dropped after its re-arbitration. (3) Scoring health: `legacy_yahoo_labels` (58) renamed to `yahoo_served` -- Yahoo is the intended source since v1.553.0; the strip shows "Yahoo-served". (4) `score_health.no_detail` names the ~32 scored names with no IM3 detail that the self-heal keeps counting. (5) index header comment (still read v5.409) brought up to date. Includes v1.567.0 news prefetch.

## v1.567.0 (scanner): justETF cache CONFIRMED live (30 calls, 0.8 s, was 20-24 s) -- but live_lookthrough rose to 32 s, which exposed the other cost: ~70 Google News RSS fetches (5 holdings + exchange + theme per fund) made one after another. They are now prefetched 8 at a time into a per-run memo (`meta.fetch_profile.lt_news_prefetch` reports count and ms). Expect live_lookthrough to land near 5-8 s.

## v1.566.0 (scanner): force guard FIX -- the scoring step wrote `im3_last_full_utc` into data.json, but the next scanner run rebuilt data.json without it, so the guard never saw a stamp (two forced full passes 15 min apart on 23 Oct both ran). The scanner now carries the stamp from the previous payload. (justETF cache confirmed written by v1.565.0; saving lands on the next scan.)

## v1.565.0 (scanner): BUG FIX to v1.563.0 -- the justETF cache was copied into data right after the explosive block, but live_lookthrough (which fills it) runs later, so justetf_cache.json was never written and live_lookthrough stayed at ~20-24 s. The copy now happens inside the side-state writer at the end of the run. Verified offline: the side file is written and re-read on the next load.

## v1.564.0 (scanner) / index v5.415: BOTTOM HOLD TEST. A confirmation now carries `signal_date`, `hold_pending` (the signal is the latest settled bar -> FIRST tranche only), `held_sessions`, and loses `tranche_ok` if any later session closed below the signal low. Three or more holdings confirming on the same session get a `cluster` note (one correlated move, size as one position). Pill: amber "BOTTOM CONFIRMED · 1st TRANCHE ONLY, HOLD TEST PENDING" on the signal day, green "held Nd" after, "CLUSTER" tag when correlated. Built after 4 of 6 same-day confirmations on 21 Oct failed their hold on 22 Oct.

## v1.563.0 (scanner) + daily.yml: justETF holdings cached across runs (side file justetf_cache.json, 6-9 day TTL per ISIN, misses retried daily): live_lookthrough should fall from ~22 s to ~1-2 s from the second scan. `meta.macro_fetch_profile` times FRED series pulls, TradingView econ, TradingEconomics and TIC inside fetch_us_macros so the 73 s spike is readable if it repeats. Leveraged-line drift, force guard, bottom holds: nothing to build.

## index v5.414: Tab-19 bottom pill now appends "NO TRANCHE" when the engine itself has withdrawn the add (tranche_ok false: the session after the reversal candle broke its low) and "thin vol" when the confirming signal printed on thin volume. The CONFIRMED label alone was reading as a buy on SMH and AINF where the engine said no further tranche.

## v1.562.0 (scanner): explosive_us ROOT CAUSE (profile proved fetches were only ~5 s of 46 s): `_build_explosive_rec` fell back to a full SEC companyfacts GET for every name stockanalysis cannot serve (~166 of 350) on every run. The SEC quarterly series is now cached 40-50 days in the Signal-T side file (`secq:<ticker>`, dated) -- expect explosive_us to fall by ~30-40 s from the second run. `meta.explosive_profile` adds secq_fetch_n/ms and secq_cache_hits. `meta.fetch_profile` times the five fetchers inside live_lookthrough / discovery_holdings (ishares, justetf, etf holdings, US and foreign analyst blocks) so those 22 s stages can be read next. TIMB/VIV/VOD unchanged (owner decision). Force guard: no change (awaits a live full pass).

## v1.561.0 (scanner): (1) AAPL/APD + all holdings now in the daily-close chart set, so their EMA50 slope is real on day one. (2) explosive_us profiled: the statement cache hits 97% (339/350), so the time is the Signal-T stockanalysis fetches -- up to 30 retries per run of names that returned empty before, each a live page fetch; budget cut to 8, and `meta.explosive_profile` now publishes fetch counts and ms (stockanalysis vs SEC) every run. (3) Parity warning names the names neither SEC nor Yahoo serve (VOD, TIMB, VIV today); they stay in the pool, scored from the history path. (4) Force guard verified offline on 5 cases: ticked box <20h after a full pass -> incremental; >20h or no stamp -> full; FULL_RESCORE=true -> full even inside 20h. (5) MSF3: nothing to build.

## v1.560.0 (scanner) / daily.yml / index v5.413: (1) FORCE GUARD in the scoring step: force_im3 within 20h of the last full re-score runs incremental (stamp `im3_last_full_utc`; FULL_RESCORE=true overrides; `scoring_entry.force_suppressed`). (2) tail_builders profiled: the 39 s radar_m1_m2 bucket was 36.5 s of m1_buylist = three names Yahoo could not serve (VOD, TIMB, VIV) x 3 retries with 1.5/3/4.5 s back-off; back-off cut to 0.6/1.2/1.8 s (~22 s saved); momentum_signals, psx_m2_watch and m1m2_etf_proxies now timed as their own stages. (3) Trend playbook: rising-EMA50 test now computed from the stored daily closes where present (top-40 chart names), so it no longer waits 4 days for those. (4) Tab 19 NAV line shows how old the scan prices are and names the leveraged lines that drift 1-2% from IBKR between scans; live prices in the page are not possible (no browser-side price source). (5) BRK.A/BRK.B/PBR.A/SHEL/CVS: accepted as-is (owner decision pending; nothing built).

## v1.559.0 (scanner) / index v5.412: TREND-CONTINUATION RULESET on every tab. Scanner: `entry_timing.rows[t].trend_pb` (state TRENDING / BROKEN / BOTTOMING, action BREAKOUT BUY / BUY DIP / IN DIP ZONE / TREND - WAIT FOR DIP / STRETCHED - DONT CHASE / TREND BROKEN, dip zone EMA50-EMA20, breakout level, exit below EMA50, trailing stop = tighter of EMA50 and close - 2 x ATR14) plus `entry_timing.trend_summary`; ATR via a separate best-effort TradingView call; owner holdings + AAPL/APD/LLY always carry a row. Rising EMA50 uses the stored daily history (4+ days), until then EMA50 > EMA200. Index: a chip after every ticker on every tab (decorates text nodes that are tickers; hover shows levels) and a "trend playbook" panel from the header. Limits: higher-low and green-reversal use the last two bars only; BOTTOMING names get no chip.

## v1.558.0 (scanner): Yahoo is the IM3 source for every name SEC cannot serve. Share-class tickers are now sent to Yahoo with a hyphen (BRK.B -> BRK-B, PBR.A -> PBR-A) -- the likely reason Yahoo "returned nothing" for BRK.A, BRK.B and PBR.A. TradingView-only shadow test switched OFF (IM3_TV_ONLY_TEST=1 re-enables) after 0 of 8 names came within 0.5 points (mean shift 13.5).

## v1.557.0 (scanner) / index: SHADOW TEST `meta.im3_tv_only_test`: 8 Yahoo-served names per scan (rotating) are also scored from TradingView annual history alone and compared with their published score; nothing published changes. Verdict flips to PASS only at >=20 names with >=90% within 0.5 points. IM3_TV_ONLY_TEST=0 turns it off. Validated offline: routing (SEC and Yahoo skipped, only tv_history called, flag/state restored) and the whole block executed in isolation; live validation needs the runner (TradingView is blocked from the sandbox).

## v1.556.0 (scanner): BUG FIX. The v1.553.0 edit left the old `src == yahoo` clause in the M1 force-rescore rule, so all 50 Yahoo-labelled names (plus 3 history-path names) were re-fetched on EVERY scan: m1_buylist 111-113 s, tail.radar_m1_m2 98-116 s, ~3 min on the workflow. Yahoo labels are now the target state; history-path names retry once per day. Expect m1_buylist to drop to ~15-30 s from the next scan.

## v1.555.0 (scanner): real cadences for amc_fmr, psx_valuation_matrix, cot_futures (7 days), measured from the data.json git history (19 sampled scans). sec_filings runs on a 20h window by design and explosive_us fell back to 36 s, so no profiling cut was justified.

## v1.554.0 (scanner) / index v5.411: Yahoo statement fetch retries 3x with back-off (2 of 30 names came back empty); one-time rescore backlog clears in one scan (budget up to 60); block cadences LEARNED from each block's own as_of changes (`meta.block_obs`), `meta.block_ages.all` lists every dated block; header parity chip opens a data-age table with age, cadence and tab for every block. NOT done: entry_timing split (saves 0.73 MB, touches the EXISTING merge and daily.yml) and scorer merge (would change scores, conflicts with the parity target).

## v1.553.0 (scanner) + requirements.txt: OWNER-AUTHORISED Yahoo RETURN for IM3 statements of names SEC cannot serve (XOM, CVX, COP, PSX, ABEV, BHP, BTI, banks...). Measured: stockanalysis/TV substitute shifted scores 3.4 pts on average vs the last Yahoo scan (55% of names within 0.5), so the 0.5% bar was unreachable without Yahoo. Order: SEC (unchanged) -> Yahoo -> history path only if Yahoo fails. SEC gap-fill and path comparator switched OFF by default (IM3_SEC_FILL=1 / IM3_PATH_COMPARE=1 re-enable) because the fill moved SEC names away from their Yahoo-era scores. The 55 history names and the 11 filled SEC names rescore once (marker 553). requirements.txt gets yfinance back.

## v1.552.0 (scanner): live v1.551.0 comparator showed AFRM fixed by the fill but ABNB capex/fcf and AMG operating income still NA on SEC because those rows were sparse, not empty. Fill now replaces SEC rows with <3 years when history has more; Operating Income, Net Income and Total Revenue added to the filled rows. Names rescore once more (marker 552).

## v1.551.0 (scanner): live comparator after v1.550.0 showed the remaining gaps are SEC-side NA rows (ABNB capex/fcf/eps, AFRM/AMG receivables) -- SEC-path names lacked scorecard rows Yahoo used to supply. `_fill_sec_gaps` fills a row from stockanalysis/TV history only when the SEC row is entirely empty and history has >=3y; filled rows are listed in the audit (`fill`). The 74 sec+tv names rescore once (30/run).

## v1.550.0 (scanner): live path comparator (12 rows) showed the history path loses rev/op/np CAGR (4-5 fiscal years vs 6) and net_cash (no cash-flow line). Fixes: CAGR over the longest available span (>=3y) on the history path only; `Changes In Cash` derived from balance-sheet cash. The 55 stockanalysis+tv names rescore once (30/run). Comparator history now one row per name per day.

## v1.549.0 (scanner): path comparator also lists the metrics whose verdict differs between SEC and history paths (`diff_metrics`), to find why the history path scores ~2.5 pts lower (live n=4: mean abs 3.8).

## v1.548.0 (scanner): `meta.im3_path_compare` rotates 4 SEC-scored names/run through the stockanalysis+TV history path and publishes deltas (history keeps 60 rows) + parity check `im3_history_vs_sec_mean_abs_delta`.

## v1.547.0 (scanner) / index v5.410 / daily.yml
- M1: `m1_buylist.score_health` (attempted, ok, failed names with reason, source mix, legacy yahoo labels, scores older than TTL); each scored row carries `im3_src` (shown as a tooltip on the grade).
- `meta.changes`: buy-list adds/drops and cash-gate flips versus the previous scan.
- Parity guard gains 4 checks (fresh-rescore success, legacy Yahoo labels, stale scores, Yahoo last-resort answer rate; WARN status) and `meta.yahoo_residual_hist` keeps 30 runs.
- daily.yml `scoring_entry` now records `reason`, `detail_missing`, `n_universe` (answers why a full rescore ran).
- index: header chip (parity, warnings, late blocks) on every tab; run-health strip shows M1 scoring health and the changed-since-last-scan line.

## v1.546.0 (18 Oct 2026)
- FOUND on the v1.545.0 live scan: 46 m1_im3_audit entries still 'yahoo' and only 2 of 30 fresh rescores succeeded. The scanner's M1 scorer (_fetch_im3_data) had NO fallback after SEC (v1.528.0 removed Yahoo there, and the stockanalysis/TradingView tiers exist only in im3_score.py). Names SEC cannot serve (foreign 20-F filers, and US names without OperatingIncomeLoss such as XOM, CVX, COP, PSX, banks) were frozen on their pre-cutout scores.
- _hist_im3_statements: those names now fall back to im3_score's stockanalysis three-statement history (then TradingView *_fy_h for empty series), mapped to the same Yahoo-shaped frames; source labelled 'stockanalysis+tv'. Rows the history lacks (shares outstanding, minority interest, change in cash) stay NA, so the scorecard max can be lower than on the SEC path.
- The 11.9 s 'unmeasured' stretch before run_tce_us is the short-interest / revision-bridge / Yahoo-residual block, not the FINRA downloads: the Yahoo last-resort calls now run six at a time.
- m1_buylist: the per-name sleep was 0.7 s (YF_DELAY*2, a Yahoo-era delay) x 30 fresh scores; now 0.15 s.
## v1.545.0 / index v5.409 (18 Oct 2026)
- KPMG bank-sector block: the Banking Perspective is ANNUAL, so its age is judged against when the next edition is due (as_of + 485 days), not its year-end. The CY2025 edition (latest published) is no longer flagged as 291 days stale; it turns amber/red only once the next edition is overdue.
- s8 interim short interest: SHADOW nowcast (last FINRA short interest scaled by the newest-5 vs 10-session Reg SHO short-volume share, clamped 0.85-1.20) published in meta.short_interest.nowcast with the names that would cross 8 percent. Not used by s8. When the next FINRA file arrives the previous nowcast is scored (meta.short_interest.nowcast_scored, mean error in points) so it can be switched on, or dropped, on evidence.
- m1_im3_audit: entries still labelled 'yahoo' are force-rescored first, up to the per-run budget (30), until none remain.
- meta.block_ages: every dated block's age against its own refresh cadence; shown as chips on the Run health strip.
- Speed: the 10-14 FINRA short-volume downloads run concurrently, and FINRA short interest, TradingView float and short volume are fetched together (about 11 s of unmeasured serial time before run_tce_us).
## v1.544.0 / index v5.408 (18 Oct 2026)
- moat_cover: the carry gate demanded >=50 holdings from IVV, ITOT, KBE and QUAL, which return 0-2 for good, so the 7-day cache was never used and 59-72 s was spent every scan. A target already attempted now counts; a new target still forces one refresh.
- PSX market watch: dps.psx.com.pk/market-watch answers 404 to the runner (carried a 24 Sep copy). fetch_psx_market_watch_tv rebuilds the same table from TradingView's Pakistan scan (index memberships and sector carried from the last good copy), source labelled. Falls back to the carried copy only if TradingView also fails.
- FINRA: meta.short_interest.age_days / stale (>25 days warns); shown on the strip.
- s9: streams.s9_source (yahoo_last_resort | tradingview_eps | tradingview_other); the EPS-rev cell marks Yahoo-sourced values with *.
- PAYLOAD_SOFT_CEILING_MB 7.5 -> 9.0.
## v1.543.0 (18 Oct 2026)
- Live v1.542.0: Yahoo answered 26 of 30 asked names from the runner, parity 8 PASS + 1 WARN (s9 share 0.459). 4 Yahoo flips (CBRS, LRCX, RGNX, SATL) were still overridden by TradingView's consensus-down vote; the Yahoo up>down breadth now replaces eps_primary for those names. Scanner 258 s run + 74 s final stages.

## v1.542.0 / index v5.407 (18 Oct 2026)
- Live audit of v1.541.0: parity FAIL on tce_us_s9_share (0.351 vs 0.514 baseline, floor 0.385). Cause: removing Finnhub dropped 5 flags absent from the Yahoo-era list (CSCO, MSFT, NVDA, OABI, PLTR) plus ASPI (a Yahoo-era name). Matched 13 of 19 comparable Yahoo names, 13 of 14 flags are Yahoo-era names. The 6 misses (APLD, ASPI, CBRS, LRCX, RGNX, SATL) have flat or falling consensus: Yahoo counted individual analysts, no TradingView field does. Step-count, up-only and 45/60-day variants all tested worse.
- s9 LAST RESORT (owner permission 18 Oct): fetch_yahoo_s9_residual, Yahoo earningsTrend epsRevisions up/down 30d, asked only for names TradingView did not flag, fail-open (no crumb / 401 / 403 / 429 leaves s9 TradingView-only), 60 s budget, YAHOO_RESIDUAL=0 turns it off. Published as meta.yahoo_residual. Not testable from the sandbox (Yahoo blocked there): unit-tested with a stubbed session only.

## v1.541.0 / index v5.406 (17 Oct 2026)
- s9: Finnhub recommendation and earnings-surprise legs removed from the revision bridge (28 of 88 calls were HTTP 429); s9 is TradingView-only. Old cached rec/surprise votes no longer count.
- index v5.406: "Yahoo replacement" strip under Run health (parity verdict and 9 checks, s8 FINRA file and coverage, s9 bridge counts, TradingView socket run).
- Measured and NOT changed: s9 threshold sweep (0.05% to 1%) lost matched Yahoo-era names faster than it removed extras (13 hits at 0.05%, 9 at 0.2%, 6 at 0.5%), so 0.05% stays. data.json (8.16 MB) has no lossless saving large enough for 7.5 MB (nulls about 0.2 MB); no displayed content was dropped.

## scanner v1.540.0 -- audit of the live v1.539.0 scan (16 Oct 2026)
- Live v1.539.0 result: s8 on FINRA short interest works (file 2026-09-30, pipe-delimited, 44 names, 43 with a percent); s8 name overlap 0.73 (all 4 missing names are no longer in the TCE pool); s9 FAILED (0.341 vs 0.375): rating-change votes cancelled real EPS raises (XOM +9 percent, CVX +3.3, AAPL +0.2 had net 0).
- Fix: a forward-EPS consensus change beyond +-0.05 percent decides s9 on its own (`eps_primary`); rating, price-target, NTM and surprise votes are used only when there is no EPS signal.
- The dashboard's own `estimate_history` snapshots (622 names, weekly then daily, 25 dates) are merged in as extra baseline, with `fwd_eps_seed.json` and the stored history.
- Parity: s8 and s9 shares are measured on names that were in the Yahoo-era pool AND are in today's pool (3 Yahoo-era s9 names left the pool), against the Yahoo-era flagged share of those same names. Simulated on the live 16 Oct pool: 15 flagged, 13 of the 19 comparable Yahoo-era names (recall 0.68), share 0.395 against a 0.375 floor.

## scanner v1.539.0 -- s9 from the 30-day change in TradingView consensus forward EPS (16 Oct 2026)
- Recovered 21 daily snapshots of `streams.fwd_eps` (TradingView next-quarter consensus EPS) for 80 tickers from the repo's own data.json history (643 commits back to 22 Jul) and ship them as `fwd_eps_seed.json` (place it in the repo root). The scanner merges the seed into `fwd_eps_hist.us` once; stored values win on shared dates. A 30-day window therefore exists on day one instead of 15 Nov.
- `_tv_fwd_votes`: consensus forward EPS up more than 0.05 percent over about 30 days is an up vote, down more than 0.05 percent a down vote (s9 = up > down and up > 0, unchanged). Back-test on the 44-name pool against the v1.526.0 Yahoo-era s9 names: 15 flagged, 13 of them Yahoo-era (precision 0.87, recall 0.59), against 19 flagged and 10 matched with the earlier proxy.
- Quarter-roll guard: `earnings_release_date` added to the US analyst pull; snapshots dated on or before the latest report are not used as a baseline, because the next-quarter estimate changes identity at a report, not value.
- EPS-surprise beats no longer vote (information only: `meta.revision_bridge.surprise_beats_info_only`). They produced the 9 false s9 flags.
- Still running in parallel: rating-change vote (Finnhub), price-target / buy-share / NTM EPS / NTM revenue snapshot votes (from 18 Oct).

## scanner v1.538.0 -- s8 on real short interest, honest parity (16 Oct 2026, self-audit of s8/s9)
- FAULT: s8 used FINRA daily short VOLUME (a market-maker flow figure around 50 percent for every stock) with a cut-off set to the top third so the share matched Yahoo's 34 percent. It passed the parity count by construction while only 6 of the 15 Yahoo-era names matched (XOM, a 1 percent short-interest stock, was flagged). The comment 'not published by any source we hold' was wrong: FINRA publishes consolidated short interest twice a month at cdn.finra.org/equity/otcmarket/biweekly/shrtYYYYMMDD.csv.
- FIX: `fetch_finra_short_interest` (newest of the 15th / month-end files that parses, delimiter sniffed, header-named columns), float from TradingView (`fetch_tv_float`: float_shares_outstanding, else total x float percent), s8 = shares short / float >= 8 percent, the same rule Yahoo fed. The volume proxy runs only if the whole short-interest download fails. Diagnostics in `meta.short_interest` (files tried, header, delimiter, names covered).
- Parity guard now also compares NAMES: `tce_us_s8_name_overlap` / `tce_us_s9_name_overlap` against the v1.526.0 flagged sets (WARN below 0.6). Counts alone let a different signal pass.
- s9 findings recorded, not yet changed: the 9 'new' s9 names are all driven by TradingView EPS-surprise votes (a beat is not a revision); Finnhub surprise and rating legs were empty for every name; the price-target / NTM EPS / NTM revenue snapshots have one day of history until 18 Oct (a clean 30-day window on 15 Nov).

## IM3 v2.36.0 -- TradingView statement history (16 Oct 2026)
- Found by the widened v1.537.0 discovery on the runner: TradingView serves ~20-year ANNUAL arrays (newest first) in `*_fy_h` columns -- total_revenue, net_income, earnings_per_share_diluted, ebitda, free_cash_flow, total_assets, total_debt, gross_profit -- and 20+ quarters in `*_fq_h`, plus `earnings_fq_h` / `revenues_fq_h` (Actual vs Estimate per quarter). No key, no quota.
- `tv_history(ticker)`: last tier after SEC and stockanalysis for names with under 3 years of revenue (source `tradingview`). `_tv_fill`: fills only EMPTY series (EPS, EBITDA, FCF, assets, debt, COGS) of an SEC/stockanalysis history; never overwrites, so SEC/stockanalysis-served scores are unchanged.
- Why-string now ends with the TradingView reason.

## scanner v1.537.1 (16 Oct 2026)
- The weekly TradingView discovery cache is now versioned: the live v1.537.0 scan reused the 15:20 UTC result, so the widened short-interest/float/growth search had not run. It runs on the next scan, then weekly.

## scanner v1.537.0 -- 100%-TradingView s9 (16 Oct 2026, from the live v1.536.0 discovery: 120 of 136 analyst fields serve)
- s9 now also votes on TradingView consensus snapshots: `eps_estimate_ntm` and `revenue_estimate_ntm` (both proven served) added to the US analyst pull, kept daily as `fwd_eps_hist.us_ntm` / `us_rvn`, +-0.5 percent against the baseline is a vote (`_tv_estimate_votes`).
- Snapshot baselines (price target, buy share, NTM EPS, NTM revenue) open after 2 days instead of 5.
- Discovery widened to short interest / float / ownership / growth / CAGR / history style field names (900 candidates, 1 sample value each) so a TradingView short-interest or multi-year column, if one exists, shows in `tv_discovery.serving`.

## scanner v1.536.0 / IM3 v2.35.0 -- TradingView-only (owner decision 16 Oct 2026)
- FMP and its quota removed: scanner bridge no longer calls FMP, IM3 `FMP_KEY` hard-off, `FMP_API_KEY` env lines removed from daily.yml (3). IM3 history tiers are now SEC -> stockanalysis (FMP never served in the IM3 step before v1.530, so no regression).
- New `build_tv_discovery`: weekly, reads TradingView `metainfo`, tests every analyst/estimate/revision/surprise-looking field one by one, publishes `data.tv_discovery.serving`. Daily, fetches the proven surprise columns (`eps_surprise_percent_fq` etc.) for the US pool; a surprise of 5 percent or more adds one s9 vote (`tv_up`/`tv_down`), alongside the price-target and buy-share snapshots.
- Finnhub (free key, no daily cap) stays as a secondary vote source; remove `FINNHUB_KEY` to make it purely TradingView.
- Retired tests (they asserted FMP behaviour): b27/test_v1531, test_v1532, test_v1535 FMP legs, test_im3_v232/v233.

## v1.535.0 — 16 Oct 2026 — measured on the live v1.534.0 / IM3 v2.34.0 scan
Live result: the stockanalysis URL fix WORKED -- in the shipped file only 5 explosive_us names have no statement history (AADX, AVEX, BMNP, GAU, HAWK: 2-year listings or a 404; baseline 5) and 41 names are served by stockanalysis; XOM, PBR, SNDK, ALAB, MRVL, KNSA, AYA, CAI, SLDE now score. The parity guard's "46" was the PREVIOUS run's IM3 rows (the guard runs before the IM3 step) counting a name once per section.
- Parity guard: counts unique tickers; daily.yml re-measures the IM3 row on the merged records right after the scores are written, so `meta.yahoo_parity` reports what is shipped (`measured: after IM3 merge`).
- s9 (13.6% vs 50%): FMP answered HTTP 429 again (free plan, daily quota already spent), so only the Finnhub trend vote ran. Added a second keyless-of-FMP Finnhub vote: the latest reported quarter's earnings surprise within 120 days, +5 points or more = up, -5 or less = down (analysts revise toward the surprise within weeks). Bridge entries fetched while FMP was down (or without the surprise leg) are retried the next day instead of being frozen for 3 days. `tv_votes` was being overwritten by the stats block; fixed so the TradingView snapshot votes are visible from 21 Oct when 5 days of snapshots exist.
- Probe answers (Finnhub, from the runner): `stock/financials-reported` works -- XOM 16 filings, GORO 15, revenue concepts us-gaap_Revenues / RevenueFromContractWithCustomerExcludingAssessedTax, 18-33 rows per statement -- but returns nothing for MWH and VMET (recent listings). `stock/metric` serves 41-point annual series (salesPerShare, eps, ebitda, margins, roe, roic). TradingView serves price_target_high/low/median, recommendation_hold/sell/over/under, total_revenue_yoy_growth_fy/fq, last_annual_revenue/eps, earnings_per_share_forecast_fq. Kept in reserve (not wired): Finnhub statements as a fourth history tier for names SEC/FMP/stockanalysis all miss.
- Time (v1.534.0): scanner 330s, post 93s, workflow wall 659s (758s the run before, 584s pre-cut); outside the scanner and post stages the IM3 steps still cost ~236s while the stockanalysis cache warms (30-day positive and 7-day negative cache from this run on).
- Tests: test_v1535 (8) added; all earlier suites pass; the workflow's embedded Python compiles.

## v1.534.0 / IM3 v2.34.0 — 16 Oct 2026 — research-first fixes (owner: "research alternatives first, test, then render")
Network reality: the build sandbox is policy-blocked from TradingView, SEC, FMP, Finnhub, stockanalysis, FINRA and Nasdaq (CONNECT 403), and has no GitHub push access, so nothing here could run against those hosts. What WAS verified, by loading the live public pages through the fetch tool: stockanalysis page structure (all three statements, XOM and VMET) and SEC companyconcept records for XOM.
- ROOT CAUSE of the stockanalysis tier failing for every name: `_SA_US_INC` pointed at /financials/, which is the Financials OVERVIEW page (11 summary rows, 3-6 columns). The statement is /financials/income-statement/ (27-33 rows incl. Revenue and EPS (Diluted)). Corrected. Tax label corrected to "Income Tax Expense" (was "Provision for Income Taxes"); the page has no EBITDA row, so EBITDA is derived as operating income + D&A (same as the SEC path). Every mapped label was checked against the real row lists.
- SEC extractor `_sec_annual` returns the right five years on real-structure XOM records, so XOM's earlier "0 annual values" was not a parsing bug (likely a throttled or partial companyfacts reply); the tier now logs the reason.
- s9 without any key: TradingView snapshots of the average price target and the buy share of analysts are kept daily (fwd_eps_hist us_pt / us_rec) beside forward EPS; the comparison window opens at 5 days (was 20) and converges on a 30-day window; price target moved >1% or buy share moved >2 points casts a vote (`meta.revision_bridge.tv_votes`). FMP and Finnhub votes stay as extra inputs.
- Probe v1.534.0 (re-runs once, then weekly): looks inside Finnhub `stock/metric` (series.annual names and lengths) and `stock/financials-reported` (filings, statement rows, revenue concepts) which the old probe wrongly marked "not ok" because their numbers are nested; adds the small-cap names SEC cannot serve (MWH, VMET, GORO) and 12 more TradingView analyst/growth columns. The next payload answers whether Finnhub statements can replace SEC/FMP for IPO and small-cap names.
- Tests: test_v1534 (13) and test_im3_v234 (24, labels checked against the real pages) added; all earlier suites pass.

## v1.533.0 / IM3 v2.33.0 — 16 Oct 2026 — second live-scan fixes (v1.532.0 scan: PSX bars now PASS)
Live v1.532.0: PSX bars 48/48 PASS (backfill served 35 names, ~+15s once; they are now stored). s9 13.6% (base 50%) and IM3 no-history 48 still FAIL. Wall 758s (runtime 360s + 398s outside the scanner).
- Time: the outside-scanner share (215s pre-cut to 398s) is IM3. Every no-history name cost SEC + 3 stockanalysis page loads (retries and sleeps) in BOTH IM3 steps on EVERY run. Now the income page is fetched first and the other two are skipped when it gives under 3 revenue years; a "page fine, too little revenue" verdict is remembered 7 days (per IM3 version); FMP has a per-step call budget (70) so the shared 250/day quota is not drained.
- s9: Finnhub trend vote now fires on any net-buy change above 0.005 (was 0.02: only 6 of 44 voted up); source label is `analyst_bridge` (it said fmp_bridge for Finnhub-only votes). FMP still answered HTTP 429 on its first call today (daily quota spent by earlier runs); the 30-day statement cache and 3-day bridge cache fill as soon as it resets.
- IM3 stockanalysis: the "fetched but revenue row has 0 annual values" verdict for VMET/MWH/AADX/GORO has an unknown cause (the sandbox cannot load the page). The reason now carries the first row labels the page returned, alias labels (Total Revenue, Operating Revenue) are accepted, and unparseable cells are named. Read `src.why` on the next scan.
- Tests: test_im3_v233 (8) added; all earlier suites pass.

## v1.532.0 / IM3 v2.32.0 — 16 Oct 2026 — fixes from the first live v1.531.0 scan (parity FAIL on 3 of 7)
Live scan: s7 47.7% (base 40.9) PASS, s8 34.1% PASS, HIGH+WATCH 56.8% PASS, country rows 13 PASS; s9 0%, IM3 no-history 49, PSX bars 41/48 FAILED.
- s9 root cause: FMP's free plan is 250 calls/day and IM3 spent it (3 uncached calls per name, twice per workflow, plus forced re-scores), so the bridge got HTTP 429 and cached nothing. Bridge now: 3-day cache with stale fallback to 14 days; an HTTP 402/429 switches FMP off for the run instead of retrying; Finnhub stock/recommendation (probe-proven, no daily cap) supplies a second vote (latest month net-buy score vs prior month) so s9 no longer depends on FMP quota. Published as `meta.revision_bridge` (calls, HTTP codes, cache hits; no keys).
- IM3 FMP: statements cached 30 days in us_history_cache.json (annual data), one call instead of three for a name FMP refuses, plan-excluded (402) names cached 30 days, HTTP 429 turns FMP off for the run.
- IM3 SEC: when the named revenue tags give under 3 years (XOM 0, RBRK 2, SLDE 1), any revenue/sales-like us-gaap tag with 3+ annual values is used (largest latest value wins); if still none, the row's `why` lists the revenue-like tags it saw.
- IM3 stockanalysis: header-missing, FY-column-missing and exception cases now put their reason in `src.why` (they were silent -- every row said "no usable 3y revenue").
- PSX bars: 7 candidates (PACE TBL GTYR SPWL HCAR HUMNL IPAK) sat on a single partial bar because they entered the candidate list after 16 Oct's first scan; names with under two settled bars are now backfilled from the TradingView chart socket (<=80 names, validated rows only, never today's bar). Published as bar stamp `backfill`.
- Tests: all prior suites pass; new test_v1532 (16 checks) and test_im3_v232 (14 checks).

## v1.531.0 / IM3 v2.31.0 — 16 Oct 2026 — remaining Yahoo streams replaced, parity guard fixed
- TCE US s8 (external capital): FINRA daily short-volume ratio (10 days, >=5 files), top-third cutoff across the pool. A PROXY for Yahoo's short-interest flag, labelled `s8_src=finra_short_volume_proxy`; no free short-interest source serves (Finnhub 403).
- TCE US s9 (EPS revision): FMP grades + price-target bridge (30-day upgrades/downgrades plus target direction, 2-day cache, stops on 402/429) used while the TradingView forward-EPS history is under 20 days; then the TV 30-day baseline takes over. `s9_src` records which.
- TCE US s10 (revenue revision): TradingView `revenue_forecast_fq` snapshot vs the prior run.
- Parity guard `meta.yahoo_parity` now runs just before governors (after PSX bars attach, fixing the false 0.0% bar share); `meta.tv_socket_run` published there.
- IM3 v2.31.0: FMP requests use limit=5 (limit above 5 is premium-gated); SEC CIK map never caches empty and retries; stockanalysis fetch retries on 429/5xx; every row records `src.why` (sec / fmp / stockanalysis reason) so the none-rows are diagnosable on the next scan.
- Tests: all suites pass (v1527 12, v1530 14, v1531 6, probe, im3 sa/fmp, bottoms 1524/1525, cashhunt 1514/1518/1519/1520). Live PASS/FAIL is only provable on the next scan via `meta.yahoo_parity`.

## v1.530.0 — 16 Oct 2026 — Yahoo replacements + standing parity guard
Audit of the Yahoo cut (v1.526.0 last Yahoo scan vs v1.529.1): TCE US streams s7/s8/s9 went 18/15/22 of 44 to 0, HIGH+WATCH tier names 27 to 5, 49 US names scored with no statement history (XOM coverage 100% to 20%), 7 PSX candidates lost their daily bar, New Zealand dropped out of country RS. This build replaces each:
- TCE s7 (margin inflection): US now uses TradingView quarterly YoY revenue/EPS growth (same basis as Yahoo's earningsGrowth/revenueGrowth); pool names that arrive without them are filled by one america/scan batch.
- TCE s9 (EPS revision): the TradingView forward-EPS revision now compares against a 30-day-old snapshot (kept in `fwd_eps_hist`), matching Yahoo's 30-day breadth; the 1-day baseline remains until 20 days of history exist.
- IM3 statements: root cause found -- the IM3 workflow steps never received FMP_API_KEY, so FMP was dead and SEC failures fell straight to Yahoo. Now: keys passed (daily.yml), order SEC -> FMP -> stockanalysis US three-statement tier (the parser already validated live on MU and ASM) so SEC-served names score exactly as before; names with no history carry a `why`.
- Country RS: NZ50 tries four TradingView symbols.
- Probe `yahoo_replacement_probe` (weekly): measures which Finnhub/FMP endpoints, TradingView columns and FINRA files serve revenue estimates, EPS revisions and short interest, for the two still-open streams (s8 short interest, s10 revenue revision). Keys are never written to the payload.
- Standing guard `meta.yahoo_parity`: every scan compares the streams/coverage Yahoo fed with the pre-cut baseline and publishes PASS/FAIL per metric; on the v1.529.1 payload it fails exactly the seven regressions above, on the v1.526.0 payload it passes.
- `meta.tv_socket_run` publishes the chart-socket failures (to explain the 7 PSX names).
- Open until the probe reports: s8 (short % of float) and s10 (revenue-estimate revision).

## v1.529.1 — 16 Oct 2026
- Probe verdict fix: v1.529.0 counted HTTP-200 lookbacks with null cells as "history" and reported 53 columns with history. Live result: TradingView serves 53 statement columns as current values only (FY latest, FQ latest, TTM); 0 of 1,060 prior-period cells held a number. A lookback now counts only when it returns a number.

## v1.529.0 — 16 Oct 2026 — TradingView fundamentals probe
- Why: cutting Yahoo left 51 names (XOM, MRVL, ...) scored with no multi-year statement history (IM3 coverage 20%). TradingView is unreachable from the build sandbox, so what it serves for statements has to be measured on the runner.
- New weekly stage `post.tv_fund_probe` (about 15-20s, once a week): tries ~84 statement columns one per request, then prior-period lookbacks [1]..[4] on every column that answers, for XOM, MRVL, MU, AAPL, CVX. Result is published as `tv_fundamentals_probe` (working columns with values, lookback results, error kinds, a plain-English verdict). The IM3 history tier is built from that measurement, not from guesses.
- Mock-server test passes (column discovery, lookback depth, weekly reuse).

## v1.528.0 — 16 Oct 2026 — Yahoo scrubbed from the rest of the stack
- im3_score.py v2.29.0: the Yahoo backstop (statements and info) is removed; names TradingView/FMP/SEC cannot serve show source "none" instead of "yahoo". Cached Yahoo statement parses are no longer served, so ~25 names that carried "hist: yahoo" lose that history until a non-Yahoo source covers them.
- scanner.py: no Yahoo statement fallback in the explosive screen (no more per-miss Yahoo sleep), no Yahoo last-resort in the IM3 helpers, Yahoo-named labels now read tradingview.
- moat_cover: dead-fund retries are staggered per fund (the 16 Oct scan retried all 13 together and the stage went 68s to 120s); funds dead 28+ runs retry every 28th.
- Includes v1.527.1 (ITWN pence rescale).

# v1.526.0 (index unchanged, v5.405) - 2026-10-16
- Yahoo is out of the bottom check and the exit-day count (owner, 16 Oct: "i have always said cut yahoo and replace it with tv"). Both read TradingView scanner lookback columns only (open/high/low/close/volume and [1]..[n] on global/scan), no Yahoo fallback.
- The reachable depth is PROVEN every run (separate probes at 1, 5, 20, 60, 100, 129 sessions on NASDAQ:MSFT); under 60 sessions the check goes dark with the depth stated on the board instead of guessing. Published in data.bottoms.tv_history (depth_proven, probe, requests, failed_requests, rejected).
- Every name's bars are validated: finite and ordered (low <= open/close <= high), at least 60 usable bars, and for holdings the newest close within 12% of the live price after a pence/pound correction (catches a wrong listing line or currency). A rejected name is NO DATA with its reason (tv_reason).
- TradingView's live bar is dropped while the exchange is open; bars are dated to the last closed session.
- Rule 3 (hourly structure) is OFF until TradingView hourly lookback is proven; it was the only Yahoo-hourly use.
- live_portfolio.json override renamed yahoo_symbol -> tv_symbol; UCITS holdings map to LSE:/EURONEXT: symbols (_BT_TV_MAP).
- NOT verified from the build sandbox (TradingView is unreachable there): first scan will show whether lookback columns work; check data.bottoms.tv_history. Tests use a fake TradingView: v1526 16, v1525 12, v1524 61, v1520 25, v1519 68, earlier suites pass.
- Remaining Yahoo call sites predate this build (TCE 6-month batch, SPY benchmark, USDPKR, 5-day re-pricing, ETF meta, PSX .KA, metals); listed for the next cut.

# v1.525.0 (index unchanged, v5.405) - 2026-10-15
- FIX: the 15 Oct scan called KSTR "bottom CONFIRMED" (rule 4) on a Yahoo history that ended 13 Oct, while the market had traded two more sessions down (IBKR: 14 Oct close 21.074, 15 Oct low 20.64, new low every day). A daily history that ends before the last closed session (London 16:30, Amsterdam 17:30, US 21:00 UTC, weekends rolled back) is now NO DATA with stale_bars / last_bar / expected_bar / price_gap_pct and a plain reason; the availability board says "behind the last closed session". Seven London/Amsterdam holdings were affected that day (SMH, ITWN, KSTR, AINF, STOR, FLXK, PHPM all ended 13 Oct).
- FIX: "thin volume" now also means small traded value (median 30-day volume x price under 250k), which switches the volume rule off. KSTR's rule 4 fired on a 9.9x volume day on Yahoo's numbers; the broker shows 964 shares that day (its volume spike was 9 Oct, which would not have passed the lowest-low test).
- Exit engine: a stale history falls back to the scan counter for days-below-trend instead of under-counting.
- Tests: v1525 12, v1524 61, v1520 25, v1519 68, earlier suites pass.

# v1.524.0 (index v5.405) - 2026-10-15
- Index v5.405: availability items and governed calls are shown at the top of the tab the board names -- Tab 11 (bank survey 288 days old), Tab 9 (TCE-HIGH half vote weight), Tab 3 (PSX market watch stale); Run health gains a "Why this run differs" line.
- Scanner: psx_market_watch board item names Tab 3; a failed dps.psx.com.pk fetch now records why (HTTP status / 200 with no parsed rows / exception) in last_error and on the board.
- Bottom engine: a CONFIRMED bottom more than 25% off its 52-week high carries knife_probe (flagged, not cancelled) and the why-text says treat the tranche as a probe (KSTR case: rule 4 confirmed at 36% off its high while closing under the old AVOID line).
- meta.stage_cadence names heavy stages that swung between scans because of freshness windows (sec_filings 20h, bank_snapshot 24h): 14 Oct 333s vs 15 Oct 438s was sec_filings +56s, bank_snapshot +36s, m1_buylist +39s.
- Tests: v1524 61, v1520 25, v1519 68, earlier suites pass; render check of the three notices on the live 15 Oct payload.

# v1.523.0 (index unchanged, v5.404) - 2026-10-14
- Availability board no longer lists the broker valuation matrix once live TradingView ratios replace it (live_overlay present); the item stays if only the superseded flag is set.
- psx_market_watch: a failed or empty dps.psx.com.pk fetch is now stamped last_error, warned, and appended to the board reason (it had been carrying the 24 Sep copy silently for 20 days).
- Exit engine: 3x holdings (AMD3/TSM3/MSF3) count days-below-trend on their US stock's daily bars (below_days_basis = "underlying daily bars"); count is zeroed while the product itself is above its 50-day.
- Bottom rule 2 tightened: the undercut must be of a significant low (tested by another swing low within 2%, or the lowest low of the prior 60 sessions), no deeper than 5%, and the reclaim must close in the upper half of the day's range. Result stamps "tested".
- Tests: v1523 58, v1520 24, v1519 68, earlier suites pass. test_v1521 is superseded by the decline-filter tests.

# v1.522.0 (index v5.404) - 2026-10-14
- Bottom rules tightened: a signal now needs a prior decline of at least 10% from the 60-session high (rules 1, 2, 4, 5); rule 3 and WATCHING need it too. New field decline_to_low_pct. CONFIRMED + entry-timing AVOID is flagged "probe, not full position" (flagged, not overridden).
- PSX valuation: live TradingView ratios overlay the Valuation Matrix (P/E, yield, ROE, P/B, EV/EBITDA, mkt cap), lists re-ranked, stale-matrix warning suppressed; green LIVE TRADINGVIEW banner on the tabs.
- Exit engine: days-below-trend now counted from Yahoo daily bars (below_days_basis = daily bars / scan counter), not the scan counter.
- New timing checkpoints seg.etf_live_prices, seg.emerging_holdings, seg.hydrogen_notes, seg.etf_trackers close the ~18.7s unmeasured stretch.
- Tab 1 Run-health strip (scan time, biggest gaps, warnings).
- Tests: v1522 55, v1521 38, v1520 23, v1519 68, earlier suites pass.

## v1.527.1 — 16 Oct 2026
- Bottoms: a London line quoted in pence while the holding is priced in USD/GBP (ITWN) is rescaled by one constant factor instead of being rejected as "wrong line". Audit of the live v1.527.0 scan: socket 552/554 names, SMH London bars match IBKR (15 Oct close 101.94).

## v1.527.0 — 16 Oct 2026 — Yahoo removed completely
- No `yfinance` import, URL or requirement remains. All ~20 former Yahoo call sites (oil, USDPKR, ETF, SPY, country/FX RS, TCE pool history, repricing, exit/bottom engines) now read TradingView through one chart-socket client (`tvh_history`), with a once-per-run probe, per-series validation and each consumer's existing last-good fallback.
- Bottoms: real 130-bar daily history plus hourly bars (rule 3 is back). A series is rejected, with the reason shown in `bottoms.tv_history.rejected`, if bars are mis-ordered, too few, or the last close is >12% from the live price.
- Yahoo-only fundamentals (TCE margin/capital/estimate revisions, statement fallback, fund holdings) are now honestly empty. The Yahoo news feed was replaced by Bing News RSS.
- requirements.txt: yfinance dropped, websocket-client added.
- Tests: mock TradingView socket, shim shape tests, static scan, suites 1513-1520/1524/1525 pass (1526 retired).

## v1.521.0 / index v5.403 — 2026-10-14
- **Bottom engine (owner's six rules):** every Tab-17 holding and every Tab-19 name is checked each scan. Rule 1 reversal candle at a support zone (green, above prior day's midpoint, upper third; next session must hold the low). Rule 2 undercut and reclaim of a prior swing low. Rule 3 hourly higher low then a close above the previous hourly swing high. Rule 4 capitulation volume (>=1.5x the 30-day average) then a lighter down day or an up day on above-average volume. Rule 5 RSI 30-40 at the touch with price lower low / RSI higher low. Any ONE of 1-5 confirms (a session late, by design); rule 6 invalidates: a close below the base floor = BASE BROKEN (no averaging until the next level is tested and confirms by rule 1 or 2); a close below that next level = AVOID.
- **Zones are automatic:** clustered swing lows of the last 120 sessions (minimum 1% wide) plus the 50- and 200-day averages when within 10% below / 1% above price. Signals count for 3 sessions.
- **3x London products** are read on their US stock; the tranche bid is the existing London fair value x 1.005.
- **Advisor gate:** an ADD on a holding whose base is BROKEN or AVOID becomes WAIT ("no averaging into a broken base").
- **Data:** Yahoo daily (1y) and hourly (1 month) bars, settled bars only; PSX has no OHLC source so it is not covered; a listing with no history says NO DATA and shows on the availability board (add `yahoo_symbol` in live_portfolio.json to fix a UCITS ETF).
- **Thin names** (median daily volume under 1,000 shares) have rule 4 switched off.
- **index v5.403:** BOTTOM CHECK card on Tab 17 and Tab 19, a pill on each Tab-19 row, the six rules in plain words.

## v1.520.0 / index v5.402 — 2026-10-14
- **Exit-day counter fixed:** the "closes below trend" count advanced once per scan, so three scans in one day counted as three closes. It now books once per trading session (`counted_on`). Affects the 2-close confirmation band (PHPM).
- **Time-gap finder:** `meta.timing_gaps` names every stretch of scan time no timed stage covers, with the stage before and after each hole (targets the ~162s unmeasured).
- **Availability board is generic:** every dated block is judged against its own refresh cadence (default 3 days; 13F 100; market watch and fund ownership 7). psx_market_watch (20 days) now shows.
- **Live PSX valuation from TradingView:** `psx_valuation_tv` (P/E, P/B, ROE, yield, market cap, EV/EBITDA). Each column probed separately; fill rate logged; the broker matrix is marked superseded once P/E fill is 60% or more.
- **Seed refresh:** live_portfolio.json now AMD3 1,477 sh @ 8.46773, MSF3 115 sh @ 64.52096, USD 0.51, AED 76,081.35 (IBKR pull 14 Oct).
- **index v5.402:** Tab 19 valuation label (no more `[object Object]`); Tab 17 note "positions as of <statement date>"; governor board and seed banner (from v5.401) included.

## v1.519.0 — 2026-10-14 — CALL GOVERNOR, AVAILABILITY BOARD, SEED GUARD (index v5.401)

**No approval step.** You corrected my first design: the system decides by itself, from evidence, and says so on the dashboard.

### 1. Call governor (TCE HIGH-tier vote)
Judged every scan on four factors over a **rolling window of its last 30 matured calls**: hit rate, median alpha, share beating the benchmark, median return vs the IGNORE tier. FAIL needs 3+ failing factors; PASS needs 3+ passing.
Ladder with hysteresis: **ACTIVE 1.0 → DISCOUNTED 0.5** after 3 FAIL scan-days → **SUSPENDED 0.0** after 7. Climbing back needs 7 PASS days per rung. Streaks count distinct dates, so two scans in a day are one day. The tier keeps being scored while governed, so it can earn its way back.
Day one honours the v1.492.0 discount already live (nothing flips today). Real payload today: 30 matured, 0% hit, median alpha −10.95%, 4 of 4 factors fail, DISCOUNTED, fail streak 3 → **suspends on the 7th FAIL day (~18 Oct) unless the evidence changes**.
ETF picks lapse after 7 scan-days at −5% or worse vs ACWI and return after 7 days at or ahead.

### 2. Availability board (Tab 19)
`availability` lists everything not fully available, each with reason, since-date, back-on date and what clears it: bank-sector survey (287 days — UNAVAILABLE at >180d, notice at >90d), frozen PSX valuation matrix, 10 new PSX names awaiting a candle check (back ~16 Oct), flat-base pattern (back ~2 Nov), 8 Zacks names without a price, lapsed ETF picks.

### 3. Portfolio-seed guard (item 8, approved)
`_li_load_config` validates shape; on failure Tab 17 shows a red DO-NOT-TRADE banner, the advisor is suspended, and the scan warns. Tested against a truncated file, a missing file, empty holdings, scanner.py pasted over the file (the 24 Sep incident), zero/bool shares.

### 4. Record sync
`meta.record_sync` re-measures the decision record's factual claims each scan; a false claim warns as DRIFT. Record updated: ETF tracker computes; bank-sector threshold 90d.

**Tested:** 68 new assertions on the real functions and the real payload (plus 418 existing, all passing). The tests caught one real defect before render: a corrupt stored streak value crashed the step; hardened. Board and banner rendered and inspected.

## v1.518.0 — 2026-10-14 — THREE FIXES FROM THE FIVE-PASS AUDIT

**Owner said go.** The warm-up veto, the dead flat-base, the bank-sector watchdog.

### 1. An unknowable test is not a failed test

The own-history store held one settled bar on the 04:23 run, so `prev_high` was `None` on all 391 store-graded rows. The midpoint check came back `null`, `_candle_quality` graded that 'mixed', and the veto fired on every store-graded BUY.

**Correction to my own audit:** I said "41 of 41 Zacks vetoes are false." Running the real rows through the fix shows **9 were false and 32 were legitimate** — those 32 failed a *known* test (not green, or not in the upper third). 13 Oct was a red day. The bug was real; its scale was a quarter of what I said.

Now: a `null` check with **no known failure** passes through as `candle_basis: 'partial'` and says the missing test runs tomorrow. A rejection or a known failure still vetoes. Classify-mode rows (Tab 10) carry the same honesty — RERE (green, 95% of range, midpoint unknown) is labelled 'partial', not 'mixed'. Tab 1 was never affected; its engine-native grades carry `prev_*`.

### 2. Flat base was dead code

`_pattern_book` read `range_pct_20d`. No block computed it. I tested the function on fixtures that had the field and never ran the wiring against real rows — the lesson from the day before, half-repeated.

The store now keeps **21 bars** (was 3; ~440 kB at 467 names) and `_range_pct()` publishes `range_pct_20d` once **15 settled bars** are on file. Honest absence until then — the real store has 1–2 bars per name today, so flat base becomes possible in roughly 13 trading days. The pattern's `why` states the real session count, not a hardcoded 20.

### 3. Bank-sector watchdog 400d → 90d

It sat at `as_of 2025-12-31` — 287 days — with no warning and no `stale_days` stamp, because the threshold was 400. Now 90, matching the quarterly screening clock. Tab 11 will carry the warning on the next run.

### Validation

**486 assertions across seven suites.** The null-check fix was run against the 41 real vetoed Zacks rows from the 04:23 payload, not fixtures. Two stale test expectations updated for deliberate changes (the non-buy 'partial' label; the store cap).

## v1.517.0 / index v5.400 — 2026-10-14 — THE RENDER WAVE, and a correction

**Owner said go.** Tab 17 London 3x card, Tab 1 veto made legible, risk-budget reasoning, the timing export, the four-decimal averages.

### Correction to my 13-Oct audit

I said "no block carries OHLC at all." **Wrong for Tab 1.** `build_entry_timing` has carried its own bars and graded its own candle since v1.503.0 — 153 of 154 rows on 13 Oct under `candle_quality` (26 strong / 52 weak / 18 rejection / 57 mixed), beside `candle` = the confirmation-*state* object. My payload check read the block's top-level keys instead of its ticker-keyed rows. Right for the other ten blocks; wrong for the one that mattered most.

What *was* true: the engine graded the candle but never vetoed the BUY on it. **14 of 32 BUYs sat on weak or rejection candles** while `_tech_call`'s one-call pill already read WAIT for the same names — CBNA: verdict BUY, call WAIT, *"the last daily candle was a REJECTION."* Two pills, two answers. The veto on `verdict` brings them into line. It is coherence, not new logic.

### A bug fixed before it bit

v1.515.0 wrote its grade into `r['candle']` — overwriting the state object the index renders as the "✓ candle in / forming / waiting" pill. It would have broken on the first warm run. The pass now **trusts an engine-native grade** and leaves both objects alone; it grades from the own-history store only where the engine did not, and writes to `candle_quality`, the key the renderer already reads.

### One real disagreement, resolved

**TARS**: green, above the prior midpoint, but closed at 39% of its range. The engine's call pill said BUY NOW; your rule needs all three tests, so the verdict pill says WAIT. The verdict follows the rule as you stated it. Rather than ship two pills disagreeing, the veto now reaches the call pill too — `tech_call.call` BUY NOW → WAIT, original preserved in `call_before_candle`, reason prefixed `CANDLE VETO`. "BUY ON TRIGGER" is conditional and compatible with WAIT, so only BUY NOW is touched.

The veto sentence now **names the test that failed**. The 'mixed' wording said *"not green closing above the prior midpoint and in the upper third"* — for TARS, which *is* green and *is* above the midpoint, that was a wrong explanation. Now: *"it did not close in the upper third of its own range (it closed at 43% of its range)."*

### Also in the scanner

- `trading_rules` stage time exported as `post.trading_rules` — it ran after `timings_post_ms` was written, so the TV fetch cost was invisible.
- Coarse-exit sentences: 50-day averages and prices to two decimals (`$108.78`, not `$108.7776`).
- The risk budget updates the advisor **row** as well as the action — the Tab-17 paragraph read `rows[]` and still said $1,959 while the instruction list said $2,500.

### index v5.400

1. **Tab 17 — London 3× card** on AMD3, TSM3, MSF3: FAIR (mark × 1+3× the US underlying move), BID UP TO (+0.5%), NEVER ABOVE (+1.5%), window state, first-hour premium warning, dormant-overnight-stop note.
2. **Tab 1 — the veto made legible:** the pill shows ~~BUY~~ WAIT ✖, and the hover names the test that failed.
3. **Tab 17 — risk-budget note** under every ADD: the size allowed and why, trailing stop, invalidation.

### Validation

**456 scanner assertions (six suites) + 40 renderer assertions.** The renderers were run in node against rows produced by the real post-pass from the real 20:17 payload — all three 3x holdings, TARS/CBNA/NVDA (vetoed), AAPL (strong candle, untouched), the STOR budget.

Caught this round: the `candle` clobber above; the harness still loading yesterday's payload (TARS wasn't in it); a `<s` regex matching `<span`; and my assumption that NVDA wasn't vetoed — it failed all three candle checks, so it was.

## v1.516.0 — 2026-10-13 — THE BAR FEED MOVES TO TRADINGVIEW

**My error.** v1.515.0 read its bars from `_batch_history_cache` — one `yf.download` — because that was the only existing OHLC path in the file. That breaks a standing rule recorded since v1.491.0: *"Yahoo is never used where TradingView can serve the field."* I chose a data source without reading the data-source rules, which are in the decision record under that exact heading.

### Why the old path was Yahoo, and why it didn't have to be

`_batch_history_cache` is Yahoo because **TradingView has no OHLC-history endpoint** — that much of the record is right. But the candle rule never needed history. It needs **one settled bar's open/high/low/close**, and that is a per-symbol column on the same `/scan` POST this scanner already makes about twenty times a run.

### What replaces it

**`_tv_bar_batch`** — request shape copied *verbatim* from the proven `_tv_close_batch`: `symbols.tickers` + `columns`, 150 per chunk, same endpoint, same UA. Only the column list differs, so nothing here is a guessed structure.

**The prior day's range** — which the midpoint test needs — now comes from the dashboard's **own accumulated history** (`_bar_store_merge` → `data['bar_history']`, three bars per name). That is the pattern you locked for the oil trends in v1.490.0: *"the dashboard's own daily history is the SOLE authority."* TradingView gives one bar per call, so the series is built by keeping them, not by asking a second vendor.

**`_settled_rows`** refuses to grade a half-finished candle: a bar counts only once it is dated before today, or dated today after 21:00 UTC.

### The honest limit

**I cannot confirm that TradingView serves `open`/`high`/`low`.** The build sandbox's egress proxy answers 403 to CONNECT for `scanner.tradingview.com` — logged in the proxy's own relay-failure list. Your rule forbids shipping a fetcher at an unconfirmed structure, and I can't web-fetch it to confirm.

So `_tv_bar_batch` returns a **probe** naming exactly which columns came back populated, stamped at `meta.trading_rules.tv_probe`. The runner reaches TV; the next scan settles it in the payload instead of in an assumption.

If TV does not serve them: **nothing grades**, every verdict stays byte-identical to what its engine produced, the probe says why — and **no Yahoo fallback is added.**

### Warm-up, stated plainly

The midpoint test needs two settled bars, so it is live **from the third run**. The rejection test — close in the bottom tenth of its own range — needs only one bar and works as soon as a session has closed. Before that, honest absence: `candle_basis: 'no data'`, verdicts untouched.

### One thing the Yahoo path never had

Because the store is the dashboard's own, **a TradingView outage for one run no longer blinds the rule** — yesterday's settled bar is still on file and still valid. Proven in the harness: TV raising on every call, warm store, 656 rows still graded.

### Scope

Pre-existing Yahoo uses your record already lists as irreducible — the frozen TCE six-month history, the SPY benchmark series, off-pool re-pricing, non-SEC income statements — are **untouched** by this wave. No new Yahoo anywhere: verified by scanning the whole `apply_trading_rules` body.

### Validation

**444 assertions across six suites.** This round caught a real bug — `_bar_store_merge`'s own exception fallback raised on a non-dict store, because `dict('x')` throws — plus three defects in my own harness (a seed dated against the simulated day instead of the real clock, a self-wrapping scope stub, and a leftover line that nulled the datetime module).

## v1.515.0 — 2026-10-13 — TRADING-RULES COMPLIANCE (sections C, D, E, F)

**Owner:** all four sections, across every tab, in one go. Bar cadence: **option B every run, option A weekly.**

### The finding that shaped the build

Section C wasn't under-wired — **no payload block carried daily OHLC at all.** Not even `build_entry_timing`, the one engine that called `_candle_quality`: its rows come from a TradingView batch of closes, EMAs and RSI, and its `history` is `[date, close]` pairs. The rule had nothing to read. For eleven days it decorated one sentence on one tab while every other tab published level-only BUYs with no candle check.

### One pass, not eleven edits

The eleven technical blocks are assigned into `data` from eight different functions, so wiring C into each would have meant eleven implementations of one rule — the drift you objected to over the breakout calculation. `apply_trading_rules` runs after every builder and before the governor: one batched OHLC call per market, grade the last **settled** bar, apply the rule. Same code, same bar, every tab.

### The mode split — read from the live vocabularies, not assumed

| block | field | vocabulary | mode |
|---|---|---|---|
| `entry_timing` | verdict | BUY / WAIT / AVOID / WAIT FOR DIP | **timing → vetoed** |
| `zacks_radar` | verdict | "ZACKS DISCOVERY — Buy / Strong Buy" | **timing → vetoed** |
| `explosive_us` / `explosive_psx` | verdict | "EXPLOSIVE — both signals", "INFLECTION" | classify → attached |
| `us_candidates` / `psx_candidates` | status | WATCH / STRONG / HIGH-CONVICTION | classify → attached |
| 5 weekly screening blocks | grade/score | — | classify → attached |

Vetoing "EXPLOSIVE — both signals" to "WAIT" would turn a statement about accelerating fundamentals into a timing verdict and destroy what the engine computed. Section C vetoes level-only **timing** signals; it is not a licence to overwrite every label.

### Sections D, E, F

**D** — adds **flat base** and **failed breakout**, and publishes the trigger / stop / target / status contract for every named pattern. The honesty rule holds: a near-miss returns nothing rather than a weaker label on a pattern that isn't there.

**E** — enforces what the scanner never did: the **$2,500–5,000** tranche band, the **$7,500** daily ceiling, the **two-buys-a-day** cap, a **7% trailing stop over the whole position**, and the invalidation level recorded at entry. (What existed was `min(spare/3, 10% of NAV)` and a 2×ATR trail on eight US names.)

**F** — the three London 3x holdings finally get mechanics: fair = London mark × (1 + 3 × the US underlying's move), limit **fair +0.5%**, never above **+1.5%**, the **18:30–20:30 PKT** window, the first-hour premium warning, and the **dormant overnight stop**.

### Fail-safe

A dead bar feed leaves every verdict byte-identical to what its engine produced, and records the failure in the payload. Proven, not asserted.

### Validation — and what it caught

**383 assertions across five suites.** The end-to-end harness runs the *real* pass over the *real* 15:10 payload with a stubbed feed, because Yahoo is blocked in the build sandbox — only the runner can confirm the fetch itself.

That harness caught **three defects before release**:

1. `_tr_rows` dropped **all 154 `entry_timing` rows** — that block is keyed by ticker and its rows carry no `ticker` field, so the one tab whose verdict is a real BUY/WAIT call got no grade. It showed up as `rows=154 graded=0 no_bar=0`: never even reached. Fixed, then fixed again when the first patch sat after an earlier early-return.
2. Prefix matching missed **every Zacks row** ("ZACKS DISCOVERY — Buy" doesn't start with BUY).
3. The first draft had no mode and would have **overwritten the explosive classifications**.

Dry-run result on the 15:10 payload: 656 rows graded, **34 of 34 `entry_timing` BUYs** and all 41 Zacks rows put through the rule, 9 patterns named, all three 3x holdings priced, the one ADD clamped to the tranche floor.

## v1.514.0 — 2026-10-13 — OPTIONS 1 AND 3 (owner-approved)

### 1. Buffer and confirmation on the coarse exit

Any close below the 50-day average — by any margin, on a single day — read **EXIT**. On the 12:18 run that put EXIT on **five of ten holdings**, including SMH at 1.25% below its average and PHPM down 1.4% overall. A 50-day cross is among the noisiest signals there is; half a diversified book sitting slightly under it in a mild drawdown is ordinary, not a sell on each name.

Three bands:

| gap vs 50-day | rule |
|---|---|
| shallower than **−2.5%** | noise — reported, not acted on |
| **−2.5% to −8%** | real break, needs **2 consecutive closes** below |
| deeper than **−8%** | decisive on its own, no confirmation |

The consecutive count persists across runs through the `EXISTING` exit-rules carry.

**The −8% decisive band is not in the brief.** I added it because buffer-plus-confirmation alone would have gone blind for one full cycle on genuinely broken positions (KSTR −11.1%, FLXK −8.9%) on the first run after deploy, when no prior below-day count exists. All three numbers are single constants, deliberately easy to retune — say the word and they move.

### 2. Hard gate on ADD

The dashboard was issuing **ADD $1,954 into STOR while its own exit rule labelled STOR EXIT**. v1.513.2's note explained that clash in words but left the instruction standing, so one screen said buy and sell the same holding.

New PURE `_gate_add()`. The advisor cannot see the exit verdict itself — exit rules are built after it — so the gate runs over the finished advisor output and rewrites the row, the action, the notes and the headline. **ADD only** is blocked: TRIM and WAIT are consistent with selling, and HOLD carries no instruction.

`build_exit_rules` is now three passes — verdicts, then the gate, then the reconciliation notes — because a note computed before the gate would quote a sizing verdict the gate was about to overturn.

### Effect on the 12:18 book

| | gap | EXIT was | EXIT now |
|---|---|---|---|
| SMH | −1.25% | EXIT | **HOLD** — inside the noise buffer |
| STOR | −1.96% | EXIT | **HOLD** — inside the noise buffer |
| PHPM | −4.95% | EXIT | **HOLD** — awaiting a 2nd close |
| FLXK | −8.88% | EXIT | EXIT — decisive |
| KSTR | −11.10% | EXIT | EXIT — decisive |

**EXIT count 5 → 2.** ADDs gated: **none** — because option 1 removed STOR's spurious EXIT at the root, so the gate had nothing to block. The two fixes interact: the contradiction disappeared because the EXIT was the thing that was wrong, not the ADD. The gate stays armed for a genuine break.

### Validation — the step whose absence let v1.513.0 ship broken

Every one of the ten live holding rows is a fixture read from the 12:18 payload, with expected verdicts written down *before* the run. Plus the fully enumerated band × confirmation × leverage space (10 gaps × 4 below-day counts), leverage precedence, gain-TRIM reachability, `below_days` bookkeeping, absence and hostile inputs, backward compatibility with all three older call shapes, the complete 6×7 `_gate_add` matrix, and a no-raw-floats sweep. The gate was additionally simulated end-to-end against the real payload before render.

**That run caught two defects before release:**

- **A real bug:** `int(below_days)` raised on a non-numeric string, in a function documented as never raising. Hardened.
- **A bad test:** the −8% boundary was asserted on a constructed float — `100.0*(1−0.08)` re-derives as `−7.9999999999999964`, so an exact-boundary input lands either side by ~1e-14. The assertion now tests the contract around the boundary instead.

## v1.513.2 — 2026-10-13 — COMPLETES "ONE SURFACE ONE ANSWER"

**Scope note:** this finishes approved item 5 from the 13-Oct audit, which v1.513.0 only half-delivered. Not new scope.

### Verified in production first — v1.513.1 worked

The 12:01 run on v1.513.1:

| | result |
|---|---|
| AMD3 cap / basis | **2.5% `unknown`** (was 5.0% `calm`) |
| AMD3 sizing | **TRIM $1,832** (was HOLD) |
| AMD3 exit chip | TRIM — **both surfaces agree for the first time** |
| Headline | "4 instructions; KSTR wait, STOR add, TSM3 trim, **AMD3 trim**" |
| Unrounded floats in owner-facing text | none |
| `nav = holdings + cash + interest` | reconciles to the cent |

### The remaining gap

v1.513.0 reconciled the exit chip with the sizing verdict using two inline branches, which covered only **two of the four** combinations. On the 12:01 run **TSM3 displayed exit HOLD directly beside a TRIM instruction for $4,017**, with nothing linking them — the same silent-disagreement shape the fix existed to remove, on a different pair.

TSM3 is healthy (+3.2%, above its 50-day line) *and* oversized (4.1% against a 2.5% cap). Those are not contradictory. But shown side by side with no explanation, they read as one.

### Fix

New **PURE `_exit_sizing_note()`** covering every combination:

| exit \ sizing | HOLD | ADD | WAIT | TRIM |
|---|---|---|---|---|
| **HOLD** | — | — | — | note |
| **TRIM** | note | note | note | note |
| **EXIT** | note | note | note | note |
| **NO DATA** | — | — | — | — |

- **EXIT vs HOLD/ADD/WAIT** — the sizing engine answers how *much* to hold, not whether to hold at all; on hold-or-sell the exit rule governs.
- **TRIM/EXIT vs TRIM** — both reads agree.
- **HOLD vs TRIM** — healthy and oversized is not a contradiction: one chip answers hold-or-sell, the other answers how much.
- **TRIM vs HOLD/ADD/WAIT** — inside its size cap is a question about SIZE; the trim is about RISK, and on risk it stands.

Silence is reserved for genuine agreement and for `NO DATA`.

Being pure, it is **unit-tested rather than eyeballed** — which the v1.513.0 inline version could not be. That is the structural point: the previous version's incompleteness was invisible because the logic sat inside a loop where nothing could reach it.

**Tests:** the full 4×4 matrix, the four production pairs from the 12:01 run, both combinations v1.513.0 missed, plus case/whitespace tolerance and garbage inputs. All passing, and the v1.513.1 suite stays green.

## v1.513.1 — 2026-10-13 — THE SAME FAIL-OPEN, ONE LAYER DOWN

**v1.513.0 did not actually close the bug it was written for.** Found by the post-deploy audit of its own first run.

### What happened

The 11:44 run on v1.513.0 still reported AMD3 as `cap_basis: calm`, cap 5.0%, target 4.0%, verdict **HOLD** — the exact verdict the release existed to correct.

The unknown-volatility test required **both** readings to be missing:

```python
if wow is None and day is None:   # v1.513.0 -- too strict
```

AMD3's week was still unmeasurable (no week-ago snapshot carries a position re-entered on 8 Oct), but its **day happened to be a quiet −1.5%**, so the holding was certified calm and drew the loose cap again. Its real five-session move was **−29.4%**. A 3x product can post a flat day in the middle of a collapse; one day is not a volatility estimate.

### The test passed because it encoded the same wrong assumption as the code

```python
ck('only daily known, calm -> loose', _lev_cap({'wow': None, 'daily_pct': 1.0}, False)['cap'], 0.05)
```

That assertion expected `0.05`. It was written from the same mistaken belief as the implementation, so a green suite certified the defect. The assertion is now inverted, and **the four production rows from the 11:44 run are fixtures** — AMD3, MSF3, TSM3, KSTR with their verbatim `wow`/`daily_pct` values — so a test can no longer certify the bug it was meant to catch.

### Fixes

1. **The week is the primary measure.** An unknown week means unknown volatility and the tight 2.5% cap. The daily move may only **add** a storm trigger, never remove one. The reason string names the trap explicitly when a lone day is all that is on file.
2. **No raw floats in owner-facing text.** The leveraged exit sentence was printing `down -18.496439403667996% from entry`. Now one decimal.

### Effect on the live book (next scan)

| | v1.513.0 shipped | v1.513.1 |
|---|---|---|
| AMD3 cap / basis | 5.0% `calm` | **2.5% `unknown`** |
| AMD3 sizing verdict | HOLD | **TRIM $1,883 (266 sh)** |
| AMD3 exit chip | TRIM | TRIM |
| TSM3 | TRIM $3,950 `storm` | unchanged |
| MSF3 | HOLD (1.0%, under cap) | unchanged |
| KSTR cap basis | n/a (not leveraged) | `calm` — wow −6.19 is real and inside thresholds |

Both surfaces now agree on AMD3 for the first time.

### What v1.513.0 did get right — confirmed in production

- **The stale-lookback gate works.** AMD3's false `mom +34.2%` is gone, replaced by the published reason: *"held only since 2026-10-08 — the month-ago lookback (2026-09-13) predates this position"*.
- **The leverage-aware exit stop works.** It fired **TRIM** on AMD3 at −18.5% where the 50-day-average rule had said HOLD.
- **The coherence fix works.** KSTR's exit chip now reads *"…the sizing engine says WAIT, but that answers whether to BUY MORE, not whether to hold: on hold-or-sell this exit rule governs, and it says sell."*

**Tests:** 55 assertions, including the four production fixtures and two no-raw-float regressions. All passing.

## v1.513.0 / index v5.399 — 2026-10-13 — THE LEVERAGED-SIZING FAIL-OPEN

**Owner:** "go" — approved from the 13-Oct post-deploy audit.

### What the engine was telling him

The 13-Oct 08:16 run said **TRIM TSM3** (+2.7%, making money) and **HOLD AMD3** (−18%, in free-fall). Two 3x holdings, near-identical cost bases ($10,002.49 vs $10,003.59), same theme family, both flagged `leveraged: true`, opposite verdicts.

| | weight | target the engine set | over the 2.5% storm cap? | verdict |
|---|---|---|---|---|
| TSM3 | 4.1% | 2.5% (cap applied) | yes | TRIM |
| AMD3 | 3.2% | **4.0% (cap NOT applied)** | yes | **HOLD** |

### Root cause, two layers deep

**Layer 1 — the cap failed open.** The inline rule read:

```python
_fund_storm = abs(float(r.get('wow') or 0)) >= 8 or abs(float(r.get('daily_pct') or 0)) >= 6 or storm
cap = 0.025 if _fund_storm else 0.05
```

`or 0` turned an **unknown** week-over-week into a **zero** one — the calmest reading possible. AMD3 (`wow = None`) drew the loose 5% cap; TSM3 (`wow = −24.68`) drew the tight 2.5%. AMD3 had in fact fallen **29.4% in five sessions**, three times the storm threshold.

**Layer 2 — why `wow` was unknown at all.** The `px` maps inside the stored history snapshots are keyed by **ISIN**, so a position re-entered after a closed round compares against the *previous* round. The 30-day snapshot still carried AMD3 round 1 (21 Jul – 23 Sep) and published **`mom +34.2%`** on a holding 18% under water; the 7-day snapshot carried no AMD3 at all.

Net: the newest, least-understood, most leveraged position drew the most rope *and* the most flattering momentum.

### Fixes

1. **New PURE `_lev_cap()`** — unknown volatility is now a **storm, not calm**. A position whose risk cannot be measured is sized as if it were risky; that is the only assumption that cannot lose money through ignorance. It also rejects **NaN/inf**, which this function's own test suite caught sailing past both thresholds on the first run, because every comparison against NaN is False.
2. **Stale-lookback gate** on per-holding `wow`/`mom` — a lookback predating a holding's own `acquired` date describes a period the owner did not own it, so it is blanked and the reason published in `wow_basis`/`mom_basis` rather than papered over.
3. **`_exit_rule_coarse()` is leverage-aware** — a 50-day average is far too slow a stop for a 3x wrapper. AMD3's sat at **$5.99 against spot $7.12**, 16% below, so it could not be breached until the position was ~45% under water. Leveraged rows now use a loss-from-entry stop: **−12% trim, −20% exit**, stated in underlying terms (~4% and ~6.7% adverse moves, amplified three times).
4. **The 10% 3x sleeve cap now issues an instruction.** It was a note only, so the sleeve could be breached while every individual name sat inside its own cap and no trade was ever proposed.
5. **One surface, one answer** — the exit chip now carries the sizing verdict and, where they pull apart (KSTR read **EXIT** on one surface and **WAIT** on the other), states that the sizing engine answers *buy-more* while the exit rule governs *hold-or-sell*. The index's WAIT paragraph says the same in plain words.
6. **index v5.399** — the leveraged-TRIM paragraph inferred its explanation from the target number alone ("the market is rough right now"). With a second possible reason for a tight cap, that would have shipped the corrected verdict with a *wrong* reason. It now branches on `cap_basis` and quotes `cap_why`.

### Effect on the live book

| | before | after |
|---|---|---|
| AMD3 cap | 5.0% | **2.5%** |
| AMD3 sizing verdict | HOLD | **TRIM $1,883 (264 sh)** |
| AMD3 exit chip | HOLD | **TRIM** |
| TSM3 / MSF3 | unchanged | unchanged |

### Two audit claims withdrawn

Both were wrong on inspection and are recorded as wrong:

- **The "$26.33 NAV gap" is not a bug.** It is `interest_usd`; `nav = holdings_usd + cash_usd + interest_usd` reconciles to the cent.
- **The 10% sleeve cap already existed.** It had simply never fired, because the sleeve is at 8.3%.

**Tests:** 25 assertions against the real AST-extracted `_lev_cap` and `_exit_rule_coarse` (production values, every boundary, garbage inputs, backward compatibility), plus `node --check` on the index and a five-case branch test on the new reason string. All passing.

## v1.512.0 — 2026-10-13 — NETBENEFITS TRUE-UP TO THE 30-SEP STATEMENT

**Owner:** reconcile the Live Investment tab against the attached Fidelity Stock Plan Services eStatement (1–30 Sep 2026).

`_NB_FACTS` advanced from the 31-Aug seed to the 30-Sep statement:

| Field | Was (31 Aug) | Now (30 Sep) |
|---|---|---|
| APD mark | $309.46 | **$278.23** |
| APD market value | $257,470.72 | **$231,487.36** |
| APD unrealized | **+$20,593.02** | **−$5,390.34** |
| FYIXX core balance | $9,894.92 | **$9,923.18** |
| FYIXX 7-day yield | 3.44% | **3.53%** |
| 2026 YTD income | $4,682.29 | **$4,710.55** |
| Plan value | $267,365.64 | **$241,410.54** |

Shares unchanged at 832; cost basis unchanged at $236,877.70. The 30-Sep interest row (+$28.26, reinvested) is appended to the core-cash ledger. **The $25,955.10 fall is the APD price alone** — no share change, no withdrawal, no new tax in September (YTD withholding still $1,350.34).

**Reconciliation — 9 assertions, all passing:** 832 × 278.23 = statement MV; MV − cost = unrealized; APD + core = account value $241,410.54; the ledger chains row to row; ledger end = stated balance; Sep interest = $28.26; YTD income = $4,710.55; plan value = $241,410.54; period change = −$25,955.10 as the statement states.

**The projection engine validated itself.** v1.509.0 forecast September interest at **$27.12** against the actual **$28.26** — a $1.14 miss on an unseen month. It has now re-based off 30 Sep and self-corrected its inferred rate from **0.2741% to 0.2818%/month** from the newly confirmed row, exactly as designed. Its November sweep still projects **$1,054.14** against the statement's own estimated-cash-flow table ($1,506 gross × 0.70 = $1,054.20) — a six-cent agreement from two independent routes.

The `next` note now states there is **no October APD dividend**, per the statement's 12-month cash-flow table (stock income appears only in Nov/Feb/May/Aug).

No index change.

## live_portfolio.json — 2026-10-08 — AMD3 RE-ENTERED (round 2)

**Owner:** update the dashboard with the latest AMD3 trade.

Pulled live from IBKR (trades + positions + balances, 15:19 UTC):
- **BUY 523 AMD3 @ $9.4425** on 8 Oct 14:34 UTC, LSEETF, order 1667856399, commission **$4.00**, net **$4,942.43**. IBKR `average_price` 9.45014818 includes the commission, so that is the recorded `cost_price` (same convention as every other holding).
- ISIN **XS2337090422**, confirmed from the September AMD3 trade records in the payload rather than assumed — pricing is keyed by ISIN, so a wrong one would have left the position unpriced.
- `world_theme` **US-Tech** (AMD is a US company; TSM3 is Asia-Tech because TSMC is Taiwanese). Theme reuses the existing "Semiconductors / AI (3x)".
- **Holdings 8 → 9.** All nine share counts reconciled against the broker, tickers match exactly.
- **Cash updated:** AED 97,372.56, USD 9,189.83. USD fell $4,668.55 = the $4,942.43 purchase less the $271.69 ITWN dividend and credit interest. Cash in USD totals $35,700, matching the broker's BASE cash to the dollar; stock $227,614 + cash $35,700 = $263,314 against broker NAV $263,325 (the $11 is intraday FX/mark drift).
- The first AMD3 round is **renamed** "LS 3X AMD — round 1 (closed 23 Sep)" with a note, so the completed +$3,855.43 journey can never be read as the live position now that AMD3 is open again.
- The **$4.00 commission is deliberately NOT added** to `broker_costs`, which is scoped to the 1–17 Jul statement; noted in `reconciled` instead.

**Why file this by hand rather than wait:** the scanner's Flex sync does auto-add unknown positions, but it would have landed AMD3 as *"Unclassified (new via IBKR Flex)"* / `Global-Other` with no name or news query, and only after the T+1 statement. Entering it properly now gives correct classification immediately; Flex will simply confirm the share count and cost on its next sync.

No scanner or index change.

## index v5.398 — 2026-10-08 — TAB-17 DONUT: HARDCODED FUND COUNT + CASH-KEPT ARITHMETIC

Two display defects in the "where each dollar went" donut, both exposed the moment the capital ledger became complete (scanner v1.510.x + the live_portfolio.json backfill).

1. **The centre label was a hardcoded `"7 funds"`** — wrong since TSM3 was bought on 23 July. Now derived from `holdings.length` (currently 8, singular/plural handled).
2. **"Cash kept" ignored withdrawals.** It was money-in minus fund cost, so with the ledger complete it would have shown **$48,872** against **~$36,792** actually unspent — overstating cash by the full $12,080 taken out. Withdrawals now get their own amber slice ("Taken back out") and cash kept is money-in − spent − withdrawn, so the ring closes: 227,326 + 12,080 + 36,792 = 276,197 = money in.

Display-only; no scanner change (pairs with v1.510.0+). Tests: node --check; extracted real `_liMoneyViz` run against the live payload — slices sum to money-in to the dollar, fund count matches holdings, withdrawal slice present, and correctly absent when `out_usd` is 0; no nulls.

**Context:** the user reported "SINCE YOU STARTED" showing a dash. That was a stale browser page — the 11:19 scan had already written `complete: true`, `in_usd $276,197`, `true_pnl $3,056.50`. A reload fixes the dash; this wave fixes what the reload would otherwise have revealed.

## v1.511.0 + index v5.397 + live_portfolio.json — 2026-10-08 — BOTH OPEN ITEMS CLOSED

**Owner:** close the two items left open by yesterday's audit.

### 1. Opening funding backfilled (live_portfolio.json)
`capital_flows` gains the transfer that funded the account: **2026-07-02, $272,260.00**. Derived from the broker's own NAV step — IBKR net liquidation went from **$272.26 on 1 Jul to $272,532.26 on 2 Jul**, a difference of exactly $272,260.00 with no positions held that could move in price. It comprises the AED leg (AED 801,249.98 sold for $218,079.00 after spread) plus the GBP leg (~$54,181). This is a one-time historical backfill: the transfer predates the broker's rolling activity window, so v1.510.x cannot auto-harvest it; every movement from 22 Sep onward already is.

**Effect:** `capital.complete` flips to true and Tab 17's money story comes back to life — ledger of 4 flows, **$276,197 in, $12,080 out, true profit $3,056.50 = +1.11% of money put in**. (That is the money-weighted figure, which counts when cash arrived; the +2.10% time-weighted figure answers a different question — how the picks performed irrespective of flow timing. Both are correct.)

### 2. Valuation Matrix — the evidence says neither "second source" nor "quarterly"
The SCS "weekly" PDF has been frozen at **July 2, 2026 for 97 days** while every fetch returns HTTP 200 — and it has now missed a **quarterly** refresh window too, so reclassifying it as quarterly is not available either. The source is abandoned, not merely slow. Two defects followed from treating it as a single-threshold problem:
- v1.499.0's watchdog emitted the **same >30d warning for 97 consecutive days** — a line that stops being read.
- Worse, **neither Pakistan-tab renderer showed the age at all**, so July's P/E, ROE and dividend-yield screens were presented as current decision context.

**Scanner v1.511.0** — PURE `_vm_staleness()` grades the printed as-of into **fresh (<14d) / aging (14–45d) / stale (45–90d) / frozen (>90d)**, each carrying its own plain-language note stating what the reader may and may not conclude. Stamped as `psx_valuation_matrix.staleness {days,tier,frozen,label,note}` plus a top-level `.frozen`. Aging logs; stale and frozen warn in the tier's own words. The data is still carried — history is useful — only the claim that it is current is withdrawn.

**Index v5.397** — `_vmStaleBanner()` renders the tier as a colour-coded banner (grey current / amber aging / orange STALE / red FROZEN) prepended to **both** `renderScsSuggest()` and `renderPsxValQuality()`, including their empty states. Payloads without the stamp render exactly as before.

**Tests:** py_compile; 9 tier-boundary assertions + guard cases on the AST-extracted real `_vm_staleness`; live payload recomputes to `frozen` at 98 days; capital ledger re-tested with the backfill (4 flows, complete=true, sane percentage). Index: node --check; all four tiers plus absent-stamp fallback on the extracted real `_vmStaleBanner`; `renderScsSuggest` verified to carry the banner in both its empty state and its table (banner precedes data, rows intact) and to render unchanged without the stamp; Playwright screenshot of all three warning tiers eyeballed.

**Open decision, not a defect:** a replacement PSX valuation source still has to be chosen — that needs your broker relationships, not code. Until then the dashboard is honest about what it is showing.

## v1.510.1 — 2026-10-07 — FX-DRIFT DEDUPE FIX (caught by the post-deploy audit, before it did damage)

v1.510.0's `_merge_capital_flows` deduped on (date, **converted USD**, currency). That USD figure is recomputed from each run's own fx table, so the moment the AED rate moved one basis point (0.2723 → 0.2722) the **same** broker transfer produced a different key and was harvested again. A simulated next run turned the 3-flow ledger into 5 — carrying both −$7,079.65 and −$7,077.20 for the single 22-Sep transfer — and it would have compounded every day, silently corrupting every return figure the ledger feeds.

**Fix:** the key is now the SOURCE identity — date + currency + **native amount** — which no fx move can perturb. Converted USD remains only as the fallback for a flow carrying no native amount. The live 3-flow ledger is unaffected and stays correct; index v5.396 pairs unchanged.

**Tests:** five consecutive simulated runs with the AED rate drifting each time (0.2722 / 0.2725 / 0.2719 / 0.2731 / 0.2723) — ledger holds at 3 flows with 0 phantom harvests; first-harvest still produces 1 config + 2 broker = 3; a genuinely new movement is still picked up; two distinct same-day movements stay separate; capital block unchanged.

## v1.510.0 + index v5.396 — 2026-10-07 — CAPITAL-FLOW LEDGER AUTO-HARVEST + HONEST TRUE-PROFIT

**Owner found it:** the dashboard reported the live book at **−1.1%** when the real time-weighted return was **+2.1%**.

**Root cause.** `capital_flows` was a hand-maintained list in live_portfolio.json holding only the 20-Jul −$5,000 withdrawal. The broker's own activity feed carried a **22-Sep −AED 26,000 (−$7,080)** and a **29-Sep +AED 14,460 (+$3,937)** that nothing ever read — so two real cash movements were being counted as investment performance, understating every return figure on Tab 17 by ~3 points. Separately `true_pnl_pct` divided by NET flow and printed **−5,506%**.

**Scanner v1.510.0**
- PURE `_merge_capital_flows()` unions three sources: the hand-seeded config flows (history), every flow harvested on **previous** runs (carried in EXISTING — the broker's activity window is a rolling ~2 weeks, so one read can never hold the history), and this run's Deposits/Withdrawals rows. Deduped on date+USD+currency so it is **idempotent**; non-USD converted at the run's own fx table. The ledger now builds itself and never loses an entry.
- PURE `_capital_block()` replaces the inline lambda. The percentage is measured on money actually **put in**, not net flow. Crucially it applies a **plausibility gate**: recorded deposits must be ≥50% of NAV before any profit figure is published — because a small transfer *in* (the 29-Sep return of funds) otherwise made an incomplete ledger look complete and produced **+7,072%**, as absurd as the −5,506% it replaced (caught in testing). When the gate fails, both figures return None with a plain-language note naming exactly what is missing. Adds `capital.complete` and `capital.n_auto`.
- Tests: py_compile; 11 assertions on the AST-extracted real functions — merge correctness on live data (3 flows from 1 config + 2 harvested), idempotency, history preservation when the broker window moves on, new-movement harvest, unknown-currency and bad-amount guards, incomplete-ledger honesty, and the complete path. **Cross-validation: with the opening funding seeded the engine returns +2.15%, independently matching the +2.10% time-weighted return computed from the NAV series.**

**Index v5.396**
- The money-flow waterfall and the "what it is worth right now" sentence are both gated on `capital.complete`; in their place an amber panel states what is missing and how to fix it. Figures that remain trustworthy (deposits, withdrawals, money at work, today/week/month scoreboard) render exactly as before.
- Tests: node --check; both ledger states exercised against the **extracted real renderers** (`_liMoneyViz`, `_liMoneyStory`) — incomplete shows panel+note with the waterfall suppressed and no `$null`/`NaN` anywhere; complete restores the waterfall and the "2 cents gained" sentence.

**One manual step remains.** The account's **opening funding (~$272,532 on 2 July)** has never been entered in any ledger and is outside the broker's activity window, so it cannot be auto-harvested. Add it to `capital_flows` in live_portfolio.json and the true-profit figure fills in by itself; until then the dashboard honestly declines to state one.

## v1.509.0 + index v5.395 — 2026-10-07 — NETBENEFITS AUTO-SEED (no more frozen Fidelity section)

**Owner (verbatim):** "make it automatic- future all seeds"

**The problem.** Fidelity Stock Plan Services has no API (data is locked to the Akoya channel), so the Tab-17 NetBenefits block sat frozen at the last hand-seeded statement — 31 Aug. The 30 Sep FYIXX interest and the 9 Nov APD dividend sweep would both have been invisible until a manual true-up.

**Scanner v1.509.0 — `_nb_project(nb, today)` (PURE, never raises)**
- Projects the account forward from the last CONFIRMED statement using the owner's **own ledger as the model**. It infers, from the confirmed rows themselves: the APD dividend cadence (quarterly month-set from the last confirmed sweep), the pay-day (median of confirmed sweep days), the NET per-share amount (last sweep ÷ shares, withholding already embedded), and the FYIXX monthly interest rate (median of what the confirmed interest rows actually earned).
- **No new feed, no scraping, no credential, no added runtime** — and the model self-corrects at every true-up, because the inference re-reads the newly confirmed rows. (Design note: Yahoo and TradingView are both unreachable from the build sandbox, so an unverifiable external dividend feed was rejected in favour of inference that can be fully tested offline.)
- Cross-checks the inferred per-share rate against the Zacks forward estimate; raises a plain-language flag when they diverge >2% (i.e. APD changed its dividend).
- Every synthesized row carries `projected: True` and a note saying it confirms on the next statement. **The confirmed ledger is never mutated.**
- Attached as `nb.projection {rows, balance, basis, note}` + `nb.core_cash_projected` + `nb.account_total_live_projected`.
- **Validated on the live ledger:** Sep-30 interest projects **$27.12** against the block's own hand-written "~$28"; the November sweep projects **$1,054.14**, matching the hand calculation (832 sh × $1.81 × 0.70) exactly; a 12-month run produces exactly 4 sweeps in Nov/Feb/May/Aug.
- Tests: py_compile; 14 assertions on the AST-extracted real function (live case, forward case, full-year cadence, all guard paths, dividend-raise divergence flag); spliced-function identity + wiring order verified.

**Index v5.395**
- Projected rows render **beneath** the confirmed ledger in a visually separated amber band: dashed rule, "PROJECTED — NOT YET ON A STATEMENT" chip, `~` prefix on every approximate date, per-row explanation, projected closing balance, and the full how-it-was-calculated basis on hover.
- **Contradiction removed:** the hand-written `core_cash.next` line ("unchanged since 31 Aug — nothing lands between statements") is suppressed whenever a projection renders, since the band above now shows those very events. One surface, one answer.
- Payload without `projection` renders exactly as before (verified).
- Tests: node --check; jsdom (projected rows present, confirmed rows intact, row counts, absent-projection fallback clean); Playwright screenshot eyeballed — which is how the contradictory line was caught.

**Still manual (unchanged):** the statement true-up itself remains the authority — real balances, withdrawals, new grants, PSU outcomes and share-count changes still come from the statement. The projection is the bridge between statements, not a replacement for them. `_MOAT_SEED` is a separate manual block, untouched by this wave.

## v1.508.0 — 2026-10-01 — SEC WEEKLY-HEAL STAMP CARRY + HONEST PAYLOAD SENTINEL (index unchanged at v5.394)

**Owner:** "Go fix it" (the two queued fixes from the morning audit).

**Fix 1 — the daily 138s SEC crawl (root cause proven from the payload chain).** The weekly full-crawl heal fired every cold morning because the <20h carry path copied the SEC events but NOT `sec_last_full_utc` — every skipped run shipped a payload without the stamp, so next morning's EXISTING said "never healed" and all 210 names were re-crawled (138.2s / 137.7s on consecutive cold runs, names_checked 210 daily; the carried 07:01/19:27 payloads shipped the stamp as None while the 04:15 payload had it). Fix: the stamp is seeded from EXISTING at the top of the SEC section so every path (carry / index-narrowed crawl / crash-carry) preserves it; a genuine weekly heal still overwrites it. Expected: the ~54s daily-index narrow path serves 6 mornings of 7; the 138s full crawl returns to weekly — ~85s off most cold runs.

**Fix 2 — honest payload sentinel.** The 7.5MB ceiling warning measured the PRE-split serialization, but the workflow's post-scoring step already splits im3_detail (1.47MB, 374 entries) into im3_detail.json — the published data.json was 6.59MB while the scanner cried 8.01MB every run, a false alarm that would have masked real growth. The sentinel now warns on the SHIPPED size (total minus im3_detail), names both numbers, and logs both sizes quietly when under the ceiling. (Audit note: the queued "im3_detail split" build was discovered already live — workflow step + index v5.370 lazy fetch + v1.479 superset union all working; only the measurement was wrong.)

**Tests:** py_compile; stamp-carry simulated across the four-run chain (survives two carries; next cold morning takes the index path); sentinel math verified; key-function regression sweep (breakout/tech_call/pattern/candle all present, untouched).

**Verification next cold morning (04:23 UTC run):** log should show "[SEC index] N of 210 names filed recently" instead of "FULL CRAWL (weekly heal)", sec_filings stage ~54s not ~138s, and `sec_last_full_utc` present in every payload including carried runs.

## v1.507.0 + index v5.394 — 2026-10-01 — UNIVERSAL BREAKOUT RULE

**Owner (verbatim):** "The breakout calculation throughout the dashboard in all tabs is inconsistent, it should be consistent and should be calculated in a universal bonified manner and with a pill on hovering it should explain how it has been calculated."

**Audit finding — five different things rendered as "breakout":** (a) the entry ZONE (within 3% of the 52-week high); (b) the BUY verdict's "breaking out at its 52-week high" wording, which fired while price was still BELOW the high; (c) the pattern chip BREAKOUT, which fired on merely being in the zone; (d) the structure engine's resistance cleared/broken close-through; (e) Tab 9's RSI-cross "▲ BREAKOUT", a momentum signal with no price level at all.

**Scanner v1.507.0**
- PURE `_breakout_state(row)` is the single authority: **a breakout = a DAILY CLOSE above the stock's ceiling (the nearest lid overhead — 6-month swing resistance or the 52-week high), confirmed by volume above the 30-day average.** Statuses: confirmed / unconfirmed (close-through without volume — the classic trap, said so on hover) / breaking (intraday, counts only if it holds to the close) / approaching (3% zone = preparation, never a breakout) / none. Stamped `row.breakout {line, basis, status, vol_x, note}` — note carries the full how-calculated text for the hover.
- Structure now stamps BEFORE pattern; `_pattern_status(row, bk)` only labels BREAKOUT when the rule fired, else new code `breakout_zone` → "AT THE CEILING (breakout zone)".
- BUY-verdict wording: "in the breakout ZONE at its 52-week high", pointing at the pill. Logic unchanged.
- Paper-book momentum weight note "fresh breakout" → "momentum surge (RSI cross)".
- Tests: py_compile; 12 branch tests on AST-extracted `_breakout_state` + reconciliation tests on `_pattern_status`; live sweep over all 147 rows (19 approaching, 3 breaking — TXG/TWST/PBF, 0 settled confirmations, 0 label contradictions).

**Index v5.394**
- `_breakoutPill(r)`: solid green BREAKOUT ✓ confirmed / amber BREAKOUT · volume missing / blue breaking ↑ intraday · line $x / teal outline breakout zone · ceiling $x / nothing when not near. Hover = the scanner-written universal rule + this stock's numbers. On every tech strip (Tab 19 cards, every M1/M2 row), TCE/Explosive mini lines, and the technical card header. Old payloads without the stamp render as before.
- The word "breakout" is now RESERVED for the pill: the hi52 entry-zone chip renamed "52w-high zone" everywhere (strip chip, trigger panel, legends); Tab 9 RSI-cross chips renamed "▲ MOMENTUM SURGE / ▼ MOMENTUM FADE" with a hover stating they are an energy-gauge signal, not a price breakout.
- Tests: node --check; jsdom (all five pill states + strip/mini injection + all four board renderers boot on live data); Playwright screenshot eyeballed — caught and fixed a dual "breakout zone" naming collision before delivery.

## v1.506.0 + index v5.393 — 2026-09-30 — ONE-CALL WAIT-OR-BUY VERDICT, BIG PRICE, TCE + EXPLOSIVE COVERAGE

**Owner (verbatim):** "also explosive tab and all other engines like tce needs this. all factors identified but the thing missing in morning scan is the price which should be displayed in large font for reader to know and all factors calculated whats the analysis technically to wait or to buy it?"

**Scanner v1.506.0**
- PURE `_tech_call(row)`: reads EVERY factor already stamped on a timing row (entry verdict, 3-condition trigger, confirmation candle, candle-QUALITY grade, breakout/reversal pattern, chart structure) and synthesizes ONE call: **BUY NOW** (verdict BUY + trigger TRIGGERED + quality not weak/rejection), **BUY ON TRIGGER** (setup right; the why names exactly what is missing), **WAIT** (rejection candle / stretched / damaged trend, dip zone priced), **AVOID** (downtrend or reversal underway), **NO DATA**. Stamped as `row.tech_call {call,color,why}` after all other stamps. The owner's rejection-candle rule gates BUY NOW: a fired trigger on a rejection candle is a WAIT.
- Timing universe extended: TCE tier HIGH+WATCH (~28) and Explosive Signal A+B survivors (cap 40). ~18 net-new rows on live data (127 → ~145); TV-unserved names degrade to NO DATA as usual.
- Tests: py_compile; 16 branch unit tests on the AST-extracted real `_tech_call` incl. garbage-subfield hardening; live sweep over all 127 real rows (calls: 87 WAIT / 25 BUY ON TRIGGER / 12 AVOID / 3 NO DATA — no BUY NOW on a red day, correct).

**Index v5.393**
- `_bigPx(t)`: last SETTLED daily close in large bold mono (24–26px) + small live tick and day-change — on every Tab-19 actionable card and the technical card header.
- `_callChip(t)`: the tech_call as a solid color pill, hover = the one-sentence plain-language why, click = full technical card. Absent tech_call (older payload) → honest "call lands next scan" chip.
- `_pxCall(t)` (bold price + call pill) prepended to every M1 board row and M2 mini-board row.
- `_taMini(t)` (price + call + candle chips) spliced under the ticker cell of every TCE (Tab 9) and Explosive (Tab 10) row that has timing data; rows without render exactly as before.
- Tests: node --check; jsdom boot of the real page with live data.json + synthetic tech_call stamps (TCE 15 / Explosive 87 / M1 8 / M2 10 TA lines confirmed, action-strip big price confirmed, modal big price + call confirmed); Playwright screenshots of the action strip, TCE table, M1 and M2 boards eyeballed (one ternary-paren syntax bug and one pill-wrap defect caught and fixed before delivery).

## scanner v1.505.0 + index v5.392 — 2026-09-30 — Classic pattern library (owner: "research on other
chart patterns as well not just cup and handle and identify them")

Seven conservative detectors added to `_chart_structure`, on the same swing points, returning up to two as
`structure.patterns` (confirmed > testing > forming): DOUBLE BOTTOM / DOUBLE TOP (matched extremes within
3%, ≥12 bars apart, neckline from the swing between; confirmed only on the close-through), HEAD & SHOULDERS
TOP and INVERSE H&S (head beats both shoulders ≥3%, shoulders within 5%; the forming-stage note explicitly
warns never to front-run the neckline), ASCENDING and DESCENDING TRIANGLES (flat line within 2% + trending
opposite swings), BULL FLAG (≥15% pole in ≤15 bars, then a 2–10-bar drift retracing ≤40% of the pole;
target = pole above the flag top). Every hover note prices the trigger line, carries the widely-cited odds
from the standard historical pattern studies (Bulkowski), and repeats the discipline: a pattern means
nothing until its line breaks. Index: ⚑ pattern chips (bias+stage colored) on Tab 19 and every M1/M2 row;
the technical card's chart draws the primary pattern's trigger line in purple dashes.

Tests: synthetic suites for all seven (double bottom/top confirmed, H&S top confirmed w/ neckline, ascending
triangle forming, bull flag forming after the pole-base fix caught by the tests, cap-at-2, safety); LIVE
sweep on today's 40 charts found 12 real patterns — MU & ADPT double bottoms CONFIRMED, NVDA/VOXR ascending
triangles, VLO/MU/ADPT/ATRC/CVI/CAI bull flags, ERO an H&S-top warning, PBF a descending triangle. jsdom:
chips + chart line + board regressions. Supersedes today's v1.504.0/v5.391 staging; deploy this pair.

## scanner v1.504.0 + index v5.391 — 2026-09-30 — Chart-structure engine (owner: cup-and-handle and other
patterns, consolidation, higher-highs/lower-highs, and each chart's support & resistance with
broken-or-still-tested status — full technical confidence, all explained on cursor hover)

**Scanner v1.504.0:** pure `_chart_structure(closes, price)` on the same 6-month series the technical card
draws — swing points (3-bar fractal), market structure (HH·HL uptrend / LH·LL downtrend / coiling triangle /
widening), SUPPORT & RESISTANCE as clustered swing levels each stamped holding / TESTED (within 2%) /
BROKEN (violated in the last 5 sessions, with the floor-becomes-ceiling note) or cleared, CONSOLIDATION
(longest 10–30-session window inside a ≤6% band, with dollar bounds), and a conservative CUP-AND-HANDLE
detector (12–40% rounded dip, right side ≥93% recovered, 2–12% handle → right_side / rim / handle stages
with the BUY LINE priced). Every element carries its own plain-language hover note. Names without the chart
series get `_coarse_levels` (nearest MA/52-week level each way, labelled coarse). Stamped as
entry_timing.rows[t].structure alongside candle/quality/pattern.

**Index v5.391:** structure chips in the tech strip on Tab 19 + every M1/M2 row (trend shape, S/R with
status colors, base band, ☕ cup&handle with rim price); the technical card's chart now DRAWS the support
(green dashes) and resistance (orange dashes) lines with (testing)/(BROKEN) tags; legend extended.

**Tests:** synthetic uptrend/downtrend/consolidation/cup-and-handle/broken-cleared/coarse/safety suites
pass; real-data sweep: 40/40 charted names structured, live cup-and-handle hits found (XOM, CVX, ERO,
IDYA, CVI, CAI, TGTX in handle stage; GRAL, TWST at the rim). jsdom: chips, coarse chips, chart lines,
legend, boards + unstamped-row regressions. Built on the staged v1.503.0/v5.390 pair (candle quality) —
deploy this pair and everything from today ships together.

## scanner v1.503.0 + index v5.390 — 2026-09-30 — Candle-QUALITY rule (owner, verbatim: "a green daily
close above the midpoint of the prior day's range, and the close must be in the upper third of its own
range... That's a rejection candle, not a reversal, even if the close had been $2 higher" — all engines
incl. Tab 19)

**Scanner v1.503.0:**
1. The settled-bar pipeline now carries the bar's OPEN (yf batch already had it; bars + _completed_bars
   keep it as bar_open, guarded; green falls back to close-vs-prior-close on the first run).
2. Pure `_candle_quality(row)` grades the LAST COMPLETED bar: STRONG (green + close above the PRIOR day's
   range midpoint + close in the upper third of its OWN range), MIXED, WEAK (bottom third), REJECTION
   (bottom 10% of its own range regardless of level — the note carries the owner's exact reasoning and a
   ✓/✗ checklist with the % mark where it closed). Stamped per row beside candle/pattern.
3. Integration: a candle that clears close-above-prior-high but grades rejection/weak gets
   candle.quality_flag + its note extended ("HOWEVER the candle QUALITY fails your rule… treat the
   confirmation as unconvincing") — a level-only confirmation can never masquerade as conviction.

**Index v5.390:** Tab 19 cards gain a second colored line — "Candle quality — STRONG/MIXED/WEAK/REJECTION"
with the full note; M1/M2 rows gain a quality chip (★ strong / ▽ weak / ✖ REJECTION; mixed chipless), and a
quality-flagged confirmation flips the candle chip itself to "✖ rejection candle" so a rejection can never
wear a green check. Unstamped (pre-v1.503.0) rows render exactly as before.

**Tests:** the owner's exact Tuesday scenario (close above prior high BUT 9% of own range → REJECTION +
downgraded confirmation), strong/mixed/weak grades, open-fallback, legacy-bars safety, bar_open plumbing;
index — syntax, Tab-19 quality lines (REJECTION + STRONG), board chips, rejection override, unstamped-row
and board regressions. py_compile clean. Quality stamps appear from the first v1.503.0 run.

## scanner v1.502.1 — 2026-09-29 — KPMG anchors from the report's real wording (diagnostic loop closed)

The v1.499.2 payload diagnostic delivered on the 06:16 run: the report's actual sentences arrived in
bank_sector._diag_snippets and revealed why the prose anchors could never parse — the summary numbers live
in a STATS ROW ("Net Profit Deposits Gross ADR" … "8.3% 25.2% 40.3%"), deposits are never stated as a % in
any sentence, and the NPL line reads "(NPL) ratio declining to around 5.7%" with no from-clause.
`_bank_sector_parse` gains two anchors written verbatim against the captured text: the stats-row triple
(profit 8.3 / deposits 25.2 / gross ADR 40.3 — filling only still-null fields) and the declining-to-around
NPL variant. Once profit+deposit parse, the fast re-probe and the diagnostic both stop by themselves.
Unit-tested on the exact captured snippet (7 fields) + 2025-wording regression. Index untouched at v5.389.
Expected next-run result: Tab 11 strip shows profit +8.3%, deposits +25.2%, assets +19.4%, FY2025 · 22 banks.

## scanner v1.502.0 + index v5.389 — 2026-09-28 — Pattern + market-pulse layer (owner: "emas, volumes, rsis,
buy zones, sell zones... also identifying breakouts and retracements, market top and reversals" — Tab 19 + M1 + M2)

**Scanner v1.502.0** (both additive, display-only, stamped in the same pass as the v1.501.0 candle):
1. Pure `_pattern_status(row)` → entry_timing.rows[t].pattern: BREAKOUT / PULLBACK (RETRACEMENT) /
   RETRACING / STRETCHED—TOP RISK (red-day nuance in the note) / POSSIBLE REVERSAL / REVERSAL UNDERWAY /
   DEEP RETRACEMENT / NO CLEAR PATTERN, each with a plain-language note. 10-scenario unit suite passes.
2. `build_market_pulse(data)` → data['market_pulse']: ONE market-wide top/reversal verdict from the timing
   universe + gauges on file (shares overbought/oversold/broken-below-200d, breadth deceleration, positive
   sectors) → HEALTHY / TOPPING RISK / ROLLING OVER / WASHED OUT—BASING, note names the numbers. All four
   regimes unit-tested on synthetic universes; on today's REAL data it reads HEALTHY (6% ob, 24% <200d).

**Index v5.389:**
- `_techStripRow`: compact chip strip on every Tab-19 card and every M1/M2 board row — pattern chip first,
  RSI thermometer (oversold/calm/warm/overbought), price-vs-20/50/200-day checks (20d✓ 50d✓ 200d✗), the
  two BUY ZONES as price bands (active one highlighted), the SELL LINE ("if it CLOSES below this, the idea
  is wrong — exit"), volume-vs-30-day-average. Every chip self-explains on hover.
- `_pulseBanner`: the market top/reversal gauge as a color-coded banner in three places — Tab 19 under the
  Actionable legend, and atop both the M1 and M2 boards.
Verified: py_compile + full unit suites; node --check; jsdom boot (Tab-19 card carries pattern+RSI+EMAs+
zones+sell line+vol+candle; pulse banner on all three surfaces; absent-pulse silent; renderTopDown
regression); rendered in chromium and eyeballed; live-data screenshot shipped. Chips appear after the first
v1.502.0 run stamps the payload.

## scanner v1.501.0 + index v5.388 — 2026-09-28 — Confirmation-candle layer + verdict-first M1/M2 boards

Owner: the Tab-19 technical layer, and specifically the candle rule in his own words ("No confirmation
candle. Today is a big red day. The rule is a daily close above the previous day's high. That can't happen
before Tuesday at the earliest"), must appear in Tab 19 AND in M1/M2 — on the approved verdict-first design.

**Scanner v1.501.0:**
1. Pure `_candle_status(row)` — states the candle rule per stock in plain words from settled-bar fields the
   timing engine already computes: confirmed / forming ("only counts if it HOLDS to the close") / waiting,
   and on a red day names the earliest possible print day, weekend-aware ("cannot happen before Tuesday's
   close at the earliest"). Stamped as entry_timing.rows[t].candle; display-only, arbitration untouched.
   Unit-tested on the owner's exact red-Monday scenario, weekend skip, all five states, missing-data safety.
2. Timing universe extended: + top-60 of each M2 watch list + the M1 buys (deduped, ~103→~190), so Tabs 6/8b
   carry the SAME verdict + candle as Tab 19 instead of pretending timing stops at Tab 19.

**Index v5.388:**
- Tab 19: every card's trigger block ends with a color-coded CANDLE CHECK sentence.
- Tabs 6/8b rebuilt to the approved mockup: question headlines, auto-written TODAY'S BOTTOM LINE (including
  which names read BUY on timing — or plainly that none do: "quality alone is not an entry"), the M1 funnel,
  ENGINE'S OWN PICKS vs YOUR OVERRIDES split with 80–100-zoomed score bars, per-row timing pill
  (click-through to the Tab-19 chart card) + candle chip + full candle sentence; M2's one-bar market-health
  split + TOP-FLAGGED mini-boards (top 5 quality + top 5 turnaround by signal count) with the same TA per
  row; "no timing data" stated honestly where the scan can't serve a name.
- Bug fix: Tab-8b explainer showed literal escape text (\u25b2/\u26a0) instead of ▲/⚠ — now HTML entities.

Verified: py_compile + candle unit tests on the real extracted function; node --check; jsdom boot of the
real page + real payload (boards, Tab-19 candle line via _etTrigLine, renderTopDown regression, pending
states); rendered in real chromium and eyeballed; live-data screenshot shipped. Note: candle chips/sentences
appear after the FIRST v1.501.0 scanner run stamps the payload; until then rows show the timing pill only.

## index v5.387 — 2026-09-28 — M1/M2 hero boards (owner: "this should also be in m1 and m2 as per their results")

Display-only; scanner stays v1.500.0. The v5.386 visual language extended to both sleeve engines, each in
its established tab colour (M1 teal, M2 orange — the v5.209 convention):
- **Tab 6 (M1):** teal banner "DISCIPLINED SLEEVE · THE STEADY 70%", five KPI cards from m1_buylist
  (macro regime, favored sectors w/ list on hover, eligible pool, buy-list count, quality-gate mark), and
  THIS RUN'S BUY LIST as a ranked leaders board — rank circles, deep-quality gradient bars, grade, amber
  "off-regime" chips for override entries, peer-position pill + data chip per row.
- **Tab 8b (M2):** orange banner "SPECULATIVE SLEEVE · THE 30% ENGINE", four KPI cards (whole market
  scored, disciplined ≥ gate, speculative < gate, flagged-for-review from m2_watch), and a NEW
  score-distribution column chart of m2_universe.dist — direct count labels, green at/above the gate,
  dashed gate line, plain-language read on breadth of market quality.
Verified: node --check; jsdom boot on the real page + real payload (both boards assert-pass incl. TSM row
and 11 histogram columns; absent-feed pending lines); rendered in real chromium and eyeballed — live
screenshot shipped. Live render surfaced a real insight immediately: 6 of 8 M1 buys are off-regime
overrides, now visible at a glance.

## index v5.386 — 2026-09-28 — Decision-board graphics rebuild (owner: "the graphics are pathetic, take inspiration from the pictures I attached")

Display-only; scanner stays v1.500.0. The four v5.385 panels rebuilt to the DeepAnalytics visual standard:
- **Cycle maps (Tabs 2/3):** navy gradient banner, real SVG speedometer gauge (four colored arc segments,
  active phase enlarged, needle driven continuously by the same Economy Clock angle — still one gauge, one
  answer), phase table with phase-colored NOW column header, zebra rows.
- **Sector board (Tab 15):** navy banner + eyebrow, five KPI cards with tinted icon badges, NEW diverging
  YTD bar chart (zero baseline, rounded data-ends, dashed navy S&P reference line, fixed value column),
  heat table with zebra + bold YTD, TOP/BOTTOM-5 boards with gradient headers + numbered rank circles,
  auto KEY TAKEAWAYS box (leader / laggard / breadth-narrowness in plain words).
- **Gauge check (Tab 2):** green pill w/ check icon on agree; bold amber banner w/ icon on disagree.
- **Peer pills (Tabs 19/6):** solid percentile-colored score chip (#1/58 white-on-gradient) + track bar +
  "N% data" chip.
Phase palette (#16A34A/#0EA5E9/#F59E0B/#DC2626) machine-validated CVD-safe; low-contrast segments carry
text labels per the relief rule. Verified: node --check, jsdom boot on the REAL page + REAL live payload
(all panels assert-pass, renderTopDown regression, absent-feed honesty), then RENDERED IN REAL CHROMIUM and
eyeballed — two visual defects caught and fixed before delivery (gauge edge labels clipped; a positive
laggard value printed red). Screenshot of the live-data render shipped alongside.

## scanner v1.500.0 + index v5.385 — 2026-09-28 — Decision-board wave (owner: "consolidated scanner covering all above builds with stunning graphics")

The DeepAnalytics-comparison items, built as one consolidated pair.

**Scanner v1.500.0** (all additive — no existing engine, score, rank or display field changed):
1. **Sector peer-position + coverage** — build_m2_universe stamps every scored name (FULL pre-cap
   universe ~1,873; the shipped top-250 alone cannot know "#4 of 619") with sector_rank/sector_n/
   global_rank + coverage_pct (share of the 13 keystone inputs present), and ships a compact
   `sector_positions` per-ticker lookup (~35KB). `_apply_sector_positions` copies the stamps onto
   Tab 19 recommended rows and Tab 6 M1 buys — runs in the post block AFTER recommended exists
   (order-proof by reading `data`; the v1.484/1.494 lesson applied at design time).
2. **Sector returns board** — `fetch_sector_returns`: one TradingView batch over the 11 SPDR sector
   ETFs + SPY (proven request shape) → `sector_returns` {Today/1M/3M/YTD/1Y rows, S&P yardstick,
   top/bottom-5, positive-breadth}; <6 sectors = failure; failure carries last-good.
3. **Gauge-coherence guard** — pure `_cycle_coherence` compares the breadth gauge (us_diffusion)
   against the Economy Clock's growth needle every run → `cycle_coherence.us`; meta warning on
   disagreement. Silent agreement, loud disagreement — the DeepAnalytics two-tabs-two-verdicts
   failure made impossible here.

**Index v5.385:**
- Peer-position pills ("#4 of 619" + gradient percentile bar + "data N%" coverage chip) on Tab 19
  Actionable cards and Tab 6 M1 rows, plain-language hovers throughout.
- Cycle-phase maps on Tab 2 (US) and Tab 3 (PSX): sector-by-phase leadership grid with the CURRENT
  column highlighted from the clock's own needle angle — one gauge, one answer.
- Sector returns board on Tab 15: hero stat chips, heat-colored returns table with S&P row, TOP/
  BOTTOM-5 signed gradient bars; honest "live feed pending" until v1.500.0 has run once.
- Coherence line atop Tab 2: quiet green when gauges agree, loud amber banner when they disagree.
- All renderers: own local esc, errors surfaced INTO the container, honest pending lines.

**Tests:** scanner — py_compile clean; unit tests on real extracted functions (sector returns parse on
synthetic TV payload incl. leader/laggard/breadth; coherence agree/disagree/missing-safe; position
stamping incl. case-insensitive + unknown-ticker untouched; ranking math). Index — node --check on the
full script; REAL page booted in jsdom against the REAL live data.json + synthesized v1.500.0 keys:
all four renderers assert-verified (US phase "Mid cycle" and PSX "Late cycle" derive correctly from the
live clock angles), agree + disagree + all absent-feed pending states, pill output, and regression on
renderTopDown (487KB output, pill present) + _etActionStrip (31KB, badges intact).

## scanner v1.499.2 — 2026-09-28 — KPMG anchor-gap diagnostic (owner: yes)

The 09:02 run proved the 2026 edition landed (as_of 2025-12-31, 22 banks, assets +19.4%, KSE 174,054) but only
3 of 8 fields parsed — the report's real wording for profit/deposits/NPL differs from the second-hand wording
the anchors were built against, and neither the PDF (sandbox egress blocked) nor the Actions log (HTTP 403) is
readable from the build side. Two additive, self-limiting changes:

1. **Payload diagnostic:** when an accepted parse still leaves profit/deposit null, the pure
   `_bank_sector_diag` ships ±160-char windows around each anchor keyword from the real report text into
   `bank_sector._diag_snippets` (~3KB cap) — data.json is pullable, so the exact sentences can be read and the
   anchors fixed against them next version. Renderer reads named keys only; never displays.
2. **Re-probe cadence:** while core fields are missing, the fetch throttle drops from 30 days to 18 HOURS
   (hours, not whole days — a 24h-cadence run lands at ~23.x elapsed hours, which a whole-days `<1` check
   would skip forever). Returns to 30 days the moment profit+deposit parse; the diag key stops being written.

Tests (real extracted functions, stubbed network/PDF): diag windows capped and keyword-bearing; partial cache
at 20h → re-probe fires; same-day rerun → 18h floor holds (no hammering); complete cache → 30d throttle back;
old-edition bypass regression intact; end-to-end accepted-partial parse ships snippets in payload. py_compile
clean. Index unchanged at v5.384.

## scanner v1.499.1 — 2026-09-28 — Throttle-order fix (caught by the post-deploy audit of the 08:48 run)

Payload ground truth from the first v1.499.0 run: `bank_sector._fetched_utc` unchanged at 25-Sep — the fetch
never ran. The 30-day throttle sat AHEAD of the new candidate-URL list, and the cache's stamp was only 3 days
old (from the old code re-fetching the OLD edition), so the run skipped straight past the 2026 URL and would
have kept skipping until ~25 Oct. The throttle now applies ONLY when the cache is already on the newest
candidate's as_of; an older-edition cache bypasses it with an explicit log line and fetches immediately.

Verified by executing the REAL function with stubbed EXISTING/requests: old-edition cache + fresh stamp →
fetch attempted (2026 first); newest-edition cache + fresh stamp → throttled, zero fetches; newest-edition
cache + 40-day stamp → re-fetch; failure path → last-good carried. py_compile clean.

Also confirmed on the live 08:48 run: the v1.499.0 valmatrix staleness stamp is WORKING (stale_days=88 on the
payload, warning present in meta.warnings). Index unchanged at v5.384.

## scanner v1.499.0 — 2026-09-28 — Stale-source pair (owner: "fix it", from the 27-Sep all-tabs audit)

**Item 1 — Tab 11 bank sector (was 635 days stale).** Root cause: the KPMG fetcher was hardcoded to the
2025 edition (FY2024 data) and re-fetched that same PDF every 30 days forever — `_fetched_utc` stayed fresh
while `as_of` sat at 2024-12-31. Fix: `fetch_bank_sector_kpmg` now tries the newest edition first
(Pakistan-Banking-Perspective-**2026**, CY2025 data, 22 banks — URL confirmed live before build) with 2025 as
fallback; each candidate stamps its own `as_of`/`source`. Parsing extracted to the pure `_bank_sector_parse`
with anchors covering BOTH editions' wording (2026 changes verified against the real report summary: profits
as PKR levels → % computed, "total assets increased by approximately X%", NPL as a ratio move → additive
`npl_ratio_pct`/`npl_ratio_prev_pct`, "closing 2025 at N points"). ≥2-fields acceptance gate kept per
candidate — a wording miss can only carry last-good, never poison. No index change needed (null tiles hide;
FY label and bank count derive from the payload).

**Item 2 — PSX valuation matrix (frozen at "July 2, 2026" for 88 days).** Root cause: the broker (SCS)
stopped updating the weekly PDF — the fetch kept succeeding (HTTP 200, 162 tickers, last_fetch 23-Sep), so
nothing flagged it. Fix: new pure `_vm_stale_days` parses the printed as-of; the call site stamps
`psx_valuation_matrix.stale_days` every run and raises a meta warning when a weekly product is >30 days old
(same honest-staleness pattern as the bank-sector 400-day stamp). The broker resuming publication is the only
true cure; until then the dashboard says so instead of silently showing July numbers.

Tests: py_compile clean; unit tests on the real extracted functions — 2025 wording regression (8 fields,
identical result set), 2026 wording (7 fields incl. computed profit +8.4%), garbage rejection (<2 fields →
last-good), stale-days parse (88 today) + None/empty/garbage/abbreviated-month edges. Live KPMG fetch could
not be exercised from the build sandbox (egress blocked); the runner proves it next run — worst case is
carry-last-good by construction. Index unchanged at v5.384.

# Dashboard Changelog

Format: newest first.

---

## scanner v1.498.0 — 26 Sep 2026

**Fixed a rule I missed.** The exit-rule layer (below) had defaulted the 10 PSX paper-book names to "no data" instead of trying the dashboard's own standing PSX price source (TradingView). Fixed: PSX names now get the same trailing-stop check as the ETF holdings on **Tabs 1–2** (price vs 50-day average) — but with a real overbought check too, since TradingView also supplies RSI for these names, something the ETF holdings don't have. A genuine feed failure still shows honestly as "no data" rather than being hidden.

## scanner v1.497.0 + index v5.383 — 26 Sep 2026

**Four-item wave + a labeling fix.** (1) Fixed the run-timing math so it can never report an impossible negative number for unaccounted time, on **any tab that shows scan diagnostics**. (2) Checked whether the SEC insider-filing check runs too often — it doesn't; left alone. (3) Added a concentration cap on **Tab 19** so one sector can't fill the whole "buy today" list. (4) Built the exit-rule layer: every held or paper-tracked position on **Tabs 1–2 and Tab 17** now carries a HOLD / TRIM / EXIT signal with a trailing stop, labeled by how much data backs it. (5) Fixed a mislabeling on **Tab 19** where stocks freshly hitting a 52-week high were wrongly called "repairing" because of an old, unrelated all-time high.

--- Each entry names the scanner and/or index version, the date, and what changed in plain language, with the tab it affects. This file was not staged during the last several deploys — the entries below back-fill that gap from the actual `SCAN_VERSION` / `index.html v` strings shipped, cross-checked against the live `data.json` after each run.

---

## scanner v1.496.0 + index v5.382 — 26 Sep 2026

**Verdict-on-completed-bar fix + stable demotion flag.** A two-run audit caught two real bugs:
- The daily BUY/WAIT/AVOID call on **Tab 19** was still reading the live, mid-session price tick instead of yesterday's settled close — so a name could flip from BUY to WAIT and back within the same afternoon with no new trading day. Fixed: the verdict is now recomputed once the settled daily bar lands, and the technical card states plainly when the live tick disagrees with the settled call ("the settled verdict is WAIT... the live tick alone would read AVOID — shown for comparison only").
- The rule that penalizes a "trend damaged" name in the ranking was matching on a snippet of sentence text, which meant a one-cent price tick could silently flip whether a stock got penalized at all (found on DVN). Fixed in **two places** — the main ranking and the paper-book sizing — to key off a stable internal flag instead of the sentence.

## scanner v1.495.0 — 25 Sep 2026

**Fixed the same-run re-ranking I shipped the day before.** The v1.494.0 fix (below) called the re-ranking function 24 lines before the data it needed was actually saved, so it silently ran on empty data every time — 13 stocks flagged AVOID on **Tab 19** stayed ranked as if nothing were wrong. One-line fix: moved the call to after the data exists. Confirmed on the next live run: 0 inconsistent names, down from 13.

## scanner v1.494.0 + index v5.381 — 25 Sep 2026

**Entry-trigger correctness fix.** The three-condition buy trigger added in v1.493.0 (below) was comparing the day's price and volume against a full-day average while the market was still open — so every single recommended stock showed volume at 10–30% of normal and none could ever trigger. Fixed: the three conditions now judge the **last completed daily bar**, not the live tick; the technical card on **Tab 19** states which bar it judged and shows the live price separately, labelled "now (intraday)". Also added: the cash line now says how many positions your deployable cash actually covers at the sized amount, and the "Actionable today" cards are ordered closest-to-buy first.

## scanner v1.493.0 + index v5.380 — 25 Sep 2026

**Entry-trigger layer (owner-requested) + a regression fix.** Added the three-condition entry trigger to **Tab 19**: (1) price in a pullback or breakout zone, (2) a daily close above the prior day's high, (3) volume above the 30-day average — all three met shows TRIGGERED, with a sized buy plan (dollars, shares, stop, two tranches) computed from the live cash figures on **Tab 17**. Also fixed a regression from the prior build (v1.492.0) that had silently blanked the entire Recommended Stocks list on **Tab 19** — a miskeyed dictionary entry caused the ranking function to fail in 3 milliseconds with no visible error.

## scanner v1.492.0 + index v5.379 — 25 Sep 2026

**Decision wave — coherence, calibration, and the "Actionable today" strip.** (1) The falling-knife / insider-selling penalties that were only ever shown on **Tab 19** now live inside the ranking itself, so the number and the label can never disagree. (2) A calibration loop: while the TCE engine's HIGH-conviction tier is still 0-for-10 on its own scorecard (**Tab 9**), its vote in the ranking is discounted. (3) The paper-book model portfolios (**Tabs 1–2**) now obey the same penalties. (4–9) Efficiency and housekeeping: the MOAT-holdings fetch (**Tab 22**) skips funds that have returned nothing for two runs running, off-exchange pricing and ETF fee lookups go through TradingView first, and the stale bank-sector data notice on **Tab 11** now states its own age. (10) A new "Actionable today" strip on **Tab 19**: the handful of names that clear every gate at once — engine agreement, quality grade, buy timing, and not flagged — with a concentration line showing where the live book (**Tab 17**) is piled up by sector and theme.

---

*Earlier history (scanner v1.480–v1.491, index v5.371–v5.378: Fidelity reconciliation, IBKR settlement-truth, the position-journey chart, the oil-trend authority switch, the Yahoo→TradingView cut) is recorded in the project's Decision Record, not repeated here.*
