let purchaseStart = '';
let purchaseEnd = '';
let purchCart = [];
let purchSuppliers = [];
let purchProducts = [];

async function renderPurchases(container) {
    if (!purchaseStart) {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        purchaseStart = d.toISOString().split('T')[0];
        purchaseEnd = new Date().toISOString().split('T')[0];
    }
    
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="flex items-center gap-2">
                <button class="btn btn-secondary text-xs" onclick="exportPurchasesExcel()">
                    <svg class="w-3.5 h-3.5 text-emerald-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span>${t('btn.export_excel', 'Export to Excel')}</span>
                </button>
                <button class="btn btn-primary text-xs" onclick="openPurchaseModal()">
                    <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>${t('pur.add_button', 'Record Purchase Invoice')}</span>
                </button>
            </div>
        `;
    }

    showLoading(true);
    let purchases = [];
    try {
        purchases = await callBackend('get_purchases', purchaseStart, purchaseEnd);
    } catch (e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }

    const totalInvoiced = purchases.reduce((acc, p) => acc + (p.total_amount || 0), 0);
    const totalPaid = purchases.reduce((acc, p) => acc + (p.amount_paid || 0), 0);
    const totalDue = totalInvoiced - totalPaid;

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2.5">
                <div class="flex items-center gap-2 text-xs">
                    <span class="font-semibold text-slate-700">${t('sales.filter_start', 'Invoice Period:')}</span>
                    <input type="date" id="purch-start" class="form-input text-xs w-36 py-1" value="${purchaseStart}" onchange="updatePurchaseDates()">
                    <span class="text-slate-400">to</span>
                    <input type="date" id="purch-end" class="form-input text-xs w-36 py-1" value="${purchaseEnd}" onchange="updatePurchaseDates()">
                    <button class="btn btn-sm btn-secondary" onclick="updatePurchaseDates()">${t('btn.filter', 'Apply')}</button>
                </div>

                <div class="flex items-center gap-2 text-xs">
                    <span class="badge badge-neutral font-mono">${purchases.length} ${t('col.invoice', 'Invoices')}</span>
                    <span class="badge badge-teal font-mono font-bold">${t('pur.total_amount', 'Invoiced')}: ${formatMoney(totalInvoiced)}</span>
                    <span class="badge badge-success font-mono">${t('col.paid', 'Paid')}: ${formatMoney(totalPaid)}</span>
                    ${totalDue > 0 ? `<span class="badge badge-warning font-mono">${t('pur.outstanding', 'Due')}: ${formatMoney(totalDue)}</span>` : `<span class="badge badge-success">${t('status.completed', 'Zero Balance')}</span>`}
                </div>
            </div>

            <!-- Invoices Table -->
            <div class="flex-1 overflow-auto">
                <table class="table w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-2/12">${t('pur.date', 'Invoice Date')}</th>
                            <th class="th w-2/12">${t('pur.invoice_no', 'Bill / PO Ref #')}</th>
                            <th class="th w-3/12">${t('pur.supplier', 'Supplier / Vendor')}</th>
                            <th class="th text-right w-2/12">${t('pur.total_amount', 'Total Amount')}</th>
                            <th class="th text-right w-2/12">${t('pur.amount_paid', 'Paid Amount')}</th>
                            <th class="th text-right w-2/12">${t('pur.outstanding', 'Balance Due')}</th>
                            <th class="th text-center w-1/12">${t('col.status', 'Payment Status')}</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${purchases.length === 0 ? `<tr><td colspan="7" class="py-12 text-center text-slate-400 text-xs">${t('msg.no_data', 'No purchase invoices found in this period.')}</td></tr>` : ''}
                        ${purchases.map(p => {
                            const paid = p.amount_paid || 0;
                            const due = (p.total_amount || 0) - paid;
                            const isPaid = due <= 0;
                            return `
                                <tr class="tr-hover">
                                    <td class="td text-xs font-mono text-slate-600 whitespace-nowrap">${p.date}</td>
                                    <td class="td font-mono font-bold text-xs text-teal-900 whitespace-nowrap">${p.reference}</td>
                                    <td class="td text-xs font-bold text-slate-800 break-words">${p.supplier_name || '-'}</td>
                                    <td class="td-num font-bold text-slate-900 text-xs whitespace-nowrap">${formatMoney(p.total_amount)}</td>
                                    <td class="td-num text-xs text-slate-600 whitespace-nowrap">${formatMoney(paid)}</td>
                                    <td class="td-num text-xs font-mono whitespace-nowrap ${due > 0 ? 'text-amber-800 font-bold' : 'text-slate-400'}">${formatMoney(due)}</td>
                                    <td class="td text-center whitespace-nowrap">
                                        <span class="badge ${isPaid ? 'badge-success' : 'badge-warning'} text-[10px]">
                                            ${isPaid ? t('status.completed', 'Fully Paid') : t('status.active', 'Pending Payment')}
                                        </span>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700" colspan="3">${t('rep.disclosure_purchases', 'Total Period Procurement')} (${purchases.length})</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${formatMoney(totalInvoiced)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-700">${formatMoney(totalPaid)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs ${totalDue > 0 ? 'text-amber-800 font-bold' : 'text-slate-500'}">${formatMoney(totalDue)}</td>
                            <td class="px-4 py-2.5 text-center text-xs text-slate-400">-</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

        </div>
    `;
}

window.exportPurchasesExcel = async function() {
    try {
        const res = await callBackend('export_purchases_excel', purchaseStart, purchaseEnd);
        if (res && !res.cancelled) {
            showToast(`${t('msg.export_success', 'Spreadsheet successfully exported to:')}\n${res.file_path}`);
        }
    } catch (e) {
        showToast(`${t('msg.export_failed', 'Excel export failed:')} ${e}`, "error");
    }
};

window.updatePurchaseDates = function() {
    purchaseStart = document.getElementById('purch-start').value;
    purchaseEnd = document.getElementById('purch-end').value;
    loadPageData('purchases');
};

window.openPurchaseModal = async function() {
    purchCart = [];
    showLoading(true);
    try {
        purchSuppliers = await callBackend('list_suppliers');
        purchProducts = await callBackend('list_products');
    } finally {
        showLoading(false);
    }
    
    if (purchSuppliers.length === 0) {
        showToast("Please register at least one supplier before recording purchase invoices.", "warning");
        navigate('suppliers');
        return;
    }

    const html = `
        <div class="space-y-3.5 text-xs">
            
            <!-- Invoice Details Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 p-3 bg-slate-50 border border-slate-200 rounded-md">
                <div>
                    <label class="form-label" for="pm-date">${t('pur.date', 'Invoice Date')} *</label>
                    <input type="date" id="pm-date" class="form-input text-xs" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                <div>
                    <label class="form-label" for="pm-supplier">${t('pur.supplier', 'Supplier')} *</label>
                    <select id="pm-supplier" class="form-select text-xs" required>
                        <option value="">${t('pur.supplier', 'Select Supplier...')}</option>
                        ${purchSuppliers.map(s => `<option value="${s.id}">${s.name} ${s.phone ? `(${s.phone})` : ''}</option>`).join('')}
                    </select>
                </div>
                <div>
                    <label class="form-label" for="pm-ref">${t('pur.invoice_no', 'Supplier Invoice / Bill #')} *</label>
                    <input type="text" id="pm-ref" class="form-input text-xs" placeholder="e.g. PO-2026-001" required>
                </div>
            </div>
            
            <!-- Add Item Row -->
            <div class="p-3 border border-slate-200 rounded-md bg-white space-y-2.5 shadow-xs">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-700 block">${t('pur.add_line', 'Add Item Line to Invoice')}</span>
                
                <div class="grid grid-cols-12 gap-2 items-end">
                    <div class="col-span-12 sm:col-span-5">
                        <label class="form-label" for="pm-item-prod">${t('col.name', 'Product')} *</label>
                        <select id="pm-item-prod" class="form-select text-xs" onchange="pmProductSelected()">
                            <option value="">${t('prod.filter_search', 'Select Catalog Item...')}</option>
                            ${purchProducts.filter(p => p.is_active).map(p => `
                                <option value="${p.id}" data-med="${p.is_medicine ? '1' : '0'}">
                                    ${escapeHtml(p.name)} ${p.is_medicine ? '[Medicine]' : ''} (${escapeHtml(p.unit_measure || 'units')})
                                </option>
                            `).join('')}
                        </select>
                    </div>

                    <div class="col-span-12 sm:col-span-3">
                        <label class="form-label" for="pm-item-unit">${t('pur.packaging_unit', 'Intake Unit')} *</label>
                        <select id="pm-item-unit" class="form-select text-xs font-semibold">
                            <option value="1">${t('pur.base_unit', 'Base Unit')}</option>
                        </select>
                    </div>

                    <div class="col-span-6 sm:col-span-2">
                        <label class="form-label" for="pm-item-qty">${t('col.qty', 'Quantity')} *</label>
                        <input type="number" id="pm-item-qty" placeholder="Qty" class="form-input text-xs font-mono" min="1">
                    </div>

                    <div class="col-span-6 sm:col-span-2">
                        <label class="form-label" for="pm-item-cost">${t('col.cost', 'Unit Cost (Ks)')} *</label>
                        <input type="number" id="pm-item-cost" placeholder="0" class="form-input text-xs font-mono" min="0">
                    </div>
                </div>

                <!-- Medicine Batch Details -->
                <div id="pm-medicine-fields" class="hidden p-2.5 rounded bg-teal-50 border border-teal-200 space-y-2">
                    <div class="flex items-center gap-1 text-[11px] font-bold text-teal-800">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                        <span>${t('prod.field_is_medicine', 'Medicine Batch & Expiry Date (Required for FEFO tracking)')}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="form-label text-teal-800" for="pm-item-batch">${t('col.batch_no', 'Batch Number')} *</label>
                            <input type="text" id="pm-item-batch" placeholder="e.g. BATCH-2026A" class="form-input text-xs bg-white">
                        </div>
                        <div>
                            <label class="form-label text-teal-800" for="pm-item-expiry">${t('col.expiry_date', 'Expiry Date')} *</label>
                            <input type="date" id="pm-item-expiry" class="form-input text-xs bg-white">
                        </div>
                    </div>
                </div>

                <div class="flex justify-end">
                    <button type="button" class="btn btn-sm btn-secondary text-xs" onclick="pmAddItem(event)">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                        <span>${t('pur.add_line', 'Add Item to Bill')}</span>
                    </button>
                </div>
            </div>
            
            <!-- Items Table in Modal -->
            <div class="border border-slate-200 rounded-md overflow-hidden max-h-48 overflow-y-auto">
                <table class="table w-full text-xs">
                    <thead class="sticky top-0 bg-slate-50">
                        <tr>
                            <th class="px-2.5 py-1.5 text-left font-semibold text-slate-600">${t('col.name', 'Product')}</th>
                            <th class="px-2.5 py-1.5 text-right font-semibold text-slate-600">${t('col.qty', 'Qty')}</th>
                            <th class="px-2.5 py-1.5 text-right font-semibold text-slate-600">${t('col.cost', 'Cost')}</th>
                            <th class="px-2.5 py-1.5 text-left font-semibold text-slate-600">${t('col.batch_no', 'Batch')} / ${t('col.expiry_date', 'Expiry')}</th>
                            <th class="px-2.5 py-1.5 text-right font-semibold text-slate-600">${t('col.total', 'Total')}</th>
                            <th class="px-2.5 py-1.5"></th>
                        </tr>
                    </thead>
                    <tbody id="pm-cart-tbody" class="divide-y divide-slate-100 bg-white">
                        <tr><td colspan="6" class="px-2.5 py-3 text-center text-slate-400">${t('msg.no_data', 'No items added to invoice yet.')}</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- Grand Total Bar -->
            <div class="p-2.5 bg-slate-50 border border-slate-200 rounded-md flex justify-between items-center">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-600">${t('pur.total_amount', 'Total Invoice Amount')}</span>
                <span id="pm-total" class="text-lg font-bold font-mono text-slate-900 tabular-nums">0 Ks</span>
            </div>

        </div>
    `;

    openModal(t('pur.modal_title', "Record Purchase Invoice"), html, async () => {
        const date = document.getElementById('pm-date').value;
        const ref = document.getElementById('pm-ref').value.trim();
        const suppId = document.getElementById('pm-supplier').value;

        if (!date) throw "Invoice date is required.";
        if (!ref) throw "Supplier Invoice / PO reference number is required.";
        if (!suppId) throw "Supplier must be selected.";
        if (purchCart.length === 0) throw "Please add at least one line item to the invoice.";

        const items = purchCart.map(c => ({
            product_id: c.product.id,
            quantity: c.qty,
            unit_cost: c.cost,
            packaging_unit: c.packaging_unit || null,
            packaging_factor: c.packaging_factor || 1,
            batch_number: c.batch || null,
            expiry_date: c.expiry || null
        }));

        await callBackend('create_purchase', ref, parseInt(suppId), date, JSON.stringify(items));
        showToast(`Purchase invoice "${ref}" recorded and inventory received.`);
        loadPageData('purchases');
    }, {
        maxWidth: 'max-w-xl',
        saveText: t('pur.add_button', 'Confirm & Receive Stock')
    });
};

window.pmProductSelected = function() {
    const sel = document.getElementById('pm-item-prod');
    if (!sel) return;
    const opt = sel.options[sel.selectedIndex];
    const isMed = opt && opt.getAttribute('data-med') === '1';
    const medFields = document.getElementById('pm-medicine-fields');
    if (medFields) {
        if (isMed) medFields.classList.remove('hidden');
        else medFields.classList.add('hidden');
    }

    const unitSel = document.getElementById('pm-item-unit');
    if (unitSel) {
        const prodId = parseInt(sel.value || 0);
        const prod = purchProducts.find(p => p.id === prodId);
        if (prod) {
            let opts = `<option value="1" data-unit="${escapeHtml(prod.unit_measure || 'units')}">1 ${escapeHtml(prod.unit_measure || 'unit')} (Base)</option>`;
            (prod.packagings || []).forEach(pkg => {
                opts += `<option value="${pkg.conversion_factor}" data-unit="${escapeHtml(pkg.unit_name)}">1 ${escapeHtml(pkg.unit_name)} [${pkg.conversion_factor} ${escapeHtml(prod.unit_measure)}]</option>`;
            });
            unitSel.innerHTML = opts;
        } else {
            unitSel.innerHTML = `<option value="1">${t('pur.base_unit', 'Base Unit')}</option>`;
        }
    }
};

window.pmAddItem = function(e) {
    if (e) e.preventDefault();
    const pid = document.getElementById('pm-item-prod').value;
    const qty = parseInt(document.getElementById('pm-item-qty').value);
    const cost = parseFloat(document.getElementById('pm-item-cost').value);
    
    if (!pid) {
        showToast("Please select a product from the list.", "warning");
        return;
    }
    if (isNaN(qty) || qty <= 0) {
        showToast("Quantity must be a positive number.", "warning");
        return;
    }
    if (isNaN(cost) || cost < 0) {
        showToast("Unit cost must be a valid positive Kyat amount.", "warning");
        return;
    }

    const prod = purchProducts.find(p => p.id == pid);
    const unitSel = document.getElementById('pm-item-unit');
    const factor = parseInt(unitSel ? unitSel.value : 1) || 1;
    const selectedOpt = unitSel ? unitSel.options[unitSel.selectedIndex] : null;
    const unitName = selectedOpt ? (selectedOpt.getAttribute('data-unit') || prod.unit_measure) : prod.unit_measure;

    let batch = null;
    let expiry = null;
    
    if (prod && prod.is_medicine) {
        batch = document.getElementById('pm-item-batch').value.trim();
        expiry = document.getElementById('pm-item-expiry').value;
        if (!batch) {
            showToast("Batch number is required for medicine products.", "warning");
            return;
        }
        if (!expiry) {
            showToast("Expiry date is required for medicine products.", "warning");
            return;
        }
    }

    purchCart.push({
        product: prod,
        qty: qty,
        cost: cost,
        factor: factor,
        unitName: unitName,
        packaging_unit: factor > 1 ? unitName : null,
        packaging_factor: factor,
        batch: batch,
        expiry: expiry
    });
    
    // reset item inputs
    document.getElementById('pm-item-prod').value = '';
    document.getElementById('pm-item-qty').value = '';
    document.getElementById('pm-item-cost').value = '';
    document.getElementById('pm-item-batch').value = '';
    document.getElementById('pm-item-expiry').value = '';
    document.getElementById('pm-medicine-fields').classList.add('hidden');
    if (unitSel) unitSel.innerHTML = '<option value="1">${t('pur.base_unit', 'Base Unit')}</option>';
    
    pmRenderCart();
};

window.pmRemoveItem = function(idx) {
    purchCart.splice(idx, 1);
    pmRenderCart();
};

function pmRenderCart() {
    const tbody = document.getElementById('pm-cart-tbody');
    let total = 0;
    
    if (purchCart.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="px-2.5 py-3 text-center text-slate-400">${t('pur.empty_items', 'No items added to purchase invoice yet.')}</td></tr>`;
        document.getElementById('pm-total').innerText = '0 Ks';
        return;
    }

    tbody.innerHTML = purchCart.map((c, i) => {
        const lineTotal = c.qty * c.cost;
        total += lineTotal;
        return `
            <tr class="hover:bg-slate-50">
                <td class="px-2.5 py-1.5 font-bold text-slate-900">
                    ${escapeHtml(c.product.name)}
                    ${c.factor > 1 ? `<span class="badge badge-teal text-[10px] ml-1 font-bold">[${escapeHtml(c.unitName)} x${c.factor}]</span>` : `<span class="text-slate-400 text-[10px] ml-1">(${escapeHtml(c.unitName)})</span>`}
                </td>
                <td class="px-2.5 py-1.5 text-right font-mono font-bold">${c.qty} ${escapeHtml(c.unitName)}</td>
                <td class="px-2.5 py-1.5 text-right font-mono">${formatMoney(c.cost)}</td>
                <td class="px-2.5 py-1.5 font-mono text-[10px]">
                    ${c.batch ? `<span class="font-bold text-teal-800">${c.batch}</span> <span class="text-slate-400">(${c.expiry})</span>` : '<span class="text-slate-400">N/A</span>'}
                </td>
                <td class="px-2.5 py-1.5 text-right font-mono font-bold text-slate-900">${formatMoney(lineTotal)}</td>
                <td class="px-2.5 py-1.5 text-right">
                    <button type="button" class="text-slate-400 hover:text-rose-600 transition-colors p-0.5" onclick="pmRemoveItem(${i})" title="Remove item">
                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    document.getElementById('pm-total').innerText = formatMoney(total);
}
