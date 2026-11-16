# XLP 30-Day Intraday Signal — analysis & TradingView port

Reconstruction and TradingView (Pine v6) implementation of Tom Bowley's
(EarningsBeats.com) **"XLP 30-day cumulative intraday" signal** and its companion
**intraday XLY:XLP ratio**.

Source material: EarningsBeats.com Daily/Weekly Market Reports, Aug–Sep 2026
(`260819-4725`, `260824-4729`, `260825-4730`, `260831-4735`, and the back-to-1999
special report `260901-4737`).

---

## Contents

1. [What the signal is](#1-what-the-signal-is)
2. [The exact math](#2-the-exact-math)
3. [How it differs from the XLY:XLP ratio](#3-how-it-differs-from-the-xlyxlp-ratio)
4. [The TradingView port](#4-the-tradingview-port)
5. [Script inputs (incl. "Set start date")](#5-script-inputs)
6. [Validation against Bowley's charts](#6-validation-against-bowleys-charts)
7. [Caveats & known differences](#7-caveats--known-differences)
8. [Is the signal actually any good?](#8-is-the-signal-actually-any-good)
9. [Non-TradingView options](#9-non-tradingview-options)
10. [Files](#10-files)

---

## 1. What the signal is

Bowley's thesis: **big institutions rotate into defensive consumer-staples (XLP)
during the cash session — buying it "all day long" — ahead of major S&P 500
tops**, and dump staples into capitulation lows. Overnight gaps are treated as
"retail / news" noise; the open→close move is treated as the "professional"
footprint. So the signal only looks at **open→close**.

He publishes it on StockCharts as a hand-maintained **User-Defined Index (UDI)**:

| Symbol | Coverage | Subtitle |
|---|---|---|
| `@XLP30DAY` | Jan 2022 → | "Shows Intraday XLP Accumulation Distribution Over A 30 Day Period" |
| `@XLP30DLT` | 1999 → (`DLT` = long-term) | "Consumer stock rotation over 30 days long-term since 1999" |

### Thresholds (his, eyeballed round numbers)

| Reading | Meaning | Action |
|---|---|---|
| **≥ 106** | heavy intraday **accumulation** of staples | S&P 500 top warning — caution |
| ~100 | no meaningful daytime rotation | neutral |
| **≤ 94** | heavy intraday **distribution** of staples | capitulation — bullish / bottom watch |

### His claimed track record (1999–2026)

- Every major cyclical S&P top since 1999 had a **106+** reading nearby —
  **except Feb 2020** (pandemic, unforecastable): 2000, 2007, 2011, 2015/16,
  2018, Jan 2022 (hit ~110), early 2025, early 2026 (hit ~114 on `@XLP30DLT`).
- **Sub-94** readings marked major bottoms: 2002, 2008–09 era, Feb 2014, 2022
  lows, Apr 2025.
- Weak stretch: **2009–2013**, when 106 was tagged several times with little or no
  subsequent selling (he admits the false positives).

---

## 2. The exact math

Reconstructed from his descriptions (he never published a formula):

```
per trading day :  r_t   = (close_t / open_t − 1) × 100      # open→close %, gap EXCLUDED
rolling window  :  cum30_t = Σ r  over the last 30 trading days
published index :  signal_t = 100 + cum30_t                  # 100 = neutral centreline
```

Cross-checks that pin the reconstruction:

| Report | Quote | Implication |
|---|---|---|
| 8/24/26 weekly | "the 30-day cumulative gain in the XLP is at **+2.61%**" (UDI ~102.6–103.7) | `signal = 100 + cum%` |
| 8/19/26 daily | "almost squarely in neutral **near zero**" | same series, centred at 0 |
| 8/19 & 8/25 | "**ignoring gaps**", "intraday formula" | open→close, not close→close |
| 8/25/26 daily | "the first 30-trading-day reading occurred on **January 4, 2022**" (started Nov 2021) | window = 30 **trading** days = 30 bars |

Simple sum vs. compounding the 30 daily returns differs by < 0.1 index point at
this scale — the script defaults to the simple sum with a toggle for compounding.

---

## 3. How it differs from the XLY:XLP ratio

Bowley already tracked an **intraday XLY:XLP ratio ("ignores gaps")** in his
weekly "Sustainability Ratios" panel. Same philosophy, different instrument:

| | **XLY:XLP intraday (older)** | **XLP30 (the new signal)** |
|---|---|---|
| Legs | Two ETFs — XLY **vs** XLP | One ETF — XLP only |
| Measures | *Relative* daytime performance (discretionary vs. staples) | *Absolute* daytime performance of staples |
| Per-day input | `XLY(open→close%) − XLP(open→close%)` | `XLP(open→close%)` |
| Aggregation | Running cumulative since an anchor date (no lookback) | Fixed **30-trading-day rolling** sum |
| Level meaning | Arbitrary — read slope & divergence vs. $SPX | Calibrated — mean-reverts to 100; 106 / 94 meant to hold across 27 yrs |
| How you use it | Divergence: *"falling while SPX rising = warning"* — no hard trigger | Threshold cross: ≥ 106 caution, ≤ 94 capitulation |
| "Bad" direction | **Down** = defensive | **Up** = defensive |
| Status | "work in progress" dashboard tile | dedicated UDI, back-tested to 1999 |

**Why the XLY leg matters:** XLY is ~20% AMZN + ~15% TSLA — effectively a growth
proxy. The ratio can fall hard purely because Amazon/Tesla sold off intraday,
with nothing defensive happening in staples. XLP30 strips that out: it *only*
answers "are desks buying staples during the session?"

**Overlap:** XLP30 is essentially **the XLP half of the ratio, isolated and put
on a fixed 30-bar window**.
- Ratio falls *because XLP intraday is rising* → both agree (XLP30 up, ratio down).
- Ratio falls *because XLY intraday is collapsing while XLP is flat* → they
  diverge; XLP30 does nothing. That disagreement tells you which mechanism is
  actually driving the tape.

In the 9/1/26 special report Bowley says the next step is to fold XLY's intraday
performance back into the XLP30 methodology — i.e. rebuild a cleaner ratio on top
of the new engine.

---

## 4. The TradingView port

Everything the signal needs is native Pine v6: per-bar `open`/`close`, a 30-bar
rolling sum (`math.sum`), and horizontal lines. Both scripts pull the ETF's
**daily** O/C via `request.security(..., "D", ...)`, so you can drop them in their
own pane under **any** chart (e.g. under `SP:SPX`) and reproduce Bowley's
two-panel layout.

### `xlp30_intraday_signal.pine` — main indicator

- Plots `100 + Σ(30-day XLP intraday %)`.
- Dashed centreline at 100; red line at 106; green line at 94.
- Background shades **red** when ≥ 106, **green** when ≤ 94.
- `alertcondition`s on both threshold crossings.

### `xly_xlp_intraday_ratio.pine` — companion

- Cumulative intraday discretionary-vs-staples index from a chosen anchor date.
- Two methods (see below).
- Dashed line at the start value (parity).

**Read it the way Bowley does:** put `$SPX` in the main pane, these two in
sub-panes. XLP30 pushing toward 106 **and** the XLY:XLP line sloping down while
$SPX makes new highs = the pre-top configuration he flags.

---

## 5. Script inputs

### `xlp30_intraday_signal.pine`

| Input | Default | Purpose |
|---|---|---|
| Sector ETF | `AMEX:XLP` | symbol whose intraday flow is measured |
| Rolling window | `30` | trading-day lookback |
| Top-warning level | `106` | upper hline / red shade / alert |
| Bottom / capitulation level | `94` | lower hline / green shade / alert |
| Compound daily returns | `off` | product of `(1+r)` instead of simple Σ (negligible) |
| Plot raw cumulative % | `off` | centre on **0** instead of **100** |
| **Limit start date** | `off` | when on, hides the plot & shading before the date below |
| **Set start date** | `2022-01-04` | the cut-off used by "Limit start date" |

> On XLP30 the start date is **cosmetic only**. The value on any bar is a
> self-contained 30-bar sum — it does not depend on earlier history — so the date
> just blanks bars before it to declutter the pane and align the left edge with
> Bowley's chart. Window math and alerts are unaffected. Leave "Limit start date"
> off to see full history.

### `xly_xlp_intraday_ratio.pine`

| Input | Default | Purpose |
|---|---|---|
| Numerator | `AMEX:XLY` | discretionary |
| Denominator | `AMEX:XLP` | staples |
| Index start value | `100` | value the line is anchored to on the start date |
| **Method** | `Cumulative spread` | see below |
| **Set start date** | `2022-01-03` | accumulation **resets to the start value** on the first bar at/after this date |

> On the ratio the start date is **structural, not cosmetic**. The line is a
> running cumulative — where you anchor it *is* the definition of the series.
> Match it to Bowley's chart origin (he starts **2022-01-04**) and the line will
> track his scale, not merely his shape.

**Method:**
- **Cumulative spread** *(default — Bowley's method)* — running additive sum of
  `(XLY intraday % − XLP intraday %)`. Checked 2026-10-15 against his 9 Oct
  2026 prints: daily changes @XLYXLP −0.13 and @SPYQQQ −0.47 equal the
  open→close differences to 2 decimals (the ratio method gives −0.11 / −0.49);
  the 2025-high-to-now drop is −20.2 here vs his −20.4.
- **Ratio of compounded indices** — build
  two separately-compounded intraday indices, `iXLY` and `iXLP`, each starting at
  100 on the anchor date, then plot `iXLY / iXLP × 100`. Drifts below 100 when
  XLY intraday cumulatively underperforms XLP intraday. Diverges from the
  spread over multi-year spans.

`input.time` renders the graphical date-picker in the settings dialog — click the
date, don't type a timestamp.

---

## 6. Validation against Bowley's charts

XLP30 pane, ported vs. `@XLP30DAY` / `@XLP30DLT`:

| Feature | Bowley | Port |
|---|---|---|
| Early-2026 peak | ~114 | ~113–114 ✓ |
| Feb-2025 peak | ~108–109 | ~107–108 ✓ |
| Apr-2025 tariff low | ~92–93 (green top-line) | green tick ~92–93 ✓ |
| Current reading (late Aug '26) | 103.4 | ~104 ✓ |

Within ~1 index point across the board — the `100 + Σ 30-day intraday %`
reconstruction is correct. Red shading in early 2025 / early 2026 lands where he
drew his red-dotted "top" lines.

XLY:XLP pane: **shape** reproduces faithfully — up into early 2025, sharp drop at
the March/April 2025 selloff, recovery into fall 2025, then a persistent grind
lower through 2026 while the S&P makes new highs. **Absolute level** depends on
method + anchor date (see §5, §7).

---

## 7. Caveats & known differences

1. **Data vendor differences.** StockCharts and TradingView don't share identical
   XLP OHLC — open prints especially (consolidated vs. primary-listing open).
   Over a 30-day sum small per-bar gaps accumulate, so your line can sit a point
   or two off his. If you want *his* hit rate, recalibrate 106/94 to your data —
   or replace the round numbers with rolling percentile bands (e.g. 90th / 10th
   percentile over 3–5 yrs).
2. **Dividend / split adjustment is harmless here.** `(close/open − 1)` on a
   single bar is scale-invariant, so adjusted vs. unadjusted history doesn't
   matter for XLP30. (It *can* matter for the compounded ratio method over long
   spans — keep both ETFs on the same adjustment setting.)
3. **History depth.** Full replication to 1999 ≈ 6,800 daily bars — fine on
   TradingView Premium; lower tiers cap historical bars. The **live** signal only
   needs 30 bars, so any plan works going forward.
4. **Timeframe.** Keep the indicator on a **daily or higher** chart. It requests
   `"D"` explicitly, but on an intraday chart the values will repaint intrabar.
5. **"30 trading days" = 30 bars.** Holidays/half-days already collapse out of a
   daily series; no calendar math needed.
6. **The XLY:XLP absolute scale won't match Bowley's** unless you set the same
   anchor date and method. The divergence read (slope vs. price) is identical
   regardless.

---

## 8. Is the signal actually any good?

Reasons for measured skepticism:

- **Hindsight-fitted presentation.** The vertical lines are drawn *at known
  tops/bottoms*. "Every top had a 106" is a **recall** claim and says nothing
  about **precision** — 2009–13 fired 106 repeatedly with no selloff, and the
  2023–26 chart has 106+ prints that led only to shallow dips. As a standalone
  trigger it whipsaws.
- **Leading vs. coincident.** "Wall Street KNOWS and positions early" is a strong
  claim. Safer reading: intraday staples outperformance is a real-time
  **risk-appetite gauge** — solid as *confirmation / context*, weaker as a pure
  forecaster.
- **Regime dependence.** Distinguishes "grinding bull" from "topping" reasonably;
  useless for exogenous shocks (2020). The **94 / bottom side has been the more
  reliable half** — bottoms need visible capitulation.
- **Small n.** ~5 clean cyclical tops since 1999. Statistically thin.
- **Better as a spread.** The XLY−XLP intraday spread carries similar information
  with less single-sector noise; Bowley himself wants to fold XLY in.

**Where it stands in the reports:** early 2025 and early 2026 both spiked > 106
ahead of S&P pullbacks — his two best recent live calls. As of 8/31/26 the
reading was ~103.4, rising but below 106 ("correction, not cyclical bear" in his
framing) — and the XLY:XLP intraday line was already grinding to new lows while
$SPX printed highs, the same divergence shape seen before the 2025 and 2026 tops.
That divergence, not the raw 103, is what he was actually worried about.

---

## 9. Non-TradingView options

- **thinkorSwim (thinkScript):** `Sum((close - open) / open * 100, 30) + 100`
- **Python:**
  `(df.close / df.open - 1).mul(100).rolling(30).sum().add(100)`
  — watch your source's `open` quality (Stooq / Norgate good; Yahoo `open` is
  often the weak point).
- **Excel / Google Sheets → StockCharts UDI upload**, exactly as Bowley does it.

---

## 10. Files

| File | What it is |
|---|---|
| `xlp30_intraday_signal.pine` | Main indicator — `100 + Σ(30-day XLP intraday %)`, thresholds 106 / 94 |
| `xly_xlp_intraday_ratio.pine` | Companion — cumulative intraday XLY-vs-XLP index from a chosen anchor date |
| `README.md` | This document |
