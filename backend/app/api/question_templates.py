from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import get_db
from app.models.user import User
from app.models.question_template import QuestionTemplate, DEFAULT_QUESTIONS
from app.api.deps import get_current_investor


router = APIRouter()


# Request/Response Schemas
class QuestionTemplateCreate(BaseModel):
    question_text: str


class QuestionTemplateUpdate(BaseModel):
    question_text: Optional[str] = None
    display_order: Optional[int] = None


class QuestionTemplateResponse(BaseModel):
    id: str
    question_text: str
    is_default: bool
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionTemplateListResponse(BaseModel):
    templates: List[QuestionTemplateResponse]


class SendQuestionsRequest(BaseModel):
    pitch_id: str
    question_ids: List[str]  # Template IDs to send
    custom_question: Optional[str] = None  # Optional custom question


@router.get("/templates", response_model=QuestionTemplateListResponse)
async def get_question_templates(
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Get all question templates for the current investor."""
    templates = db.query(QuestionTemplate).filter(
        QuestionTemplate.investor_id == current_user.id
    ).order_by(QuestionTemplate.display_order, QuestionTemplate.created_at).all()

    # If no templates exist, create defaults
    if not templates:
        templates = []
        for i, question in enumerate(DEFAULT_QUESTIONS):
            template = QuestionTemplate(
                investor_id=current_user.id,
                question_text=question,
                is_default=True,
                display_order=i
            )
            db.add(template)
            templates.append(template)
        db.commit()

    return QuestionTemplateListResponse(
        templates=[
            QuestionTemplateResponse(
                id=str(t.id),
                question_text=t.question_text,
                is_default=t.is_default,
                display_order=t.display_order,
                created_at=t.created_at
            )
            for t in templates
        ]
    )


@router.post("/templates", response_model=QuestionTemplateResponse)
async def create_question_template(
    request: QuestionTemplateCreate,
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Create a new question template."""
    # Get max display order
    max_order = db.query(QuestionTemplate).filter(
        QuestionTemplate.investor_id == current_user.id
    ).count()

    template = QuestionTemplate(
        investor_id=current_user.id,
        question_text=request.question_text,
        is_default=False,
        display_order=max_order
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return QuestionTemplateResponse(
        id=str(template.id),
        question_text=template.question_text,
        is_default=template.is_default,
        display_order=template.display_order,
        created_at=template.created_at
    )


@router.put("/templates/{template_id}", response_model=QuestionTemplateResponse)
async def update_question_template(
    template_id: str,
    request: QuestionTemplateUpdate,
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Update a question template."""
    template = db.query(QuestionTemplate).filter(
        QuestionTemplate.id == template_id,
        QuestionTemplate.investor_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    if request.question_text is not None:
        template.question_text = request.question_text
    if request.display_order is not None:
        template.display_order = request.display_order

    db.commit()
    db.refresh(template)

    return QuestionTemplateResponse(
        id=str(template.id),
        question_text=template.question_text,
        is_default=template.is_default,
        display_order=template.display_order,
        created_at=template.created_at
    )


@router.delete("/templates/{template_id}")
async def delete_question_template(
    template_id: str,
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Delete a question template."""
    template = db.query(QuestionTemplate).filter(
        QuestionTemplate.id == template_id,
        QuestionTemplate.investor_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    db.delete(template)
    db.commit()

    return {"deleted": True}


@router.post("/send-questions")
async def send_questions_to_founder(
    request: SendQuestionsRequest,
    current_user: User = Depends(get_current_investor),
    db: Session = Depends(get_db)
):
    """Send selected questions to a founder via Q&A thread."""
    from app.models.pitch import Pitch
    from app.models.qa import QAThread, QAMessage

    # Verify pitch exists
    pitch = db.query(Pitch).filter(Pitch.id == request.pitch_id).first()
    if not pitch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pitch not found"
        )

    # Get or create thread
    thread = db.query(QAThread).filter(
        QAThread.pitch_id == request.pitch_id,
        QAThread.investor_id == current_user.id
    ).first()

    if not thread:
        thread = QAThread(
            pitch_id=request.pitch_id,
            investor_id=current_user.id
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)

    messages_sent = []

    # Send template questions
    if request.question_ids:
        templates = db.query(QuestionTemplate).filter(
            QuestionTemplate.id.in_(request.question_ids),
            QuestionTemplate.investor_id == current_user.id
        ).all()

        for template in templates:
            message = QAMessage(
                thread_id=thread.id,
                sender_id=current_user.id,
                content=template.question_text
            )
            db.add(message)
            messages_sent.append(template.question_text)

    # Send custom question if provided
    if request.custom_question and request.custom_question.strip():
        message = QAMessage(
            thread_id=thread.id,
            sender_id=current_user.id,
            content=request.custom_question.strip()
        )
        db.add(message)
        messages_sent.append(request.custom_question.strip())

    # Update thread timestamp
    thread.updated_at = datetime.utcnow()
    db.commit()

    return {
        "thread_id": str(thread.id),
        "messages_sent": len(messages_sent),
        "questions": messages_sent
    }
