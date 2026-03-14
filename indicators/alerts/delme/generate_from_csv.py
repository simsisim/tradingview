#!/usr/bin/env python3
"""
Generate TradingView Pine Script alerts from CSV watchlist.

Usage:
    python3 generate_from_csv.py                        # Process all watchlists in watchlists.txt
    python3 generate_from_csv.py watchlist_TTG.csv      # Generate Pine script from specific CSV
    python3 generate_from_csv.py watchlist_TECH.csv     # Generate Pine script from TECH watchlist

The script will:
- Read from: watchlist_TTG.csv
- Generate: TTG_alerts.pine
- Indicator name: "TTG_alerts"

If no arguments provided, reads watchlists from watchlists.txt
"""

import csv
import sys
import os
import re

def extract_watchlist_suffix(csv_filename):
    """
    Extract the watchlist suffix from the CSV filename.
    Examples:
        watchlist_TTG.csv -> TTG
        watchlist_TECH.csv -> TECH
        watchlist.csv -> DEFAULT
        TTG_watchlist.csv -> TTG
    """
    basename = os.path.basename(csv_filename)
    name_without_ext = os.path.splitext(basename)[0]

    # Try to extract suffix after "watchlist_"
    if 'watchlist_' in name_without_ext.lower():
        parts = name_without_ext.split('_')
        for i, part in enumerate(parts):
            if part.lower() == 'watchlist' and i + 1 < len(parts):
                return parts[i + 1].upper()

    # Try to extract prefix before "_watchlist"
    if '_watchlist' in name_without_ext.lower():
        parts = name_without_ext.split('_')
        for i, part in enumerate(parts):
            if part.lower() == 'watchlist' and i > 0:
                return parts[i - 1].upper()

    # Try to find any uppercase pattern
    match = re.search(r'([A-Z]+)', name_without_ext)
    if match:
        return match.group(1)

    # Default
    return "DEFAULT"

def read_csv(csv_path):
    """Read stock data from CSV file."""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found!")
        sys.exit(1)

    stocks = []
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ticker = row['Ticker'].strip()
            try:
                trigger = float(row['Trigger']) if row['Trigger'] else 0.0
                stop = float(row['Stop']) if row['Stop'] else 0.0
            except ValueError:
                print(f"Warning: Skipping {ticker} - invalid price values")
                continue
            notes = row.get('Notes', '').strip()
            stocks.append((ticker, trigger, stop, notes))

    return stocks

def generate_pine_script(stocks, output_path, watchlist_suffix):
    """Generate Pine Script from stock data with custom suffix."""

    # Generate indicator name with suffix
    indicator_name = f"{watchlist_suffix}_alerts"
    short_title = f"{watchlist_suffix} Alerts"

    # Header with custom indicator name
    pine_script = f"""//@version=5
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

    # Generate stock inputs
    for i, (ticker, trigger, stop, notes) in enumerate(stocks, 1):
        pine_script += f"""// Stock {i} - {ticker}
enable_stock{i} = input.bool(true, "Alert", inline="{i}", group=g_stocks, display=display.data_window)
ticker{i} = input.symbol("{ticker}", "{ticker}", inline="{i}", group=g_stocks, display=display.data_window)
trigger{i} = input.float({trigger}, "Trigger", inline="{i}", group=g_stocks, display=display.data_window)
stop{i} = input.float({stop}, "Stop", inline="{i}", group=g_stocks, display=display.data_window)
show_stock{i} = input.bool(true, "Show", inline="{i}", group=g_stocks, display=display.data_window)

"""

    # Visual settings section
    pine_script += """// ============================================================================
