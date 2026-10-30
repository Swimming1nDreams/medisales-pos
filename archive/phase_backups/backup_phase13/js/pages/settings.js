let isBackingUp = false;
let isRestoring = false;

// Denominations for Myanmar Kyat
const MM_DENOMINATIONS = [
    { value: 50000, label: '50,000 Ks notes' },
    { value: 20000, label: '20,000 Ks notes' },
    { value: 10000, label: '10,000 Ks notes' },
    { value: 5000,  label: '5,000 Ks notes' },
    { value: 1000,  label: '1,000 Ks notes' },
    { value: 500,   label: '500 Ks notes' }
];

let denominationCounts = {
    50000: 0,
    20000: 0,
    10000: 0,
    5000: 0,
    1000: 0,
    500: 0
};
let otherCashAmount = 0;

async function renderSettings(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-secondary text-xs py-1" onclick="renderSettings(document.getElementById('content-area'))">
                <svg class="w-3.5 h-3.5 mr-1 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span>Refresh System Status</span>
            </button>
        `;
    }

    let dbInfo = { db_path: 'medisales.db', size_bytes: 0 };
    try {
        dbInfo = await callBackend('get_database_info');
    } catch(e) {
        console.warn("Could not retrieve db info:", e);
    }

    const today = new Date().toISOString().split('T')[0];
    let todaySales = 0;
    try {
        const salesSummary = await callBackend('get_sales_summary', today, today);
        todaySales = salesSummary.total_sales || salesSummary.total_revenue || 0;
    } catch(e) {
        console.warn("Could not retrieve today's sales for reconciliation:", e);
    }

    const formatBytes = (bytes) => {
        if (!bytes) return '0 KB';
        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    };

    container.innerHTML = `
        <div class="space-y-4 max-w-6xl mx-auto">
            
            <!-- System Status Header Card -->
            <div class="p-4 bg-white border border-slate-200 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div class="space-y-0.5">
                    <div class="flex items-center gap-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5"></span>
                            Standalone Offline Engine Active
                        </span>
                        <span class="text-[11px] text-slate-500 font-mono">SQLite WAL Mode</span>
                    </div>
                    <h3 class="text-base font-bold text-slate-900">System Settings & Data Management</h3>
                    <p class="text-xs text-slate-500">Medisales Pharmacy & Retail POS &bull; Commercial Edition 2.4</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5 text-right">
                        <div class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Active Database Size</div>
                        <div class="text-sm font-bold text-slate-900 font-mono">${formatBytes(dbInfo.size_bytes)}</div>
                    </div>
                </div>
            </div>

            <!-- Main 2-Column Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                
                <!-- Column 1: Database Operations -->
                <div class="space-y-4">
                    
                    <!-- Active Storage Card -->
                    <div class="card p-4">
                        <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                            <div class="flex items-center gap-2">
                                <div class="w-7 h-7 rounded bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-xs border border-teal-200">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7c0-2-1.5-3-3.5-3h-9C5.5 4 4 5 4 7zm0 5h16m-16 5h16"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-slate-900">Active Database Storage</h4>
                                    <p class="text-[11px] text-slate-500">Local embedded SQLite instance</p>
                                </div>
                            </div>
                            <span class="badge badge-success text-[10px]">Connected</span>
                        </div>

                        <div class="bg-slate-50 border border-slate-200 rounded-md p-3 space-y-2 text-xs">
                            <div>
                                <span class="font-medium text-slate-500 block text-[11px] mb-0.5">Physical File Location:</span>
                                <div class="font-mono text-slate-900 bg-white p-2 rounded border border-slate-200 select-all break-all text-[11px] leading-relaxed">
                                    ${escapeHtml(dbInfo.db_path)}
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                                <div>
                                    <span class="text-slate-500">File Size:</span>
                                    <div class="text-slate-900 font-bold">${formatBytes(dbInfo.size_bytes)}</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">Concurrency:</span>
                                    <div class="text-slate-900 font-medium">Write-Ahead Log (WAL)</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">Cloud Dependency:</span>
                                    <div class="text-emerald-700 font-semibold">100% Offline Local</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">Safety Guarantee:</span>
                                    <div class="text-slate-900 font-medium">ACID Atomic Commits</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Backup Card -->
                    <div class="card p-4 border-l-4 border-l-teal-600">
                        <div class="flex items-center gap-2 mb-2">
                            <div class="w-7 h-7 rounded bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-xs border border-teal-200">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-bold text-slate-900">Database Backup</h4>
                                <p class="text-[11px] text-slate-500">Online non-blocking snapshot</p>
                            </div>
                        </div>
                        <p class="text-xs text-slate-600 mb-3 leading-relaxed">
                            Creates a complete snapshot of all products, medicine batches, sales history, and audit trails. Uses SQLite online backup API so cashier operations continue without interruption.
                        </p>
                        <div class="bg-teal-50/50 border border-teal-200/80 rounded p-2.5 mb-3 text-[11px] text-teal-900">
                            <strong>Recommended Practice:</strong> Save backups to an external USB flash drive or secondary drive at the end of each business day.
                        </div>
                        <button id="backup-btn" class="btn btn-primary w-full justify-center text-xs py-1.5" onclick="backupDatabase()">
                            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                            </svg>
                            Create Local Database Backup
                        </button>
                    </div>

                    <!-- Restore Card -->
                    <div class="card p-4 border-l-4 border-l-amber-500">
                        <div class="flex items-center gap-2 mb-2">
                            <div class="w-7 h-7 rounded bg-amber-50 text-amber-700 flex items-center justify-center font-bold text-xs border border-amber-200">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-bold text-slate-900">Database Restore</h4>
                                <p class="text-[11px] text-amber-700 font-medium">Safe replacement from backup</p>
                            </div>
                        </div>
                        <p class="text-xs text-slate-600 mb-3 leading-relaxed">
                            Restores shop records from a previously saved backup file.
                        </p>
                        <div class="bg-amber-50 border border-amber-200 rounded p-2.5 mb-3 text-[11px] text-amber-900">
                            <strong>Automatic Safety Guarantee:</strong> Before overwriting any records, Medisales automatically takes a timestamped safety copy of your current active database.
                        </div>
                        <button id="restore-btn" class="btn btn-secondary w-full justify-center text-amber-800 border-amber-300 hover:bg-amber-50 hover:border-amber-400 font-semibold text-xs py-1.5" onclick="confirmAndRestoreDatabase()">
                            <svg class="w-3.5 h-3.5 mr-1.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                            </svg>
                            Restore From Backup File...
                        </button>
                    </div>

                </div>

                <!-- Column 2: Cash Reconciliation & System Profile -->
                <div class="space-y-4">
                    
                    <!-- Cash Reconciliation Widget -->
                    <div class="card p-4">
                        <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                            <div class="flex items-center gap-2">
                                <div class="w-7 h-7 rounded bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xs border border-emerald-200">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-slate-900">End-of-Day Cash Reconciliation</h4>
                                    <p class="text-[11px] text-slate-500">Drawer denomination counter & balance</p>
                                </div>
                            </div>
                            <button class="text-xs text-slate-500 hover:text-slate-800 underline" onclick="resetDenominations()">Reset Form</button>
                        </div>

                        <p class="text-xs text-slate-600 mb-3">
                            Count physical cash notes in your drawer and compare directly with today's POS cash sales.
                        </p>

                        <!-- Denomination Entry Table -->
                        <div class="space-y-1.5 mb-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                            ${MM_DENOMINATIONS.map(d => `
                                <div class="flex items-center justify-between text-xs gap-2">
                                    <label class="w-32 font-medium text-slate-700 text-[11px]">${d.label}</label>
                                    <div class="flex items-center gap-1 flex-1 max-w-[130px]">
                                        <span class="text-slate-400">&times;</span>
                                        <input type="number" min="0" value="${denominationCounts[d.value] || 0}" 
                                            class="form-input text-right py-1 px-2 text-xs" 
                                            id="denom-${d.value}" 
                                            oninput="updateDenomination(${d.value}, this.value, ${todaySales})" />
                                    </div>
                                    <div class="w-24 text-right font-mono font-semibold text-slate-800 text-xs" id="subtotal-${d.value}">
                                        ${formatMoney((denominationCounts[d.value] || 0) * d.value)}
                                    </div>
                                </div>
                            `).join('')}

                            <div class="flex items-center justify-between text-xs gap-2 pt-2 border-t border-slate-200">
                                <label class="w-32 font-medium text-slate-700 text-[11px]">Other / Coins (Ks)</label>
                                <div class="flex items-center gap-1 flex-1 max-w-[130px]">
                                    <span class="text-slate-400">+</span>
                                    <input type="number" min="0" value="${otherCashAmount}" 
                                        class="form-input text-right py-1 px-2 text-xs" 
                                        id="denom-other" 
                                        oninput="updateOtherCash(this.value, ${todaySales})" />
                                </div>
                                <div class="w-24 text-right font-mono font-semibold text-slate-800 text-xs" id="subtotal-other">
                                    ${formatMoney(otherCashAmount)}
                                </div>
                            </div>
                        </div>

                        <!-- Reconciliation Summary -->
                        <div class="bg-white border border-slate-200 rounded-md p-3 space-y-2 text-xs">
                            <div class="flex justify-between items-center text-slate-600">
                                <span>Total Cash Counted in Drawer:</span>
                                <span class="font-mono font-bold text-slate-900 text-sm" id="recon-counted">0 Ks</span>
                            </div>
                            <div class="flex justify-between items-center text-slate-600">
                                <span>Today's System Cash Sales (${today}):</span>
                                <span class="font-mono font-bold text-teal-800 text-sm" id="recon-expected">${formatMoney(todaySales)}</span>
                            </div>
                            <div class="flex justify-between items-center pt-2 border-t border-slate-100 font-bold">
                                <span>Drawer Discrepancy:</span>
                                <span class="font-mono text-xs px-2 py-0.5 rounded" id="recon-variance">0 Ks</span>
                            </div>
                        </div>
                    </div>

                    <!-- Store Profile -->
                    <div class="card p-4">
                        <div class="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
                            <div class="w-7 h-7 rounded bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs border border-slate-200">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-bold text-slate-900">Store Operational Profile</h4>
                                <p class="text-[11px] text-slate-500">Retail pharmacy system parameters</p>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Trading Name</span>
                                <span class="font-bold text-slate-800">Medisales Pharmacy & Retail</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Primary Currency</span>
                                <span class="font-bold text-slate-800">Myanmar Kyat (MMK / Ks)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Accounting Precision</span>
                                <span class="font-bold text-slate-800">Integer Kyat (No Decimals)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Inventory Expiry Rule</span>
                                <span class="font-bold text-slate-800">FEFO (First Expired First Out)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200 col-span-2">
                                <span class="text-slate-500 block text-[10px]">Audit Integrity</span>
                                <span class="font-medium text-slate-800">Permanent record retention with explicit void logs</span>
                            </div>
                        </div>
                    </div>

                </div>

            </div>
        </div>
    `;

    // Recalculate cash initial state
    updateReconciliationDisplay(todaySales);
}

