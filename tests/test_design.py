"""Dark data-console design: header, home, experience timeline, palette and safety checks."""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import main
from build import build

client = TestClient(main.app)
PAGES = ["/", "/about", "/experience", "/projects", "/skills", "/lab", "/media", "/contact"]
NAV_LABELS = [
    "~/home",
    "~/about",
    "~/experience",
    "~/projects",
    "~/skills",
    "~/ai-lab",
    "~/media",
    "~/contact",
]
PHONE_PATTERN = re.compile(r"\+\d[\d\s-]{6,}\d|\btel:")
STYLE = Path(__file__).resolve().parent.parent / "site" / "static" / "style.css"


def search_index(html: str) -> list[dict]:
    match = re.search(
        r'<script type="application/json" id="search-index">(.*?)</script>', html, re.S
    )
    assert match, "search index missing"
    return json.loads(match.group(1))


@pytest.mark.parametrize("path", PAGES)
def test_header_has_brand_file_nav_and_open_to_work_badge(path):
    html = client.get(path).text
    assert '<span class="brand-box" aria-hidden="true">B.A</span>' in html
    assert "blessing.adegbenle" in html
    for label in NAV_LABELS:
        assert f">{label}</a>" in html
    assert "open to work · from 12/2026" in html
    assert 'data-menu-toggle aria-expanded="false" aria-controls="site-nav"' in html


@pytest.mark.parametrize(
    ("path", "label"), [("/", "~/home"), ("/experience", "~/experience"), ("/lab", "~/ai-lab")]
)
def test_current_page_is_marked_in_the_nav(path, label):
    html = client.get(path).text
    assert re.search(rf'aria-current="page">{re.escape(label)}</a>', html)


@pytest.mark.parametrize("path", PAGES)
def test_dark_only_without_theme_toggle(path):
    html = client.get(path).text
    assert "data-theme-toggle" not in html
    assert 'localStorage.getItem("theme")' not in html
    assert '<meta name="color-scheme" content="dark">' in html


def test_no_light_theme_in_the_stylesheet():
    css = STYLE.read_text()
    assert 'data-theme="light"' not in css
    assert "--accent: #22d3ee" in css


def test_home_matches_the_mockup_sections():
    html = client.get("/").text
    # SQL panel with the current role from content/
    assert "query.sql" in html
    assert re.search(r"<span>Data Engineer</span><span>Phaina</span><span>2026-05</span>", html)
    # Metric cards with snake_case labels from profile.md highlights
    for label in (
        "products_ingested",
        "attribute_values",
        "company_catalogues",
        "years_experience",
    ):
        assert f'<p class="mono-label">{label}</p>' in html
    assert '<p class="metric-value accent">4+</p>' in html
    # Five-step DAG from content/stack.md
    for name in ("Extract", "Load", "Transform", "Store", "AI &amp; analytics"):
        assert f'<p class="step-name">{name}</p>' in html
    # Projects and a real recorded AI Lab answer
    assert "select * from projects" in html
    assert "recorded example" in html


def test_home_lab_teaser_is_a_real_recorded_answer():
    recorded = json.loads(Path("evals/recorded_examples.json").read_text())
    answers = [example["answer"] for example in recorded["examples"]]
    html = client.get("/").text
    teaser = re.search(r'<p class="answer-text">(.*?)</p>', html, re.S).group(1)
    assert teaser.replace("&#39;", "'") in answers


def test_experience_timeline_shows_running_and_success():
    html = client.get("/experience").text
    assert html.count("status: running") == 1
    assert html.count("status: success") == 2
    assert html.index("status: running") < html.index("Data Engineer · Miele")
    assert "dag: career · 3 tasks · 4+ years" in html


def test_search_index_covers_pages_roles_projects_and_skills():
    entries = search_index(client.get("/").text)
    assert {entry["kind"] for entry in entries} == {"Page", "Role", "Project", "Skills"}
    urls = {entry["url"] for entry in entries}
    assert "/experience#role-miele" in urls
    assert "/projects#project-adhereai" in urls


@pytest.mark.parametrize("path", PAGES)
def test_no_phone_number_anywhere_including_search_data(path):
    html = client.get(path).text
    assert not PHONE_PATTERN.search(html)
    assert not PHONE_PATTERN.search(json.dumps(search_index(html)))


def test_no_phone_number_in_any_tracked_text_file():
    root = Path(__file__).resolve().parent.parent
    for folder in ("content", "site", "api", "rag", "evals", "docs"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and path.suffix in {
                ".md",
                ".html",
                ".py",
                ".js",
                ".css",
                ".json",
                ".yaml",
            }:
                assert not PHONE_PATTERN.search(path.read_text(errors="ignore")), path


def test_animations_are_switched_off_for_reduced_motion():
    block = STYLE.read_text().split("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert "animation: none !important" in block
    assert "transition: none !important" in block


def test_static_build_keeps_scripts_and_versioned_links(tmp_path):
    build(tmp_path, base="/portfolio/")
    assert (tmp_path / "static" / "site.js").is_file()
    html = (tmp_path / "index.html").read_text()
    assert re.search(r'href="/portfolio/static/style\.css\?v=[0-9a-f]{10}"', html)
    assert "/portfolio/experience/#role-miele" in {e["url"] for e in search_index(html)}


@pytest.mark.parametrize("asset", ["static/style.css", "static/site.js"])
def test_css_and_js_links_carry_a_content_version(asset):
    html = client.get("/").text
    match = re.search(rf'"/{asset}\?v=([0-9a-f]{{10}})"', html)
    assert match, f"{asset} has no version"
    assert client.get(f"/{asset}?v={match.group(1)}").status_code == 200


def test_version_changes_when_the_file_changes(tmp_path, monkeypatch):
    from api import pages

    (tmp_path / "static").mkdir()
    css = tmp_path / "static" / "x.css"
    css.write_text("a{}")
    monkeypatch.setattr(pages, "SITE_DIR", tmp_path)
    first = pages.asset_version("static/x.css")
    css.write_text("b{}")
    assert pages.asset_version("static/x.css") != first
