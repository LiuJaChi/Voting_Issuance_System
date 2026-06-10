"""
投票項目數據模型
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VotingItemModel(BaseModel):
    """投票項目模型"""
    id: Optional[int] = None
    case_number: str       # 案號，例如 001、002
    name: str              # 項目名稱
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "case_number": "001",
                "name": "第一案：社區費用調整",
                "description": "調整社區管理費",
                "created_at": "2024-06-10T10:00:00"
            }
        }
