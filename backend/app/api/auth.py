import os
import uuid
import shutil
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt

from app.database import get_db
from app.config import settings
from app.models.user import User, FounderProfile, InvestorProfile, TalentProfile
from app.api.deps import get_current_user
from app.services.firebase import verify_firebase_token

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "avatars")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


# Request/Response Schemas
class SignupRequest(BaseModel):
    firebase_token: str
    role: str  # 'founder', 'investor', or 'talent'
    email: EmailStr


class LoginRequest(BaseModel):
    firebase_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class FounderProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None


class InvestorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    firm_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    ticket_size_min: Optional[int] = None
    ticket_size_max: Optional[int] = None
    sectors: Optional[list[str]] = None
    stages: Optional[list[str]] = None
    geographies: Optional[list[str]] = None


class InvestorOnboardingRequest(BaseModel):
    investor_type: str  # angel, vc, family_office, syndicate
    sectors: list[str]
    stages: list[str]
    ticket_size_min: Optional[int] = None
    ticket_size_max: Optional[int] = None
    geographies: Optional[list[str]] = None


class FounderOnboardingRequest(BaseModel):
    seeking_investor_types: list[str]  # angel, vc, family_office, syndicate
    desired_check_size_min: Optional[int] = None
    desired_check_size_max: Optional[int] = None
    value_add_preferences: Optional[list[str]] = None  # network, operational, hands_off, domain_expertise


class TalentOnboardingRequest(BaseModel):
    full_name: Optional[str] = None
    job_title_seeking: str
    skills: list[str]
    experience_level: str  # junior, mid, senior, lead, executive
    compensation_type: str  # equity_only, pay_equity, cash_only
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    availability: str  # immediate, 2_weeks, 1_month, 3_months
    location: Optional[str] = None
    remote_preference: str  # remote_only, hybrid, onsite, flexible
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class ProfileCompletionRequest(BaseModel):
    full_name: str
    company_name: str  # firm_name for investors, company_name for founders
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None


