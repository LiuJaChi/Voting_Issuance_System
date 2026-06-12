    def get_check_in_area_stats(self) -> Dict:
        """獲取報到面積統計（包括坪數和占比）"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 計算總坪數
        cursor.execute("SELECT COALESCE(SUM(share_amount), 0) as total_area FROM households")
        total_area = cursor.fetchone()['total_area']

        # 計算已報到的坪數
        cursor.execute("""
            SELECT COALESCE(SUM(h.share_amount), 0) as checked_in_area
            FROM households h
            INNER JOIN check_in_records c ON h.household_id = c.household_id
        """)
        checked_in_area = cursor.fetchone()['checked_in_area']

        conn.close()

        # 計算坪數占比百分比
        area_percentage = (checked_in_area / total_area * 100) if total_area > 0 else 0
        
        return {
            'total_area': total_area,
            'checked_in_area': checked_in_area,
            'area_percentage': round(area_percentage, 2)
        }
