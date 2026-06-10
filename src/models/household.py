"""
住戶數據模型
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class HouseholdModel(BaseModel):
    """住戶模型"""
    household_id: str  # 戶號，例如 06-02F
    name: str          # 姓名
    status: str = "pending"  # pending, checked_in, voted
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "household_id": "06-02F",
                "name": "李某",
                "status": "pending",
                "created_at": "2024-06-10T10:00:00"
            }
        }
