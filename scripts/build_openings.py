"""Builds data/openings.json (position -> ECO code and opening name) from the lichess `chess-openings` dataset (CC0).

    python scripts/build_openings.py            # downloads the five .tsv files from GitHub
    python scripts/build_openings.py DIR        # or reads a..e.tsv from a local folder

The app never needs the network for openings: it ships the generated JSON."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

import chess

BASE = "https://raw.githubusercontent.com/lichess-org/chess-openings/master/{}.tsv"
OUT = Path(__file__).resolve().parent.parent / "data" / "openings.json"


def _rows(src: str | None):
    for letter in "abcde":
        if src:
            text = (Path(src) / f"{letter}.tsv").read_text(encoding="utf-8")
        else:
            with urllib.request.urlopen(BASE.format(letter), timeout=60) as r:
                text = r.read().decode("utf-8")
        for line in text.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 3 and parts[0]:
                yield parts[0], parts[1], parts[2]


def main():
    book: dict[str, list] = {}
    for eco, name, pgn in _rows(sys.argv[1] if len(sys.argv) > 1 else None):
        board = chess.Board()
        try:
            for tok in re.sub(r"\d+\.(\.\.)?", " ", pgn).split():
                board.push_san(tok)
        except ValueError:
            continue
        key = board.epd()
        if key not in book or len(name) < len(book[key][1]):
            book[key] = [eco, name]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(book, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(book)} positions -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
