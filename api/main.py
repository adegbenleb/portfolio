"""FastAPI app that renders the portfolio pages from content/ at request time."""

import asyncio
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from api import content

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:16335")
HEALTH_TIMEOUT_SECONDS = 2.0

NAV = [
    ("/", "home", "Home"),
    ("/experience", "experience", "Experience"),
    ("/projects", "projects", "Projects"),
    ("/skills", "skills", "Skills"),
    ("/lab", "lab", "AI Lab"),
    ("/contact", "contact", "Contact"),
]

app = FastAPI(title="Blessing Adegbenle Portfolio")
app.mount("/static", StaticFiles(directory=SITE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=SITE_DIR / "templates")


def render(request: Request, template: str, active: str, **context) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        template,
        {"nav": NAV, "active": active, "profile": content.load_profile(), **context},
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "home.html", "home")


@app.get("/experience", response_class=HTMLResponse)
def experience(request: Request):
    return render(request, "experience.html", "experience", roles=content.load_experience())


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return render(request, "projects.html", "projects", projects=content.load_projects())


@app.get("/skills", response_class=HTMLResponse)
def skills(request: Request):
    return render(request, "skills.html", "skills", groups=content.load_skills())


@app.get("/lab", response_class=HTMLResponse)
def lab(request: Request):
    return render(request, "lab.html", "lab")


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return render(request, "contact.html", "contact")


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
            _responds(client, OLLAMA_URL), _responds(client, QDRANT_URL)
        )
    return {
        "ollama": "online" if ollama else "offline",
        "qdrant": "online" if qdrant else "offline",
    }


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def ask(question: Question):
    # The RAG backend is the next step. Until then, say so honestly.
    raise HTTPException(status_code=503, detail="The AI Lab is coming soon.")
