// dashboard page - publish form and product management
(function () {
    'use strict';

    var form = document.getElementById('publish-form');
    var feedback = document.getElementById('publish-feedback');
    var container = document.getElementById('my-products-container');

    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // load my published products
    async function loadMyProducts() {
        if (!container) return;
        try {
            var res = await apiFetch('/api/products/my/');
        } catch (e) {
            console.error('loadMyProducts network error:', e);
            container.innerHTML = '<p class="text-danger">Network error loading products.</p>';
            return;
        }
        if (!res.ok) {
            console.error('loadMyProducts failed:', res.status, res.statusText);
            container.innerHTML = '<p class="text-danger">Failed to load products (status ' + res.status + ').</p>';
            return;
        }
        var products = await res.json();
        if (!products.length) {
            container.innerHTML = '<p class="text-muted">You haven\'t published any products yet.</p>';
            return;
        }

        container.innerHTML = '<div class="list-group">' +
            products.map(function (p) {
                var isSold = p.has_sold;
                var hasOrders = p.has_orders;
                var isDelisted = p.is_active === false;
                var imgHtml = p.image
                    ? '<img src="' + p.image + '" alt="" style="width:40px;height:40px;object-fit:cover;border-radius:4px" class="me-2">'
                    : '<div class="bg-light d-flex align-items-center justify-content-center me-2" style="width:40px;height:40px;border-radius:4px;font-size:10px;color:#999">No img</div>';
                var soldBadge = isSold ? '<span class="badge bg-success ms-2">Sold</span>' : '';
                if (isDelisted) soldBadge += '<span class="badge bg-danger ms-2">Delisted by Staff</span>';
                var actionBtns;
                if (isSold) {
                    actionBtns = '<span class="text-muted small"><i class="bi bi-lock" aria-hidden="true"></i> Sold</span>';
                } else if (hasOrders) {
                    // Has pending orders: allow edit but not delete
                    actionBtns = '<div class="btn-group btn-group-sm">' +
                            '<button class="btn btn-outline-primary edit-prod-btn" data-id="' + p.id + '" aria-label="Edit ' + escHtml(p.product_name) + '">' +
                                '<i class="bi bi-pencil" aria-hidden="true"></i>' +
                            '</button>' +
                            '<button class="btn btn-outline-secondary" disabled title="Cannot delete: has pending orders">' +
                                '<i class="bi bi-trash" aria-hidden="true"></i>' +
                            '</button>' +
                        '</div>';
                } else {
                    actionBtns = '<div class="btn-group btn-group-sm">' +
                            '<button class="btn btn-outline-primary edit-prod-btn" data-id="' + p.id + '" aria-label="Edit ' + escHtml(p.product_name) + '">' +
                                '<i class="bi bi-pencil" aria-hidden="true"></i>' +
                            '</button>' +
                            '<button class="btn btn-outline-danger delete-prod-btn" data-id="' + p.id + '" aria-label="Delete ' + escHtml(p.product_name) + '">' +
                                '<i class="bi bi-trash" aria-hidden="true"></i>' +
                            '</button>' +
                        '</div>';
                }
                return '<div class="list-group-item" data-product-id="' + p.id + '">' +
                    '<div class="d-flex justify-content-between align-items-start mb-1">' +
                        '<div class="d-flex align-items-center">' +
                            imgHtml +
                            '<div>' +
                                '<strong class="prod-name">' + escHtml(p.product_name) + '</strong>' +
                                '<span class="badge bg-secondary ms-2 prod-cat">' + escHtml(p.category) + '</span>' +
                                soldBadge +
                            '</div>' +
                        '</div>' +
                        actionBtns +
                    '</div>' +
                    '<small class="text-muted">&pound;' + Number(p.unit_price).toFixed(2) +
                    ' &middot; Stock: ' + p.stock_quantity + '</small>' +
                    (p.description ? '<br><small class="text-muted">' + escHtml(p.description) + '</small>' : '') +
                '</div>';
            }).join('') +
        '</div>';

        // Bind edit buttons
        container.querySelectorAll('.edit-prod-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = Number(btn.dataset.id);
                var p = products.find(function (x) { return x.id === pid; });
                if (p) openEditModal(p);
            });
        });

        // Bind delete buttons
        container.querySelectorAll('.delete-prod-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = Number(btn.dataset.id);
                if (confirm('Are you sure you want to delete this product?')) {
                    deleteProduct(pid);
                }
            });
        });
    }

    // edit product (inline modal)
    function openEditModal(p) {
        // Reuse the publish form for editing
        document.getElementById('pub-name').value = p.product_name;
        document.getElementById('pub-category').value = p.category;
        document.getElementById('pub-price').value = p.unit_price;
        document.getElementById('pub-stock').value = p.stock_quantity;
        document.getElementById('pub-desc').value = p.description || '';
        // Reset file input (can't set value for security reasons)
        var imageInput = document.getElementById('pub-image');
        if (imageInput) imageInput.value = '';

        var submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<i class="bi bi-save" aria-hidden="true"></i> Save Changes';

        // Temporarily replace submit handler
        var editHandler = async function (e) {
            e.preventDefault();
            var imageInput = document.getElementById('pub-image');
            var fd = new FormData();
            fd.append('productName', document.getElementById('pub-name').value.trim());
            fd.append('category', document.getElementById('pub-category').value);
            fd.append('unitPrice', parseFloat(document.getElementById('pub-price').value));
            fd.append('stockQuantity', parseInt(document.getElementById('pub-stock').value, 10));
            fd.append('description', document.getElementById('pub-desc').value.trim());
            if (imageInput && imageInput.files[0]) {
                fd.append('image', imageInput.files[0]);
            }
            var res = await apiFetch('/api/products/' + p.id + '/', {
                method: 'PATCH',
                body: fd
            });
            var data = await res.json();
            if (res.ok) {
                feedback.innerHTML = '<div class="alert alert-success">Product updated.</div>';
                form.reset();
                submitBtn.innerHTML = '<i class="bi bi-upload" aria-hidden="true"></i> Publish Product';
                form.removeEventListener('submit', editHandler);
                form.addEventListener('submit', publishHandler);
                loadMyProducts();
                loadAccountStatus();
            } else {
                feedback.innerHTML = '<div class="alert alert-danger">' + escHtml(data.error || 'Update failed.') + '</div>';
            }
        };

        // Remove publish listener temporarily
        form.removeEventListener('submit', publishHandler);
        form.addEventListener('submit', editHandler);

        // Restore on next publish form interaction
        var editMsg = 'Editing <strong>' + escHtml(p.product_name) +
            '</strong>. Submit to save changes or <a href="#" class="cancel-edit">cancel</a>.';
        if (p.image) {
            editMsg += '<br><img src="' + p.image + '" alt="Current image" style="width:60px;height:60px;object-fit:cover;border-radius:4px;margin-top:6px"> <small class="text-muted">Current image (upload new to replace)</small>';
        }
        feedback.innerHTML = '<div class="alert alert-info">' + editMsg + '</div>';

        feedback.querySelector('.cancel-edit').addEventListener('click', function (e) {
            e.preventDefault();
            form.reset();
            submitBtn.innerHTML = '<i class="bi bi-upload" aria-hidden="true"></i> Publish Product';
            form.removeEventListener('submit', editHandler);
            form.addEventListener('submit', publishHandler);
            feedback.innerHTML = '';
        });
    }

    // delete product
    async function deleteProduct(pid) {
        var res = await apiFetch('/api/products/' + pid + '/delete/', { method: 'DELETE' });
        if (res.ok) {
            loadMyProducts();
            loadAccountStatus();
        } else {
            var data = await res.json();
            alert(data.error || 'Delete failed.');
        }
    }

    // named publish handler so we can detach/reattach
    var publishHandler = async function (e) {
        e.preventDefault();
        var name = document.getElementById('pub-name').value.trim();
        var category = document.getElementById('pub-category').value;
        var price = document.getElementById('pub-price').value;
        var stock = document.getElementById('pub-stock').value || 1;
        var desc = document.getElementById('pub-desc').value.trim();
        var imageInput = document.getElementById('pub-image');

        if (!name || !price) {
            feedback.innerHTML = '<div class="alert alert-warning">Product name and price are required.</div>';
            return;
        }
        if (parseFloat(price) <= 0) {
            feedback.innerHTML = '<div class="alert alert-warning">Price must be greater than zero.</div>';
            return;
        }

        var fd = new FormData();
        fd.append('productName', name);
        fd.append('category', category);
        fd.append('unitPrice', parseFloat(price));
        fd.append('stockQuantity', parseInt(stock, 10));
        fd.append('description', desc);
        if (imageInput && imageInput.files[0]) {
            fd.append('image', imageInput.files[0]);
        }
        // console.log('form data:', data);

        var res = await apiFetch('/api/products/publish/', {
            method: 'POST',
            body: fd
        });
        var data = await res.json();

        if (res.ok) {
            feedback.innerHTML = '<div class="alert alert-success">' + escHtml(data.message) + '</div>';
            form.reset();
            loadMyProducts();
            loadAccountStatus();
        } else {
            feedback.innerHTML = '<div class="alert alert-danger">' + escHtml(data.error || 'Failed to publish.') + '</div>';
        }
    };

    // Replace the inline submit handler with the named one
    if (form) {
        // Remove the original handler by cloning
        var newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        form = newForm;
        feedback = document.getElementById('publish-feedback');
        form.addEventListener('submit', publishHandler);
    }

    // recent activity
    async function loadRecentActivity() {
        var el = document.getElementById('recent-activity');
        if (!el) return;
        var res = await apiFetch('/api/orders/my/');
        if (!res.ok) { el.innerHTML = '<p class="text-muted">Unable to load activity.</p>'; return; }
        var orders = await res.json();
        if (!orders.length) { el.innerHTML = '<p class="text-muted">No recent activity.</p>'; return; }
        var recent = orders.slice(0, 5);
        el.innerHTML = '<ul class="list-group list-group-flush">' +
            recent.map(function (o) {
                var badge = { pending: 'bg-warning text-dark', processing: 'bg-info', completed: 'bg-success', cancelled: 'bg-secondary' };
                return '<li class="list-group-item d-flex justify-content-between align-items-center px-0">' +
                    '<div><strong>Order #' + o.id + '</strong><br>' +
                    '<small class="text-muted">' + new Date(o.order_time).toLocaleDateString() +
                    ' &middot; &pound;' + Number(o.total_amount).toFixed(2) + '</small></div>' +
                    '<span class="badge ' + (badge[o.status] || 'bg-secondary') + '">' + o.status + '</span></li>';
            }).join('') + '</ul>';
    }

    // account status
    async function loadAccountStatus() {
        var el = document.getElementById('account-status');
        if (!el) return;
        var ordersRes = await apiFetch('/api/orders/my/');
        var prodsRes = await apiFetch('/api/products/my/');
        var favsRes = await apiFetch('/api/favorites/');
        var orders = ordersRes.ok ? await ordersRes.json() : [];
        var prods = prodsRes.ok ? await prodsRes.json() : [];
        var favs = favsRes.ok ? await favsRes.json() : [];

        var totalSpent = orders.reduce(function (s, o) { return s + Number(o.total_amount); }, 0);

        // Seller stats
        var statsRes = await apiFetch('/api/products/seller-stats/');
        var stats = statsRes.ok ? await statsRes.json() : { total_revenue: '0', total_items_sold: 0, total_orders: 0 };

        el.innerHTML =
            '<div class="row text-center">' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold text-primary">' + orders.length + '</div><small class="text-muted">Orders</small></div>' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold text-success">&pound;' + totalSpent.toFixed(2) + '</div><small class="text-muted">Spent</small></div>' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold text-info">' + prods.length + '</div><small class="text-muted">Published</small></div>' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold text-danger">' + favs.length + '</div><small class="text-muted">Favorites</small></div>' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold text-warning">&pound;' + Number(stats.total_revenue).toFixed(2) + '</div><small class="text-muted">Revenue</small></div>' +
                '<div class="col-6 col-md-2 mb-3"><div class="fs-4 fw-bold" style="color:#6f42c1">' + stats.total_items_sold + '</div><small class="text-muted">Items Sold</small></div>' +
            '</div>';
    }

    // load categories dynamically
    async function loadCategories() {
        var sel = document.getElementById('pub-category');
        if (!sel) return;
        var res = await apiFetch('/api/categories/');
        if (!res.ok) return;
        var cats = await res.json();
        sel.innerHTML = cats.map(function (c) {
            return '<option value="' + escHtml(c.name) + '">' + escHtml(c.name) + '</option>';
        }).join('');
    }

    loadCategories();
    loadMyProducts();
    loadRecentActivity();
    loadAccountStatus();
})();
