Pharmacy and General Store Management System
1. Project Overview

Develop a modern Windows desktop application for managing a single retail shop that sells both medicines and general merchandise.

The application must provide an integrated system for sales, product management, inventory, medicine batch tracking, purchases, suppliers, expenses, financial analysis, reports, and database backup.

The application is intended for a small, owner-managed business. It must be practical, reliable, easy to learn, and suitable for daily commercial use.

2. Technology Stack

Proposed technology stack:

Programming language: Python.
Desktop UI framework: PySide6.
Database: SQLite.
Database access: A suitable Python SQLite data-access layer.
Testing: pytest.
Windows packaging: PyInstaller or an equivalent appropriate packaging tool.

These technologies are the approved starting direction. Before implementation, verify that the selected libraries and versions are compatible.

The application must run locally on Windows and must not require an internet connection for normal business operations.

The final application should be distributable as a Windows executable.

3. Business Scope

The application manages one physical shop containing two broad product groups:

Medicines.
General merchandise, including groceries, beverages, personal care products, and household goods.

These product groups belong to the same business and use one integrated inventory, purchasing, sales, and financial system.

The application must not treat them as separate businesses.

The initial deployment will use one Windows laptop and one local database.

The application is primarily operated by the shop owner. A complex user-role or multi-branch system is unnecessary.

4. Explicit Exclusions

The following features are not required in the initial version:

Barcode scanning.
Discount functionality.
Multiple shop branches.
Complex role-based access control.
Online-only operation.
Cloud-dependent business operations.
Unnecessary enterprise-level features.

Do not add these features without explicit approval.

5. User Interface Requirements

Create a clean, modern, professional desktop interface.

Use:

A persistent sidebar for navigation.
A consistent top bar and page-title system.
Clear buttons, forms, dialogs, and searchable tables.
Readable typography and consistent spacing.
Helpful confirmation dialogs for consequential operations.
Clear success messages and understandable error messages.
Loading indicators only where useful.
Keyboard-friendly workflows, especially for sales.

The visual design should prioritize usability rather than decorative effects.

Main navigation:

Dashboard.
Sales.
Products.
Inventory.
Purchases.
Suppliers.
Expenses.
Finance.
Reports.
Settings.

Use a consistent UI design system across all modules.

6. Dashboard

The dashboard should provide a useful summary of the business.

Display:

Today's sales revenue.
Today's completed sales count.
Cost of goods sold for the selected reporting period.
Estimated gross profit.
Recorded operating expenses.
Estimated net profit.
Low-stock products.
Out-of-stock products.
Medicines approaching expiry.
Expired medicine inventory requiring attention.

Provide useful navigation from dashboard alerts to the relevant records.

Clearly distinguish revenue, profit, expenses, and cash-related figures.

Do not present an unverified calculation as actual profit.

7. Product Management

Each product should have an internal unique ID and appropriate identifying information.

Product information should include:

Product ID.
Product name.
Category.
Unit of measurement.
Selling price.
Minimum stock level.
Product status.
Medicine-tracking configuration where applicable.
Creation and modification timestamps.

Support product creation, editing, searching, filtering, and deactivation.

Categories should be configurable.

Examples include:

Medicine.
Grocery and Beverage.
Personal Care.
Household.

Products must not be permanently deleted if they are referenced by historical transactions. Use appropriate deactivation or archival behavior.

Preserve historical transaction prices when a product's current price changes.

8. Inventory Management

The system must maintain an accurate stock balance for every product.

Inventory changes must be associated with recorded business events.

Examples include:

Purchase receipts.
Sales.
Damaged goods.
Expired goods removed from sale.
Stock corrections.
Other explicitly recorded adjustments.

Maintain an inventory movement history containing:

Product.
Quantity change.
Movement type.
Date and time.
Reason or notes where appropriate.
Related transaction.
Medicine batch reference where applicable.

The system must prevent ordinary sales from reducing stock below zero.

Stock adjustments must be authorized through the application's normal management workflow and must retain an audit trail.

The system must support low-stock and out-of-stock alerts.

Historical inventory movements must not be silently overwritten.

9. Medicine Batch and Expiry Management

Medicines require batch-level tracking.

Each medicine batch should be associated with its product and store the information available for that batch, including:

Batch number, when available.
Expiry date.
Purchase cost.
Quantity received.
Current remaining quantity.
Purchase reference.
Relevant timestamps.

Do not assume that every general merchandise product requires medicine-specific batch tracking.

