"""Record the AI Lab demo video from the running local site.

Needs the local site (uv run uvicorn api.main:app --port 18600), Qdrant and Ollama running,
plus Google Chrome and ffmpeg installed. Run with: uv run python scripts/record_demo.py

Playwright drives a headless Chrome on /lab, asks a few questions, waits for each answer and
its sources, and records the browser. ffmpeg then converts the recording to an H.264 MP4 at
site/static/demo.mp4 plus a poster image, which the static site shows on its AI Lab page.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

SITE = "http://localhost:18600/lab"
STATIC = Path(__file__).resolve().parent.parent / "site" / "static"
OUTPUT = STATIC / "demo.mp4"
POSTER = STATIC / "demo-poster.jpg"
# The first moments show the page still loading, so they are cut.
TRIM_START_SECONDS = "1.5"
SIZE = {"width": 1280, "height": 800}
ANSWER_TIMEOUT_MS = 60_000


def wait_for_answer(page: Page) -> None:
    page.wait_for_function(
        "() => { const a = document.getElementById('answer').textContent;"
        " return a && a !== 'Thinking…'; }",
        timeout=ANSWER_TIMEOUT_MS,
    )
    # Bring the answer and its sources into view, then let the viewer read.
    page.locator("#result").scroll_into_view_if_needed()
    page.wait_for_timeout(3500)


def ask_with_example_button(page: Page, question: str) -> None:
    page.get_by_role("button", name=question).click()
    wait_for_answer(page)


def ask_by_typing(page: Page, question: str) -> None:
    page.locator("#question").scroll_into_view_if_needed()
    page.locator("#question").fill("")
    page.locator("#question").press_sequentially(question, delay=45)
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Ask", exact=True).click()
    wait_for_answer(page)


def record(video_dir: Path) -> Path:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport=SIZE,
            record_video_dir=str(video_dir),
            record_video_size=SIZE,
            color_scheme="light",
        )
        page = context.new_page()
        page.goto(SITE, wait_until="networkidle")
        page.wait_for_selector(".status[data-state='online']")
        page.wait_for_timeout(1500)

        ask_with_example_button(page, "Where does Blessing work now?")
        ask_with_example_button(page, "What did he do at Miele?")
        ask_by_typing(page, "When can he start, and would he relocate?")

        video_path = Path(page.video.path())
        context.close()
        browser.close()
    return video_path


def convert(source: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-ss", TRIM_START_SECONDS, "-i", str(source),
            "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-an", str(OUTPUT),
        ],
        check=True,
    )  # fmt: skip
    # Poster: the last frame, which shows a finished answer with its sources.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-1", "-i", str(OUTPUT),
         "-frames:v", "1", "-q:v", "4", str(POSTER)],
        check=True,
    )  # fmt: skip


def main() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not installed.")
    with tempfile.TemporaryDirectory() as tmp:
        webm = record(Path(tmp))
        convert(webm)
    print(f"Saved {OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
