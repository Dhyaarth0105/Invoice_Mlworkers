// Mobile Menu Toggle
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebar = document.querySelector('.sidebar');
const overlay = document.getElementById('sidebarOverlay');

function closeMobileMenu() {
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
}

function openMobileMenu() {
    if (sidebar) sidebar.classList.add('active');
    if (overlay) overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (sidebar && sidebar.classList.contains('active')) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    });
}

if (overlay) {
    overlay.addEventListener('click', closeMobileMenu);
}

// Close sidebar when clicking on a nav link (mobile)
document.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            closeMobileMenu();
        }
    });
});

// Close sidebar on window resize if larger than mobile
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        closeMobileMenu();
    }
});

// Animated Counter
document.querySelectorAll('.stat-value[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    const prefix = el.dataset.prefix || '';
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = prefix + Math.floor(current).toLocaleString('en-IN');
    }, 16);
});

// Invoice Item Calculations
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
    if (document.getElementById('subtotal')) {
        document.getElementById('subtotal').textContent = '₹' + subtotal.toLocaleString('en-IN');
    }
    if (document.getElementById('taxAmount')) {
        document.getElementById('taxAmount').textContent = '₹' + taxAmt.toLocaleString('en-IN');
    }
    if (document.getElementById('discountAmount')) {
        document.getElementById('discountAmount').textContent = '-₹' + discount.toLocaleString('en-IN');
    }
    if (document.getElementById('totalAmount')) {
        document.getElementById('totalAmount').textContent = '₹' + total.toLocaleString('en-IN');
    }
}

// Initialize calculations
document.querySelectorAll('.qty, .rate').forEach(input => {
    input.addEventListener('input', calculateTotals);
});

document.getElementById('taxInput')?.addEventListener('input', calculateTotals);
document.getElementById('discountInput')?.addEventListener('input', calculateTotals);


