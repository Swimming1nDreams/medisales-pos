let inventoryTab = 'stock';
let inventoryData = [];
let inventorySearch = '';
let inventoryLowStockOnly = false;

async function renderInventory(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-secondary text-xs border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 font-semibold" onclick="${inventoryTab === 'stock' ? 'exportInventoryValuationExcel()' : 'exportMedicineBatchesExcel()'}">
                <svg class="w-3.5 h-3.5 text-emerald-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                <span>${t('btn.export_excel', 'Export to Excel')}</span>
            </button>
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

    const tfootEl = document.getElementById('inventory-stock-tfoot'); if (tfootEl) { tfootEl.style.display = filtered.length === 0 ? 'none' : ''; }
    const tfootTotalEl = document.getElementById('inventory-stock-tfoot-total');
    if (tfootTotalEl) tfootTotalEl.textContent = `${t('inv.tab_stock', 'Total Stock On Hand')} (${filtered.length})`;
    const tfootQtyEl = document.getElementById('inventory-stock-tfoot-qty');
    if (tfootQtyEl) tfootQtyEl.textContent = totalQty.toLocaleString('en-US');

    if (filtered.length === 0) {
        if (inventoryData.length === 0 && !inventorySearch && !inventoryLowStockOnly) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="py-14 px-6 text-center">
                        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-50 text-teal-700 mb-3 border border-teal-100 shadow-sm">
                            <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                        </div>
                        <div class="text-sm font-bold text-slate-800">${t('inv.empty_welcome_title', 'Inventory Tracking Ready')}</div>
                        <p class="text-xs text-slate-500 max-w-md mx-auto mt-1.5 mb-5 leading-relaxed">
                            ${t('inv.empty_welcome_desc', 'Once you catalog products or record purchases from suppliers, stock levels, batch expiries and valuations will be tracked here in real time.')}
                        </p>
                        <div class="flex items-center justify-center gap-2.5">
                            <button class="btn btn-primary inline-flex items-center gap-1.5" onclick="navigate('products')">
                                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                                <span>${t('prod.add_button', 'Add New Product')}</span>
                            </button>
                            <button class="btn btn-secondary inline-flex items-center gap-1.5" onclick="navigate('purchases')">
                                <svg class="w-3.5 h-3.5 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                                <span>${t('pur.add_button', 'Receive Purchase')}</span>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-14 text-center">
                    <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-400 mb-3">
                        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </div>
                    <div class="text-sm font-semibold text-slate-700">${t('msg.no_data', 'No stock records found')}</div>
                    <p class="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                        ${inventorySearch || inventoryLowStockOnly ? t('inv.empty_filter', 'No inventory items match your current search or low-stock filter.') : t('inv.empty_catalog', 'There are currently no products tracked in inventory.')}
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
                    <div class="flex items-center gap-1.5 text-[10px] text-slate-500 mt-0.5">
                        <span class="badge badge-purple text-[9px] py-0">${highlightedCat}</span>
                        <span class="text-slate-300">•</span>
                        <span>${t('col.unit', 'Unit')}: <strong class="text-slate-700">${escapeHtml(s.unit_measure || 'piece')}</strong></span>
                    </div>
                </td>
                <td class="td-num">
                    <span class="badge ${isOut ? 'badge-danger font-black' : (isLow ? 'badge-warning font-bold' : 'badge-success font-bold')} text-xs font-mono">
                        ${s.current_stock}
                    </span>
                </td>
                <td class="td-num text-xs text-slate-500 font-mono font-bold">${s.min_stock_level || 0}</td>
                <td class="td text-center">
                    ${isOut ? `<span class="badge badge-danger text-[10px] font-bold">${t('status.out_of_stock', 'Out of Stock')}</span>` : 
                      (isLow ? `<span class="badge badge-warning text-[10px] font-bold">${t('status.low_stock', 'Low Stock')}</span>` : 
                      `<span class="badge badge-success text-[10px] font-bold">${t('status.active', 'In Stock')}</span>`)}
                </td>
                <td class="td text-right whitespace-nowrap">
                    <button class="btn btn-sm btn-secondary text-teal-800 border-teal-200 bg-teal-50/50 hover:bg-teal-100/80 py-0.5 text-xs font-semibold" onclick="navigate('purchases')">
                        ${t('pur.add_button', 'Receive Stock')}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}


function _renderInventoryTabs() {
    return `
        <div class="flex items-center gap-1.5 p-1 bg-slate-200/80 rounded-xl border border-slate-200 overflow-x-auto text-xs flex-shrink-0">
            <button class="px-3.5 py-1.5 font-semibold rounded-lg transition-all flex items-center gap-1.5 ${inventoryTab === 'stock' ? 'bg-teal-700 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'}" onclick="switchInventoryTab('stock')">
                <svg class="w-3.5 h-3.5 ${inventoryTab === 'stock' ? 'text-white' : 'text-teal-700'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                <span>${t('inv.tab_stock', 'Stock on Hand')}</span>
            </button>
            <button class="px-3.5 py-1.5 font-semibold rounded-lg transition-all flex items-center gap-1.5 ${inventoryTab === 'all_batches' ? 'bg-indigo-700 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'}" onclick="switchInventoryTab('all_batches')">
                <svg class="w-3.5 h-3.5 ${inventoryTab === 'all_batches' ? 'text-white' : 'text-indigo-700'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span>${t('inv.filter_all_batches', 'All Medicine Batches')}</span>
            </button>
            <button class="px-3.5 py-1.5 font-semibold rounded-lg transition-all flex items-center gap-1.5 ${inventoryTab === 'expiring_soon' ? 'bg-amber-500 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'}" onclick="switchInventoryTab('expiring_soon')">
                <svg class="w-3.5 h-3.5 ${inventoryTab === 'expiring_soon' ? 'text-white' : 'text-amber-700'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                <span>${t('inv.filter_expiring_soon', 'Expiring within 90 Days')}</span>
            </button>
            <button class="px-3.5 py-1.5 font-semibold rounded-lg transition-all flex items-center gap-1.5 ${inventoryTab === 'expired' ? 'bg-rose-600 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'}" onclick="switchInventoryTab('expired')">
                <svg class="w-3.5 h-3.5 ${inventoryTab === 'expired' ? 'text-white' : 'text-rose-700'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                <span>${t('inv.filter_expired', 'Expired Batches')}</span>
            </button>
        </div>
    `;
}

function _renderStockTable(container) {
    const totalQty = inventoryData.reduce((acc, it) => acc + (it.current_stock || 0), 0);
    const lowCount = inventoryData.filter(it => it.current_stock <= (it.min_stock_level || 5)).length;

    container.innerHTML = `
        <div class="flex flex-col h-full gap-2.5">
            ${_renderInventoryTabs()}
            <div class="card flex flex-col flex-1 min-h-0">
            
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
                    <tfoot id="inventory-stock-tfoot" class="bg-slate-50 font-bold border-t-2 border-slate-300">
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
                        ${inventoryTab === 'expiring_soon' ? t('inv.empty_expiring', 'No batches are currently expiring within 90 days.') : (inventoryTab === 'expired' ? t('inv.empty_expired', 'No expired batches recorded in system.') : t('inv.empty_batches', 'No medicine batches match your filter.'))}
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
        <div class="flex flex-col h-full gap-2.5">
            ${_renderInventoryTabs()}
            <div class="card flex flex-col flex-1 min-h-0">
            
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
                    <tfoot id="inventory-stock-tfoot" class="bg-slate-50 font-bold border-t-2 border-slate-300">
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
