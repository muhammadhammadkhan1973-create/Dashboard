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
