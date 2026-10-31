let salesProducts = [];
let salesCart = [];
let salesReceived = 0;
let salesDiscount = 0;
let salesPaymentType = 'cash'; // 'cash' or 'credit'
let salesSelectedCustomerId = '';
let salesCustomers = [];
let salesCustomerBalances = [];
let salesTab = 'pos'; // 'pos' or 'history'
let salesStart = '';
let salesEnd = '';
let salesCategoryFilter = 'all';
let isCheckingOut = false;

async function renderSales(container) {
    if (!salesStart) {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        salesStart = d.toISOString().split('T')[0];
        salesEnd = new Date().toISOString().split('T')[0];
    }

    // Header tab switcher
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="inline-flex rounded-md border border-slate-300 bg-slate-100 p-0.5">
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${salesTab === 'pos' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchSalesTab('pos')">
                    ${t('sales.pos_tab', 'Point of Sale (POS)')}
                </button>
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${salesTab === 'history' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchSalesTab('history')">
                    ${t('sales.history_tab', 'Sales History & Returns')}
                </button>
            </div>
        `;
    }

    if (salesTab === 'pos') {
        salesProducts = await callBackend('list_products');
        try {
            salesCustomers = await callBackend('list_customers');
            salesCustomerBalances = await callBackend('get_customer_balances');
        } catch(e) {
            console.error("Failed to fetch customer data for POS:", e);
        }
        _renderPosView(container);
    } else {
        await _renderHistoryView(container);
    }
}

window.switchSalesTab = function(tab) {
    salesTab = tab;
    renderSales(document.getElementById('content-area'));
};

window.updateSalesDates = function() {
    salesStart = document.getElementById('sales-start-date').value;
    salesEnd = document.getElementById('sales-end-date').value;
    renderSales(document.getElementById('content-area'));
};

window.exportSalesExcel = async function() {
    try {
        const res = await callBackend('export_sales_excel', salesStart, salesEnd);
        if (res && !res.cancelled) {
            showToast(`${t('msg.export_success', 'Spreadsheet successfully exported to:')}\n${res.file_path}`);
        }
    } catch (e) {
        showToast(`${t('msg.export_failed', 'Excel export failed:')} ${e}`, "error");
    }
};

function _renderPosView(container) {
    const categories = Array.from(new Set(salesProducts.map(p => p.category_name).filter(Boolean)));

    container.innerHTML = `
        <div class="flex flex-col lg:flex-row h-full gap-4">
            
            <!-- Left: Product Search & Selection -->
            <div class="flex-1 flex flex-col card min-w-0 h-full overflow-hidden">
                
                <!-- Search & Filters Toolbar -->
                <div class="p-3 border-b border-slate-200 bg-white space-y-2.5">
                    <div class="flex items-center gap-2">
                        <div class="relative flex-1">
                            <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            </span>
                            <input type="text" id="sales-search" class="form-input pl-8 text-xs py-2" placeholder="${t('sales.search_placeholder', 'Search medicine name, barcode, or general product...')}" oninput="salesSearch(this.value)" onkeydown="if(event.key==='Enter') salesSearchEnter()" autofocus>
                        </div>
                        <select id="sales-cat-filter" class="form-select w-44 text-xs font-semibold py-2" onchange="salesFilterCategory(this.value)">
                            <option value="all">${t('sales.all_categories', 'All Categories')}</option>
                            <option value="medicine">${t('prod.type_medicine', 'Medicines Only')}</option>
                            <option value="general">${t('prod.type_general', 'General Merchandise')}</option>
                            ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>

                    <!-- Filter pills -->
                    <div class="flex items-center gap-1.5 overflow-x-auto text-[11px] pb-0.5">
                        <button type="button" class="px-2.5 py-0.5 rounded-full border transition-colors ${salesCategoryFilter === 'all' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('all')">${t('prod.type_all', 'All Products')}</button>
                        <button type="button" class="px-2.5 py-0.5 rounded-full border transition-colors ${salesCategoryFilter === 'medicine' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('medicine')">${t('prod.type_medicine', 'Medicines (FEFO)')}</button>
                        <button type="button" class="px-2.5 py-0.5 rounded-full border transition-colors ${salesCategoryFilter === 'general' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('general')">${t('prod.type_general', 'General Goods')}</button>
                    </div>
                </div>

                <!-- Products Grid -->
                <div class="flex-1 overflow-auto p-2.5 bg-slate-50/50">
                    <div id="sales-product-grid" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-2.5">
                        <!-- Products rendered here -->
                    </div>
                </div>

                <!-- Footer Summary of in-stock items -->
                <div class="px-3.5 py-2 border-t border-slate-200 bg-white text-[11px] text-slate-500 flex justify-between items-center flex-shrink-0">
                    <span id="sales-products-count" class="font-medium">${t('status.active', 'Available Products')}: 0</span>
                    <span class="text-teal-800 font-medium">${t('sales.hint_click_add', 'Click product or press Enter to add')}</span>
                </div>
            </div>

            <!-- Right: POS Cart & Checkout Register -->
            <div class="w-full lg:w-[420px] flex flex-col card flex-shrink-0 h-full overflow-hidden">
                
                <!-- Cart Header -->
                <div class="px-3.5 py-2 border-b border-slate-200 bg-slate-50/80 flex justify-between items-center flex-shrink-0">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-slate-900 text-xs uppercase tracking-wide">${t('sales.cart_title', 'Current Bill')}</span>
                        <span id="sales-cart-badge" class="badge badge-neutral text-[10px]">0 lines</span>
                    </div>
                    <button class="text-xs text-rose-600 hover:text-rose-800 font-medium hover:underline flex items-center gap-1" onclick="salesConfirmClearCart()">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        ${t('sales.clear_cart', 'Clear')}
                    </button>
                </div>

                <!-- Cart Items List -->
                <div class="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 min-h-0 bg-white" id="sales-cart-items">
                    <!-- Cart items rendered here -->
                </div>

                <!-- Cart Totals & Cash Register Drawer -->
                <div class="border-t border-slate-200 bg-slate-50/90 p-3 space-y-2 flex-shrink-0 text-xs">
                    
                    <!-- Subtotal & Units -->
                    <div class="flex justify-between items-center text-slate-600">
                        <span>${t('sales.subtotal', 'Subtotal')}: <span id="sales-cart-units" class="font-mono text-slate-500 font-semibold">(0 units)</span></span>
                        <span id="sales-cart-subtotal" class="font-mono font-bold text-slate-800 text-sm">0 Ks</span>
                    </div>

                    <!-- Quick Round-off & Discount Section -->
                    <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/90 space-y-1.5 shadow-xs">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold text-amber-900 text-[11px] flex items-center gap-1">
                                <svg class="w-3 h-3 text-amber-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                                ${t('sales.discount_roundoff', 'Round-off / Discount')}:
                            </span>
                            <div class="flex items-center gap-1">
                                <input type="number" id="sales-discount-input" class="form-input text-xs font-mono font-bold w-20 py-0.5 text-right bg-white text-rose-700" placeholder="0" min="0" value="${salesDiscount || 0}" oninput="salesSetCustomDiscount(this.value)">
                                <span class="text-[10px] text-amber-800 font-semibold">Ks</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-1 text-[10px]">
                            <span class="text-amber-800 font-medium">Quick:</span>
                            <button type="button" class="px-2 py-0.5 bg-white border border-amber-300 rounded-md hover:bg-amber-100 text-amber-900 font-mono font-bold transition-colors" onclick="salesSetCustomDiscount(0)">0 Ks</button>
                            <button type="button" class="px-2 py-0.5 bg-white border border-amber-300 rounded-md hover:bg-amber-100 text-amber-900 font-mono font-bold transition-colors" onclick="salesRoundDiscount(500)" title="Round down to nearest 500 Ks">Round 500</button>
                            <button type="button" class="px-2 py-0.5 bg-white border border-amber-300 rounded-md hover:bg-amber-100 text-amber-900 font-mono font-bold transition-colors" onclick="salesRoundDiscount(1000)" title="Round down to nearest 1,000 Ks">Round 1,000</button>
                        </div>
                    </div>

                    <!-- Grand Net Total Due Banner -->
                    <div class="p-3.5 bg-gradient-to-r from-emerald-600 via-teal-700 to-teal-800 rounded-xl border border-emerald-500 text-white flex justify-between items-center shadow-md">
                        <div>
                            <span class="text-xs font-black uppercase tracking-wider text-emerald-100 block">${t('sales.total_due', 'Net Total Due')}</span>
                            <span class="text-[10px] text-teal-200 font-medium">${t('sales.payable_amount', 'Payable Amount')}</span>
                        </div>
                        <div id="sales-cart-total" data-subtotal="0" data-val="0" class="text-3xl font-black font-mono text-white tabular-nums whitespace-nowrap drop-shadow-sm">0 Ks</div>
                    </div>

                    <!-- Payment Mode Switcher (Cash vs Credit) -->
                    <div class="grid grid-cols-2 gap-1.5 p-1 bg-slate-200/70 rounded-xl">
                        <button type="button" class="py-1.5 px-2 text-xs font-bold rounded-lg transition-all duration-150 flex items-center justify-center gap-1.5 ${salesPaymentType === 'cash' ? 'bg-white text-teal-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="salesSetPaymentType('cash')">
                            <span>💵</span>
                            <span>${t('sales.cash_mode', 'Cash Sale')}</span>
                        </button>
                        <button type="button" class="py-1.5 px-2 text-xs font-bold rounded-lg transition-all duration-150 flex items-center justify-center gap-1.5 ${salesPaymentType === 'credit' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="salesSetPaymentType('credit')">
                            <span>📒</span>
                            <span>${t('sales.credit_mode', 'Credit Sale')}</span>
                        </button>
                    </div>

                    <!-- Mode 1: Cash Checkout Register -->
                    <div id="sales-cash-drawer" class="${salesPaymentType === 'cash' ? '' : 'hidden'} space-y-1.5">
                        <div class="flex justify-between items-center">
                            <label class="form-label mb-0 text-[11px]" for="sales-received">${t('sales.tendered', 'Amount Tendered (Kyat)')}</label>
                            <button type="button" class="text-[11px] text-teal-800 hover:underline font-semibold" onclick="salesExactAmount()">${t('sales.exact_cash', 'Exact Tender')}</button>
                        </div>
                        <input type="number" id="sales-received" class="form-input text-sm font-bold font-mono text-slate-900 py-1" placeholder="0" min="0" oninput="salesCalcChange()" onkeydown="if(event.key==='Enter') salesCheckout()">
                        
                        <!-- Quick Cash Chips (Banknote Colors: Blue=1,000, Rose=5,000, Purple=10,000) -->
                        <div class="flex items-center justify-between text-[10px] text-slate-500">
                            <span class="font-medium">Quick Notes (+):</span>
                            <div class="flex gap-1.5">
                                <button type="button" class="px-2.5 py-1 text-[10px] font-mono bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 text-blue-900 font-bold shadow-xs active:scale-95 transition-all" onclick="salesAddCash(1000)">+1,000</button>
                                <button type="button" class="px-2.5 py-1 text-[10px] font-mono bg-rose-50 border border-rose-300 rounded-md hover:bg-rose-100 text-rose-900 font-bold shadow-xs active:scale-95 transition-all" onclick="salesAddCash(5000)">+5,000</button>
                                <button type="button" class="px-2.5 py-1 text-[10px] font-mono bg-purple-50 border border-purple-300 rounded-md hover:bg-purple-100 text-purple-900 font-bold shadow-xs active:scale-95 transition-all" onclick="salesAddCash(10000)">+10,000</button>
                            </div>
                        </div>

                        <!-- Change Banner -->
                        <div id="sales-change-banner" class="flex justify-between items-center px-3 py-2 rounded-lg border border-slate-200/90 bg-white text-xs shadow-xs">
                            <span class="font-semibold text-slate-600">${t('sales.change_due', 'Change Due:')}</span>
                            <span id="sales-change" class="font-mono font-bold text-teal-800 tabular-nums whitespace-nowrap">0 Ks</span>
                        </div>
                    </div>

                    <!-- Mode 2: Credit Checkout Drawer -->
                    <div id="sales-credit-drawer" class="${salesPaymentType === 'credit' ? '' : 'hidden'} space-y-2 p-2 bg-amber-50/70 rounded border border-amber-200">
                        <div class="flex items-center justify-between">
                            <label class="form-label mb-0 text-[11px] font-bold text-amber-950">${t('cust.select_customer', 'Select Customer')} *</label>
                            <button type="button" class="text-[10px] text-amber-900 font-bold hover:underline flex items-center gap-0.5" onclick="salesQuickAddCustomer()">
                                + ${t('cust.add_new', 'New Customer')}
                            </button>
                        </div>
                        <select id="sales-customer-select" class="form-select text-xs font-semibold py-1 bg-white" onchange="salesOnCustomerChange(this.value)">
                            <option value="">-- ${t('cust.choose', 'Select Customer')} --</option>
                            ${salesCustomers.filter(c => c.is_active).map(c => {
                                const bal = salesCustomerBalances.find(b => b.customer_id === c.id);
                                const debt = bal ? bal.outstanding_balance : 0;
                                const debtStr = debt > 0 ? ` (Debt: ${formatMoney(debt)})` : '';
                                return `<option value="${c.id}" ${salesSelectedCustomerId == c.id ? 'selected' : ''}>${escapeHtml(c.name)} - ${escapeHtml(c.phone || 'No phone')}${debtStr}</option>`;
                            }).join('')}
                        </select>

                        <!-- Customer Debt Summary -->
                        <div id="sales-customer-debt-info" class="text-[11px] space-y-1 bg-white p-2 rounded border border-amber-200">
                            <div class="flex justify-between text-slate-600">
                                <span>${t('cust.current_debt', 'Current Debt')}:</span>
                                <span id="sales-curr-debt" class="font-mono font-bold text-slate-800">0 Ks</span>
                            </div>
                            <div class="flex justify-between items-center pt-1 border-t border-slate-100">
                                <span>${t('cust.upfront_cash', 'Upfront Cash Paid')}:</span>
                                <input type="number" id="sales-credit-upfront" class="form-input text-xs font-mono font-bold w-24 py-0.5 text-right" placeholder="0" min="0" value="0" oninput="salesCalcCredit()">
                            </div>
                            <div class="flex justify-between text-amber-900 font-semibold pt-1 border-t border-slate-100">
                                <span>${t('cust.added_credit', 'Added to Credit Book')}:</span>
                                <span id="sales-added-debt" class="font-mono font-bold text-amber-700">0 Ks</span>
                            </div>
                            <div class="flex justify-between font-bold text-rose-800 pt-1 border-t border-slate-200">
                                <span>${t('cust.new_total_debt', 'New Total Debt')}:</span>
                                <span id="sales-new-debt" class="font-mono font-bold">0 Ks</span>
                            </div>
                        </div>
                    </div>

                    <!-- Complete Sale Button -->
                    <button id="sales-checkout-btn" class="btn ${salesPaymentType === 'credit' ? 'bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white border-amber-600 shadow-md' : 'bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white border-emerald-600 shadow-md'} w-full py-3 text-xs font-bold flex items-center justify-center gap-1.5 active:scale-[0.98] transition-all" onclick="salesCheckout()">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        <span id="sales-checkout-btn-label">${salesPaymentType === 'credit' ? t('sales.record_credit_sale', 'Record to Credit Book (Enter)') : t('sales.complete_sale', 'Complete Sale & Print (F2)')}</span>
                    </button>

                </div>
            </div>

        </div>
    `;

    _renderSalesProducts('');
    _renderSalesCart();
}

function _renderSalesProducts(query) {
    const grid = document.getElementById('sales-product-grid');
    if (!grid) return;
    
    let activeStock = salesProducts.filter(p => p.is_active && p.current_stock > 0);
    
    if (salesCategoryFilter === 'medicine') {
        activeStock = activeStock.filter(p => p.is_medicine);
    } else if (salesCategoryFilter === 'general') {
        activeStock = activeStock.filter(p => !p.is_medicine);
    } else if (salesCategoryFilter !== 'all') {
        activeStock = activeStock.filter(p => p.category_name === salesCategoryFilter);
    }

    const filtered = (typeof window.filterAndRankItems === 'function') 
        ? window.filterAndRankItems(activeStock, query, (p) => ({
            primary: p.name,
            secondary: [p.category_name, p.barcode, p.unit_measure]
        }))
        : activeStock.filter(p => !query || p.name.toLowerCase().includes(query.toLowerCase()));

    const countEl = document.getElementById('sales-products-count');
    if (countEl) countEl.textContent = `${t('status.active', 'Available Products')}: ${filtered.length}`;

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-12 text-center text-slate-400">
                <svg class="w-8 h-8 mx-auto text-slate-300 mb-1.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <p class="text-xs font-medium text-slate-600">${t('msg.no_data', 'No in-stock products match your filter.')}</p>
                <p class="text-[11px] text-slate-400 mt-0.5">Try another search term or record a new purchase invoice.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(p => {
        const isMed = Boolean(p.is_medicine);
        const isLow = p.current_stock <= (p.min_stock_level || 5);
        const highlightedName = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(p.name, query)
            : escapeHtml(p.name);
        const categoryLabel = p.category_name || (isMed ? 'Medicine' : 'General');
        const highlightedCategory = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(categoryLabel, query)
            : escapeHtml(categoryLabel);

        return `
            <div class="bg-white border border-slate-200/90 rounded-xl p-3 shadow-xs hover:border-teal-600 hover:shadow-md cursor-pointer transition-all duration-150 flex flex-col justify-between min-h-[110px] group" onclick="salesAddToCart(${p.id})">
                <div>
                    <div class="flex items-center justify-between gap-1 mb-1">
                        <span class="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full ${isMed ? 'bg-teal-50 text-teal-800 border border-teal-200' : 'bg-slate-100 text-slate-700 border border-slate-200'}">
                            ${isMed ? t('prod.type_medicine', 'Medicine (FEFO)') : t('prod.type_general', 'General')}
                        </span>
                        <span class="text-[11px] font-mono font-medium ${isLow ? 'text-amber-800 font-bold' : 'text-slate-600'}">
                            ${p.current_stock} ${p.unit_measure || 'units'}
                        </span>
                    </div>
                    <h4 class="font-bold text-slate-900 text-xs leading-snug group-hover:text-teal-800 break-words" title="${escapeHtml(p.name)}">
                        ${highlightedName}
                    </h4>
                    <p class="text-[10px] text-slate-500 mt-0.5">${highlightedCategory}</p>
                </div>
                
                <div class="mt-2 pt-1.5 border-t border-slate-100">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold font-mono text-teal-800 tabular-nums whitespace-nowrap">
                            ${formatMoney(p.selling_price)} / ${escapeHtml(p.unit_measure || 'unit')}
                        </span>
                        <span class="btn btn-sm btn-subtle text-teal-800 group-hover:bg-teal-700 group-hover:text-white transition-colors py-0.5 px-2.5 text-[11px] rounded-md font-bold">
                            + ${t('btn.add', 'Add')}
                        </span>
                    </div>
                    ${(p.packagings && p.packagings.length > 0) ? `
                        <div class="flex flex-wrap gap-1 mt-1.5 pt-1 border-t border-dashed border-slate-200" onclick="event.stopPropagation()">
                            <button type="button" class="text-[10px] px-1.5 py-0.5 rounded-md border border-slate-300 bg-white hover:bg-slate-100 font-semibold text-slate-700 transition-colors" onclick="salesAddToCart(${p.id}, null)">
                                ${escapeHtml(p.unit_measure)}
                            </button>
                            ${p.packagings.map(pkg => `
                                <button type="button" class="text-[10px] px-1.5 py-0.5 rounded-md border border-teal-300 bg-teal-50 hover:bg-teal-100 font-bold text-teal-800 transition-colors" onclick="salesAddToCart(${p.id}, ${pkg.id})" title="${pkg.conversion_factor} ${escapeHtml(p.unit_measure)}">
                                    ${escapeHtml(pkg.unit_name)}: ${formatMoney(pkg.selling_price)}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

window.salesSearch = function(val) {
    _renderSalesProducts(val);
};

window.salesSearchEnter = function() {
    const input = document.getElementById('sales-search');
    const val = input ? input.value.trim() : '';
    if (!val) return;

    let activeStock = salesProducts.filter(p => p.is_active && p.current_stock > 0);
    if (salesCategoryFilter === 'medicine') {
        activeStock = activeStock.filter(p => p.is_medicine);
    } else if (salesCategoryFilter === 'general') {
        activeStock = activeStock.filter(p => !p.is_medicine);
    } else if (salesCategoryFilter !== 'all') {
        activeStock = activeStock.filter(p => p.category_name === salesCategoryFilter);
    }

    const matches = (typeof window.filterAndRankItems === 'function')
        ? window.filterAndRankItems(activeStock, val, (p) => ({
            primary: p.name,
            secondary: [p.category_name, p.barcode, p.unit_measure]
        }))
        : activeStock.filter(p => p.name.toLowerCase().includes(val.toLowerCase()));

    if (matches.length > 0) {
        salesAddToCart(matches[0].id);
        input.value = '';
        _renderSalesProducts('');
        showToast(`Added ${matches[0].name} to order.`);
    }
};

window.salesFilterCategory = function(cat) {
    salesCategoryFilter = cat;
    const catSelect = document.getElementById('sales-cat-filter');
    if (catSelect) catSelect.value = cat;
    _renderSalesProducts(document.getElementById('sales-search')?.value || '');
};

window.salesAddToCart = function(id, packagingId = null) {
    const p = salesProducts.find(x => x.id === id);
    if (!p) return;
    
    const pkg = packagingId ? (p.packagings || []).find(x => x.id === packagingId) : null;
    const factor = pkg ? pkg.conversion_factor : 1;
    const unitName = pkg ? pkg.unit_name : (p.unit_measure || 'unit');
    const unitPrice = pkg ? pkg.selling_price : p.selling_price;
    const cartKey = `${p.id}_${pkg ? pkg.id : 'base'}`;

    const currentBaseInCart = salesCart
        .filter(x => x.product.id === id)
        .reduce((sum, item) => sum + (item.qty * item.factor), 0);

    if (currentBaseInCart + factor > p.current_stock) {
        showToast(`${t('sales.stock_warning', 'Cannot add more')}: only ${p.current_stock} ${p.unit_measure || 'units'} in stock.`, "warning");
        return;
    }

    const existing = salesCart.find(x => x.cartKey === cartKey);
    if (existing) {
        existing.qty += 1;
    } else {
        salesCart.push({
            cartKey: cartKey,
            product: p,
            packaging: pkg,
            factor: factor,
            unit_name: unitName,
            unit_price: unitPrice,
            qty: 1
        });
    }
    _renderSalesCart();
};

window.salesUpdateQty = function(idx, delta) {
    const item = salesCart[idx];
    if (!item) return;
    const newQty = item.qty + delta;
    if (newQty <= 0) {
        salesCart.splice(idx, 1);
    } else {
        const otherBase = salesCart
            .filter((x, i) => i !== idx && x.product.id === item.product.id)
            .reduce((sum, x) => sum + (x.qty * x.factor), 0);
        if (otherBase + (newQty * item.factor) > item.product.current_stock) {
            showToast(`Cannot exceed available stock (${item.product.current_stock} ${item.product.unit_measure}).`, "warning");
            return;
        }
        item.qty = newQty;
    }
    _renderSalesCart();
};

window.salesSetQty = function(idx, val) {
    const item = salesCart[idx];
    if (!item) return;
    let qty = parseInt(val) || 0;
    if (qty <= 0) {
        salesCart.splice(idx, 1);
    } else {
        const otherBase = salesCart
            .filter((x, i) => i !== idx && x.product.id === item.product.id)
            .reduce((sum, x) => sum + (x.qty * x.factor), 0);
        const maxQty = Math.floor((item.product.current_stock - otherBase) / item.factor);
        if (qty > maxQty) {
            showToast(`Cannot exceed available stock. Max: ${maxQty} ${item.unit_name}.`, "warning");
            item.qty = Math.max(1, maxQty);
        } else {
            item.qty = qty;
        }
    }
    _renderSalesCart();
};

function _renderSalesCart() {
    const container = document.getElementById('sales-cart-items');
    if (!container) return;
    
    let subtotal = 0;
    let count = 0;
    
    if (salesCart.length === 0) {
        container.innerHTML = `
            <div class="h-44 flex flex-col items-center justify-center text-center p-4">
                <div class="w-12 h-12 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mb-2.5 border border-teal-100 shadow-sm">
                    <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                </div>
                <p class="text-xs font-bold text-slate-800">${t('sales.empty_cart_title', 'Scan barcode or select product to sell (F1)')}</p>
                <p class="text-[11px] text-slate-500 mt-1 max-w-xs leading-relaxed">${t('sales.empty_cart_sub', 'Search by product name, category, or scan barcode to add items to cart.')}</p>
                <div class="flex items-center gap-1.5 mt-3 flex-wrap justify-center">
                    <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] font-bold border border-slate-200">F1 ${t('nav.sales', 'Sale')}</span>
                    <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] font-bold border border-slate-200">Enter ${t('btn.add', 'Add')}</span>
                    <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] font-bold border border-slate-200">F4 ${t('sales.cash_tender', 'Checkout')}</span>
                </div>
            </div>
        `;
    } else {
        container.innerHTML = salesCart.map((c, i) => {
            const lineTotal = c.qty * c.unit_price;
            subtotal += lineTotal;
            count += c.qty;
            return `
                <div class="py-2 px-1.5 flex items-center justify-between gap-2 hover:bg-slate-50 rounded transition-colors group">
                    <div class="flex-1 min-w-0 pr-1">
                        <div class="text-xs font-bold text-slate-900 leading-snug break-words" title="${c.product.name}">
                            ${c.product.name}
                            ${c.packaging ? `<span class="badge badge-teal text-[10px] ml-1 font-bold">[${escapeHtml(c.unit_name)} x${c.factor}]</span>` : `<span class="text-slate-400 text-[10px] ml-1">(${escapeHtml(c.unit_name)})</span>`}
                        </div>
                        <div class="flex items-center gap-2 mt-0.5">
                            <span class="text-[11px] font-mono text-slate-600 font-semibold">${formatMoney(c.unit_price)}</span>
                            ${c.product.is_medicine ? `<span class="text-[9px] bg-teal-50 text-teal-800 px-1 rounded border border-teal-200">${t('sales.auto_fefo', 'Auto FEFO')}</span>` : ''}
                        </div>
                    </div>
                    
                    <!-- Qty Stepper -->
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        <div class="flex items-center border border-slate-300 rounded-md bg-white overflow-hidden shadow-xs">
                            <button type="button" class="w-5 h-5 flex items-center justify-center text-slate-600 hover:bg-slate-100 font-bold text-xs" onclick="salesUpdateQty(${i}, -1)">−</button>
                            <input type="number" class="w-9 h-5 text-center text-xs font-mono font-bold border-x border-slate-200 focus:outline-none" value="${c.qty}" min="1" max="${c.product.current_stock}" onchange="salesSetQty(${i}, this.value)">
                            <button type="button" class="w-5 h-5 flex items-center justify-center text-slate-600 hover:bg-slate-100 font-bold text-xs" onclick="salesUpdateQty(${i}, 1)">+</button>
                        </div>
                        
                        <div class="w-20 text-right font-mono font-bold text-xs text-slate-900 tabular-nums whitespace-nowrap">
                            ${formatMoney(lineTotal)}
                        </div>

                        <button type="button" class="text-slate-300 hover:text-rose-600 p-0.5 transition-colors" onclick="salesUpdateQty(${i}, -9999)" title="Remove item">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    const badgeEl = document.getElementById('sales-cart-badge');
    if (badgeEl) badgeEl.textContent = `${salesCart.length} lines`;

    const unitsEl = document.getElementById('sales-cart-units');
    if (unitsEl) unitsEl.textContent = `(${count} units)`;

    const subtotalEl = document.getElementById('sales-cart-subtotal');
    if (subtotalEl) subtotalEl.textContent = formatMoney(subtotal);

    if (salesDiscount > subtotal) {
        salesDiscount = subtotal;
        const discInput = document.getElementById('sales-discount-input');
        if (discInput) discInput.value = salesDiscount;
    }

    const netTotal = Math.max(0, subtotal - salesDiscount);

    const totalEl = document.getElementById('sales-cart-total');
    if (totalEl) {
        totalEl.textContent = formatMoney(netTotal);
        totalEl.dataset.val = netTotal;
        totalEl.dataset.subtotal = subtotal;
    }

    if (salesPaymentType === 'cash') {
        salesCalcChange();
    } else {
        salesCalcCredit();
    }
}

window.salesSetCustomDiscount = function(val) {
    const disc = parseInt(val) || 0;
    const totalEl = document.getElementById('sales-cart-total');
    const subtotal = totalEl ? (parseFloat(totalEl.dataset.subtotal) || 0) : 0;
    salesDiscount = Math.max(0, Math.min(disc, subtotal));
    const discInput = document.getElementById('sales-discount-input');
    if (discInput && discInput.value != salesDiscount) {
        discInput.value = salesDiscount;
    }
    _renderSalesCart();
};

window.salesRoundDiscount = function(roundTo) {
    const totalEl = document.getElementById('sales-cart-total');
    const subtotal = totalEl ? (parseFloat(totalEl.dataset.subtotal) || 0) : 0;
    if (subtotal <= 0) return;
    const rem = subtotal % roundTo;
    salesDiscount = rem;
    const discInput = document.getElementById('sales-discount-input');
    if (discInput) discInput.value = salesDiscount;
    _renderSalesCart();
};

window.salesSetPaymentType = function(type) {
    salesPaymentType = type;
    const cashDrawer = document.getElementById('sales-cash-drawer');
    const creditDrawer = document.getElementById('sales-credit-drawer');
    const checkoutBtn = document.getElementById('sales-checkout-btn');
    const checkoutLabel = document.getElementById('sales-checkout-btn-label');

    if (type === 'cash') {
        if (cashDrawer) cashDrawer.classList.remove('hidden');
        if (creditDrawer) creditDrawer.classList.add('hidden');
        if (checkoutBtn) {
            checkoutBtn.className = "btn btn-primary w-full py-2 text-xs font-bold shadow-xs flex items-center justify-center gap-1.5";
        }
        if (checkoutLabel) {
            checkoutLabel.textContent = t('sales.complete_sale', 'Complete Sale & Print (F2)');
        }
        salesCalcChange();
    } else {
        if (cashDrawer) cashDrawer.classList.add('hidden');
        if (creditDrawer) creditDrawer.classList.remove('hidden');
        if (checkoutBtn) {
            checkoutBtn.className = "btn btn-warning bg-amber-600 hover:bg-amber-700 text-white w-full py-2 text-xs font-bold shadow-xs flex items-center justify-center gap-1.5";
        }
        if (checkoutLabel) {
            checkoutLabel.textContent = t('sales.record_credit_sale', 'Record to Credit Book (Enter)');
        }
        salesCalcCredit();
    }
    _renderPosView(document.getElementById('content-area'));
};

window.salesOnCustomerChange = function(cid) {
    salesSelectedCustomerId = cid;
    salesCalcCredit();
};

window.salesCalcCredit = function() {
    const totalEl = document.getElementById('sales-cart-total');
    const netTotal = parseFloat(totalEl ? totalEl.dataset.val : 0) || 0;
    const upfrontInput = document.getElementById('sales-credit-upfront');
    const upfront = parseFloat(upfrontInput ? upfrontInput.value : 0) || 0;

    let currDebt = 0;
    if (salesSelectedCustomerId) {
        const bal = salesCustomerBalances.find(b => b.customer_id == salesSelectedCustomerId);
        if (bal) currDebt = bal.outstanding_balance;
    }

    const addedDebt = Math.max(0, netTotal - upfront);
    const newDebt = currDebt + addedDebt;

    const currDebtEl = document.getElementById('sales-curr-debt');
    if (currDebtEl) currDebtEl.textContent = formatMoney(currDebt);

    const addedDebtEl = document.getElementById('sales-added-debt');
    if (addedDebtEl) addedDebtEl.textContent = formatMoney(addedDebt);

    const newDebtEl = document.getElementById('sales-new-debt');
    if (newDebtEl) newDebtEl.textContent = formatMoney(newDebt);
};

window.salesQuickAddCustomer = function() {
    const html = `
        <div class="space-y-3 text-xs">
            <div>
                <label class="form-label">${t('col.customer_name', 'Customer Name')} *</label>
                <input type="text" id="quick-cust-name" class="form-input text-xs" placeholder="e.g. ဒေါ်သန်းသန်း" required autofocus>
            </div>
            <div>
                <label class="form-label">${t('col.phone', 'Phone Number')}</label>
                <input type="text" id="quick-cust-phone" class="form-input text-xs" placeholder="09xxxxxxxxx">
            </div>
            <div>
                <label class="form-label">${t('col.address', 'Address / Street')}</label>
                <input type="text" id="quick-cust-address" class="form-input text-xs" placeholder="e.g. အမှတ် ၄၅၊ သရက်တောလမ်း">
            </div>
        </div>
    `;

    openModal(t('cust.add_title', 'Register New Customer'), html, async () => {
        const name = document.getElementById('quick-cust-name').value.trim();
        const phone = document.getElementById('quick-cust-phone').value.trim();
        const address = document.getElementById('quick-cust-address').value.trim();
        if (!name) throw "Customer name is required.";

        const res = await callBackend('create_customer', name, phone, address, 'Added from POS');
        showToast(`Customer ${name} registered!`);
        salesCustomers = await callBackend('list_customers');
        salesCustomerBalances = await callBackend('get_customer_balances');
        if (res && res.customer_id) {
            salesSelectedCustomerId = String(res.customer_id);
        }
        _renderPosView(document.getElementById('content-area'));
    }, {
        saveText: t('btn.save', 'Add Customer'),
        maxWidth: 'max-w-sm'
    });
};

window.salesCalcChange = function() {
    const receivedEl = document.getElementById('sales-received');
    if (!receivedEl) return;
    const received = parseFloat(receivedEl.value) || 0;
    const totalEl = document.getElementById('sales-cart-total');
    const total = parseFloat(totalEl ? totalEl.dataset.val : 0) || 0;
    
    const change = received - total;
    const changeEl = document.getElementById('sales-change');
    const bannerEl = document.getElementById('sales-change-banner');
    if (!changeEl || !bannerEl) return;

    if (total === 0) {
        changeEl.textContent = "0 Ks";
        changeEl.className = "font-mono font-bold text-slate-400 tabular-nums";
        bannerEl.className = "flex justify-between items-center px-3 py-1.5 rounded border border-slate-200 bg-white text-xs";
        return;
    }

    if (received === 0) {
        changeEl.textContent = "0 Ks";
        changeEl.className = "font-mono text-[11px] text-slate-500";
        bannerEl.className = "flex justify-between items-center px-3 py-1.5 rounded border border-slate-200 bg-white text-xs";
    } else if (change < 0) {
        changeEl.textContent = `Short by ${formatMoney(Math.abs(change))}`;
        changeEl.className = "font-mono font-bold text-rose-700 tabular-nums text-xs";
        bannerEl.className = "flex justify-between items-center px-3 py-1.5 rounded border border-rose-300 bg-rose-50 text-xs";
    } else {
        changeEl.textContent = formatMoney(change);
        changeEl.className = "font-mono font-bold text-emerald-800 tabular-nums text-sm";
        bannerEl.className = "flex justify-between items-center px-3 py-1.5 rounded border border-emerald-300 bg-emerald-50 text-xs";
    }
};

window.salesExactAmount = function() {
    const totalEl = document.getElementById('sales-cart-total');
    const total = parseFloat(totalEl ? totalEl.dataset.val : 0) || 0;
    const rEl = document.getElementById('sales-received');
    if (rEl) {
        rEl.value = total;
        salesCalcChange();
    }
};

window.salesAddCash = function(amount) {
    const rEl = document.getElementById('sales-received');
    if (!rEl) return;
    const current = parseFloat(rEl.value) || 0;
    rEl.value = current + amount;
    salesCalcChange();
};

window.salesConfirmClearCart = function() {
    if (salesCart.length === 0) return;
    openConfirmModal(
        t('sales.clear_cart', 'Clear Current Order'),
        "Are you sure you want to remove all items from the current sales order?",
        () => {
            salesCart = [];
            salesDiscount = 0;
            const rEl = document.getElementById('sales-received');
            if (rEl) rEl.value = '';
            _renderSalesCart();
        },
        { confirmText: t('sales.clear_cart', 'Clear Order'), danger: true }
    );
};

window.salesCheckout = async function() {
    if (isCheckingOut) return;

    if (salesCart.length === 0) {
        showToast(t('sales.cart_empty', 'Order is empty. Please select products before completing sale.'), "warning");
        return;
    }
    
    const totalEl = document.getElementById('sales-cart-total');
    const subtotal = parseFloat(totalEl ? totalEl.dataset.subtotal : 0) || 0;
    const netTotal = parseFloat(totalEl ? totalEl.dataset.val : 0) || 0;
    let received = 0;
    let customerInfo = null;

    if (salesPaymentType === 'cash') {
        received = parseFloat(document.getElementById('sales-received')?.value);
        if (isNaN(received) || received < netTotal) {
            if (isNaN(received) || received === 0) {
                received = netTotal; // Auto-assume exact cash if not entered
            } else {
                showToast(`${t('sales.insufficient_cash', 'Amount tendered')} (${formatMoney(received)}) < (${formatMoney(netTotal)}).`, "error");
                return;
            }
        }
    } else { // credit
        if (!salesSelectedCustomerId) {
            showToast(t('cust.select_required', 'Please select a customer for credit recording.'), "warning");
            return;
        }
        received = parseFloat(document.getElementById('sales-credit-upfront')?.value) || 0;
        customerInfo = salesCustomers.find(c => c.id == salesSelectedCustomerId);
    }
    
    const items = salesCart.map(c => ({
        product_id: c.product.id,
        quantity: c.qty,
        unit_price: c.unit_price,
        packaging_unit: c.packaging ? c.packaging.unit_name : null,
        packaging_factor: c.factor || 1
    }));
    
    const ref = 'INV-' + Date.now().toString().slice(-6);
    const checkoutBtn = document.getElementById('sales-checkout-btn');
    
    isCheckingOut = true;
    if (checkoutBtn) {
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-1.5 h-3.5 w-3.5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg> ${t('btn.processing', 'Recording Sale...')}
        `;
    }
    
    try {
        const cartCopy = [...salesCart];
        const appliedDiscount = salesDiscount;
        
        await callBackend('create_sale', 
            ref, 
            JSON.stringify(items), 
            Number(received), 
            Number(appliedDiscount), 
            String(salesPaymentType), 
            String(salesSelectedCustomerId || '')
        );

        if (salesPaymentType === 'cash') {
            const changeDue = received - netTotal;
            showToast(`Sale ${ref} completed! Change: ${formatMoney(changeDue)}`, "success");
            _showReceiptModal(ref, cartCopy, subtotal, appliedDiscount, netTotal, received, changeDue, 'cash', null);
        } else {
            const creditAdded = Math.max(0, netTotal - received);
            showToast(`Credit Sale ${ref} recorded for ${customerInfo ? customerInfo.name : 'Customer'}!`, "success");
            salesCustomerBalances = await callBackend('get_customer_balances');
            const newBal = salesCustomerBalances.find(b => b.customer_id == salesSelectedCustomerId);
            _showReceiptModal(ref, cartCopy, subtotal, appliedDiscount, netTotal, received, creditAdded, 'credit', {
                ...customerInfo,
                newDebt: newBal ? newBal.outstanding_balance : creditAdded
            });
        }

        salesCart = [];
        salesDiscount = 0;
        const rEl = document.getElementById('sales-received');
        if (rEl) rEl.value = '';
        const dEl = document.getElementById('sales-discount-input');
        if (dEl) dEl.value = '0';
        _renderSalesCart();

        salesProducts = await callBackend('list_products');
        _renderSalesProducts(document.getElementById('sales-search')?.value || '');
    } catch(e) {
        showToast(e, "error");
    } finally {
        isCheckingOut = false;
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = `
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>${salesPaymentType === 'credit' ? t('sales.record_credit_sale', 'Record to Credit Book (Enter)') : t('sales.complete_sale', 'Complete Sale & Print (F2)')}</span>
            `;
        }
    }
};

function _showReceiptModal(ref, items, subtotal, discount, netTotal, received, changeOrCredit, paymentType, customerInfo) {
    const dateStr = new Date().toLocaleString();
    const isCredit = paymentType === 'credit';
    const html = `
        <div class="space-y-3 text-slate-800 text-xs">
            <div class="text-center pb-2.5 border-b border-slate-200">
                <h4 class="font-bold text-sm tracking-wide text-slate-900">${t('sales.receipt_title', 'SAY MAHAR PHARMACY & RETAIL')}</h4>
                <p class="text-[11px] text-slate-500">${isCredit ? t('cust.credit_invoice', 'Credit Sale Receipt') : t('sales.receipt_subtitle', 'Official Cash Sales Receipt')}</p>
                <div class="mt-2 text-[11px] font-mono text-slate-600 flex justify-between px-1">
                    <span>${t('col.invoice', 'Invoice')}: ${ref}</span>
                    <span>${dateStr}</span>
                </div>
                ${customerInfo ? `
                    <div class="mt-1 text-[11px] bg-amber-50 border border-amber-200 rounded p-1.5 text-left text-amber-950">
                        <span class="font-bold">${t('col.customer_name', 'Customer')}:</span> ${escapeHtml(customerInfo.name)} ${customerInfo.phone ? `(${escapeHtml(customerInfo.phone)})` : ''}
                    </div>
                ` : ''}
            </div>

            <div class="max-h-52 overflow-y-auto divide-y divide-slate-100">
                ${items.map(it => `
                    <div class="py-1.5 flex justify-between items-center text-xs">
                        <div class="pr-2 min-w-0">
                            <span class="font-bold text-slate-900 block truncate">${it.product.name} ${it.packaging ? `(${it.unit_name})` : ''}</span>
                            <span class="text-slate-500 text-[11px]">${it.qty} ${it.unit_name} x ${formatMoney(it.unit_price)}</span>
                        </div>
                        <span class="font-mono font-bold whitespace-nowrap">${formatMoney(it.qty * it.unit_price)}</span>
                    </div>
                `).join('')}
            </div>

            <div class="pt-2 border-t border-slate-200 space-y-1 font-mono text-xs">
                <div class="flex justify-between text-slate-600">
                    <span>${t('sales.subtotal', 'Subtotal')}:</span>
                    <span class="whitespace-nowrap">${formatMoney(subtotal)}</span>
                </div>
                ${discount > 0 ? `
                    <div class="flex justify-between text-rose-600 font-semibold">
                        <span>${t('sales.discount_amount', 'Discount / Round-off')}:</span>
                        <span class="whitespace-nowrap">-${formatMoney(discount)}</span>
                    </div>
                ` : ''}
                <div class="flex justify-between font-bold text-sm text-slate-900 pt-1 border-t border-slate-100">
                    <span>${t('sales.total_due', 'TOTAL AMOUNT:')}</span>
                    <span class="whitespace-nowrap">${formatMoney(netTotal)}</span>
                </div>

                ${!isCredit ? `
                    <div class="flex justify-between text-slate-600">
                        <span>${t('sales.tendered', 'Cash Tendered:')}</span>
                        <span class="whitespace-nowrap">${formatMoney(received)}</span>
                    </div>
                    <div class="flex justify-between font-bold text-teal-800 text-sm">
                        <span>${t('sales.change_due', 'CHANGE DUE:')}</span>
                        <span class="whitespace-nowrap">${formatMoney(changeOrCredit)}</span>
                    </div>
                ` : `
                    <div class="flex justify-between text-slate-600">
                        <span>${t('cust.upfront_cash', 'Upfront Cash Paid')}:</span>
                        <span class="whitespace-nowrap">${formatMoney(received)}</span>
                    </div>
                    <div class="flex justify-between font-bold text-amber-800">
                        <span>${t('cust.added_credit', 'Added to Credit Book')}:</span>
                        <span class="whitespace-nowrap">+${formatMoney(changeOrCredit)}</span>
                    </div>
                    ${customerInfo && customerInfo.newDebt !== undefined ? `
                        <div class="flex justify-between font-bold text-rose-800 pt-1 border-t border-amber-200 bg-amber-50/70 p-1 rounded">
                            <span>${t('cust.new_total_debt', 'Total Customer Debt')}:</span>
                            <span class="whitespace-nowrap">${formatMoney(customerInfo.newDebt)}</span>
                        </div>
                    ` : ''}
                `}
            </div>

            <div class="text-center pt-2 text-[11px] text-slate-500 italic">
                ${t('sales.receipt_thanks', 'Thank you for your visit! Goods sold in good order.')}
            </div>

            <div class="pt-2 flex justify-center">
                <button type="button" class="btn btn-secondary text-xs" onclick="window.print()">
                    <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2m2 4h6a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2zm8-12V5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v4h10z"></path></svg>
                    ${t('btn.print_receipt', 'Print Receipt')}
                </button>
            </div>
        </div>
    `;

    openModal(`${isCredit ? t('cust.credit_invoice', 'Credit Sale') : t('sales.receipt_subtitle', 'Sales Receipt')} • ${ref}`, html, null, {
        maxWidth: 'max-w-md',
        cancelText: t('btn.done', 'Done / Close')
    });
}

async function _renderHistoryView(container) {
    showLoading(true);
    let sales = [];
    try {
        sales = await callBackend('get_sales', salesStart, salesEnd);
    } catch(e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="flex items-center gap-2 text-xs flex-wrap">
                    <span class="font-semibold text-slate-700">${t('sales.filter_start', 'Filter Period:')}</span>
                    <input type="date" id="sales-start-date" class="form-input text-xs w-36 py-1" value="${salesStart}" onchange="updateSalesDates()">
                    <span class="text-slate-400">to</span>
                    <input type="date" id="sales-end-date" class="form-input text-xs w-36 py-1" value="${salesEnd}" onchange="updateSalesDates()">
                    <button class="btn btn-sm btn-secondary" onclick="updateSalesDates()">${t('btn.filter', 'Apply')}</button>
                </div>
                <div class="flex items-center gap-3">
                    <button class="btn btn-secondary text-xs py-1" onclick="exportSalesExcel()">
                        <svg class="w-3.5 h-3.5 mr-1 text-emerald-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        <span>${t('btn.export_excel', 'Export to Excel')}</span>
                    </button>
                    <div class="text-xs text-slate-600 font-mono">
                        ${sales.length} ${t('sales.cart_items', 'Transactions')}
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th">${t('col.date_time', 'Date & Time')}</th>
                            <th class="th">${t('col.receipt', 'Receipt #')}</th>
                            <th class="th">${t('col.type', 'Mode / Customer')}</th>
                            <th class="th text-center">${t('col.qty', 'Items')}</th>
                            <th class="th text-right">${t('col.total', 'Net Total')}</th>
                            <th class="th text-right">${t('col.paid', 'Tendered')}</th>
                            <th class="th text-right">${t('col.balance', 'Change / Credit')}</th>
                            <th class="th text-center">${t('col.status', 'Status')}</th>
                            <th class="th text-right">${t('col.actions', 'Actions')}</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${sales.length === 0 ? `<tr><td colspan="9" class="py-12 text-center text-slate-400 text-xs">${t('msg.no_data', 'No sales transactions recorded in this period.')}</td></tr>` : ''}
                        ${sales.map(s => {
                            const isVoid = s.status === 'Voided';
                            const isCredit = s.payment_type === 'credit';
                            return `
                                <tr class="tr-hover ${isVoid ? 'opacity-60 bg-slate-50/60' : ''}">
                                    <td class="td text-xs font-mono text-slate-600">${s.date_time}</td>
                                    <td class="td font-mono font-bold text-xs ${isVoid ? 'text-slate-400 line-through' : 'text-teal-900'}">${s.reference}</td>
                                    <td class="td text-xs">
                                        <div class="flex items-center gap-1.5">
                                            <span class="badge ${isCredit ? 'badge-warning' : 'badge-neutral'} text-[10px]">${isCredit ? 'အကြွေး' : 'ငွေသား'}</span>
                                            ${s.customer_name ? `<span class="font-bold text-slate-800 truncate max-w-[120px]">${escapeHtml(s.customer_name)}</span>` : ''}
                                        </div>
                                    </td>
                                    <td class="td text-center font-mono">${s.items_count}</td>
                                    <td class="td-num font-bold ${isVoid ? 'text-slate-400' : 'text-slate-900'}">
                                        ${formatMoney(s.total_amount)}
                                        ${s.discount_amount > 0 ? `<span class="block text-[10px] text-rose-600">-${formatMoney(s.discount_amount)}</span>` : ''}
                                    </td>
                                    <td class="td-num">${formatMoney(s.amount_received)}</td>
                                    <td class="td-num">
                                        ${isCredit ? `
                                            <span class="font-bold text-amber-700">+${formatMoney(s.credit_amount || 0)}</span>
                                        ` : `
                                            <span class="text-teal-800">${formatMoney(s.change_given)}</span>
                                        `}
                                    </td>
                                    <td class="td text-center">
                                        <span class="badge ${isVoid ? 'badge-danger' : 'badge-success'}">${isVoid ? t('status.voided', 'Voided') : t('status.completed', 'Completed')}</span>
                                    </td>
                                    <td class="td text-right">
                                        ${!isVoid ? `
                                            <button class="btn btn-sm btn-danger py-0.5 text-xs" onclick="openVoidSaleModal(${s.id}, '${s.reference}')">
                                                ${t('btn.void', 'Void & Return')}
                                            </button>
                                        ` : `<span class="text-xs text-slate-400 italic">${t('status.voided', 'Voided')}</span>`}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

window.openVoidSaleModal = function(saleId, reference) {
    const html = `
        <div class="space-y-3 text-slate-700 text-xs">
            <div class="bg-rose-50 border border-rose-200 rounded p-2.5 text-rose-800">
                <strong>Attention:</strong> ${t('sales.void_confirm_msg', 'Voiding sale will restore all items into inventory (FEFO), reverse revenue, and record an audit log.')}
            </div>
            <div>
                <label class="form-label" for="void-sale-reason">${t('col.description', 'Reason for Voiding / Customer Return')} *</label>
                <input type="text" id="void-sale-reason" class="form-input text-xs" required placeholder="e.g. Customer returned unopened strip, incorrect barcode scanned">
                <span class="form-hint">This reason will be permanently recorded in the audit trail.</span>
            </div>
        </div>
    `;

    openModal(`${t('sales.void_confirm_title', 'Void Sale')} • ${reference}`, html, async () => {
        const reason = document.getElementById('void-sale-reason').value.trim();
        if (!reason) throw "A void reason is required.";
        await callBackend('void_sale', saleId, reason);
        showToast(`Sale ${reference} voided and stock restored.`);
        salesProducts = await callBackend('list_products');
        await _renderHistoryView(document.getElementById('content-area'));
    }, {
        saveText: t('btn.void', 'Confirm Void Sale'),
        saveBtnClass: 'btn-danger'
    });
};

window._showReceiptModal = _showReceiptModal;