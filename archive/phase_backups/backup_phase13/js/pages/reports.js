let reportStart = '';
let reportEnd = '';
let reportType = 'financial'; 

async function renderReports(container) {
    if (!reportStart) {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        reportStart = d.toISOString().split('T')[0];
        reportEnd = new Date().toISOString().split('T')[0];
    }

    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <div class="flex flex-wrap items-center gap-2">
                <select class="form-select text-xs w-48 font-semibold text-slate-800 py-1 px-2.5" onchange="switchReportType(this.value)">
                    <option value="financial" ${reportType === 'financial' ? 'selected' : ''}>Profit & Loss Statement</option>
                    <option value="product" ${reportType === 'product' ? 'selected' : ''}>Sales by Product</option>
                    <option value="category" ${reportType === 'category' ? 'selected' : ''}>Sales by Category</option>
                    <option value="expenses" ${reportType === 'expenses' ? 'selected' : ''}>Operating Expenses Summary</option>
                </select>

                <div class="flex items-center gap-1.5 text-xs">
                    <input type="date" id="rep-start" class="form-input text-xs w-32 py-1 px-2" value="${reportStart}">
                    <span class="text-slate-400">to</span>
                    <input type="date" id="rep-end" class="form-input text-xs w-32 py-1 px-2" value="${reportEnd}">
                    <button class="btn btn-sm btn-secondary text-xs py-1" onclick="applyReportDates()">Run</button>
                </div>

                <button class="btn btn-sm btn-secondary text-xs py-1" onclick="window.print()" title="Print or save PDF report">
                    <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
                    </svg>
                    Print
                </button>
            </div>
        `;
    }

    showLoading(true);
    try {
        if (reportType === 'financial') {
            await _renderFinancialReport(container);
        } else if (reportType === 'product') {
            await _renderProductReport(container);
        } else if (reportType === 'category') {
            await _renderCategoryReport(container);
        } else if (reportType === 'expenses') {
            await _renderExpensesReport(container);
        }
    } catch(e) {
        showToast(e, "error");
    } finally {
        showLoading(false);
    }
}

async function _renderFinancialReport(container) {
    const salesData = await callBackend('get_sales_summary', reportStart, reportEnd);
    const expData = await callBackend('get_expenses_by_category', reportStart, reportEnd);
    
    let totalExpenses = 0;
    expData.forEach(e => totalExpenses += (e.total_amount || 0));

    const rev = salesData.total_revenue ?? salesData.revenue ?? 0;
    const cogs = salesData.total_cogs ?? salesData.cogs ?? 0;
    const grossProfit = salesData.gross_profit ?? (rev - cogs);
    const netProfit = grossProfit - totalExpenses;
    const grossMargin = rev > 0 ? ((grossProfit / rev) * 100).toFixed(1) : '0.0';
    const netMargin = rev > 0 ? ((netProfit / rev) * 100).toFixed(1) : '0.0';

    container.innerHTML = `
        <div class="space-y-4">
            
            <!-- Official Statement Header -->
            <div class="p-4 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                    <div class="text-[11px] font-bold uppercase tracking-wider text-teal-800">Medisales Pharmacy & Retail</div>
                    <h3 class="text-base font-bold text-slate-900 mt-0.5">Statement of Profit and Loss (Income Statement)</h3>
                    <p class="text-xs text-slate-500 font-mono mt-0.5">Period: ${reportStart} &nbsp;to&nbsp; ${reportEnd}</p>
                </div>
                <div class="text-right">
                    <span class="badge badge-neutral text-xs">Myanmar Retail GAAP</span>
                    <div class="text-[11px] text-slate-400 mt-1">Currency: MMK (Ks)</div>
                </div>
            </div>

            <!-- Two Column Financial Breakdown -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                
                <!-- Trading Account: Sales & Gross Profit -->
                <div class="card flex flex-col justify-between">
                    <div>
                        <div class="card-header bg-slate-50/70">
                            <span class="card-title text-xs">1. Trading Account (Gross Margin)</span>
                            <span class="text-xs font-semibold text-emerald-700 font-mono">${grossMargin}% Margin</span>
                        </div>
                        <div class="p-4 space-y-3 text-xs">
                            <div class="flex justify-between items-center">
                                <span class="text-slate-600">Total Sales Revenue (POS)</span>
                                <span class="font-mono font-bold text-slate-900 text-sm">${formatMoney(rev)}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-600">Less: Cost of Goods Sold (COGS)</span>
                                <span class="font-mono text-slate-700">− ${formatMoney(cogs)}</span>
                            </div>
                        </div>
                    </div>

                    <div class="p-4 pt-3 border-t border-slate-200 bg-slate-50/50 flex justify-between items-center">
                        <div>
                            <span class="font-bold text-slate-900 text-xs block">GROSS PROFIT</span>
                            <span class="text-[11px] text-slate-400">Revenue minus stock purchase cost</span>
                        </div>
                        <span class="font-mono font-black text-base text-teal-800 tabular-nums">${formatMoney(grossProfit)}</span>
                    </div>
                </div>

                <!-- Operating Overheads: Expenses -->
                <div class="card flex flex-col justify-between">
                    <div>
                        <div class="card-header bg-slate-50/70">
                            <span class="card-title text-xs">2. Operating Overheads</span>
                            <span class="text-xs font-semibold text-rose-700 font-mono">${expData.length} Heads</span>
                        </div>
                        <div class="p-4 space-y-2.5 max-h-56 overflow-y-auto text-xs">
                            ${expData.map(e => `
                                <div class="flex justify-between items-center">
                                    <span class="text-slate-600 font-medium">${e.category_name ?? e.category}</span>
                                    <span class="font-mono text-slate-800">${formatMoney(e.total_amount)}</span>
                                </div>
                            `).join('')}
                            ${expData.length === 0 ? '<div class="text-slate-400 py-3 italic text-center">No operating expenses recorded for this period.</div>' : ''}
                        </div>
                    </div>
                    
                    <div class="p-4 pt-3 border-t border-slate-200 bg-slate-50/50 flex justify-between items-center">
                        <span class="font-bold text-slate-900 text-xs">TOTAL OPERATING EXPENSES</span>
                        <span class="font-mono font-bold text-rose-700 text-sm">${formatMoney(totalExpenses)}</span>
                    </div>
                </div>

            </div>

            <!-- Net Operating Profit Statement Card -->
            <div class="p-5 rounded-lg bg-white border-2 ${netProfit >= 0 ? 'border-teal-600' : 'border-rose-400'} flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full ${netProfit >= 0 ? 'bg-teal-600' : 'bg-rose-600'}"></span>
                        <h4 class="text-base font-bold text-slate-900">NET OPERATING PROFIT / (LOSS)</h4>
                    </div>
                    <p class="text-xs text-slate-500 mt-1">
                        Gross Profit (${formatMoney(grossProfit)}) &minus; Operating Expenses (${formatMoney(totalExpenses)})
                    </p>
                    <div class="text-xs font-mono font-semibold ${netProfit >= 0 ? 'text-teal-700' : 'text-rose-700'} mt-1">
                        Net Profit Margin: ${netMargin}%
                    </div>
                </div>
                
                <div class="text-right flex-shrink-0">
                    <div class="text-2xl font-black font-mono ${netProfit >= 0 ? 'text-teal-900' : 'text-rose-700'} tabular-nums border-b-2 border-double ${netProfit >= 0 ? 'border-teal-700' : 'border-rose-600'} pb-0.5">
                        ${formatMoney(netProfit)}
                    </div>
                    <span class="text-[11px] font-semibold text-slate-500 block mt-1">
                        ${netProfit >= 0 ? 'Store Operating Surplus' : 'Store Operating Deficit'}
                    </span>
                </div>
            </div>

        </div>
    `;
}

async function _renderProductReport(container) {
    const data = await callBackend('get_sales_by_product', reportStart, reportEnd);
    
    let totalQty = 0;
    let totalRev = 0;
    let totalCogs = 0;
    let totalGross = 0;
    
    data.forEach(r => {
        totalQty += (r.total_quantity ?? r.quantity_sold ?? 0);
        totalRev += (r.total_revenue ?? r.revenue ?? 0);
        totalCogs += (r.total_cogs ?? r.cogs ?? 0);
        totalGross += (r.gross_profit || 0);
    });

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            <div class="p-3 border-b border-slate-200 bg-white flex justify-between items-center text-xs">
                <span class="font-bold text-slate-800">Product Sales & Profitability Analysis</span>
                <span class="text-slate-500 font-mono">${data.length} Products Sold in Period</span>
            </div>
            
            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-4/12">Product / Medicine Name</th>
                            <th class="th w-2/12 text-right">Units Sold</th>
                            <th class="th w-2/12 text-right">Revenue (Ks)</th>
                            <th class="th w-2/12 text-right">Cost COGS (Ks)</th>
                            <th class="th w-2/12 text-right">Gross Profit (Ks)</th>
                            <th class="th w-1/12 text-right">Margin %</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${data.length === 0 ? '<tr><td colspan="6" class="py-12 text-center text-slate-400 text-xs">No sales recorded for this period.</td></tr>' : ''}
                        ${data.map(r => {
                            const q = r.total_quantity ?? r.quantity_sold ?? 0;
                            const rev = r.total_revenue ?? r.revenue ?? 0;
                            const cogs = r.total_cogs ?? r.cogs ?? 0;
                            const gp = r.gross_profit || 0;
                            const margin = rev > 0 ? ((gp / rev) * 100).toFixed(1) : '0.0';
                            return `
                                <tr class="tr-hover">
                                    <td class="td font-bold text-slate-900 text-xs">${r.product_name}</td>
                                    <td class="td-num">${q}</td>
                                    <td class="td-num font-bold text-slate-900">${formatMoney(rev)}</td>
                                    <td class="td-num text-slate-500">${formatMoney(cogs)}</td>
                                    <td class="td-num font-bold text-teal-800">${formatMoney(gp)}</td>
                                    <td class="td-num text-xs font-semibold ${gp >= 0 ? 'text-emerald-700' : 'text-rose-600'}">${margin}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700">Total Period Summary</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs">${totalQty}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${formatMoney(totalRev)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-600">${formatMoney(totalCogs)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-teal-800">${formatMoney(totalGross)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-emerald-700">${totalRev > 0 ? ((totalGross / totalRev) * 100).toFixed(1) : '0.0'}%</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    `;
}

async function _renderCategoryReport(container) {
    const data = await callBackend('get_sales_by_category', reportStart, reportEnd);
    
    let totalRev = 0;
    let totalCogs = 0;
    let totalGross = 0;

    data.forEach(r => {
        totalRev += (r.total_revenue ?? r.revenue ?? 0);
        totalCogs += (r.total_cogs ?? r.cogs ?? 0);
        totalGross += (r.gross_profit || 0);
    });

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            <div class="p-3 border-b border-slate-200 bg-white flex justify-between items-center text-xs">
                <span class="font-bold text-slate-800">Sales & Margins by Product Category</span>
                <span class="text-slate-500 font-mono">${data.length} Categories</span>
            </div>

            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-4/12">Category Name</th>
                            <th class="th w-2/12 text-right">Revenue (Ks)</th>
                            <th class="th w-2/12 text-right">Cost COGS (Ks)</th>
                            <th class="th w-2/12 text-right">Gross Profit (Ks)</th>
                            <th class="th w-2/12 text-right">Gross Margin %</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${data.length === 0 ? '<tr><td colspan="5" class="py-12 text-center text-slate-400 text-xs">No sales in this period.</td></tr>' : ''}
                        ${data.map(r => {
                            const rev = r.total_revenue ?? r.revenue ?? 0;
                            const cogs = r.total_cogs ?? r.cogs ?? 0;
                            const gp = r.gross_profit || 0;
                            const margin = rev > 0 ? ((gp / rev) * 100).toFixed(1) : '0.0';
                            return `
                                <tr class="tr-hover">
                                    <td class="td font-bold text-slate-900 text-xs">${r.category_name ?? r.category}</td>
                                    <td class="td-num font-bold text-slate-900">${formatMoney(rev)}</td>
                                    <td class="td-num text-slate-500">${formatMoney(cogs)}</td>
                                    <td class="td-num font-bold text-teal-800">${formatMoney(gp)}</td>
                                    <td class="td-num text-xs font-semibold text-emerald-700">${margin}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700">Total All Categories</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-900">${formatMoney(totalRev)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-slate-600">${formatMoney(totalCogs)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-teal-800">${formatMoney(totalGross)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-emerald-700">${totalRev > 0 ? ((totalGross / totalRev) * 100).toFixed(1) : '0.0'}%</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    `;
}

async function _renderExpensesReport(container) {
    const data = await callBackend('get_expenses_by_category', reportStart, reportEnd);
    const total = data.reduce((acc, r) => acc + (r.total_amount || 0), 0);

    container.innerHTML = `
        <div class="card flex flex-col h-full">
            <div class="p-3 border-b border-slate-200 bg-white flex justify-between items-center text-xs">
                <span class="font-bold text-slate-800">Operating Expenses by Expense Head</span>
                <span class="badge badge-danger font-mono font-bold">Total: ${formatMoney(total)}</span>
            </div>

            <div class="flex-1 overflow-auto">
                <table class="table">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th w-5/12">Expense Head / Category</th>
                            <th class="th w-4/12 text-right">Total Amount (Ks)</th>
                            <th class="th w-3/12 text-right">% of Total Overhead Costs</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
                        ${data.length === 0 ? '<tr><td colspan="3" class="py-12 text-center text-slate-400 text-xs">No expenses recorded for this period.</td></tr>' : ''}
                        ${data.map(r => {
                            const pct = total > 0 ? ((r.total_amount / total) * 100).toFixed(1) : '0.0';
                            return `
                                <tr class="tr-hover">
                                    <td class="td font-bold text-slate-900 text-xs">${r.category_name ?? r.category}</td>
                                    <td class="td-num font-bold text-rose-700">${formatMoney(r.total_amount)}</td>
                                    <td class="td-num text-xs text-slate-600">${pct}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                    <tfoot class="bg-slate-50 font-bold border-t-2 border-slate-300">
                        <tr>
                            <td class="px-4 py-2.5 text-xs uppercase text-slate-700">Total Operating Expenses</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs text-rose-700">${formatMoney(total)}</td>
                            <td class="px-4 py-2.5 text-right font-mono text-xs">100.0%</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    `;
}

window.applyReportDates = function() {
    reportStart = document.getElementById('rep-start').value;
    reportEnd = document.getElementById('rep-end').value;
    loadPageData('reports');
};

window.switchReportType = function(type) {
    reportType = type;
    renderReports(document.getElementById('content-area'));
};
