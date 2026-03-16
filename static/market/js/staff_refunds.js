/**
 * staff_refunds.js — Staff refund request management.
 */
(function () {
    'use strict';

    var container = document.getElementById('refunds-container');
    var filterSelect = document.getElementById('refund-status-filter');

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
        var statusVal = filterSelect ? filterSelect.value : '';
        var url = '/api/staff/refunds/' + (statusVal ? '?status=' + statusVal : '');
        var res = await apiFetch(url);
        if (!res.ok) {
            container.innerHTML = '<p class="text-danger">Failed to load refund requests.</p>';
            return;
        }
        var refunds = await res.json();
        if (!refunds.length) {
            container.innerHTML = '<p class="text-muted">No refund requests found.</p>';
            return;
        }

        container.innerHTML = refunds.map(function (r) {
            var actions = '';
            if (r.status === 'pending') {
                actions = '<div class="mt-2 d-flex gap-2">' +
                    '<button class="btn btn-sm btn-success approve-btn" data-id="' + r.id + '" aria-label="Approve refund #' + r.id + '">' +
                        '<i class="bi bi-check-lg" aria-hidden="true"></i> Approve</button>' +
                    '<button class="btn btn-sm btn-danger reject-btn" data-id="' + r.id + '" aria-label="Reject refund #' + r.id + '">' +
                        '<i class="bi bi-x-lg" aria-hidden="true"></i> Reject</button>' +
                    '</div>';
            }
            return '<div class="card mb-3">' +
                '<div class="card-header d-flex justify-content-between align-items-center">' +
                    '<span><strong>Refund #' + r.id + '</strong> &mdash; Order #' + r.order_id +
                    ' &mdash; <span class="text-muted">' + escHtml(r.customer_username) + '</span></span>' +
                    '<span class="badge ' + badgeClass(r.status) + '">' + r.status + '</span>' +
                '</div>' +
                '<div class="card-body">' +
                    '<p class="mb-1"><strong>Product:</strong> ' + escHtml(r.product_name) + '</p>' +
                    '<p class="mb-1"><strong>Quantity:</strong> ' + r.quantity + '</p>' +
                    '<p class="mb-1"><strong>Unit Price:</strong> &pound;' + Number(r.unit_price).toFixed(2) + '</p>' +
                    (r.reason ? '<p class="mb-1"><strong>Reason:</strong> ' + escHtml(r.reason) + '</p>' : '') +
                    '<p class="small text-muted mb-0">Submitted: ' + new Date(r.created_time).toLocaleString() + '</p>' +
                    actions +
                '</div></div>';
        }).join('');

        // Attach approve/reject handlers
        container.querySelectorAll('.approve-btn').forEach(function (btn) {
            btn.addEventListener('click', function () { processRefund(btn.dataset.id, 'approved'); });
        });
        container.querySelectorAll('.reject-btn').forEach(function (btn) {
            btn.addEventListener('click', function () { processRefund(btn.dataset.id, 'rejected'); });
        });
    }

    async function processRefund(refundId, newStatus) {
        var res = await apiFetch('/api/staff/refunds/' + refundId + '/', {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            loadRefunds();
        } else {
            var data = await res.json();
            alert(data.error || 'Failed to process refund.');
        }
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', loadRefunds);
    }

    loadRefunds();
})();
