#!/usr/bin/env python3
"""
Generate TradingView Pine Script alerts from CSV watchlist.

Usage:
    python3 generate_from_csv.py                        # Process all watchlists in watchlists.txt
    python3 generate_from_csv.py buyList_tzar.csv       # Generate from specific CSV

CSV format:
    ticker,BuyPrice,Notes
    COHR,240-220,buy between these levels
    TSLA,350,buy at this exact level

BuyPrice formats:
    240-220  ->  buy zone  (2 green lines + shaded fill)
                 alerts: price entered zone / price broke below zone
    350      ->  buy level (1 green line)
                 alert: price reached level

Output file named from CSV suffix:
    buyList_tzar.csv  ->  TZAR_alerts.pine
    watchlist_RM.csv  ->  RM_alerts.pine
"""

import csv
import sys
import os
import re


def extract_watchlist_suffix(csv_filename):
    """
    Extract suffix from CSV filename (last underscore-separated segment).
    Examples:
        buyList_tzar.csv  -> TZAR
        watchlist_RM.csv  -> RM
    """
    basename = os.path.basename(csv_filename)
    name_without_ext = os.path.splitext(basename)[0]
    parts = name_without_ext.split('_')
    if len(parts) > 1:
        return parts[-1].upper()
    return name_without_ext.upper() if name_without_ext else "DEFAULT"


def parse_buy_price(buy_price_str, ticker):
    """
    Parse BuyPrice field.
    Returns (buy_type, val1, val2):
        'zone'  -> (val1=upper, val2=lower)   auto-sorted so upper > lower
        'level' -> (val1=level, val2=None)
    Returns None on parse error.
    """
    s = buy_price_str.strip()
    range_match = re.match(r'^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$', s)
    if range_match:
        a = float(range_match.group(1))
        b = float(range_match.group(2))
        return ('zone', max(a, b), min(a, b))
    try:
        return ('level', float(s), None)
    except ValueError:
        print(f"Warning: Skipping {ticker} - invalid BuyPrice '{buy_price_str}'")
        return None


def read_csv(csv_path):
    """Read stock data from CSV. Column names are case-insensitive."""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found!")
        sys.exit(1)

    stocks = []
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_n = {k.strip().lower(): v.strip() for k, v in row.items()}
            ticker = row_n.get('ticker', '').strip()
            if not ticker:
                continue
            buy_price_str = row_n.get('buyprice', '')
            if not buy_price_str:
                print(f"Warning: Skipping {ticker} - missing BuyPrice")
                continue
            parsed = parse_buy_price(buy_price_str, ticker)
            if parsed is None:
                continue
            notes = row_n.get('notes', '').strip()
            buy_type, val1, val2 = parsed
            stocks.append((ticker, buy_type, val1, val2, notes))

    return stocks


MAX_SLOTS = 40


