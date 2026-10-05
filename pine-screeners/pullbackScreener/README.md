# PB — 21 Structure Pullback  (DRAFT, not yet compiled in TradingView)

`s-PB21Structure.pine` → script **`s-PB 21 Structure Pullback`** (`PB 21`), indicator + Pine Screener.
Everything is prefixed **`PB`** (alert names, screener columns).

Source idea: "ADJUSTABLE MA STRUCTURE" by BalarezoCapital, modified by PrimeTrading
(`gd_systems/primeTrading/21dma-structure TV script_v7.3.txt`). That script only draws
the band and colors bars; the pullback / trigger logic below is ours.

Purpose: **put eyes on the chart.** It flags every pullback into the band in an uptrend,
shallow or deep. Whether to take the trade is the trader's call. Daily chart, no `request.*`.

## Rules

```
top    = MA(high, 21)     middle = MA(close, 21)     bottom = MA(low, 21)     (EMA by default)

Uptrend   = middle > middle[5]                                  (middle line rising over 5 bars)
            and a close > top within the last 10 bars           (pulling back from strength)
Pullback  = Uptrend and low <= top and high >= bottom           (bar reaches into the band, down to its bottom)
Trigger   = after a pullback, within 5 bars:
            close > top and close > high of the last pullback bar (and still Uptrend)
            fires once per pullback
```

No "close must hold the band" rule. A bar whose low goes below the band still counts
if the bar overlaps the band; the **Low zone** and **Close vs band** columns show how deep it went.

**Weekly filter: not implemented.** The original script only switches to a 10 SMA when the
chart itself is weekly. Checking the weekly structure from a daily chart is a possible later add.

## Screener

Filters (True/False chips): `PB In Pullback`, `PB Triggered`, `PB Pullback or Triggered`, `PB Uptrend`.

| Column | Meaning |
|---|---|
| PB State (0/1/2) | 0 none, 1 pullback, 2 trigger |
| PB In pullback 1/0 · Triggered 1/0 · Uptrend 1/0 | as above |
| PB Pullback # | pullback count since the trend (re)started; a whole bar below the band or a non-rising middle line resets it. 1st/2nd are usually the best |
| PB Low zone (1/2/3) | how deep the low went: 1 top half, 2 bottom half, 3 below the band (0 = no touch) |
| PB Close vs band (1/0/-1) | close above / inside / below the band |
| PB Dist mid % · (ATR) | close vs the middle line |
| PB Low to bottom (ATR) | low vs the bottom of the band (negative = pierced it) |
| PB Off high % | low vs the highest high of the last 20 bars |
| PB Vol / avg | volume / 50-bar average (drying up on the pullback < 1) |
| PB Trend age (bars) | bars since a whole bar was below the band |

Price / volume / liquidity filters: use the Screener's own filters.

## Chart

Band (top/bottom gray, cloud, middle gray when all 3 MAs rise, magenta when all 3 fall,
otherwise keeps its last color — same as the original). Orange dot = pullback bar,
green triangle = trigger bar.
