import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Startup(Base):
    __tablename__ = "startups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    tagline = Column(String(500))
    website = Column(String(500))
    sector = Column(String(100))
    stage = Column(String(50))  # 'idea', 'pre_seed', 'seed', 'series_a'
    location = Column(String(255))
    round_size_min = Column(Integer)
    round_size_max = Column(Integer)
    traction_bullets = Column(ARRAY(String))
    logo_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    founder = relationship("User", back_populates="startups")
    pitches = relationship("Pitch", back_populates="startup", cascade="all, delete-orphan")
