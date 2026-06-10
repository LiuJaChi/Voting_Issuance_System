"""
實用工具函數
"""
import hashlib
from datetime import datetime
from typing import List


def generate_voter_id(prefix: str = "VOTER", index: int = 1) -> str:
    """生成投票者 ID"""
    return f"{prefix}{index:05d}"


def generate_barcode(voter_id: str) -> str:
    """根據投票者 ID 生成條碼"""
    return voter_id


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
    """批量生成投票者 ID"""
    return [generate_voter_id(prefix, i) for i in range(1, count + 1)]


def batch_generate_barcodes(voter_ids: List[str]) -> List[str]:
    """批量生成條碼"""
    return [generate_barcode(voter_id) for voter_id in voter_ids]


def validate_barcode(barcode: str) -> bool:
    """驗證條碼格式"""
    return bool(barcode) and len(barcode) > 0


def validate_vote(vote: str) -> bool:
    """驗證投票選項"""
    return vote.lower() in ['yes', 'no', '贊成', '反對']


def normalize_vote(vote: str) -> str:
    """規範化投票選項"""
    vote_lower = vote.lower()
    if vote_lower in ['yes', '贊成']:
        return 'yes'
    elif vote_lower in ['no', '反對']:
        return 'no'
    return vote_lower