# Custom Performance Dashboard

A multi-symbol performance table displaying up to 20 stocks in a single, configurable dashboard. Designed for active traders who track a personal watchlist and want price action signals, technical levels, and candle patterns visible at a glance — without switching between charts.

The script comes pre-filled with 20 semiconductor and photonics names as a starting point. All symbols can be replaced via the indicator settings panel.

---

## Getting Started

1. Open the Pine Script Editor in TradingView
2. Paste the full script and click **Save**
3. Click **Add to chart**
4. The dashboard table appears on the chart — customize symbols and columns in the **Settings** panel

> **Note on TradingView plans:** This script uses 2 `request.security()` calls per symbol (40 total for 20 symbols). It was built and tested on a **Premium subscription**. Free plan users are limited to fewer security calls and may need to reduce the number of active symbols to around 10 to avoid errors. To disable a symbol row, uncheck the toggle next to it in the Symbols settings group.

---

## Dashboard Columns

All column groups can be toggled on or off independently in the settings panel.

| Column Group | Default | What it shows |
|---|---|---|
| **Basic Info** | On | Ticker, price, % change from open, daily % change |
| **Buy Price** | On | Your buy zone / price range (e.g. `240-220`) |
| **Metrics** | On | EMA 10, EMA 20, SMA 50 values |
| **Distances** | On | % distance from current price to each metric |
| **SlingShot** | On | Momentum signal + trigger price |
| **PV Breakout** | On | Price & volume breakout signal |
| **Candle Combos** | On | Pattern detection (see below) |
| **Industry** | On | Notes / sector label per symbol |
| **Trading** | Off | Trigger price, stop loss, Risk:Reward ratio |
| **Price Levels** | Off | Previous day high (PDH) and previous day low (PDL) |
| **Pre-Market** | Off | Pre-market % change |
| **Post-Market** | Off | Post-market % change |

---

## Signals

### SlingShot
Triggers when the close crosses **above** the EMA of the high for the first time after being below it for at least 3 bars. Signals a momentum shift / trend re-engagement.

- **EMA length**: configurable (default 4)
- Output: `Yes` / blank + the trigger price level

### Price & Volume Breakout (PV Breakout)
Confirms a breakout when three conditions align simultaneously:
- Close exceeds the rolling highest high (last N bars)
- Volume exceeds the rolling highest volume (last N bars)
- Price is on the correct side of the trend filter (SMA)

**Long**: above prior high, above prior volume high, above SMA
**Short**: below prior low, above prior volume high, below SMA

Configurable parameters:
- **Price Breakout Period**: bars to look back for highest high/low (default 60)
- **Volume Breakout Period**: bars to look back for highest volume (default 60)
- **Trendline Length**: SMA length used as trend filter (default 200)

---

## Candle Patterns

Detected on the **daily** timeframe regardless of the chart's current timeframe.

| Pattern | Condition |
|---|---|
| **Kicker** | Previous bar bearish, today opens above prior open — bullish reversal |
| **Oops+** | Opens below prior low, closes back above it — failed breakdown |
| **Oops-** | Opens above prior high, closes back below it — failed breakout |
| **OEL** | Open equals Low — full-day bullish pressure |
| **OEH** | Open equals High — full-day bearish pressure |
| **Inside** | High ≤ prior high and Low ≥ prior low — compression / coiling |
| **Engulf** | High > prior high and Low < prior low — engulfing range expansion |
| **3Bar+** | Close breaks above the high of the last 3 bars |
| **3Bar-** | Close breaks below the low of the last 3 bars |

---

## Symbol Configuration

Each of the 20 symbol rows has the following fields editable in the settings panel:

- **Show**: toggle the row on/off
- **Ticker**: the symbol (use exchange prefix if needed, e.g. `NASDAQ:AAPL`)
- **Name**: display label shown in the table
- **Buy Price**: your buy zone, displayed as-is (e.g. `240-220`)
- **Trigger**: entry price level
- **Stop**: stop loss level
- **Notes**: sector, theme, or any label

---

## Table Display Options

| Setting | Options | Default |
|---|---|---|
| Position | Top/Middle/Bottom × Left/Center/Right | Top Left |
| Size | Auto / Tiny / Small / Normal / Large / Huge | Auto |
| Font | Default / Monospace | Default |
| Horizontal offset | 0–n columns right | 0 |
| Vertical offset | 0–n rows down | 0 |
| Frame & Border | Color + width | Transparent / 1px |
