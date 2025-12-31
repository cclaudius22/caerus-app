import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class QuestionTemplate(Base):
    """Pre-saved question templates for investors to quickly send to founders."""

    __tablename__ = "question_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)  # System default templates
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    investor = relationship("User", backref="question_templates")


# Default question templates that every investor gets
DEFAULT_QUESTIONS = [
    "What's your current MRR/ARR?",
    "How did you validate the problem?",
    "What's your unfair advantage?",
    "Who are your main competitors?",
    "What's your go-to-market strategy?",
    "How are you planning to use the funds?",
    "What's your customer acquisition cost?",
    "What milestones do you expect to hit in the next 12 months?",
]
