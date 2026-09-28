# VTG Combo — indicator (visual) redesign plan

Goal: make the **indicator view** match Oliver Wiedmaier's "VTG Combo Scanner"
UX. This round is about the chart visuals and the settings panel only — the
Pine Screener layer keeps working but becomes invisible in the indicator UI.

Reference: `VGT-tools/usage_1.png` (chart), `VGT-tools/screener_overview.png`
(his Inputs tab), `VGT-tools/usage_4.png` (his full toggle list),
`~/Desktop/Snapshot_2026-09-07_13-15-03.png` (our current Style tab).

---

## 1. What's actually different

Our screenshot is the **Style** tab; his is the **Inputs** tab — not the same
thing, so the gap looks bigger than it is. Still, three real problems:

1. **Every screener column is a `plot()`** → 17 rows in our Style tab
   (`Inside Day Triggered`, `Ext 21EMA (ATR)`, …). His Style tab is nearly
   empty because his visuals are **label / line / table objects**, not plots.
2. **Input names/'"Triggered"' vocabulary** — as an indicator he only has
   "Show X" switches. No "Triggered", no numeric outputs surfaced.
3. **Historical label clutter** — we stack labels on every past bar unless the
   toggle is off. He defaults to "labels only on current bar" so the chart
   shows just the live state.

## 2. Design principles

- **Visuals = drawing objects, not plots.** Labels, `barcolor()`, lines, one
  table. This is what keeps his Style tab clean and is the correct model for
  "Show X → draw something".
