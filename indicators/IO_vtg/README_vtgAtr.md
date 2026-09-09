# s-VTG ATR

Extension / risk-before-entry table. Companion to **s-VTG Combo** — you scan with
s-VTG Combo, then check on the chart with s-VTG ATR whether the name is already
stretched.

Re-implementation of the invite-only **VTG ATR** (Ollie_AllCaps) built on the open
**ALEX – ATR Extensions + ADR + Table** feature set (Alex_PrimeTrading).

`indicator('s-VTG ATR', 'VTG ATR', overlay = true)` — **chart only**. The same
metrics are also emitted as hidden columns by **s-VTG Combo**, so a whole
watchlist can be screened on them (values + range filters, no colour); this
script is the coloured, single-chart read.

The extension / range-expansion formulas are **duplicated inline** in both this
file and `visual_vtgCombo.pine` (no shared library — kept simple on purpose).
Both files carry a `KEEP IN SYNC` comment on that block; change one, change the
other. `useDaily` / `request.security` live here only.

## Table rows

| Row | Meaning |
|---|---|
| **ATR %** | daily ATR ÷ price × 100 |
| **ADR %** | 20-day average `High−Low` ÷ price × 100 |
| **ATR from Low** | ATRs between price and today's **low** — pullback / stop gauge |
| **ATR from Open** | ATRs between price and today's **open** |
| **LoD dist / price** | distance to today's low, in % / absolute |
| **ATR dist 21 / 50** | ATRs between price and the 21 EMA / 50 SMA |
| **21 / 50 price** | the MA values |
| **Day range exp** | today's `High−Low` ÷ **yesterday's** — `>1` = expansion |
| **Body range exp** | today's `|Open−Close|` ÷ **yesterday's** body |
| **ATR extension targets** | `MA + ATR × multiplier` price levels |

The **ATR from Low / Open**, **Day/Body range expansion**, and the green/red row
colouring are the parts VTG ATR adds over the ALEX script; the rest is the ALEX
feature set.

## Colouring

**Text is always black.** Each classified row is green (OK) or red (caution);
`ATR %`, `ADR %`, `LoD`, MA-price and target rows stay the neutral table colour.

| Row | Green | Red |
|---|---|---|
| **Low**, **Open** | value ≥ 0 | value < 0 (close below the day's low / open) |
| **Day / Body Range Expansion** | value ≥ 0 (expanding vs yesterday) | value < 0 (contracting) |
| **21 EMA distance** | between 0 and `odT21` ATR above the MA | below the MA, **or** more than `odT21` (3) ATR above it — overextended, too late to initiate |
| **50 SMA distance** | between 0 and `odT50` ATR above the MA | below the MA, **or** more than `odT50` (5) ATR above it |

Colours and the two thresholds (`odT21`, `odT50`) are in the inputs — *Row colour*
and *Table style* groups.

## Chart extras

- **ATR extension target lines** — `showLine21 / showLine50`, at
  `MA + ATR × mult`.
- **Bar markers** — a char above the bar when price is `≥ threshold` ATRs from the
  21 MA (`●`) or 50 MA (`—`), ALEX-style.

## Notes

- Values are pulled from the **1D** timeframe (`useDaily`, on by default) so they
  stay correct on intraday charts. Turn off to use the chart timeframe.
- Blank on Monthly charts (guarded).
- On the live daily bar the range/body-expansion ratios grow through the session
  and settle at the close.
