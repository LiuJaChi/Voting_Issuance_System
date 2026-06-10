"""
條碼生成模塊
"""
import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from typing import List


class BarcodeGenerator:
    """Code128 條碼生成器"""
    
    def __init__(self, output_dir: str = "exports/barcodes"):
        """初始化條碼生成器"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_barcode(self, barcode_data: str, filename: str = None) -> str:
        """
        生成單個條碼
        
        Args:
            barcode_data: 條碼數據
            filename: 輸出文件名（不含副檔名）
        
        Returns:
            條碼文件路徑
        """
        if not filename:
            filename = f"barcode_{barcode_data}"
        
        filepath = str(Path(self.output_dir) / filename)
        
        # 生成 Code128 條碼
        code128 = barcode.get_barcode_class('code128')
        bar = code128(barcode_data, writer=ImageWriter())
        bar.save(filepath)
        
        return f"{filepath}.png"
    
    def generate_batch_barcodes(self, barcode_list: List[str]) -> List[str]:
        """
        批量生成條碼
        
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
    
    def generate_voter_barcodes(self, voter_count: int, prefix: str = "VOTER") -> List[str]:
        """
        為投票者生成條碼
        
        Args:
            voter_count: 投票者數量
            prefix: 條碼前綴
        
        Returns:
            條碼列表
        """
        barcodes = []
        for i in range(1, voter_count + 1):
            barcode_data = f"{prefix}{i:05d}"
            barcodes.append(barcode_data)
        
        return barcodes
