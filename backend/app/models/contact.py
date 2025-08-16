from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Contact(Base):
    """Contact model for storing contact information and friendliness scores."""
    
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_address = Column(String, nullable=False)
    name = Column(String, nullable=True)
    
    # Friendliness metrics
    friendliness_score = Column(Float, default=0.0)
    communication_frequency = Column(Integer, default=0)
    avg_response_time_hours = Column(Float, nullable=True)
    avg_email_length = Column(Float, nullable=True)
    avg_sentiment_score = Column(Float, nullable=True)
    
    # Engagement metrics
    total_emails = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_received = Column(Integer, default=0)
    last_communication = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    is_favorite = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    emails = relationship("Email", back_populates="contact")
    analytics = relationship("ContactAnalytics", back_populates="contact")


class ContactAnalytics(Base):
    """Historical analytics data for contacts."""
    
    __tablename__ = "contact_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    
    # Time-based metrics
    date = Column(DateTime(timezone=True), nullable=False)
    emails_count = Column(Integer, default=0)
    sentiment_trend = Column(Float, nullable=True)
    response_time_trend = Column(Float, nullable=True)
    
    # Weekly/Monthly aggregations
    period_type = Column(String, nullable=False)  # 'daily', 'weekly', 'monthly'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="analytics")
