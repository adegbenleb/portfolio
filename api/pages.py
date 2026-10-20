"""Page definitions shared by the live FastAPI site and the static build (build.py).

Both render the same templates with the same context, so the published site cannot drift
from the local one. The only differences are the URL scheme and the AI Lab page:
- live:   links like "/experience", and the lab page calls /api/ask
- static: links like "/portfolio/experience/", and the lab page shows recorded examples
"""

import json
from collections.abc import Callable
from pathlib import Path

from api import content

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
RECORDED_EXAMPLES = ROOT / "evals" / "recorded_examples.json"
DEMO_VIDEO = SITE_DIR / "static" / "demo.mp4"

# (path, key, label). "" is the home page.
NAV = [
    ("", "home", "Home"),
    ("experience", "experience", "Experience"),
    ("projects", "projects", "Projects"),
    ("skills", "skills", "Skills"),
    ("lab", "lab", "AI Lab"),
    ("contact", "contact", "Contact"),
]

LAB_EXAMPLES = [
    "Where does Blessing work now?",
    "What did he do at Miele?",
    "Which vector database does he use?",
    "What is the ShopFlow project?",
]


def make_url(base: str = "/", static_site: bool = False) -> Callable[[str], str]:
    """Build links for templates: url("experience"), url("static/style.css"), url("")."""

    def url(path: str = "") -> str:
        is_page = path and not path.startswith("static/")
        if static_site and is_page:
            return f"{base}{path}/"
        return f"{base}{path}"

    return url


def load_recorded_examples() -> dict:
    if not RECORDED_EXAMPLES.exists():
        return {"recorded_on": "", "examples": []}
    return json.loads(RECORDED_EXAMPLES.read_text())


def page(key: str, static_site: bool = False) -> tuple[str, dict]:
    """Template name and page-specific context for one page."""
    if key == "home":
        return "home.html", {}
    if key == "experience":
        return "experience.html", {"roles": content.load_experience()}
    if key == "projects":
        return "projects.html", {"projects": content.load_projects()}
    if key == "skills":
        return "skills.html", {"groups": content.load_skills()}
    if key == "lab" and static_site:
        return "lab_static.html", {
            "recorded": load_recorded_examples(),
            "has_video": DEMO_VIDEO.exists(),
        }
    if key == "lab":
        return "lab.html", {"examples": LAB_EXAMPLES}
    if key == "contact":
        return "contact.html", {}
    raise KeyError(key)


def context(key: str, url: Callable[[str], str], static_site: bool = False) -> tuple[str, dict]:
    """Full template context: shared layout data plus the page's own data."""
    template, extra = page(key, static_site)
    return template, {
        "nav": NAV,
        "active": key,
        "url": url,
        "static_site": static_site,
        "profile": content.load_profile(),
        **extra,
    }
