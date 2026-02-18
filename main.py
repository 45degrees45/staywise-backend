"""
main.py — Staywise FastAPI cloud backend.

Serves:
  - REST API for the Telegram bot (publish, fetch, feed, duplicate-check)
  - Server-side rendered HTML pages for the public website
"""

import os
from contextlib import asynccontextmanager
from urllib.parse import quote as urlquote

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Report
from routes.reports import router

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# ── Startup ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Staywise API",
    version="1.0.0",
    description="Scientific credibility analysis for Instagram Reels",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Jinja2 custom filters ─────────────────────────────────────────────────────

def _verdict_class(verdict: str) -> str:
    v = verdict.lower()
    if "true" in v or "green" in v:
        return "green"
    if "mislead" in v or "red" in v:
        return "red"
    return "yellow"


def _score_class(score: int) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"


templates.env.filters["verdict_class"] = _verdict_class
templates.env.filters["score_class"] = _score_class
templates.env.filters["urlencode"] = lambda s: urlquote(str(s), safe="")

# ── Include API router ────────────────────────────────────────────────────────

app.include_router(router)

# ── HTML pages ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    reports = (
        db.query(Report)
        .order_by(Report.published_at.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "reports": reports},
    )


@app.get("/report/{slug}", response_class=HTMLResponse)
async def report_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.slug == slug).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    report_url = f"{BASE_URL}/report/{slug}"
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "report": report,
            "report_url": report_url,
        },
    )
