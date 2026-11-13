"""
记忆服务模块 - 处理用户记忆和心情数据的CRUD操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.memory import UserMemory, UserMood


class MemoryService:
    """记忆服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_user_memory(self, user_id: str, keyword: str) -> List[UserMemory]:
        """搜索用户记忆"""
        try:
            memories = self.db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.keyword.ilike(f"%{keyword}%")
            ).all()

            # 查不到就是没有：返回空列表，由前端展示空态。
            # （历史版本这里返回示例假数据，导致新账号一进记忆页就看到“别人的记忆”，已按 P1-2 清理）
            return memories
        except Exception as e:
            print(f"[MemoryService] 查询记忆失败: {e}")
            return []
    
    def add_user_memory(self, user_id: str, memory_type: str, keyword: str, content: str) -> UserMemory:
        """添加用户记忆"""
        memory = UserMemory(
            user_id=user_id,
            memory_type=memory_type,
            keyword=keyword,
            content=content,
            created_at=datetime.now()
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory


class MoodService:
    """心情服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_mood_history(self, user_id: str, days: int = 7) -> List[UserMood]:
        """获取用户最近的心情历史"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            moods = self.db.query(UserMood).filter(
                UserMood.user_id == user_id,
                UserMood.created_at >= cutoff_date
            ).order_by(UserMood.created_at.desc()).all()

            # 同理：没有记录就返回空列表，不再伪造示例心情（P1-2 第 2 项）
            return moods
        except Exception as e:
            print(f"[MoodService] 查询心情历史失败: {e}")
            return []
    
    def add_user_mood(self, user_id: str, mood: str, score: float, note: Optional[str] = None) -> UserMood:
        """记录用户心情"""
        mood_rec = UserMood(
            user_id=user_id,
            mood=mood,
            score=score,
            note=note,
            created_at=datetime.now()
        )
        self.db.add(mood_rec)
        self.db.commit()
        self.db.refresh(mood_rec)
        return mood_rec
