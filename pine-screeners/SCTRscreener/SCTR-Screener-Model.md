# SCTR Screener — Mathematical Model & Implementation Guide

## 1. What is SCTR?

The **StockCharts Technical Rank (SCTR)**, conceived by John Murphy, is a 0–100 score that ranks a
stock's technical strength using six indicators across three time horizons. It is commonly called
"scooter." The score tells you *where a stock stands technically*, not whether it is cheap or
overvalued.

The canonical lookback is **~5 months** — driven by the 125-day Rate-of-Change, which is the
longest raw lookback in the formula. The 200-day EMA is also used, but as a reference level rather
than a raw window.

---

## 2. The Formula (Murphy / TradingCharts correct version)

```
var1 = (close - EMA(close, 200)) / EMA(close, 200) × 100   ← % above/below 200-day EMA
var2 = ROC(close, 125)                                       ← 125-day Rate-of-Change (~5M)
var3 = (close - EMA(close, 50))  / EMA(close, 50)  × 100   ← % above/below 50-day EMA
var4 = ROC(close, 20)                                        ← 20-day Rate-of-Change (~1M)
var5 = (PPO_hist - PPO_hist[2]) / 3                         ← 3-day slope of PPO histogram ÷ 3
var6 = RSI(14) - 50                                          ← RSI centered on zero

SCTR = 50 + 2.5 × ( 0.60 × avg(var1, var2)
                   + 0.30 × avg(var3, var4)
                   + 0.10 × avg(var5, var6) )

SCTR = clamp(SCTR, 0, 99.9)
```

Where `PPO` uses SMA(12) and SMA(26), signal line SMA(9):
```
PPO_line = (SMA(close,12) - SMA(close,26)) / SMA(close,26) × 100
PPO_signal = SMA(PPO_line, 9)
PPO_hist = PPO_line - PPO_signal
```

### Why `50 + 2.5 × (...)`?

The formula is designed so that a stock *perfectly at its moving averages, with flat momentum
and RSI = 50* scores exactly **50**. The `2.5` scaling factor stretches a typical range of
indicator values into the 0–100 window. A stock with extreme positive readings across all six
indicators will approach 100; extreme negative readings approach 0.

### Time-horizon weights

| Horizon | Weight | Indicators | Typical lookback |
|---|---|---|---|
| Long-term | 60% | 200d EMA %, 125d ROC | 5–10 months |
| Medium-term | 30% | 50d EMA %, 20d ROC | 1–3 months |
| Short-term | 10% | PPO histogram slope, RSI(14) | days–weeks |

The 60% long-term weight means SCTR is *structurally biased toward sustained trends*. A stock
cannot score 90 from short-term momentum alone.

---

## 3. Three Analytical Approaches — and Why Each Exists

### Approach A — SCTR Deltas (velocity of rank)

**Core question:** Is this stock's technical rank *improving or deteriorating*, and how fast?

A stock at SCTR = 75 that was at 60 one month ago is fundamentally different from one that was at
90 one month ago — even though today's score is identical. The delta tells you the *direction and
speed* of change.

```
SCTR Δ1D  = SCTR[today]  − SCTR[1 bar ago]
SCTR Δ5D  = SCTR[today]  − SCTR[5 bars ago]   (≈ 1 calendar week)
SCTR Δ1M  = SCTR[today]  − SCTR[21 bars ago]  (≈ 1 trading month)
SCTR Δ3M  = SCTR[today]  − SCTR[63 bars ago]  (≈ 1 trading quarter)
```

**How to use:**
- Sort by `SCTR Δ1D` desc → stocks gaining technical strength *today*
- Sort by `SCTR Δ5D` desc → weekly momentum in technical rank
- Sort by `SCTR Δ3M` desc → sustained structural improvement over a quarter
- Combine: `SCTR > 60 AND SCTR Δ1M > 5` → strong stocks that are still strengthening

**Interpretation of delta values:**
| Delta | Signal |
|---|---|
| > +10 over 1M | Rapid technical improvement — potential breakout setup |
| +3 to +10 over 1M | Steady rank improvement |
| −3 to +3 over 1M | Rank holding steady |
| < −3 over 1M | Technical deterioration |
| < −10 over 1M | Sharp breakdown — avoid or short |

---

### Approach B — Component Sub-scores (LT / MT / ST)

**Core question:** *Which time horizon* is driving the SCTR?

Each component is extracted from the weighted formula and rescaled to 0–100 independently,
so all three sub-scores are on the same scale as the total SCTR.

```
LT component = 50 + 2.5 × avg(var1, var2)    ← 200d EMA + 125d ROC only
MT component = 50 + 2.5 × avg(var3, var4)    ← 50d EMA + 20d ROC only
ST component = 50 + 2.5 × avg(var5, var6)    ← PPO slope + RSI only
```

Note: These are *not* weighted sub-scores — the weight (60/30/10) tells you how much each
contributes to the total SCTR. The sub-scores themselves are extracted without weights so they are
comparable to each other and to the total.

**How to use:**
- `SCTR LT > 70` → stock is above its long-term averages with sustained uptrend (5M+ base)
- `SCTR ST > 70, SCTR LT < 50` → short-term momentum but long-term trend is down — fade or
  mean-reversion setup
- `SCTR LT > 70, SCTR MT > 70, SCTR ST < 40` → strong trend but short-term exhausted — potential
  pullback entry after ST recovers
- `SCTR LT rising, SCTR MT rising, SCTR ST > 60` → all time horizons aligned — strongest setups

**Divergence signals:**

