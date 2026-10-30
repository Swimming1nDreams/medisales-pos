from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog, 
    QMessageBox, QHeaderView, QTabWidget, QFormLayout, QCheckBox, QSpinBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

class SupplierDialog(QDialog):
    def __init__(self, supplier_service, supplier=None, parent=None):
        super().__init__(parent)
        self.supplier_service = supplier_service
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "New Supplier")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.addr_input = QLineEdit()
        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(True)
        
        if self.supplier:
            self.name_input.setText(self.supplier['name'])
            self.phone_input.setText(self.supplier['phone'] or "")
            self.addr_input.setText(self.supplier['address'] or "")
            self.active_check.setChecked(bool(self.supplier['is_active']))
        else:
            self.active_check.hide()
            
        form.addRow("Name:", self.name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Address:", self.addr_input)
        form.addRow("", self.active_check)
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save(self):
        try:
            name = self.name_input.text()
            phone = self.phone_input.text()
            addr = self.addr_input.text()
            if self.supplier:
                self.supplier_service.update_supplier(
                    self.supplier['id'], name, phone, addr, self.active_check.isChecked()
                )
            else:
                self.supplier_service.create_supplier(name, phone, addr)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class PaymentDialog(QDialog):
    def __init__(self, supplier, purchase_service, report_service, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.purchase_service = purchase_service
        self.report_service = report_service
        self.setWindowTitle(f"Record Payment to {supplier['name']}")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.ref_input = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(1, 999999999)
        self.amount_spin.setPrefix("Ks ")
        
        self.notes_input = QLineEdit()
        
        form.addRow("Reference:", self.ref_input)
        form.addRow("Date:", self.date_edit)
        form.addRow("Payment Amount:", self.amount_spin)
        form.addRow("Notes:", self.notes_input)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("Allocate to outstanding purchases (Auto-fills top-down):"))
        self.purch_table = QTableWidget()
        self.purch_table.setColumnCount(4)
        self.purch_table.setHorizontalHeaderLabels(["ID", "Ref", "Outstanding", "Allocate"])
        layout.addWidget(self.purch_table)
        
        # Load outstanding purchases for this supplier
        self.outstanding = []
        try:
            conn = self.report_service.db.get_connection()
            rows = conn.execute('''
                SELECT id, reference, total_amount, amount_paid 
                FROM purchases 
                WHERE supplier_id = ? AND status = 'Completed' AND total_amount > amount_paid
                ORDER BY date ASC
            ''', (self.supplier['id'],)).fetchall()
            self.outstanding = [dict(r) for r in rows]
        except Exception:
            pass
            
        self.purch_table.setRowCount(len(self.outstanding))
        for i, p in enumerate(self.outstanding):
            bal = p['total_amount'] - p['amount_paid']
            self.purch_table.setItem(i, 0, QTableWidgetItem(str(p['id'])))
            self.purch_table.setItem(i, 1, QTableWidgetItem(p['reference']))
            self.purch_table.setItem(i, 2, QTableWidgetItem(f"{bal} Ks"))
            
            spin = QSpinBox()
            spin.setRange(0, bal)
            self.purch_table.setCellWidget(i, 3, spin)
            
        btns = QHBoxLayout()
        save_btn = QPushButton("Submit Payment")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save(self):
        ref = self.ref_input.text().strip()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amt = self.amount_spin.value()
        notes = self.notes_input.text().strip()
        
        if not ref:
            QMessageBox.warning(self, "Warning", "Reference required.")
            return
            
        allocations = []
        total_alloc = 0
        for i in range(self.purch_table.rowCount()):
            spin = self.purch_table.cellWidget(i, 3)
            alloc_amt = spin.value()
            if alloc_amt > 0:
                pid = int(self.purch_table.item(i, 0).text())
                allocations.append({'purchase_id': pid, 'allocated_amount': alloc_amt})
                total_alloc += alloc_amt
                
        if total_alloc > amt:
            QMessageBox.warning(self, "Warning", "Allocations exceed total payment amount.")
            return
            
        try:
            self.purchase_service.record_payment(ref, self.supplier['id'], date, amt, allocations, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class SuppliersPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.supplier_service = services['supplier_service']
        self.purchase_service = services['purchase_service']
        self.report_service = services['report_service']
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Suppliers")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Manage supplier directory and outstanding balances")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Suppliers List Tab ---
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search suppliers...")
        self.search_input.textChanged.connect(self.refresh_data)
        
        new_btn = QPushButton("New Supplier")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_supplier)
        
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        toolbar.addWidget(new_btn)
        list_layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Address", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self._edit_supplier)
        list_layout.addWidget(self.table)
        
        self.tabs.addTab(list_tab, "Suppliers")
        
        # --- Balances & Payments Tab ---
        bal_tab = QWidget()
        bal_layout = QVBoxLayout(bal_tab)
        
        self.bal_table = QTableWidget()
        self.bal_table.setColumnCount(4)
        self.bal_table.setHorizontalHeaderLabels(["Supplier", "Total Purchased", "Total Paid", "Outstanding"])
        self.bal_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        bal_layout.addWidget(self.bal_table)
        
        pay_btn = QPushButton("Record Payment to Selected Supplier")
        pay_btn.setProperty("class", "success")
        pay_btn.setMinimumHeight(36)
        pay_btn.clicked.connect(self._record_payment)
        bal_layout.addWidget(pay_btn)
        
        self.tabs.addTab(bal_tab, "Balances")

    def refresh_data(self):
        try:
            search = self.search_input.text()
            supps = self.supplier_service.list_suppliers(include_inactive=True, search_term=search)
            
            self.table.setRowCount(len(supps))
            for i, s in enumerate(supps):
                item = QTableWidgetItem(str(s['id']))
                item.setData(Qt.UserRole, s)
                self.table.setItem(i, 0, item)
                self.table.setItem(i, 1, QTableWidgetItem(s['name']))
                self.table.setItem(i, 2, QTableWidgetItem(s['phone'] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(s['address'] or ""))
                self.table.setItem(i, 4, QTableWidgetItem("Active" if s['is_active'] else "Inactive"))
                
            bals = self.report_service.get_supplier_balances()
            self.bals_data = bals
            self.bal_table.setRowCount(len(bals))
            for i, b in enumerate(bals):
                item = QTableWidgetItem(b['supplier_name'])
                item.setData(Qt.UserRole, b)
                self.bal_table.setItem(i, 0, item)
                self.bal_table.setItem(i, 1, QTableWidgetItem(f"{b['total_purchased']:,} Ks"))
                self.bal_table.setItem(i, 2, QTableWidgetItem(f"{b['total_paid']:,} Ks"))
                
                out_item = QTableWidgetItem(f"{b['outstanding_balance']:,} Ks")
                out_item.setForeground(Qt.red)
                self.bal_table.setItem(i, 3, out_item)
                
        except Exception:
            pass

    def _new_supplier(self):
        dlg = SupplierDialog(self.supplier_service, parent=self)
        if dlg.exec_():
            self.refresh_data()

    def _edit_supplier(self, item):
        s = self.table.item(item.row(), 0).data(Qt.UserRole)
        dlg = SupplierDialog(self.supplier_service, supplier=s, parent=self)
        if dlg.exec_():
            self.refresh_data()

    def _record_payment(self):
        row = self.bal_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select a supplier from the balances table.")
            return
            
        b = self.bal_table.item(row, 0).data(Qt.UserRole)
        # We need the full supplier dict
        conn = self.report_service.db.get_connection()
        s_row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (b['supplier_id'],)).fetchone()
        
        dlg = PaymentDialog(dict(s_row), self.purchase_service, self.report_service, parent=self)
        if dlg.exec_():
            QMessageBox.information(self, "Success", "Payment recorded successfully!")
            self.refresh_data()
