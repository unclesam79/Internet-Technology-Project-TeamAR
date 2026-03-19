// --- Tenant-specific data is set by the template via inline <script> ---
// Expected globals: currentUser, allRequests, profileUpdateUrl, urls

// Map view IDs to page titles for switchView
const viewTitles = { dashboardView: 'Dashboard', newRequestView: 'Submit Request', historyView: 'Request History', profileView: 'My Profile', supportView: 'Help & Support' };

function initProfileUI() {
    document.getElementById('uName').innerText    = currentUser.name;
    document.getElementById('profName').value     = currentUser.name;
    document.getElementById('profEmail').value    = currentUser.email;
    document.getElementById('profPhone').value    = currentUser.phone;
    const avatarUrl = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=3b82f6&color=fff`;
    document.getElementById('userImgTop').src     = avatarUrl;
    document.getElementById('profilePreview').src = avatarUrl;
}

function refreshDashboard() {
    document.getElementById('statTotal').innerText    = allRequests.length;
    document.getElementById('statProgress').innerText = allRequests.filter(r => r.status === 'Pending').length;
    document.getElementById('statFixed').innerText    = allRequests.filter(r => r.status === 'Fixed').length;

    const historyBody = document.getElementById('historyTableBody');
    const recentBody  = document.getElementById('recentTableBody');
    historyBody.innerHTML = '';
    recentBody.innerHTML  = '';

    allRequests.forEach((r, idx) => {
        const statusColor = r.status === 'Fixed' ? 'success' : 'warning';
        const urgColor    = r.urgency === 'High' ? 'danger' : 'secondary';
        historyBody.innerHTML += `<tr><td class="small fw-bold text-muted">#${r.id}</td><td class="fw-bold">${r.title}</td><td><span class="badge bg-${urgColor}">${r.urgency}</span></td><td class="small">${r.date}</td><td><span class="badge bg-${statusColor} ${r.status !== 'Fixed' ? 'text-dark' : ''}">${r.status}</span></td><td class="text-end">${r.status === 'Pending' ? `<button class="btn btn-sm btn-link text-danger" onclick="cancelReq(${r.id})">Cancel</button>` : '<i class="bi bi-lock-fill text-muted"></i>'}</td></tr>`;
        if (idx < 5) {
            recentBody.innerHTML += `<tr><td><span class="small text-muted">#${r.id}</span></td><td class="small fw-bold">${r.title}</td><td><span class="badge bg-${statusColor} ${r.status !== 'Fixed' ? 'text-dark' : ''}" style="font-size:0.6rem;">${r.status}</span></td></tr>`;
        }
    });
}

// --- Form handlers ---
document.getElementById('reqForm').onsubmit = async (e) => {
    e.preventDefault();
    const result = await post(urls.requestCreate, {
        title:    document.getElementById('reqTitle').value,
        location: document.getElementById('reqLoc').value,
        urgency:  document.getElementById('reqUrg').value,
        detail:   document.getElementById('reqDetail').value,
    });
    allRequests.unshift(result.request);
    refreshDashboard();
    alert("New maintenance request has been recorded.");
    switchView('dashboardView', document.querySelector('.nav-link'));
    document.getElementById('reqForm').reset();
};

async function cancelReq(id) {
    if (!confirm("Permanently cancel this maintenance ticket?")) return;
    await post(urls.requestCancel.replace('/0/', `/${id}/`));
    allRequests = allRequests.filter(r => r.id !== id);
    refreshDashboard();
}

// Avatar upload
initAvatarUpload('profilePreview', 'userImgTop', '3b82f6');

document.getElementById('profileForm').onsubmit = async (e) => {
    e.preventDefault();
    const name  = document.getElementById('profName').value;
    const phone = document.getElementById('profPhone').value;
    await post(profileUpdateUrl, { name, phone });
    currentUser.name  = name;
    currentUser.phone = phone;
    alert("Your profile has been updated!");
    initProfileUI();
};

document.getElementById('contactAdminForm').onsubmit = async (e) => {
    e.preventDefault();
    await post(urls.messageSend, { msg: document.getElementById('adminMsgText').value });
    alert("Your message has been sent successfully! The Admin team will review it in their inbox.");
    document.getElementById('contactAdminForm').reset();
};

function filterHistory() {
    const val = document.getElementById('historySearch').value.toLowerCase();
    document.querySelectorAll('#historyTableBody tr').forEach(row => {
        row.style.display = row.innerText.toLowerCase().includes(val) ? '' : 'none';
    });
}

initProfileUI();
refreshDashboard();
