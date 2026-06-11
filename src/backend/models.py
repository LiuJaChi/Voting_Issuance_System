"""即時報到 API 的數據模型"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class CheckInRequest:
    household_id: str
    name: str = ''
    status: str = 'checked_in'

    @classmethod
    def from_dict(cls, data: Dict):
        household_id = str(data.get('household_id', '')).strip()
        name = str(data.get('name', '')).strip()
        status = str(data.get('status', 'checked_in')).strip() or 'checked_in'

        if not household_id:
            raise ValueError('household_id is required')

        return cls(household_id=household_id, name=name, status=status)
