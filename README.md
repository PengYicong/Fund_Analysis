# Funds Analysis

A lightweight Python project for Eastmoney fund-page data collection and stock-holdings parsing.

## Current Status

- Implemented HTML downloader for a given fund code.
- Implemented HTML parser for stock holdings table.
- Implemented integrated fetch+parse script that outputs:
  - `{"fund_number": {"stock_name": "percentage"}}`
- Supports batch input from `txt/json/csv` files.

## Project Structure

- `src/fetch_fund_html.py`: download fund detail HTML from Eastmoney.
- `src/parse_fund_stocks.py`: parse local HTML and print formatted stock table.
- `src/fund_stock_dict.py`: integrated fetch+parse and dictionary output (single or batch).
- `assets/`: sample HTML and sample batch-input files.

## Requirements

- Python 3.9+ (standard library only).

## Usage

### 1) Download fund HTML

```bash
python3 src/fetch_fund_html.py 017731 -o assets/017731.html
python3 src/fetch_fund_html.py 017731 -o assets/017731.html --timeout 60
```

### 2) Parse stock table from local HTML

```bash
python3 src/parse_fund_stocks.py assets/017731.html
python3 src/parse_fund_stocks.py assets/sample_017731_downloaded.html
```

### 3) Integrated dictionary output (single fund)

```bash
python3 src/fund_stock_dict.py 017731
```

Example output:

```json
{
  "017731": {
    "博通": "5.37%",
    "美光科技": "4.85%"
  }
}
```

### 4) Integrated dictionary output (multiple funds from file)

```bash
python3 src/fund_stock_dict.py --fund-file assets/test_funds.json
python3 src/fund_stock_dict.py --fund-file assets/test_funds.txt
python3 src/fund_stock_dict.py --fund-file assets/test_funds.csv
```

## Batch Input File Formats

- `txt`: any text containing 6-digit fund numbers.
- `json`:
  - list style: `["519674", "017731", "166301"]`
  - object style: `{"fund_numbers": ["519674", "017731"]}` or `{"funds": [...]}`
- `csv`: any cells containing 6-digit fund numbers.

## Included Test Files

- `assets/test_funds.json`
- `assets/test_funds.txt`
- `assets/test_funds.csv`

Current test fund numbers:

- `519674`
- `017731`
- `166301`

## Notes

- Eastmoney page structure can change over time; parser logic may need updates.
- If parsing fails, check and adjust regex/selectors in `src/parse_fund_stocks.py`.