def generate_pine_script(stocks, output_path, watchlist_suffix):
    """Generate Pine Script from stock data, always padded to MAX_SLOTS slots."""

    indicator_name = f"{watchlist_suffix}_alerts"
    short_title = f"{watchlist_suffix} Alerts"

    pine = f"""//@version=5
indicator("{indicator_name}", shorttitle="{short_title}", overlay=true, max_lines_count=500, max_labels_count=500)

// ============================================================================
// MASTER CONTROL
// ============================================================================
string g_master = "Master Control"
enable_all = input.bool(true, "Enable All Alerts", group=g_master, display=display.data_window)
show_all_visual = input.bool(true, "Show All Visual Clues", group=g_master, display=display.data_window)

// ============================================================================
// STOCK TRACKING - PRE-CONFIGURED WITH YOUR WATCHLIST
// ============================================================================
string g_stocks = "Stock Tracking"

"""

    # Stock inputs
    for i, (ticker, buy_type, val1, val2, notes) in enumerate(stocks, 1):
        pine += f"// Stock {i} - {ticker} [{buy_type}]\n"
        pine += f'enable_stock{i} = input.bool(true, "Alert", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'ticker{i} = input.symbol("{ticker}", "{ticker}", inline="{i}", group=g_stocks, display=display.data_window)\n'
        if buy_type == 'zone':
            pine += f'upper{i} = input.float({val1}, "Upper", inline="{i}", group=g_stocks, display=display.data_window)\n'
            pine += f'lower{i} = input.float({val2}, "Lower", inline="{i}", group=g_stocks, display=display.data_window)\n'
        else:
            pine += f'level{i} = input.float({val1}, "Level", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'show_stock{i} = input.bool(true, "Show", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += "\n"

    # Empty slots padded to MAX_SLOTS
    for i in range(len(stocks) + 1, MAX_SLOTS + 1):
        pine += f"// Stock {i} - [empty]\n"
        pine += f'enable_stock{i} = input.bool(false, "Alert", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'ticker{i} = input.symbol("", "", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'upper{i} = input.float(0.0, "Upper", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'lower{i} = input.float(0.0, "Lower", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += f'show_stock{i} = input.bool(false, "Show", inline="{i}", group=g_stocks, display=display.data_window)\n'
        pine += "\n"

    # Visual settings
    pine += """// ============================================================================
// VISUAL SETTINGS
// ============================================================================
string g_visual = "Visual Settings"
line_width = input.int(2, "Line Width", minval=1, maxval=4, group=g_visual, display=display.data_window)
line_style_input = input.string("Solid", "Line Style", options=["Solid", "Dashed", "Dotted"], group=g_visual, display=display.data_window)
extend_lines = input.bool(false, "Extend Lines to Right", group=g_visual, display=display.data_window)
line_length = input.int(50, "Line Length (bars)", minval=10, maxval=500, group=g_visual, tooltip="Number of bars to extend lines when Extend to Right is disabled", display=display.data_window)
show_labels = input.bool(true, "Show Labels", group=g_visual, display=display.data_window)
buy_color = input.color(color.new(color.green, 0), "Buy Color", group=g_visual, display=display.data_window)
zone_transparency = input.int(85, "Zone Fill Transparency", minval=0, maxval=100, group=g_visual, display=display.data_window)

// Convert line style
line_style = line_style_input == "Solid" ? line.style_solid :
             line_style_input == "Dashed" ? line.style_dashed :
             line.style_dotted

// Convert line extension
line_extend = extend_lines ? extend.right : extend.none

// ============================================================================
// ALERT SETTINGS
// ============================================================================
string g_settings = "Alert Settings"
timeframe_alert = input.timeframe("", "Alert Timeframe (blank = current)", group=g_settings, display=display.data_window)

// ============================================================================
// GET PRICE DATA FOR SELECTED TIMEFRAME
// ============================================================================
tf = timeframe_alert == "" ? timeframe.period : timeframe_alert

// ============================================================================
// GET PRICE DATA FOR EACH STOCK
// ============================================================================
"""

    for i in range(1, MAX_SLOTS + 1):
        pine += f'stock{i}_close = enable_all and enable_stock{i} and ticker{i} != "" ? request.security(ticker{i}, tf, close, lookahead=barmerge.lookahead_off) : na\n'

    # Visual drawing
    pine += """
// ============================================================================
// DRAW HORIZONTAL LINES AND LABELS
// ============================================================================
if show_all_visual and barstate.islast
"""

    for i, (ticker, buy_type, val1, val2, notes) in enumerate(stocks, 1):
        pine += f"    // Stock {i} - {ticker} [{buy_type}]\n"
        pine += f"    if show_stock{i} and str.contains(syminfo.tickerid, ticker{i})\n"
        if buy_type == 'zone':
            pine += f"        l_u{i} = line.new(bar_index, upper{i}, bar_index + line_length, upper{i}, extend=line_extend, color=buy_color, style=line_style, width=line_width)\n"
            pine += f"        l_l{i} = line.new(bar_index, lower{i}, bar_index + line_length, lower{i}, extend=line_extend, color=buy_color, style=line_style, width=line_width)\n"
            pine += f"        linefill.new(l_u{i}, l_l{i}, color=color.new(buy_color, zone_transparency))\n"
            pine += f"        if show_labels\n"
            pine += f'            label.new(bar_index, upper{i}, "{ticker} zone ▲ " + str.tostring(upper{i}), style=label.style_label_left, color=buy_color, textcolor=color.white, size=size.small)\n'
            pine += f'            label.new(bar_index, lower{i}, "{ticker} zone ▼ " + str.tostring(lower{i}), style=label.style_label_left, color=buy_color, textcolor=color.white, size=size.small)\n'
        else:
            pine += f"        line.new(bar_index, level{i}, bar_index + line_length, level{i}, extend=line_extend, color=buy_color, style=line_style, width=line_width)\n"
            pine += f"        if show_labels\n"
            pine += f'            label.new(bar_index, level{i}, "{ticker} ◆ " + str.tostring(level{i}), style=label.style_label_left, color=buy_color, textcolor=color.white, size=size.small)\n'
        pine += "\n"

    # Empty slot drawing (zone format: upper+lower, both must be > 0)
    for i in range(len(stocks) + 1, MAX_SLOTS + 1):
        pine += f"    // Stock {i} - [empty]\n"
        pine += f"    if show_stock{i} and ticker{i} != \"\" and upper{i} > 0 and str.contains(syminfo.tickerid, ticker{i})\n"
        pine += f"        l_u{i} = line.new(bar_index, upper{i}, bar_index + line_length, upper{i}, extend=line_extend, color=buy_color, style=line_style, width=line_width)\n"
        pine += f"        if lower{i} > 0 and lower{i} != upper{i}\n"
        pine += f"            l_l{i} = line.new(bar_index, lower{i}, bar_index + line_length, lower{i}, extend=line_extend, color=buy_color, style=line_style, width=line_width)\n"
        pine += f"            linefill.new(l_u{i}, l_l{i}, color=color.new(buy_color, zone_transparency))\n"
        pine += f"        if show_labels\n"
        pine += f'            label.new(bar_index, upper{i}, ticker{i} + " ▲ " + str.tostring(upper{i}), style=label.style_label_left, color=buy_color, textcolor=color.white, size=size.small)\n'
        pine += f'            if lower{i} > 0 and lower{i} != upper{i}\n'
        pine += f'                label.new(bar_index, lower{i}, ticker{i} + " ▼ " + str.tostring(lower{i}), style=label.style_label_left, color=buy_color, textcolor=color.white, size=size.small)\n'
        pine += "\n"

    # Alert conditions
    pine += """// ============================================================================
// ALERT CONDITIONS
// ============================================================================
"""

    for i, (ticker, buy_type, val1, val2, notes) in enumerate(stocks, 1):
        notes_escaped = notes.replace('"', '\\"') if notes else ""
        note_suffix = f"] - {notes_escaped}" if notes_escaped else "]"
        pine += f"// Stock {i} - {ticker} [{buy_type}]\n"
        if buy_type == 'zone':
            entered_msg = (
                f'\'{{\"content\":\"🟢 BUY ZONE: {ticker} entered buy zone $\''
                f" + str.tostring(upper{i}) + '-$' + str.tostring(lower{i})"
                f" + ' [Timeframe: ' + tf + '{note_suffix}\"}}'"
            )
            failed_msg = (
                f'\'{{\"content\":\"🔴 ZONE FAILED: {ticker} broke below $\''
                f" + str.tostring(lower{i})"
                f" + ' [Timeframe: ' + tf + '{note_suffix}\"}}'"
            )
            pine += f"if enable_all and enable_stock{i}\n"
            pine += f"    _entered{i} = ta.crossunder(stock{i}_close, upper{i}) and not ta.crossunder(stock{i}_close, lower{i})\n"
            pine += f"    _failed{i} = ta.crossunder(stock{i}_close, lower{i})\n"
            pine += f"    if _entered{i}\n"
            pine += f"        alert({entered_msg}, alert.freq_once_per_bar_close)\n"
            pine += f"    if _failed{i}\n"
            pine += f"        alert({failed_msg}, alert.freq_once_per_bar_close)\n"
        else:
            reached_msg = (
                f'\'{{\"content\":\"🟢 BUY LEVEL: {ticker} reached $\''
                f" + str.tostring(level{i})"
                f" + ' [Timeframe: ' + tf + '{note_suffix}\"}}'"
            )
            pine += f"if enable_all and enable_stock{i} and ta.crossover(stock{i}_close, level{i})\n"
            pine += f"    alert({reached_msg}, alert.freq_once_per_bar_close)\n"
        pine += "\n"

    # Empty slot alerts (zone format: upper/lower)
    for i in range(len(stocks) + 1, MAX_SLOTS + 1):
        entered_msg = (
            f'\'{{\"content\":\"🟢 BUY ZONE: \' + ticker{i} + \' entered buy zone $\''
            f" + str.tostring(upper{i}) + '-$' + str.tostring(lower{i})"
            f" + ' [Timeframe: ' + tf + ']\"}}'"
        )
        failed_msg = (
            f'\'{{\"content\":\"🔴 ZONE FAILED: \' + ticker{i} + \' broke below $\''
            f" + str.tostring(lower{i})"
            f" + ' [Timeframe: ' + tf + ']\"}}'"
        )
        pine += f"// Stock {i} - [empty]\n"
        pine += f"if enable_all and enable_stock{i} and ticker{i} != \"\"\n"
        pine += f"    _entered{i} = ta.crossunder(stock{i}_close, upper{i}) and not ta.crossunder(stock{i}_close, lower{i})\n"
        pine += f"    _failed{i} = lower{i} > 0 and lower{i} != upper{i} and ta.crossunder(stock{i}_close, lower{i})\n"
        pine += f"    if _entered{i}\n"
        pine += f"        alert({entered_msg}, alert.freq_once_per_bar_close)\n"
        pine += f"    if _failed{i}\n"
        pine += f"        alert({failed_msg}, alert.freq_once_per_bar_close)\n"
        pine += "\n"

    with open(output_path, 'w') as f:
        f.write(pine)

    print(f"✓ Generated Pine Script with {len(stocks)} stocks")
    print(f"  Indicator name: {indicator_name}")


def read_watchlists_file(filepath="watchlists.txt"):
    """Read list of CSV files from watchlists.txt"""
    if not os.path.exists(filepath):
        return []
    watchlists = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                watchlists.append(line)
    return watchlists


def process_single_watchlist(csv_file):
    """Process a single watchlist CSV file."""
    watchlist_suffix = extract_watchlist_suffix(csv_file)
    pine_file = f"{watchlist_suffix}_alerts.pine"

    print("=" * 70)
    print(f"Generating Pine Script from {csv_file}")
    print("=" * 70)
    print(f"Watchlist suffix: {watchlist_suffix}")
    print(f"Output file:      {pine_file}")
    print()

    print(f"Reading {csv_file}...")
    stocks = read_csv(csv_file)
    print(f"Found {len(stocks)} stocks:")
    for ticker, buy_type, val1, val2, notes in stocks[:5]:
        if buy_type == 'zone':
            print(f"  {ticker:10s} [zone]  ${val1} - ${val2}")
        else:
            print(f"  {ticker:10s} [level] ${val1}")
    if len(stocks) > 5:
        print(f"  ... and {len(stocks) - 5} more")

    print(f"\nGenerating {pine_file}...")
    generate_pine_script(stocks, pine_file, watchlist_suffix)
    print(f"✓ Done! File saved as: {pine_file}")
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return

    if len(sys.argv) < 2:
        watchlists_file = "watchlists.txt"
        watchlists = read_watchlists_file(watchlists_file)
        if not watchlists:
            print("Error: No CSV file specified and watchlists.txt not found or empty")
            print("\nUsage:")
            print("  python3 generate_from_csv.py                       # Process all in watchlists.txt")
            print("  python3 generate_from_csv.py buyList_tzar.csv      # Process specific file")
            sys.exit(1)

        print("=" * 70)
        print(f"Reading watchlists from {watchlists_file}")
        print("=" * 70)
        for wl in watchlists:
            print(f"  - {wl}")
        print()
        for csv_file in watchlists:
            process_single_watchlist(csv_file)
        print("=" * 70)
        print(f"ALL WATCHLISTS PROCESSED — {len(watchlists)} Pine Script file(s) generated")
        print("=" * 70)
        return

    csv_file = sys.argv[1]
    process_single_watchlist(csv_file)

    print("=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    watchlist_suffix = extract_watchlist_suffix(csv_file)
    pine_file = f"{watchlist_suffix}_alerts.pine"
    print(f"1. Review the generated file: {pine_file}")
    print(f"2. Copy the contents to TradingView Pine Script editor")
    print(f"3. The indicator will be named: {watchlist_suffix}_alerts")
    print(f"4. To update: Edit {csv_file} and re-run this script")


if __name__ == "__main__":
    main()
