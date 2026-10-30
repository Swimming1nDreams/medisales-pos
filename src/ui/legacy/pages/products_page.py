from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, 
    QMessageBox, QHeaderView, QFormLayout, QDialog, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt

class ProductDialog(QDialog):
    def __init__(self, product_service, product=None, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.product = product
        
        self.setWindowTitle("Edit Product" if product else "New Product")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        if self.product: self.name_input.setText(self.product['name'])
        
        self.cat_combo = QComboBox()
        cats = self.product_service.list_categories()
        for c in cats:
            self.cat_combo.addItem(c['name'], c['id'])
        if self.product:
            idx = self.cat_combo.findData(self.product['category_id'])
            if idx >= 0: self.cat_combo.setCurrentIndex(idx)
            
        self.unit_input = QLineEdit()
        if self.product: self.unit_input.setText(self.product['unit_measure'])
        
        self.price_spin = QSpinBox()
        self.price_spin.setMaximum(999999999)
        if self.product: self.price_spin.setValue(self.product['selling_price'])
        
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMaximum(99999)
        if self.product: self.min_stock_spin.setValue(self.product['min_stock_level'])
        
        self.med_check = QCheckBox("Is Medicine?")
        if self.product: 
            self.med_check.setChecked(bool(self.product['is_medicine']))
            self.med_check.setEnabled(False) # Can't change after creation in schema
            
        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(True)
        if self.product: 
            self.active_check.setChecked(bool(self.product['is_active']))
        else:
            self.active_check.hide()

        form.addRow("Name:", self.name_input)
        form.addRow("Category:", self.cat_combo)
        form.addRow("Unit Measure:", self.unit_input)
        form.addRow("Selling Price (Ks):", self.price_spin)
        form.addRow("Min Stock Level:", self.min_stock_spin)
        form.addRow("", self.med_check)
        form.addRow("", self.active_check)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        try:
            name = self.name_input.text().strip()
            cat_id = self.cat_combo.currentData()
            unit = self.unit_input.text().strip()
            price = self.price_spin.value()
            min_stock = self.min_stock_spin.value()
            
            if not cat_id:
                raise ValueError("Please select a category or create one first.")
                
            if self.product:
                self.product_service.update_product(
                    self.product['id'], name, cat_id, unit, price, min_stock, self.active_check.isChecked()
                )
            else:
                self.product_service.create_product(
                    name, cat_id, unit, price, min_stock, self.med_check.isChecked()
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class ProductsPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.product_service = services['product_service']
        self._setup_ui()
        self.refresh_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Products")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Manage your catalog, prices, and settings")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Top toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_table)
        
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories", None)
        self.cat_filter.setMinimumWidth(200)
        self.cat_filter.currentIndexChanged.connect(self._filter_table)
        
        new_btn = QPushButton("New Product")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_product)
        
        new_cat_btn = QPushButton("New Category")
        new_cat_btn.clicked.connect(self._new_category)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.cat_filter)
        toolbar.addStretch()
        toolbar.addWidget(new_cat_btn)
        toolbar.addWidget(new_btn)
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Unit", "Price", "Min Stock", "Current Stock", "Type", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self._edit_product)
        layout.addWidget(self.table)

    def refresh_data(self):
        try:
            # Refresh category filter
            cats = self.product_service.list_categories()
            # Store categories in a dict for easy lookup in table
            self.cat_dict = {c['id']: c['name'] for c in cats}
            
            # Update combo box without triggering filter multiple times
            self.cat_filter.blockSignals(True)
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories", None)
            for c in cats:
                self.cat_filter.addItem(c['name'], c['id'])
            self.cat_filter.blockSignals(False)
            
            self.products = self.product_service.list_products(include_inactive=True)
            self._filter_table()
        except Exception as e:
            pass

    def _filter_table(self):
        search_text = self.search_input.text().lower()
        cat_id = self.cat_filter.currentData()
        
        filtered = [
            p for p in self.products 
            if (search_text in p['name'].lower() or search_text in str(p['id']))
            and (cat_id is None or p['category_id'] == cat_id)
        ]
        
        self.table.setRowCount(len(filtered))
        for i, p in enumerate(filtered):
            # Store ID in hidden data
            item_id = QTableWidgetItem(str(p['id']))
            item_id.setData(Qt.UserRole, p)
            
            self.table.setItem(i, 0, item_id)
            self.table.setItem(i, 1, QTableWidgetItem(p['name']))
            self.table.setItem(i, 2, QTableWidgetItem(p['unit_measure']))
            self.table.setItem(i, 3, QTableWidgetItem(f"{p['selling_price']:,}"))
            self.table.setItem(i, 4, QTableWidgetItem(str(p['min_stock_level'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(p['current_stock'])))
            self.table.setItem(i, 6, QTableWidgetItem("Medicine" if p['is_medicine'] else "General"))
            self.table.setItem(i, 7, QTableWidgetItem("Active" if p['is_active'] else "Inactive"))

    def _new_product(self):
        dialog = ProductDialog(self.product_service, parent=self)
        if dialog.exec_():
            self.refresh_data()

    def _edit_product(self, item):
        row = item.row()
        p = self.table.item(row, 0).data(Qt.UserRole)
        dialog = ProductDialog(self.product_service, product=p, parent=self)
        if dialog.exec_():
            self.refresh_data()

    def _new_category(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Category", "Category Name:")
        if ok and name.strip():
            try:
                self.product_service.create_category(name)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
