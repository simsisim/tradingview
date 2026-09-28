# Oliver Kell — Cycle of Price Action tools

Pine v6 indicators for Oliver Kell's *Cycle of Price Action*:

> **reversal → wedge pop → EMA crossback → base-n-break → exhaustion → wedge drop**

Built on the ATR-extension engine from `../IO_vtg/` (`visual_vtgAtr.pine`):
extension from every MA is measured in **ATR units** — `(close − MA) / ATR` — and
each setup is a threshold on that plus a price-structure trigger.

All setups are **daily** — run them on a Daily chart. No `request.*`, so they
drop straight into the Pine Screener.

### `okCycle.pine` — `s-OK Cycle` ← use this one

**All three long setups in one indicator** (Reversal Extension + Wedge Pop +
EMA Crossback), modelled on `../IO_vtg/visual_vtgCombo.pine`:

- one `Show *` switch per setup
- per-setup colour, used for **both** the painted bar and the label background
- `Show trigger labels` + `Labels only on current bar` + `Paint the trigger bar`
- stacked labels (one tag per firing setup, auto black/white text)
- background tinted by the active *state* (red extended-down · yellow wedging · blue uptrend-dip)
- extension table with a `State` and `Last signal` row
- every trigger → `alertcondition` Screener column; metrics → `plot(display.none)` columns

The single-setup files below are the same logic broken out — reference / simpler
tuning. Delete them if you only want the combo.

| File | Setup | Direction | Status |
|---|---|---|---|
| `okCycle.pine` | **all 3 long setups combined** | long | built |
| `reversalExtension.pine` | Reversal Extension | long (bottom) | built (standalone) |
| `wedgePop.pine` | Wedge Pop | long (continuation) | built (standalone) |
| _exhaustionExtension.pine_ | Exhaustion Extension | short / take-profit (top) | todo |
| _wedgeDrop.pine_ | Wedge Drop | short (breakdown) | todo |

### EMA Crossback (in `okCycle.pine`)

Secondary continuation entry — **not** a bottom. Uptrend already confirmed, price
dips shallowly to the 10 EMA, then reclaims it.

```
trendUp    = ma10 > ma21 and ma21 > ma50 and ma21 rising over cbTrendLook bars
dipTagged  = low reached the 10 MA within cbPbBars                       // low - ma10 <= 0
heldAbove  = no close more than cbShallowK×ATR below the 21 MA in that window
dipShallow = the dip low is at most cbMaxFlushAtr×ATR below the 10 MA    // it's a dip, not a flush
cross      = close reclaims the 10 MA (prior close was below)
emaCrossback = trendUp and dipTagged and heldAbove and dipShallow and not extendedDown and cross
```

Reversal Extension and Wedge Pop want the MA stack broken / price stretched below;
Crossback wants the stack **intact**. `not extendedDown` keeps them from overlapping.

---

## `reversalExtension.pine` — `s-OK Reversal Extension`

**Concept.** A stock has sold off in fear and is stretched far *below* its
10 / 21 EMA (sometimes the 50). Then a reversal bar prints — strong green close,
often an undercut-and-rally on heavy volume. Flags a potential bottom.

### Logic

```
ma10/ma21/ma50 = EMA/EMA/SMA(close, 10/21/50)      // types & lengths configurable
atr            = ta.atr(14)

// distance below the 10 MA, in ATR (measure from close, or the bar high)
below10        = (ma10 − (extUseHigh ? high : close)) / atr

extendedDown   = below10 >= extAtr                 // default extAtr = 1.0
                 and (not reqBelow21 or close < ma21)   // default on
                 and (not reqBelow50 or close < ma50)   // default off

wasExtended    = ta.barssince(extendedDown) <= lookback   // default lookback = 5

revBar         = (close > open)                    // green            (revNeedGreen)
                 and (close > close[1])            // up day           (revNeedUpDay)
                 and (close−low)/(high−low) >= 0.5 // closes strong    (revClosePos)
                 and volume > sma(volume,20)       // heavy volume     (revNeedVol)
                 and low <= lowest(low,lookback)[1]// undercut the low (revUndercut)
                 and close < ma10                  // still below 10   (revStillBelow)

reversalExt    = wasExtended and revBar            // + `cooldown` bars quiet after a hit
```

