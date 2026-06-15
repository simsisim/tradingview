# s-SCTR Screener — Calculation Reference

All formulas as implemented in `s-SCTR.pine`. For the theoretical background and
screening recipes see `SCTR-Screener-Model.md`.

---

## Base: Standard SCTR (Murphy formula)

### PPO components
```
PPO_fast    = EMA(close, 12)
PPO_slow    = EMA(close, 26)
PPO_line    = (PPO_fast - PPO_slow) / PPO_slow × 100
PPO_signal  = EMA(PPO_line, 9)
PPO_hist    = PPO_line - PPO_signal
```
EMA-based to match StockCharts' standard MACD/PPO calculation.
The original TradingCharts reference used SMA — switching to EMA brings v5
closer to the StockCharts value (though absolute score differences remain
due to cross-stock percentile ranking, which Pine cannot replicate).

### Six input variables
| Var | Formula | Horizon |
|-----|---------|---------|
| v1 | `(close − EMA(close,200)) / EMA(close,200) × 100` | Long-term |
| v2 | `ROC(close, 125)` | Long-term |
| v3 | `(close − EMA(close, 50)) / EMA(close, 50) × 100` | Medium-term |
| v4 | `ROC(close, 20)` | Medium-term |
| v5 | `(PPO_hist − PPO_hist[2]) / 3` | Short-term |
| v6 | `RSI(close, 14) − 50` | Short-term |

### Score
```
SCTR_raw = 50 + 2.5 × ( 0.60 × (v1 + v2) / 2
                        + 0.30 × (v3 + v4) / 2
                        + 0.10 × (v5 + v6) / 2 )

SCTR = clamp(SCTR_raw, 0, 99.9)
```

Score of **50** = stock exactly at all moving averages with flat momentum and RSI = 50.
Score approaches **100** on extreme positive readings across all six variables.

---

## Column 0 — Is Daily

```
Is Daily = timeframe.isdaily ? 1 : 0
```

Always filter `Is Daily = 1` first. SCTR parameters (200d EMA, 125d ROC) are only
meaningful on daily charts.

---

## Column 1 — SCTR

The standard Murphy score as defined above. Range 0–99.9.

---

## Columns 2–5 — SCTR Deltas (Approach A)

Change in SCTR score over N bars. Positive = rank improving. Negative = rank weakening.

| Column | Formula | Horizon |
|--------|---------|---------|
| SCTR Δ1D | `SCTR − SCTR[1]` | 1 trading day |
| SCTR Δ5D | `SCTR − SCTR[5]` | 1 calendar week |
| SCTR Δ1M | `SCTR − SCTR[21]` | ~1 trading month |
| SCTR Δ3M | `SCTR − SCTR[63]` | ~1 trading quarter |

---

## Columns 6–8 — Component Sub-scores (Approach B)

Each pair of variables extracted from the SCTR formula and rescaled to 0–100
**without** the 60/30/10 weights, so all three sub-scores are directly comparable
to each other and to the total SCTR.

| Column | Formula | Inputs |
|--------|---------|--------|
| SCTR LT | `clamp(50 + 2.5 × (v1 + v2) / 2, 0, 99.9)` | 200d EMA %, 125d ROC |
| SCTR MT | `clamp(50 + 2.5 × (v3 + v4) / 2, 0, 99.9)` | 50d EMA %, 20d ROC |
| SCTR ST | `clamp(50 + 2.5 × (v5 + v6) / 2, 0, 99.9)` | PPO slope, RSI(14) |

Note: SCTR ≠ 0.6×LT + 0.3×MT + 0.1×ST because the sub-scores here are
unweighted. The weighted reconstruction would be:

```
SCTR ≈ 0.6 × (SCTR_LT − 50)/2.5 × 2.5 + 50   [not how it's exposed]
```

Treat LT/MT/ST as independent lenses, not additive components.

---

## Columns 9–11 — Scaled SCTR Variants (Approach C)

Same structural formula applied with proportionally compressed parameters.
The scaling ratio is `target_horizon / 125` (125d = standard long-term ROC).

| Column | EMA long | ROC long | EMA mid | ROC mid | PPO | RSI |
|--------|----------|----------|---------|---------|-----|-----|
| SCTR 3M | 120 | 63 | 30 | 10 | SMA(9,19) sig SMA(6) | 10 |
| SCTR 1M | 80 | 21 | 20 | 5 | SMA(6,13) sig SMA(4) | 7 |
| SCTR 1W | 40 | 10 | 10 | 3 | SMA(4, 8) sig SMA(3) | 5 |

Each variant uses the identical formula:
```
raw = 50 + 2.5 × ( 0.60 × (v1_n + v2_n) / 2
                  + 0.30 × (v3_n + v4_n) / 2
                  + 0.10 × (v5_n + v6_n) / 2 )

SCTR_n = clamp(raw, 0, 99.9)
```

**Caveat:** Shorter-period indicators swing wider, so these variants cluster more
toward 0 and 100 than the standard SCTR. Use for relative ranking within a
watchlist, not for comparing absolute values across different variants.

---

## Columns 12–13 — Composite Scores

### Composite A — Cross-horizon average

```
Composite A = (SCTR + SCTR_1M + SCTR_1W) / 3
```

Averages the standard score with two shorter-scale variants. Rewards stocks that
are technically strong **across all timeframe scales simultaneously**. A stock with
a strong long-term base but broken short-term mechanics scores lower than one
aligned at all scales.

### Composite B — Strength × Momentum

```
Δ1M_norm  = clamp(SCTR_Δ1M + 50, 0, 100)
Composite B = 0.60 × SCTR + 0.40 × Δ1M_norm
```

Maps the 1-month delta from its natural range [≈−50, +50] into [0, 100] by
adding 50, then blends it with the current score. A stock at SCTR=75 with
Δ1M=+15 scores higher than one at SCTR=75 with Δ1M=−10.

| Δ1M | Δ1M_norm | Effect on Composite B |
|-----|----------|-----------------------|
| +30 | 80 | Strong upward boost |
| +10 | 60 | Mild boost |
| 0 | 50 | Neutral (Comp B ≈ SCTR) |
| −10 | 40 | Mild drag |
| −30 | 20 | Strong drag |

When Δ1M = 0, Composite B = 0.6 × SCTR + 0.4 × 50 = 0.6 × SCTR + 20.
A flat SCTR=75 gives Composite B ≈ 65, not 75 — the momentum penalty is real.

---

## Full column index

| # | Column | Range | Type |
|---|--------|-------|------|
| 0 | Is Daily | 0 or 1 | Flag |
| 1 | SCTR | 0–99.9 | Score |
| 2 | SCTR Δ1D | −99 to +99 | Delta |
| 3 | SCTR Δ5D | −99 to +99 | Delta |
| 4 | SCTR Δ1M | −99 to +99 | Delta |
| 5 | SCTR Δ3M | −99 to +99 | Delta |
| 6 | SCTR LT | 0–99.9 | Sub-score |
| 7 | SCTR MT | 0–99.9 | Sub-score |
| 8 | SCTR ST | 0–99.9 | Sub-score |
| 9 | SCTR 3M | 0–99.9 | Scaled score |
| 10 | SCTR 1M | 0–99.9 | Scaled score |
| 11 | SCTR 1W | 0–99.9 | Scaled score |
| 12 | Composite A | 0–99.9 | Composite |
| 13 | Composite B | 0–99.9 | Composite |
