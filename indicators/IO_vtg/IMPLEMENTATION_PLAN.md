# VTG Combo — Indicator + Pine Screener: Implementation Plan

Rebuild of Oliver Wiedmaier's (Voyage Trading Group) **"VTG Combo Screener"** as a
single Pine v6 script that works **both** as an on‑chart indicator and as a
**TradingView Pine Screener** source, plus a lightweight backtest/stats layer.

Source video: `ALL IN ONE STOCK SCANNER and INDICATOR – Breakouts, back testing and
watchlist builder (TradingView)` — https://www.youtube.com/watch?v=oeWZj4mMKug
(Substack: *NEW INDICATOR*, Jun 24 2025). The original TradingView script
("VTG Builder" / "VTG Breakouts" by `Ollie_AllCaps`) is **invite‑only, closed
source** — this is a clean re‑implementation from the described behaviour and
screenshots, not a port.

---

## 1. What the tool does (from video description + screenshots)

The one script exposes ~11 momentum sub‑models, grouped by use case:

| Use case | Sub‑models |
|---|---|
| **Breakouts** | Slingshot · 4% Breakout · Inside Day Breakout · OEL · (generic) Breakout |
| **Watchlist building** | Pre‑Slingshot · Oops Reversal · Inside Day · Super Oops |
| **Context / filters** | ATR 100%+ · ATR < 100% · extension‑from‑MA (in ATR units) |
| **Backtesting** | replay every historical trigger of one or many edges; hit/return stats |

### On‑chart visuals (from `VGT-tools/usage_1.png`)
- 21 EMA **band/cloud** (shaded) + 50 SMA line.
- Bottom‑left readout box: `21 EMA: x.xx ATR` / `50 SMA: x.xx ATR`
  = current price distance from each MA expressed in **ATR multiples** (extension gauge).
- Signal **labels** on bars (e.g. green `Slingshot` tag).
- **Pre‑Slingshot = yellow bar colouring.**
- Input `Show Labels Only on Current Bar` (declutter historical labels).

### Indicator inputs (from `VGT-tools/usage_4.png`)
`Show Labels Only on Current Bar`, `Show Breakout`, `Show Pre‑Slingshot (yellow bars)`,
`Show Slingshot`, `Show 4% Breakout`, `Show Inside Day`, `Show Inside Day Breakout`,
`Show Oops Reversal`, `Show Super Oops`, `Show OEL`, `Show 100%+ ATR`, `Show < 100% ATR`,
`Inputs in status line`.

### Pine Screener columns (from `usage_2/3.png` + `screener_overview.png`)
`Inside Day Triggered`, `Inside Day Breakout Triggered`, `Oops Reversal`, `Super Oops`,
`OEL Triggered`, `ATR 100%+`, `ATR < 100%`, `Slingshot Triggered`,
`Pre‑Slingshot Triggered`, `4% Breakout Triggered`, `Breakout Triggered`
— each filterable as **True/False**.

---

## 2. Architecture — one script, two modes

**Do not build two scripts.** TradingView's Pine Screener runs a normal
`indicator()` and reads its `plot()` outputs (numeric) on the last bar of every
symbol in a watchlist. So:

```
indicator("VTG Combo", overlay = true)
  ├─ ENGINE            price/MA/ATR series, all sub-model booleans (single symbol, no request.security)
  ├─ VISUAL LAYER      EMA cloud, SMA, extension table, labels, bar-color  → gated by show_* inputs
  ├─ SCREENER LAYER    plot(cond ? 1 : 0, "Slingshot Triggered", display = display.none)  ×N
  │                    plot(atr_ext_21, "Ext 21EMA (ATR)", display = display.none)  (sortable numeric cols)
  ├─ BACKTEST LAYER    plotshape() historical triggers + forward-return stats table
  └─ ALERTS            alertcondition() per sub-model
```

Key facts that make this work:
- Pine Screener **does** pick up plots marked `display = display.none`, so signal
  plots never touch the chart but are still filterable columns.
- Screener columns are numeric only → booleans go out as `1 / 0`, filter `== 1`.
- Also emit continuous numeric columns for sorting/ranking: ATR extension,
  1‑day % change, $ volume, RS vs SPY, range‑as‑%‑of‑ATR.
- Practical budget: keep total plots ≲ 20–25 for a responsive screener.
- No `request.security()` in the screener path — each sub‑model must be
  computable from the symbol's own `open/high/low/close/volume` on the chart TF.

---

## 3. Sub‑model specs (baseline logic — **confirm against video**)

