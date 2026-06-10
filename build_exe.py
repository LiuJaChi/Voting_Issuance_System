#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 自動打包腳本 - 投票系統（Python 版本）
用法: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text):
    """打印標題"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_python():
    """檢查 Python 版本"""
    print("[1/8] 檢查 Python 版本...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 錯誤: 需要 Python 3.8 或更高版本")
        return False
    print("✅ Python 版本符合要求\n")
    return True


def uninstall_conflicting_packages():
    """卸載衝突的包"""
    print("[2/8] 卸載衝突的舊依賴...")
    conflicting_packages = ['reportlab', 'greenlet', 'pillow-simd']
    
    for package in conflicting_packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", package, "-y"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and "Successfully uninstalled" in result.stdout:
                print(f"  ✓ {package} 已卸載")
            elif "not installed" not in result.stdout:
                print(f"  ℹ️ {package} 不存在或已卸載")
        except Exception as e:
            print(f"  ⚠️  {package}: {e}")
    
    print("✅ 衝突包檢查完成\n")


def cleanup_pip_cache():
    """清理 pip 緩存"""
    print("[3/8] 清理 pip 緩存...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "cache", "purge"],
            capture_output=True,
            timeout=30
        )
        print("✅ pip 緩存已清理\n")
    except Exception as e:
        print(f"⚠️  緩存清理失敗: {e}\n")


def install_pyinstaller():
    """安裝 PyInstaller"""
    print("[4/8] 檢查並安裝 PyInstaller...")
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安裝 (版本: {PyInstaller.__version__})\n")
    except ImportError:
        print("⚠️  PyInstaller 未安裝，正在安裝...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"❌ 安裝失敗: {result.stderr}")
            return False
        print("✅ PyInstaller 安裝成功\n")
    return True


def install_requirements():
    """安裝項目依賴"""
    print("[5/8] 安裝項目依賴...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode != 0:
        print(f"❌ 依賴安裝失敗: {result.stderr}")
        return False
    print("✅ 依賴安裝成功\n")
    return True


def cleanup_old_builds():
    """清理舊的構建文件"""
    print("[6/8] 清理舊的構建文件...")
    dirs_to_remove = ["build", "dist", "__pycache__", ".pytest_cache", ".pyinstaller"]
    
    for dir_name in dirs_to_remove:
        if Path(dir_name).exists():
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ 刪除 {dir_name}/")
            except Exception as e:
                print(f"  ⚠️  無法刪除 {dir_name}/: {e}")
    
    # 遞歸刪除所有 .pyc 文件
    pyc_count = 0
    for pyc_file in Path(".").rglob("*.pyc"):
        try:
            pyc_file.unlink()
            pyc_count += 1
        except:
            pass
    
    if pyc_count > 0:
        print(f"  ✓ 刪除 {pyc_count} 個 .pyc 文件")
    
    print("✅ 清理完成\n")


def build_exe():
    """使用 PyInstaller 構建 EXE"""
    print("[7/8] 開始打包程序...")
    print("這可能需要 2-5 分鐘...\n")
    
    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "Voting_Issuance_System.spec",
            "--distpath=dist",
            "--workpath=build",
            "--clean"
        ],
        capture_output=False,
        text=True,
        timeout=600
    )
    
    if result.returncode != 0:
        print(f"\n❌ 打包失敗!")
        return False
    
    print("✅ 打包完成\n")
    return True


def verify_build():
    """驗證構建結果"""
    print("[8/8] 驗證打包結果...\n")
    
    exe_path = Path("dist/Voting_Issuance_System.exe")
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # 轉換為 MB
        print("✅ 打包成功！")
        print("\n" + "=" * 60)
        print("📦 構建完成")
        print("=" * 60)
        print(f"EXE 文件位置: {exe_path.absolute()}")
        print(f"EXE 大小: {file_size:.2f} MB")
        print("\n💡 使用方法:")
        print("1. 雙擊 dist/Voting_Issuance_System.exe 運行程序")
        print("2. 或在命令行執行: dist\\Voting_Issuance_System.exe")
        print("\n📝 分發方法:")
        print("只需將 dist/Voting_Issuance_System.exe 發送給用戶")
        print("用戶無需安裝 Python 環境即可運行")
        print("=" * 60 + "\n")
        return True
    else:
        print("❌ EXE 文件生成失敗!")
        print("請檢查上面的錯誤信息")
        return False


def main():
    """主函數"""
    print_header("投票系統 EXE 打包程序 - 完整清潔修復")
    
    try:
        if not check_python():
            return False
        
        uninstall_conflicting_packages()
        cleanup_pip_cache()
        
        if not install_pyinstaller():
            return False
        
        if not install_requirements():
            return False
        
        cleanup_old_builds()
        
        if not build_exe():
            return False
        
        if not verify_build():
            return False
        
        print("🎉 所有步驟完成！準備好了嗎？\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
