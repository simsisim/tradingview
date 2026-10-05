//@version=6
// dynamic_requests=false: this script's 3 requests (revenue, EPS, shares outstanding) are
// static (global scope, simple-qualified args), so it needs none of v6's default
// dynamic-request machinery. The Pine Screener allows at most 5 request.*() calls.
// Output is identical; only the request engine changes (same opt-out as Sue in a box).
// NOTE: this forbids calling request.*() inside if/for — keep them global.
indicator("Stockbee Screener", overlay=true, max_bars_back=500, dynamic_requests=false)

// ===== ENTRY MA INPUT =====
// MA period for the ATR-daylight entry threshold.
entryMaPeriod = input.int(70, "Entry MA Period", minval=1, maxval=499, group="Entry Settings", tooltip="MA period for the ATR-daylight entry threshold. MA70 is default.")

// ===== ENTRY THRESHOLD SETTINGS =====
// ATR-based Daylight Threshold (default 2.0x ATR — calibration source not in this repo;
// see .planning/STOCKBEE-AUDIT-2026-10-01/FINDINGS.md C-I2)
atrMultiple = input.float(2.0, "ATR Multiple", minval=0.5, maxval=10, step=0.5, group="Entry Settings", tooltip="Price must be >= X * ATR above MA to enter. Default 2.0x ATR, from an earlier analysis that is not documented alongside this script.")

// ===== DIRECTIONAL INDICATOR FILTER =====
// +DI > -DI confirms bullish trend direction
useDIFilter = input.bool(true, "Use +DI > -DI Filter", group="DI Filter", tooltip="Require +DI > -DI for bullish trend confirmation.")
diPeriod = input.int(14, "DI Period", minval=1, maxval=100, group="DI Filter", tooltip="Period for Directional Indicator calculation (standard: 14)")

// ===== ANTS TTT (TIGHT CONSOLIDATION) FILTER =====
// Tight consolidation setup
useTTTFilter = input.bool(false, "Use Ants TTT Filter", group="Ants TTT", tooltip="Require the tight consolidation pattern: the closing price has barely changed over 3 bars and barely changed today (close-to-close change, not the high-low range), plus the volume, price and gap-bar checks below.")
tttMinVolume = input.int(300000, "TTT Min Volume", minval=1000, group="Ants TTT", tooltip="Lowest daily volume over the prior 3 days (today's bar excluded) must be at least this")
tttMinPrice = input.float(10.0, "TTT Min Price", minval=0.01, group="Ants TTT", tooltip="Minimum price")
tttLookbackGaps = input.int(100, "TTT Gap Lookback", minval=1, maxval=499, group="Ants TTT", tooltip="Bars to look back for a gap bar. A gap bar here means a close more than 20% above the prior close with a high-low range under 4% of price. Ordinary opening gaps are not counted.")
tttMaxPct3Bar = input.float(1.5, "TTT Max % 3-Bar", minval=0.1, group="Ants TTT", tooltip="Max % change between today's close and the close 3 bars ago (consolidation)")
tttMaxPctToday = input.float(0.3, "TTT Max % Today", minval=0.01, group="Ants TTT", tooltip="Max % change between today's close and yesterday's close")

// ===== ANTS BULLISH (MWG - MOMENTUM WITHOUT GAPS) FILTER =====
// Controlled momentum with no disruptive gaps
useMWGFilter = input.bool(false, "Use Ants Bullish Filter", group="Ants Bullish", tooltip="Require momentum without gaps pattern (controlled moves)")
mwgMinVolume = input.int(100000, "MWG Min Volume", minval=1000, group="Ants Bullish", tooltip="Minimum volume threshold")
mwgMinVolDays = input.int(3, "MWG Volume Days", minval=1, maxval=60, group="Ants Bullish", tooltip="Days for volume check")
mwgMinPrice = input.float(10.0, "MWG Min Price", minval=0.01, group="Ants Bullish", tooltip="Minimum price")
mwgLookbackGaps = input.int(100, "MWG Gap Lookback", minval=1, maxval=499, group="Ants Bullish", tooltip="Bars to look back for a gap bar. A gap bar here means a close more than 20% above the prior close with a high-low range under 4% of price. Ordinary opening gaps are not counted.")
mwgMaxDayPct = input.float(0.4, "MWG Max Day %", minval=0.05, group="Ants Bullish", tooltip="Max |today % change| (controlled move)")

