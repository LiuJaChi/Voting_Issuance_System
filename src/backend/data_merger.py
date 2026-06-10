"""
數據合併模塊
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class DataMerger:
    """數據合併和計票工具"""

    @staticmethod
    def _vote_key(vote: Dict) -> Tuple[str, str]:
        return (
            (vote.get('household_id') or '').strip().upper(),
            (vote.get('case_number') or '').strip().upper()
        )

    @staticmethod
    def merge_export_files(file_paths: List[str], output_path: str = "exports/merged_data.json") -> bool:
        """合併多個導出的數據文件"""
        try:
            merged_data = {
                'config': None,
                'voters': [],
                'check_in_records': [],
                'voting_items': [],
                'votes': [],
                'merged_at': datetime.now().isoformat()
            }

            voter_keys = set()
            check_in_keys = set()
            item_keys = set()
            vote_keys = set()

            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if merged_data['config'] is None and 'config' in data:
                    merged_data['config'] = data['config']

                for voter in data.get('voters', []):
                    household_id = (voter.get('household_id') or '').strip().upper()
                    if household_id and household_id not in voter_keys:
                        merged_data['voters'].append(voter)
                        voter_keys.add(household_id)

                for item in data.get('voting_items', []):
                    case_number = (item.get('case_number') or '').strip().upper()
                    key = case_number or item.get('name')
                    if key and key not in item_keys:
                        merged_data['voting_items'].append(item)
                        item_keys.add(key)

                for record in data.get('check_in_records', []):
                    household_id = (record.get('household_id') or '').strip().upper()
                    if household_id and household_id not in check_in_keys:
                        merged_data['check_in_records'].append(record)
                        check_in_keys.add(household_id)

                for vote in data.get('votes', []):
                    key = DataMerger._vote_key(vote)
                    if all(key) and key not in vote_keys:
                        merged_data['votes'].append(vote)
                        vote_keys.add(key)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"數據合併錯誤: {e}")
            return False

    @staticmethod
    def calculate_voting_results(data: Dict, pass_percentage: float) -> Dict:
        """計算投票結果"""
        results = {
            'total_votes': len(data.get('votes', [])),
            'total_check_in': len(data.get('check_in_records', [])),
            'pass_percentage': pass_percentage,
            'skipped_votes_missing_case_number': 0,
            'items': {}
        }

        votes_by_case = {}
        for vote in data.get('votes', []):
            case_number = (vote.get('case_number') or '').strip().upper()
            vote_value = (vote.get('vote') or '').lower()
            if not case_number:
                results['skipped_votes_missing_case_number'] += 1
                continue
            if case_number not in votes_by_case:
                votes_by_case[case_number] = {'yes': 0, 'no': 0}
            if vote_value == 'yes':
                votes_by_case[case_number]['yes'] += 1
            else:
                votes_by_case[case_number]['no'] += 1

        for item in data.get('voting_items', []):
            case_number = (item.get('case_number') or '').strip().upper()
            item_name = item.get('name', f"Item {case_number or item.get('id')}")
            key = case_number or str(item.get('id'))
            yes_count = votes_by_case.get(case_number, {}).get('yes', 0)
            no_count = votes_by_case.get(case_number, {}).get('no', 0)
            total = yes_count + no_count
            yes_percentage = (yes_count / total * 100) if total > 0 else 0
            results['items'][key] = {
                'case_number': case_number,
                'item_name': item_name,
                'yes': yes_count,
                'no': no_count,
                'total': total,
                'yes_percentage': round(yes_percentage, 2),
                'passed': yes_percentage >= pass_percentage
            }

        return results

    @staticmethod
    def export_voting_report(results: Dict, output_path: str = "exports/voting_report.json") -> bool:
        """導出投票結果報告"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"報告導出錯誤: {e}")
            return False
