"""
Customer model representing internet service subscribers.
"""

from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import re

class InvalidEmailError(ValueError):
    """Raised when email validation fails."""
    pass

class InvalidPhoneError(ValueError):
    """Raised when phone number validation fails."""
    pass

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index('ix_customers_email', 'email', unique=True),
        Index('ix_customers_router_id', 'router_id', unique=True),
        {'sqlite_autoincrement': True}
    )
    
    id = Column(Integer, primary_key=True)
    router_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(String(200))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    subscriptions = relationship(
        "Subscription", 
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __str__(self):
        return f"{self.name} (Router: {self.router_id})"
    
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise InvalidEmailError("Invalid email format")
        return email.lower().strip()
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if not phone:
            return None
        cleaned = re.sub(r'[^\d+]', '', phone)
        if cleaned.startswith('0') and len(cleaned) == 10:
            cleaned = '+254' + cleaned[1:]
        if not re.match(r'^\+2547[0-247-9]\d{7}$', cleaned):
            raise InvalidPhoneError("Invalid Kenyan phone. Use +2547XXXXXXXX or 07XXXXXXXX")
        return cleaned

    def __repr__(self):
        return (
            f"<Customer(id={self.id}, name='{self.name}', "
            f"email='{self.email}', router_id={self.router_id})>"
        )
