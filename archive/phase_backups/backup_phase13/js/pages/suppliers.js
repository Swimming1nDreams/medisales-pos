let allSuppliers = [];
let supplierSearchTerm = '';

async function renderSuppliers(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-primary text-xs" onclick="openSupplierModal()">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span>Register New Supplier</span>
            </button>
        `;
    }

    showLoading(true);
    let balances = [];
    try {
        allSuppliers = await callBackend('list_suppliers');
        balances = await callBackend('get_supplier_balances');
    } catch(e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }
    
    const balMap = {};
    balances.forEach(b => balMap[b.supplier_id] = b.outstanding_balance);

    const totalOutstanding = balances.reduce((acc, b) => acc + (b.outstanding_balance || 0), 0);
    const withDue = allSuppliers.filter(s => (balMap[s.id] || 0) > 0).length;

    // Filter suppliers
    const q = supplierSearchTerm.toLowerCase().trim();
    const filtered = allSuppliers.filter(s => {
        if (!q) return true;
        const name = (s.name || '').toLowerCase();
        const phone = (s.phone || '').toLowerCase();
        const addr = (s.address || '').toLowerCase();
        return name.includes(q) || phone.includes(q) || addr.includes(q);
    });

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-3 flex-1 min-w-[280px]">
                    <div class="relative w-72">
                        <input type="text" 
                               id="supplier-search"
                               class="form-input text-xs pl-8 pr-3 py-1.5 w-full" 
                               placeholder="Search vendor name, phone, address..."
                               value="${supplierSearchTerm}"
                               oninput="handleSupplierSearch(this.value)">
                        <svg class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>

                    <div class="flex items-center gap-2 text-xs text-slate-500">
                        <span>Showing <strong>${filtered.length}</strong> of ${allSuppliers.length} vendors</span>
                    </div>
                </div>

                <div class="flex items-center gap-2 text-xs">
                    <span class="badge badge-neutral font-mono font-medium">${withDue} Accounts With Due</span>
                    <span class="badge ${totalOutstanding > 0 ? 'badge-warning' : 'badge-success'} font-mono font-bold">
                        Total Payables: ${formatMoney(totalOutstanding)}
                    </span>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-3/12">Supplier / Vendor Name</th>
                            <th class="th w-2/12">Phone Contact</th>
                            <th class="th w-3/12">Office / Warehouse Address</th>
                            <th class="th w-2/12 text-right">Outstanding Balance</th>
                            <th class="th w-1/12 text-center">Status</th>
                            <th class="th w-1/12 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${filtered.length === 0 ? `
                            <tr>
                                <td colspan="6" class="py-12 text-center text-slate-400 text-xs">
                                    ${allSuppliers.length === 0 ? 'No suppliers registered yet. Click "Register New Supplier" to get started.' : 'No suppliers match your search query.'}
                                </td>
                            </tr>
                        ` : ''}
                        ${filtered.map(s => {
                            const bal = balMap[s.id] || 0;
                            return `
                                <tr class="tr-hover ${!s.is_active ? 'opacity-60 bg-slate-50/50' : ''}">
                                    <td class="td">
                                        <div class="font-bold text-slate-900 text-xs">${s.name}</div>
                                        <div class="text-[11px] text-slate-400 font-mono">Vendor ID: #${s.id}</div>
                                    </td>
                                    <td class="td font-mono text-xs text-slate-600">${s.phone || '-'}</td>
                                    <td class="td text-xs text-slate-600">
                                        <div class="truncate max-w-[260px]" title="${s.address || ''}">
                                            ${s.address || '-'}
                                        </div>
                                    </td>
                                    <td class="td-num">
                                        <span class="font-bold ${bal > 0 ? 'text-amber-800' : 'text-slate-700'}">
                                            ${formatMoney(bal)}
                                        </span>
                                    </td>
                                    <td class="td text-center">
                                        <span class="badge ${s.is_active ? 'badge-success' : 'badge-neutral'}">
                                            ${s.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td class="td text-right">
                                        <div class="flex items-center justify-end gap-1.5">
                                            ${bal > 0 ? `
                                                <button class="btn btn-sm btn-primary py-1 px-2 text-xs" onclick="openPaymentModal(${s.id}, '${escapeHtml(s.name)}', ${bal})">
                                                    Settle
                                                </button>
                                            ` : `
                                                <span class="text-[11px] text-emerald-700 font-medium px-2 py-0.5 bg-emerald-50 rounded border border-emerald-200">
                                                    Settled
                                                </span>
                                            `}
                                            <button class="btn btn-sm btn-secondary py-1 px-2 text-xs" onclick="editSupplier(${s.id})">
                                                Edit
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>

            <!-- Footer summary -->
            <div class="p-2.5 px-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex items-center justify-between">
                <div>
                    Suppliers supply wholesale pharmaceuticals and store inventory. Payments are applied in FIFO order to unpaid purchase orders.
                </div>
                <div class="font-mono text-slate-700 font-semibold">
                    ${allSuppliers.length} Registered Accounts
                </div>
            </div>

        </div>
    `;
}

window.handleSupplierSearch = function(val) {
    supplierSearchTerm = val;
    renderSuppliers(document.getElementById('content-area'));
};

window.openSupplierModal = function(s = null) {
    const isEdit = s !== null;
    const title = isEdit ? "Edit Supplier Details" : "Register New Supplier";
    
    const html = `
        <form class="space-y-4" onsubmit="event.preventDefault()">
            <div>
                <label class="form-label" for="s-name">Supplier / Company Name *</label>
                <input type="text" id="s-name" class="form-input text-xs" required placeholder="e.g. AA Medical Products Ltd, Mega Lifesciences" value="${isEdit ? escapeHtml(s.name) : ''}">
                <span class="form-hint">Official trade or distributor name.</span>
            </div>
            <div>
                <label class="form-label" for="s-phone">Contact Phone Number *</label>
                <input type="text" id="s-phone" class="form-input text-xs font-mono" required placeholder="e.g. 09-123456789" value="${isEdit ? (s.phone || '') : ''}">
                <span class="form-hint">Primary number for purchase orders and delivery coordination.</span>
            </div>
            <div>
                <label class="form-label" for="s-address">Office / Warehouse Address</label>
                <textarea id="s-address" class="form-input text-xs h-20" placeholder="e.g. No. 45, Bogyoke Road, Pabedan Township, Yangon">${isEdit ? (s.address || '') : ''}</textarea>
            </div>
            ${isEdit ? `
                <div class="pt-2">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="s-active" class="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-4 w-4" ${s.is_active ? 'checked' : ''}>
                        <span class="text-xs font-semibold text-slate-700">Account is Active for New Purchases</span>
                    </label>
                </div>
            ` : ''}
        </form>
    `;

    openModal(title, html, async () => {
        const name = document.getElementById('s-name').value.trim();
        const phone = document.getElementById('s-phone').value.trim();
        const address = document.getElementById('s-address').value.trim();
        
        if (!name) throw "Supplier name is required.";
        if (!phone) throw "Contact phone number is required.";

        if (isEdit) {
            const active = document.getElementById('s-active').checked;
            await callBackend('update_supplier', s.id, name, phone, address, active);
            showToast(`Supplier "${name}" updated successfully.`);
        } else {
            await callBackend('create_supplier', name, phone, address);
            showToast(`Supplier "${name}" registered successfully.`);
        }
        
        loadPageData('suppliers');
    }, {
        maxWidth: 'max-w-md',
        saveText: isEdit ? 'Update Supplier' : 'Register Supplier'
    });
};

window.editSupplier = function(id) {
    const s = allSuppliers.find(x => x.id === id);
    if (s) openSupplierModal(s);
};

let paymentOutstanding = [];

window.openPaymentModal = async function(supplierId, supplierName, balance) {
    showLoading(true);
    try {
        paymentOutstanding = await callBackend('get_outstanding_purchases', supplierId);
    } catch(e) {
        showToast(e, "error");
        return;
    } finally {
        showLoading(false);
    }

    const html = `
        <div class="space-y-4">
            
            <!-- Balance Banner -->
            <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between">
                <div>
                    <span class="text-[11px] font-bold uppercase tracking-wider text-amber-800 block">Total Balance Due</span>
                    <span class="text-2xl font-black font-mono text-amber-900 tabular-nums">${formatMoney(balance)}</span>
                </div>
                <button type="button" class="btn btn-sm btn-secondary text-xs" onclick="payFillFullBalance(${balance})">
                    Pay Full Balance
                </button>
            </div>
            
            <!-- Payment Form -->
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="pay-date">Payment Date *</label>
                    <input type="date" id="pay-date" class="form-input text-xs" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                <div>
                    <label class="form-label" for="pay-ref">Payment Voucher # *</label>
                    <input type="text" id="pay-ref" class="form-input text-xs" placeholder="e.g. PV-2026-001" required>
                </div>
                <div class="col-span-2">
                    <label class="form-label" for="pay-amount">Amount to Settle (Ks) *</label>
                    <input type="number" id="pay-amount" class="form-input text-sm font-bold font-mono" min="1" max="${balance}" placeholder="0" required oninput="allocatePaymentAuto()">
                    <span class="form-hint">Cannot exceed total outstanding balance (${formatMoney(balance)}).</span>
                </div>
                <div class="col-span-2">
                    <label class="form-label" for="pay-notes">Notes / Payment Method</label>
                    <input type="text" id="pay-notes" class="form-input text-xs" placeholder="e.g. Cash drawer payout, KBZPay, AYA Pay">
                </div>
            </div>

            <!-- Invoice Allocation Table -->
            <div class="space-y-1.5">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-700">Invoice Allocation (First-In, First-Out)</span>
                    <span class="text-[11px] text-slate-500">${paymentOutstanding.length} unpaid invoices</span>
                </div>
                <div class="max-h-40 overflow-auto border border-slate-200 rounded-lg">
                    <table class="min-w-full divide-y divide-slate-200 text-xs">
                        <thead class="bg-slate-50 sticky top-0">
                            <tr>
                                <th class="px-3 py-2 text-left font-semibold text-slate-600">Invoice Ref</th>
                                <th class="px-3 py-2 text-right font-semibold text-slate-600">Balance Owed</th>
                                <th class="px-3 py-2 text-right font-semibold text-teal-800">Allocated Amount</th>
                            </tr>
                        </thead>
                        <tbody id="pay-allocations" class="divide-y divide-slate-100 bg-white">
                            ${paymentOutstanding.map((p, i) => `
                                <tr>
                                    <td class="px-3 py-2 font-mono font-bold text-slate-900">${p.reference}</td>
                                    <td class="px-3 py-2 text-right font-mono text-slate-700">${formatMoney(p.total_amount - p.amount_paid)}</td>
                                    <td class="px-3 py-2 text-right font-mono font-bold text-teal-700" id="alloc-${i}">0 Ks</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    openModal(`Settle Supplier Payment • ${supplierName}`, html, async () => {
        const date = document.getElementById('pay-date').value;
        const ref = document.getElementById('pay-ref').value.trim();
        const amt = parseFloat(document.getElementById('pay-amount').value);
        const notes = document.getElementById('pay-notes').value.trim();

        if (!date) throw "Payment date is required.";
        if (!ref) throw "Payment voucher reference is required.";
        if (isNaN(amt) || amt <= 0) throw "Valid positive payment amount in Kyat is required.";
        if (amt > balance) throw `Payment cannot exceed total outstanding balance of ${formatMoney(balance)}.`;

        let remaining = amt;
        const allocations = [];
        for (let p of paymentOutstanding) {
            if (remaining <= 0) break;
            const owed = p.total_amount - p.amount_paid;
            const toAllocate = Math.min(owed, remaining);
            allocations.push({ purchase_id: p.id, allocated_amount: toAllocate });
            remaining -= toAllocate;
        }

        await callBackend('record_payment', ref, supplierId, date, amt, JSON.stringify(allocations), notes);
        showToast(`Payment of ${formatMoney(amt)} to "${supplierName}" recorded successfully.`);
        loadPageData('suppliers');
    }, {
        maxWidth: 'max-w-lg',
        saveText: 'Confirm Payment Settlement'
    });
};

window.payFillFullBalance = function(bal) {
    const el = document.getElementById('pay-amount');
    if (el) {
        el.value = bal;
        allocatePaymentAuto();
    }
};

window.allocatePaymentAuto = function() {
    let amt = parseFloat(document.getElementById('pay-amount').value) || 0;
    paymentOutstanding.forEach((p, i) => {
        const owed = p.total_amount - p.amount_paid;
        const toAllocate = Math.min(owed, amt);
        const allocEl = document.getElementById(`alloc-${i}`);
        if (allocEl) allocEl.innerText = formatMoney(toAllocate);
        amt -= toAllocate;
        if (amt < 0) amt = 0;
    });
};
