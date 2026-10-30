from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
    QLineEdit, QComboBox, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

class InventoryPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.report_service = services['report_service']
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Inventory")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Track stock levels, values, and medicine expirations")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Current Stock Tab ---
        stock_tab = QWidget()
        stock_layout = QVBoxLayout(stock_tab)
        
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory...")
        self.search_input.textChanged.connect(self._filter_stock)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Items", "Low Stock Only", "Medicines Only", "General Only"])
        self.filter_combo.currentIndexChanged.connect(self._filter_stock)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch()
        stock_layout.addLayout(toolbar)
        
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels([
            "Product", "Unit", "Current Stock", "Min Stock", "Total Value", "Status"
        ])
        self.stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        stock_layout.addWidget(self.stock_table)
        self.tabs.addTab(stock_tab, "Current Stock")
        
        # --- Medicine Batches Tab ---
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        batch_toolbar = QHBoxLayout()
        self.batch_filter = QComboBox()
        self.batch_filter.addItems(["All Sellable", "Expiring Soon (30 days)", "Expired", "Unknown Expiry"])
        self.batch_filter.currentIndexChanged.connect(self._load_batches)
        
        batch_toolbar.addWidget(QLabel("Filter:"))
        batch_toolbar.addWidget(self.batch_filter)
        batch_toolbar.addStretch()
        batch_layout.addLayout(batch_toolbar)
        
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels([
            "Product", "Batch #", "Current Qty", "Expiry Date", "Unit Cost"
        ])
        self.batch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        batch_layout.addWidget(self.batch_table)
        self.tabs.addTab(batch_tab, "Medicine Batches")

    def refresh_data(self):
        self._load_stock()
        self._load_batches()

    def _load_stock(self):
        try:
            self.stock_data = self.report_service.get_current_stock()
            self._filter_stock()
        except Exception:
            pass

    def _filter_stock(self):
        if not hasattr(self, 'stock_data'): return
        
        search = self.search_input.text().lower()
        f_type = self.filter_combo.currentIndex()
        
        filtered = []
        for p in self.stock_data:
            if search not in p['name'].lower():
                continue
                
            if f_type == 1 and p['current_stock'] > p['min_stock_level']:
                continue
            if f_type == 2 and not p['is_medicine']:
                continue
            if f_type == 3 and p['is_medicine']:
                continue
                
            filtered.append(p)
            
        self.stock_table.setRowCount(len(filtered))
        for i, p in enumerate(filtered):
            self.stock_table.setItem(i, 0, QTableWidgetItem(p['name']))
            self.stock_table.setItem(i, 1, QTableWidgetItem(p['unit_measure']))
            
            qty_item = QTableWidgetItem(str(p['current_stock']))
            if p['current_stock'] <= p['min_stock_level']:
                qty_item.setForeground(Qt.red)
            self.stock_table.setItem(i, 2, qty_item)
            
            self.stock_table.setItem(i, 3, QTableWidgetItem(str(p['min_stock_level'])))
            self.stock_table.setItem(i, 4, QTableWidgetItem(f"{p['inventory_value']:,} Ks"))
            
            status = "Low Stock" if p['current_stock'] <= p['min_stock_level'] else "OK"
            self.stock_table.setItem(i, 5, QTableWidgetItem(status))

    def _load_batches(self):
        try:
            idx = self.batch_filter.currentIndex()
            f_map = {0: 'all', 1: 'expiring_soon', 2: 'expired', 3: 'unknown_expiry'}
            filter_type = f_map[idx]
            
            batches = self.report_service.get_medicine_batches_report(filter_type=filter_type)
            
            self.batch_table.setRowCount(len(batches))
            for i, b in enumerate(batches):
                self.batch_table.setItem(i, 0, QTableWidgetItem(b['product_name']))
                self.batch_table.setItem(i, 1, QTableWidgetItem(b['batch_number'] or "N/A"))
                self.batch_table.setItem(i, 2, QTableWidgetItem(str(b['current_qty'])))
                
                exp_item = QTableWidgetItem(b['expiry_date'] or "Unknown")
                if filter_type == 'expired' or filter_type == 'unknown_expiry':
                    exp_item.setForeground(Qt.red)
                self.batch_table.setItem(i, 3, exp_item)
                
                self.batch_table.setItem(i, 4, QTableWidgetItem(f"{b['unit_cost']:,} Ks"))
        except Exception:
            pass
