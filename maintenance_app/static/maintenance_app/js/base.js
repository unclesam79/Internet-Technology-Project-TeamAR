/* --- Shared JS utilities --- */

// Extract a cookie value by name (used for CSRF token)
function getCookie(name) {
    for (let cookie of document.cookie.split(';')) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) return decodeURIComponent(cookie.slice(name.length + 1));
    }
    return null;
}
const csrftoken = getCookie('csrftoken');

// POST JSON helper — returns parsed response
async function post(url, data = {}) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

// Toggle between dashboard view panes
function switchView(viewId, el) {
    document.querySelectorAll('.view-pane').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
    if (el) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        el.classList.add('active');
    }
    // Let child pages update the page title if they define viewTitles
    if (typeof viewTitles !== 'undefined' && viewTitles[viewId]) {
        const titleEl = document.getElementById('pageTitle');
        if (titleEl) titleEl.innerText = viewTitles[viewId];
    }
}

// Shared profile UI: avatar upload via base64
// profileUpdateUrl must be set by the template before calling this
function initAvatarUpload(previewId, topImgId, accentColor) {
    const avatarInput = document.getElementById('avatarInput');
    if (!avatarInput) return;
    avatarInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onloadend = () => {
            currentUser.avatar = reader.result;
            document.getElementById(previewId).src = reader.result;
            document.getElementById(topImgId).src  = reader.result;
            post(profileUpdateUrl, { avatar: reader.result });
        };
        reader.readAsDataURL(file);
    };
}
