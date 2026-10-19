import pytest
from fastapi.testclient import TestClient

from api import main
from api.content import format_month
from rag.config import settings

client = TestClient(main.app)

PAGES = ["/", "/experience", "/projects", "/skills", "/lab", "/contact"]
PHONE_FRAGMENTS = ["0000000", "+49 30", "+4930"]


@pytest.mark.parametrize("path", PAGES)
def test_every_page_returns_200(path):
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("path", PAGES)
def test_phone_number_appears_on_no_page(path):
    html = client.get(path).text
    for fragment in PHONE_FRAGMENTS:
        assert fragment not in html


def test_experience_lists_newest_role_first():
    html = client.get("/experience").text
    positions = [html.index(company) for company in ("Phaina", "Miele", "GI Group")]
    assert positions == sorted(positions)


def test_experience_shows_cv_dates():
    html = client.get("/experience").text
    for dates in ("05/2026 – Present", "08/2024 – 03/2026", "07/2022 – 07/2024"):
        assert dates in html


def test_home_shows_headline_facts_as_plain_html():
    html = client.get("/").text
    for fact in ("4+", "500,000+", "15", "5.9M"):
        assert fact in html


def test_current_page_is_highlighted_in_navigation():
    html = client.get("/skills").text
    assert 'href="/skills" aria-current="page"' in html


def test_format_month():
    assert format_month("2026-05") == "05/2026"
    assert format_month("present") == "Present"


def test_health_returns_status_for_both_services():
    data = client.get("/api/health").json()
    assert set(data) == {"ollama", "qdrant"}
    assert all(value in {"online", "offline"} for value in data.values())


def test_health_reports_offline_when_service_is_unreachable(monkeypatch):
    # Port 9 (discard) is closed on a normal machine, so the connection is refused.
    monkeypatch.setattr(settings, "ollama_url", "http://127.0.0.1:9")
    monkeypatch.setattr(settings, "qdrant_url", "http://127.0.0.1:9")
    assert client.get("/api/health").json() == {"ollama": "offline", "qdrant": "offline"}
