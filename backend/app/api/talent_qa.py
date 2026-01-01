from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User, TalentProfile
from app.models.talent_pitch import TalentPitch
from app.models.talent_qa import TalentQAThread, TalentQAMessage
from app.api.deps import get_current_user, get_current_talent, get_talent_viewer_access, TalentViewAccess

router = APIRouter()


# Request/Response Schemas
class CreateThreadRequest(BaseModel):
    pitch_id: str
    initial_message: str


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"  # text or video
    video_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_role: str
    message_type: str
    content: str
    video_url: Optional[str]
    is_read: bool
    created_at: datetime


class ThreadResponse(BaseModel):
    id: str
    pitch_id: str
    talent_id: str
    recruiter_id: str
    talent_name: Optional[str]
    recruiter_role: str
    last_message: Optional[dict]
    unread_count: int
    created_at: datetime


@router.post("/threads")
async def create_thread(
    request: CreateThreadRequest,
    access: TalentViewAccess = Depends(get_talent_viewer_access),
    db: Session = Depends(get_db)
):
    """Create a new Q&A thread with a talent (recruiter initiates)."""
    # Check pitch exists and is from approved talent
    pitch = db.query(TalentPitch).join(
        TalentProfile, TalentPitch.talent_id == TalentProfile.user_id
    ).filter(
        TalentPitch.id == request.pitch_id,
        TalentPitch.status == "published",
        TalentProfile.status == "approved"
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Check if thread already exists
    existing_thread = db.query(TalentQAThread).filter(
        TalentQAThread.pitch_id == pitch.id,
        TalentQAThread.recruiter_id == access.user.id
    ).first()

    if existing_thread:
        # Add message to existing thread
        message = TalentQAMessage(
            thread_id=existing_thread.id,
            sender_id=access.user.id,
            content=request.initial_message,
            message_type="text"
        )
        db.add(message)
        db.commit()

        return {
            "thread_id": str(existing_thread.id),
            "message": "Message added to existing thread"
        }

    # Create new thread
    thread = TalentQAThread(
        pitch_id=pitch.id,
        recruiter_id=access.user.id,
        talent_id=pitch.talent_id
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    # Add initial message
    message = TalentQAMessage(
        thread_id=thread.id,
        sender_id=access.user.id,
        content=request.initial_message,
        message_type="text"
    )
    db.add(message)
    db.commit()

    return {
        "thread_id": str(thread.id),
        "message": "Thread created successfully"
    }


@router.get("/threads")
async def list_threads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Q&A threads for current user (works for both talent and recruiters)."""
    if current_user.role == "talent":
        # Talent sees threads where they are the talent
        threads = db.query(TalentQAThread).filter(
            TalentQAThread.talent_id == current_user.id
        ).order_by(TalentQAThread.updated_at.desc()).all()
    else:
        # Founder/investor sees threads where they are the recruiter
        threads = db.query(TalentQAThread).filter(
            TalentQAThread.recruiter_id == current_user.id
        ).order_by(TalentQAThread.updated_at.desc()).all()

    items = []
    for thread in threads:
        # Get last message
        last_msg = db.query(TalentQAMessage).filter(
            TalentQAMessage.thread_id == thread.id
        ).order_by(TalentQAMessage.created_at.desc()).first()

        # Count unread messages
        unread_count = db.query(TalentQAMessage).filter(
            TalentQAMessage.thread_id == thread.id,
            TalentQAMessage.sender_id != current_user.id,
            TalentQAMessage.is_read == False
        ).count()

        # Get talent profile
        talent_profile = db.query(TalentProfile).filter(
            TalentProfile.user_id == thread.talent_id
        ).first()

        # Get recruiter info
        recruiter = db.query(User).filter(User.id == thread.recruiter_id).first()

        items.append({
            "id": str(thread.id),
            "pitch_id": str(thread.pitch_id),
            "talent_id": str(thread.talent_id),
            "recruiter_id": str(thread.recruiter_id),
            "talent_name": talent_profile.full_name if talent_profile else None,
            "talent_job_title": talent_profile.job_title_seeking if talent_profile else None,
            "recruiter_role": recruiter.role if recruiter else None,
            "last_message": {
                "content": last_msg.content if last_msg else None,
                "created_at": last_msg.created_at if last_msg else None,
                "sender_id": str(last_msg.sender_id) if last_msg else None
            } if last_msg else None,
            "unread_count": unread_count,
            "created_at": thread.created_at
        })

    return {"threads": items}


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages in a thread."""
    thread = db.query(TalentQAThread).filter(TalentQAThread.id == thread_id).first()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check user is part of thread
    if str(thread.talent_id) != str(current_user.id) and str(thread.recruiter_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this thread"
        )

    messages = db.query(TalentQAMessage).filter(
        TalentQAMessage.thread_id == thread_id
    ).order_by(TalentQAMessage.created_at.asc()).all()

    # Mark messages as read
    for msg in messages:
        if str(msg.sender_id) != str(current_user.id) and not msg.is_read:
            msg.is_read = True
    db.commit()

    # Get sender info
    talent = db.query(User).filter(User.id == thread.talent_id).first()
    recruiter = db.query(User).filter(User.id == thread.recruiter_id).first()

    items = []
    for msg in messages:
        sender_role = "talent" if str(msg.sender_id) == str(thread.talent_id) else recruiter.role if recruiter else "unknown"
        items.append({
            "id": str(msg.id),
            "sender_id": str(msg.sender_id),
            "sender_role": sender_role,
            "message_type": msg.message_type,
            "content": msg.content,
            "video_url": msg.video_url,
            "is_read": msg.is_read,
            "created_at": msg.created_at
        })

    return {"messages": items}


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a thread."""
    thread = db.query(TalentQAThread).filter(TalentQAThread.id == thread_id).first()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check user is part of thread
    if str(thread.talent_id) != str(current_user.id) and str(thread.recruiter_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this thread"
        )

    message = TalentQAMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        content=request.content,
        message_type=request.message_type,
        video_url=request.video_url
    )
    db.add(message)

    # Update thread timestamp
    thread.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return {
        "message": {
            "id": str(message.id),
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at
        }
    }
