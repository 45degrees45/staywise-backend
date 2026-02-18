"""
schemas.py — Pydantic models for request validation and response serialisation.
"""

from datetime import datetime

from pydantic import BaseModel, field_validator


class ReportCreate(BaseModel):
    """Payload sent by the Telegram bot when publishing a report."""

    id: str
    reel_url: str
    claim: str
    transcript_summary: str
    domain: str
    evidence_level: str
    red_flags: list[str]
    explanation: str
    credibility_score: int
    verdict: str
    created_at: str  # ISO 8601 string from the bot

    @field_validator("credibility_score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, v))

    @field_validator("red_flags", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v


class ReportResponse(BaseModel):
    """Full report returned by GET /api/report/{slug}."""

    id: str
    slug: str
    reel_url: str
    claim: str
    transcript_summary: str
    domain: str
    evidence_level: str
    red_flags: list[str]
    explanation: str
    credibility_score: int
    verdict: str
    created_at: datetime
    published_at: datetime

    model_config = {"from_attributes": True}


class FeedItem(BaseModel):
    """Lightweight item returned by GET /api/feed."""

    slug: str
    claim: str
    domain: str
    credibility_score: int
    verdict: str
    published_at: datetime

    model_config = {"from_attributes": True}


class PublishResponse(BaseModel):
    slug: str
    message: str  # "published" | "already_exists"
