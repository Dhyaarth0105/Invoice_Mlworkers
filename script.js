// Animated Counter
document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.dataset.target), prefix = el.dataset.prefix || '';
    const duration = 2000, increment = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) { current = target; clearInterval(timer); }
        el.textContent = prefix + Math.floor(current).toLocaleString('en-IN');
    }, 16);
});

// Revenue Chart
const ctx = document.getElementById('revenueChart').getContext('2d');
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
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', callback: v => '₹' + (v/1000) + 'k' } }
        },
        interaction: { intersect: false, mode: 'index' }
    }
});

// Modal
const modal = document.getElementById('invoiceModal');
const openBtn = document.getElementById('createInvoiceBtn');
const closeBtn = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');

openBtn.addEventListener('click', () => modal.classList.add('active'));
closeBtn.addEventListener('click', () => modal.classList.remove('active'));
cancelBtn.addEventListener('click', () => modal.classList.remove('active'));
modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

// Add Invoice Item
document.querySelector('.add-item-btn').addEventListener('click', () => {
    const container = document.querySelector('.invoice-items');
    const row = document.createElement('div');
    row.className = 'item-row';
    row.innerHTML = `<input type="text" placeholder="Item description"><input type="number" placeholder="Qty" class="qty"><input type="number" placeholder="Rate" class="rate"><span class="item-total">₹0</span><button class="remove-item"><i class="fas fa-trash"></i></button>`;
    container.appendChild(row);
    row.querySelector('.remove-item').addEventListener('click', () => { row.remove(); calculateTotals(); });
    row.querySelectorAll('.qty, .rate').forEach(input => input.addEventListener('input', calculateTotals));
});

// Calculate Totals
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

// Init event listeners
document.querySelectorAll('.qty, .rate').forEach(input => input.addEventListener('input', calculateTotals));
document.querySelectorAll('.remove-item').forEach(btn => btn.addEventListener('click', function() { this.closest('.item-row').remove(); calculateTotals(); }));
document.getElementById('taxInput')?.addEventListener('input', calculateTotals);
document.getElementById('discountInput')?.addEventListener('input', calculateTotals);

// Chart filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelector('.filter-btn.active')?.classList.remove('active');
        this.classList.add('active');
    });
});

// Quick action buttons
document.querySelectorAll('.quick-action-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        if (this.querySelector('span').textContent === 'Create Invoice') modal.classList.add('active');
    });
});

// Nav items
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector('.nav-item.active')?.classList.remove('active');
        this.classList.add('active');
    });
});

// Table row hover effect & action buttons
document.querySelectorAll('.invoice-table tbody tr').forEach(row => {
    row.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const icon = this.querySelector('i').className;
            if (icon.includes('eye')) alert('Viewing invoice details...');
            else if (icon.includes('download')) alert('Downloading invoice PDF...');
        });
    });
});
