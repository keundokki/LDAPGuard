// API base URL
const API_URL = (window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || window.API_URL || '/api';

// Auth helper functions
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

function clearAuthToken() {
    localStorage.removeItem('auth_token');
}

function authHeaders() {
    const token = getAuthToken();
    return token ? {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    } : {
        'Content-Type': 'application/json'
    };
}

function setAdminVisibility(isAdmin) {
    console.log('setAdminVisibility called with:', isAdmin);
    const adminTab = document.querySelector('.nav-tab[data-tab="admin"]');
    const adminSection = document.getElementById('admin');
    
    console.log('Admin tab element:', adminTab);
    console.log('Admin section element:', adminSection);

    if (adminTab) {
        adminTab.style.display = isAdmin ? '' : 'none';
        console.log('Admin tab display set to:', adminTab.style.display);
    }

    if (adminSection) {
        adminSection.style.display = isAdmin ? '' : 'none';
        console.log('Admin section display set to:', adminSection.style.display);
    }

    if (!isAdmin) {
        const activeTab = document.querySelector('.nav-tab.active');
        if (activeTab && activeTab.getAttribute('data-tab') === 'admin') {
            const dashboardTab = document.querySelector('.nav-tab[data-tab="dashboard"]');
            if (dashboardTab) {
                dashboardTab.click();
            }
        }
    }
}

// Control operator-level actions visibility
function setOperatorVisibility(isOperator) {
    // Operator action buttons
    const operatorButtons = [
        'addServerBtn',
        'createBackupBtn',
        'createRestoreBtn',
        'scheduleBackupBtn',
        'batchDeleteBtn'
    ];

    operatorButtons.forEach(buttonId => {
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.style.display = isOperator ? '' : 'none';
        }
    });

    if (!isOperator) {
        // Disable action columns in tables (edit/delete buttons)
        document.querySelectorAll('.action-cell').forEach(cell => {
            cell.style.display = 'none';
        });
    }
}

// Check authentication and initialize app
async function checkAuthAndInit() {
    const token = getAuthToken();
    
    if (!token) {
        // Show login modal
        document.getElementById('loginModal').style.display = 'block';
        setAdminVisibility(false);
        return;
    }
    
    try {
        // Verify token by calling a protected endpoint
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const user = await response.json();
            console.log('User from /auth/me:', user);
            console.log('User role:', user.role);
            console.log('User role type:', typeof user.role);
            console.log('Is admin check:', user.role === 'admin');
            // Show main app
            document.getElementById('mainApp').style.display = 'block';
            document.getElementById('loginModal').style.display = 'none';
            
            // Update auth status
            document.getElementById('auth-status').textContent = `${user.username} (${user.role})`;
            document.getElementById('login-button').style.display = 'none';
            document.getElementById('login-button').textContent = 'Logout';
            document.getElementById('login-button').onclick = handleLogout;

            console.log('Calling setAdminVisibility with:', user.role === 'admin');
            setAdminVisibility(user.role === 'admin');
            setOperatorVisibility(user.role === 'admin' || user.role === 'operator');
            
            // Initialize theme
            initTheme();
            
            // Load initial data
            loadDashboard();
        } else {
            // Token invalid, show login
            clearAuthToken();
            document.getElementById('loginModal').style.display = 'block';
            setAdminVisibility(false);
            setOperatorVisibility(false);
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        clearAuthToken();
        document.getElementById('loginModal').style.display = 'block';
        setAdminVisibility(false);
        setOperatorVisibility(false);
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const contentType = response.headers.get('content-type') || '';
        let payload;
        if (contentType.includes('application/json')) {
            payload = await response.json();
        } else {
            payload = await response.text();
        }

        if (!response.ok) {
            const message = payload && payload.detail
                ? payload.detail
                : (typeof payload === 'string' && payload.length > 0
                    ? payload
                    : 'Login failed');
            throw new Error(message);
        }

        if (!payload || !payload.access_token) {
            throw new Error('Login failed');
        }

        setAuthToken(payload.access_token);
        
        // Hide login modal and show app
        document.getElementById('loginModal').style.display = 'none';
        await checkAuthAndInit();
    } catch (error) {
        console.error('Login error:', error);
        showToast('error', error.message || 'Login failed');
    }
}