// ===== BULLISH COMBO (BMS) FILTER =====
// Bullish momentum scanner - candle patterns with volume
useBMSFilter = input.bool(false, "Use Bullish Combo Filter", group="Bullish Combo", tooltip="Require bullish candle pattern with volume")
bmsMinPrice = input.float(10.0, "BMS Min Price", minval=0.01, group="Bullish Combo", tooltip="Minimum price")
bmsMinVolCond1 = input.int(1000000, "BMS Cond1 Min Vol", minval=1000, group="Bullish Combo", tooltip="Min volume for Condition 1 (bullish candle)")
bmsMinVolCond2 = input.int(100000, "BMS Cond2 Min Vol", minval=1000, group="Bullish Combo", tooltip="Min volume for Condition 2 (breakout)")
bmsBreakoutPct = input.float(4.0, "BMS Breakout %", minval=0.1, group="Bullish Combo", tooltip="Breakout % for Condition 2")
bmsPriceStablePct = input.float(2.0, "BMS Stability %", minval=0.1, group="Bullish Combo", tooltip="Prior stability % (c1/c2 ratio)")
bmsCloseStrMin = input.float(0.70, "BMS Close Strength", minval=0.0, maxval=1.0, group="Bullish Combo", tooltip="Min close strength (close-low)/(high-low)")

// ===== ATR vs MA (EXTENSION RISK) FILTER =====
// Measures how extended price is from 50d MA in ATR units
// Generic Sue-in-a-box retracement bands (7/10) — no N / CI in this repo. NOTE:
// PEAD_ATR_MA_CALIBRATION.md found 7-14 favourable for PEAD continuation, so these
// bands are not PEAD-calibrated (FINDINGS.md C-I2).
useAtrMaFilter = input.bool(false, "Use ATR vs MA Filter", group="ATR vs MA", tooltip="Filter stocks by extension risk. Excludes severely extended stocks.")
atrMaThreshold = input.float(7.0, "Max ATR Extension", minval=0, maxval=20, step=0.5, group="ATR vs MA", tooltip="Maximum ATR extension allowed (0-7 = normal, 7-10 = elevated, 10+ = severe)")
atrMaPeriod = input.int(50, "MA Period for ATR", minval=1, maxval=499, group="ATR vs MA", tooltip="Moving average period for extension calculation (standard: 50)")

// ===== ADR% (AVERAGE DAILY RANGE) SETTINGS =====
// ADR% measures volatility as the average daily range expressed as percentage of price
adrPeriod = input.int(14, "ADR Period", minval=1, maxval=252, group="ADR%", tooltip="Period for Average Daily Range calculation (standard: 14 or 20 days)")

// Display options
showLabels = input.bool(true, "Show Info Labels", group="Display")

// ===== STOCKBEE EP SCANNER — 4 Fundamental Scans =====
// Uses array accumulation approach (same as Sue in a box) to access multiple quarters.
// Revenue: request.financial with gaps_on, accumulate in array, index back for YoY.
// EPS: request.earnings with gaps_on, accumulate in array, index back for YoY.

// --- YoY comparator with year-spacing check ---
// Array position alone is not enough: if the feed skips a quarter, "4 entries back"
// is 15 months ago and the YoY % is silently wrong. Same function as f_yoyPrior in
// MarketSurge_Earnings_Table.pine; tolerances from its call sites (sales 45d, EPS 60d).
int DAY_MS = 86400000  // one day in ms

// @function Year-ago value for YoY: entry 4 positions back, accepted only when its
// capture time is ~365 days earlier (tolDays jitter); na otherwise.
f_yoyPrior(array<float> vals, array<int> times, int idx, int tolDays) =>
    float prior = na
    if idx >= 4
        int spacing = times.get(idx) - times.get(idx - 4)
        if math.abs(spacing - 365 * DAY_MS) <= tolDays * DAY_MS
            prior := vals.get(idx - 4)
    prior

// @function Index of the sales entry covering the quarter reported at `epsT`, or -1.
// request.financial posts values on the bar where the NEXT fiscal period begins
// (~the covered quarter's end), while request.earnings posts on the report
// publication bar 3-7 weeks later (TradingView support doc 43000564727). So the
// matching sales entry sits 0-85 days BEFORE the EPS report time; the previous
// quarter's entry is >=112 days back, so the window cannot false-match it.
// Same logic as f_matchSalesIdx in MarketSurge_Earnings_Table.pine.
f_matchSalesIdx(array<int> salesTimes, int epsT) =>
    int found = -1
    int nS = salesTimes.size()
    if nS > 0 and not na(epsT)
        for k = nS - 1 to 0
            int st = salesTimes.get(k)
            if st > epsT + 5 * DAY_MS
                continue
            found := epsT - st <= 85 * DAY_MS ? k : -1
            break
    found

