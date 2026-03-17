// profile page
(function () {
    'use strict';

    function escHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // load profile
    async function loadProfile() {
        var res = await apiFetch('/api/customer/profile/');
        if (!res.ok) return;
        var data = await res.json();
        document.getElementById('prof-username').value = data.username || '';
        document.getElementById('prof-email').value = data.email || '';
        document.getElementById('prof-phone').value = data.phone_number || '';
    }

    // save profile
    var profileForm = document.getElementById('profile-form');
    var profileFb = document.getElementById('profile-feedback');
    if (profileForm) {
        profileForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            var res = await apiFetch('/api/customer/profile/', {
                method: 'PATCH',
                body: JSON.stringify({
                    email: document.getElementById('prof-email').value.trim(),
                    phone_number: document.getElementById('prof-phone').value.trim(),
                })
            });
            var data = await res.json();
            profileFb.innerHTML = res.ok
                ? '<div class="alert alert-success">' + escHtml(data.message) + '</div>'
                : '<div class="alert alert-danger">' + escHtml(data.error) + '</div>';
        });
    }

    // change password
    var pwForm = document.getElementById('password-form');
    var pwFb = document.getElementById('password-feedback');
    if (pwForm) {
        pwForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            var pw = document.getElementById('pw-new').value;
            var confirm = document.getElementById('pw-confirm').value;
            if (pw !== confirm) {
                pwFb.innerHTML = '<div class="alert alert-danger">Passwords do not match.</div>';
                return;
            }
            var res = await apiFetch('/api/customer/profile/', {
                method: 'PATCH',
                body: JSON.stringify({ password: pw })
            });
            var data = await res.json();
            if (res.ok) {
                pwFb.innerHTML = '<div class="alert alert-success">Password updated.</div>';
                pwForm.reset();
            } else {
                pwFb.innerHTML = '<div class="alert alert-danger">' + escHtml(data.error) + '</div>';
            }
        });
    }

    loadProfile();
})();
