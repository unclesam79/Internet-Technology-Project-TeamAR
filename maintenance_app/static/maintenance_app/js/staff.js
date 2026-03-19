// --- Staff-specific data is set by the template via inline <script> ---
// Expected globals: currentUser, allRequests, profileUpdateUrl, urls

// Map view IDs to page titles for switchView
const viewTitles = { dashboardView: 'Staff Dashboard', tasksView: 'Work Orders', profileView: 'Staff Profile' };

document.getElementById('currentDate').innerText = new Date().toLocaleDateString();

function initProfileUI() {
    document.getElementById('uName').innerText    = currentUser.name;
    document.getElementById('profName').value     = currentUser.name;
    document.getElementById('profEmail').value    = currentUser.email;
    document.getElementById('profPhone').value    = currentUser.phone;
    const avatarUrl = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=0d9488&color=fff`;
    document.getElementById('userImgTop').src     = avatarUrl;
    document.getElementById('profilePreview').src = avatarUrl;
    document.getElementById('quickNotesArea').value = staffNoteBody;
}

// Notes: debounced auto-save to database
let noteTimer = null;
document.getElementById('quickNotesArea').oninput = (e) => {
    clearTimeout(noteTimer);
    noteTimer = setTimeout(() => post(urls.notesSave, { body: e.target.value }), 800);
};

function clearNotes() {
    if (confirm("Clear all your notes?")) {
        document.getElementById('quickNotesArea').value = '';
        post(urls.notesSave, { body: '' });
    }
}

function refreshDashboard() {
    const pendingTasks   = allRequests.filter(r => r.status === 'Pending' || r.status === 'In Progress');
    const emergencyTasks = allRequests.filter(r => (r.status === 'Pending' || r.status === 'In Progress') && r.urgency === 'High');
    const fixedTasks     = allRequests.filter(r => r.status === 'Fixed');

    document.getElementById('statPending').innerText   = pendingTasks.length;
    document.getElementById('statEmergency').innerText = emergencyTasks.length;
    document.getElementById('statFixed').innerText     = fixedTasks.length;

    const total   = allRequests.length;
    const percent = total > 0 ? Math.round((fixedTasks.length / total) * 100) : 0;
    document.getElementById('analyticsProgressBar').style.width = percent + '%';
    document.getElementById('completionPercent').innerText      = percent + '% Fixed';
    document.getElementById('totalTasksCount').innerText        = total + ' Tasks';

    document.getElementById('navBadgeHigh').innerText = emergencyTasks.length;
    document.getElementById('navBadgeHigh').classList.toggle('d-none', emergencyTasks.length === 0);

    // Action needed table — top 5 pending tasks
    const actionBody = document.getElementById('actionNeededBody');
    actionBody.innerHTML = '';
    pendingTasks.slice(0, 5).forEach(r => {
        const urgBadge    = r.urgency === 'High' ? 'danger' : 'secondary';
        const statusBadge = r.status === 'In Progress' ? 'warning text-dark' : 'secondary';
        actionBody.innerHTML += `<tr><td class="small fw-bold text-muted">#${r.id}</td><td class="small"><i class="bi bi-geo-alt-fill text-muted me-1"></i>${r.location}</td><td class="fw-bold">${r.title}</td><td><span class="badge bg-${urgBadge}">${r.urgency}</span></td><td><span class="badge bg-${statusBadge}">${r.status}</span></td></tr>`;
    });

    // Full work orders table
    const workBody = document.getElementById('workOrdersBody');
    workBody.innerHTML = '';
    allRequests.forEach(r => {
        const urgBadge = r.urgency === 'High' ? 'danger' : 'secondary';
        let statusBadge  = 'success';
        let actionButton = `<button class="btn btn-sm btn-light border text-muted ticket-action-btn" disabled><i class="bi bi-check-lg me-1"></i>Completed</button>`;
        if (r.status === 'Pending') {
            statusBadge  = 'secondary';
            actionButton = `<button class="btn btn-sm btn-primary ticket-action-btn fw-bold shadow-sm" onclick="updateTicketStatus(${r.id}, 'In Progress')"><i class="bi bi-play-fill me-1"></i>Start Work</button>`;
        } else if (r.status === 'In Progress') {
            statusBadge  = 'warning text-dark';
            actionButton = `<button class="btn btn-sm btn-success ticket-action-btn fw-bold shadow-sm" onclick="updateTicketStatus(${r.id}, 'Fixed')"><i class="bi bi-check2-circle me-1"></i>Mark Fixed</button>`;
        }
        workBody.innerHTML += `<tr class="${r.urgency === 'High' && r.status !== 'Fixed' ? 'table-danger' : ''}"><td><div class="small fw-bold text-muted">#${r.id}</div><div class="small" style="font-size:0.75rem;">${r.date}</div></td><td><div class="fw-bold small">${r.owner}</div><div class="small text-muted"><i class="bi bi-geo-alt me-1"></i>${r.location}</div></td><td><div class="fw-bold">${r.title}</div><div class="small text-muted text-truncate" style="max-width:200px;">${r.detail || 'No details provided.'}</div></td><td><span class="badge bg-${urgBadge}">${r.urgency}</span></td><td><span class="badge bg-${statusBadge}">${r.status}</span></td><td class="text-end">${actionButton}</td></tr>`;
    });
}

async function updateTicketStatus(ticketId, newStatus) {
    if (newStatus === 'Fixed' && !confirm("Are you sure this issue is completely fixed?")) return;
    await post(urls.requestStatus.replace('/0/', `/${ticketId}/`), { status: newStatus });
    const idx = allRequests.findIndex(r => r.id === ticketId);
    if (idx !== -1) allRequests[idx].status = newStatus;
    refreshDashboard();
}

// Avatar upload
initAvatarUpload('profilePreview', 'userImgTop', '0d9488');

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

initProfileUI();
refreshDashboard();
