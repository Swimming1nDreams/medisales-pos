from datetime import datetime
from typing import Dict, Any, List
import sqlite3

class FinanceService:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_today_summary(self) -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_summary(today, today)

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        return self.get_summary(date, date)

    def get_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        conn = self.db.get_connection()
        
        # 1. Total sales revenue and COGS
        # We need to join sales and sale_items. But wait, sales table has date_time (YYYY-MM-DD HH:MM:SS)
        # So we need to match date prefix.
        
        sales_query = '''
            SELECT 
                COALESCE(SUM(si.line_total), 0) as total_revenue,
                COALESCE(SUM(si.total_cost), 0) as total_cogs
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            WHERE s.status = 'Completed'
              AND substr(s.date_time, 1, 10) >= ?
              AND substr(s.date_time, 1, 10) <= ?
        '''
        sales_data = conn.execute(sales_query, (start_date, end_date)).fetchone()
        
        total_revenue = sales_data['total_revenue'] or 0
        total_cogs = sales_data['total_cogs'] or 0
        gross_profit = total_revenue - total_cogs

        # 2. Operating expenses
        expenses_query = '''
            SELECT SUM(amount) as total_expenses
            FROM expenses
            WHERE status = 'Completed'
              AND date >= ? 
              AND date <= ?
        '''
        expenses_data = conn.execute(expenses_query, (start_date, end_date)).fetchone()
        operating_expenses = expenses_data['total_expenses'] or 0
        
        net_operating_profit = gross_profit - operating_expenses

        # 3. Supplier payments made during the selected period
        payments_query = '''
            SELECT SUM(total_amount) as total_payments
            FROM supplier_payments
            WHERE date >= ? 
              AND date <= ?
        '''
        payments_data = conn.execute(payments_query, (start_date, end_date)).fetchone()
        supplier_payments = payments_data['total_payments'] or 0

        # 4. Purchases recorded during the selected period
        purchases_query = '''
            SELECT SUM(total_amount) as total_purchases
            FROM purchases
            WHERE status = 'Completed'
              AND date >= ? 
              AND date <= ?
        '''
        purchases_data = conn.execute(purchases_query, (start_date, end_date)).fetchone()
        total_purchases = purchases_data['total_purchases'] or 0

        # 5. Outstanding supplier balances (Total across all time? The prompt asks for "Outstanding supplier balances", 
        # usually this is a point-in-time or current total. I'll provide the current total outstanding balance)
        outstanding_query = '''
            SELECT SUM(total_amount - amount_paid) as total_outstanding
            FROM purchases
            WHERE status = 'Completed'
        '''
        outstanding_data = conn.execute(outstanding_query).fetchone()
        outstanding_balances = outstanding_data['total_outstanding'] or 0

        # 6. Expense totals grouped by category
        category_query = '''
            SELECT category, SUM(amount) as category_total
            FROM expenses
            WHERE status = 'Completed'
              AND date >= ? 
              AND date <= ?
            GROUP BY category
            ORDER BY category_total DESC
        '''
        category_rows = conn.execute(category_query, (start_date, end_date)).fetchall()
        expenses_by_category = {row['category']: row['category_total'] for row in category_rows}

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_sales_revenue": total_revenue,
            "cost_of_goods_sold": total_cogs,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expenses,
            "net_operating_profit": net_operating_profit,
            "supplier_payments_made": supplier_payments,
            "purchases_recorded": total_purchases,
            "total_outstanding_supplier_balances": outstanding_balances,
            "expenses_by_category": expenses_by_category
        }
