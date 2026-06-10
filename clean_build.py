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
import tempfile


def print_header(text):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step, total, text):
    """打印步驟"""
    print(f"[{step}/{total}] {text}")


def run_command(cmd, description, timeout=120):
    """執行命令並返回成功狀態"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            print(f"    ❌ {description} 失敗")
            if result.stderr:
                print(f"    錯誤: {result.stderr[:200]}")
            return False
        print(f"    ✅ {description} 成功")
        return True
    except subprocess.TimeoutExpired:
        print(f"    ⏱️  {description} 超時")
        return False
    except Exception as e:
        print(f"    ⚠️  {description} 異常: {e}")
        return False


def step1_check_python():
    """步驟 1: 檢查 Python"""
    print_step(1, 10, "檢查 Python 版本")
    version = sys.version_info
    print(f"    Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("    ❌ 需要 Python 3.8 或更高版本")
        return False
    
    print("    ✅ Python 版本符合要求\n")
    return True


def step2_kill_processes():
    """步驟 2: 殺死 Python 進程"""
    print_step(2, 10, "停止 Python 進程")
    
    # Windows 特定
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True,
                timeout=5
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "pythonw.exe"],
                capture_output=True,
                timeout=5
            )
            print("    ✅ 已終止 Python 進程\n")
        except:
            print("    ℹ️  無法終止進程（可能已結束）\n")
    else:
        print("    ℹ️  非 Windows 系統，跳過\n")
    
    return True


def step3_nuke_everything():
    """步驟 3: 徹底清理所有緩存"""
    print_step(3, 10, "徹底清理所有緩存和構建文件")
    
    # 本地目錄
    local_dirs = ["build", "dist", "__pycache__", ".pytest_cache", ".pyinstaller"]
    for d in local_dirs:
        path = Path(d)
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"    ✓ 刪除 {d}/")
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
        appdata = Path(os.environ.get("APPDATA", ""))
        pyinstaller_cache = appdata / "Python" / "PyInstaller"
        if pyinstaller_cache.exists():
            try:
                shutil.rmtree(pyinstaller_cache)
                print(f"    ✓ 清理 PyInstaller 全局緩存")
            except:
                pass
    
    print("    ✅ 清理完成\n")
    return True


def step4_uninstall_conflicting():
    """步驟 4: 卸載衝突包"""
    print_step(4, 10, "卸載衝突的舊依賴")
    
    conflicting = ["reportlab", "greenlet", "pillow-simd", "pdf", "pypdf2"]
    
    for package in conflicting:
        run_command(
            [sys.executable, "-m", "pip", "uninstall", package, "-y"],
            f"卸載 {package}",
            timeout=30
        )
    
    print()
    return True


def step5_clean_pip():
    """步驟 5: 清理 pip 緩存"""
    print_step(5, 10, "清理 pip 緩存")
    
    run_command(
        [sys.executable, "-m", "pip", "cache", "purge"],
        "清理 pip 緩存",
        timeout=60
    )
    
    print()
    return True


def step6_install_pyinstaller():
    """步驟 6: 重新安裝 PyInstaller"""
    print_step(6, 10, "重新安裝 PyInstaller")
    
    # 先卸載
    run_command(
        [sys.executable, "-m", "pip", "uninstall", "pyinstaller", "-y"],
        "卸載舊版 PyInstaller",
        timeout=30
    )
    
    # 再安裝
    if not run_command(
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "pyinstaller"],
        "安裝新版 PyInstaller",
        timeout=60
    ):
        return False
    
    print()
    return True


def step7_install_requirements():
    """步驟 7: 安裝項目依賴"""
    print_step(7, 10, "安裝項目依賴")
    
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "安裝 requirements.txt",
        timeout=120
    ):
        return False
    
    print()
    return True


def step8_verify_imports():
    """步驟 8: 驗證導入"""
    print_step(8, 10, "驗證關鍵模塊導入")
    
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
        except ImportError:
            print(f"    ❌ {module} 導入失敗")
            all_ok = False
    
    # 確保 reportlab 不存在
    try:
        __import__('reportlab')
        print(f"    ❌ ⚠️  reportlab 仍然存在！")
        all_ok = False
    except ImportError:
        print(f"    ✓ reportlab 已移除（正常）")
    
    if not all_ok:
        print("\n    ❌ 某些模塊導入失敗")
        return False
    
    print("    ✅ 所有模塊驗證完成\n")
    return True


def step9_build_exe():
    """步驟 9: 構建 EXE"""
    print_step(9, 10, "構建 EXE（請稍候 2-5 分鐘）")
    print()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "Voting_Issuance_System.spec",
        "--distpath=dist",
        "--workpath=build",
        "--clean",
        "--onedir"
    ]
    
    try:
        result = subprocess.run(cmd, timeout=600)
        if result.returncode != 0:
            print(f"\n    ❌ 構建失敗")
            return False
        print(f"\n    ✅ 構建完成\n")
        return True
    except subprocess.TimeoutExpired:
        print(f"\n    ⏱️  構建超時")
        return False
    except Exception as e:
        print(f"\n    ❌ 構建異常: {e}\n")
        return False


def step10_verify_build():
    """步驟 10: 驗證構建結果"""
    print_step(10, 10, "驗證構建結果")
    
    exe_path = Path("dist/Voting_Issuance_System/Voting_Issuance_System.exe")
    
    if not exe_path.exists():
        exe_path = Path("dist/Voting_Issuance_System.exe")
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"    ✅ EXE 生成成功！")
        print(f"    📦 位置: {exe_path.absolute()}")
        print(f"    📊 大小: {file_size:.2f} MB")
        print()
        return True
    else:
        print(f"    ❌ EXE 文件不存在")
        print(f"    預期位置: {exe_path}")
        print()
        return False


def main():
    """主函數"""
    print_header("投票系統超級清潔打包腳本")
    print("警告: 此腳本將完全清除所有舊的構建文件和緩存")
    print("請確保已保存所有重要文件\n")
    
    input("按 Enter 鍵繼續...\n")
    
    steps = [
        ("檢查 Python", step1_check_python),
        ("停止進程", step2_kill_processes),
        ("清理緩存", step3_nuke_everything),
        ("卸載衝突包", step4_uninstall_conflicting),
        ("清理 pip", step5_clean_pip),
        ("安裝 PyInstaller", step6_install_pyinstaller),
        ("安裝依賴", step7_install_requirements),
        ("驗證導入", step8_verify_imports),
        ("構建 EXE", step9_build_exe),
        ("驗證結果", step10_verify_build),
    ]
    
    for i, (name, step_func) in enumerate(steps, 1):
        try:
            if not step_func():
                print_header(f"❌ 失敗：{name}")
                print("修復建議:")
                print("1. 檢查 Python 是否正確安裝")
                print("2. 確保有管理員權限")
                print("3. 檢查網絡連接")
                print("4. 試試重新運行此腳本")
                sys.exit(1)
        except Exception as e:
            print_header(f"❌ 異常：{name}")
            print(f"錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print_header("✅ 所有步驟完成！")
    print("📍 EXE 文件位置:")
    
    exe_path1 = Path("dist/Voting_Issuance_System/Voting_Issuance_System.exe")
    exe_path2 = Path("dist/Voting_Issuance_System.exe")
    
    if exe_path1.exists():
        print(f"   {exe_path1.absolute()}\n")
    elif exe_path2.exists():
        print(f"   {exe_path2.absolute()}\n")
    
    print("🚀 下一步:")
    print("1. 雙擊 EXE 文件運行程序")
    print("2. 或在命令行執行: dist\\Voting_Issuance_System.exe\n")
    
    print("📝 分發:")
    print("   將整個 dist 文件夾發送給用戶")
    print("   用戶無需安裝 Python 環境\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
