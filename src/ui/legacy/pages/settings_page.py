import os
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.db_manager = services['db_manager']
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Settings")
        title.setProperty("class", "page-title")
        subtitle = QLabel("System configuration and maintenance")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        info = QLabel(f"<b>Database Location:</b> {os.path.abspath(self.db_manager.db_path)}")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px; margin-bottom: 20px;")
        layout.addWidget(info)
        
        layout.addWidget(QLabel("<hr>"))
        db_title = QLabel("Database Backup")
        db_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b; margin-top: 10px;")
        layout.addWidget(db_title)
        
        layout.addWidget(QLabel("Create a safe backup of your entire Medisales database. This operation is safe and can be done while the application is running."))
        
        backup_btn = QPushButton("Create Database Backup")
        backup_btn.setProperty("class", "primary")
        backup_btn.setMinimumHeight(40)
        backup_btn.setFixedWidth(300)
        backup_btn.clicked.connect(self._backup_db)
        layout.addWidget(backup_btn)
        
        layout.addWidget(QLabel("<hr>"))
        db_restore = QLabel("Database Restore")
        db_restore.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b; margin-top: 10px;")
        layout.addWidget(db_restore)
        
        restore_warn = QLabel("Restoring an active database safely requires closing all connections. For safety, restore is currently <b>unavailable from the UI</b>. Please replace the database file manually while the application is closed.")
        restore_warn.setWordWrap(True)
        restore_warn.setStyleSheet("color: #ef4444;")
        layout.addWidget(restore_warn)
        
        restore_btn = QPushButton("Restore Database (Disabled)")
        restore_btn.setMinimumHeight(40)
        restore_btn.setFixedWidth(300)
        restore_btn.setEnabled(False)
        layout.addWidget(restore_btn)
        
        layout.addStretch()

    def _backup_db(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Backup", "medisales_backup.db", "SQLite Database (*.db)")
        if not file_path:
            return
            
        try:
            # SQLite online backup API is safe and locks correctly
            src = self.db_manager.get_connection()
            dst = sqlite3.connect(file_path)
            
            with dst:
                src.backup(dst)
                
            dst.close()
            QMessageBox.information(self, "Success", f"Database backed up successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup database: {str(e)}")
