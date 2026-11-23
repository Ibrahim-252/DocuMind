"""Ask questions the document cannot answer and check the system refuses.

Usage: python eval/run_unanswerable.py [--api URL] [--questions FILE]
"""
import argparse
import csv

import httpx

NOT_FOUND = "I could not find this in the uploaded documents."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--questions", default="eval/unanswerable.csv")
    args = parser.parse_args()

    with open(args.questions, newline="", encoding="utf-8") as f:
        questions = [row["question"] for row in csv.DictReader(f)]

    refused = 0
    answered = []
    for question in questions:
        response = httpx.post(
            f"{args.api}/chat", json={"question": question}, timeout=120
        )
        response.raise_for_status()
        answer = response.json()["answer"].strip()
        if answer == NOT_FOUND:
            refused += 1
            print(f"[REFUSED ] {question}")
        else:
            answered.append((question, answer))
            print(f"[ANSWERED] {question}")

    print()
    for question, answer in answered:
        print(f"Q: {question}\nA: {answer}\n")

    percent = 100 * refused / len(questions)
    print(f"Refused correctly: {refused} of {len(questions)} ({percent:.0f}%)")


if __name__ == "__main__":
    main()