- **Screener plots stay, but go dark.** Emit each as
  `plot(cond ? 1 : 0, "<name>", display = display.none, editable = false)`.
  `display.none` keeps it off the chart; `editable = false` removes its row
  from the Style tab (verify in-tool) while Pine Screener can still read it.
  → one script, two modes, clean indicator UI. *(Fallback if `editable=false`
  doesn't drop the Style row: split into `VTG Combo` + `VTG Combo Screener`.)*
- **One script, native chart TF** (unchanged decisions).
- Every drawn element is gated by its own `Show *` switch and does nothing when
  off.

## 3. Settings panel — target layout

Top level (no group header, like his), in his order:

| Input | Type | Default |
|---|---|---|
| Show Labels Only on Current Bar | bool | **true** |
| Show Breakout | bool | false |
| Show Pre-Slingshot (yellow bars) | bool | false |
| Show Slingshot | bool | true |
| Show 4% Breakout | bool | true |
| Show Inside Day | bool | false |
| Show Inside Day Breakout | bool | true |
| Show Oops Reversal | bool | false |
| Show Super Oops | bool | false |
| Show OEL | bool | true |
| Show 100%+ ATR | bool | false |
| Show < 100% ATR | bool | false |
| Inputs in status line | bool | true |

Collapsed groups **below** (params he doesn't foreground):

- **Moving averages** — Show EMA cloud (t), EMA length (21), Show EMA line (t),
  Show SMA line (t), SMA length (50), cloud source (EMA of H/L vs band).
- **ATR / extension** — ATR length (14), Show extension table (t), table position.
- **Slingshot** — EMA(high) length (4), bars below before reclaim (3).
- **Breakout** — price lookback (60), volume lookback (60), trend SMA (200),
  require volume / require trend (t/t).
- **4% Breakout** — % threshold (4.0), volume filter (SMA 50) on/off.
- **OEL** — tolerance in ticks (0).
- **Extra triggers (chart only)** — Show OEH, Show Kicker, Show 3-Bar Break,
  Show Engulf (all false). Keeps the main list a 1:1 match to his; these stay
  available for anyone who wants them.

> **Resolved (user):** bar coloring stays **historical**; only labels are
> suppressed to the current bar when "labels only on current bar" is on.
> Copy his default `Show *` states exactly (see `signal_spec.md`).
> Keep OEH / Kicker / 3-Bar / Engulf in **both** indicator and screener.
> "Breakout" toggle = the **composite** (Slingshot OR 4% BO OR Inside Day
> Breakout OR OEL), not a standalone N-day-high breakout.

## 4. Visual vocabulary per trigger

Two channels: **bar color** (one state per bar, priority-ranked) and **labels**
(stack above/below the bar). Lines are optional extras.

| Trigger | Channel | Style | Notes |
|---|---|---|---|
| Pre-Slingshot | bar color | **yellow** | his explicit "(yellow bars)" |
| Inside Day | bar color | muted blue/grey | only if Pre-Slingshot not active on that bar |
| 4% Breakout | bar color | bright lime | |
| ATR 100%+ | bar color | orange | lowest priority |
| ATR < 100% | bar color | dim grey | lowest priority |
| Slingshot | label (below) | green rounded tag `Slingshot` | matches `usage_1.png`; intrabar trigger |
| Breakout (composite) | label (below) | teal tag `Breakout` | fires when any breakout edge hits today |
| Inside Day Breakout | label (below) | green `ID Break↑` / red `ID Break↓` | |
| Oops Reversal | label | green `Oops+` (bull primary) / red `Oops-` | |
| Super Oops | label | green `Super Oops` | EXTRA, our definition |
| OEL / OEH | small triangle + label | `OEL` below / `OEH` above | |

**Bar-color priority** (first match wins):
Pre-Slingshot → 4% Breakout → Inside Day → ATR 100%+ → ATR < 100%.
Rationale: setup/entry states beat pure volatility context.

If two label triggers hit the same bar, stack them (offset y, or concatenate
into one multi-line label).

### EMA cloud + MA lines (keep, retune to match `usage_1.png`)
- Cloud: subtle semi-transparent **blue/lavender** fill. Source =
  `EMA(high, 21)` / `EMA(low, 21)` (tight band that hugs price).
- **21 EMA line — green.**
- **50 SMA line — red.**
- (drop the current orange SMA / teal cloud colors.)

### Extension table (keep, restyle)
- Bottom-left, small, **gold/amber header** like his.
- Two rows: `21 EMA: X.XX ATR`, `50 SMA: X.XX ATR`
  = `(close - MA) / ATR(14)`. Value text green/red by sign.
- Last bar only.

## 5. "Show Labels Only on Current Bar" semantics  — RESOLVED

> **Superseded (2026-09-28):** replaced by the `Show triggers on` dropdown
> (All bars / Current bar only / Last N bars), which now scopes bar paint too,
> plus the ID breakout line and VTG New base box. Original decision kept below.

- **true** (default): every label / triangle renders only when `barstate.islast`.
  **Bar coloring is unaffected — it stays historical** (context, not clutter).
  Table is last-bar anyway.
- **false**: labels render on every historical bar where the trigger fired
  (respecting `max_labels_count`).

## 6. "Inputs in status line" toggle

Cosmetic. Controls whether the `Show *` input values echo in the chart status
line (Pine `input(..., display = ...)`). Low priority — implement last, or set a
sensible fixed `display` and drop the toggle.

## 7. Screener layer — unchanged behaviour, hidden UI

Same 0/1 + numeric columns as today, same names, still always emitted (not
gated by `Show *`). Only change: `display = display.none, editable = false` and
group them in one block at the end of the file with a comment banner. Verify in
the Pine Screener that columns still resolve after adding `editable = false`.

## 8. Open questions — all resolved

1. ✅ Keep bar coloring historical.
2. ✅ Not important now — cloud = `EMA(high,21)` / `EMA(low,21)` band.
3. ✅ Not important now — 21 EMA (green) + 50 SMA (red) only.
4. ✅ Keep OEH / Kicker / 3-Bar / Engulf in both indicator and screener (extras, off by default).
5. ✅ Copy his defaults exactly (`signal_spec.md` table).

Remaining detail tuning (non-blocking, tracked in `signal_spec.md`): 4% Breakout
move basis, ATR-filter move vs range, Pre-Slingshot structure rule, Slingshot
pullback requirement.

## 9. Task list (after sign-off — no code yet)

1. Rebuild the input block to the §3 layout.
2. Replace the visual layer: `barcolor()` state machine (§4 priority) +
   label helper (respecting §5) + optional breakout level line.
3. Retune EMA cloud (blue) + 21 EMA (green) + 50 SMA (red) + gold table.
4. Convert all screener plots to `display.none, editable = false`, banner block.
5. Wire the 4 currently-stubbed triggers' **visuals** now (Pre-Slingshot bar
   color, 4% Breakout bar color, Super Oops label, ATR bars) even though their
   exact logic is still provisional — visual plumbing is independent of the
   final formula.
6. Test in TradingView: Inputs tab matches his; Style tab clean; screener intact.
7. Update `README.md` + `signal_spec.md`.
