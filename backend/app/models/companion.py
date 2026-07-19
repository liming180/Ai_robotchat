"""
Companion database models.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Companion(Base):
    """
    AI Companion model.
    Includes both preset companions and user-created companions.
    """
    __tablename__ = "companions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    avatar = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    personality = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    is_preset = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    creator = relationship("User", backref="companions")


class UserCompanion(Base):
    """
    User-Companion relationship model.
    Stores favorite status and intimacy level.
    """
    __tablename__ = "user_companions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    companion_id = Column(UUID(as_uuid=True), ForeignKey("companions.id"), nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    intimacy = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="user_companions")
    companion = relationship("Companion", backref="user_companions")
