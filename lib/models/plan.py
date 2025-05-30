"""
Internet service plan model representing available subscription packages.
"""

from .database import Base
from sqlalchemy import Column, Integer, String, Numeric, CheckConstraint, DateTime, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import re

class InvalidSpeedError(ValueError):
    """Raised when speed format is invalid."""
    pass

class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("price >= 2000 AND price <= 100000", name="kes_price_range"),
        CheckConstraint("duration_months >= 1", name="min_duration"),
        Index('ix_plans_name', 'name', unique=True),
        {'sqlite_autoincrement': True}
    )
    
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False)
    description = Column(String(300))
    price = Column(Numeric(10, 2), nullable=False)
    speed = Column(String(30), nullable=False)
    duration_months = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    subscriptions = relationship(
        "Subscription", 
        back_populates="plan",
        lazy="dynamic"
    )

    def __str__(self):
        return f"{self.name} - {self.speed} ({self.price:.2f} KES/month)"
    
    @validates('speed')
    def validate_speed(self, key, speed):
        if not re.match(r'^\d+\s?(Mbps|Gbps)$', speed, re.IGNORECASE):
            raise InvalidSpeedError("Speed must be like '10 Mbps' or '1 Gbps'")
        return speed.strip()
    
    @validates('name')
    def validate_name(self, key, name):
        return name.strip().title()
    
    def __repr__(self):
        return (
            f"<Plan(id={self.id}, name='{self.name}', "
            f"price={self.price:.2f} KES, speed='{self.speed}')>"
        )
