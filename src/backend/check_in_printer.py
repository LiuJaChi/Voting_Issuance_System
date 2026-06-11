"""
報到單 PDF 生成模塊 - 使用 QR Code

報到單規格：
- QR Code 內容：戶號（例如 06-02F）
- 每張大小：BARCODE 標籤尺寸（90mm × 35mm）
- 每頁 A4：2 欄 × 8 列 = 最多 16 張
- 內容：戶號 + 姓名 + QR Code
"""
import io
from pathlib import Path
from typing import List, Tuple

import qrcode
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


class CheckInPrinter:
    """報到單 PDF 生成器 - 使用 QR Code"""

    def __init__(self, output_dir: str = "exports/check_in_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_qrcode_image(content: str) -> io.BytesIO:
        """
        生成 QR Code 圖片，返回 BytesIO 流
        
        Args:
            content: QR Code 內容（戶號）
            
        Returns:
            BytesIO 流
        """
        buf = io.BytesIO()
        
        # 生成 QR Code
        qr = qrcode.QRCode(
            version=1,  # 自動調整大小
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        
        qr.add_data(content)
        qr.make(fit=True)
        
        # 創建圖片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 保存到 BytesIO
        img.save(buf, format='PNG')
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
            # 生成 QR Code 圖片
            try:
                qrcode_buf = self._generate_qrcode_image(household_id)
                qrcode_img = RLImage(qrcode_buf, width=20 * mm, height=20 * mm)
            except Exception as e:
                print(f"QR Code 生成失敗 {household_id}: {e}")
                qrcode_img = Paragraph(f"[QR: {household_id}]", center_style)

            cell_content = [
                Paragraph(f"<b>{household_id}</b>", center_style),
                Paragraph(name, id_style),
                qrcode_img,
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
