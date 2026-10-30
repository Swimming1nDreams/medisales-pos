from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

class ReportsPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.report_service = services['report_service']
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Reports")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Generate financial, sales, and expense reports")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        gen_btn = QPushButton("Generate Reports")
        gen_btn.setProperty("class", "primary")
        gen_btn.clicked.connect(self.refresh_data)
        
        toolbar.addWidget(QLabel("Date Range:"))
        toolbar.addWidget(self.start_date)
        toolbar.addWidget(QLabel("to"))
        toolbar.addWidget(self.end_date)
        toolbar.addWidget(gen_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Summary Tab ---
        sum_tab = QWidget()
        sum_layout = QVBoxLayout(sum_tab)
        self.sum_label = QLabel("Loading...")
        self.sum_label.setStyleSheet("font-size: 16px; line-height: 1.5;")
        self.sum_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        sum_layout.addWidget(self.sum_label)
        sum_layout.addStretch()
        self.tabs.addTab(sum_tab, "Financial Summary")
        
        # --- Sales by Product Tab ---
        prod_tab = QWidget()
        prod_layout = QVBoxLayout(prod_tab)
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(4)
        self.prod_table.setHorizontalHeaderLabels(["Product", "Qty Sold", "Revenue", "Gross Profit"])
        self.prod_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        prod_layout.addWidget(self.prod_table)
        self.tabs.addTab(prod_tab, "Sales by Product")
        
        # --- Sales by Category Tab ---
        cat_tab = QWidget()
        cat_layout = QVBoxLayout(cat_tab)
        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(4)
        self.cat_table.setHorizontalHeaderLabels(["Category", "Qty Sold", "Revenue", "Gross Profit"])
        self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        cat_layout.addWidget(self.cat_table)
        self.tabs.addTab(cat_tab, "Sales by Category")
        
        # --- Expenses by Category Tab ---
        exp_tab = QWidget()
        exp_layout = QVBoxLayout(exp_tab)
        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(2)
        self.exp_table.setHorizontalHeaderLabels(["Category", "Total Amount"])
        self.exp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        exp_layout.addWidget(self.exp_table)
        self.tabs.addTab(exp_tab, "Expenses by Category")

    def refresh_data(self):
        try:
            s_date = self.start_date.date().toString("yyyy-MM-dd")
            e_date = self.end_date.date().toString("yyyy-MM-dd")
            
            # Financial Summary
            sales_sum = self.report_service.get_sales_summary(s_date, e_date)
            exp_sum = self.report_service.get_expenses_by_category(s_date, e_date)
            total_exp = sum(e['total_amount'] for e in exp_sum)
            
            net_op = sales_sum['gross_profit'] - total_exp
            
            summary_html = f"""
            <h3>Financial Summary ({s_date} to {e_date})</h3>
            <table cellpadding="5">
                <tr><td><b>Total Sales Revenue:</b></td><td>{sales_sum['total_revenue']:,} Ks</td></tr>
                <tr><td><b>Cost of Goods Sold:</b></td><td>{sales_sum['total_cogs']:,} Ks</td></tr>
                <tr><td><b>Gross Profit:</b></td><td>{sales_sum['gross_profit']:,} Ks</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>Operating Expenses:</b></td><td>{total_exp:,} Ks</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>Net Operating Profit:</b></td><td><b>{net_op:,} Ks</b></td></tr>
                <tr><td><b>Total Transactions:</b></td><td>{sales_sum['sales_count']}</td></tr>
            </table>
            """
            self.sum_label.setText(summary_html)
            
            # Sales by Product
            prod_sales = self.report_service.get_sales_by_product(s_date, e_date)
            self.prod_table.setRowCount(len(prod_sales))
            for i, p in enumerate(prod_sales):
                self.prod_table.setItem(i, 0, QTableWidgetItem(p['product_name']))
                self.prod_table.setItem(i, 1, QTableWidgetItem(str(p['total_quantity'])))
                self.prod_table.setItem(i, 2, QTableWidgetItem(f"{p['total_revenue']:,} Ks"))
                self.prod_table.setItem(i, 3, QTableWidgetItem(f"{p['gross_profit']:,} Ks"))
                
            # Sales by Category
            cat_sales = self.report_service.get_sales_by_category(s_date, e_date)
            self.cat_table.setRowCount(len(cat_sales))
            for i, c in enumerate(cat_sales):
                self.cat_table.setItem(i, 0, QTableWidgetItem(c['category_name']))
                self.cat_table.setItem(i, 1, QTableWidgetItem(str(c['total_quantity'])))
                self.cat_table.setItem(i, 2, QTableWidgetItem(f"{c['total_revenue']:,} Ks"))
                self.cat_table.setItem(i, 3, QTableWidgetItem(f"{c['gross_profit']:,} Ks"))
                
            # Expenses by Category
            self.exp_table.setRowCount(len(exp_sum))
            for i, e in enumerate(exp_sum):
                self.exp_table.setItem(i, 0, QTableWidgetItem(e['category']))
                self.exp_table.setItem(i, 1, QTableWidgetItem(f"{e['total_amount']:,} Ks"))
                
        except Exception:
            pass
