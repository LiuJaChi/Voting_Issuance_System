"""
投票系統數據庫管理模塊

使用 SQLite 存儲：
- 住戶信息（household_id, name, share_amount）
- 報到記錄（household_id, checked_in_at）
- 投票項目（case_number, name, description, vote_type, pass_percentage）
- 投票記錄（household_id, case_number, vote）
- 條碼映射（household_id, barcode_data）
"""
import json
import os
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class Database:
    """SQLite 數據庫管理類"""

    def __init__(self, db_path: str = "data/votes.db"):
        """初始化數據庫連接"""
        self.db_path = db_path
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
        except Exception:
            conn.close()
            return False

    def get_household(self, household_id: str) -> Optional[Dict]:
        """通過戶號獲取住戶"""
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
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def import_households(self, households: List[Dict]) -> Tuple[int, int]:
        """批量導入住戶，返回 (成功數, 失敗數)"""
        success = 0
        failed = 0
        for h in households:
            share_amount = h.get('share_amount', 0.0)
            if self.add_household(h['household_id'], h['name'], share_amount):
                success += 1
            else:
                failed += 1
        return success, failed

    # ─────────────────────────── 條碼映射管理 ───────────────────────────

    def add_barcode_mapping(self, household_id: str, barcode_data: str) -> bool:
        """添加戶號-條碼映射"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 先刪除該戶號的舊映射（如果存在）
            cursor.execute("DELETE FROM barcode_mapping WHERE household_id = ?", (household_id,))

            # 插入新映射
            cursor.execute("""
                INSERT INTO barcode_mapping (household_id, barcode_data)
                VALUES (?, ?)
            """, (household_id, barcode_data))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_household_id_by_barcode(self, barcode_data: str) -> Optional[str]:
        """通過條碼查詢戶號"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT household_id FROM barcode_mapping WHERE barcode_data = ?
        """, (barcode_data,))
        row = cursor.fetchone()
        conn.close()
        return row['household_id'] if row else None

    def get_barcode_by_household_id(self, household_id: str) -> Optional[str]:
        """通過戶號查詢條碼"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT barcode_data FROM barcode_mapping WHERE household_id = ?
        """, (household_id,))
        row = cursor.fetchone()
        conn.close()
        return row['barcode_data'] if row else None

    def get_all_barcode_mappings(self) -> List[Dict]:
        """獲取所有條碼映射"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT household_id, barcode_data FROM barcode_mapping ORDER BY household_id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_barcode_mapping(self, household_id: str) -> bool:
        """刪除條碼映射"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM barcode_mapping WHERE household_id = ?", (household_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    # ─────────────────────────── 報到管理 ───────────────────────────

    def check_in_household(self, household_id: str, device_id: str = None) -> bool:
        """住戶報到 - 使用電腦當前系統時間"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 使用電腦當前系統時間，而不是數據庫服務器時間
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"📝 報到時間: {current_time} (戶號: {household_id})")

            cursor.execute("""
                INSERT INTO check_in_records (household_id, checked_in_at, device_id)
                VALUES (?, ?, ?)
            """, (household_id, current_time, device_id))
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

        cursor.execute("SELECT COUNT(*) as count FROM households")
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM check_in_records")
        checked_in = cursor.fetchone()['count']

        conn.close()

        percentage = (checked_in / total * 100) if total > 0 else 0
        return {
            'total_expected': total,
            'checked_in': checked_in,
            'percentage': round(percentage, 2)
        }

    # ─────────────────────────── 投票項目管理 ───────────────────────────

    def add_voting_item(self, case_number: str, name: str, description: str = "",
                        vote_type: str = "一般議案", pass_percentage: float = 66.7) -> bool:
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

    def update_voting_item(self, case_number: str, name: str, description: str = "",
                          vote_type: str = "一般議案", pass_percentage: float = 66.7) -> bool:
        """更新投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE voting_items SET name = ?, description = ?, vote_type = ?, pass_percentage = ?
                WHERE case_number = ?
            """, (name, description, vote_type, pass_percentage, case_number))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"更新投票項目失敗: {e}")
            return False

    def delete_voting_item(self, case_number: str) -> bool:
        """刪除投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM voting_items WHERE case_number = ?", (case_number,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    def get_voting_item(self, case_number: str) -> Optional[Dict]:
        """通過案號獲取投票項目"""
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
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─────────────────────────── 投票管理 ───────────────────────────

    def record_vote(self, household_id: str, case_number: str, vote: str,
                    device_id: str = None) -> bool:
        """記錄投票（戶號+案號為複合主鍵，每個戶號每個案號只能投票一次）"""
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
        """更新投票（修改已投票的選項）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE votes SET vote = ? WHERE household_id = ? AND case_number = ?
            """, (vote, household_id, case_number))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    def delete_vote(self, household_id: str, case_number: str) -> bool:
        """刪除投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM votes WHERE household_id = ? AND case_number = ?
            """, (household_id, case_number))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    def get_vote(self, household_id: str, case_number: str) -> Optional[str]:
        """查詢某住戶對某案號的投票選項"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vote FROM votes WHERE household_id = ? AND case_number = ?
        """, (household_id, case_number))
        row = cursor.fetchone()
        conn.close()
        return row['vote'] if row else None

    def get_all_votes_for_case(self, case_number: str) -> List[Dict]:
        """獲取某案號的所有投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE case_number = ? ORDER BY voted_at
        """, (case_number,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_votes_for_household(self, household_id: str) -> List[Dict]:
        """獲取某住戶的所有投票記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE household_id = ? ORDER BY voted_at
        """, (household_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def has_voted(self, household_id: str, case_number: str) -> bool:
        """檢查是否已投票"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM votes WHERE household_id = ? AND case_number = ?
        """, (household_id, case_number))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def get_voting_results(self, case_number: str) -> Dict:
        """獲取某案號的投票結果"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM voting_items WHERE case_number = ?", (case_number,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return {}

        cursor.execute("""
            SELECT vote, COUNT(*) as count
            FROM votes
            WHERE case_number = ?
            GROUP BY vote
        """, (case_number,))

        rows = cursor.fetchall()
        conn.close()

        # 初始化所有三個投票選項為 0
        result = {
            'case_number': case_number,
            'item_name': item['name'],
            'vote_type': item['vote_type'],
            'pass_percentage': item['pass_percentage'],
            'votes': {
                '同意': 0,
                '不同意': 0,
                '棄權': 0
            }
        }

        total = 0
        for row in rows:
            result['votes'][row['vote']] = row['count']
            total += row['count']

        result['total'] = total
        return result

    def get_all_voting_results(self) -> List[Dict]:
        """獲取所有投票項目的結果"""
        items = self.get_all_voting_items()
        return [self.get_voting_results(item['case_number']) for item in items]

    # ─────────────────────────── 數據管理 ───────────────────────────

    def export_data(self) -> bool:
        """導出所有數據庫內容到 exports/ 目錄下的 JSON 檔案"""
        conn = None
        try:
            os.makedirs("exports", exist_ok=True)
            export_path = os.path.join("exports", "data.json")

            data = {
                "exported_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "households": self.get_all_households(),
                "check_in_records": [],
                "voting_items": self.get_all_voting_items(),
                "votes": [],
                "barcode_mapping": self.get_all_barcode_mappings(),
            }

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM check_in_records ORDER BY checked_in_at")
            data["check_in_records"] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM votes ORDER BY voted_at")
            data["votes"] = [dict(row) for row in cursor.fetchall()]

            conn.close()
            conn = None

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            return True
        except Exception as e:
            print(f"導出數據失敗: {e}")
            return False
        finally:
            if conn is not None:
                conn.close()

    def clear_all_data(self) -> bool:
        """清空所有資料表中的資料（households, check_in_records, voting_items, votes, barcode_mapping）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM votes")
            cursor.execute("DELETE FROM check_in_records")
            cursor.execute("DELETE FROM barcode_mapping")
            cursor.execute("DELETE FROM voting_items")
            cursor.execute("DELETE FROM households")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"清空數據失敗: {e}")
            return False

    # ─────────────────────────── 向後兼容 ───────────────────────────

    def add_voter(self, voter_id: str, barcode: str, name: str = None) -> bool:
        """添加投票者（向後兼容，使用 household_id）"""
        return self.add_household(voter_id, name or voter_id)

    def get_voter(self, barcode: str) -> Optional[Dict]:
        """通過條碼（戶號）獲取住戶"""
        return self.get_household(barcode)

    def get_all_voters(self) -> List[Dict]:
        """獲取所有投票者（向後兼容）"""
        return self.get_all_households()
