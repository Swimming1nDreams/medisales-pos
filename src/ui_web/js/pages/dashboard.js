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

    // Set top header actions - Clean and minimal
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-primary shadow-sm hover:shadow transition-all" onclick="navigate('sales')">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                <span class="font-bold">${t('dash.quick_pos', 'POS Cashier (F1)')}</span>
            </button>
            <button class="btn btn-secondary text-slate-700 hover:bg-slate-100" onclick="navigate('purchases')">
                <svg class="w-4 h-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span>${t('pur.add_button', 'Purchase')}</span>
            </button>
            <button class="btn btn-secondary text-slate-700 hover:bg-slate-100" onclick="navigate('expenses')">
                <svg class="w-4 h-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                <span>${t('exp.add_button', 'Expense')}</span>
            </button>
        `;
    }

    const hasAlerts = lowStockCount > 0 || expiringSoonCount > 0 || expiredCount > 0;

    container.innerHTML = `
        <div class="space-y-4 max-w-7xl mx-auto">
            
            <!-- ROW 1: 4 Core Essential Metrics (Clean, Spacious, No Button Clutter) -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                
                <!-- 1. Today's Revenue -->
                <div class="card p-4 bg-gradient-to-br from-emerald-50/40 via-white to-white border-slate-200/90 shadow-xs hover:border-emerald-300 transition-colors">
                    <div class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-slate-500 uppercase tracking-wider text-[11px]">${t('dash.revenue_today', "Today's Sales")}</span>
                        <span class="badge badge-success text-[10px] font-bold px-2 py-0.5">${salesCount} ${t('sales.cart_items', 'orders')}</span>
                    </div>
                    <div class="mt-2 flex items-baseline gap-1">
                        <span class="text-2xl font-black text-slate-900 font-mono tracking-tight">${formatMoney(revenue)}</span>
                    </div>
                    <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                        <span>${t('dash.val_cogs_clean', 'Product Cost')}:</span>
                        <span class="font-mono font-medium text-slate-700">${formatMoney(cogs)}</span>
                    </div>
                </div>

                <!-- 2. Today's Gross Profit -->
                <div class="card p-4 bg-gradient-to-br from-teal-50/40 via-white to-white border-slate-200/90 shadow-xs hover:border-teal-300 transition-colors">
                    <div class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-slate-500 uppercase tracking-wider text-[11px]">${t('dash.gross_profit_today', 'Gross Profit')}</span>
                        <span class="badge badge-teal text-[10px] font-bold px-2 py-0.5">${marginPct}%</span>
                    </div>
                    <div class="mt-2 flex items-baseline gap-1">
                        <span class="text-2xl font-black text-teal-900 font-mono tracking-tight">${formatMoney(grossProfit)}</span>
                    </div>
                    <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                        <span>${t('rep.tab_pnl', 'Performance')}:</span>
                        <span class="text-teal-700 font-medium">${revenue > 0 ? t('set.recon_surplus', 'Profitable') : '—'}</span>
                    </div>
                </div>

                <!-- 3. Operating Expenses -->
                <div class="card p-4 bg-gradient-to-br from-amber-50/40 via-white to-white border-slate-200/90 shadow-xs hover:border-amber-300 transition-colors">
                    <div class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-slate-500 uppercase tracking-wider text-[11px]">${t('nav.expenses', 'Today Expenses')}</span>
                        <span class="badge ${expenses > 0 ? 'badge-warning font-bold' : 'badge-neutral'} text-[10px] px-2 py-0.5">${t('rep.date_today', 'Today')}</span>
                    </div>
                    <div class="mt-2 flex items-baseline gap-1">
                        <span class="text-2xl font-black text-slate-900 font-mono tracking-tight">${formatMoney(expenses)}</span>
                    </div>
                    <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                        <span>${t('dash.launch_exp_title', 'Shop costs')}:</span>
                        <span class="text-slate-600 truncate max-w-[130px]">${t('dash.expenses_sub', 'Rent, power & wages')}</span>
                    </div>
                </div>

                <!-- 4. Total Stock Valuation -->
                <div class="card p-4 bg-gradient-to-br from-indigo-50/40 via-white to-white border-slate-200/90 shadow-xs hover:border-indigo-300 transition-colors">
                    <div class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-slate-500 uppercase tracking-wider text-[11px]">${t('dash.inventory_valuation', 'Inventory Value')}</span>
                        <span class="badge badge-info text-[10px] font-bold px-2 py-0.5">${activeProducts} ${t('status.active', 'SKUs')}</span>
                    </div>
                    <div class="mt-2 flex items-baseline gap-1">
                        <span class="text-2xl font-black text-indigo-950 font-mono tracking-tight">${formatMoney(invValue)}</span>
                    </div>
                    <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                        <span>${t('pur.outstanding', 'Vendor Debt')}:</span>
                        <span class="font-mono font-medium ${supplierDue > 0 ? 'text-amber-800' : 'text-slate-600'}">${formatMoney(supplierDue)}</span>
                    </div>
                </div>

            </div>

            <!-- ROW 2: Actionable Alerts Bar (Consolidated into ONE clean notification) -->
            ${hasAlerts ? `
                <div class="card p-3 bg-amber-50/70 border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center flex-shrink-0">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        </div>
                        <div class="text-xs">
                            <span class="font-bold text-amber-950">${t('dash.low_stock_alerts', 'Stock & Safety Notifications')}:</span>
                            <span class="text-amber-900 ml-1">
                                ${lowStockCount > 0 ? `<span class="font-semibold text-amber-800">${lowStockCount} ${t('dash.low_stock_unit', 'items low stock')}</span>` : ''}
                                ${(lowStockCount > 0 && expiringSoonCount > 0) ? ' • ' : ''}
                                ${expiringSoonCount > 0 ? `<span class="font-semibold text-rose-700">${expiringSoonCount} ${t('dash.expiring_soon_unit', 'batch expiring soon')}</span>` : ''}
                            </span>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-secondary text-amber-900 border-amber-300 bg-white hover:bg-amber-100 self-start sm:self-auto text-xs font-medium" onclick="navigate('inventory')">
                        ${t('dash.view_inventory', 'Check Inventory')} &rarr;
                    </button>
                </div>
            ` : `
                <div class="card px-3.5 py-2.5 bg-emerald-50/50 border-emerald-200/60 flex items-center justify-between text-xs">
                    <div class="flex items-center gap-2 text-emerald-800">
                        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                        <span class="font-medium">${t('dash.health_all_ok', 'All Stock Healthy')} &bull; ${t('dash.health_expiring_ok', 'No Expiring Batches')}</span>
                    </div>
                    <span class="text-[11px] text-emerald-700 font-mono">${data.date || new Date().toISOString().split('T')[0]}</span>
                </div>
            `}

            <!-- ROW 3: Main Working Workspace (65% Sales Register / 35% Quick Actions & Ledger) -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                
                <!-- Left Column (7 cols): Today's Recent Sales Register -->
                <div class="lg:col-span-7 card flex flex-col shadow-xs overflow-hidden">
                    <div class="px-4 py-3 border-b border-slate-100 bg-white flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <h3 class="font-bold text-xs uppercase tracking-wider text-slate-800">${t('dash.recent_sales', 'Recent Sales')}</h3>
                            <span class="badge badge-neutral text-[10px] font-mono">${recentSales.length}</span>
                        </div>
                        <button class="btn btn-sm btn-secondary text-xs text-slate-600 hover:text-slate-900" onclick="navigate('sales')">
                            ${t('dash.view_all_sales', 'View All')} &rarr;
                        </button>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="table w-full">
                            <thead>
                                <tr class="bg-slate-50/50 text-[11px] text-slate-500 border-b border-slate-100">
                                    <th class="th py-2 px-3">${t('col.receipt', 'Receipt #')}</th>
                                    <th class="th py-2 px-3">${t('col.date', 'Time')}</th>
                                    <th class="th py-2 px-3 text-center">${t('col.qty', 'Items')}</th>
                                    <th class="th py-2 px-3 text-right">${t('col.total', 'Amount (Ks)')}</th>
                                    <th class="th py-2 px-3 text-center">${t('col.status', 'Status')}</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 bg-white text-xs">
                                ${recentSales.length === 0 ? `
                                    <tr>
                                        <td colspan="5" class="py-10 text-center text-slate-400">
                                            <p>${t('msg.no_data', 'No sales transactions recorded yet today.')}</p>
                                            <button class="btn btn-sm btn-primary mt-3" onclick="navigate('sales')">
                                                ${t('dash.quick_pos', 'Open POS Cashier')}
                                            </button>
                                        </td>
                                    </tr>
                                ` : ''}
                                ${recentSales.map(s => {
                                    const isVoid = s.status === 'Voided';
                                    return `
                                        <tr class="hover:bg-slate-50/80 transition-colors">
                                            <td class="py-2.5 px-3 font-mono font-bold text-xs ${isVoid ? 'text-slate-400 line-through' : 'text-slate-900'}">${s.reference}</td>
                                            <td class="py-2.5 px-3 text-slate-500 font-mono text-[11px]">${(s.date_time || '').split(' ')[1] || s.date_time}</td>
                                            <td class="py-2.5 px-3 text-center font-mono text-slate-600">${s.items_count || 1}</td>
                                            <td class="py-2.5 px-3 text-right font-mono font-bold ${isVoid ? 'text-slate-400' : 'text-slate-900'}">${formatMoney(s.total_amount)}</td>
                                            <td class="py-2.5 px-3 text-center">
                                                <span class="badge ${isVoid ? 'badge-danger' : 'badge-success'} text-[10px] font-semibold">${isVoid ? t('status.voided', 'Voided') : t('status.completed', 'Completed')}</span>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Right Column (5 cols): Quick Launch & Neighborhood Ledger Shortcuts -->
                <div class="lg:col-span-5 space-y-3.5">
                    
                    <!-- Fast POS Cashier Hero Card -->
                    <div class="card p-4 bg-gradient-to-br from-teal-900 to-slate-900 text-white shadow-md border-0">
                        <div class="flex items-start justify-between">
                            <div>
                                <span class="badge bg-teal-500/20 text-teal-300 border border-teal-500/30 text-[10px] font-mono font-bold">POS Cashier</span>
                                <h3 class="text-base font-bold text-white mt-1.5">${t('dash.quick_pos', 'Open POS Cashier')}</h3>
                                <p class="text-xs text-slate-300 mt-0.5">${t('dash.launch_pos_sub', 'Quick checkout, barcodes & dispensing')}</p>
                            </div>
                            <span class="px-2 py-1 bg-white/10 rounded-md font-mono text-xs font-bold text-teal-300 border border-white/10">F1</span>
                        </div>
                        <button class="w-full mt-4 py-2.5 px-4 bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-bold rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 text-xs" onclick="navigate('sales')">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                            <span>${t('dash.launch_pos_title', 'Start New Sale (F1)')}</span>
                        </button>
                    </div>

                    <!-- 3 Essential Shortcuts -->
                    <div class="card p-3 divide-y divide-slate-100">
                        
                        <!-- Add Product -->
                        <div class="py-2.5 flex items-center justify-between hover:bg-slate-50/80 px-2 rounded-lg cursor-pointer transition-colors" onclick="navigate('products')">
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-lg bg-sky-100 text-sky-800 flex items-center justify-center flex-shrink-0">
                                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-slate-800">${t('dash.launch_prod_title', 'Add New Product')}</h4>
                                    <p class="text-[11px] text-slate-500">${t('dash.launch_prod_sub', 'Medicines, pricing & units')}</p>
                                </div>
                            </div>
                            <span class="text-xs text-slate-400">&rarr;</span>
                        </div>

                        <!-- Customer Credit Ledger -->
                        <div class="py-2.5 flex items-center justify-between hover:bg-slate-50/80 px-2 rounded-lg cursor-pointer transition-colors" onclick="navigate('customers')">
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center flex-shrink-0">
                                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-slate-800">${t('dash.launch_cust_title', 'Customer Credit Book')}</h4>
                                    <p class="text-[11px] text-slate-500">${t('dash.launch_cust_sub', 'Debt ledger & repayments')}</p>
                                </div>
                            </div>
                            <span class="text-xs text-slate-400">&rarr;</span>
                        </div>

                        <!-- Receive Purchase -->
                        <div class="py-2.5 flex items-center justify-between hover:bg-slate-50/80 px-2 rounded-lg cursor-pointer transition-colors" onclick="navigate('purchases')">
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-800 flex items-center justify-center flex-shrink-0">
                                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-slate-800">${t('dash.launch_pur_title', 'Receive Purchase')}</h4>
                                    <p class="text-[11px] text-slate-500">${t('dash.launch_pur_sub', 'Restock from distributors')}</p>
                                </div>
                            </div>
                            <span class="text-xs text-slate-400">&rarr;</span>
                        </div>

                    </div>

                    <!-- Low Stock Quick Glance (Only shown if items are low stock) -->
                    ${lowStockItems.length > 0 ? `
                        <div class="card p-3 bg-white">
                            <div class="flex items-center justify-between pb-1.5 border-b border-slate-100 text-xs">
                                <span class="font-bold text-slate-700 uppercase tracking-wider text-[10px]">${t('dash.low_stock_alerts', 'Reorder Watchlist')}</span>
                                <button class="text-teal-700 hover:underline text-[11px] font-medium" onclick="navigate('inventory')">${t('dash.view_inventory', 'View Inventory')}</button>
                            </div>
                            <div class="divide-y divide-slate-100 mt-1">
                                ${lowStockItems.map(item => `
                                    <div class="py-1.5 flex items-center justify-between text-xs">
                                        <span class="text-slate-800 truncate pr-2">${item.name}</span>
                                        <span class="font-mono font-bold text-rose-700 text-xs flex-shrink-0">${item.current_stock} ${item.unit_measure || ''}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                </div>

            </div>

        </div>
    `;
}
