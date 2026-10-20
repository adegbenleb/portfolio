---
title: AI Lab
---

## How it works

1. **Content files.** Everything starts with a few Markdown files: my profile, skills, one file per role and one per project. The website pages are built from the same files, so the AI Lab and the site cannot disagree.
2. **Chunking.** The files are split by meaning, not by length: one chunk per CV bullet with the company, title and dates in front, and one per profile section, skill group, case study and project paragraph.
3. **Embeddings.** Each chunk is turned into a vector with nomic-embed-text, running locally through Ollama.
4. **Qdrant.** The vectors are stored in Qdrant. A question is embedded the same way, and the five closest chunks are fetched. If the question names a company or project, all of its chunks are added.
5. **LLM.** A local Llama 3.1 model writes a short answer from those chunks only and cites them as [1], [2].
6. **Guardrails.** Questions that match nothing well get a fixed answer without calling the LLM. The question is treated as data, not as instructions. After the answer is written, a check makes sure every tool it names really appears in the sources.
7. **Evals.** A set of test questions with required and forbidden facts, off-topic questions and a prompt injection runs after every change, and is used to compare local models.

## Roadmap

These are planned, not built yet.

- **Planned:** catch unsupported general claims, not only unknown tool names.
- **Planned:** stream answers word by word instead of waiting for the full answer.
- **Planned:** hybrid search that combines keyword matching with vector search.
- **Planned:** follow-up questions that remember the previous answer.

## API reference

The live AI Lab runs on my own machine, so this API is available during demos, not on the published site.

**POST /api/ask**

Request:

```json
{"question": "What did he do at Miele?"}
```

The question must be 1 to 500 characters. Response:

```json
{
  "answer": "Blessing worked as a Data Engineer at Miele ... [1, 2]",
  "sources": [
    {"n": 1, "label": "Miele", "section": "experience", "snippet": "Miele, Data Engineer, ...", "score": 0.72}
  ],
  "seconds": 7.6
}
```

Returns 422 for an empty or too long question, and 503 with a message naming the service if Ollama or Qdrant is down.

**GET /api/health**

```json
{"ollama": "online", "qdrant": "online"}
```
