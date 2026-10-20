"""Page definitions shared by the live FastAPI site and the static build (build.py).

Both render the same templates with the same context, so the published site cannot drift
from the local one. The only differences are the URL scheme and the AI Lab page:
- live:   links like "/experience", and the lab page calls /api/ask
- static: links like "/portfolio/experience/", and the lab page shows recorded examples
"""

import hashlib
import json
import os
import re
from collections.abc import Callable
from pathlib import Path

from api import content

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
RECORDED_EXAMPLES = ROOT / "evals" / "recorded_examples.json"
DEMO_VIDEO = SITE_DIR / "static" / "demo.mp4"
CV_PDF = ROOT / "content" / "cv-public.pdf"
CV_DOWNLOAD_PATH = "files/Blessing_Adegbenle_CV.pdf"
# Public address of the published site, used for absolute URLs in share previews.
SITE_URL = os.getenv("SITE_URL", "https://adegbenleb.github.io/portfolio/").rstrip("/") + "/"

# (path, key, label). "" is the home page.
NAV = [
    ("", "home", "Home"),
    ("about", "about", "About"),
    ("experience", "experience", "Experience"),
    ("projects", "projects", "Projects"),
    ("skills", "skills", "Skills"),
    ("lab", "lab", "AI Lab"),
    ("media", "media", "Media"),
    ("contact", "contact", "Contact"),
]

# Short descriptions for the "Explore" cards on the home page.
EXPLORE = {
    "about": "How I got from forestry and ecology into data engineering, and how I work.",
    "experience": "Three data engineering roles, each with a short case study.",
    "projects": "AdhereAI, ShopFlow and this website, with tools and status.",
    "skills": "Databases, platforms, pipelines and the AI tooling I use.",
    "lab": "Ask questions about my experience, answered from my CV with sources.",
    "media": "The AI Lab demo video and my CV as a PDF.",
    "contact": "Email, LinkedIn and GitHub.",
}

PROJECT_CATEGORIES = ["Professional", "Personal", "Academic"]

LAB_EXAMPLES = [
    "Where does Blessing work now?",
    "What did he do at Miele?",
    "Which vector database does he use?",
    "What is the ShopFlow project?",
]


def asset_version(path: str) -> str:
    """Short hash of a CSS or JS file, so its URL changes whenever the file changes.

    Browsers cache these files (GitHub Pages sends max-age=600). Without a version, a
    visitor can get new HTML with an old stylesheet, which breaks the layout.
    """
    file = SITE_DIR / path
    if not file.is_file():
        return ""
    return hashlib.sha256(file.read_bytes()).hexdigest()[:10]


def make_url(base: str = "/", static_site: bool = False) -> Callable[[str], str]:
    """Build links for templates: url("experience"), url("static/style.css"), url("")."""

    def url(path: str = "") -> str:
        if path.startswith("static/") and path.endswith((".css", ".js")):
            version = asset_version(path)
            return f"{base}{path}?v={version}" if version else f"{base}{path}"
        is_file = "." in path.rsplit("/", 1)[-1]
        is_page = path and not path.startswith("static/") and not is_file
        if static_site and is_page:
            return f"{base}{path}/"
        return f"{base}{path}"

    return url


def load_recorded_examples() -> dict:
    if not RECORDED_EXAMPLES.exists():
        return {"recorded_on": "", "examples": []}
    return json.loads(RECORDED_EXAMPLES.read_text())


def key_facts(profile: dict, career: dict) -> list[dict]:
    education = next((s for s in profile["sections"] if s["heading"] == "Education"), None)
    degree = ""
    if education and education["bullets"]:
        # "**Master of Science (MSc) in Ecology**, Universität Bielefeld, ..." -> degree, school
        first = education["bullets"][0]
        title = re.search(r"\*\*(.+?)\*\*", first)
        school = first.split("**, ", 1)[1].split(",")[0] if "**, " in first else ""
        degree = f"{title[1]}, {school}" if title else content.plain(first)
    facts = [
        ("Location", profile.get("location", "")),
        ("Role", career["current"]),
        ("Education", degree),
        ("Experience", f"{career['years']} years, since {career['since']}"),
        ("Languages", ", ".join(profile.get("languages", []))),
        ("Availability", f"From {profile['available']}" if profile.get("available") else ""),
        ("Relocation", profile.get("relocation", "")),
    ]
    return [{"label": label, "value": value} for label, value in facts if value]


def metrics(profile: dict) -> list[dict]:
    """Highlights as dashboard metrics with snake_case labels, e.g. products_ingested."""
    return [
        {"label": content.snake(item["label"]), "value": item["value"]}
        for item in profile.get("highlights", [])
    ]


