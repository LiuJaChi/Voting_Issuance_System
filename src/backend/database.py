"""
數據庫管理模塊
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
        
        # 投票者表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY,
                voter_id TEXT UNIQUE NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'pending',
                checked_in_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 投票項目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voting_items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 投票紀錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY,
                voter_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                vote TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                FOREIGN KEY (item_id) REFERENCES voting_items(id)
            )
        """)
        
        # 報到紀錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_in_records (
                id INTEGER PRIMARY KEY,
                voter_id TEXT NOT NULL,
                barcode TEXT NOT NULL,
                checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT,
                UNIQUE(voter_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
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
        
        if row:
            return dict(row)
        return None
    
    def add_voter(self, voter_id: str, barcode: str, name: str = None) -> bool:
        """添加投票者"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO voters (voter_id, barcode, name)
                VALUES (?, ?, ?)
            """, (voter_id, barcode, name))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_voter(self, barcode: str) -> Optional[Dict]:
        """通過條碼獲取投票者"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM voters WHERE barcode = ?", (barcode,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def check_in_voter(self, voter_id: str, barcode: str, device_id: str = None) -> bool:
        """報到投票者"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO check_in_records (voter_id, barcode, device_id)
                VALUES (?, ?, ?)
            """, (voter_id, barcode, device_id))
            
            cursor.execute("""
                UPDATE voters SET status = 'checked_in', checked_in_at = CURRENT_TIMESTAMP
                WHERE voter_id = ?
            """, (voter_id,))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def add_voting_item(self, name: str, description: str = None) -> int:
        """添加投票項目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO voting_items (name, description)
            VALUES (?, ?)
        """, (name, description))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def record_vote(self, voter_id: str, item_id: int, vote: str, device_id: str = None) -> bool:
        """記錄投票"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO votes (voter_id, item_id, vote, device_id)
                VALUES (?, ?, ?, ?)
            """, (voter_id, item_id, vote, device_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            conn.close()
            print(f"投票記錄錯誤: {e}")
            return False
    
    def get_check_in_stats(self) -> Dict:
        """獲取報到統計"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        config = self.get_config()
        if not config:
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
        """獲取投票結果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM voting_items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return {}
        
        cursor.execute("""
            SELECT vote, COUNT(*) as count
            FROM votes
            WHERE item_id = ?
            GROUP BY vote
        """, (item_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = {'item_name': item['name'], 'votes': {}}
        total = 0
        
        for row in rows:
            result['votes'][row['vote']] = row['count']
            total += row['count']
        
        result['total'] = total
        return result
    
    def export_data(self, export_path: str = "exports/data.json") -> bool:
        """導出所有數據"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            config = self.get_config()
            
            cursor.execute("SELECT * FROM check_in_records")
            check_in_records = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM voting_items")
            voting_items = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM votes")
            votes = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            export_data = {
                'config': config,
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
        """清空所有數據"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM votes")
        cursor.execute("DELETE FROM check_in_records")
        cursor.execute("DELETE FROM voters")
        cursor.execute("DELETE FROM voting_items")
        cursor.execute("DELETE FROM config")
        
        conn.commit()
        conn.close()
