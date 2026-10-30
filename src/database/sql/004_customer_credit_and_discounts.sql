-- 004_customer_credit_and_discounts.sql

-- 1. Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- 2. Create customer debt repayments table
CREATE TABLE IF NOT EXISTS customer_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    date_time TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0 AND TYPEOF(amount) IN ('integer', 'null')),
    notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- 3. Modernize sales table with subtotal, discount_amount, payment_type, customer_id, credit_amount
CREATE TABLE new_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    date_time TEXT NOT NULL,
    subtotal INTEGER NOT NULL DEFAULT 0 CHECK (subtotal >= 0 AND TYPEOF(subtotal) IN ('integer', 'null')),
    discount_amount INTEGER NOT NULL DEFAULT 0 CHECK (discount_amount >= 0 AND TYPEOF(discount_amount) IN ('integer', 'null')),
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0 AND TYPEOF(total_amount) IN ('integer', 'null')),
    amount_received INTEGER NOT NULL CHECK (amount_received >= 0 AND TYPEOF(amount_received) IN ('integer', 'null')),
    change_given INTEGER NOT NULL CHECK (change_given >= 0 AND TYPEOF(change_given) IN ('integer', 'null')),
    payment_type TEXT NOT NULL DEFAULT 'cash' CHECK (payment_type IN ('cash', 'credit')),
    customer_id INTEGER REFERENCES customers(id),
    credit_amount INTEGER NOT NULL DEFAULT 0 CHECK (credit_amount >= 0 AND TYPEOF(credit_amount) IN ('integer', 'null')),
    status TEXT NOT NULL CHECK (status IN ('Completed', 'Voided')),
    CHECK (
        (payment_type = 'cash' AND amount_received >= total_amount AND change_given == amount_received - total_amount AND credit_amount = 0)
        OR
        (payment_type = 'credit' AND credit_amount == CASE WHEN amount_received < total_amount THEN total_amount - amount_received ELSE 0 END)
    )
);

INSERT INTO new_sales (id, reference, date_time, subtotal, discount_amount, total_amount, amount_received, change_given, payment_type, customer_id, credit_amount, status)
SELECT id, reference, date_time, total_amount, 0, total_amount, amount_received, change_given, 'cash', NULL, 0, status
FROM sales;

DROP TABLE sales;

ALTER TABLE new_sales RENAME TO sales;

CREATE TRIGGER IF NOT EXISTS prevent_sale_delete
BEFORE DELETE ON sales
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete completed sales');
END;
