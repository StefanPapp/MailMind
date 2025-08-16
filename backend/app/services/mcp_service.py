import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.interfaces import EmailProviderInterface
from app.core.config import settings


class MCPService(EmailProviderInterface):
    """MCP (Model Context Protocol) service implementation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = settings.mcp_server_url
        self.api_key = settings.mcp_api_key
        self.client = httpx.AsyncClient()
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with MCP server."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.post(
                f"{self.base_url}/auth",
                headers=headers,
                json=credentials
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"MCP authentication failed: {e}")
            return False
    
    async def fetch_emails(self, user_id: int, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch emails via MCP."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {"user_id": user_id}
            if since:
                params["since"] = since.isoformat()
            
            response = await self.client.get(
                f"{self.base_url}/emails",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"MCP fetch emails failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"MCP fetch emails error: {e}")
            return []
    
    async def sync_incremental(self, user_id: int, last_sync: datetime) -> List[Dict[str, Any]]:
        """Perform incremental sync via MCP."""
        return await self.fetch_emails(user_id, since=last_sync)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
