/**
 * products.js — Product listing, search, detail view, and favorites toggle (AJAX).
 * Uses global Cart module from cart.js for cart operations.
 */
(function () {
    'use strict';

    // ── State ───────────────────────────────────────────────
    var allProducts = [];
    var favoriteIds = new Set();
    var selectedProduct = null;

    var grid = document.getElementById('product-grid');
    var searchInput = document.getElementById('product-search');
    var categoryFilter = document.getElementById('category-filter');
    var detailPanel = document.getElementById('product-detail');

    // ── Load data ───────────────────────────────────────────
    var currentPage = 1;
    var totalCount = 0;
    var pageSize = 50;

    async function loadProducts(search, category, page) {
        search = search || '';
        category = category || '';
        page = page || 1;
        currentPage = page;
        var url = '/api/products/?page=' + page + '&page_size=' + pageSize + '&';
        if (search) url += 'search=' + encodeURIComponent(search) + '&';
        if (category) url += 'category=' + encodeURIComponent(category);
        var res = await apiFetch(url);
        var data = await res.json();
        allProducts = data.results || data;
        totalCount = data.count || allProducts.length;
        renderProducts(allProducts);
        renderPagination();
        populateCategories();
    }

    async function loadFavorites() {
        var res = await apiFetch('/api/favorites/');
        if (res.ok) {
            var data = await res.json();
            favoriteIds = new Set(data.map(function (f) { return f.product; }));
        }
    }

    var categoriesLoaded = false;
    async function populateCategories() {
        if (categoriesLoaded) return;
        var current = categoryFilter.value;
        try {
            var res = await apiFetch('/api/categories/');
            if (res.ok) {
                var cats = await res.json();
                categoryFilter.innerHTML = '<option value="">All Categories</option>';
                cats.forEach(function (c) {
                    var opt = document.createElement('option');
                    opt.value = c.name;
                    opt.textContent = c.name;
                    if (c.name === current) opt.selected = true;
                    categoryFilter.appendChild(opt);
                });
                categoriesLoaded = true;
                return;
            }
        } catch (e) { /* fallback below */ }
        // Fallback: derive from loaded products
        var names = [...new Set(allProducts.map(function (p) { return p.category; }))].sort();
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        names.forEach(function (c) {
            var opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            if (c === current) opt.selected = true;
            categoryFilter.appendChild(opt);
        });
    }

    // ── Render product grid ─────────────────────────────────
    function renderProducts(products) {
        if (!products.length) {
            grid.innerHTML = '<p class="text-muted col">No products found.</p>';
            return;
        }
        grid.innerHTML = products.map(function (p) {
            var isFav = favoriteIds.has(p.id);
            return '<div class="col-sm-6 col-md-4 col-lg-3" role="listitem">' +
                '<div class="card product-card h-100 product-select-card" data-id="' + p.id + '" style="cursor:pointer">' +
                (p.image ? '<img src="' + p.image + '" class="card-img-top" alt="' + escHtml(p.product_name) + '" style="height:160px;object-fit:cover">' : '<div class="product-img-placeholder">Product</div>') +
                '<div class="card-body d-flex flex-column">' +
                '<div class="d-flex justify-content-between align-items-start">' +
                '<h2 class="h6 card-title mb-1">' + escHtml(p.product_name) + '</h2>' +
                '<button class="btn-fav ' + (isFav ? 'active' : '') + '"' +
                ' data-id="' + p.id + '"' +
                ' aria-label="' + (isFav ? 'Remove from favorites' : 'Add to favorites') + '"' +
                ' aria-pressed="' + isFav + '">' +
                '<i class="bi ' + (isFav ? 'bi-heart-fill' : 'bi-heart') + '" aria-hidden="true"></i>' +
                '</button></div>' +
                '<span class="badge bg-secondary mb-2">' + escHtml(p.category) + '</span>' +
                '<p class="fw-bold mb-1">&pound;' + Number(p.unit_price).toFixed(2) + '</p>' +
                '<p class="small text-muted mb-1">Stock: ' + p.stock_quantity + '</p>' +
                (p.seller_name ? '<p class="small text-muted mb-0"><i class="bi bi-person" aria-hidden="true"></i> ' + escHtml(p.seller_name) + '</p>' : '<p class="small text-muted mb-0"><i class="bi bi-shop" aria-hidden="true"></i> UNIMarket Store</p>') +
                '</div></div></div>';
        }).join('');

        // Bind favorite buttons
        grid.querySelectorAll('.btn-fav').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                toggleFavorite(btn);
            });
        });

        // Bind card click to show detail
        grid.querySelectorAll('.product-select-card').forEach(function (card) {
            card.addEventListener('click', function () {
                var pid = Number(card.dataset.id);
                showDetail(pid);
            });
        });
    }

    // ── Product detail view ─────────────────────────────────
    function showDetail(productId) {
        var p = allProducts.find(function (x) { return x.id === productId; });
        if (!p) return;
        selectedProduct = p;

        var detailImg = document.getElementById('detail-img');
        if (detailImg && p.image) {
            detailImg.outerHTML = '<img src="' + p.image + '" id="detail-img" class="img-fluid rounded mb-3" alt="' + escHtml(p.product_name) + '">';
        } else if (detailImg && !detailImg.tagName.match(/DIV/i)) {
            detailImg.src = p.image || '';
        }
        document.getElementById('detail-name').textContent = p.product_name;
        document.getElementById('detail-price').textContent = '\u00A3' + Number(p.unit_price).toFixed(2);
        document.getElementById('detail-desc').textContent = p.description || (p.category + ' product available at UofG UNIMarket.');
        document.getElementById('detail-category').textContent = 'Category: ' + p.category;
        document.getElementById('detail-stock').textContent = 'In stock: ' + p.stock_quantity;
        var sellerEl = document.getElementById('detail-seller');
        if (sellerEl) sellerEl.textContent = 'Seller: ' + (p.seller_name || 'UNIMarket Store');
        var chatBtn = document.getElementById('detail-chat-btn');
        if (chatBtn) {
            var isOwnProduct = (typeof CURRENT_CUSTOMER_ID !== 'undefined') && p.seller === CURRENT_CUSTOMER_ID;
            if (isOwnProduct) {
                // Disable button with tooltip instead of hiding
                chatBtn.removeAttribute('href');
                chatBtn.classList.add('disabled');
                chatBtn.style.opacity = '0.5';
                chatBtn.style.cursor = 'not-allowed';
                chatBtn.style.pointerEvents = 'auto';
                chatBtn.setAttribute('tabindex', '-1');
                chatBtn.setAttribute('aria-disabled', 'true');
                chatBtn.setAttribute('title', 'You cannot chat with yourself');
                chatBtn.setAttribute('data-bs-toggle', 'tooltip');
                chatBtn.setAttribute('data-bs-placement', 'top');
                chatBtn.innerHTML = '<i class="bi bi-chat-dots" aria-hidden="true"></i> Chat with ' + escHtml(p.seller_name || 'Seller');
                // Initialize Bootstrap tooltip
                if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                    new bootstrap.Tooltip(chatBtn);
                }
                chatBtn.onclick = function (e) {
                    e.preventDefault();
                    alert('You cannot chat with yourself.');
                };
            } else {
                chatBtn.classList.remove('disabled');
                chatBtn.style.opacity = '';
                chatBtn.style.cursor = '';
                chatBtn.style.pointerEvents = '';
                chatBtn.removeAttribute('tabindex');
                chatBtn.removeAttribute('aria-disabled');
                chatBtn.removeAttribute('title');
                chatBtn.removeAttribute('data-bs-toggle');
                chatBtn.onclick = null;
                var chatUrl = p.seller
                    ? '/chat/?room=seller' + p.seller + 'p' + p.id + '&product=' + encodeURIComponent(p.product_name) + '&productId=' + p.id
                    : '/chat/?room=support';
                chatBtn.href = chatUrl;
                chatBtn.innerHTML = '<i class="bi bi-chat-dots" aria-hidden="true"></i> ' +
                    (p.seller_name ? 'Chat with ' + escHtml(p.seller_name) : 'Chat with Support');
            }
        }
        document.getElementById('detail-qty').value = 1;
        document.getElementById('detail-qty').max = p.stock_quantity;

        // Disable Add to Cart for own products (same style as Chat with)
        var addCartBtn = document.getElementById('detail-add-cart');
        if (addCartBtn) {
            var isOwnProduct = (typeof CURRENT_CUSTOMER_ID !== 'undefined') && p.seller === CURRENT_CUSTOMER_ID;
            if (isOwnProduct) {
                addCartBtn.classList.add('disabled');
                addCartBtn.style.opacity = '0.5';
                addCartBtn.style.cursor = 'not-allowed';
                addCartBtn.setAttribute('title', 'You cannot purchase your own product');
                addCartBtn.setAttribute('data-bs-toggle', 'tooltip');
                addCartBtn.setAttribute('data-bs-placement', 'top');
                if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                    new bootstrap.Tooltip(addCartBtn);
                }
            } else {
                addCartBtn.classList.remove('disabled');
                addCartBtn.style.opacity = '';
                addCartBtn.style.cursor = '';
                addCartBtn.removeAttribute('title');
                addCartBtn.removeAttribute('data-bs-toggle');
            }
        }

        // Favorite button state
        var favBtn = document.getElementById('detail-fav-btn');
        var isFav = favoriteIds.has(p.id);
        favBtn.innerHTML = '<i class="bi ' + (isFav ? 'bi-heart-fill' : 'bi-heart') + '" aria-hidden="true"></i> ' +
            (isFav ? 'Remove from Favorites' : 'Add to Favorites');
        favBtn.className = isFav ? 'btn btn-danger btn-lg' : 'btn btn-dark btn-lg';

        // Related products
        renderRelated(p);

        detailPanel.classList.remove('d-none');
        detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ── Detail panel event bindings ─────────────────────────
    document.getElementById('detail-add-cart').addEventListener('click', function () {
        if (!selectedProduct) return;
        // Prevent purchasing own product
        var isOwn = (typeof CURRENT_CUSTOMER_ID !== 'undefined') && selectedProduct.seller === CURRENT_CUSTOMER_ID;
        if (isOwn) {
            alert('You cannot purchase your own product.');
            return;
        }
        var qty = Math.max(1, parseInt(document.getElementById('detail-qty').value) || 1);
        var maxStock = selectedProduct.stock_quantity || 0;
        if (qty > maxStock) {
            alert('Cannot add more than ' + maxStock + ' items (available stock).');
            document.getElementById('detail-qty').value = maxStock;
            return;
        }
        if (maxStock <= 0) {
            alert('This product is out of stock.');
            return;
        }
        Cart.addItem(selectedProduct.id, selectedProduct.product_name, Number(selectedProduct.unit_price), qty);
    });

    // Enforce stock limit on quantity input change
    document.getElementById('detail-qty').addEventListener('change', function () {
        if (!selectedProduct) return;
        var val = parseInt(this.value) || 1;
        var maxStock = selectedProduct.stock_quantity || 0;
        if (val > maxStock) { this.value = maxStock; }
        if (val < 1) { this.value = 1; }
    });

    document.getElementById('detail-fav-btn').addEventListener('click', function () {
        if (!selectedProduct) return;
        toggleFavoriteById(selectedProduct.id);
    });

    // ── Favorites toggle (AJAX, no reload) ──────────────────
    async function toggleFavorite(btn) {
        var productId = Number(btn.dataset.id);
        var res = await apiFetch('/api/favorites/toggle/', {
            method: 'POST',
            body: JSON.stringify({ productId: productId }),
        });
        if (res.ok) {
            var data = await res.json();
            if (data.status === 'added') {
                favoriteIds.add(productId);
            } else {
                favoriteIds.delete(productId);
            }
            renderProducts(allProducts);
            if (selectedProduct && selectedProduct.id === productId) {
                showDetail(productId);
            }
        }
    }

    async function toggleFavoriteById(productId) {
        var res = await apiFetch('/api/favorites/toggle/', {
            method: 'POST',
            body: JSON.stringify({ productId: productId }),
        });
        if (res.ok) {
            var data = await res.json();
            if (data.status === 'added') {
                favoriteIds.add(productId);
            } else {
                favoriteIds.delete(productId);
            }
            renderProducts(allProducts);
            showDetail(productId);
        }
    }

    // ── Related products ──────────────────────────────────────
    function renderRelated(product) {
        var el = document.getElementById('related-products');
        if (!el) return;
        var related = allProducts.filter(function (p) {
            return p.category === product.category && p.id !== product.id;
        }).slice(0, 4);
        if (!related.length) {
            el.innerHTML = '<p class="text-muted">No related products in this category.</p>';
            return;
        }
        el.innerHTML = related.map(function (p) {
            return '<div class="col-sm-6 col-md-3">' +
                '<div class="card product-card h-100 product-select-card" data-id="' + p.id + '" style="cursor:pointer">' +
                (p.image ? '<img src="' + p.image + '" class="card-img-top" alt="' + escHtml(p.product_name) + '" style="height:100px;object-fit:cover">' : '<div class="product-img-placeholder" style="height:100px">Product</div>') +
                '<div class="card-body p-2">' +
                '<p class="small fw-bold mb-0">' + escHtml(p.product_name) + '</p>' +
                '<p class="small text-muted mb-0">&pound;' + Number(p.unit_price).toFixed(2) + '</p>' +
                '</div></div></div>';
        }).join('');
        el.querySelectorAll('.product-select-card').forEach(function (card) {
            card.addEventListener('click', function () { showDetail(Number(card.dataset.id)); });
        });
    }

    // ── Pagination ────────────────────────────────────────────
    function renderPagination() {
        var pager = document.getElementById('product-pagination');
        if (!pager) return;
        var totalPages = Math.ceil(totalCount / pageSize);
        if (totalPages <= 1) { pager.innerHTML = ''; return; }
        var html = '<nav aria-label="Product pages"><ul class="pagination justify-content-center">';
        for (var i = 1; i <= totalPages; i++) {
            html += '<li class="page-item ' + (i === currentPage ? 'active' : '') + '">' +
                '<a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>';
        }
        html += '</ul></nav>';
        pager.innerHTML = html;
        pager.querySelectorAll('.page-link').forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                loadProducts(searchInput.value, categoryFilter.value, Number(link.dataset.page));
            });
        });
    }

    // ── Helpers ──────────────────────────────────────────────
    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // ── Event listeners ─────────────────────────────────────
    var debounceTimer;
    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
            loadProducts(searchInput.value, categoryFilter.value);
        }, 300);
    });

    categoryFilter.addEventListener('change', function () {
        loadProducts(searchInput.value, categoryFilter.value);
    });

    // ── Init ────────────────────────────────────────────────
    async function init() {
        await loadFavorites();
        await loadProducts();
    }
    init();
})();
