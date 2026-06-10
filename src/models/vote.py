"""
投票紀錄數據模型
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VoteModel(BaseModel):
    """投票紀錄模型"""
    voter_id: str
    item_id: int
    vote: str  # yes, no
    voted_at: Optional[datetime] = None
    device_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "voter_id": "VOTER00001",
                "item_id": 1,
                "vote": "yes",
                "voted_at": "2024-06-10T10:30:00",
                "device_id": "DEVICE_001"
            }
        }