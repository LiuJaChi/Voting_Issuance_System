"""
投票單 PDF 生成模塊 - 使用 python-barcode 生成 Code128 條碼圖像

投票單規格：
- 每張投票單：案號 + 項目名稱 + 描述 + 住戶條碼 + 投票選項
- 每張大小：約 95mm × 70mm
- 每頁 A4：2 欄 × 4 列 = 8 張
- 內容：第X案 + 項目名稱 + 描述 + 住戶條碼 + 投票選項(同意/不同意/棄權)
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime

import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image as RLImage


# 投票單（標籤）尺寸
LABEL_WIDTH = 95 * mm
LABEL_HEIGHT = 70 * mm

# 每頁欄數與列數
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 4


class VotingBallotPrinter:
    """投票單 PDF 生成器"""

    def __init__(self, output_dir: str = "exports/voting_ballots"):
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
            
            # 使用 python-barcode 生成 Code128 條碼
            code128_class = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            
            # 生成條碼實例
            bar = code128_class(content, writer=writer)
            
            # 條碼配置選項 - 簡化版本，避免字體渲染問題
            options = {
                'module_width': 0.5,       # 條碼條的寬度（較小以適應投票單空間）
                'module_height': 10.0,     # 條碼的高度
                'quiet_zone': 2.0,         # 靜區寬度
                'write_text': False,       # 不寫入文字，避免字體初始化問題
            }
            
            # 保存條碼圖像到文件
            actual_path = bar.save(temp_path, options=options)
            
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
        voting_data: List[Dict],
        filename: str = "voting_ballots.pdf"
    ) -> str:
        """
        生成投票單 PDF
        
        投票單格式：
        第X案 + 項目名稱 + 描述 + 住戶條碼 + 投票選項
        
        Args:
            voting_data: [
                {
                    'case_number': '1',
                    'name': '物業管理費調整',
                    'description': '擬調整2026年物業管理費',
                    'households': [
                        {'household_id': 'A106-02', 'name': '洪正平'},
                        ...
                    ]
                },
                ...
            ]
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
        
        # 案號樣式
        case_number_style = ParagraphStyle(
            'CaseNumber',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            leading=11,
            fontName='Helvetica-Bold',
        )
        
        # 項目名稱樣式
        item_name_style = ParagraphStyle(
            'ItemName',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=8,
            leading=9,
            fontName='Helvetica-Bold',
        )
        
        # 描述樣式
        description_style = ParagraphStyle(
            'Description',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=7,
            leading=8,
            fontName='Helvetica',
        )
        
        # 投票選項樣式
        voting_option_style = ParagraphStyle(
            'VotingOption',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=6,
            leading=7,
            fontName='Helvetica',
        )

        # 每個標籤的寬度
        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE

        # 每個標籤的高度
        cell_h = LABEL_HEIGHT

        table_data = []
        row_cells = []

        # 遍歷每個投票案號
        for case_idx, case in enumerate(voting_data):
            case_number = case['case_number']
            case_name = case['name']
            description = case['description']
            households = case.get('households', [])
            
            print(f"\n📋 處理投票案號 {case_idx + 1}/{len(voting_data)}: 第{case_number}案 {case_name}")
            
            # 遍歷每個住戶生成投票單
            for hh_idx, household in enumerate(households):
                household_id = household['household_id']
                print(f"  🏠 生成投票單 {hh_idx + 1}/{len(households)}: {household_id}")
                
                # 生成 Code128 條碼圖像
                try:
                    code128_path = self._generate_code128_image(household_id)
                    code128_img = RLImage(code128_path, width=cell_w * 0.8, height=8 * mm)
                except Exception as e:
                    print(f"❌ 條碼生成失敗 {household_id}: {e}")
                    code128_img = Paragraph(f"Error: {household_id}", item_name_style)
                
                # 構建投票單內容
                ballot_content_data = [
                    # 第X案
                    [Paragraph(f"第 {case_number} 案", case_number_style)],
                    # 項目名稱
                    [Paragraph(case_name, item_name_style)],
                    # 描述（限制行數）
                    [Paragraph(description[:30], description_style)],
                    # 空白（間距）
                    [Spacer(1, 1 * mm)],
                    # 條碼
                    [code128_img],
                    # 住戶條碼下方顯示戶號
                    [Paragraph(household_id, voting_option_style)],
                    # 投票選項
                    [Paragraph("□同意  □不同意  □棄權", voting_option_style)],
                ]
                
                ballot_content_table = Table(
                    ballot_content_data,
                    colWidths=[cell_w * 0.95],
                    rowHeights=[6 * mm, 7 * mm, 7 * mm, 1 * mm, 8 * mm, 4 * mm, 5 * mm],
                )
                ballot_content_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    # 邊框
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ]))

                row_cells.append(ballot_content_table)

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
