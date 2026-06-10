"""
數據合併模塊
"""
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class DataMerger:
    """數據合併和計票工具"""
    
    @staticmethod
    def merge_export_files(file_paths: List[str], output_path: str = "exports/merged_data.json") -> bool:
        """
        合併多個導出的數據文件
        
        Args:
            file_paths: 數據文件路徑列表
            output_path: 合併後的輸出文件路徑
        
        Returns:
            是否成功合併
        """
        try:
            merged_data = {
                'config': None,
                'check_in_records': [],
                'voting_items': [],
                'votes': [],
                'merged_at': datetime.now().isoformat()
            }
            
            # 收集所有唯一的投票項目 ID
            item_id_map = {}
            
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 使用第一個配置（所有文件應該有相同的配置）
                if merged_data['config'] is None and 'config' in data:
                    merged_data['config'] = data['config']
                
                # 合併投票項目
                if 'voting_items' in data:
                    for item in data['voting_items']:
                        item_name = item.get('name')
                        if item_name not in item_id_map:
                            item_id_map[item_name] = len(merged_data['voting_items'])
                            merged_data['voting_items'].append(item)
                
                # 合併報到紀錄（去重）
                if 'check_in_records' in data:
                    existing_voters = {record['voter_id'] for record in merged_data['check_in_records']}
                    for record in data['check_in_records']:
                        if record['voter_id'] not in existing_voters:
                            merged_data['check_in_records'].append(record)
                            existing_voters.add(record['voter_id'])
                
                # 合併投票紀錄
                if 'votes' in data:
                    for vote in data['votes']:
                        merged_data['votes'].append(vote)
            
            # 保存合併後的數據
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"數據合併錯誤: {e}")
            return False
    
    @staticmethod
    def calculate_voting_results(data: Dict, pass_percentage: float) -> Dict:
        """
        計算投票結果
        
        Args:
            data: 合併後的數據
            pass_percentage: 通過所需的百分比
        
        Returns:
            投票結果統計
        """
        results = {
            'total_votes': len(data.get('votes', [])),
            'total_check_in': len(data.get('check_in_records', [])),
            'pass_percentage': pass_percentage,
            'items': {}
        }
        
        # 按投票項目統計
        votes_by_item = {}
        for vote in data.get('votes', []):
            item_id = vote.get('item_id')
            vote_value = vote.get('vote')
            
            if item_id not in votes_by_item:
                votes_by_item[item_id] = {'yes': 0, 'no': 0}
            
            if vote_value.lower() == 'yes':
                votes_by_item[item_id]['yes'] += 1
            else:
                votes_by_item[item_id]['no'] += 1
        
        # 計算每個項目的結果
        for item in data.get('voting_items', []):
            item_id = item.get('id')
            item_name = item.get('name', f"Item {item_id}")
            
            if item_id in votes_by_item:
                yes_count = votes_by_item[item_id]['yes']
                no_count = votes_by_item[item_id]['no']
                total = yes_count + no_count
                yes_percentage = (yes_count / total * 100) if total > 0 else 0
                
                results['items'][item_name] = {
                    'yes': yes_count,
                    'no': no_count,
                    'total': total,
                    'yes_percentage': round(yes_percentage, 2),
                    'passed': yes_percentage >= pass_percentage
                }
        
        return results
    
    @staticmethod
    def export_voting_report(results: Dict, output_path: str = "exports/voting_report.json") -> bool:
        """
        導出投票結果報告
        
        Args:
            results: 投票結果統計
            output_path: 輸出文件路徑
        
        Returns:
            是否成功導出
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"報告導出錯誤: {e}")
            return False