// Handle logout
function handleLogout() {
    clearAuthToken();
    document.getElementById('mainApp').style.display = 'none';
    document.getElementById('loginModal').style.display = 'block';
    document.getElementById('auth-status').textContent = 'Not signed in';
    document.getElementById('login-button').textContent = 'Login';
    document.getElementById('login-button').style.display = 'inline-block';
    document.getElementById('login-button').onclick = showLoginModal;
    document.getElementById('loginForm').reset();
    setAdminVisibility(false);
    setOperatorVisibility(false);
}

// Show login modal
function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
}

// Close login modal
function closeLoginModal() {
    if (!getAuthToken()) {
        // Don't allow closing if not authenticated
        return;
    }
    document.getElementById('loginModal').style.display = 'none';
}

// Toggle user menu dropdown
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    if (menu) {
        menu.classList.toggle('active');
    }
}

// Hide user menu when clicking elsewhere
document.addEventListener('click', function(event) {
    const userMenu = document.getElementById('userMenu');
    const authStatus = document.getElementById('auth-status');
    if (userMenu && !event.target.closest('.user-menu-container')) {
        userMenu.classList.remove('active');
    }
});

// Show change password modal
function showChangePasswordModal() {
    const menu = document.getElementById('userMenu');
    if (menu) {
        menu.classList.remove('active');
    }
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

// Close change password modal
function closeChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('changePasswordForm');
    if (form) {
        form.reset();
    }
}

// Handle change password form submission
async function handleChangePassword(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('changeCurrentPassword').value;
    const newPassword = document.getElementById('changeNewPassword').value;
    const confirmPassword = document.getElementById('changeConfirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        showToast('error', 'Please fill in all password fields');
        return;
    }

    if (newPassword !== confirmPassword) {
        showToast('error', 'New passwords do not match');
        return;
    }

    if (newPassword.length < 8) {
        showToast('error', 'New password must be at least 8 characters');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/change-password`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                old_password: currentPassword,
                new_password: newPassword
            })
        });

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = data && data.detail
                ? data.detail
                : (typeof data === 'string' && data.length > 0
                    ? data
                    : 'Failed to change password');
            throw new Error(message);
        }

        closeChangePasswordModal();
        showToast('success', 'Password changed successfully');
    } catch (error) {
        console.error('Change password error:', error);
        showToast('error', error.message || 'Failed to change password');
    }
}

// Toast notifications
function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Dark mode functions
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const button = document.querySelector('.theme-toggle');
    if (button) {
        button.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

// Tab switching
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.getAttribute('data-tab');
        
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(targetTab).classList.add('active');
        
        // Load data for the tab
        loadTabData(targetTab);
    });
});

// Load data for a specific tab
function loadTabData(tab) {
    switch(tab) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'servers':
            loadServers();
            break;
        case 'backups':
            loadBackups();
            break;
        case 'restores':
            loadRestores();
            break;
        case 'scheduled':
            loadScheduled();
            break;
        case 'admin':
            if (typeof loadUsers === 'function') {
                loadUsers();
            }
            break;
    }
}

// Load dashboard
async function loadDashboard() {
    try {
        // Load stats
        const [servers, backups] = await Promise.all([
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load servers: ${r.status} ${r.statusText}`);
                return r.json();
            }),
            fetch(`${API_URL}/backups/`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load backups: ${r.status} ${r.statusText}`);
                return r.json();
            })
        ]);
        
        document.getElementById('total-servers').textContent = servers.length;
        document.getElementById('total-backups').textContent = backups.length;
        
        // Count active jobs
        const activeJobs = backups.filter(b => b.status === 'in_progress' || b.status === 'pending').length;
        document.getElementById('active-jobs').textContent = activeJobs;
        
        // Last backup
        if (backups.length > 0) {
            const lastBackup = new Date(backups[0].created_at);
            document.getElementById('last-backup').textContent = lastBackup.toLocaleString();
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load LDAP servers
async function loadServers() {
    try {
        const response = await fetch(`${API_URL}/ldap-servers/`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load servers: ${response.status} ${response.statusText}`);
        }
        const servers = await response.json();
        
        const tbody = document.getElementById('servers-tbody');
        
        if (servers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No LDAP servers configured</td></tr>';
            return;
        }
        
        tbody.innerHTML = servers.map(server => `
            <tr>
                <td>${escapeHtml(server.name)}</td>
                <td>${escapeHtml(server.host)}</td>
                <td>${parseInt(server.port)}</td>
                <td>${escapeHtml(server.base_dn)}</td>
                <td>
                    <span class="status-badge ${server.is_active ? 'status-completed' : 'status-failed'}">
                        ${server.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="action-cell">
                    <button class="btn btn-primary" onclick="backupServer(${parseInt(server.id)})">Backup Now</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading servers:', error);
    }
}

async function loadServerOptions(selectId, selectedId = null) {
    const select = document.getElementById(selectId);
    if (!select) return;

    try {
        const response = await fetch(`${API_URL}/ldap-servers/`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load servers: ${response.status} ${response.statusText}`);
        }

        const servers = await response.json();

        if (servers.length === 0) {
            select.innerHTML = '<option value="">No servers available</option>';
            return;
        }

        select.innerHTML = servers.map(server => {
            const isSelected = selectedId && parseInt(server.id) === parseInt(selectedId);
            return `<option value="${parseInt(server.id)}"${isSelected ? ' selected' : ''}>${escapeHtml(server.name)}</option>`;
        }).join('');
    } catch (error) {
        console.error('Error loading server options:', error);
        select.innerHTML = '<option value="">Failed to load servers</option>';
    }
}

