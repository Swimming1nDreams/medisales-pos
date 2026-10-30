/**
 * Medisales Localization System (Bilingual English / Myanmar Unicode)
 * Centralized translation dictionary with safe English fallback.
 */

const I18N = {
    en: {
        // App Chrome & Navigation
        "app.name": "Medisales",
        "app.subtitle": "Pharmacy & Retail Manager",
        "app.pos_badge": "POS",
        "app.offline_status": "Standalone Offline",
        "app.wal_status": "SQLite WAL • v2.4",
        "app.active_badge": "Active",
        "app.central_counter": "Central Counter",

        "nav.group.dispensing": "OPERATIONS & DISPENSING",
        "nav.group.procurement": "PROCUREMENT & EXPENSES",
        "nav.group.finance": "FINANCE & SYSTEM",

        "nav.dashboard": "Dashboard",
        "nav.sales": "Sales / POS",
        "nav.products": "Products Catalog",
        "nav.inventory": "Inventory & FEFO",
        "nav.purchases": "Purchases & Receiving",
        "nav.suppliers": "Suppliers Ledger",
        "nav.expenses": "Operating Expenses",
        "nav.reports": "Financial Reports",
        "nav.settings": "Settings & Database",

        "badge.dispensing": "DISPENSING",
        "badge.procurement": "PROCUREMENT",
        "badge.finance": "FINANCE",

        "subtitle.dashboard": "Store summary & financial performance",
        "subtitle.sales": "Cashier checkout & customer register",
        "subtitle.products": "Medicine & merchandise catalog",
        "subtitle.inventory": "Stock on hand & medicine FEFO batches",
        "subtitle.purchases": "Supplier invoices & goods receiving",
        "subtitle.suppliers": "Vendor accounts & settlement ledger",
        "subtitle.expenses": "Store overheads & operational costs",
        "subtitle.reports": "Financial statements & P&L analysis",
        "subtitle.settings": "Database storage & system utilities",

        // Common Buttons & Actions
        "btn.save": "Save",
        "btn.cancel": "Cancel",
        "btn.close": "Close",
        "btn.confirm": "Confirm",
        "btn.delete": "Delete",
        "btn.edit": "Edit",
        "btn.add": "Add",
        "btn.export_excel": "Export to Excel",
        "btn.refresh": "Refresh",
        "btn.retry": "Retry",
        "btn.print": "Print",
        "btn.print_receipt": "Print Receipt",
        "btn.done": "Done / Close",
        "btn.void": "Void Transaction",
        "btn.filter": "Filter",
        "btn.clear": "Clear",
        "btn.search": "Search",
        "btn.processing": "Processing...",

        // Status Badges & Alerts
        "status.completed": "Completed",
        "status.voided": "Voided",
        "status.active": "Active",
        "status.inactive": "Inactive",
        "status.expired": "Expired",
        "status.expiring_soon": "Expiring Soon",
        "status.unknown_expiry": "Unknown Expiry",
        "status.normal": "Normal",
        "status.low_stock": "Low Stock",
        "status.out_of_stock": "Out of Stock",
        "status.connected": "Connected",
        "status.no_expiry": "No Expiry",

        // Common Table & Form Headers
        "col.id": "ID",
        "col.name": "Name",
        "col.category": "Category",
        "col.unit": "Unit",
        "col.price": "Selling Price",
        "col.stock": "Current Stock",
        "col.value": "Value (Ks)",
        "col.status": "Status",
        "col.actions": "Actions",
        "col.date": "Date",
        "col.date_time": "Date & Time",
        "col.invoice": "Invoice #",
        "col.receipt": "Receipt #",
        "col.total": "Total (Ks)",
        "col.amount": "Amount (Ks)",
        "col.paid": "Paid (Ks)",
        "col.balance": "Balance (Ks)",
        "col.supplier": "Supplier",
        "col.phone": "Phone",
        "col.batch_no": "Batch #",
        "col.expiry_date": "Expiry Date",
        "col.qty": "Quantity",
        "col.cost": "Unit Cost (Ks)",
        "col.type": "Type",
        "col.description": "Description",

        // Messages & Toasts
        "msg.loading": "Loading system data...",
        "msg.no_data": "No records found.",
        "msg.error_title": "Unable to Load Page Data",
        "msg.export_success": "Spreadsheet successfully exported to:",
        "msg.export_failed": "Excel export failed:",

        // Dashboard
        "dash.revenue_today": "Today's Sales Revenue",
        "dash.gross_profit_today": "Today's Gross Profit",
        "dash.completed_orders": "Completed Orders",
        "dash.inventory_valuation": "Total Inventory Value",
        "dash.recent_sales": "Recent Sales Transactions",
        "dash.low_stock_alerts": "Low Stock & Reorder Alerts",
        "dash.view_all_sales": "View All Sales",
        "dash.view_inventory": "View Inventory",
        "dash.no_low_stock": "All product stocks are currently healthy above minimum thresholds.",
        "dash.quick_pos": "Open POS Cashier (F1)",
        "dash.quick_product": "Add New Product",

        // Sales / POS
        "sales.search_placeholder": "Search product by name or category...",
        "sales.all_categories": "All Categories",
        "sales.cart_title": "Current Customer Bill",
        "sales.cart_items": "items",
        "sales.cart_empty": "No items added yet. Click items or search above to begin checkout.",
        "sales.clear_cart": "Clear All",
        "sales.subtotal": "Subtotal",
        "sales.total_due": "Total Amount Due",
        "sales.tendered": "Cash Tendered",
        "sales.change_due": "Change Due",
        "sales.exact_cash": "Exact Cash",
        "sales.complete_sale": "Complete Sale & Print (F2)",
        "sales.insufficient_cash": "Cash tendered is less than the total sale amount.",
        "sales.stock_warning": "Cannot add more. Available stock reached.",
        "sales.history_tab": "Sales History",
        "sales.pos_tab": "Register / POS",
        "sales.filter_start": "From Date",
        "sales.filter_end": "To Date",
        "sales.receipt_title": "MEDISALES PHARMACY & RETAIL",
        "sales.receipt_subtitle": "Official Cash Sales Receipt",
        "sales.receipt_thanks": "Thank you for your visit! Goods sold in good order.",
        "sales.void_confirm_title": "Void Sales Transaction",
        "sales.void_confirm_msg": "Are you sure you want to void this completed sale? Inventory will be accurately restored, and financial totals updated.",

        // Products
        "prod.add_button": "Add New Product",
        "prod.filter_search": "Filter products...",
        "prod.filter_category": "Filter by Category",
        "prod.filter_type": "Filter by Type",
        "prod.type_all": "All Types",
        "prod.type_medicine": "Medicine Only",
        "prod.type_general": "General Goods Only",
        "prod.modal_add_title": "Add New Product",
        "prod.modal_edit_title": "Edit Product Details",
        "prod.field_name": "Product Name",
        "prod.field_category": "Category",
        "prod.field_unit": "Unit Measure (e.g. Strip, Box, Bottle)",
        "prod.field_price": "Selling Price (Ks)",
        "prod.field_min_stock": "Minimum Stock Level",
        "prod.field_is_medicine": "Pharmaceutical Medicine (Track batches & FEFO expiry)",
        "prod.field_is_active": "Product Active for Sale",

        // Inventory
        "inv.tab_stock": "Current Stock & Valuation",
        "inv.tab_batches": "Medicine Batches (FEFO)",
        "inv.tab_movements": "Stock Movement History",
        "inv.filter_all_batches": "All Active Batches",
        "inv.filter_expiring_soon": "Expiring Within 90 Days",
        "inv.filter_expired": "Expired Batches",
        "inv.filter_unknown": "Unknown Expiry Date",
        "inv.total_valuation": "Total Inventory Valuation",
        "inv.total_skus": "Tracked Stock Items",

        // Purchases
        "pur.add_button": "Record Purchase Invoice",
        "pur.modal_title": "Record Inward Purchase",
        "pur.invoice_no": "Invoice / Bill #",
        "pur.supplier": "Supplier",
        "pur.date": "Purchase Date",
        "pur.items_header": "Purchased Line Items",
        "pur.add_line": "+ Add Product Item",
        "pur.amount_paid": "Amount Paid Immediately (Ks)",
        "pur.total_amount": "Total Invoice Amount (Ks)",
        "pur.outstanding": "Remaining Supplier Balance (Ks)",

        // Suppliers
        "sup.add_button": "Add New Supplier",
        "sup.modal_add_title": "Add New Supplier",
        "sup.modal_edit_title": "Edit Supplier Details",
        "sup.field_name": "Supplier / Company Name",
        "sup.field_phone": "Phone Number",
        "sup.field_address": "Address / City",
        "sup.btn_record_payment": "Record Payment",
        "sup.modal_payment_title": "Record Supplier Debt Payment",
        "sup.payment_amount": "Payment Amount (Ks)",
        "sup.payment_date": "Payment Date",
        "sup.payment_notes": "Payment Reference / Notes",

        // Expenses
        "exp.add_button": "Record Expense",
        "exp.modal_title": "Record Store Operating Expense",
        "exp.field_date": "Expense Date",
        "exp.field_category": "Expense Category",
        "exp.field_amount": "Expense Amount (Ks)",
        "exp.field_desc": "Description / Purpose",
        "exp.cat_rent": "Shop Rent",
        "exp.cat_utilities": "Electricity & Water",
        "exp.cat_salaries": "Staff Salaries",
        "exp.cat_transport": "Transport & Delivery",
        "exp.cat_supplies": "Store Supplies",
        "exp.cat_maintenance": "Maintenance & Repairs",
        "exp.cat_other": "Miscellaneous",
        "exp.notice": "Operating expenses only. Merchandise purchases and supplier debt settlements are tracked separately.",
        "exp.void_confirm_title": "Void Operating Expense",
        "exp.void_confirm_msg": "Are you sure you want to void this expense entry? It will be excluded from financial operating overheads.",

        // Reports
        "rep.tab_pnl": "Profit & Loss Statement",
        "rep.tab_products": "Sales by Product",
        "rep.tab_categories": "Sales by Category",
        "rep.tab_expenses": "Expenses by Category",
        "rep.date_today": "Today",
        "rep.date_7d": "Last 7 Days",
        "rep.date_30d": "Last 30 Days",
        "rep.date_month": "This Month",
        "rep.date_custom": "Custom Range",
        "rep.kpi_revenue": "Total Sales Revenue",
        "rep.kpi_cogs": "Cost of Goods Sold (COGS)",
        "rep.kpi_gross_profit": "Gross Operating Profit",
        "rep.kpi_expenses": "Operating Expenses",
        "rep.kpi_net_profit": "Net Operating Profit",
        "rep.pnl_title": "Commercial Profit & Loss Analysis",
        "rep.accounting_disclosures": "Authoritative Accounting Notes",
        "rep.disclosure_purchases": "Merchandise Purchases (Capitalized, not an operating expense)",
        "rep.disclosure_payments": "Supplier Payments (Liability settlements, not an operating expense)",

        // Settings
        "set.title": "System Settings & Data Management",
        "set.edition": "Medisales Pharmacy & Retail POS • Commercial Edition 2.4",
        "set.language_card_title": "Language & Localization / ဘာသာစကား",
        "set.language_card_subtitle": "Select interface display language",
        "set.lang_en": "English (US)",
        "set.lang_my": "မြန်မာစာ (Myanmar Unicode)",
        "set.lang_saved": "Language preference updated and persisted successfully.",
        "set.active_storage": "Active Database Storage",
        "set.local_instance": "Local embedded SQLite instance",
        "set.physical_location": "Physical File Location:",
        "set.file_size": "Active File Size:",
        "set.concurrency": "Concurrency:",
        "set.cloud_dep": "Cloud Dependency:",
        "set.safety": "Safety Guarantee:",
        "set.backup_title": "Database Backup",
        "set.backup_subtitle": "Online non-blocking snapshot",
        "set.backup_desc": "Creates a complete snapshot of all products, medicine batches, sales history, and audit trails. Uses SQLite online backup API so cashier operations continue without interruption.",
        "set.backup_btn": "Create Local Database Backup",
        "set.restore_title": "Database Restore",
        "set.restore_subtitle": "Safe replacement from backup",
        "set.restore_desc": "Restores shop records from a previously saved backup file. Before overwriting any records, Medisales automatically takes a timestamped safety copy of your current active database.",
        "set.restore_btn": "Restore From Backup File...",
        "set.recon_title": "End-of-Day Cash Reconciliation",
        "set.recon_subtitle": "Drawer denomination counter & balance",
        "set.recon_desc": "Count physical cash notes in your drawer and compare directly with today's POS cash sales.",
        "set.recon_reset": "Reset Form",
        "set.recon_other": "Other / Coins (Ks)",
        "set.recon_counted": "Total Cash Counted in Drawer:",
        "set.recon_expected": "Today's System Cash Sales:",
        "set.recon_variance": "Drawer Discrepancy:",
        "set.recon_balanced": "Balanced (0 Ks)",
        "set.recon_surplus": "Surplus",
        "set.recon_shortage": "Shortage",
        "set.store_profile": "Store Operational Profile",
        "set.store_profile_sub": "Retail pharmacy system parameters",
        "set.trading_name": "Trading Name",
        "set.primary_currency": "Primary Currency",
        "set.precision": "Accounting Precision",
        "set.expiry_rule": "Inventory Expiry Rule",
        "set.audit_integrity": "Audit Integrity",
        "set.denom_50k": "50,000 Ks notes",
        "set.denom_20k": "20,000 Ks notes",
        "set.denom_10k": "10,000 Ks notes",
        "set.denom_5k": "5,000 Ks notes",
        "set.denom_1k": "1,000 Ks notes",
        "set.denom_500": "500 Ks notes"
    },

    my: {
        // App Chrome & Navigation
        "app.name": "မေဒီဆေးအရောင်း",
        "app.subtitle": "ဆေးဆိုင်နှင့် ကုန်စုံဆိုင် စီမံခန့်ခွဲမှုစနစ်",
        "app.pos_badge": "အရောင်း",
        "app.offline_status": "အော့ဖ်လိုင်းစနစ် အပြည့်အဝအလုပ်လုပ်နေသည်",
        "app.wal_status": "SQLite WAL • v2.4",
        "app.active_badge": "အသင့်ရှိ",
        "app.central_counter": "ပင်မကောင်တာ",

        "nav.group.dispensing": "အရောင်းနှင့် ဆေးထုတ်ပေးခြင်း",
        "nav.group.procurement": "အဝယ်နှင့် အသုံးစရိတ်များ",
        "nav.group.finance": "ဘဏ္ဍာရေးနှင့် စနစ်ပိုင်းဆိုင်ရာ",

        "nav.dashboard": "ပင်မစာမျက်နှာ",
        "nav.sales": "အရောင်း / ကောင်တာ",
        "nav.products": "ကုန်ပစ္စည်းများ စာရင်း",
        "nav.inventory": "လက်ကျန်နှင့် သက်တမ်း (FEFO)",
        "nav.purchases": "အဝယ်နှင့် ကုန်လက်ခံခြင်း",
        "nav.suppliers": "ကုန်သွင်းသူများ စာရင်း",
        "nav.expenses": "ဆိုင်သုံးစရိတ်များ",
        "nav.reports": "ဘဏ္ဍာရေး အစီရင်ခံစာများ",
        "nav.settings": "စနစ်ဆက်တင်နှင့် ဒေတာဘေ့စ်",

        "badge.dispensing": "အရောင်း",
        "badge.procurement": "အဝယ်",
        "badge.finance": "ဘဏ္ဍာရေး",

        "subtitle.dashboard": "ဆိုင်၏ နေ့စဉ်အခြေအနေနှင့် အရောင်းအကျဉ်းချုပ်",
        "subtitle.sales": "ငွေကိုင်ကောင်တာနှင့် ဘောက်ချာထုတ်ပေးခြင်း",
        "subtitle.products": "ဆေးဝါးနှင့် လူသုံးကုန်ပစ္စည်းများ စာရင်း",
        "subtitle.inventory": "ဆိုင်တွင်းလက်ကျန်နှင့် ဆေးဝါးသက်တမ်းစောင့်ကြည့်ခြင်း",
        "subtitle.purchases": "ကုန်ပစ္စည်းအဝယ်နှင့် ကုန်လက်ခံမှု ဘောက်ချာများ",
        "subtitle.suppliers": "ကုန်သွင်းသူများနှင့် ပေးရန်ကျန်ငွေစာရင်း",
        "subtitle.expenses": "ဆိုင်၏ လည်ပတ်မှုအထွေထွေ အသုံးစရိတ်များ",
        "subtitle.reports": "အမြတ်/အရှုံးနှင့် ဘဏ္ဍာရေး အစီရင်ခံစာများ",
        "subtitle.settings": "ဒေတာဘေ့စ်သိမ်းဆည်းမှုနှင့် စနစ်ဆက်တင်များ",

        // Common Buttons & Actions
        "btn.save": "သိမ်းဆည်းမည်",
        "btn.cancel": "မလုပ်တော့ပါ",
        "btn.close": "ပိတ်မည်",
        "btn.confirm": "အတည်ပြုမည်",
        "btn.delete": "ဖျက်မည်",
        "btn.edit": "ပြင်ဆင်မည်",
        "btn.add": "အသစ်ထည့်မည်",
        "btn.export_excel": "Excel သို့ ထုတ်ယူမည်",
        "btn.refresh": "အသစ်ပြန်တင်မည်",
        "btn.retry": "ပြန်လည်ကြိုးစားမည်",
        "btn.print": "ပရင့်ထုတ်မည်",
        "btn.print_receipt": "ပြေစာ ထုတ်မည်",
        "btn.done": "ပြီးပါပြီ / ပိတ်မည်",
        "btn.void": "အရောင်း ပယ်ဖျက်မည်",
        "btn.filter": "စစ်ထုတ်မည်",
        "btn.clear": "ရှင်းလင်းမည်",
        "btn.search": "ရှာဖွေမည်",
        "btn.processing": "ဆောင်ရွက်နေပါသည်...",

        // Status Badges & Alerts
        "status.completed": "အောင်မြင်သည်",
        "status.voided": "ပယ်ဖျက်ထားသည်",
        "status.active": "အသုံးပြုဆဲ",
        "status.inactive": "ပိတ်ထားသည်",
        "status.expired": "သက်တမ်းကုန်ပြီ",
        "status.expiring_soon": "မကြာမီ သက်တမ်းကုန်မည်",
        "status.unknown_expiry": "သက်တမ်းမသိရပါ",
        "status.normal": "ပုံမှန်",
        "status.low_stock": "လက်ကျန်နည်းနေသည်",
        "status.out_of_stock": "ပစ္စည်းပြတ်နေသည်",
        "status.connected": "ချိတ်ဆက်ပြီး",
        "status.no_expiry": "သက်တမ်းမရှိပါ",

        // Common Table & Form Headers
        "col.id": "အမှတ်စဉ်",
        "col.name": "အမည်",
        "col.category": "အမျိုးအစား",
        "col.unit": "ယူနစ်",
        "col.price": "ရောင်းဈေး",
        "col.stock": "လက်ကျန်",
        "col.value": "တန်ဖိုး (ကျပ်)",
        "col.status": "အခြေအနေ",
        "col.actions": "လုပ်ဆောင်ချက်",
        "col.date": "ရက်စွဲ",
        "col.date_time": "ရက်စွဲနှင့် အချိန်",
        "col.invoice": "ဘောက်ချာနံပါတ်",
        "col.receipt": "ပြေစာနံပါတ်",
        "col.total": "စုစုပေါင်း (ကျပ်)",
        "col.amount": "ငွေပမာဏ (ကျပ်)",
        "col.paid": "ပေးချေပြီး (ကျပ်)",
        "col.balance": "ကျန်ငွေ (ကျပ်)",
        "col.supplier": "ကုန်သွင်းသူ",
        "col.phone": "ဖုန်းနံပါတ်",
        "col.batch_no": "အသုတ်/ဘတ်ခ်ျ #",
        "col.expiry_date": "သက်တမ်းကုန်ရက်",
        "col.qty": "အရေအတွက်",
        "col.cost": "ဝယ်ဈေး (ကျပ်)",
        "col.type": "အမျိုးအစား",
        "col.description": "ဖော်ပြချက်",

        // Messages & Toasts
        "msg.loading": "ဒေတာများ တင်ယူနေပါသည်...",
        "msg.no_data": "စာရင်းမှတ်တမ်း မရှိသေးပါ။",
        "msg.error_title": "ဒေတာများ တင်ယူ၍ မရနိုင်ပါ",
        "msg.export_success": "Excel ဖိုင် ထုတ်ယူမှု အောင်မြင်ပါသည်-",
        "msg.export_failed": "Excel ဖိုင် ထုတ်ယူမှု မအောင်မြင်ပါ-",

        // Dashboard
        "dash.revenue_today": "ယနေ့ စုစုပေါင်း အရောင်းရငွေ",
        "dash.gross_profit_today": "ယနေ့ အကြမ်းဖျင်းအမြတ်",
        "dash.completed_orders": "အရောင်းဘောက်ချာ စုစုပေါင်း",
        "dash.inventory_valuation": "ဆိုင်တွင်း ပစ္စည်းစုစုပေါင်း တန်ဖိုး",
        "dash.recent_sales": "လတ်တလော အရောင်းမှတ်တမ်းများ",
        "dash.low_stock_alerts": "လက်ကျန်နည်းနေသော ပစ္စည်းများ သတိပေးချက်",
        "dash.view_all_sales": "အရောင်းအားလုံး ကြည့်ရန်",
        "dash.view_inventory": "လက်ကျန်စာရင်း ကြည့်ရန်",
        "dash.no_low_stock": "လက်ကျန်နည်းနေသော ပစ္စည်းမရှိပါ။ ပစ္စည်းများ လုံလောက်စွာ ရှိနေပါသည်။",
        "dash.quick_pos": "အရောင်းကောင်တာ ဖွင့်မည် (F1)",
        "dash.quick_product": "ကုန်ပစ္စည်းအသစ် ထည့်မည်",

        // Sales / POS
        "sales.search_placeholder": "ကုန်ပစ္စည်းအမည် သို့မဟုတ် အမျိုးအစားဖြင့် ရှာဖွေပါ...",
        "sales.all_categories": "အမျိုးအစား အားလုံး",
        "sales.cart_title": "လက်ရှိ ဝယ်ယူသူ ဘောက်ချာ",
        "sales.cart_items": "ခု",
        "sales.cart_empty": "ပစ္စည်းမရွေးရသေးပါ။ အထက်မှ ပစ္စည်းကို နှိပ်၍ ထည့်သွင်းပါ။",
        "sales.clear_cart": "အားလုံးဖျက်မည်",
        "sales.subtotal": "စုစုပေါင်း ကျသင့်ငွေ",
        "sales.total_due": "ကျသင့်ငွေ စုစုပေါင်း",
        "sales.tendered": "ပေးချေငွေ",
        "sales.change_due": "ပြန်အမ်းငွေ",
        "sales.exact_cash": "အကြွေစေ့စပ်",
        "sales.complete_sale": "အရောင်းသိမ်းပြီး ပြေစာထုတ်မည် (F2)",
        "sales.insufficient_cash": "ပေးချေငွေသည် ကျသင့်ငွေထက် နည်းနေပါသည်။",
        "sales.stock_warning": "လက်ကျန်မလုံလောက်တော့သဖြင့် ထပ်ထည့်၍ မရတော့ပါ။",
        "sales.history_tab": "အရောင်းမှတ်တမ်းများ",
        "sales.pos_tab": "အရောင်းကောင်တာ",
        "sales.filter_start": "စတင်သည့်ရက်",
        "sales.filter_end": "ပြီးဆုံးသည့်ရက်",
        "sales.receipt_title": "မေဒီဆေး ဆေးဆိုင်နှင့် ကုန်စုံဆိုင်",
        "sales.receipt_subtitle": "တရားဝင် ငွေလက်ခံပြေစာ",
        "sales.receipt_thanks": "ဝယ်ယူအားပေးမှုကို အထူးကျေးဇူးတင်ရှိပါသည်။ ကုန်ပစ္စည်းများ စစ်ဆေးပြီးဖြစ်ပါသည်။",
        "sales.void_confirm_title": "အရောင်းဘောက်ချာ ပယ်ဖျက်ခြင်း",
        "sales.void_confirm_msg": "ဤအရောင်းဘောက်ချာကို ပယ်ဖျက်ရန် သေချာပါသလား? ရောင်းချခဲ့သော ပစ္စည်းများသည် လက်ကျန်စာရင်းသို့ အလိုအလျောက် ပြန်လည်ရောက်ရှိသွားမည်ဖြစ်ပါသည်။",

        // Products
        "prod.add_button": "ကုန်ပစ္စည်းအသစ် ထည့်မည်",
        "prod.filter_search": "ကုန်ပစ္စည်း ရှာဖွေရန်...",
        "prod.filter_category": "အမျိုးအစားအလိုက် စစ်ထုတ်ရန်",
        "prod.filter_type": "ပစ္စည်းအမျိုးအစား စစ်ထုတ်ရန်",
        "prod.type_all": "ပစ္စည်းအားလုံး",
        "prod.type_medicine": "ဆေးဝါးပစ္စည်းများသာ",
        "prod.type_general": "လူသုံးကုန်ပစ္စည်းများသာ",
        "prod.modal_add_title": "ကုန်ပစ္စည်းအသစ် ထည့်သွင်းခြင်း",
        "prod.modal_edit_title": "ကုန်ပစ္စည်း အချက်အလက် ပြင်ဆင်ခြင်း",
        "prod.field_name": "ကုန်ပစ္စည်း အမည်",
        "prod.field_category": "အမျိုးအစား",
        "prod.field_unit": "ရေတွက်ပုံယူနစ် (ဥပမာ- ကတ်၊ ဘူး၊ ပုလင်း)",
        "prod.field_price": "ရောင်းဈေး (ကျပ်)",
        "prod.field_min_stock": "အနည်းဆုံး လက်ကျန်သတိပေးချက်",
        "prod.field_is_medicine": "ဆေးဝါးပစ္စည်းဖြစ်သည် (အသုတ်နှင့် သက်တမ်းကုန်ရက် FEFO စစ်ဆေးမည်)",
        "prod.field_is_active": "ရောင်းချခွင့် အသက်ဝင်သည်",

        // Inventory
        "inv.tab_stock": "လက်ကျန်ပစ္စည်းနှင့် တန်ဖိုး",
        "inv.tab_batches": "ဆေးဝါးအသုတ်များနှင့် သက်တမ်း (FEFO)",
        "inv.tab_movements": "ပစ္စည်းအဝင်/အထွက် မှတ်တမ်း",
        "inv.filter_all_batches": "လက်ကျန်ရှိသော အသုတ်အားလုံး",
        "inv.filter_expiring_soon": "ရက်ပေါင်း ၉၀ အတွင်း သက်တမ်းကုန်မည့်အသုတ်များ",
        "inv.filter_expired": "သက်တမ်းကုန်ပြီးသော အသုတ်များ",
        "inv.filter_unknown": "သက်တမ်းကုန်ရက် မသိရသောအသုတ်များ",
        "inv.total_valuation": "ဆိုင်တွင်း ပစ္စည်းစုစုပေါင်း တန်ဖိုး",
        "inv.total_skus": "ပစ္စည်းအမျိုးအမည် စုစုပေါင်း",

        // Purchases
        "pur.add_button": "အဝယ်ဘောက်ချာ အသစ်သွင်းမည်",
        "pur.modal_title": "အဝယ်ပစ္စည်းနှင့် ဘောက်ချာ မှတ်တမ်းတင်ခြင်း",
        "pur.invoice_no": "အဝယ်ဘောက်ချာ နံပါတ်",
        "pur.supplier": "ကုန်သွင်းသူ",
        "pur.date": "ဝယ်ယူသည့်ရက်စွဲ",
        "pur.items_header": "ဝယ်ယူသော ကုန်ပစ္စည်းများ စာရင်း",
        "pur.add_line": "+ ပစ္စည်းစာရင်း ထပ်ထည့်မည်",
        "pur.amount_paid": "ချက်ချင်း ပေးချေငွေ (ကျပ်)",
        "pur.total_amount": "ကျသင့်ငွေ စုစုပေါင်း (ကျပ်)",
        "pur.outstanding": "ကုန်သွင်းသူထံ ပေးရန်ကျန်ငွေ (ကျပ်)",

        // Suppliers
        "sup.add_button": "ကုန်သွင်းသူအသစ် ထည့်မည်",
        "sup.modal_add_title": "ကုန်သွင်းသူအသစ် မှတ်ပုံတင်ခြင်း",
        "sup.modal_edit_title": "ကုန်သွင်းသူ အချက်အလက် ပြင်ဆင်ခြင်း",
        "sup.field_name": "ကုန်သွင်းသူ / ကုမ္ပဏီအမည်",
        "sup.field_phone": "ဆက်သွယ်ရန် ဖုန်းနံပါတ်",
        "sup.field_address": "လိပ်စာ / မြို့နယ်",
        "sup.btn_record_payment": "ကြွေးကျန်ငွေ ပေးချေမည်",
        "sup.modal_payment_title": "ကုန်သွင်းသူထံ ကြွေးကျန် ပေးချေမှု မှတ်တမ်း",
        "sup.payment_amount": "ပေးချေငွေ ပမာဏ (ကျပ်)",
        "sup.payment_date": "ပေးချေသည့် ရက်စွဲ",
        "sup.payment_notes": "ပေးချေမှုဆိုင်ရာ မှတ်ချက်",

        // Expenses
        "exp.add_button": "ဆိုင်သုံးစရိတ် အသစ်ထည့်မည်",
        "exp.modal_title": "ဆိုင်လည်ပတ်မှု အသုံးစရိတ် မှတ်တမ်းတင်ခြင်း",
        "exp.field_date": "အသုံးစရိတ် ရက်စွဲ",
        "exp.field_category": "စရိတ်အမျိုးအစား",
        "exp.field_amount": "ငွေပမာဏ (ကျပ်)",
        "exp.field_desc": "အသုံးစရိတ် ဖော်ပြချက်",
        "exp.cat_rent": "ဆိုင်ခန်းငှားရမ်းခ",
        "exp.cat_utilities": "မီးခနှင့် ရေဖိုး",
        "exp.cat_salaries": "ဝန်ထမ်းလစာ",
        "exp.cat_transport": "သယ်ယူပို့ဆောင်ခ",
        "exp.cat_supplies": "ဆိုင်သုံးပစ္စည်းများ",
        "exp.cat_maintenance": "ပြင်ဆင်ထိန်းသိမ်းစရိတ်",
        "exp.cat_other": "အထွေထွေ အသုံးစရိတ်",
        "exp.notice": "ဆိုင်သုံးစရိတ်များသာ ဖြစ်ပါသည်။ ကုန်ပစ္စည်းဝယ်ယူခြင်းနှင့် ကုန်သွင်းသူကြွေးမြီဆပ်ခြင်းများကို သီးခြားတွက်ချက်ပါသည်။",
        "exp.void_confirm_title": "အသုံးစရိတ် ပယ်ဖျက်ခြင်း",
        "exp.void_confirm_msg": "ဤအသုံးစရိတ်စာရင်းကို ပယ်ဖျက်ရန် သေချာပါသလား? ဆိုင်သုံးစရိတ် စုစုပေါင်းမှ နှုတ်ပယ်သွားမည်ဖြစ်ပါသည်။",

        // Reports
        "rep.tab_pnl": "အမြတ်/အရှုံး ရှင်းတမ်း",
        "rep.tab_products": "ပစ္စည်းအလိုက် အရောင်းစာရင်း",
        "rep.tab_categories": "အမျိုးအစားအလိုက် အရောင်းစာရင်း",
        "rep.tab_expenses": "အသုံးစရိတ် အသေးစိတ်စာရင်း",
        "rep.date_today": "ယနေ့",
        "rep.date_7d": "လွန်ခဲ့သော ၇ ရက်",
        "rep.date_30d": "လွန်ခဲ့သော ရက် ၃၀",
        "rep.date_month": "ယခုလ",
        "rep.date_custom": "ရက်စွဲ ရွေးချယ်မည်",
        "rep.kpi_revenue": "စုစုပေါင်း အရောင်းရငွေ",
        "rep.kpi_cogs": "ရောင်းကုန်များ၏ ဝယ်ရင်းကုန်ကျစရိတ် (COGS)",
        "rep.kpi_gross_profit": "အကြမ်းဖျင်း ရောင်းရငွေအမြတ်",
        "rep.kpi_expenses": "ဆိုင်လည်ပတ်မှု စရိတ်များ",
        "rep.kpi_net_profit": "အသားတင် လည်ပတ်မှုအမြတ်",
        "rep.pnl_title": "ဘဏ္ဍာရေး အမြတ်/အရှုံး စာရင်းစစ်တမ်း",
        "rep.accounting_disclosures": "တရားဝင် စာရင်းကိုင်စည်းမျဉ်းများ ဖော်ပြချက်",
        "rep.disclosure_purchases": "ပစ္စည်းအဝယ်စာရင်း (ပိုင်ဆိုင်မှုအဖြစ် သတ်မှတ်ပြီး ဆိုင်သုံးစရိတ်တွင် မပါဝင်ပါ)",
        "rep.disclosure_payments": "ကုန်သွင်းသူကြွေးကျန်ဆပ်ငွေ (ကြွေးမြီလျှော့ချခြင်းဖြစ်ပြီး ဆိုင်သုံးစရိတ်တွင် မပါဝင်ပါ)",

        // Settings
        "set.title": "စနစ်ဆက်တင်နှင့် ဒေတာဘေ့စ် စီမံခန့်ခွဲမှု",
        "set.edition": "မေဒီဆေး အရောင်းစနစ် • လုပ်ငန်းသုံးဗားရှင်း ၂.၄",
        "set.language_card_title": "ဘာသာစကား ရွေးချယ်မှု / Language",
        "set.language_card_subtitle": "စနစ်တစ်ခုလုံး ပြသမည့် ဘာသာစကားကို ရွေးချယ်ပါ",
        "set.lang_en": "English (အင်္ဂလိပ်ဘာသာ)",
        "set.lang_my": "မြန်မာစာ (Myanmar Unicode)",
        "set.lang_saved": "ဘာသာစကား ရွေးချယ်မှု သိမ်းဆည်းပြီးပါပြီ။",
        "set.active_storage": "အသုံးပြုနေသော ဒေတာဘေ့စ်",
        "set.local_instance": "စက်တွင်း အော့ဖ်လိုင်း SQLite ဒေတာဘေ့စ်",
        "set.physical_location": "ဖိုင်တည်နေရာ လမ်းကြောင်း:",
        "set.file_size": "ဖိုင်ဆိုဒ် ပမာဏ:",
        "set.concurrency": "ဒေတာထိန်းသိမ်းမှု:",
        "set.cloud_dep": "အင်တာနက် မှီခိုမှု:",
        "set.safety": "ဒေတာလုံခြုံမှု:",
        "set.backup_title": "ဒေတာဘေ့စ် မိတ္တူကူးယူခြင်း (Backup)",
        "set.backup_subtitle": "စနစ်လည်ပတ်နေစဉ် မိတ္တူကူးယူနိုင်သည်",
        "set.backup_desc": "ကုန်ပစ္စည်းများ၊ ဆေးဝါးအသုတ်များ၊ အရောင်းမှတ်တမ်းများနှင့် စာရင်းစစ်မှတ်တမ်းအားလုံးကို ပြည့်စုံစွာ မိတ္တူကူးယူပေးပါသည်။ အရောင်းလုပ်ငန်းများကို မရပ်တန့်စေဘဲ လုပ်ဆောင်နိုင်ပါသည်။",
        "set.backup_btn": "စက်တွင်း ဒေတာဘေ့စ် မိတ္တူကူးယူမည်",
        "set.restore_title": "ဒေတာဘေ့စ် ပြန်လည်တင်သွင်းခြင်း (Restore)",
        "set.restore_subtitle": "မိတ္တူဖိုင်မှ လုံခြုံစွာ ပြန်လည်ရယူခြင်း",
        "set.restore_desc": "ယခင်သိမ်းဆည်းထားသော မိတ္တူဖိုင်မှ ဒေတာများကို ပြန်လည်ရယူပါသည်။ လက်ရှိဒေတာများကို မအစားထိုးမီ စနစ်မှ အလိုအလျောက် အချိန်မှတ်တမ်းပါ လုံခြုံရေးမိတ္တူကို အရင်ကူးယူပေးပါသည်။",
        "set.restore_btn": "မိတ္တူဖိုင်မှ ဒေတာများ ပြန်တင်မည်...",
        "set.recon_title": "နေ့ကုန် ငွေစာရင်းစစ်ဆေးခြင်း (Cash Reconciliation)",
        "set.recon_subtitle": "ငွေပုံးတွင်းရှိ ငွေစက္ကူများနှင့် အရောင်းစာရင်း နှိုင်းယှဉ်ချက်",
        "set.recon_desc": "ငွေပုံးထဲရှိ ငွေစက္ကူများကို ရေတွက်ပြီး ယနေ့အရောင်းရငွေနှင့် တိုက်ဆိုင်စစ်ဆေးပါ။",
        "set.recon_reset": "ဇယားရှင်းမည်",
        "set.recon_other": "အခြားငွေ / အကြွေ (ကျပ်)",
        "set.recon_counted": "ငွေပုံးထဲ ရေတွက်ရရှိငွေ စုစုပေါင်း:",
        "set.recon_expected": "ယနေ့ စနစ်တွင်း အရောင်းရငွေ:",
        "set.recon_variance": "ငွေကွာဟချက် ပမာဏ:",
        "set.recon_balanced": "ငွေစာရင်း ကိုက်ညီပါသည် (၀ ကျပ်)",
        "set.recon_surplus": "ငွေပိုနေသည်",
        "set.recon_shortage": "ငွေလိုနေသည်",
        "set.store_profile": "ဆိုင်၏ လုပ်ငန်းဆိုင်ရာ အချက်အလက်များ",
        "set.store_profile_sub": "ဆေးဆိုင် လုပ်ငန်းသုံး စနစ်ကန့်သတ်ချက်များ",
        "set.trading_name": "ဆိုင်အမည်",
        "set.primary_currency": "အသုံးပြုသော ငွေကြေး",
        "set.precision": "စာရင်းကိုင် တန်ဖိုးထားရှိမှု",
        "set.expiry_rule": "ဆေးဝါးသက်တမ်း ထိန်းချုပ်မှု",
        "set.audit_integrity": "စာရင်းစစ် မှတ်တမ်းလုံခြုံမှု",
        "set.denom_50k": "၅၀,၀၀၀ ကျပ်တန် ငွေစက္ကူ",
        "set.denom_20k": "၂၀,၀၀၀ ကျပ်တန် ငွေစက္ကူ",
        "set.denom_10k": "၁၀,၀၀၀ ကျပ်တန် ငွေစက္ကူ",
        "set.denom_5k": "၅,၀၀၀ ကျပ်တန် ငွေစက္ကူ",
        "set.denom_1k": "၁,၀၀၀ ကျပ်တန် ငွေစက္ကူ",
        "set.denom_500": "၅၀၀ ကျပ်တန် ငွေစက္ကူ"
    }
};

