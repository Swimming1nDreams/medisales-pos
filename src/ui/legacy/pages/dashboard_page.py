from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt

class StatCard(QFrame):
    def __init__(self, title, value="0", color="#3498db"):
        super().__init__()
        self.setProperty("class", "card")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                border-left: 5px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748b; border: none;")
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))

class DashboardPage(QWidget):
    def __init__(self, services):
        super().__init__()
        self.dashboard_service = services['dashboard_service']
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Dashboard")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Overview of your shop's performance today")
        subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Financial Cards
        fin_label = QLabel("Today's Financials")
        fin_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 16px; margin-bottom: 8px;")
        layout.addWidget(fin_label)
        
        fin_layout = QGridLayout()
        fin_layout.setSpacing(16)
        
        self.rev_card = StatCard("Sales Revenue", "0 Ks", "#10b981") # Green
        self.sales_count_card = StatCard("Completed Sales", "0", "#0ea5e9") # Blue
        self.gp_card = StatCard("Gross Profit", "0 Ks", "#f59e0b") # Amber
        self.np_card = StatCard("Net Operating Profit", "0 Ks", "#8b5cf6") # Purple
        self.exp_card = StatCard("Operating Expenses", "0 Ks", "#ef4444") # Red
        
        fin_layout.addWidget(self.rev_card, 0, 0)
        fin_layout.addWidget(self.sales_count_card, 0, 1)
        fin_layout.addWidget(self.gp_card, 0, 2)
        fin_layout.addWidget(self.np_card, 1, 0)
        fin_layout.addWidget(self.exp_card, 1, 1)
        layout.addLayout(fin_layout)
        
        # Inventory & Warnings
        inv_label = QLabel("Current Status")
        inv_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 24px; margin-bottom: 8px;")
        layout.addWidget(inv_label)
        
        inv_layout = QGridLayout()
        inv_layout.setSpacing(16)
        
        self.inv_val_card = StatCard("Total Inventory Value", "0 Ks", "#64748b") # Slate
        self.supp_bal_card = StatCard("Supplier Outstanding", "0 Ks", "#f97316") # Orange
        self.low_stock_card = StatCard("Low Stock Warnings", "0", "#ef4444") # Red
        self.med_exp_card = StatCard("Medicine Expiry Warnings", "0", "#ef4444") # Red
        
        inv_layout.addWidget(self.inv_val_card, 0, 0)
        inv_layout.addWidget(self.supp_bal_card, 0, 1)
        inv_layout.addWidget(self.low_stock_card, 0, 2)
        inv_layout.addWidget(self.med_exp_card, 1, 0)
        layout.addLayout(inv_layout)
        
        layout.addStretch()

    def refresh_data(self):
        try:
            summary = self.dashboard_service.get_dashboard_summary()
            
            self.rev_card.set_value(f"{summary['total_sales_revenue']:,} Ks")
            self.sales_count_card.set_value(str(summary['number_of_completed_sales']))
            self.gp_card.set_value(f"{summary['gross_profit']:,} Ks")
            self.np_card.set_value(f"{summary['net_operating_profit']:,} Ks")
            self.exp_card.set_value(f"{summary['operating_expenses']:,} Ks")
            
            self.inv_val_card.set_value(f"{summary['total_inventory_value']:,} Ks")
            self.supp_bal_card.set_value(f"{summary['total_outstanding_supplier_balances']:,} Ks")
            
            self.low_stock_card.set_value(str(summary['low_stock_products_count']))
            exp_warns = summary['medicine_expired_products_count'] + summary['medicine_expiring_soon_products_count']
            self.med_exp_card.set_value(str(exp_warns))
        except Exception as e:
            print(f"Error loading dashboard: {e}")
