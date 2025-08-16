from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.ai_query_service import AIQueryService
from app.api.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class QueryRequest(BaseModel):
    query: str
    include_summary: bool = True


class QueryResponse(BaseModel):
    query: str
    response: str
    intent: dict
    data: List[dict]
    summary: Optional[str] = None
    timestamp: str


@router.post("/query", response_model=QueryResponse)
async def process_ai_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process natural language query and return AI-powered response."""
    try:
        ai_service = AIQueryService(db)
        result = await ai_service.process_query(request.query, current_user.id)
        
        # Generate summary if requested
        summary = None
        if request.include_summary and result.get('data'):
            summary = await ai_service.generate_summary(result['data'])
        
        return QueryResponse(
            query=result['query'],
            response=result.get('response', 'No response generated'),
            intent=result.get('intent', {}),
            data=result.get('data', []),
            summary=summary,
            timestamp=result.get('timestamp', '')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get suggested queries for the user."""
    suggestions = [
        {
            "query": "Who are my friendliest contacts?",
            "category": "contacts",
            "description": "Find contacts with the highest friendliness scores"
        },
        {
            "query": "Show me emails with positive sentiment",
            "category": "emails",
            "description": "Find emails with positive sentiment scores"
        },
        {
            "query": "What are my email trends over the last month?",
            "category": "trends",
            "description": "Analyze email patterns and trends"
        },
        {
            "query": "Who responds to my emails the fastest?",
            "category": "contacts",
            "description": "Find contacts with the quickest response times"
        },
        {
            "query": "Give me a summary of my email activity",
            "category": "summary",
            "description": "Get an overview of your email analytics"
        },
        {
            "query": "Which contacts do I communicate with most frequently?",
            "category": "contacts",
            "description": "Find your most active communication partners"
        }
    ]
    
    return {
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }


@router.post("/summarize")
async def summarize_data(
    data: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate summary for provided data."""
    try:
        ai_service = AIQueryService(db)
        summary = await ai_service.generate_summary(data)
        
        return {
            "summary": summary,
            "data_count": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/capabilities")
async def get_ai_capabilities():
    """Get information about AI capabilities."""
    return {
        "capabilities": [
            {
                "name": "Natural Language Queries",
                "description": "Ask questions about your emails in plain English",
                "examples": [
                    "Who are my friendliest contacts?",
                    "Show me emails with positive sentiment",
                    "What are my email trends?"
                ]
            },
            {
                "name": "Contact Analysis",
                "description": "Analyze contact friendliness, response times, and communication patterns",
                "metrics": [
                    "Friendliness score",
                    "Response time",
                    "Communication frequency",
                    "Email length patterns"
                ]
            },
            {
                "name": "Sentiment Analysis",
                "description": "Analyze the emotional tone of emails using AI",
                "features": [
                    "Positive/negative/neutral classification",
                    "Sentiment scoring",
                    "Trend analysis"
                ]
            },
            {
                "name": "Trend Analysis",
                "description": "Identify patterns and trends in your email communication",
                "timeframes": [
                    "Daily",
                    "Weekly", 
                    "Monthly",
                    "Custom periods"
                ]
            }
        ],
        "supported_providers": ["Gmail", "MCP"],
        "ai_models": ["OpenAI GPT-4", "TextBlob", "Custom sentiment analysis"]
    }
