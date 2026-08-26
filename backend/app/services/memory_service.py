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
        memories = self.db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.keyword.ilike(f"%{keyword}%")
        ).all()
        
        # 如果没找到，返回一些示例数据（演示用）
        if not memories:
            return self._get_sample_memories(user_id, keyword)
        
        return memories
    
    def _get_sample_memories(self, user_id: str, keyword: str) -> List[UserMemory]:
        """获取示例记忆数据（演示用）"""
        samples = []
        
        sample_data = {
            "生日": f"用户 {user_id} 的生日是10月1日，天秤座",
            "喜欢": f"用户 {user_id} 喜欢喝咖啡、听音乐和看书",
            "宠物": f"用户 {user_id} 有一只叫小白的白色猫咪",
            "食物": f"用户 {user_id} 喜欢吃火锅和川菜，不喜欢太甜的东西",
            "工作": f"用户 {user_id} 是一名程序员，工作很忙，经常加班"
        }
        
        for k, v in sample_data.items():
            if keyword in k or keyword in v:
                memory = UserMemory(
                    user_id=user_id,
                    memory_type="fact",
                    keyword=k,
                    content=v,
                    created_at=datetime.now()
                )
                samples.append(memory)
        
        return samples
    
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
        cutoff_date = datetime.now() - timedelta(days=days)
        moods = self.db.query(UserMood).filter(
            UserMood.user_id == user_id,
            UserMood.created_at >= cutoff_date
        ).order_by(UserMood.created_at.desc()).all()
        
        # 如果没有数据，返回示例数据（演示用）
        if not moods:
            return self._get_sample_moods(user_id, days)
        
        return moods
    
    def _get_sample_moods(self, user_id: str, days: int) -> List[UserMood]:
        """获取示例心情数据（演示用）"""
        sample_moods = []
        moods_config = [
            ("开心", 8.5, "今天项目上线成功！"),
            ("平静", 6.0, "工作顺利，一切如常"),
            ("疲惫", 4.0, "加班到很晚"),
            ("难过", 3.0, "遇到了一些困难"),
            ("兴奋", 9.0, "有开心的事情发生！"),
            ("平静", 7.0, "享受周末时光")
        ]
        
        for i, (mood, score, note) in enumerate(moods_config[:days]):
            sample_moods.append(UserMood(
                user_id=user_id,
                mood=mood,
                score=score,
                note=note,
                created_at=datetime.now() - timedelta(days=i)
            ))
        
        return sample_moods
    
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
