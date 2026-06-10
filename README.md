# 投票系統 (Voting Issuance System)

一個功能完整的桌面應用，用於管理報到、投票、開票的整個流程。系統支持離線運作、多設備使用，並可自動生成 Code128 條碼。

## 功能特性

### 🎯 核心功能
- **系統配置**：自定義系統名稱、參與人數、投票通過百分比
- **條碼生成**：自動生成 Code128 條碼供掃碼使用
- **報到管理**：掃碼快速報到，實時統計出席人數
- **投票功能**：掃碼投票（支持多個投票項目）
- **離線運作**：完全離線支持，不依賴網絡連接
- **多設備支持**：支持多台設備並行使用
- **數據導出**：導出投票數據、出席記錄
- **數據合併**：支持多設備數據合併計票
- **實時儀表板**：投票結果、出席率實時統計

## 技術棧

- **GUI 框架**：PyQt6
- **後端**：Python 3.10+
- **數據庫**：SQLite
- **條碼生成**：python-barcode / pylibdmtx
- **數據處理**：Pandas

## 項目結構

```
Voting_Issuance_System/
├── src/
│   ├── main.py                  # 應用入口
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py       # 主窗口
│   │   ├── setup_dialog.py      # 系統設置對話框
│   │   ├── check_in_window.py   # 報到窗口
│   │   ├── voting_window.py     # 投票窗口
│   │   ├── results_window.py    # 結果窗口
│   │   └── resources/
│   │       └── style.qss        # 樣式表
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite 數據庫操作
│   │   ├── barcode_generator.py # Code128 條碼生成
│   │   ├── data_merger.py       # 數據合併
│   │   ├── config_manager.py    # 配置管理
│   │   └── utils.py             # 工具函數
│   └── models/
│       ├── __init__.py
│       ├── config.py            # 配置模型
│       ├── voter.py             # 投票者模型
│       └── vote.py              # 投票紀錄模型
├── data/
│   └── .gitkeep                 # 數據目錄
├── exports/
│   └── .gitkeep                 # 導出文件目錄
├── requirements.txt
├── .gitignore
└── README.md
```

## 快速開始

### 環境要求
- Python 3.10+
- Windows / macOS / Linux

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 運行應用

```bash
python src/main.py
```

### 打包成可執行文件

```bash
pyinstaller --onefile --windowed src/main.py
```

## 使用流程

### 1. 系統初始化
- 設置系統名稱
- 配置預期出席人數
- 設置投票項目和通過百分比
- 生成參與者編號和條碼

### 2. 生成條碼
- 系統自動為每個參與者生成唯一的 Code128 條碼
- 可導出條碼進行打印

### 3. 報到流程
- 參與者掃描條碼報到
- 系統記錄報到時間和出席狀態
- 實時顯示出席人數和出席率

### 4. 投票流程
- 參與者掃描條碼進行投票
- 支持多投票項目配置
- 實時統計投票結果
- 顯示各項通過情況

### 5. 數據合併與計票
- 多設備投票數據導出為 JSON/CSV 文件
- 合併多個設備的數據
- 自動去重和衝突處理
- 生成最終計票結果報告

## 數據格式

### 出席記錄導出 (CSV/JSON)
```json
{
  "systemName": "2024年度大會",
  "totalExpected": 100,
  "checkInRecords": [
    {
      "id": 1,
      "barcode": "2024001",
      "name": "用戶1",
      "checkInTime": "2024-06-10 10:30:15",
      "status": "已簽到"
    }
  ]
}
```

### 投票數據導出 (CSV/JSON)
```json
{
  "systemName": "2024年度大會",
  "votingItems": ["提案A", "提案B"],
  "passPercentage": 66.7,
  "votes": [
    {
      "voterId": 1,
      "barcode": "2024001",
      "votes": ["提案A", "提案B"],
      "timestamp": "2024-06-10 10:35:20"
    }
  ],
  "results": {
    "提案A": {
      "yes": 70,
      "no": 30,
      "percentage": 70.0,
      "passed": true
    }
  }
}
```

## 主要功能模塊

### 數據庫管理 (database.py)
- SQLite 數據庫初始化
- 投票紀錄存儲
- 出席紀錄存儲
- 配置信息存儲

### 條碼生成 (barcode_generator.py)
- Code128 條碼自動生成
- 批量生成條碼圖片
- 條碼與參與者綁定

### 數據合併 (data_merger.py)
- 導入多個設備的數據文件
- 自動去重和檢測衝突
- 合併計票結果

### UI 界面
- 直觀的操作流程
- 實時數據顯示
- 掃碼條形框輸入
- 統計圖表和報告

## 許可證

MIT

## 聯繫方式

如有任何問題或建議，歡迎提交 Issue 或 Pull Request。
