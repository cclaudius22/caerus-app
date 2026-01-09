from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.user import User, InvestorProfile, FounderProfile
from app.api.deps import get_current_user

router = APIRouter()


class InvestorPublicProfile(BaseModel):
    """Public investor profile for trust verification."""
    id: str
    full_name: Optional[str]
    firm_name: Optional[str]
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    website: Optional[str]
    investor_type: Optional[str]
    sectors: Optional[List[str]]
    stages: Optional[List[str]]
    avatar_url: Optional[str]
    is_verified: bool


class FounderPublicProfile(BaseModel):
    """Public founder profile for trust verification."""
    id: str
    full_name: Optional[str]
    company_name: Optional[str]
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    website: Optional[str]
    avatar_url: Optional[str]


@router.get("/investor/{investor_id}", response_model=InvestorPublicProfile)
async def get_investor_profile(
    investor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get public profile of an investor for trust verification.
    Allows founders and talent to view investor details before engaging.
    """
    # Only founders and talent can view investor profiles (they receive DMs from investors)
    if current_user.role not in ["founder", "talent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only founders and talent can view investor profiles"
        )

    # Get the investor user
    investor_user = db.query(User).filter(
        User.id == investor_id,
        User.role == "investor"
    ).first()

    if not investor_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investor not found"
        )

    # Get investor profile
    profile = db.query(InvestorProfile).filter(
        InvestorProfile.user_id == investor_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investor profile not found"
        )

    return InvestorPublicProfile(
        id=str(investor_user.id),
        full_name=profile.full_name,
        firm_name=profile.firm_name,
        linkedin_url=profile.linkedin_url,
        twitter_url=profile.twitter_url,
        website=profile.website,
        investor_type=profile.investor_type,
        sectors=profile.sectors,
        stages=profile.stages,
        avatar_url=investor_user.avatar_url,
        is_verified=profile.is_verified or False
    )


@router.get("/founder/{founder_id}", response_model=FounderPublicProfile)
async def get_founder_profile(
    founder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get public profile of a founder for trust verification.
    Allows investors and talent to view founder details.
    """
    # Only investors and talent can view founder profiles
    if current_user.role not in ["investor", "talent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investors and talent can view founder profiles"
        )

    # Get the founder user
    founder_user = db.query(User).filter(
        User.id == founder_id,
        User.role == "founder"
    ).first()

    if not founder_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Founder not found"
        )

    # Get founder profile
    profile = db.query(FounderProfile).filter(
        FounderProfile.user_id == founder_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Founder profile not found"
        )

    return FounderPublicProfile(
        id=str(founder_user.id),
        full_name=profile.full_name,
        company_name=profile.company_name,
        linkedin_url=profile.linkedin_url,
        twitter_url=profile.twitter_url,
        website=profile.website,
        avatar_url=founder_user.avatar_url
    )
