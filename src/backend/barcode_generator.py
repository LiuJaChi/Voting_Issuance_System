"""
條碼生成模塊 - 使用 qrcode 生成 QR Code
"""
import qrcode
from pathlib import Path
from typing import List, Tuple, Dict
import os


class BarcodeGenerator:
    """使用 qrcode 生成 QR Code"""

    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化 QR Code 生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # 存儲轉換映射
        self.conversion_map: Dict[str, str] = {}

    def generate_qrcode_image(self, qr_data: str, filename: str = None) -> str:
        """
        生成單個 QR Code 圖片（PNG 格式）

        Args:
            qr_data: QR Code 數據（例如：06-02F）
            filename: 輸出文件名（不含副檔名）

        Returns:
            QR Code 文件路徑（含 .png）
        """
        if not filename:
            safe_name = qr_data.replace("/", "_").replace("\\", "_").replace(" ", "_")
            filename = f"qrcode_{safe_name}"

        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 生成 QR Code
            qr = qrcode.QRCode(
                version=1,  # 控制 QR Code 的大小（1-40）
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,  # 每個方塊的像素大小
                border=2,  # 邊框大小
            )
            
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # 創建圖片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 保存圖片
            img.save(f"{filepath}.png")
            
            # 記錄映射關係
            self.conversion_map[qr_data] = qr_data
            
            return f"{filepath}.png"
        except Exception as e:
            print(f"QR Code 生成失敗 {qr_data}: {e}")
            raise

    def generate_household_qrcode(self, household_id: str) -> str:
        """
        為住戶（戶號）生成報到 QR Code

        Args:
            household_id: 戶號，例如 06-02F

        Returns:
            QR Code 文件路徑
        """
        safe_name = household_id.replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"checkin_{safe_name}"
        return self.generate_qrcode_image(household_id, filename)

    def generate_voting_ballot_qrcode(self, household_id: str, case_number: str) -> str:
        """
        生成投票單 QR Code（戶號+案號）

        Args:
            household_id: 戶號，例如 06-02F
            case_number: 案號，例如 001

        Returns:
            QR Code 文件路徑
        """
        qr_data = self.make_ballot_qrcode_content(household_id, case_number)
        safe_name = qr_data.replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"ballot_{safe_name}"
        return self.generate_qrcode_image(qr_data, filename)

    @staticmethod
    def make_ballot_qrcode_content(household_id: str, case_number: str) -> str:
        """生成投票單 QR Code 內容字串（戶號_案號）"""
        return f"{household_id}_{case_number}"

    @staticmethod
    def parse_ballot_qrcode(qrcode_content: str):
        """
        解析投票單 QR Code，返回 (household_id, case_number) 或 None

        QR Code 格式：{household_id}_{case_number}
        例如：06-02F_001
        """
        if "_" not in qrcode_content:
            return None
        # 從最後一個 _ 分割，因為戶號本身可能包含 -
        idx = qrcode_content.rfind("_")
        household_id = qrcode_content[:idx]
        case_number = qrcode_content[idx + 1:]
        if household_id and case_number:
            return household_id, case_number
        return None

    def generate_batch_qrcodes(self, qrcode_list: List[str]) -> List[str]:
        """
        批量生成 QR Code 圖片

        Args:
            qrcode_list: QR Code 數據列表

        Returns:
            生成的 QR Code 文件路徑列表
        """
        paths = []
        for qr_data in qrcode_list:
            try:
                path = self.generate_qrcode_image(qr_data)
                paths.append(path)
            except Exception as e:
                print(f"QR Code 生成失敗 {qr_data}: {e}")
        return paths

    def generate_household_qrcodes_batch(
        self, households: List[Tuple[str, str]]
    ) -> List[str]:
        """
        批量生成住戶報到 QR Code

        Args:
            households: [(household_id, name), ...]

        Returns:
            生成的 QR Code 文件路徑列表
        """
        paths = []
        for household_id, _ in households:
            try:
                path = self.generate_household_qrcode(household_id)
                paths.append(path)
            except Exception as e:
                print(f"QR Code 生成失敗 {household_id}: {e}")
        return paths

    def generate_barcodes(self, household_ids: List[str]) -> List[str]:
        """
        批量生成住戶 QR Code

        Args:
            household_ids: 戶號列表

        Returns:
            生成的 QR Code 文件路徑列表
        """
        return self.generate_batch_qrcodes(household_ids)

    def get_conversion_map(self) -> Dict[str, str]:
        """取得 QR Code 到原始數據的映射"""
        return self.conversion_map


if __name__ == "__main__":
    # 測試 QR Code 生成
    generator = BarcodeGenerator()
    
    # 測試報到 QR Code
    print("生成報到 QR Code...")
    checkin_qrcode = generator.generate_household_qrcode("06-03F")
    print(f"報到 QR Code: {checkin_qrcode}")
    
    # 測試投票單 QR Code
    print("\n生成投票單 QR Code...")
    ballot_qrcode = generator.generate_voting_ballot_qrcode("06-03F", "001")
    print(f"投票單 QR Code: {ballot_qrcode}")
    
    # 測試 QR Code 解析
    print("\n測試 QR Code 解析...")
    result = BarcodeGenerator.parse_ballot_qrcode("06-03F_001")
    print(f"解析結果: {result}")
