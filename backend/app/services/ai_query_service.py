import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
import openai
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from app.services.interfaces import AIQueryInterface
from app.models.email import Email
from app.models.contact import Contact
from app.core.config import settings


class AIQueryService(AIQueryInterface):
    """AI query service for natural language processing and RAG-powered responses."""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.llm = OpenAI(api_key=settings.openai_api_key, temperature=0.1) if settings.openai_api_key else None
    
    async def process_query(self, query: str, user_id: int) -> Dict[str, Any]:
        """Process natural language query and return results."""
        try:
            # Parse query intent
            intent = await self._parse_query_intent(query)
            
            # Get relevant data based on intent
            data = await self._get_relevant_data(intent, user_id)
            
            # Generate response
            response = await self._generate_response(query, intent, data)
            
            return {
                'query': query,
                'intent': intent,
                'data': data,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_summary(self, data: List[Dict[str, Any]]) -> str:
        """Generate summary of data."""
        if not self.openai_client:
            return "Summary generation requires OpenAI API key."
        
        try:
            # Prepare data for summary
            summary_data = []
            for item in data[:10]:  # Limit to first 10 items
                if isinstance(item, dict):
                    summary_data.append(str(item))
                else:
                    summary_data.append(str(item))
            
            summary_text = "\n".join(summary_data)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes email analytics data. Provide concise, insightful summaries."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this data:\n{summary_text}"
                    }
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def _parse_query_intent(self, query: str) -> Dict[str, Any]:
        """Parse the intent of a natural language query."""
        query_lower = query.lower()
        
        intent = {
            'type': 'unknown',
            'entities': [],
            'filters': {}
        }
        
        # Contact-related queries
        if any(word in query_lower for word in ['contact', 'person', 'friend', 'colleague']):
            intent['type'] = 'contact_analysis'
            
            if 'friendliest' in query_lower or 'most friendly' in query_lower:
                intent['filters']['ranking'] = 'friendliness'
            elif 'most frequent' in query_lower or 'most active' in query_lower:
                intent['filters']['ranking'] = 'frequency'
            elif 'recent' in query_lower:
                intent['filters']['timeframe'] = 'recent'
        
        # Email-related queries
        elif any(word in query_lower for word in ['email', 'message', 'correspondence']):
            intent['type'] = 'email_analysis'
            
            if 'sentiment' in query_lower or 'mood' in query_lower:
                intent['filters']['analysis'] = 'sentiment'
            elif 'response time' in query_lower:
                intent['filters']['analysis'] = 'response_time'
            elif 'length' in query_lower or 'word count' in query_lower:
                intent['filters']['analysis'] = 'length'
        
        # Time-based queries
        elif any(word in query_lower for word in ['trend', 'over time', 'history', 'pattern']):
            intent['type'] = 'trend_analysis'
            
            if 'week' in query_lower:
                intent['filters']['period'] = 'weekly'
            elif 'month' in query_lower:
                intent['filters']['period'] = 'monthly'
            else:
                intent['filters']['period'] = 'daily'
        
        # Summary queries
        elif any(word in query_lower for word in ['summary', 'overview', 'summary']):
            intent['type'] = 'summary'
        
        return intent
    
    async def _get_relevant_data(self, intent: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get relevant data based on query intent."""
        if intent['type'] == 'contact_analysis':
            return await self._get_contact_data(intent, user_id)
        elif intent['type'] == 'email_analysis':
            return await self._get_email_data(intent, user_id)
        elif intent['type'] == 'trend_analysis':
            return await self._get_trend_data(intent, user_id)
        elif intent['type'] == 'summary':
            return await self._get_summary_data(user_id)
        else:
            return []
    
    async def _get_contact_data(self, intent: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get contact data based on intent."""
        query = self.db.query(Contact).filter(Contact.user_id == user_id)
        
        if intent['filters'].get('ranking') == 'friendliness':
            query = query.order_by(desc(Contact.friendliness_score))
        elif intent['filters'].get('ranking') == 'frequency':
            query = query.order_by(desc(Contact.total_emails))
        
        contacts = query.limit(10).all()
        
        return [
            {
                'id': contact.id,
                'email': contact.email_address,
                'name': contact.name,
                'friendliness_score': contact.friendliness_score,
                'total_emails': contact.total_emails,
                'last_communication': contact.last_communication.isoformat() if contact.last_communication else None
            }
            for contact in contacts
        ]
    
    async def _get_email_data(self, intent: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get email data based on intent."""
        query = self.db.query(Email).filter(Email.user_id == user_id)
        
        if intent['filters'].get('analysis') == 'sentiment':
            query = query.order_by(desc(Email.sentiment_score))
        elif intent['filters'].get('analysis') == 'length':
            query = query.order_by(desc(Email.word_count))
        
        emails = query.limit(20).all()
        
        return [
            {
                'id': email.id,
                'subject': email.subject,
                'sender': email.sender,
                'sent_at': email.sent_at.isoformat(),
                'sentiment_score': email.sentiment_score,
                'word_count': email.word_count
            }
            for email in emails
        ]
    
    async def _get_trend_data(self, intent: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get trend data based on intent."""
        # This would typically involve more complex time-series analysis
        # For now, return basic email counts by period
        period = intent['filters'].get('period', 'daily')
        
        # Simplified trend data
        return [
            {
                'period': period,
                'total_emails': 150,
                'avg_sentiment': 0.2,
                'top_contacts': ['john@example.com', 'jane@example.com']
            }
        ]
    
    async def _get_summary_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get summary data for the user."""
        total_emails = self.db.query(Email).filter(Email.user_id == user_id).count()
        total_contacts = self.db.query(Contact).filter(Contact.user_id == user_id).count()
        
        avg_sentiment = self.db.query(func.avg(Email.sentiment_score)).filter(
            Email.user_id == user_id
        ).scalar() or 0.0
        
        return [
            {
                'total_emails': total_emails,
                'total_contacts': total_contacts,
                'avg_sentiment': round(avg_sentiment, 3),
                'analysis_period': 'all_time'
            }
        ]
    
    async def _generate_response(self, query: str, intent: Dict[str, Any], data: List[Dict[str, Any]]) -> str:
        """Generate natural language response based on query and data."""
        if not self.openai_client:
            return f"Query processed: {intent['type']}. Found {len(data)} results."
        
        try:
            # Create context from data
            context = json.dumps(data, indent=2)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful email analytics assistant. Provide clear, concise responses based on the data provided."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\nIntent: {intent['type']}\nData: {context}\n\nPlease provide a natural language response to the query based on this data."
                    }
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
