"""Load the Markdown files in content/. They are the single source of truth for every page."""

import re
from pathlib import Path

import frontmatter
import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

SKILL_LINE = re.compile(r"^- \*\*(?P<label>.+?)\*\*:\s*(?P<items>.+)$")


def format_month(value) -> str:
    """Turn "2026-05" into "05/2026", and "present" into "Present"."""
    text = str(value)
    if text.lower() == "present":
        return "Present"
    year, month = text.split("-")[:2]
    return f"{month}/{year}"


def date_range(start, end) -> str:
    return f"{format_month(start)} – {format_month(end)}"


def _paragraphs(body: str) -> list[str]:
    return [p.strip() for p in body.strip().split("\n\n") if p.strip()]


def load_profile() -> dict:
    post = frontmatter.load(CONTENT_DIR / "profile.md")
    summary, *rest = _paragraphs(post.content)
    sentences = re.split(r"(?<=\.)\s+", summary)
    return {
        **post.metadata,
        "summary": summary,
        "intro": " ".join(sentences[:2]),
        "details_html": markdown.markdown("\n\n".join(rest)),
    }


def load_experience() -> list[dict]:
    """All roles, newest first."""
    roles = []
    for path in (CONTENT_DIR / "experience").glob("*.md"):
        post = frontmatter.load(path)
        roles.append(
            {
                **post.metadata,
                "slug": path.stem,
                "dates": date_range(post["start"], post["end"]),
                "body_html": markdown.markdown(post.content),
            }
        )
    return sorted(roles, key=lambda role: str(role["start"]), reverse=True)


def load_projects() -> list[dict]:
    projects = []
    for path in (CONTENT_DIR / "projects").glob("*.md"):
        post = frontmatter.load(path)
        first, *rest = _paragraphs(post.content)
        projects.append(
            {
                **post.metadata,
                "slug": path.stem,
                "dates": date_range(post["start"], post["end"]),
                "description": first,
                "more_html": markdown.markdown("\n\n".join(rest)),
            }
        )
    return sorted(projects, key=lambda project: str(project["start"]), reverse=True)


def load_skills() -> list[dict]:
    """Skill groups as [{"label": ..., "tools": [...]}], parsed from "- **Label**: a, b" lines."""
    post = frontmatter.load(CONTENT_DIR / "skills.md")
    groups = []
    for line in post.content.splitlines():
        match = SKILL_LINE.match(line.strip())
        if match:
            tools = [tool.strip() for tool in match["items"].split(",")]
            groups.append({"label": match["label"], "tools": tools})
    return groups
