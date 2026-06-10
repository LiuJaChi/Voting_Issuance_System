"""
投票紀錄數據模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VoteModel(BaseModel):
    """投票紀錄模型"""

    household_id: str
    item_id: int
    case_number: str
    vote: str  # yes, no
    voted_at: Optional[datetime] = None
    device_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "household_id": "06-02F",
                "item_id": 1,
                "case_number": "001",
                "vote": "yes",
                "voted_at": "2024-06-10T10:30:00",
                "device_id": "DEVICE_001"
            }
        }
