let inventoryTab = 'stock';
let inventoryData = [];
let inventorySearch = '';
let inventoryLowStockOnly = false;

async function renderInventory(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="inline-flex rounded-md border border-slate-300 bg-slate-100 p-0.5">
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${inventoryTab === 'stock' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('stock')">
                    Stock on Hand
                </button>
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${inventoryTab === 'all_batches' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('all_batches')">
                    All Medicine Batches
                </button>
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${inventoryTab === 'expiring_soon' ? 'bg-white text-amber-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('expiring_soon')">
                    Expiring Soon
                </button>
                <button class="px-3 py-1 text-xs font-semibold rounded transition-colors ${inventoryTab === 'expired' ? 'bg-white text-rose-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'}" onclick="switchInventoryTab('expired')">
                    Expired Batches
                </button>
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

window.switchInventoryTab = function(tab) {
    inventoryTab = tab;
    renderInventory(document.getElementById('content-area'));
};

function _renderStockTable(container) {
    let filtered = inventoryData.filter(s => {
        if (inventoryLowStockOnly && s.current_stock > (s.min_stock_level || 5)) return false;
        if (inventorySearch && !s.name.toLowerCase().includes(inventorySearch.toLowerCase()) && !(s.category_name && s.category_name.toLowerCase().includes(inventorySearch.toLowerCase()))) return false;
        return true;
    });

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
                        <input type="text" placeholder="Search stock by product or category..." class="form-input pl-8 text-xs" oninput="inventorySearchFn(this.value)" value="${inventorySearch}">
                    </div>

                    <label class="flex items-center gap-1.5 cursor-pointer text-xs font-semibold text-slate-700 select-none">
                        <input type="checkbox" class="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-3.5 w-3.5" ${inventoryLowStockOnly ? 'checked' : ''} onchange="inventoryToggleLowStock(this.checked)">
                        <span>Low Stock Only</span>
                    </label>
                </div>

                <div class="flex items-center gap-1.5 text-xs">
                    <span class="badge badge-neutral font-mono">${inventoryData.length} Products</span>
                    <span class="badge badge-teal font-mono">${totalQty.toLocaleString('en-US')} Units in Stock</span>
                    ${lowCount > 0 ? `<span class="badge badge-warning font-mono">${lowCount} Low Stock</span>` : '<span class="badge badge-success">All Healthy</span>'}
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">Product Name & Category</th>
                            <th class="th text-right w-2/12">Current Stock</th>
                            <th class="th text-right w-2/12">Reorder Level</th>
                            <th class="th text-center w-2/12">Inventory Status</th>
                            <th class="th text-right w-1/12">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${filtered.length === 0 ? '<tr><td colspan="5" class="py-12 text-center text-slate-400 text-xs">No inventory records found.</td></tr>' : ''}
                        ${filtered.map(s => {
                            const isLow = s.current_stock <= (s.min_stock_level || 5);
                            const isOut = s.current_stock === 0;
                            return `
                                <tr class="tr-hover">
                                    <td class="td">
                                        <div class="font-bold text-slate-900 text-xs leading-snug break-words">${s.name}</div>
                                        <div class="flex items-center gap-1 text-[10px] text-slate-500 mt-0.5">
                                            <span>${s.category_name || 'General'}</span>
                                            <span class="text-slate-300">•</span>
                                            <span>Unit: ${s.unit_measure || 'piece'}</span>
                                        </div>
                                    </td>
                                    <td class="td-num">
                                        <span class="text-xs font-bold ${isOut ? 'text-rose-700 font-black' : (isLow ? 'text-amber-800' : 'text-slate-900')}">
                                            ${s.current_stock}
                                        </span>
                                    </td>
                                    <td class="td-num text-xs text-slate-500 font-mono">${s.min_stock_level || 0}</td>
                                    <td class="td text-center">
                                        ${isOut ? '<span class="badge badge-danger text-[10px]">Out of Stock</span>' : 
                                          (isLow ? '<span class="badge badge-warning text-[10px]">Low Stock</span>' : 
                                          '<span class="badge badge-success text-[10px]">In Stock</span>')}
                                    </td>
                                    <td class="td text-right whitespace-nowrap">
                                        <button class="btn btn-sm btn-secondary py-0.5 text-xs" onclick="navigate('purchases')">
                                            Receive Stock
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700">Total Stock On Hand (${filtered.length} products)</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${filtered.reduce((acc, it) => acc + (it.current_stock || 0), 0).toLocaleString('en-US')} units</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-500">-</td>
                            <td class="px-4 py-2.5 text-center text-xs text-slate-600">${lowCount > 0 ? `<span class="badge badge-warning text-[10px]">${lowCount} Low</span>` : '<span class="badge badge-success text-[10px]">All Healthy</span>'}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-400">-</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

        </div>
    `;
}

function _renderBatchTable(container) {
    let filtered = inventoryData.filter(b => {
        if (inventorySearch && !b.product_name.toLowerCase().includes(inventorySearch.toLowerCase()) && !(b.batch_number && b.batch_number.toLowerCase().includes(inventorySearch.toLowerCase()))) return false;
        return true;
    });

    const totalBatchUnits = filtered.reduce((acc, b) => acc + (b.remaining_quantity ?? b.current_qty ?? 0), 0);

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="relative flex-1 max-w-sm">
                    <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </span>
                    <input type="text" placeholder="Search by medicine name or batch number..." class="form-input pl-8 text-xs" oninput="inventorySearchFn(this.value)" value="${inventorySearch}">
                </div>

                <div class="text-xs text-slate-600 font-mono">
                    Batches Displayed: <strong class="text-slate-900">${filtered.length}</strong>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">Medicine Product Name</th>
                            <th class="th w-2/12">Batch Number</th>
                            <th class="th text-right w-2/12">Remaining Quantity</th>
                            <th class="th w-2/12">Expiry Date</th>
                            <th class="th text-center w-1/12">FEFO Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${filtered.length === 0 ? '<tr><td colspan="5" class="py-12 text-center text-slate-400 text-xs">No batches match this filter criteria.</td></tr>' : ''}
                        ${filtered.map(b => {
                            const qty = b.remaining_quantity ?? b.current_qty ?? 0;
                            return `
                                <tr class="tr-hover">
                                    <td class="td">
                                        <div class="font-bold text-slate-900 text-xs leading-snug break-words">${b.product_name}</div>
                                        <span class="text-[10px] text-slate-500">Unit Cost: ${formatMoney(b.unit_cost || 0)}</span>
                                    </td>
                                    <td class="td font-mono font-bold text-xs text-teal-900 whitespace-nowrap">${b.batch_number || 'N/A'}</td>
                                    <td class="td-num font-bold text-slate-900 text-xs">${qty}</td>
                                    <td class="td font-mono text-xs whitespace-nowrap">${b.expiry_date || '<span class="text-slate-400">None</span>'}</td>
                                    <td class="td text-center whitespace-nowrap">
                                        ${formatExpiryBadge(b.expiry_date)}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700">Total Medicine Batches (${filtered.length} batches)</td>
                            <td class="px-4 py-2.5 font-mono text-xs text-slate-500">-</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${totalBatchUnits.toLocaleString('en-US')} units</td>
                            <td class="px-4 py-2.5 font-mono text-xs text-slate-500">-</td>
                            <td class="px-4 py-2.5 text-center text-xs text-slate-500">-</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

        </div>
    `;
}

window.inventorySearchFn = function(val) {
    inventorySearch = val;
    if (inventoryTab === 'stock') {
        _renderStockTable(document.getElementById('content-area'));
    } else {
        _renderBatchTable(document.getElementById('content-area'));
    }
};

window.inventoryToggleLowStock = function(checked) {
    inventoryLowStockOnly = checked;
    _renderStockTable(document.getElementById('content-area'));
};
