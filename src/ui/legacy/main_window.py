from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt

from .pages.dashboard_page import DashboardPage
from .pages.sales_page import SalesPage
from .pages.products_page import ProductsPage
from .pages.inventory_page import InventoryPage
from .pages.purchases_page import PurchasesPage
from .pages.suppliers_page import SuppliersPage
from .pages.expenses_page import ExpensesPage
from .pages.reports_page import ReportsPage
from .pages.settings_page import SettingsPage

from .theme import GLOBAL_STYLE

class MainWindow(QMainWindow):
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.setWindowTitle("Medisales - Pharmacy & General Merchandise")
        self.resize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLE)

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Navigation Sidebar Container
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(220)
        sidebar_container.setStyleSheet("background-color: #0f172a;")
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Brand Area
        brand_label = QLabel("Medisales")
        brand_label.setProperty("class", "brand-title")
        sidebar_layout.addWidget(brand_label)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFocusPolicy(Qt.NoFocus)

        nav_items = [
            "Dashboard", "Sales", "Products", "Inventory", 
            "Purchases", "Suppliers", "Expenses", "Reports", "Settings"
        ]
        
        for item in nav_items:
            self.sidebar.addItem(item)
            
        sidebar_layout.addWidget(self.sidebar)

        # Main Content Area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 24, 24, 24)
        
        self.content_stack = QStackedWidget()

        # Pages
        self.pages = {
            "Dashboard": DashboardPage(self.services),
            "Sales": SalesPage(self.services),
            "Products": ProductsPage(self.services),
            "Inventory": InventoryPage(self.services),
            "Purchases": PurchasesPage(self.services),
            "Suppliers": SuppliersPage(self.services),
            "Expenses": ExpensesPage(self.services),
            "Reports": ReportsPage(self.services),
            "Settings": SettingsPage(self.services)
        }

        for item in nav_items:
            self.content_stack.addWidget(self.pages[item])

        content_layout.addWidget(self.content_stack)

        main_layout.addWidget(sidebar_container)
        main_layout.addWidget(content_container)

        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.sidebar.currentRowChanged.connect(self._on_page_changed)
        
        self.sidebar.setCurrentRow(0)

    def _on_page_changed(self, index):
        # Refresh the data of the newly selected page
        nav_items = [
            "Dashboard", "Sales", "Products", "Inventory", 
            "Purchases", "Suppliers", "Expenses", "Reports", "Settings"
        ]
        page_name = nav_items[index]
        if hasattr(self.pages[page_name], 'refresh_data'):
            self.pages[page_name].refresh_data()
