#!/usr/bin/env python3
"""Fetch and parse Eastmoney fund stock holdings into a dictionary.

Output format:
    {
      "<fund_number>": {
        "fund_name": "<name>",
        "fund_type": "<type>",
        "holdings": {"<stock_name>": "<percentage>"}
      }
    }

Example:
    python3 src/fund_stock_dict.py 017731
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import pathlib
import re
import sys
from typing import Any, Dict
import urllib.error

try:
    from .fetch_fund_html import DEFAULT_TIMEOUT, build_url, fetch_html
    from .parse_fund_stocks import extract_stock_rows
except ImportError:
    from fetch_fund_html import DEFAULT_TIMEOUT, build_url, fetch_html
    from parse_fund_stocks import extract_stock_rows


PLACEHOLDER_FUND_NAME = "N/A"
PLACEHOLDER_FUND_TYPE = "N/A"


def normalize_fund_number(value: str | int) -> str:
    """Normalize a fund number to a 6-digit string."""
    code = str(value).strip()
    if not code:
        raise ValueError("fund number cannot be empty")
    if not code.isdigit():
        raise ValueError(f"invalid fund number: {value}")
    if len(code) > 6:
        raise ValueError(f"fund number must be 6 digits: {value}")
    return code.zfill(6)


def _build_placeholder_result(code: str) -> Dict[str, Dict[str, Any]]:
    return {
        code: {
            "fund_name": PLACEHOLDER_FUND_NAME,
            "fund_type": PLACEHOLDER_FUND_TYPE,
            "holdings": {},
        }
    }


def _extract_fund_name(content: str, code: str) -> str:
    name_match = re.search(
        r'class=["\']funCur-FundName["\']>\s*([^<]+?)\s*</span>',
        content,
        flags=re.IGNORECASE,
    )
    if name_match:
        return html.unescape(name_match.group(1)).strip()

    title_match = re.search(
        rf"<title>\s*(.*?)\({re.escape(code)}\)基金净值",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if title_match:
        return html.unescape(title_match.group(1)).strip()

    return ""


def _extract_fund_type(content: str) -> str:
    type_match = re.search(
        r"类型：\s*(?:<a[^>]*>)?\s*([^<|]+?)\s*(?:</a>)?(?:\s|&nbsp;)*(?:\||</td>)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not type_match:
        return ""

    return html.unescape(type_match.group(1)).replace("\xa0", " ").strip()


def get_fund_stock_dict(fund_number: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Dict[str, Any]]:
    """Fetch fund page HTML and return fund summary + holdings as a dict.

    Returns:
        {
            "<fund_number>": {
                "fund_name": "<name>",
                "fund_type": "<type>",
                "holdings": {"<stock_name>": "<percentage>"}
            }
        }
    """
    code = normalize_fund_number(fund_number)

    url = build_url(code)
    try:
        html_bytes = fetch_html(url, timeout)
    except urllib.error.HTTPError as exc:
        # Invalid fund pages can respond with HTTP errors. Return placeholder instead.
        if exc.code in (400, 404):
            return _build_placeholder_result(code)
        raise

    content = html_bytes.decode("utf-8", errors="ignore")

    try:
        rows = extract_stock_rows(content)
    except ValueError:
        # Missing holdings section usually means invalid/non-standard fund page.
        return _build_placeholder_result(code)

    stock_map = {stock_name: percentage for stock_name, percentage, _change in rows}
    fund_name = _extract_fund_name(content, code)
    fund_type = _extract_fund_type(content)

    return {
        code: {
            "fund_name": fund_name or PLACEHOLDER_FUND_NAME,
            "fund_type": fund_type or PLACEHOLDER_FUND_TYPE,
            "holdings": stock_map,
        }
    }


def _extract_codes_from_text(content: str) -> list[str]:
    codes = re.findall(r"\d{6}", content)
    return [normalize_fund_number(code) for code in codes]


def _extract_codes_from_json_data(data: object) -> list[str]:
    if isinstance(data, list):
        return [normalize_fund_number(v) for v in data]

    if isinstance(data, dict):
        if "fund_numbers" in data and isinstance(data["fund_numbers"], list):
            return [normalize_fund_number(v) for v in data["fund_numbers"]]
        if "funds" in data and isinstance(data["funds"], list):
            return [normalize_fund_number(v) for v in data["funds"]]
        # Fallback: scan full JSON text for 6-digit sequences.
        return _extract_codes_from_text(json.dumps(data, ensure_ascii=False))

    raise ValueError("JSON file must be a list or object containing fund numbers.")


def load_fund_numbers(file_path: str | pathlib.Path) -> list[str]:
    """Load a list of 6-digit fund numbers from txt/json/csv file."""
    path = pathlib.Path(file_path)
    if not path.exists():
        raise ValueError(f"file not found: {path}")

    suffix = path.suffix.lower()
    unique_codes: list[str] = []
    seen: set[str] = set()

    if suffix == ".txt":
        content = path.read_text(encoding="utf-8", errors="ignore")
        codes = _extract_codes_from_text(content)
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        codes = _extract_codes_from_json_data(data)
    elif suffix == ".csv":
        codes = []
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    codes.extend(_extract_codes_from_text(cell))
    else:
        raise ValueError("unsupported file type. use .txt, .json, or .csv")

    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)

    if not unique_codes:
        raise ValueError(f"no valid 6-digit fund numbers found in: {path}")

    return unique_codes


def get_multiple_fund_stock_dict(
    file_path: str | pathlib.Path, timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Dict[str, Any]]:
    """Fetch and parse stock holdings for multiple fund numbers from a file."""
    fund_numbers = load_fund_numbers(file_path)
    result: Dict[str, Dict[str, str]] = {}

    for fund_number in fund_numbers:
        result.update(get_fund_stock_dict(fund_number, timeout=timeout))

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Eastmoney fund stock holdings as dictionary."
    )
    parser.add_argument(
        "fund_number",
        nargs="?",
        help="Single fund code, e.g. 017731",
    )
    parser.add_argument(
        "--fund-file",
        type=pathlib.Path,
        help="Path to txt/json/csv file containing fund numbers",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.fund_number and not args.fund_file:
        print("Error: provide fund_number or --fund-file", file=sys.stderr)
        return 2
    if args.fund_number and args.fund_file:
        print("Error: use either fund_number or --fund-file, not both", file=sys.stderr)
        return 2

    try:
        if args.fund_file:
            result = get_multiple_fund_stock_dict(args.fund_file, timeout=args.timeout)
        else:
            result = get_fund_stock_dict(args.fund_number, timeout=args.timeout)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Request timed out", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
