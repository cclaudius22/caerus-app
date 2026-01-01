from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User, TalentProfile, FounderProfile, InvestorProfile
from app.models.talent_pitch import TalentPitch, TalentPitchView
from app.api.deps import (
    get_current_user,
    get_current_talent,
    get_approved_talent,
    get_talent_viewer_access,
    TalentViewAccess
)
from app.services.gcs import GCSService

router = APIRouter()
storage_service = GCSService()


# Request/Response Schemas
class UploadURLRequest(BaseModel):
    filename: str
    content_type: str = "video/mp4"
    headline: Optional[str] = None


class UploadURLResponse(BaseModel):
    upload_url: str
    pitch_id: str


class PublishPitchRequest(BaseModel):
    duration_seconds: int
    headline: str


class TalentPitchResponse(BaseModel):
    id: str
    headline: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    status: str
    view_count: int
    created_at: datetime


class TalentFeedItem(BaseModel):
    id: str
    talent: dict
    headline: Optional[str]
    thumbnail_url: Optional[str]
    view_count: int
    created_at: datetime


@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(
    request: UploadURLRequest,
    current_user: User = Depends(get_approved_talent),
    db: Session = Depends(get_db)
):
    """Get a signed URL for video upload (approved talent only)."""
    # Check if talent already has an active pitch
    existing_pitch = db.query(TalentPitch).filter(
        TalentPitch.talent_id == current_user.id,
        TalentPitch.status.in_(["draft", "published"])
    ).first()

    if existing_pitch and existing_pitch.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a published pitch. Archive it first to create a new one."
        )

    # Generate signed upload URL
    upload_url, object_key = storage_service.generate_upload_url(
        filename=request.filename,
        content_type=request.content_type
    )

    # Create or update pitch record
    if existing_pitch and existing_pitch.status == "draft":
        pitch = existing_pitch
        pitch.video_url = object_key
        pitch.headline = request.headline
    else:
        pitch = TalentPitch(
            talent_id=current_user.id,
            video_url=object_key,
            headline=request.headline,
            status="draft"
        )
        db.add(pitch)

    db.commit()
    db.refresh(pitch)

    return UploadURLResponse(
        upload_url=upload_url,
        pitch_id=str(pitch.id)
    )


@router.post("/{pitch_id}/publish", response_model=TalentPitchResponse)
async def publish_pitch(
    pitch_id: str,
    request: PublishPitchRequest,
    current_user: User = Depends(get_approved_talent),
    db: Session = Depends(get_db)
):
    """Publish a pitch after video upload is complete."""
    pitch = db.query(TalentPitch).filter(
        TalentPitch.id == pitch_id,
        TalentPitch.talent_id == current_user.id
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    if pitch.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pitch is already published"
        )

    pitch.status = "published"
    pitch.duration_seconds = request.duration_seconds
    pitch.headline = request.headline
    db.commit()
    db.refresh(pitch)

    return TalentPitchResponse(
        id=str(pitch.id),
        headline=pitch.headline,
        video_url=None,  # Don't expose raw URL
        thumbnail_url=pitch.thumbnail_url,
        duration_seconds=pitch.duration_seconds,
        status=pitch.status,
        view_count=pitch.view_count,
        created_at=pitch.created_at
    )