let currentLanguage = 'en';

/**
 * Translate a key into the active language, falling back to English, then to fallback text.
 */
function t(key, fallback = null) {
    const langDict = I18N[currentLanguage] || I18N.en;
    if (langDict && langDict[key] !== undefined && langDict[key] !== "") {
        return langDict[key];
    }
    // Safe fallback to English
    if (I18N.en && I18N.en[key] !== undefined) {
        return I18N.en[key];
    }
    return fallback !== null ? fallback : key;
}

function getLanguage() {
    return currentLanguage;
}

async function setLanguage(lang) {
    if (lang !== 'en' && lang !== 'my') {
        lang = 'en';
    }
    currentLanguage = lang;
    document.documentElement.lang = lang;

    // Apply font priority to body
    if (lang === 'my') {
        document.body.classList.add('font-myanmar');
    } else {
        document.body.classList.remove('font-myanmar');
    }

    // Persist to SQLite backend
    try {
        if (typeof callBackend === 'function') {
            await callBackend('set_language', lang);
        }
    } catch (e) {
        console.warn("Failed to persist language:", e);
    }

    // Re-render navigation & current active page
    if (typeof initNavigation === 'function') {
        initNavigation();
    }
    if (typeof updateNavState === 'function') {
        updateNavState();
    }
    if (typeof loadPageData === 'function' && typeof currentPage !== 'undefined') {
        loadPageData(currentPage);
    }
}

async function initLanguageFromBackend() {
    try {
        if (typeof callBackend === 'function') {
            const lang = await callBackend('get_language');
            currentLanguage = (lang === 'my') ? 'my' : 'en';
        }
    } catch (e) {
        console.warn("Could not load language from backend, defaulting to en:", e);
        currentLanguage = 'en';
    }
    document.documentElement.lang = currentLanguage;
    if (currentLanguage === 'my') {
        document.body.classList.add('font-myanmar');
    } else {
        document.body.classList.remove('font-myanmar');
    }
}

window.t = t;
window.getLanguage = getLanguage;
window.setLanguage = setLanguage;
window.initLanguageFromBackend = initLanguageFromBackend;
window.I18N = I18N;
