"""
配置管理模塊
"""
import json
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """系統配置管理器"""
    
    def __init__(self, config_file: str = "config/system_config.json"):
        """初始化配置管理器"""
        self.config_file = config_file
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加載配置文件"""
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"配置加載錯誤: {e}")
                return self.get_default_config()
        return self.get_default_config()
    
    def save_config(self, config: Dict) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.config = config
            return True
        except Exception as e:
            print(f"配置保存錯誤: {e}")
            return False
    
    @staticmethod
    def get_default_config() -> Dict:
        """獲取默認配置"""
        return {
            'system_name': '投票系統',
            'total_participants': 100,
            'pass_percentage': 66.7,
            'barcode_prefix': 'VOTER',
            'device_id': 'DEVICE_001',
            'theme': 'light',
            'language': 'zh_TW'
        }
    
    def update_config(self, key: str, value):
        """更新配置項"""
        self.config[key] = value
        return self.save_config(self.config)
    
    def get_config(self, key: str, default=None):
        """獲取配置項"""
        return self.config.get(key, default)