def create_access_token(user_id: str) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Verify Firebase token
    firebase_uid = await verify_firebase_token(request.firebase_token)
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.firebase_uid == firebase_uid) | (User.email == request.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    # Validate role
    if request.role not in ["founder", "investor", "talent"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'founder', 'investor', or 'talent'"
        )

    # Create user
    user = User(
        firebase_uid=firebase_uid,
        email=request.email,
        role=request.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create profile based on role
    if request.role == "founder":
        profile = FounderProfile(user_id=user.id)
        db.add(profile)
    elif request.role == "investor":
        profile = InvestorProfile(user_id=user.id)
        db.add(profile)
    else:  # talent
        profile = TalentProfile(user_id=user.id, status="pending")
        db.add(profile)

    db.commit()

    # Generate JWT token
    token = create_access_token(str(user.id))

    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            created_at=user.created_at
        ),
        token=token
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with Firebase token."""
    # Verify Firebase token
    firebase_uid = await verify_firebase_token(request.firebase_token)
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )

    # Find user
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sign up first."
        )

    # Generate JWT token
    token = create_access_token(str(user.id))

    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            created_at=user.created_at
        ),
        token=token
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user info with profile."""
    profile = None
    onboarding_completed = False
    profile_completed = False

    if current_user.role == "founder":
        founder_profile = db.query(FounderProfile).filter(
            FounderProfile.user_id == current_user.id
        ).first()
        if founder_profile:
            onboarding_completed = founder_profile.onboarding_completed or False
            profile_completed = founder_profile.profile_completed or False
            profile = {
                "full_name": founder_profile.full_name,
                "company_name": founder_profile.company_name,
                "linkedin_url": founder_profile.linkedin_url,
                "twitter_url": founder_profile.twitter_url,
                "website": founder_profile.website,
                "profile_completed": profile_completed,
                "onboarding_completed": onboarding_completed,
                "seeking_investor_types": founder_profile.seeking_investor_types,
                "desired_check_size_min": founder_profile.desired_check_size_min,
                "desired_check_size_max": founder_profile.desired_check_size_max,
                "value_add_preferences": founder_profile.value_add_preferences,
            }
    elif current_user.role == "investor":
        investor_profile = db.query(InvestorProfile).filter(
            InvestorProfile.user_id == current_user.id
        ).first()
        if investor_profile:
            onboarding_completed = investor_profile.onboarding_completed or False
            profile_completed = investor_profile.profile_completed or False
            profile = {
                "full_name": investor_profile.full_name,
                "firm_name": investor_profile.firm_name,
                "linkedin_url": investor_profile.linkedin_url,
                "twitter_url": investor_profile.twitter_url,
                "website": investor_profile.website,
                "profile_completed": profile_completed,
                "onboarding_completed": onboarding_completed,
                "investor_type": investor_profile.investor_type,
                "ticket_size_min": investor_profile.ticket_size_min,
                "ticket_size_max": investor_profile.ticket_size_max,
                "sectors": investor_profile.sectors,
                "stages": investor_profile.stages,
                "geographies": investor_profile.geographies,
                "free_views_remaining": investor_profile.free_views_remaining,
                "is_verified": investor_profile.is_verified,
            }
    else:  # talent
        talent_profile = db.query(TalentProfile).filter(
            TalentProfile.user_id == current_user.id
        ).first()
        if talent_profile:
            onboarding_completed = talent_profile.onboarding_completed or False
            profile_completed = talent_profile.profile_completed or False
            profile = {
                "full_name": talent_profile.full_name,
                "linkedin_url": talent_profile.linkedin_url,
                "twitter_url": talent_profile.twitter_url,
                "website": talent_profile.website,
                "profile_completed": profile_completed,
                "status": talent_profile.status,  # pending, approved, rejected
                "applied_at": talent_profile.applied_at,
                "approved_at": talent_profile.approved_at,
                "rejection_reason": talent_profile.rejection_reason,
                "onboarding_completed": onboarding_completed,
                "job_title_seeking": talent_profile.job_title_seeking,
                "skills": talent_profile.skills,
                "experience_level": talent_profile.experience_level,
                "compensation_type": talent_profile.compensation_type,
                "salary_range_min": talent_profile.salary_range_min,
                "salary_range_max": talent_profile.salary_range_max,
                "availability": talent_profile.availability,
                "location": talent_profile.location,
                "remote_preference": talent_profile.remote_preference,
                "github_url": talent_profile.github_url,
                "portfolio_url": talent_profile.portfolio_url,
            }

    return {
        "user": UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            role=current_user.role,
            created_at=current_user.created_at
        ),
        "avatar_url": current_user.avatar_url,
        "profile": profile,
        "onboarding_completed": onboarding_completed,
        "profile_completed": profile_completed,
        "is_hidden": current_user.is_hidden or False,
        "scheduled_deletion_date": current_user.scheduled_deletion_date.isoformat() if current_user.scheduled_deletion_date else None
    }


@router.put("/profile")
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    if current_user.role == "founder":
        profile = db.query(FounderProfile).filter(
            FounderProfile.user_id == current_user.id
        ).first()

        if profile_data.get("full_name"):
            profile.full_name = profile_data["full_name"]
        if profile_data.get("linkedin_url"):
            profile.linkedin_url = profile_data["linkedin_url"]
    else:
        profile = db.query(InvestorProfile).filter(
            InvestorProfile.user_id == current_user.id
        ).first()

        updatable_fields = [
            "full_name", "firm_name", "linkedin_url", "website",
            "ticket_size_min", "ticket_size_max", "sectors", "stages", "geographies"
        ]
        for field in updatable_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(profile, field, profile_data[field])

    db.commit()
    db.refresh(profile)

    return {"message": "Profile updated successfully"}