// --- Revenue data ---
float rev_raw = request.financial(syminfo.tickerid, "TOTAL_REVENUE", "FQ", gaps=barmerge.gaps_on, ignore_invalid_symbol=true, currency=currency.USD)
// New-quarter event = a value appears or changes (same detector as Sue in a box). The
// value-change term covers 3M+ charts, where consecutive bars both carry a report and
// the na-edge alone never fires after the first one.
bool rev_event = not na(rev_raw) and (na(rev_raw[1]) or rev_raw != rev_raw[1])
var array<float> sb_rev_quarters = array.new<float>()
var array<int> sb_rev_times = array.new<int>()  // capture time of each quarter, parallel to sb_rev_quarters
// Dedup guard: reject events < 60 days after the previous push (restatements /
// re-emits would shift every YoY index by one slot). Quarters are ~91 days apart.
var int sb_rev_lastEventTime = na

if rev_event and (na(sb_rev_lastEventTime) or time - sb_rev_lastEventTime >= 60 * 86400000)
    array.push(sb_rev_quarters, rev_raw)
    array.push(sb_rev_times, time)
    sb_rev_lastEventTime := time
    if array.size(sb_rev_quarters) > 10
        array.shift(sb_rev_quarters)
        array.shift(sb_rev_times)

// --- EPS data ---
float eps_raw = request.earnings(syminfo.tickerid, earnings.actual, gaps=barmerge.gaps_on, lookahead=barmerge.lookahead_off, ignore_invalid_symbol=true)
bool eps_event = not na(eps_raw) and (na(eps_raw[1]) or eps_raw != eps_raw[1])
var array<float> sb_eps_quarters = array.new<float>()
var array<int> sb_eps_times = array.new<int>()  // capture time of each quarter, parallel to sb_eps_quarters
// Same 60-day dedup guard as revenue (see above).
var int sb_eps_lastEventTime = na

if eps_event and (na(sb_eps_lastEventTime) or time - sb_eps_lastEventTime >= 60 * 86400000)
    array.push(sb_eps_quarters, eps_raw)
    array.push(sb_eps_times, time)
    sb_eps_lastEventTime := time
    if array.size(sb_eps_quarters) > 10
        array.shift(sb_eps_quarters)
        array.shift(sb_eps_times)

// --- Market cap (for Growth/Turnaround $11B cap) ---
// Must be the FQ fundamentals request: syminfo.shares_outstanding_total and _float both
// return na on the Pine Screener (checked 2026-10-01), which would zero the chip.
float sb_shares = request.financial(syminfo.tickerid, "TOTAL_SHARES_OUTSTANDING", "FQ", ignore_invalid_symbol=true)
float sb_mktCap = not na(sb_shares) ? sb_shares * close : na

// --- 50-day avg volume in thousands ---
float avgVol50_es = ta.sma(volume, 50)
float avgVol50K = avgVol50_es / 1000

// --- Compute revenue metrics ---
int sb_rev_sz = array.size(sb_rev_quarters)

// Revenue values by quarter (most recent = last element)
float sb_rev_q0 = sb_rev_sz >= 1 ? array.get(sb_rev_quarters, sb_rev_sz - 1) : na  // latest Q
float sb_rev_q1 = sb_rev_sz >= 2 ? array.get(sb_rev_quarters, sb_rev_sz - 2) : na  // 1Q ago
float sb_rev_q2 = sb_rev_sz >= 3 ? array.get(sb_rev_quarters, sb_rev_sz - 3) : na  // 2Q ago
float sb_rev_q3 = sb_rev_sz >= 4 ? array.get(sb_rev_quarters, sb_rev_sz - 4) : na  // 3Q ago
float sb_rev_q4 = f_yoyPrior(sb_rev_quarters, sb_rev_times, sb_rev_sz - 1, 45)  // 4Q ago (same Q last year); na unless ~365d before latest Q
float sb_rev_q5 = f_yoyPrior(sb_rev_quarters, sb_rev_times, sb_rev_sz - 2, 45)  // 5Q ago (1Q ago's YoY comp); na unless ~365d before 1Q ago

// Sales % Chg Last Qtr (YoY: Q0 vs Q4)
float salesGrowthPct = not na(sb_rev_q0) and not na(sb_rev_q4) and sb_rev_q4 > 0 ? ((sb_rev_q0 - sb_rev_q4) / sb_rev_q4) * 100 : na

// Sales % Chg 1Q Ago (YoY: Q1 vs Q5)
float salesGrowth1QAgo = not na(sb_rev_q1) and not na(sb_rev_q5) and sb_rev_q5 > 0 ? ((sb_rev_q1 - sb_rev_q5) / sb_rev_q5) * 100 : na

