"""Generate the link preview image and favicons. Run with: uv run python scripts/build_og_image.py

Renders site/templates/og.html (name, headline and metrics from content/) at 1200x627 for
LinkedIn and other link previews, and rasterises site/static/favicon.svg to PNG icons.
Re-run after changing the profile highlights or headline, then commit the images.
"""

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api import content, pages  # noqa: E402

STATIC = pages.SITE_DIR / "static"


def main() -> None:
    env = Environment(
        loader=FileSystemLoader(pages.SITE_DIR / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    profile = content.load_profile()
    html = env.get_template("og.html").render(profile=profile, metrics=pages.metrics(profile))
    svg = (STATIC / "favicon.svg").read_text()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 627})
        page.set_content(html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(STATIC / "og-image.png"))
        for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
            icon = browser.new_page(viewport={"width": size, "height": size})
            icon.set_content(
                f'<body style="margin:0"><div style="width:{size}px;height:{size}px">{svg}</div>'
                "<style>svg{width:100%;height:100%;display:block}</style></body>"
            )
            icon.screenshot(path=str(STATIC / name))
        browser.close()
    for name in ("og-image.png", "favicon-32.png", "apple-touch-icon.png"):
        print(f"Saved site/static/{name}")


if __name__ == "__main__":
    main()
