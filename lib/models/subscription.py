"""
Subscription model representing customer-plan relationships.
"""

from .database import Base
from sqlalchemy import Column, Integer, Date, ForeignKey, String, CheckConstraint, DateTime, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import datetime

class InvalidSubscriptionDateError(ValueError):
    """Raised when subscription dates are invalid."""
    pass

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="valid_end_date"),
        CheckConstraint("status IN ('active', 'suspended', 'terminated', 'expired')", name="valid_status"),
        CheckConstraint("router_id BETWEEN 1000000000 AND 9999999999", name="valid_router_id"),
        Index('ix_subscriptions_router_id', 'router_id', unique=True),
        Index('ix_subscriptions_status', 'status'),
        {'sqlite_autoincrement': True}
    )

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete="CASCADE"))
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete="RESTRICT"))
    router_id = Column(Integer, nullable=False)
    start_date = Column(Date, server_default=func.current_date())
    end_date = Column(Date)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    last_reminder_sent = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

    def __str__(self):
        status_icon = {
            'active': '✓',
            'suspended': '⚠',
            'terminated': '✗',
            'expired': '⌛'
        }.get(self.status, '?')
        
        return (
            f"{status_icon} Subscription #{self.id} - "
            f"{self.plan.name if self.plan else 'No Plan'} "
            f"(Since: {self.start_date})"
        )
    
    @validates('start_date')
    def validate_start_date(self, key, start_date):
        if start_date < datetime.date.today():
            raise InvalidSubscriptionDateError("Start date cannot be in the past")
        return start_date
    
    def is_active(self):
        today = datetime.date.today()
        return (
            self.status == 'active' and 
            (self.end_date is None or self.end_date >= today)
        )
    
    def days_remaining(self):
        if not self.end_date:
            return None
        return (self.end_date - datetime.date.today()).days
    
    def __repr__(self):
        return (
            f"<Subscription(id={self.id}, customer={self.customer_id}, "
            f"plan={self.plan_id}, status='{self.status}', "
            f"router_id={self.router_id})>"
        )
