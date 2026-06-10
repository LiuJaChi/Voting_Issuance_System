"""
實用工具函數
"""
import re
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple


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


# ─────────────────────────── 戶號與案號驗證 ───────────────────────────

# 戶號格式：數字-數字[英文字母]，例如 06-02F、20-02F、06-01、1-1A
HOUSEHOLD_ID_PATTERN = re.compile(r'^\d{1,4}-\d{1,4}[A-Za-z]?$')


def validate_household_id(household_id: str) -> bool:
    """
    驗證戶號格式

    合法格式示例：06-02F、20-02F、06-01、1-1A
    """
    if not household_id:
        return False
    return bool(HOUSEHOLD_ID_PATTERN.match(household_id.strip()))


def normalize_household_id(household_id: str) -> str:
    """規範化戶號（去除前後空白，轉大寫）"""
    return household_id.strip().upper()


# 案號格式：1-3 位數字，例如 001、01、1
CASE_NUMBER_PATTERN = re.compile(r'^\d{1,3}$')


def validate_case_number(case_number: str) -> bool:
    """
    驗證案號格式

    合法格式示例：001、01、1
    """
    if not case_number:
        return False
    return bool(CASE_NUMBER_PATTERN.match(case_number.strip()))


def normalize_case_number(case_number: str) -> str:
    """規範化案號（去除前後空白）"""
    return case_number.strip()


# ─────────────────────────── 條碼解析 ───────────────────────────

def parse_check_in_barcode(barcode_content: str) -> Optional[str]:
    """
    解析報到單條碼，返回戶號

    報到單條碼內容即為戶號（例如 06-02F）
    """
    content = barcode_content.strip()
    if content:
        return content
    return None


def parse_voting_ballot_barcode(barcode_content: str) -> Optional[Tuple[str, str]]:
    """
    解析投票單條碼，返回 (household_id, case_number) 或 None

    投票單條碼格式：{household_id}_{case_number}
    例如：06-02F_001
    """
    content = barcode_content.strip()
    if "_" not in content:
        return None
    idx = content.rfind("_")
    household_id = content[:idx]
    case_number = content[idx + 1:]
    if household_id and case_number:
        return household_id, case_number
    return None

