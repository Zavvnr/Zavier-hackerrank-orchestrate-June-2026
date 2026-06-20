"""Robust CSV read/write helpers for the claim pipeline."""

import csv
import pathlib
from typing import Iterator


def read_claims(csv_path: str | pathlib.Path) -> list[dict]:
    """Read all rows from a claims CSV file."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(dict(row))
    return rows


def read_lookup(csv_path: str | pathlib.Path, key_col: str) -> dict[str, dict]:
    """Read a CSV into a dict keyed by key_col."""
    lookup = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            lookup[row[key_col]] = dict(row)
    return lookup


def read_list(csv_path: str | pathlib.Path) -> list[dict]:
    """Read a CSV as a plain list of dicts."""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_output(rows: list[dict], out_path: str | pathlib.Path, columns: list[str]) -> None:
    """Write prediction rows to output CSV with QUOTE_ALL to guard embedded newlines."""
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=columns,
            quoting=csv.QUOTE_ALL,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
