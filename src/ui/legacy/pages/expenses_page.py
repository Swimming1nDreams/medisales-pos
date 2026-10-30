from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, 
    QMessageBox, QHeaderView, QDateEdit, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt, QDate

class ExpensesPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.expense_service = services['expense_service']
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Expenses")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Record and manage operating expenses")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)
        
        # --- Left Panel: New Expense ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(300)
        
        left_layout.addWidget(QLabel("<h2>Record Expense</h2>"))
        
        form = QFormLayout()
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Rent", "Utilities", "Payroll", "Supplies", "Maintenance", "Other"])
        self.cat_combo.setEditable(True)
        
        self.desc_input = QLineEdit()
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(1, 999999999)
        self.amount_spin.setPrefix("Ks ")
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        form.addRow("Category:", self.cat_combo)
        form.addRow("Description:", self.desc_input)
        form.addRow("Amount:", self.amount_spin)
        form.addRow("Date:", self.date_edit)
        left_layout.addLayout(form)
        
        save_btn = QPushButton("Save Expense")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self._save_expense)
        left_layout.addWidget(save_btn)
        left_layout.addStretch()
        
        content_layout.addWidget(left_panel)
        
        # --- Right Panel: Expense List ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        toolbar = QHBoxLayout()
        self.filter_start = QDateEdit()
        self.filter_start.setCalendarPopup(True)
        self.filter_start.setDate(QDate.currentDate().addDays(-30))
        
        self.filter_end = QDateEdit()
        self.filter_end.setCalendarPopup(True)
        self.filter_end.setDate(QDate.currentDate())
        
        self.filter_cat = QComboBox()
        self.filter_cat.addItem("All Categories", None)
        self.filter_cat.addItems(["Rent", "Utilities", "Payroll", "Supplies", "Maintenance", "Other"])
        
        filter_btn = QPushButton("Apply Filter")
        filter_btn.clicked.connect(self.refresh_data)
        
        toolbar.addWidget(QLabel("From:"))
        toolbar.addWidget(self.filter_start)
        toolbar.addWidget(QLabel("To:"))
        toolbar.addWidget(self.filter_end)
        toolbar.addWidget(self.filter_cat)
        toolbar.addWidget(filter_btn)
        toolbar.addStretch()
        right_layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Category", "Description", "Amount", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        right_layout.addWidget(self.table)
        
        footer = QHBoxLayout()
        self.total_label = QLabel("Total: 0 Ks")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        void_btn = QPushButton("Void Selected Expense")
        void_btn.setProperty("class", "danger")
        void_btn.clicked.connect(self._void_expense)
        
        footer.addWidget(void_btn)
        footer.addStretch()
        footer.addWidget(self.total_label)
        right_layout.addLayout(footer)
        
        content_layout.addWidget(right_panel)

    def refresh_data(self):
        try:
            start = self.filter_start.date().toString("yyyy-MM-dd")
            end = self.filter_end.date().toString("yyyy-MM-dd")
            cat = self.filter_cat.currentData()
            
            # include_voided=True so we see voided ones
            expenses = self.expense_service.list_expenses(start, end, cat, include_voided=True)
            
            self.table.setRowCount(len(expenses))
            total = 0
            for i, e in enumerate(expenses):
                self.table.setItem(i, 0, QTableWidgetItem(str(e['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(e['date']))
                self.table.setItem(i, 2, QTableWidgetItem(e['category']))
                self.table.setItem(i, 3, QTableWidgetItem(e['description']))
                
                amt_item = QTableWidgetItem(f"{e['amount']:,} Ks")
                if e['status'] == 'Voided':
                    amt_item.setForeground(Qt.red)
                    amt_item.setText(f"({e['amount']:,} Ks)")
                else:
                    total += e['amount']
                    
                self.table.setItem(i, 4, amt_item)
                
                stat_item = QTableWidgetItem(e['status'])
                if e['status'] == 'Voided':
                    stat_item.setForeground(Qt.red)
                self.table.setItem(i, 5, stat_item)
                
            self.total_label.setText(f"Total: {total:,} Ks")
        except Exception:
            pass

    def _save_expense(self):
        cat = self.cat_combo.currentText().strip()
        desc = self.desc_input.text().strip()
        amt = self.amount_spin.value()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        
        if not cat:
            QMessageBox.warning(self, "Warning", "Category is required.")
            return
            
        try:
            self.expense_service.create_expense(cat, desc, amt, date)
            self.desc_input.clear()
            self.amount_spin.setValue(1)
            self.refresh_data()
            QMessageBox.information(self, "Success", "Expense recorded.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _void_expense(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select an expense to void.")
            return
            
        exp_id = int(self.table.item(row, 0).text())
        status = self.table.item(row, 5).text()
        
        if status == 'Voided':
            QMessageBox.warning(self, "Warning", "Expense is already voided.")
            return
            
        reply = QMessageBox.question(self, "Confirm Void", "Are you sure you want to void this expense? This action cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.expense_service.void_expense(exp_id)
                self.refresh_data()
                QMessageBox.information(self, "Success", "Expense voided.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
