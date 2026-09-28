# s-VTG Combo

A single Pine v6 script that works as **both** an on-chart indicator and a
**TradingView Pine Screener** source. Re-implementation of the Voyage Trading
Group "VTG Combo" momentum toolkit.

Files:
- `visual_vtgCombo.pine` — the script
- `visual_vtgComboTriggers.pine` — alert-only sibling (no plots, no bar colour,
  no screener columns) for sending Discord webhook alerts on a checked subset
  of the 20 triggers — see "Discord alerts" below
- `signal_spec.md` — exact trigger definitions / parameters
- `IMPLEMENTATION_PLAN.md` — full roadmap

## Shared with s-VTG ATR

The Combo screener emits the same extension / range-expansion metrics that the
**s-VTG ATR** on-chart table draws (`21 EMA (ATR)`, `50 SMA (ATR)`, `Low (ATR)`,
`Day Range Exp %`, `Body Range Exp %`). The formulas are **duplicated inline** in
both `visual_vtgCombo.pine` and `visual_vtgAtr.pine` — if you change one, change
the other. Each file has a `KEEP IN SYNC` comment on that block.

## Chart mode

Add to a **Daily** chart. You get:
- 21 EMA cloud (EMA of high / EMA of low) + 50 SMA
- ATR-extension table (price distance from each MA in ATR units)
- Trigger labels — toggle each in *Triggers to label on chart*
- `Show triggers on: All bars / Current bar only / Last N bars` to declutter history
  (scopes painted bars, labels, ID breakout line and VTG New base box together)

## Screener mode

1. In the Pine editor, paste the current `visual_vtgCombo.pine`, **Save**, then
   **Add to favorites** (star icon).
2. Open **Pine Screener** (tradingview.com/pine-screener).
3. Pick a watchlist. Set *Indicator* to **s-VTG Combo** (the `s-` prefix makes it
   quick to find). **If it was already loaded from an earlier version, remove it
   and add it again** — the screener caches the old column list.
4. Set the timeframe to **1D** and press **Scan**. Every column shows `—` until
   you press Scan.
5. **Triggers are filters, not columns** — add a filter chip from the
   `alertcondition()` names: `Slingshot Triggered`, `Breakout Triggered`,
   `4% Breakout Triggered`, `Inside Day Breakout Triggered`, `OEL Triggered`, …
   It keeps only the tickers where that trigger fired on the last bar
   (Oliver's `Breakout Triggered = True`).
   Click the **column manager** (the icon top-right of the table) and tick the
   columns you want:
   - **Metric columns** — mirror the s-VTG ATR table so you screen extension in
     the same pass: `21 EMA (ATR)`, `50 SMA (ATR)`, `Low (ATR)`,
     `Day Range Exp %`, `Body Range Exp %`, `Move / ATR`, `Chg 1D %`, `$ Vol (M)`.
6. Combine e.g. `Slingshot Triggered` **and** `21 EMA (ATR) < 3` **and**
   `Day Range Exp % > 0` **and** `$ Vol (M) ≥ 20` — trigger fired, not yet
   overextended, range expanding, liquid.

Why no 1/0 trigger columns: `alertcondition()` counts toward Pine's 64-plot
limit, and chips + 1/0 columns for every trigger went over it (73). The chips
filter identically, so the columns were dropped (2026-09-28). The pre-change
version with trigger columns is kept as `ORIG_visual_vtgCombo.pine`.

Screener notes / limits:
- Screener evaluates the **last bar only** — no historical scanning.
- Cells show values only — **no cell colouring**, no ✓/✗ glyphs (that lives on
  the s-VTG ATR on-chart table).
- Every column is always available (the chart `Show *` toggles do **not** affect
  the screener).
- Set the Pine Screener timeframe to **1D** to match the intended setups.
- No `request.*` is used, so every column works in the screener.
- After **any** edit to the script, remove the indicator from the screener and
  re-add it, then Scan — otherwise you keep seeing the old columns.
- The chart plots (`EMA cloud top/bottom`, `EMA line`, `SMA line`) also appear
  as numeric columns — harmless, just don't tick them.

## Discord alerts

`visual_vtgComboTriggers.pine` is a separate, alert-only companion script —
same trigger math as the "Engine" section above (`KEEP IN SYNC` comments mark
the duplicated blocks), but with every plot/label/bar-colour/screener-column
line stripped out, so it does nothing except fire `alert()`.

- Add it to a **Daily** chart (same native-TF requirement).
- Its **Alerts** input group has one checkbox per trigger (Slingshot and 4 EMA
  Close Cross on by default) — tick whichever subset you actually want pinged.
- Create **one** TradingView alert on it: Condition = "s-VTG Combo Triggers" →
  **"Any alert() function call"**, Frequency = **"Once Per Bar Close"**. That
  single alert fires for every checked trigger — you don't need one alert per
  condition.
- In the alert's **Notifications** tab, tick **Webhook URL** and paste your
  Discord webhook there. The webhook destination can **only** be set in that
  dialog (or as your account's default webhook URL in Notification settings) —
  Pine cannot read or dial a URL from inside the script, so there is no way to
  bake the Discord link into the `.pine` file itself.
- Discord requires the POST body to be JSON. The alert dialog's "Message" box
  is ignored for `alert()` firings — the JSON string is hardcoded per trigger
  in the script (`{"content":"..."}`), which is why messages built with plain
  `alertcondition()` text (not JSON) fail silently against a Discord webhook.
- Want same-day heads-up instead of waiting for the daily bar to close? Switch
  that one alert's Frequency to **"Once Per Bar"** — no script change, it just
  evaluates against the still-forming daily bar (can fire on a move that
  reverses before the real close).
- A true hourly-cadence version (checking the developing daily bar every hour)
  would need `request.security(..., "D", ...)` and its own chart timeframe —
  that's a real rewrite, not a toggle, and would live as yet another separate
  file (not screener-safe, per the `visual_vtgCombo.pine` design).

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
  each in its own method colour. Shown on every bar within the
  `Show triggers on` scope (All bars / Current bar only / Last N bars), which
  also limits the painted bars, ID breakout line and VTG New base box. Live
  caveat: a bar that fired while forming keeps its paint after the window moves
  past it (Pine can't un-paint a closed bar); labels/lines/boxes are deleted. Master switch `Show trigger labels`; text
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

**VTG Breakout Signal — Old vs New** (PROVISIONAL, off by default): two
independent triggers, `Show VTG Breakout (Old)` and `Show VTG Breakout (New)`.
You can turn on both together to compare them on the same chart. Old = 4/9 EMA
compression + tight candle, then expansion. New = a qualified 3+ bar base near a
rising 21 EMA, then a strong-close/volume breakout (the base gets a box around it). Screener filters
`VTG Breakout (Old) Triggered` / `VTG Breakout (New) Triggered` /
`VTG Base (New) Qualified`; Discord checkboxes in
`visual_vtgComboTriggers.pine`. Definitions: `signal_spec.md`.

> Every screener column is a `plot()` with `display = display.none, editable =
> false` (metrics only — triggers are `alertcondition()` filter chips). If a column fails to
> appear, temporarily switch that block to `display = display.all`, and remember
> to remove + re-add the indicator in the screener after every edit.
