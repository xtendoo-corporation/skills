#!/usr/bin/env python3
import re
import sys


def normalize(raw: str) -> str:
    # Split by commas, trim, collapse spaces
    parts = [re.sub(r"\s+", " ", p.strip()) for p in raw.split(",")]
    parts = [p for p in parts if p]

    # Lowercase to keep consistent SEO format
    parts = [p.lower() for p in parts]

    # De-duplicate preserving order
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)

    # Hard limit to 15
    out = out[:15]
    return ", ".join(out)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: normalize_keywords.py "kw1, kw2, kw3"', file=sys.stderr)
        sys.exit(2)
    raw = sys.argv[1]
    print(normalize(raw))


if __name__ == "__main__":
    main()
