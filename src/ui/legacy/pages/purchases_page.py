from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, 
    QMessageBox, QHeaderView, QTabWidget, QSpinBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

class PurchasesPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.purchase_service = services['purchase_service']
        self.supplier_service = services['supplier_service']
        self.product_service = services['product_service']
        self.report_service = services['report_service']
        
        self.cart_items = []
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Purchases")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Record new incoming stock and view purchase history")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- New Purchase Tab ---
        new_tab = QWidget()
        new_layout = QVBoxLayout(new_tab)
        
        # Header Info
        header_layout = QHBoxLayout()
        self.supp_combo = QComboBox()
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Invoice / Ref Number")
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        header_layout.addWidget(QLabel("Supplier:"))
        header_layout.addWidget(self.supp_combo)
        header_layout.addWidget(QLabel("Ref:"))
        header_layout.addWidget(self.ref_input)
        header_layout.addWidget(QLabel("Date:"))
        header_layout.addWidget(self.date_edit)
        new_layout.addLayout(header_layout)
        
        # Item Entry
        item_layout = QHBoxLayout()
        self.prod_combo = QComboBox()
        self.prod_combo.setMinimumWidth(200)
        self.prod_combo.currentIndexChanged.connect(self._on_product_selected)
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999999)
        
        self.cost_spin = QSpinBox()
        self.cost_spin.setRange(0, 99999999)
        self.cost_spin.setPrefix("Ks ")
        
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("Batch # (Med)")
        
        self.expiry_edit = QDateEdit()
        self.expiry_edit.setCalendarPopup(True)
        self.expiry_edit.setSpecialValueText("No Expiry")
        self.expiry_edit.setDate(self.expiry_edit.minimumDate())
        
        add_btn = QPushButton("Add Item")
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self._add_item)
        
        item_layout.addWidget(QLabel("Product:"))
        item_layout.addWidget(self.prod_combo)
        item_layout.addWidget(QLabel("Qty:"))
        item_layout.addWidget(self.qty_spin)
        item_layout.addWidget(QLabel("Unit Cost:"))
        item_layout.addWidget(self.cost_spin)
        item_layout.addWidget(self.batch_input)
        item_layout.addWidget(self.expiry_edit)
        item_layout.addWidget(add_btn)
        new_layout.addLayout(item_layout)
        
        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(7)
        self.cart_table.setHorizontalHeaderLabels([
            "Product", "Qty", "Unit Cost", "Line Total", "Batch", "Expiry", "Action"
        ])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        new_layout.addWidget(self.cart_table)
        
        # Footer
        footer = QHBoxLayout()
        self.total_label = QLabel("Total: 0 Ks")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        save_btn = QPushButton("Save Purchase")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(44)
        save_btn.setMinimumWidth(200)
        save_btn.setStyleSheet("font-size: 16px;")
        save_btn.clicked.connect(self._save_purchase)
        
        footer.addStretch()
        footer.addWidget(self.total_label)
        footer.addWidget(save_btn)
        new_layout.addLayout(footer)
        
        self.tabs.addTab(new_tab, "Record Purchase")
        
        # --- History Tab ---
        hist_tab = QWidget()
        hist_layout = QVBoxLayout(hist_tab)
        
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels([
            "ID", "Date", "Supplier", "Ref", "Total Amount", "Status"
        ])
        self.hist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        hist_layout.addWidget(self.hist_table)
        self.tabs.addTab(hist_tab, "Purchase History")

    def refresh_data(self):
        try:
            # Load suppliers
            supps = self.supplier_service.list_suppliers(include_inactive=False)
            self.supp_combo.clear()
            for s in supps:
                self.supp_combo.addItem(s['name'], s['id'])
                
            # Load products
            prods = self.product_service.list_products(include_inactive=False)
            self.prod_combo.clear()
            self.prod_combo.addItem("-- Select Product --", None)
            for p in prods:
                self.prod_combo.addItem(p['name'], p)
                
            # Load history
            today = datetime.now().strftime("%Y-%m-%d")
            past = (datetime.now().replace(year=datetime.now().year-1)).strftime("%Y-%m-%d")
            hist = self.report_service.get_purchases(past, today)
            
            self.hist_table.setRowCount(len(hist))
            for i, h in enumerate(hist):
                self.hist_table.setItem(i, 0, QTableWidgetItem(str(h['id'])))
                self.hist_table.setItem(i, 1, QTableWidgetItem(h['date']))
                self.hist_table.setItem(i, 2, QTableWidgetItem(h['supplier_name']))
                self.hist_table.setItem(i, 3, QTableWidgetItem(h['reference']))
                self.hist_table.setItem(i, 4, QTableWidgetItem(f"{h['total_amount']:,} Ks"))
                self.hist_table.setItem(i, 5, QTableWidgetItem(h['status']))
        except Exception:
            pass

    def _on_product_selected(self, idx):
        p = self.prod_combo.currentData()
        if p and p['is_medicine']:
            self.batch_input.setEnabled(True)
            self.expiry_edit.setEnabled(True)
        else:
            self.batch_input.setEnabled(False)
            self.batch_input.clear()
            self.expiry_edit.setEnabled(False)
            self.expiry_edit.setDate(self.expiry_edit.minimumDate())

    def _add_item(self):
        p = self.prod_combo.currentData()
        if not p:
            QMessageBox.warning(self, "Warning", "Select a product.")
            return
            
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()
        
        batch = None
        expiry = None
        if p['is_medicine']:
            batch = self.batch_input.text().strip()
            if not batch:
                QMessageBox.warning(self, "Warning", "Batch number is required for medicine.")
                return
            if self.expiry_edit.date() != self.expiry_edit.minimumDate():
                expiry = self.expiry_edit.date().toString("yyyy-MM-dd")
            else:
                QMessageBox.warning(self, "Warning", "Expiry date is required for medicine.")
                return
                
        self.cart_items.append({
            'product_id': p['id'],
            'name': p['name'],
            'quantity': qty,
            'unit_cost': cost,
            'batch_number': batch,
            'expiry_date': expiry
        })
        self._update_cart()

    def _update_cart(self):
        self.cart_table.setRowCount(len(self.cart_items))
        total = 0
        for i, item in enumerate(self.cart_items):
            line_total = item['quantity'] * item['unit_cost']
            total += line_total
            
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"{item['unit_cost']:,}"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{line_total:,}"))
            self.cart_table.setItem(i, 4, QTableWidgetItem(item['batch_number'] or ""))
            self.cart_table.setItem(i, 5, QTableWidgetItem(item['expiry_date'] or ""))
            
            btn = QPushButton("Remove")
            btn.setProperty("class", "danger")
            btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            self.cart_table.setCellWidget(i, 6, btn)
            
        self.total_label.setText(f"Total: {total:,} Ks")

    def _remove_item(self, idx):
        if 0 <= idx < len(self.cart_items):
            self.cart_items.pop(idx)
            self._update_cart()

    def _save_purchase(self):
        supp_id = self.supp_combo.currentData()
        ref = self.ref_input.text().strip()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        
        if not supp_id:
            QMessageBox.warning(self, "Warning", "Select a supplier.")
            return
        if not ref:
            QMessageBox.warning(self, "Warning", "Reference is required.")
            return
        if not self.cart_items:
            QMessageBox.warning(self, "Warning", "No items added.")
            return
            
        reply = QMessageBox.question(self, "Confirm", "Save purchase and update stock?", QMessageBox.Yes | QMessageBox.No)
        # To prevent double clicks, we should disable the button but we don't have a direct reference to it. Let's find it or just rely on synchronous execution blocking the UI thread.
        # Wait, the method is synchronous, but `QMessageBox.information` runs an event loop.
        # We can clear the cart IMMEDIATELY before showing the message box so double clicking is harmless.
        if reply == QMessageBox.Yes:
            try:
                self.purchase_service.create_purchase(ref, supp_id, date_str, self.cart_items)
                self.cart_items.clear()
                self._update_cart()
                self.ref_input.clear()
                self.refresh_data()
                QMessageBox.information(self, "Success", "Purchase saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
