"""The website and the public CV PDF must say exactly what content/ says."""

import re
import unicodedata

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from api import content
from api.main import app
from api.pages import CV_PDF

client = TestClient(app)


def squash(text: str) -> str:
    """Compare text regardless of line breaks, entities and bold markers."""
    text = unicodedata.normalize("NFKC", text).replace("**", "")
    text = text.replace("&amp;", "&").replace("&#39;", "'")
    return re.sub(r"\s+", "", text)


@pytest.fixture(scope="module")
def pdf_text() -> str:
    return " ".join(page.extract_text() for page in PdfReader(CV_PDF).pages)


def test_cv_pdf_has_no_ligatures_that_break_applicant_tracking(pdf_text):
    ligatures = {c for c in pdf_text if unicodedata.name(c, "").startswith("LATIN SMALL LIGATURE")}
    assert not ligatures
    assert "Snowflake" in pdf_text and "Airflow" in pdf_text


def test_every_role_fact_and_bullet_is_in_the_cv_pdf(pdf_text):
    pdf = squash(pdf_text)
    for role in content.load_experience():
        for fact in (role["title"], role["company"], role["dates"], role["location"]):
            assert squash(fact) in pdf, (role["company"], fact)
        for bullet in role["bullets"]:
            assert squash(bullet) in pdf, (role["company"], bullet[:60])


def test_every_bullet_and_date_is_on_the_experience_page():
    page = squash(client.get("/experience").text)
    for role in content.load_experience():
        assert squash(role["iso_dates"]) in page
        for bullet in role["bullets"]:
            assert squash(bullet) in page, (role["company"], bullet[:60])


def test_education_certificates_summary_and_skills_are_in_the_cv_pdf(pdf_text):
    pdf = squash(pdf_text)
    profile = content.load_profile()
    for section in profile["sections"]:
        for item in section["bullets"]:
            assert squash(item) in pdf, item[:60]
    assert squash(profile["summary"]) in pdf
    for group in content.load_skills():
        for tool in group["tools"]:
            assert squash(tool) in pdf, tool


def test_msc_dates_match_the_cv(pdf_text):
    assert squash("(04/2022 to 03/2026)") in squash(pdf_text)
    about = content.load_page("about")["html_by_heading"]
    assert "In April 2022 I started an MSc" in " ".join(about.values())
    assert "I finished it in March 2026" in " ".join(about.values())
