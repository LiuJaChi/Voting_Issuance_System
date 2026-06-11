"""
字符清理和過濾工具
"""
import unicodedata
import re


def clean_barcode_input(barcode_str: str) -> str:
    """
    清理條碼掃描輸入
    
    移除所有控制字符、換行符、回車符、制表符、空格等隱藏字符
    
    Args:
        barcode_str: 原始掃描字符串
        
    Returns:
        清理後的字符串
    """
    if not barcode_str:
        return ""
    
    # 1. 移除換行符 \n
    barcode_str = barcode_str.replace('\n', '')
    
    # 2. 移除回車符 \r
    barcode_str = barcode_str.replace('\r', '')
    
    # 3. 移除制表符 \t
    barcode_str = barcode_str.replace('\t', '')
    
    # 4. 移除其他控制字符（ASCII 0-31 和 127）
    barcode_str = ''.join(
        char for char in barcode_str 
        if ord(char) >= 32 or char in '\n\r\t'  # 保留已處理的
    )
    
    # 5. 移除前後空格
    barcode_str = barcode_str.strip()
    
    # 6. 移除中間多餘空格（保留單個空格）
    barcode_str = re.sub(r'\s+', ' ', barcode_str)
    
    # 7. 移除其他Unicode控制字符
    barcode_str = ''.join(
        char for char in barcode_str
        if unicodedata.category(char)[0] != 'C'  # C = Control characters
    )
    
    # 8. 最後再次 strip
    barcode_str = barcode_str.strip()
    
    return barcode_str


def sanitize_household_id(household_id: str) -> str:
    """
    清理戶號輸入
    
    Args:
        household_id: 原始戶號
        
    Returns:
        清理後的戶號
    """
    return clean_barcode_input(household_id)


def sanitize_case_number(case_number: str) -> str:
    """
    清理案號輸入
    
    Args:
        case_number: 原始案號
        
    Returns:
        清理後的案號
    """
    return clean_barcode_input(case_number)


def print_debug_info(original: str, cleaned: str) -> None:
    """
    打印調試信息，顯示原始輸入和清理後的輸入
    
    Args:
        original: 原始字符串
        cleaned: 清理後的字符串
    """
    print(f"原始輸入: {repr(original)}")
    print(f"清理後: {repr(cleaned)}")
    
    if original != cleaned:
        print("⚠️  檢測到隱藏字符：")
        
        # 顯示每個字符的信息
        for i, char in enumerate(original):
            char_code = ord(char)
            char_name = unicodedata.name(char, "UNKNOWN")
            if char != cleaned[min(i, len(cleaned) - 1)]:
                print(f"  位置 {i}: '{char}' (U+{char_code:04X}) - {char_name}")
    else:
        print("✓ 沒有隱藏字符")