window.updateDenomination = function(denom, countStr, expectedSales) {
    const count = parseInt(countStr) || 0;
    denominationCounts[denom] = count;
    const subtotalEl = document.getElementById(`subtotal-${denom}`);
    if (subtotalEl) {
        subtotalEl.innerText = formatMoney(count * denom);
    }
    updateReconciliationDisplay(expectedSales);
};

window.updateOtherCash = function(valStr, expectedSales) {
    otherCashAmount = parseInt(valStr) || 0;
    const subtotalEl = document.getElementById('subtotal-other');
    if (subtotalEl) {
        subtotalEl.innerText = formatMoney(otherCashAmount);
    }
    updateReconciliationDisplay(expectedSales);
};

window.resetDenominations = function() {
    MM_DENOMINATIONS.forEach(d => {
        denominationCounts[d.value] = 0;
        const input = document.getElementById(`denom-${d.value}`);
        if (input) input.value = 0;
        const subtotal = document.getElementById(`subtotal-${d.value}`);
        if (subtotal) subtotal.innerText = "0 Ks";
    });
    otherCashAmount = 0;
    const otherInput = document.getElementById('denom-other');
    if (otherInput) otherInput.value = 0;
    const otherSubtotal = document.getElementById('subtotal-other');
    if (otherSubtotal) otherSubtotal.innerText = "0 Ks";

    const expectedEl = document.getElementById('recon-expected');
    const expected = expectedEl ? parseInt(expectedEl.innerText.replace(/[^0-9]/g, '')) || 0 : 0;
    updateReconciliationDisplay(expected);
};

