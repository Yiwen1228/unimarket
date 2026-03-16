/**
 * favorites.js — Customer favorites page (AJAX).
 */
(function () {
    'use strict';

    const container = document.getElementById('favorites-container');

    async function loadFavorites() {
        const res = await apiFetch('/api/favorites/');
        if (!res.ok) {
            container.innerHTML = '<p class="text-danger">Failed to load favorites.</p>';
            return;
        }
        const favorites = await res.json();
        if (!favorites.length) {
            container.innerHTML = '<p class="text-muted col">You have no favorites yet. Browse <a href="/products/">products</a> to add some!</p>';
            return;
        }

        container.innerHTML = favorites.map(f => `
        <div class="col-sm-6 col-md-4 col-lg-3" role="listitem">
            <div class="card product-card h-100">
                <div class="card-body">
                    <h2 class="h6 card-title">${escHtml(f.product_name)}</h2>
                    <span class="badge bg-secondary mb-2">${escHtml(f.category)}</span>
                    <p class="fw-bold mb-2">&pound;${Number(f.unit_price).toFixed(2)}</p>
                    <button class="btn btn-sm btn-outline-danger btn-remove-fav" data-id="${f.product}"
                            aria-label="Remove ${escHtml(f.product_name)} from favorites">
                        <i class="bi bi-heart-fill" aria-hidden="true"></i> Remove
                    </button>
                </div>
            </div>
        </div>`).join('');

        container.querySelectorAll('.btn-remove-fav').forEach(btn => {
            btn.addEventListener('click', () => removeFavorite(btn));
        });
    }

    async function removeFavorite(btn) {
        const productId = Number(btn.dataset.id);
        const res = await apiFetch('/api/favorites/toggle/', {
            method: 'POST',
            body: JSON.stringify({ productId }),
        });
        if (res.ok) {
            loadFavorites();
        }
    }

    function escHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    loadFavorites();
})();
