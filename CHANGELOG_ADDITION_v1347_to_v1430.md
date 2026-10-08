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