async function loadBackupOptions(selectId, selectedId = null) {
    const select = document.getElementById(selectId);
    if (!select) return;

    try {
        const response = await fetch(`${API_URL}/backups/?status=completed`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load backups: ${response.status} ${response.statusText}`);
        }

        const backups = await response.json();

        if (backups.length === 0) {
            select.innerHTML = '<option value="">No completed backups available</option>';
            return;
        }

        select.innerHTML = backups.map(backup => {
            const id = parseInt(backup.id);
            const label = `#${id} - Server ${parseInt(backup.ldap_server_id)} (${backup.backup_type})`;
            const isSelected = selectedId && id === parseInt(selectedId);
            return `<option value="${id}"${isSelected ? ' selected' : ''}>${label}</option>`;
        }).join('');
    } catch (error) {
        console.error('Error loading backup options:', error);
        select.innerHTML = '<option value="">Failed to load backups</option>';
    }
}

// Load backups
async function loadBackups() {
    try {
        const response = await fetch(`${API_URL}/backups/`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load backups: ${response.status} ${response.statusText}`);
        }
        const backups = await response.json();
        
        const tbody = document.getElementById('backups-tbody');
        
        if (backups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-data">No backups found</td></tr>';
            return;
        }
        
        tbody.innerHTML = backups.map(backup => `
            <tr>
                <td>${parseInt(backup.id)}</td>
                <td>Server #${parseInt(backup.ldap_server_id)}</td>
                <td>${escapeHtml(backup.backup_type)}</td>
                <td>
                    <!-- Note: status is a backend enum value (pending|in_progress|completed|failed), safe for use in CSS class -->
                    <span class="status-badge status-${backup.status.replace('_', '-')}">
                        ${escapeHtml(backup.status)}
                    </span>
                </td>
                <td>${backup.file_size ? formatBytes(backup.file_size) : 'N/A'}</td>
                <td>${backup.entry_count ? parseInt(backup.entry_count) : 'N/A'}</td>
                <td>${new Date(backup.created_at).toLocaleString()}</td>
                <td class="action-cell">
                    ${backup.status === 'completed' ? 
                        `<button class="btn btn-success" onclick="restoreBackup(${parseInt(backup.id)})">Restore</button>` : 
                        ''}
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading backups:', error);
    }
}

// Load restore jobs
async function loadRestores() {
    try {
        const response = await fetch(`${API_URL}/restores/`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load restores: ${response.status} ${response.statusText}`);
        }
        const restores = await response.json();
        
        const tbody = document.getElementById('restores-tbody');
        
        if (restores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No restore jobs found</td></tr>';
            return;
        }
        
        tbody.innerHTML = restores.map(restore => `
            <tr>
                <td>${parseInt(restore.id)}</td>
                <td>${parseInt(restore.backup_id)}</td>
                <td>Server #${parseInt(restore.ldap_server_id)}</td>
                <td>
                    <!-- Note: status is a backend enum value (pending|in_progress|completed|failed), safe for use in CSS class -->
                    <span class="status-badge status-${restore.status.replace('_', '-')}">
                        ${escapeHtml(restore.status)}
                    </span>
                </td>
                <td>${restore.entries_restored ? parseInt(restore.entries_restored) : 'N/A'}</td>
                <td>${new Date(restore.created_at).toLocaleString()}</td>
                <td class="action-cell">-</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading restores:', error);
    }
}

// Load scheduled backups
async function loadScheduled() {
    try {
        const response = await fetch(`${API_URL}/scheduled-backups/`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            throw new Error(`Failed to load scheduled backups: ${response.status} ${response.statusText}`);
        }

        const scheduled = await response.json();
        const tbody = document.getElementById('scheduled-tbody');

        if (scheduled.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No scheduled backups</td></tr>';
            return;
        }

        tbody.innerHTML = scheduled.map(schedule => `
            <tr>
                <td>${escapeHtml(schedule.name)}</td>
                <td>Server #${parseInt(schedule.ldap_server_id)}</td>
                <td>${escapeHtml(schedule.cron_expression)}</td>
                <td>${escapeHtml(schedule.backup_type)}</td>
                <td>${parseInt(schedule.retention_days)}</td>
                <td>
                    <span class="status-badge ${schedule.is_active ? 'status-completed' : 'status-failed'}">
                        ${schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="action-cell">-</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading scheduled backups:', error);
    }
}

// Helper functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showAddServerModal() {
    const modal = document.getElementById('addServerModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeAddServerModal() {
    const modal = document.getElementById('addServerModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('addServerForm');
    if (form) {
        form.reset();
    }
}

function updatePort(checkbox) {
    const portInput = document.getElementById('serverPort');
    if (!portInput) return;

    if (checkbox.checked && (portInput.value === '' || portInput.value === '389')) {
        portInput.value = '636';
    } else if (!checkbox.checked && (portInput.value === '' || portInput.value === '636')) {
        portInput.value = '389';
    }
}

async function handleAddServer(event) {
    event.preventDefault();

    const name = document.getElementById('serverName').value.trim();
    const host = document.getElementById('serverHost').value.trim();
    const port = document.getElementById('serverPort').value;
    const use_ssl = document.getElementById('serverSSL').checked;
    const base_dn = document.getElementById('serverBaseDN').value.trim();
    const bind_dn = document.getElementById('serverBindDN').value.trim() || null;
    const bind_password = document.getElementById('serverBindPassword').value || null;

    if (!name || !host || !port || !base_dn) {
        showToast('error', 'Please fill in required fields (Name, Host, Port, Base DN)');
        return;
    }

    const payload = {
        name,
        host,
        port: parseInt(port),
        use_ssl,
        base_dn,
        bind_dn,
        bind_password,
        is_active: true
    };

    try {
        const response = await fetch(`${API_URL}/ldap-servers/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = data && data.detail
                ? data.detail
                : (typeof data === 'string' && data.length > 0
                    ? data
                    : 'Failed to add LDAP server');
            throw new Error(message);
        }

        showToast('success', 'LDAP server added successfully');
        closeAddServerModal();
        await loadServers();
    } catch (error) {
        console.error('Add server error:', error);
        showToast('error', error.message || 'Failed to add LDAP server');
    }
}

function showCreateBackupModal() {
    const modal = document.getElementById('createBackupModal');
    if (modal) {
        modal.style.display = 'block';
    }
    loadServerOptions('backupServerId');
}

function closeCreateBackupModal() {
    const modal = document.getElementById('createBackupModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('createBackupForm');
    if (form) {
        form.reset();
    }
}

async function handleCreateBackup(event) {
    event.preventDefault();

    const serverId = document.getElementById('backupServerId').value;
    const backupType = document.getElementById('backupType').value;
    const encrypted = document.getElementById('backupEncrypted').checked;
    const compressionEnabled = document.getElementById('backupCompression').checked;

    if (!serverId) {
        showToast('error', 'Please select an LDAP server');
        return;
    }

    const payload = {
        ldap_server_id: parseInt(serverId),
        backup_type: backupType,
        encrypted,
        compression_enabled: compressionEnabled
    };

    try {
        const response = await fetch(`${API_URL}/backups/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = data && data.detail
                ? data.detail
                : (typeof data === 'string' && data.length > 0
                    ? data
                    : 'Failed to create backup');
            throw new Error(message);
        }

        showToast('success', 'Backup created successfully');
        closeCreateBackupModal();
        await loadBackups();
    } catch (error) {
        console.error('Create backup error:', error);
        showToast('error', error.message || 'Failed to create backup');
    }
}

function showCreateRestoreModal() {
    const modal = document.getElementById('createRestoreModal');
    if (modal) {
        modal.style.display = 'block';
    }
    loadBackupOptions('restoreBackupId');
    loadServerOptions('restoreServerId');
}

function closeCreateRestoreModal() {
    const modal = document.getElementById('createRestoreModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('createRestoreForm');
    if (form) {
        form.reset();
    }
    toggleRestoreFilter();
}

function toggleRestoreFilter() {
    const filterGroup = document.getElementById('restoreFilterGroup');
    const selective = document.getElementById('restoreSelective');
    if (!filterGroup || !selective) return;

    filterGroup.style.display = selective.checked ? 'block' : 'none';
}

async function handleCreateRestore(event) {
    event.preventDefault();

    const backupId = document.getElementById('restoreBackupId').value;
    const serverId = document.getElementById('restoreServerId').value;
    const selectiveRestore = document.getElementById('restoreSelective').checked;
    const restoreFilter = document.getElementById('restoreFilter').value.trim();
    const pointInTime = document.getElementById('restorePointInTime').value;

    if (!backupId || !serverId) {
        showToast('error', 'Please select a backup and a target server');
        return;
    }

    if (selectiveRestore && !restoreFilter) {
        showToast('error', 'Please provide an LDAP filter for selective restore');
        return;
    }

    const payload = {
        backup_id: parseInt(backupId),
        ldap_server_id: parseInt(serverId),
        selective_restore: selectiveRestore,
        restore_filter: selectiveRestore ? restoreFilter : null,
        point_in_time: pointInTime || null
    };

    try {
        const response = await fetch(`${API_URL}/restores/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = data && data.detail
                ? data.detail
                : (typeof data === 'string' && data.length > 0
                    ? data
                    : 'Failed to create restore job');
            throw new Error(message);
        }

        showToast('success', 'Restore job created successfully');
        closeCreateRestoreModal();
        await loadRestores();
    } catch (error) {
        console.error('Create restore error:', error);
        showToast('error', error.message || 'Failed to create restore job');
    }
}

function showScheduleModal() {
    const modal = document.getElementById('createScheduleModal');
    if (modal) {
        modal.style.display = 'block';
    }
    loadServerOptions('scheduleServerId');
}

function closeCreateScheduleModal() {
    const modal = document.getElementById('createScheduleModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('createScheduleForm');
    if (form) {
        form.reset();
    }
}

async function handleCreateSchedule(event) {
    event.preventDefault();

    const name = document.getElementById('scheduleName').value.trim();
    const serverId = document.getElementById('scheduleServerId').value;
    const backupType = document.getElementById('scheduleType').value;
    const cronExpression = document.getElementById('scheduleCron').value.trim();
    const retention = document.getElementById('scheduleRetention').value;

    if (!name || !serverId || !cronExpression) {
        showToast('error', 'Please fill in required fields (Name, Server, Cron)');
        return;
    }

    const payload = {
        name,
        ldap_server_id: parseInt(serverId),
        backup_type: backupType,
        cron_expression: cronExpression,
        retention_days: parseInt(retention || '30')
    };

    try {
        const response = await fetch(`${API_URL}/scheduled-backups/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = data && data.detail
                ? data.detail
                : (typeof data === 'string' && data.length > 0
                    ? data
                    : 'Failed to create schedule');
            throw new Error(message);
        }

        showToast('success', 'Schedule created successfully');
        closeCreateScheduleModal();
        await loadScheduled();
    } catch (error) {
        console.error('Create schedule error:', error);
        showToast('error', error.message || 'Failed to create schedule');
    }
}

function backupServer(serverId) {
    const modal = document.getElementById('createBackupModal');
    if (modal) {
        modal.style.display = 'block';
    }
    loadServerOptions('backupServerId', serverId);
}

function restoreBackup(backupId) {
    const modal = document.getElementById('createRestoreModal');
    if (modal) {
        modal.style.display = 'block';
    }
    loadBackupOptions('restoreBackupId', backupId);
    loadServerOptions('restoreServerId');
}

// Fetch and display app version
async function loadAppVersion() {
    try {
        const response = await fetch(`${API_URL}/`);
        if (!response.ok) {
            throw new Error(`Failed to load app version: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        if (data.version) {
            document.getElementById('app-version').textContent = `v${data.version}`;
        }
    } catch (error) {
        console.error('Failed to load app version:', error);
    }
}

// Initialize dashboard on load
window.addEventListener('DOMContentLoaded', () => {
    checkAuthAndInit();
    loadAppVersion();
});

// Auto-refresh every 10 seconds for backups and restores
setInterval(() => {
    if (!getAuthToken()) return;
    
    const activeTab = document.querySelector('.nav-tab.active')?.getAttribute('data-tab');
    if (activeTab === 'backups' || activeTab === 'restores') {
        loadTabData(activeTab);
    }
}, 10000);
