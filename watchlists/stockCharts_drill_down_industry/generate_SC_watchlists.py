"""
generate_SC_watchlists.py
Generates TradingView watchlist .txt files from StockCharts sector drill-down HTML saves.

Naming convention:
  - Sector file : SC_<first3>_<first3>...txt  e.g. "Communication Services" → SC_com_ser.txt
  - Section hdr : ### <first3>_<first3>...    e.g. "mobile_telecommunications" → ### mob_tel

Output: ./output/SC_*.txt  (one file per sector, sections = industries, plain tickers)
"""

from bs4 import BeautifulSoup
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fullwidth colon used in timestamps inside filenames
FULLWIDTH_COLON = "\uff1a"


def abbrev(name: str, n: int = 3) -> str:
    """Return first-n-letters abbreviation of each word, joined by underscores."""
    words = re.split(r"[\s_]+", name.strip())
    return "_".join(w[:n].lower() for w in words if w)


def resolve_abbrevs(industry_suffixes: list) -> dict:
    """
    Return {suffix: abbreviation} with no collisions.
    Starts at n=3 and increases n for all colliding entries until unique.
    """
    result = {s: abbrev(s) for s in industry_suffixes}
    changed = True
    while changed:
        changed = False
        # Group by current abbreviation
        by_abbrev = {}
        for suffix, ab in result.items():
            by_abbrev.setdefault(ab, []).append(suffix)
        for ab, suffixes in by_abbrev.items():
            if len(suffixes) > 1:
                # Find the current n being used (length of first part before first _)
                cur_n = len(ab.split("_")[0])
                new_n = cur_n + 1
                for s in suffixes:
                    result[s] = abbrev(s, new_n)
                changed = True
    return result


def sector_filename(sector_name: str) -> str:
    return f"SC_{abbrev(sector_name)}.txt"


def industry_section(industry_suffix: str) -> str:
    return f"### {abbrev(industry_suffix)}"


def extract_timestamp(fname: str):
    """Extract sortable timestamp from filename for ordering industries."""
    # Pattern: (MM_DD_YYYY H：MM：SS PM)
    m = re.search(
        r"\((\d+)_(\d+)_(\d+)\s+(\d+)" + FULLWIDTH_COLON + r"(\d+)" + FULLWIDTH_COLON + r"(\d+)\s+(AM|PM)\)",
        fname,
    )
    if not m:
        return (0, 0, 0, 0, 0, 0)
    month, day, year, hour, minute, second, ampm = (
        int(m.group(1)), int(m.group(2)), int(m.group(3)),
        int(m.group(4)), int(m.group(5)), int(m.group(6)),
        m.group(7),
    )
    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0
    return (year, month, day, hour, minute, second)


def extract_tickers(html_path: str) -> list:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    spans = soup.find_all("span", {"class": "symlink"})
    return [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]


def get_industry_suffix(fname: str) -> str:
    """Extract the industry label from filename suffix after PM)_..."""
    m = re.search(r"PM\)_(.+?)\.html$", fname)
    return m.group(1) if m else re.sub(r"\.html$", "", fname)


def process_sector(sector_name: str, sector_path: str):
    html_files = [f for f in os.listdir(sector_path) if f.endswith(".html")]
    # Sort by embedded timestamp
    html_files.sort(key=extract_timestamp)

    industries = [get_industry_suffix(f) for f in html_files]
    abbrev_map = resolve_abbrevs(industries)

    output_file = os.path.join(OUTPUT_DIR, sector_filename(sector_name))
    total = 0

    with open(output_file, "w", encoding="utf-8") as out:
        for fname, industry in zip(html_files, industries):
            section = abbrev_map[industry]
            tickers = extract_tickers(os.path.join(sector_path, fname))
            out.write(f"### {section}\n")
            for ticker in tickers:
                out.write(f"{ticker}\n")
            total += len(tickers)
            print(f"  {industry:40} → ### {section:20}  ({len(tickers)} stocks)")

    print(f"  → {output_file}  [{total} stocks total]\n")
    return total


def main():
    sectors = []
    for name in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, name)
        if os.path.isdir(path) and not name.startswith(".") and name != "output":
            sectors.append((name, path))

    # Communication Services first, then alphabetical
    def sort_key(item):
        name = item[0]
        return (0 if name == "Communication Services" else 1, name)

    sectors.sort(key=sort_key)

    grand_total = 0
    for sector_name, sector_path in sectors:
        print(f"=== {sector_name} → {sector_filename(sector_name)} ===")
        grand_total += process_sector(sector_name, sector_path)

    print(f"{'='*60}")
    print(f"GRAND TOTAL: {grand_total} stocks across {len(sectors)} sectors")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
