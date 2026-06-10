"""
實用工具函數
"""
import hashlib
from datetime import datetime
from typing import List


def generate_voter_id(prefix: str = "VOTER", index: int = 1) -> str:
    """生成內部流水號"""
    return f"{prefix}{index:05d}"


def generate_barcode(household_id: str) -> str:
    """根據戶號生成條碼內容"""
    return (household_id or "").strip().upper()


def hash_barcode(barcode: str) -> str:
    """對條碼進行哈希"""
    return hashlib.sha256(barcode.encode()).hexdigest()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期時間"""
    if isinstance(dt, str):
        return dt
    return dt.strftime(format_str) if dt else ""


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析日期時間字符串"""
    return datetime.strptime(date_str, format_str)


def get_current_timestamp() -> str:
    """獲取當前時間戳"""
    return datetime.now().isoformat()


def batch_generate_voter_ids(count: int, prefix: str = "VOTER") -> List[str]:
    """批量生成內部流水號"""
    return [generate_voter_id(prefix, i) for i in range(1, count + 1)]


def batch_generate_barcodes(household_ids: List[str]) -> List[str]:
    """批量生成戶號條碼內容"""
    return [generate_barcode(household_id) for household_id in household_ids]


def validate_barcode(barcode: str) -> bool:
    """驗證條碼格式"""
    return bool((barcode or "").strip())


def validate_vote(vote: str) -> bool:
    """驗證投票選項"""
    return vote.lower() in ['yes', 'no', '贊成', '反對']


def normalize_vote(vote: str) -> str:
    """規範化投票選項"""
    vote_lower = vote.lower()
    if vote_lower in ['yes', '贊成']:
        return 'yes'
    if vote_lower in ['no', '反對']:
        return 'no'
    return vote_lower