// Avg Sales % Chg 2Q (average of last 2 quarterly YoY growth rates)
// Fail-closed: requires BOTH quarters' YoY. No single-quarter fallback — scans
// advertising a 2Q average must not pass on 1Q of evidence (short-history symbols).
float avgSalesChg2Q = not na(salesGrowthPct) and not na(salesGrowth1QAgo) ? (salesGrowthPct + salesGrowth1QAgo) / 2 : na

// Trailing 4-quarter annual sales in $M
// No spacing check of its own: every scan that reads it also requires salesGrowthPct,
// which is na when a quarter is skipped between Q0 and Q4. NOT caught: a re-emitted
// quarter that displaces the next real one (duplicate + skip keeps ~365d spacing).
float annualSalesMil = na
if not na(sb_rev_q0) and not na(sb_rev_q1) and not na(sb_rev_q2) and not na(sb_rev_q3)
    annualSalesMil := (sb_rev_q0 + sb_rev_q1 + sb_rev_q2 + sb_rev_q3) / 1000000

// --- Compute EPS metrics ---
int sb_eps_sz = array.size(sb_eps_quarters)

float sb_eps_q0 = sb_eps_sz >= 1 ? array.get(sb_eps_quarters, sb_eps_sz - 1) : na  // latest Q
float sb_eps_q1 = sb_eps_sz >= 2 ? array.get(sb_eps_quarters, sb_eps_sz - 2) : na  // 1Q ago
float sb_eps_q4 = f_yoyPrior(sb_eps_quarters, sb_eps_times, sb_eps_sz - 1, 60)  // 4Q ago (same Q last year); na unless ~365d before latest Q
float sb_eps_q5 = f_yoyPrior(sb_eps_quarters, sb_eps_times, sb_eps_sz - 2, 60)  // 5Q ago (1Q ago's YoY comp); na unless ~365d before 1Q ago

// EPS % Chg Last Qtr (YoY: Q0 vs Q4), using abs(prior) for negative base
float epsChgLastQtr = not na(sb_eps_q0) and not na(sb_eps_q4) and sb_eps_q4 != 0 ? ((sb_eps_q0 - sb_eps_q4) / math.abs(sb_eps_q4)) * 100 : na

// EPS % Chg 1Q Ago (YoY: Q1 vs Q5)
float epsChg1QAgo = not na(sb_eps_q1) and not na(sb_eps_q5) and sb_eps_q5 != 0 ? ((sb_eps_q1 - sb_eps_q5) / math.abs(sb_eps_q5)) * 100 : na

// --- 4 Scan Filters ---

// Scans are named by their screener chip; "Bucket N" is the chip's column position.

// Extreme_Sales (Bucket 2): Extreme Sales Growth (99S)
bool extremeSalesPass = not na(salesGrowthPct) and salesGrowthPct >= 99 and not na(annualSalesMil) and annualSalesMil >= 25 and close >= 10 and not na(avgVol50K) and avgVol50K >= 100

// Shared core for Sales_Growth and Growth_Turnaround: 39%+ sales last Q, 39%+ 2Q avg, $25M+ annual sales, $10+, 100K+ avg vol
bool salesCoreOK = not na(salesGrowthPct) and salesGrowthPct >= 39 and not na(avgSalesChg2Q) and avgSalesChg2Q >= 39 and not na(annualSalesMil) and annualSalesMil >= 25 and close >= 10 and not na(avgVol50K) and avgVol50K >= 100

// Sales_Growth (Bucket 1): Sales Growth (39S/39S)
bool salesGrowthPass = salesCoreOK

// Market cap check: $11B threshold is USD — fail closed on non-USD-quoted symbols
// (shares * close is in chart currency; revenue is forced USD but cap is not).
bool sb_capOK = syminfo.currency == "USD" and not na(sb_mktCap) and sb_mktCap <= 11e9

// Growth_Turnaround (Bucket 0): Growth/Turnaround (small/mid-cap: sales core + $11B cap)
// Listing age is deliberately NOT tested. The Pine Screener cannot measure it: it loads
// 500 chart bars, caps a requested "1M" series at 16 bars and rejects timeframes above
// 1M (checked 2026-10-01), so any bar-count "IPO within 10y" test is always true there
// while still filtering on a chart — the two would disagree for older stocks.
bool growthTurnaroundPass = salesCoreOK and sb_capOK

// Earnings_Sales pairs EPS with sales, so both must describe the same fiscal quarter: the
// newest sales entry has to be the one the newest EPS report covers. Fail-closed while
// TradingView has posted the EPS but not yet the revenue for that quarter.
int sb_salesIdxForEps = f_matchSalesIdx(sb_rev_times, sb_eps_lastEventTime)
bool sb_salesMatchesEps = sb_rev_sz > 0 and sb_salesIdxForEps == sb_rev_sz - 1

