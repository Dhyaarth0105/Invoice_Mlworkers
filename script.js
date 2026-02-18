// ========== ANIMATED COUNTER ==========
document.querySelectorAll('.stat-value[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target), prefix = el.dataset.prefix || '';
    const duration = 2000, increment = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) { current = target; clearInterval(timer); }
        el.textContent = prefix + Math.floor(current).toLocaleString('en-IN');
    }, 16);
});

// ========== REVENUE CHART ==========
const ctx = document.getElementById('revenueChart')?.getContext('2d');
if (ctx) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.5)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Revenue',
                data: [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                borderColor: '#6366f1',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', callback: v => '₹' + (v / 1000) + 'k' } }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

// ========== REPORT CHART ==========
const reportCtx = document.getElementById('reportChart')?.getContext('2d');
if (reportCtx) {
    new Chart(reportCtx, {
        type: 'bar',
        data: {
            labels: ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'],
            datasets: [{
                label: 'Revenue',
                data: [65000, 78000, 85000, 72000, 95000, 112000],
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                borderColor: '#6366f1',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#64748b' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', callback: v => '₹' + (v / 1000) + 'k' } }
            }
        }
    });
}

// ========== MODALS ==========
const modal = document.getElementById('invoiceModal');
const poModal = document.getElementById('poModal');

// Invoice Modal
document.getElementById('createInvoiceBtn')?.addEventListener('click', () => modal.classList.add('active'));
document.getElementById('newInvoiceBtnAlt')?.addEventListener('click', () => modal.classList.add('active'));
document.getElementById('quickNewInvoice')?.addEventListener('click', () => modal.classList.add('active'));
document.getElementById('closeModal')?.addEventListener('click', () => modal.classList.remove('active'));
document.getElementById('cancelBtn')?.addEventListener('click', () => modal.classList.remove('active'));
modal?.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

// PO Modal
document.getElementById('addPOBtn')?.addEventListener('click', () => poModal.classList.add('active'));
document.getElementById('closePOModal')?.addEventListener('click', () => poModal.classList.remove('active'));
document.getElementById('cancelPOBtn')?.addEventListener('click', () => poModal.classList.remove('active'));
poModal?.addEventListener('click', e => { if (e.target === poModal) poModal.classList.remove('active'); });

// ========== SAVE PO ==========
document.getElementById('savePOBtn')?.addEventListener('click', () => {
    const poNum = document.getElementById('poNumber').value;
    const mainNum = document.getElementById('poMainLineNum').value;
    const mainDesc = document.getElementById('poMainLineDesc').value;
    const subNum = document.getElementById('poSublineNum').value;
    const subDesc = document.getElementById('poSublineDesc').value;
    const qty = document.getElementById('poQty').value;
    const uom = document.getElementById('poUOM').value;

    if (!poNum || !mainDesc || !subDesc) {
        alert('Please fill in all required fields');
        return;
    }

    const table = document.getElementById('poTableBody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td data-label="PO Number"><span class="invoice-id">${poNum}</span></td>
        <td data-label="Main Line #">${mainNum}</td>
        <td data-label="Main Line Desc">${mainDesc}</td>
        <td data-label="Subline #">${subNum}</td>
        <td data-label="Subline Desc">${subDesc}</td>
        <td data-label="Qty">${qty}</td>
        <td data-label="UOM">${uom}</td>
        <td data-label="Actions" class="actions">
            <button class="action-btn"><i class="fas fa-edit"></i></button>
            <button class="action-btn"><i class="fas fa-trash"></i></button>
        </td>
    `;
    table.appendChild(row);

    // Add to invoice dropdown
    const poSelect = document.getElementById('invoicePOSelect');
    const option = document.createElement('option');
    option.value = poNum;
    option.textContent = `${poNum} - ${mainDesc}`;
    poSelect.appendChild(option);

    poModal.classList.remove('active');
    document.getElementById('poForm').reset();
    alert('PO Saved Successfully!');
});

// ========== SIDEBAR / MOBILE MENU ==========
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebar = document.querySelector('.sidebar');
const overlay = document.getElementById('sidebarOverlay');

mobileMenuBtn?.addEventListener('click', () => {
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
});

overlay?.addEventListener('click', () => {
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
});

// ========== PAGE NAVIGATION ==========
function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.page-view').forEach(v => v.classList.remove('active'));

    // Show selected view
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }

    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
    if (activeNav) activeNav.classList.add('active');

    // Update header
    const titles = {
        'dashboard': { title: 'Dashboard', subtitle: "Welcome back! Here's your business overview." },
        'manage-po': { title: 'Manage Purchase Orders', subtitle: 'Add and manage your Purchase Orders. These are used when creating invoices.' },
        'uom-master': { title: 'UOM Master', subtitle: 'Manage Units of Measurement (KG, PCS, etc.)' },
        'invoices': { title: 'Invoices', subtitle: 'View, create and manage all your invoices.' },
        'clients': { title: 'Clients', subtitle: 'Manage your client database and contact information.' },
        'companies': { title: 'Companies', subtitle: 'Manage related companies and organizations.' },
        'products': { title: 'Products & Services', subtitle: 'Manage your product catalog and pricing.' },
        'reports': { title: 'Reports & Analytics', subtitle: 'Business insights and financial reports.' },
        'settings': { title: 'Settings', subtitle: 'Configure your company and invoice preferences.' }
    };
    const pageInfo = titles[viewName] || { title: viewName, subtitle: '' };
    document.querySelector('.page-title').textContent = pageInfo.title;
    document.querySelector('.page-subtitle').textContent = pageInfo.subtitle;

    // Close sidebar on mobile
    if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    }
}

// Nav item clicks
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        const view = this.getAttribute('data-view');
        if (view) switchView(view);
    });
});

// Quick action clicks
document.querySelectorAll('.quick-action-btn[data-view]').forEach(btn => {
    btn.addEventListener('click', function () {
        const view = this.getAttribute('data-view');
        if (view) switchView(view);
    });
});

// View All links
document.querySelectorAll('.view-all[data-view]').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const view = this.getAttribute('data-view');
        if (view) switchView(view);
    });
});

// ========== INVOICE ITEM MANAGEMENT ==========
document.querySelector('.add-item-btn')?.addEventListener('click', () => {
    const container = document.querySelector('.invoice-items');
    const row = document.createElement('div');
    row.className = 'item-row';
    row.innerHTML = `<input type="text" placeholder="Item description"><input type="number" placeholder="Qty" class="qty"><input type="number" placeholder="Rate" class="rate"><span class="item-total">₹0</span><button class="remove-item"><i class="fas fa-trash"></i></button>`;
    container.appendChild(row);
    row.querySelector('.remove-item').addEventListener('click', () => { row.remove(); calculateTotals(); });
    row.querySelectorAll('.qty, .rate').forEach(input => input.addEventListener('input', calculateTotals));
});

function calculateTotals() {
    let subtotal = 0;
    document.querySelectorAll('.item-row').forEach(row => {
        const qty = parseFloat(row.querySelector('.qty')?.value) || 0;
        const rate = parseFloat(row.querySelector('.rate')?.value) || 0;
        const total = qty * rate;
        const totalEl = row.querySelector('.item-total');
        if (totalEl) totalEl.textContent = '₹' + total.toLocaleString('en-IN');
        subtotal += total;
    });
    const tax = parseFloat(document.getElementById('taxInput')?.value) || 0;
    const discount = parseFloat(document.getElementById('discountInput')?.value) || 0;
    const taxAmt = subtotal * tax / 100;
    const total = subtotal + taxAmt - discount;
    document.getElementById('subtotal').textContent = '₹' + subtotal.toLocaleString('en-IN');
    document.getElementById('taxAmount').textContent = '₹' + taxAmt.toLocaleString('en-IN');
    document.getElementById('discountAmount').textContent = '-₹' + discount.toLocaleString('en-IN');
    document.getElementById('totalAmount').textContent = '₹' + total.toLocaleString('en-IN');
}

// Init event listeners for existing items
document.querySelectorAll('.qty, .rate').forEach(input => input.addEventListener('input', calculateTotals));
document.querySelectorAll('.remove-item').forEach(btn => btn.addEventListener('click', function () { this.closest('.item-row').remove(); calculateTotals(); }));
document.getElementById('taxInput')?.addEventListener('input', calculateTotals);
document.getElementById('discountInput')?.addEventListener('input', calculateTotals);

// Chart filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelector('.filter-btn.active')?.classList.remove('active');
        this.classList.add('active');
    });
});

// Table action buttons
document.querySelectorAll('.invoice-table tbody tr').forEach(row => {
    row.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            const icon = this.querySelector('i').className;
            if (icon.includes('eye')) alert('Viewing details...');
            else if (icon.includes('download')) alert('Downloading PDF...');
            else if (icon.includes('print')) alert('Preparing print view...');
            else if (icon.includes('edit')) alert('Opening edit form...');
            else if (icon.includes('trash')) alert('Confirm delete?');
        });
    });
});
