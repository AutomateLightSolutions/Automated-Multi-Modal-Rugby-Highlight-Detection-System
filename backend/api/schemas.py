"""
Pydantic request/response schemas for the API layer.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, UUID4

from constants import EventClass, HighlightType


class MatchUploadResponse(BaseModel):
    match_id: UUID4
    filename: str
    status: str
    message: str


class HighlightJobRequest(BaseModel):
    match_id: UUID4
    highlight_type: HighlightType
    requested_events: list[EventClass] = Field(..., min_length=1)


class HighlightJobResponse(BaseModel):
    job_id: UUID4
    match_id: UUID4
    status: str
    output_path: Optional[str] = None


class HighlightClipResult(BaseModel):
    rank: int
    global_start_sec: float
    global_end_sec: float
    duration_sec: float
    event: str
    peak_score: float
    mean_score: float
    was_expanded: bool
    was_trimmed: bool


class JobStatusResponse(BaseModel):
    job_id: UUID4
    status: str
    highlight_type: HighlightType
    requested_events: list[EventClass]
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    clips: Optional[list[HighlightClipResult]] = None


class MatchStatusResponse(BaseModel):
    match_id: UUID4
    filename: str
    status: str
    duration_sec: Optional[float] = None
    fps: Optional[float] = None
    created_at: datetime
    progress: Optional[dict] = None


class HighlightJobSummary(BaseModel):
    job_id: UUID4
    status: str
    highlight_type: HighlightType
    requested_events: list[EventClass]
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