Use FEFO: First Expired, First Out.

When selling a medicine, allocate stock from the earliest-expiring eligible batch first.

The system must:

Prevent expired medicines from being sold.
Exclude expired batches from ordinary sale allocation.
Alert the owner about upcoming expiry dates.
Show remaining quantities by batch.
Preserve the batch allocation for every completed sale.
Record expired or damaged stock removals.
Handle missing or unknown expiry information explicitly rather than inventing a date.

The expiry-warning period must be configurable.

Batch quantities and overall product stock must remain consistent.

10. Supplier Management

Maintain supplier records with appropriate fields, including:

Supplier ID.
Supplier name.
Phone number.
Address.
Notes.
Active status.

Support searching, editing, and viewing purchase history.

Do not require supplier details to be duplicated in every purchase item.

Historical transactions must remain understandable if a supplier's contact information changes.

11. Purchase Management

A purchase transaction should contain:

Purchase reference.
Supplier reference, when available.
Purchase date.
Individual purchased products.
Quantities.
Actual unit purchase prices.
Line totals.
Overall transaction total.
Payment status.
Amount paid.
Outstanding amount, if applicable.
Relevant notes.

Purchase headers and purchase items must be stored separately.

Each purchase item must preserve its actual historical purchase price.

When a purchase is confirmed, inventory must increase consistently.

For medicine purchases, create or update the appropriate batch records with the relevant expiry information.

Support purchases that are fully paid, partially paid, or unpaid.

Do not treat recording a purchase and paying for it as necessarily the same event.

If purchase correction or cancellation is supported, the application must preserve transaction history and reverse associated stock and financial effects correctly.

12. Sales Management

The sales screen must be optimized for fast daily use.

Expected workflow:

Search for a product by name or category.
Select the product.
Enter the quantity.
Add it to the current sale.
Review the selected items and total.
Enter the amount received.
Calculate the change.
Confirm the sale.
Save the transaction and update stock.

The system must validate quantities, prices, payment amounts, and stock availability.

A completed sale should preserve:

Sale reference.
Date and time.
Individual sale items.
Quantities.
Historical selling prices.
Historical cost information needed for profit calculations.
Total amount.
Amount received.
Change given.
Payment method or status, where applicable.
Medicine batch allocations where applicable.

Use database transactions to ensure that the sale and its inventory changes succeed or fail together.

If a sale cannot be completed, the system must not leave partial stock deductions or incomplete financial records.

Do not silently delete completed sales.

Any future void, return, or correction feature must use an auditable process.

13. Cost of Goods Sold and Profit

The application must distinguish:

Sales revenue.
Cost of goods sold.
Gross profit.
Operating expenses.
Net profit.
Cash balance.
Outstanding customer receivables.
Outstanding supplier payables.

Gross profit is calculated as sales revenue minus the cost of the goods sold.

Net profit is calculated as gross profit minus applicable operating expenses.

Inventory purchases must not automatically be treated entirely as an operating expense for the purchase date.

Use a consistent, documented inventory-costing method.

For medicine batches, the actual allocated batch costs should be preserved.

For general merchandise, the costing approach must be finalized during database and accounting design before implementation.

Use decimal-safe monetary calculations or integer minor units as appropriate. Do not use binary floating-point arithmetic for financial calculations.

Reports must clearly identify the reporting period and calculation method.

Do not confuse cash received with sales revenue or cash paid for inventory with cost of goods sold.

14. Expenses

Allow the owner to record business expenses.

Each expense should include:

Expense ID.
Category.
Description.
Amount.
Date.
Payment information where applicable.
Notes.

Examples include rent, electricity, transportation, and packaging.

Expenses should be categorized for reporting.

Corrections and deletions must be handled safely and must not silently corrupt financial history.

15. Payments and Outstanding Balances

The design must support recording payment status independently from purchase or sale records.

Supplier purchases may be fully paid, partially paid, or unpaid.

Customer credit sales may be supported if the accounting design can implement them consistently.

Outstanding balances must be calculated from recorded transactions and payments rather than entered as arbitrary, disconnected figures.

The implementation plan must explain how payments affect cash balances, receivables, and payables.

16. Reports

Support daily, monthly, and custom-date-range reporting.

Required reports include:

