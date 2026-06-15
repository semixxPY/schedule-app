from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

# 活动模型
class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String, index=True)  # 学习/工作、休息、运动/娱乐、通勤/家务/吃饭
    date = Column(String, index=True)  # YYYY-MM-DD格式
    start_time = Column(String)  # HH:mm格式
    end_time = Column(String)    # HH:mm格式
    notes = Column(String, nullable=True)
    is_plan = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now(), onupdate=func.now())

# 用户设置模型
class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_time = Column(String, default="20:00")
    enable_reminders = Column(Boolean, default=True)
    enable_ai = Column(Boolean, default=True)