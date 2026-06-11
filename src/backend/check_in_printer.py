"""
報到單 PDF 生成模塊

報到單規格：
- 條碼內容：戶號（例如 06-02F）
- 每張大小：BARCODE 標籤尺寸（90mm × 35mm）
- 每頁 A4：2 欄 × 8 列 = 最多 16 張
- 內容：戶號 + 姓名 + EAN-13 條碼
"""
import io
from pathlib import Path
from typing import List, Tuple

import barcode as bc
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image as RLImage


# 報到單（標籤）尺寸
LABEL_WIDTH = 90 * mm
LABEL_HEIGHT = 35 * mm

# 每頁欄數與列數
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 8


class CustomEAN13Writer(ImageWriter):
    """自訂 EAN-13 Writer - 隱藏編碼文字"""
    
    def _text(self, code):
        """隱藏 EAN-13 編碼文字"""
        return ""


class CheckInPrinter:
    """報到單 PDF 生成器"""

    def __init__(self, output_dir: str = "exports/check_in_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _convert_to_ean13(data: str) -> str:
        """
        將任意字符串轉換為 EAN-13 格式（13 位數字）
        
        Args:
            data: 輸入數據（例如：06-02F）
        
        Returns:
            13 位 EAN-13 編碼字符串
        """
        # 移除非數字字符，只保留數字
        digits_only = ''.join(c for c in data if c.isdigit())
        
        # 如果沒有數字，使用原始數據的 ASCII 值轉換
        if not digits_only:
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

    def _generate_barcode_image(self, content: str) -> io.BytesIO:
        """生成 EAN-13 條碼圖片，返回 BytesIO 流"""
        buf = io.BytesIO()
        
        # 將戶號轉換為 EAN-13 編碼
        ean13_content = self._convert_to_ean13(content)
        
        # 使用 EAN-13 格式生成條碼
        ean13_cls = bc.get_barcode_class('ean13')
        writer = CustomEAN13Writer()
        bar = ean13_cls(ean13_content, writer=writer)

        options = {
            'module_height': 8.0,
            'module_width': 0.3,
            'quiet_zone': 2.0,
            'font_size': 6,
            'text_distance': 2.0,
            'write_text': False,  # ✅ 隱藏編碼文字
        }
        bar.write(buf, options=options)
        buf.seek(0)
        return buf

    def generate_pdf(
        self,
        households: List[Tuple[str, str]],
        filename: str = "check_in_ballots.pdf"
    ) -> str:
        """
        生成報到單 PDF

        Args:
            households: [(household_id, name), ...]
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
        center_style = ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=9,
            leading=11,
        )
        id_style = ParagraphStyle(
            'ID',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#333333'),
        )

        # 每個標籤的寬度
        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE

        # 每個標籤的高度
        cell_h = LABEL_HEIGHT

        table_data = []
        row_cells = []

        for idx, (household_id, name) in enumerate(households):
            # 生成條碼圖片
            try:
                barcode_buf = self._generate_barcode_image(household_id)
                barcode_img = RLImage(barcode_buf, width=cell_w * 0.75, height=18 * mm)
            except Exception as e:
                print(f"條碼生成失敗 {household_id}: {e}")
                barcode_img = Paragraph(f"[條碼: {household_id}]", center_style)

            cell_content = [
                Paragraph(f"<b>{household_id}</b>", center_style),
                Paragraph(name, id_style),
                barcode_img,
            ]

            row_cells.append(cell_content)

            if len(row_cells) == COLS_PER_PAGE:
                table_data.append(row_cells)
                row_cells = []

        # 補齊最後一行
        if row_cells:
            while len(row_cells) < COLS_PER_PAGE:
                row_cells.append("")
            table_data.append(row_cells)

        if not table_data:
            return output_path

        col_widths = [cell_w] * COLS_PER_PAGE
        row_heights = [cell_h] * len(table_data)

        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        doc.build([table])
        return output_path
