"""Record example answers from the real local pipeline for the static AI Lab page.

Run with: uv run python -m evals.record_examples   (needs Qdrant and Ollama running)
Writes evals/recorded_examples.json, which build.py renders as cards. Re-run it after
changing content/ (and re-ingesting), the prompt or the model.
"""

import json
import sys
from datetime import date

from api.pages import RECORDED_EXAMPLES
from rag.answer import OFF_TOPIC_ANSWER, answer
from rag.config import settings
from rag.services import ServiceUnavailable

QUESTIONS = [
    "Where does Blessing work now?",
    "What did he do at Miele?",
    "Which data warehouse did he use at GI Group?",
    "What is the ShopFlow project?",
    "What is AdhereAI?",
    "What is the weather in Berlin?",
]

OFF_TOPIC_NOTE = (
    "Off-topic question: no chunk matched well enough, so the guardrail answered "
    "without calling the LLM."
)


def main() -> None:
    examples = []
    for question in QUESTIONS:
        try:
            result = answer(question)
        except ServiceUnavailable as error:
            sys.exit(str(error))
        example = {
            "question": question,
            "answer": result["answer"],
            "sources": [
                {key: source[key] for key in ("n", "label", "section", "snippet")}
                for source in result["sources"]
            ],
        }
        if result["answer"] == OFF_TOPIC_ANSWER:
            example["note"] = OFF_TOPIC_NOTE
        examples.append(example)
        print(f"- {question}\n  {result['answer']}\n")

    recorded = {
        "recorded_on": date.today().strftime("%d %B %Y").lstrip("0"),
        "model": settings.ollama_model,
        "examples": examples,
    }
    RECORDED_EXAMPLES.write_text(json.dumps(recorded, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {len(examples)} examples to {RECORDED_EXAMPLES.name}")


if __name__ == "__main__":
    main()
