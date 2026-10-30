-- 002_phase2_schema_updates.sql

-- 1. Create Opening Stock Operations Table to prevent duplicate opening stocks
CREATE TABLE opening_stock_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    date_time TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- 2. Make purchase_item_id NULLABLE in medicine_batches for opening stock support
ALTER TABLE medicine_batches RENAME TO old_medicine_batches;
ALTER TABLE medicine_batch_movements RENAME TO old_medicine_batch_movements;
ALTER TABLE sale_item_batches RENAME TO old_sale_item_batches;

CREATE TABLE medicine_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    purchase_item_id INTEGER, -- Now NULLABLE for opening stock
    batch_number TEXT,
    expiry_date TEXT,
    initial_qty INTEGER NOT NULL CHECK (initial_qty >= 0 AND TYPEOF(initial_qty) IN ('integer', 'null')),
    current_qty INTEGER NOT NULL CHECK (current_qty >= 0 AND TYPEOF(current_qty) IN ('integer', 'null')),
    unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0 AND TYPEOF(unit_cost) IN ('integer', 'null')),
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (purchase_item_id) REFERENCES purchase_items (id),
    CHECK (current_qty <= initial_qty)
);

CREATE TABLE medicine_batch_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    quantity_change INTEGER NOT NULL CHECK (TYPEOF(quantity_change) IN ('integer', 'null')),
    movement_type TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    date_time TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches (id),
    UNIQUE(movement_type, reference_type, reference_id, batch_id)
);

CREATE TABLE sale_item_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_item_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    quantity_deducted INTEGER NOT NULL CHECK (quantity_deducted >= 0 AND TYPEOF(quantity_deducted) IN ('integer', 'null')),
    FOREIGN KEY (sale_item_id) REFERENCES sale_items (id),
    FOREIGN KEY (batch_id) REFERENCES medicine_batches (id)
);

INSERT INTO medicine_batches SELECT * FROM old_medicine_batches;
INSERT INTO medicine_batch_movements SELECT * FROM old_medicine_batch_movements;
INSERT INTO sale_item_batches SELECT * FROM old_sale_item_batches;

DROP TABLE old_sale_item_batches;
DROP TABLE old_medicine_batch_movements;
DROP TABLE old_medicine_batches;

-- Recreate immutable audit log triggers for medicine batch movements
CREATE TRIGGER prevent_med_batch_mov_update
BEFORE UPDATE ON medicine_batch_movements
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable');
END;

CREATE TRIGGER prevent_med_batch_mov_delete
BEFORE DELETE ON medicine_batch_movements
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable');
END;
