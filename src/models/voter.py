"""
投票者數據模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VoterModel(BaseModel):
    """投票者模型"""

    household_id: str
    barcode: str
    name: str
    status: str = "pending"  # pending, checked_in, voted
    checked_in_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "household_id": "06-02F",
                "barcode": "06-02F",
                "name": "李某",
                "status": "pending",
                "checked_in_at": None,
                "created_at": "2024-06-10T10:00:00"
            }
        }
