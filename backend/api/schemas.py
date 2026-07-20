"""
Pydantic request/response schemas for the API layer.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, UUID4

from constants import EventType, HighlightType


class MatchUploadResponse(BaseModel):
    match_id: UUID4
    filename: str
    status: str
    message: str


class HighlightJobRequest(BaseModel):
    match_id: UUID4
    highlight_type: HighlightType
    requested_events: list[EventType] = Field(..., min_length=1)


class HighlightJobResponse(BaseModel):
    job_id: UUID4
    match_id: UUID4
    status: str
    output_path: Optional[str] = None


class SegmentResult(BaseModel):
    segment_id: UUID4
    global_start_sec: float
    global_end_sec: float
    fused_confidence: float
    selected: bool
    rank: Optional[int] = None
    event_type: Optional[str] = None
    event_confidence: Optional[float] = None


class JobStatusResponse(BaseModel):
    job_id: UUID4
    status: str
    highlight_type: HighlightType
    requested_events: list[EventType]
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    segments: Optional[list[SegmentResult]] = None


class MatchStatusResponse(BaseModel):
    match_id: UUID4
    filename: str
    status: str
    duration_sec: Optional[float] = None
    fps: Optional[float] = None
    created_at: datetime


class HighlightJobSummary(BaseModel):
    job_id: UUID4
    status: str
    highlight_type: HighlightType
    requested_events: list[EventType]
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
