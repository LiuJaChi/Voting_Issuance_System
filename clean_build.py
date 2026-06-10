#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超級清潔打包腳本 - 投票系統（完全重新構建）
用法: python clean_build.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time


def print_header(text):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step, total, text):
    """打印步驟"""
    print(f"[{step}/{total}] {text}")


def run_command(cmd, description, timeout=120, show_output=False):
    """執行命令並返回成功狀態"""
    try:
        if show_output:
            result = subprocess.run(cmd, timeout=timeout)
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        
        if result.returncode != 0:
            print(f"    ⚠️  {description} (返回碼: {result.returncode})")
            return False
        print(f"    ✅ {description}")
        return True
    except subprocess.TimeoutExpired:
        print(f"    ⏱️  {description} 超時")
        return False
    except Exception as e:
        print(f"    ℹ️  {description}: {e}")
        return True  # 不算失敗


def step1_check_python():
    """步驟 1: 檢查 Python"""
    print_step(1, 9, "檢查 Python 版本")
    version = sys.version_info
    print(f"    Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("    ❌ 需要 Python 3.8 或更高版本")
        return False
    
    print("    ✅ Python 版本符合要求\n")
    return True


def step2_nuke_everything():
    """步驟 2: 徹底清理所有緩存"""
    print_step(2, 9, "清理所有緩存和構建文件")
    
    # 本地目錄
    local_dirs = ["build", "dist", "__pycache__", ".pytest_cache", ".pyinstaller"]
    deleted_count = 0
    
    for d in local_dirs:
        path = Path(d)
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"    ✓ 刪除 {d}/")
                deleted_count += 1
            except Exception as e:
                print(f"    ⚠️  無法刪除 {d}: {e}")
    
    # 遞歸清理 .pyc
    pyc_count = 0
    for pyc in Path(".").rglob("*.pyc"):
        try:
            pyc.unlink()
            pyc_count += 1
        except:
            pass
    
    if pyc_count > 0:
        print(f"    ✓ 刪除 {pyc_count} 個 .pyc 文件")
    
    # PyInstaller 全局緩存
    if sys.platform == "win32":
        try:
            appdata = Path(os.environ.get("APPDATA", ""))
            pyinstaller_cache = appdata / "Python" / "PyInstaller"
            if pyinstaller_cache.exists():
                shutil.rmtree(pyinstaller_cache)
                print(f"    ✓ 清理 PyInstaller 全局緩存")
        except:
            pass
    
    print(f"    ✅ 清理完成 ({deleted_count} 個目錄)\n")
    return True


def step3_uninstall_conflicting():
    """步驟 3: 卸載衝突包"""
    print_step(3, 9, "卸載衝突的舊依賴")
    
    conflicting = ["reportlab", "greenlet", "pillow-simd", "pdf", "pypdf2"]
    
    for package in conflicting:
        run_command(
            [sys.executable, "-m", "pip", "uninstall", package, "-y"],
            f"卸載 {package}",
            timeout=30
        )
    
    print()
    return True


def step4_clean_pip():
    """步驟 4: 清理 pip 緩存"""
    print_step(4, 9, "清理 pip 緩存")
    
    run_command(
        [sys.executable, "-m", "pip", "cache", "purge"],
        "清理 pip 緩存",
        timeout=60
    )
    
    print()
    return True


def step5_install_pyinstaller():
    """步驟 5: 安裝 PyInstaller"""
    print_step(5, 9, "安裝 PyInstaller")
    
    # 先嘗試卸載（不強制成功）
    run_command(
        [sys.executable, "-m", "pip", "uninstall", "pyinstaller", "-y"],
        "卸載舊版 PyInstaller",
        timeout=30
    )
    
    # 安裝新版本
    if not run_command(
        [sys.executable, "-m", "pip", "install", "pyinstaller"],
        "安裝 PyInstaller",
        timeout=60
    ):
        print("    ⚠️  PyInstaller 安裝可能有問題，繼續...\n")
    
    print()
    return True


def step6_install_requirements():
    """步驟 6: 安裝項目依賴"""
    print_step(6, 9, "安裝項目依賴")
    
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "安裝 requirements.txt",
        timeout=120
    ):
        print("    ❌ 依賴安裝失敗")
        return False
    
    print()
    return True


def step7_verify_imports():
    """步驟 7: 驗證導入"""
    print_step(7, 9, "驗證關鍵模塊導入")
    
    modules_to_check = [
        'PyQt6',
        'barcode',
        'PIL',
        'pydantic',
        'sqlite3',
    ]
    
    all_ok = True
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"    ✓ {module} 可導入")
        except ImportError as e:
            print(f"    ❌ {module} 導入失敗: {e}")
            all_ok = False
    
    # 確保 reportlab 不存在
    try:
        __import__('reportlab')
        print(f"    ⚠️  reportlab 仍然存在！")
    except ImportError:
        print(f"    ✓ reportlab 已移除（正常）")
    
    if not all_ok:
        print("\n    ⚠️  某些模塊導入失敗，但繼續嘗試...\n")
        return True
    
    print("    ✅ 所有模塊驗證完成\n")
    return True


