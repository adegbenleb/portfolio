"""Generate the public CV PDF from content/. Run with: uv run python scripts/build_cv.py

Renders site/templates/cv.html with the same content reader as the website and prints it to
content/cv-public.pdf with headless Chrome. The phone number is not in content/, so it
cannot end up in the PDF; tests/test_build.py checks that anyway.

Re-run after changing content/, then commit the new PDF.
"""

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api import content  # noqa: E402
from api.pages import CV_PDF, SITE_DIR  # noqa: E402


def render_html() -> str:
    env = Environment(
        loader=FileSystemLoader(SITE_DIR / "templates"), autoescape=select_autoescape(["html"])
    )
    return env.get_template("cv.html").render(
        profile=content.load_profile(),
        roles=content.load_experience(),
        projects=content.load_projects(),
        skills=content.load_skills(),
    )


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page.set_content(render_html(), wait_until="load")
        page.pdf(path=str(CV_PDF), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()
    print(f"Saved {CV_PDF.relative_to(ROOT)} ({CV_PDF.stat().st_size / 1000:.0f} KB)")


if __name__ == "__main__":
    main()
