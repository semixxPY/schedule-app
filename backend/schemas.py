from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime

# 活动基础模型
class ActivityBase(BaseModel):
    title: str
    type: str = Field(..., pattern=r"^(学习/工作|休息|运动/娱乐|通勤/家务/吃饭)$")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    notes: Optional[str] = None
    is_plan: Optional[bool] = False

# 创建活动模型（不含ID）
class ActivityCreate(ActivityBase):
    id: str  # 客户端生成的唯一ID

# 更新活动模型（所有字段可选）
class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = Field(None, pattern=r"^(学习/工作|休息|运动/娱乐|通勤/家务/吃饭)$")
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    notes: Optional[str] = None
    is_plan: Optional[bool] = None

# 活动响应模型
class ActivityResponse(ActivityBase):
    id: str
    title: str
    type: str
    date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None
    is_plan: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """将 datetime 对象序列化为 ISO 格式字符串"""
        if value is None:
            return None
        return value.isoformat() if isinstance(value, datetime) else value
# 用户设置模型
class UserSettingsBase(BaseModel):
    reminder_time: str = Field("20:00", pattern=r"^\d{2}:\d{2}$")
    enable_reminders: bool = True
    enable_ai: bool = True

# 用户设置响应模型
class UserSettingsResponse(UserSettingsBase):
    id: int
    
    class Config:
        from_attributes = True