| Pattern | Meaning |
|---|---|
| LT high, ST low | Strong base, short-term pullback — buy the dip candidate |
| ST high, LT low | Short-term pop in a weak trend — potential fade |
| LT↑ + MT↑ + ST↑ | All horizons aligned bullish — strongest momentum state |
| LT↑ + MT↓ | Long-term uptrend but medium-term deteriorating — early warning |

---

### Approach C — Scaled SCTR Variants (shorter timeframe ranks)

**Core question:** How would Murphy's formula look if optimized for *shorter time horizons*?

The standard SCTR parameters were calibrated for end-of-day data on a 5-month horizon. A
"1-week SCTR" scales all parameters proportionally so the formula retains the same structural
logic but at a compressed timescale.

**Scaling method:** Divide all bar-count parameters by the ratio of the target horizon to the
standard horizon (~125 trading days).

```
Standard (5M):  EMA(200), ROC(125), EMA(50), ROC(20), PPO(12,26,9), RSI(14)
3M variant:     EMA(120), ROC(63),  EMA(30), ROC(10), PPO( 9,19,6), RSI(10)
1M variant:     EMA( 80), ROC(21),  EMA(20), ROC( 5), PPO( 6,13,4), RSI( 7)
1W variant:     EMA( 40), ROC(10),  EMA(10), ROC( 3), PPO( 4, 8,3), RSI( 5)
```

The same formula structure applies:
```
SCTR_1W = 50 + 2.5 × ( 0.60 × avg(var1_1w, var2_1w)
                       + 0.30 × avg(var3_1w, var4_1w)
                       + 0.10 × avg(var5_1w, var6_1w) )
```

**Important caveats:**
- These are *approximations*. The 0–100 scale and `2.5` multiplier were calibrated for the
  standard parameters — shorter-period indicators have wider swings, so these variants will show
  more extreme values near 0 and 100.
- They are most useful for *relative ranking within a watchlist*, not for comparing absolute
  scores across different variants.
- Think of them as "which stocks are strongest technically *right now* at this shorter scale?"

**How to use:**
- `SCTR_1W > 70` → strong short-term technical setup (days–2 weeks horizon)
- `SCTR_3M > SCTR` → medium-term strength is outpacing the longer-term rank — accelerating
- Sort by `SCTR_1W` desc to find short-term momentum leaders in a watchlist
- `SCTR > 70 AND SCTR_1W > 70` → technically strong at *both* scales — high-conviction setup

---

## 4. All Screener Columns at a Glance

| Column | Approach | Formula basis | Sort to find... |
|---|---|---|---|
| `SCTR` | Standard | Murphy formula, 5M params | Top overall technical rank |
| `SCTR Δ1D` | A — Delta | SCTR − SCTR[1] | Today's biggest rank gainers |
| `SCTR Δ5D` | A — Delta | SCTR − SCTR[5] | Weekly rank momentum |
| `SCTR Δ1M` | A — Delta | SCTR − SCTR[21] | 1-month rank acceleration |
| `SCTR Δ3M` | A — Delta | SCTR − SCTR[63] | Sustained structural climb |
| `SCTR LT` | B — Component | 200d EMA + 125d ROC | Long-term trend leaders |
| `SCTR MT` | B — Component | 50d EMA + 20d ROC | Medium-term momentum leaders |
| `SCTR ST` | B — Component | PPO slope + RSI | Short-term technical leaders |
| `SCTR 1W` | C — Scaled | Scaled params, 1W horizon | Short-term rank (days–2W) |
| `SCTR 1M` | C — Scaled | Scaled params, 1M horizon | Medium rank (~1M) |
| `SCTR 3M` | C — Scaled | Scaled params, 3M horizon | Quarterly rank |

---

## 5. Practical Screening Recipes

### Find stocks climbing technically before a breakout
```
SCTR > 50
SCTR Δ1M > 8
SCTR ST > 60
```
_Reasonable overall rank, improving fast, short-term momentum already positive._

### Find multi-timeframe aligned leaders
```
SCTR > 70
SCTR LT > 65
SCTR MT > 65
SCTR ST > 55
```
_All three horizons are bullish — highest-conviction setups._

### Find short-term oversold in long-term uptrend (pullback entries)
```
SCTR LT > 65
SCTR ST < 35
SCTR Δ5D < −3
```
_Long-term trend intact but short-term weak — potential buy-the-dip._

### Find short-term momentum regardless of long-term
```
Sort: SCTR 1W desc
Filter: SCTR 1W > 70
```
_Use when you want fast movers for shorter holds._

---

## 6. Known Limitations

- **SCTR is not percentile-based in Pine Screener.** The original StockCharts SCTR ranks stocks
  *relative to their peer group* (e.g., S&P 500 large caps vs. all US stocks). In Pine Screener,
  the formula is computed per-symbol independently, so a SCTR of 75 does not mean "top 25% of
  the market" — it means the indicator inputs are in the upper portion of their historical range.

- **Scaled variants are approximations.** The `2.5` multiplier was empirically calibrated for the
  5-month parameter set. Shorter-period parameters produce wider raw swings, so `SCTR_1W` will
  cluster near 0 and 100 more often than the standard SCTR.

- **Deltas lag.** `SCTR Δ3M` uses 63-bar-old SCTR values. The SCTR itself already has an
  inherent lag from its long-period EMAs and ROC. Stacking a 3M delta on top means you are
  comparing a lagged indicator to its own lagged history.

- **Short-term component (ST) is noisy.** The PPO histogram slope over 3 days is sensitive to
  single-bar moves. Use `SCTR ST` to confirm, not as a standalone signal.
