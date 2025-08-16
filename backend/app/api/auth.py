from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.gmail_service import GmailService
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/gmail/authorize")
async def authorize_gmail(db: Session = Depends(get_db)):
    """Initiate Gmail OAuth authorization."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.gmail_redirect_uri]
                }
            },
            GmailService.SCOPES
        )
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        return {"auth_url": auth_url}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")


@router.post("/gmail/callback")
async def gmail_callback(code: str, db: Session = Depends(get_db)):
    """Handle Gmail OAuth callback."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.gmail_redirect_uri]
                }
            },
            GmailService.SCOPES
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info from Gmail
        from googleapiclient.discovery import build
        gmail_service = GmailService(db)
        gmail_service.service = build('gmail', 'v1', credentials=credentials)
        
        profile = gmail_service.service.users().getProfile(userId='me').execute()
        email = profile['emailAddress']
        
        # Create or update user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                gmail_access_token=credentials.token,
                gmail_refresh_token=credentials.refresh_token,
                gmail_token_expires_at=credentials.expiry
            )
            db.add(user)
        else:
            user.gmail_access_token = credentials.token
            user.gmail_refresh_token = credentials.refresh_token
            user.gmail_token_expires_at = credentials.expiry
        
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Callback failed: {str(e)}")


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login to get access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified
    }
