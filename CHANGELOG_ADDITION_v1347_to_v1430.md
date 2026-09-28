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