@router.post("/onboarding/investor")
async def complete_investor_onboarding(
    request: InvestorOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete investor onboarding with preferences."""
    if current_user.role != "investor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investors can complete investor onboarding"
        )

    profile = db.query(InvestorProfile).filter(
        InvestorProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investor profile not found"
        )

    # Update preferences
    profile.investor_type = request.investor_type
    profile.sectors = request.sectors
    profile.stages = request.stages
    profile.ticket_size_min = request.ticket_size_min
    profile.ticket_size_max = request.ticket_size_max
    profile.geographies = request.geographies or []
    profile.onboarding_completed = True

    db.commit()
    db.refresh(profile)

    return {
        "message": "Onboarding completed successfully",
        "profile": {
            "investor_type": profile.investor_type,
            "sectors": profile.sectors,
            "stages": profile.stages,
            "ticket_size_min": profile.ticket_size_min,
            "ticket_size_max": profile.ticket_size_max,
            "geographies": profile.geographies,
            "onboarding_completed": profile.onboarding_completed
        }
    }


@router.post("/onboarding/founder")
async def complete_founder_onboarding(
    request: FounderOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete founder onboarding with preferences."""
    if current_user.role != "founder":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only founders can complete founder onboarding"
        )

    profile = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Founder profile not found"
        )

    # Update preferences
    profile.seeking_investor_types = request.seeking_investor_types
    profile.desired_check_size_min = request.desired_check_size_min
    profile.desired_check_size_max = request.desired_check_size_max
    profile.value_add_preferences = request.value_add_preferences or []
    profile.onboarding_completed = True

    db.commit()
    db.refresh(profile)

    return {
        "message": "Onboarding completed successfully",
        "profile": {
            "seeking_investor_types": profile.seeking_investor_types,
            "desired_check_size_min": profile.desired_check_size_min,
            "desired_check_size_max": profile.desired_check_size_max,
            "value_add_preferences": profile.value_add_preferences,
            "onboarding_completed": profile.onboarding_completed
        }
    }


@router.post("/onboarding/talent")
async def complete_talent_onboarding(
    request: TalentOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete talent onboarding with profile info. Status remains 'pending' until approved."""
    if current_user.role != "talent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only talent can complete talent onboarding"
        )

    profile = db.query(TalentProfile).filter(
        TalentProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talent profile not found"
        )

    # Update profile info
    if request.full_name:
        profile.full_name = request.full_name
    profile.job_title_seeking = request.job_title_seeking
    profile.skills = request.skills
    profile.experience_level = request.experience_level
    profile.compensation_type = request.compensation_type
    profile.salary_range_min = request.salary_range_min
    profile.salary_range_max = request.salary_range_max
    profile.availability = request.availability
    profile.location = request.location
    profile.remote_preference = request.remote_preference
    profile.linkedin_url = request.linkedin_url
    profile.github_url = request.github_url
    profile.portfolio_url = request.portfolio_url
    profile.onboarding_completed = True
    # Note: status stays "pending" until admin approves

    db.commit()
    db.refresh(profile)

    return {
        "message": "Onboarding completed. Your profile is pending approval.",
        "profile": {
            "full_name": profile.full_name,
            "status": profile.status,
            "job_title_seeking": profile.job_title_seeking,
            "skills": profile.skills,
            "experience_level": profile.experience_level,
            "compensation_type": profile.compensation_type,
            "availability": profile.availability,
            "location": profile.location,
            "remote_preference": profile.remote_preference,
            "onboarding_completed": profile.onboarding_completed
        }
    }


@router.post("/profile/complete")
async def complete_profile(
    request: ProfileCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user profile with professional details. Requires at least one social link."""
    # Validate at least one social link is provided
    has_social_link = any([
        request.linkedin_url,
        request.twitter_url,
        request.website
    ])
    if not has_social_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one social link (LinkedIn, Twitter, or Website) is required to build trust in our community."
        )

    # Validate full_name and company_name
    if len(request.full_name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters."
        )
    if len(request.company_name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company/Organization name must be at least 2 characters."
        )

    if current_user.role == "founder":
        profile = db.query(FounderProfile).filter(
            FounderProfile.user_id == current_user.id
        ).first()
        if profile:
            profile.full_name = request.full_name.strip()
            profile.company_name = request.company_name.strip()
            profile.linkedin_url = request.linkedin_url
            profile.twitter_url = request.twitter_url
            profile.website = request.website
            profile.profile_completed = True

    elif current_user.role == "investor":
        profile = db.query(InvestorProfile).filter(
            InvestorProfile.user_id == current_user.id
        ).first()
        if profile:
            profile.full_name = request.full_name.strip()
            profile.firm_name = request.company_name.strip()  # Use firm_name for investors
            profile.linkedin_url = request.linkedin_url
            profile.twitter_url = request.twitter_url
            profile.website = request.website
            profile.profile_completed = True

    else:  # talent
        profile = db.query(TalentProfile).filter(
            TalentProfile.user_id == current_user.id
        ).first()
        if profile:
            profile.full_name = request.full_name.strip()
            # Talent doesn't have company_name, but we store it somewhere or skip
            profile.linkedin_url = request.linkedin_url
            profile.twitter_url = request.twitter_url
            profile.website = request.website
            profile.profile_completed = True

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile completed successfully. Welcome to our trusted community!",
        "profile_completed": True
    }


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload or replace user avatar photo. Only one photo at a time."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are allowed."
        )

    # Validate file size (max 5MB)
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must be less than 5MB."
        )

    # Delete old avatar if exists
    if current_user.avatar_url:
        old_filename = current_user.avatar_url.split("/")[-1]
        old_path = os.path.join(UPLOAD_DIR, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(filepath, "wb") as f:
        f.write(content)

    # Update user avatar_url
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.commit()

    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }


@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user avatar photo."""
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete."
        )

    # Delete file
    filename = current_user.avatar_url.split("/")[-1]
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Clear avatar_url
    current_user.avatar_url = None
    db.commit()

    return {"message": "Avatar deleted successfully"}


@router.delete("/profile")
async def schedule_profile_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule account deletion with 30-day grace period. Works for all user types."""
    # Set scheduled deletion date to 30 days from now
    deletion_date = datetime.utcnow() + timedelta(days=30)
    current_user.scheduled_deletion_date = deletion_date
    db.commit()

    return {
        "message": "Your account will be permanently deleted in 30 days. You can cancel this anytime by logging back in.",
        "scheduled_deletion_date": deletion_date.isoformat()
    }


class ProfileVisibilityRequest(BaseModel):
    is_hidden: bool


@router.put("/profile/visibility")
async def update_profile_visibility(
    request: ProfileVisibilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile visibility. Hidden profiles don't appear in feeds/search."""
    current_user.is_hidden = request.is_hidden
    db.commit()

    status_text = "hidden from" if request.is_hidden else "visible in"
    return {
        "message": f"Your profile is now {status_text} feeds and search.",
        "is_hidden": current_user.is_hidden
    }


@router.post("/profile/cancel-deletion")
async def cancel_profile_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel scheduled account deletion."""
    if not current_user.scheduled_deletion_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending deletion to cancel."
        )

    current_user.scheduled_deletion_date = None
    db.commit()

    return {"message": "Account deletion has been cancelled. Your account is safe."}


class PushTokenRequest(BaseModel):
    push_token: str  # Expo push token (ExponentPushToken[...])


@router.post("/push-token")
async def register_push_token(
    request: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register or update the user's push notification token."""
    # Validate token format
    if not request.push_token.startswith("ExponentPushToken["):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid push token format. Expected ExponentPushToken[...]"
        )

    # Update user's push token
    current_user.push_token = request.push_token
    db.commit()

    return {"message": "Push token registered successfully"}


@router.delete("/push-token")
async def unregister_push_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove the user's push notification token (e.g., on logout)."""
    current_user.push_token = None
    db.commit()

    return {"message": "Push token removed successfully"}