def lab_teaser() -> dict | None:
    """A real recorded answer for the home page console, never a made-up one."""
    examples = load_recorded_examples().get("examples", [])
    with_sources = [e for e in examples if e.get("sources")]
    preferred = [e for e in with_sources if "Miele" in e["question"]]
    return (preferred or with_sources or [None])[0]


def page(key: str, static_site: bool = False) -> tuple[str, dict]:
    """Template name and page-specific context for one page."""
    if key == "home":
        profile = content.load_profile()
        roles = content.load_experience()
        current = next((role for role in roles if role["current"]), None)
        projects = content.load_projects()
        present = {project["category"] for project in projects}
        return "home.html", {
            "current_role": current,
            "metrics": metrics(profile),
            "stack": content.load_stack(),
            "projects": projects,
            "categories": [c for c in PROJECT_CATEGORIES if c in present],
            "teaser": lab_teaser(),
            "recorded_on": load_recorded_examples().get("recorded_on", ""),
            "cv_path": CV_DOWNLOAD_PATH,
        }
    if key == "about":
        profile, career = content.load_profile(), content.career_summary()
        return "about.html", {
            "about": content.load_page("about"),
            "key_facts": key_facts(profile, career),
        }
    if key == "experience":
        return "experience.html", {
            "roles": content.load_experience(),
            "career": content.career_summary(),
            "intro": content.load_profile().get("experience_intro", ""),
        }
    if key == "projects":
        projects = content.load_projects()
        present = {project["category"] for project in projects}
        return "projects.html", {
            "projects": projects,
            # Only offer filters that have projects behind them.
            "categories": [c for c in PROJECT_CATEGORIES if c in present],
        }
    if key == "media":
        return "media.html", {
            "has_video": DEMO_VIDEO.exists(),
            "has_cv": CV_PDF.exists(),
            "cv_path": CV_DOWNLOAD_PATH,
        }
    if key == "skills":
        return "skills.html", {"groups": content.load_skills()}
    if key == "lab" and static_site:
        return "lab_static.html", {
            "recorded": load_recorded_examples(),
            "has_video": DEMO_VIDEO.exists(),
            "lab": content.load_page("lab"),
        }
    if key == "lab":
        return "lab.html", {"examples": LAB_EXAMPLES, "lab": content.load_page("lab")}
    if key == "contact":
        return "contact.html", {}
    raise KeyError(key)


def search_index(url: Callable[[str], str]) -> list[dict]:
    """Entries for the Cmd+K command palette: pages, roles, projects and skill groups."""
    entries = [
        {"title": label, "kind": "Page", "url": url(path), "hint": EXPLORE.get(key, "")}
        for path, key, label in NAV
    ]
    for role in content.load_experience():
        entries.append(
            {
                "title": f"{role['title']}, {role['company']}",
                "kind": "Role",
                "url": f"{url('experience')}#role-{role['slug']}",
                "hint": f"{role['dates']} · {' '.join(role.get('tags', []))}",
            }
        )
    for project in content.load_projects():
        entries.append(
            {
                "title": project["title"],
                "kind": "Project",
                "url": f"{url('projects')}#project-{project['slug']}",
                "hint": f"{project['type']} · {' '.join(project.get('tags', []))}",
            }
        )
    for i, group in enumerate(content.load_skills(), start=1):
        entries.append(
            {
                "title": group["label"],
                "kind": "Skills",
                "url": f"{url('skills')}#skills-{i}",
                "hint": ", ".join(group["tools"]),
            }
        )
    return entries


def share_meta(key: str, profile: dict) -> dict:
    """Open Graph and Twitter card data for LinkedIn and other link previews."""
    path = next(path for path, k, _label in NAV if k == key)
    label = next(label for _path, k, label in NAV if k == key)
    name, headline = profile["name"], profile["headline"]
    return {
        "title": f"{name}, {headline}" if key == "home" else f"{label}, {name}",
        "description": profile.get("tagline") or profile["intro"],
        "url": SITE_URL + (f"{path}/" if path else ""),
        "image": SITE_URL + "static/og-image.png",
        "image_alt": f"{name}, {headline}",
    }


def context(key: str, url: Callable[[str], str], static_site: bool = False) -> tuple[str, dict]:
    """Full template context: shared layout data plus the page's own data."""
    template, extra = page(key, static_site)
    profile = content.load_profile()
    return template, {
        "share": share_meta(key, profile),
        "nav": NAV,
        "active": key,
        "url": url,
        "static_site": static_site,
        "profile": content.load_profile(),
        "search_index": search_index(url),
        **extra,
    }
