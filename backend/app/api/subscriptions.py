from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.startup import Startup
from app.models.subscription import Subscription, PitchUnlock
from app.api.deps import get_current_user, get_current_investor, get_current_founder
from app.services.iap_verify import IAPVerifier

router = APIRouter()
iap_verifier = IAPVerifier()


# Request/Response Schemas
class VerifySubscriptionRequest(BaseModel):
    receipt_data: str
    transaction_id: str
    product_id: str


class VerifyUnlockRequest(BaseModel):
    startup_id: str
    receipt_data: str
    transaction_id: str


class SubscriptionResponse(BaseModel):
    status: str
    plan_type: str
    expires_at: datetime


@router.post("/iap/verify-subscription")
async def verify_subscription(
    request: VerifySubscriptionRequest,
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Verify and activate investor subscription."""
    # Verify receipt with Apple
    receipt_data = await iap_verifier.verify_receipt(request.receipt_data)

    if not receipt_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid receipt"
        )

    # Extract subscription info
    sub_info = iap_verifier.extract_subscription_info(receipt_data)

    if not sub_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found in receipt"
        )

    # Determine plan type
    plan_type = "monthly" if "monthly" in request.product_id.lower() else "annual"

    # Calculate expiration
    expires_at = datetime.fromtimestamp(sub_info["expires_date_ms"] / 1000)

    # Check for existing subscription
    existing = db.query(Subscription).filter(
        Subscription.investor_id == current_user.id
    ).first()

    if existing:
        # Update existing
        existing.plan_type = plan_type
        existing.apple_transaction_id = request.transaction_id
        existing.apple_original_transaction_id = sub_info["original_transaction_id"]
        existing.status = "active"
        existing.expires_at = expires_at
        existing.updated_at = datetime.utcnow()
    else:
        # Create new
        subscription = Subscription(
            investor_id=current_user.id,
            plan_type=plan_type,
            apple_transaction_id=request.transaction_id,
            apple_original_transaction_id=sub_info["original_transaction_id"],
            status="active",
            expires_at=expires_at
        )
        db.add(subscription)

    db.commit()

    return {
        "subscription": {
            "status": "active",
            "expires_at": expires_at,
            "plan_type": plan_type
        }
    }


@router.post("/iap/verify-unlock")
async def verify_pitch_unlock(
    request: VerifyUnlockRequest,
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Verify and unlock 5-minute pitch for a startup."""
    # Verify startup ownership
    startup = db.query(Startup).filter(
        Startup.id == request.startup_id,
        Startup.founder_id == current_user.id
    ).first()

    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup not found"
        )

    # Verify receipt with Apple
    receipt_data = await iap_verifier.verify_receipt(request.receipt_data)

    if not receipt_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid receipt"
        )

    # Check if already unlocked
    existing = db.query(PitchUnlock).filter(
        PitchUnlock.startup_id == request.startup_id,
        PitchUnlock.founder_id == current_user.id
    ).first()

    if existing:
        return {"unlocked": True, "pitch_type": "5min_paid"}

    # Create unlock record
    unlock = PitchUnlock(
        startup_id=request.startup_id,
        founder_id=current_user.id,
        apple_transaction_id=request.transaction_id,
        product_id="com.caerus.founder.5min"
    )
    db.add(unlock)
    db.commit()

    return {"unlocked": True, "pitch_type": "5min_paid"}


@router.get("/investor/subscription", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Get current subscription status."""
    subscription = db.query(Subscription).filter(
        Subscription.investor_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    # Check if expired
    if subscription.expires_at < datetime.utcnow():
        subscription.status = "expired"
        db.commit()

    return SubscriptionResponse(
        status=subscription.status,
        plan_type=subscription.plan_type,
        expires_at=subscription.expires_at
    )


@router.get("/founder/unlocks")
async def get_founder_unlocks(
    current_user: User = Depends(get_current_founder),
    db: Session = Depends(get_db)
):
    """Get list of unlocked 5-minute pitches for founder."""
    unlocks = db.query(PitchUnlock).filter(
        PitchUnlock.founder_id == current_user.id
    ).all()

    return {
        "unlocks": [
            {
                "startup_id": str(u.startup_id),
                "product_id": u.product_id,
                "purchased_at": u.purchased_at
            }
            for u in unlocks
        ]
    }
