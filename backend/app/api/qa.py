from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User, InvestorProfile, FounderProfile
from app.models.startup import Startup
from app.models.pitch import Pitch
from app.models.qa import QAThread, QAMessage, ThreadStatus
from app.api.deps import get_current_user, get_subscribed_investor
from app.services.notifications import (
    notify_founder_investor_interested,
    notify_founder_investor_declined,
    notify_founder_new_question,
    notify_investor_founder_replied,
)

router = APIRouter()


# Request/Response Schemas
class CreateThreadRequest(BaseModel):
    pitch_id: str


class SendMessageRequest(BaseModel):
    message_type: str = "text"  # 'text' or 'video'
    content: Optional[str] = None
    video_url: Optional[str] = None


class UpdateThreadStatusRequest(BaseModel):
    status: str  # 'interested' or 'declined'
    decline_message: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_role: str
    message_type: str
    content: Optional[str]
    video_url: Optional[str]
    is_read: bool
    is_from_founder: bool
    created_at: datetime


class InvestorInfo(BaseModel):
    id: str
    name: Optional[str]
    firm: Optional[str]


class FounderInfo(BaseModel):
    id: str
    name: Optional[str]


class ThreadResponse(BaseModel):
    id: str
    pitch_id: str
    startup: dict
    investor: Optional[InvestorInfo]
    founder: Optional[FounderInfo]
    status: str
    decline_message: Optional[str]
    last_message: Optional[MessageResponse]
    unread_count: int
    created_at: datetime


class ThreadDetailResponse(BaseModel):
    thread: dict
    messages: List[MessageResponse]


