"""
配置數據模型
"""
from typing import Optional
from pydantic import BaseModel


class ConfigModel(BaseModel):
    """系統配置模型"""
    system_name: str
    total_participants: int
    pass_percentage: float
    barcode_prefix: str = "VOTER"
    device_id: str = "DEVICE_001"
    theme: str = "light"
    language: str = "zh_TW"
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "2024年度大會",
                "total_participants": 100,
                "pass_percentage": 66.7,
                "barcode_prefix": "VOTER",
                "device_id": "DEVICE_001",
                "theme": "light",
                "language": "zh_TW"
            }
        }
