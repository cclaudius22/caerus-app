import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, ARRAY, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'founder', 'investor', or 'talent'
    avatar_url = Column(String(500), nullable=True)  # Profile photo URL
    push_token = Column(String(255), nullable=True)  # Expo push notification token
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    founder_profile = relationship("FounderProfile", back_populates="user", uselist=False)
    investor_profile = relationship("InvestorProfile", back_populates="user", uselist=False)
    talent_profile = relationship("TalentProfile", back_populates="user", uselist=False)
    startups = relationship("Startup", back_populates="founder")


class FounderProfile(Base):
    __tablename__ = "founder_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Profile info
    full_name = Column(String(255))
    company_name = Column(String(255))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    website = Column(String(500))
    profile_completed = Column(Boolean, default=False)

    # Onboarding preferences
    onboarding_completed = Column(Boolean, default=False)
    seeking_investor_types = Column(ARRAY(String))  # angel, vc, family_office, syndicate
    desired_check_size_min = Column(Integer)
    desired_check_size_max = Column(Integer)
    value_add_preferences = Column(ARRAY(String))  # network, operational, hands_off, domain_expertise

    # Talent view tracking (5/day limit)
    talent_views_today = Column(Integer, default=0)
    talent_views_reset_date = Column(Date, nullable=True)

    # Talent DM tracking (5/month limit)
    talent_dms_this_month = Column(Integer, default=0)
    talent_dms_reset_month = Column(Integer, nullable=True)  # Month number (1-12)
    talent_dms_reset_year = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="founder_profile")


class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Profile info
    full_name = Column(String(255))
    firm_name = Column(String(255))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    website = Column(String(500))
    profile_completed = Column(Boolean, default=False)

    # Onboarding preferences
    onboarding_completed = Column(Boolean, default=False)
    ticket_size_min = Column(Integer)
    ticket_size_max = Column(Integer)
    sectors = Column(ARRAY(String))  # SaaS, Fintech, HealthTech, etc.
    stages = Column(ARRAY(String))  # idea, pre_seed, seed, series_a
    geographies = Column(ARRAY(String))  # US, Europe, Asia, etc.
    investor_type = Column(String(50))  # angel, vc, family_office, syndicate

    # View tracking for freemium (startup pitches)
    free_views_remaining = Column(Integer, default=15)

    # Talent view tracking (5/day limit)
    talent_views_today = Column(Integer, default=0)
    talent_views_reset_date = Column(Date, nullable=True)

    # Talent DM tracking (5/month limit)
    talent_dms_this_month = Column(Integer, default=0)
    talent_dms_reset_month = Column(Integer, nullable=True)  # Month number (1-12)
    talent_dms_reset_year = Column(Integer, nullable=True)

    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="investor_profile")


class TalentProfile(Base):
    __tablename__ = "talent_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Basic info
    full_name = Column(String(255))

    # Approval status (CRITICAL for quality control)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    applied_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Compensation preference
    compensation_type = Column(String(20))  # equity_only, pay_equity, cash_only

    # Role-focused
    job_title_seeking = Column(String(255))  # "Senior Software Engineer"
    skills = Column(ARRAY(String))  # ["Python", "React", "ML"]
    experience_level = Column(String(20))  # junior, mid, senior, lead, executive
    salary_range_min = Column(Integer)
    salary_range_max = Column(Integer)
    availability = Column(String(20))  # immediate, 2_weeks, 1_month, 3_months

    # Portfolio-focused
    past_projects = Column(Text)  # JSON or text description
    portfolio_url = Column(String(500))
    certifications = Column(ARRAY(String))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    github_url = Column(String(500))
    website = Column(String(500))

    # Location
    location = Column(String(255))
    remote_preference = Column(String(20))  # remote_only, hybrid, onsite, flexible

    # Sector preferences (sectors they want to work in)
    preferred_sectors = Column(ARRAY(String))  # SaaS, Fintech, HealthTech, etc.

    # Onboarding & Profile
    onboarding_completed = Column(Boolean, default=False)
    profile_completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="talent_profile")