`H1=high[1] L1=low[1] C1=close[1] O1=open[1]`. Baseline daily TF.
Items marked ⚠ are my best reconstruction and need a pass against the walkthrough.

| # | Sub‑model | Baseline logic | Status |
|---|---|---|---|
| 1 | **Slingshot** | `close` closes **back above** `ema(high, L)` for the first time after ≥3 bars below it. `L` default 4. | ✅ already in `dashboard/dashboard.pine` (`s*_sling`) |
| 2 | **Pre‑Slingshot** ⚠ | Still below `ema(high,L)` but coiled to reclaim: `close < ema(high,L)` and `close > open` and `(ema(high,L)-close) <= k*atr` (k≈0.5) — paint bar **yellow**. | 🔨 new |
| 3 | **Breakout** | `close > highest(high, N)[1]` **and** `volume > highest(volume, N)[1]` **and** `close > sma(close, T)`. Defaults N=60, T=200. | ✅ `_pv_compute` in dashboard.pine |
| 4 | **4% Breakout** ⚠ | `close/close[1]-1 >= 0.04` **and** `volume > sma(volume,50)` (Stockbee‑style); optional `close == highest(close,N)`. | 🔨 new |
| 5 | **Inside Day** | `high <= H1 and low >= L1`. | ✅ `inside` in dashboard.pine |
| 6 | **Inside Day Breakout** ⚠ | `inside[1] and close > H1` (breaks the mother‑bar high after an inside day). Bear: `inside[1] and close < L1`. | 🔨 new |
| 7 | **Oops Reversal** | Larry Williams *Oops*: `open < L1 and close > L1` (bull). Bear: `open > H1 and close < H1`. | ✅ `oopsUp/oopsDn` in dashboard.pine |
| 8 | **Super Oops** ⚠ | Stronger reclaim: `open < L1 and close > H1` (opens below prior low, closes above prior **high** — full prior range reclaimed). | 🔨 new |
| 9 | **OEL** | `open == low` (open equals low). Also **OEH** `open == high`. | ✅ `oel/oeh` in dashboard.pine |
| 10 | **ATR 100%+** ⚠ | `(high - low) >= atr(14)` — today's range ≥ 100% of ATR. | 🔨 new |
| 11 | **ATR < 100%** ⚠ | `(high - low) < atr(14)`. | 🔨 new |
| 12 | **Extension gauge** | `ext21 = (close - ema(close,21)) / atr(14)`, `ext50 = (close - sma(close,50)) / atr(14)` → readout box + screener columns. | 🔨 new |

Bonus sub‑models already coded in `dashboard.pine` we can expose for free:
**Kicker**, **3‑Bar Break (up/down)**, **Engulf/expansion**, **OEH**.

> **Open question for you:** can you paste the video transcript (or the key
> timestamps where he defines Pre‑Slingshot, Super Oops, 4% Breakout and the ATR
> filter)? I could not pull captions automatically. Everything marked ⚠ above is a
> placeholder until confirmed.

---

## 4. Reuse from the existing codebase

| Need | Reuse from | Notes |
|---|---|---|
| Oops / OEL / OEH / Inside / Engulf / Kicker / 3‑Bar | `indicators/dashboard/dashboard.pine` `_fetch_D()` body (lines ~308‑319) | strip `request.security`, use local OHLC |
| Slingshot | `dashboard.pine` `s*_sling` (line ~628) | already single‑bar logic |
| N‑day price+volume breakout | `dashboard.pine` `_pv_compute()` (lines ~322‑331) | copy as‑is |
| Distance‑to‑MA % helper | `dashboard.pine` `_dist()` | adapt to ATR units |
| Repo file conventions | `indicators/relative_measured_volatility/`, `indicators/Industry_Group_Strength_Indicator_improvement/` | `visual_<name>.pine` + `.txt` mirror + `tradingview_description.txt` + `*_improvements.md` |

The multi‑symbol table `dashboard/dashboard.pine` (© valpatradd) is a **separate
tool** and stays as‑is. Optionally (Phase 8) we add Pre‑Slingshot / 4% Breakout /
Inside‑Day‑Breakout / Super‑Oops / ATR% columns to it via its `_fetch_D` payload.

---

## 5. File layout

```
indicators/IO_vtg/
├── IMPLEMENTATION_PLAN.md      ← this file
├── resources.md               ← existing (video link)
├── signal_spec.md             ← Phase 0 output: locked definitions + params
├── visual_vtgCombo.pine       ← the single dual-mode script
├── visual_vtgCombo.txt        ← plain-text mirror (repo convention)
├── tradingview_description.txt ← publish text
└── README.md                  ← usage: chart mode + screener mode + backtest
```