// VISUAL SETTINGS
// ============================================================================
string g_visual = "Visual Settings"
line_width = input.int(2, "Line Width", minval=1, maxval=4, group=g_visual, display=display.data_window)
line_style_input = input.string("Solid", "Line Style", options=["Solid", "Dashed", "Dotted"], group=g_visual, display=display.data_window)
extend_lines = input.bool(false, "Extend Lines to Right", group=g_visual, display=display.data_window)
line_length = input.int(50, "Line Length (bars)", minval=10, maxval=500, group=g_visual, tooltip="Number of bars to extend lines when 'Extend to Right' is disabled", display=display.data_window)
show_labels = input.bool(true, "Show Labels", group=g_visual, display=display.data_window)
trigger_color = input.color(color.new(color.green, 0), "Trigger Color", group=g_visual, display=display.data_window)
stop_color = input.color(color.new(color.red, 0), "Stop Loss Color", group=g_visual, display=display.data_window)

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

    # Generate request.security calls for each stock
    for i in range(1, len(stocks) + 1):
        pine_script += f"stock{i}_close = enable_all and enable_stock{i} and ticker{i} != \"\" ? request.security(ticker{i}, tf, close, lookahead=barmerge.lookahead_off) : na\n"

    # Visual lines section
    pine_script += """
// ============================================================================
// DRAW HORIZONTAL LINES AND LABELS
// ============================================================================
if show_all_visual and barstate.islast
"""

    # Generate visual lines for each stock
    for i, (ticker, trigger, stop, notes) in enumerate(stocks, 1):
        pine_script += f"""    // Stock {i} - {ticker}
    if show_stock{i} and trigger{i} > 0 and str.contains(syminfo.tickerid, ticker{i})
        line.new(bar_index, trigger{i}, bar_index + line_length, trigger{i}, extend=line_extend, color=trigger_color, style=line_style, width=line_width)
        if show_labels
            label.new(bar_index, trigger{i}, "{ticker} ▲ " + str.tostring(trigger{i}), style=label.style_label_left, color=trigger_color, textcolor=color.white, size=size.small)
    if show_stock{i} and stop{i} > 0 and str.contains(syminfo.tickerid, ticker{i})
        line.new(bar_index, stop{i}, bar_index + line_length, stop{i}, extend=line_extend, color=stop_color, style=line_style, width=line_width)
        if show_labels
            label.new(bar_index, stop{i}, "{ticker} ▼ " + str.tostring(stop{i}), style=label.style_label_left, color=stop_color, textcolor=color.white, size=size.small)

"""

    # Alert conditions section
    pine_script += """// ============================================================================
// ALERT CONDITIONS - UNIFIED ALERT SYSTEM
// ============================================================================
"""

    # Generate alert conditions for each stock
    for i, (ticker, trigger, stop, notes) in enumerate(stocks, 1):
        # Escape quotes for JSON (notes are inside JSON double quotes)
        notes_escaped = notes.replace('"', '\\"') if notes else ""

        # Build alert messages in Discord webhook JSON format
        if notes_escaped:
            trigger_alert = f"'{{\"content\":\"🟢 TRIGGER: {ticker} crossed above trigger price $' + str.tostring(trigger{i}) + ' [Timeframe: ' + tf + '] - {notes_escaped}\"}}'"
            stop_alert = f"'{{\"content\":\"🔴 STOP LOSS: {ticker} crossed below stop loss $' + str.tostring(stop{i}) + ' [Timeframe: ' + tf + '] - {notes_escaped}\"}}'"
        else:
            trigger_alert = f"'{{\"content\":\"🟢 TRIGGER: {ticker} crossed above trigger price $' + str.tostring(trigger{i}) + ' [Timeframe: ' + tf + ']\"}}'"
            stop_alert = f"'{{\"content\":\"🔴 STOP LOSS: {ticker} crossed below stop loss $' + str.tostring(stop{i}) + ' [Timeframe: ' + tf + ']\"}}'"

        pine_script += f"""// Stock {i} - {ticker}
if enable_all and enable_stock{i} and ta.crossover(stock{i}_close, trigger{i})
    alert({trigger_alert}, alert.freq_once_per_bar_close)
if enable_all and enable_stock{i} and ta.crossunder(stock{i}_close, stop{i})
    alert({stop_alert}, alert.freq_once_per_bar_close)

"""

    # Write to file
    with open(output_path, 'w') as f:
        f.write(pine_script)

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
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                watchlists.append(line)
    return watchlists

def process_single_watchlist(csv_file):
    """Process a single watchlist CSV file."""
    # Extract watchlist suffix
    watchlist_suffix = extract_watchlist_suffix(csv_file)

    # Determine output filename
    pine_file = f"{watchlist_suffix}_alerts.pine"

    print("=" * 70)
    print(f"Generating Pine Script from {csv_file}")
    print("=" * 70)
    print(f"Watchlist suffix: {watchlist_suffix}")
    print(f"Output file: {pine_file}")
    print()

    # Read CSV
    print(f"Reading watchlist from {csv_file}...")
    stocks = read_csv(csv_file)
    print(f"Found {len(stocks)} stocks in CSV:")
    for ticker, trigger, stop, notes in stocks[:5]:  # Show first 5
        print(f"  {ticker:10s} - Trigger: ${trigger:7.2f} | Stop: ${stop:7.2f}")
    if len(stocks) > 5:
        print(f"  ... and {len(stocks) - 5} more")

    # Generate Pine Script
    print(f"\nGenerating {pine_file}...")
    generate_pine_script(stocks, pine_file, watchlist_suffix)
    print(f"✓ Done! File saved as: {pine_file}")
    print()

def main():
    """Main function."""

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return

    # Parse command line arguments
    if len(sys.argv) < 2:
        # No arguments - try to read from watchlists.txt
        watchlists_file = "watchlists.txt"
        watchlists = read_watchlists_file(watchlists_file)

        if not watchlists:
            print("Error: No CSV file specified and watchlists.txt not found or empty")
            print("\nUsage:")
            print("  python3 generate_from_csv.py                     # Process all in watchlists.txt")
            print("  python3 generate_from_csv.py watchlist_TTG.csv   # Process specific file")
            print("\nRun with --help for more information")
            sys.exit(1)

        # Process all watchlists from file
        print("=" * 70)
        print(f"Reading watchlists from {watchlists_file}")
        print("=" * 70)
        print(f"Found {len(watchlists)} watchlist(s):")
        for wl in watchlists:
            print(f"  - {wl}")
        print()

        for csv_file in watchlists:
            process_single_watchlist(csv_file)

        print("=" * 70)
        print("ALL WATCHLISTS PROCESSED")
        print("=" * 70)
        print(f"Generated {len(watchlists)} Pine Script file(s)")
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
