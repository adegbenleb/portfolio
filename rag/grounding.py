"""Check that an answer only names tools and products that appear in the retrieved chunks.

Small local models like to add general knowledge ("Azure Data Factory can be managed with
Kubernetes"). The prompt forbids it, but a prompt is a request, not a guarantee, so we check
the answer after it is written.

What counts as a name:
- every tool from content/ (role and project tags, and skills with a capital letter, such
  as "Azure Data Factory" or "dbt"), matched anywhere in the answer, and
- every capitalised or CamelCase word that is not the first word of a sentence, which also
  catches tools that appear nowhere in content/, such as "Kubernetes" or "Spark".

A name is supported if it appears in the question or in at least one retrieved chunk.
"""

import re

from api import content

# Words that may be capitalised mid-sentence without being a tool or product. Month names
# matter because models rewrite "08/2024" as "August 2024".
MONTHS = "january february march april may june july august september october november december"
DAYS = "monday tuesday wednesday thursday friday saturday sunday"
ALLOWED_WORDS = {
    "blessing",
    "blessing's",
    "i",
    "he",
    "his",
    "him",
    "data",
    "engineer",
    *MONTHS.split(),
    *DAYS.split(),
}

SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[\"'])")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#.'-]*[A-Za-z0-9+#]|[A-Za-z]")
CITATION = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")


def vocabulary() -> set[str]:
    """Tool names from content/, read on each call so edits are picked up."""
    terms = set()
    for item in content.load_experience() + content.load_projects():
        terms.update(item.get("tags", []))
    for group in content.load_skills():
        terms.update(e["name"] for e in group["entries"] if not e["name"].islower())
    return terms


def sentences(text: str) -> list[str]:
    return [s for s in SENTENCE_END.split(text.strip()) if s]


def _contains(haystack: str, term: str) -> bool:
    return bool(re.search(rf"(?<![A-Za-z0-9]){re.escape(term.lower())}(?![A-Za-z0-9])", haystack))


def names_in(sentence: str, vocab: set[str]) -> set[str]:
    clean = CITATION.sub(" ", sentence)
    found = {term for term in vocab if _contains(clean.lower(), term)}
    words = WORD.findall(clean)
    for word in words[1:]:
        word = word.rstrip(".").removesuffix("'s")
        capitalised = word[0].isupper() or any(ch.isupper() for ch in word[1:])
        if capitalised and word.lower() not in ALLOWED_WORDS:
            found.add(word)
    return found


def unsupported_names(text: str, context: str) -> dict[str, set[str]]:
    """Map each sentence that names something missing from the context to those names."""
    haystack = context.lower()
    vocab = vocabulary()
    result = {}
    for sentence in sentences(text):
        missing = {name for name in names_in(sentence, vocab) if not _contains(haystack, name)}
        if missing:
            result[sentence] = missing
    return result


def supported_only(text: str, context: str) -> str:
    """The answer with every sentence that names an unsupported tool removed."""
    bad = unsupported_names(text, context)
    return " ".join(s for s in sentences(text) if s not in bad)
