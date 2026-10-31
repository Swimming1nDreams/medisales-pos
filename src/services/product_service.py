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

    # --- Product Packagings ---
    def _save_packagings_internal(self, conn, product_id: int, base_unit: str, packagings: List[Dict[str, Any]]):
        conn.execute("DELETE FROM product_packagings WHERE product_id = ?", (product_id,))
        if not packagings:
            return

        seen_names = set()
        for p in packagings:
            uname = (p.get('unit_name') or '').strip()
            if not uname:
                raise ValueError("Packaging unit name cannot be empty.")
            if uname.lower() == base_unit.lower():
                raise ValueError(f"Packaging unit '{uname}' cannot have the same name as base unit.")
            if uname.lower() in seen_names:
                raise ValueError(f"Duplicate packaging unit '{uname}' for product.")
            seen_names.add(uname.lower())

            factor = self._ensure_integer(p.get('conversion_factor'))
            price = self._ensure_integer(p.get('selling_price'))
            if factor <= 1:
                raise ValueError(f"Conversion factor for '{uname}' must be greater than 1.")
            if price < 0:
                raise ValueError(f"Selling price for '{uname}' cannot be negative.")

            barcode = (p.get('barcode') or '').strip() or None
            is_active = 1 if p.get('is_active', True) else 0

            conn.execute('''
                INSERT INTO product_packagings (product_id, unit_name, conversion_factor, selling_price, barcode, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_id, uname, factor, price, barcode, is_active))

    def set_product_packagings(self, product_id: int, packagings: List[Dict[str, Any]]):
        with self.db.transaction() as conn:
            prod = conn.execute("SELECT unit_measure FROM products WHERE id = ?", (product_id,)).fetchone()
            if not prod:
                raise ValueError(f"Product #{product_id} not found.")
            self._save_packagings_internal(conn, product_id, prod['unit_measure'], packagings)

    def get_product_packagings(self, product_id: int) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        rows = conn.execute(
            "SELECT * FROM product_packagings WHERE product_id = ? AND is_active = 1 ORDER BY conversion_factor ASC",
            (product_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        row = conn.execute('''
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.id = ?
        ''', (product_id,)).fetchone()
        if not row:
            return None
        prod = dict(row)
        prod['packagings'] = self.get_product_packagings(product_id)
        return prod

    # --- Products ---
    def create_product(self, name: str, category_id: int, unit_measure: str,
                       selling_price: int, min_stock_level: int, is_medicine: bool,
                       packagings: Optional[List[Dict[str, Any]]] = None) -> int:
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
            prod_id = cursor.lastrowid
            if packagings:
                self._save_packagings_internal(conn, prod_id, unit_measure, packagings)
            return prod_id

    def update_product(self, product_id: int, name: str, category_id: int, unit_measure: str,
                       selling_price: int, min_stock_level: int, is_active: bool,
                       packagings: Optional[List[Dict[str, Any]]] = None):
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

            if packagings is not None:
                self._save_packagings_internal(conn, product_id, unit_measure, packagings)

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
        prods = [dict(row) for row in conn.execute(query).fetchall()]

        pkg_rows = conn.execute(
            "SELECT * FROM product_packagings WHERE is_active = 1 ORDER BY conversion_factor ASC"
        ).fetchall()
        pkgs_by_prod = {}
        for r in pkg_rows:
            d = dict(r)
            pkgs_by_prod.setdefault(d['product_id'], []).append(d)

        for p in prods:
            p['packagings'] = pkgs_by_prod.get(p['id'], [])

        return prods
