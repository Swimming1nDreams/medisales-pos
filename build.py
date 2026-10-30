import os
import sys
import subprocess
from pathlib import Path

def build():
    print("=== Building Medisales Windows Desktop App ===")
    root_dir = Path(__file__).resolve().parent
    
    # 1. Compile Tailwind CSS
    print("\n[Step 1/2] Compiling Tailwind CSS bundle...")
    ui_web_dir = root_dir / "src" / "ui_web"
    res = subprocess.run(
        ["npx", "tailwindcss", "-i", "./input.css", "-o", "./output.css", "--minify"],
        cwd=str(ui_web_dir),
        shell=True,
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        print(f"Warning: Tailwind CSS compile returned code {res.returncode}:\n{res.stderr}")
    else:
        print("Tailwind CSS compilation complete.")

    # 2. Run PyInstaller
    print("\n[Step 2/2] Running PyInstaller build...")
    pyinstaller_bin = root_dir / "venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_bin.exists():
        pyinstaller_bin = "pyinstaller"

    res = subprocess.run(
        [str(pyinstaller_bin), "--noconfirm", "medisales.spec"],
        cwd=str(root_dir)
    )
    if res.returncode != 0:
        print(f"Error: PyInstaller build failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    dist_exe = root_dir / "dist" / "Medisales" / "Medisales.exe"
    print("\n==============================================")
    print("Build Succeeded!")
    print(f"Packaged executable located at: {dist_exe}")
    print("==============================================")

if __name__ == "__main__":
    build()
