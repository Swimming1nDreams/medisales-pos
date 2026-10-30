import os
import sys
from pathlib import Path

def get_bundle_dir() -> Path:
    """
    Returns the root directory of the application bundle.
    In PyInstaller frozen mode, this points to sys._MEIPASS or executable directory.
    In source development mode, this points to the repository root.
    """
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)))
    return Path(__file__).resolve().parent.parent.parent

def get_web_ui_dir() -> Path:
    """
    Locates the ui_web directory containing index.html, output.css, and JS modules.
    Works whether packaged flat, under src/ui_web, or run from source.
    """
    bundle_dir = get_bundle_dir()
    candidates = [
        bundle_dir / "src" / "ui_web",
        bundle_dir / "ui_web",
        Path(__file__).resolve().parent.parent / "ui_web"
    ]
    for c in candidates:
        if (c / "index.html").exists():
            return c
    # Fallback to candidate 0
    return candidates[0]

def get_migrations_dir() -> Path:
    """
    Locates the database migrations SQL directory.
    """
    bundle_dir = get_bundle_dir()
    candidates = [
        bundle_dir / "src" / "database" / "sql",
        bundle_dir / "database" / "sql",
        Path(__file__).resolve().parent.parent / "database" / "sql"
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("*.sql")):
            return c
    return candidates[0]

def get_user_data_dir() -> Path:
    """
    Returns the writable per-user application data directory for live databases.
    On Windows: %LOCALAPPDATA%\\Medisales (e.g. C:\\Users\\<user>\\AppData\\Local\\Medisales)
    On Linux/macOS: ~/.local/share/Medisales
    """
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data)
        else:
            app_data = os.environ.get("APPDATA")
            base = Path(app_data) if app_data else Path.home() / "AppData" / "Local"
        data_dir = base / "Medisales"
    else:
        data_dir = Path.home() / ".local" / "share" / "Medisales"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def resolve_database_path(cli_override: str = None) -> tuple[Path, bool]:
    """
    Determines the database path safely.
    Returns (db_path, is_first_launch).
    
    Safety Rules:
    1. CLI argument (--db / --database) takes highest priority.
    2. Environment variable MEDISALES_DB_PATH takes next priority.
    3. In packaged mode, uses %LOCALAPPDATA%\\Medisales\\medisales.db.
       - If an existing database was previously initialized but is now missing,
         raises FileNotFoundError rather than silently creating an empty database.
       - If first launch, returns is_first_launch=True.
    4. In development mode (from source), if a local medisales.db exists in the
       project root and no override was specified, uses it to preserve workflow.
    """
    # 1. CLI Override
    if cli_override:
        path = Path(cli_override).resolve()
        is_first_launch = not path.exists()
        return path, is_first_launch

    # 2. Environment Variable Override
    env_path = os.environ.get("MEDISALES_DB_PATH")
    if env_path:
        path = Path(env_path).resolve()
        is_first_launch = not path.exists()
        return path, is_first_launch

    # 3. Packaged vs Development Mode
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        data_dir = get_user_data_dir()
        db_path = data_dir / "medisales.db"
        marker_file = data_dir / ".medisales_initialized"

        if db_path.exists():
            return db_path, False

        if marker_file.exists() and not db_path.exists():
            # Safety check: database was expected because system was initialized earlier,
            # but the file is missing!
            raise FileNotFoundError(
                f"Expected Medisales database file at '{db_path}' was not found.\n\n"
                f"To prevent accidental data loss or running on an empty database, "
                f"Medisales will not automatically initialize a blank database here.\n\n"
                f"If you have a backup file, please restore it to this location or "
                f"launch with --db <path> to specify its new location."
            )

        # Clean first launch
        return db_path, True

    else:
        # Development mode from source
        # Check project root first
        repo_root = get_bundle_dir()
        root_db = repo_root / "medisales.db"
        if root_db.exists():
            return root_db, False

        # Otherwise fallback to user data dir
        data_dir = get_user_data_dir()
        db_path = data_dir / "medisales.db"
        is_first_launch = not db_path.exists()
        return db_path, is_first_launch

def mark_database_initialized(db_path: Path):
    """
    Records an initialization marker next to the database so that subsequent
    launches know an existing database is expected.
    """
    try:
        marker = db_path.parent / ".medisales_initialized"
        marker.write_text(f"initialized: {db_path.name}\n", encoding="utf-8")
    except Exception as e:
        print(f"Warning: could not write initialization marker: {e}")
