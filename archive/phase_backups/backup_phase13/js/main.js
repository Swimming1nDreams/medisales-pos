let backend = null;
let currentPage = 'dashboard';

const NAV_GROUPS = [
    {
        title: "OPERATIONS & DISPENSING",
        badge: "DISPENSING",
        items: [
            { id: 'dashboard', label: 'Dashboard', badge: '', icon: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>` },
            { id: 'sales', label: 'Sales / POS', badge: 'F1', icon: `<circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>` },
            { id: 'products', label: 'Products Catalog', badge: '', icon: `<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line>` },
            { id: 'inventory', label: 'Inventory & FEFO', badge: '', icon: `<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>` },
        ]
    },
    {
        title: "PROCUREMENT & EXPENSES",
        badge: "PROCUREMENT",
        items: [
            { id: 'purchases', label: 'Purchases & Receiving', badge: '', icon: `<line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>` },
            { id: 'suppliers', label: 'Suppliers Ledger', badge: '', icon: `<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>` },
            { id: 'expenses', label: 'Operating Expenses', badge: '', icon: `<line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>` },
        ]
    },
    {
        title: "FINANCE & SYSTEM",
        badge: "FINANCE",
        items: [
            { id: 'reports', label: 'Financial Reports', badge: '', icon: `<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>` },
            { id: 'settings', label: 'Settings & Database', badge: '', icon: `<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>` }
        ]
    }
];

const ALL_PAGES = NAV_GROUPS.flatMap(g => g.items.map(item => ({ ...item, groupBadge: g.badge })));

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    
    // Global hotkey: F1 opens Sales / POS
    window.addEventListener('keydown', (e) => {
        if (e.key === 'F1') {
            e.preventDefault();
            navigate('sales');
        }
    });

    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            backend = channel.objects.backend;
            backend.dataChanged.connect((dataType) => {
                if (dataType === currentPage || currentPage === 'dashboard' || currentPage === 'reports') {
                    loadPageData(currentPage);
                }
            });
            console.log("Connected to Python backend successfully.");
            navigate('dashboard');
        });
    } else {
        console.warn("Qt WebChannel not found. Running in mock mode?");
        navigate('dashboard');
    }
});

function initNavigation() {
    const container = document.getElementById('nav-container');
    container.innerHTML = NAV_GROUPS.map(g => `
        <div class="space-y-1">
            <div class="px-2.5 text-[9px] font-bold uppercase tracking-wider text-slate-500 select-none">${g.title}</div>
            <div class="space-y-0.5">
                ${g.items.map(p => `
                    <button id="nav-${p.id}" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 group" onclick="navigate('${p.id}')">
                        <div class="flex items-center gap-2.5 min-w-0">
                            <svg class="w-4 h-4 opacity-75 group-hover:opacity-100 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${p.icon}</svg>
                            <span class="truncate">${p.label}</span>
                        </div>
                        ${p.badge ? `<span class="text-[9px] font-mono font-bold bg-slate-800 text-teal-400 px-1.5 py-0.5 rounded border border-slate-700/80">${p.badge}</span>` : ''}
                    </button>
                `).join('')}
            </div>
        </div>
    `).join('');
}

const PAGE_SUBTITLES = {
    'dashboard': 'Store summary & financial performance',
    'sales': 'Cashier checkout & customer register',
    'products': 'Medicine & merchandise catalog',
    'inventory': 'Stock on hand & medicine FEFO batches',
    'purchases': 'Supplier invoices & goods receiving',
    'suppliers': 'Vendor accounts & settlement ledger',
    'expenses': 'Store overheads & operational costs',
    'reports': 'Financial statements & P&L analysis',
    'settings': 'Database storage & system utilities'
};

function updateNavState() {
    ALL_PAGES.forEach(p => {
        const el = document.getElementById(`nav-${p.id}`);
        if (!el) return;
        if (p.id === currentPage) {
            el.className = "w-full flex items-center justify-between px-3 py-2 text-xs font-semibold rounded bg-teal-800 text-white shadow-xs border-l-2 border-teal-400 group";
            
            const badgeEl = document.getElementById('page-badge');
            if (badgeEl) badgeEl.textContent = p.groupBadge || 'OPERATIONS';

            const titleEl = document.getElementById('page-title');
            if (titleEl) titleEl.textContent = p.label;

            const sub = document.getElementById('page-subtitle');
            if (sub) sub.textContent = PAGE_SUBTITLES[p.id] || '';
        } else {
            el.className = "w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 group";
        }
    });
}

function navigate(pageId) {
    currentPage = pageId;
    updateNavState();
    document.getElementById('header-actions').innerHTML = '';
    loadPageData(pageId);
}

function showLoading(show) {
    const el = document.getElementById('loading-overlay');
    if (!el) return;
    if (show) el.classList.remove('hidden');
    else el.classList.add('hidden');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    
    let bgStyle = 'bg-slate-900 text-white border-slate-700';
    let iconSvg = '<svg class="w-4 h-4 text-slate-300 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

    if (type === 'success') {
        bgStyle = 'bg-slate-900 text-white border-emerald-500/80';
        iconSvg = '<svg class="w-4 h-4 text-emerald-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    } else if (type === 'error') {
        bgStyle = 'bg-rose-950 text-rose-100 border-rose-500/80';
        iconSvg = '<svg class="w-4 h-4 text-rose-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
    } else if (type === 'warning') {
        bgStyle = 'bg-amber-950 text-amber-100 border-amber-500/80';
        iconSvg = '<svg class="w-4 h-4 text-amber-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
    }

    toast.className = `${bgStyle} px-3.5 py-2.5 rounded-md shadow-lg border flex items-center gap-2.5 transform transition-all duration-150 translate-y-0 opacity-100 pointer-events-auto max-w-sm text-xs font-medium`;
    toast.innerHTML = `
        ${iconSvg}
        <div class="flex-1 leading-snug">${message}</div>
        <button class="text-slate-400 hover:text-white p-0.5" onclick="this.parentElement.remove()">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-[-0.25rem]');
        setTimeout(() => toast.remove(), 200);
    }, 3500);
}

async function callBackend(methodName, ...args) {
    return new Promise((resolve, reject) => {
        if (!backend) {
            reject("Backend not connected");
            return;
        }
        backend[methodName](...args, (responseStr) => {
            try {
                const res = JSON.parse(responseStr);
                if (res.status === 'success') {
                    resolve(res.data);
                } else {
                    reject(res.message);
                }
            } catch (e) {
                reject("Failed to parse backend response");
            }
        });
    });
}

const formatMoney = (amount) => {
    const val = Math.round(Number(amount) || 0);
    return val.toLocaleString('en-US') + ' Ks';
};

const formatNumber = (val) => {
    return (Number(val) || 0).toLocaleString('en-US');
};

const escapeHtml = (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
};
window.escapeHtml = escapeHtml;

const formatExpiryBadge = (expiryDate) => {
    if (!expiryDate) return '<span class="badge badge-neutral">No Expiry</span>';
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const exp = new Date(expiryDate);
    const diffDays = Math.ceil((exp - today) / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) {
        return `<span class="badge badge-danger">Expired (${expiryDate})</span>`;
    } else if (diffDays <= 90) {
        return `<span class="badge badge-warning">${diffDays}d left (${expiryDate})</span>`;
    } else {
        return `<span class="badge badge-success">${expiryDate}</span>`;
    }
};

// === MODAL SYSTEM ===
let isSubmitting = false;

function openModal(title, htmlContent, onSave, options = {}) {
    const backdrop = document.getElementById('modal-backdrop');
    const content = document.getElementById('modal-content');
    const maxWidthClass = options.maxWidth || 'max-w-xl';
    
    content.className = `bg-white rounded-lg shadow-xl ${maxWidthClass} w-full transform scale-95 opacity-0 transition-all duration-150 max-h-[92vh] flex flex-col overflow-hidden border border-slate-200`;

    content.innerHTML = `
        <div class="px-5 py-3.5 border-b border-slate-200 flex justify-between items-center bg-slate-50/80 flex-shrink-0">
            <div>
                <h3 class="text-sm font-bold text-slate-900 leading-tight">${title}</h3>
                ${options.subtitle ? `<p class="text-[11px] text-slate-500 mt-0.5">${options.subtitle}</p>` : ''}
            </div>
            <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600 rounded p-1 hover:bg-slate-200/60 transition-colors" title="Close (Esc)">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        <div class="px-5 py-4 overflow-y-auto flex-1 bg-white space-y-4">
            ${htmlContent}
        </div>
        <div class="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50/80 flex-shrink-0">
            <button onclick="closeModal()" class="btn btn-secondary">${options.cancelText || 'Cancel'}</button>
            <button id="modal-save-btn" class="${options.saveBtnClass || 'btn-primary'}">${options.saveText || 'Save'}</button>
        </div>
    `;
    
    backdrop.classList.remove('hidden');
    setTimeout(() => {
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    }, 10);
    
    const saveBtn = document.getElementById('modal-save-btn');
    if (onSave) {
        saveBtn.onclick = async () => {
            if (isSubmitting) return;
            isSubmitting = true;
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = `
                <svg class="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg> Processing...
            `;
            saveBtn.disabled = true;
            try {
                await onSave();
                closeModal();
            } catch (e) {
                showToast(e, "error");
            } finally {
                isSubmitting = false;
                saveBtn.innerHTML = originalText;
                saveBtn.disabled = false;
            }
        };
    } else {
        saveBtn.classList.add('hidden');
    }
}

function openConfirmModal(title, message, onConfirm, options = {}) {
    const isDanger = options.danger !== false;
    const saveBtnClass = isDanger ? 'btn btn-danger' : 'btn btn-primary';
    const html = `
        <div class="flex items-start gap-3 py-1">
            <div class="w-9 h-9 rounded-full ${isDanger ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'bg-teal-50 text-teal-600 border border-teal-200'} flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${isDanger ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>' : '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>'}
                </svg>
            </div>
            <div>
                <p class="text-xs text-slate-700 leading-relaxed">${message}</p>
                ${options.subtext ? `<p class="text-[11px] text-slate-500 mt-2">${options.subtext}</p>` : ''}
            </div>
        </div>
    `;
    openModal(title, html, onConfirm, {
        maxWidth: 'max-w-md',
        saveText: options.confirmText || 'Confirm',
        saveBtnClass: saveBtnClass,
        cancelText: options.cancelText || 'Cancel'
    });
}

function closeModal() {
    const backdrop = document.getElementById('modal-backdrop');
    const content = document.getElementById('modal-content');
    if (!backdrop || !content) return;
    
    content.classList.remove('scale-100', 'opacity-100');
    content.classList.add('scale-95', 'opacity-0');
    
    setTimeout(() => {
        backdrop.classList.add('hidden');
        content.innerHTML = '';
        isSubmitting = false;
    }, 150);
}

// Global escape key to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const backdrop = document.getElementById('modal-backdrop');
        if (backdrop && !backdrop.classList.contains('hidden')) {
            closeModal();
        }
    }
});

