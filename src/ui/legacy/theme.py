# src/ui/theme.py

GLOBAL_STYLE = """
/* Global Reset & Base */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif;
    font-size: 14px;
    color: #1e293b;
}

QMainWindow, QStackedWidget {
    background-color: #f1f5f9;
}

/* Sidebar */
QListWidget#Sidebar {
    background-color: #0f172a;
    color: #94a3b8;
    border: none;
    outline: none;
}

QListWidget#Sidebar::item {
    padding: 12px 20px;
    border-left: 4px solid transparent;
}

QListWidget#Sidebar::item:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QListWidget#Sidebar::item:selected {
    background-color: #1e293b;
    color: #ffffff;
    border-left: 4px solid #0d9488;
}

/* Headings */
QLabel.page-title {
    font-size: 24px;
    font-weight: 600;
    color: #0f172a;
    padding-bottom: 8px;
}

QLabel.page-subtitle {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 16px;
}

QLabel.brand-title {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
    padding: 20px 10px;
    qproperty-alignment: AlignCenter;
}

/* Cards */
QWidget.card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    color: #334155;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #f1f5f9;
}

QPushButton.primary {
    background-color: #0d9488;
    color: #ffffff;
    border: none;
}
QPushButton.primary:hover {
    background-color: #0f766e;
}
QPushButton.primary:pressed {
    background-color: #115e59;
}

QPushButton.danger {
    background-color: #ef4444;
    color: #ffffff;
    border: none;
}
QPushButton.danger:hover {
    background-color: #dc2626;
}

QPushButton.success {
    background-color: #10b981;
    color: #ffffff;
    border: none;
}
QPushButton.success:hover {
    background-color: #059669;
}

/* Inputs */
QLineEdit, QSpinBox, QDateEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 10px;
    color: #1e293b;
    selection-background-color: #0d9488;
}

QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid #0d9488;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #64748b;
    margin-right: 8px;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    alternate-background-color: #f8fafc;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0369a1;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #f1f5f9;
    font-weight: 600;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    padding: 8px 16px;
    color: #64748b;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom-color: #ffffff;
    color: #0d9488;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #f8fafc;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
