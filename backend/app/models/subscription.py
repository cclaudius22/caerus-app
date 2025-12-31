import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_type = Column(String(20), nullable=False)  # 'monthly' or 'annual'
    apple_transaction_id = Column(String(255), unique=True)
    apple_original_transaction_id = Column(String(255))
    status = Column(String(20), default="active")  # 'active', 'expired', 'cancelled'
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PitchUnlock(Base):
    __tablename__ = "pitch_unlocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    startup_id = Column(UUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False)
    founder_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    apple_transaction_id = Column(String(255), unique=True, nullable=False)
    product_id = Column(String(100), nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