// Earnings_Sales (Bucket 3): Earnings + Sales Growth (39E39E)
bool earningsSalesPass = sb_salesMatchesEps and not na(epsChgLastQtr) and epsChgLastQtr >= 39 and not na(epsChg1QAgo) and epsChg1QAgo >= 39 and not na(salesGrowthPct) and salesGrowthPct >= 20 and not na(avgSalesChg2Q) and avgSalesChg2Q >= 20 and not na(annualSalesMil) and annualSalesMil >= 25 and close >= 10 and not na(avgVol50K) and avgVol50K >= 200

// ===== SHARED CALCULATIONS (computed once, reused everywhere) =====
// Single ATR(14) calculation - reused for extension and entry
float atr14 = ta.atr(14)

// Calculate Moving Average (entry MA)
ma = ta.sma(close, entryMaPeriod)

// 21 EMA for screening
ema21 = ta.ema(close, 21)
isBelowEma21 = close < ema21

// 10 EMA for screening
ema10 = ta.ema(close, 10)
isBelowEma10 = close < ema10

// ===== DIRECTIONAL INDICATOR CALCULATION =====
// Calculate +DI and -DI using Wilder's method
[plusDI, minusDI, adxValue] = ta.dmi(diPeriod, diPeriod)
diBullish = plusDI > minusDI

// Apply DI filter based on user setting
passesDI = useDIFilter ? diBullish : true

// ===== ANTS TTT (TIGHT CONSOLIDATION) CALCULATION =====
// Volume condition: min volume over the prior 3 days (today excluded)
ttt_minVol3d = math.min(volume[1], math.min(volume[2], volume[3]))
ttt_volumeOK = ttt_minVol3d >= tttMinVolume

// Price condition
ttt_priceOK = close > tttMinPrice

// 3-bar consolidation: |price change over 3 bars| <= threshold
ttt_pctChange3Bar = close[3] != 0 ? ((close - close[3]) / close[3]) * 100.0 : na
ttt_consolOK = not na(ttt_pctChange3Bar) and math.abs(ttt_pctChange3Bar) <= tttMaxPct3Bar

// Today tight: |close-to-close change| <= threshold (not the high-low range)
float pctChangeToday = close[1] != 0 ? ((close - close[1]) / close[1]) * 100.0 : na
ttt_tightOK = not na(pctChangeToday) and math.abs(pctChangeToday) <= tttMaxPctToday

// "Gap bar": close > 1.2 × prior close AND high-low < 0.04 × close. Not a true
// opening-gap test — it never reads open, so a +25% gap with a normal range is not counted.
isGapBar = not na(close[1]) and (close > 1.2 * close[1]) and ((high - low) < 0.04 * close)

// Bars since the last gap bar (na until the first one ever) — shared by TTT and MWG.
// "No gap in the last N bars, today included" == the last gap is N+ bars back, or never.
int gapBarsSince = ta.barssince(isGapBar)
// Fail-closed: "no gaps in last N bars" is unverifiable until N bars exist.
// Without this guard, young IPOs (exactly where gaps live) pass by default.
ttt_noGapsOK = bar_index >= tttLookbackGaps and (na(gapBarsSince) or gapBarsSince >= tttLookbackGaps)

// Final TTT signal
ttt_pass = ttt_volumeOK and ttt_priceOK and ttt_consolOK and ttt_tightOK and ttt_noGapsOK
passesTTT = useTTTFilter ? ttt_pass : true

// ===== ANTS BULLISH (MWG) CALCULATION =====
// Momentum conditions (any one must pass)
mwg_min30 = ta.lowest(close, 30)
mwg_avg7 = ta.sma(close, 7)
mwg_avg65 = ta.sma(close, 65)

mwg_mom1 = mwg_min30 > 0 and close / mwg_min30 >= 1.20  // 20% above 30-day low
mwg_mom2 = mwg_avg65 > 0 and mwg_avg7 / mwg_avg65 >= 1.05  // 7-day avg 5% above 65-day avg
mwg_momentumOK = mwg_mom1 or mwg_mom2

// Price above minimum
mwg_priceOK = close > mwgMinPrice

// No gaps in the MWG lookback (shares gapBarsSince from the TTT section).
// Fail-closed until full lookback window exists (same rationale as TTT above).
mwg_noGapsOK = bar_index >= mwgLookbackGaps and (na(gapBarsSince) or gapBarsSince >= mwgLookbackGaps)

// Volume condition: min volume in N days
mwg_minVolNd = ta.lowest(volume[1], mwgMinVolDays)
mwg_volumeOK = mwg_minVolNd >= mwgMinVolume

