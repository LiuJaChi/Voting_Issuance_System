"""
投票紀錄數據模型
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VoteModel(BaseModel):
    """投票紀錄模型（以戶號+案號為複合主鍵）"""
    household_id: str   # 戶號（複合主鍵之一）
    case_number: str    # 案號（複合主鍵之一）
    vote: str           # yes, no
    voted_at: Optional[datetime] = None
    device_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "household_id": "06-02F",
                "case_number": "001",
                "vote": "yes",
                "voted_at": "2024-06-10T10:30:00",
                "device_id": "DEVICE_001"
            }
        }
