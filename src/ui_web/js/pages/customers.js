let allCustomers = [];
let customerBalancesMap = {};
let customerSearchTerm = '';
let customerFilterDebtOnly = false;

function _renderCustomersTbody() {
    const tbody = document.getElementById('customers-tbody');
    if (!tbody) return;

    let candidates = allCustomers.filter(c => {
        if (customerFilterDebtOnly) {
            const bal = (customerBalancesMap[c.id] ? customerBalancesMap[c.id].outstanding_balance : 0);
            if (bal <= 0) return false;
        }
        return true;
    });

    const filtered = (typeof window.filterAndRankItems === 'function')
        ? window.filterAndRankItems(candidates, customerSearchTerm, (c) => ({
            primary: c.name,
            secondary: [c.phone, c.address, c.notes]
        }))
        : candidates.filter(c => {
            const q = customerSearchTerm.toLowerCase().trim();
            if (!q) return true;
            return (c.name || '').toLowerCase().includes(q) || (c.phone || '').toLowerCase().includes(q);
        });

    const countHeader = document.getElementById('customers-count-header');
    if (countHeader) countHeader.innerHTML = `${t('col.showing_accounts', 'Showing {count} of {total} accounts').replace('{count}', filtered.length).replace('{total}', allCustomers.length)}`;

    if (filtered.length === 0) {
        if (allCustomers.length === 0 && !customerSearchTerm && !customerFilterDebtOnly) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="py-14 px-6 text-center">
                        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-50 text-amber-700 mb-3 border border-amber-100 shadow-sm">
                            <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        </div>
                        <div class="text-sm font-bold text-slate-800">${t('cust.empty_welcome_title', 'Neighborhood Customer Credit Ledger')}</div>
                        <p class="text-xs text-slate-500 max-w-md mx-auto mt-1.5 mb-5 leading-relaxed">
                            ${t('cust.empty_welcome_desc', 'Track credit sales, store accounts, and customer debt settlements for neighborhood regulars.')}
                        </p>
                        <button class="btn btn-primary inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold" onclick="openCustomerModal()">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                            <span>${t('cust.empty_add_first', 'Register First Customer')}</span>
                        </button>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="py-12 text-center text-slate-400 text-xs">
                    ${t('msg.no_data', 'No customers match your search query.')}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(c => {
        const balInfo = customerBalancesMap[c.id] || { total_credit: 0, total_repaid: 0, outstanding_balance: 0 };
        const bal = balInfo.outstanding_balance || 0;
        const highlightedName = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(c.name, customerSearchTerm)
            : escapeHtml(c.name);
        const highlightedPhone = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(c.phone || '-', customerSearchTerm)
            : escapeHtml(c.phone || '-');
        const highlightedAddr = (typeof window.highlightSearchMatch === 'function')
            ? window.highlightSearchMatch(c.address || '-', customerSearchTerm)
            : escapeHtml(c.address || '-');

        return `
            <tr class="tr-hover ${!c.is_active ? 'opacity-60 bg-slate-50/50' : ''}">
                <td class="td">
                    <div class="font-bold text-slate-900 text-xs">${highlightedName}</div>
                    <div class="text-[10px] text-slate-400 font-mono">ID: #CUST-${c.id}</div>
                </td>
                <td class="td font-mono text-xs text-slate-600">${highlightedPhone}</td>
                <td class="td text-xs text-slate-600">
                    <div class="truncate max-w-[220px]" title="${escapeHtml(c.address || '')}">
                        ${highlightedAddr}
                    </div>
                </td>
                <td class="td-num">
                    <span class="badge ${bal > 0 ? 'badge-danger font-black' : 'badge-success font-bold'} text-xs font-mono">
                        ${formatMoney(bal)}
                    </span>
                    <span class="text-[10px] text-slate-400 block font-mono mt-0.5">Repaid: ${formatMoney(balInfo.total_repaid)}</span>
                </td>
                <td class="td text-center">
                    ${bal > 0 ? 
                        `<span class="badge badge-warning text-[10px] font-bold">⚠️ ${t('cust.accounts_due', 'Debt Due')}</span>` : 
                        `<span class="badge badge-success text-[10px] font-bold">✓ ${t('status.completed', 'Clear')}</span>`}
                </td>
                <td class="td text-right">
                    <div class="flex items-center justify-end gap-1">
                        ${bal > 0 ? `
                            <button class="btn btn-sm btn-success py-0.5 px-2.5 text-xs font-bold shadow-xs" onclick="openCustomerPaymentModal(${c.id}, '${escapeHtml(c.name)}', ${bal})">
                                ${t('cust.btn_repay', 'Repay')}
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-secondary py-0.5 px-2 text-xs" onclick="openCustomerStatementModal(${c.id})" title="View Ledger Statement">
                            <svg class="w-3 h-3 text-slate-500 inline mr-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            ${t('cust.btn_statement', 'History')}
                        </button>
                        <button class="btn btn-sm btn-secondary py-0.5 px-1.5 text-xs" onclick="editCustomer(${c.id})">
                            ${t('btn.edit', 'Edit')}
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function renderCustomers(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="flex items-center gap-2">
                <button class="btn btn-primary text-xs bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-bold border-amber-600 shadow-sm" onclick="openCustomerModal()">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>${t('cust.add_button', 'Register New Customer')}</span>
                </button>
            </div>
        `;
    }

    showLoading(true);
    let balances = [];
    try {
        allCustomers = await callBackend('list_customers');
        balances = await callBackend('get_customer_balances');
    } catch(e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }

    customerBalancesMap = {};
    balances.forEach(b => {
        customerBalancesMap[b.customer_id] = b;
    });

    const totalReceivables = balances.reduce((acc, b) => acc + (b.outstanding_balance > 0 ? b.outstanding_balance : 0), 0);
    const withDueCount = balances.filter(b => b.outstanding_balance > 0).length;

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-3 flex-1 min-w-[280px]">
                    <div class="relative w-72">
                        <input type="text" 
                               id="customer-search"
                               class="form-input text-xs pl-8 pr-3 py-1.5 w-full" 
                               placeholder="${t('cust.search_placeholder', 'Search customer name, phone, address...')}"
                               value="${escapeHtml(customerSearchTerm)}"
                               oninput="handleCustomerSearch(this.value)">
                        <svg class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>

                    <label class="flex items-center gap-1.5 cursor-pointer text-xs font-semibold text-slate-700 select-none">
                        <input type="checkbox" id="customer-debt-only-check" class="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-3.5 w-3.5" ${customerFilterDebtOnly ? 'checked' : ''} onchange="toggleCustomerDebtFilter(this.checked)">
                        <span>${t('cust.filter_debt_only', 'Customers with Due Only')}</span>
                    </label>

                    <div id="customers-count-header" class="text-xs text-slate-500 font-mono">
                        ${t('col.showing_accounts', 'Showing {count} of {total} accounts').replace('{count}', allCustomers.length).replace('{total}', allCustomers.length)}
                    </div>
                </div>

                <div class="flex items-center gap-2 text-xs">
                    <span class="badge badge-neutral font-mono font-medium">${withDueCount} ${t('cust.accounts_due', 'Accounts in Debt')}</span>
                    <span class="badge ${totalReceivables > 0 ? 'badge-danger' : 'badge-success'} font-mono font-bold">
                        ${t('cust.total_receivables', 'Total Customer Debt')}: ${formatMoney(totalReceivables)}
                    </span>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-3/12">${t('cust.field_name', 'Customer / Patient Name')}</th>
                            <th class="th w-2/12">${t('cust.field_phone', 'Phone Contact')}</th>
                            <th class="th w-3/12">${t('cust.field_address', 'Address / Notes')}</th>
                            <th class="th w-2/12 text-right">${t('cust.col_debt', 'Outstanding Debt (Ks)')}</th>
                            <th class="th w-1/12 text-center">${t('col.status', 'Status')}</th>
                            <th class="th w-1/12 text-right">${t('col.actions', 'Actions')}</th>
                        </tr>
                    </thead>
                    <tbody id="customers-tbody" class="divide-y divide-slate-100 bg-white">
                        <!-- Rendered by _renderCustomersTbody -->
                    </tbody>
                </table>
            </div>

            <!-- Footer summary -->
            <div class="p-2.5 px-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex items-center justify-between">
                <div>
                    ${t('cust.ledger_info', 'Neighborhood Customer Ledger tracks credit sales and debt settlements. When recording POS sales, select Credit Sale to add to customer account.')}
                </div>
                <div class="font-mono text-slate-700 font-semibold">
                    ${allCustomers.length} ${t('status.normal', 'Accounts')}
                </div>
            </div>
        </div>
    `;

    _renderCustomersTbody();
}

window.handleCustomerSearch = function(val) {
    customerSearchTerm = val;
    const tbody = document.getElementById('customers-tbody');
    if (tbody) {
        _renderCustomersTbody();
        return;
    }
    renderCustomers(document.getElementById('content-area'));
};

window.toggleCustomerDebtFilter = function(checked) {
    customerFilterDebtOnly = checked;
    const tbody = document.getElementById('customers-tbody');
    if (tbody) {
        _renderCustomersTbody();
        return;
    }
    renderCustomers(document.getElementById('content-area'));
};

window.openCustomerModal = function(c = null) {
    const isEdit = c !== null;
    const title = isEdit ? t('cust.modal_edit_title', "Edit Customer Details") : t('cust.modal_add_title', "Register New Customer");
    
    const html = `
        <form id="customer-form" class="space-y-3 text-xs" onsubmit="event.preventDefault()">
            <div>
                <label class="form-label" for="cust-name">${t('cust.field_name', 'Customer Full Name / Nickname')} *</label>
                <input type="text" id="cust-name" class="form-input text-xs" required placeholder="e.g. ဦးသန်းနိုင်, ဒေါ်လှလှ (မနက်ပိုင်းဖောက်သည်)" value="${isEdit ? escapeHtml(c.name) : ''}">
                <span class="form-hint">${t('cust.help_desc', 'Name of neighborhood neighbor or regular patient.')}</span>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="cust-phone">${t('cust.field_phone', 'Phone Number')}</label>
                    <input type="text" id="cust-phone" class="form-input text-xs font-mono" placeholder="09xxxxxxxxx" value="${isEdit ? escapeHtml(c.phone || '') : ''}">
                </div>
                <div>
                    <label class="form-label" for="cust-address">${t('cust.field_address', 'Address / Street')}</label>
                    <input type="text" id="cust-address" class="form-input text-xs" placeholder="e.g. လမ်း ၅၀၊ အမှတ် ၄" value="${isEdit ? escapeHtml(c.address || '') : ''}">
                </div>
            </div>

            <div>
                <label class="form-label" for="cust-notes">${t('cust.field_notes', 'Notes / Chronic Medication History')}</label>
                <textarea id="cust-notes" class="form-textarea text-xs h-16" placeholder="e.g. သွေးတိုး၊ ဆီးချို ပုံမှန်ဆေးဝယ်ယူသူ">${isEdit ? escapeHtml(c.notes || '') : ''}</textarea>
            </div>

            ${isEdit ? `
                <div class="pt-2 border-t border-slate-100 flex items-center gap-2">
                    <input type="checkbox" id="cust-active" class="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-4 w-4" ${c.is_active ? 'checked' : ''}>
                    <label for="cust-active" class="font-medium text-slate-700 text-xs">${t('cust.status_active', 'Customer Account Active')}</label>
                </div>
            ` : ''}
        </form>
    `;

    openModal(title, html, async () => {
        const name = document.getElementById('cust-name').value.trim();
        const phone = document.getElementById('cust-phone').value.trim();
        const address = document.getElementById('cust-address').value.trim();
        const notes = document.getElementById('cust-notes').value.trim();

        if (!name) throw new Error("Customer name is required.");

        if (isEdit) {
            const isActive = document.getElementById('cust-active').checked;
            await callBackend('update_customer', c.id, name, phone, address, notes, isActive);
            showToast(t('cust.msg_updated', 'Customer profile updated successfully!'));
        } else {
            await callBackend('create_customer', name, phone, address, notes);
            showToast(t('cust.msg_registered', 'New customer registered successfully!'));
        }
        await renderCustomers(document.getElementById('content-area'));
    });
};

window.editCustomer = function(id) {
    const cust = allCustomers.find(c => c.id === id);
    if (cust) openCustomerModal(cust);
};

window.openCustomerPaymentModal = function(id, name, balance) {
    const title = `${t('cust.modal_repay_title', 'Record Debt Settlement')}: ${name}`;
    const subtitle = `Current Outstanding Debt: ${formatMoney(balance)}`;

    const html = `
        <div class="space-y-3.5 text-xs">
            <div class="p-3 bg-rose-50 border border-rose-200 rounded-md flex justify-between items-center">
                <span class="font-semibold text-rose-900">${t('cust.outstanding_debt', 'Customer Owed Balance:')}</span>
                <span class="font-mono font-bold text-base text-rose-800">${formatMoney(balance)}</span>
            </div>

            <div>
                <label class="form-label" for="repay-amount">${t('cust.repay_amount', 'Repayment Cash Amount (Kyat)')} *</label>
                <input type="number" id="repay-amount" class="form-input text-sm font-bold font-mono text-slate-900 py-2" placeholder="0" min="1" max="${balance}" value="${balance}" autofocus>
                
                <div class="flex gap-1.5 mt-2 overflow-x-auto pb-0.5">
                    <button type="button" class="btn btn-sm btn-subtle text-xs" onclick="document.getElementById('repay-amount').value = ${balance}">${t('cust.full_repay', 'Full Repayment')}</button>
                    ${balance > 5000 ? `<button type="button" class="btn btn-sm btn-subtle text-xs font-mono" onclick="document.getElementById('repay-amount').value = 5000">5,000 Ks</button>` : ''}
                    ${balance > 10000 ? `<button type="button" class="btn btn-sm btn-subtle text-xs font-mono" onclick="document.getElementById('repay-amount').value = 10000">10,000 Ks</button>` : ''}
                    ${balance > 20000 ? `<button type="button" class="btn btn-sm btn-subtle text-xs font-mono" onclick="document.getElementById('repay-amount').value = 20000">20,000 Ks</button>` : ''}
                </div>
            </div>

            <div>
                <label class="form-label" for="repay-notes">${t('cust.field_notes', 'Payment Notes / Receiver')}</label>
                <input type="text" id="repay-notes" class="form-input text-xs" placeholder="e.g. ဆိုင်ရှင်ကိုယ်တိုင် လက်ခံရရှိသည်">
            </div>
        </div>
    `;

    openModal(title, html, async () => {
        const amtInput = document.getElementById('repay-amount');
        const notesInput = document.getElementById('repay-notes');
        const amount = parseInt(amtInput.value) || 0;
        const notes = notesInput ? notesInput.value.trim() : '';

        if (amount <= 0) throw new Error("Repayment amount must be greater than zero.");
        if (amount > balance) throw new Error(`Repayment (${formatMoney(amount)}) cannot exceed outstanding debt (${formatMoney(balance)}).`);

        const res = await callBackend('record_customer_payment', id, amount, notes);
        showToast(`${t('cust.msg_repay_success', 'Settlement recorded!')} Ref: ${res.reference}`);
        await renderCustomers(document.getElementById('content-area'));
    }, {
        subtitle: subtitle,
        saveText: t('cust.btn_confirm_repay', 'Confirm Settlement'),
        saveBtnClass: 'btn-primary'
    });
};

window.openCustomerStatementModal = async function(id) {
    showLoading(true);
    let stmt = null;
    try {
        stmt = await callBackend('get_customer_statement', id);
    } catch(e) {
        showToast(e, "error");
        return;
    } finally {
        showLoading(false);
    }

    if (!stmt) return;
    const c = stmt.customer;

    const html = `
        <div class="space-y-4 text-xs">
            <!-- Customer Summary Card -->
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-md grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                <div>
                    <span class="text-slate-400 block text-[10px]">Customer:</span>
                    <span class="font-bold text-slate-800">${escapeHtml(c.name)}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Total Credit Purchases:</span>
                    <span class="font-mono font-bold text-slate-800">${formatMoney(stmt.total_credit)}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Total Repaid:</span>
                    <span class="font-mono font-bold text-emerald-700">${formatMoney(stmt.total_repaid)}</span>
                </div>
                <div class="col-span-full pt-1.5 border-t border-slate-200 flex justify-between items-center">
                    <span class="font-semibold text-slate-700">Remaining Outstanding Debt:</span>
                    <span class="font-mono font-black text-sm ${stmt.outstanding_balance > 0 ? 'text-rose-700' : 'text-emerald-700'}">
                        ${formatMoney(stmt.outstanding_balance)}
                    </span>
                </div>
            </div>

            <!-- Statement Table -->
            <div class="max-h-72 overflow-y-auto border border-slate-200 rounded">
                <table class="table w-full text-xs">
                    <thead class="sticky top-0 bg-slate-100 z-10">
                        <tr>
                            <th class="th">Date & Ref</th>
                            <th class="th">${t('col.description', 'Description')}</th>
                            <th class="th text-right text-rose-700">Credit (+)</th>
                            <th class="th text-right text-emerald-700">Repaid (-)</th>
                            <th class="th text-right">${t('col.balance', 'Balance')}</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${stmt.entries.length === 0 ? `
                            <tr><td colspan="5" class="py-8 text-center text-slate-400">${t('cust.no_transactions', 'No transactions recorded for this customer.')}</td></tr>
                        ` : stmt.entries.map(e => `
                            <tr class="tr-hover">
                                <td class="td whitespace-nowrap">
                                    <span class="font-mono font-medium">${e.reference}</span>
                                    <span class="text-[10px] text-slate-400 block">${e.date_time}</span>
                                </td>
                                <td class="td">
                                    <div class="font-medium text-slate-800">${e.description}</div>
                                    ${e.notes ? `<div class="text-[10px] text-slate-400 italic">${escapeHtml(e.notes)}</div>` : ''}
                                </td>
                                <td class="td-num font-mono text-rose-700 font-semibold">
                                    ${e.debit > 0 ? '+' + formatMoney(e.debit) : '-'}
                                </td>
                                <td class="td-num font-mono text-emerald-700 font-semibold">
                                    ${e.credit > 0 ? '-' + formatMoney(e.credit) : '-'}
                                </td>
                                <td class="td-num font-mono font-bold text-slate-900">
                                    ${formatMoney(e.balance)}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    openModal(
        `${t('cust.modal_statement_title', 'Customer Ledger Statement')}: ${c.name}`, 
        html, 
        null, 
        { maxWidth: 'max-w-2xl', cancelText: t('btn.close', 'Close') }
    );
};
