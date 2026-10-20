# Blessing Adegbenle Portfolio

## Purpose
A personal portfolio website with an "AI Lab": a RAG assistant that answers questions about
Blessing's experience, skills and projects. The website pages and the RAG index are both built
from the same Markdown files in `content/`.

## Structure
- `content/`: single source of truth. Markdown files with YAML front matter.
  - `profile.md`: name, headline, contact, languages; body has summary, education, certificates
  - `skills.md`: one bullet per skill group
  - `experience/*.md`: one file per role (title, company, location, start, end, tags)
  - `projects/*.md`: personal projects (title, type, start, end, github, tags)
- `site/`: website pages, generated from `content/`
- `rag/`: chunking, embedding and indexing of `content/` into Qdrant
- `api/`: backend for the AI Lab
- `evals/`: evaluation questions and scripts for the AI Lab
- `docker/`: container and compose files

## Ports
- API: 18600
- Qdrant: 16335
- Ollama: 11434

## Commands
- Install: `uv sync`, then `cp .env.example .env` (settings: OLLAMA_URL, QDRANT_URL,
  OLLAMA_MODEL, EMBED_MODEL)
- Models: `ollama pull llama3.1:8b && ollama pull nomic-embed-text`
- Start Qdrant: `docker compose -f docker/compose.yml up -d`
- Build the search index: `uv run python -m rag.ingest`
- Run the site: `uv run uvicorn api.main:app --port 18600 --reload`, then open
  http://localhost:18600
- Run the evals: `uv run python -m evals.run_evals` (results go to `evals/results/`;
  compare models with `OLLAMA_MODEL=<model> uv run python -m evals.run_evals`)
- Static build: `uv run python build.py` (dist/, not committed; `--base /` for a custom domain)
- Recorded examples for the static AI Lab: `uv run python -m evals.record_examples`
- Demo video: `uv run python scripts/record_demo.py` (local site, Qdrant, Ollama running)
- Lint and test: `uv run ruff check . --fix && uv run ruff format . && uv run pytest -q`

## How the AI Lab works
- `rag/chunks.py` reads `content/` through `api/content.py` (the same reader as the pages)
  and makes one chunk per experience bullet (prefixed with company, title and dates), per
  profile section, per skill group and per project paragraph.
- `rag/ingest.py` embeds the chunks with nomic-embed-text ("search_document: " prefix) and
  recreates the Qdrant collection with deterministic IDs.
- `rag/search.py` fetches the top 5 chunks ("search_query: " prefix), plus every chunk of
  a company or project named in the question. `rag/answer.py` returns a fixed off-topic
  answer when the best score is below `min_score` (0.58, tuned with the evals), otherwise
  asks the LLM to answer from the chunks with [n] citations.
- `rag/grounding.py` checks that every tool or product named in an answer appears in a
  retrieved chunk or the question. If not: one stricter retry, then unsupported sentences
  are removed, else the fixed "Blessing's profile doesn't mention that." answer.

## Publishing
- GitHub Pages at https://adegbenleb.github.io/portfolio/, deployed by
  `.github/workflows/pages.yml` on every push to main (lint, test, build, deploy).
- `api/pages.py` defines the pages for both the live app and `build.py`. The static lab page
  (`lab_static.html`) shows the demo video and `evals/recorded_examples.json`, never the
  live status panel or the ask form.
- Never set up tunnels, port forwarding or anything that exposes this laptop (it is
  company-managed). The live AI Lab is for local demos only.

## Rules
- `content/` is the single source of truth. Pages and the RAG index never hold facts of their own.
- After editing anything in `content/`, re-run `uv run python -m rag.ingest`. Otherwise the
  pages show the new text but the AI Lab still answers from the old index.
- After changing chunking, the prompt, the threshold or the model, re-run the evals, then
  re-record the examples (and the demo video if the lab page changed).
- Never invent facts about Blessing. Everything must come from the CV or the content files.
  If something is missing or unclear, ask instead of guessing.
- Personal project only. No employer code, data, credentials or internal context.
- Never commit `.env` or any secret, and never put the real phone number anywhere in the repo,
  not even in tests (use made-up numbers).
