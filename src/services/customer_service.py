from datetime import datetime
import sqlite3
from typing import List, Dict, Any, Optional

class CustomerService:
    def __init__(self, db_manager):
        self.db = db_manager

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    def create_customer(self, name: str, phone: str = None, address: str = None, notes: str = None) -> int:
        name = name.strip() if name else ""
        if not name:
            raise ValueError("Customer name is required.")
        
        phone = phone.strip() if phone else None
        address = address.strip() if address else None
        notes = notes.strip() if notes else None

        with self.db.transaction() as conn:
            # Check duplicate customer name
            existing = conn.execute("SELECT id FROM customers WHERE name = ?", (name,)).fetchone()
            if existing:
                raise ValueError(f"Customer '{name}' already exists.")

            cursor = conn.execute(
                "INSERT INTO customers (name, phone, address, notes, is_active) VALUES (?, ?, ?, ?, 1)",
                (name, phone, address, notes)
            )
            return cursor.lastrowid

    def update_customer(self, customer_id: int, name: str, phone: str = None, address: str = None, notes: str = None, is_active: bool = True):
        name = name.strip() if name else ""
        if not name:
            raise ValueError("Customer name is required.")

        phone = phone.strip() if phone else None
        address = address.strip() if address else None
        notes = notes.strip() if notes else None

        with self.db.transaction() as conn:
            existing = conn.execute("SELECT id FROM customers WHERE name = ? AND id != ?", (name, customer_id)).fetchone()
            if existing:
                raise ValueError(f"Customer '{name}' already exists.")

            conn.execute(
                "UPDATE customers SET name = ?, phone = ?, address = ?, notes = ?, is_active = ? WHERE id = ?",
                (name, phone, address, notes, int(is_active), customer_id)
            )

    def list_customers(self, include_inactive: bool = False, search_term: str = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM customers WHERE 1=1"
        params = []

        if not include_inactive:
            query += " AND is_active = 1"

        if search_term and search_term.strip():
            term = search_term.strip()
            query += " AND (name LIKE ? OR phone LIKE ? OR address LIKE ?)"
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])

        query += " ORDER BY name ASC"
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute(query, params).fetchall()]

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        return dict(row) if row else None

    def get_customer_balances(self) -> List[Dict[str, Any]]:
        """
        Returns list of customer balances showing total credit taken, repayments, and outstanding debt.
        """
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT 
                c.id as customer_id,
                c.name as customer_name,
                c.phone,
                c.address,
                c.is_active,
                COALESCE(sales_summary.total_credit, 0) as total_credit,
                COALESCE(payments_summary.total_repaid, 0) as total_repaid,
                (COALESCE(sales_summary.total_credit, 0) - COALESCE(payments_summary.total_repaid, 0)) as outstanding_balance
            FROM customers c
            LEFT JOIN (
                SELECT customer_id, SUM(credit_amount) as total_credit
                FROM sales
                WHERE status = 'Completed' AND customer_id IS NOT NULL
                GROUP BY customer_id
            ) sales_summary ON c.id = sales_summary.customer_id
            LEFT JOIN (
                SELECT customer_id, SUM(amount) as total_repaid
                FROM customer_payments
                GROUP BY customer_id
            ) payments_summary ON c.id = payments_summary.customer_id
            ORDER BY outstanding_balance DESC, c.name ASC
        ''').fetchall()
        return [dict(r) for r in rows]

    def record_debt_repayment(self, customer_id: int, amount: int, notes: str = None) -> str:
        amount = self._ensure_integer(amount)
        if amount <= 0:
            raise ValueError("Repayment amount must be greater than zero.")

        notes = notes.strip() if notes else None
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ref = 'CPAY-' + datetime.now().strftime("%y%m%d%H%M%S")[-8:]

        with self.db.transaction() as conn:
            cust = conn.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if not cust:
                raise ValueError(f"Customer #{customer_id} not found.")

            conn.execute(
                "INSERT INTO customer_payments (reference, customer_id, date_time, amount, notes) VALUES (?, ?, ?, ?, ?)",
                (ref, customer_id, now, amount, notes)
            )
            return ref

    def get_customer_statement(self, customer_id: int) -> Dict[str, Any]:
        """
        Full chronological ledger statement of credit purchases and repayments for a customer.
        """
        conn = self.db.get_connection()
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer #{customer_id} not found.")

        # Credit Sales
        sales_rows = conn.execute('''
            SELECT id, reference, date_time, total_amount, amount_received, credit_amount, status
            FROM sales
            WHERE customer_id = ? AND status = 'Completed' AND credit_amount > 0
            ORDER BY date_time ASC
        ''', (customer_id,)).fetchall()

        # Payments
        payment_rows = conn.execute('''
            SELECT id, reference, date_time, amount, notes
            FROM customer_payments
            WHERE customer_id = ?
            ORDER BY date_time ASC
        ''', (customer_id,)).fetchall()

        # Build chronological timeline
        timeline = []
        for s in sales_rows:
            timeline.append({
                'type': 'credit_sale',
                'reference': s['reference'],
                'date_time': s['date_time'],
                'debit': s['credit_amount'], # Increases customer's debt
                'credit': 0,
                'description': f"Credit Purchase ({s['reference']})",
                'notes': ''
            })

        for p in payment_rows:
            timeline.append({
                'type': 'repayment',
                'reference': p['reference'],
                'date_time': p['date_time'],
                'debit': 0,
                'credit': p['amount'], # Decreases customer's debt
                'description': f"Debt Repayment ({p['reference']})",
                'notes': p['notes'] or ''
            })

        timeline.sort(key=lambda x: x['date_time'])

        running_balance = 0
        for entry in timeline:
            running_balance += (entry['debit'] - entry['credit'])
            entry['balance'] = running_balance

        return {
            'customer': customer,
            'total_credit': sum(s['credit_amount'] for s in sales_rows),
            'total_repaid': sum(p['amount'] for p in payment_rows),
            'outstanding_balance': running_balance,
            'entries': list(reversed(timeline)) # Return latest entries first for display
        }
