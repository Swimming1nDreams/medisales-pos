let salesProducts = [];
let salesCart = [];
let salesReceived = 0;
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
                    Point of Sale (POS)
                </button>
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${salesTab === 'history' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchSalesTab('history')">
                    Sales History & Returns
                </button>
            </div>
        `;
    }

    if (salesTab === 'pos') {
        salesProducts = await callBackend('list_products');
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
                            <input type="text" id="sales-search" class="form-input pl-8 text-xs" placeholder="Search medicine name, barcode, or general product..." oninput="salesSearch(this.value)" onkeydown="if(event.key==='Enter') salesSearchEnter()" autofocus>
                        </div>
                        <select id="sales-cat-filter" class="form-select w-40 text-xs font-medium" onchange="salesFilterCategory(this.value)">
                            <option value="all">All Categories</option>
                            <option value="medicine">Medicines Only</option>
                            <option value="general">General Merchandise</option>
                            ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>

                    <!-- Filter pills -->
                    <div class="flex items-center gap-1.5 overflow-x-auto text-[11px] pb-0.5">
                        <button type="button" class="px-2 py-0.5 rounded border ${salesCategoryFilter === 'all' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('all')">All Products</button>
                        <button type="button" class="px-2 py-0.5 rounded border ${salesCategoryFilter === 'medicine' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('medicine')">Medicines (FEFO)</button>
                        <button type="button" class="px-2 py-0.5 rounded border ${salesCategoryFilter === 'general' ? 'bg-teal-700 text-white border-teal-700 font-semibold' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}" onclick="salesFilterCategory('general')">General Goods</button>
                    </div>
                </div>

                <!-- Products Grid -->
                <div class="flex-1 overflow-auto p-3 bg-slate-50/50">
                    <div id="sales-product-grid" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-2.5">
                        <!-- Products rendered here -->
                    </div>
                </div>

                <!-- Footer Summary of in-stock items -->
                <div class="px-3.5 py-2 border-t border-slate-200 bg-white text-[11px] text-slate-500 flex justify-between items-center flex-shrink-0">
                    <span id="sales-products-count" class="font-medium">Available Products: 0</span>
                    <span class="text-teal-800 font-medium">Click product or press Enter to add</span>
                </div>
            </div>

            <!-- Right: POS Cart & Checkout Register -->
            <div class="w-full lg:w-[410px] flex flex-col card flex-shrink-0 h-full overflow-hidden">
                
                <!-- Cart Header -->
                <div class="px-3.5 py-2.5 border-b border-slate-200 bg-slate-50/80 flex justify-between items-center flex-shrink-0">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-slate-900 text-xs uppercase tracking-wide">Current Order</span>
                        <span id="sales-cart-badge" class="badge badge-neutral text-[10px]">0 lines</span>
                    </div>
                    <button class="text-xs text-rose-600 hover:text-rose-800 font-medium hover:underline flex items-center gap-1" onclick="salesConfirmClearCart()">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        Clear Order
                    </button>
                </div>

                <!-- Cart Items List -->
                <div class="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 min-h-0 bg-white" id="sales-cart-items">
                    <!-- Cart items rendered here -->
                </div>

                <!-- Cart Totals & Cash Register Drawer -->
                <div class="border-t border-slate-200 bg-slate-50/90 p-3 space-y-2 flex-shrink-0">
                    
                    <!-- Breakdown row -->
                    <div class="flex justify-between text-xs text-slate-600">
                        <span>Total Items / Units:</span>
                        <span id="sales-cart-units" class="font-mono font-bold text-slate-800">0 units</span>
                    </div>

                    <!-- Grand Total Banner -->
                    <div class="p-2.5 bg-white rounded-md border border-slate-200 flex justify-between items-baseline shadow-xs">
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-600">Total Due</span>
                        <div id="sales-cart-total" data-val="0" class="text-xl font-bold font-mono text-teal-800 tabular-nums whitespace-nowrap">0 Ks</div>
                    </div>

                    <!-- Amount Tendered -->
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="form-label mb-0 text-[11px]" for="sales-received">Amount Tendered (Kyat)</label>
                            <button type="button" class="text-[11px] text-teal-800 hover:underline font-semibold" onclick="salesExactAmount()">Exact Tender</button>
                        </div>
                        <input type="number" id="sales-received" class="form-input text-sm font-bold font-mono text-slate-900 py-1.5" placeholder="0" min="0" oninput="salesCalcChange()" onkeydown="if(event.key==='Enter') salesCheckout()">
                        
                        <!-- Quick Cash Chips -->
                        <div class="flex gap-1 mt-1 overflow-x-auto pb-0.5">
                            <button type="button" class="px-2 py-0.5 text-[10px] font-mono bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-semibold whitespace-nowrap" onclick="salesAddCash(1000)">+1,000</button>
                            <button type="button" class="px-2 py-0.5 text-[10px] font-mono bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-semibold whitespace-nowrap" onclick="salesAddCash(5000)">+5,000</button>
                            <button type="button" class="px-2 py-0.5 text-[10px] font-mono bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-semibold whitespace-nowrap" onclick="salesAddCash(10000)">+10,000</button>
                            <button type="button" class="px-2 py-0.5 text-[10px] font-mono bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-semibold whitespace-nowrap" onclick="salesAddCash(20000)">+20,000</button>
                            <button type="button" class="px-2 py-0.5 text-[10px] font-mono bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-semibold whitespace-nowrap" onclick="salesAddCash(50000)">+50,000</button>
                        </div>
                    </div>

                    <!-- Change Calculation Banner -->
                    <div id="sales-change-banner" class="flex justify-between items-center px-3 py-1.5 rounded border border-slate-200 bg-white text-xs">
                        <span class="font-semibold text-slate-600">Change Due:</span>
                        <span id="sales-change" class="font-mono font-bold text-teal-800 tabular-nums whitespace-nowrap">0 Ks</span>
                    </div>

                    <!-- Complete Sale Button -->
                    <button id="sales-checkout-btn" class="btn btn-primary w-full py-2 text-xs font-bold shadow-xs flex items-center justify-center gap-1.5" onclick="salesCheckout()">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        <span>Complete Sale (Enter)</span>
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
    
    let filtered = salesProducts.filter(p => p.is_active && p.current_stock > 0);
    
    if (salesCategoryFilter === 'medicine') {
        filtered = filtered.filter(p => p.is_medicine);
    } else if (salesCategoryFilter === 'general') {
        filtered = filtered.filter(p => !p.is_medicine);
    } else if (salesCategoryFilter !== 'all') {
        filtered = filtered.filter(p => p.category_name === salesCategoryFilter);
    }

    if (query && query.trim()) {
        const q = query.toLowerCase().trim();
        filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || (p.category_name && p.category_name.toLowerCase().includes(q)));
    }

    const countEl = document.getElementById('sales-products-count');
    if (countEl) countEl.textContent = `Available Products: ${filtered.length}`;

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-12 text-center text-slate-400">
                <svg class="w-8 h-8 mx-auto text-slate-300 mb-1.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <p class="text-xs font-medium text-slate-600">No in-stock products match your filter.</p>
                <p class="text-[11px] text-slate-400 mt-0.5">Try another search term or record a new purchase invoice.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(p => {
        const isMed = Boolean(p.is_medicine);
        const isLow = p.current_stock <= (p.min_stock_level || 5);
        return `
            <div class="bg-white border border-slate-200 rounded-md p-2.5 shadow-xs hover:border-teal-700 hover:shadow-sm cursor-pointer transition-all flex flex-col justify-between group" onclick="salesAddToCart(${p.id})">
                <div>
                    <div class="flex items-center justify-between gap-1 mb-1">
                        <span class="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.2 rounded ${isMed ? 'bg-teal-50 text-teal-800 border border-teal-200' : 'bg-slate-100 text-slate-700 border border-slate-200'}">
                            ${isMed ? 'Medicine (FEFO)' : 'General'}
                        </span>
                        <span class="text-[11px] font-mono font-medium ${isLow ? 'text-amber-800 font-bold' : 'text-slate-600'}">
                            ${p.current_stock} ${p.unit_measure || 'units'}
                        </span>
                    </div>
                    <!-- Full untruncated product name so cashier sees strength/size -->
                    <h4 class="font-bold text-slate-900 text-xs leading-snug group-hover:text-teal-800 break-words" title="${p.name}">
                        ${p.name}
                    </h4>
                    <p class="text-[10px] text-slate-500 mt-0.5">${p.category_name || 'General'}</p>
                </div>
                
                <div class="flex items-center justify-between mt-2.5 pt-1.5 border-t border-slate-100">
                    <span class="text-xs font-bold font-mono text-teal-800 tabular-nums whitespace-nowrap">
                        ${formatMoney(p.selling_price)}
                    </span>
                    <span class="btn btn-sm btn-subtle text-teal-800 group-hover:bg-teal-800 group-hover:text-white transition-colors">
                        + Add
                    </span>
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
    const val = input ? input.value.trim().toLowerCase() : '';
    if (!val) return;
    const matches = salesProducts.filter(p => p.is_active && p.current_stock > 0 && (p.name.toLowerCase().includes(val) || (p.category_name && p.category_name.toLowerCase().includes(val))));
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

window.salesAddToCart = function(id) {
    const p = salesProducts.find(x => x.id === id);
    if (!p) return;
    
    const existing = salesCart.find(x => x.product.id === id);
    if (existing) {
        if (existing.qty < p.current_stock) {
            existing.qty += 1;
        } else {
            showToast(`Cannot add more: only ${p.current_stock} ${p.unit_measure || 'units'} in stock.`, "warning");
        }
    } else {
        salesCart.push({ product: p, qty: 1 });
    }
    _renderSalesCart();
};

window.salesUpdateQty = function(idx, delta) {
    const item = salesCart[idx];
    if (!item) return;
    const newQty = item.qty + delta;
    if (newQty <= 0) {
        salesCart.splice(idx, 1);
    } else if (newQty > item.product.current_stock) {
        showToast(`Cannot exceed available stock (${item.product.current_stock} ${item.product.unit_measure || 'units'}).`, "warning");
    } else {
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
    } else if (qty > item.product.current_stock) {
        showToast(`Cannot exceed available stock (${item.product.current_stock}).`, "warning");
        item.qty = item.product.current_stock;
    } else {
        item.qty = qty;
    }
    _renderSalesCart();
};

function _renderSalesCart() {
    const container = document.getElementById('sales-cart-items');
    if (!container) return;
    
    let total = 0;
    let count = 0;
    
    if (salesCart.length === 0) {
        container.innerHTML = `
            <div class="h-40 flex flex-col items-center justify-center text-slate-400">
                <svg class="w-8 h-8 text-slate-300 mb-1.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                <p class="text-xs font-semibold text-slate-600">Cart is empty</p>
                <p class="text-[11px] text-slate-400 mt-0.5">Select products from the catalog to add items</p>
            </div>
        `;
    } else {
        container.innerHTML = salesCart.map((c, i) => {
            const lineTotal = c.qty * c.product.selling_price;
            total += lineTotal;
            count += c.qty;
            return `
                <div class="py-2 px-1.5 flex items-center justify-between gap-2 hover:bg-slate-50 rounded transition-colors group">
                    <div class="flex-1 min-w-0 pr-1">
                        <div class="text-xs font-bold text-slate-900 leading-snug break-words" title="${c.product.name}">
                            ${c.product.name}
                        </div>
                        <div class="flex items-center gap-2 mt-0.5">
                            <span class="text-[11px] font-mono text-slate-600 font-semibold">${formatMoney(c.product.selling_price)}</span>
                            ${c.product.is_medicine ? '<span class="text-[9px] bg-teal-50 text-teal-800 px-1 rounded border border-teal-200">Auto FEFO</span>' : ''}
                        </div>
                    </div>
                    
                    <!-- Qty Stepper -->
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        <div class="flex items-center border border-slate-300 rounded bg-white overflow-hidden shadow-xs">
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
    if (unitsEl) unitsEl.textContent = `${count} units`;

    const totalEl = document.getElementById('sales-cart-total');
    if (totalEl) {
        totalEl.textContent = formatMoney(total);
        totalEl.dataset.val = total;
    }

    salesCalcChange();
}

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
        changeEl.textContent = "0 Ks (Enter cash received)";
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
        "Clear Current Order",
        "Are you sure you want to remove all items from the current sales order?",
        () => {
            salesCart = [];
            const rEl = document.getElementById('sales-received');
            if (rEl) rEl.value = '';
            _renderSalesCart();
        },
        { confirmText: "Clear Order", danger: true }
    );
};

window.salesCheckout = async function() {
    if (isCheckingOut) return;

    if (salesCart.length === 0) {
        showToast("Order is empty. Please select products before completing sale.", "warning");
        return;
    }
    
    const total = parseFloat(document.getElementById('sales-cart-total').dataset.val);
    let received = parseFloat(document.getElementById('sales-received').value);
    
    if (isNaN(received) || received < total) {
        if (isNaN(received) || received === 0) {
            received = total; // Auto-assume exact cash if not entered
        } else {
            showToast(`Amount tendered (${formatMoney(received)}) is less than total due (${formatMoney(total)}).`, "error");
            return;
        }
    }
    
    const items = salesCart.map(c => ({
        product_id: c.product.id,
        quantity: c.qty,
        unit_price: c.product.selling_price
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
            </svg> Recording Sale...
        `;
    }
    
    try {
        const cartCopy = [...salesCart];
        const changeDue = received - total;
        
        await callBackend('create_sale', ref, JSON.stringify(items), received);
        showToast(`Sale ${ref} completed! Change: ${formatMoney(changeDue)}`, "success");
        
        // Show commercial receipt dialog
        _showReceiptModal(ref, cartCopy, total, received, changeDue);

        salesCart = [];
        const rEl = document.getElementById('sales-received');
        if (rEl) rEl.value = '';
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
                <span>Complete Sale (Enter)</span>
            `;
        }
    }
};

function _showReceiptModal(ref, items, total, received, change) {
    const dateStr = new Date().toLocaleString();
    const html = `
        <div class="space-y-3 text-slate-800 text-xs">
            <div class="text-center pb-2.5 border-b border-slate-200">
                <h4 class="font-bold text-sm tracking-wide text-slate-900">MEDISALES PHARMACY & RETAIL</h4>
                <p class="text-[11px] text-slate-500">Official Cash Sales Receipt</p>
                <div class="mt-2 text-[11px] font-mono text-slate-600 flex justify-between px-1">
                    <span>Invoice: ${ref}</span>
                    <span>${dateStr}</span>
                </div>
            </div>

            <div class="max-h-56 overflow-y-auto divide-y divide-slate-100">
                ${items.map(it => `
                    <div class="py-1.5 flex justify-between items-center text-xs">
                        <div class="pr-2 min-w-0">
                            <span class="font-bold text-slate-900 block truncate">${it.product.name}</span>
                            <span class="text-slate-500 text-[11px]">${it.qty} x ${formatMoney(it.product.selling_price)}</span>
                        </div>
                        <span class="font-mono font-bold whitespace-nowrap">${formatMoney(it.qty * it.product.selling_price)}</span>
                    </div>
                `).join('')}
            </div>

            <div class="pt-2.5 border-t border-slate-200 space-y-1 font-mono text-xs">
                <div class="flex justify-between font-bold text-sm text-slate-900">
                    <span>TOTAL AMOUNT:</span>
                    <span class="whitespace-nowrap">${formatMoney(total)}</span>
                </div>
                <div class="flex justify-between text-slate-600">
                    <span>Cash Tendered:</span>
                    <span class="whitespace-nowrap">${formatMoney(received)}</span>
                </div>
                <div class="flex justify-between font-bold text-teal-800 text-sm">
                    <span>CHANGE DUE:</span>
                    <span class="whitespace-nowrap">${formatMoney(change)}</span>
                </div>
            </div>

            <div class="text-center pt-2 text-[11px] text-slate-500 italic">
                Thank you for your visit! Goods sold in good order.
            </div>

            <div class="pt-2 flex justify-center">
                <button type="button" class="btn btn-secondary text-xs" onclick="window.print()">
                    <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
                    Print Receipt
                </button>
            </div>
        </div>
    `;

    openModal(`Sales Receipt • ${ref}`, html, null, {
        maxWidth: 'max-w-md',
        cancelText: 'Done / Close'
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
                <div class="flex items-center gap-2 text-xs">
                    <span class="font-semibold text-slate-700">Filter Period:</span>
                    <input type="date" id="sales-start-date" class="form-input text-xs w-36 py-1" value="${salesStart}" onchange="updateSalesDates()">
                    <span class="text-slate-400">to</span>
                    <input type="date" id="sales-end-date" class="form-input text-xs w-36 py-1" value="${salesEnd}" onchange="updateSalesDates()">
                    <button class="btn btn-sm btn-secondary" onclick="updateSalesDates()">Apply</button>
                </div>
                <div class="text-xs text-slate-600 font-mono">
                    Transactions: <strong class="text-slate-900">${sales.length}</strong>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th">Date & Time</th>
                            <th class="th">Receipt #</th>
                            <th class="th text-center">Items</th>
                            <th class="th text-right">Total Amount</th>
                            <th class="th text-right">Tendered</th>
                            <th class="th text-right">Change</th>
                            <th class="th text-center">Status</th>
                            <th class="th text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${sales.length === 0 ? '<tr><td colspan="8" class="py-12 text-center text-slate-400 text-xs">No sales transactions recorded in this period.</td></tr>' : ''}
                        ${sales.map(s => {
                            const isVoid = s.status === 'Voided';
                            return `
                                <tr class="tr-hover ${isVoid ? 'opacity-60 bg-slate-50/60' : ''}">
                                    <td class="td text-xs font-mono text-slate-600">${s.date_time}</td>
                                    <td class="td font-mono font-bold text-xs ${isVoid ? 'text-slate-400 line-through' : 'text-teal-900'}">${s.reference}</td>
                                    <td class="td text-center font-mono">${s.items_count}</td>
                                    <td class="td-num font-bold ${isVoid ? 'text-slate-400' : 'text-slate-900'}">${formatMoney(s.total_amount)}</td>
                                    <td class="td-num">${formatMoney(s.amount_received)}</td>
                                    <td class="td-num">${formatMoney(s.change_given)}</td>
                                    <td class="td text-center">
                                        <span class="badge ${isVoid ? 'badge-danger' : 'badge-success'}">${s.status}</span>
                                    </td>
                                    <td class="td text-right">
                                        ${!isVoid ? `
                                            <button class="btn btn-sm btn-danger py-0.5 text-xs" onclick="openVoidSaleModal(${s.id}, '${s.reference}')">
                                                Void & Return
                                            </button>
                                        ` : '<span class="text-xs text-slate-400 italic">Voided</span>'}
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
                <strong>Attention:</strong> Voiding sale <strong>${reference}</strong> will restore all sold items back into inventory (FEFO batches), reverse financial revenue, and record an immutable audit entry.
            </div>
            <div>
                <label class="form-label" for="void-sale-reason">Reason for Voiding / Customer Return *</label>
                <input type="text" id="void-sale-reason" class="form-input text-xs" required placeholder="e.g. Customer returned unopened strip, incorrect barcode scanned">
                <span class="form-hint">This reason will be permanently recorded in the audit trail.</span>
            </div>
        </div>
    `;

    openModal(`Void Sale ${reference}`, html, async () => {
        const reason = document.getElementById('void-sale-reason').value.trim();
        if (!reason) throw "A void reason is required.";
        await callBackend('void_sale', saleId, reason);
        showToast(`Sale ${reference} voided and stock restored.`);
        salesProducts = await callBackend('list_products');
        await _renderHistoryView(document.getElementById('content-area'));
    }, {
        saveText: 'Confirm Void Sale',
        saveBtnClass: 'btn-danger'
    });
};
