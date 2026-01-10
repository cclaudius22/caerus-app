from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User, InvestorProfile
from app.models.startup import Startup
from app.models.pitch import Pitch, PitchView
from app.models.subscription import PitchUnlock
from app.api.deps import get_current_user, get_current_founder, get_subscribed_investor, get_investor_with_access, InvestorAccess
from app.services.gcs import GCSService

router = APIRouter()
storage_service = GCSService()


# Request/Response Schemas
class UploadURLRequest(BaseModel):
    startup_id: str
    type: str  # '30s_free' or '5min_paid'
    filename: str
    content_type: str = "video/mp4"


class UploadURLResponse(BaseModel):
    upload_url: str
    video_id: str


class PublishPitchRequest(BaseModel):
    duration_seconds: int


class PitchResponse(BaseModel):
    id: str
    startup_id: str
    type: str
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    status: str
    view_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PitchFeedItem(BaseModel):
    id: str
    startup: dict
    type: str
    thumbnail_url: Optional[str]
    view_count: int
    created_at: datetime


class FounderDashboard(BaseModel):
    startups: List[dict]
    stats: dict


@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(
    request: UploadURLRequest,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Get a signed URL for video upload."""
    # Verify user owns the startup
    startup = db.query(Startup).filter(
        Startup.id == request.startup_id,
        Startup.founder_id == current_user.id
    ).first()

    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup not found"
        )

    # Validate pitch type
    if request.type not in ["30s_free", "5min_paid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be '30s_free' or '5min_paid'"
        )

    # Check if 5min pitch requires unlock
    if request.type == "5min_paid":
        unlock = db.query(PitchUnlock).filter(
            PitchUnlock.startup_id == request.startup_id,
            PitchUnlock.founder_id == current_user.id
        ).first()

        if not unlock:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="5-minute pitch requires payment"
            )

    # Generate signed upload URL
    upload_url, object_key = storage_service.generate_upload_url(
        filename=request.filename,
        content_type=request.content_type
    )

    # Create pitch record
    pitch = Pitch(
        startup_id=request.startup_id,
        type=request.type,
        video_url=object_key,
        status="draft"
    )
    db.add(pitch)
    db.commit()
    db.refresh(pitch)

    return UploadURLResponse(
        upload_url=upload_url,
        video_id=str(pitch.id)
    )


@router.post("/{pitch_id}/publish", response_model=PitchResponse)
async def publish_pitch(
    pitch_id: str,
    request: PublishPitchRequest,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Publish a pitch after video upload is complete."""
    pitch = db.query(Pitch).join(Startup).filter(
        Pitch.id == pitch_id,
        Startup.founder_id == current_user.id
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Auto-archive any existing published pitches of the same type for this startup
    existing_published = db.query(Pitch).filter(
        Pitch.startup_id == pitch.startup_id,
        Pitch.type == pitch.type,
        Pitch.status == "published",
        Pitch.id != pitch.id
    ).all()

    for existing in existing_published:
        existing.status = "archived"

    pitch.status = "published"
    pitch.duration_seconds = request.duration_seconds
    db.commit()
    db.refresh(pitch)

    return PitchResponse(
        id=str(pitch.id),
        startup_id=str(pitch.startup_id),
        type=pitch.type,
        video_url=None,  # Don't expose raw URL
        thumbnail_url=pitch.thumbnail_url,
        duration_seconds=pitch.duration_seconds,
        status=pitch.status,
        view_count=pitch.view_count,
        created_at=pitch.created_at
    )


@router.get("/feed", response_model=dict)
async def get_pitch_feed(
    sector: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    access: InvestorAccess = Depends(get_investor_with_access),
    db: Session = Depends(get_db)
):
    """Get pitch feed for investors (requires subscription or free views)."""
    # Check if investor can view pitches
    if not access.can_view:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No free views remaining. Subscription required."
        )

    query = db.query(Pitch).join(Startup).filter(Pitch.status == "published")

    # Apply filters
    if sector:
        query = query.filter(Startup.sectors.any(sector))
    if stage:
        query = query.filter(Startup.stage == stage)
    if location:
        query = query.filter(Startup.location.ilike(f"%{location}%"))

    # Get total count
    total = query.count()

    # Get paginated results
    pitches = query.order_by(Pitch.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for pitch in pitches:
        items.append(PitchFeedItem(
            id=str(pitch.id),
            startup={
                "id": str(pitch.startup.id),
                "name": pitch.startup.name,
                "tagline": pitch.startup.tagline,
                "sectors": pitch.startup.sectors,
                "stage": pitch.startup.stage,
                "location": pitch.startup.location,
                "logo_url": pitch.startup.logo_url
            },
            type=pitch.type,
            thumbnail_url=pitch.thumbnail_url,
            view_count=pitch.view_count,
            created_at=pitch.created_at
        ))

    return {
        "pitches": items,
        "total": total,
        "access": {
            "has_subscription": access.has_subscription,
            "free_views_remaining": access.free_views_remaining
        }
    }


@router.get("/{pitch_id}")
async def get_pitch_detail(
    pitch_id: str,
    access: InvestorAccess = Depends(get_investor_with_access),
    db: Session = Depends(get_db)
):
    """Get pitch detail with signed video URL (requires subscription or free views)."""
    # Check if investor can view
    if not access.can_view:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No free views remaining. Subscription required."
        )

    pitch = db.query(Pitch).filter(
        Pitch.id == pitch_id,
        Pitch.status == "published"
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Generate signed download URL
    video_url = storage_service.generate_download_url(pitch.video_url)

    return {
        "id": str(pitch.id),
        "startup": {
            "id": str(pitch.startup.id),
            "name": pitch.startup.name,
            "tagline": pitch.startup.tagline,
            "sectors": pitch.startup.sectors,
            "stage": pitch.startup.stage,
            "location": pitch.startup.location,
            "website": pitch.startup.website,
            "round_size_min": pitch.startup.round_size_min,
            "round_size_max": pitch.startup.round_size_max,
            "traction_bullets": pitch.startup.traction_bullets,
            "logo_url": pitch.startup.logo_url
        },
        "type": pitch.type,
        "video_url": video_url,
        "duration_seconds": pitch.duration_seconds,
        "view_count": pitch.view_count,
        "created_at": pitch.created_at,
        "access": {
            "has_subscription": access.has_subscription,
            "free_views_remaining": access.free_views_remaining
        }
    }


@router.post("/{pitch_id}/view")
async def record_view(
    pitch_id: str,
    access: InvestorAccess = Depends(get_investor_with_access),
    db: Session = Depends(get_db)
):
    """Record a pitch view and decrement free views if not subscribed."""
    # Check if investor can view
    if not access.can_view:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No free views remaining. Subscription required."
        )

    pitch = db.query(Pitch).filter(Pitch.id == pitch_id).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Check if already viewed by this investor (don't double-count)
    existing_view = db.query(PitchView).filter(
        PitchView.pitch_id == pitch.id,
        PitchView.investor_id == access.user.id
    ).first()

    if existing_view:
        # Already viewed, don't decrement free views again
        return {
            "viewed": True,
            "already_viewed": True,
            "free_views_remaining": access.free_views_remaining
        }

    # Record view
    view = PitchView(
        pitch_id=pitch.id,
        investor_id=access.user.id
    )
    db.add(view)

    # Increment view count on pitch
    pitch.view_count += 1

    # Decrement free views if not subscribed
    new_free_views = access.free_views_remaining
    if not access.has_subscription and access.free_views_remaining > 0:
        profile = db.query(InvestorProfile).filter(
            InvestorProfile.user_id == access.user.id
        ).first()
        if profile:
            profile.free_views_remaining = max(0, profile.free_views_remaining - 1)
            new_free_views = profile.free_views_remaining

    db.commit()

    return {
        "viewed": True,
        "already_viewed": False,
        "free_views_remaining": new_free_views,
        "has_subscription": access.has_subscription
    }


@router.get("/founder/dashboard", response_model=FounderDashboard)
async def get_founder_dashboard(
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Get founder dashboard with stats."""
    startups = db.query(Startup).filter(Startup.founder_id == current_user.id).all()

    startup_data = []
    total_views = 0
    unique_investors = set()
    questions_received = 0

    for startup in startups:
        pitches = db.query(Pitch).filter(Pitch.startup_id == startup.id).all()

        pitch_list = []
        for pitch in pitches:
            total_views += pitch.view_count

            # Get unique investors who viewed
            views = db.query(PitchView.investor_id).filter(
                PitchView.pitch_id == pitch.id
            ).distinct().all()
            for v in views:
                if v.investor_id:
                    unique_investors.add(v.investor_id)

            pitch_list.append({
                "id": str(pitch.id),
                "type": pitch.type,
                "status": pitch.status,
                "view_count": pitch.view_count,
                "created_at": pitch.created_at
            })

        startup_data.append({
            "id": str(startup.id),
            "name": startup.name,
            "sectors": startup.sectors,
            "stage": startup.stage,
            "pitches": pitch_list
        })

    # Count Q&A threads for this founder's startups
    from app.models.qa import QAThread
    questions_received = db.query(func.count(QAThread.id)).join(Startup).filter(
        Startup.founder_id == current_user.id
    ).scalar() or 0

    return FounderDashboard(
        startups=startup_data,
        stats={
            "total_views": total_views,
            "unique_investors": len(unique_investors),
            "questions_received": questions_received
        }
    )
