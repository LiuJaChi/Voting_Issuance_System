"""
數據庫管理模塊 - 支持住戶面積（持分）
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class Database:
    """SQLite 數據庫管理類"""

    def __init__(self, db_path: str = "data/votes.db"):
        """初始化數據庫連接"""
        self.db_path = db_path
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

        # 系統配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                system_name TEXT NOT NULL,
                total_participants INTEGER NOT NULL,
                pass_percentage REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 住戶表（以戶號為主鍵）- 新增 share_amount 欄位
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS households (
                household_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                share_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 條碼映射表（戶號 <-> 掃描結果）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barcode_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id TEXT NOT NULL UNIQUE,
                barcode_data TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        # 投票項目表（以案號為唯一標識）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voting_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 投票記錄表（戶號+案號為複合主鍵）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                household_id TEXT NOT NULL,
                case_number TEXT NOT NULL,
                vote TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                PRIMARY KEY (household_id, case_number),
                FOREIGN KEY (household_id) REFERENCES households(household_id),
                FOREIGN KEY (case_number) REFERENCES voting_items(case_number)
            )
        """)

        # 報到記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_in_records (
                household_id TEXT PRIMARY KEY,
                checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        conn.commit()
        
        # 檢查是否需要添加 share_amount 欄位（用於數據庫升級）
        cursor.execute("PRAGMA table_info(households)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'share_amount' not in columns:
            cursor.execute("""
                ALTER TABLE households ADD COLUMN share_amount REAL DEFAULT 0.0
            """)
            conn.commit()
        
        conn.close()

    # ─────────────────────────── 配置管理 ───────────────────────────

    def save_config(self, system_name: str, total_participants: int, pass_percentage: float):
        """保存系統配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config")
        cursor.execute("""
            INSERT INTO config (system_name, total_participants, pass_percentage)
            VALUES (?, ?, ?)
        """, (system_name, total_participants, pass_percentage))
        conn.commit()
        conn.close()

    def get_config(self) -> Optional[Dict]:
        """獲取系統配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM config LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ─────────────────────────── 住戶管理 ───────────────────────────

    def add_household(self, household_id: str, name: str, share_amount: float = 0.0) -> bool:
        """新增住戶（支持面積/持分）"""
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
        """住戶報到"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO check_in_records (household_id, device_id)
                VALUES (?, ?)
            """, (household_id, device_id))
            cursor.execute("""
                UPDATE households SET status = 'checked_in'
                WHERE household_id = ?
            """, (household_id,))
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

    def add_voting_item(self, case_number: str, name: str, description: str = None) -> bool:
        """新增投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO voting_items (case_number, name, description)
                VALUES (?, ?, ?)
            """, (case_number, name, description))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
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
            # 更新住戶狀態
            cursor.execute("""
                UPDATE households SET status = 'voted'
                WHERE household_id = ?
            """, (household_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
        except sqlite3.Error as e:
            conn.close()
            print(f"投票記錄錯誤: {e}")
            return False

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

        cursor.execute("SELECT name FROM voting_items WHERE case_number = ?", (case_number,))
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

        result = {'case_number': case_number, 'item_name': item['name'], 'votes': {}}
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

    # ─────────────────────────── 向後兼容 ───────────────────────────

    def add_voter(self, voter_id: str, barcode: str, name: str = None) -> bool:
        """添加投票者（向後兼容，使用 household_id）"""
        return self.add_household(voter_id, name or voter_id)

    def get_voter(self, barcode: str) -> Optional[Dict]:
        """通過條碼（戶號）獲取住戶"""
        return self.get_household(barcode)

    def check_in_voter(self, voter_id: str, barcode: str = None, device_id: str = None) -> bool:
        """報到（向後兼容）"""
        return self.check_in_household(voter_id, device_id)

    # ─────────────────────────── 數據導出 ───────────────────────────

    def export_data(self, export_path: str = "exports/data.json") -> bool:
        """導出所有數據"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            config = self.get_config()

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

            export_data = {
                'config': config,
                'households': households,
                'check_in_records': check_in_records,
                'barcode_mappings': barcode_mappings,
                'voting_items': voting_items,
                'votes': votes,
                'exported_at': datetime.now().isoformat()
            }

            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

            return True
        except Exception as e:
            print(f"數據導出錯誤: {e}")
            return False

    def clear_all_data(self):
        """清空所有數據"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM votes")
        cursor.execute("DELETE FROM check_in_records")
        cursor.execute("DELETE FROM barcode_mapping")
        cursor.execute("DELETE FROM households")
        cursor.execute("DELETE FROM voting_items")
        cursor.execute("DELETE FROM config")
        conn.commit()
        conn.close()

    def clear_household_data(self):
        """清空所有住戶及相關投票/報到記錄（保留投票項目和系統配置）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM votes")
        cursor.execute("DELETE FROM check_in_records")
        cursor.execute("DELETE FROM barcode_mapping")
        cursor.execute("DELETE FROM households")
        conn.commit()
        conn.close()
