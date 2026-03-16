/**
 * notifications.js — Notification bell polling + dropdown display.
 * Loaded for both customer and staff roles.
 */
(function () {
    'use strict';

    var bell = document.getElementById('notif-bell');
    var badge = document.getElementById('notif-badge');
    var dropdown = document.getElementById('notif-dropdown');
    if (!bell || !badge) return;

    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    /* ── Poll unread count every 30 seconds ────────────── */
    async function updateCount() {
        try {
            var res = await apiFetch('/api/notifications/count/');
            if (!res.ok) return;
            var data = await res.json();
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        } catch (e) { /* ignore */ }
    }

    updateCount();
    setInterval(updateCount, 30000);

    /* ── Show dropdown on bell click ──────────────────── */
    bell.addEventListener('click', async function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!dropdown) return;

        if (dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
            return;
        }

        dropdown.innerHTML = '<li class="dropdown-item text-muted small">Loading...</li>';
        dropdown.classList.add('show');

        var res = await apiFetch('/api/notifications/');
        if (!res.ok) {
            dropdown.innerHTML = '<li class="dropdown-item text-danger small">Failed to load.</li>';
            return;
        }
        var notifs = await res.json();
        if (!notifs.length) {
            dropdown.innerHTML = '<li class="dropdown-item text-muted small">No notifications.</li>';
            return;
        }

        dropdown.innerHTML = notifs.slice(0, 15).map(function (n) {
            return '<li>' +
                '<a class="dropdown-item small notif-item' + (n.is_read ? '' : ' fw-bold') + '" ' +
                'href="' + (n.link || '#') + '" data-id="' + n.id + '">' +
                escHtml(n.message) +
                '<br><span class="text-muted" style="font-size:.7rem">' +
                new Date(n.created_time).toLocaleString() + '</span>' +
                '</a></li>';
        }).join('');

        // Mark as read on click
        dropdown.querySelectorAll('.notif-item').forEach(function (item) {
            item.addEventListener('click', function () {
                var nid = item.dataset.id;
                apiFetch('/api/notifications/' + nid + '/read/', { method: 'PATCH' });
            });
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function () {
        if (dropdown) dropdown.classList.remove('show');
    });
})();
