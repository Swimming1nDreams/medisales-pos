import json
from PySide6.QtCore import QObject, Slot, Signal

class FrontendBridge(QObject):
    # Signals for pushing updates from Python to JS
    dataChanged = Signal(str) # e.g. "dashboard", "products", "sales"

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.services = services
        self.parent_window = parent

    def _success(self, data=None):
        return json.dumps({"status": "success", "data": data})

    def _error(self, message):
        return json.dumps({"status": "error", "message": str(message)})

    # --- Dashboard ---
    @Slot(result=str)
    def get_dashboard_summary(self):
        try:
            summary = self.services['dashboard_service'].get_dashboard_summary()
            return self._success(summary)
        except Exception as e:
            return self._error(e)

    # --- Sales ---
    @Slot(str, str, float, result=str)
    @Slot(str, str, float, float, str, str, result=str)
    def create_sale(self, reference, items_json, amount_received, discount_amount=0, payment_type="cash", customer_id=""):
        try:
            items = json.loads(items_json)
            # items: [{'product_id': int, 'quantity': int, 'unit_price': float}]
            cid = int(customer_id) if customer_id and str(customer_id).isdigit() else None
            sale_id = self.services['sales_service'].create_sale(
                reference, 
                items, 
                int(amount_received),
                discount_amount=int(discount_amount),
                payment_type=payment_type,
                customer_id=cid
            )
            self.dataChanged.emit("dashboard")
            self.dataChanged.emit("sales")
            self.dataChanged.emit("inventory")
            if cid:
                self.dataChanged.emit("customers")
            return self._success({"sale_id": sale_id})
        except Exception as e:
            return self._error(e)

    @Slot(int, str, result=str)
    def void_sale(self, sale_id, reason=""):
        try:
            self.services['sales_service'].void_sale(sale_id)
            self.dataChanged.emit("dashboard")
            self.dataChanged.emit("sales")
            self.dataChanged.emit("inventory")
            return self._success()
        except Exception as e:
            return self._error(e)

    @Slot(str, str, result=str)
    def get_sales(self, start_date, end_date):
        try:
            sales = self.services['report_service'].get_sales(start_date, end_date)
            return self._success(sales)
        except Exception as e:
            return self._error(e)

    # --- Products ---
    @Slot(result=str)
    def list_products(self):
        try:
            products = self.services['product_service'].list_products(include_inactive=True)
            return self._success(products)
        except Exception as e:
            return self._error(e)

    @Slot(result=str)
    def list_categories(self):
        try:
            cats = self.services['product_service'].list_categories()
            return self._success(cats)
        except Exception as e:
            return self._error(e)

    @Slot(str, result=str)
    def create_category(self, name):
        try:
            cat_id = self.services['product_service'].create_category(name)
            self.dataChanged.emit("products")
            return self._success({"category_id": cat_id})
        except Exception as e:
            return self._error(e)

    @Slot(str, int, str, float, int, bool, result=str)
    @Slot(str, int, str, float, int, bool, str, result=str)
    def create_product(self, name, category_id, unit_measure, selling_price, min_stock, is_medicine, packagings_json="[]"):
        try:
            packagings = json.loads(packagings_json) if packagings_json else []
            pid = self.services['product_service'].create_product(
                name, category_id, unit_measure, selling_price, min_stock, is_medicine, packagings=packagings
            )
            self.dataChanged.emit("products")
            return self._success({"product_id": pid})
        except Exception as e:
            return self._error(e)

    @Slot(int, str, int, str, float, int, bool, result=str)
    @Slot(int, str, int, str, float, int, bool, str, result=str)
    def update_product(self, product_id, name, category_id, unit_measure, selling_price, min_stock, is_active, packagings_json="[]"):
        try:
            packagings = json.loads(packagings_json) if packagings_json else []
            self.services['product_service'].update_product(
                product_id, name, category_id, unit_measure, selling_price, min_stock, is_active, packagings=packagings
            )
            self.dataChanged.emit("products")
            return self._success()
        except Exception as e:
            return self._error(e)

    @Slot(int, str, result=str)
    def set_product_packagings(self, product_id, packagings_json):
        try:
            packagings = json.loads(packagings_json) if packagings_json else []
            self.services['product_service'].set_product_packagings(product_id, packagings)
            self.dataChanged.emit("products")
            return self._success()
        except Exception as e:
            return self._error(e)

    @Slot(int, result=str)
    def get_product_packagings(self, product_id):
        try:
            pkgs = self.services['product_service'].get_product_packagings(product_id)
            return self._success(pkgs)
        except Exception as e:
            return self._error(e)

    # --- Inventory ---
    @Slot(result=str)
    def get_current_stock(self):
        try:
            stock = self.services['report_service'].get_current_stock()
            return self._success(stock)
        except Exception as e:
            return self._error(e)

    @Slot(str, result=str)
    def get_medicine_batches_report(self, filter_type):
        try:
            batches = self.services['report_service'].get_medicine_batches_report(filter_type)
            return self._success(batches)
        except Exception as e:
            return self._error(e)

    @Slot(int, result=str)
    def get_sellable_medicine_batches(self, product_id):
        try:
            batches = self.services['inventory_service'].get_sellable_medicine_batches(product_id)
            return self._success(batches)
        except Exception as e:
            return self._error(e)

    # --- Suppliers ---
    @Slot(result=str)
    def list_suppliers(self):
        try:
            supps = self.services['supplier_service'].list_suppliers(include_inactive=True)
            return self._success(supps)
        except Exception as e:
            return self._error(e)

    @Slot(str, str, str, result=str)
    def create_supplier(self, name, phone, address):
        try:
            sid = self.services['supplier_service'].create_supplier(name, phone, address)
            self.dataChanged.emit("suppliers")
            return self._success({"supplier_id": sid})
        except Exception as e:
            return self._error(e)

    @Slot(int, str, str, str, bool, result=str)
    def update_supplier(self, supplier_id, name, phone, address, is_active):
        try:
            self.services['supplier_service'].update_supplier(supplier_id, name, phone, address, is_active)
            self.dataChanged.emit("suppliers")
            return self._success()
        except Exception as e:
            return self._error(e)

    @Slot(result=str)
    def get_supplier_balances(self):
        try:
            bals = self.services['report_service'].get_supplier_balances()
            return self._success(bals)
        except Exception as e:
            return self._error(e)

    @Slot(int, result=str)
    def get_outstanding_purchases(self, supplier_id):
        try:
            conn = self.services['report_service'].db.get_connection()
            rows = conn.execute('''
                SELECT id, reference, total_amount, amount_paid 
                FROM purchases 
                WHERE supplier_id = ? AND status = 'Completed' AND total_amount > amount_paid
                ORDER BY date ASC
            ''', (supplier_id,)).fetchall()
            return self._success([dict(r) for r in rows])
        except Exception as e:
            return self._error(e)

    # --- Customers & Credit Ledger ---
    @Slot(result=str)
    def list_customers(self):
        try:
            custs = self.services['customer_service'].list_customers(include_inactive=True)
            return self._success(custs)
        except Exception as e:
            return self._error(e)

    @Slot(str, str, str, str, result=str)
    def create_customer(self, name, phone, address, notes):
        try:
            cid = self.services['customer_service'].create_customer(name, phone, address, notes)
            self.dataChanged.emit("customers")
            return self._success({"customer_id": cid})
        except Exception as e:
            return self._error(e)

    @Slot(int, str, str, str, str, bool, result=str)
    def update_customer(self, customer_id, name, phone, address, notes, is_active):
        try:
            self.services['customer_service'].update_customer(customer_id, name, phone, address, notes, is_active)
            self.dataChanged.emit("customers")
            return self._success()
        except Exception as e:
            return self._error(e)

    @Slot(result=str)
    def get_customer_balances(self):
        try:
            bals = self.services['customer_service'].get_customer_balances()
            return self._success(bals)
        except Exception as e:
            return self._error(e)

    @Slot(int, float, str, result=str)
    def record_customer_payment(self, customer_id, amount, notes=""):
        try:
            ref = self.services['customer_service'].record_debt_repayment(customer_id, int(amount), notes)
            self.dataChanged.emit("customers")
            self.dataChanged.emit("dashboard")
            return self._success({"reference": ref})
        except Exception as e:
            return self._error(e)

    @Slot(int, result=str)
    def get_customer_statement(self, customer_id):
        try:
            stmt = self.services['customer_service'].get_customer_statement(customer_id)
            return self._success(stmt)
        except Exception as e:
            return self._error(e)

    # --- Purchases ---
    @Slot(str, str, result=str)
    def get_purchases(self, start_date, end_date):
        try:
            purchases = self.services['report_service'].get_purchases(start_date, end_date)
            return self._success(purchases)
        except Exception as e:
            return self._error(e)

    @Slot(str, int, str, str, result=str)
    def create_purchase(self, reference, supplier_id, date, items_json):
        try:
            items = json.loads(items_json)
            # items: [{'product_id': int, 'quantity': int, 'unit_cost': float, 'batch_number': str|None, 'expiry_date': str|None}]
            pid = self.services['purchase_service'].create_purchase(reference, supplier_id, date, items)
            self.dataChanged.emit("purchases")
            self.dataChanged.emit("inventory")
            self.dataChanged.emit("suppliers")
            return self._success({"purchase_id": pid})
        except Exception as e:
            return self._error(e)

    @Slot(str, int, str, float, str, str, result=str)
    def record_payment(self, reference, supplier_id, date, amount, allocations_json, notes):
        try:
            allocations = json.loads(allocations_json)
            # allocations: [{'purchase_id': int, 'allocated_amount': float}]
            self.services['purchase_service'].record_payment(reference, supplier_id, date, amount, allocations, notes)
            self.dataChanged.emit("purchases")
            self.dataChanged.emit("suppliers")
            return self._success()
        except Exception as e:
            return self._error(e)

    # --- Expenses ---
    @Slot(str, str, result=str)
    def get_expenses(self, start_date, end_date):
        try:
            expenses = self.services['expense_service'].list_expenses(start_date, end_date, include_voided=True)
            return self._success(expenses)
        except Exception as e:
            return self._error(e)
            
    @Slot(str, str, float, str, result=str)
    def record_expense(self, date, category, amount, description):
        try:
            eid = self.services['expense_service'].create_expense(category, description, int(amount), date)
            self.dataChanged.emit("expenses")
            self.dataChanged.emit("dashboard")
            return self._success({"expense_id": eid})
        except Exception as e:
            return self._error(e)

    @Slot(int, str, result=str)
    def void_expense(self, expense_id, reason):
        try:
            self.services['expense_service'].void_expense(expense_id)
            self.dataChanged.emit("expenses")
            self.dataChanged.emit("dashboard")
            return self._success()
        except Exception as e:
            return self._error(e)

    # --- Reports ---
    @Slot(str, str, result=str)
    def get_sales_summary(self, start_date, end_date):
        try:
            sum = self.services['report_service'].get_sales_summary(start_date, end_date)
            return self._success(sum)
        except Exception as e:
            return self._error(e)

    @Slot(str, str, result=str)
    def get_sales_by_product(self, start_date, end_date):
        try:
            res = self.services['report_service'].get_sales_by_product(start_date, end_date)
            return self._success(res)
        except Exception as e:
            return self._error(e)
            
    @Slot(str, str, result=str)
    def get_sales_by_category(self, start_date, end_date):
        try:
            res = self.services['report_service'].get_sales_by_category(start_date, end_date)
            return self._success(res)
        except Exception as e:
            return self._error(e)

    @Slot(str, str, result=str)
    def get_expenses_by_category(self, start_date, end_date):
        try:
            res = self.services['report_service'].get_expenses_by_category(start_date, end_date)
            return self._success(res)
        except Exception as e:
            return self._error(e)

    # --- Settings / Backup & Restore ---
    @Slot(result=str)
    def get_database_info(self):
        try:
            import os
            db_manager = self.services['db_manager']
            db_path = os.path.abspath(db_manager.db_path)
            size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            return self._success({
                "db_path": db_path,
                "size_bytes": size_bytes
            })
        except Exception as e:
            return self._error(e)

    @Slot(result=str)
    def backup_database(self):
        try:
            import os
            from datetime import datetime
            from PySide6.QtWidgets import QFileDialog, QApplication

            parent = QApplication.activeWindow()
            default_name = f"medisales_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Save Medisales Database Backup",
                default_name,
                "SQLite Database (*.db);;All Files (*)"
            )
            if not file_path:
                return self._success({"cancelled": True})

            db_manager = self.services['db_manager']
            db_manager.backup_to_file(file_path)

            return self._success({
                "cancelled": False,
                "file_path": file_path,
                "message": f"Database successfully backed up to:\n{file_path}"
            })
        except Exception as e:
            return self._error(f"Failed to backup database: {str(e)}")

    @Slot(result=str)
    def restore_database(self):
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication

            parent = QApplication.activeWindow()
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Select Medisales Backup File to Restore",
                "",
                "SQLite Database (*.db);;All Files (*)"
            )
            if not file_path:
                return self._success({"cancelled": True})

            # Explicit confirmation before restoring
            reply = QMessageBox.warning(
                parent,
                "Confirm Database Restore",
                "Restoring a backup will overwrite your current live database.\n\n"
                "A safety backup of your current database will be created automatically before restoring.\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return self._success({"cancelled": True})

            db_manager = self.services['db_manager']
            safety_backup = db_manager.restore_from_file(file_path)

            # Emit update signals for all views
            self.dataChanged.emit("dashboard")
            self.dataChanged.emit("sales")
            self.dataChanged.emit("inventory")
            self.dataChanged.emit("purchases")
            self.dataChanged.emit("suppliers")
            self.dataChanged.emit("expenses")
            self.dataChanged.emit("products")
            self.dataChanged.emit("reports")

            return self._success({
                "cancelled": False,
                "file_path": file_path,
                "safety_backup": safety_backup,
                "message": f"Database successfully restored from {file_path}.\nA safety copy of your previous data was saved to:\n{safety_backup}"
            })
        except Exception as e:
            return self._error(f"Failed to restore database: {str(e)}")

    # --- Language & Localization ---
    @Slot(result=str)
    def get_language(self):
        try:
            conn = self.services['db_manager'].get_connection()
            row = conn.execute("SELECT value FROM settings WHERE key = 'language'").fetchone()
            lang = row['value'] if row and row['value'] else 'en'
            return self._success(lang)
        except Exception as e:
            return self._error(e)

    @Slot(str, result=str)
    def set_language(self, lang):
        try:
            if lang not in ('en', 'my'):
                lang = 'en'
            with self.services['db_manager'].transaction() as tx:
                tx.execute("""
                    INSERT INTO settings (key, value) VALUES ('language', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (lang,))
            if self.parent_window and hasattr(self.parent_window, 'update_language_title'):
                self.parent_window.update_language_title(lang)
            return self._success(lang)
        except Exception as e:
            return self._error(e)

    # --- Cash Reconciliation ---
    @Slot(str, result=str)
    def save_cash_reconciliation(self, recon_json):
        try:
            data = json.loads(recon_json)
            result = self.services['reconciliation_service'].save_cash_reconciliation(data)
            return self._success(result)
        except Exception as e:
            return self._error(e)

    @Slot(str, result=str)
    def get_cash_reconciliation(self, date_str=""):
        try:
            result = self.services['reconciliation_service'].get_cash_reconciliation(date_str or None)
            return self._success(result)
        except Exception as e:
            return self._error(e)

    # --- Excel Export Helper & Slots ---
    def _export_to_excel_dialog(self, default_filename: str, export_fn: str, *args):
        try:
            import os
            from PySide6.QtWidgets import QFileDialog, QApplication

            parent = QApplication.activeWindow()
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Save Say Mahar Excel Export",
                default_filename,
                "Excel Workbook (*.xlsx);;All Files (*)"
            )
            if not file_path:
                return self._success({"cancelled": True})

            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"

            if 'export_service' not in self.services:
                from src.services.export_service import ExportService
                self.services['export_service'] = ExportService(self.services)

            export_service = self.services['export_service']
            method = getattr(export_service, export_fn)
            saved_path = method(file_path, *args)

            return self._success({
                "cancelled": False,
                "file_path": saved_path,
                "message": f"Spreadsheet successfully exported to:\n{saved_path}"
            })
        except PermissionError:
            return self._error("Permission Denied: The destination file may be currently open in another program (e.g. Microsoft Excel). Please close it and try again.")
        except Exception as e:
            return self._error(f"Failed to export Excel file: {str(e)}")

    @Slot(str, str, result=str)
    def export_sales_excel(self, start_date="", end_date=""):
        from datetime import datetime
        name = f"medisales_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_sales', start_date or None, end_date or None)

    @Slot(result=str)
    def export_products_excel(self):
        from datetime import datetime
        name = f"medisales_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_products')

    @Slot(result=str)
    def export_inventory_valuation_excel(self):
        from datetime import datetime
        name = f"medisales_inventory_valuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_inventory_valuation')

    @Slot(str, result=str)
    def export_medicine_batches_excel(self, filter_type="all"):
        from datetime import datetime
        name = f"medisales_medicine_batches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_medicine_batches', filter_type)

    @Slot(str, str, result=str)
    def export_purchases_excel(self, start_date="", end_date=""):
        from datetime import datetime
        name = f"medisales_purchases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_purchases', start_date or None, end_date or None)

    @Slot(result=str)
    def export_suppliers_excel(self):
        from datetime import datetime
        name = f"medisales_suppliers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_suppliers')

    @Slot(str, str, result=str)
    def export_expenses_excel(self, start_date="", end_date=""):
        from datetime import datetime
        name = f"medisales_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_expenses', start_date or None, end_date or None)

    @Slot(str, str, result=str)
    def export_financial_report_excel(self, start_date, end_date):
        from datetime import datetime
        name = f"medisales_financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._export_to_excel_dialog(name, 'export_financial_report', start_date, end_date)