// Controlled daily move (reuse pctChangeToday from TTT)
mwg_controlledMove = not na(pctChangeToday) and math.abs(pctChangeToday) <= mwgMaxDayPct

// Final MWG signal
mwg_pass = mwg_momentumOK and mwg_priceOK and mwg_noGapsOK and mwg_volumeOK and mwg_controlledMove
passesMWG = useMWGFilter ? mwg_pass : true

// ===== BULLISH COMBO (BMS) CALCULATION =====
// Condition 1: Bullish candle setup
bms_bullishCandle = open > 0 and (close - open) / open >= 0.02  // 2% candle body
bms_highVolume = volume > bmsMinVolCond1
bms_continuation = math.abs(close[1] - open[1]) <= (close - open)
bms_stability = close[2] != 0 and math.abs(close[1] / close[2] - 1.0) <= (bmsPriceStablePct / 100.0)
bms_condition1 = bms_bullishCandle and bms_highVolume and bms_continuation and bms_stability

// Condition 2: Breakout setup
bms_breakout = close[1] > 0 and close / close[1] >= (1.0 + bmsBreakoutPct / 100.0)
bms_volumeSurge = volume > volume[1]
bms_minVolume2 = volume >= bmsMinVolCond2
bms_condition2 = bms_breakout and bms_volumeSurge and bms_minVolume2 and bms_stability

// Common filters
bms_priceOK = close >= bmsMinPrice

// Close strength: (close - low) / (high - low)
bms_range = high - low
bms_closeStrength = bms_range > 0 ? (close - low) / bms_range : na
bms_closeStrengthOK = not na(bms_closeStrength) and bms_closeStrength >= bmsCloseStrMin

// Final BMS signal
bms_pass = (bms_condition1 or bms_condition2) and bms_priceOK and bms_closeStrengthOK
passesBMS = useBMSFilter ? bms_pass : true

// ===== ATR vs MA (EXTENSION RISK) CALCULATION =====
// Measures how extended price is from 50d MA in ATR units
// Risk labels (text only — this script draws no colour bands):
// below MA, 0-7 ATR (normal), 7-10 ATR (elevated risk), 10+ (severe risk)
float ma50_atr = ta.sma(close, atrMaPeriod)
// Same formula as Sue in a box / Clean Relative Volume / Ticker_Snapshot_Table (retune in
// lockstep): (% above MA) / (ATR as % of price). The 7/10 bands were set on this form.
float atrPct = not na(atr14) and close > 0 ? atr14 / close : na
float pctGainFromMa = not na(ma50_atr) and ma50_atr > 0 ? (close - ma50_atr) / ma50_atr : na
float extensionAtr = not na(atrPct) and atrPct > 1e-10 and not na(pctGainFromMa) ? pctGainFromMa / atrPct : na

// ATR vs MA risk category
string atrMaRisk = na(extensionAtr) ? "N/A" : extensionAtr < 0 ? "Below MA" : extensionAtr < 7 ? "Normal" : extensionAtr < 10 ? "Elevated" : "Severe"

// ATR vs MA filter pass (allows stocks below threshold)
bool passesAtrMa = useAtrMaFilter ? (not na(extensionAtr) and extensionAtr <= atrMaThreshold) : true

// ===== ADR% (AVERAGE DAILY RANGE PERCENTAGE) CALCULATION =====
// ADR% = Average of (High - Low) / Close * 100 over N periods
// Measures volatility - higher ADR% = more volatile stock
float dailyRangePct = close > 0 ? (high - low) / close * 100 : na
float adrPct = ta.sma(dailyRangePct, adrPeriod)

// ===== EXTENSION FROM MA70 (Primary Extension Metric) =====
// Extension uses a fixed MA70 (risk thresholds from an earlier MA70 analysis; artefact not in this repo)
// Based on 11,180 historical signals (directional; Wilson CI not computed):
// Green: <6x (safe), Orange: 6-7x (elevated), Red: 7-8x (extended), Maroon: >8x (danger - negative returns)
float ma70_fixed = ta.sma(close, 70)
float extensionMA70 = not na(atr14) and atr14 > 0 and not na(ma70_fixed) ? (close - ma70_fixed) / atr14 : na

// Extension risk category based on MA70
string extensionRisk = na(extensionMA70) ? "N/A" : extensionMA70 < 0 ? "Below MA" : extensionMA70 < 6 ? "Safe" : extensionMA70 < 7 ? "Elevated" : extensionMA70 < 8 ? "Extended" : "Danger"

// ===== TI65, 9M VOL, +4% CHANGE CALCULATIONS =====
// TI65: Trend Intensity = avgC7 / avgC65 (reuses mwg_avg7 and mwg_avg65)
float ti65 = mwg_avg65 > 0 ? mwg_avg7 / mwg_avg65 : na

