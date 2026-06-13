"""
SQLite 數據庫管理模塊
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from html import escape
from src.backend.config_manager import ConfigManager


class Database:
    """SQLite 數據庫管理類"""

    def __init__(self, db_path: str = "data/votes.db", config_manager: Optional[ConfigManager] = None):
        """初始化數據庫連接"""
        self.db_path = db_path
        self.config_manager = config_manager or ConfigManager()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """獲取數據庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """初始化數據庫表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 住戶表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS households (
                household_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                share_amount REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 報到記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_in_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id TEXT NOT NULL UNIQUE,
                checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        # 投票項目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voting_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                vote_type TEXT DEFAULT '一般議案',
                pass_percentage REAL DEFAULT 66.7,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 投票記錄表（複合主鍵：household_id + case_number）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id TEXT NOT NULL,
                case_number TEXT NOT NULL,
                vote TEXT NOT NULL,
                device_id TEXT,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(household_id, case_number),
                FOREIGN KEY (household_id) REFERENCES households(household_id),
                FOREIGN KEY (case_number) REFERENCES voting_items(case_number)
            )
        """)

        # 條碼映射表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barcode_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id TEXT NOT NULL UNIQUE,
                barcode_data TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        conn.commit()
        conn.close()

    # ─────────────────────────── 住戶管理 ───────────────────────────

    def add_household(self, household_id: str, name: str, share_amount: float = 0.0) -> bool:
        """添加住戶"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO households (household_id, name, share_amount)
                VALUES (?, ?, ?)
            """, (household_id, name, share_amount))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def update_household(self, household_id: str, name: str, share_amount: float = None) -> bool:
        """更新住戶信息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if share_amount is not None:
            cursor.execute("""
                UPDATE households SET name = ?, share_amount = ? WHERE household_id = ?
            """, (name, share_amount, household_id))
        else:
            cursor.execute("""
                UPDATE households SET name = ? WHERE household_id = ?
            """, (name, household_id))

        conn.commit()
        conn.close()
        return True

    def delete_household(self, household_id: str) -> bool:
        """刪除住戶"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM households WHERE household_id = ?", (household_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"刪除住戶失敗: {e}")
            conn.close()
            return False

    def get_household(self, household_id: str) -> Optional[Dict]:
        """獲取住戶信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM households WHERE household_id = ?", (household_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_households(self) -> List[Dict]:
        """獲取所有住戶"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM households ORDER BY household_id")
        households = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return households

    def import_households(self, households: List[Dict]) -> Tuple[int, int]:
        """批量導入住戶"""
        conn = self.get_connection()
        cursor = conn.cursor()
        success = 0
        skipped = 0

        for household in households:
            try:
                cursor.execute("""
                    INSERT INTO households (household_id, name, share_amount)
                    VALUES (?, ?, ?)
                """, (household['household_id'], household['name'], household.get('share_amount', 0.0)))
                success += 1
            except sqlite3.IntegrityError:
                skipped += 1

        conn.commit()
        conn.close()
        return success, skipped

    # ─────────────────────────── 條碼管理 ───────────────────────────

    def get_household_id_by_barcode(self, barcode_data: str) -> Optional[str]:
        """通過條碼獲取住戶ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT household_id FROM barcode_mapping WHERE barcode_data = ?", (barcode_data,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_barcode_by_household_id(self, household_id: str) -> Optional[str]:
        """通過住戶ID獲取條碼"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT barcode_data FROM barcode_mapping WHERE household_id = ?", (household_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_barcode_mappings(self) -> List[Dict]:
        """獲取所有條碼映射"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM barcode_mapping")
        mappings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return mappings

    def delete_barcode_mapping(self, household_id: str) -> bool:
        """刪除條碼映射"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM barcode_mapping WHERE household_id = ?", (household_id,))
        conn.commit()
        conn.close()
        return True

    # ─────────────────────────── 報到管理 ───────────────────────────

    def add_check_in(self, household_id: str, device_id: str = None) -> bool:
        """添加報到記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO check_in_records (household_id, device_id)
                VALUES (?, ?)
            """, (household_id, device_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_check_in_stats(self) -> Dict:
        """獲取報到統計"""
        conn = self.get_connection()
        cursor = conn.cursor()

        total_config = self.config_manager.get_config('total_participants', 0)
        try:
            total_expected = int(total_config)
        except (TypeError, ValueError):
            total_expected = 0

        cursor.execute("SELECT COUNT(*) FROM check_in_records")
        checked_in = cursor.fetchone()[0]

        conn.close()

        return {
            'expected_total': total_expected,
            'checked_in': checked_in,
            'not_checked_in': total_expected - checked_in,
            'checked_in_percentage': (checked_in / total_expected * 100) if total_expected > 0 else 0
        }

    def get_check_in_area_stats(self) -> Dict:
        """獲取報到面積統計"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 總面積
        cursor.execute("SELECT SUM(share_amount) FROM households")
        total_area = cursor.fetchone()[0] or 0.0

        # 已報到面積
        cursor.execute("""
            SELECT SUM(h.share_amount)
            FROM households h
            LEFT JOIN check_in_records c ON h.household_id = c.household_id
            WHERE c.household_id IS NOT NULL
        """)
        checked_in_area = cursor.fetchone()[0] or 0.0

        conn.close()

        return {
            'total_area': total_area,
            'checked_in_area': checked_in_area,
            'not_checked_in_area': total_area - checked_in_area,
            'checked_in_area_percentage': (checked_in_area / total_area * 100) if total_area > 0 else 0
        }

    def is_checked_in(self, household_id: str) -> bool:
        """檢查是否已報到"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM check_in_records WHERE household_id = ?", (household_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def clear_check_in_data(self) -> bool:
        """清空報到數據"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM check_in_records")
            conn.commit()
            conn.close()
            print("✓ 報到數據已清空")
            return True
        except Exception as e:
            print(f"✗ 清空報到數據失敗: {e}")
            return False

    # ─────────────────────────── 投票項目管理 ───────────────────────────

    def add_voting_item(self, case_number: str, name: str, description: str = '',
                       vote_type: str = '一般議案', pass_percentage: float = 66.7) -> bool:
        """添加投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO voting_items (case_number, name, description, vote_type, pass_percentage)
                VALUES (?, ?, ?, ?, ?)
            """, (case_number, name, description, vote_type, pass_percentage))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def update_voting_item(self, case_number: str, name: str, description: str,
                          vote_type: str, pass_percentage: float) -> bool:
        """更新投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE voting_items
            SET name = ?, description = ?, vote_type = ?, pass_percentage = ?
            WHERE case_number = ?
        """, (name, description, vote_type, pass_percentage, case_number))
        conn.commit()
        conn.close()
        return True

    def delete_voting_item(self, case_number: str) -> bool:
        """刪除投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM voting_items WHERE case_number = ?", (case_number,))
        conn.commit()
        conn.close()
        return True

    def get_voting_item(self, case_number: str) -> Optional[Dict]:
        """獲取投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM voting_items WHERE case_number = ?", (case_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_voting_items(self) -> List[Dict]:
        """獲取所有投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM voting_items ORDER BY case_number")
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return items

    # ─────────────────────────── 投票記錄管理 ───────────────────────────

    def add_vote(self, household_id: str, case_number: str, vote: str, device_id: str = None) -> bool:
        """添加投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO votes (household_id, case_number, vote, device_id)
                VALUES (?, ?, ?, ?)
            """, (household_id, case_number, vote, device_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def update_vote(self, household_id: str, case_number: str, vote: str) -> bool:
        """更新投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE votes SET vote = ? WHERE household_id = ? AND case_number = ?
        """, (vote, household_id, case_number))
        conn.commit()
        conn.close()
        return True

    def delete_vote(self, household_id: str, case_number: str) -> bool:
        """刪除投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM votes WHERE household_id = ? AND case_number = ?
        """, (household_id, case_number))
        conn.commit()
        conn.close()
        return True

    def get_vote(self, household_id: str, case_number: str) -> Optional[str]:
        """獲取投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vote FROM votes WHERE household_id = ? AND case_number = ?
        """, (household_id, case_number))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_votes_for_case(self, case_number: str) -> List[Dict]:
        """獲取某案件的所有投票"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE case_number = ? ORDER BY household_id
        """, (case_number,))
        votes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return votes

    def get_voting_data_with_details(self, case_number: str) -> List[Dict]:
        """獲取投票數據（包含住戶詳情）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.*, h.name, h.share_amount
            FROM votes v
            LEFT JOIN households h ON v.household_id = h.household_id
            WHERE v.case_number = ?
        """, (case_number,))
        votes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return votes

    def get_all_votes_for_household(self, household_id: str) -> List[Dict]:
        """獲取某住戶的所有投票"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE household_id = ? ORDER BY case_number
        """, (household_id,))
        votes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return votes

    def has_voted(self, household_id: str, case_number: str) -> bool:
        """檢查是否已投票"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM votes WHERE household_id = ? AND case_number = ?
        """, (household_id, case_number))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def get_voting_results(self, case_number: str) -> Dict:
        """獲取投票結果統計"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 獲取投票項目
        voting_item = self.get_voting_item(case_number)
        if not voting_item:
            return {}

        # 計算投票統計
        cursor.execute("""
            SELECT vote, COUNT(*) as count, SUM(h.share_amount) as area
            FROM votes v
            LEFT JOIN households h ON v.household_id = h.household_id
            WHERE v.case_number = ?
            GROUP BY vote
        """, (case_number,))

        results = {
            'case_number': case_number,
            'name': voting_item['name'],
            'by_vote': {},
            'total_count': 0,
            'total_area': 0.0
        }

        for row in cursor.fetchall():
            vote_type = row[0]
            count = row[1]
            area = row[2] or 0.0
            results['by_vote'][vote_type] = {
                'count': count,
                'area': area,
                'area_percentage': 0.0
            }
            results['total_count'] += count
            results['total_area'] += area

        # 計算百分比
        for vote_type in results['by_vote']:
            if results['total_area'] > 0:
                results['by_vote'][vote_type]['area_percentage'] = (
                    results['by_vote'][vote_type]['area'] / results['total_area'] * 100
                )

        conn.close()
        return results

    def get_voting_statistics(self, case_number: str) -> Dict:
        """獲取投票統計"""
        return self.get_voting_results(case_number)

    # ─────────────────────────── 數據導出 ───────────────────────────

    def export_data(self, export_path: str = None) -> bool:
        """導出所有數據到 XLSX 文件"""
        if export_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = f"exports/data_{timestamp}.xlsx"

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 獲取所有表的數據
            cursor.execute("SELECT * FROM households")
            households = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM check_in_records")
            check_in_records = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM barcode_mapping")
            barcode_mappings = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM voting_items")
            voting_items = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM votes")
            votes = [dict(row) for row in cursor.fetchall()]

            conn.close()

            # 創建工作簿
            wb = Workbook()
            ws_households = wb.active
            ws_households.title = "住戶"

            # 住戶工作表
            ws_households.append(["戶號", "戶名", "面積(坪)", "創建時間"])
            for h in households:
                ws_households.append([
                    h.get('household_id', ''),
                    h.get('name', ''),
                    h.get('share_amount', 0.0),
                    h.get('created_at', '')
                ])

            # 報到記錄工作表
            ws_check_in = wb.create_sheet("報到記錄")
            ws_check_in.append(["戶號", "報到時間", "設備ID"])
            for c in check_in_records:
                ws_check_in.append([
                    c.get('household_id', ''),
                    c.get('checked_in_at', ''),
                    c.get('device_id', '')
                ])

            # 投票項目工作表
            ws_items = wb.create_sheet("投票項目")
            ws_items.append(["案號", "項目名稱", "描述", "投票類型", "通過百分比", "創建時間"])
            for item in voting_items:
                ws_items.append([
                    item.get('case_number', ''),
                    item.get('name', ''),
                    item.get('description', ''),
                    item.get('vote_type', ''),
                    item.get('pass_percentage', 0.0),
                    item.get('created_at', '')
                ])

            # 投票記錄工作表
            ws_votes = wb.create_sheet("投票記錄")
            ws_votes.append(["戶號", "案號", "投票", "設備ID", "投票時間"])
            for v in votes:
                ws_votes.append([
                    v.get('household_id', ''),
                    v.get('case_number', ''),
                    v.get('vote', ''),
                    v.get('device_id', ''),
                    v.get('voted_at', '')
                ])

            # 創建導出目錄
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存工作簿
            wb.save(export_path)

            print(f"✓ 數據已導出到: {export_path}")
            return export_path
        except Exception as e:
            print(f"✗ 數據導出失敗: {e}")
            return False

    # ─────────────────────────── 數據清空 ───────────────────────────

    def clear_all_data(self) -> bool:
        """清空所有數據（所有表）"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 刪除所有表中的數據
            cursor.execute("DELETE FROM votes")
            cursor.execute("DELETE FROM check_in_records")
            cursor.execute("DELETE FROM barcode_mapping")
            cursor.execute("DELETE FROM voting_items")
            cursor.execute("DELETE FROM households")

            conn.commit()
            conn.close()

            print("✓ 所有數據已清空")
            return True
        except Exception as e:
            print(f"✗ 清空數據失敗: {e}")
            return False

    def clear_household_data(self) -> bool:
        """清空住戶及相關數據（保留投票項目）"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM votes")
            cursor.execute("DELETE FROM check_in_records")
            cursor.execute("DELETE FROM barcode_mapping")
            cursor.execute("DELETE FROM households")

            conn.commit()
            conn.close()

            print("✓ 住戶數據已清空")
            return True
        except Exception as e:
            print(f"✗ 清空住戶數據失敗: {e}")
            return False
