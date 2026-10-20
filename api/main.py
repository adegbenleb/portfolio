"""FastAPI app that renders the portfolio pages from content/ at request time."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, StringConstraints

from api import pages
from api.pages import SITE_DIR, make_url
from rag import answer as rag_answer
from rag.config import settings
from rag.services import ServiceUnavailable, collection_size

HEALTH_TIMEOUT_SECONDS = 2.0

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warn, but never ingest automatically: indexing is an explicit step.
    try:
        if await run_in_threadpool(collection_size) == 0:
            logger.warning(
                "The Qdrant collection '%s' is empty. Run: uv run python -m rag.ingest",
                settings.collection,
            )
    except ServiceUnavailable as error:
        logger.warning("%s", error)
    yield


app = FastAPI(title="Blessing Adegbenle Portfolio", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=SITE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=SITE_DIR / "templates")


live_url = make_url("/")


def render(request: Request, key: str) -> HTMLResponse:
    template, page_context = pages.context(key, live_url)
    return templates.TemplateResponse(request, template, page_context)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "home")


@app.get("/experience", response_class=HTMLResponse)
def experience(request: Request):
    return render(request, "experience")


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return render(request, "projects")


@app.get("/skills", response_class=HTMLResponse)
def skills(request: Request):
    return render(request, "skills")


@app.get("/lab", response_class=HTMLResponse)
def lab(request: Request):
    return render(request, "lab")


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return render(request, "contact")


async def _responds(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.get(url)
    except httpx.HTTPError:
        return False
    return response.status_code < 500


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Check whether Ollama and Qdrant actually respond."""
    async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT_SECONDS) as client:
        ollama, qdrant = await asyncio.gather(
            _responds(client, settings.ollama_url), _responds(client, settings.qdrant_url)
        )
    return {
        "ollama": "online" if ollama else "offline",
        "qdrant": "online" if qdrant else "offline",
    }


class Question(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class Source(BaseModel):
    n: int
    label: str
    section: str
    snippet: str
    score: float


class Answer(BaseModel):
    answer: str
    sources: list[Source]
    seconds: float


@app.post("/api/ask")
def ask(body: Question) -> Answer:
    try:
        return Answer(**rag_answer.answer(body.question))
    except ServiceUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
