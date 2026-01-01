from typing import Generator, Optional
from datetime import date
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database import get_db
from app.config import settings
from app.models.user import User, TalentProfile, FounderProfile, InvestorProfile

security = HTTPBearer()


def get_db_session() -> Generator:
    """Get database session."""
    db = get_db()
    try:
        yield from db
    finally:
        pass


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_founder(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is a founder."""
    if current_user.role != "founder":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a founder account"
        )
    return current_user


async def get_current_investor(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is an investor."""
    if current_user.role != "investor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires an investor account"
        )
    return current_user


async def get_subscribed_investor(
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
) -> User:
    """Ensure current investor has an active subscription."""
    from app.models.subscription import Subscription
    from datetime import datetime

    subscription = db.query(Subscription).filter(
        Subscription.investor_id == current_user.id,
        Subscription.status == "active",
        Subscription.expires_at > datetime.utcnow()
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    return current_user


class InvestorAccess:
    """Holds investor access information."""
    def __init__(self, user: User, has_subscription: bool, free_views_remaining: int):
        self.user = user
        self.has_subscription = has_subscription
        self.free_views_remaining = free_views_remaining

    @property
    def can_view(self) -> bool:
        return self.has_subscription or self.free_views_remaining > 0


async def get_investor_with_access(
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
) -> InvestorAccess:
    """Get investor with access information (subscription or free views)."""
    from app.models.subscription import Subscription
    from app.models.user import InvestorProfile
    from datetime import datetime

    # Check subscription
    subscription = db.query(Subscription).filter(
        Subscription.investor_id == current_user.id,
        Subscription.status == "active",
        Subscription.expires_at > datetime.utcnow()
    ).first()

    has_subscription = subscription is not None

    # Get free views remaining
    profile = db.query(InvestorProfile).filter(
        InvestorProfile.user_id == current_user.id
    ).first()

    free_views_remaining = profile.free_views_remaining if profile else 0

    return InvestorAccess(
        user=current_user,
        has_subscription=has_subscription,
        free_views_remaining=free_views_remaining
    )


async def get_current_talent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is a talent."""
    if current_user.role != "talent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a talent account"
        )
    return current_user


async def get_approved_talent(
    current_user: User = Depends(get_current_talent),
    db: Session = Depends(get_db)
) -> User:
    """Ensure current talent is approved."""
    profile = db.query(TalentProfile).filter(
        TalentProfile.user_id == current_user.id
    ).first()

    if not profile or profile.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your profile must be approved to perform this action"
        )
    return current_user


class TalentViewAccess:
    """Holds talent viewing access information for founders/investors."""
    def __init__(self, user: User, has_subscription: bool, talent_views_remaining_today: int):
        self.user = user
        self.has_subscription = has_subscription
        self.talent_views_remaining_today = talent_views_remaining_today

    @property
    def can_view_talent(self) -> bool:
        return self.has_subscription or self.talent_views_remaining_today > 0


async def get_talent_viewer_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TalentViewAccess:
    """Allow founders OR investors to view talent, with daily limits (5/day)."""
    if current_user.role not in ["founder", "investor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only founders and investors can browse talent"
        )

    has_subscription = False
    talent_views_remaining = 5  # Default daily limit

    if current_user.role == "investor":
        # Check investor subscription
        from app.models.subscription import Subscription
        from datetime import datetime

        subscription = db.query(Subscription).filter(
            Subscription.investor_id == current_user.id,
            Subscription.status == "active",
            Subscription.expires_at > datetime.utcnow()
        ).first()
        has_subscription = subscription is not None

        # Get investor profile for talent views
        profile = db.query(InvestorProfile).filter(
            InvestorProfile.user_id == current_user.id
        ).first()

        if profile:
            today = date.today()
            if profile.talent_views_reset_date != today:
                profile.talent_views_today = 0
                profile.talent_views_reset_date = today
                db.commit()
            talent_views_remaining = 5 - (profile.talent_views_today or 0)

    else:  # founder
        profile = db.query(FounderProfile).filter(
            FounderProfile.user_id == current_user.id
        ).first()

        if profile:
            today = date.today()
            if profile.talent_views_reset_date != today:
                profile.talent_views_today = 0
                profile.talent_views_reset_date = today
                db.commit()
            talent_views_remaining = 5 - (profile.talent_views_today or 0)

    return TalentViewAccess(
        user=current_user,
        has_subscription=has_subscription,
        talent_views_remaining_today=talent_views_remaining
    )
