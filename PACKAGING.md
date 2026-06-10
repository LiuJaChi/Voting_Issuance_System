# 📦 打包說明文件

本文件說明如何將投票發行系統打包成單一 `.exe` 可執行檔，  
讓系統能在**沒有安裝 Python** 的 Windows 機器上直接執行。

---

## 🛠 環境需求

| 項目 | 需求 |
|------|------|
| 作業系統 | Windows 10 / 11（64 位元）|
| Python | 3.8 以上版本 |
| pip | 最新版本 |

---

## 🚀 快速打包（三步驟）

### 方法一：使用批次腳本（Windows，最簡單）

```bat
build_exe.bat
```

雙擊或在命令提示字元中執行，腳本會自動完成所有步驟。

### 方法二：使用 Python 腳本（跨平台）

```bash
python build_exe.py
```

---

## 📋 手動打包步驟

如需手動執行，請依序執行以下命令（在專案根目錄）：

```bash
# 1. 安裝所有依賴（含 PyInstaller）
pip install -r requirements.txt

# 2. 清理舊的打包結果（可選）
rmdir /s /q dist build

# 3. 執行打包
pyinstaller Voting_Issuance_System.spec
```

---

## 📁 打包後的檔案結構

```
Voting_Issuance_System/
├── dist/
│   └── Voting_Issuance_System.exe   ← 最終可執行檔
├── build/                            ← 中間編譯檔案（可刪除）
├── Voting_Issuance_System.spec       ← PyInstaller 設定檔
├── build_exe.bat                     ← Windows 打包腳本
└── build_exe.py                      ← Python 打包腳本
```

---

## ✅ 打包內容說明

`.spec` 設定檔已配置為包含以下所有依賴：

| 類別 | 包含項目 |
|------|---------|
| GUI 框架 | PyQt6（含所有子模組）|
| 條碼生成 | python-barcode（Code128 等）|
| 圖片處理 | Pillow / PIL |
| 資料庫 | SQLite3（Python 內建）|
| 資料處理 | pandas、SQLAlchemy、pydantic |
| 本地模組 | src/backend、src/models、src/ui |

---

## ▶ 執行打包後的 exe

打包完成後，`dist/Voting_Issuance_System.exe` 可直接複製到目標機器執行：

```
dist\Voting_Issuance_System.exe
```

- ✅ 無需安裝 Python
- ✅ 無需安裝任何第三方套件
- ✅ 支援 SQLite 資料庫操作
- ✅ 支援 JSON 檔案讀寫
- ✅ 支援條碼生成功能

> **注意**：首次啟動可能需要數秒解壓縮，屬正常現象。

---

## 🔧 常見問題排解

### Q: 打包失敗，提示找不到模組

確認已在**專案根目錄**執行打包腳本，且 `src/main.py` 存在。

### Q: exe 執行時出現錯誤視窗

暫時修改 `.spec` 檔案中的 `console=False` 為 `console=True`，  
重新打包後執行可看到詳細錯誤訊息。

### Q: 如何縮小 exe 檔案大小

在 `.spec` 的 `excludes` 清單中加入不需要的套件名稱，再重新打包。

### Q: 如何更換應用程式圖示

準備 `.ico` 圖示檔案，修改 `.spec` 檔案中的 `icon=None` 為：

```python
icon='path/to/icon.ico'
```

---

## 📞 技術支援

如遇到問題，請至 GitHub Issues 回報：  
https://github.com/LiuJaChi/Voting_Issuance_System/issues
