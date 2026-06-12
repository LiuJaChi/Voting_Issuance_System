"""
報到單 PDF 生成模塊 - 使用 python-barcode 生成 Code128 條碼圖像

報到單規格：
- 每張標籤：戶號 + Code128 條碼圖像
- 每張大小：BARCODE 標籤尺寸（90mm × 35mm）
- 每頁 A4：2 欄 × 8 列 = 最多 16 張
- 內容：戶號（上方） + 條碼圖像（下方）
"""
import os
import tempfile
from pathlib import Path
from typing import List, Dict
from io import BytesIO

import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Spacer
from PIL import Image as PILImage


# 報到單（標籤）尺寸
LABEL_WIDTH = 90 * mm
LABEL_HEIGHT = 35 * mm

# 每頁欄數與列數
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 8


class CheckInPrinter:
    """報到單 PDF 生成器"""

    def __init__(self, output_dir: str = "exports/check_in_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.temp_barcodes = []  # 存儲臨時條碼文件路徑

    def _cleanup_temp_files(self):
        """清理臨時條碼文件"""
        for temp_path in self.temp_barcodes:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"清理臨時文件失敗 {temp_path}: {e}")
        self.temp_barcodes = []

    def _generate_code128_image(self, content: str) -> str:
        """
        生成 Code128 條碼圖片，返回文件路徑
        
        使用 python-barcode 庫直接生成條碼圖像，保存為臨時文件
        
        Args:
            content: Code128 內容（例如 A106-02）
            
        Returns:
            條碼圖像文件路徑
        """
        try:
            # 建立臨時目錄存放條碼
            temp_dir = tempfile.gettempdir()
            
            # 確保內容適合作為文件名
            safe_content = content.replace('/', '_').replace('\\', '_')
            temp_path = os.path.join(temp_dir, f"barcode_{safe_content}")
            
            # 使用 python-barcode 生成 Code128 條碼
            code128_class = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            
            # 生成條碼實例
            bar = code128_class(content, writer=writer, add_checksum=False)
            
            # 條碼配置選項 - 調整高度和寬度確保清晰度
            options = {
                'module_width': 0.75,      # 條碼條的寬度（增加以提高清晰度）
                'module_height': 15.0,    # 條碼的高度（增加以提高掃描率）
                'font_size': 0,           # 不顯示下方文字
                'text_distance': 0,       # 文字距離
                'quiet_zone': 3.0,        # 靜區寬度
            }
            
            # 保存條碼圖像到文件（不包含副檔名，barcode 會自動添加 .png）
            bar.save(temp_path, options=options)
            
            # barcode 庫自動添加 .png 副檔名
            final_path = temp_path + '.png'
            
            # 記錄臨時文件，用於後續清理
            if os.path.exists(final_path):
                self.temp_barcodes.append(final_path)
                print(f"✓ Code128 條碼生成成功: {content} -> {final_path}")
                return final_path
            else:
                raise FileNotFoundError(f"條碼文件未生成: {final_path}")
            
        except Exception as e:
            print(f"✗ Code128 條碼生成失敗 {content}: {e}")
            raise

    def generate_pdf(
        self,
        households: List[Dict],
        filename: str = "check_in_ballots.pdf"
    ) -> str:
        """
        生成報到單 PDF
        
        報到單格式：
        戶號（上方） + Code128 條碼圖像（下方）
        
        Args:
            households: [{'household_id': 'A106-02', 'name': '洪正平'}, ...]
            filename: 輸出文件名
            
        Returns:
            輸出文件路徑
        """
        output_path = str(Path(self.output_dir) / filename)

        page_w, page_h = A4
        margin = 10 * mm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )

        styles = getSampleStyleSheet()
        
        # 戶號樣式（加粗、居中）
        household_id_style = ParagraphStyle(
            'HouseholdID',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            leading=14,
            fontName='Helvetica-Bold',
        )

        # 每個標籤的寬度
        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE

        # 每個標籤的高度
        cell_h = LABEL_HEIGHT

        table_data = []
        row_cells = []

        for household in households:
            household_id = household['household_id']
            
            # 生成 Code128 條碼圖像
            try:
                code128_path = self._generate_code128_image(household_id)
                # 從文件讀取條碼圖像到 PDF
                # 調整寬度和高度使條碼更清晰
                code128_img = RLImage(code128_path, width=cell_w * 0.9, height=14 * mm)
            except Exception as e:
                print(f"條碼生成失敗 {household_id}: {e}")
                # 如果生成失敗，顯示文字代替
                code128_img = Paragraph(f"Error: {household_id}", household_id_style)
            
            # 單元格內容：戶號（上方）+ 條碼圖像（下方）
            # 使用垂直排列
            cell_content_table = Table(
                [
                    [Paragraph(household_id, household_id_style)],
                    [Spacer(1, 2 * mm)],  # 間距
                    [code128_img],
                ],
                colWidths=[cell_w * 0.95],
                rowHeights=[8 * mm, 2 * mm, 14 * mm],
            )
            cell_content_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            row_cells.append(cell_content_table)

            if len(row_cells) == COLS_PER_PAGE:
                table_data.append(row_cells)
                row_cells = []

        # 補齊最後一行
        if row_cells:
            while len(row_cells) < COLS_PER_PAGE:
                row_cells.append("")
            table_data.append(row_cells)

        if not table_data:
            self._cleanup_temp_files()
            return output_path

        col_widths = [cell_w] * COLS_PER_PAGE
        row_heights = [cell_h] * len(table_data)

        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))

        doc.build([table])
        
        # 清理臨時文件
        self._cleanup_temp_files()
        
        return output_path
