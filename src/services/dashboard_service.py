from datetime import datetime, timedelta
from typing import Dict, Any

class DashboardService:
    def __init__(self, db_manager, finance_service):
        self.db = db_manager
        self.finance = finance_service

    def get_dashboard_summary(self, date: str = None, days_expiring_soon: int = 30) -> Dict[str, Any]:
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        
        # 1. Financial metrics (delegated to finance service)
        finance_summary = self.finance.get_daily_summary(target_date)
        
        # Number of completed sales for the date
        conn = self.db.get_connection()
        sales_count = conn.execute('''
            SELECT COUNT(id) FROM sales 
            WHERE status = 'Completed' AND substr(date_time, 1, 10) = ?
        ''', (target_date,)).fetchone()[0]

        # 2. Inventory snapshots (current state)
        inv_snapshot = conn.execute('''
            SELECT 
                SUM(current_stock) as total_qty,
                SUM(inventory_value) as total_value,
                COUNT(id) as active_products,
                SUM(CASE WHEN current_stock <= min_stock_level THEN 1 ELSE 0 END) as low_stock_count
            FROM products
            WHERE is_active = 1
        ''').fetchone()

        # 3. Medicine expiry snapshots (current state)
        today_date = datetime.now().strftime("%Y-%m-%d")
        soon_date = (datetime.now() + timedelta(days=days_expiring_soon)).strftime("%Y-%m-%d")

        expiry_metrics = conn.execute('''
            SELECT 
                COUNT(DISTINCT CASE WHEN expiry_date != '' AND expiry_date <= ? THEN product_id END) as expired_products_count,
                COUNT(DISTINCT CASE WHEN expiry_date != '' AND expiry_date > ? AND expiry_date <= ? THEN product_id END) as expiring_soon_products_count
            FROM medicine_batches
            WHERE current_qty > 0 AND expiry_date IS NOT NULL
        ''', (today_date, today_date, soon_date)).fetchone()

        return {
            "date": target_date,
            "total_sales_revenue": finance_summary['total_sales_revenue'],
            "number_of_completed_sales": sales_count,
            "cost_of_goods_sold": finance_summary['cost_of_goods_sold'],
            "gross_profit": finance_summary['gross_profit'],
            "operating_expenses": finance_summary['operating_expenses'],
            "net_operating_profit": finance_summary['net_operating_profit'],
            "total_inventory_quantity": inv_snapshot['total_qty'] or 0,
            "total_inventory_value": inv_snapshot['total_value'] or 0,
            "total_outstanding_supplier_balances": finance_summary['total_outstanding_supplier_balances'],
            "active_products_count": inv_snapshot['active_products'],
            "low_stock_products_count": inv_snapshot['low_stock_count'],
            "medicine_expired_products_count": expiry_metrics['expired_products_count'],
            "medicine_expiring_soon_products_count": expiry_metrics['expiring_soon_products_count']
        }
