import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TalentPitch(Base):
    __tablename__ = "talent_pitches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Video content
    video_url = Column(String(500))  # GCS object key
    thumbnail_url = Column(String(500))
    duration_seconds = Column(Integer)

    # Pitch info
    headline = Column(String(255))  # "Full-stack engineer with 5 years startup experience"
    status = Column(String(20), default="draft")  # draft, published, archived

    # Stats
    view_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    talent = relationship("User", backref="talent_pitches")
    views = relationship("TalentPitchView", back_populates="pitch", cascade="all, delete-orphan")


class TalentPitchView(Base):
    __tablename__ = "talent_pitch_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id = Column(UUID(as_uuid=True), ForeignKey("talent_pitches.id", ondelete="CASCADE"), nullable=False)
    viewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pitch = relationship("TalentPitch", back_populates="views")
    viewer = relationship("User", backref="talent_pitch_views")
