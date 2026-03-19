function getCookie(name) {
    for (const cookie of document.cookie.split(';')) {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return null;
}

window.onload = () => {
    document.getElementById("lEmail").focus();
};

document.getElementById('regForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        name:     form.name.value,
        email:    form.email.value,
        password: form.password.value,
        role:     form.role.value,
    };
    const res = await fetch(registerUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    const result = await res.json();
    if (result.error) {
        alert(result.error);
    } else {
        form.reset();
        new bootstrap.Tab(document.getElementById('login-tab')).show();
        new bootstrap.Modal(document.getElementById('regSuccessModal')).show();
    }
});
