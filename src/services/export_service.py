import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExportService:
    """
    Authoritative Excel (.xlsx) export service for Medisales.
    Generates genuine formatted spreadsheets using openpyxl, querying
    authoritative service layers and strictly preserving accounting rules.
    """

    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.db = services['db_manager']
        self.report_service = services.get('report_service')
        self.finance_service = services.get('finance_service')
        self.product_service = services.get('product_service')
        self.sales_service = services.get('sales_service')
        self.purchase_service = services.get('purchase_service')
        self.supplier_service = services.get('supplier_service')
        self.expense_service = services.get('expense_service')

        # Design Styles
        self.font_title = Font(name="Calibri", size=15, bold=True, color="0F172A")
        self.font_subtitle = Font(name="Calibri", size=10, italic=True, color="475569")
        self.font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        self.font_bold = Font(name="Calibri", size=11, bold=True, color="0F172A")
        self.font_regular = Font(name="Calibri", size=11, color="1E293B")
        self.font_muted = Font(name="Calibri", size=10, italic=True, color="64748B")

        self.fill_header_teal = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
        self.fill_header_slate = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        self.fill_summary = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        self.fill_alt_row = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        self.thin_border_side = Side(style='thin', color="CBD5E1")
        self.double_border_side = Side(style='double', color="0F172A")
        self.thick_border_side = Side(style='medium', color="0F766E")

        self.cell_border = Border(
            left=self.thin_border_side,
            right=self.thin_border_side,
            top=self.thin_border_side,
            bottom=self.thin_border_side
        )
        self.summary_border = Border(
            top=self.thin_border_side,
            bottom=self.double_border_side
        )

        self.align_center = Alignment(horizontal="center", vertical="center")
        self.align_right = Alignment(horizontal="right", vertical="center")
        self.align_left = Alignment(horizontal="left", vertical="center")

    def _apply_sheet_styling(self, ws, max_col: int, start_row: int, end_row: int, num_cols_money: List[int] = None, num_cols_qty: List[int] = None, center_cols: List[int] = None):
        """Applies readable borders, alignments, and column auto-widths."""
        num_cols_money = num_cols_money or []
        num_cols_qty = num_cols_qty or []
        center_cols = center_cols or []

        for row in range(start_row, end_row + 1):
            is_alt = (row % 2 == 0)
            for col in range(1, max_col + 1):
                cell = ws.cell(row=row, column=col)
                cell.font = self.font_regular
                cell.border = self.cell_border
                if is_alt and not cell.fill.start_color.rgb:
                    cell.fill = self.fill_alt_row

                if col in num_cols_money:
                    cell.number_format = '#,##0'
                    cell.alignment = self.align_right
                elif col in num_cols_qty:
                    cell.number_format = '#,##0'
                    cell.alignment = self.align_right
                elif col in center_cols:
                    cell.alignment = self.align_center
                else:
                    cell.alignment = self.align_left

        # Adjust column widths
        for col in range(1, max_col + 1):
            col_letter = get_column_letter(col)
            max_len = 0
            for row in range(start_row - 1, end_row + 1):
                val = ws.cell(row=row, column=col).value
                if val is not None:
                    val_str = str(val)
                    if len(val_str) > max_len:
                        max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 13)

    def _write_title_block(self, ws, title: str, subtitle: str, max_col: int):
        ws.cell(row=1, column=1, value="Say Mahar Pharmacy & Retail Management System").font = self.font_subtitle
        ws.cell(row=2, column=1, value=title).font = self.font_title
        ws.cell(row=3, column=1, value=f"{subtitle}  •  Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").font = self.font_subtitle
        ws.row_dimensions[2].height = 24
        ws.row_dimensions[3].height = 18

    def _write_header_row(self, ws, row_idx: int, headers: List[str], fill=None):
        fill = fill or self.fill_header_teal
        ws.row_dimensions[row_idx].height = 26
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = self.font_header
            cell.fill = fill
            cell.alignment = self.align_center
            cell.border = self.cell_border

    # =========================================================================
    # 1. SALES TRANSACTIONS EXPORT
    # =========================================================================
    def export_sales(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sales Transactions"

        period_desc = f"Period: {start_date} to {end_date}" if start_date and end_date else "All Recorded Sales"
        self._write_title_block(ws, "Sales Transactions Report", period_desc, 7)

        headers = ["Invoice #", "Date & Time", "Status", "Items Count", "Total Amount (Ks)", "Amount Tendered (Ks)", "Change Due (Ks)"]
        self._write_header_row(ws, 5, headers, self.fill_header_teal)

        sales = self.report_service.get_sales(start_date, end_date, include_voided=True)

        current_row = 6
        completed_count = 0
        completed_rev = 0
        voided_count = 0
        voided_amount = 0

        for s in sales:
            is_void = (s['status'] == 'Voided')
            ws.cell(row=current_row, column=1, value=s.get('reference', ''))
            ws.cell(row=current_row, column=2, value=s.get('date_time', ''))
            ws.cell(row=current_row, column=3, value=s.get('status', 'Completed'))
            ws.cell(row=current_row, column=4, value=int(s.get('items_count', 0)))
            ws.cell(row=current_row, column=5, value=int(s.get('total_amount', 0)))
            ws.cell(row=current_row, column=6, value=int(s.get('amount_received', 0)))
            ws.cell(row=current_row, column=7, value=int(s.get('change_given', 0)))

            if is_void:
                voided_count += 1
                voided_amount += int(s.get('total_amount', 0))
            else:
                completed_count += 1
                completed_rev += int(s.get('total_amount', 0))

            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if sales:
            self._apply_sheet_styling(ws, 7, 6, end_data_row, num_cols_money=[5, 6, 7], num_cols_qty=[4], center_cols=[1, 2, 3])

        # Summary Section
        summary_row = current_row + 1
        ws.cell(row=summary_row, column=3, value="Total Completed Sales:").font = self.font_bold
        cell_c_rev = ws.cell(row=summary_row, column=5, value=completed_rev)
        cell_c_rev.font = self.font_bold
        cell_c_rev.number_format = '#,##0'
        cell_c_rev.border = self.summary_border

        summary_row2 = summary_row + 1
        ws.cell(row=summary_row2, column=3, value="Voided Sales (Excluded):").font = self.font_muted
        cell_v_rev = ws.cell(row=summary_row2, column=5, value=voided_amount)
        cell_v_rev.font = self.font_muted
        cell_v_rev.number_format = '#,##0'

        summary_row3 = summary_row2 + 1
        note_cell = ws.cell(row=summary_row3, column=1, value=f"* Accounting Note: Completed sales revenue = {completed_rev:,} Ks ({completed_count} receipts). Voided sales ({voided_count} receipts totaling {voided_amount:,} Ks) are strictly excluded from net sales.")
        note_cell.font = self.font_muted

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 2. PRODUCTS CATALOG EXPORT
    # =========================================================================
    def export_products(self, file_path: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products Catalog"

        self._write_title_block(ws, "Master Products Catalog", "All Active & Inactive Inventory SKUs", 10)

        headers = ["Product ID", "Product Name", "Category", "Unit Measure", "Selling Price (Ks)", "Current Stock", "Inventory Value (Ks)", "Min Stock Level", "Classification", "Status"]
        self._write_header_row(ws, 5, headers, self.fill_header_teal)

        products = self.product_service.list_products(include_inactive=True)

        current_row = 6
        total_val = 0
        for p in products:
            val = int(p.get('inventory_value', 0) or 0)
            total_val += val
            ws.cell(row=current_row, column=1, value=p.get('id'))
            ws.cell(row=current_row, column=2, value=p.get('name', ''))
            ws.cell(row=current_row, column=3, value=p.get('category_name', 'General'))
            ws.cell(row=current_row, column=4, value=p.get('unit_measure', ''))
            ws.cell(row=current_row, column=5, value=int(p.get('selling_price', 0)))
            ws.cell(row=current_row, column=6, value=int(p.get('current_stock', 0)))
            ws.cell(row=current_row, column=7, value=val)
            ws.cell(row=current_row, column=8, value=int(p.get('min_stock_level', 0)))
            ws.cell(row=current_row, column=9, value="Medicine" if p.get('is_medicine') else "General Merchandise")
            ws.cell(row=current_row, column=10, value="Active" if p.get('is_active') else "Inactive")
            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if products:
            self._apply_sheet_styling(ws, 10, 6, end_data_row, num_cols_money=[5, 7], num_cols_qty=[6, 8], center_cols=[1, 4, 9, 10])

        sum_row = current_row + 1
        ws.cell(row=sum_row, column=4, value="Total Inventory Valuation:").font = self.font_bold
        val_cell = ws.cell(row=sum_row, column=7, value=total_val)
        val_cell.font = self.font_bold
        val_cell.number_format = '#,##0'
        val_cell.border = self.summary_border

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 3. INVENTORY & VALUATION EXPORT
    # =========================================================================
    def export_inventory_valuation(self, file_path: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventory Valuation"

        self._write_title_block(ws, "Stock on Hand & Inventory Valuation", "Active Products Stock & Valuation (FEFO for Medicine, WAC for General Goods)", 9)

        headers = ["Product ID", "Product Name", "Category", "Type", "Stock on Hand", "Unit Measure", "Inventory Value (Ks)", "Min Stock Level", "Stock Alert"]
        self._write_header_row(ws, 5, headers, self.fill_header_slate)

        stock_items = self.report_service.get_current_stock()

        current_row = 6
        total_value = 0
        for item in stock_items:
            stock = int(item.get('current_stock', 0))
            min_lvl = int(item.get('min_stock_level', 0))
            val = int(item.get('inventory_value', 0) or 0)
            total_value += val

            alert = "Normal"
            if stock == 0:
                alert = "Out of Stock"
            elif stock <= min_lvl:
                alert = "Low Stock"

            ws.cell(row=current_row, column=1, value=item.get('id'))
            ws.cell(row=current_row, column=2, value=item.get('name', ''))
            ws.cell(row=current_row, column=3, value=item.get('category_name', 'General'))
            ws.cell(row=current_row, column=4, value="Medicine" if item.get('is_medicine') else "General Goods")
            ws.cell(row=current_row, column=5, value=stock)
            ws.cell(row=current_row, column=6, value=item.get('unit_measure', ''))
            ws.cell(row=current_row, column=7, value=val)
            ws.cell(row=current_row, column=8, value=min_lvl)
            ws.cell(row=current_row, column=9, value=alert)
            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if stock_items:
            self._apply_sheet_styling(ws, 9, 6, end_data_row, num_cols_money=[7], num_cols_qty=[5, 8], center_cols=[1, 4, 6, 9])

        sum_row = current_row + 1
        ws.cell(row=sum_row, column=4, value="Total Stock Value (Ks):").font = self.font_bold
        sum_cell = ws.cell(row=sum_row, column=7, value=total_value)
        sum_cell.font = self.font_bold
        sum_cell.number_format = '#,##0'
        sum_cell.border = self.summary_border

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 4. MEDICINE BATCHES & EXPIRY EXPORT
    # =========================================================================
    def export_medicine_batches(self, file_path: str, filter_type: str = 'all') -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Medicine Batches"

        self._write_title_block(ws, "Medicine Batches & Expiry Ledger", f"FEFO Tracking Filter: {filter_type.upper()}", 9)

        headers = ["Batch ID", "Product ID", "Medicine Name", "Batch Number", "Expiry Date", "Quantity on Hand", "Unit Cost (Ks)", "Batch Value (Ks)", "Expiry Status"]
        self._write_header_row(ws, 5, headers, self.fill_header_teal)

        batches = self.report_service.get_medicine_batches_report(filter_type)

        today_str = datetime.now().strftime("%Y-%m-%d")
        current_row = 6
        total_qty = 0
        total_val = 0

        for b in batches:
            qty = int(b.get('current_qty', 0))
            cost = int(b.get('unit_cost') or b.get('cost_per_unit') or 0)
            b_val = qty * cost
            total_qty += qty
            total_val += b_val

            exp = b.get('expiry_date')
            status = "Active"
            if not exp:
                status = "Unknown Expiry (Unsellable)"
            elif exp <= today_str:
                status = "Expired (Unsellable)"
            else:
                try:
                    exp_dt = datetime.strptime(exp, "%Y-%m-%d")
                    diff = (exp_dt - datetime.now()).days
                    if diff <= 90:
                        status = f"Expiring Soon ({diff}d)"
                except Exception:
                    pass

            ws.cell(row=current_row, column=1, value=b.get('id'))
            ws.cell(row=current_row, column=2, value=b.get('product_id'))
            ws.cell(row=current_row, column=3, value=b.get('product_name', ''))
            ws.cell(row=current_row, column=4, value=b.get('batch_number', ''))
            ws.cell(row=current_row, column=5, value=exp or 'N/A')
            ws.cell(row=current_row, column=6, value=qty)
            ws.cell(row=current_row, column=7, value=cost)
            ws.cell(row=current_row, column=8, value=b_val)
            ws.cell(row=current_row, column=9, value=status)
            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if batches:
            self._apply_sheet_styling(ws, 9, 6, end_data_row, num_cols_money=[7, 8], num_cols_qty=[6], center_cols=[1, 2, 4, 5, 9])

        sum_row = current_row + 1
        ws.cell(row=sum_row, column=3, value="Total Medicine Batch Value:").font = self.font_bold
        qty_cell = ws.cell(row=sum_row, column=6, value=total_qty)
        qty_cell.font = self.font_bold
        qty_cell.number_format = '#,##0'
        qty_cell.border = self.summary_border

        val_cell = ws.cell(row=sum_row, column=8, value=total_val)
        val_cell.font = self.font_bold
        val_cell.number_format = '#,##0'
        val_cell.border = self.summary_border

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 5. PURCHASES EXPORT
    # =========================================================================
    def export_purchases(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Purchases"

        period_desc = f"Period: {start_date} to {end_date}" if start_date and end_date else "All Recorded Purchases"
        self._write_title_block(ws, "Procurement & Inward Purchases Report", period_desc, 8)

        headers = ["Purchase ID", "Invoice #", "Date", "Supplier", "Total Amount (Ks)", "Amount Paid (Ks)", "Outstanding (Ks)", "Status"]
        self._write_header_row(ws, 5, headers, self.fill_header_slate)

        start = start_date or "1900-01-01"
        end = end_date or "2100-12-31"
        purchases = self.report_service.get_purchases(start, end)

        current_row = 6
        tot_amount = 0
        tot_paid = 0
        tot_bal = 0

        for p in purchases:
            amt = int(p.get('total_amount', 0))
            paid = int(p.get('amount_paid', 0))
            bal = amt - paid
            tot_amount += amt
            tot_paid += paid
            tot_bal += bal

            ws.cell(row=current_row, column=1, value=p.get('id'))
            ws.cell(row=current_row, column=2, value=p.get('invoice_number', ''))
            ws.cell(row=current_row, column=3, value=p.get('date', ''))
            ws.cell(row=current_row, column=4, value=p.get('supplier_name', ''))
            ws.cell(row=current_row, column=5, value=amt)
            ws.cell(row=current_row, column=6, value=paid)
            ws.cell(row=current_row, column=7, value=bal)
            ws.cell(row=current_row, column=8, value=p.get('status', 'Completed'))
            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if purchases:
            self._apply_sheet_styling(ws, 8, 6, end_data_row, num_cols_money=[5, 6, 7], center_cols=[1, 2, 3, 8])

        sum_row = current_row + 1
        ws.cell(row=sum_row, column=4, value="Total Procurement:").font = self.font_bold
        c5 = ws.cell(row=sum_row, column=5, value=tot_amount)
        c5.font = self.font_bold
        c5.number_format = '#,##0'
        c5.border = self.summary_border

        c6 = ws.cell(row=sum_row, column=6, value=tot_paid)
        c6.font = self.font_bold
        c6.number_format = '#,##0'
        c6.border = self.summary_border

        c7 = ws.cell(row=sum_row, column=7, value=tot_bal)
        c7.font = self.font_bold
        c7.number_format = '#,##0'
        c7.border = self.summary_border

        note_row = sum_row + 2
        ws.cell(row=note_row, column=1, value="* Accounting Rule: Inventory purchases are balance sheet capital investments, not operating expenses.").font = self.font_muted

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 6. SUPPLIERS & BALANCES EXPORT
    # =========================================================================
    def export_suppliers(self, file_path: str) -> str:
        wb = openpyxl.Workbook()
        
        # Sheet 1: Suppliers & Balances
        ws1 = wb.active
        ws1.title = "Suppliers & Balances"
        self._write_title_block(ws1, "Supplier Ledger & Balances", "Vendor Accounts Payable", 7)

        headers1 = ["Supplier ID", "Supplier Name", "Phone", "Address", "Total Invoiced (Ks)", "Total Paid (Ks)", "Outstanding Balance (Ks)"]
        self._write_header_row(ws1, 5, headers1, self.fill_header_teal)

        conn = self.db.get_connection()
        suppliers = conn.execute("""
            SELECT s.id, s.name, s.phone, s.address,
                   COALESCE(SUM(p.total_amount), 0) as total_invoiced,
                   COALESCE(SUM(p.amount_paid), 0) as total_paid,
                   COALESCE(SUM(p.total_amount - p.amount_paid), 0) as outstanding_balance
            FROM suppliers s
            LEFT JOIN purchases p ON s.id = p.supplier_id AND p.status = 'Completed'
            GROUP BY s.id, s.name
            ORDER BY outstanding_balance DESC, s.name ASC
        """).fetchall()

        current_row = 6
        tot_inv = 0
        tot_paid = 0
        tot_out = 0
        for s in suppliers:
            inv = int(s['total_invoiced'] or 0)
            pd = int(s['total_paid'] or 0)
            bal = int(s['outstanding_balance'] or 0)
            tot_inv += inv
            tot_paid += pd
            tot_out += bal

            ws1.cell(row=current_row, column=1, value=s['id'])
            ws1.cell(row=current_row, column=2, value=s['name'])
            ws1.cell(row=current_row, column=3, value=s['phone'] or '')
            ws1.cell(row=current_row, column=4, value=s['address'] or '')
            ws1.cell(row=current_row, column=5, value=inv)
            ws1.cell(row=current_row, column=6, value=pd)
            ws1.cell(row=current_row, column=7, value=bal)
            current_row += 1

        end_data_row1 = max(current_row - 1, 6)
        if suppliers:
            self._apply_sheet_styling(ws1, 7, 6, end_data_row1, num_cols_money=[5, 6, 7], center_cols=[1])

        sum_row = current_row + 1
        ws1.cell(row=sum_row, column=4, value="Total Outstanding Payables:").font = self.font_bold
        c5 = ws1.cell(row=sum_row, column=5, value=tot_inv)
        c5.font = self.font_bold; c5.number_format = '#,##0'; c5.border = self.summary_border
        c6 = ws1.cell(row=sum_row, column=6, value=tot_paid)
        c6.font = self.font_bold; c6.number_format = '#,##0'; c6.border = self.summary_border
        c7 = ws1.cell(row=sum_row, column=7, value=tot_out)
        c7.font = self.font_bold; c7.number_format = '#,##0'; c7.border = self.summary_border

        # Sheet 2: Payments History
        ws2 = wb.create_sheet(title="Supplier Payments")
        self._write_title_block(ws2, "Supplier Payments Audit Log", "Debt Disbursements to Suppliers", 7)

        headers2 = ["Payment ID", "Date", "Supplier", "Total Paid (Ks)", "Allocated Amount (Ks)", "Unallocated Balance (Ks)", "Notes"]
        self._write_header_row(ws2, 5, headers2, self.fill_header_slate)

        payments = conn.execute("""
            SELECT sp.id, sp.date, s.name as supplier_name, sp.total_amount, sp.allocated_amount, sp.notes
            FROM supplier_payments sp
            JOIN suppliers s ON s.id = sp.supplier_id
            ORDER BY sp.date DESC, sp.id DESC
        """).fetchall()

        p_row = 6
        tot_pmt = 0
        for p in payments:
            amt = int(p['total_amount'] or 0)
            alloc = int(p['allocated_amount'] or 0)
            unalloc = amt - alloc
            tot_pmt += amt

            ws2.cell(row=p_row, column=1, value=p['id'])
            ws2.cell(row=p_row, column=2, value=p['date'])
            ws2.cell(row=p_row, column=3, value=p['supplier_name'])
            ws2.cell(row=p_row, column=4, value=amt)
            ws2.cell(row=p_row, column=5, value=alloc)
            ws2.cell(row=p_row, column=6, value=unalloc)
            ws2.cell(row=p_row, column=7, value=p['notes'] or '')
            p_row += 1

        end_data_row2 = max(p_row - 1, 6)
        if payments:
            self._apply_sheet_styling(ws2, 7, 6, end_data_row2, num_cols_money=[4, 5, 6], center_cols=[1, 2])

        p_sum_row = p_row + 1
        ws2.cell(row=p_sum_row, column=3, value="Total Supplier Payments:").font = self.font_bold
        p_cell = ws2.cell(row=p_sum_row, column=4, value=tot_pmt)
        p_cell.font = self.font_bold; p_cell.number_format = '#,##0'; p_cell.border = self.summary_border

        note_row2 = p_sum_row + 2
        ws2.cell(row=note_row2, column=1, value="* Accounting Rule: Supplier payments are liabilities settlement, not operating expenses.").font = self.font_muted

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 7. OPERATING EXPENSES EXPORT
    # =========================================================================
    def export_expenses(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Operating Expenses"

        period_desc = f"Period: {start_date} to {end_date}" if start_date and end_date else "All Recorded Expenses"
        self._write_title_block(ws, "Store Operating Expenses Ledger", period_desc, 6)

        headers = ["Expense ID", "Date", "Category", "Amount (Ks)", "Description", "Status"]
        self._write_header_row(ws, 5, headers, self.fill_header_slate)

        conn = self.db.get_connection()
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC, id DESC"

        expenses = conn.execute(query, params).fetchall()

        current_row = 6
        completed_tot = 0
        voided_tot = 0

        for e in expenses:
            amt = int(e['amount'] or 0)
            status = e['status'] or 'Completed'

            if status == 'Completed':
                completed_tot += amt
            else:
                voided_tot += amt

            ws.cell(row=current_row, column=1, value=e['id'])
            ws.cell(row=current_row, column=2, value=e['date'])
            ws.cell(row=current_row, column=3, value=e['category'])
            ws.cell(row=current_row, column=4, value=amt)
            ws.cell(row=current_row, column=5, value=e['description'] or '')
            ws.cell(row=current_row, column=6, value=status)
            current_row += 1

        end_data_row = max(current_row - 1, 6)
        if expenses:
            self._apply_sheet_styling(ws, 6, 6, end_data_row, num_cols_money=[4], center_cols=[1, 2, 6])

        sum_row = current_row + 1
        ws.cell(row=sum_row, column=3, value="Total Operating Expenses:").font = self.font_bold
        sum_cell = ws.cell(row=sum_row, column=4, value=completed_tot)
        sum_cell.font = self.font_bold; sum_cell.number_format = '#,##0'; sum_cell.border = self.summary_border

        sum_row2 = sum_row + 1
        ws.cell(row=sum_row2, column=3, value="Voided Expenses (Excluded):").font = self.font_muted
        v_cell = ws.cell(row=sum_row2, column=4, value=voided_tot)
        v_cell.font = self.font_muted; v_cell.number_format = '#,##0'

        note_row = sum_row2 + 2
        ws.cell(row=note_row, column=1, value="* Accounting Compliance: Supplier debt payments and merchandise purchases are strictly excluded from operating expenses.").font = self.font_muted

        wb.save(file_path)
        return file_path

    # =========================================================================
    # 8. FINANCIAL STATEMENT & SALES REPORTS EXPORT
    # =========================================================================
    def export_financial_report(self, file_path: str, start_date: str, end_date: str) -> str:
        wb = openpyxl.Workbook()

        # Sheet 1: Profit & Loss Statement
        ws1 = wb.active
        ws1.title = "Profit & Loss Statement"

        self._write_title_block(ws1, "Financial Performance & Profit Analysis", f"Reporting Period: {start_date} to {end_date}", 4)

        # Get authoritative financial summary from FinanceService
        fin = self.finance_service.get_summary(start_date, end_date)

        rev = int(fin.get('total_sales_revenue', 0))
        cogs = int(fin.get('cost_of_goods_sold', 0))
        gp = int(fin.get('gross_profit', 0))
        opex = int(fin.get('operating_expenses', 0))
        net_profit = int(fin.get('net_operating_profit', 0))
        purchases = int(fin.get('purchases_recorded', 0))
        payments = int(fin.get('supplier_payments_made', 0))
        outstanding = int(fin.get('total_outstanding_supplier_balances', 0))

        # Build formal P&L Table
        self._write_header_row(ws1, 5, ["Account Line Item", "Classification", "Amount (Ks)", "% of Revenue"], self.fill_header_teal)

        def pct(amt):
            if rev == 0:
                return "0.0%"
            return f"{(amt / rev) * 100:.1f}%"

        pnl_lines = [
            ("Sales Revenue (Completed Sales)", "Gross Inflows", rev, pct(rev), True),
            ("Cost of Goods Sold (FEFO + WAC COGS)", "Direct Product Cost", cogs, pct(cogs), False),
            ("GROSS OPERATING PROFIT", "Trading Margin", gp, pct(gp), True),
            ("", "", "", "", False),
            ("Store Operating Overheads (Itemized below)", "Operating Expenses", opex, pct(opex), False)
        ]

        curr_row = 6
        for item, cls, amt, p, is_bold in pnl_lines:
            if not item:
                curr_row += 1
                continue
            ws1.cell(row=curr_row, column=1, value=item).font = self.font_bold if is_bold else self.font_regular
            ws1.cell(row=curr_row, column=2, value=cls).font = self.font_muted
            amt_cell = ws1.cell(row=curr_row, column=3, value=amt)
            amt_cell.font = self.font_bold if is_bold else self.font_regular
            amt_cell.number_format = '#,##0'
            ws1.cell(row=curr_row, column=4, value=p).font = self.font_regular
            curr_row += 1

        # Itemized operating expenses
        cat_expenses = fin.get('expenses_by_category', {})
        for cat, c_amt in sorted(cat_expenses.items()):
            ws1.cell(row=curr_row, column=1, value=f"    • {cat}").font = self.font_regular
            ws1.cell(row=curr_row, column=2, value="Expense Category").font = self.font_muted
            c_cell = ws1.cell(row=curr_row, column=3, value=int(c_amt))
            c_cell.font = self.font_regular; c_cell.number_format = '#,##0'
            ws1.cell(row=curr_row, column=4, value=pct(c_amt)).font = self.font_regular
            curr_row += 1

        # NET OPERATING PROFIT
        curr_row += 1
        net_cell_lbl = ws1.cell(row=curr_row, column=1, value="NET OPERATING PROFIT")
        net_cell_lbl.font = self.font_bold
        ws1.cell(row=curr_row, column=2, value="Bottom Line (Gross Profit - Expenses)").font = self.font_bold
        net_cell_val = ws1.cell(row=curr_row, column=3, value=net_profit)
        net_cell_val.font = self.font_bold
        net_cell_val.number_format = '#,##0'
        net_cell_val.border = self.summary_border
        ws1.cell(row=curr_row, column=4, value=pct(net_profit)).font = self.font_bold

        # Disclosure Box
        disc_row = curr_row + 3
        ws1.cell(row=disc_row, column=1, value="Accounting Reconciliations & Non-Expense Cash Flows:").font = self.font_bold
        ws1.cell(row=disc_row + 1, column=1, value=f"1. Merchandise Purchases in Period: {purchases:,} Ks (Capitalized into inventory assets, not an operating expense)").font = self.font_muted
        ws1.cell(row=disc_row + 2, column=1, value=f"2. Supplier Payments in Period: {payments:,} Ks (Settlement of accounts payable, not an operating expense)").font = self.font_muted
        ws1.cell(row=disc_row + 3, column=1, value=f"3. Current Outstanding Supplier Balance: {outstanding:,} Ks").font = self.font_muted

        self._apply_sheet_styling(ws1, 4, 6, curr_row, num_cols_money=[3], center_cols=[4])

        # Sheet 2: Sales by Product
        ws2 = wb.create_sheet(title="Sales by Product")
        self._write_title_block(ws2, "Product Sales & Profitability Breakdown", f"Period: {start_date} to {end_date}", 6)
        headers2 = ["Product ID", "Product Name", "Quantity Sold", "Revenue (Ks)", "COGS (Ks)", "Gross Profit (Ks)"]
        self._write_header_row(ws2, 5, headers2, self.fill_header_slate)

        prod_sales = self.report_service.get_sales_by_product(start_date, end_date)
        r2 = 6
        for ps in prod_sales:
            ws2.cell(row=r2, column=1, value=ps.get('product_id'))
            ws2.cell(row=r2, column=2, value=ps.get('product_name', ''))
            ws2.cell(row=r2, column=3, value=int(ps.get('quantity_sold', 0)))
            ws2.cell(row=r2, column=4, value=int(ps.get('revenue', 0)))
            ws2.cell(row=r2, column=5, value=int(ps.get('cogs', 0)))
            ws2.cell(row=r2, column=6, value=int(ps.get('gross_profit', 0)))
            r2 += 1

        end_r2 = max(r2 - 1, 6)
        if prod_sales:
            self._apply_sheet_styling(ws2, 6, 6, end_r2, num_cols_money=[4, 5, 6], num_cols_qty=[3], center_cols=[1])

        # Sheet 3: Sales by Category
        ws3 = wb.create_sheet(title="Sales by Category")
        self._write_title_block(ws3, "Category Sales & Profitability Breakdown", f"Period: {start_date} to {end_date}", 5)
        headers3 = ["Category Name", "Quantity Sold", "Revenue (Ks)", "COGS (Ks)", "Gross Profit (Ks)"]
        self._write_header_row(ws3, 5, headers3, self.fill_header_slate)

        cat_sales = self.report_service.get_sales_by_category(start_date, end_date)
        r3 = 6
        for cs in cat_sales:
            ws3.cell(row=r3, column=1, value=cs.get('category_name', ''))
            ws3.cell(row=r3, column=2, value=int(cs.get('total_quantity', 0)))
            ws3.cell(row=r3, column=3, value=int(cs.get('revenue', 0)))
            ws3.cell(row=r3, column=4, value=int(cs.get('cogs', 0)))
            ws3.cell(row=r3, column=5, value=int(cs.get('gross_profit', 0)))
            r3 += 1

        end_r3 = max(r3 - 1, 6)
        if cat_sales:
            self._apply_sheet_styling(ws3, 5, 6, end_r3, num_cols_money=[3, 4, 5], num_cols_qty=[2])

        wb.save(file_path)
        return file_path
