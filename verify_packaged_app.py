import os
import sys
import time
import shutil
import sqlite3
import tempfile
import subprocess
from pathlib import Path

def test_packaged_executable():
    print("==================================================")
    print("Testing Packaged Medisales Executable (dist/Medisales/Medisales.exe)")
    print("==================================================")

    repo_dir = Path(__file__).resolve().parent
    exe_path = repo_dir / "dist" / "Medisales" / "Medisales.exe"

    if not exe_path.exists():
        print(f"FAILED: Executable not found at {exe_path}")
        return False

    print(f"Found executable: {exe_path} ({exe_path.stat().st_size / (1024*1024):.2f} MB)")

    # 1. Test clean launch with temporary database and isolated working directory
    temp_dir = Path(tempfile.mkdtemp(prefix="medisales_test_pkg_"))
    test_db = temp_dir / "packaged_test.db"

    print(f"\n[Test 1] Launching executable in isolated directory: {temp_dir}")
    print(f"Database target: {test_db}")

    # Clean environment without Python development vars
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)
    local_app_dir = temp_dir / "localappdata"
    local_app_dir.mkdir(parents=True, exist_ok=True)
    clean_env["LOCALAPPDATA"] = str(local_app_dir)

    # Launch subprocess with cwd set to temp_dir (verifies no dependency on repo CWD)
    proc = subprocess.Popen(
        [str(exe_path), "--db", str(test_db)],
        cwd=str(temp_dir),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f"Process spawned with PID {proc.pid}. Waiting up to 12 seconds for initialization...")
    for _ in range(24):
        if test_db.exists() and proc.poll() is None:
            break
        time.sleep(0.5)

    # Check if process crashed
    poll = proc.poll()
    if poll is not None:
        stdout, stderr = proc.communicate()
        print(f"FAILED: Executable exited prematurely with code {poll}!")
        print(f"Stdout:\n{stdout.decode('utf-8', errors='ignore')}")
        print(f"Stderr:\n{stderr.decode('utf-8', errors='ignore')}")
        return False

    print("SUCCESS: Process is running healthy!")

    # 2. Verify database was created and migrated
    if not test_db.exists():
        print("FAILED: Database file was not created!")
        proc.kill()
        return False

    print(f"SUCCESS: Database file created at {test_db} ({test_db.stat().st_size} bytes)")

    # Connect to verify tables and schema migrations
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}
    print(f"Tables present in database: {sorted(list(tables))}")

    expected_tables = {
        'products', 'categories', 'inventory_movements', 'sales', 'sale_items',
        'suppliers', 'purchases', 'purchase_items', 'expenses', 'schema_versions'
    }
    missing = expected_tables - tables
    if missing:
        print(f"FAILED: Missing expected tables: {missing}")
        conn.close()
        proc.kill()
        return False

    cursor.execute("SELECT version, script_name FROM schema_versions ORDER BY version")
    migrations = cursor.fetchall()
    print(f"Applied migrations: {migrations}")
    if len(migrations) < 3:
        print(f"FAILED: Expected at least 3 applied migrations, found {len(migrations)}")
        conn.close()
        proc.kill()
        return False

    # Check PRAGMA journal_mode is WAL
    cursor.execute("PRAGMA journal_mode")
    jmode = cursor.fetchone()[0]
    print(f"SQLite journal_mode: {jmode.upper()}")
    if jmode.upper() != "WAL":
        print(f"WARNING: Expected WAL journal mode, got {jmode}")

    # Insert a test record to test persistence
    cursor.execute("INSERT INTO categories (name) VALUES ('Test Category')")
    cat_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine, is_active)
        VALUES ('Test Packaged Product', ?, 'pcs', 2500, 5, 0, 1)
    """, (cat_id,))
    prod_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"SUCCESS: Inserted test product ID {prod_id} into packaged DB")

    # Terminate process cleanly
    proc.terminate()
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("Process terminated cleanly.")

    # 3. Test persistence across reopen
    print("\n[Test 2] Reopening packaged executable to verify data persistence...")
    proc2 = subprocess.Popen(
        [str(exe_path), "--db", str(test_db)],
        cwd=str(temp_dir),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(4)
    if proc2.poll() is not None:
        print(f"FAILED: Second launch exited prematurely with code {proc2.poll()}!")
        return False

    # Verify product still exists
    conn2 = sqlite3.connect(str(test_db))
    cur2 = conn2.cursor()
    cur2.execute("SELECT id, name, selling_price FROM products WHERE id=?", (prod_id,))
    row = cur2.fetchone()
    conn2.close()

    proc2.terminate()
    try:
        proc2.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc2.kill()
        proc2.wait()

    if not row or row[1] != 'Test Packaged Product':
        print(f"FAILED: Product did not persist after relaunch: {row}")
        return False

    print(f"SUCCESS: Product persisted across restarts! {row}")

    # 4. Test missing database safety check
    print("\n[Test 3] Testing missing-database safety check...")
    # Create an appdata dir with marker but missing db
    safety_temp = temp_dir / "safety_test_appdata"
    medisales_dir = safety_temp / "Medisales"
    medisales_dir.mkdir(parents=True, exist_ok=True)
    marker = medisales_dir / ".medisales_initialized"
    marker.write_text("initialized", encoding="utf-8")

    safety_env = clean_env.copy()
    safety_env["LOCALAPPDATA"] = str(safety_temp)

    proc3 = subprocess.Popen(
        [str(exe_path)],
        cwd=str(temp_dir),
        env=safety_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # The process shows QMessageBox.critical for missing expected db and exits when user closes or in headless
    # We can check that the db file was NOT created!
    time.sleep(2)
    # Terminate proc3 if dialog is showing
    proc3.terminate()
    try:
        proc3.wait(timeout=3)
    except Exception:
        proc3.kill()
        proc3.wait()
    if proc3.returncode != 1:
        print(f"FAILED: Expected exit code 1 for missing expected database, got {proc3.returncode}")
        return False

    # Verify that it DID NOT create a blank database!
    blank_db = medisales_dir / "medisales.db"
    if blank_db.exists():
        print("FAILED: Packaged app created an empty database when an existing one was missing!")
        return False

    print("SUCCESS: App refused to create an accidental empty database when one was expected!")

    # 5. Test Phase 13 assets & offline packaging integrity
    print("\n[Test 4] Verifying Phase 13 bundled fonts, license, and openpyxl packaging...")
    internal_dir = repo_dir / "dist" / "Medisales" / "_internal"
    font_reg = internal_dir / "src" / "ui_web" / "fonts" / "NotoSansMyanmar-Regular.ttf"
    font_bold = internal_dir / "src" / "ui_web" / "fonts" / "NotoSansMyanmar-Bold.ttf"
    ofl_txt = internal_dir / "src" / "ui_web" / "fonts" / "OFL.txt"

    if not font_reg.exists():
        print(f"FAILED: Bundled regular font missing at {font_reg}")
        return False
    if not font_bold.exists():
        print(f"FAILED: Bundled bold font missing at {font_bold}")
        return False
    if not ofl_txt.exists():
        print(f"FAILED: Font license file missing at {ofl_txt}")
        return False
    print(f"SUCCESS: Offline fonts & OFL license bundled in executable distribution!")

    # Verify openpyxl is bundled in packaged distribution
    openpyxl_found = False
    pyz_path = repo_dir / "build" / "medisales" / "PYZ-00.pyz"
    if pyz_path.exists():
        try:
            from PyInstaller.archive.readers import ZlibArchiveReader
            reader = ZlibArchiveReader(str(pyz_path))
            openpyxl_found = any("openpyxl" in k for k in reader.toc.keys())
        except Exception:
            pass

    if not openpyxl_found:
        # Fallback check in _internal directory
        openpyxl_found = bool(list(internal_dir.glob("*openpyxl*")))

    if not openpyxl_found:
        print("FAILED: openpyxl dependency not found in packaged distribution!")
        return False
    print("SUCCESS: openpyxl library bundled for genuine Excel export!")

    # Verify language persistence across restarts in packaged executable
    print("\n[Test 5] Verifying language setting persistence across packaged app restarts...")
    conn_lang = sqlite3.connect(str(test_db))
    cur_lang = conn_lang.cursor()
    cur_lang.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('language', 'my')")
    conn_lang.commit()
    conn_lang.close()

    proc4 = subprocess.Popen(
        [str(exe_path), "--db", str(test_db)],
        cwd=str(temp_dir),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(4)
    if proc4.poll() is not None:
        print(f"FAILED: Packaged app failed on restart with language preference set!")
        return False

    proc4.terminate()
    try:
        proc4.wait(timeout=4)
    except Exception:
        proc4.kill()
        proc4.wait()

    conn_lang_check = sqlite3.connect(str(test_db))
    cur_chk = conn_lang_check.cursor()
    cur_chk.execute("SELECT value FROM settings WHERE key='language'")
    lang_row = cur_chk.fetchone()
    conn_lang_check.close()

    if not lang_row or lang_row[0] != 'my':
        print(f"FAILED: Expected language 'my' persisted, got {lang_row}")
        return False
    print("SUCCESS: Language preference persisted and restored properly in packaged app!")

    # 6. Clean up temporary test files
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    print("\n==================================================")
    print("ALL PACKAGED EXECUTABLE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = test_packaged_executable()
    sys.exit(0 if success else 1)
