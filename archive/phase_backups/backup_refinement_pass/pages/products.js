let allProducts = [];
let allCategories = [];
let currentCategoryFilter = '';
let currentTypeFilter = 'all';
let currentSearch = '';

async function renderProducts(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="flex items-center gap-2">
                <button class="btn btn-secondary text-xs" onclick="openCategoryModal()">
                    <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h7"></path></svg>
                    <span>Categories</span>
                </button>
                <button class="btn btn-primary text-xs" onclick="openProductModal()">
                    <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>New Product</span>
                </button>
            </div>
        `;
    }

    allProducts = await callBackend('list_products');
    allCategories = await callBackend('list_categories');
    _renderProductsView(container);
}

function _renderProductsView(container) {
    const filtered = allProducts.filter(p => {
        if (currentCategoryFilter && p.category_id !== parseInt(currentCategoryFilter)) return false;
        if (currentTypeFilter === 'medicine' && !p.is_medicine) return false;
        if (currentTypeFilter === 'general' && p.is_medicine) return false;
        if (currentSearch && !p.name.toLowerCase().includes(currentSearch.toLowerCase())) return false;
        return true;
    });

    const activeCount = allProducts.filter(p => p.is_active).length;
    const medCount = allProducts.filter(p => p.is_medicine).length;
    const lowCount = allProducts.filter(p => p.current_stock <= (p.min_stock_level || 5)).length;

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Filter & Stats Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="flex flex-wrap items-center gap-2 flex-1 min-w-[280px]">
                    <div class="relative flex-1 min-w-[180px] max-w-sm">
                        <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        </span>
                        <input type="text" placeholder="Search catalog..." class="form-input pl-8 text-xs" oninput="filterProducts(this.value)" value="${currentSearch}">
                    </div>
                    
                    <select class="form-select text-xs w-40" onchange="filterCategory(this.value)">
                        <option value="">All Categories</option>
                        ${allCategories.map(c => `<option value="${c.id}" ${currentCategoryFilter == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                    </select>

                    <select class="form-select text-xs w-36" onchange="filterType(this.value)">
                        <option value="all" ${currentTypeFilter === 'all' ? 'selected' : ''}>All Types</option>
                        <option value="medicine" ${currentTypeFilter === 'medicine' ? 'selected' : ''}>Medicines Only</option>
                        <option value="general" ${currentTypeFilter === 'general' ? 'selected' : ''}>General Only</option>
                    </select>
                </div>

                <!-- Stats summary badges -->
                <div class="flex items-center gap-1.5 text-xs">
                    <span class="badge badge-neutral font-mono">${allProducts.length} Total</span>
                    <span class="badge badge-success font-mono">${activeCount} Active</span>
                    <span class="badge badge-teal font-mono">${medCount} Meds</span>
                    ${lowCount > 0 ? `<span class="badge badge-warning font-mono">${lowCount} Low Stock</span>` : ''}
                </div>
            </div>

            <!-- Table - Engineered to fit desktop viewport without clipping -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">Product Name & Specifications</th>
                            <th class="th w-3/12">Category</th>
                            <th class="th text-right w-2/12">Selling Price</th>
                            <th class="th text-right w-2/12">Stock on Hand</th>
                            <th class="th text-center w-1/12">Status</th>
                            <th class="th text-right w-1/12">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${filtered.length === 0 ? '<tr><td colspan="6" class="py-12 text-center text-slate-400 text-xs">No products found matching your search and filter criteria.</td></tr>' : ''}
                        ${filtered.map(p => {
                            const isLow = p.current_stock <= (p.min_stock_level || 5);
                            return `
                                <tr class="tr-hover ${!p.is_active ? 'opacity-60 bg-slate-50/50' : ''}">
                                    <td class="td">
                                        <div class="font-bold text-slate-900 text-xs leading-snug break-words">${p.name}</div>
                                        <div class="flex items-center gap-1.5 mt-0.5">
                                            <span class="text-[10px] text-slate-500">Unit: ${p.unit_measure || 'piece'}</span>
                                            <span class="text-slate-300">•</span>
                                            ${p.is_medicine ? 
                                                '<span class="badge badge-teal text-[9px] py-0">Medicine (FEFO)</span>' : 
                                                '<span class="badge badge-neutral text-[9px] py-0">General Goods</span>'}
                                        </div>
                                    </td>
                                    <td class="td text-xs text-slate-700">
                                        ${p.category_name || (allCategories.find(c => c.id === p.category_id)?.name) || '-'}
                                    </td>
                                    <td class="td-num font-bold text-slate-900 text-xs">
                                        ${formatMoney(p.selling_price)}
                                    </td>
                                    <td class="td-num">
                                        <span class="font-bold text-xs ${isLow ? 'text-amber-800' : 'text-slate-800'}">${p.current_stock}</span>
                                        <span class="text-[10px] text-slate-400 block">Min: ${p.min_stock_level || 0}</span>
                                    </td>
                                    <td class="td text-center">
                                        <span class="badge ${p.is_active ? 'badge-success' : 'badge-neutral'} text-[10px]">
                                            ${p.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td class="td text-right whitespace-nowrap space-x-1">
                                        <button class="btn btn-sm btn-secondary py-0.5 text-xs" onclick="editProduct(${p.id})">Edit</button>
                                        <button class="btn btn-sm ${p.is_active ? 'btn-danger' : 'btn-success'} py-0.5 text-xs" onclick="confirmToggleProduct(${p.id}, ${!p.is_active})">
                                            ${p.is_active ? 'Disable' : 'Enable'}
                                        </button>
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

window.filterProducts = function(val) {
    currentSearch = val;
    _renderProductsView(document.getElementById('content-area'));
};

window.filterCategory = function(val) {
    currentCategoryFilter = val;
    _renderProductsView(document.getElementById('content-area'));
};

window.filterType = function(val) {
    currentTypeFilter = val;
    _renderProductsView(document.getElementById('content-area'));
};

window.openProductModal = function(p = null) {
    const isEdit = p !== null;
    const title = isEdit ? "Edit Product Details" : "Register New Product";
    
    const html = `
        <form id="product-form" class="space-y-3 text-xs" onsubmit="event.preventDefault()">
            <div>
                <label class="form-label" for="p-name">Product Name & Strength / Dosage *</label>
                <input type="text" id="p-name" class="form-input text-xs" required placeholder="e.g. Paracetamol 500mg Tablets, Augmentin 625mg" value="${isEdit ? p.name : ''}">
                <span class="form-hint">Include dosage, strength, and brand/generic name clearly.</span>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="p-category">Category *</label>
                    <select id="p-category" class="form-select text-xs" required>
                        <option value="">Select Category</option>
                        ${allCategories.map(c => `<option value="${c.id}" ${isEdit && p.category_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                    </select>
                </div>
                <div>
                    <label class="form-label" for="p-unit">Unit of Measure *</label>
                    <input type="text" id="p-unit" class="form-input text-xs" required placeholder="e.g. strip, bottle, box, tube" value="${isEdit ? p.unit_measure : ''}">
                </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="p-price">Selling Price (Kyat) *</label>
                    <input type="number" id="p-price" class="form-input text-xs font-mono font-bold" required min="0" placeholder="0" value="${isEdit ? p.selling_price : ''}">
                    <span class="form-hint">Standard cash retail price per unit.</span>
                </div>
                <div>
                    <label class="form-label" for="p-min">Reorder Alert Level *</label>
                    <input type="number" id="p-min" class="form-input text-xs font-mono" required min="0" placeholder="5" value="${isEdit ? p.min_stock_level : 5}">
                    <span class="form-hint">Triggers low stock notice when below this.</span>
                </div>
            </div>

            <div class="p-3 bg-slate-50 border border-slate-200 rounded-md">
                <label class="flex items-start gap-2.5 cursor-pointer">
                    <input type="checkbox" id="p-medicine" class="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-4 w-4" ${isEdit && p.is_medicine ? 'checked' : ''} ${isEdit ? 'disabled' : ''}>
                    <div>
                        <span class="text-xs font-bold text-slate-800 block">Pharmaceutical Medicine (Enforces FEFO)</span>
                        <span class="text-[11px] text-slate-500 leading-normal block mt-0.5">Requires batch numbers & expiry dates when recording purchases. Dispensed automatically by earliest expiry first.</span>
                    </div>
                </label>
            </div>
        </form>
    `;

    openModal(title, html, async () => {
        const name = document.getElementById('p-name').value.trim();
        const catId = parseInt(document.getElementById('p-category').value);
        const price = parseFloat(document.getElementById('p-price').value);
        const min = parseInt(document.getElementById('p-min').value);
        const unit = document.getElementById('p-unit').value.trim();
        const isMed = document.getElementById('p-medicine').checked;

        if (!name) throw "Product name is required.";
        if (!catId) throw "Category selection is required.";
        if (isNaN(price) || price < 0) throw "Valid positive selling price in Kyat is required.";
        if (isNaN(min) || min < 0) throw "Minimum stock alert level is required.";
        if (!unit) throw "Unit of measure is required.";

        if (isEdit) {
            await callBackend('update_product', p.id, name, catId, unit, price, min, p.is_active);
            showToast(`Product "${name}" updated successfully.`);
        } else {
            await callBackend('create_product', name, catId, unit, price, min, isMed);
            showToast(`Product "${name}" registered successfully.`);
        }
        
        allProducts = await callBackend('list_products');
        _renderProductsView(document.getElementById('content-area'));
    }, {
        maxWidth: 'max-w-md',
        saveText: isEdit ? 'Save Changes' : 'Register Product'
    });
};

window.editProduct = function(id) {
    const p = allProducts.find(x => x.id === id);
    if (p) openProductModal(p);
};

window.confirmToggleProduct = function(id, newState) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    const actionLabel = newState ? 'Enable' : 'Disable';
    openConfirmModal(
        `${actionLabel} Product • ${p.name}`,
        `Are you sure you want to ${actionLabel.toLowerCase()} "${p.name}"? ${!newState ? 'Disabled products will not appear in the Point of Sale catalog.' : 'Enabled products will immediately appear in the catalog.'}`,
        async () => {
            await callBackend('update_product', p.id, p.name, p.category_id, p.unit_measure, p.selling_price, p.min_stock_level, newState);
            showToast(`Product "${p.name}" ${newState ? 'enabled' : 'disabled'}.`);
            allProducts = await callBackend('list_products');
            _renderProductsView(document.getElementById('content-area'));
        },
        { confirmText: `${actionLabel} Product`, danger: !newState }
    );
};

window.openCategoryModal = function() {
    const html = `
        <div class="space-y-3 text-xs">
            <div>
                <label class="form-label">Active Product Categories</label>
                <div class="flex flex-wrap gap-1 max-h-36 overflow-y-auto p-2 border rounded border-slate-200 bg-slate-50">
                    ${allCategories.map(c => `
                        <span class="inline-flex items-center px-2 py-0.5 bg-white border border-slate-200 text-slate-800 text-[11px] font-medium rounded shadow-xs">
                            ${c.name}
                        </span>
                    `).join('')}
                </div>
            </div>
            
            <form onsubmit="event.preventDefault()">
                <label class="form-label" for="c-name">New Category Name *</label>
                <input type="text" id="c-name" class="form-input text-xs" placeholder="e.g. Dermatological, Oral Care, Supplements" required>
            </form>
        </div>
    `;

    openModal("Product Categories", html, async () => {
        const name = document.getElementById('c-name').value.trim();
        if (!name) throw "Category name is required.";
        await callBackend('create_category', name);
        showToast(`Category "${name}" created successfully.`);
        allCategories = await callBackend('list_categories');
        allProducts = await callBackend('list_products');
        _renderProductsView(document.getElementById('content-area'));
    }, {
        saveText: 'Add Category'
    });
};
