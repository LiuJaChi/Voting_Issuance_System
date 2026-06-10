# 投票系統 EXE 打包指南

## 📦 打包配置文件說明

本項目包含完整的 PyInstaller 打包配置，可以將投票系統打包成獨立的 Windows EXE 執行檔。

---

## 📋 快速開始

### 方式 1：使用 BAT 腳本（推薦 Windows 用戶）

1. **打開命令提示符或 PowerShell**
   ```
   cd D:\Voting_Issuance_System
   ```

2. **雙擊或運行打包腳本**
   ```
   build_exe.bat
   ```

3. **等待打包完成**
   - 腳本會自動檢查依賴、安裝 PyInstaller、清理舊文件、打包程序
   - 完成後會顯示 EXE 文件的位置

### 方式 2：使用 Python 腳本（跨平台）

1. **打開命令行**
   ```
   cd D:\Voting_Issuance_System
   ```

2. **運行 Python 打包腳本**
   ```
   python build_exe.py
   ```

3. **等待打包完成**

### 方式 3：手動使用 PyInstaller

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 使用 spec 配置文件打包
pyinstaller Voting_Issuance_System.spec --distpath=dist --workpath=build

# 3. EXE 文件將生成在 dist\ 目錄下
```

---

## 📂 生成的文件結構

```
Voting_Issuance_System/
├── dist/
│   ├── Voting_Issuance_System.exe      ← 主程序（可直接執行）
│   ├── _internal/                      ← 內部依賴文件
│   └── ...
├── build/
│   └── ...                             ← 中間構建文件（可刪除）
├── Voting_Issuance_System.spec         ← PyInstaller 配置
├── build_exe.bat                       ← Windows 打包腳本
├── build_exe.py                        ← Python 打包腳本
└── ...
```

---

## 🚀 使用 EXE 檔

### 方式 1：直接執行
```
雙擊 dist/Voting_Issuance_System.exe
```

### 方式 2：命令行執行
```
D:\Voting_Issuance_System\dist\Voting_Issuance_System.exe
```

### 方式 3：快捷方式
- 右鍵點擊 EXE 文件 → 創建快捷方式
- 可以放在桌面或開始菜單

---

## 📤 分發 EXE

### 給單個用戶
1. 只需發送 `dist/Voting_Issuance_System.exe`
2. 用戶無需安裝 Python 環境即可直接運行

### 部署到組織
1. 將 `dist/` 目錄全部複製到目標位置
2. 創建快捷方式供用戶使用
3. 或使用網絡共享

### 製作安裝程序（可選）
可以使用 NSIS 或 Inno Setup 將 EXE 包裝成安裝程序

---

## 🔧 打包配置文件說明

### Voting_Issuance_System.spec

此文件是 PyInstaller 的配置文件，定義了：

- **入口文件**: `src/main.py`
- **數據文件**: 包含所有必要的模塊和配置文件
- **隱藏導入**: PyQt6、barcode、PIL 等庫
- **輸出選項**: 生成在 `dist/` 目錄

**主要配置項**:
```python
# 數據文件
datas=[
    ('src/backend', 'src/backend'),
    ('src/models', 'src/models'),
    ('src/ui', 'src/ui'),
    ('config', 'config'),
    ('data', 'data'),
    ('exports', 'exports'),
],

# 隱藏導入（確保依賴被包含）
hiddenimports=[
    'PyQt6',
    'barcode',
    'PIL',
    'pydantic',
    ...
],
```

---

## ⚙️ 自訂打包選項

### 修改 EXE 圖標
在 `Voting_Issuance_System.spec` 中找到 `EXE()` 部分，添加：

```python
exe = EXE(
    ...
    icon='path/to/your/icon.ico',  # 添加此行
    ...
)
```

### 生成單一 EXE 文件
如果希望生成單一的 EXE（不需要 `_internal/` 文件夾），修改 spec 文件：

```python
exe = EXE(
    ...
    onefile=True,  # 生成單一 EXE
    ...
)
```

**注意**: 單一 EXE 文件會更大，但分發更簡單。

### 添加版本信息
創建 `version_info.txt`:

```
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx?id=7
VSVersionInfo(
  ffi=FixedFileInfo(
    # mask=0x3f,
    # contains: VFT_DLL | VFT_STATIC_LIB
    mask=0x3f,
    # contains: VFT_UNKNOWN
    # Contains: VFT_APP
    mask=0x0,
    VS_FF_DEBUG=0x0,
    VS_FF_PRERELEASE=0x0),
  kids=[StringFileInfo(
      [StringTable(
        u'040904B0',
        [StringData(u'CompanyName', u'Your Company'),
        StringData(u'FileDescription', u'投票系統'),
        StringData(u'FileVersion', u'1.0.0.0'),
        StringData(u'InternalName', u'Voting_Issuance_System'),
        StringData(u'LegalCopyright', u'Copyright (C) 2024'),
        StringData(u'OriginalFilename', u'Voting_Issuance_System.exe'),
        StringData(u'ProductName', u'投票系統'),
        StringData(u'ProductVersion', u'1.0.0')])]),
      VarFileInfo([VarFileInfo(u'Translation', [1033, 1200])])])
```

然後在 spec 文件中：
```python
exe = EXE(
    ...
    version_file='version_info.txt',
    ...
)
```

---

## 📊 打包文件大小

| 打包模式 | 文件大小 |
|--------|--------|
| 目錄模式 | ~150-200 MB（包含所有依賴） |
| 單一 EXE | ~180-220 MB（一個文件） |

---

## 🐛 常見問題

### Q1: 打包失敗，提示缺少模塊？
**A**: 檢查 `Voting_Issuance_System.spec` 中的 `hiddenimports` 是否包含缺少的模塊。

### Q2: EXE 啟動很慢？
**A**: 這是正常的，第一次啟動會解包依賴到臨時目錄。後續啟動會快很多。

### Q3: 如何在沒有打包腳本的情況下重新打包？
**A**: 直接使用 PyInstaller 命令：
```bash
pyinstaller Voting_Issuance_System.spec --distpath=dist --workpath=build
```

### Q4: 用戶電腦上 EXE 無法運行？
**A**: 檢查用戶是否使用 Windows 7 或更高版本，並且有足夠的磁盤空間。

### Q5: 如何更新已分發的 EXE？
**A**: 修改源代碼後重新打包，然後分發新的 EXE 文件。

---

## 📝 打包流程總結

```
1. 克隆或下載項目
   ↓
2. 安裝 Python 3.8+
   ↓
3. 運行打包腳本 (build_exe.bat 或 build_exe.py)
   ↓
4. 自動檢查依賴和安裝
   ↓
5. 使用 PyInstaller 打包程序
   ↓
6. 生成 dist/Voting_Issuance_System.exe
   ↓
7. 測試 EXE 是否能正常運行
   ↓
8. 分發 EXE 給用戶
```

---

## 🔗 相關資源

- [PyInstaller 官方文檔](https://pyinstaller.readthedocs.io/)
- [PyQt6 文檔](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python 官方下載](https://www.python.org/downloads/)

---

## 📞 技術支持

如有問題，請檢查：
1. Python 版本 >= 3.8
2. 所有依賴已正確安裝
3. 項目路徑不包含中文字符（可選但推薦）
4. 磁盤空間充足（至少 500 MB 用於打包）

---

**最後更新**: 2026-06-10
