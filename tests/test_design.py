"""Redesign: theme toggle, command palette, timeline and motion settings."""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import main
from build import build

client = TestClient(main.app)
PAGES = ["/", "/about", "/experience", "/projects", "/skills", "/lab", "/media", "/contact"]
PHONE_PATTERN = re.compile(r"\+\d[\d\s-]{6,}\d|\btel:")
STYLE = Path(__file__).resolve().parent.parent / "site" / "static" / "style.css"


def search_index(html: str) -> list[dict]:
    match = re.search(
        r'<script type="application/json" id="search-index">(.*?)</script>', html, re.S
    )
    assert match, "search index missing"
    return json.loads(match.group(1))


@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_the_theme_toggle_and_dark_default(path):
    html = client.get(path).text
    assert '<html lang="en" data-theme="dark">' in html
    assert "data-theme-toggle" in html
    assert 'aria-label="Switch to light theme"' in html
    # The saved choice is applied before paint.
    assert 'localStorage.getItem("theme")' in html


@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_palette_menu_and_progress_bar(path):
    html = client.get(path).text
    assert 'id="command-palette"' in html
    assert "data-open-palette" in html
    assert 'data-menu-toggle aria-expanded="false" aria-controls="site-nav"' in html
    assert 'class="scroll-progress"' in html
    assert "Built with FastAPI, Qdrant and Ollama" in html


def test_search_index_covers_pages_roles_projects_and_skills():
    entries = search_index(client.get("/").text)
    kinds = {entry["kind"] for entry in entries}
    assert kinds == {"Page", "Role", "Project", "Skills"}
    urls = {entry["url"] for entry in entries}
    assert "/experience#role-miele" in urls
    assert "/projects#project-adhereai" in urls


@pytest.mark.parametrize("path", PAGES)
def test_no_phone_number_anywhere_including_search_data(path):
    html = client.get(path).text
    assert not PHONE_PATTERN.search(html)
    assert not PHONE_PATTERN.search(json.dumps(search_index(html)))


def test_first_role_is_open_and_others_are_collapsed():
    html = client.get("/experience").text
    cards = re.findall(r'<details class="role-card"( open)?>', html)
    assert cards == [" open", "", ""]
    assert html.index('id="role-phaina"') < html.index('id="role-miele"')


def test_pipeline_hero_comes_from_content():
    html = client.get("/").text
    for stage in ("Sources", "Pipelines", "Stores", "AI answers"):
        assert f'<span class="stage-name">{stage}</span>' in html
    assert "BMEcat · PIM · CSV · SAP" in html


def test_metrics_are_plain_numbers_not_counters():
    html = client.get("/").text
    assert '<span class="metric-value">500,000+</span>' in html
    assert "data-count" not in html


def test_animations_are_switched_off_for_reduced_motion():
    css = STYLE.read_text()
    block = css.split("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert "animation: none !important" in block
    assert "transition: none !important" in block


def test_static_build_keeps_the_shared_script_and_palette_links(tmp_path):
    build(tmp_path, base="/portfolio/")
    assert (tmp_path / "static" / "site.js").is_file()
    html = (tmp_path / "index.html").read_text()
    urls = {entry["url"] for entry in search_index(html)}
    assert "/portfolio/experience/#role-miele" in urls


@pytest.mark.parametrize("asset", ["static/style.css", "static/site.js"])
def test_css_and_js_links_carry_a_content_version(asset):
    html = client.get("/").text
    match = re.search(rf'"/{asset}\?v=([0-9a-f]{{10}})"', html)
    assert match, f"{asset} has no version"
    # The versioned URL still serves the file.
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
