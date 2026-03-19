// --- Admin-specific data is set by the template via inline <script> ---
// Expected globals: currentUser, allUsers, allRequests, allMessages, profileUpdateUrl, urls

const userModal = new bootstrap.Modal(document.getElementById('userModal'));

function initUI() {
    document.getElementById('adminName').innerText = currentUser.name;
    document.getElementById('profName').value = currentUser.name;
    document.getElementById('profEmail').value = currentUser.email;
    const avatarUrl = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=6366f1&color=fff`;
    document.getElementById('adminImgTop').src = avatarUrl;
    document.getElementById('profilePreview').src = avatarUrl;
    setInterval(() => { if (document.getElementById('liveTime')) document.getElementById('liveTime').innerText = new Date().toLocaleString(); }, 1000);
    renderAll();
}

function renderAll() {
    const pending     = allRequests.filter(r => r.status === 'Pending' || r.status === 'In Progress');
    const fixedCount  = allRequests.filter(r => r.status === 'Fixed').length;
    const highUrgency = pending.filter(r => r.urgency === 'High');

    document.getElementById('statUsers').innerText   = allUsers.length;
    document.getElementById('statPending').innerText = pending.length;
    document.getElementById('statFixed').innerText   = fixedCount;
    document.getElementById('statHigh').innerText    = highUrgency.length;
    document.getElementById('adminName').innerText   = currentUser.name;

    const badge = document.getElementById('supportBadge');
    if (badge) { badge.innerText = allMessages.length; badge.classList.toggle('d-none', allMessages.length === 0); }

    // Priority monitor — shows high-urgency unresolved tasks
    const monitor = document.getElementById('priorityMonitorList');
    if (monitor) {
        monitor.innerHTML = '';
        if (highUrgency.length === 0) {
            monitor.innerHTML = '<div class="col-12 text-center py-5 text-muted"><i class="bi bi-check-circle fs-1 text-success"></i><p class="mt-2">All high-urgency tasks are resolved.</p></div>';
        } else {
            highUrgency.forEach(t => {
                monitor.innerHTML += `<div class="col-md-6"><div class="card p-3 priority-item border-0 shadow-sm h-100"><div class="d-flex justify-content-between align-items-start"><div class="overflow-hidden"><h6 class="fw-bold mb-1 text-truncate">${t.title}</h6><div class="small text-muted mb-1"><i class="bi bi-geo-alt me-1"></i>${t.location}</div><div class="small text-muted"><i class="bi bi-person me-1"></i>${t.owner}</div></div><span class="badge bg-danger rounded-pill px-2">URGENT</span></div></div></div>`;
            });
        }
    }

    // User table
    const userBody = document.getElementById('userTableBody');
    if (userBody) {
        userBody.innerHTML = '';
        allUsers.forEach(u => {
            const isAdmin = u.role === 'admin';
            userBody.innerHTML += `<tr><td><div class="fw-bold">${u.name}</div></td><td class="small text-muted">${u.email}</td><td><span class="badge ${isAdmin ? 'bg-primary' : 'bg-light text-dark border'}">${u.role}</span></td><td><span class="text-success small"><i class="bi bi-circle-fill me-1" style="font-size:0.5rem"></i> Active</span></td><td class="text-end"><button class="btn btn-sm btn-light border me-1" onclick="editUser(${u.id})"><i class="bi bi-pencil"></i></button>${isAdmin ? '' : `<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${u.id})"><i class="bi bi-trash"></i></button>`}</td></tr>`;
        });
    }

    // Ticket table
    const ticketBody = document.getElementById('ticketTableBody');
    if (ticketBody) {
        ticketBody.innerHTML = '';
        allRequests.forEach(t => {
            const bClass = t.status === 'Fixed' ? 'bg-success' : 'bg-warning text-dark';
            const uClass = t.urgency === 'High' ? 'bg-danger' : 'bg-secondary';
            ticketBody.innerHTML += `<tr><td>#${t.id}</td><td class="fw-bold">${t.title}</td><td>${t.owner}</td><td><span class="badge ${uClass}">${t.urgency}</span></td><td><span class="badge ${bClass}">${t.status}</span></td><td><button class="btn btn-sm btn-link text-danger" onclick="deleteTicket(${t.id})">Delete</button></td></tr>`;
        });
    }

    // Messages
    const msgList = document.getElementById('messageList');
    if (msgList) {
        msgList.innerHTML = allMessages.length === 0 ? '<p class="text-center py-5 text-muted">No support messages.</p>' : '';
        allMessages.forEach(m => {
            msgList.innerHTML += `<div class="list-group-item py-3 border-0 border-bottom"><div class="d-flex justify-content-between"><h6 class="fw-bold mb-1">${m.from}</h6><small class="text-muted">${m.date}</small></div><p class="small text-muted mb-0">${m.msg}</p></div>`;
        });
    }
}

// Avatar upload
initAvatarUpload('profilePreview', 'adminImgTop', '6366f1');

document.getElementById('profileForm').onsubmit = async (e) => {
    e.preventDefault();
    const newName = document.getElementById('profName').value;
    await post(profileUpdateUrl, { name: newName });
    currentUser.name = newName;
    document.getElementById('adminName').innerText = newName;
    alert("Profile saved successfully!");
};

// --- User management ---
function openUserModal() {
    document.getElementById('userForm').reset();
    document.getElementById('editIdx').value = '';
    document.getElementById('userModalTitle').innerText = 'Onboard New User';
    userModal.show();
}

function editUser(id) {
    const u = allUsers.find(u => u.id === id);
    document.getElementById('uNameField').value  = u.name;
    document.getElementById('uEmailField').value = u.email;
    document.getElementById('uRoleField').value  = u.role;
    document.getElementById('editIdx').value     = id;
    document.getElementById('userModalTitle').innerText = 'Edit User Settings';
    userModal.show();
}

document.getElementById('userForm').onsubmit = async (e) => {
    e.preventDefault();
    const id   = document.getElementById('editIdx').value;
    const data = {
        name:  document.getElementById('uNameField').value,
        email: document.getElementById('uEmailField').value,
        role:  document.getElementById('uRoleField').value,
    };
    if (id === '') {
        const result = await post(urls.usersAdd, data);
        if (result.error) { alert(result.error); return; }
        allUsers.push(result.user);
    } else {
        await post(`/api/users/${id}/edit/`, data);
        const idx = allUsers.findIndex(u => u.id === parseInt(id));
        if (idx !== -1) allUsers[idx] = { ...allUsers[idx], ...data };
    }
    userModal.hide();
    renderAll();
};

async function deleteUser(id) {
    if (!confirm('Permanently remove this user?')) return;
    await post(`/api/users/${id}/delete/`);
    allUsers = allUsers.filter(u => u.id !== id);
    renderAll();
}

async function deleteTicket(id) {
    if (!confirm('Delete this maintenance ticket?')) return;
    await post(`/api/requests/${id}/delete/`);
    allRequests = allRequests.filter(t => t.id !== id);
    renderAll();
}

async function clearMessages() {
    if (!confirm('Empty the support inbox?')) return;
    await post(urls.messagesClear);
    allMessages = [];
    renderAll();
}

window.onload = initUI;
