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

## Planned ports
- API: 18600
- Qdrant: 16335
- Ollama: 11434

## Rules
- `content/` is the single source of truth. Pages and the RAG index never hold facts of their own.
- Never invent facts about Blessing. Everything must come from the CV or the content files.
  If something is missing or unclear, ask instead of guessing.
- Personal project only. No employer code, data, credentials or internal context.
- Never commit `.env` or any secret.
