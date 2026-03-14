# TradingView Dashboard Generator

Generate a TradingView Pine Script dashboard from a buy-list CSV file.

## Quick Start

1. **Create your buy list**: Make a CSV named `buyList_<name>.csv`
2. **Generate dashboard**: `python3 gen_dashboard.py buyList_<name>.csv`
3. **Load in TradingView**: Copy the generated `db_<name>.pine` into the Pine Editor

## Files

| File | Description |
|------|-------------|
| `buyList_<name>.csv` | Your input buy list (one per strategy/theme) |
| `gen_dashboard.py` | Generator script |
| `db_<name>.pine` | Generated Pine Script — load this into TradingView |

---

## CSV Format

```csv
ticker,BuyPrice,Trigger,Stop,Notes
COHR,240-220,,,Optical/Photonics
MU,375-350,241.53,231.97,Semiconductors
TSM,345-325,,,Semiconductors
```

**Columns:**
- **ticker** *(required)*: Stock symbol. Use exchange prefix if needed (e.g. `GETTEX:RHM`)
- **BuyPrice** *(optional)*: Buy zone or price range (e.g. `240-220`)
- **Trigger** *(optional)*: Entry/trigger price level
- **Stop** *(optional)*: Stop loss price
- **Notes** *(optional)*: Industry or notes

Only `ticker` is required. All other columns can be omitted or left empty.

---

## Running the Generator

### Process all files at once (no argument)

```bash
python3 gen_dashboard.py
```

Finds every `buyList_*.csv` in the current folder and generates a `db_*.pine` for each:

```
✅  buyList_tzar.csv   → db_tzar.pine
✅  buyList_energy.csv → db_energy.pine
```

### Single file — auto-named output

```bash
python3 gen_dashboard.py buyList_tzar.csv
# → produces db_tzar.pine
```

### Single file — explicit output name

```bash
python3 gen_dashboard.py buyList_tzar.csv my_custom.pine
```

**Naming rule:** `buyList_<name>.csv` → `db_<name>.pine`

### Install dependency if needed

```bash
pip install pandas
```

---

## Loading into TradingView

1. Open TradingView → Pine Editor
2. Click **Open** → **Import script**
3. Select the generated `db_<name>.pine`
4. Click **Add to chart**

To update the dashboard (e.g. after editing your CSV), regenerate and re-import.

---

## Dashboard Features

### Columns (toggleable in TradingView settings)

| Column group | Default | Description |
|---|---|---|
| Basic Info | On | Ticker name, Price, Chg from Open %, Daily Chg % |
| Buy Price | On | Buy zone from CSV (e.g. `240-220`) |
| Metrics | On | EMA 10, EMA 20, SMA 50 values |
| Distances | On | % distance from price to each metric |
| SlingShot | On | Breakout pattern signal + trigger price |
| PV Breakout | On | Price & Volume breakout signal |
| Candle Combos | On | Kicker, Oops, OEL/OEH, Inside/Engulf, 3Bar |
| Industry | On | Notes from CSV |
| Trading | **Off** | Trigger, Stop, R:R ratio |
| Price Levels | **Off** | Previous Day High / Low |
| Pre-MP | **Off** | Pre-market change % |
| Post-MP | **Off** | Post-market change % |

All columns can be toggled on/off in the indicator settings panel.

### Candle Patterns
- **Kicker**: Strong bullish reversal
- **Oops**: Failed breakout (Oops+ / Oops-)
- **OEL/OEH**: Open equals Low / Open equals High
- **Inside/Engulf**: Inside bar / Engulfing bar
- **3Bar**: 3-bar breakout (3Bar+ / 3Bar-)

### Technical Indicators
- **SlingShot**: Close crosses above EMA of High (configurable length, default 4)
- **PV Breakout**: Price AND volume breakout above rolling high, confirmed by trend filter
- **Metrics**: EMA/SMA computed on the fetched close series — no extra data requests

---

## Technical Notes

### Request limit (free plan)
TradingView's free plan allows **40 unique `request.security()` calls** per script.
The generator uses exactly **2 calls per symbol** (one for timeframe data, one for daily data),
so 20 symbols = 40 calls — right at the limit with no upgrade needed.

### Max symbols
20 symbol slots per dashboard. To monitor more symbols, create multiple buy lists and run once:
```bash
# Create buyList_tech.csv, buyList_energy.csv, buyList_tzar.csv ...
python3 gen_dashboard.py
# → db_tech.pine, db_energy.pine, db_tzar.pine
```
Add each generated `.pine` as a separate indicator on the same chart.

### Timeframe
By default the dashboard forces Daily timeframe when the chart is on an intraday resolution.
This can be toggled off in the indicator settings (Timeframe group).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: pandas` | `pip install pandas` |
| CSV not found | Run the command from the same directory as `gen_dashboard.py` |
| Ticker shows no data | Use exchange prefix, e.g. `NASDAQ:AAPL` instead of `AAPL` |
| "Too many requests" error | Reduce symbols below 20, or add the script a second time for a second batch |
| Single quotes breaking script | Already handled automatically — `'` is escaped in Notes/BuyPrice |
