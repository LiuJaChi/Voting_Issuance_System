"""
投票系統數據庫管理模塊

使用 SQLite 存儲：
- 住戶信息（household_id, name, share_amount）
- 報到記錄（household_id, checked_in_at）
- 投票項目（case_number, name, description, vote_type, pass_percentage）
- 投票記錄（household_id, case_number, vote）
- 條碼映射（household_id, barcode_data）
"""
import sqlite3
import csv
import io
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
            cursor.execute("DELETE FROM barcode_mapping WHERE household_id = ?", (household_id,))
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

    def add_voting_item(self, case_number: str, name: str, description: str = None,
                       vote_type: str = '一般議案', pass_percentage: float = 66.7) -> bool:
        """新增投票項目"""
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

        result = {
            'case_number': case_number,
            'item_name': item['name'],
            'votes': {}
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

    # ─────────────────────────── 投票數據匯出/匯入 ───────────────────────────

    @staticmethod
    def _fmt_timestamp(ts) -> str:
        """將時間戳截取為 'YYYY-MM-DD HH:MM:SS' 格式字符串"""
        return str(ts)[:19] if ts else ''

    def export_voting_data(self, format: str = 'csv', export_path: str = None) -> str:
        """匯出所有投票數據，支持 csv 和 json 兩種格式。

        Returns:
            匯出的文件路徑字符串，失敗時返回空字符串。
        """
        format = format.lower()
        if export_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = f"exports/votes_{timestamp}.{format}"

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 取得所有投票記錄，JOIN 投票項目以獲得 case_name
            cursor.execute("""
                SELECT v.household_id,
                       v.case_number,
                       vi.name AS case_name,
                       v.vote,
                       v.voted_at
                FROM votes v
                LEFT JOIN voting_items vi ON v.case_number = vi.case_number
                ORDER BY v.case_number, v.household_id
            """)
            votes = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM voting_items ORDER BY case_number")
            voting_items = [dict(row) for row in cursor.fetchall()]

            conn.close()

            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            if format == 'csv':
                # utf-8-sig adds a BOM so that Excel on Windows opens the file correctly
                with open(export_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=['household_id', 'case_number', 'case_name', 'vote', 'voted_at']
                    )
                    writer.writeheader()
                    for row in votes:
                        writer.writerow({
                            'household_id': row['household_id'],
                            'case_number': row['case_number'],
                            'case_name': row.get('case_name', ''),
                            'vote': row['vote'],
                            'voted_at': self._fmt_timestamp(row['voted_at']),
                        })
            elif format == 'json':
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'total_records': len(votes),
                    'voting_items': voting_items,
                    'votes': [
                        {
                            'household_id': r['household_id'],
                            'case_number': r['case_number'],
                            'case_name': r.get('case_name', ''),
                            'vote': r['vote'],
                            'voted_at': self._fmt_timestamp(r['voted_at']),
                        }
                        for r in votes
                    ],
                }
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            else:
                print(f"✗ 不支持的格式: {format}")
                return ''

            print(f"✓ 投票數據已匯出到: {export_path}（共 {len(votes)} 筆）")
            return export_path
        except Exception as e:
            print(f"✗ 投票數據匯出失敗: {e}")
            return ''

    def validate_voting_data(self, data: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """驗證匯入的投票數據格式和內容。

        Args:
            data: 每筆記錄包含 household_id, case_number, vote 欄位的列表。

        Returns:
            (valid_rows, errors) — 通過驗證的列表和錯誤訊息列表。
        """
        valid_options = {'同意', '不同意', '棄權'}

        # 預先獲取所有合法的 household_id 和 case_number
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT household_id FROM households")
        existing_households = {row['household_id'] for row in cursor.fetchall()}
        cursor.execute("SELECT case_number FROM voting_items")
        existing_cases = {row['case_number'] for row in cursor.fetchall()}
        conn.close()

        valid_rows: List[Dict] = []
        errors: List[str] = []

        for idx, row in enumerate(data, start=1):
            household_id = str(row.get('household_id', '')).strip()
            case_number = str(row.get('case_number', '')).strip()
            vote = str(row.get('vote', '')).strip()

            if not household_id:
                errors.append(f"第 {idx} 筆：household_id 為空")
                continue
            if not case_number:
                errors.append(f"第 {idx} 筆（{household_id}）：case_number 為空")
                continue
            if vote not in valid_options:
                errors.append(f"第 {idx} 筆（{household_id}/{case_number}）：無效投票選項「{vote}」")
                continue
            if household_id not in existing_households:
                errors.append(f"第 {idx} 筆：戶號「{household_id}」不存在")
                continue
            if case_number not in existing_cases:
                errors.append(f"第 {idx} 筆：案號「{case_number}」不存在")
                continue

            valid_rows.append({
                'household_id': household_id,
                'case_number': case_number,
                'vote': vote,
                'voted_at': str(row.get('voted_at', '')).strip() or None,
            })

        return valid_rows, errors

    def import_voting_data(self, file_path: str, mode: str = 'merge') -> Dict:
        """匯入投票數據。

        Args:
            file_path: CSV 或 JSON 文件路徑。
            mode: 'merge'（合併）或 'replace'（覆蓋）。

        Returns:
            包含 success, skipped, errors, messages 的字典。
        """
        result = {
            'success': 0,
            'skipped': 0,
            'errors': [],
            'messages': [],
        }

        try:
            file_path = str(file_path)
            ext = Path(file_path).suffix.lower()

            # 讀取文件
            raw_rows: List[Dict] = []
            if ext == '.csv':
                with open(file_path, newline='', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    raw_rows = list(reader)
            elif ext == '.json':
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                # 支持兩種 JSON 結構：純列表，或含 "votes" 鍵的物件
                if isinstance(data, list):
                    raw_rows = data
                elif isinstance(data, dict) and 'votes' in data:
                    raw_rows = data['votes']
                else:
                    result['errors'].append('JSON 格式不正確：需要列表或含 "votes" 鍵的物件')
                    return result
            else:
                result['errors'].append(f'不支持的文件格式：{ext}（僅支持 .csv / .json）')
                return result

            if not raw_rows:
                result['messages'].append('文件中沒有數據記錄')
                return result

            # 驗證數據
            valid_rows, errors = self.validate_voting_data(raw_rows)
            result['errors'].extend(errors)

            if not valid_rows:
                result['messages'].append('沒有通過驗證的有效記錄')
                return result

            conn = self.get_connection()
            cursor = conn.cursor()

            # 覆蓋模式：清空所有投票記錄
            if mode == 'replace':
                cursor.execute("DELETE FROM votes")
                conn.commit()
                result['messages'].append('已清空現有投票記錄（覆蓋模式）')

            # 記錄插入前的行數，用於計算實際成功數
            cursor.execute("SELECT COUNT(*) FROM votes")
            count_before = cursor.fetchone()[0]

            # 使用 INSERT OR IGNORE 批量插入，重複記錄由資料庫自動跳過
            rows_with_time = [
                (r['household_id'], r['case_number'], r['vote'], r['voted_at'])
                for r in valid_rows if r.get('voted_at')
            ]
            rows_no_time = [
                (r['household_id'], r['case_number'], r['vote'])
                for r in valid_rows if not r.get('voted_at')
            ]

            if rows_with_time:
                cursor.executemany("""
                    INSERT OR IGNORE INTO votes (household_id, case_number, vote, voted_at)
                    VALUES (?, ?, ?, ?)
                """, rows_with_time)

            if rows_no_time:
                cursor.executemany("""
                    INSERT OR IGNORE INTO votes (household_id, case_number, vote)
                    VALUES (?, ?, ?)
                """, rows_no_time)

            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM votes")
            count_after = cursor.fetchone()[0]
            conn.close()

            result['success'] = count_after - count_before
            result['skipped'] = len(valid_rows) - result['success']

            result['messages'].append(
                f"匯入完成：成功 {result['success']} 筆，"
                f"跳過重複 {result['skipped']} 筆，"
                f"驗證錯誤 {len(result['errors'])} 筆"
            )
            print(f"✓ 投票數據匯入完成: {result}")
        except Exception as e:
            result['errors'].append(f'匯入失敗：{e}')
            print(f"✗ 投票數據匯入失敗: {e}")

        return result

    # ─────────────────────────── 數據導出 ───────────────────────────

    def export_data(self, export_path: str = "exports/data.json") -> bool:
        """導出所有數據到 JSON 文件"""
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

            # 構建導出數據
            export_data = {
                'households': households,
                'check_in_records': check_in_records,
                'barcode_mappings': barcode_mappings,
                'voting_items': voting_items,
                'votes': votes,
                'exported_at': datetime.now().isoformat()
            }

            # 創建導出目錄
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # 寫入 JSON 文件
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"✓ 數據已導出到: {export_path}")
            return True
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

            # 只刪除與住戶相關的數據
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
