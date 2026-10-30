let expenseStart = '';
let expenseEnd = '';
let expenseCategoryFilter = 'all';

async function renderExpenses(container) {
    if (!expenseStart) {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        expenseStart = d.toISOString().split('T')[0];
        expenseEnd = new Date().toISOString().split('T')[0];
    }

    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-primary text-xs" onclick="openExpenseModal()">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span>Record Expense</span>
            </button>
        `;
    }

    showLoading(true);
    let expenses = [];
    try {
        expenses = await callBackend('get_expenses', expenseStart, expenseEnd);
    } catch (e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }
    
    let totalActive = 0;
    const catMap = {};
    expenses.forEach(e => {
        if (e.status === 'Completed') {
            totalActive += e.amount;
            catMap[e.category] = (catMap[e.category] || 0) + e.amount;
        }
    });

    const categories = Object.keys(catMap);
    let filtered = expenses;
    if (expenseCategoryFilter !== 'all') {
        filtered = filtered.filter(e => e.category === expenseCategoryFilter);
    }

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            
            <!-- Toolbar -->
            <div class="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-3">
                <div class="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
                    <div class="flex items-center gap-2 text-xs">
                        <span class="font-medium text-slate-600">Period:</span>
                        <input type="date" id="exp-start" class="form-input text-xs w-32 py-1 px-2" value="${expenseStart}">
                        <span class="text-slate-400">to</span>
                        <input type="date" id="exp-end" class="form-input text-xs w-32 py-1 px-2" value="${expenseEnd}">
                        <button class="btn btn-sm btn-secondary text-xs py-1" onclick="updateExpenseDates()">Apply</button>
                    </div>

                    ${categories.length > 0 ? `
                        <div class="flex items-center gap-1.5 text-xs">
                            <span class="text-slate-400">|</span>
                            <select class="form-select text-xs py-1 px-2.5 min-w-[160px]" onchange="expenseFilterCategory(this.value)">
                                <option value="all" ${expenseCategoryFilter === 'all' ? 'selected' : ''}>All Categories (${categories.length})</option>
                                ${categories.map(c => `<option value="${c}" ${expenseCategoryFilter === c ? 'selected' : ''}>${c} (${formatMoney(catMap[c])})</option>`).join('')}
                            </select>
                        </div>
                    ` : ''}
                </div>

                <div class="flex items-center gap-2 text-xs">
                    <span class="badge badge-neutral font-mono font-medium">${expenses.length} Records</span>
                    <span class="badge badge-danger font-mono font-bold">
                        Total Active: ${formatMoney(totalActive)}
                    </span>
                </div>
            </div>

            <!-- Table -->
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-2/12">Expense Date</th>
                            <th class="th w-2/12">Category / Head</th>
                            <th class="th w-4/12">Description / Purpose</th>
                            <th class="th w-2/12 text-right">Amount (Ks)</th>
                            <th class="th w-1/12 text-center">Audit Status</th>
                            <th class="th w-1/12 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${filtered.length === 0 ? `
                            <tr>
                                <td colspan="6" class="py-12 text-center text-slate-400 text-xs">
                                    No operating expenses recorded for the selected period.
                                </td>
                            </tr>
                        ` : ''}
                        ${filtered.map(e => {
                            const isVoid = e.status !== 'Completed';
                            return `
                                <tr class="tr-hover ${isVoid ? 'opacity-50 bg-slate-50/60' : ''}">
                                    <td class="td text-xs font-mono text-slate-600">${e.date}</td>
                                    <td class="td font-bold text-slate-900 text-xs">${e.category}</td>
                                    <td class="td text-xs text-slate-600">
                                        <div class="max-w-[340px] truncate" title="${escapeHtml(e.description || '')}">
                                            ${e.description ? escapeHtml(e.description) : '-'}
                                        </div>
                                    </td>
                                    <td class="td-num font-bold ${isVoid ? 'text-slate-400 line-through' : 'text-rose-700'}">
                                        ${formatMoney(e.amount)}
                                    </td>
                                    <td class="td text-center">
                                        <span class="badge ${isVoid ? 'badge-danger' : 'badge-success'}">
                                            ${e.status}
                                        </span>
                                    </td>
                                    <td class="td text-right">
                                        ${!isVoid ? `
                                            <button class="btn btn-sm btn-danger py-1 px-2 text-xs" onclick="voidExpense(${e.id}, '${escapeHtml(e.category)}', ${e.amount})">
                                                Void
                                            </button>
                                        ` : '<span class="text-[11px] text-slate-400 italic">Voided</span>'}
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
                    Operating expenses are deducted directly from Gross Profit to calculate Net Operating Profit in Financial Reports.
                </div>
                <div class="font-mono text-slate-700 font-semibold">
                    Net Expense: ${formatMoney(totalActive)}
                </div>
            </div>

        </div>
    `;
}

window.updateExpenseDates = function() {
    expenseStart = document.getElementById('exp-start').value;
    expenseEnd = document.getElementById('exp-end').value;
    loadPageData('expenses');
};

window.expenseFilterCategory = function(cat) {
    expenseCategoryFilter = cat;
    renderExpenses(document.getElementById('content-area'));
};

window.openExpenseModal = function() {
    const html = `
        <form class="space-y-4" onsubmit="event.preventDefault()">
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="form-label" for="em-date">Expense Date *</label>
                    <input type="date" id="em-date" class="form-input text-xs" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                <div>
                    <label class="form-label" for="em-cat">Expense Category *</label>
                    <input type="text" id="em-cat" class="form-input text-xs" placeholder="Select or type..." required list="exp-cat-list">
                    <datalist id="exp-cat-list">
                        <option value="Generator Fuel / Diesel">
                        <option value="Electricity & Utilities">
                        <option value="Staff Refreshment & Food">
                        <option value="Staff Salaries & Wages">
                        <option value="Packaging & Bags">
                        <option value="Store Maintenance">
                        <option value="Shop Rent">
                        <option value="Transportation / Delivery">
                        <option value="Municipal & Licenses">
                        <option value="Printing & Stationery">
                    </datalist>
                </div>
            </div>

            <div>
                <label class="form-label" for="em-amount">Amount in Kyat (Ks) *</label>
                <input type="number" id="em-amount" class="form-input text-base font-bold font-mono" min="1" placeholder="0" required>
                <span class="form-hint">Must be a positive integer Kyat amount paid from shop funds.</span>
            </div>

            <div>
                <label class="form-label" for="em-desc">Description / Purpose</label>
                <input type="text" id="em-desc" class="form-input text-xs" placeholder="e.g. 10 gallons diesel for generator blackout">
            </div>
        </form>
    `;

    openModal("Record Operating Expense", html, async () => {
        const date = document.getElementById('em-date').value;
        const cat = document.getElementById('em-cat').value.trim();
        const amt = parseFloat(document.getElementById('em-amount').value);
        const desc = document.getElementById('em-desc').value.trim();

        if (!date) throw "Expense date is required.";
        if (!cat) throw "Category is required.";
        if (isNaN(amt) || amt <= 0) throw "Amount must be a positive Kyat value.";

        await callBackend('record_expense', date, cat, amt, desc);
        showToast(`Operating expense of ${formatMoney(amt)} recorded.`);
        loadPageData('expenses');
    }, {
        maxWidth: 'max-w-md',
        saveText: 'Save Expense'
    });
};

window.voidExpense = function(id, catName, amount) {
    const html = `
        <div class="space-y-3 text-slate-700">
            <div class="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-800">
                Are you sure you want to void this <strong>${catName}</strong> expense of <strong>${formatMoney(amount)}</strong>? This will remove it from operating overhead calculations while keeping immutable audit history.
            </div>
            <div>
                <label class="form-label" for="void-reason">Reason for Voiding *</label>
                <input type="text" id="void-reason" class="form-input text-xs" required placeholder="e.g. Duplicate voucher entry, wrong amount recorded">
            </div>
        </div>
    `;

    openModal("Void Operating Expense", html, async () => {
        const reason = document.getElementById('void-reason').value.trim();
        if (!reason) throw "A void reason is required.";
        await callBackend('void_expense', id, reason);
        showToast("Expense record successfully voided.");
        loadPageData('expenses');
    }, {
        maxWidth: 'max-w-md',
        saveText: 'Confirm Void',
        saveBtnClass: 'btn-danger'
    });
};