def step8_build_exe():
    """步驟 8: 構建 EXE"""
    print_step(8, 9, "構建 EXE（請稍候 2-5 分鐘）")
    print("    (此過程不會有輸出，請耐心等待)\n")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "Voting_Issuance_System.spec",
        "--distpath=dist",
        "--workpath=build",
        "--clean"
    ]
    
    try:
        result = subprocess.run(cmd, timeout=600, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ❌ 構建失敗")
            print(f"    錯誤:\n{result.stderr[:500]}")
            return False
        print(f"    ✅ 構建完成\n")
        return True
    except subprocess.TimeoutExpired:
        print(f"    ⏱️  構建超時（超過 10 分鐘）")
        return False
    except Exception as e:
        print(f"    ❌ 構建異常: {e}\n")
        return False


def step9_verify_build():
    """步驟 9: 驗證構建結果"""
    print_step(9, 9, "驗證構建結果")
    
    # 嘗試多個可能的位置
    possible_paths = [
        Path("dist/Voting_Issuance_System/Voting_Issuance_System.exe"),
        Path("dist/Voting_Issuance_System.exe"),
        Path("build/Voting_Issuance_System/Voting_Issuance_System.exe"),
    ]
    
    exe_path = None
    for path in possible_paths:
        if path.exists():
            exe_path = path
            break
    
    if exe_path:
        file_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"    ✅ EXE 生成成功！")
        print(f"    📦 位置: {exe_path.absolute()}")
        print(f"    📊 大小: {file_size:.2f} MB")
        print()
        return True
    else:
        print(f"    ❌ 在以下位置未找到 EXE 文件:")
        for path in possible_paths:
            print(f"       {path.absolute()}")
        print()
        return False


def main():
    """主函數"""
    print_header("投票系統超級清潔打包腳本")
    print("此腳本將完全清除所有舊的構建文件和緩存，然後重新構建\n")
    
    try:
        input("按 Enter 鍵開始（或 Ctrl+C 退出）...\n")
    except KeyboardInterrupt:
        print("\n❌ 用戶取消")
        return False
    
    steps = [
        ("檢查 Python", step1_check_python),
        ("清理緩存", step2_nuke_everything),
        ("卸載衝突包", step3_uninstall_conflicting),
        ("清理 pip", step4_clean_pip),
        ("安裝 PyInstaller", step5_install_pyinstaller),
        ("安裝依賴", step6_install_requirements),
        ("驗證導入", step7_verify_imports),
        ("構建 EXE", step8_build_exe),
        ("驗證結果", step9_verify_build),
    ]
    
    failed_step = None
    
    for i, (name, step_func) in enumerate(steps, 1):
        try:
            print(f"\n{'='*70}")
            if not step_func():
                failed_step = name
                break
        except KeyboardInterrupt:
            print("\n\n⚠️  用戶中斷")
            sys.exit(1)
        except Exception as e:
            print(f"\n    ❌ 異常: {e}")
            import traceback
            traceback.print_exc()
            failed_step = name
            break
    
    print("=" * 70)
    
    if failed_step:
        print_header(f"❌ 在 '{failed_step}' 步驟失敗")
        print("建議:")
        print("1. 確保有管理員權限運行此腳本")
        print("2. 檢查網絡連接是否正常")
        print("3. 試試重新運行此腳本")
        print("4. 或者手動檢查 requirements.txt 是否正確\n")
        return False
    
    print_header("✅ 所有步驟完成！")
    
    # 尋找 EXE
    exe_path = None
    possible_paths = [
        Path("dist/Voting_Issuance_System/Voting_Issuance_System.exe"),
        Path("dist/Voting_Issuance_System.exe"),
    ]
    
    for path in possible_paths:
        if path.exists():
            exe_path = path
            break
    
    if exe_path:
        print(f"📍 EXE 文件已生成:")
        print(f"   {exe_path.absolute()}\n")
        print("🚀 使用方法:")
        print("1. 雙擊 EXE 文件運行程序")
        print("2. 或在命令行執行")
        print(f"   {exe_path}\n")
        print("📝 分發:")
        print("   複製 dist 文件夾發送給用戶")
        print("   用戶無需安裝 Python 環境\n")
    else:
        print("⚠️  EXE 文件未找到")
        print("請檢查 dist/ 目錄\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
