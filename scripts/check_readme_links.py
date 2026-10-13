#!/usr/bin/env python3
"""Prüft, dass beide Profil-READMEs dieselben GitHub-Links führen."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt


MARKDOWN = MarkdownIt("gfm-like")
COMMENTS_ONLY = re.compile(r"(?:\s*<!--(?:(?!-->)[\s\S])*-->)*\s*\Z")
REPO_ROOT = Path(__file__).resolve().parent.parent


def github_links(path: Path) -> list[tuple[int, str]]:
    """Liefert Linkziele in Dokumentreihenfolge mit der Startzeile ihres Textblocks."""
    links: list[tuple[int, str]] = []
    for block in MARKDOWN.parse(path.read_text(encoding="utf-8")):
        line_number = block.map[0] + 1 if block.map else 1
        for token in [block, *(block.children or [])]:
            if token.type in {"html_inline", "html_block"}:
                # HTML kann Links oder Sichtbarkeit verändern. Ohne HTML-Auswertung
                # dürfen nur Kommentare eine erfolgreiche Paritätsprüfung passieren.
                if not COMMENTS_ONLY.fullmatch(token.content):
                    raise ValueError(
                        f"{path}: ab Zeile {line_number}: HTML außer Kommentaren "
                        "wird nicht unterstützt; bitte Markdown verwenden."
                    )
            if token.type == "link_open":
                url = token.attrGet("href")
                if url and url.startswith("https://github.com/"):
                    links.append((line_number, url))
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

    try:
        english_links = github_links(english_path)
        german_links = github_links(german_path)
    except (OSError, ValueError) as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        return 1
    if not english_links:
        print(f"FEHLER: {english_path} enthält keine GitHub-Links.", file=sys.stderr)
        return 1
    if [url for _, url in english_links] != [url for _, url in german_links]:
        print("FEHLER: Die GitHub-Links der Sprachfassungen weichen ab.", file=sys.stderr)
        for path, links in ((english_path, english_links), (german_path, german_links)):
            print(f"{path}:", file=sys.stderr)
            for line_number, url in links:
                print(f"  ab Zeile {line_number}: {url}", file=sys.stderr)
        return 1

    print(f"OK: {len(english_links)} GitHub-Links stimmen in ihrer Reihenfolge überein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
