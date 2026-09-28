# TC — Tight Coil / Base tools  (DRAFT, not yet compiled in TradingView)

Two new Pine v6 indicator + Pine Screener scripts built from two Voyage Trading
Group cards. Everything is prefixed **`s-TC` / `TC`** (titles, labels, alert
names, screener columns) so nothing collides with `IO_vtg/` (s-VTG Combo,
s-VTG ATR) or `oliverKell/` (s-OK Cycle).

| File | Script name | Card |
|---|---|---|
| `tcContractionExpansion.pine` | `s-TC Contraction Expansion` (`TC ContrExp`) | "VTG Breakout Signal — Old vs New" (`gd_systems/tradying_voyage/HS2aXjWbIAAoVyX.jpeg`) + book rules + dashboard "Tight & orderly" stage |
| `tcCoilBreakout.pine` | `s-TC Coil Breakout` (`TC Coil`) | "Best actual breakout: tight coil under resistance" — `gd_systems/tradying_voyage/HS7qCHxbMAAaN8g.jpeg` |

Both are **daily-oriented**, use **no `request.*`** (screener-safe), and every
threshold is **our own reading of the card's bullets** — the cards give no numbers.

---

## Shared conventions

```
atr        = ta.atr(atrLen)                    // atrLen = 14
rng        = high − low                        // bar range
ok(x)      = x is not na and x ≠ 0
brk(lvl)   = (confirmBody ? min(open, close) : close) > lvl     // close-confirmed break
             // confirmBody = false by default → the close must be above the level
```

- All distances are in **ATR units** (same engine idea as s-VTG ATR / s-OK Cycle).
- Signals are **close-confirmed** (they can flicker on the forming bar, final on close).
- **Cooldown** per signal: after a signal fires, the same signal is suppressed for
  `cooldown` bars (default 3). Each signal has its own counter.
- **Show switches** only hide the visuals; the screener/alert columns are always computed.
- Screener: `alertcondition()` → True/False filter (not a column);
  `plot(..., display.none)` → numeric sortable column.

### "Longest qualifying window" search (used by both scripts)
Both scripts look for a base/coil **ending on the current bar**, test every length
`n` from `min` to `max`, and keep the **longest** `n` that passes all conditions.
Running stats are accumulated in one loop over bars `0 … max−1`:

```
hiH = max(high[0..n−1])     loL = min(low[0..n−1])
hiC = max(close[0..n−1])    loC = min(close[0..n−1])
```

The breakout is then tested on the **next** bar against the base/coil that ended on
the **previous** bar (`base[1]`, `baseHi[1]`, …).

---

## 1. `tcContractionExpansion.pine` — s-TC Contraction Expansion  (3 methods side by side)

One indicator, three ways of defining a tight base, so they can be compared on
the same chart:

| Method | Source | Base | Trigger |
|---|---|---|---|
| **OLD** | card left column = book's "fast version" | 4/9 EMA compression + tight last candle | **Expansion**: EMA expansion, Day + Body Range Expansion ≥ 0%, rising ATR, VTG ATR green zone |
| **NEW** | card right column (updated rules) | 3+ day base: pullback toward a rising 21 EMA, tight controlled closes, ATR decreasing (older-book extras optional) | **Confirmation**: close above the base high, strong close, volume, rising ATR |
| **T&O** | dashboard-screener workflow "Trading Voyage (Ollie)", stage **Tight & orderly** | RTI(50) zone 1–2 AND Golden Launch Pad (1:1 port) | none of its own; optional `T&O BO` = the NEW trigger over the prior day's high |

**The card beats the book.** The card is the newer version. Book rules missing from the card are optional and off.
Provenance tags in the input tooltips: **(book)** = *Momentum Trader's Guide* (older)
(`python/sandBox/Oliver_wiedmeier/ollie_screening_workflow.md` §5.3–5.4),
**(card)** = card bullet, **(ours)** = our own number.

### Tightness unit