async function loadPageData(pageId) {
    window._pageRendered = false;
    window._renderedPage = null;
    const contentArea = document.getElementById('content-area');
    showLoading(true);
    try {
        switch(pageId) {
            case 'dashboard': await renderDashboard(contentArea); break;
            case 'sales': await renderSales(contentArea); break;
            case 'products': await renderProducts(contentArea); break;
            case 'inventory': await renderInventory(contentArea); break;
            case 'purchases': await renderPurchases(contentArea); break;
            case 'suppliers': await renderSuppliers(contentArea); break;
            case 'expenses': await renderExpenses(contentArea); break;
            case 'reports': await renderReports(contentArea); break;
            case 'settings': await renderSettings(contentArea); break;
            default:
                contentArea.innerHTML = `<div class="p-8 text-center text-slate-500">Page ${pageId} under construction.</div>`;
        }
    } catch (e) {
        contentArea.innerHTML = `
            <div class="bg-rose-50 border border-rose-200 p-4 rounded-lg card">
                <div class="flex items-center">
                    <svg class="h-5 w-5 text-rose-600 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    <h3 class="text-sm font-bold text-rose-900">Unable to Load Page Data</h3>
                </div>
                <p class="mt-2 text-xs text-rose-700 leading-normal">${e}</p>
                <div class="mt-3">
                    <button class="btn btn-secondary text-xs" onclick="loadPageData('${pageId}')">Retry</button>
                </div>
            </div>`;
    } finally {
        showLoading(false);
        window._renderedPage = pageId;
        window._pageRendered = true;
    }
}