Sales summary.
Sales transaction details.
Purchase summary.
Purchase transaction details.
Current stock.
Low-stock products.
Out-of-stock products.
Medicine batch quantities.
Expired medicines.
Upcoming medicine expirations.
Inventory movements.
Expenses by category.
Gross profit.
Net profit.
Best-selling products.
Supplier purchase history.
Outstanding supplier balances.
Outstanding customer balances, if customer credit is implemented.

Reports must use consistent business logic and database records.

A report must not use a separate, manually maintained value when the underlying transactions are available.

17. Database and Data Integrity

Use SQLite with appropriate relational constraints.

Design the database with:

Primary keys.
Foreign keys.
Required-field constraints.
Unique constraints where appropriate.
Indexes for common searches.
Appropriate transaction boundaries.
A documented database migration strategy.

Enable foreign-key enforcement.

Use a consistent transaction model for operations that affect multiple related records.

Use parameterized SQL statements or an equivalent safe data-access mechanism.

Do not concatenate user-provided input into SQL statements.

Database schema changes must be handled through controlled migrations rather than destructive recreation.

Never reset or overwrite the production database simply to accommodate a schema change.

18. Backup and Restore

Implement a reliable local backup-and-restore workflow.

The system should support creating a consistent database backup and restoring a previously created backup.

Restoration must require confirmation and validate the backup before replacing the active database.

Create safeguards against accidental overwriting and data loss.

The implementation plan should explain how backups work with SQLite, including the safe handling of active database connections.

The application should support choosing a backup destination.

Although normal business operations must work offline, the owner should eventually be able to keep backup copies on separate storage.

19. Settings

Provide configurable settings where useful, including:

Shop name.
Currency display.
Expiry-warning period.
Low-stock defaults.
Receipt preferences, if receipts are implemented.
Backup destination or backup preferences.

The shop's initial operating currency is Myanmar Kyat (MMK).

Settings must be validated and stored persistently.

20. Error Handling and Reliability

The application must handle expected failures gracefully.

Examples include:

Invalid quantities.
Insufficient stock.
Expired medicine.
Missing required fields.
Invalid dates.
Database errors.
Failed backup or restoration.
Duplicate records.
Interrupted transaction operations.

Display understandable error messages.

Do not silently ignore failed database operations.

Use logging to help diagnose errors without exposing sensitive data unnecessarily.

21. Testing Requirements

Use automated tests for important business logic.

At minimum, test:

Product creation and validation.
Purchase creation and stock increases.
Sales and stock decreases.
Insufficient-stock prevention.
FEFO batch allocation.
Expired-medicine sale prevention.
Batch quantity consistency.
Historical price preservation.
Cost of goods sold.
Gross and net profit calculations.
Partial supplier payments, if implemented.
Customer credit and payments, if implemented.
Inventory adjustments.
Transaction rollback after failure.
Backup creation and restoration.
Database migrations.

Test both normal operation and important failure cases.

Do not claim that a feature is tested unless the tests have actually been run.

22. Development Workflow

Develop the application incrementally.

Required sequence:

Review and finalize the project specification.
Propose the architecture and detailed database schema.
Review the schema for accounting and inventory correctness.
Create the project structure and development environment instructions.
Implement and test the database foundation.
Implement product and inventory management.
Implement purchasing and medicine batch tracking.
Implement sales and FEFO allocation.
Implement expenses and financial calculations.
Implement dashboard and reports.
Implement backup and restore.
Integrate the user interface and business modules.
Run integration and regression tests.
Package the application for Windows.
Document installation, usage, backup, and recovery.

The exact order may be refined if dependencies require it, but database integrity and business correctness must take priority.

23. Rules for the Coding Agent

The coding agent must:

Read this specification before implementing a feature.
Preserve existing working code unless a justified change is required.
Inspect the project files before modifying them.
Avoid generating the entire application in one uncontrolled code dump.
Work in small, verifiable stages.
Explain architectural decisions.
Identify ambiguities instead of silently inventing business rules.
Write and run tests for important business logic.
Report actual test results honestly.
Keep dependencies and project structure manageable.
Avoid unnecessary complexity.
Document changes and commands needed to run the application.
Never destroy existing business data to make development easier.

If requirements conflict or an important decision remains unresolved, explain the issue and recommend a solution before implementing it.

24. Definition of Success

The project is successful when the owner can operate the shop using one offline Windows application, maintain accurate stock and medicine expiry records, record purchases and sales reliably, track expenses, understand business profitability, generate useful reports, and recover the database from a valid backup.

The final system must prioritize data integrity, ease of use, and reliability over unnecessary features.