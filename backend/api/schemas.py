"""
Pydantic request/response schemas for the API layer.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


class MatchUploadResponse(BaseModel):
    match_id: UUID4
    filename: str
    status: str
    message: str


class HighlightJobRequest(BaseModel):
    match_id: UUID4
    user_filter: Optional[str] = None
    # user_filter examples: "scrums only", "tries only", "lineouts only"
    # Pass None for full automatic highlight


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
