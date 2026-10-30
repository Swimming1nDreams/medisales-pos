import sqlite3
from typing import List, Dict, Any, Optional

class ProductService:
    def __init__(self, db_manager):
        self.db = db_manager

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    # --- Categories ---
    def create_category(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Category name is required.")
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO categories (name, is_active) VALUES (?, 1)",
                    (name,)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{name}' already exists.")

    def update_category(self, category_id: int, name: str, is_active: bool):
        name = name.strip()
        if not name:
            raise ValueError("Category name is required.")
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    "UPDATE categories SET name = ?, is_active = ? WHERE id = ?",
                    (name, int(is_active), category_id)
                )
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{name}' already exists.")

    def list_categories(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT * FROM categories"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute(query).fetchall()]

    # --- Products ---
    def create_product(self, name: str, category_id: int, unit_measure: str,
                       selling_price: int, min_stock_level: int, is_medicine: bool) -> int:
        name = name.strip()
        unit_measure = unit_measure.strip()
        if not name or not unit_measure:
            raise ValueError("Product name and unit measure are required.")
            
        selling_price = self._ensure_integer(selling_price)
        min_stock_level = self._ensure_integer(min_stock_level)

        if selling_price < 0 or min_stock_level < 0:
            raise ValueError("Prices and stock levels cannot be negative.")

        with self.db.transaction() as conn:
            # Validate category
            cat = conn.execute("SELECT id FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not cat:
                raise ValueError("Invalid category.")
                
            cursor = conn.execute('''
                INSERT INTO products (
                    name, category_id, unit_measure, selling_price,
                    min_stock_level, is_medicine, is_active, current_stock, inventory_value
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0)
            ''', (name, category_id, unit_measure, selling_price, min_stock_level, int(is_medicine)))
            return cursor.lastrowid

    def update_product(self, product_id: int, name: str, category_id: int, unit_measure: str,
                       selling_price: int, min_stock_level: int, is_active: bool):
        name = name.strip()
        unit_measure = unit_measure.strip()
        if not name or not unit_measure:
            raise ValueError("Product name and unit measure are required.")
            
        selling_price = self._ensure_integer(selling_price)
        min_stock_level = self._ensure_integer(min_stock_level)

        with self.db.transaction() as conn:
            cat = conn.execute("SELECT id FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not cat:
                raise ValueError("Invalid category.")
                
            old_prod = conn.execute("SELECT unit_measure FROM products WHERE id = ?", (product_id,)).fetchone()
            if old_prod and old_prod['unit_measure'] != unit_measure:
                has_tx = conn.execute("SELECT 1 FROM inventory_movements WHERE product_id = ?", (product_id,)).fetchone()
                if has_tx:
                    raise ValueError("Cannot change unit measure: product already has inventory transactions.")
                
            conn.execute('''
                UPDATE products 
                SET name = ?, category_id = ?, unit_measure = ?, selling_price = ?,
                    min_stock_level = ?, is_active = ?
                WHERE id = ?
            ''', (name, category_id, unit_measure, selling_price, min_stock_level, int(is_active), product_id))

    def list_products(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        query = '''
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
        '''
        if not include_inactive:
            query += " WHERE p.is_active = 1"
        query += " ORDER BY p.name"
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute(query).fetchall()]
