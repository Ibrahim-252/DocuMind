"""Measure retrieval quality: is the expected file and page among the returned sources?

Usage:
  python eval/run_eval.py --questions eval/questions.csv [--api http://localhost:8000]

questions.csv columns: question,expected_file,expected_page
"""
import argparse
import csv
import sys

import requests


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

    hits = 0
    for row in rows:
        reply = requests.post(f"{args.api}/chat", json={"question": row["question"]}, timeout=120)
        reply.raise_for_status()
        sources = reply.json()["sources"]
        found = any(s["filename"] == row["expected_file"] and s["page"] == int(row["expected_page"]) for s in sources)
        hits += found
        print(f"[{'OK ' if found else 'MISS'}] {row['question']}")

    total = len(rows)
    print(f"\nCorrect source in the returned results for {hits} of {total} questions ({hits / total:.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
