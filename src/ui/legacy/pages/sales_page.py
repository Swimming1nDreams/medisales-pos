from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, 
    QMessageBox, QHeaderView, QTabWidget, QSpinBox
)
from PySide6.QtCore import Qt
from datetime import datetime

class SalesPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.sales_service = services['sales_service']
        self.product_service = services['product_service']
        self.inventory_service = services['inventory_service']
        self.report_service = services['report_service']
        
        self.cart_items = [] # list of dicts: product, batch_number, quantity, unit_price
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- POS / Checkout Tab ---
        pos_tab = QWidget()
        pos_layout = QVBoxLayout(pos_tab)
        
        # Product selection row
        sel_layout = QHBoxLayout()
        self.prod_combo = QComboBox()
        self.prod_combo.setMinimumWidth(250)
        self.prod_combo.currentIndexChanged.connect(self._on_product_selected)
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99999)
        self.qty_spin.setMinimumHeight(36)
        self.qty_spin.setMinimumWidth(100)
        
        add_btn = QPushButton("Add to Cart")
        add_btn.setProperty("class", "primary")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._add_to_cart)
        
        sel_layout.addWidget(QLabel("Product:"))
        sel_layout.addWidget(self.prod_combo)
        sel_layout.addWidget(QLabel("Qty:"))
        sel_layout.addWidget(self.qty_spin)
        sel_layout.addWidget(add_btn)
        sel_layout.addStretch()
        pos_layout.addLayout(sel_layout)
        
        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Line Total", "Action"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        pos_layout.addWidget(self.cart_table)
        
        # Checkout Footer
        foot_layout = QHBoxLayout()
        self.total_label = QLabel("Total: 0 Ks")
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.checkout_btn = QPushButton("Complete Sale")
        self.checkout_btn.setProperty("class", "success")
        self.checkout_btn.setMinimumHeight(44)
        self.checkout_btn.setMinimumWidth(200)
        self.checkout_btn.setStyleSheet("font-size: 16px;")
        self.checkout_btn.clicked.connect(self._checkout)
        
        foot_layout.addStretch()
        foot_layout.addWidget(self.total_label)
        foot_layout.addSpacing(20)
        foot_layout.addWidget(self.checkout_btn)
        pos_layout.addLayout(foot_layout)
        
        self.tabs.addTab(pos_tab, "Checkout")
        
        # --- History Tab ---
        hist_tab = QWidget()
        hist_layout = QVBoxLayout(hist_tab)
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(4)
        self.hist_table.setHorizontalHeaderLabels(["Sale ID", "Date", "Items", "Total Revenue"])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        hist_layout.addWidget(self.hist_table)
        self.tabs.addTab(hist_tab, "Sale History")

    def refresh_data(self):
        # Load products
        try:
            prods = self.product_service.list_products(include_inactive=False)
            self.products_data = prods
            self.prod_combo.clear()
            self.prod_combo.addItem("-- Select Product --", None)
            for p in prods:
                self.prod_combo.addItem(f"{p['name']} (Stock: {p['current_stock']}) - {p['selling_price']} Ks", p)
                
            self._load_history()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    def _on_product_selected(self, index):
        # Batch selection is no longer needed in the UI since the backend handles FEFO
        pass

    def _add_to_cart(self):
        p = self.prod_combo.currentData()
        if not p:
            QMessageBox.warning(self, "Warning", "Please select a product.")
            return
            
        qty = self.qty_spin.value()
        
        if p.get('is_medicine'):
            try:
                batches = self.inventory_service.get_sellable_medicine_batches(p['id'])
                total_eligible = sum(b['current_qty'] for b in batches)
                if qty > total_eligible:
                    QMessageBox.warning(self, "Warning", f"Insufficient eligible stock for medicine (available: {total_eligible}).")
                    return
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to check medicine batches: {e}")
                return
        else:
            if qty > p['current_stock']:
                QMessageBox.warning(self, "Warning", f"Insufficient stock (available: {p['current_stock']}).")
                return
                
        # Check if already in cart
        for item in self.cart_items:
            if item['product_id'] == p['id']:
                item['quantity'] += qty
                self._update_cart_table()
                return
                
        self.cart_items.append({
            'product_id': p['id'],
            'name': p['name'],
            'quantity': qty,
            'unit_price': p['selling_price']
        })
        self._update_cart_table()

    def _update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart_items))
        total = 0
        for i, item in enumerate(self.cart_items):
            line_total = item['quantity'] * item['unit_price']
            total += line_total
            
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"{item['unit_price']} Ks"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{line_total:,} Ks"))
            
            rm_btn = QPushButton("Remove")
            rm_btn.setProperty("class", "danger")
            rm_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            self.cart_table.setCellWidget(i, 4, rm_btn)
            
        self.total_label.setText(f"Total: {total:,} Ks")

    def _remove_item(self, idx):
        if 0 <= idx < len(self.cart_items):
            self.cart_items.pop(idx)
            self._update_cart_table()

    def _checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Warning", "Cart is empty.")
            return
            
        reply = QMessageBox.question(self, "Confirm Sale", "Complete this sale?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
            
        self.checkout_btn.setEnabled(False)
        
        # Calculate total
        total = sum(i['quantity'] * i['unit_price'] for i in self.cart_items)
        
        # Generate a reference
        ref = f"SALE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            sale_id = self.sales_service.create_sale(
                reference=ref,
                items=self.cart_items,
                amount_received=total
            )
            QMessageBox.information(self, "Success", f"Sale completed successfully! ID: {sale_id}")
            self.cart_items.clear()
            self._update_cart_table()
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete sale: {str(e)}")
        finally:
            self.checkout_btn.setEnabled(True)

    def _load_history(self):
        # We can just fetch recent sales using report service
        try:
            conn = self.report_service.db.get_connection()
            rows = conn.execute('''
                SELECT s.id, s.date_time, s.total_amount, COUNT(si.id) as items_count
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE s.status = 'Completed'
                GROUP BY s.id
                ORDER BY s.date_time DESC LIMIT 50
            ''').fetchall()
            
            self.hist_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.hist_table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.hist_table.setItem(i, 1, QTableWidgetItem(row['date_time']))
                self.hist_table.setItem(i, 2, QTableWidgetItem(str(row['items_count'])))
                self.hist_table.setItem(i, 3, QTableWidgetItem(f"{row['total_amount']:,} Ks"))
        except Exception:
            pass
