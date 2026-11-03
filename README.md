# Say Mahar (ဆေးမဟာ) — Pharmacy & General Retail POS System
### Commercial-Grade Offline Desktop Point-of-Sale & Inventory Management ERP

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20QtWebEngine-41CD52.svg)](https://www.qt.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%20v3-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-134%20Passed%20(100%25)-success.svg)](https://pytest.org/)

---

## 📌 Overview

**Say Mahar (ဆေးမဟာ)** is an integrated Windows desktop Point-of-Sale (POS) and inventory ERP system engineered specifically for independent retail pharmacies and drugstores that simultaneously sell **pharmaceuticals** (requiring strict expiry dates and FEFO batch dispensing) and **general consumer merchandise** (groceries, personal care, packaged goods using Weighted Average Costing).

The application is architected around a **100% offline, zero-cloud runtime** — ensuring zero downtime during power or internet outages in Myanmar. It pairs an embedded **SQLite 3 database (WAL mode)** with an enterprise-style **Python 3 service layer** and a modern **PySide6 QtWebEngine frontend styled with Tailwind CSS**.

---

## 🌟 Key Features

### 1. Dual-Track Inventory Valuation & FEFO Dispensing
- **FEFO (First-Expired, First-Out) for Pharmaceuticals:** Automatically routes batch sales to deplete earliest-expiring medicine batches first, preventing stock waste and expired drug sales.
- **Weighted Average Cost (WAC) for General Retail:** Automatically computes running weighted average costs for consumer goods upon purchase receiving.
- **Multi-Unit Packaging Hierarchy:** Seamless unit conversion between primary dispensing units (Tablets/Capsules), packaging sub-units (Strips/Blisters), and master cartons (Boxes/Packs).

### 2. High-Speed POS Cashier Checkout
- Optimized for keyboard-driven retail checkout with customizable function key shortcuts (`F1` - `F12`).
- Instant barcode scanning and multi-attribute fuzzy search (Trade Name, Generic Formula, Manufacturer, Barcode).
- Myanmar Kyat quick-cash banknote buttons (1,000 to 50,000 Ks) with instant change calculation.
- Support for multiple payment methods: Cash, Mobile Wallets (KBZPay, Wave Money), and Customer Credit.

### 3. Customer & Supplier Credit Ledgers
- Complete store-level credit management with customer balance tracking, credit limits, debt repayment receipts, and chronological statement audit logs.
- Supplier procurement ledgers tracking purchase invoices, credit purchases, partial payments, and supplier debts.

### 4. Bilingual Localization (Myanmar Unicode & English)
- 100% bilingual UI with instantaneous English / Myanmar Unicode (`Pyidaungsu` / System font) language toggling.
- Full formatting of Myanmar currency denominations (Ks / ကျပ်).

### 5. Automated Data Safety & Backups
- SQLite Write-Ahead Logging (WAL) mode for concurrency and instant crash recovery.
- Automated daily backup rotations with SHA-256 integrity hashing and one-click database restore.

---

## 🏗️ Technical Architecture

```
Medisales/
├── main.py                    # Application Entrypoint & PySide6 Host Window
├── build.py                   # Automated Packaging & Tailwind Compilation Pipeline
├── requirements.txt           # Python Dependencies
├── pytest.ini                 # Test Configuration (134 automated tests)
│
├── src/
│   ├── database/              # SQLite Connection Manager, Schema & Migration Triggers
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── migrations/
│   │
│   ├── services/              # Pure Python Domain Service Layer (Zero UI Dependencies)
│   │   ├── sales_service.py
│   │   ├── product_service.py
│   │   ├── inventory_service.py
│   │   ├── customer_service.py
│   │   ├── supplier_service.py
│   │   ├── expense_service.py
│   │   ├── report_service.py
│   │   └── backup_service.py
│   │
│   ├── ui/                    # Native PySide6 Host & Chromium Engine
│   │   ├── main_window_web.py
│   │   └── bridge.py          # QWebChannel RPC Bridge connecting JS to Python
│   │
│   └── ui_web/                # Modern Semantic Frontend
│       ├── index.html         # Desktop Shell
│       ├── css/output.css     # Compiled Tailwind CSS v3
│       └── js/                # Modular ES6 Page Controllers
│           ├── sales.js
│           ├── products.js
│           ├── inventory.js
│           ├── customers.js
│           ├── suppliers.js
│           ├── expenses.js
│           ├── reports.js
│           ├── settings.js
│           └── i18n.js
│
└── tests/                     # Comprehensive Pytest Suite (Unit, Integration & E2E)
    ├── test_sales_service.py
    ├── test_inventory_fefo.py
    ├── test_credit_ledger.py
    └── test_database_migrations.py
```

---

## 🚀 Installation & Running

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Windows 10 / 11

### Setup Virtual Environment
```powershell
# 1. Clone repository
git clone https://github.com/Swimming1nDreams/medisales-pos.git
cd medisales-pos

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed demo dataset (Optional, includes realistic Myanmar pharmacy data)
python seed_demo_data.py

# 5. Launch Application
python main.py
```

### Running Test Suite
```powershell
pytest
# Output: 134 passed in ~35s
```

---

## 📦 Distribution & Packaging

The application compiles into a standalone, single-directory Windows executable using PyInstaller:
```powershell
python build.py
# Distribution output created in dist/Medisales/
```

---

## 👤 Author Profile
- **Developer:** Swimming1nDreams
- **Domain:** Desktop Software Engineering, Retail ERP, Pharmacy Informatics & Distributed Data Systems
