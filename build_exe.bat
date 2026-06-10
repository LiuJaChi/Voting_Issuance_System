@echo off
REM PyInstaller 自動打包腳本 - 投票系統
REM 此腳本會自動將投票系統打包成 EXE 檔

echo.
echo =====================================
echo 投票系統 EXE 打包程序
echo =====================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 錯誤: 未檢測到 Python
    echo 請先安裝 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo [1/5] 檢查 PyInstaller...
pip list | findstr PyInstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PyInstaller 未安裝，正在安裝...
    pip install pyinstaller
)

echo.
echo [2/5] 安裝項目依賴...
pip install -r requirements.txt

echo.
echo [3/5] 清理舊的構建文件...
if exist "build\" (
    rmdir /s /q build
)
if exist "dist\" (
    rmdir /s /q dist
)
if exist "__pycache__\" (
    rmdir /s /q __pycache__
)

echo.
echo [4/5] 開始打包程序...
pyinstaller Voting_Issuance_System.spec --distpath=dist --workpath=build

if %errorlevel% neq 0 (
    echo.
    echo 錯誤: 打包失敗！
    pause
    exit /b 1
)

echo.
echo [5/5] 驗證打包結果...
if exist "dist\Voting_Issuance_System.exe" (
    echo.
    echo =====================================
    echo 打包成功！
    echo =====================================
    echo.
    echo EXE 文件位置: dist\Voting_Issuance_System.exe
    echo.
    dir dist\Voting_Issuance_System.exe
    echo.
    echo 你可以直接雙擊 EXE 文件運行程序
    echo.
    pause
) else (
    echo.
    echo 錯誤: EXE 文件生成失敗！
    echo 請檢查上面的錯誤信息
    pause
    exit /b 1
)
