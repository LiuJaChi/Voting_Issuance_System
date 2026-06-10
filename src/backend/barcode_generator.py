"""
條碼生成模塊
"""
import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from typing import List, Tuple


class BarcodeGenerator:
    """Code128 條碼生成器"""

    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化條碼生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def generate_barcode(self, barcode_data: str, filename: str = None) -> str:
        """
        生成單個條碼圖片

        Args:
            barcode_data: 條碼數據
            filename: 輸出文件名（不含副檔名）

        Returns:
            條碼文件路徑（含 .png）
        """
        if not filename:
            # 將戶號中的特殊字符替換為安全字符
            safe_name = barcode_data.replace("/", "_").replace("\\", "_")
            filename = f"barcode_{safe_name}"

        filepath = str(Path(self.output_dir) / filename)

        code128 = barcode.get_barcode_class('code128')
        bar = code128(barcode_data, writer=ImageWriter())
        bar.save(filepath)

        return f"{filepath}.png"

    def generate_batch_barcodes(self, barcode_list: List[str]) -> List[str]:
        """
        批量生成條碼圖片

        Args:
            barcode_list: 條碼數據列表

        Returns:
            生成的條碼文件路徑列表
        """
        paths = []
        for barcode_data in barcode_list:
            try:
                path = self.generate_barcode(barcode_data)
                paths.append(path)
            except Exception as e:
                print(f"條碼生成失敗 {barcode_data}: {e}")
        return paths

    def generate_household_barcode(self, household_id: str) -> str:
        """
        為住戶（戶號）生成報到條碼

        Args:
            household_id: 戶號，例如 06-02F

        Returns:
            條碼文件路徑
        """
        safe_name = household_id.replace("/", "_").replace("\\", "_")
        filename = f"checkin_{safe_name}"
        return self.generate_barcode(household_id, filename)

    def generate_voting_ballot_barcode(self, household_id: str, case_number: str) -> str:
        """
        生成投票單條碼（戶號+案號）

        Args:
            household_id: 戶號，例如 06-02F
            case_number: 案號，例如 001

        Returns:
            條碼文件路徑
        """
        barcode_data = self.make_ballot_barcode_content(household_id, case_number)
        safe_name = barcode_data.replace("/", "_").replace("\\", "_")
        filename = f"ballot_{safe_name}"
        return self.generate_barcode(barcode_data, filename)

    @staticmethod
    def make_ballot_barcode_content(household_id: str, case_number: str) -> str:
        """生成投票單條碼內容字串（戶號_案號）"""
        return f"{household_id}_{case_number}"

    @staticmethod
    def parse_ballot_barcode(barcode_content: str):
        """
        解析投票單條碼，返回 (household_id, case_number) 或 None

        投票單條碼格式：{household_id}_{case_number}
        例如：06-02F_001
        """
        if "_" not in barcode_content:
            return None
        # 從最後一個 _ 分割，因為戶號本身可能包含 -
        idx = barcode_content.rfind("_")
        household_id = barcode_content[:idx]
        case_number = barcode_content[idx + 1:]
        if household_id and case_number:
            return household_id, case_number
        return None

    def generate_household_barcodes_batch(
        self, households: List[Tuple[str, str]]
    ) -> List[str]:
        """
        批量生成住戶報到條碼

        Args:
            households: [(household_id, name), ...]

        Returns:
            生成的條碼文件路徑列表
        """
        paths = []
        for household_id, _ in households:
            try:
                path = self.generate_household_barcode(household_id)
                paths.append(path)
            except Exception as e:
                print(f"條碼生成失敗 {household_id}: {e}")
        return paths

    # ─── 向後兼容 ───
    def generate_voter_barcodes(self, voter_count: int, prefix: str = "VOTER") -> List[str]:
        """為投票者生成條碼（向後兼容）"""
        barcodes = []
        for i in range(1, voter_count + 1):
            barcodes.append(f"{prefix}{i:05d}")
        return barcodes

