import json
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.services.interfaces import EmailProviderInterface
from app.models.user import User
from app.models.email import Email
from app.core.config import settings


class GmailService(EmailProviderInterface):
    """Gmail service implementation using OAuth 2.0 and Gmail API."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, db: Session):
        self.db = db
        self.service = None
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Gmail using OAuth 2.0."""
        try:
            creds = Credentials.from_authorized_user_info(credentials)
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    async def fetch_emails(self, user_id: int, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail API."""
        if not self.service:
            raise Exception("Gmail service not authenticated")
        
        try:
            # Build query for emails
            query = "in:inbox"
            if since:
                query += f" after:{since.strftime('%Y/%m/%d')}"
            
            # Get list of email IDs
            results = self.service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = await self._fetch_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as error:
            print(f"Gmail API error: {error}")
            return []
    
    async def sync_incremental(self, user_id: int, last_sync: datetime) -> List[Dict[str, Any]]:
        """Perform incremental sync of emails."""
        return await self.fetch_emails(user_id, since=last_sync)
    
    async def _fetch_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific email."""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                sent_at = parsedate_to_datetime(date_str)
            except:
                sent_at = datetime.now()
            
            # Get body content
            body = self._extract_body(message['payload'])
            
            return {
                'gmail_id': message_id,
                'subject': subject,
                'sender': sender,
                'sent_at': sent_at,
                'body_plain': body.get('plain', ''),
                'body_html': body.get('html', ''),
                'snippet': message.get('snippet', ''),
                'thread_id': message.get('threadId', ''),
                'labels': message.get('labelIds', [])
            }
            
        except HttpError as error:
            print(f"Error fetching email {message_id}: {error}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract plain text and HTML body from email payload."""
        body = {'plain': '', 'html': ''}
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body['plain'] = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    body['html'] = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                body['plain'] = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                body['html'] = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body
