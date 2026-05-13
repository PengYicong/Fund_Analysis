#!/usr/bin/env python3
"""Download Eastmoney fund detail HTML by fund number.

Example:
    python fetch_fund_html.py 017731
    python fetch_fund_html.py 017731 -o 017731.html
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import urllib.error
import urllib.request


DEFAULT_TIMEOUT = 15


def build_url(fund_number: str) -> str:
    return f"https://fund.eastmoney.com/{fund_number}.html?spm=search"


def fetch_html(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "close",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Eastmoney fund detail page HTML by fund number."
    )
    parser.add_argument(
        "fund_number",
        help="Fund code, e.g. 017731",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Output HTML file path (default: <fund_number>.html)",
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
    fund_number = args.fund_number.strip()

    if not fund_number.isdigit() or len(fund_number) != 6:
        print("Error: fund_number must be a 6-digit code, e.g. 017731", file=sys.stderr)
        return 2

    url = build_url(fund_number)
    output_path = args.output or pathlib.Path(f"{fund_number}.html")

    try:
        html_bytes = fetch_html(url, args.timeout)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code} for {url}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error for {url}: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"Timeout while requesting {url}", file=sys.stderr)
        return 1

    output_path.write_bytes(html_bytes)
    print(f"Saved {len(html_bytes)} bytes to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
