#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包源代碼到 D 盤腳本
用法: python package_to_d_drive.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def print_header(text):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step, total, text):
    """打印步驟"""
    print(f"[{step}/{total}] {text}")


def main():
    """主函數"""
    print_header("投票系統 - 打包源代碼到 D 盤")
    
    # 檢查 D 盤
    d_drive = Path("D:/")
    if not d_drive.exists():
        print("❌ D 盤不存在")
        print("請插入 U 盤或檢查 D 盤是否可用\n")
        return False
    
    print(f"✓ D 盤已檢測到: {d_drive}\n")
    
    # 生成時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"Voting_Issuance_System_{timestamp}"
    package_dir = d_drive / package_name
    
    print(f"📦 打包目錄: {package_dir}\n")
    
    # 步驟 1: 清理舊文件
    print_step(1, 5, "清理舊的構建文件")
    
    dirs_to_clean = ["build", "dist", "__pycache__", ".pytest_cache"]
    for d in dirs_to_clean:
        path = Path(d)
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"    ✓ 刪除 {d}/")
            except:
                pass
    
    print()
    
    # 步驟 2: 創建打包目錄
    print_step(2, 5, "創建打包目錄")
    
    try:
        package_dir.mkdir(parents=True, exist_ok=True)
        print(f"    ✓ 目錄已創建: {package_dir}\n")
    except Exception as e:
        print(f"    ❌ 創建目錄失敗: {e}\n")
        return False
    
    # 步驟 3: 複製源代碼
    print_step(3, 5, "複製源代碼和配置文件")
    
    # 需要複製的目錄
    dirs_to_copy = {
        "src": package_dir / "src",
        "data": package_dir / "data",
    }
    
    # 需要複製的文件
    files_to_copy = [
        "main.py",
        "requirements.txt",
        "Voting_Issuance_System.spec",
        "clean_build.py",
        "README.md",
        ".gitignore",
    ]
    
    # 複製目錄
    for src, dst in dirs_to_copy.items():
        src_path = Path(src)
        if src_path.exists():
            try:
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src_path, dst)
                print(f"    ✓ 複製目錄: {src}/")
            except Exception as e:
                print(f"    ⚠️  複製 {src}/ 失敗: {e}")
    
    # 複製文件
    for file in files_to_copy:
        src_file = Path(file)
        if src_file.exists():
            try:
                dst_file = package_dir / file
                shutil.copy2(src_file, dst_file)
                print(f"    ✓ 複製文件: {file}")
            except Exception as e:
                print(f"    ⚠️  複製 {file} 失敗: {e}")
    
    print()
    
    # 步驟 4: 計算大小
    print_step(4, 5, "計算打包大小")
    
    total_size = 0
    file_count = 0
    
    for item in package_dir.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
    
    size_mb = total_size / (1024 * 1024)
    print(f"    ✓ 文件數量: {file_count} 個")
    print(f"    ✓ 總大小: {size_mb:.2f} MB\n")
    
    # 步驟 5: 創建 README
    print_step(5, 5, "創建説明文檔")
    
    readme_content = f"""# 投票系統 - 源代碼包
    
## 📦 包信息

- **打包時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **版本**: main branch (2026-06-10)
- **文件數量**: {file_count}
- **包大小**: {size_mb:.2f} MB

## 📂 目錄結構

```
Voting_Issuance_System/
├── src/                           # 源代碼
│   ├── backend/                   # 後端模塊
│   │   ├── database.py            # 數據庫管理 (households 表)
│   │   ├── config_manager.py      # 配置管理
│   │   └── ...
│   ├── models/                    # 數據模型
│   └── ui/                        # UI 界面
├── data/                          # 數據存儲目錄
├── main.py                        # 主程序入口
├── requirements.txt               # 依賴列表
├── Voting_Issuance_System.spec   # PyInstaller 配置
├── clean_build.py                 # 清潔打包腳本
└── README.md                      # 文檔
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 直接運行

```bash
python src/main.py
```

### 3. 打包為 EXE

```bash
python clean_build.py
```

## 📋 功能特性

✅ **住戶管理**
- 戶號管理（以戶號為主鍵）
- 批量導入住戶
- 住戶資料查詢

✅ **報到管理**
- 條碼掃描報到
- 報到統計
- 報到歷史紀錄

✅ **投票管理**
- 案號管理（以案號為唯一標識）
- 投票紀錄（戶號+案號複合主鍵）
- 投票結果統計

✅ **數據管理**
- 數據導出 (JSON)
- 數據清空
- 備份恢復

## 🗄️ 數據庫架構

### households 表
- `household_id` (TEXT PRIMARY KEY) - 戶號
- `name` (TEXT) - 住戶名稱
- `status` (TEXT) - 狀態 (pending/checked_in/voted)
- `created_at` (TIMESTAMP) - 創建時間

### voting_items 表
- `id` (INTEGER PRIMARY KEY) - 內部 ID
- `case_number` (TEXT UNIQUE) - 案號
- `name` (TEXT) - 項目名稱
- `description` (TEXT) - 項目描述
- `created_at` (TIMESTAMP) - 創建時間

### votes 表
- `household_id` (TEXT) - 戶號
- `case_number` (TEXT) - 案號
- `vote` (TEXT) - 投票結果
- `voted_at` (TIMESTAMP) - 投票時間
- PRIMARY KEY: (household_id, case_number)

### check_in_records 表
- `household_id` (TEXT PRIMARY KEY) - 戶號
- `checked_in_at` (TIMESTAMP) - 報到時間
- `device_id` (TEXT) - 設備 ID

## 🔧 系統要求

- Python 3.8+
- Windows / macOS / Linux
- 3GB 硬盤空間（含虛擬環境）

## 📞 支持

如有問題，請聯繫開發人員

---

**打包日期**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    try:
        readme_file = package_dir / "PACKAGE_INFO.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"    ✓ 創建說明文檔: PACKAGE_INFO.md\n")
    except Exception as e:
        print(f"    ⚠️  創建說明文檔失敗: {e}\n")
    
    print_header("✅ 打包完成！")
    
    print(f"📦 打包位置:")
    print(f"   {package_dir}\n")
    print(f"📊 打包統計:")
    print(f"   - 文件數量: {file_count}")
    print(f"   - 總大小: {size_mb:.2f} MB\n")
    print(f"📋 包含文件:")
    print(f"   ✓ 完整源代碼 (src/)")
    print(f"   ✓ 依賴列表 (requirements.txt)")
    print(f"   ✓ PyInstaller 配置 (.spec)")
    print(f"   ✓ 打包腳本 (clean_build.py)")
    print(f"   ✓ 說明文檔 (PACKAGE_INFO.md)\n")
    
    print(f"🚀 下一步:")
    print(f"1. 打開 D 盤: {d_drive}")
    print(f"2. 進入文件夾: {package_name}")
    print(f"3. 閱讀 PACKAGE_INFO.md 瞭解詳情\n")
    
    # 打開資源管理器
    try:
        if sys.platform == "win32":
            os.startfile(str(package_dir))
            print(f"✓ 已打開資源管理器\n")
    except:
        pass
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
