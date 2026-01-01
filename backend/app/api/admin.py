from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, TalentProfile
from app.api.deps import get_current_user

router = APIRouter()

# Admin user IDs (in production, use a proper admin role system)
ADMIN_USER_IDS = set()  # Add admin user UUIDs here


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is an admin."""
    # For now, check if user ID is in admin list or email ends with specific domain
    # In production, add proper admin role to User model
    if str(current_user.id) not in ADMIN_USER_IDS and not current_user.email.endswith("@caerus.app"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class TalentApprovalResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: Optional[str]
    status: str
    applied_at: datetime
    job_title_seeking: Optional[str]
    skills: Optional[list]
    experience_level: Optional[str]
    compensation_type: Optional[str]
    linkedin_url: Optional[str]
    location: Optional[str]


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/talent/pending")
async def list_pending_talent(
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all pending talent applications."""
    query = db.query(TalentProfile).filter(
        TalentProfile.status == "pending",
        TalentProfile.onboarding_completed == True
    )

    total = query.count()

    profiles = query.order_by(TalentProfile.applied_at.desc()).offset(offset).limit(limit).all()

    items = []
    for profile in profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()
        items.append({
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "email": user.email if user else None,
            "full_name": profile.full_name,
            "status": profile.status,
            "applied_at": profile.applied_at,
            "job_title_seeking": profile.job_title_seeking,
            "skills": profile.skills,
            "experience_level": profile.experience_level,
            "compensation_type": profile.compensation_type,
            "linkedin_url": profile.linkedin_url,
            "location": profile.location,
        })

    return {
        "pending": items,
        "total": total
    }


@router.post("/talent/{profile_id}/approve")
async def approve_talent(
    profile_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a talent application."""
    profile = db.query(TalentProfile).filter(TalentProfile.id == profile_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talent profile not found"
        )

    if profile.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile is already {profile.status}"
        )

    profile.status = "approved"
    profile.approved_at = datetime.utcnow()
    profile.rejection_reason = None

    db.commit()
    db.refresh(profile)

    return {
        "message": "Talent approved successfully",
        "profile": {
            "id": str(profile.id),
            "status": profile.status,
            "approved_at": profile.approved_at
        }
    }


@router.post("/talent/{profile_id}/reject")
async def reject_talent(
    profile_id: str,
    request: RejectRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reject a talent application."""
    profile = db.query(TalentProfile).filter(TalentProfile.id == profile_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talent profile not found"
        )

    if profile.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile is already {profile.status}"
        )

    profile.status = "rejected"
    profile.rejection_reason = request.reason

    db.commit()
    db.refresh(profile)

    return {
        "message": "Talent rejected",
        "profile": {
            "id": str(profile.id),
            "status": profile.status,
            "rejection_reason": profile.rejection_reason
        }
    }


@router.get("/talent/stats")
async def get_talent_stats(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get talent application statistics."""
    pending = db.query(func.count(TalentProfile.id)).filter(
        TalentProfile.status == "pending"
    ).scalar() or 0

    approved = db.query(func.count(TalentProfile.id)).filter(
        TalentProfile.status == "approved"
    ).scalar() or 0

    rejected = db.query(func.count(TalentProfile.id)).filter(
        TalentProfile.status == "rejected"
    ).scalar() or 0

    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total": pending + approved + rejected
    }
