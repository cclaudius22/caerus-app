from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, TalentProfile, FounderProfile, InvestorProfile
from app.models.startup import Startup
from app.models.support import SupportTicket, SupportMessage
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


# ============ Dashboard Stats ============

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get overall dashboard statistics."""
    founders_count = db.query(func.count(User.id)).filter(User.role == "founder").scalar() or 0
    investors_count = db.query(func.count(User.id)).filter(User.role == "investor").scalar() or 0
    talent_count = db.query(func.count(User.id)).filter(User.role == "talent").scalar() or 0

    pending_talent = db.query(func.count(TalentProfile.id)).filter(
        TalentProfile.status == "pending",
        TalentProfile.onboarding_completed == True
    ).scalar() or 0

    startups_count = db.query(func.count(Startup.id)).scalar() or 0

    return {
        "users": {
            "founders": founders_count,
            "investors": investors_count,
            "talent": talent_count,
            "total": founders_count + investors_count + talent_count
        },
        "pending_talent": pending_talent,
        "startups": startups_count
    }


# ============ All Users Lists ============

@router.get("/users/founders")
async def list_founders(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all founders with their profiles."""
    query = db.query(User).filter(User.role == "founder")

    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for user in users:
        profile = db.query(FounderProfile).filter(FounderProfile.user_id == user.id).first()
        startup_count = db.query(func.count(Startup.id)).filter(Startup.founder_id == user.id).scalar() or 0

        items.append({
            "id": str(user.id),
            "email": user.email,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at,
            "full_name": profile.full_name if profile else None,
            "company_name": profile.company_name if profile else None,
            "linkedin_url": profile.linkedin_url if profile else None,
            "profile_completed": profile.profile_completed if profile else False,
            "onboarding_completed": profile.onboarding_completed if profile else False,
            "startup_count": startup_count
        })

    return {"founders": items, "total": total}


@router.get("/users/investors")
async def list_investors(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all investors with their profiles."""
    query = db.query(User).filter(User.role == "investor")

    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for user in users:
        profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == user.id).first()

        items.append({
            "id": str(user.id),
            "email": user.email,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at,
            "full_name": profile.full_name if profile else None,
            "firm_name": profile.firm_name if profile else None,
            "linkedin_url": profile.linkedin_url if profile else None,
            "investor_type": profile.investor_type if profile else None,
            "is_verified": profile.is_verified if profile else False,
            "profile_completed": profile.profile_completed if profile else False,
            "onboarding_completed": profile.onboarding_completed if profile else False,
            "free_views_remaining": profile.free_views_remaining if profile else None
        })

    return {"investors": items, "total": total}


@router.get("/users/talent")
async def list_all_talent(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all talent with their profiles."""
    query = db.query(TalentProfile)

    if status_filter:
        query = query.filter(TalentProfile.status == status_filter)

    total = query.count()
    profiles = query.order_by(TalentProfile.applied_at.desc()).offset(offset).limit(limit).all()

    items = []
    for profile in profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()

        if search and user:
            if search.lower() not in user.email.lower() and (not profile.full_name or search.lower() not in profile.full_name.lower()):
                continue

        items.append({
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "email": user.email if user else None,
            "avatar_url": user.avatar_url if user else None,
            "full_name": profile.full_name,
            "status": profile.status,
            "applied_at": profile.applied_at,
            "approved_at": profile.approved_at,
            "job_title_seeking": profile.job_title_seeking,
            "skills": profile.skills,
            "experience_level": profile.experience_level,
            "compensation_type": profile.compensation_type,
            "linkedin_url": profile.linkedin_url,
            "location": profile.location,
            "remote_preference": profile.remote_preference,
            "availability": profile.availability,
            "profile_completed": profile.profile_completed,
            "onboarding_completed": profile.onboarding_completed
        })

    return {"talent": items, "total": total}


# ============ Support Tickets ============

class AdminReplyRequest(BaseModel):
    content: str


@router.get("/support/tickets")
async def list_support_tickets(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all support tickets for admin."""
    query = db.query(SupportTicket)

    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)

    total = query.count()
    tickets = query.order_by(SupportTicket.updated_at.desc()).offset(offset).limit(limit).all()

    items = []
    for ticket in tickets:
        user = db.query(User).filter(User.id == ticket.user_id).first()
        message_count = db.query(func.count(SupportMessage.id)).filter(
            SupportMessage.ticket_id == ticket.id
        ).scalar() or 0

        last_message = db.query(SupportMessage).filter(
            SupportMessage.ticket_id == ticket.id
        ).order_by(SupportMessage.created_at.desc()).first()

        # Check if there are unread messages (user messages after last admin reply)
        last_admin_message = db.query(SupportMessage).filter(
            SupportMessage.ticket_id == ticket.id,
            SupportMessage.sender_type == "admin"
        ).order_by(SupportMessage.created_at.desc()).first()

        has_unread = False
        if last_message and last_message.sender_type == "user":
            if not last_admin_message or last_message.created_at > last_admin_message.created_at:
                has_unread = True

        items.append({
            "id": str(ticket.id),
            "user_id": str(ticket.user_id),
            "user_email": user.email if user else None,
            "user_name": None,  # Could add name lookup here
            "subject": ticket.subject,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "message_count": message_count,
            "last_message": last_message.content[:100] if last_message else None,
            "last_sender": last_message.sender_type if last_message else None,
            "has_unread": has_unread
        })

    # Count open tickets for badge
    open_count = db.query(func.count(SupportTicket.id)).filter(
        SupportTicket.status == "open"
    ).scalar() or 0

    return {"tickets": items, "total": total, "open_count": open_count}


@router.get("/support/tickets/{ticket_id}")
async def get_support_ticket(
    ticket_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get a specific support ticket with all messages."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    user = db.query(User).filter(User.id == ticket.user_id).first()
    messages = db.query(SupportMessage).filter(
        SupportMessage.ticket_id == ticket.id
    ).order_by(SupportMessage.created_at).all()

    return {
        "ticket": {
            "id": str(ticket.id),
            "user_id": str(ticket.user_id),
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,
            "subject": ticket.subject,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "messages": [
                {
                    "id": str(msg.id),
                    "sender_type": msg.sender_type,
                    "content": msg.content,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        }
    }


@router.post("/support/tickets/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: str,
    request: AdminReplyRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Send an admin reply to a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Add admin message
    message = SupportMessage(
        ticket_id=ticket.id,
        sender_type="admin",
        content=request.content
    )
    db.add(message)

    # Update ticket timestamp
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return {
        "message": {
            "id": str(message.id),
            "sender_type": "admin",
            "content": message.content,
            "created_at": message.created_at
        }
    }


@router.post("/support/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Mark a support ticket as resolved."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    ticket.status = "resolved"
    ticket.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Ticket resolved", "status": "resolved"}


@router.post("/support/tickets/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reopen a resolved support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    ticket.status = "open"
    ticket.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Ticket reopened", "status": "open"}
