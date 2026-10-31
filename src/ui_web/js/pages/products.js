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
                <button class="btn btn-secondary text-xs" onclick="exportProductsExcel()">
                    <svg class="w-3.5 h-3.5 text-emerald-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span>${t('btn.export_excel', 'Export to Excel')}</span>
                </button>
                <button class="btn btn-secondary text-xs" onclick="openCategoryModal()">
                    <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h7"></path></svg>
                    <span>${t('prod.field_category', 'Categories')}</span>
                </button>
                <button class="btn btn-primary text-xs" onclick="openProductModal()">
                    <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>${t('prod.add_button', 'New Product')}</span>
                </button>
            </div>
        `;
    }

    allProducts = await callBackend('list_products');
    allCategories = await callBackend('list_categories');
    _renderProductsView(container);
}

window.exportProductsExcel = async function() {
    try {
        const res = await callBackend('export_products_excel');
        if (res && !res.cancelled) {
            showToast(`${t('msg.export_success', 'Spreadsheet successfully exported to:')}\n${res.file_path}`);
        }
    } catch (e) {
        showToast(`${t('msg.export_failed', 'Excel export failed:')} ${e}`, "error");
    }
};

function formatSmartStock(qty, baseUnit, packagings) {
    if (!packagings || packagings.length === 0 || qty <= 0) {
        return `${qty} ${baseUnit || 'units'}`;
    }
    const sorted = [...packagings].sort((a, b) => b.conversion_factor - a.conversion_factor);
    let rem = qty;
    const parts = [];
    for (const pkg of sorted) {
        const count = Math.floor(rem / pkg.conversion_factor);
        if (count > 0) {
            parts.push(`${count} ${pkg.unit_name}`);
            rem %= pkg.conversion_factor;
        }
    }
    if (rem > 0 || parts.length === 0) {
        parts.push(`${rem} ${baseUnit}`);
    }
    return `${qty} ${baseUnit} (${parts.join(' ')})`;
}

function _renderProductsTbody() {
    const tbody = document.getElementById('products-tbody');
    if (!tbody) return;

    let candidates = allProducts.filter(p => {
        if (currentCategoryFilter && p.category_id !== parseInt(currentCategoryFilter)) return false;
        if (currentTypeFilter === 'medicine' && !p.is_medicine) return false;
        if (currentTypeFilter === 'general' && p.is_medicine) return false;
        return true;
    });

    const filtered = (typeof window.filterAndRankItems === 'function')
        ? window.filterAndRankItems(candidates, currentSearch, (p) => ({
            primary: p.name,
            secondary: [p.category_name, p.unit_measure]
        }))
        : candidates.filter(p => !currentSearch || p.name.toLowerCase().includes(currentSearch.toLowerCase()));

    const countBadge = document.getElementById('products-badge-count');
    if (countBadge) {
        countBadge.textContent = `${filtered.length} ${t('status.normal', 'Total')}`;
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="py-16 text-center">
                    <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-400 mb-3">
                        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </div>
                    <div class="text-sm font-semibold text-slate-700">${t('msg.no_data', 'No matching products found')}</div>
                    <p class="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                        No products match your current search terms or category/type filters.
                    </p>
                    ${(currentSearch || currentCategoryFilter || currentTypeFilter !== 'all') ? `
                        <button class="btn btn-sm btn-secondary inline-flex items-center gap-1.5" onclick="clearProductFilters()">
                            <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            <span>${t('btn.clear', 'Clear Search & Filters')}</span>
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-primary inline-flex items-center gap-1.5" onclick="openProductModal()">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                            <span>${t('prod.add_button', 'Add New Product')}</span>
                        </button>
                    `}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(p => {
        const isLow = p.current_stock <= (p.min_stock_level || 5);
        const highlightedName = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(p.name, currentSearch)
            : escapeHtml(p.name);
        const catName = p.category_name || (allCategories.find(c => c.id === p.category_id)?.name) || '-';
        const highlightedCat = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(catName, currentSearch)
            : escapeHtml(catName);
        const packagings = p.packagings || [];

        return `
            <tr class="tr-hover ${!p.is_active ? 'opacity-60 bg-slate-50/50' : ''}">
                <td class="td">
                    <div class="font-bold text-slate-900 text-xs leading-snug break-words" title="${escapeHtml(p.name)}">${highlightedName}</div>
                    <div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
                        <span class="text-[10px] text-slate-500">${t('col.unit', 'Unit')}: ${escapeHtml(p.unit_measure || 'piece')}</span>
                        <span class="text-slate-300">•</span>
                        ${p.is_medicine ? 
                            `<span class="badge badge-teal text-[9px] py-0">${t('prod.type_medicine', 'Medicine (FEFO)')}</span>` : 
                            `<span class="badge badge-neutral text-[9px] py-0">${t('prod.type_general', 'General Goods')}</span>`}
                    </div>
                    ${packagings.length > 0 ? `
                        <div class="flex flex-wrap items-center gap-1 mt-1 text-[10px]">
                            <span class="px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200">
                                1 ${escapeHtml(p.unit_measure)}: ${formatMoney(p.selling_price)}
                            </span>
                            ${packagings.map(pkg => `
                                <span class="px-1.5 py-0.2 rounded bg-teal-50 text-teal-800 border border-teal-200 font-semibold" title="1 ${escapeHtml(pkg.unit_name)} = ${pkg.conversion_factor} ${escapeHtml(p.unit_measure)}">
                                    1 ${escapeHtml(pkg.unit_name)} [${pkg.conversion_factor}]: ${formatMoney(pkg.selling_price)}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </td>
                <td class="td text-xs text-slate-700">
                    ${highlightedCat}
                </td>
                <td class="td-num font-bold text-slate-900 text-xs">
                    ${formatMoney(p.selling_price)}
                </td>
                <td class="td-num">
                    <span class="font-bold text-xs ${isLow ? 'text-amber-800' : 'text-slate-800'}">${p.current_stock}</span>
                    <span class="text-[10px] text-slate-400 block" title="${escapeHtml(formatSmartStock(p.current_stock, p.unit_measure, packagings))}">Min: ${p.min_stock_level || 0}</span>
                </td>
                <td class="td text-center">
                    <span class="badge ${p.is_active ? 'badge-success' : 'badge-neutral'} text-[10px]">
                        ${p.is_active ? t('status.active', 'Active') : t('status.inactive', 'Inactive')}
                    </span>
                </td>
                <td class="td text-right whitespace-nowrap space-x-1">
                    <button class="btn btn-sm btn-secondary py-0.5 text-xs" onclick="editProduct(${p.id})">${t('btn.edit', 'Edit')}</button>
                    <button class="btn btn-sm ${p.is_active ? 'btn-danger' : 'btn-success'} py-0.5 text-xs" onclick="confirmToggleProduct(${p.id}, ${!p.is_active})">
                        ${p.is_active ? t('btn.delete', 'Disable') : t('btn.add', 'Enable')}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function _renderProductsView(container) {
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
                        <input type="text" id="products-search-input" placeholder="${t('prod.filter_search', 'Search catalog...')}" class="form-input pl-8 text-xs" oninput="filterProducts(this.value)" value="${escapeHtml(currentSearch)}">
                    </div>
                    
                    <select id="products-cat-select" class="form-select text-xs w-40" onchange="filterCategory(this.value)">
                        <option value="">${t('sales.all_categories', 'All Categories')}</option>
                        ${allCategories.map(c => `<option value="${c.id}" ${currentCategoryFilter == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                    </select>

                    <select id="products-type-select" class="form-select text-xs w-36" onchange="filterType(this.value)">
                        <option value="all" ${currentTypeFilter === 'all' ? 'selected' : ''}>${t('prod.type_all', 'All Types')}</option>
                        <option value="medicine" ${currentTypeFilter === 'medicine' ? 'selected' : ''}>${t('prod.type_medicine', 'Medicines Only')}</option>
                        <option value="general" ${currentTypeFilter === 'general' ? 'selected' : ''}>${t('prod.type_general', 'General Only')}</option>
                    </select>
                </div>

                <!-- Stats summary badges -->
                <div class="flex items-center gap-1.5 text-xs">
                    <span id="products-badge-count" class="badge badge-neutral font-mono">${allProducts.length} ${t('status.normal', 'Total')}</span>
                    <span class="badge badge-success font-mono">${activeCount} ${t('status.active', 'Active')}</span>
                    <span class="badge badge-teal font-mono">${medCount} ${t('prod.type_medicine', 'Meds')}</span>
                    ${lowCount > 0 ? `<span class="badge badge-warning font-mono">${lowCount} ${t('status.low_stock', 'Low Stock')}</span>` : ''}
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">${t('col.name', 'Product Name & Specifications')}</th>
                            <th class="th w-3/12">${t('col.category', 'Category')}</th>
                            <th class="th text-right w-2/12">${t('col.price', 'Selling Price')}</th>
                            <th class="th text-right w-2/12">${t('col.stock', 'Stock on Hand')}</th>
                            <th class="th text-center w-1/12">${t('col.status', 'Status')}</th>
                            <th class="th text-right w-1/12">${t('col.actions', 'Actions')}</th>
                        </tr>
                    </thead>
                    <tbody id="products-tbody" class="divide-y divide-slate-100 bg-white">
                        <!-- Rows rendered dynamically -->
                    </tbody>
                </table>
            </div>
        </div>
    `;

    _renderProductsTbody();
}

window.filterProducts = function(val) {
    currentSearch = val;
    const tbody = document.getElementById('products-tbody');
    if (tbody) {
        _renderProductsTbody();
        return;
    }
    _renderProductsView(document.getElementById('content-area'));
};

window.filterCategory = function(val) {
    currentCategoryFilter = val;
    const tbody = document.getElementById('products-tbody');
    if (tbody) {
        _renderProductsTbody();
        return;
    }
    _renderProductsView(document.getElementById('content-area'));
};

window.filterType = function(val) {
    currentTypeFilter = val;
    const tbody = document.getElementById('products-tbody');
    if (tbody) {
        _renderProductsTbody();
        return;
    }
    _renderProductsView(document.getElementById('content-area'));
};

window.clearProductFilters = function() {
    currentSearch = '';
    currentCategoryFilter = '';
    currentTypeFilter = 'all';
    const input = document.getElementById('products-search-input');
    if (input) input.value = '';
    const catSel = document.getElementById('products-cat-select');
    if (catSel) catSel.value = '';
    const typeSel = document.getElementById('products-type-select');
    if (typeSel) typeSel.value = 'all';
    const tbody = document.getElementById('products-tbody');
    if (tbody) {
        _renderProductsTbody();
        return;
    }
    _renderProductsView(document.getElementById('content-area'));
};

window.addPackagingRow = function(unitName = '', factor = '', price = '') {
    const container = document.getElementById('p-packagings-list');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'pkg-row grid grid-cols-12 gap-2 items-center p-2 rounded bg-slate-50 border border-slate-200 text-xs';
    row.innerHTML = `
        <div class="col-span-4">
            <label class="text-[10px] text-slate-500 block mb-0.5">${t('prod.pkg_name', 'Packaging Unit')} *</label>
            <input type="text" class="form-input text-xs pkg-name" placeholder="e.g. Strip / Box" value="${escapeHtml(unitName)}" required>
        </div>
        <div class="col-span-3">
            <label class="text-[10px] text-slate-500 block mb-0.5">${t('prod.pkg_factor', 'Base Units')} *</label>
            <input type="number" class="form-input text-xs font-mono pkg-factor" placeholder="e.g. 10" min="2" value="${factor || ''}" required>
        </div>
        <div class="col-span-4">
            <label class="text-[10px] text-slate-500 block mb-0.5">${t('prod.pkg_price', 'Price (Kyat)')} *</label>
            <input type="number" class="form-input text-xs font-mono font-bold pkg-price" placeholder="Kyat" min="0" value="${price || ''}" required>
        </div>
        <div class="col-span-1 pt-3 text-center">
            <button type="button" class="text-rose-500 hover:text-rose-700 font-bold p-1 text-base leading-none" onclick="this.closest('.pkg-row').remove()" title="Remove unit">&times;</button>
        </div>
    `;
    container.appendChild(row);
};

window.openProductModal = function(p = null) {
    const isEdit = p !== null;
    const title = isEdit ? t('prod.modal_edit_title', "Edit Product Details") : t('prod.modal_add_title', "Register New Product");
    
    const html = `
        <form id="product-form" class="space-y-3 text-xs" onsubmit="event.preventDefault()">
            <div>
                <label class="form-label" for="p-name">${t('prod.field_name', 'Product Name & Strength / Dosage')} *</label>
                <input type="text" id="p-name" class="form-input text-xs" required placeholder="e.g. Paracetamol 500mg Tablets, Augmentin 625mg" value="${isEdit ? escapeHtml(p.name) : ''}">
                <span class="form-hint">Include dosage, strength, and brand/generic name clearly.</span>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="p-category">${t('prod.field_category', 'Category')} *</label>
                    <select id="p-category" class="form-select text-xs" required>
                        <option value="">${t('sales.all_categories', 'Select Category')}</option>
                        ${allCategories.map(c => `<option value="${c.id}" ${isEdit && p.category_id === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`).join('')}
                    </select>
                </div>
                <div>
                    <label class="form-label" for="p-unit">${t('prod.field_unit', 'Base Unit of Measure')} *</label>
                    <input type="text" id="p-unit" class="form-input text-xs" required placeholder="e.g. tablet, capsule, bottle, piece" value="${isEdit ? escapeHtml(p.unit_measure) : ''}">
                    <span class="form-hint">The smallest retail unit (e.g. tablet).</span>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="p-price">${t('prod.field_price', 'Base Unit Selling Price (Kyat)')} *</label>
                    <input type="number" id="p-price" class="form-input text-xs font-mono font-bold" required min="0" placeholder="0" value="${isEdit ? p.selling_price : ''}">
                    <span class="form-hint">Price per base unit (e.g. 1 tablet).</span>
                </div>
                <div>
                    <label class="form-label" for="p-min">${t('prod.field_min_stock', 'Reorder Alert Level')} *</label>
                    <input type="number" id="p-min" class="form-input text-xs font-mono" required min="0" placeholder="5" value="${isEdit ? p.min_stock_level : 5}">
                    <span class="form-hint">Triggers low stock notice when below this.</span>
                </div>
            </div>

            <!-- Multi-unit Packaging Configuration Section -->
            <div class="p-3 bg-slate-50/80 border border-slate-200 rounded-md space-y-2">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="text-xs font-bold text-slate-800 block">${t('prod.packagings_title', 'Multi-unit Packaging (Sub-units)')}</span>
                        <span class="text-[11px] text-slate-500">Optional: define larger packaging units (e.g. Strip = 10, Box = 100).</span>
                    </div>
                    <button type="button" class="btn btn-sm btn-secondary text-xs px-2 py-0.5" onclick="addPackagingRow()">
                        + ${t('prod.add_packaging', 'Add Unit')}
                    </button>
                </div>
                <div id="p-packagings-list" class="space-y-1.5 max-h-40 overflow-y-auto pt-1">
                    <!-- Dynamic packaging rows -->
                </div>
            </div>

            <div class="p-3 bg-slate-50 border border-slate-200 rounded-md">
                <label class="flex items-start gap-2.5 cursor-pointer">
                    <input type="checkbox" id="p-medicine" class="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-4 w-4" ${isEdit && p.is_medicine ? 'checked' : ''} ${isEdit ? 'disabled' : ''}>
                    <div>
                        <span class="text-xs font-bold text-slate-800 block">${t('prod.field_is_medicine', 'Pharmaceutical Medicine (Enforces FEFO)')}</span>
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

        // Collect packagings
        const pkgRows = document.querySelectorAll('.pkg-row');
        const packagings = [];
        for (const row of pkgRows) {
            const uname = row.querySelector('.pkg-name').value.trim();
            const ufactor = parseInt(row.querySelector('.pkg-factor').value);
            const uprice = parseFloat(row.querySelector('.pkg-price').value);
            if (!uname) throw "All packaging units must have a unit name.";
            if (uname.toLowerCase() === unit.toLowerCase()) throw `Packaging unit "${uname}" cannot have the same name as base unit.`;
            if (isNaN(ufactor) || ufactor <= 1) throw `Conversion factor for "${uname}" must be greater than 1 base unit.`;
            if (isNaN(uprice) || uprice < 0) throw `Valid selling price required for "${uname}".`;
            packagings.push({
                unit_name: uname,
                conversion_factor: ufactor,
                selling_price: uprice
            });
        }

        const packagingsJson = JSON.stringify(packagings);

        if (isEdit) {
            await callBackend('update_product', p.id, name, catId, unit, price, min, p.is_active, packagingsJson);
            showToast(`Product "${name}" updated successfully.`);
        } else {
            await callBackend('create_product', name, catId, unit, price, min, isMed, packagingsJson);
            showToast(`Product "${name}" registered successfully.`);
        }
        
        allProducts = await callBackend('list_products');
        _renderProductsView(document.getElementById('content-area'));
    }, {
        maxWidth: 'max-w-lg',
        saveText: isEdit ? t('btn.save', 'Save Changes') : t('btn.add', 'Register Product')
    });

    if (isEdit && p.packagings && p.packagings.length > 0) {
        setTimeout(() => {
            p.packagings.forEach(pkg => addPackagingRow(pkg.unit_name, pkg.conversion_factor, pkg.selling_price));
        }, 50);
    }
};

window.editProduct = function(id) {
    const p = allProducts.find(x => x.id === id);
    if (p) openProductModal(p);
};

window.confirmToggleProduct = function(id, newState) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    const actionLabel = newState ? t('btn.add', 'Enable') : t('btn.delete', 'Disable');
    openConfirmModal(
        `${actionLabel} • ${p.name}`,
        `Are you sure you want to update "${p.name}"? ${!newState ? 'Disabled products will not appear in the Point of Sale catalog.' : 'Enabled products will immediately appear in the catalog.'}`,
        async () => {
            await callBackend('update_product', p.id, p.name, p.category_id, p.unit_measure, p.selling_price, p.min_stock_level, newState);
            showToast(`Product "${p.name}" updated.`);
            allProducts = await callBackend('list_products');
            _renderProductsView(document.getElementById('content-area'));
        },
        { danger: !newState, confirmText: actionLabel }
    );
};

window.openCategoryModal = function() {
    const html = `
        <div class="space-y-4 text-xs">
            <!-- Add category -->
            <div class="flex items-center gap-2">
                <input type="text" id="new-cat-name" class="form-input text-xs flex-1" placeholder="e.g. Antibiotics, Baby Care, Beverages" required>
                <button type="button" class="btn btn-primary text-xs" onclick="addCategorySubmit()">${t('btn.add', 'Add')}</button>
            </div>
            
            <!-- Category list -->
            <div class="border border-slate-200 rounded-md divide-y divide-slate-100 max-h-56 overflow-y-auto bg-white" id="cat-list">
                ${allCategories.map(c => `
                    <div class="p-2 flex items-center justify-between hover:bg-slate-50 transition-colors">
                        <span class="font-medium text-slate-800">${escapeHtml(c.name)}</span>
                        <span class="badge ${c.is_active ? 'badge-success' : 'badge-neutral'} text-[10px]">${c.is_active ? t('status.active', 'Active') : t('status.inactive', 'Inactive')}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    openModal(t('prod.field_category', 'Manage Product Categories'), html, null, {
        maxWidth: 'max-w-md',
        cancelText: t('btn.done', 'Done')
    });
};

window.addCategorySubmit = async function() {
    const input = document.getElementById('new-cat-name');
    const name = input ? input.value.trim() : '';
    if (!name) return;
    
    try {
        await callBackend('create_category', name);
        showToast(`Category "${name}" created.`);
        allCategories = await callBackend('list_categories');
        
        // Update category list inside modal
        const list = document.getElementById('cat-list');
        if (list) {
            list.innerHTML = allCategories.map(c => `
                <div class="p-2 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <span class="font-medium text-slate-800">${escapeHtml(c.name)}</span>
                    <span class="badge ${c.is_active ? 'badge-success' : 'badge-neutral'} text-[10px]">${c.is_active ? t('status.active', 'Active') : t('status.inactive', 'Inactive')}</span>
                </div>
            `).join('');
        }
        input.value = '';
    } catch(e) {
        showToast(e, "error");
    }
};