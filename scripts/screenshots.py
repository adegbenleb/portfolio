"""Screenshot key pages in both themes on desktop and mobile, for design review.

Needs the local site running (uv run uvicorn api.main:app --port 18600) and Google Chrome.
Run with: uv run python scripts/screenshots.py   Writes docs/screenshots/<page>-<theme>-<device>.jpg
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = "http://localhost:18600"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
PAGES = {"home": "/", "experience": "/experience", "projects": "/projects", "lab": "/lab"}
DEVICES = {
    "desktop": {"viewport": {"width": 1280, "height": 900}, "device_scale_factor": 1},
    "mobile": {
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 1,
        "is_mobile": True,
        "has_touch": True,
    },
}
THEMES = ("dark", "light")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for theme in THEMES:
            for device, options in DEVICES.items():
                context = browser.new_context(**options, reduced_motion="reduce")
                # Same mechanism a visitor's saved choice uses.
                context.add_init_script(f"localStorage.setItem('theme', '{theme}')")
                page = context.new_page()
                for name, path in PAGES.items():
                    page.goto(SITE + path, wait_until="networkidle")
                    page.evaluate("document.fonts.ready")
                    if name == "lab":
                        page.wait_for_selector(".status:not([data-state='checking'])")
                    target = OUT / f"{name}-{theme}-{device}.jpg"
                    page.screenshot(path=str(target), full_page=True, type="jpeg", quality=70)
                    print(target.relative_to(OUT.parent.parent))
                context.close()
        browser.close()


if __name__ == "__main__":
    main()
