/**
 * staff_orders.js — Staff order management page.
 */
(function () {
    'use strict';

    const tbody = document.getElementById('orders-tbody');
    const feedback = document.getElementById('order-feedback');
    var allOrders = [];

    function badgeClass(status) {
        const map = { pending: 'badge-pending', processing: 'badge-processing', completed: 'badge-completed', cancelled: 'badge-cancelled' };
        return map[status] || 'bg-secondary';
    }

    async function loadOrders() {
        const res = await apiFetch('/api/staff/orders/');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-danger">Failed to load orders.</td></tr>';
            return;
        }
        allOrders = await res.json();
        const orders = allOrders;
        if (!orders.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-muted">No orders yet.</td></tr>';
            return;
        }

        tbody.innerHTML = orders.map(o => `
        <tr>
            <td>${o.id}</td>
            <td>${escHtml(o.customer_username)}</td>
            <td>${o.items.map(it => escHtml(it.product_name) + ' x' + it.quantity).join(', ')}</td>
            <td>&pound;${Number(o.total_amount).toFixed(2)}</td>
            <td>${new Date(o.order_time).toLocaleString()}</td>
            <td><span class="badge ${badgeClass(o.status)}">${o.status}</span></td>
            <td>
                <label for="status-${o.id}" class="visually-hidden">Update status for order ${o.id}</label>
                <select id="status-${o.id}" class="form-select form-select-sm status-select" data-id="${o.id}"
                        aria-label="Change status for order ${o.id}">
                    <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>Pending</option>
                    <option value="processing" ${o.status === 'processing' ? 'selected' : ''}>Processing</option>
                    <option value="completed" ${o.status === 'completed' ? 'selected' : ''}>Completed</option>
                    <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
            </td>
        </tr>`).join('');

        tbody.querySelectorAll('.status-select').forEach(sel => {
            sel.addEventListener('change', () => updateStatus(sel));
        });
    }

    async function updateStatus(sel) {
        const orderId = sel.dataset.id;
        const newStatus = sel.value;
        const res = await apiFetch('/api/staff/orders/' + orderId + '/', {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus }),
        });
        if (res.ok) {
            feedback.innerHTML = '<span class="text-success">Order #' + orderId + ' updated.</span>';
            loadOrders();
        } else {
            feedback.innerHTML = '<span class="text-danger">Failed to update order.</span>';
        }
    }

    function escHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    /* ── CSV Export ─────────────────────────────────────── */
    var exportBtn = document.getElementById('export-orders-csv');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            if (!allOrders.length) { alert('No orders to export.'); return; }
            var csv = 'Order #,Customer,Items,Total,Date,Status\n';
            allOrders.forEach(function (o) {
                var items = o.items.map(function (it) { return it.product_name + ' x' + it.quantity; }).join('; ');
                csv += [o.id, o.customer_username, '"' + items.replace(/"/g, '""') + '"',
                    o.total_amount, new Date(o.order_time).toLocaleString(), o.status].join(',') + '\n';
            });
            var blob = new Blob([csv], { type: 'text/csv' });
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'orders_export.csv';
            a.click();
        });
    }

    loadOrders();
})();