@router.get("/feed", response_model=dict)
async def get_talent_feed(
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    experience_level: Optional[str] = Query(None),
    compensation_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    remote_preference: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    access: TalentViewAccess = Depends(get_talent_viewer_access),
    db: Session = Depends(get_db)
):
    """Get talent feed for founders/investors (requires 5/day views or subscription)."""
    if not access.can_view_talent:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Daily talent view limit reached. Subscribe for unlimited access."
        )

    # Only show approved talent with published pitches
    query = db.query(TalentPitch).join(
        TalentProfile, TalentPitch.talent_id == TalentProfile.user_id
    ).filter(
        TalentPitch.status == "published",
        TalentProfile.status == "approved"
    )

    # Apply filters
    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        query = query.filter(TalentProfile.skills.overlap(skill_list))
    if experience_level:
        query = query.filter(TalentProfile.experience_level == experience_level)
    if compensation_type:
        query = query.filter(TalentProfile.compensation_type == compensation_type)
    if location:
        query = query.filter(TalentProfile.location.ilike(f"%{location}%"))
    if remote_preference:
        query = query.filter(TalentProfile.remote_preference == remote_preference)

    total = query.count()
    pitches = query.order_by(TalentPitch.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for pitch in pitches:
        talent_profile = db.query(TalentProfile).filter(
            TalentProfile.user_id == pitch.talent_id
        ).first()

        items.append(TalentFeedItem(
            id=str(pitch.id),
            talent={
                "id": str(pitch.talent_id),
                "full_name": talent_profile.full_name if talent_profile else None,
                "job_title_seeking": talent_profile.job_title_seeking if talent_profile else None,
                "skills": talent_profile.skills if talent_profile else [],
                "experience_level": talent_profile.experience_level if talent_profile else None,
                "compensation_type": talent_profile.compensation_type if talent_profile else None,
                "location": talent_profile.location if talent_profile else None,
                "remote_preference": talent_profile.remote_preference if talent_profile else None,
            },
            headline=pitch.headline,
            thumbnail_url=pitch.thumbnail_url,
            view_count=pitch.view_count,
            created_at=pitch.created_at
        ))

    return {
        "pitches": items,
        "total": total,
        "access": {
            "has_subscription": access.has_subscription,
            "talent_views_remaining_today": access.talent_views_remaining_today
        }
    }


@router.get("/my-pitch")
async def get_my_pitch(
    current_user: User = Depends(get_current_talent),
    db: Session = Depends(get_db)
):
    """Get current talent's pitch."""
    pitch = db.query(TalentPitch).filter(
        TalentPitch.talent_id == current_user.id,
        TalentPitch.status.in_(["draft", "published"])
    ).first()

    if not pitch:
        return {"pitch": None}

    video_url = None
    if pitch.video_url and pitch.status == "published":
        video_url = storage_service.generate_download_url(pitch.video_url)

    return {
        "pitch": {
            "id": str(pitch.id),
            "headline": pitch.headline,
            "video_url": video_url,
            "thumbnail_url": pitch.thumbnail_url,
            "duration_seconds": pitch.duration_seconds,
            "status": pitch.status,
            "view_count": pitch.view_count,
            "created_at": pitch.created_at
        }
    }


@router.get("/dashboard")
async def get_talent_dashboard(
    current_user: User = Depends(get_current_talent),
    db: Session = Depends(get_db)
):
    """Get talent dashboard with stats."""
    profile = db.query(TalentProfile).filter(
        TalentProfile.user_id == current_user.id
    ).first()

    pitch = db.query(TalentPitch).filter(
        TalentPitch.talent_id == current_user.id,
        TalentPitch.status == "published"
    ).first()

    total_views = pitch.view_count if pitch else 0

    # Count unique viewers
    unique_viewers = 0
    if pitch:
        unique_viewers = db.query(func.count(TalentPitchView.viewer_id.distinct())).filter(
            TalentPitchView.pitch_id == pitch.id
        ).scalar() or 0

    # Count message threads
    from app.models.talent_qa import TalentQAThread
    messages_received = db.query(func.count(TalentQAThread.id)).filter(
        TalentQAThread.talent_id == current_user.id
    ).scalar() or 0

    return {
        "profile": {
            "status": profile.status if profile else "pending",
            "full_name": profile.full_name if profile else None,
            "job_title_seeking": profile.job_title_seeking if profile else None,
        },
        "pitch": {
            "id": str(pitch.id) if pitch else None,
            "status": pitch.status if pitch else None,
            "headline": pitch.headline if pitch else None,
        } if pitch else None,
        "stats": {
            "total_views": total_views,
            "unique_viewers": unique_viewers,
            "messages_received": messages_received
        }
    }


@router.get("/{pitch_id}")
async def get_pitch_detail(
    pitch_id: str,
    access: TalentViewAccess = Depends(get_talent_viewer_access),
    db: Session = Depends(get_db)
):
    """Get pitch detail with signed video URL."""
    if not access.can_view_talent:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Daily talent view limit reached. Subscribe for unlimited access."
        )

    pitch = db.query(TalentPitch).join(
        TalentProfile, TalentPitch.talent_id == TalentProfile.user_id
    ).filter(
        TalentPitch.id == pitch_id,
        TalentPitch.status == "published",
        TalentProfile.status == "approved"
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    talent_profile = db.query(TalentProfile).filter(
        TalentProfile.user_id == pitch.talent_id
    ).first()

    video_url = storage_service.generate_download_url(pitch.video_url)

    return {
        "id": str(pitch.id),
        "talent": {
            "id": str(pitch.talent_id),
            "full_name": talent_profile.full_name,
            "job_title_seeking": talent_profile.job_title_seeking,
            "skills": talent_profile.skills,
            "experience_level": talent_profile.experience_level,
            "compensation_type": talent_profile.compensation_type,
            "salary_range_min": talent_profile.salary_range_min,
            "salary_range_max": talent_profile.salary_range_max,
            "availability": talent_profile.availability,
            "location": talent_profile.location,
            "remote_preference": talent_profile.remote_preference,
            "linkedin_url": talent_profile.linkedin_url,
            "github_url": talent_profile.github_url,
            "portfolio_url": talent_profile.portfolio_url,
        },
        "headline": pitch.headline,
        "video_url": video_url,
        "duration_seconds": pitch.duration_seconds,
        "view_count": pitch.view_count,
        "created_at": pitch.created_at,
        "access": {
            "has_subscription": access.has_subscription,
            "talent_views_remaining_today": access.talent_views_remaining_today
        }
    }


@router.post("/{pitch_id}/view")
async def record_view(
    pitch_id: str,
    access: TalentViewAccess = Depends(get_talent_viewer_access),
    db: Session = Depends(get_db)
):
    """Record a pitch view and decrement daily views if not subscribed."""
    if not access.can_view_talent:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Daily talent view limit reached. Subscribe for unlimited access."
        )

    pitch = db.query(TalentPitch).filter(TalentPitch.id == pitch_id).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Check if already viewed by this user today
    existing_view = db.query(TalentPitchView).filter(
        TalentPitchView.pitch_id == pitch.id,
        TalentPitchView.viewer_id == access.user.id
    ).first()

    if existing_view:
        return {
            "viewed": True,
            "already_viewed": True,
            "talent_views_remaining_today": access.talent_views_remaining_today
        }

    # Record view
    view = TalentPitchView(
        pitch_id=pitch.id,
        viewer_id=access.user.id
    )
    db.add(view)

    # Increment view count
    pitch.view_count += 1

    # Decrement daily views if not subscribed
    new_views_remaining = access.talent_views_remaining_today
    if not access.has_subscription:
        if access.user.role == "investor":
            profile = db.query(InvestorProfile).filter(
                InvestorProfile.user_id == access.user.id
            ).first()
        else:
            profile = db.query(FounderProfile).filter(
                FounderProfile.user_id == access.user.id
            ).first()

        if profile:
            profile.talent_views_today = (profile.talent_views_today or 0) + 1
            new_views_remaining = 5 - profile.talent_views_today

    db.commit()

    return {
        "viewed": True,
        "already_viewed": False,
        "talent_views_remaining_today": new_views_remaining,
        "has_subscription": access.has_subscription
    }
