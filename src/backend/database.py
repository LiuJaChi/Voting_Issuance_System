"""
數據庫管理模塊
"""
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Database:
    """SQLite 數據庫管理類"""

    def __init__(self, db_path: str = "data/votes.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @staticmethod
    def normalize_household_id(household_id: str) -> str:
        return (household_id or "").strip().upper()

    @staticmethod
    def normalize_case_number(case_number: str) -> str:
        return (case_number or "").strip().upper()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY,
                household_id TEXT UNIQUE NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                checked_in_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voting_items (
                id INTEGER PRIMARY KEY,
                case_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY,
                household_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                case_number TEXT NOT NULL,
                vote TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                FOREIGN KEY (item_id) REFERENCES voting_items(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_in_records (
                id INTEGER PRIMARY KEY,
                household_id TEXT NOT NULL,
                barcode TEXT NOT NULL,
                checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT
            )
        """)

        self._migrate_legacy_schema(cursor)
        self._ensure_indexes(cursor)

        conn.commit()
        conn.close()

    def _get_columns(self, cursor, table_name: str) -> List[str]:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    def _migrate_legacy_schema(self, cursor):
        self._migrate_voters_table(cursor)
        self._migrate_voting_items_table(cursor)
        self._migrate_votes_table(cursor)
        self._migrate_check_in_table(cursor)

    def _migrate_voters_table(self, cursor):
        columns = self._get_columns(cursor, "voters")
        if "household_id" not in columns:
            cursor.execute("ALTER TABLE voters ADD COLUMN household_id TEXT")
            columns.append("household_id")

        household_sources = ["NULLIF(household_id, '')"]
        if "barcode" in columns:
            household_sources.append("NULLIF(barcode, '')")
        if "voter_id" in columns:
            household_sources.append("NULLIF(voter_id, '')")
        household_expr = f"COALESCE({', '.join(household_sources)})"

        cursor.execute(f"""
            UPDATE voters
            SET household_id = UPPER(TRIM({household_expr}))
            WHERE household_id IS NULL OR TRIM(household_id) = ''
        """)
        cursor.execute("UPDATE voters SET household_id = UPPER(TRIM(household_id)) WHERE household_id IS NOT NULL")

        if "barcode" in columns:
            cursor.execute("UPDATE voters SET barcode = UPPER(TRIM(barcode)) WHERE barcode IS NOT NULL")
            cursor.execute("UPDATE voters SET barcode = household_id WHERE barcode IS NULL OR TRIM(barcode) = ''")
        if "name" in columns:
            cursor.execute("UPDATE voters SET name = household_id WHERE name IS NULL OR TRIM(name) = ''")

        cursor.execute("DELETE FROM voters WHERE household_id IS NULL OR TRIM(household_id) = ''")
        cursor.execute("""
            DELETE FROM voters
            WHERE id NOT IN (
                SELECT MIN(id) FROM voters GROUP BY household_id
            )
        """)
        if "barcode" in columns:
            cursor.execute("""
                DELETE FROM voters
                WHERE id NOT IN (
                    SELECT MIN(id) FROM voters GROUP BY barcode
                )
            """)

    def _migrate_voting_items_table(self, cursor):
        columns = self._get_columns(cursor, "voting_items")
        if "case_number" not in columns:
            cursor.execute("ALTER TABLE voting_items ADD COLUMN case_number TEXT")
            columns.append("case_number")

        cursor.execute("""
            UPDATE voting_items
            SET case_number = printf('%03d', id)
            WHERE case_number IS NULL OR TRIM(case_number) = ''
        """)
        cursor.execute("UPDATE voting_items SET case_number = UPPER(TRIM(case_number)) WHERE case_number IS NOT NULL")
        cursor.execute("""
            DELETE FROM voting_items
            WHERE id NOT IN (
                SELECT MIN(id) FROM voting_items GROUP BY case_number
            )
        """)

    def _migrate_votes_table(self, cursor):
        columns = self._get_columns(cursor, "votes")
        if "household_id" not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN household_id TEXT")
            columns.append("household_id")
        if "case_number" not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN case_number TEXT")
            columns.append("case_number")

        if "voter_id" in columns:
            cursor.execute("""
                UPDATE votes
                SET household_id = UPPER(TRIM(voter_id))
                WHERE household_id IS NULL OR TRIM(household_id) = ''
            """)

        cursor.execute("""
            UPDATE votes
            SET household_id = UPPER(TRIM(household_id))
            WHERE household_id IS NOT NULL
        """)
        cursor.execute("""
            UPDATE votes
            SET case_number = (
                SELECT vi.case_number FROM voting_items vi WHERE vi.id = votes.item_id
            )
            WHERE case_number IS NULL OR TRIM(case_number) = ''
        """)
        cursor.execute("UPDATE votes SET case_number = UPPER(TRIM(case_number)) WHERE case_number IS NOT NULL")

        cursor.execute("""
            DELETE FROM votes
            WHERE household_id IS NULL OR TRIM(household_id) = ''
               OR case_number IS NULL OR TRIM(case_number) = ''
        """)
        cursor.execute("""
            DELETE FROM votes
            WHERE id NOT IN (
                SELECT MIN(id) FROM votes GROUP BY household_id, case_number
            )
        """)

    def _migrate_check_in_table(self, cursor):
        columns = self._get_columns(cursor, "check_in_records")
        if "household_id" not in columns:
            cursor.execute("ALTER TABLE check_in_records ADD COLUMN household_id TEXT")
            columns.append("household_id")

        if "voter_id" in columns:
            cursor.execute("""
                UPDATE check_in_records
                SET household_id = UPPER(TRIM(voter_id))
                WHERE household_id IS NULL OR TRIM(household_id) = ''
            """)

        cursor.execute("""
            UPDATE check_in_records
            SET household_id = UPPER(TRIM(COALESCE(NULLIF(household_id, ''), NULLIF(barcode, ''))))
            WHERE household_id IS NULL OR TRIM(household_id) = ''
        """)
        cursor.execute("UPDATE check_in_records SET household_id = UPPER(TRIM(household_id)) WHERE household_id IS NOT NULL")
        cursor.execute("UPDATE check_in_records SET barcode = UPPER(TRIM(barcode)) WHERE barcode IS NOT NULL")
        cursor.execute("UPDATE check_in_records SET barcode = household_id WHERE barcode IS NULL OR TRIM(barcode) = ''")

        cursor.execute("DELETE FROM check_in_records WHERE household_id IS NULL OR TRIM(household_id) = ''")
        cursor.execute("""
            DELETE FROM check_in_records
            WHERE id NOT IN (
                SELECT MIN(id) FROM check_in_records GROUP BY household_id
            )
        """)

    def _ensure_indexes(self, cursor):
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_voters_household_id ON voters(household_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_voters_barcode ON voters(barcode)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_voting_items_case_number ON voting_items(case_number)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_votes_household_case ON votes(household_id, case_number)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_check_in_household ON check_in_records(household_id)")

    def save_config(self, system_name: str, total_participants: int, pass_percentage: float):
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM config LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_voter(self, household_id: str, name: str, barcode: str = None) -> bool:
        household_id = self.normalize_household_id(household_id)
        barcode = self.normalize_household_id(barcode or household_id)
        name = (name or "").strip()
        if not household_id or not name:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO voters (household_id, barcode, name)
                VALUES (?, ?, ?)
            """, (household_id, barcode, name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_voters(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT household_id, barcode, name, status, checked_in_at, created_at
            FROM voters
            ORDER BY household_id
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def import_voters_from_csv(self, file_path: str) -> Tuple[int, int]:
        headers_map = {
            'household_id': {'household_id', 'household', '戶號', '戶別'},
            'name': {'name', '姓名', '戶名'}
        }

        def find_key(fieldnames: List[str], target: str) -> Optional[str]:
            normalized = {name.strip().lower(): name for name in fieldnames if name}
            for alias in headers_map[target]:
                matched = normalized.get(alias.lower())
                if matched:
                    return matched
            return None

        last_error = None
        for encoding in ('utf-8-sig', 'utf-8', 'cp950', 'big5'):
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as csv_file:
                    reader = csv.DictReader(csv_file)
                    fieldnames = reader.fieldnames or []
                    household_key = find_key(fieldnames, 'household_id')
                    name_key = find_key(fieldnames, 'name')
                    if not household_key or not name_key:
                        raise ValueError('CSV 必須包含 household_id（或 戶號/戶別）與 name（或 姓名/戶名）欄位')

                    inserted = 0
                    skipped = 0
                    for row in reader:
                        household_id = self.normalize_household_id(row.get(household_key, ''))
                        name = (row.get(name_key, '') or '').strip()
                        if not household_id or not name:
                            skipped += 1
                            continue
                        if self.add_voter(household_id, name, household_id):
                            inserted += 1
                        else:
                            skipped += 1
                    return inserted, skipped
            except UnicodeDecodeError as exc:
                last_error = exc
                continue

        raise ValueError(str(last_error) if last_error else 'CSV 編碼不支援或檔案內容無法讀取；已嘗試 utf-8-sig、utf-8、cp950、big5')

    def get_voter(self, barcode: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM voters WHERE barcode = ?", (self.normalize_household_id(barcode),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def check_in_voter(self, household_id: str, barcode: str, device_id: str = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        household_id = self.normalize_household_id(household_id)
        barcode = self.normalize_household_id(barcode)
        try:
            cursor.execute("""
                INSERT INTO check_in_records (household_id, barcode, device_id)
                VALUES (?, ?, ?)
            """, (household_id, barcode, device_id))
            cursor.execute("""
                UPDATE voters
                SET status = 'checked_in', checked_in_at = CURRENT_TIMESTAMP
                WHERE household_id = ?
            """, (household_id,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def add_voting_item(self, case_number: str, name: str, description: str = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        case_number = self.normalize_case_number(case_number)
        name = (name or '').strip()
        description = (description or '').strip() or None
        if not case_number or not name:
            conn.close()
            return 0

        try:
            cursor.execute("""
                INSERT INTO voting_items (case_number, name, description)
                VALUES (?, ?, ?)
            """, (case_number, name, description))
            item_id = cursor.lastrowid
            conn.commit()
            return item_id
        except sqlite3.IntegrityError:
            return 0
        finally:
            conn.close()

    def get_voting_items(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, case_number, name, description
            FROM voting_items
            ORDER BY case_number, id
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_voted_item_ids(self, household_id: str) -> List[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT item_id FROM votes WHERE household_id = ?", (self.normalize_household_id(household_id),))
        item_ids = [row['item_id'] for row in cursor.fetchall()]
        conn.close()
        return item_ids

    def record_vote(self, household_id: str, item_id: int, vote: str, device_id: str = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        household_id = self.normalize_household_id(household_id)

        try:
            cursor.execute("SELECT case_number FROM voting_items WHERE id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                return False

            cursor.execute("""
                INSERT INTO votes (household_id, item_id, case_number, vote, device_id)
                VALUES (?, ?, ?, ?, ?)
            """, (household_id, item_id, item['case_number'], vote, device_id))
            cursor.execute("UPDATE voters SET status = 'voted' WHERE household_id = ?", (household_id,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            print(f"投票記錄錯誤: {e}")
            return False
        finally:
            conn.close()

    def get_check_in_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        config = self.get_config()
        if not config:
            conn.close()
            return {}

        cursor.execute("SELECT COUNT(*) as count FROM check_in_records")
        checked_in = cursor.fetchone()['count']
        total = config['total_participants']
        percentage = (checked_in / total * 100) if total > 0 else 0
        conn.close()

        return {
            'total_expected': total,
            'checked_in': checked_in,
            'percentage': round(percentage, 2)
        }

    def get_voting_results(self, item_id: int) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT case_number, name FROM voting_items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return {}

        cursor.execute("""
            SELECT vote, COUNT(*) as count
            FROM votes
            WHERE item_id = ?
            GROUP BY vote
        """, (item_id,))
        rows = cursor.fetchall()
        conn.close()

        result = {
            'case_number': item['case_number'],
            'item_name': item['name'],
            'votes': {}
        }
        total = 0
        for row in rows:
            result['votes'][row['vote']] = row['count']
            total += row['count']
        result['total'] = total
        return result

    def export_data(self, export_path: str = "exports/data.json") -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            config = self.get_config()

            cursor.execute("SELECT household_id, barcode, name, status, checked_in_at, created_at FROM voters ORDER BY household_id")
            voters = [dict(row) for row in cursor.fetchall()]
            cursor.execute("SELECT * FROM check_in_records ORDER BY checked_in_at DESC")
            check_in_records = [dict(row) for row in cursor.fetchall()]
            cursor.execute("SELECT * FROM voting_items ORDER BY case_number, id")
            voting_items = [dict(row) for row in cursor.fetchall()]
            cursor.execute("SELECT * FROM votes ORDER BY voted_at DESC")
            votes = [dict(row) for row in cursor.fetchall()]
            conn.close()

            export_data = {
                'config': config,
                'voters': voters,
                'check_in_records': check_in_records,
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM votes")
        cursor.execute("DELETE FROM check_in_records")
        cursor.execute("DELETE FROM voters")
        cursor.execute("DELETE FROM voting_items")
        cursor.execute("DELETE FROM config")
        conn.commit()
        conn.close()
