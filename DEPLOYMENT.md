# Say Mahar (ဆေးမဟာ) Windows Desktop Deployment Guide

This guide describes how to build, deploy, update, and maintain the **Say Mahar (ဆေးမဟာ) Pharmacy & Retail POS** Windows desktop application (formerly Medisales).

---

## 1. System Architecture & Prerequisites

Say Mahar is engineered as a **100% offline, standalone Windows desktop application**.

- **Frontend:** Local HTML5, JavaScript (ES6+ modules), and compiled Tailwind CSS.
- **Desktop Runtime:** PySide6 `QWebEngineView` with bidirectional `QWebChannel` RPC bridge.
- **Database Engine:** Embedded SQLite 3 with Write-Ahead Logging (`WAL`) mode, foreign key enforcement, and immutable audit triggers.
- **Target OS:** Windows 10 (64-bit) / Windows 11 (64-bit).
- **Client Machine Dependencies:** **None**. The target computer does *not* require Python, Node.js, npm, or an active internet connection.

---

## 2. How to Build the Application

From the project root on a build machine with Python and Node.js installed:

```powershell
# 1. Activate development virtual environment
.\venv\Scripts\Activate.ps1

# 2. Run the automated build script
python build.py
```

### What `build.py` Does:
1. **Compiles Tailwind CSS:** Runs Tailwind CLI with `--minify` using `src/ui_web/tailwind.config.js` and `src/ui_web/input.css` to generate optimized `src/ui_web/output.css`.
2. **Executes PyInstaller:** Uses [medisales.spec](file:///c:/Users/Lenovo/Downloads/Medisales/medisales.spec) to bundle Python, PySide6, QtWebEngine, local web assets, and SQL migrations into a standalone `onedir` distribution.

### Build Output Location:
- The completed application is output to:
  ```text
  dist\Medisales\
  ├── Medisales.exe         (Application launcher)
  └── _internal\            (Bundled QtWebEngine, Python runtime, and assets)
  ```

---

## 3. Deployment to the Shop Computer

To install the application on the pharmacy cashier/owner PC:

1. Copy the entire `dist\Medisales` folder to the target machine (e.g., `C:\Program Files\Medisales` or `C:\Medisales`).
2. Create a Windows Desktop shortcut pointing to `Medisales.exe`.
3. Launch `Medisales.exe`.

---

## 4. Live Database Location & Data Safety Architecture

To ensure data safety, multi-user Windows permissions compliance, and seamless software updates:

### Deliberate Separation of Executable and Live Data
- **Live Database File:**
  ```text
  %LOCALAPPDATA%\Medisales\medisales.db
  (e.g., C:\Users\<Username>\AppData\Local\Medisales\medisales.db)
  ```
- **Why `%LOCALAPPDATA%`?**
  1. **Full Write Permissions:** Standard Windows cashier accounts always have write permissions to `%LOCALAPPDATA%`, preventing permission errors when installed in `C:\Program Files\Medisales`.
  2. **Update Isolation:** Upgrading or reinstalling the application files in `Program Files` will **never** delete, overwrite, or touch the shop's active database.
  3. **Multi-Process Concurrency:** SQLite `WAL` mode safely manages concurrent reads and atomic writes.

### Accidental Data Loss Safeguards
- **First Launch Detection:** On the very first launch on a new PC, Medisales initializes a clean schema, applies all database migrations, and creates a `.medisales_initialized` marker.
- **Missing Database Protection:** If the application was previously initialized but `medisales.db` cannot be found (e.g. accidental deletion or unmounted network drive), Medisales **refuses to silently initialize an empty database**. It halts with a critical alert instructing the user to restore their backup.

### Custom Database Overrides (Advanced)
You can point Medisales to an alternate database path using either:
```powershell
# Command-line parameter:
.\Medisales.exe --db "D:\MyData\medisales.db"

# Or environment variable:
set MEDISALES_DB_PATH=D:\MyData\medisales.db
```

---

## 5. Backup & Restore Procedures

### Method A: In-App Database Backup (Recommended)
1. Open Medisales and click **Settings** in the sidebar.
2. In the **Database Backup** card, click **"Create Local Database Backup"**.
3. Choose a destination folder (e.g., an external USB flash drive or secure backup folder).
4. Medisales uses SQLite's non-blocking online backup engine; cashiers can continue serving customers without interruption.

### Method B: In-App Database Restore
1. Open **Settings** -> **Database Restore** -> Click **"Restore From Backup File..."**.
2. Review the confirmation dialog.
3. Select your `.db` backup file.
4. **Safety Guarantee:** Before restoring, Medisales automatically creates a timestamped safety backup of the active database (`medisales_pre_restore_YYYYMMDD_HHMMSS.db`) in `%LOCALAPPDATA%\Medisales\`.

### Method C: Manual File Backup
1. Close Medisales.
2. Navigate to `C:\Users\<Username>\AppData\Local\Medisales\`.
3. Copy `medisales.db` (and `medisales.db-wal` / `medisales.db-shm` if present) to an external storage drive.

---

## 6. How to Update the Application

When a new software version is released:

1. Close the running `Medisales.exe`.
2. Replace the contents of the `Medisales` program folder (e.g. `C:\Program Files\Medisales\`) with the new `dist\Medisales` build.
3. Launch `Medisales.exe`.
4. **Automatic Migrations:** On startup, Medisales inspects the `schema_versions` table and applies any new schema updates in a single atomic transaction without modifying existing inventory or transaction history.

---

## 7. Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **"Expected Medisales database file was not found" on startup** | The active database file was moved, renamed, or deleted after initial setup. | Check `C:\Users\<Username>\AppData\Local\Medisales\`. Restore a backup copy named `medisales.db` into that folder, or launch with `--db <path>`. |
| **"Failed to initialize database: database is locked"** | Another instance or background process is currently holding an exclusive lock. | Open Windows Task Manager (`Ctrl+Shift+Esc`), terminate any lingering `Medisales.exe` processes, and restart. |
| **Blank window or failed rendering** | Corrupted GPU cache or graphics driver conflict. | Clear the cache at `%LOCALAPPDATA%\Medisales\QtWebEngine\` and restart. |
