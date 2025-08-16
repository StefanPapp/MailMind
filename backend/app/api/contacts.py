from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.services.analytics_service import AnalyticsService
from app.api.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/")
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of contacts for the current user."""
    contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id
    ).order_by(desc(Contact.friendliness_score)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": contact.id,
            "email": contact.email_address,
            "name": contact.name,
            "friendliness_score": contact.friendliness_score,
            "total_emails": contact.total_emails,
            "emails_sent": contact.emails_sent,
            "emails_received": contact.emails_received,
            "last_communication": contact.last_communication.isoformat() if contact.last_communication else None,
            "avg_response_time_hours": contact.avg_response_time_hours,
            "is_favorite": contact.is_favorite
        }
        for contact in contacts
    ]


@router.get("/rankings")
async def get_contact_rankings(
    ranking_type: str = Query("friendliness", regex="^(friendliness|frequency|recency|engagement)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get contact rankings by various metrics."""
    analytics_service = AnalyticsService(db)
    rankings = await analytics_service.generate_contact_rankings(current_user.id)
    
    return {
        "ranking_type": ranking_type,
        "contacts": rankings.get(f"by_{ranking_type}", [])[:20],  # Top 20
        "total_contacts": len(rankings.get(f"by_{ranking_type}", []))
    }


@router.get("/{contact_id}")
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {
        "id": contact.id,
        "email": contact.email_address,
        "name": contact.name,
        "friendliness_score": contact.friendliness_score,
        "communication_frequency": contact.communication_frequency,
        "total_emails": contact.total_emails,
        "emails_sent": contact.emails_sent,
        "emails_received": contact.emails_received,
        "last_communication": contact.last_communication.isoformat() if contact.last_communication else None,
        "avg_response_time_hours": contact.avg_response_time_hours,
        "avg_email_length": contact.avg_email_length,
        "avg_sentiment_score": contact.avg_sentiment_score,
        "is_favorite": contact.is_favorite,
        "notes": contact.notes
    }


@router.put("/{contact_id}/favorite")
async def toggle_favorite(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status for a contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_favorite = not contact.is_favorite
    db.commit()
    
    return {
        "id": contact.id,
        "is_favorite": contact.is_favorite
    }


@router.put("/{contact_id}/notes")
async def update_contact_notes(
    contact_id: int,
    notes: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notes for a contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.notes = notes
    db.commit()
    
    return {
        "id": contact.id,
        "notes": contact.notes
    }


@router.get("/analytics/friendliness")
async def get_friendliness_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get friendliness analytics for all contacts."""
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
    
    if not contacts:
        return {
            "total_contacts": 0,
            "avg_friendliness": 0.0,
            "friendliness_distribution": {"high": 0, "medium": 0, "low": 0}
        }
    
    avg_friendliness = sum(contact.friendliness_score for contact in contacts) / len(contacts)
    
    friendliness_distribution = {"high": 0, "medium": 0, "low": 0}
    for contact in contacts:
        if contact.friendliness_score >= 0.7:
            friendliness_distribution["high"] += 1
        elif contact.friendliness_score >= 0.4:
            friendliness_distribution["medium"] += 1
        else:
            friendliness_distribution["low"] += 1
    
    return {
        "total_contacts": len(contacts),
        "avg_friendliness": round(avg_friendliness, 3),
        "friendliness_distribution": friendliness_distribution,
        "top_friendly_contacts": [
            {
                "id": contact.id,
                "email": contact.email_address,
                "name": contact.name,
                "friendliness_score": contact.friendliness_score
            }
            for contact in sorted(contacts, key=lambda x: x.friendliness_score, reverse=True)[:5]
        ]
    }
