import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class QAThread(Base):
    __tablename__ = "qa_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id = Column(UUID(as_uuid=True), ForeignKey("pitches.id", ondelete="CASCADE"), nullable=False)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    startup_id = Column(UUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pitch = relationship("Pitch", back_populates="qa_threads")
    messages = relationship("QAMessage", back_populates="thread", cascade="all, delete-orphan")

    # Unique constraint: one thread per investor-pitch pair
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class QAMessage(Base):
    __tablename__ = "qa_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("qa_threads.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(20), default="text")  # 'text' or 'video'
    content = Column(Text)
    video_url = Column(String(1000))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    thread = relationship("QAThread", back_populates="messages")
