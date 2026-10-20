"""Static build for GitHub Pages. Needs no services."""

import re

import pytest

from build import build, normalise_base

PAGES = [
    "index.html",
    *(f"{p}/index.html" for p in ("experience", "projects", "skills", "lab", "contact")),
]
INTERNAL_LINK = re.compile(r'(?:href|src)="(/[^"]*)"')
PHONE_PATTERN = re.compile(r"\+\d[\d\s-]{6,}\d|\btel:")


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    build(out, base="/portfolio/")
    return out


def test_every_page_is_built(dist):
    for page in PAGES:
        assert (dist / page).is_file(), page
    assert (dist / "static" / "style.css").is_file()
    assert (dist / ".nojekyll").is_file()


@pytest.mark.parametrize("page", PAGES)
def test_internal_links_use_the_published_base_path(dist, page):
    links = INTERNAL_LINK.findall((dist / page).read_text())
    assert links, page
    assert all(link.startswith("/portfolio/") for link in links), links


@pytest.mark.parametrize("page", PAGES)
def test_no_phone_number_on_published_pages(dist, page):
    assert not PHONE_PATTERN.search((dist / page).read_text())


def test_static_lab_has_no_live_parts(dist):
    html = (dist / "lab" / "index.html").read_text()
    for live_only in ("status-list", "/api/ask", "/api/health", "lab.js", "ask-form"):
        assert live_only not in html
    assert not (dist / "static" / "lab.js").exists()


def test_static_lab_shows_recorded_examples(dist):
    html = (dist / "lab" / "index.html").read_text()
    assert "Recorded from the local AI Lab on" in html
    assert "Where does Blessing work now?" in html


def test_cname_is_written_for_a_custom_domain(tmp_path):
    build(tmp_path, base="/", cname="example.com")
    assert (tmp_path / "CNAME").read_text() == "example.com\n"
    assert 'href="/experience/"' in (tmp_path / "index.html").read_text()


@pytest.mark.parametrize(
    ("raw", "expected"), [("/portfolio/", "/portfolio/"), ("portfolio", "/portfolio/"), ("", "/")]
)
def test_normalise_base(raw, expected):
    assert normalise_base(raw) == expected
