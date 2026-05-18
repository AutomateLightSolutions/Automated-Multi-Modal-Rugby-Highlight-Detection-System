"""
SQLAlchemy ORM models for matches, segments, module outputs, fusion results, and highlight jobs.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
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
    fused_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="fusion_results")
    match: Mapped["Match"] = relationship("Match", back_populates="fusion_results")


class HighlightJob(Base):
    __tablename__ = "highlight_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    user_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    output_path: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="highlight_jobs")
