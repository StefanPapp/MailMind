import re
import json
from typing import List, Dict, Any
from datetime import datetime
from email.utils import parsedate_to_datetime


def extract_email_address(email_string: str) -> str:
    """Extract email address from various formats."""
    if not email_string:
        return ""
    
    # Remove display name if present (e.g., "John Doe <john@example.com>")
    match = re.search(r'<(.+?)>', email_string)
    if match:
        return match.group(1).strip()
    
    # Return as is if no angle brackets
    return email_string.strip()


def parse_email_headers(headers: List[Dict[str, str]]) -> Dict[str, Any]:
    """Parse email headers into structured data."""
    parsed = {}
    
    for header in headers:
        name = header.get('name', '').lower()
        value = header.get('value', '')
        
        if name == 'from':
            parsed['sender'] = extract_email_address(value)
        elif name == 'to':
            parsed['recipients'] = [extract_email_address(addr) for addr in value.split(',')]
        elif name == 'cc':
            parsed['cc'] = [extract_email_address(addr) for addr in value.split(',')]
        elif name == 'bcc':
            parsed['bcc'] = [extract_email_address(addr) for addr in value.split(',')]
        elif name == 'subject':
            parsed['subject'] = value
        elif name == 'date':
            try:
                parsed['sent_at'] = parsedate_to_datetime(value)
            except:
                parsed['sent_at'] = datetime.now()
    
    return parsed


def clean_email_text(text: str) -> str:
    """Clean email text for analysis."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove email signatures (common patterns)
    text = re.sub(r'--\s*\n.*', '', text, flags=re.DOTALL)
    text = re.sub(r'Sent from my iPhone.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Get Outlook for.*', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def calculate_word_count(text: str) -> int:
    """Calculate word count in text."""
    if not text:
        return 0
    
    clean_text = clean_email_text(text)
    words = clean_text.split()
    return len(words)


def extract_contacts_from_emails(emails: List[Dict[str, Any]]) -> List[str]:
    """Extract unique contact email addresses from emails."""
    contacts = set()
    
    for email in emails:
        sender = email.get('sender', '')
        if sender:
            contacts.add(extract_email_address(sender))
        
        recipients = email.get('recipients', [])
        for recipient in recipients:
            if recipient:
                contacts.add(extract_email_address(recipient))
    
    return list(contacts)


def format_email_summary(email: Dict[str, Any]) -> str:
    """Format email for summary display."""
    subject = email.get('subject', 'No Subject')
    sender = email.get('sender', 'Unknown')
    sent_at = email.get('sent_at', datetime.now())
    
    if isinstance(sent_at, datetime):
        date_str = sent_at.strftime('%Y-%m-%d %H:%M')
    else:
        date_str = str(sent_at)
    
    return f"{date_str} - {sender}: {subject}"
