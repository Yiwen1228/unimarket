// cart module using localStorage
var Cart = (function () {
    'use strict';

    var STORAGE_KEY = 'unimarket_cart';

    function getItems() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        } catch (e) {
            return [];
        }
    }

    function saveItems(items) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    }

    function addItem(productId, productName, unitPrice, qty) {
        var items = getItems();
        var existing = items.find(function (c) { return c.productId === productId; });
        if (existing) {
            existing.qty += qty;
        } else {
            items.push({ productId: productId, productName: productName, unitPrice: unitPrice, qty: qty });
        }
        saveItems(items);
        renderCart();
    }

    function removeItem(index) {
        var items = getItems();
        items.splice(index, 1);
        saveItems(items);
        renderCart();
    }

    function clear() {
        localStorage.removeItem(STORAGE_KEY);
        renderCart();
    }

    function getCount() {
        return getItems().reduce(function (s, c) { return s + c.qty; }, 0);
    }

    // this works but could be cleaner
    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function renderCart() {
        var items = getItems();
        var badge = document.getElementById('cart-badge');
        var cartItemsEl = document.getElementById('cart-items');
        var cartTotalEl = document.getElementById('cart-total');
        var btnPlaceOrder = document.getElementById('btn-place-order');

        // Update badge everywhere
        if (badge) badge.textContent = getCount();

        // Only render full cart if elements exist (on pages with offcanvas)
        if (!cartItemsEl) return;

        if (btnPlaceOrder) btnPlaceOrder.disabled = items.length === 0;

        if (!items.length) {
            cartItemsEl.innerHTML = '<li class="list-group-item text-muted">Cart is empty.</li>';
            if (cartTotalEl) cartTotalEl.textContent = '\u00A30.00';
            return;
        }

        var total = 0;
        cartItemsEl.innerHTML = items.map(function (c, i) {
            var sub = c.unitPrice * c.qty;
            total += sub;
            return '<li class="list-group-item d-flex justify-content-between align-items-center">' +
                '<div><strong>' + escHtml(c.productName) + '</strong>' +
                '<br><small class="text-muted">&pound;' + c.unitPrice.toFixed(2) + ' &times; ' + c.qty + '</small></div>' +
                '<div class="d-flex align-items-center gap-2">' +
                '<span>&pound;' + sub.toFixed(2) + '</span>' +
                '<button class="btn btn-sm btn-outline-danger btn-remove-cart" data-index="' + i + '"' +
                ' aria-label="Remove ' + escHtml(c.productName) + ' from cart">' +
                '<i class="bi bi-trash" aria-hidden="true"></i></button>' +
                '</div></li>';
        }).join('');

        if (cartTotalEl) cartTotalEl.textContent = '\u00A3' + total.toFixed(2);

        cartItemsEl.querySelectorAll('.btn-remove-cart').forEach(function (btn) {
            btn.addEventListener('click', function () {
                removeItem(Number(btn.dataset.index));
            });
        });
    }

    async function placeOrder() {
        var items = getItems();
        if (!items.length) return;

        // Confirmation dialog
        var total = items.reduce(function (s, c) { return s + c.unitPrice * c.qty; }, 0);
        var msg = 'Place order for ' + items.length + ' item(s) totalling \u00A3' + total.toFixed(2) + '?';
        if (!confirm(msg)) return;

        var btnPlaceOrder = document.getElementById('btn-place-order');
        var orderFeedback = document.getElementById('order-feedback');

        if (btnPlaceOrder) btnPlaceOrder.disabled = true;
        if (orderFeedback) orderFeedback.textContent = 'Placing order...';

        var payload = items.map(function (c) {
            return { productId: c.productId, qty: c.qty };
        });

        var res = await apiFetch('/api/orders/', {
            method: 'POST',
            body: JSON.stringify({ items: payload }),
        });
        var data = await res.json();

        if (res.ok) {
            if (orderFeedback) orderFeedback.innerHTML = '<span class="text-success">Order placed successfully!</span>';
            clear();
        } else {
            if (orderFeedback) orderFeedback.innerHTML = '<span class="text-danger">' + escHtml(data.error) + '</span>';
            if (btnPlaceOrder) btnPlaceOrder.disabled = false;
        }
    }

    // Init: render cart on page load, bind place order button
    document.addEventListener('DOMContentLoaded', function () {
        renderCart();
        var btnPlaceOrder = document.getElementById('btn-place-order');
        if (btnPlaceOrder) {
            btnPlaceOrder.addEventListener('click', placeOrder);
        }
    });

    return {
        getItems: getItems,
        addItem: addItem,
        removeItem: removeItem,
        clear: clear,
        getCount: getCount,
        renderCart: renderCart,
    };
})();
