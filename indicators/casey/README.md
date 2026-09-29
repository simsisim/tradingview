# caseyModule

Intraday overlay (Pine v6), `caseyModule.pine` (indicator title `caseyModule`). Inspired by `../prev_day_hl/prev_day_hl.pine` and `../vwap_ema_signals/vwap_ema_signals.pine`.

## What it draws

| Element | Details |
|---|---|
| Day separator | Vertical line on the first bar of each calendar day (session timezone). Intraday only. Default black, dotted, width 4. |
| Week separator | Replaces the day line on the first bar of a new week. Intraday + daily. Default blue, solid, width 4. |
| PD-H / PD-L | Previous day's high/low. `PD H/L Range`: *Regular only* (09:30–16:00, default) or *Regular + Extended*. |
| PW-H / PW-L | Previous week's high/low, from the same bars as PD (per `PD H/L Range`). Intraday only. |
| Pre-H / Pre-L | Today's premarket high/low: bars before the regular open. Needs extended hours on the chart. |
| EMA 1/2/3 | Default 13 / 48 / 200 on close, blue / green / orange, solid, width 4. Each has show, length, color, width. |
| VWAP | Magenta, solid, width 2. hlc3, anchored at the *start of the day* (resets on the first bar of the calendar day, which includes premarket) or at the *regular open* (hidden outside RTH). |

Each of the 6 levels has its own **show · color · width · style**. Highs default to green (#4CAF50) and lows to red (#F23645). The line style tells them apart: PD is solid width 1, premarket is dashed width 1, and PW-H/PW-L (previous week high/low) are solid width 2. The week range uses the same bars as PD (**PD H/L Range**: regular only, or regular + extended), rolls on the week separator, and skips empty weeks.

## Level look (group "Key Levels — Look")

- **Line starts at**: the bar that set the level, or the start of today.
- **Extend right**.
- **Zone** (on by default): a thin translucent band that hugs each level. It sits below a high (PD-H, Pre-H) and above a low (PD-L, Pre-L). Thickness is the previous day's daily ATR(14) × 0.03, or a price tier (0.10 / 0.25 / 0.50). Default transparency is 80. The look is borrowed from "Key Levels + Zones" by oXXo1.
- **Glow** (off by default): a wider, mostly transparent solid line under the main line (a soft halo). You can set its transparency and extra width.
- **Labels**: `PD-H 123.45` to the right of the last bar. The price is optional (**Show price**, off by default). The size can be small, normal, large (the default) or huge. The offset is set in bars.
  - *Filled tag* (default): a solid tag in the level color that sits on the line. The text is black by default (**Tag text color**: Black / White / Auto, where Auto picks by the tag's brightness). PD tags are pushed a further 5 bars right (**PD labels extra offset**) so they don't cover the Pre tags. PW tags are pushed twice that far.
  - *Text only*: colored text only. Labels for highs sit above the line and labels for lows sit below it.
- **Show levels on previous days**: thin segments that span each past day, each with a fainter zone. The lines use the 500-line budget that the separators also use. The zones use a separate 500-box budget.

## Bias table and background (group "Bias Table & Background")

| Row | States |
|---|---|
| Prev day | Above PD-H / Below PD-L / Inside PD range |
| Premarket | Above Pre-H / Below Pre-L / Inside Pre range. Shows "Premarket forming" before the open and "n/a" without premarket data. |
| EMA stack | P > 13 > 48 > 200 / P < 13 < 48 < 200 / Mixed (uses the EMA input lengths) |
| Setup | FULL BULL: wait for 13/48 test → BULL: testing 13–48 (entry zone). The bear side mirrors it. |

- **Full bull** means the close is above PD-H and above Pre-H, and close > EMA 1 > EMA 2 > EMA 3. Pre-H is skipped while premarket is forming or when the chart has no premarket data. **Full bear** is the mirror.
- **Armed**: after a full bull on the same day, the setup stays armed while the EMA stack holds and the close stays at or above EMA 2. It resets each new day.
- **EMA test (the entry bar)**: while armed, the bar's low reaches EMA 1 and the close holds at or above EMA 2.
- **Background** (off by default): full bull/bear bars get a light green/red tint (transparency 88). Test bars get a stronger tint (transparency 65), so the entry bars stand out.

## Notes

- The current-day level lines are deleted and redrawn on the last bar only, so they cost little to run.
- A day with no qualifying bars (such as a holiday) does not overwrite PD-H/PD-L.
- Day separators, the key levels and VWAP only show on intraday timeframes. On daily and higher you see only the EMAs and the week separators.
