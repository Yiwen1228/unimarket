/**
 * refunds.js — Customer "My Refunds" page.
 */
(function () {
    'use strict';

    var container = document.getElementById('refunds-container');

    function badgeClass(status) {
        var map = { pending: 'badge-pending', approved: 'badge-completed', rejected: 'badge-cancelled' };
        return map[status] || 'bg-secondary';
    }

    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    async function loadRefunds() {
        var res = await apiFetch('/api/refunds/my/');
        if (!res.ok) {
            container.innerHTML = '<p class="text-danger">Failed to load refund requests.</p>';
            return;
        }
        var refunds = await res.json();
        if (!refunds.length) {
            container.innerHTML = '<p class="text-muted">You have no refund requests.</p>';
            return;
        }

        container.innerHTML = refunds.map(function (r) {
            return '<div class="card mb-3">' +
                '<div class="card-header d-flex justify-content-between align-items-center">' +
                    '<span><strong>Refund #' + r.id + '</strong> &mdash; Order #' + r.order_id + '</span>' +
                    '<span class="badge ' + badgeClass(r.status) + '">' + r.status + '</span>' +
                '</div>' +
                '<div class="card-body">' +
                    '<p class="mb-1"><strong>Product:</strong> ' + escHtml(r.product_name) + '</p>' +
                    '<p class="mb-1"><strong>Quantity:</strong> ' + r.quantity + '</p>' +
                    '<p class="mb-1"><strong>Unit Price:</strong> &pound;' + Number(r.unit_price).toFixed(2) + '</p>' +
                    (r.reason ? '<p class="mb-1"><strong>Reason:</strong> ' + escHtml(r.reason) + '</p>' : '') +
                    '<p class="small text-muted mb-0">Submitted: ' + new Date(r.created_time).toLocaleString() + '</p>' +
                '</div></div>';
        }).join('');
    }

    loadRefunds();
})();
