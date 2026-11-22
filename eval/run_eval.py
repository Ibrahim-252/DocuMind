"""Measure retrieval quality: is the expected file and page among the returned sources?

Reports top-1 (the right page is the first result), top-3 and top-6.
Top-k counts returned chunks, not distinct pages, so top-6 is lenient on short documents.

Usage:
  python eval/run_eval.py --questions eval/questions.csv [--api http://localhost:8000]

questions.csv columns: question,expected_file,expected_page
"""
import argparse
import csv
import sys

import requests

KS = (1, 3, 6)


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuMind retrieval evaluation")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--questions", default="eval/questions.csv")
    args = parser.parse_args()

    with open(args.questions, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        print("No questions found.")
        return 1

    hits = dict.fromkeys(KS, 0)
    for row in rows:
        reply = requests.post(f"{args.api}/chat", json={"question": row["question"]}, timeout=120)
        reply.raise_for_status()
        ranked = [(s["filename"], s["page"]) for s in reply.json()["sources"]]
        expected = (row["expected_file"], int(row["expected_page"]))

        best = None
        for k in KS:
            if expected in ranked[:k]:
                hits[k] += 1
                best = best or k
        label = f"top-{best}" if best else "MISS"
        print(f"[{label:<5}] {row['question']}")

    total = len(rows)
    print()
    for k in KS:
        print(f"Top-{k}: {hits[k]} of {total} questions ({hits[k] / total:.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())