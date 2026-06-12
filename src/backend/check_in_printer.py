"""
報到單 PDF 生成模塊 - 使用 python-barcode 生成 Code128 條碼圖像

報到單規格：
- 每張標籤：戶號 + Code128 條碼圖像
- 每張大小：BARCODE 標籤尺寸（90mm × 35mm）
- 每頁 A4：2 欄 × 8 列 = 最多 16 張
- 內容：戶號（上方） + 條碼圖像（下方）
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict

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
        
        # 建立臨時條碼目錄（用於存儲 PDF 生成過程中的條碼）
        self.temp_barcode_dir = os.path.join(output_dir, ".temp_barcodes")
        Path(self.temp_barcode_dir).mkdir(parents=True, exist_ok=True)

    def _cleanup_temp_barcode_dir(self):
        """清理臨時條碼目錄"""
        try:
            if os.path.exists(self.temp_barcode_dir):
                shutil.rmtree(self.temp_barcode_dir)
                print(f"✓ 臨時條碼目錄已清理: {self.temp_barcode_dir}")
        except Exception as e:
            print(f"清理臨時條碼目錄失敗: {e}")

    def _generate_code128_image(self, content: str) -> str:
        """
        生成 Code128 條碼圖片，返回文件路徑
        
        使用 python-barcode 庫直接生成條碼圖像，保存到臨時目錄
        
        Args:
            content: Code128 內容（例如 A106-02）
            
        Returns:
            條碼圖像文件路徑
        """
        try:
            # 確保內容適合作為文件名
            safe_content = content.replace('/', '_').replace('\\', '_').replace('-', '_')
            temp_filename = f"barcode_{safe_content}"
            temp_path = os.path.join(self.temp_barcode_dir, temp_filename)
            
            print(f"📝 開始生成條碼: {content}")
            print(f"📂 條碼路徑: {temp_path}")
            
            # 使用 python-barcode 生成 Code128 條碼
            code128_class = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            
            # 生成條碼實例（移除 add_checksum=False 參數）
            bar = code128_class(content, writer=writer)
            
            # 條碼配置選項 - 調整高度和寬度確保清晰度
            options = {
                'module_width': 0.75,      # 條碼條的寬度（增加以提高清晰度）
                'module_height': 15.0,    # 條碼的高度（增加以提高掃描率）
                'font_size': 0,           # 不顯示下方文字
                'text_distance': 0,       # 文字距離
                'quiet_zone': 3.0,        # 靜區寬度
            }
            
            # 保存條碼圖像到文件
            # barcode.save() 返回完整文件路徑（包含 .png）
            actual_path = bar.save(temp_path, options=options)
            
            print(f"✓ 條碼庫返回路徑: {actual_path}")
            
            # 驗證文件是否存在
            if os.path.exists(actual_path):
                print(f"✓ Code128 條碼生成成功: {content}")
                return actual_path
            else:
                raise FileNotFoundError(f"條碼文件未生成: {actual_path}")
            
        except Exception as e:
            print(f"✗ Code128 條碼生成失敗 {content}: {e}")
            import traceback
            traceback.print_exc()
            raise

    def generate_pdf(
        self,
        households: List[Dict],
        filename: str = "check_in_ballots.pdf"
    ) -> str:
        """
        生成報到單 PDF
        
        報到單格式：
        戶號（上方）+ Code128 條碼圖像（下方）
        
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

        for idx, household in enumerate(households):
            household_id = household['household_id']
            print(f"\n🏠 處理住戶 {idx + 1}/{len(households)}: {household_id}")
            
            # 生成 Code128 條碼圖像
            try:
                code128_path = self._generate_code128_image(household_id)
                print(f"✓ 條碼路徑已驗證: {code128_path}")
                
                # 從文件讀取條碼圖像到 PDF
                # 調整寬度和高度使條碼更清晰
                code128_img = RLImage(code128_path, width=cell_w * 0.9, height=14 * mm)
                print(f"✓ 條碼圖像已載入 PDF")
            except Exception as e:
                print(f"❌ 條碼生成失敗 {household_id}: {e}")
                import traceback
                traceback.print_exc()
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
            self._cleanup_temp_barcode_dir()
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

        print(f"\n📄 開始生成 PDF: {output_path}")
        doc.build([table])
        print(f"✓ PDF 生成完成: {output_path}")
        
        # PDF 已生成完成，現在可以安全地清理臨時條碼文件
        self._cleanup_temp_barcode_dir()
        
        return output_path
