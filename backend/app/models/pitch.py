import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Pitch(Base):
    __tablename__ = "pitches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    startup_id = Column(UUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # '30s_free' or '5min_paid'
    video_url = Column(String(1000), nullable=False)  # GCS blob path
    thumbnail_url = Column(String(1000))
    duration_seconds = Column(Integer)
    status = Column(String(20), default="draft")  # 'draft', 'published', 'archived'
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="pitches")
    views = relationship("PitchView", back_populates="pitch", cascade="all, delete-orphan")
    qa_threads = relationship("QAThread", back_populates="pitch", cascade="all, delete-orphan")


class PitchView(Base):
    __tablename__ = "pitch_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id = Column(UUID(as_uuid=True), ForeignKey("pitches.id", ondelete="CASCADE"), nullable=False)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    viewed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pitch = relationship("Pitch", back_populates="views")
