from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.email import Email
from app.services.gmail_service import GmailService
from app.services.mcp_service import MCPService
from app.services.analytics_service import AnalyticsService
from app.api.auth import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/")
async def get_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of emails for the current user."""
    emails = db.query(Email).filter(
        Email.user_id == current_user.id
    ).order_by(desc(Email.sent_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": email.id,
            "gmail_id": email.gmail_id,
            "subject": email.subject,
            "sender": email.sender,
            "sent_at": email.sent_at.isoformat(),
            "snippet": email.snippet,
            "sentiment_score": email.sentiment_score,
            "word_count": email.word_count,
            "is_read": email.is_read,
            "is_starred": email.is_starred
        }
        for email in emails
    ]


@router.get("/{email_id}")
async def get_email(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific email."""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "id": email.id,
        "gmail_id": email.gmail_id,
        "subject": email.subject,
        "sender": email.sender,
        "recipients": email.recipients,
        "cc": email.cc,
        "bcc": email.bcc,
        "body_plain": email.body_plain,
        "body_html": email.body_html,
        "snippet": email.snippet,
        "sent_at": email.sent_at.isoformat(),
        "received_at": email.received_at.isoformat(),
        "sentiment_score": email.sentiment_score,
        "word_count": email.word_count,
        "is_read": email.is_read,
        "is_starred": email.is_starred,
        "is_important": email.is_important,
        "thread_id": email.thread_id
    }


@router.post("/sync")
async def sync_emails(
    provider: str = Query("gmail", regex="^(gmail|mcp)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync emails from the specified provider."""
    try:
        if provider == "gmail":
            if not current_user.gmail_access_token:
                raise HTTPException(status_code=400, detail="Gmail not connected")
            
            service = GmailService(db)
            credentials = {
                "token": current_user.gmail_access_token,
                "refresh_token": current_user.gmail_refresh_token,
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "scopes": GmailService.SCOPES
            }
            
            if not await service.authenticate(credentials):
                raise HTTPException(status_code=401, detail="Gmail authentication failed")
        
        elif provider == "mcp":
            service = MCPService(db)
            credentials = {"user_id": current_user.id}
            
            if not await service.authenticate(credentials):
                raise HTTPException(status_code=401, detail="MCP authentication failed")
        
        # Get last sync time
        last_email = db.query(Email).filter(
            Email.user_id == current_user.id
        ).order_by(desc(Email.sent_at)).first()
        
        last_sync = last_email.sent_at if last_email else datetime.now() - timedelta(days=30)
        
        # Fetch new emails
        new_emails = await service.sync_incremental(current_user.id, last_sync)
        
        # Process and store emails
        analytics_service = AnalyticsService(db)
        synced_count = 0
        
        for email_data in new_emails:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.gmail_id == email_data['gmail_id'],
                Email.user_id == current_user.id
            ).first()
            
            if not existing:
                email = Email(
                    user_id=current_user.id,
                    gmail_id=email_data['gmail_id'],
                    subject=email_data.get('subject'),
                    sender=email_data['sender'],
                    body_plain=email_data.get('body_plain'),
                    body_html=email_data.get('body_html'),
                    snippet=email_data.get('snippet'),
                    sent_at=email_data['sent_at'],
                    received_at=email_data.get('received_at', email_data['sent_at']),
                    thread_id=email_data.get('thread_id')
                )
                
                db.add(email)
                db.flush()  # Get the email ID
                
                # Calculate analytics
                await analytics_service.update_email_analytics(email.id)
                synced_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully synced {synced_count} new emails",
            "synced_count": synced_count,
            "provider": provider
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/analytics/sentiment")
async def get_sentiment_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sentiment analytics for emails."""
    since_date = datetime.now() - timedelta(days=days)
    
    emails = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.sent_at >= since_date,
        Email.sentiment_score.isnot(None)
    ).all()
    
    if not emails:
        return {
            "total_emails": 0,
            "avg_sentiment": 0.0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
        }
    
    avg_sentiment = sum(email.sentiment_score for email in emails) / len(emails)
    
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    for email in emails:
        if email.sentiment_score > 0.1:
            sentiment_distribution["positive"] += 1
        elif email.sentiment_score < -0.1:
            sentiment_distribution["negative"] += 1
        else:
            sentiment_distribution["neutral"] += 1
    
    return {
        "total_emails": len(emails),
        "avg_sentiment": round(avg_sentiment, 3),
        "sentiment_distribution": sentiment_distribution,
        "period_days": days
    }


@router.get("/analytics/trends")
async def get_email_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get email trends over time."""
    since_date = datetime.now() - timedelta(days=days)
    
    # Get daily email counts
    from sqlalchemy import func, cast, Date
    
    daily_counts = db.query(
        cast(Email.sent_at, Date).label('date'),
        func.count(Email.id).label('count')
    ).filter(
        Email.user_id == current_user.id,
        Email.sent_at >= since_date
    ).group_by(
        cast(Email.sent_at, Date)
    ).order_by(
        cast(Email.sent_at, Date)
    ).all()
    
    return {
        "daily_counts": [
            {"date": str(count.date), "count": count.count}
            for count in daily_counts
        ],
        "period_days": days
    }
