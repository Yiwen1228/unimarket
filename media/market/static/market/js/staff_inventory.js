/**
 * staff_inventory.js — Staff inventory management page.
 */
(function () {
    'use strict';

    const tbody = document.getElementById('inventory-tbody');
    const feedback = document.getElementById('inventory-feedback');
    var allProducts = [];

    async function loadInventory() {
        const res = await apiFetch('/api/staff/inventory/');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-danger">Failed to load inventory.</td></tr>';
            return;
        }
        allProducts = await res.json();
        const products = allProducts;
        if (!products.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-muted">No products.</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(p => {
            var statusBadge = p.is_active
                ? '<span class="badge bg-success">Active</span>'
                : '<span class="badge bg-danger">Delisted</span>';
            var delistBtn = p.is_active
                ? `<button class="btn btn-sm btn-outline-danger btn-toggle-active" data-id="${p.id}"
                        aria-label="Delist ${escHtml(p.product_name)}">
                        <i class="bi bi-x-circle" aria-hidden="true"></i> Delist</button>`
                : `<button class="btn btn-sm btn-outline-success btn-toggle-active" data-id="${p.id}"
                        aria-label="Relist ${escHtml(p.product_name)}">
                        <i class="bi bi-check-circle" aria-hidden="true"></i> Relist</button>`;
            return `
        <tr class="${p.is_active ? '' : 'table-secondary'}">
            <td>${p.id}</td>
            <td>${escHtml(p.product_name)} ${statusBadge}</td>
            <td>${escHtml(p.category)}</td>
            <td>&pound;${Number(p.unit_price).toFixed(2)}</td>
            <td><span id="stock-${p.id}">${p.stock_quantity}</span></td>
            <td>
                <div class="d-flex align-items-center gap-1">
                    <label for="delta-${p.id}" class="visually-hidden">Quantity to adjust for ${escHtml(p.product_name)}</label>
                    <input type="number" id="delta-${p.id}" class="form-control form-control-sm"
                           value="1" min="1" style="width:70px" aria-label="Adjust quantity">
                    <button class="btn btn-sm btn-success btn-stock-in" data-id="${p.id}"
                            aria-label="Add stock for ${escHtml(p.product_name)}">
                        <i class="bi bi-plus" aria-hidden="true"></i> In
                    </button>
                    <button class="btn btn-sm btn-warning btn-stock-out" data-id="${p.id}"
                            aria-label="Remove stock for ${escHtml(p.product_name)}">
                        <i class="bi bi-dash" aria-hidden="true"></i> Out
                    </button>
                </div>
            </td>
            <td>${delistBtn}</td>
        </tr>`;
        }).join('');

        tbody.querySelectorAll('.btn-stock-in').forEach(btn => {
            btn.addEventListener('click', () => adjustStock(btn.dataset.id, 'in'));
        });
        tbody.querySelectorAll('.btn-stock-out').forEach(btn => {
            btn.addEventListener('click', () => adjustStock(btn.dataset.id, 'out'));
        });
        tbody.querySelectorAll('.btn-toggle-active').forEach(btn => {
            btn.addEventListener('click', () => toggleActive(btn.dataset.id));
        });
    }

    async function adjustStock(productId, mode) {
        const delta = parseInt(document.getElementById('delta-' + productId).value) || 1;
        const res = await apiFetch('/api/staff/inventory/' + productId + '/', {
            method: 'PATCH',
            body: JSON.stringify({ mode, delta }),
        });
        if (res.ok) {
            feedback.innerHTML = '<span class="text-success">Stock updated.</span>';
            loadInventory();
        } else {
            feedback.innerHTML = '<span class="text-danger">Failed to update stock.</span>';
        }
    }

    async function toggleActive(productId) {
        var product = allProducts.find(function (p) { return p.id == productId; });
        var action = product && product.is_active ? 'delist' : 'relist';
        if (!confirm('Are you sure you want to ' + action + ' this product?')) return;

        const res = await apiFetch('/api/staff/inventory/' + productId + '/toggle-active/', {
            method: 'PATCH',
        });
        if (res.ok) {
            var data = await res.json();
            feedback.innerHTML = '<span class="text-success">Product ' + (data.is_active ? 'relisted' : 'delisted') + '.</span>';
            loadInventory();
        } else {
            feedback.innerHTML = '<span class="text-danger">Failed to update product status.</span>';
        }
    }

    function escHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    /* ── CSV Export ─────────────────────────────────────── */
    var exportBtn = document.getElementById('export-inventory-csv');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            if (!allProducts.length) { alert('No inventory to export.'); return; }
            var csv = 'ID,Product,Category,Price,Stock,Status\n';
            allProducts.forEach(function (p) {
                csv += [p.id, '"' + p.product_name.replace(/"/g, '""') + '"',
                    p.category, p.unit_price, p.stock_quantity,
                    p.is_active ? 'Active' : 'Delisted'].join(',') + '\n';
            });
            var blob = new Blob([csv], { type: 'text/csv' });
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'inventory_export.csv';
            a.click();
        });
    }

    loadInventory();
})();
