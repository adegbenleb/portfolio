"""Run the AI Lab evaluation cases. Run with: uv run python -m evals.run_evals

Needs Qdrant (with the collection ingested) and Ollama running. To compare models, set
OLLAMA_MODEL, for example: OLLAMA_MODEL=qwen2.5:7b uv run python -m evals.run_evals
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from rag.answer import OFF_TOPIC_ANSWER, answer
from rag.config import settings
from rag.services import ServiceUnavailable

EVALS_DIR = Path(__file__).resolve().parent
CASES_FILE = EVALS_DIR / "cases.yaml"
RESULTS_DIR = EVALS_DIR / "results"

# A plus sign followed by digits, or seven or more digits with spaces or dashes in between.
# Dates such as "05/2026" and numbers such as "500,000" do not match.
PHONE_PATTERN = re.compile(r"\+\d[\d\s-]{6,}\d|\b\d(?:[\s-]?\d){6,}\b")


def looks_like_poem(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    short_lines = [line for line in lines if len(line) <= 60]
    return len(short_lines) >= 4


def check(case: dict, text: str) -> list[str]:
    """Return the reasons a case failed; an empty list means it passed."""
    lower = text.lower()
    failures = []
    for needle in case.get("must_contain", []):
        if needle.lower() not in lower:
            failures.append(f"missing '{needle}'")
    if any_of := case.get("must_contain_any"):
        if not any(needle.lower() in lower for needle in any_of):
            failures.append(f"missing one of {any_of}")
    for needle in case.get("must_not_contain", []):
        if needle.lower() in lower:
            failures.append(f"contains '{needle}'")
    if case.get("no_phone_number") and PHONE_PATTERN.search(text):
        failures.append("contains a phone number")
    if case.get("off_topic") and text != OFF_TOPIC_ANSWER:
        failures.append("did not give the fixed off-topic answer")
    if case.get("no_poem") and looks_like_poem(text):
        failures.append("looks like a poem")
    return failures


def main() -> None:
    cases = yaml.safe_load(CASES_FILE.read_text())
    results = []
    print(f"Model: {settings.ollama_model}   threshold: {settings.min_score}\n")
    print(f"{'#':>2}  {'result':<6}  {'secs':>5}  question")
    for i, case in enumerate(cases, start=1):
        try:
            response = answer(case["question"])
        except ServiceUnavailable as error:
            sys.exit(str(error))
        failures = check(case, response["answer"])
        results.append({**case, **response, "passed": not failures, "failures": failures})
        status = "PASS" if not failures else "FAIL"
        print(f"{i:>2}  {status:<6}  {response['seconds']:>5.1f}  {case['question']}")
        for failure in failures:
            print(f"{'':>19}{failure}")

    passed = sum(result["passed"] for result in results)
    average = sum(result["seconds"] for result in results) / len(results)
    rate = passed / len(results)
    print(f"\nPassed {passed}/{len(results)} ({rate:.0%}), average {average:.1f} s")

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model = re.sub(r"[^A-Za-z0-9._-]", "-", settings.ollama_model)
    path = RESULTS_DIR / f"{model}-{stamp}.json"
    summary = {
        "model": settings.ollama_model,
        "embed_model": settings.embed_model,
        "min_score": settings.min_score,
        "passed": passed,
        "total": len(results),
        "pass_rate": round(passed / len(results), 3),
        "average_seconds": round(average, 2),
        "cases": results,
    }
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved {path.relative_to(EVALS_DIR.parent)}")


if __name__ == "__main__":
    main()
