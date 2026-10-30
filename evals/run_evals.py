"""Run the agent over evals/questions.yml and report accuracy.

Costs API credits: one agent run per question (12 by default). Usage: python -m evals.run_evals [--limit N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import duckdb
import yaml

from agent.agent import OUT_OF_SCOPE, ask
from agent.query import DEFAULT_DB

QUESTIONS = Path(__file__).resolve().parent / "questions.yml"


def numbers_in(text: str) -> list[float]:
    return [float(n.replace(",", "")) for n in re.findall(r"-?\d[\d,]*\.?\d*", text)]


def is_correct(answer: str, case: dict, expected: float | None, tolerance: float = 0.005) -> bool:
    if case.get("answerable", True) is False:
        return OUT_OF_SCOPE.lower() in answer.lower()
    return any(abs(n - expected) <= max(abs(expected) * tolerance, 0.01) or abs(abs(n) - abs(expected)) <= 0.01
               for n in numbers_in(answer))


def expected_values(cases: list[dict], db_path) -> list[float | None]:
    with duckdb.connect(str(db_path), read_only=True) as con:
        return [float(con.execute(c["expected_sql"]).fetchone()[0]) if c.get("expected_sql") else None for c in cases]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    db = Path(os.environ.get("AGENT_DB_PATH", DEFAULT_DB))
    cases = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))[: args.limit]
    expected = expected_values(cases, db)
    results = []
    for case, exp in zip(cases, expected):
        answer = ask(case["question"], db_path=db)
        ok = is_correct(answer.text, case, exp)
        results.append({"question": case["question"], "expected": exp, "correct": ok, "answer": answer.text,
                        "queries": answer.queries})
        print(f"{'PASS' if ok else 'FAIL'}  {case['question']}")
    accuracy = sum(r["correct"] for r in results) / len(results)
    out = Path(__file__).resolve().parent.parent / "output" / "eval_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"accuracy": accuracy, "results": results}, indent=2), encoding="utf-8")
    print(f"\nAccuracy: {accuracy:.0%} ({sum(r['correct'] for r in results)}/{len(results)})  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
