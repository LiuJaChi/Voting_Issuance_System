@echo off
chcp 65001 >nul
title 投票系統打包工具

echo ============================================
echo   投票發行系統 - EXE 打包工具
echo ============================================
echo.

REM 確認在專案根目錄執行
if not exist "src\main.py" (
    echo [錯誤] 請在專案根目錄執行此腳本！
    echo 專案根目錄應包含 src\ 資料夾。
    pause
    exit /b 1
)

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python，請先安裝 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 安裝/更新所需套件...
pip install -r requirements.txt
if errorlevel 1 (
    echo [錯誤] 套件安裝失敗！
    pause
    exit /b 1
)

echo.
echo [2/4] 清理舊的打包結果...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo [3/4] 開始打包（使用 .spec 設定檔）...
pyinstaller Voting_Issuance_System.spec
if errorlevel 1 (
    echo [錯誤] 打包失敗！請確認所有依賴已正確安裝。
    pause
    exit /b 1
)

echo.
echo [4/4] 驗證輸出檔案...
if exist "dist\Voting_Issuance_System.exe" (
    echo.
    echo ============================================
    echo   打包成功！
    echo   輸出檔案: dist\Voting_Issuance_System.exe
    echo ============================================
    echo.
    echo 可直接將 dist\Voting_Issuance_System.exe
    echo 複製到目標 Windows 機器執行，無需安裝 Python。
) else (
    echo [錯誤] 找不到輸出的 exe 檔案，打包可能失敗。
    pause
    exit /b 1
)

echo.
pause