// 9M Vol: Volume >= 9,000,000 AND today's volume > yesterday's AND close up 4%+ vs yesterday
bool is9mVol = volume >= 9000000 and volume > volume[1] and close >= 1.04 * close[1]

// Stockbee 4% B/O (breakout): close up 4%+ AND today's volume > yesterday's.
// Full Stockbee 4% scan minus the version-dependent liquidity floor.
bool isPlus4Breakout = not na(pctChangeToday) and pctChangeToday >= 4.0 and volume > volume[1]

// Stockbee 4% B/D (breakdown): close down 4%+ AND today's volume > yesterday's.
bool isMinus4Breakdown = not na(pctChangeToday) and pctChangeToday <= -4.0 and volume > volume[1]

// ===== ENTRY & EXIT SIGNALS =====
// Daylight indicator
float daylightPercent = ma > 0 ? ((close - ma) / ma) * 100 : na

// ATR-based threshold: Price must be >= ATR multiple above MA (reuse atr14)
atrThreshold = atrMultiple * atr14
entryThresholdPrice = ma + atrThreshold
float entryThresholdPct = ma > 0 ? (atrThreshold / ma) * 100 : na  // For display purposes

// Entry condition: Price >= MA + (ATR multiple * ATR) AND passes all enabled filters
optimalEntry = close >= entryThresholdPrice and passesDI and passesTTT and passesMWG and passesBMS and passesAtrMa

// EXIT SIGNAL: 10-day MA violated for 3+ consecutive days
ma10 = ta.sma(close, 10)
isBelow10MA = close < ma10

// Count consecutive days below 10-day MA
var int consecutiveDaysBelow10MA = 0
if isBelow10MA
    consecutiveDaysBelow10MA := consecutiveDaysBelow10MA + 1
else
    consecutiveDaysBelow10MA := 0

// Exit signal triggered when 3+ consecutive days below 10-day MA
exitSignal = consecutiveDaysBelow10MA >= 3

// ===== PLOTS FOR PINE SCREENER =====
// SCREENER CHIPS (display.data_window) - Pine Screener data-window only, off-chart (plot order = column order)
// 1-4: Stockbee EP Scanner chips
plot(growthTurnaroundPass ? 1 : 0, "Growth_Turnaround", display=display.data_window)  // Bucket 0: 39%+ sales last Q + 2Q avg, market cap <= $11B (no listing-age test)
plot(salesGrowthPass ? 1 : 0, "Sales_Growth", display=display.data_window)  // Bucket 1: 39%+ sales last Q + 2Q avg
plot(extremeSalesPass ? 1 : 0, "Extreme_Sales", display=display.data_window)  // Bucket 2: 99%+ sales last Q
plot(earningsSalesPass ? 1 : 0, "Earnings_Sales", display=display.data_window)  // Bucket 3: EPS YoY 39%+ in EACH of the last 2 quarters (abs base, so a narrowing loss counts) + 20%+ sales
// 5-7: Ants pattern chips
plot(ttt_pass ? 1 : 0, "Ants TTT", display=display.data_window)  // Tight consolidation pattern
plot(mwg_pass ? 1 : 0, "Ants Bullish", display=display.data_window)
plot(bms_pass ? 1 : 0, "Bullish Combo", display=display.data_window)
// 8-15: Trend, momentum & volume chips
plot(ti65, "TI65", display=display.data_window)  // Trend Intensity: avgC7/avgC65 (>= 1.05 bullish, <= 0.95 bearish — same bands as Stockbee_chart_indicator.pine)
plot(adxValue, "ADX", display=display.data_window)  // Average Directional Index - trend strength (>25 = strong trend)
plot(diBullish ? 1 : 0, "DI", display=display.data_window)  // Directional Indicator: 1 = +DI > -DI (bullish), 0 = bearish
plot(isBelowEma10 ? 1 : 0, "Below_10EMA", display=display.data_window)
plot(isBelowEma21 ? 1 : 0, "Below_21EMA", display=display.data_window)
plot(is9mVol ? 1 : 0, "9M_Vol", display=display.data_window)  // 9M+ volume AND vol > prior day AND close +4% (always a subset of Plus_4Pct_Breakout)
plot(isPlus4Breakout ? 1 : 0, "Plus_4Pct_Breakout", display=display.data_window)  // Stockbee 4% B/O: +4% AND today's vol > prior day
plot(isMinus4Breakdown ? 1 : 0, "Minus_4Pct_Breakdown", display=display.data_window)  // Stockbee 4% B/D: -4% AND today's vol > prior day

