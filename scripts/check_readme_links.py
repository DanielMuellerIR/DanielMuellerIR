#!/usr/bin/env python3
"""Prüft, dass beide Profil-READMEs dieselben GitHub-Links führen."""

from __future__ import annotations

import re
import sys
from pathlib import Path


GITHUB_LINK = re.compile(r"]\((https://github\.com/[^)\s]+)\)")
REPO_ROOT = Path(__file__).resolve().parent.parent


def github_links(path: Path) -> list[tuple[int, str]]:
    """Liefert GitHub-Links mit ihrer Zeilennummer in Dokumentreihenfolge."""
    links: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        links.extend((line_number, url) for url in GITHUB_LINK.findall(line))
    return links


def main(arguments: list[str]) -> int:
    if arguments:
        if len(arguments) != 2:
            print("Aufruf: check_readme_links.py [README.md README.de.md]", file=sys.stderr)
            return 2
        english_path, german_path = map(Path, arguments)
    else:
        english_path = REPO_ROOT / "README.md"
        german_path = REPO_ROOT / "README.de.md"

    english_links = github_links(english_path)
    german_links = github_links(german_path)
    if not english_links:
        print(f"FEHLER: {english_path} enthält keine GitHub-Links.", file=sys.stderr)
        return 1
    if english_links != german_links:
        print("FEHLER: Die GitHub-Links der Sprachfassungen weichen ab.", file=sys.stderr)
        print(f"{english_path}: {english_links}", file=sys.stderr)
        print(f"{german_path}: {german_links}", file=sys.stderr)
        return 1

    print(f"OK: {len(english_links)} GitHub-Links stimmen samt Zeilennummern überein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
