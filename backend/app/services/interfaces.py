from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class EmailProviderInterface(ABC):
    """Interface for email providers (Gmail, MCP, etc.)."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the email provider."""
        pass
    
    @abstractmethod
    async def fetch_emails(self, user_id: int, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch emails from the provider."""
        pass
    
    @abstractmethod
    async def sync_incremental(self, user_id: int, last_sync: datetime) -> List[Dict[str, Any]]:
        """Perform incremental sync of emails."""
        pass


class AnalyticsInterface(ABC):
    """Interface for analytics services."""
    
    @abstractmethod
    async def calculate_sentiment(self, text: str) -> Dict[str, float]:
        """Calculate sentiment scores for text."""
        pass
    
    @abstractmethod
    async def calculate_friendliness_score(self, contact_id: int) -> float:
        """Calculate friendliness score for a contact."""
        pass
    
    @abstractmethod
    async def generate_contact_rankings(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate contact rankings by various metrics."""
        pass


class AIQueryInterface(ABC):
    """Interface for AI query processing."""
    
    @abstractmethod
    async def process_query(self, query: str, user_id: int) -> Dict[str, Any]:
        """Process natural language query and return results."""
        pass
    
    @abstractmethod
    async def generate_summary(self, data: List[Dict[str, Any]]) -> str:
        """Generate summary of data."""
        pass


class ExportInterface(ABC):
    """Interface for export services."""
    
    @abstractmethod
    async def export_to_pdf(self, data: List[Dict[str, Any]], format_type: str) -> bytes:
        """Export data to PDF format."""
        pass
    
    @abstractmethod
    async def export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """Export data to CSV format."""
        pass
    
    @abstractmethod
    async def export_to_json(self, data: List[Dict[str, Any]]) -> str:
        """Export data to JSON format."""
        pass