// Background color for optimal entry zone
bgcolor(optimalEntry ? color.new(color.lime, 95) : na, title="Optimal Entry Zone")

// Background color for exit signal warning
bgcolor(exitSignal ? color.new(color.red, 92) : na, title="Exit Signal Warning")

// Plot visual indicators

// Entry signal indicator
plotshape(optimalEntry and not optimalEntry[1], "Entry Signal", shape.circle, location.belowbar,
         color.lime, size=size.small, text="ENTRY")

// Exit signal indicator
plotshape(exitSignal and not exitSignal[1], "Exit Warning", shape.xcross, location.abovebar,
         color.red, size=size.normal, text="EXIT")

// Create info label
var label infoLabel = na
if showLabels and barstate.islast
    label.delete(infoLabel)

    // Build Ants status string
    string antsText = ""
    if useTTTFilter or useMWGFilter or useBMSFilter
        antsText := "-------------\nAnts Patterns:\n"
        if useTTTFilter
            antsText := antsText + "  TTT: " + (ttt_pass ? "PASS" : "FAIL") + "\n"
        if useMWGFilter
            antsText := antsText + "  MWG: " + (mwg_pass ? "PASS" : "FAIL") + "\n"
        if useBMSFilter
            antsText := antsText + "  BMS: " + (bms_pass ? "PASS" : "FAIL") + "\n"

    // Build ATR vs MA status string
    string atrMaStatusText = na(extensionAtr) ? "N/A" : str.tostring(extensionAtr, "#.##") + " (" + atrMaRisk + ")"
    string atrMaFilterText = useAtrMaFilter ? (passesAtrMa ? " PASS" : " FAIL") : ""

    // Build Extension MA70 status string
    string extMA70Text = na(extensionMA70) ? "N/A" : str.tostring(extensionMA70, "#.#") + "x ATR (" + extensionRisk + ")"

    // Build TI65/9MVol/4% B/O & B/D status
    string ti65Text = na(ti65) ? "N/A" : str.tostring(ti65, "#.###")
    string vol9mText = is9mVol ? "YES (" + str.tostring(volume / 1000000, "#.#") + "M)" : "No"
    // Volume-confirmed 4% moves (Stockbee). Show the day's % when the signal fires.
    string breakout4pctText = isPlus4Breakout ? "YES (+" + str.tostring(pctChangeToday, "#.#") + "%)" : "No"
    string breakdown4pctText = isMinus4Breakdown ? "YES (" + str.tostring(pctChangeToday, "#.#") + "%)" : "No"

    string labelText = "MA Period: " + str.tostring(entryMaPeriod) + "-day\n" +
                 "-------------\n" +
                 "TI65: " + ti65Text + "\n" +
                 "9M Vol: " + vol9mText + "\n" +
                 "4% B/O (vol>prior): " + breakout4pctText + "\n" +
                 "4% B/D (vol>prior): " + breakdown4pctText + "\n" +
                 "-------------\n" +
                 "DI Filter: " + (diBullish ? "+DI > -DI BULLISH" : "+DI < -DI BEARISH") + "\n" +
                 "ADR%: " + (na(adrPct) ? "N/A" : str.tostring(adrPct, "#.##") + "%") + "\n" +
                 "Extension (MA70): " + extMA70Text + "\n" +
                 "ATR vs MA (" + str.tostring(atrMaPeriod) + "d): " + atrMaStatusText + atrMaFilterText + "\n" +
                 antsText +
                 "Entry Threshold: " + str.tostring(atrMultiple, "#.#") + "x ATR (" + (na(entryThresholdPct) ? "N/A" : str.tostring(entryThresholdPct, "#.#") + "%") + ")\n" +
                 "Daylight: " + (na(daylightPercent) ? "N/A" : str.tostring(daylightPercent, "#.#") + "%") + (optimalEntry ? " OPTIMAL" : "") + "\n" +
                 "Exit Signal: " + (exitSignal ? "EXIT (" + str.tostring(consecutiveDaysBelow10MA) + "d)" : "HOLD")

    color labelColor = optimalEntry ? color.new(color.green, 20) : color.new(color.gray, 20)

    infoLabel := label.new(bar_index, high, labelText,
                          style=label.style_label_down,
                          color=labelColor,
                          textcolor=color.white,
                          size=size.normal)

// Alert conditions
// Entry & Exit alerts
alertcondition(optimalEntry and not optimalEntry[1], "Optimal Entry Zone", "{{ticker}} entered OPTIMAL ENTRY ZONE at {{close}}")
alertcondition(exitSignal and not exitSignal[1], "Exit Signal Triggered", "{{ticker}} EXIT SIGNAL - Price below MA10 for 3+ days at {{close}}")