function updateReconciliationDisplay(expectedSales) {
    let totalCounted = otherCashAmount;
    MM_DENOMINATIONS.forEach(d => {
        totalCounted += (denominationCounts[d.value] || 0) * d.value;
    });

    const countedEl = document.getElementById('recon-counted');
    if (countedEl) countedEl.innerText = formatMoney(totalCounted);

    const varianceEl = document.getElementById('recon-variance');
    if (varianceEl) {
        const diff = totalCounted - expectedSales;
        if (diff === 0) {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold";
            varianceEl.innerText = "Balanced (0 Ks)";
        } else if (diff > 0) {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold";
            varianceEl.innerText = `+${formatMoney(diff)} (Surplus)`;
        } else {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-bold";
            varianceEl.innerText = `-${formatMoney(Math.abs(diff))} (Shortage)`;
        }
    }
}

window.backupDatabase = async function() {
    if (isBackingUp) return;
    const btn = document.getElementById('backup-btn');
    isBackingUp = true;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            Selecting Destination & Backing Up...
        `;
    }

    try {
        const res = await callBackend('backup_database');
        if (res.cancelled) {
            return;
        }
        showToast("Database backup created successfully!\nLocation: " + (res.file_path || 'saved'));
        await renderSettings(document.getElementById('content-area'));
    } catch (e) {
        showToast("Backup failed: " + e, "error");
    } finally {
        isBackingUp = false;
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `
                <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                </svg>
                Create Local Database Backup
            `;
        }
    }
};

window.confirmAndRestoreDatabase = function() {
    openConfirmModal({
        title: "Confirm Database Restore",
        message: "Restoring a database backup replaces all current products, sales, and inventory with the backup file data. Medisales will first create an automatic timestamped safety copy of your current active database before performing the restore.",
        confirmText: "Proceed to Select File",
        confirmClass: "btn-danger",
        onConfirm: () => {
            executeRestore();
        }
    });
};

window.executeRestore = async function() {
    if (isRestoring) return;
    const btn = document.getElementById('restore-btn');
    isRestoring = true;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin w-3.5 h-3.5 mr-1.5 text-amber-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            Restoring Database...
        `;
    }

    try {
        const res = await callBackend('restore_database');
        if (res.cancelled) {
            return;
        }
        showToast("Database restored successfully!\nSafety backup saved.");
        await renderSettings(document.getElementById('content-area'));
    } catch (e) {
        showToast("Restore failed: " + e, "error");
    } finally {
        isRestoring = false;
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `
                <svg class="w-3.5 h-3.5 mr-1.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                </svg>
                Restore From Backup File...
            `;
        }
    }
};
