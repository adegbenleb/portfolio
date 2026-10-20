"""Render the website into dist/ for GitHub Pages. Run with: uv run python build.py

Uses the same templates and content reader as the live FastAPI site (api/pages.py). The AI
Lab page is replaced by a static version with a demo video and recorded examples, because
GitHub Pages cannot run the local LLM.

SITE_BASE sets the path the site is served from: "/portfolio/" for
https://adegbenleb.github.io/portfolio/ (the default), or "/" for a custom domain.
"""

import argparse
import os
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from api import pages

DEFAULT_BASE = "/portfolio/"


def normalise_base(base: str) -> str:
    return "/" + base.strip("/") + "/" if base.strip("/") else "/"


def build(out_dir: Path, base: str = DEFAULT_BASE, cname: str = "") -> list[Path]:
    base = normalise_base(base)
    env = Environment(
        loader=FileSystemLoader(pages.SITE_DIR / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    url = pages.make_url(base, static_site=True)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(pages.SITE_DIR / "static", out_dir / "static")
    # The live lab script calls /api/ask, which does not exist on the static site.
    (out_dir / "static" / "lab.js").unlink(missing_ok=True)

    written = []
    for path, key, _label in pages.NAV:
        template, context = pages.context(key, url, static_site=True)
        target = out_dir / path / "index.html" if path else out_dir / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(**context))
        written.append(target)

    # Serve files as they are, without Jekyll processing.
    (out_dir / ".nojekyll").touch()
    if cname:
        (out_dir / "CNAME").write_text(cname.strip() + "\n")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="dist", help="output folder (default: dist)")
    parser.add_argument("--base", default=os.getenv("SITE_BASE", DEFAULT_BASE))
    parser.add_argument("--cname", default=os.getenv("SITE_CNAME", ""), help="custom domain")
    args = parser.parse_args()
    written = build(Path(args.out), args.base, args.cname)
    for path in written:
        print(path)
    print(f"Built {len(written)} pages into {args.out}/ for base {normalise_base(args.base)}")


if __name__ == "__main__":
    main()
