"""
條碼生成模塊 - 使用 python-barcode 生成 Code128 條碼
"""
import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from typing import List, Tuple, Dict
import os


class BarcodeGenerator:
    """使用 python-barcode 生成 Code128 條碼"""

    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化條碼生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # 存儲轉換映射
        self.conversion_map: Dict[str, str] = {}

    def generate_barcode_image(self, barcode_data: str, filename: str = None, show_original_text: bool = True) -> str:
        """
        生成單個條碼圖片（PNG 格式）- 使用 Code128

        Args:
            barcode_data: 條碼數據（例如：A106-02）
            filename: 輸出文件名（不含副檔名）
            show_original_text: 是否在圖片底部顯示原始文字

        Returns:
            條碼文件路徑（含 .png）
        """
        if not filename:
            safe_name = barcode_data.replace("/", "_").replace("\\", "_").replace(" ", "_")
            filename = f"barcode_{safe_name}"

        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 使用 Code128 格式直接編碼戶號
            code128_class = barcode.get_barcode_class('code128')
            bar = code128_class(barcode_data, writer=ImageWriter())
            
            # 設置條碼選項
            options = {
                'module_width': 0.75,     # 條碼寬度（增加以提高清晰度）
                'module_height': 15.0,    # 條碼高度
                'font_size': 12,          # 文字大小
                'text_distance': 5,       # 文字與條碼距離
                'quiet_zone': 3.0,        # 靜區寬度
            }
            
            actual_path = bar.save(filepath, options=options)
            
            # 記錄映射關係
            self.conversion_map[barcode_data] = barcode_data
            
            return actual_path
        except Exception as e:
            print(f"Code128 條碼生成失敗 {barcode_data}: {e}")
            raise

    def generate_household_barcode(self, household_id: str, show_text: bool = True) -> str:
        """
        為住戶（戶號）生成報到條碼

        Args:
            household_id: 戶號，例如 A106-02
            show_text: 是否顯示戶號文字

        Returns:
            條碼文件路徑
        """
        safe_name = household_id.replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"checkin_{safe_name}"
        return self.generate_barcode_image(household_id, filename, show_text)

    def generate_voting_ballot_barcode(self, household_id: str, case_number: str, show_text: bool = True) -> str:
        """
        生成投票單條碼（戶號+案號）

        Args:
            household_id: 戶號，例如 A106-02
            case_number: 案號，例如 001
            show_text: 是否顯示文字

        Returns:
            條碼文件路徑
        """
        barcode_data = self.make_ballot_barcode_content(household_id, case_number)
        safe_name = barcode_data.replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"ballot_{safe_name}"
        return self.generate_barcode_image(barcode_data, filename, show_text)

    @staticmethod
    def make_ballot_barcode_content(household_id: str, case_number: str) -> str:
        """生成投票單條碼內容字串（戶號_案號）"""
        return f"{household_id}_{case_number}"

    @staticmethod
    def parse_ballot_barcode(barcode_content: str):
        """
        解析投票單條碼，返回 (household_id, case_number) 或 None

        投票單條碼格式：{household_id}_{case_number}
        例如：A106-02_001
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

    def generate_batch_barcodes(self, barcode_list: List[str], show_text: bool = True) -> List[str]:
        """
        批量生成條碼圖片

        Args:
            barcode_list: 條碼數據列表
            show_text: 是否顯示文字

        Returns:
            生成的條碼文件路徑列表
        """
        paths = []
        for barcode_data in barcode_list:
            try:
                path = self.generate_barcode_image(barcode_data, show_text=show_text)
                paths.append(path)
            except Exception as e:
                print(f"Code128 條碼生成失敗 {barcode_data}: {e}")
        return paths

    def generate_household_barcodes_batch(
        self, households: List[Tuple[str, str]], show_text: bool = True
    ) -> List[str]:
        """
        批量生成住戶報到條碼

        Args:
            households: [(household_id, name), ...]
            show_text: 是否顯示文字

        Returns:
            生成的條碼文件路徑列表
        """
        paths = []
        for household_id, _ in households:
            try:
                path = self.generate_household_barcode(household_id, show_text)
                paths.append(path)
            except Exception as e:
                print(f"Code128 條碼生成失敗 {household_id}: {e}")
        return paths

    def generate_barcodes(self, household_ids: List[str]) -> List[str]:
        """
        批量生成住戶條碼

        Args:
            household_ids: 戶號列表

        Returns:
            生成的條碼文件路徑列表
        """
        return self.generate_batch_barcodes(household_ids, show_text=True)

    def get_conversion_map(self) -> Dict[str, str]:
        """取得條碼到原始數據的映射"""
        return self.conversion_map


if __name__ == "__main__":
    # 測試條碼生成
    generator = BarcodeGenerator()
    
    # 測試報到條碼
    print("生成報到條碼...")
    checkin_barcode = generator.generate_household_barcode("A106-02", show_text=True)
    print(f"報到條碼: {checkin_barcode}")
    
    # 測試投票單條碼
    print("\n生成投票單條碼...")
    ballot_barcode = generator.generate_voting_ballot_barcode("A106-02", "001", show_text=True)
    print(f"投票單條碼: {ballot_barcode}")
    
    # 測試條碼解析
    print("\n測試條碼解析...")
    result = BarcodeGenerator.parse_ballot_barcode("A106-02_001")
    print(f"解析結果: {result}")
