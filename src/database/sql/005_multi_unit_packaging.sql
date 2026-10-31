-- 005_multi_unit_packaging.sql

-- 1. Create product_packagings table for multi-tier unit conversions
CREATE TABLE IF NOT EXISTS product_packagings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    unit_name TEXT NOT NULL,
    conversion_factor INTEGER NOT NULL CHECK (conversion_factor > 1 AND TYPEOF(conversion_factor) IN ('integer', 'null')),
    selling_price INTEGER NOT NULL CHECK (selling_price >= 0 AND TYPEOF(selling_price) IN ('integer', 'null')),
    barcode TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    UNIQUE (product_id, unit_name)
);

CREATE INDEX IF NOT EXISTS idx_product_packagings_product_id ON product_packagings (product_id);

-- 2. Add packaging details to sale_items
ALTER TABLE sale_items ADD COLUMN packaging_unit TEXT DEFAULT NULL;
ALTER TABLE sale_items ADD COLUMN packaging_factor INTEGER DEFAULT 1;

-- 3. Add packaging details to purchase_items
ALTER TABLE purchase_items ADD COLUMN packaging_unit TEXT DEFAULT NULL;
ALTER TABLE purchase_items ADD COLUMN packaging_factor INTEGER DEFAULT 1;
