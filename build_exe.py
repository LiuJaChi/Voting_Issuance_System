#!/usr/bin/env python3
"""
投票發行系統 - EXE 打包腳本 (跨平台)
支援 Windows / macOS / Linux
"""
import subprocess
import sys
import shutil
from pathlib import Path


def check_requirements() -> bool:
    """確認在專案根目錄執行，且 main.py 存在"""
    if not Path("src/main.py").exists():
        print("[錯誤] 請在專案根目錄執行此腳本！")
        return False
    return True


def install_dependencies() -> bool:
    """安裝/更新所需套件"""
    print("[1/4] 安裝/更新所需套件...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        check=False,
    )
    if result.returncode != 0:
        print("[錯誤] 套件安裝失敗！")
        return False
    return True


def clean_build() -> None:
    """清理舊的打包結果"""
    print("\n[2/4] 清理舊的打包結果...")
    for folder in ("dist", "build"):
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"  已刪除 {folder}/")


def run_pyinstaller() -> bool:
    """執行 PyInstaller 打包"""
    print("\n[3/4] 開始打包（使用 .spec 設定檔）...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "Voting_Issuance_System.spec"],
        check=False,
    )
    if result.returncode != 0:
        print("[錯誤] 打包失敗！請確認所有依賴已正確安裝。")
        return False
    return True


def verify_output() -> bool:
    """驗證輸出的 exe 檔案"""
    print("\n[4/4] 驗證輸出檔案...")
    exe_path = Path("dist") / "Voting_Issuance_System.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 48)
        print("  打包成功！")
        print(f"  輸出檔案 : {exe_path}")
        print(f"  檔案大小 : {size_mb:.1f} MB")
        print("=" * 48)
        print("\n可直接將 dist\\Voting_Issuance_System.exe")
        print("複製到目標 Windows 機器執行，無需安裝 Python。")
        return True
    else:
        print("[錯誤] 找不到輸出的 exe 檔案，打包可能失敗。")
        return False


def main() -> int:
    print("=" * 48)
    print("  投票發行系統 - EXE 打包工具")
    print("=" * 48)
    print()

    if not check_requirements():
        return 1

    if not install_dependencies():
        return 1

    clean_build()

    if not run_pyinstaller():
        return 1

    if not verify_output():
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