@router.post("/threads")
async def create_thread(
    request: CreateThreadRequest,
    current_user: User = Depends(get_subscribed_investor),
    db: Session = Depends(get_db)
):
    """Create a Q&A thread for a pitch (investor only)."""
    # Get pitch and startup
    pitch = db.query(Pitch).filter(
        Pitch.id == request.pitch_id,
        Pitch.status == "published"
    ).first()

    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Check if thread already exists
    existing_thread = db.query(QAThread).filter(
        QAThread.pitch_id == pitch.id,
        QAThread.investor_id == current_user.id
    ).first()

    if existing_thread:
        return {"thread_id": str(existing_thread.id), "created_at": existing_thread.created_at}

    # Create new thread
    thread = QAThread(
        pitch_id=pitch.id,
        investor_id=current_user.id,
        startup_id=pitch.startup_id
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    return {"thread_id": str(thread.id), "created_at": thread.created_at}


@router.get("/threads", response_model=List[ThreadResponse])
async def list_threads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Q&A threads for current user."""
    if current_user.role == "investor":
        threads = db.query(QAThread).filter(
            QAThread.investor_id == current_user.id
        ).order_by(QAThread.updated_at.desc()).all()
    else:
        # Founder: get threads for their startups
        threads = db.query(QAThread).join(Startup).filter(
            Startup.founder_id == current_user.id
        ).order_by(QAThread.updated_at.desc()).all()

    result = []
    for thread in threads:
        # Get last message
        last_msg = db.query(QAMessage).filter(
            QAMessage.thread_id == thread.id
        ).order_by(QAMessage.created_at.desc()).first()

        # Get unread count
        unread_count = db.query(QAMessage).filter(
            QAMessage.thread_id == thread.id,
            QAMessage.sender_id != current_user.id,
            QAMessage.is_read == False
        ).count()

        # Get pitch to get startup and founder info
        pitch = db.query(Pitch).filter(Pitch.id == thread.pitch_id).first()
        startup = pitch.startup

        # Get founder info
        founder_user = db.query(User).filter(User.id == startup.founder_id).first()
        founder_profile = db.query(FounderProfile).filter(FounderProfile.user_id == startup.founder_id).first()
        founder_info = FounderInfo(
            id=str(founder_user.id),
            name=founder_profile.full_name if founder_profile else founder_user.email
        ) if founder_user else None

        # Get investor info
        investor_user = db.query(User).filter(User.id == thread.investor_id).first()
        investor_profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == thread.investor_id).first()
        investor_info = InvestorInfo(
            id=str(investor_user.id),
            name=investor_profile.full_name if investor_profile else investor_user.email,
            firm=investor_profile.firm_name if investor_profile else None
        ) if investor_user else None

        last_message = None
        if last_msg:
            sender = db.query(User).filter(User.id == last_msg.sender_id).first()
            last_message = MessageResponse(
                id=str(last_msg.id),
                sender_id=str(last_msg.sender_id),
                sender_role=sender.role if sender else "unknown",
                message_type=last_msg.message_type,
                content=last_msg.content,
                video_url=last_msg.video_url,
                is_read=last_msg.is_read,
                is_from_founder=sender.role == "founder" if sender else False,
                created_at=last_msg.created_at
            )

        result.append(ThreadResponse(
            id=str(thread.id),
            pitch_id=str(thread.pitch_id),
            startup={
                "id": str(startup.id),
                "name": startup.name,
                "logo_url": startup.logo_url
            },
            investor=investor_info,
            founder=founder_info,
            status=thread.status or ThreadStatus.active.value,
            decline_message=thread.decline_message,
            last_message=last_message,
            unread_count=unread_count,
            created_at=thread.created_at
        ))

    return result


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a Q&A thread."""
    # Verify thread access
    thread = db.query(QAThread).filter(QAThread.id == thread_id).first()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check access: investor must be the thread owner, founder must own the startup
    if current_user.role == "investor":
        if thread.investor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this thread"
            )
    else:
        startup = db.query(Startup).filter(Startup.id == thread.startup_id).first()
        if startup.founder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this thread"
            )

    # Create message
    message = QAMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        message_type=request.message_type,
        content=request.content,
        video_url=request.video_url
    )
    db.add(message)

    # Update thread timestamp
    thread.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return {"id": str(message.id), "created_at": message.created_at}


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages in a Q&A thread with thread info."""
    # Verify thread access
    thread = db.query(QAThread).filter(QAThread.id == thread_id).first()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check access
    if current_user.role == "investor":
        if thread.investor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this thread"
            )
    else:
        startup = db.query(Startup).filter(Startup.id == thread.startup_id).first()
        if startup.founder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this thread"
            )

    # Get messages
    messages = db.query(QAMessage).filter(
        QAMessage.thread_id == thread_id
    ).order_by(QAMessage.created_at.asc()).all()

    # Mark messages as read
    for msg in messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    db.commit()

    # Get startup info
    pitch = db.query(Pitch).filter(Pitch.id == thread.pitch_id).first()
    startup = pitch.startup

    # Get investor info
    investor_user = db.query(User).filter(User.id == thread.investor_id).first()
    investor_profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == thread.investor_id).first()

    # Get founder info
    founder_user = db.query(User).filter(User.id == startup.founder_id).first()
    founder_profile = db.query(FounderProfile).filter(FounderProfile.user_id == startup.founder_id).first()

    result = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append(MessageResponse(
            id=str(msg.id),
            sender_id=str(msg.sender_id),
            sender_role=sender.role if sender else "unknown",
            message_type=msg.message_type,
            content=msg.content,
            video_url=msg.video_url,
            is_read=msg.is_read,
            is_from_founder=sender.role == "founder" if sender else False,
            created_at=msg.created_at
        ))

    return {
        "thread": {
            "id": str(thread.id),
            "status": thread.status or ThreadStatus.active.value,
            "decline_message": thread.decline_message,
            "startup": {
                "id": str(startup.id),
                "name": startup.name,
            },
            "investor": {
                "id": str(investor_user.id),
                "name": investor_profile.full_name if investor_profile else investor_user.email,
                "firm": investor_profile.firm_name if investor_profile else None,
            } if investor_user else None,
            "founder": {
                "id": str(founder_user.id),
                "name": founder_profile.full_name if founder_profile else founder_user.email,
            } if founder_user else None,
        },
        "messages": result
    }


@router.put("/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: str,
    request: UpdateThreadStatusRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update thread status (investor only - to mark as interested or declined)."""
    # Only investors can update thread status
    if current_user.role != "investor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investors can update thread status"
        )

    thread = db.query(QAThread).filter(QAThread.id == thread_id).first()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Verify investor owns this thread
    if thread.investor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this thread"
        )

    # Validate status
    if request.status not in [ThreadStatus.interested.value, ThreadStatus.declined.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'interested' or 'declined'"
        )

    # Update thread
    thread.status = request.status
    if request.status == ThreadStatus.declined.value and request.decline_message:
        thread.decline_message = request.decline_message
    thread.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(thread)

    # Get founder info for notification
    startup = db.query(Startup).filter(Startup.id == thread.startup_id).first()
    founder_user = db.query(User).filter(User.id == startup.founder_id).first()
    investor_profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == current_user.id).first()
    investor_name = investor_profile.full_name if investor_profile and investor_profile.full_name else current_user.email

    # Send push notification to founder
    if founder_user and founder_user.push_token:
        if request.status == ThreadStatus.interested.value:
            background_tasks.add_task(
                notify_founder_investor_interested,
                founder_push_token=founder_user.push_token,
                investor_name=investor_name,
                startup_name=startup.name,
                thread_id=str(thread.id),
            )
        elif request.status == ThreadStatus.declined.value:
            background_tasks.add_task(
                notify_founder_investor_declined,
                founder_push_token=founder_user.push_token,
                investor_name=investor_name,
                startup_name=startup.name,
                thread_id=str(thread.id),
                has_message=bool(request.decline_message),
            )

    return {
        "id": str(thread.id),
        "status": thread.status,
        "decline_message": thread.decline_message,
        "updated_at": thread.updated_at
    }
