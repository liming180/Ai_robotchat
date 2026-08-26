"""
用户记忆和心情数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Index
from sqlalchemy.sql import func
from app.database import Base


class UserMemory(Base):
    """用户记忆表 - 存储用户的重要信息"""
    __tablename__ = "user_memories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # preference, fact, birthday等
    keyword = Column(String(100), nullable=False)  # 搜索关键词
    content = Column(Text, nullable=False)  # 记忆内容
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_user_memory_type", "user_id", "memory_type"),
    )


class UserMood(Base):
    """用户心情记录表 - 存储用户的历史心情数据"""
    __tablename__ = "user_moods"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    mood = Column(String(50), nullable=False)  # happy, calm, tired, sad等
    score = Column(Float, default=5.0)  # 心情分数1-10
    note = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_user_mood_time", "user_id", "created_at"),
    )
