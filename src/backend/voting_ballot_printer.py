"""
投票單 PDF 生成模塊 - 使用 python-barcode 生成 Code128 條碼圖像

投票單規格：
- 每張投票單：案號 + 項目名稱 + 投票種類 + 描述 + 住戶條碼 + 投票選項
- 每張大小：約 95mm × 70mm
- 每頁 A4：2 欄 × 4 列 = 8 張
- 內容：第X案 + 項目名稱 + 投票種類 + 描述 + 住戶條碼 + 投票選項(同意/不同意/棄權)
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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
        
        self._init_chinese_fonts()

    def _init_chinese_fonts(self):
        """初始化繁體中文字體支持"""
        try:
            # 嘗試註冊中文字體
            font_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
                "/System/Library/Fonts/STHeiti Medium.ttf",  # macOS
                "C:\\Windows\\Fonts\\kaiu.ttf",  # Windows (標楷體)
                "C:\\Windows\\Fonts\\msyh.ttf",  # Windows (微軟雅黑)
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    pdfmetrics.registerFont(TTFont('ChineseFontBold', font_path))
                    break
        except Exception as e:
            print(f"⚠ 中文字體初始化失敗: {e}，將使用默認字體")

    def _cleanup_temp_barcode_dir(self):
        """清理臨時條碼目錄"""
        try:
            if os.path.exists(self.temp_barcode_dir):
                shutil.rmtree(self.temp_barcode_dir)
        except Exception as e:
            print(f"⚠ 清理臨時文件失敗: {e}")

    def _generate_code128_image(self, content: str) -> str:
        """
        生成 Code128 條碼圖像
        
        Args:
            content: 條碼內容
            
        Returns:
            條碼圖像路徑
        """
        try:
            output_path = os.path.join(self.temp_barcode_dir, f"{content}.png")
            
            # 生成 Code128 條碼
            ean = barcode.get('code128', content, writer=ImageWriter())
            ean.save(output_path.replace('.png', ''))
            
            return output_path
        except Exception as e:
            print(f"⚠ 生成條碼失敗 ({content}): {e}")
            return None

    def generate_pdf(
        self,
        voting_data: List[Dict],
        filename: str = "voting_ballots.pdf"
    ) -> str:
        """
        生成投票單 PDF
        
        投票單格式：
        第X案 + 項目名稱 + 投票種類 + 描述 + 住戶條碼 + 投票選項
        
        Args:
            voting_data: [
                {
                    'case_number': '1',
                    'name': '物業管理費調整',
                    'vote_type': '重大議案',
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
        
        # 檢查中文字體是否可用
        try:
            pdfmetrics.getFont('ChineseFont')
            font_name = 'ChineseFont'
            font_bold_name = 'ChineseFontBold'
        except:
            font_name = 'Helvetica'
            font_bold_name = 'Helvetica-Bold'
        
        # 案號樣式
        case_number_style = ParagraphStyle(
            'CaseNumber',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=14,
            leading=16,
            fontName=font_bold_name,
            textColor=colors.darkblue,
        )
        
        # 項目名稱樣式
        item_name_style = ParagraphStyle(
            'ItemName',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=9,
            leading=10,
            fontName=font_name,
            textColor=colors.darkblue,
        )
        
        # 投票種類樣式
        vote_type_style = ParagraphStyle(
            'VoteType',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=7,
            leading=8,
            fontName=font_name,
            textColor=colors.darkblue,
        )
        
        # 描述樣式
        description_style = ParagraphStyle(
            'Description',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=7,
            leading=8,
            fontName=font_name,
            textColor=colors.black,
        )
        
        # 投票選項樣式 - 放大字體從 6pt 改為 12pt
        voting_option_style = ParagraphStyle(
            'VotingOption',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            leading=14,
            fontName=font_bold_name,
            textColor=colors.darkred,
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
            vote_type = case.get('vote_type', '一般議案')
            description = case.get('description', '')
            households = case.get('households', [])
            
            print(f"\n📋 處理投票案號 {case_idx + 1}/{len(voting_data)}: 第{case_number}案 {case_name}")
            
            # 遍歷每個住戶
            for household_idx, household in enumerate(households):
                household_id = household['household_id']
                
                # 生成條碼
                barcode_path = self._generate_code128_image(household_id)
                
                if barcode_path and os.path.exists(barcode_path):
                    code128_img = RLImage(barcode_path, width=7 * mm, height=4 * mm)
                else:
                    code128_img = Paragraph(f"Error: {household_id}", item_name_style)
                
                # 構建投票單內容
                ballot_content_data = [
                    # 第X案
                    [Paragraph(f"第 {case_number} 案", case_number_style)],
                    # 項目名稱
                    [Paragraph(case_name, item_name_style)],
                    # 投票種類
                    [Paragraph(f"({vote_type})", vote_type_style)],
                    # 描述（限制行數）
                    [Paragraph(description[:40] if description else "無", description_style)],
                    # 空白（間距）
                    [Spacer(1, 1 * mm)],
                    # 條碼
                    [code128_img],
                    # 住戶條碼下方顯示戶號
                    [Paragraph(household_id, voting_option_style)],
                    # 投票選項 - 放大字體
                    [Paragraph("□ 同意  □ 不同意  □ 棄權", voting_option_style)],
                ]
                
                ballot_content_table = Table(
                    ballot_content_data,
                    colWidths=[cell_w * 0.95],
                    rowHeights=[6 * mm, 7 * mm, 5 * mm, 6 * mm, 1 * mm, 8 * mm, 4 * mm, 6 * mm],
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
