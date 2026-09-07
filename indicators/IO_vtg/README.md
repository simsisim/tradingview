# s-VTG Combo

A single Pine v6 script that works as **both** an on-chart indicator and a
**TradingView Pine Screener** source. Re-implementation of the Voyage Trading
Group "VTG Combo" momentum toolkit.

Files:
- `visual_vtgCombo.pine` — the script
- `signal_spec.md` — exact trigger definitions / parameters
- `IMPLEMENTATION_PLAN.md` — full roadmap

## Chart mode

Add to a **Daily** chart. You get:
- 21 EMA cloud (EMA of high / EMA of low) + 50 SMA
- ATR-extension table (price distance from each MA in ATR units)
- Trigger labels — toggle each in *Triggers to label on chart*
- `Show labels only on current bar` to declutter history

## Screener mode

1. In the Pine editor, **Save** the script, then **Add to favorites** (star icon).
2. Open **Pine Screener** (tradingview.com/pine-screener).
3. Pick a watchlist, set *Indicator* to **s-VTG Combo** (the `s-` prefix makes it
   quick to find in the list), click **Scan**.
4. Add filters:
   - **Trigger columns are True/False** — they come from `alertcondition()`
     (that is the mechanism the Pine Screener turns into a True/False dropdown,
     *not* `plot`/`plotshape`). Pick `Inside Day Triggered`, `Slingshot
     Triggered`, `Breakout Triggered`, … and set it to **True** → the screener
     lists only the tickers where it fired on the last bar. Exactly Oliver's
     `Breakout Triggered = True`.
   - **Numeric columns** (from `plot`) filter by range / sort:
     `Ext EMA (ATR)`, `Ext SMA (ATR)`, `Move / ATR`, `Chg 1D %`, `$ Vol (M)`.
5. Combine e.g. `Inside Day Breakout Triggered = True` **and** `$ Vol (M) ≥ 20`.

Screener notes / limits:
- Screener evaluates the **last bar only** — no historical scanning.
- Every column is always available (the chart `Show *` toggles do **not** affect
  the screener).
- Set the Pine Screener timeframe to **1D** to match the intended setups.
- No `request.*` is used, so every column works in the screener.
- After updating the script, **remove the indicator from the screener and re-add
  it** so it drops any cached columns from an earlier version.
- The 4 chart plots (`EMA cloud top/bottom`, `EMA line`, `SMA line`) also appear
  as numeric columns — harmless, just don't add them.

## Confirmation

Every level-break signal (Slingshot, Inside Day Breakout, Oops, Super Oops,
3-Bar, N-day) is **close-confirmed** — a wick that pierces a level then fades is
never a signal. With defaults, the Slingshot output is identical to the public
TAPLOT "Sling Shot" script on historical bars (see `signal_spec.md`).

*Live intrabar preview* (**off** by default) adds Oliver-style tentative signals
on the still-forming bar, removed on close if unconfirmed. *Confirm on full body*
requires the whole candle body beyond the level. Completed-bar signals (Inside
Day, OEL/OEH, Engulf, Kicker, 4%, ATR filters) are unaffected by either.

## Visual vocabulary

- **Painted bar** — `Paint the trigger bar` (on): the candle is coloured with the
  firing method's colour (single `barcolor`, TAPLOT-style; highest-priority
  method wins if several fire). Only when the method's *Show* switch is on.
- **Per-method colours** live in the **Trigger colours** input group — one colour
  each (Slingshot, Breakout, Pre-Slingshot, 4% Breakout, …). The same colour is
  used for the painted bar **and** the label background. *(Pine can't put
  `barcolor` colours in the Style tab, so they're in Inputs.)*
- **Labels** — one small tag per firing method, **stacked** above the candle,
  each in its own method colour. Shown on **every** bar (history included) unless
  `Show Labels Only on Current Bar`. Master switch `Show trigger labels`; text
  auto black/white for contrast; stack spacing set by `Label stack spacing
  (× ATR)`.
- **Multiple triggers on one bar:** every one gets its own stacked tag; the
  painted candle takes the single highest-priority colour (priority = the
  `Show *` list order, Slingshot first).

**Painted bar and labels are independent** — either, neither, or both:
`Paint the trigger bar` controls the candle colour, `Show trigger labels`
controls the text tags.
- **EMA cloud** (blue EMA-high / EMA-low band) + **green 21 EMA** + **red 50 SMA**.
- **Extension table** (gold, corner): price distance from 21 EMA / 50 SMA in ATR units.

## Status

All triggers implemented in `visual_vtgCombo.pine`. Definitions per
`signal_spec.md` — CORE (from the walkthrough): Slingshot, 4% Breakout, Inside
Day, Inside Day Breakout, Oops Reversal, OEL, Breakout (composite). PROVISIONAL
(tune vs his charts): Pre-Slingshot, ATR 100%+ / < 100%, and the 4% move basis.
EXTRA (off by default): Super Oops, OEH, Kicker, 3-Bar, Engulf, N-day High Breakout.

> Screener plots use `display = display.none, editable = false`. If a column
> fails to appear in Pine Screener, change that block to `display = display.all`.
