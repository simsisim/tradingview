# caseyModule

Intraday overlay (Pine v6), `caseyModule.pine` (indicator title `caseyModule`). Inspired by `../prev_day_hl/prev_day_hl.pine` and `../vwap_ema_signals/vwap_ema_signals.pine`.

## What it draws

| Element | Details |
|---|---|
| Day separator | Vertical line on the first bar of each calendar day (session timezone). Intraday only. Default black, dotted, width 4. |
| Week separator | Replaces the day line on the first bar of a new week. Intraday + daily. Default blue, solid, width 4. |
| PD-H / PD-L | Previous day's high/low. `PD H/L Range`: *Regular only* (09:30–16:00, default) or *Regular + Extended*. |
| Pre-H / Pre-L | Today's premarket high/low: bars before the regular open. Needs extended hours on the chart. |
| EMA 1/2/3 | Default 13 / 48 / 200 on close, blue / green / orange, solid, width 4. Each has show, length, color, width. |
| VWAP | Magenta, solid, width 2. hlc3, anchored at the *start of the day* (resets on the first bar of the calendar day, which includes premarket) or at the *regular open* (hidden outside RTH). |

Each of the 4 levels has its own **show · color · width · style**. PD levels default to solid purple, premarket to dashed cyan.

## Level look (group "Key Levels — Look")

- **Line starts at**: the bar that set the level, or the start of today.
- **Extend right**.
- **Glow**: a wider, mostly transparent solid line under the main line (a soft halo). You can set its transparency and extra width.
- **Labels**: `PD-H 123.45` to the right of the last bar. Labels are always shown. The price is optional (**Show price**, off by default). The size can be small, normal, large (the default) or huge. The offset is set in bars. Labels for highs sit above the line and labels for lows sit below it.
- **Show levels on previous days**: thin segments that span each past day. These use the 500-line budget that the separators also use.

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
- **Background**: full bull/bear bars get a light green/red tint (transparency 88). Test bars get a stronger tint (transparency 65), so the entry bars stand out.

## Notes

- The current-day level lines are deleted and redrawn on the last bar only, so they cost little to run.
- A day with no qualifying bars (such as a holiday) does not overwrite PD-H/PD-L.
- Day separators, the key levels and VWAP only show on intraday timeframes. On daily and higher you see only the EMAs and the week separators.
