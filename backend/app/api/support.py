import os
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from anthropic import Anthropic

from app.database import get_db
from app.models.user import User
from app.models.support import SupportTicket, SupportMessage
from app.api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = None
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ============ Request/Response Models ============

class CreateTicketRequest(BaseModel):
    subject: str
    message: str


class SendMessageRequest(BaseModel):
    content: str


class TicketResponse(BaseModel):
    id: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    sender_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    id: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


# ============ AI Support System ============

SYSTEM_PROMPT = """You are a helpful support assistant for Caerus, a mobile app that connects startup founders with investors and talent.

## About Caerus
Caerus is a deal flow platform where:
- **Founders** can record 30-second pitch videos to attract investors and find talent for their startups
- **Investors** can browse founder pitches and discover investment opportunities (requires subscription)
- **Talent** (job seekers) can create profiles to be discovered by founders looking to hire

## Common Support Topics

### Recording Pitch Videos
- Go to Dashboard and tap "Record Pitch"
- Ensure good lighting and a quiet environment
- Free tier allows one 30-second pitch video
- Premium founders can record additional videos

### Video Playback Issues
- Check internet connection
- Close and reopen the app
- Ensure camera permissions are granted in device Settings
- Try on WiFi if mobile data is slow

### Account & Profile
- To delete account: Profile > scroll down > "Delete Profile" (permanent, cannot be undone)
- Role (Founder/Investor/Talent) cannot be changed after signup - contact human support for role changes
- Profile photos and videos are stored securely in the cloud

### Talent Approval
- Talent profiles are reviewed within 24-48 hours
- Check status on your Profile screen
- LinkedIn URL is required to verify professional identity
- Approval status: Pending → Approved/Rejected

### Subscriptions (Investors)
- Managed through Apple ID subscriptions
- Go to Settings > Apple ID > Subscriptions to manage or cancel
- Subscription gives access to browse all founder pitches

### LinkedIn Requirements
- Required for Talent profiles to verify identity
- Go to Profile > Edit to add your LinkedIn URL
- Must be a valid LinkedIn profile URL

## Response Guidelines
1. Be friendly, concise, and helpful
2. If you can answer the question, do so clearly
3. If the question is outside your knowledge or requires account-specific action (refunds, role changes, account issues), set needs_human to true
4. Keep responses under 3-4 sentences when possible
5. Don't make up information - if unsure, suggest contacting human support

Respond in JSON format: {"response": "your message", "needs_human": true/false}"""


async def get_ai_response(message: str, user_role: Optional[str] = None) -> dict:
    """Get AI response using Claude Haiku."""

    if not anthropic_client:
        logger.warning("Anthropic client not initialized - no API key")
        return {
            "response": "I'm having trouble connecting right now. Would you like to contact our support team directly?",
            "needs_human": True
        }

    try:
        # Add user context if available
        user_context = f"\n\nUser role: {user_role}" if user_role else ""

        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"{message}{user_context}"
                }
            ]
        )

        # Parse the response
        content = response.content[0].text

        # Try to extract JSON from the response
        import json
        try:
            # Handle case where response is wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return {
                "response": result.get("response", content),
                "needs_human": result.get("needs_human", False)
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw response
            return {
                "response": content,
                "needs_human": False
            }

    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        return {
            "response": "I'm having trouble processing your request. Would you like to contact our support team?",
            "needs_human": True
        }


# ============ User Endpoints ============

@router.post("/tickets")
async def create_ticket(
    request: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new support ticket with initial message."""
    # Create ticket
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=request.subject,
        status="open"
    )
    db.add(ticket)
    db.flush()

    # Add initial user message
    user_message = SupportMessage(
        ticket_id=ticket.id,
        sender_type="user",
        content=request.message
    )
    db.add(user_message)

    # Try to get an AI response
    ai_result = await get_ai_response(request.message, current_user.role)
    ai_response = ai_result["response"]

    ai_message = SupportMessage(
        ticket_id=ticket.id,
        sender_type="ai",
        content=ai_response
    )
    db.add(ai_message)

    db.commit()
    db.refresh(ticket)

    return {
        "ticket": {
            "id": str(ticket.id),
            "subject": ticket.subject,
            "status": ticket.status,
            "created_at": ticket.created_at
        },
        "ai_response": ai_response,
        "needs_human": ai_result["needs_human"]
    }


@router.get("/tickets")
async def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's support tickets."""
    tickets = db.query(SupportTicket).filter(
        SupportTicket.user_id == current_user.id
    ).order_by(desc(SupportTicket.updated_at)).all()

    items = []
    for ticket in tickets:
        message_count = db.query(SupportMessage).filter(
            SupportMessage.ticket_id == ticket.id
        ).count()

        last_message = db.query(SupportMessage).filter(
            SupportMessage.ticket_id == ticket.id
        ).order_by(desc(SupportMessage.created_at)).first()

        items.append({
            "id": str(ticket.id),
            "subject": ticket.subject,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "message_count": message_count,
            "last_message": last_message.content[:100] if last_message else None,
            "last_sender": last_message.sender_type if last_message else None
        })

    return {"tickets": items}


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific ticket with all messages."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    messages = db.query(SupportMessage).filter(
        SupportMessage.ticket_id == ticket.id
    ).order_by(SupportMessage.created_at).all()

    return {
        "ticket": {
            "id": str(ticket.id),
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


@router.post("/tickets/{ticket_id}/messages")
async def send_message(
    ticket_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to a ticket."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Add user message
    user_message = SupportMessage(
        ticket_id=ticket.id,
        sender_type="user",
        content=request.content
    )
    db.add(user_message)

    # Update ticket timestamp
    ticket.updated_at = datetime.utcnow()

    # Get AI response
    ai_result = await get_ai_response(request.content, current_user.role)
    ai_response = ai_result["response"]

    ai_message = SupportMessage(
        ticket_id=ticket.id,
        sender_type="ai",
        content=ai_response
    )
    db.add(ai_message)

    db.commit()

    return {
        "message": {
            "id": str(user_message.id),
            "sender_type": "user",
            "content": user_message.content,
            "created_at": user_message.created_at
        },
        "ai_response": ai_response,
        "needs_human": ai_result["needs_human"]
    }


@router.post("/ai-chat")
async def ai_chat(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI response without creating a ticket (for initial chat)."""
    ai_result = await get_ai_response(request.content, current_user.role)

    return {
        "response": ai_result["response"],
        "needs_human": ai_result["needs_human"]
    }
