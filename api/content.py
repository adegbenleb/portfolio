"""Load the Markdown files in content/. They are the single source of truth for every page
and for the AI Lab's search index (rag/chunks.py reads content through this module too)."""

import re
from pathlib import Path

import frontmatter
import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

SKILL_LINE = re.compile(r"^\*\*(?P<label>.+?)\*\*:\s*(?P<items>.+)$")
TOOL_NOTE = re.compile(r"^(?P<name>.+?)\s*\((?P<note>[^)]+)\)$")


def format_month(value) -> str:
    """Turn "2026-05" into "05/2026", and "present" into "Present"."""
    text = str(value)
    if text.lower() == "present":
        return "Present"
    year, month = text.split("-")[:2]
    return f"{month}/{year}"


def date_range(start, end, separator: str = " – ") -> str:
    return f"{format_month(start)}{separator}{format_month(end)}"


def plain(text: str) -> str:
    """Strip the bold markers used in the content files, for search chunks."""
    return text.replace("**", "")


def parse_body(body: str) -> list[dict]:
    """Split a Markdown body into sections: [{"heading", "paragraphs", "bullets"}].

    Text before the first "## " heading belongs to a section whose heading is None.
    """
    sections = [{"heading": None, "paragraphs": [], "bullets": []}]
    paragraph: list[str] = []

    def flush():
        if paragraph:
            sections[-1]["paragraphs"].append(" ".join(paragraph))
            paragraph.clear()

    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            flush()
            sections.append({"heading": line[3:].strip(), "paragraphs": [], "bullets": []})
        elif line.startswith("- "):
            flush()
            sections[-1]["bullets"].append(line[2:].strip())
        elif line:
            paragraph.append(line)
        else:
            flush()
    flush()
    return [s for s in sections if s["heading"] or s["paragraphs"] or s["bullets"]]


def load_profile() -> dict:
    post = frontmatter.load(CONTENT_DIR / "profile.md")
    intro_section, *sections = parse_body(post.content)
    summary = intro_section["paragraphs"][0]
    sentences = re.split(r"(?<=\.)\s+", summary)
    return {
        **post.metadata,
        "file": "content/profile.md",
        "summary": summary,
        "intro": " ".join(sentences[:2]),
        "available": format_month(post["available_from"]) if "available_from" in post else "",
        "sections": sections,
    }


def load_experience() -> list[dict]:
    """All roles, newest first."""
    roles = []
    for path in (CONTENT_DIR / "experience").glob("*.md"):
        post = frontmatter.load(path)
        body = parse_body(post.content)[0]
        roles.append(
            {
                **post.metadata,
                "slug": path.stem,
                "file": f"content/experience/{path.name}",
                "dates": date_range(post["start"], post["end"]),
                "intro": body["paragraphs"],
                "bullets": body["bullets"],
                "body_html": markdown.markdown(post.content),
            }
        )
    return sorted(roles, key=lambda role: str(role["start"]), reverse=True)


def load_projects() -> list[dict]:
    projects = []
    for path in (CONTENT_DIR / "projects").glob("*.md"):
        post = frontmatter.load(path)
        first, *rest = parse_body(post.content)[0]["paragraphs"]
        projects.append(
            {
                **post.metadata,
                "slug": path.stem,
                "file": f"content/projects/{path.name}",
                "dates": date_range(post["start"], post["end"]),
                "description": first,
                "paragraphs": [first, *rest],
                "more_html": markdown.markdown("\n\n".join(rest)),
            }
        )
    return sorted(projects, key=lambda project: str(project["start"]), reverse=True)


def load_skills() -> list[dict]:
    """Skill groups parsed from "- **Label**: a, b (note)" lines.

    Returns [{"label", "tools": ["a", "b (note)"], "entries": [{"name", "note"}]}]. The
    search chunks use "tools" as written; the Skills page shows the note separately.
    """
    post = frontmatter.load(CONTENT_DIR / "skills.md")
    groups = []
    for bullet in parse_body(post.content)[0]["bullets"]:
        match = SKILL_LINE.match(bullet)
        if match:
            tools = [tool.strip() for tool in match["items"].split(",")]
            entries = []
            for tool in tools:
                note = TOOL_NOTE.match(tool)
                entries.append(
                    {"name": note["name"], "note": note["note"]}
                    if note
                    else {"name": tool, "note": ""}
                )
            groups.append({"label": match["label"], "tools": tools, "entries": entries})
    return groups
