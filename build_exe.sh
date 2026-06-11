#!/bin/bash
# 投票系統打包脚本 - macOS/Linux

echo "========================================"
echo "投票系統 EXE 打包脚本"
echo "========================================"

# 检查 PyInstaller 是否安装
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[错误] PyInstaller 未安装"
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 检查所有依赖
echo ""
echo "[1/5] 检查依赖..."
pip3 install PyQt6 barcode pillow pydantic reportlab pyinstaller

# 清除旧构建
echo ""
echo "[2/5] 清除旧构建文件..."
rm -rf build
rm -rf dist
echo "已删除构建文件夹"

# 清除 Python 缓存
echo ""
echo "[3/5] 清除 Python 缓存..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "已清除缓存"

# 打包
echo ""
echo "[4/5] 开始打包 EXE (这可能需要几分钟)..."
pyinstaller Voting_Issuance_System.spec

# 检查是否打包成功
if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 打包失败！"
    exit 1
fi

echo ""
echo "[5/5] 打包完成！"
echo ""
echo "========================================"
echo "生成的文件位置:"
echo "dist/Voting_Issuance_System/Voting_Issuance_System.exe"
echo "========================================"
