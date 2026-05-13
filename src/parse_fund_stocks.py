#!/usr/bin/env python3
"""Parse stock holdings from a downloaded Eastmoney fund HTML page.

Example:
    python parse_fund_stocks.py sample_017731_downloaded.html
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys
import unicodedata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse stock holdings from Eastmoney fund HTML and print as a table."
    )
    parser.add_argument("html_file", type=pathlib.Path, help="Path to downloaded HTML file")
    return parser.parse_args()


def display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text: str, width: int, align: str = "left") -> str:
    current = display_width(text)
    fill = max(0, width - current)
    if align == "right":
        return " " * fill + text
    return text + " " * fill


def clean_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_stock_rows(content: str) -> list[tuple[str, str, str]]:
    section_match = re.search(
        r"<li[^>]*id=['\"]position_shares['\"][^>]*>(.*?)</li>",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not section_match:
        raise ValueError("Could not find stock holdings section (position_shares).")

    section_html = section_match.group(1)
    table_match = re.search(
        r"<table[^>]*>(.*?)</table>", section_html, flags=re.IGNORECASE | re.DOTALL
    )
    if not table_match:
        raise ValueError("Could not find stock holdings table inside position_shares.")

    table_html = table_match.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.IGNORECASE | re.DOTALL)

    result: list[tuple[str, str, str]] = []
    for row_html in rows:
        cols = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.IGNORECASE | re.DOTALL)
        if len(cols) < 3:
            continue

        stock_name = clean_text(cols[0])
        ratio = clean_text(cols[1])
        change = clean_text(cols[2])

        if stock_name in {"股票名称", ""}:
            continue

        result.append((stock_name, ratio, change))

    if not result:
        raise ValueError("No stock rows parsed from stock holdings table.")

    return result


def print_table(rows: list[tuple[str, str, str]]) -> None:
    headers = ("股票名称", "持占比", "涨跌幅")

    name_w = max(display_width(headers[0]), *(display_width(r[0]) for r in rows))
    ratio_w = max(display_width(headers[1]), *(display_width(r[1]) for r in rows))
    change_w = max(display_width(headers[2]), *(display_width(r[2]) for r in rows))

    sep = f"+-{'-' * name_w}-+-{'-' * ratio_w}-+-{'-' * change_w}-+"
    print(sep)
    print(
        "| "
        + pad(headers[0], name_w, "left")
        + " | "
        + pad(headers[1], ratio_w, "right")
        + " | "
        + pad(headers[2], change_w, "right")
        + " |"
    )
    print(sep)

    for name, ratio, change in rows:
        print(
            "| "
            + pad(name, name_w, "left")
            + " | "
            + pad(ratio, ratio_w, "right")
            + " | "
            + pad(change, change_w, "right")
            + " |"
        )

    print(sep)


def main() -> int:
    args = parse_args()

    if not args.html_file.exists():
        print(f"Error: file not found: {args.html_file}", file=sys.stderr)
        return 2

    content = args.html_file.read_text(encoding="utf-8", errors="ignore")

    try:
        rows = extract_stock_rows(content)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
