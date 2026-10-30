-- 001_initial_schema.sql

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    unit_measure TEXT NOT NULL,
    selling_price INTEGER NOT NULL CHECK (selling_price >= 0 AND TYPEOF(selling_price) IN ('integer', 'null')),
    min_stock_level INTEGER NOT NULL CHECK (min_stock_level >= 0 AND TYPEOF(min_stock_level) IN ('integer', 'null')),
    is_medicine BOOLEAN NOT NULL,
    current_stock INTEGER NOT NULL DEFAULT 0 CHECK (current_stock >= 0 AND TYPEOF(current_stock) IN ('integer', 'null')),
    inventory_value INTEGER DEFAULT 0 CHECK (inventory_value >= 0 AND TYPEOF(inventory_value) IN ('integer', 'null')),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0 AND TYPEOF(total_amount) IN ('integer', 'null')),
    amount_paid INTEGER NOT NULL DEFAULT 0 CHECK (amount_paid >= 0 AND TYPEOF(amount_paid) IN ('integer', 'null')),
    status TEXT NOT NULL CHECK (status IN ('Completed', 'Voided')),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
    CHECK (amount_paid <= total_amount)
);

CREATE TABLE purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0 AND TYPEOF(quantity) IN ('integer', 'null')),
    unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0 AND TYPEOF(unit_cost) IN ('integer', 'null')),
    line_total INTEGER NOT NULL CHECK (line_total >= 0 AND TYPEOF(line_total) IN ('integer', 'null')),
    FOREIGN KEY (purchase_id) REFERENCES purchases (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE supplier_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0 AND TYPEOF(total_amount) IN ('integer', 'null')),
    allocated_amount INTEGER NOT NULL DEFAULT 0 CHECK (allocated_amount >= 0 AND TYPEOF(allocated_amount) IN ('integer', 'null')),
    notes TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
    CHECK (allocated_amount <= total_amount)
);

CREATE TABLE supplier_payment_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL,
    purchase_id INTEGER NOT NULL,
    allocated_amount INTEGER NOT NULL CHECK (allocated_amount >= 0 AND TYPEOF(allocated_amount) IN ('integer', 'null')),
    FOREIGN KEY (payment_id) REFERENCES supplier_payments (id),
    FOREIGN KEY (purchase_id) REFERENCES purchases (id)
);

CREATE TABLE medicine_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    purchase_item_id INTEGER NOT NULL,
    batch_number TEXT,
    expiry_date TEXT, -- YYYY-MM-DD
    initial_qty INTEGER NOT NULL CHECK (initial_qty >= 0 AND TYPEOF(initial_qty) IN ('integer', 'null')),
    current_qty INTEGER NOT NULL CHECK (current_qty >= 0 AND TYPEOF(current_qty) IN ('integer', 'null')),
    unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0 AND TYPEOF(unit_cost) IN ('integer', 'null')),
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (purchase_item_id) REFERENCES purchase_items (id),
    CHECK (current_qty <= initial_qty)
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    date_time TEXT NOT NULL,
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0 AND TYPEOF(total_amount) IN ('integer', 'null')),
    amount_received INTEGER NOT NULL CHECK (amount_received >= 0 AND TYPEOF(amount_received) IN ('integer', 'null')),
    change_given INTEGER NOT NULL CHECK (change_given >= 0 AND TYPEOF(change_given) IN ('integer', 'null')),
    status TEXT NOT NULL CHECK (status IN ('Completed', 'Voided')),
    CHECK (amount_received >= total_amount),
    CHECK (change_given == amount_received - total_amount)
);

CREATE TABLE sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0 AND TYPEOF(quantity) IN ('integer', 'null')),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0 AND TYPEOF(unit_price) IN ('integer', 'null')),
    total_cost INTEGER NOT NULL CHECK (total_cost >= 0 AND TYPEOF(total_cost) IN ('integer', 'null')),
    line_total INTEGER NOT NULL CHECK (line_total >= 0 AND TYPEOF(line_total) IN ('integer', 'null')),
    FOREIGN KEY (sale_id) REFERENCES sales (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE sale_item_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_item_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    quantity_deducted INTEGER NOT NULL CHECK (quantity_deducted >= 0 AND TYPEOF(quantity_deducted) IN ('integer', 'null')),
    FOREIGN KEY (sale_item_id) REFERENCES sale_items (id),
    FOREIGN KEY (batch_id) REFERENCES medicine_batches (id)
);

CREATE TABLE inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity_change INTEGER NOT NULL CHECK (TYPEOF(quantity_change) IN ('integer', 'null')),
    value_change INTEGER NOT NULL CHECK (TYPEOF(value_change) IN ('integer', 'null')),
    movement_type TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    date_time TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id),
    UNIQUE(movement_type, reference_type, reference_id, product_id)
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

CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    description TEXT,
    amount INTEGER NOT NULL CHECK (amount >= 0 AND TYPEOF(amount) IN ('integer', 'null')),
    date TEXT NOT NULL
);

-- TRIGGERS --

-- Immutable Audit Log Triggers
CREATE TRIGGER prevent_inv_mov_update
BEFORE UPDATE ON inventory_movements
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable');
END;

CREATE TRIGGER prevent_inv_mov_delete
BEFORE DELETE ON inventory_movements
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable');
END;

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

-- Supplier Payments & Allocations
CREATE TRIGGER check_allocation_supplier
BEFORE INSERT ON supplier_payment_allocations
BEGIN
    SELECT RAISE(ABORT, 'Payment and Purchase must belong to same supplier')
    WHERE (SELECT supplier_id FROM supplier_payments WHERE id = NEW.payment_id) !=
          (SELECT supplier_id FROM purchases WHERE id = NEW.purchase_id);
END;

CREATE TRIGGER update_payment_allocation_insert
AFTER INSERT ON supplier_payment_allocations
BEGIN
    UPDATE supplier_payments SET allocated_amount = allocated_amount + NEW.allocated_amount WHERE id = NEW.payment_id;
    UPDATE purchases SET amount_paid = amount_paid + NEW.allocated_amount WHERE id = NEW.purchase_id;
END;

CREATE TRIGGER update_payment_allocation_delete
AFTER DELETE ON supplier_payment_allocations
BEGIN
    UPDATE supplier_payments SET allocated_amount = allocated_amount - OLD.allocated_amount WHERE id = OLD.payment_id;
    UPDATE purchases SET amount_paid = amount_paid - OLD.allocated_amount WHERE id = OLD.purchase_id;
END;

-- Voiding Purchase Restrictions
CREATE TRIGGER prevent_purchase_void_if_paid
BEFORE UPDATE ON purchases
WHEN NEW.status = 'Voided' AND OLD.amount_paid > 0
BEGIN
    SELECT RAISE(ABORT, 'Cannot void purchase with existing payment allocations');
END;

-- Prevent Deletions of core records
CREATE TRIGGER prevent_sale_delete
BEFORE DELETE ON sales
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete completed sales');
END;

CREATE TRIGGER prevent_purchase_delete
BEFORE DELETE ON purchases
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete completed purchases');
END;

CREATE TRIGGER prevent_allocation_update
BEFORE UPDATE ON supplier_payment_allocations
BEGIN
    SELECT RAISE(ABORT, 'Allocations cannot be updated');
END;

