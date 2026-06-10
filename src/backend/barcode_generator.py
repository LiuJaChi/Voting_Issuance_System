"""
條碼生成模塊
"""
import re
from pathlib import Path
from typing import List

import barcode
from barcode.writer import ImageWriter


class BarcodeGenerator:
    """Code39 條碼生成器"""

    CODE39_PATTERN = re.compile(r'^[0-9A-Z \-\.\$/\+%]+$')

    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化條碼生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize_barcode_data(barcode_data: str) -> str:
        """規範化條碼內容"""
        normalized = (barcode_data or "").strip().upper()
        if not normalized:
            raise ValueError("條碼內容不可為空")
        if not BarcodeGenerator.CODE39_PATTERN.fullmatch(normalized):
            raise ValueError(f"條碼內容 `{normalized}` 不符合 Code39 規則；僅支援英數大寫及 - . $ / + % 空白")
        return normalized

    def generate_barcode(self, barcode_data: str, filename: str = None) -> str:
        """生成單個條碼"""
        barcode_data = self.normalize_barcode_data(barcode_data)
        if not filename:
            safe_name = re.sub(r'[^0-9A-Z\-]+', '_', barcode_data)
            filename = f"barcode_{safe_name}"

        filepath = str(Path(self.output_dir) / filename)
        code39 = barcode.get_barcode_class('code39')
        bar = code39(barcode_data, writer=ImageWriter(), add_checksum=False)
        bar.save(filepath)
        return f"{filepath}.png"

    def generate_batch_barcodes(self, barcode_list: List[str]) -> List[str]:
        """批量生成條碼"""
        paths = []
        for barcode_data in barcode_list:
            try:
                path = self.generate_barcode(barcode_data)
                paths.append(path)
            except Exception as e:
                print(f"條碼生成失敗 {barcode_data}: {e}")
        return paths

    def generate_voter_barcodes(self, household_ids: List[str]) -> List[str]:
        """為戶號生成條碼內容列表"""
        return [self.normalize_barcode_data(household_id) for household_id in household_ids if str(household_id).strip()]
