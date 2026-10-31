let inventoryTab = 'stock';
let inventoryData = [];
let inventorySearch = '';
let inventoryLowStockOnly = false;

async function renderInventory(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="flex items-center gap-2">
                <button class="btn btn-secondary text-xs" onclick="${inventoryTab === 'stock' ? 'exportInventoryValuationExcel()' : 'exportMedicineBatchesExcel()'}">
                    <svg class="w-3.5 h-3.5 text-emerald-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span>${t('btn.export_excel', 'Export to Excel')}</span>
                </button>
                <div class="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
                    <button class="px-3 py-1 text-xs font-semibold rounded whitespace-nowrap transition-colors ${inventoryTab === 'stock' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('stock')">
                        ${t('inv.tab_stock', 'Stock on Hand')}
                    </button>
                    <button class="px-3 py-1 text-xs font-semibold rounded whitespace-nowrap transition-colors ${inventoryTab === 'all_batches' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('all_batches')">
                        ${t('inv.filter_all_batches', 'All Medicine Batches')}
                    </button>
                    <button class="px-3 py-1 text-xs font-semibold rounded whitespace-nowrap transition-colors ${inventoryTab === 'expiring_soon' ? 'bg-white text-amber-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('expiring_soon')">
                        ${t('inv.filter_expiring_soon', 'Expiring Soon')}
                    </button>
                    <button class="px-3 py-1 text-xs font-semibold rounded whitespace-nowrap transition-colors ${inventoryTab === 'expired' ? 'bg-white text-rose-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('expired')">
                        ${t('inv.filter_expired', 'Expired Batches')}
                    </button>
                </div>
            </div>
        `;
    }

    showLoading(true);
    try {
        if (inventoryTab === 'stock') {
            inventoryData = await callBackend('get_current_stock');
            _renderStockTable(container);
        } else {
            const filterKey = inventoryTab === 'all_batches' ? null : inventoryTab;
            inventoryData = await callBackend('get_medicine_batches_report', filterKey);
            _renderBatchTable(container);
        }
    } catch (e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }
}

window.exportInventoryValuationExcel = async function() {
    try {
        const res = await callBackend('export_inventory_valuation_excel');
        if (res && !res.cancelled) {
            showToast(`${t('msg.export_success', 'Spreadsheet successfully exported to:')}\n${res.file_path}`);
        }
    } catch (e) {
        showToast(`${t('msg.export_failed', 'Excel export failed:')} ${e}`, "error");
    }
};

window.exportMedicineBatchesExcel = async function() {
    try {
        const filterKey = inventoryTab === 'stock' || inventoryTab === 'all_batches' ? 'all' : inventoryTab;
        const res = await callBackend('export_medicine_batches_excel', filterKey);
        if (res && !res.cancelled) {
            showToast(`${t('msg.export_success', 'Spreadsheet successfully exported to:')}\n${res.file_path}`);
        }
    } catch (e) {
        showToast(`${t('msg.export_failed', 'Excel export failed:')} ${e}`, "error");
    }
};

window.switchInventoryTab = function(tab) {
    inventoryTab = tab;
    renderInventory(document.getElementById('content-area'));
};

function _renderStockTbody() {
    const tbody = document.getElementById('inventory-stock-tbody');
    if (!tbody) return;

    let candidates = inventoryData.filter(s => {
        if (inventoryLowStockOnly && s.current_stock > (s.min_stock_level || 5)) return false;
        return true;
    });

    const filtered = (typeof window.filterAndRankItems === 'function')
        ? window.filterAndRankItems(candidates, inventorySearch, (s) => ({
            primary: s.name,
            secondary: [s.category_name, s.unit_measure]
        }))
        : candidates.filter(s => !inventorySearch || s.name.toLowerCase().includes(inventorySearch.toLowerCase()));

    const lowCount = filtered.filter(it => it.current_stock <= (it.min_stock_level || 5)).length;
    const totalQty = filtered.reduce((acc, it) => acc + (it.current_stock || 0), 0);

    const countBadge = document.getElementById('inventory-stock-count-badge');
    if (countBadge) countBadge.textContent = `${filtered.length} ${t('status.normal', 'Products')}`;
    const qtyBadge = document.getElementById('inventory-stock-qty-badge');
    if (qtyBadge) qtyBadge.textContent = `${totalQty.toLocaleString('en-US')} ${t('col.stock', 'Units in Stock')}`;

    const tfootTotalEl = document.getElementById('inventory-stock-tfoot-total');
    if (tfootTotalEl) tfootTotalEl.textContent = `${t('inv.tab_stock', 'Total Stock On Hand')} (${filtered.length})`;
    const tfootQtyEl = document.getElementById('inventory-stock-tfoot-qty');
    if (tfootQtyEl) tfootQtyEl.textContent = totalQty.toLocaleString('en-US');

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-16 text-center">
                    <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-400 mb-3">
                        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                    </div>
                    <div class="text-sm font-semibold text-slate-700">${t('msg.no_data', 'No stock records found')}</div>
                    <p class="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                        ${inventorySearch || inventoryLowStockOnly ? 'No inventory items match your current search or low-stock filter.' : 'There are currently no products tracked in inventory.'}
                    </p>
                    ${(inventorySearch || inventoryLowStockOnly) ? `
                        <button class="btn btn-sm btn-secondary inline-flex items-center gap-1.5" onclick="clearInventoryFilters()">
                            <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            <span>${t('btn.clear', 'Reset Filters')}</span>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(s => {
        const isLow = s.current_stock <= (s.min_stock_level || 5);
        const isOut = s.current_stock === 0;
        const highlightedName = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(s.name, inventorySearch)
            : escapeHtml(s.name);
        const catName = s.category_name || 'General';
        const highlightedCat = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(catName, inventorySearch)
            : escapeHtml(catName);

        return `
            <tr class="tr-hover">
                <td class="td">
                    <div class="font-bold text-slate-900 text-xs leading-snug break-words" title="${escapeHtml(s.name)}">${highlightedName}</div>
                    <div class="flex items-center gap-1 text-[10px] text-slate-500 mt-0.5">
                        <span>${highlightedCat}</span>
                        <span class="text-slate-300">•</span>
                        <span>${t('col.unit', 'Unit')}: ${escapeHtml(s.unit_measure || 'piece')}</span>
                    </div>
                </td>
                <td class="td-num">
                    <span class="text-xs font-bold ${isOut ? 'text-rose-700 font-black' : (isLow ? 'text-amber-800' : 'text-slate-900')}">
                        ${s.current_stock}
                    </span>
                </td>
                <td class="td-num text-xs text-slate-500 font-mono">${s.min_stock_level || 0}</td>
                <td class="td text-center">
                    ${isOut ? `<span class="badge badge-danger text-[10px]">${t('status.out_of_stock', 'Out of Stock')}</span>` : 
                      (isLow ? `<span class="badge badge-warning text-[10px]">${t('status.low_stock', 'Low Stock')}</span>` : 
                      `<span class="badge badge-success text-[10px]">${t('status.active', 'In Stock')}</span>`)}
                </td>
                <td class="td text-right whitespace-nowrap">
                    <button class="btn btn-sm btn-secondary py-0.5 text-xs" onclick="navigate('purchases')">
                        ${t('pur.add_button', 'Receive Stock')}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function _renderStockTable(container) {
    const totalQty = inventoryData.reduce((acc, it) => acc + (it.current_stock || 0), 0);
    const lowCount = inventoryData.filter(it => it.current_stock <= (it.min_stock_level || 5)).length;

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="flex items-center gap-3 flex-1 min-w-[280px]">
                    <div class="relative flex-1 max-w-sm">
                        <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        </span>
                        <input type="text" id="inventory-search-input" placeholder="${t('prod.filter_search', 'Search stock by product or category...')}" class="form-input pl-8 text-xs" oninput="inventorySearchFn(this.value)" value="${escapeHtml(inventorySearch)}">
                    </div>

                    <label class="flex items-center gap-1.5 cursor-pointer text-xs font-semibold text-slate-700 select-none">
                        <input type="checkbox" id="inventory-low-stock-check" class="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-3.5 w-3.5" ${inventoryLowStockOnly ? 'checked' : ''} onchange="inventoryToggleLowStock(this.checked)">
                        <span>${t('status.low_stock', 'Low Stock Only')}</span>
                    </label>
                </div>

                <div class="flex items-center gap-1.5 text-xs">
                    <span id="inventory-stock-count-badge" class="badge badge-neutral font-mono">${inventoryData.length} ${t('status.normal', 'Products')}</span>
                    <span id="inventory-stock-qty-badge" class="badge badge-teal font-mono">${totalQty.toLocaleString('en-US')} ${t('col.stock', 'Units in Stock')}</span>
                    ${lowCount > 0 ? `<span class="badge badge-warning font-mono">${lowCount} ${t('status.low_stock', 'Low Stock')}</span>` : `<span class="badge badge-success">${t('status.active', 'All Healthy')}</span>`}
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">${t('col.name', 'Product Name & Category')}</th>
                            <th class="th text-right w-2/12">${t('col.stock', 'Current Stock')}</th>
                            <th class="th text-right w-2/12">${t('prod.field_min_stock', 'Reorder Level')}</th>
                            <th class="th text-center w-2/12">${t('col.status', 'Inventory Status')}</th>
                            <th class="th text-right w-1/12">${t('col.actions', 'Action')}</th>
                        </tr>
                    </thead>
                    <tbody id="inventory-stock-tbody" class="divide-y divide-slate-100 bg-white">
                        <!-- Rendered by _renderStockTbody -->
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td id="inventory-stock-tfoot-total" class="px-4 py-2.5 text-xs uppercase text-slate-700">${t('inv.tab_stock', 'Total Stock On Hand')} (${inventoryData.length})</td>
                            <td id="inventory-stock-tfoot-qty" class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${totalQty.toLocaleString('en-US')}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-500">-</td>
                            <td class="px-4 py-2.5 text-center text-xs text-slate-600">${lowCount > 0 ? `<span class="badge badge-warning text-[10px]">${lowCount} ${t('status.low_stock', 'Low')}</span>` : `<span class="badge badge-success text-[10px]">${t('status.active', 'All Healthy')}</span>`}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-400">-</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

        </div>
    `;

    _renderStockTbody();
}

function _renderBatchTbody() {
    const tbody = document.getElementById('inventory-batch-tbody');
    if (!tbody) return;

    const filtered = (typeof window.filterAndRankItems === 'function')
        ? window.filterAndRankItems(inventoryData, inventorySearch, (b) => ({
            primary: b.product_name,
            secondary: [b.batch_number]
        }))
        : inventoryData.filter(b => !inventorySearch || b.product_name.toLowerCase().includes(inventorySearch.toLowerCase()));

    const totalBatchUnits = filtered.reduce((acc, b) => acc + (b.remaining_quantity ?? b.current_qty ?? 0), 0);

    const countHeader = document.getElementById('inventory-batch-count-header');
    if (countHeader) countHeader.textContent = `${filtered.length} ${t('inv.filter_all_batches', 'Batches Displayed')}`;
    const tfootTotalEl = document.getElementById('inventory-batch-tfoot-total');
    if (tfootTotalEl) tfootTotalEl.textContent = `${t('inv.filter_all_batches', 'Total Medicine Batches')} (${filtered.length})`;
    const tfootQtyEl = document.getElementById('inventory-batch-tfoot-qty');
    if (tfootQtyEl) tfootQtyEl.textContent = totalBatchUnits.toLocaleString('en-US');

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-16 text-center">
                    <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-400 mb-3">
                        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                    </div>
                    <div class="text-sm font-semibold text-slate-700">${t('msg.no_data', 'No medicine batches found')}</div>
                    <p class="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                        ${inventoryTab === 'expiring_soon' ? 'No batches are currently expiring within 30 days.' : (inventoryTab === 'expired' ? 'No expired batches recorded in system.' : 'No medicine batches match your filter.')}
                    </p>
                    ${inventorySearch ? `
                        <button class="btn btn-sm btn-secondary inline-flex items-center gap-1.5" onclick="clearInventoryFilters()">
                            <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            <span>${t('btn.clear', 'Reset Search')}</span>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(b => {
        const qty = b.remaining_quantity ?? b.current_qty ?? 0;
        const highlightedName = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(b.product_name, inventorySearch)
            : escapeHtml(b.product_name);
        const highlightedBatch = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(b.batch_number || 'N/A', inventorySearch)
            : escapeHtml(b.batch_number || 'N/A');

        return `
            <tr class="tr-hover">
                <td class="td">
                    <div class="font-bold text-slate-900 text-xs leading-snug break-words" title="${escapeHtml(b.product_name)}">${highlightedName}</div>
                    <span class="text-[10px] text-slate-500">${t('col.cost', 'Unit Cost')}: ${formatMoney(b.unit_cost || 0)}</span>
                </td>
                <td class="td font-mono font-bold text-xs text-teal-900 whitespace-nowrap">${highlightedBatch}</td>
                <td class="td-num font-bold text-slate-900 text-xs">${qty}</td>
                <td class="td font-mono text-xs whitespace-nowrap">${b.expiry_date || `<span class="text-slate-400">${t('status.no_expiry', 'None')}</span>`}</td>
                <td class="td text-center whitespace-nowrap">
                    ${formatExpiryBadge(b.expiry_date)}
                </td>
            </tr>
        `;
    }).join('');
}

function _renderBatchTable(container) {
    const totalBatchUnits = inventoryData.reduce((acc, b) => acc + (b.remaining_quantity ?? b.current_qty ?? 0), 0);

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="relative flex-1 max-w-sm">
                    <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </span>
                    <input type="text" id="inventory-batch-search-input" placeholder="${t('prod.filter_search', 'Search by medicine name or batch number...')}" class="form-input pl-8 text-xs" oninput="inventorySearchFn(this.value)" value="${escapeHtml(inventorySearch)}">
                </div>

                <div id="inventory-batch-count-header" class="text-xs text-slate-600 font-mono">
                    ${inventoryData.length} ${t('inv.filter_all_batches', 'Batches Displayed')}
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">${t('col.name', 'Medicine Product Name')}</th>
                            <th class="th w-2/12">${t('col.batch_no', 'Batch Number')}</th>
                            <th class="th text-right w-2/12">${t('col.qty', 'Remaining Quantity')}</th>
                            <th class="th w-2/12">${t('col.expiry_date', 'Expiry Date')}</th>
                            <th class="th text-center w-1/12">${t('col.status', 'FEFO Status')}</th>
                        </tr>
                    </thead>
                    <tbody id="inventory-batch-tbody" class="divide-y divide-slate-100 bg-white">
                        <!-- Rendered by _renderBatchTbody -->
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td id="inventory-batch-tfoot-total" class="px-4 py-2.5 text-xs uppercase text-slate-700">${t('inv.filter_all_batches', 'Total Medicine Batches')} (${inventoryData.length})</td>
                            <td class="px-4 py-2.5 font-mono text-xs text-slate-500">-</td>
                            <td id="inventory-batch-tfoot-qty" class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${totalBatchUnits.toLocaleString('en-US')}</td>
                            <td class="px-4 py-2.5 font-mono text-xs text-slate-500">-</td>
                            <td class="px-4 py-2.5 text-center text-xs text-slate-500">-</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

        </div>
    `;

    _renderBatchTbody();
}

window.inventorySearchFn = function(val) {
    inventorySearch = val;
    if (inventoryTab === 'stock') {
        const tbody = document.getElementById('inventory-stock-tbody');
        if (tbody) {
            _renderStockTbody();
            return;
        }
        _renderStockTable(document.getElementById('content-area'));
    } else {
        const tbody = document.getElementById('inventory-batch-tbody');
        if (tbody) {
            _renderBatchTbody();
            return;
        }
        _renderBatchTable(document.getElementById('content-area'));
    }
};

window.inventoryToggleLowStock = function(checked) {
    inventoryLowStockOnly = checked;
    const tbody = document.getElementById('inventory-stock-tbody');
    if (tbody) {
        _renderStockTbody();
        return;
    }
    _renderStockTable(document.getElementById('content-area'));
};

window.clearInventoryFilters = function() {
    inventorySearch = '';
    inventoryLowStockOnly = false;
    const input = document.getElementById('inventory-search-input') || document.getElementById('inventory-batch-search-input');
    if (input) input.value = '';
    const lowCheck = document.getElementById('inventory-low-stock-check');
    if (lowCheck) lowCheck.checked = false;

    if (inventoryTab === 'stock') {
        const tbody = document.getElementById('inventory-stock-tbody');
        if (tbody) {
            _renderStockTbody();
            return;
        }
        _renderStockTable(document.getElementById('content-area'));
    } else {
        const tbody = document.getElementById('inventory-batch-tbody');
        if (tbody) {
            _renderBatchTbody();
            return;
        }
        _renderBatchTable(document.getElementById('content-area'));
    }
};
