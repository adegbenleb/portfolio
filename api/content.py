"""Load the Markdown files in content/. They are the single source of truth for every page
and for the AI Lab's search index (rag/chunks.py reads content through this module too)."""

import re
from datetime import date
from pathlib import Path

import frontmatter
import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

SKILL_LINE = re.compile(r"^\*\*(?P<label>.+?)\*\*:\s*(?P<items>.+)$")
TOOL_NOTE = re.compile(r"^(?P<name>.+?)\s*\((?P<note>[^)]+)\)$")
LABELLED = re.compile(r"^\*\*(?P<label>.+?)\*\*:?\s*(?P<text>.*)$")
MARKDOWN_EXTENSIONS = ["fenced_code"]


def to_html(text: str) -> str:
    return markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)


def section_markdown(section: dict) -> str:
    """Markdown for one parsed section's paragraphs and bullets (without its heading)."""
    parts = list(section["paragraphs"])
    if section["bullets"]:
        parts.append("\n".join(f"- {bullet}" for bullet in section["bullets"]))
    return "\n\n".join(parts)


def labelled_items(bullets: list[str]) -> list[dict]:
    """Turn "**Problem**: text" bullets into [{"label": "Problem", "text": "text"}]."""
    items = []
    for bullet in bullets:
        match = LABELLED.match(bullet)
        if match:
            items.append({"label": match["label"].rstrip(":"), "text": match["text"]})
    return items


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
        body, *sections = parse_body(post.content)
        case = next((s for s in sections if s["heading"] == "Case study"), None)
        roles.append(
            {
                **post.metadata,
                "slug": path.stem,
                "file": f"content/experience/{path.name}",
                "dates": date_range(post["start"], post["end"]),
                "iso_dates": f"{iso_month(post['start'])} · {iso_month(post['end'])}",
                "city": str(post.get("location", "")).split(",")[0].lower(),
                "current": str(post["end"]).lower() == "present",
                "intro": body["paragraphs"],
                "bullets": body["bullets"],
                "body_html": to_html(section_markdown(body)),
                "case_study": labelled_items(case["bullets"]) if case else [],
            }
        )
    return sorted(roles, key=lambda role: str(role["start"]), reverse=True)


def load_projects() -> list[dict]:
    projects = []
    for path in (CONTENT_DIR / "projects").glob("*.md"):
        post = frontmatter.load(path)
        body = parse_body(post.content)[0]
        first, *rest = body["paragraphs"]
        more = section_markdown({"paragraphs": rest, "bullets": body["bullets"]})
        projects.append(
            {
                **post.metadata,
                "slug": path.stem,
                "file": f"content/projects/{path.name}",
                "dates": date_range(post["start"], post["end"]),
                "description": first,
                "paragraphs": [first, *rest],
                "bullets": body["bullets"],
                "category": post.get("category", "Personal"),
                "short_title": post["title"].split(":")[0].strip(),
                "year": str(post["start"]).split("-")[0],
                "status_label": project_status(post.metadata),
                "more_html": to_html(more) if more else "",
            }
        )
    # Newest first; projects that started in the same month are ordered by title.
    projects.sort(key=lambda project: project["title"])
    return sorted(projects, key=lambda project: str(project["start"]), reverse=True)


def project_status(metadata: dict) -> str:
    """Badge text from the file: its status, or "Ongoing" when it has no end date."""
    if metadata.get("status"):
        return str(metadata["status"]).capitalize()
    if str(metadata.get("end", "")).lower() == "present":
        return "Ongoing"
    return ""


def load_page(name: str) -> dict:
    """A free-form page such as about.md or lab.md: title, sections and HTML per section."""
    post = frontmatter.load(CONTENT_DIR / f"{name}.md")
    sections = parse_body(post.content)
    for section in sections:
        section["html"] = to_html(section_markdown(section))
    raw = {}
    for chunk in re.split(r"^## ", post.content, flags=re.MULTILINE)[1:]:
        heading, _, text = chunk.partition("\n")
        raw[heading.strip()] = to_html(text)
    return {
        **post.metadata,
        "file": f"content/{name}.md",
        "sections": sections,
        "html_by_heading": raw,
    }


def load_stack() -> dict:
    """The "how I work" pipeline: title, label and five steps from content/stack.md."""
    post = frontmatter.load(CONTENT_DIR / "stack.md")
    return {**post.metadata, "file": "content/stack.md", "intro": post.content.strip()}


def iso_month(value) -> str:
    """ "2026-05" stays "2026-05"; "present" becomes "present"."""
    text = str(value)
    return "present" if text.lower() == "present" else "-".join(text.split("-")[:2])


def snake(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def months_between(start, end=None) -> int:
    year, month = (int(part) for part in str(start).split("-")[:2])
    end_date = end or date.today()
    return (end_date.year - year) * 12 + end_date.month - month


def career_summary() -> dict:
    """Career at a glance, computed from the experience files."""
    roles = load_experience()
    first_start = min(str(role["start"]) for role in roles)
    years = months_between(first_start) // 12
    current = next((r for r in roles if str(r["end"]).lower() == "present"), None)
    return {
        "years": f"{years}+",
        "since": format_month(first_start),
        "companies": [role["company"] for role in roles],
        "domains": [{"company": r["company"], "domain": r.get("domain", "")} for r in roles],
        "current": f"{current['title']} at {current['company']}" if current else "",
    }


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
