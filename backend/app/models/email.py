from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Email(Base):
    """Email model for storing email data and metadata."""
    
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Email metadata
    subject = Column(String, nullable=True)
    sender = Column(String, nullable=False)
    recipients = Column(Text, nullable=True)  # JSON array of email addresses
    cc = Column(Text, nullable=True)  # JSON array
    bcc = Column(Text, nullable=True)  # JSON array
    thread_id = Column(String, nullable=True)
    
    # Content
    body_plain = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Analytics fields
    word_count = Column(Integer, default=0)
    sentiment_score = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="emails")
    analytics = relationship("EmailAnalytics", back_populates="email", uselist=False)
    contact = relationship("Contact", back_populates="emails")


class EmailAnalytics(Base):
    """Analytics data for individual emails."""
    
    __tablename__ = "email_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    
    # Response time analysis
    response_time_hours = Column(Float, nullable=True)
    is_response = Column(Boolean, default=False)
    original_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    
    # Engagement metrics
    read_time_seconds = Column(Integer, nullable=True)
    reply_likelihood = Column(Float, nullable=True)
    
    # Sentiment analysis
    positive_score = Column(Float, nullable=True)
    negative_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    email = relationship("Email", back_populates="analytics")
