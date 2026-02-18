#!/usr/bin/env python3
import csv
import os
import sys
from datetime import datetime, timezone

HEADER = ["timestamp", "product_name", "product_ref", "website_slug", "meta_title", "meta_description", "keywords", "status", "notes"]


def main() -> None:
    # args: product_name, product_ref, website_slug, meta_title, meta_description, keywords, status, notes
    if len(sys.argv) < 9:
        print(
            "Usage: append_report_csv.py <product_name> <product_ref> <website_slug> <meta_title> <meta_description> <keywords> <status> <notes>",
            file=sys.stderr,
        )
        sys.exit(2)

    product_name, product_ref, website_slug, meta_title, meta_description, keywords, status, notes = sys.argv[1:9]
    path = os.path.join(os.getcwd(), "seo_keywords_report.csv")
    exists = os.path.exists(path)

    ts = datetime.now(timezone.utc).isoformat()

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(HEADER)
        w.writerow([ts, product_name, product_ref, website_slug, meta_title, meta_description, keywords, status, notes])

    print(f"OK: appended report line to {path}")


if __name__ == "__main__":
    main()

