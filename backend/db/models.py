"""
SQLAlchemy ORM models for matches, segments, module outputs, fusion results, and highlight jobs.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="uploaded")
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 1 = legacy fixed-30s-chunk pipeline, 2 = tiled SlowFast + 4s-grid fusion pipeline.
    pipeline_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # |audio_duration - video_duration| from extraction; both tracks must come from the
    # same untrimmed upload or every downstream absolute timestamp is wrong.
    audio_offset_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Full word-timestamped Whisper transcript (list of {word, start, end, confidence}),
    # persisted once so the admin page can render it and re-scoring is free.
    transcript: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # Per-module processing progress, updated periodically (not just once at
    # the end) so the frontend has something to show during "processing":
    # {"visual": {"status": "running", "done": 340, "total": 803},
    #  "audio": {"status": "pending"}, "commentary": {"status": "pending"}}
    progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    segments: Mapped[list["Segment"]] = relationship(
        "Segment", back_populates="match", cascade="all, delete-orphan"
    )
    highlight_jobs: Mapped[list["HighlightJob"]] = relationship(
        "HighlightJob", back_populates="match", cascade="all, delete-orphan"
    )
    fusion_results: Mapped[list["FusionResult"]] = relationship(
        "FusionResult", back_populates="match", cascade="all, delete-orphan"
    )
    module_predictions: Mapped[list["ModulePrediction"]] = relationship(
        "ModulePrediction", back_populates="match", cascade="all, delete-orphan"
    )
    visual_window_predictions: Mapped[list["VisualWindowPrediction"]] = relationship(
        "VisualWindowPrediction", back_populates="match", cascade="all, delete-orphan"
    )
    fusion_runs: Mapped[list["FusionRun"]] = relationship(
        "FusionRun", back_populates="match", cascade="all, delete-orphan"
    )


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    global_start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    global_end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    video_chunk_path: Mapped[str | None] = mapped_column(String, nullable=True)
    audio_chunk_path: Mapped[str | None] = mapped_column(String, nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="segments")
    module_outputs: Mapped[list["ModuleOutput"]] = relationship(
        "ModuleOutput", back_populates="segment", cascade="all, delete-orphan"
    )
    fusion_results: Mapped[list["FusionResult"]] = relationship(
        "FusionResult", back_populates="segment", cascade="all, delete-orphan"
    )


class ModuleOutput(Base):
    __tablename__ = "module_outputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False
    )
    module_name: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String, nullable=True)
    event_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="module_outputs")


class FusionResult(Base):
    __tablename__ = "fusion_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("highlight_jobs.id"), nullable=False
    )
    fused_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="fusion_results")
    match: Mapped["Match"] = relationship("Match", back_populates="fusion_results")
    job: Mapped["HighlightJob"] = relationship("HighlightJob", back_populates="fusion_results")


class HighlightJob(Base):
    __tablename__ = "highlight_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    highlight_type: Mapped[str] = mapped_column(String, nullable=False)
    requested_events: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    output_path: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # v2 (fusion_cell-based) jobs only — null for legacy v1 jobs.
    fusion_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fusion_runs.id"), nullable=True
    )
    # Snapshot of the profile's actual selection parameters used, so results
    # stay interpretable even if PROFILES/constants change later.
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    clip_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="highlight_jobs")
    fusion_results: Mapped[list["FusionResult"]] = relationship(
        "FusionResult", back_populates="job", cascade="all, delete-orphan"
    )
    fusion_run: Mapped["FusionRun | None"] = relationship("FusionRun")
    highlight_clips: Mapped[list["HighlightClip"]] = relationship(
        "HighlightClip", back_populates="job", cascade="all, delete-orphan"
    )


class ModulePrediction(Base):
    """
    One row per module per output cell/tile — the unified timeline the admin
    page and fusion both read. Visual writes window_sec=8 rows (tile-indexed);
    commentary/audio write window_sec=4 rows (4s-grid-cell-indexed) once P1 lands.
    """
    __tablename__ = "module_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(String, nullable=False)  # "visual" | "commentary" | "audio"
    window_sec: Mapped[float] = mapped_column(Float, nullable=False)
    index_in_module: Mapped[int] = mapped_column(Integer, nullable=False)
    global_start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    global_end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_event: Mapped[str | None] = mapped_column(String, nullable=True)
    event_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    highlight_score: Mapped[float] = mapped_column(Float, nullable=False)
    event_probs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="module_predictions")

    __table_args__ = (
        UniqueConstraint(
            "match_id", "module", "global_start_sec",
            name="uq_module_prediction_match_module_start",
        ),
        Index("ix_module_prediction_match_module_start", "match_id", "module", "global_start_sec"),
    )


class VisualWindowPrediction(Base):
    """
    Audit trail for the visual module's per-window (8s/16s/32s) raw predictions
    before class-support masking and merging. Kept so masked-out votes stay
    inspectable — the merge in module_predictions is only auditable if these survive.
    """
    __tablename__ = "visual_window_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    tile_index: Mapped[int] = mapped_column(Integer, nullable=False)
    window_sec: Mapped[int] = mapped_column(Integer, nullable=False)  # 8, 16, or 32
    clip_start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    clip_end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    raw_event: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    softmax: Mapped[dict] = mapped_column(JSON, nullable=False)
    masked_mass: Mapped[float] = mapped_column(Float, nullable=False)
    dropped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    drop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="visual_window_predictions")

    __table_args__ = (
        Index("ix_visual_window_prediction_match_tile", "match_id", "tile_index"),
    )


class FusionRun(Base):
    """
    One fusion pass over a match's module_predictions, on the 4s grid.
    Runs automatically once processing completes; re-fusing with different
    weights creates a NEW run (never overwrites) and flips is_active — this
    is what lets weights be tuned later without reprocessing any ML.
    """
    __tablename__ = "fusion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    grid_sec: Mapped[float] = mapped_column(Float, nullable=False)
    sigmoid_k: Mapped[float] = mapped_column(Float, nullable=False)
    commentary_lag_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="fusion_runs")
    cells: Mapped[list["FusionCell"]] = relationship(
        "FusionCell", back_populates="fusion_run", cascade="all, delete-orphan"
    )


class FusionCell(Base):
    """One fused prediction per 4s grid cell for one fusion_run."""
    __tablename__ = "fusion_cells"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fusion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fusion_runs.id"), nullable=False
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    cell_index: Mapped[int] = mapped_column(Integer, nullable=False)
    global_start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    global_end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    fused_event: Mapped[str] = mapped_column(String, nullable=False)
    fused_event_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    fused_score: Mapped[float] = mapped_column(Float, nullable=False)
    visual_tile_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # {module: {event, event_confidence, highlight_score, sigmoid_score, weight, present}}
    contributions: Mapped[dict] = mapped_column(JSON, nullable=False)
    modules_present: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    disagreement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    fusion_run: Mapped["FusionRun"] = relationship("FusionRun", back_populates="cells")

    __table_args__ = (
        UniqueConstraint("fusion_run_id", "cell_index", name="uq_fusion_cell_run_index"),
        Index("ix_fusion_cell_run_index", "fusion_run_id", "cell_index"),
    )


class HighlightClip(Base):
    """One selected clip within a highlight job (pipeline v2)."""
    __tablename__ = "highlight_clips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("highlight_jobs.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    global_start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    global_end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    event: Mapped[str] = mapped_column(String, nullable=False)
    peak_score: Mapped[float] = mapped_column(Float, nullable=False)
    mean_score: Mapped[float] = mapped_column(Float, nullable=False)
    source_cell_start: Mapped[int] = mapped_column(Integer, nullable=False)
    source_cell_end: Mapped[int] = mapped_column(Integer, nullable=False)
    cells: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    was_expanded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    was_trimmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    job: Mapped["HighlightJob"] = relationship("HighlightJob", back_populates="highlight_clips")

    __table_args__ = (
        Index("ix_highlight_clip_job_rank", "job_id", "rank"),
    )
