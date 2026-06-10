@echo off
REM 下載投票系統項目
REM 此腳本會將項目克隆到 D:\Voting_Issuance_System

cd D:\

if exist Voting_Issuance_System (
    echo 目錄已存在，正在更新...
    cd Voting_Issuance_System
    git pull origin main
) else (
    echo 克隆項目...
    git clone https://github.com/LiuJaChi/Voting_Issuance_System.git
    cd Voting_Issuance_System
)

echo.
echo ====================================
echo 項目已下載到: D:\Voting_Issuance_System
echo ====================================
echo.
echo 正在安裝依賴包...
pip install -r requirements.txt

echo.
echo ====================================
echo 安裝完成！
echo ====================================
echo.
echo 運行應用命令:
echo python src/main.py
echo.
pause
