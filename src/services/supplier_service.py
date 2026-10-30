import sqlite3
from typing import List, Dict, Any

class SupplierService:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_supplier(self, name: str, phone: str = None, address: str = None) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Supplier name is required.")
        
        with self.db.transaction() as conn:
            # Check for exact duplicate name
            existing = conn.execute("SELECT id FROM suppliers WHERE name = ?", (name,)).fetchone()
            if existing:
                raise ValueError(f"Supplier '{name}' already exists.")
                
            cursor = conn.execute(
                "INSERT INTO suppliers (name, phone, address, is_active) VALUES (?, ?, ?, 1)",
                (name, phone, address)
            )
            return cursor.lastrowid

    def update_supplier(self, supplier_id: int, name: str, phone: str = None, address: str = None, is_active: bool = True):
        name = name.strip()
        if not name:
            raise ValueError("Supplier name is required.")
            
        with self.db.transaction() as conn:
            # Check duplicate name
            existing = conn.execute("SELECT id FROM suppliers WHERE name = ? AND id != ?", (name, supplier_id)).fetchone()
            if existing:
                raise ValueError(f"Supplier '{name}' already exists.")
                
            # If deactivating, ensure no unallocated payments or open issues?
            # Requirements: "Deactivate suppliers without deleting historical records."
            
            conn.execute(
                "UPDATE suppliers SET name = ?, phone = ?, address = ?, is_active = ? WHERE id = ?",
                (name, phone, address, int(is_active), supplier_id)
            )

    def list_suppliers(self, include_inactive: bool = False, search_term: str = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM suppliers WHERE 1=1"
        params = []
        
        if not include_inactive:
            query += " AND is_active = 1"
            
        if search_term:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
            
        query += " ORDER BY name"
        
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute(query, params).fetchall()]