The key fix vs. the naive scanner: `extendedDown` and `revBar` do **not** have to
be true on the same bar — the flush only has to have happened within `lookback`
bars. A real reversal bar rallies back toward the MA and is no longer "extended"
by its close, which is why the one-bar AND version fires almost never.

### If you still see nothing (e.g. on SNDK)

Loosen, roughly in this order:

1. `Require undercut of the recent low` → **off**
2. `Require volume > volume MA` → **off**
3. `Min distance below the 10 MA (× ATR)` → **0.5**
4. `Extension lookback (bars)` → **8–10**
5. `Also require price below the 21 MA` → **off**

The table (bottom-left) always shows the live extension from the 10 / 21 / 50 in
ATR and the current `Flush depth` — use it to see how close the name is even when
nothing has triggered. `Reversal Ext` row: `no` → `watching` (was extended, waiting
for the bar) → `TRIGGERED`.

### Screener

- **Filter columns** (`alertcondition`): `Reversal Extension`, `Downside Extended`
- **Sortable columns** (`plot … display.none`): `Ext 10/21/50 (ATR)`,
  `Flush depth (ATR)`, `Move / ATR`, `Chg 1D %`, `$ Vol (M)`, `Screener Trigger` (1/0)

Both `alertcondition`s also work as ordinary chart alerts.

### Style tab

Black text on a green table (matches the Kell/VTG panel). Row background is tinted
by extension tier — green `< 1 ATR`, yellow `< 2 ATR`, red beyond. Background of the
chart is tinted light-red while `extendedDown` is active.

---

## `wedgePop.pine` — `s-OK Wedge Pop`

**Concept.** After the Reversal Extension the stock coils *beneath* its 10 (& 21)
EMA — range tightening, every close under the fast EMA — then a strong bar **pops**
back above both EMAs on expanding volume. The first continuation entry off the low.

### Logic

```
// wedge: every one of the last N closes below the 10 MA  (highest(close−ma10,N)[1] < 0)
pulledUnder = ta.highest(close − ma10, wedgeBars)[1] < 0          // wedgeBars = 5

winRange    = highest(high,N) − lowest(low,N)
contracted  = winRange <= winRange[N] * 0.85                      // range tighter than the prior window (reqContract)
tightAbs    = winRange / atr <= wedgeMaxAtr                       // optional absolute cap (reqTightAbs, off)
wedging     = pulledUnder and contracted [and tightAbs]

// pop: reclaim the 10 MA (and 21), strong green close, volume expansion, actual cross
popBar      = close > ma10
              and close > ma21                                   // reqReclaim21
              and close > open                                   // popNeedGreen
              and (close−low)/(high−low) >= 0.5                   // popClosePos
              and volume > sma(volume,20) * volMult              // popNeedVol, volMult = 1.0
              and close[1] <= ma10[1]                             // reqCross

wedgePop    = (ta.barssince(wedging) <= popLookback) and popBar   // popLookback = 2, + cooldown
```

Optional **prior-flush** gate (`reqPriorFlush`, default off) links it to the
reversal low: requires price to have been `≥ flushAtr` ATR below the 10 MA within
`flushWindow` bars — turn it on to only take wedge pops that follow a real flush.

### If you see nothing

1. `Require range contraction` → **off** (or ratio → `0.95`)
2. `Require the actual cross` → **off**
3. `Require volume expansion` → **off**
4. `Require close back above the 21 MA too` → **off**
5. `Wedge length` → **3–4**, `Pop within N bars` → **3**

Table `Wedge Pop` row: `no` → `armed` (wedge seen, waiting for the pop) → `TRIGGERED`.

### Screener

- **Filter columns**: `Wedge Pop`, `Wedging`
- **Sortable columns**: `Ext 10/21/50 (ATR)`, `Wedge range (ATR)` (lower = tighter),
  `Vol / MA`, `Chg 1D %`, `$ Vol (M)`, `Screener Trigger` (1/0)
