from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class BasePlaceholderPage(QWidget):
    def __init__(self, title, services):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(f"{title} Page\n(Under Construction)")
        label.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        layout.addWidget(label)
        layout.addStretch()

class ProductsPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Products", services)

class InventoryPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Inventory", services)

class PurchasesPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Purchases", services)

class SuppliersPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Suppliers", services)

class ExpensesPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Expenses", services)

class ReportsPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Reports", services)

class SettingsPage(BasePlaceholderPage):
    def __init__(self, services): super().__init__("Settings", services)
