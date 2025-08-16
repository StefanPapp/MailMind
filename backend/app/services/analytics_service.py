import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from textblob import TextBlob
import openai

from app.services.interfaces import AnalyticsInterface
from app.models.email import Email, EmailAnalytics
from app.models.contact import Contact, ContactAnalytics
from app.core.config import settings


class AnalyticsService(AnalyticsInterface):
    """Analytics service for sentiment analysis and friendliness scoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    
    async def calculate_sentiment(self, text: str) -> Dict[str, float]:
        """Calculate sentiment scores for text using TextBlob and OpenAI."""
        # Clean text
        clean_text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        # TextBlob sentiment analysis
        blob = TextBlob(clean_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Convert to positive/negative/neutral scores
        if polarity > 0.1:
            positive = polarity
            negative = 0.0
            neutral = 1 - polarity
        elif polarity < -0.1:
            positive = 0.0
            negative = abs(polarity)
            neutral = 1 - abs(polarity)
        else:
            positive = 0.0
            negative = 0.0
            neutral = 1.0
        
        # OpenAI sentiment analysis (if available)
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Analyze the sentiment of the following text. Return only a JSON object with 'sentiment' (positive/negative/neutral) and 'confidence' (0-1)."
                        },
                        {
                            "role": "user",
                            "content": clean_text[:1000]  # Limit text length
                        }
                    ],
                    max_tokens=50
                )
                
                # Parse OpenAI response (simplified)
                ai_sentiment = response.choices[0].message.content.lower()
                if 'positive' in ai_sentiment:
                    positive = max(positive, 0.7)
                elif 'negative' in ai_sentiment:
                    negative = max(negative, 0.7)
                    
            except Exception as e:
                print(f"OpenAI sentiment analysis failed: {e}")
        
        return {
            'positive': round(positive, 3),
            'negative': round(negative, 3),
            'neutral': round(neutral, 3),
            'compound': round(polarity, 3),
            'subjectivity': round(subjectivity, 3)
        }
    
    async def calculate_friendliness_score(self, contact_id: int) -> float:
        """Calculate friendliness score for a contact based on multiple factors."""
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return 0.0
        
        # Get recent emails for this contact
        recent_emails = self.db.query(Email).filter(
            Email.sender == contact.email_address
        ).order_by(desc(Email.sent_at)).limit(50).all()
        
        if not recent_emails:
            return 0.0
        
        # Calculate factors
        avg_sentiment = sum(email.sentiment_score or 0 for email in recent_emails) / len(recent_emails)
        avg_length = sum(len(email.body_plain or '') for email in recent_emails) / len(recent_emails)
        response_speed = contact.avg_response_time_hours or 24.0
        
        # Normalize factors
        sentiment_weight = 0.4
        length_weight = 0.3
        speed_weight = 0.3
        
        # Length score (0-1, longer emails are friendlier)
        length_score = min(avg_length / 500, 1.0)  # Normalize to 500 words
        
        # Speed score (0-1, faster responses are friendlier)
        speed_score = max(0, 1 - (response_speed / 48))  # 48 hours = 0 score
        
        # Calculate final friendliness score
        friendliness = (
            (avg_sentiment + 1) / 2 * sentiment_weight +  # Convert -1,1 to 0,1
            length_score * length_weight +
            speed_score * speed_weight
        )
        
        return round(friendliness, 3)
    
    async def generate_contact_rankings(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate contact rankings by various metrics."""
        contacts = self.db.query(Contact).filter(Contact.user_id == user_id).all()
        
        rankings = {
            'by_friendliness': [],
            'by_frequency': [],
            'by_recency': [],
            'by_engagement': []
        }
        
        for contact in contacts:
            # Calculate friendliness score
            friendliness_score = await self.calculate_friendliness_score(contact.id)
            contact.friendliness_score = friendliness_score
            
            contact_data = {
                'id': contact.id,
                'email': contact.email_address,
                'name': contact.name,
                'friendliness_score': friendliness_score,
                'total_emails': contact.total_emails,
                'last_communication': contact.last_communication,
                'avg_response_time': contact.avg_response_time_hours
            }
            
            rankings['by_friendliness'].append(contact_data)
            rankings['by_frequency'].append(contact_data)
            rankings['by_recency'].append(contact_data)
            rankings['by_engagement'].append(contact_data)
        
        # Sort rankings
        rankings['by_friendliness'].sort(key=lambda x: x['friendliness_score'], reverse=True)
        rankings['by_frequency'].sort(key=lambda x: x['total_emails'], reverse=True)
        rankings['by_recency'].sort(key=lambda x: x['last_communication'] or datetime.min, reverse=True)
        rankings['by_engagement'].sort(key=lambda x: x['avg_response_time'] or float('inf'))
        
        self.db.commit()
        return rankings
    
    async def update_email_analytics(self, email_id: int) -> None:
        """Update analytics for a specific email."""
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return
        
        # Calculate sentiment
        text_content = email.body_plain or email.snippet or ''
        sentiment = await self.calculate_sentiment(text_content)
        
        # Calculate word count
        word_count = len(text_content.split())
        
        # Update email
        email.sentiment_score = sentiment['compound']
        email.word_count = word_count
        
        # Create or update analytics
        analytics = self.db.query(EmailAnalytics).filter(EmailAnalytics.email_id == email_id).first()
        if not analytics:
            analytics = EmailAnalytics(email_id=email_id)
            self.db.add(analytics)
        
        analytics.positive_score = sentiment['positive']
        analytics.negative_score = sentiment['negative']
        analytics.neutral_score = sentiment['neutral']
        
        self.db.commit()