`unit = '%'` (default, the book's way) or `'ATR'`. It applies to the two-close test
and to both EMA-compression tests:

```
tight(d, kPct, kAtr) = unit == '%' ? d / close × 100 ≤ kPct : d ≤ kAtr × atr
```

### OLD — base + trigger

```
ema4, ema9 = EMA(close, 4), EMA(close, 9)          spread = ema4 − ema9

oldComp = tight(|spread|, 1.0 %, 0.5 ATR)           // 4 & 9 EMA squeezing (book 1%)
sqBars  = consecutive bars with oldComp, ending on this bar
oldBase = sqBars ≥ oMinSq                           // min squeeze bars (default 1)
      and rng ≤ 0.8 × atr                           // last candle tight (card; 0.8 ours)
          [and rng < rng[1]]                        // optional "narrower than the one before"

dayExp  = (rng  / rng[1]  − 1) × 100                // Day Range Expansion %   } KEEP IN SYNC with
bodyExp = (body / body[1] − 1) × 100                // Body Range Expansion %  } IO_vtg/visual_vtgAtr.pine
d21     = (close − EMA21) / atr                     // same as the VTG ATR 21 EMA row
d50     = (close − SMA50) / atr                     // same as the VTG ATR 50 SMA row
greenZone = 0 ≤ d21 ≤ 3  and  0 ≤ d50 ≤ 5           // VTG ATR green cells (below the MA = red)

OLD BO  = oldBase[1]                                // EXPANSION — no level, no volume
      and spread > 0 and spread > spread[1]         // EMA expansion, up (card)
      and dayExp  ≥ 0 %                             // range expands vs prior day (card), toggle
      and bodyExp ≥ 0 %                             // body expands too (VTG ATR), toggle
      and atr > atr[1]                              // rising ATR (card)
      and greenZone                                 // not extended (VTG ATR), toggle
      [and close > high[1]]                         // optional direction filter (ours, off)
      [and bookOK]                                  // optional book filters (off)
```

`≥ 0 %` is coded as `rng ≥ rng[1]` / `body ≥ body[1]`. That's the same test, but it
also works when the prior bar is a doji (prior body 0 → passes). The table shows the
`%` values exactly as the VTG ATR table does. The green-zone gate applies to **OLD
only** for now.

### NEW — base

The card is the **updated** rule set. The book (*Momentum Trader's Guide*) is the
older version, so it only supplies numbers the card lacks, and its extra rules are
optional and **off**.

Card rules, per candidate length `n` in `[3 … 10]`. The **longest** passing `n` is kept:

| Card bullet | Formula | Default | Number from |
|---|---|---|---|
| 3+ day base | `nBaseMin ≤ n ≤ nBaseMax` | 3 … 10 | card (max 10 = book) |
| Pullback toward the 21 EMA | `min(low − ema21) ≤ 1.0 × atr` | 1.0 ATR | ours |
| (closes hold the EMA) | `min(close − ema21) ≥ −1.0 × atr` | 1.0 ATR | book |
| Tight, controlled closes | `max(close) − min(close) ≤ 1.0 × atr` over the base | 1.0 ATR | ours |
| (21 EMA rising, as drawn) | `ema21 > ema21[n]` | on | card drawing |
| ATR decreasing | `atr < atr[n]` | on | card |

Older-book extras (group `NEW — base, older-book extras`, all **off**):

| Rule | Formula | Default when on |
|---|---|---|
| Last 2 closes within 1% | `|close − close[1]|` tight in the unit | 1.0 % (or 0.3 ATR) |
| 4/9/21 EMA springboard | `max(e4,e9,e21) − min(e4,e9,e21)` tight in the unit | 1.0 % (or 0.5 ATR) |
| Volume contraction | `mean(volume[0..n−1]) / SMA(volume,50)[n] < 1` | — |
| ≥ 20% leg before the base | `baseHi / lowest(low, 63)[n] − 1 ≥ 20 %` | 20 %, 63 bars (ours) |

### NEW — trigger  (shared with T&O BO)

```
trig(level) =                                        // CONFIRMATION
      close > level                                  // breakout candle confirms (card) — NEW: base high · T&O: prior high
  and (high − close) / rng ≤ 30 %                    // strong close (card; 30% = book)
  and volume ≥ 1.0 × SMA(volume, 50)                 // + volume (card; ≥ average = book)
  and atr > atr[1]                                   // rising ATR (card)
  [and bookOK]                                       // optional book filters (off)
NEW BO = newBase[1] and trig(baseHi[1])
```

### How OLD and NEW differ

| | OLD (expansion) | NEW (confirmation) |
|---|---|---|
| Needs a price level | no (only the optional prior-high filter) | yes, close above the base high |
| EMA expansion | yes | no |
| Day + Body Range Expansion ≥ 0% | yes | no (book filter only) |
| VTG ATR green zone (0–3 / 0–5 ATR) | yes | no (book filter only) |
| Close position | no | top 30% of the bar |
| Volume | no | ≥ average |
| Rising ATR | yes | yes |

### Book entry filters (optional, `Apply to OLD` / `Apply to NEW / T&O`, both off)

From book §5.3–5.4 (Continuation Breakout candle + Jack-in-the-Box):
```
bookOK = rng > rng[1]  and  body > body[1]  and  ema4 > ema4[1]
     and d21 < 3 ATR  and  d50 < 5 ATR          // d21 = (close − EMA21)/atr, d50 = (close − SMA50)/atr
```
Each part has its own toggle. Turning them on for both methods makes them converge. That's why they are off by default.

### T&O — "Tight & orderly" stage, 1:1 port

Python stage (`python/dashboard-screener/config.py`, workflow `Trading Voyage (Ollie)`):
`advanced = {adv_rti_zone: ['1','2'], adv_gold_launch_pad: True}`. Its own note
says it is a proxy for "Ollie's 2-days-tight + 4/9/21 EMA squeeze".

**RTI** (`src/focus/rti.py`). This is not the 0–100 TradingView RTI oscillator used in s-VTG ATR v2.
```
RTI(50) = SMA(high − low, 50) / hlc3 × 100
zone 1: RTI < 5 · zone 2: < 10 · zone 3: < 15         → rtiOK = zone 1 or 2
```

**Golden Launch Pad** (`src/leaders/gold_launch_pad.py`), EMAs 10/20/50:
```
z_p     = (EMA_p − SMA(EMA_p, 51)) / STDEV(EMA_p, 51)          // population stdev (ddof=0)
grp     = max(z) − min(z) ≤ 1.0                                 // tightly grouped
stk     = EMA10 > EMA20 > EMA50                                 // bullishly stacked
slp     = OLS slope of each EMA over int(p×0.3)+1 bars > 0.0001 // 4 / 7 / 16 bars
          (Pine: linreg(e,n,0) − linreg(e,n,1) = slope per bar)
>10     = close > EMA10
near    = |close − mean(EMA10,20,50)| ≤ 2.0 × STDEV(close, 20)  // sample stdev (ddof=1)
glpOK   = grp and stk and slp and >10 and near
score   = clip(1 − spread / 1.0, 0, 1)
```

**Optional upstream stages** (`Include upstream stages`, off). They follow the same funnel as the Python workflow:
```
Universe  : 20d ADR% (SMA(H−L,20)/close×100) in [3, 60], SMA(close×volume,50) > $1M,
            close > SMA50 and close > SMA200        (the Python 2A/2B stage filter is NOT ported)
Momentum  : close ≥ 30% above lowest(low,21)  OR  50% above lowest(low,63)  OR  100% above lowest(low,126)
```

```
T&O    = rtiOK and glpOK [and Universe and Momentum]
T&O BO = T&O[1] and trig(high[1])                      // optional, off by default
```

Known small differences from the Python run:
- Python EMAs are `ewm(adjust=False)`, seeded with the first close. Pine's `ta.ema` is seeded with an SMA. The difference disappears after a few hundred bars.
- Python evaluates only the last bar. Pine evaluates every bar, so on the chart you see the history.

### On screen

| Element | What it shows |
|---|---|
| Lines | 4 EMA blue, 9 EMA red, 21 EMA green (thick); optional GLP 10/20/50 EMAs in orange shades |
| Blue dot below bar | OLD base bar |
| Dashed green box | NEW base currently forming (last bar) |
| Solid green box | NEW base behind each NEW breakout |
| Orange background | T&O state |
| Labels / bar colour | `TC New BO` green · `TC Old BO` blue · `TC T&O BO` orange · magenta if more than one fire on the same bar |

**Comparison table (bottom-right).** Green = pass, red = fail.

| Row | Value |
|---|---|
| BASE NOW | `Old ✓/✗   New ✓/✗   T&O ✓/✗` |
| OLD 4/9 gap | `|ema4 − ema9|` in the unit + `(k b squeeze)` streak |
| OLD candle range | `rng / atr` |
| Day range exp | `dayExp` %, green ≥ 0 |
| Body range exp | `bodyExp` %, green ≥ 0 |
| NEW base | `YES n bars  pivot <baseHi>` |
| NEW base close span | `(max close − min close) / atr` of the base |
| NEW last 2 closes | `|close − close[1]|` in the unit (coloured only when that extra is on) |
| NEW 4/9/21 spread | EMA spread in the unit |
| NEW ATR now / start | `atr / atr[n]`, ↓ = contracting |
| NEW base vol / avg | base mean volume / 50-day avg |
| NEW leg before base | % |
| Ext 21 / 50 | `d21 / d50` in ATR, green in the VTG ATR green zone (0–3 / 0–5) |
| T&O RTI(50) | value + zone |
| T&O GLP z-spread | spread + score |
| T&O GLP checks | `grp✓ stk✓ slp✗ >10✓ near✓`, shows which GLP condition fails |
| T&O upstream | `univ ✓ mom ✓` (only when enabled) |
| Last signal | New / Old / New + Old / T&O `(k b ago)` |

### Screener columns

Filters (True/False, same pattern as s-VTG Combo). Pick one in the Pine Screener and set it to **True**.
"Triggered" = the breakout happened on the last bar. "Qualified" = the setup is there now and you're waiting for the breakout.

| Filter | True when |
|---|---|
| `TC Any Triggered` | any of the three breakouts fired on the last bar |
| `TC Old (Squeeze Expansion) Triggered` | the OLD expansion bar fired |
| `TC New (Base Breakout) Triggered` | it closed above the NEW base high |
| `TC T&O Breakout Triggered` | the T&O breakout fired |
| **`TC Tight Setup (any) Qualified`** | **any of the ticked setups is present now** (default: Old base, New base, T&O, Golden Launch Pad; RTI 1-2 off). Tick/untick them in the settings group *Tight Setup (any)*. Made for pre / post market runs: the last daily bar is the completed session, so it lists what is tight right now, no breakout needed |
| `TC Old Base Qualified` | the 4/9 EMA squeeze is present now |
| `TC New Base Qualified` | a NEW base has formed and hasn't broken out yet |
| `TC T&O State Qualified` | the stock is in the "Tight & orderly" state |
| `TC Golden Launch Pad Qualified` | the Golden Launch Pad check passes |
| `TC RTI zone 1-2 Qualified` | RTI(50) is in zone 1 or 2 |

After any edit to the script: remove it from the screener, add it back, then press **Scan** (the screener caches the compiled script; columns show `—` until you scan).

Numeric (addable via Manage columns; `> 0` on a 1/0 column = the same as the True filter): `TC Signal (any) 1/0`, `TC New BO 1/0`, `TC Old BO 1/0`, `TC T&O BO 1/0`,
`TC Tight Setup (any) 1/0`, `TC Tight Setup count` (how many ticked setups are present, 0–5; sort descending = tightest first),
`TC Old base 1/0`, `TC New base 1/0`, `TC T&O state 1/0`, `TC GLP 1/0`,
`TC New base length`, `TC To pivot %`, `TC Last 2 closes (unit)`, `TC 4/9/21 spread (unit)`,
`TC 4/9 squeeze bars`, `TC 4/9 gap (unit)`, `TC ATR now / base start`, `TC Base close span (ATR)`, `TC Base vol / avg`, `TC Leg before base %`,
`TC RTI`, `TC RTI zone`, `TC GLP z-spread`, `TC GLP score`, `TC Ext 21 EMA (ATR)`,
`TC Ext 50 SMA (ATR)`, `TC Day range exp %`, `TC Body range exp %`, `TC Vol / MA`, `TC Chg 1D %`,
`TC LoD Dist %` (`(close − low) / close × 100`, same as the s-VTG ATR LoD dist row),
`TC Low (ATR)` (`(close − low) / atr`, same as s-VTG Combo `Low (ATR)`), `TC $ Vol (M)`

**1:1 check against Python.** Run the Pine Screener with `TC T&O State Qualified` = True and
`Include upstream stages` on. Then compare the list with the dashboard's "Tight & orderly"
stage output for the same date (`results/<date>/workflows/Trading Voyage _Ollie__Tight _ orderly_<date>.txt`).
After that, compare against `TC New Base Qualified` to see how the book-based definition differs.

---

## 2. `tcCoilBreakout.pine` — s-TC Coil Breakout

### Range (the "daily range")

For a coil occupying bars `0 … n−1`, the range is measured on the `resLen` bars
**before** it — the window ending at bar `n`:

```
res(n) = highest(high, 60)[n]          // resistance
sup(n) = lowest(low,  60)[n]           // support
age(n) = −highestbars(high, 60)[n] + 1 // bars from the resistance high to the first coil bar
```

`age ≥ resMinAge` (default 5, 0 = off) keeps the level a real prior ceiling, not
just the last bar of a run-up.

> **Assumption, not from the card.** The card defines no lookback; it only
> shows a range drawn by eye (≈ 25–30 daily candles in its right panel). `60`
> is our own pick. It matches s-VTG Combo's `N-day: price lookback` default
> (≈ one quarter of daily bars). `resMinAge = 5` is also ours. Both are inputs.

### Coil — 3–5 day tight coil just under resistance

For each `n` in `[3 … 5]` ending on this bar (`avgR = mean(rng[0..n−1])`):

| Card idea | Condition | Default |
|---|---|---|
| 3–5 day coil | `3 ≤ n ≤ 5` | — |
| Tight coil | `hiH − loL ≤ coilRangeK × atr` | 1.5 ATR |
| Controlled closes | `hiC − loC ≤ coilSpanK × atr` | 1.0 ATR |
| Small candles | `avgR ≤ coilBarK × atr` | 0.9 ATR (0 = off) |
| Just under resistance | `hiH ≥ res − nearK × atr` | within 0.5 ATR |
| Wicks may poke a little | `hiH ≤ res + pokeK × atr` | 0.25 ATR |
| Not broken out yet | `hiC ≤ res` | — |
| Resistance is old enough | `age ≥ resMinAge` | 5 bars |
| (optional trend) | `close > SMA(close, 50)` | off |

```
coil     = longest n passing all rows
coilHi / coilLo / coilRes / coilSup = values for that n
coilRng  = (hiH − loL) / atr
```

### Breakout / Failed poke

```
level    = clearCoil ? max(coilRes[1], coilHi[1]) : coilRes[1]     // clearCoil = on

COIL BO  = coil[1]
       and close > level                              // close above resistance (and the coil high)
       and (close − low) / rng ≥ 1 − 50%              // close in the top half of the bar
       and volume ≥ 1.0 × SMA(volume, 50)             // 0 = off

FAILED POKE = coil[1] and high > coilRes[1] and close ≤ coilRes[1]
              // traded above resistance intraday, closed back inside the range
```

The failed poke is the **daily-bar version** of the card's left side ("big 5-min
breakout bar, still inside the daily range"). A true intraday version needs
`request.security` for daily levels and is **not** implemented (would break the
screener-safe design).

### Current levels shown

```
resNow = coil ? coilRes : highest(high, 60)[1]     // prior 60 bars, excluding today
supNow = coil ? coilSup : lowest(low,  60)[1]

To resistance (ATR) = (resNow − close) / atr        // negative = above resistance
To resistance %     = (resNow − close) / close × 100
Range position %    = (close − supNow) / (resNow − supNow) × 100
```

### On screen

| Element | What it shows |
|---|---|
| Red line | resistance `resNow`, drawn over the last 60 bars, extended 5 bars right |
| Blue line | support `supNow` |
| Dashed orange box | the coil forming now (last bar only) |
| Dashed orange box (filled) | the coil that produced each breakout |
| Label `TC Coil BO` + green bar | coil breakout |
| Label `TC Failed Poke` + red bar | poked above resistance, closed back inside |

**Table (bottom-right)**

| Row | Value | Colour |
|---|---|---|
| State | BREAKOUT / Failed poke / Coiling under resistance / Inside range / Above range / Below range | green / red / yellow / grey |
| Resistance | price `(x ATR / y %)` away | green when above it, yellow when within 0.5 ATR below |
| Support | price | — |
| Range position | `0%` = at support, `100%` = at resistance | — |
| Coil | `YES  n bars` / `—` | green when coiling |
| Coil range | `(hiH − loL) / atr` | green when coiling |
| Last signal | Coil BO / Failed poke `(k b ago)` | — |

### Screener columns

Filters: `TC Coil Breakout`, `TC Failed Poke`, `TC Coil (armed)`

Numeric: `TC Coil Signal (any) 1/0`, `TC Coil BO 1/0`, `TC Failed Poke 1/0`,
`TC Coil length (bars)`, `TC Coil range (ATR)`, `TC To resistance (ATR)`,
`TC To resistance %`, `TC Range position %`, `TC Vol / MA`, `TC Chg 1D %`, `TC $ Vol (M)`

Watchlist idea: filter `TC Coil (armed)` = true, sort `TC Coil range (ATR)` ascending.

---

## Open questions / TODO

**OLD method: decisions settled on 2026-09-28.** The squeeze needs ≥ 1 bar (input `oMinSq`). The gap is ≤ 1%, the tight candle is ≤ 0.8 ATR, and the trigger comes on the bar right after the base. Day and Body Range Expansion are ≥ 0%, and the VTG ATR green zone applies to OLD only. It's still not compiled or checked on charts.

1. **Not compiled yet.** Paste into TradingView and fix any syntax errors.
2. **Intraday "still inside the daily range" helper.** It would need `request.security`, so it would be a separate chart-only script if we want it.
3. **Thresholds are guesses.** Calibrate them on real charts or against Voyage notes.
4. **NEW defaults are card-only.** The older-book extras (2 closes within 1%, 4/9/21 within 1%, volume contraction, 20% leg) are off. Turn them on one at a time to see what each one removes.
5. **OLD / NEW overlap s-VTG Combo's `VTG BO Old / New`** but are now recalibrated to the book (%-based, volume, leg, not-extended). The Combo versions are unchanged.
6. **Resistance is a plain highest-high over an assumed 60-bar lookback.** Neither the
   definition nor the length comes from the card. Alternatives:
   - a shorter default (≈ 20–30, closer to what the card draws);
   - a minimum-touches rule (≥ 2 highs within x ATR of the level);
   - resistance = the most recent confirmed pivot high (`ta.pivothigh`), with no fixed window.
7. **T&O 1:1 check** against the Python "Tight & orderly" output has not been done yet.
