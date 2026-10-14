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
