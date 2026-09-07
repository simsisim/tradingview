# VTG Combo — signal spec

Based on `gd_systems/tradying_voyage/vtg-combo-setups.md` (user's summary of the
VTG Combo Scanner walkthrough) + screenshots in `VGT-tools/`.

Notation: `H1 = high[1]`, `L1 = low[1]`, `C1 = close[1]`, `O1 = open[1]`.
Timeframe: native chart TF — use a **Daily** chart (all setups are daily).
`atr = ta.atr(atrLen)` (atrLen default 14).

## Confirmation policy (global — applies to every level-break signal)

A signal that depends on price clearing a level (Slingshot, Inside Day Breakout,
Oops, Super Oops, 3-Bar, N-day) resolves through one shared rule:

```
f_confUp(lvl):  closed bar → (confirmBody ? min(open,close) : close) > lvl
                forming bar & livePreview → high > lvl   (tentative, repaints this bar only)
f_confDn(lvl):  mirror with low / max(open,close)
```

- `confirmBody` (default off): close beyond the level is enough; on = whole body.
- `livePreview` — **only affects the currently-forming bar; history is identical
  either way** (closed bars are always close-confirmed).
  - **off (default = TAPLOT):** the forming bar uses `close` = *current price*,
    re-evaluated every tick. The signal appears while price is beyond the level
    and disappears if it crosses back — a live process all day, frozen at the close.
  - **on:** the forming bar uses the *wick* (`high`/`low`). Once price tags the
    level intrabar the signal shows and **stays** for the rest of the session
    (the wick can't un-extend), then is reconciled against the close at the end
    of the day — removed if it didn't hold.
  - For live watching: **on** gives the earliest, stickiest heads-up (matches
    "trigger when price reaches the 4-EMA, don't wait for the close"); **off**
    tracks the true current state and never shows anything the last price doesn't
    support. Neither changes the historical/screener record.
- Signals that are completed-bar properties (Inside Day, OEL/OEH, Engulf, Kicker,
  4% Breakout, ATR filters) don't use this — they're already close/structure based.

Status: **CORE** = from the walkthrough · **PROVISIONAL** = reasonable
reconstruction, tune later · **EXTRA** = our addition, off by default.

---

## Trigger groups (matches how he uses the tool)

| Group | Triggers | Use |
|---|---|---|
| **Breakout edges** | Slingshot · 4% Breakout · Inside Day Breakout · OEL | live trading — "what's breaking today" |
| **Watchlist edges** | Pre-Slingshot · Inside Day · Oops Reversal | night routine — build tomorrow's list |
| **Context filters** | ATR 100%+ · ATR < 100% | gate entries (avoid stretched moves) |
| **Composite** | Breakout Triggered = OR(breakout edges) | the master live-trading filter |
| **Extras** | Super Oops · OEH · Kicker · 3-Bar Break · Engulf · N-day High Breakout | optional |

---

## CORE triggers

### Slingshot  — CORE
Momentum continuation: strong stock pulls back below a fast EMA for a few bars,
then snaps back through it.
**Default config reproduces the TAPLOT "Sling Shot" script (© TaPlot, MPL-2.0)
byte-for-byte on historical bars:**
```
// TAPLOT:
EMALine   = ta.ema(high, 4)
slingshot = close > EMALine and close[1]<EMALine[1] and close[2]<EMALine[2] and close[3]<EMALine[3]
```
```
// Ours (slingEmaSrc=High, slingBars=3, slingPbSrc=Close, confirmBody/livePreview off):
slingEma   = ta.ema(high, slingEmaLen)                                   // = ta.ema(high, 4)
slingPbVal = slingPbSrc == 'High' ? high : close                        // = close
pulledBack = ta.highest(slingPbVal - slingEma, slingBars)[1] < 0        // = close[1..3] < slingEma[1..3]
slingshot  = pulledBack and f_confUp(slingEma)                          // f_confUp -> close > slingEma
```
Verified algebraically: `ta.highest(close - slingEma, 3)[1] < 0`
⇔ `close[1]<slingEma[1] and close[2]<slingEma[2] and close[3]<slingEma[3]`.

Deviations from TAPLOT are all opt-in, default off:
- `slingPbSrc = High` — pullback needs the whole bar (its high) below the EMA.
- `slingEmaSrc = Close` — EMA of closes instead of highs.
- `slingBars ≠ 3` — different pullback length.
- `livePreview = on` — Oliver-style intrabar preview on the forming bar.
- `confirmBody = on` — whole body above the EMA, not just the close.

### Pre-Slingshot  — PROVISIONAL
Setup phase before a slingshot. Price still below `slingEma` but trend/structure
favourable. Painted **yellow bars**.
```
preSling = close < slingEma
        and slingEma > slingEma[trendLook]   // EMA rising (default trendLook 5)
        and (slingEma - close) <= nearK * atr // near the trigger, nearK default 0.75
        and not slingshot
```
Params: `trendLook` = 5, `nearK` = 0.75. Tune against his charts.

### 4% Breakout  — PROVISIONAL
Range-expansion breakout with an ATR **ceiling** filter (so it doesn't fire
every day on high-ATR names).
```
dayMovePct  = (close - C1) / C1 * 100
fourPctBO   = dayMovePct >= pctThresh and atr < atrMax
```
Params: `pctThresh` = 4.0, `atrMax` = 4.0 (ATR in price units).
Open: is the move measured `close-vs-C1` or `close-vs-open`? Assuming `close-vs-C1`.

### Inside Day  — CORE
```
insideDay = high < H1 and low > L1        // strictly inside
```

### Inside Day Breakout  — CORE
Confirmed break of the compressed inside-day range, **within `idBoWindow` bars**
of the inside day (default 3; 1 = only the immediately following bar).
```
// track the most recent inside day
if insideDay: idHi := high; idLo := low; idBar := bar_index; idOpen := true
idInWindow  = idOpen and 1 <= (bar_index - idBar) <= idBoWindow
idBreakUp   = idInWindow and f_confUp(idHi)
idBreakDn   = idInWindow and f_confDn(idLo)
// coil closes once it breaks or the window expires
if idBreakUp or idBreakDn or (bar_index - idBar) > idBoWindow: idOpen := false
```
- Level = the inside day's own high / low (not the mother bar).
- A new inside day inside the window replaces the tracked one.
- On a trigger, a **black horizontal line** is drawn at the broken level, from
  the inside day to one bar past the breakout, capped at `idLineLen` bars
  (default 5). Never extended right. Drawn on **every** breakout including
  historical (needs `Show Inside Day Breakout` + `idLineShow`); *labels only on
  current bar* governs only the text labels, not these lines.

### Oops Reversal  — CORE  (bullish primary)
Larry Williams gap reversal. Opens below prior low, reverses back up through it.
```
oopsUp = open < L1 and f_confUp(L1)
oopsDn = open > H1 and f_confDn(H1)       // bearish analog (extra)
```
Used as a strength / watchlist gauge, not a primary buy.

### OEL / OAL (Open = Low)  — CORE
Opening print ≈ the day's low (little/no lower wick), price trades up from open.
```
tol = oelTicks * syminfo.mintick          // oelTicks default 0
oel = open <= low + tol
```
"Favourite case" flag (optional filter `oelGapOnly`): gap up **and** open sits
inside the prior day's upper wick:
```
oelStrong = oel and open > C1 and open > math.max(O1, C1) and open < H1
```

### ATR 100%+  /  ATR < 100%  — PROVISIONAL (context filters)
Day's move relative to ATR. Used to keep entries "under 1 ATR".
```
atrMove    = math.abs(close - C1) / atr
atrOver100 = atrMove >= 1.0
atrUnder100= atrMove <  1.0
```
Open: move vs range (`high-low`)? Assuming close-to-close move.

### Breakout Triggered (composite)  — CORE
```
breakoutTrig = slingshot or fourPctBO or idBreakUp or oel
// live-trading option: AND atrUnder100  (toggle: "restrict to < 1 ATR")
```

---

## EXTRA triggers (kept, default OFF)

| Trigger | Logic |
|---|---|
| **Super Oops** | not a real Oliver term; our def: `open < L1 and f_confUp(H1)` (reclaims entire prior range) |
| **OEH** | `open >= high - tol` |
| **Kicker** (bull) | `C1 < O1 and open > O1` — exact `dashboard.pine` |
| **3-Bar Break** | up `high[1] < high[3] and f_confUp(ta.highest(high[1],3))` · down `low[1] > low[3] and f_confDn(ta.lowest(low[1],3))` — exact `dashboard.pine` (lower-high / higher-low precondition + close clears the last 3 bars) |
| **Engulf / outside bar** | `high > H1 and low < L1` |
| **N-day High Breakout** | `close > ta.highest(high, P)[1]` + optional volume/trend filter (was in `dashboard.pine`) |

---

## Screener column mechanics

- **Boolean triggers → `alertcondition(bool, 'Name', …)`**. In the Pine Screener
  each `alertcondition` title becomes a **True/False** filter column (select True
  → only firing tickers listed) — this is the mechanism Oliver's screener uses.
  `plot`/`plotshape` give a numeric "choose a value" filter instead, so they are
  **not** used for the triggers. Each alertcondition also works as a chart alert.
- **Numeric metrics → `plot(float, …, display=display.none, editable=false)`**
  for range/sort (`Ext EMA (ATR)`, `Ext SMA (ATR)`, `Move / ATR`, `Chg 1D %`,
  `$ Vol (M)`).
- None are gated by the `Show *` chart switches.
- Column names: `Slingshot Triggered`, `Breakout Triggered`,
  `4% Breakout Triggered`, `Pre-Slingshot Triggered`, `Inside Day Triggered`,
  `Inside Day Breakout Triggered`, `Inside Day Breakdown Triggered`,
  `Oops Reversal`, `Oops Reversal (bear)`, `Super Oops`, `OEL Triggered`,
  `OEH Triggered`, `ATR 100%+`, `ATR < 100%`, `Kicker`, `3-Bar Break Up`,
  `3-Bar Break Down`, `Engulf`, `N-day High Breakout`.

## Numeric columns (always emitted, screener-only)
- `Ext 21EMA (ATR)` = `(close - ema(close,21)) / atr`
- `Ext 50SMA (ATR)` = `(close - sma(close,50)) / atr`
- `Move / ATR` = `atrMove` (above)
- `Chg 1D %` = `dayMovePct`
- `$ Vol (M)` = `close * volume / 1e6`

---

## Default `Show *` states — copied from `VGT-tools/usage_4.png`

| Toggle | Default |
|---|---|
| Show Labels Only on Current Bar | **ON** |
| Show Breakout | off |
| Show Pre-Slingshot (yellow bars) | off |
| Show Slingshot | **ON** |
| Show 4% Breakout | **ON** |
| Show Inside Day | off |
| Show Inside Day Breakout | **ON** |
| Show Oops Reversal | off |
| Show Super Oops | off |
| Show OEL | **ON** |
| Show 100%+ ATR | off |
| Show < 100% ATR | off |
| Inputs in status line | **ON** |

---

## Open questions (non-blocking — assumptions noted above)
1. 4% Breakout: move measured close-vs-prior-close or close-vs-open?
2. ATR filter: move (close-to-close) or range (high-low)?
3. Pre-Slingshot: exact "structure looks suitable" rule — needs eyeballing vs his charts.
4. Slingshot: any minimum pullback depth / bars-below requirement?
