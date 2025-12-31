from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.startup import Startup
from app.api.deps import get_current_founder

router = APIRouter()


# Request/Response Schemas
class StartupCreate(BaseModel):
    name: str
    tagline: Optional[str] = None
    website: Optional[str] = None
    sector: Optional[str] = None
    stage: Optional[str] = None  # 'idea', 'pre_seed', 'seed', 'series_a'
    location: Optional[str] = None
    round_size_min: Optional[int] = None
    round_size_max: Optional[int] = None
    traction_bullets: Optional[List[str]] = None


class StartupUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    website: Optional[str] = None
    sector: Optional[str] = None
    stage: Optional[str] = None
    location: Optional[str] = None
    round_size_min: Optional[int] = None
    round_size_max: Optional[int] = None
    traction_bullets: Optional[List[str]] = None
    logo_url: Optional[str] = None


class StartupResponse(BaseModel):
    id: str
    name: str
    tagline: Optional[str]
    website: Optional[str]
    sector: Optional[str]
    stage: Optional[str]
    location: Optional[str]
    round_size_min: Optional[int]
    round_size_max: Optional[int]
    traction_bullets: Optional[List[str]]
    logo_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=StartupResponse)
async def create_startup(
    startup_data: StartupCreate,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Create a new startup."""
    # Validate stage if provided
    valid_stages = ["idea", "pre_seed", "seed", "series_a"]
    if startup_data.stage and startup_data.stage not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stage must be one of: {', '.join(valid_stages)}"
        )

    startup = Startup(
        founder_id=current_user.id,
        name=startup_data.name,
        tagline=startup_data.tagline,
        website=startup_data.website,
        sector=startup_data.sector,
        stage=startup_data.stage,
        location=startup_data.location,
        round_size_min=startup_data.round_size_min,
        round_size_max=startup_data.round_size_max,
        traction_bullets=startup_data.traction_bullets
    )

    db.add(startup)
    db.commit()
    db.refresh(startup)

    return StartupResponse(
        id=str(startup.id),
        name=startup.name,
        tagline=startup.tagline,
        website=startup.website,
        sector=startup.sector,
        stage=startup.stage,
        location=startup.location,
        round_size_min=startup.round_size_min,
        round_size_max=startup.round_size_max,
        traction_bullets=startup.traction_bullets,
        logo_url=startup.logo_url,
        created_at=startup.created_at
    )


@router.get("", response_model=List[StartupResponse])
async def list_my_startups(
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """List all startups owned by the current founder."""
    startups = db.query(Startup).filter(Startup.founder_id == current_user.id).all()

    return [
        StartupResponse(
            id=str(s.id),
            name=s.name,
            tagline=s.tagline,
            website=s.website,
            sector=s.sector,
            stage=s.stage,
            location=s.location,
            round_size_min=s.round_size_min,
            round_size_max=s.round_size_max,
            traction_bullets=s.traction_bullets,
            logo_url=s.logo_url,
            created_at=s.created_at
        )
        for s in startups
    ]


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(
    startup_id: str,
    db: Session = Depends(get_db)
):
    """Get startup details."""
    startup = db.query(Startup).filter(Startup.id == startup_id).first()

    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup not found"
        )

    return StartupResponse(
        id=str(startup.id),
        name=startup.name,
        tagline=startup.tagline,
        website=startup.website,
        sector=startup.sector,
        stage=startup.stage,
        location=startup.location,
        round_size_min=startup.round_size_min,
        round_size_max=startup.round_size_max,
        traction_bullets=startup.traction_bullets,
        logo_url=startup.logo_url,
        created_at=startup.created_at
    )


@router.put("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: str,
    startup_data: StartupUpdate,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Update a startup."""
    startup = db.query(Startup).filter(
        Startup.id == startup_id,
        Startup.founder_id == current_user.id
    ).first()

    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup not found or you don't have permission"
        )

    # Update fields
    update_data = startup_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(startup, field, value)

    db.commit()
    db.refresh(startup)

    return StartupResponse(
        id=str(startup.id),
        name=startup.name,
        tagline=startup.tagline,
        website=startup.website,
        sector=startup.sector,
        stage=startup.stage,
        location=startup.location,
        round_size_min=startup.round_size_min,
        round_size_max=startup.round_size_max,
        traction_bullets=startup.traction_bullets,
        logo_url=startup.logo_url,
        created_at=startup.created_at
    )


@router.delete("/{startup_id}")
async def delete_startup(
    startup_id: str,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Delete a startup."""
    startup = db.query(Startup).filter(
        Startup.id == startup_id,
        Startup.founder_id == current_user.id
    ).first()

    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup not found or you don't have permission"
        )

    db.delete(startup)
    db.commit()

    return {"message": "Startup deleted successfully"}
