from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3

class ExpenseService:
    def __init__(self, db_manager):
        self.db = db_manager

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    def create_expense(self, category: str, description: str, amount: int, date: str) -> int:
        category = category.strip()
        description = description.strip() if description else ""
        date = date.strip()

        if not category:
            raise ValueError("Category is required.")
        if not date:
            raise ValueError("Date is required.")
            
        amount = self._ensure_integer(amount)
        if amount <= 0:
            raise ValueError("Expense amount must be a positive integer.")

        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses (category, description, amount, date, status) VALUES (?, ?, ?, ?, 'Completed')",
                (category, description, amount, date)
            )
            return cursor.lastrowid

    def get_expense(self, expense_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        return dict(row) if row else None

    def list_expenses(self, start_date: str = None, end_date: str = None, category: str = None, include_voided: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        if category:
            query += " AND category = ?"
            params.append(category)

        if not include_voided:
            query += " AND status = 'Completed'"

        query += " ORDER BY date DESC, id DESC"
        
        conn = self.db.get_connection()
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def void_expense(self, expense_id: int):
        with self.db.transaction() as conn:
            expense = conn.execute("SELECT status FROM expenses WHERE id = ?", (expense_id,)).fetchone()
            if not expense:
                raise ValueError("Expense not found.")
            if expense['status'] == 'Voided':
                raise ValueError("Expense is already voided.")

            conn.execute("UPDATE expenses SET status = 'Voided' WHERE id = ?", (expense_id,))

    def update_expense(self, expense_id: int, category: str, description: str, amount: int, date: str):
        # We can implement update by voiding and creating a new one, or direct update if allowed.
        # But the prompt says: "Update an expense only if the existing data model and audit requirements permit it safely. Use a void/correction workflow"
        # We will strictly use void/correction for modifying amounts or dates to preserve financial history.
        # So we can just refuse to update the amount directly, and recommend void_expense + create_expense.
        raise ValueError("Updating expenses directly is not permitted to preserve audit trails. Please void the existing expense and create a new one.")
