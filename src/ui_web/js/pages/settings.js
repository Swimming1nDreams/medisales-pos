let isBackingUp = false;
let isRestoring = false;

// Denominations for Myanmar Kyat
function getDenominations() {
    return [
        { value: 10000, label: t('set.denom_10k', '10,000 Ks notes') },
        { value: 5000,  label: t('set.denom_5k', '5,000 Ks notes') },
        { value: 1000,  label: t('set.denom_1k', '1,000 Ks notes') },
        { value: 500,   label: t('set.denom_500', '500 Ks notes') }
    ];
}

let denominationCounts = {
    10000: 0,
    5000: 0,
    1000: 0,
    500: 0
};
let smallChangeAmount = 0;
let isSmallChangeValid = true;
let otherCashAmount = 0;

async function renderSettings(container) {
    const headerActions = document.getElementById('header-actions');
    if (headerActions) {
        headerActions.innerHTML = `
            <button class="btn btn-secondary text-xs py-1" onclick="renderSettings(document.getElementById('content-area'))">
                <svg class="w-3.5 h-3.5 mr-1 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span>${t('btn.refresh', 'Refresh')}</span>
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

    let todaySavedRecon = null;
    try {
        todaySavedRecon = await callBackend('get_cash_reconciliation', today);
        if (todaySavedRecon) {
            const parsed = typeof todaySavedRecon === 'string' ? JSON.parse(todaySavedRecon) : todaySavedRecon;
            if (parsed && parsed.denominations) {
                getDenominations().forEach(d => {
                    if (typeof parsed.denominations[d.value] !== 'undefined') {
                        denominationCounts[d.value] = parsed.denominations[d.value];
                    }
                });
            }
            if (parsed && typeof parsed.small_change_amount !== 'undefined') {
                smallChangeAmount = parseInt(parsed.small_change_amount) || 0;
                otherCashAmount = smallChangeAmount;
            }
            isSmallChangeValid = true;
        }
    } catch(e) {
        console.warn("Could not retrieve saved reconciliation for today:", e);
    }

    const formatBytes = (bytes) => {
        if (!bytes) return '0 KB';
        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    };

    const currentLang = getLanguage();
    const denominations = getDenominations();

    container.innerHTML = `
        <div class="space-y-4 max-w-6xl mx-auto">
            
            <!-- System Status Header Card -->
            <div class="p-4 bg-white border border-slate-200 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div class="space-y-0.5">
                    <div class="flex items-center gap-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5"></span>
                            ${t('app.offline_status', 'Standalone Offline Engine Active')}
                        </span>
                        <span class="text-[11px] text-slate-500 font-mono">${t('app.wal_status', 'SQLite WAL Mode')}</span>
                    </div>
                    <h3 class="text-base font-bold text-slate-900">${t('set.title', 'System Settings & Data Management')}</h3>
                    <p class="text-xs text-slate-500">${t('set.edition', 'Medisales Pharmacy & Retail POS • Commercial Edition 2.4')}</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5 text-right">
                        <div class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">${t('set.file_size', 'Active File Size:')}</div>
                        <div class="text-sm font-bold text-slate-900 font-mono">${formatBytes(dbInfo.size_bytes)}</div>
                    </div>
                </div>
            </div>

            <!-- Language & Localization Card -->
            <div class="card p-4 border-l-4 border-l-teal-600 bg-white">
                <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                    <div class="flex items-center gap-2.5">
                        <div class="w-7 h-7 rounded bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-xs border border-teal-200">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path>
                            </svg>
                        </div>
                        <div>
                            <h4 class="text-xs font-bold text-slate-900">${t('set.language_card_title', 'Language & Localization')}</h4>
                            <p class="text-[11px] text-slate-500">${t('set.language_card_subtitle', 'Select interface display language')}</p>
                        </div>
                    </div>
                    <span class="badge badge-teal text-[10px] font-mono">${currentLang === 'my' ? t('set.badge_my', 'Myanmar') : t('set.badge_en', 'English')}</span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <label class="flex items-center p-3 rounded-lg border cursor-pointer transition-all ${currentLang === 'en' ? 'border-teal-600 bg-teal-50/50 text-teal-950 font-bold' : 'border-slate-200 hover:bg-slate-50 text-slate-700'}">
                        <input type="radio" name="app-lang" value="en" class="mr-3 text-teal-600" ${currentLang === 'en' ? 'checked' : ''} onchange="setLanguage('en')">
                        <div>
                            <div class="text-xs">${t('set.lang_en', 'English (US)')}</div>
                            <div class="text-[11px] text-slate-500 font-normal">${t('set.lang_en_desc', 'Default system language')}</div>
                        </div>
                    </label>
                    <label class="flex items-center p-3 rounded-lg border cursor-pointer transition-all ${currentLang === 'my' ? 'border-teal-600 bg-teal-50/50 text-teal-950 font-bold' : 'border-slate-200 hover:bg-slate-50 text-slate-700'}">
                        <input type="radio" name="app-lang" value="my" class="mr-3 text-teal-600" ${currentLang === 'my' ? 'checked' : ''} onchange="setLanguage('my')">
                        <div>
                            <div class="text-xs">${t('set.lang_my', 'Myanmar (Unicode)')}</div>
                            <div class="text-[11px] text-slate-500 font-normal">${t('set.lang_my_desc', 'Use Myanmar Unicode across the system')}</div>
                        </div>
                    </label>
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
                                    <h4 class="text-xs font-bold text-slate-900">${t('set.active_storage', 'Active Database Storage')}</h4>
                                    <p class="text-[11px] text-slate-500">${t('set.local_instance', 'Local embedded SQLite instance')}</p>
                                </div>
                            </div>
                            <span class="badge badge-success text-[10px]">${t('status.connected', 'Connected')}</span>
                        </div>

                        <div class="bg-slate-50 border border-slate-200 rounded-md p-3 space-y-2 text-xs">
                            <div>
                                <span class="font-medium text-slate-500 block text-[11px] mb-0.5">${t('set.physical_location', 'Physical File Location:')}</span>
                                <div class="font-mono text-slate-900 bg-white p-2 rounded border border-slate-200 select-all break-all text-[11px] leading-relaxed">
                                    ${escapeHtml(dbInfo.db_path)}
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                                <div>
                                    <span class="text-slate-500">${t('set.file_size', 'File Size:')}</span>
                                    <div class="text-slate-900 font-bold">${formatBytes(dbInfo.size_bytes)}</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">${t('set.concurrency', 'Concurrency:')}</span>
                                    <div class="text-slate-900 font-medium">Write-Ahead Log (WAL)</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">${t('set.cloud_dep', 'Cloud Dependency:')}</span>
                                    <div class="text-emerald-700 font-semibold">100% Offline Local</div>
                                </div>
                                <div>
                                    <span class="text-slate-500">${t('set.safety', 'Safety Guarantee:')}</span>
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
                                <h4 class="text-xs font-bold text-slate-900">${t('set.backup_title', 'Database Backup')}</h4>
                                <p class="text-[11px] text-slate-500">${t('set.backup_subtitle', 'Online non-blocking snapshot')}</p>
                            </div>
                        </div>
                        <p class="text-xs text-slate-600 mb-3 leading-relaxed">
                            ${t('set.backup_desc', 'Creates a complete snapshot of all products, medicine batches, sales history, and audit trails.')}
                        </p>
                        <button id="backup-btn" class="btn btn-primary w-full justify-center text-xs py-1.5" onclick="backupDatabase()">
                            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                            </svg>
                            ${t('set.backup_btn', 'Create Local Database Backup')}
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
                                <h4 class="text-xs font-bold text-slate-900">${t('set.restore_title', 'Database Restore')}</h4>
                                <p class="text-[11px] text-amber-700 font-medium">${t('set.restore_subtitle', 'Safe replacement from backup')}</p>
                            </div>
                        </div>
                        <p class="text-xs text-slate-600 mb-3 leading-relaxed">
                            ${t('set.restore_desc', 'Restores shop records from a previously saved backup file.')}
                        </p>
                        <button id="restore-btn" class="btn btn-secondary w-full justify-center text-amber-800 border-amber-300 hover:bg-amber-50 hover:border-amber-400 font-semibold text-xs py-1.5" onclick="confirmAndRestoreDatabase()">
                            <svg class="w-3.5 h-3.5 mr-1.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                            </svg>
                            ${t('set.restore_btn', 'Restore From Backup File...')}
                        </button>
                    </div>

                </div>

                <!-- Column 2: Cash Reconciliation & System Profile -->
                <div class="space-y-4">
                    
                    <!-- Cash Reconciliation Widget -->
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
                                    <h4 class="text-xs font-bold text-slate-900">${t('set.recon_title', 'End-of-Day Cash Reconciliation')}</h4>
                                    <p class="text-[11px] text-slate-500">${t('set.recon_subtitle', 'Drawer denomination counter & balance')}</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                <button type="button" class="text-xs text-teal-800 hover:underline font-semibold" onclick="loadSavedReconciliation('${today}')">${t('set.recon_reload', 'Reload Saved')}</button>
                                <span class="text-slate-300">|</span>
                                <button type="button" class="text-xs text-slate-500 hover:text-slate-800 underline" onclick="resetDenominations()">${t('set.recon_reset', 'Reset Form')}</button>
                            </div>
                        </div>

                        <p class="text-xs text-slate-600 mb-3">
                            ${t('set.recon_desc', 'Count physical cash notes in your drawer and compare directly with today\'s POS cash sales.')}
                        </p>

                        <!-- Denomination Entry Table -->
                        <div class="space-y-1.5 mb-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                            ${denominations.map(d => `
                                <div class="flex items-center justify-between text-xs gap-2">
                                    <label class="w-36 font-medium text-slate-700 text-[11px]" for="denom-${d.value}">${d.label}</label>
                                    <div class="flex items-center gap-1 flex-1 max-w-[130px]">
                                        <span class="text-slate-400">&times;</span>
                                        <input type="number" min="0" step="1" value="${denominationCounts[d.value] || 0}" 
                                            class="form-input text-right py-1 px-2 text-xs font-mono" 
                                            id="denom-${d.value}" 
                                            oninput="updateDenomination(${d.value}, this.value, ${todaySales})" />
                                    </div>
                                    <div class="w-24 text-right font-mono font-semibold text-slate-800 text-xs" id="subtotal-${d.value}">
                                        ${formatMoney((denominationCounts[d.value] || 0) * d.value)}
                                    </div>
                                </div>
                            `).join('')}

                            <!-- Small Change ("အကြွေ") Manual Amount Input Row -->
                            <div class="pt-2 border-t border-slate-200">
                                <div class="flex items-center justify-between text-xs gap-2">
                                    <label class="w-36 font-semibold text-slate-800 text-[11px]" for="denom-small-change">
                                        ${t('set.recon_small_change', 'Small Change Amount')}
                                    </label>
                                    <div class="flex items-center gap-1 flex-1 max-w-[130px]">
                                        <span class="text-slate-400 font-mono font-bold">+</span>
                                        <input type="number" min="0" step="1" value="${smallChangeAmount || 0}" 
                                            class="form-input text-right py-1 px-2 text-xs font-mono font-bold border-slate-300" 
                                            id="denom-small-change" 
                                            placeholder="0"
                                            oninput="updateSmallChange(this.value, ${todaySales})" />
                                    </div>
                                    <div class="w-24 text-right font-mono font-bold text-slate-900 text-xs" id="subtotal-small-change">
                                        ${formatMoney(smallChangeAmount || 0)}
                                    </div>
                                </div>
                                <p id="small-change-error" class="hidden text-[10px] text-rose-600 font-medium mt-1 text-right">
                                    ${t('set.recon_invalid_input', 'Please enter a valid, non-negative whole-number MMK amount.')}
                                </p>
                            </div>
                        </div>

                        <!-- Reconciliation Summary -->
                        <div class="bg-white border border-slate-200 rounded-md p-3 space-y-2 text-xs">
                            <div class="flex justify-between items-center text-slate-600">
                                <span>${t('set.recon_counted', 'Total Cash Counted in Drawer:')}</span>
                                <span class="font-mono font-bold text-slate-900 text-sm" id="recon-counted">0 Ks</span>
                            </div>
                            <div class="flex justify-between items-center text-slate-600">
                                <span>${t('set.recon_expected', 'Today\'s System Cash Sales:')} (${today}):</span>
                                <span class="font-mono font-bold text-teal-800 text-sm" id="recon-expected">${formatMoney(todaySales)}</span>
                            </div>
                            <div class="flex justify-between items-center pt-2 border-t border-slate-100 font-bold">
                                <span>${t('set.recon_variance', 'Drawer Discrepancy:')}</span>
                                <span class="font-mono text-xs px-2 py-0.5 rounded" id="recon-variance">0 Ks</span>
                            </div>
                        </div>

                        <!-- Saved Indicator Banner -->
                        <div id="recon-saved-indicator" class="${todaySavedRecon ? '' : 'hidden'} mt-2.5 p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] flex items-center justify-between">
                            <span class="font-semibold flex items-center gap-1">
                                <svg class="w-3.5 h-3.5 text-emerald-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                                <span>${t('set.recon_saved_badge', 'Saved Reconciliation Record')}</span>
                            </span>
                            <span class="font-mono text-[10px] text-emerald-700" id="recon-saved-time">${todaySavedRecon && todaySavedRecon.saved_at ? new Date(todaySavedRecon.saved_at).toLocaleTimeString() : ''}</span>
                        </div>

                        <!-- Save Reconciliation Button -->
                        <button id="save-recon-btn" type="button" class="btn btn-primary w-full py-2 text-xs font-bold mt-3 shadow-xs flex items-center justify-center gap-1.5" onclick="saveReconciliation()">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            <span>${t('set.recon_save_btn', 'Save Cash Reconciliation')}</span>
                        </button>
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
                                <h4 class="text-xs font-bold text-slate-900">${t('set.store_profile', 'Store Operational Profile')}</h4>
                                <p class="text-[11px] text-slate-500">${t('set.store_profile_sub', 'Retail pharmacy system parameters')}</p>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">${t('set.trading_name', 'Trading Name')}</span>
                                <span class="font-bold text-slate-800">Medisales Pharmacy & Retail</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">${t('set.primary_currency', 'Primary Currency')}</span>
                                <span class="font-bold text-slate-800">Myanmar Kyat (MMK / Ks)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">${t('set.precision', 'Accounting Precision')}</span>
                                <span class="font-bold text-slate-800">Integer Kyat (No Decimals)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">${t('set.expiry_rule', 'Inventory Expiry Rule')}</span>
                                <span class="font-bold text-slate-800">FEFO (First Expired First Out)</span>
                            </div>
                            <div class="p-2 bg-slate-50 rounded border border-slate-200 col-span-2">
                                <span class="text-slate-500 block text-[10px]">${t('set.audit_integrity', 'Audit Integrity')}</span>
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

function validateSmallChangeInput(rawVal) {
    if (rawVal === '' || rawVal === null || rawVal === undefined) {
        return { isValid: true, value: 0 };
    }
    const trimmed = String(rawVal).trim();
    if (trimmed === '') {
        return { isValid: true, value: 0 };
    }
    // Must be whole-number digits only (reject negative signs, floats, non-numeric)
    if (!/^\d+$/.test(trimmed)) {
        return { isValid: false, value: 0 };
    }
    const num = parseInt(trimmed, 10);
    if (isNaN(num) || num < 0 || !Number.isSafeInteger(num)) {
        return { isValid: false, value: 0 };
    }
    return { isValid: true, value: num };
}

window.updateDenomination = function(denom, countStr, expectedSales) {
    let count = parseInt(countStr);
    if (isNaN(count) || count < 0) {
        count = 0;
    }
    denominationCounts[denom] = count;
    const subtotalEl = document.getElementById(`subtotal-${denom}`);
    if (subtotalEl) {
        subtotalEl.innerText = formatMoney(count * denom);
    }
    updateReconciliationDisplay(expectedSales);
};

window.updateSmallChange = function(valStr, expectedSales) {
    const inputEl = document.getElementById('denom-small-change') || document.getElementById('denom-other');
    const errEl = document.getElementById('small-change-error');
    const subtotalEl = document.getElementById('subtotal-small-change') || document.getElementById('subtotal-other');
    const saveBtn = document.getElementById('save-recon-btn');

    const res = validateSmallChangeInput(valStr);
    if (!res.isValid) {
        isSmallChangeValid = false;
        if (inputEl) {
            inputEl.classList.add('border-rose-500', 'bg-rose-50', 'text-rose-900');
            inputEl.classList.remove('border-slate-300');
        }
        if (errEl) {
            errEl.classList.remove('hidden');
        }
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
        if (subtotalEl) {
            subtotalEl.innerText = "Invalid";
        }
        updateReconciliationDisplay(expectedSales);
        return;
    }

    isSmallChangeValid = true;
    smallChangeAmount = res.value;
    otherCashAmount = smallChangeAmount;

    if (inputEl) {
        inputEl.classList.remove('border-rose-500', 'bg-rose-50', 'text-rose-900');
        inputEl.classList.add('border-slate-300');
    }
    if (errEl) {
        errEl.classList.add('hidden');
    }
    if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
    if (subtotalEl) {
        subtotalEl.innerText = formatMoney(smallChangeAmount);
    }
    updateReconciliationDisplay(expectedSales);
};

// Backwards-compatibility alias
window.updateOtherCash = function(valStr, expectedSales) {
    window.updateSmallChange(valStr, expectedSales);
};

window.resetDenominations = function() {
    getDenominations().forEach(d => {
        denominationCounts[d.value] = 0;
        const input = document.getElementById(`denom-${d.value}`);
        if (input) input.value = 0;
        const subtotal = document.getElementById(`subtotal-${d.value}`);
        if (subtotal) subtotal.innerText = "0 Ks";
    });
    smallChangeAmount = 0;
    otherCashAmount = 0;
    isSmallChangeValid = true;

    const changeInput = document.getElementById('denom-small-change') || document.getElementById('denom-other');
    if (changeInput) {
        changeInput.value = 0;
        changeInput.classList.remove('border-rose-500', 'bg-rose-50', 'text-rose-900');
        changeInput.classList.add('border-slate-300');
    }
    const errEl = document.getElementById('small-change-error');
    if (errEl) errEl.classList.add('hidden');

    const changeSubtotal = document.getElementById('subtotal-small-change') || document.getElementById('subtotal-other');
    if (changeSubtotal) changeSubtotal.innerText = "0 Ks";

    const saveBtn = document.getElementById('save-recon-btn');
    if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }

    const expectedEl = document.getElementById('recon-expected');
    const expected = expectedEl ? parseInt(expectedEl.innerText.replace(/[^0-9]/g, '')) || 0 : 0;
    updateReconciliationDisplay(expected);
};

function updateReconciliationDisplay(expectedSales) {
    let banknotesTotal = 0;
    getDenominations().forEach(d => {
        banknotesTotal += (denominationCounts[d.value] || 0) * d.value;
    });

    const countedEl = document.getElementById('recon-counted');
    const varianceEl = document.getElementById('recon-variance');

    if (!isSmallChangeValid) {
        if (countedEl) countedEl.innerText = `${formatMoney(banknotesTotal)} (+ invalid)`;
        if (varianceEl) {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold";
            varianceEl.innerText = t('set.recon_invalid_input', 'Please enter a valid, non-negative whole-number MMK amount.');
        }
        return;
    }

    const totalCounted = banknotesTotal + smallChangeAmount;
    if (countedEl) countedEl.innerText = formatMoney(totalCounted);

    if (varianceEl) {
        const diff = totalCounted - expectedSales;
        if (diff === 0) {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold";
            varianceEl.innerText = t('set.recon_balanced', 'Balanced (0 Ks)');
        } else if (diff > 0) {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold";
            varianceEl.innerText = `+${formatMoney(diff)} (${t('set.recon_surplus', 'Surplus')})`;
        } else {
            varianceEl.className = "font-mono text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-bold";
            varianceEl.innerText = `-${formatMoney(Math.abs(diff))} (${t('set.recon_shortage', 'Shortage')})`;
        }
    }
}

function updateSavedStatusBadge(record) {
    const badgeEl = document.getElementById('recon-saved-indicator');
    const timeEl = document.getElementById('recon-saved-time');
    if (badgeEl && record) {
        badgeEl.classList.remove('hidden');
        if (timeEl && record.saved_at) {
            timeEl.innerText = new Date(record.saved_at).toLocaleTimeString();
        }
    }
}

window.saveReconciliation = async function() {
    if (!isSmallChangeValid) {
        showToast(t('set.recon_invalid_input', 'Please enter a valid, non-negative whole-number MMK amount.'), 'error');
        return;
    }

    const today = new Date().toISOString().split('T')[0];
    const expectedEl = document.getElementById('recon-expected');
    const expectedSales = expectedEl ? parseInt(expectedEl.innerText.replace(/[^0-9]/g, '')) || 0 : 0;

    let totalCounted = smallChangeAmount;
    const denoms = {};
    getDenominations().forEach(d => {
        const count = denominationCounts[d.value] || 0;
        denoms[d.value] = count;
        totalCounted += count * d.value;
    });

    const reconData = {
        date: today,
        denominations: denoms,
        small_change_amount: smallChangeAmount,
        total_counted: totalCounted,
        expected_sales: expectedSales,
        variance: totalCounted - expectedSales,
        saved_at: new Date().toISOString()
    };

    try {
        await callBackend('save_cash_reconciliation', JSON.stringify(reconData));
        showToast(t('set.recon_save_success', 'Cash reconciliation saved successfully!'));
        updateSavedStatusBadge(reconData);
        return reconData;
    } catch(e) {
        showToast("Failed to save reconciliation: " + e, "error");
        throw e;
    }
};

window.loadSavedReconciliation = async function(dateStr) {
    try {
        const date = dateStr || new Date().toISOString().split('T')[0];
        const res = await callBackend('get_cash_reconciliation', date);
        if (res) {
            const data = typeof res === 'string' ? JSON.parse(res) : res;
            if (data && data.denominations) {
                getDenominations().forEach(d => {
                    const count = data.denominations[d.value] || 0;
                    denominationCounts[d.value] = count;
                    const input = document.getElementById(`denom-${d.value}`);
                    if (input) input.value = count;
                    const subtotal = document.getElementById(`subtotal-${d.value}`);
                    if (subtotal) subtotal.innerText = formatMoney(count * d.value);
                });
            }
            if (data && typeof data.small_change_amount !== 'undefined') {
                smallChangeAmount = parseInt(data.small_change_amount) || 0;
                otherCashAmount = smallChangeAmount;
                const changeInput = document.getElementById('denom-small-change') || document.getElementById('denom-other');
                if (changeInput) {
                    changeInput.value = smallChangeAmount;
                    changeInput.classList.remove('border-rose-500', 'bg-rose-50', 'text-rose-900');
                    changeInput.classList.add('border-slate-300');
                }
                const errEl = document.getElementById('small-change-error');
                if (errEl) errEl.classList.add('hidden');
                const changeSubtotal = document.getElementById('subtotal-small-change') || document.getElementById('subtotal-other');
                if (changeSubtotal) changeSubtotal.innerText = formatMoney(smallChangeAmount);
            }
            isSmallChangeValid = true;
            const saveBtn = document.getElementById('save-recon-btn');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            const expectedEl = document.getElementById('recon-expected');
            const expected = expectedEl ? parseInt(expectedEl.innerText.replace(/[^0-9]/g, '')) || 0 : 0;
            updateReconciliationDisplay(expected);
            updateSavedStatusBadge(data);
            return data;
        } else {
            showToast("No saved reconciliation record found for " + date, "warning");
        }
    } catch(e) {
        console.warn("Could not load saved reconciliation:", e);
    }
    return null;
};

window.reopenReconciliation = window.loadSavedReconciliation;


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
            ${t('btn.processing', 'Selecting Destination & Backing Up...')}
        `;
    }

    try {
        const res = await callBackend('backup_database');
        if (res.cancelled) {
            return;
        }
        showToast((t('set.backup_title', 'Database backup created successfully!')) + "\n" + (res.file_path || 'saved'));
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
                ${t('set.backup_btn', 'Create Local Database Backup')}
            `;
        }
    }
};

window.confirmAndRestoreDatabase = function() {
    openConfirmModal(
        t('set.restore_title', 'Confirm Database Restore'),
        t('set.restore_desc', 'Restoring a database backup replaces all current records with the backup file data. Medisales will first create an automatic timestamped safety copy of your active database.'),
        () => {
            executeRestore();
        },
        {
            confirmText: t('btn.confirm', 'Proceed to Select File'),
            danger: true
        }
    );
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
            ${t('btn.processing', 'Restoring Database...')}
        `;
    }

    try {
        const res = await callBackend('restore_database');
        if (res.cancelled) {
            return;
        }
        showToast(t('set.restore_title', 'Database restored successfully!'));
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
                ${t('set.restore_btn', 'Restore From Backup File...')}
            `;
        }
    }
};
