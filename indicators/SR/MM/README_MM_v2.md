# MM_v2 — Market Manipulation Calculator

## What this indicator does

Splits each trading day into 5 time buckets and measures how much price moved in each one.
The goal is to understand **who is driving the price** at different times of day — retail/emotional traders vs. institutional/algorithmic ones.

Runs on a **5-minute chart**. Must be on US regular session hours (9:30–16:00 ET).

---

## The 5 Time Buckets

| Column | Period | What it captures |
|--------|--------|-----------------|
| **Gap** | Prev close → 9:30 open | Overnight move: futures, pre-market news, institutional repositioning |
| **P1** | 9:30 → 10:00 | "Amateur hour" — retail reaction to the open, emotional buying/selling |
| **P2** | 10:00 → 11:00 | Transition — price discovery, early institutional activity |
| **P3** | 11:00 → 14:00 | Institutional session — the quieter, high-conviction window |
| **P4** | 14:00 → 16:00 | Late session — algos, rebalancing, position squaring |

**Total** = Gap + P1 + P2 + P3 + P4 = full day move (close-to-close)

**Sess%** = (Close − 9:30 open) / 9:30 open × 100
Measures the **session** return only, excluding the overnight gap.
A positive Sess% means the stock went up during regular hours.
A negative Sess% on a day with a positive Total means the stock gapped up but **gave back** during the session.

---

## Color coding

| Color | Meaning |
|-------|---------|
| Green | Positive value (price moved up in that period) |
| Red | Negative value (price moved down in that period) |

Darker = more opaque = stronger signal. Applies to every cell including summary rows.

---

## Summary Rows

### Last 5 / Last 10 / Last 20

Cumulative **dollar sums** of each period over the last N completed trading days.

- Gap/P1–P4 columns: simple sum of dollar moves across the window
- **Sess%** column: compounded price return over the window = (last close − first prevClose) / first prevClose × 100
  This is the true portfolio return for that window, including gaps.

### YTD

Same as above but filtered to calendar year defined in the `YTD Year` input.
**Update this input each January.**

---

## RAD Row (Rolling Average Direction)

Three rolling average metrics, each computed over 5 / 10 / 20 trading days:

| Metric | Formula | What it answers |
|--------|---------|----------------|
| **Sess** | avg of daily (Close − Open) / Open % | Is the regular session bullish on average? |
| **C-10** | avg of daily (Close − 10am) / 10am % | Is smart money (after amateur hour) bullish? |
| **C-11** | avg of daily (Close − 11am) / 11am % | Is pure institutional time bullish? |

Each metric shows three lines: `5d value / 10d value / 20d value`

A value shows `-` until enough days have accumulated (5d needs 5 days, etc.).

### Signal flags (x/3 and x/9)

Each rolling value gets a binary signal: **1 if > 0, 0 if ≤ 0**

- Each metric scores 0–3 (how many of its 5/10/20d windows are positive)
- **Total score 0–9**: sum of all nine signals

| Score color | Meaning |
|-------------|---------|
| Green | Majority positive (≥ threshold) |
| Orange | Mixed signals |
| Red | Majority negative |

A score of 7/9 or higher = strong bullish regime across all timeframes.
A score of 2/9 or lower = strong bearish regime.

---

## Analysis Row

Breaks the displayed window (last N days) into four groups:

| Cell | Components | Theory |
|------|-----------|--------|
| **Gap** | Overnight gap | Pre-market positioning, news, futures — before retail opens |
| **Amateur (P1)** | 9:30–10:00 | Emotional retail reaction to the open |
| **Middle (P3)** | 11:00–14:00 | Quiet midday — low volume, often mean-reverting |
| **Smart (P2+P4)** | 10:00–11:00 + 14:00–16:00 | Institutional bookends: morning conviction + closing positioning |

**Reading the signals:**

- **Gap positive + Amateur negative**: gapped up, retail sold immediately → watch Smart to see if institutions absorb
- **Smart positive, Amateur negative**: institutions buying what retail is selling → bullish accumulation
- **Smart negative, Gap positive**: institutions distributing into gap-up opens → bearish distribution
- **Middle positive**: sustained midday buying = high conviction move, not just reactive
- **All four positive**: broad participation across all time windows → strong trend day

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Max Display Rows | 10 | Number of daily rows shown in the table |
| YTD Year | 2025 | Calendar year for the YTD row — update each January |
| Table Position | top_right | Where the table sits on the chart |
| Override Date Range | off | When off, automatically uses last 6 months. When on, use custom start/end dates |
| Start Date | Jan 1 2024 | Only active when Override is on |
| End Date | Dec 31 2099 | Only active when Override is on |

---

## Known limitations

- Requires **5-minute chart** — will not record data on daily or other timeframes
- Data only accumulates for **completed days** (recorded at 16:00 ET bar)
- Today's data is not recorded until 16:00 ET — the table always shows through yesterday until market close
- YTD row shows `-` for all cells if `YTD Year` does not match any recorded data (e.g. still set to 2025 while looking at 2026 data)
- Rolling RAD shows `-` for the first N−1 days of data (5d needs 5 days, 20d needs 20 days)
