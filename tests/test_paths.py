import pytest
import os
import sys
from pathlib import Path
from src.utils.paths import (
    get_bundle_dir,
    get_web_ui_dir,
    get_migrations_dir,
    get_user_data_dir,
    resolve_database_path,
    mark_database_initialized
)

def test_bundle_and_asset_paths_exist():
    bundle_dir = get_bundle_dir()
    assert bundle_dir.exists()

    web_ui_dir = get_web_ui_dir()
    assert web_ui_dir.exists()
    assert (web_ui_dir / "index.html").exists()
    assert (web_ui_dir / "output.css").exists()
    assert (web_ui_dir / "js" / "main.js").exists()

    migrations_dir = get_migrations_dir()
    assert migrations_dir.exists()
    sql_files = list(migrations_dir.glob("*.sql"))
    assert len(sql_files) >= 3

def test_user_data_dir_writable(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    data_dir = get_user_data_dir()
    assert data_dir.exists()
    assert data_dir.is_dir()
    
    # Test write permissions
    test_file = data_dir / "test_write.tmp"
    test_file.write_text("ok")
    assert test_file.read_text() == "ok"
    test_file.unlink()

def test_resolve_database_path_cli_override(tmp_path):
    custom_db = tmp_path / "custom.db"
    path, is_first = resolve_database_path(str(custom_db))
    assert path == custom_db.resolve()
    assert is_first is True

def test_resolve_database_path_env_override(tmp_path, monkeypatch):
    custom_db = tmp_path / "env_custom.db"
    monkeypatch.setenv("MEDISALES_DB_PATH", str(custom_db))
    path, is_first = resolve_database_path()
    assert path == custom_db.resolve()
    assert is_first is True

def test_resolve_database_path_missing_expected_db_in_frozen_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("MEDISALES_DB_PATH", raising=False)

    data_dir = get_user_data_dir()
    db_path = data_dir / "medisales.db"
    marker_file = data_dir / ".medisales_initialized"

    # Write marker indicating DB was initialized before
    marker_file.write_text("initialized")
    # Ensure db_path does not exist
    if db_path.exists():
        db_path.unlink()

    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_database_path()
    assert "was not found" in str(exc_info.value)
    assert "accidental data loss" in str(exc_info.value)

def test_resolve_database_path_first_launch_in_frozen_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("MEDISALES_DB_PATH", raising=False)

    data_dir = get_user_data_dir()
    marker_file = data_dir / ".medisales_initialized"
    if marker_file.exists():
        marker_file.unlink()
    db_path = data_dir / "medisales.db"
    if db_path.exists():
        db_path.unlink()

    path, is_first = resolve_database_path()
    assert path == db_path
    assert is_first is True

    # Mark initialized
    mark_database_initialized(path)
    assert marker_file.exists()
