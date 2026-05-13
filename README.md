# Funds Analysis

A lightweight Python project for Eastmoney fund-page data collection and stock-holdings parsing.

## Current Status

- Implemented HTML downloader for a given 6-digit fund code.
- Implemented local HTML parser for stock holdings table.
- Parser extracts and prints these fields to console:
  - `股票名称`
  - `持占比` (from page column `持仓占比`)
  - `涨跌幅`
- Verified with fund `017731` sample page (includes row like `博通 | 5.37%`).

## Project Structure

- `src/fetch_fund_html.py`: download fund detail HTML from Eastmoney.
- `src/parse_fund_stocks.py`: parse stock holdings from downloaded HTML and print formatted table.
- `assets/`: sample downloaded HTML files for testing.

## Requirements

- Python 3.9+ (standard library only, no third-party packages).

## Usage

### 1) Download fund HTML

```bash
python3 src/fetch_fund_html.py 017731 -o assets/017731.html
```

Optional timeout:

```bash
python3 src/fetch_fund_html.py 017731 -o assets/017731.html --timeout 60
```

### 2) Parse stock holdings from local HTML

```bash
python3 src/parse_fund_stocks.py assets/017731.html
```

You can also run against included sample files:

```bash
python3 src/parse_fund_stocks.py assets/sample_017731_downloaded.html
```

## Typical Output

```text
+------------+--------+--------+
| 股票名称   | 持占比 | 涨跌幅 |
+------------+--------+--------+
| 博通       |  5.37% |     -- |
| 美光科技   |  4.85% |     -- |
...
+------------+--------+--------+
```

## Notes

- Eastmoney pages are dynamic and may change HTML structure in the future.
- If parser fails with structure-related errors, update selectors/regex in `src/parse_fund_stocks.py`.
