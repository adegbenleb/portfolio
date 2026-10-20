---
title: "Portfolio and AI Lab"
type: personal project
category: Personal
start: 2026-10
end: present
status: live
result: 15 of 15 eval cases pass with llama3.1:8b
github: github.com/adegbenleb/portfolio
url: https://adegbenleb.github.io/portfolio/
tags: [Python, FastAPI, Jinja2, RAG, Qdrant, Ollama, pytest, GitHub Actions, GitHub Pages]
---

This website. Every page is built from a few Markdown files that match my CV, and the same files feed an AI Lab that answers questions about my experience with retrieval-augmented generation.

The content is split into chunks by meaning, one per CV bullet, skill group and project paragraph, embedded with nomic-embed-text and stored in Qdrant. A local Llama 3.1 model running through Ollama answers from the retrieved chunks only and cites them as numbered sources.

Guardrails keep it honest: a similarity threshold sends off-topic questions to a fixed answer without calling the LLM, the system prompt treats every question as data, and a check after each answer makes sure every tool it names appears in the sources. An evaluation set with factual, off-topic and prompt injection cases is used to tune the threshold and compare local models.

The site is rendered with FastAPI and Jinja2 locally and published as static pages on GitHub Pages by a GitHub Actions workflow that lints, tests and builds on every push. The live AI Lab runs on my own machine for demos.
