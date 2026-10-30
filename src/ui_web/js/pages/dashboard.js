async function renderDashboard(container) {
    const data = await callBackend('get_dashboard_summary');
    
    let recentSales = [];
    let lowStockItems = [];
    try {
        const salesList = await callBackend('get_sales', '', '');
        recentSales = (salesList || []).slice(0, 5);
    } catch (e) {
        console.error('Failed to load recent sales for dashboard:', e);
    }

    try {
        const stockList = await callBackend('get_current_stock');
        lowStockItems = (stockList || []).filter(s => s.current_stock <= (s.min_stock_level || 5)).slice(0, 5);
    } catch (e) {
        console.error('Failed to load stock list for dashboard:', e);
    }
    
    const revenue = Number(data.total_sales_revenue) || 0;
    const cogs = Number(data.cost_of_goods_sold) || 0;
    const grossProfit = Number(data.gross_profit) || 0;
    const expenses = Number(data.operating_expenses) || 0;
    const netProfit = Number(data.net_operating_profit) || 0;
    const salesCount = Number(data.number_of_completed_sales) || 0;
    const invValue = Number(data.total_inventory_value) || 0;
    const supplierDue = Number(data.total_outstanding_supplier_balances) || 0;
    const activeProducts = Number(data.active_products_count) || 0;
    const lowStockCount = Number(data.low_stock_products_count) || 0;
    const expiredCount = Number(data.medicine_expired_products_count) || 0;
    const expiringSoonCount = Number(data.medicine_expiring_soon_products_count) || 0;
    const marginPct = revenue > 0 ? ((grossProfit / revenue) * 100).toFixed(1) : '0.0';

    // Set page header actions
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-primary" onclick="navigate('sales')">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                <span>${t('dash.quick_pos', 'New Sale (POS)')}</span>
            </button>
            <button class="btn btn-secondary" onclick="navigate('purchases')">
                <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span>${t('pur.add_button', 'Receive Purchase')}</span>
            </button>
            <button class="btn btn-secondary" onclick="navigate('expenses')">
                <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                <span>${t('exp.add_button', 'Record Expense')}</span>
            </button>
        `;
    }

    container.innerHTML = `
        <div class="space-y-4">
            
            <!-- Section 1: Today's Financial Overview -->
            <div>
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-700">${t('rep.tab_pnl', "Today's Financial Performance")}</h3>
                        <span class="text-[11px] text-slate-400 font-mono">(${data.date || new Date().toISOString().split('T')[0]})</span>
                    </div>
                    <span class="text-[11px] text-slate-500 font-medium">${t('set.concurrency', 'Automatic Real-Time Reconciliation')}</span>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    
                    <!-- Today's Revenue -->
                    <div class="kpi-card">
                        <div class="flex items-center justify-between">
                            <span class="kpi-title">${t('dash.revenue_today', 'Sales Revenue')}</span>
                            <span class="badge badge-success text-[10px]">${salesCount} ${t('sales.cart_items', 'sales')}</span>
                        </div>
                        <div class="kpi-value text-slate-900">${formatMoney(revenue)}</div>
                        <div class="kpi-sub">
                            <span>${t('rep.kpi_cogs', 'Cost of Goods')}: ${formatMoney(cogs)}</span>
                        </div>
                    </div>

                    <!-- Gross Profit -->
                    <div class="kpi-card">
                        <div class="flex items-center justify-between">
                            <span class="kpi-title">${t('dash.gross_profit_today', 'Gross Profit')}</span>
                            <span class="badge badge-teal text-[10px]">${marginPct}%</span>
                        </div>
                        <div class="kpi-value text-teal-800">${formatMoney(grossProfit)}</div>
                        <div class="kpi-sub">
                            <span>${t('rep.kpi_gross_profit', 'Revenue minus COGS')}</span>
                        </div>
                    </div>

                    <!-- Operating Expenses -->
                    <div class="kpi-card">
                        <div class="flex items-center justify-between">
                            <span class="kpi-title">${t('nav.expenses', 'Operating Expenses')}</span>
                            <span class="badge ${expenses > 0 ? 'badge-warning' : 'badge-neutral'} text-[10px]">${t('rep.date_today', 'Today')}</span>
                        </div>
                        <div class="kpi-value text-slate-800">${formatMoney(expenses)}</div>
                        <div class="kpi-sub">
                            <span>${t('exp.notice', 'Utilities, salaries & rent')}</span>
                        </div>
                    </div>

                    <!-- Net Operating Profit -->
                    <div class="kpi-card ${netProfit < 0 ? 'bg-rose-50/50 border-rose-300' : 'bg-emerald-50/50 border-emerald-300'}">
                        <div class="flex items-center justify-between">
                            <span class="kpi-title ${netProfit < 0 ? 'text-rose-900 font-bold' : 'text-emerald-900 font-bold'}">${t('rep.kpi_net_profit', 'Net Operating Profit')}</span>
                            <span class="badge ${netProfit >= 0 ? 'badge-success' : 'badge-danger'} text-[10px] font-bold">${netProfit >= 0 ? t('set.recon_surplus', 'Surplus') : t('set.recon_shortage', 'Deficit')}</span>
                        </div>
                        <div class="kpi-value ${netProfit >= 0 ? 'text-emerald-800' : 'text-rose-700'}">${formatMoney(netProfit)}</div>
                        <div class="kpi-sub">
                            <span>${t('rep.kpi_net_profit', 'Gross profit minus expenses')}</span>
                        </div>
                    </div>

                </div>
            </div>

            <!-- Section 2: Store Assets & Balances -->
            <div>
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">${t('nav.group.finance', 'Store Balances & Working Capital')}</h3>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    
                    <div class="card p-3.5 flex items-center justify-between">
                        <div>
                            <span class="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">${t('dash.inventory_valuation', 'Total Inventory Valuation')}</span>
                            <div class="text-lg font-bold font-mono text-slate-900 mt-0.5">${formatMoney(invValue)}</div>
                            <span class="text-[11px] text-slate-500 mt-0.5 block">FEFO (Meds) & WAC (General)</span>
                        </div>
                        <button class="btn btn-sm btn-secondary text-slate-700" onclick="navigate('inventory')">${t('dash.view_inventory', 'View Stock')}</button>
                    </div>

                    <div class="card p-3.5 flex items-center justify-between">
                        <div>
                            <span class="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">${t('pur.outstanding', 'Supplier Payables')}</span>
                            <div class="text-lg font-bold font-mono ${supplierDue > 0 ? 'text-amber-800' : 'text-slate-900'} mt-0.5">${formatMoney(supplierDue)}</div>
                            <span class="text-[11px] text-slate-500 mt-0.5 block">${t('nav.suppliers', 'Pending vendor settlement')}</span>
                        </div>
                        <button class="btn btn-sm btn-secondary text-slate-700" onclick="navigate('suppliers')">${t('nav.suppliers', 'Suppliers')}</button>
                    </div>

                    <div class="card p-3.5 flex items-center justify-between">
                        <div>
                            <span class="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">${t('inv.total_skus', 'Cataloged Inventory')}</span>
                            <div class="text-lg font-bold font-mono text-slate-900 mt-0.5">${formatNumber(activeProducts)} ${t('status.active', 'Active Items')}</div>
                            <span class="text-[11px] text-slate-500 mt-0.5 block">${t('prod.type_all', 'Medicines & general products')}</span>
                        </div>
                        <button class="btn btn-sm btn-secondary text-slate-700" onclick="navigate('products')">${t('nav.products', 'Products')}</button>
                    </div>

                </div>
            </div>

            <!-- Section 3: Safety Monitors (FEFO & Reorder Alerts) -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                
                <!-- Low Stock Alert Box -->
                <div class="card p-3.5 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0 ${lowStockCount > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        </div>
                        <div>
                            <h4 class="text-xs font-bold text-slate-900">${t('dash.low_stock_alerts', 'Low Stock Reorder Alerts')}</h4>
                            <p class="text-[11px] text-slate-500 mt-0.5">
                                ${lowStockCount > 0 ? `<span class="font-semibold text-amber-800">${lowStockCount} items</span> ${t('status.low_stock', 'below reorder alert level')}` : t('dash.no_low_stock', 'All inventory levels are currently sufficient')}
                            </p>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-secondary" onclick="navigate('inventory')">${t('dash.view_inventory', 'Check Stock')}</button>
                </div>

                <!-- Medicine Expiry Protection Box -->
                <div class="card p-3.5 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0 ${(expiredCount + expiringSoonCount) > 0 ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-600'}">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                        </div>
                        <div>
                            <h4 class="text-xs font-bold text-slate-900">${t('inv.tab_batches', 'FEFO Expiry Tracking')}</h4>
                            <p class="text-[11px] text-slate-500 mt-0.5">
                                ${expiredCount > 0 ? `<span class="font-bold text-rose-700">${expiredCount} ${t('status.expired', 'expired')}</span> • ` : ''}
                                ${expiringSoonCount > 0 ? `<span class="font-semibold text-amber-700">${expiringSoonCount} ${t('status.expiring_soon', 'expiring within 90 days')}</span>` : '0 batches expiring soon'}
                            </p>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-secondary" onclick="navigate('inventory')">${t('dash.view_inventory', 'Review Batches')}</button>
                </div>

            </div>

            <!-- Section 4: Operational Register & Action Center -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
                
                <!-- Left: Recent Sales Register (7 cols) -->
                <div class="lg:col-span-7 card flex flex-col">
                    <div class="p-3 border-b border-slate-200 bg-white flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="font-bold text-xs uppercase tracking-wider text-slate-800">${t('dash.recent_sales', 'Recent Sales Register')}</span>
                            <span class="badge badge-neutral text-[10px]">${recentSales.length}</span>
                        </div>
                        <button class="btn btn-sm btn-secondary text-xs" onclick="navigate('sales')">${t('dash.view_all_sales', 'Open Register &rarr;')}</button>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="table w-full">
                            <thead>
                                <tr>
                                    <th class="th">${t('col.receipt', 'Receipt #')}</th>
                                    <th class="th">${t('col.date', 'Time')}</th>
                                    <th class="th text-center">${t('col.qty', 'Items')}</th>
                                    <th class="th text-right">${t('col.total', 'Amount (Ks)')}</th>
                                    <th class="th text-center">${t('col.status', 'Status')}</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 bg-white">
                                ${recentSales.length === 0 ? `<tr><td colspan="5" class="py-8 text-center text-xs text-slate-400">${t('msg.no_data', 'No sales transactions recorded yet today.')}</td></tr>` : ''}
                                ${recentSales.map(s => {
                                    const isVoid = s.status === 'Voided';
                                    return `
                                        <tr class="tr-hover">
                                            <td class="td font-mono font-bold text-xs ${isVoid ? 'text-slate-400 line-through' : 'text-teal-900'}">${s.reference}</td>
                                            <td class="td text-xs text-slate-500 font-mono">${(s.date_time || '').split(' ')[1] || s.date_time}</td>
                                            <td class="td text-center font-mono text-xs">${s.items_count || 1}</td>
                                            <td class="td-num font-bold text-xs ${isVoid ? 'text-slate-400' : 'text-slate-900'}">${formatMoney(s.total_amount)}</td>
                                            <td class="td text-center">
                                                <span class="badge ${isVoid ? 'badge-danger' : 'badge-success'} text-[10px]">${isVoid ? t('status.voided', 'Voided') : t('status.completed', 'Completed')}</span>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Right: Dispensary Action & Alert Watchlist (5 cols) -->
                <div class="lg:col-span-5 space-y-3">
                    
                    <!-- Stock Alert Card -->
                    <div class="card p-3.5">
                        <div class="flex items-center justify-between pb-2 border-b border-slate-100 mb-2.5">
                            <div class="flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full ${lowStockItems.length > 0 ? 'bg-amber-500' : 'bg-emerald-500'}"></span>
                                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wide">${t('dash.low_stock_alerts', 'Stock Alert Watchlist')}</h4>
                            </div>
                            <button class="text-[11px] text-teal-800 font-semibold hover:underline" onclick="navigate('inventory')">${t('dash.view_inventory', 'View All')}</button>
                        </div>
                        
                        ${lowStockItems.length === 0 ? `
                            <div class="py-3 text-center text-slate-500 text-xs">
                                <div class="text-emerald-700 font-semibold text-xs mb-0.5">&#10003; ${t('status.normal', 'All Stock Healthy')}</div>
                                <span class="text-[11px] text-slate-400">${t('dash.no_low_stock', 'No items are currently below reorder thresholds.')}</span>
                            </div>
                        ` : `
                            <div class="divide-y divide-slate-100">
                                ${lowStockItems.map(item => `
                                    <div class="py-2 flex items-center justify-between text-xs">
                                        <div class="pr-2 min-w-0">
                                            <div class="font-bold text-slate-800 truncate">${item.name}</div>
                                            <div class="text-[10px] text-slate-400">${t('prod.field_min_stock', 'Reorder Level')}: ${item.min_stock_level || 5} ${item.unit_measure || ''}</div>
                                        </div>
                                        <div class="text-right flex-shrink-0">
                                            <span class="font-mono font-bold text-rose-700 text-xs">${item.current_stock} ${t('status.low_stock', 'left')}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `}
                    </div>

                    <!-- Quick Dispensary Operational Shortcuts -->
                    <div class="card p-3.5 bg-slate-50/70">
                        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">${t('set.store_profile', 'Dispensary Operations Guide')}</h4>
                        <div class="space-y-1.5 text-xs">
                            <div class="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                                <span class="text-slate-700 font-medium">1. ${t('sales.pos_tab', 'Fast Cashier Checkout')}</span>
                                <span class="font-mono text-[10px] bg-slate-100 border border-slate-300 px-1.5 py-0.5 rounded text-slate-700 font-bold">F1</span>
                            </div>
                            <div class="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                                <span class="text-slate-700 font-medium">2. ${t('set.expiry_rule', 'Strict Medicine FEFO')}</span>
                                <span class="text-[10px] text-teal-800 font-semibold">${t('status.expiring_soon', 'Earliest Expiry First')}</span>
                            </div>
                            <div class="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                                <span class="text-slate-700 font-medium">3. ${t('sup.btn_record_payment', 'Supplier Settlement')}</span>
                                <span class="text-[10px] text-slate-600 font-mono">${formatMoney(supplierDue)}</span>
                            </div>
                        </div>
                    </div>

                </div>

            </div>

        </div>
    `;
}
