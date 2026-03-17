// my orders page
(function () {
    'use strict';

    var container = document.getElementById('orders-container');
    var orders = [];

    function badgeClass(status) {
        var map = { pending: 'badge-pending', processing: 'badge-processing', completed: 'badge-completed badge-finished', cancelled: 'badge-cancelled' };
        return map[status] || 'bg-secondary';
    }

    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    async function loadOrders() {
        var res = await apiFetch('/api/orders/my/');
        if (!res.ok) {
            container.innerHTML = '<p class="text-danger">Failed to load orders.</p>';
            return;
        }
        orders = await res.json();
        if (!orders.length) {
            container.innerHTML = '<p class="text-muted">You have no orders yet.</p>';
            return;
        }

        container.innerHTML = orders.map(function (o) {
            var showRefund = (o.status === 'completed');
            var showConfirm = (o.status === 'pending');

            /* Collect unique sellers from this order's items */
            var sellers = {};
            o.items.forEach(function (it) {
                if (it.seller_id && it.seller_name) {
                    sellers[it.seller_id] = it.seller_name;
                }
            });

            /* Build per-product chat buttons */
            var productSellers = {};
            o.items.forEach(function (it) {
                if (it.seller_id && it.seller_name) {
                    var key = it.seller_id + '_' + it.product;
                    if (!productSellers[key]) {
                        productSellers[key] = { sellerId: it.seller_id, sellerName: it.seller_name, productId: it.product, productName: it.product_name };
                    }
                }
            });
            var sellerChatBtns = Object.keys(productSellers).map(function (key) {
                var info = productSellers[key];
                return '<a href="/chat/?room=seller' + info.sellerId + 'p' + info.productId +
                    '&product=' + encodeURIComponent(info.productName) +
                    '&productId=' + info.productId + '" ' +
                    'class="btn btn-sm btn-outline-primary me-2 mb-1" ' +
                    'aria-label="Chat with ' + escHtml(info.sellerName) + ' about ' + escHtml(info.productName) + '">' +
                    '<i class="bi bi-chat-left-text" aria-hidden="true"></i> Chat with ' + escHtml(info.sellerName) +
                    '</a>';
            }).join('');

            var helpChatBtn = '<a href="/chat/?room=support" ' +
                'class="btn btn-sm btn-outline-info mb-1" ' +
                'aria-label="Chat with support about order ' + o.id + '">' +
                '<i class="bi bi-headset" aria-hidden="true"></i> Chat for Help' +
                '</a>';

            /* Confirm Receipt button for pending orders */
            var confirmBtn = showConfirm
                ? '<button class="btn btn-sm btn-success mb-1 me-2 confirm-receipt-btn" data-order-id="' + o.id + '" ' +
                  'aria-label="Confirm receipt of order ' + o.id + '">' +
                  '<i class="bi bi-check-circle" aria-hidden="true"></i> Confirm Receipt</button>'
                : '';

            /* Status display text */
            var statusText = o.status;
            if (o.status === 'completed') statusText = 'finished';

            return '<div class="card mb-3">' +
                '<div class="card-header d-flex justify-content-between align-items-center">' +
                    '<span><strong>Order #' + o.id + '</strong></span>' +
                    '<span class="badge ' + badgeClass(o.status) + '">' + statusText + '</span>' +
                '</div>' +
                '<div class="card-body">' +
                    '<p class="small text-muted mb-2">Placed: ' + new Date(o.order_time).toLocaleString() + '</p>' +
                    '<table class="table table-sm" aria-label="Items in order ' + o.id + '">' +
                        '<thead><tr><th scope="col">Product</th><th scope="col">Seller</th><th scope="col">Qty</th><th scope="col">Price</th>' +
                        (showRefund ? '<th scope="col">Action</th>' : '') +
                        '</tr></thead><tbody>' +
                        o.items.map(function (it) {
                            return '<tr><td>' + escHtml(it.product_name) + '</td>' +
                                '<td>' + (it.seller_name ? escHtml(it.seller_name) : '<span class="text-muted">Store</span>') + '</td>' +
                                '<td>' + it.quantity + '</td>' +
                                '<td>&pound;' + Number(it.unit_price).toFixed(2) + '</td>' +
                                (showRefund ? '<td><button class="btn btn-sm btn-outline-danger refund-btn" ' +
                                    'data-item-id="' + it.id + '" ' +
                                    'data-product-name="' + escHtml(it.product_name) + '" ' +
                                    'data-max-qty="' + it.quantity + '" ' +
                                    'aria-label="Request refund for ' + escHtml(it.product_name) + '">' +
                                    '<i class="bi bi-arrow-return-left" aria-hidden="true"></i> Refund</button></td>' : '') +
                                '</tr>';
                        }).join('') +
                        '</tbody></table>' +
                    '<p class="fw-bold mb-3">Total: &pound;' + Number(o.total_amount).toFixed(2) + '</p>' +
                    /* chat + confirm + print buttons */
                    '<div class="d-flex flex-wrap align-items-center">' +
                        confirmBtn +
                        sellerChatBtns +
                        helpChatBtn +
                        '<button class="btn btn-sm btn-outline-secondary mb-1 print-invoice-btn" data-order-id="' + o.id + '" aria-label="Print invoice for order ' + o.id + '">' +
                            '<i class="bi bi-printer" aria-hidden="true"></i> Print Invoice</button>' +
                    '</div>' +
                '</div></div>';
        }).join('');

        // Attach print invoice handlers
        container.querySelectorAll('.print-invoice-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var oid = Number(btn.dataset.orderId);
                var o = orders.find(function (x) { return x.id === oid; });
                if (o) printInvoice(o);
            });
        });

        // Attach refund button handlers
        container.querySelectorAll('.refund-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                openRefundModal(btn.dataset.itemId, btn.dataset.productName, btn.dataset.maxQty);
            });
        });

        // Attach confirm receipt button handlers
        container.querySelectorAll('.confirm-receipt-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var oid = Number(btn.dataset.orderId);
                if (confirm('Are you sure you have received this order? This will mark it as finished.')) {
                    confirmReceipt(oid, btn);
                }
            });
        });
    }

    async function confirmReceipt(orderId, btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split" aria-hidden="true"></i> Confirming...';
        var res = await apiFetch('/api/orders/' + orderId + '/confirm/', { method: 'PATCH' });
        var data = await res.json();
        if (res.ok) {
            loadOrders();
        } else {
            alert(data.error || 'Failed to confirm receipt.');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-circle" aria-hidden="true"></i> Confirm Receipt';
        }
    }

    function openRefundModal(itemId, productName, maxQty) {
        document.getElementById('refund-item-id').value = itemId;
        document.getElementById('refund-product-name').textContent = productName;
        var qtyInput = document.getElementById('refund-qty');
        qtyInput.value = maxQty;
        qtyInput.max = maxQty;
        document.getElementById('refund-reason').value = '';
        document.getElementById('refund-feedback').innerHTML = '';
        var modal = new bootstrap.Modal(document.getElementById('refundModal'));
        modal.show();
    }

    // Submit refund request
    var submitBtn = document.getElementById('refund-submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', async function () {
            var itemId = document.getElementById('refund-item-id').value;
            var qty = parseInt(document.getElementById('refund-qty').value, 10);
            var reason = document.getElementById('refund-reason').value.trim();
            var feedback = document.getElementById('refund-feedback');

            submitBtn.disabled = true;
            var res = await apiFetch('/api/refunds/', {
                method: 'POST',
                body: JSON.stringify({ orderItemId: parseInt(itemId, 10), quantity: qty, reason: reason })
            });
            var data = await res.json();
            if (res.ok) {
                feedback.innerHTML = '<div class="alert alert-success">' + escHtml(data.message) + '</div>';
                setTimeout(function () {
                    bootstrap.Modal.getInstance(document.getElementById('refundModal')).hide();
                    loadOrders();
                }, 1200);
            } else {
                feedback.innerHTML = '<div class="alert alert-danger">' + escHtml(data.error || 'Failed to submit.') + '</div>';
            }
            submitBtn.disabled = false;
        });
    }

    // print invoice
    function printInvoice(o) {
        var itemsHtml = o.items.map(function (it) {
            return '<tr><td>' + escHtml(it.product_name) + '</td>' +
                '<td>' + it.quantity + '</td>' +
                '<td>&pound;' + Number(it.unit_price).toFixed(2) + '</td>' +
                '<td>&pound;' + (Number(it.unit_price) * it.quantity).toFixed(2) + '</td></tr>';
        }).join('');

        var html = '<!DOCTYPE html><html><head><title>Invoice #' + o.id + '</title>' +
            '<style>body{font-family:Arial,sans-serif;margin:2rem;color:#333}' +
            'h1{font-size:1.5rem;margin-bottom:.5rem}' +
            'table{width:100%;border-collapse:collapse;margin-top:1rem}' +
            'th,td{border:1px solid #ccc;padding:.5rem;text-align:left}' +
            'th{background:#f5f5f5}.total{text-align:right;font-weight:bold;margin-top:1rem;font-size:1.1rem}' +
            '.header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #333;padding-bottom:.5rem;margin-bottom:1rem}' +
            '</style></head><body>' +
            '<div class="header"><div><h1>UofG UNIMarket</h1><p>University Supermarket</p></div>' +
            '<div><strong>Invoice #' + o.id + '</strong><br>' + new Date(o.order_time).toLocaleDateString() + '</div></div>' +
            '<p><strong>Status:</strong> ' + o.status + '</p>' +
            '<table><thead><tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Subtotal</th></tr></thead>' +
            '<tbody>' + itemsHtml + '</tbody></table>' +
            '<p class="total">Total: &pound;' + Number(o.total_amount).toFixed(2) + '</p>' +
            '<script>window.print();window.onafterprint=function(){window.close()}<\/script>' +
            '</body></html>';

        var win = window.open('', '_blank');
        win.document.write(html);
        win.document.close();
    }

    loadOrders();
})();
