# caseyModule — TODO

## 1) Test the premarket (Pre-H / Pre-L) fix in TradingView
Uncommitted change: Pre-H/Pre-L now come from `request.security(ticker.modify(syminfo.tickerid, session.extended), ...)`.

- [ ] Compiles without errors
- [ ] Chart with extended hours ON: Pre-H/Pre-L same as before (start at the bar where the high/low printed)
- [ ] Chart with RTH only: Pre-H/Pre-L now show, lines start at 09:30
- [ ] Past-day segments (history) still draw Pre-H/Pre-L for the right day, not shifted by one day
- [ ] Bias table "Pre" row: "Premarket forming" before 09:30 on an ETH chart, a value after 09:30, never "n/a" on RTH charts
- [ ] Commit once it's OK

## 2) VWAP: what's the "correct" behavior (LevelUpTools / Brian Shannon)
Current code (`caseyModule.pine:332`): anchor is either "Start of day (incl. premarket)", which resets on the first bar of the calendar day (04:00 ET), or "Regular open" (09:30, hidden outside RTH). The default is the premarket one.

### Findings so far (2026-09-30)
- **Brian Shannon / Alphatrends** ([anchored-vwap](https://alphatrends.net/anchored-vwap/)):
  - "Each trading day begins at 9:30 AM Eastern, that is when the 'regular hours session' begins" and "the daily VWAP resets at the start of each new day."
  - "For equities, users can choose whether to use pre/post market hours in the calculation." So there's no strict rule; his definition of the trading day is RTH.
  - Recommends a 1-minute chart for accurate intraday VWAP.
- **LevelUpTools** (built with Brian Shannon):
  - [Alpha Edge Pro – Intraday](https://www.tradingview.com/script/VvLQSCPh-Alpha-Edge-Pro-Intraday-LevelUp/): auto-anchored **1-day, 2-day, week-to-date, month-to-date AVWAP** + **5-day SMA**; "respecting trading days, hours & holidays". The public page doesn't say whether premarket volume is included.
  - [Trend Follower All-In-One](https://www.tradingview.com/script/d2CNMhFb-Trend-Follower-All-In-One-LevelUp/): release notes mention "AVWAP support for extended hours, pre-market and after-hours". Details aren't public (closed-source).
  - [Video tutorials](https://leveluptools.net/video-tutorials/) were not checked yet; they probably show the premarket handling on a chart.

### Open questions / next steps
- [ ] Watch the LevelUp video tutorials, or load Alpha Edge Pro on an ETH chart: does the 1-day AVWAP start at 04:00 or 09:30?
- [ ] Decide the default: 09:30 regular open (Shannon's definition of the day) vs 04:00 with premarket.
- [ ] Should the VWAP on an RTH chart use extended data (like Pre-H/L now)? Probably not if the anchor is 09:30.
- [ ] Consider adding 2-day VWAP, WTD and MTD AVWAP (LevelUp's set). 5-day SMA is in `indicators/five_day_ma/`.
- [ ] Check Shannon's book *Maximum Trading Gains With Anchored VWAP* (2023) if the notes above aren't enough.
