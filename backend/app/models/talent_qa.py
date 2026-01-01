import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TalentQAThread(Base):
    """Thread between a recruiter (founder/investor) and a talent."""
    __tablename__ = "talent_qa_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id = Column(UUID(as_uuid=True), ForeignKey("talent_pitches.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pitch = relationship("TalentPitch", backref="qa_threads")
    recruiter = relationship("User", foreign_keys=[recruiter_id], backref="talent_threads_as_recruiter")
    talent = relationship("User", foreign_keys=[talent_id], backref="talent_threads_as_talent")
    messages = relationship("TalentQAMessage", back_populates="thread", cascade="all, delete-orphan")


class TalentQAMessage(Base):
    """Message within a talent Q&A thread."""
    __tablename__ = "talent_qa_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("talent_qa_threads.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Message content
    message_type = Column(String(20), default="text")  # text, video
    content = Column(Text)
    video_url = Column(String(500), nullable=True)  # For video messages

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    thread = relationship("TalentQAThread", back_populates="messages")
    sender = relationship("User", backref="talent_messages_sent")
