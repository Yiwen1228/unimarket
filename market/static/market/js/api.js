// shared api helpers and csrf handling

function getCookie(name) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].trim();
        if (c.indexOf(name + '=') === 0) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return null;
}

// read csrf token fresh each call so it picks up any new cookie
function getCSRFToken() {
    // Try cookie first
    var token = getCookie('csrftoken');
    if (token) return token;
    // Fallback: read from the meta tag or hidden input if present
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    return '';
}

// wrapper around fetch that includes csrf token and json headers
async function apiFetch(url, options) {
    options = options || {};
    var isFormData = options.body instanceof FormData;
    var defaultHeaders = {
        'X-CSRFToken': getCSRFToken(),
    };
    // Only set Content-Type for non-FormData (browser sets it with boundary for FormData)
    // TODO: maybe move this to a shared file later
    if (!isFormData) {
        defaultHeaders['Content-Type'] = 'application/json';
    }
    var defaults = {
        headers: defaultHeaders,
        credentials: 'same-origin',
    };
    var merged = Object.assign({}, defaults, options);
    if (options.headers) {
        merged.headers = Object.assign({}, defaults.headers, options.headers);
    }
    var response = await fetch(url, merged);
    return response;
}
