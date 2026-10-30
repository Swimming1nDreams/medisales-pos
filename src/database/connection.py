import sqlite3
from contextlib import contextmanager
import threading

class DatabaseManager:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a thread-local SQLite connection with proper PRAGMAs."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            # Enable Foreign Keys
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            # Use WAL mode for better concurrency, skip for memory DB
            if self.db_path != ":memory:":
                self._local.conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def close(self):
        """Closes the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    @contextmanager
    def transaction(self):
        """Context manager for an atomic database transaction."""
        conn = self.get_connection()
        try:
            # Begin an explicit transaction
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def backup_to_file(self, target_filepath: str) -> None:
        """
        Creates an online, consistent backup of the database to target_filepath using SQLite's backup API.
        Does not close or corrupt the active database connection.
        """
        import os
        target_dir = os.path.dirname(os.path.abspath(target_filepath))
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        src_conn = self.get_connection()
        dst_conn = sqlite3.connect(target_filepath)
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            dst_conn.close()

    def restore_from_file(self, source_filepath: str) -> str:
        """
        Safely restores the database from source_filepath.
        Validates source database integrity before restoring.
        Creates an automatic safety backup of current database before restoring.
        Returns the path of the safety backup created.
        """
        import os
        from datetime import datetime

        if not os.path.exists(source_filepath):
            raise FileNotFoundError(f"Backup file not found: {source_filepath}")

        # Validate source database
        try:
            test_conn = sqlite3.connect(source_filepath)
            try:
                check = test_conn.execute("PRAGMA integrity_check").fetchone()
                if not check or check[0] != "ok":
                    raise ValueError("The selected backup file is corrupt or not a valid SQLite database.")
                tables = [r[0] for r in test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                required = {'products', 'sales', 'purchases'}
                if not required.issubset(set(tables)):
                    raise ValueError("The selected file is not a valid Medisales database (missing required tables).")
            finally:
                test_conn.close()
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            raise ValueError(f"The selected backup file is corrupt or not a valid SQLite database: {e}")

        # Step 1: Create automatic safety backup before restore
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
        else:
            db_dir = os.getcwd()
        safety_backup_path = os.path.join(db_dir, f"medisales_pre_restore_{timestamp}.db")
        self.backup_to_file(safety_backup_path)

        # Step 2: Restore from source into active database connection using backup API
        src_conn = sqlite3.connect(source_filepath)
        live_conn = self.get_connection()
        try:
            with live_conn:
                src_conn.backup(live_conn)
            # Checkpoint WAL if on disk
            if self.db_path != ":memory:":
                live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            src_conn.close()

        return safety_backup_path
