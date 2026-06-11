"""
數據模型 - 用於數據驗證和序列化
"""
from typing import Optional


class CheckInRequest:
    """報到請求模型"""

    def __init__(self, household_id: str, name: Optional[str] = None):
        self.household_id = household_id
        self.name = name

    @classmethod
    def from_dict(cls, data: dict):
        """從字典創建實例"""
        household_id = str(data.get('household_id', '')).strip()
        if not household_id:
            raise ValueError('Missing required field: household_id')
        
        name = data.get('name', '').strip() if data.get('name') else None
        
        return cls(household_id=household_id, name=name)

    def to_dict(self):
        """轉換為字典"""
        return {
            'household_id': self.household_id,
            'name': self.name
        }
