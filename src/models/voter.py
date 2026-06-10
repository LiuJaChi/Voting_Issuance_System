"""
投票者數據模型
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VoterModel(BaseModel):
    """投票者模型"""
    voter_id: str
    barcode: str
    name: Optional[str] = None
    status: str = "pending"  # pending, checked_in, voted
    checked_in_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "voter_id": "VOTER00001",
                "barcode": "VOTER00001",
                "name": "李某",
                "status": "pending",
                "checked_in_at": None,
                "created_at": "2024-06-10T10:00:00"
            }
        }