Recommended home: **`indicators/IO_vtg/`** (already created; `IO` = your personal
prefix, `vtg` = Voyage Trading Group). Keep everything in this one folder.

---

## 6. Build phases

### Phase 0 — Lock the spec  *(needs the video)*
- Watch the walkthrough; write `signal_spec.md` with exact conditions, EMA/SMA/ATR
  lengths, the 4% and ATR thresholds, and label text/colours.
- Decide the default chart timeframe behaviour (force Daily like `dashboard.pine`
  does, or run native TF).

### Phase 1 — Engine + MA/ATR scaffold
- `indicator("VTG Combo", "VTG Combo", overlay = true, max_labels_count = 500)`.
- Inputs: all `Show *` toggles (match `usage_4.png` names exactly), sub‑model
  params in their own groups, `Labels only on current bar`, `Force Daily` toggle.
- Plot 21 EMA cloud (`plot`+`plot`+`fill`), 50 SMA, ATR(14).
- Extension table (bottom‑left): `ext21`, `ext50` in ATR units, coloured by sign.

### Phase 2 — Port proven sub‑models
Slingshot, Breakout (PV), Oops (bull/bear), OEL/OEH, Inside, Engulf, Kicker,
3‑Bar. Unit‑check each against a couple of known chart examples.

### Phase 3 — New sub‑models
Pre‑Slingshot, 4% Breakout, Inside‑Day Breakout, Super Oops, ATR 100%+ / <100%,
extension gauge. Each is a single `bool` series.

### Phase 4 — Visual layer
- `label.new` per enabled signal (respect `labelsOnlyCurrentBar`).
- `barcolor()` — yellow for Pre‑Slingshot, optional green/red for others.
- `Inputs in status line` handling via `display` args.

### Phase 5 — Screener layer  *(the core deliverable)*
- One `plot(cond ? 1 : 0, "<Name> Triggered", display = display.none)` per
  sub‑model — names verbatim from `usage_2/3.png`.
- Numeric sortable columns: `Ext 21EMA (ATR)`, `Ext 50SMA (ATR)`, `Chg 1D %`,
  `Range/ATR %`, `$ Vol (M)`, optional `RS vs SPY` (this one needs
  `request.security("SPY",...)` — **chart‑mode only**, guard for screener).
- Validate in TradingView: add script as favorite → Pine Screener → pick a
  watchlist → confirm every column appears and True/False filtering works.
- Document the ≤40‑output / no‑`security` constraints in `README.md`.

### Phase 6 — Backtest / stats layer
- `plotshape` historical markers for each enabled edge (this is the "replay every
  trigger" feature).
- Stats table: per edge → trigger count, % closing green next day, avg forward
  return at +1/+3/+5/+10 bars (arrays over history).
- Combine‑edges mode: AND / OR of the enabled sub‑models into one composite
  signal + its own stats row.
- (Optional later) a sibling `strategy()` version for TradingView's Strategy
  Tester.

### Phase 7 — Alerts + docs
- `alertcondition()` per sub‑model + one composite.
- `README.md`, `tradingview_description.txt`, `visual_vtgCombo.txt` mirror.

### Phase 8 — (Optional) dashboard.pine integration
Add the 4 new daily‑pattern columns to `dashboard/dashboard.pine`'s `_fetch_D`
payload so the 20‑symbol table gains the same edges.

---

## 7. Risks / constraints

- **Closed source original** — behaviour is inferred; expect 1–2 tuning passes
  after you compare side‑by‑side with the real script on the same charts.
- **Pine Screener limits** — no `request.*` in screener context, numeric outputs
  only, output count budget, evaluates last bar only (no historical screening).
- **`open == low` exactness** — float equality; original may use a tolerance
  (`open <= low + syminfo.mintick`). Confirm.
- **Timeframe** — most of these are daily setups; on intraday charts we either
  force‑Daily (like `dashboard.pine`) or disable signals. Pick one in Phase 0.
- **RS vs SPY column** works on chart but will be `na` in screener — label it.

---

## 8. Deliverables checklist

- [ ] `signal_spec.md` — locked definitions
- [ ] `visual_vtgCombo.pine` — engine + visuals + screener plots + backtest table + alerts
- [ ] Pine Screener verified on a real watchlist (screenshot)
- [ ] `README.md` (chart + screener + backtest usage)
- [ ] `tradingview_description.txt`
- [ ] `visual_vtgCombo.txt` mirror
- [ ] (opt) `dashboard.pine` new columns
