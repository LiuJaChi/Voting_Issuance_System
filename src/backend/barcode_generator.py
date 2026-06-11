"""
條碼生成模塊 - 使用 python-barcode 生成 EAN-13 條碼
"""
import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from typing import List, Tuple, Dict
import os


class CustomEAN13Writer(ImageWriter):
    """自訂 EAN-13 Writer - 隱藏編碼文字，只顯示原始戶號"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_data = None
    
    def _text(self, code):
        """
        覆寫文字方法，隱藏 EAN-13 的編碼文字
        EAN-13 預設會顯示 13 位編碼，我們改為不顯示任何文字
        """
        # 不顯示任何文字
        return ""


class BarcodeGenerator:
    """使用 python-barcode 生成 EAN-13 條碼"""

    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化條碼生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # 存儲轉換映射，方便後續反向查詢
        self.conversion_map: Dict[str, str] = {}

    @staticmethod
    def _convert_to_ean13(data: str) -> str:
        """
        將任意字符串轉換為 EAN-13 格式（13 位數字）
        
        轉換規則：
        - 取前 12 位字符，轉換為數字
        - 計算第 13 位校驗碼
        
        Args:
            data: 輸入數據（例如：06-02F）
        
        Returns:
            13 位 EAN-13 編碼字符串
        """
        # 移除非數字字符，只保留數字
        digits_only = ''.join(c for c in data if c.isdigit())
        
        # 如果沒有數字，使用原始數據的 ASCII 值轉換
        if not digits_only:
            # 使用原始數據的每個字符 ASCII 值模 10 得到數字
            digits_only = ''.join(str(ord(c) % 10) for c in data)
        
        # 取前 12 位，不足則補 0
        ean_base = (digits_only + '0' * 12)[:12]
        
        # 計算 EAN-13 校驗碼
        total = 0
        for i, digit in enumerate(ean_base):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        checksum = (10 - (total % 10)) % 10
        ean13 = ean_base + str(checksum)
        
        return ean13

    def generate_barcode_image(self, barcode_data: str, filename: str = None, show_original_text: bool = True) -> str:
        """
        生成單個條碼圖片（PNG 格式）

        Args:
            barcode_data: 條碼數據（例如：06-02F 或 06-02F_001）
            filename: 輸出文件名（不含副檔名）
            show_original_text: 是否在圖片底部顯示原始文字（06-02F）

        Returns:
            條碼文件路徑（含 .png）
        """
        if not filename:
            safe_name = barcode_data.replace("/", "_").replace("\\", "_").replace(" ", "_")
            filename = f"barcode_{safe_name}"

        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 將數據轉換為 EAN-13 格式
            ean13_data = self._convert_to_ean13(barcode_data)
            
            # 記錄映射關係
            self.conversion_map[ean13_data] = barcode_data
            
            # 生成 EAN-13 條碼，使用自訂 writer 隱藏編碼文字
            ean13_class = barcode.get_barcode_class('ean13')
            bar = ean13_class(ean13_data, writer=CustomEAN13Writer())
            
            # 設置條碼選項
            options = {
                'module_width': 0.5,      # 條碼寬度
                'module_height': 15.0,    # 條碼高度
                'font_size': 14,          # 文字大小
                'text_distance': 5,       # 文字與條碼距離
            }
            
            bar.save(filepath, options=options)
            
            # 如果需要顯示原始文字，再手動添加（可選功能）
            if show_original_text:
                # 生成帶有原始文字的版本（使用 PIL 添加文字）
                self._add_text_to_barcode(filepath, barcode_data)
            
            return f"{filepath}.png"
        except Exception as e:
            print(f"條碼生成失敗 {barcode_data}: {e}")
            raise

    @staticmethod
    def _add_text_to_barcode(image_path: str, text: str):
        """
        使用 PIL 在條碼下方添加原始文字

        Args:
            image_path: 條碼圖片路徑（不含副檔名）
            text: 要添加的文字
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 移除 .png 副檔名並重新添加
            image_file = f"{image_path}.png"
            
            # 打開條碼圖片
            img = Image.open(image_file)
            draw = ImageDraw.Draw(img)
            
            # 獲取圖片大小
            img_width, img_height = img.size
            
            # 計算文字位置（居中，靠近底部）
            text_y = img_height - 20
            
            # 嘗試使用系統字體，如果失敗則使用默認字體
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # 計算文字寬度以實現居中
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            # 繪製文字
            draw.text((text_x, text_y), text, fill='black', font=font)
            
            # 保存圖片
            img.save(image_file)
            
        except ImportError:
            # 如果沒有 PIL，跳過文字添加
            print("警告：未安裝 PIL，無法添加文字到條碼。請安裝 Pillow：pip install Pillow")
        except Exception as e:
            print(f"添加文字失敗 {image_path}: {e}")

    def generate_household_barcode(self, household_id: str, show_text: bool = True) -> str:
        """
        為住戶（戶號）生成報到條碼

        Args:
            household_id: 戶號，例如 06-02F
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
            household_id: 戶號，例如 06-02F
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
                print(f"條碼生成失敗 {barcode_data}: {e}")
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
                print(f"條碼生成失敗 {household_id}: {e}")
        return paths

    # ─── 向後兼容 ───
    def generate_voter_barcodes(self, voter_count: int, prefix: str = "VOTER") -> List[str]:
        """為投票者生成條碼（向後兼容）"""
        barcodes = []
        for i in range(1, voter_count + 1):
            # 轉換為 EAN-13 格式
            data = f"{prefix}{i:05d}"
            ean13 = self._convert_to_ean13(data)
            barcodes.append(ean13)
        return barcodes

    def get_conversion_map(self) -> Dict[str, str]:
        """取得 EAN-13 到原始數據的映射"""
        return self.conversion_map


if __name__ == "__main__":
    # 測試條碼生成
    generator = BarcodeGenerator()
    
    # 測試報到條碼
    print("生成報到條碼...")
    checkin_barcode = generator.generate_household_barcode("06-02F", show_text=True)
    print(f"報到條碼: {checkin_barcode}")
    print(f"EAN-13 編碼: {generator._convert_to_ean13('06-02F')}")
    
    # 測試投票單條碼
    print("\n生成投票單條碼...")
    ballot_barcode = generator.generate_voting_ballot_barcode("06-02F", "001", show_text=True)
    print(f"投票單條碼: {ballot_barcode}")
    print(f"EAN-13 編碼: {generator._convert_to_ean13('06-02F_001')}")
    
    # 測試條碼解析
    print("\n測試條碼解析...")
    result = BarcodeGenerator.parse_ballot_barcode("06-02F_001")
    print(f"解析結果: {result}")
