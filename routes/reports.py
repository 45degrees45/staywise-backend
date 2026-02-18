"""
routes/reports.py — REST API endpoints for the Staywise cloud backend.

Endpoints:
    POST  /api/publish                  Publish a new analysis (bot → backend)
    GET   /api/report/{slug}            Fetch a single report by slug
    GET   /api/feed                     Recent published reports
    GET   /api/check-duplicate/{hash}   Check if a reel URL was already published
"""

import hashlib
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session

from database import get_db
from models import Report
from schemas import FeedItem, PublishResponse, ReportCreate, ReportResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ── API key auth ──────────────────────────────────────────────────────────────
_API_KEY = os.getenv("API_KEY", "changeme")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(key: Optional[str] = Security(_api_key_header)) -> str:
    if key != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    return key


# ── Helpers ───────────────────────────────────────────────────────────────────

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _make_slug(claim: str) -> str:
    """Generate a short, URL-safe slug from the claim text."""
    cleaned = re.sub(r"[^a-z0-9 ]", "", claim.lower())
    words = cleaned.split()[:6]
    suffix = uuid.uuid4().hex[:6]
    return "-".join(words + [suffix])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/api/publish", response_model=PublishResponse, status_code=201)
def publish_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    _: str = Depends(_require_api_key),
):
    """
    Publish a new analysis report.
    Returns immediately if the reel URL was already published (idempotent).
    """
    url_hash = _url_hash(data.reel_url)

    existing = db.query(Report).filter(Report.url_hash == url_hash).first()
    if existing:
        logger.info("Duplicate publish attempt for hash %s", url_hash)
        return PublishResponse(slug=existing.slug, message="already_exists")

    slug = _make_slug(data.claim)
    report = Report(
        id=data.id,
        slug=slug,
        reel_url=data.reel_url,
        url_hash=url_hash,
        claim=data.claim,
        transcript_summary=data.transcript_summary,
        domain=data.domain,
        evidence_level=data.evidence_level,
        red_flags=data.red_flags,
        explanation=data.explanation,
        credibility_score=data.credibility_score,
        verdict=data.verdict,
        created_at=datetime.now(timezone.utc),
        published_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info("Published report: slug=%s, score=%d", slug, data.credibility_score)
    return PublishResponse(slug=report.slug, message="published")


@router.get("/api/report/{slug}", response_model=ReportResponse)
def get_report(slug: str, db: Session = Depends(get_db)):
    """Return a single published report by its slug."""
    report = db.query(Report).filter(Report.slug == slug).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/api/feed", response_model=list[FeedItem])
def get_feed(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Return the most recently published reports (newest first)."""
    limit = min(limit, 50)  # cap at 50 per page
    return (
        db.query(Report)
        .order_by(Report.published_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/api/check-duplicate/{url_hash}")
def check_duplicate(url_hash: str, db: Session = Depends(get_db)):
    """
    Return the existing report slug if this URL hash was already published.
    Used by the bot before starting a new analysis.
    """
    report = db.query(Report).filter(Report.url_hash == url_hash).first()
    if not report:
        raise HTTPException(status_code=404, detail="Not found.")
    return {"slug": report.slug}
