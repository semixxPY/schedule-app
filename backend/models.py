from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, index=True)
    type = Column(String, index=True)
    date = Column(String, index=True)
    start_time = Column(String)
    end_time = Column(String)
    notes = Column(String, nullable=True)
    is_plan = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now(), onupdate=func.now())

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reminder_time = Column(String, default="20:00")
    enable_reminders = Column(Boolean, default=True)
    enable_ai = Column(Boolean, default=True)
