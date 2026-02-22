// API base URL
const API_URL = (window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || window.API_URL || '/api';

// Pagination state
const paginationState = {
    backups: { skip: 0, limit: 50, hasMore: true, allItems: [], perServerLoaded: {} },
    sensitiveBackups: { skip: 0, limit: 50, hasMore: true, allItems: [] },
    serverBackups: { skip: 0, limit: 10, hasMore: true, allItems: [], selectedServerId: null },
    restores: { skip: 0, limit: 50, hasMore: true, allItems: [] }
};

// Feature flags
let featureFlags = {
    cloud_storage_enabled: false,
    cloud_provider: null
};

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

// Control sensitive backups tab visibility (for SECURITY_ADMIN and above)
function setSensitiveBackupsVisibility(hasSecurityAccess) {
    const sensitiveTab = document.querySelector('.nav-tab[data-tab="sensitive"]');
    const sensitiveSection = document.getElementById('sensitive');
    
    if (sensitiveTab) {
        sensitiveTab.style.display = hasSecurityAccess ? '' : 'none';
    }
    if (sensitiveSection) {
        sensitiveSection.style.display = hasSecurityAccess ? '' : 'none';
    }

    if (!hasSecurityAccess) {
        // Hiding sensitive backups creation button in regular backups tab
        const sensitiveCreateBtn = document.getElementById('createSensitiveBackupBtn');
        if (sensitiveCreateBtn) {
            sensitiveCreateBtn.style.display = 'none';
        }
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
            setSensitiveBackupsVisibility(user.role === 'admin' || user.role === 'backup_admin' || user.role === 'security_admin');
            
            // Initialize theme
            initTheme();
            
            // Load feature flags
            await loadFeatureFlags();
            
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
        case 'sensitive':
            loadSensitiveBackups();
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
        const [servers, backups, restores, scheduledBackups] = await Promise.all([
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load servers: ${r.status} ${r.statusText}`);
                return r.json();
            }),
            fetch(`${API_URL}/backups/?skip=0&limit=50`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load backups: ${r.status} ${r.statusText}`);
                return r.json();
            }),
            fetch(`${API_URL}/restores/?skip=0&limit=50`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load restores: ${r.status} ${r.statusText}`);
                return r.json();
            }),
            fetch(`${API_URL}/scheduled-backups/?skip=0&limit=100`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load scheduled backups: ${r.status} ${r.statusText}`);
                return r.json();
            }).catch(err => {
                console.warn('Failed to load scheduled backups:', err);
                return [];
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

        renderBackupHealthDashboard(backups, servers, scheduledBackups);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function renderBackupHealthDashboard(backups, servers, scheduledBackups = []) {
    const tbody = document.getElementById('backup-health-body');
    if (!tbody) return;

    if (!servers || servers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="no-data">No servers available</td></tr>';
        return;
    }

    const backupsByServer = new Map();
    backups.forEach(backup => {
        const serverId = parseInt(backup.ldap_server_id);
        if (!backupsByServer.has(serverId)) {
            backupsByServer.set(serverId, []);
        }
        backupsByServer.get(serverId).push(backup);
    });

    const schedulesByServer = new Map();
    (scheduledBackups || []).forEach(schedule => {
        const serverId = parseInt(schedule.ldap_server_id);
        if (!schedulesByServer.has(serverId)) {
            schedulesByServer.set(serverId, []);
        }
        schedulesByServer.get(serverId).push(schedule);
    });

    const formatAgeHuman = (date) => {
        if (!date) return '-';
        const now = new Date();
        const diffMs = now - new Date(date);
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    };

    const rows = servers.map(server => {
        const serverId = parseInt(server.id);
        const serverName = server.name || 'Unknown Server';
        const serverBackups = (backupsByServer.get(serverId) || []).slice();
        serverBackups.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        if (serverBackups.length === 0) {
            return `
                <tr>
                    <td>${escapeHtml(serverName)}</td>
                    <td colspan="10" class="no-data">No backups yet</td>
                </tr>
            `;
        }

        const lastBackup = serverBackups[0];
        const lastBackupTime = lastBackup.created_at
            ? new Date(lastBackup.created_at).toLocaleString()
            : 'Unknown';
        const lastStatusClass = lastBackup.status ? `status-${lastBackup.status.replace('_', '-')}` : '';

        const lastSuccess = serverBackups.find(b => b.status === 'completed');
        const lastFailure = serverBackups.find(b => b.status === 'failed');

        let failureStreak = 0;
        for (const backup of serverBackups) {
            if (backup.status === 'failed') {
                failureStreak += 1;
            } else {
                break;
            }
        }

        // Calculate 24h backup count
        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const backupsIn24h = serverBackups.filter(b => new Date(b.created_at) > oneDayAgo).length;

        // Get next scheduled backup
        const schedules = schedulesByServer.get(serverId) || [];
        let nextScheduledTime = '-';
        const activeSchedules = schedules.filter(s => s.is_active);
        if (activeSchedules.length > 0) {
            const nextSchedule = activeSchedules.reduce((min, s) => {
                const nextRun = new Date(s.next_run);
                const minRun = new Date(min.next_run);
                return nextRun < minRun ? s : min;
            });
            if (nextSchedule.next_run) {
                nextScheduledTime = new Date(nextSchedule.next_run).toLocaleString();
            }
        }

        // Detect missed schedule
        let missedSchedule = '-';
        if (activeSchedules.length > 0) {
            const nextSchedDate = new Date(activeSchedules[0].next_run);
            const now = new Date();
            const hasRecentBackup = lastBackup && new Date(lastBackup.created_at) > nextSchedDate;
            if (nextSchedDate < now && !hasRecentBackup) {
                missedSchedule = '<span class="status-badge status-failed">YES</span>';
            } else {
                missedSchedule = 'No';
            }
        }

        return `
            <tr>
                <td>${escapeHtml(serverName)}</td>
                <td>${escapeHtml(lastBackupTime)}</td>
                <td>
                    ${lastBackup.status
                        ? `<span class="status-badge ${lastStatusClass}">${escapeHtml(lastBackup.status)}</span>`
                        : 'Unknown'}
                </td>
                <td>${lastSuccess?.created_at ? escapeHtml(new Date(lastSuccess.created_at).toLocaleString()) : '-'}</td>
                <td>${escapeHtml(formatAgeHuman(lastSuccess?.created_at))}</td>
                <td>${lastFailure?.created_at ? escapeHtml(new Date(lastFailure.created_at).toLocaleString()) : '-'}</td>
                <td>${escapeHtml(formatAgeHuman(lastFailure?.created_at))}</td>
                <td>${failureStreak}</td>
                <td>${escapeHtml(nextScheduledTime)}</td>
                <td>${backupsIn24h}</td>
                <td>${missedSchedule}</td>
            </tr>
        `;
    });

    tbody.innerHTML = rows.join('');
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
                    <button class="btn btn-primary btn-sm" onclick="backupServer(${parseInt(server.id)})">Backup Now</button>
                    <button class="btn btn-info btn-sm" onclick="showEditServerModal(${parseInt(server.id)})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteServer(${parseInt(server.id)}, '${escapeHtml(server.name)}')">Delete</button>
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
        // Fetch both backups and servers in parallel
        const [backupsResponse, serversResponse] = await Promise.all([
            fetch(`${API_URL}/backups/?status=completed`, {
                headers: authHeaders()
            }),
            fetch(`${API_URL}/ldap-servers/`, {
                headers: authHeaders()
            })
        ]);

        if (!backupsResponse.ok) {
            throw new Error(`Failed to load backups: ${backupsResponse.status} ${backupsResponse.statusText}`);
        }

        const backups = await backupsResponse.json();
        const servers = serversResponse.ok ? await serversResponse.json() : [];
        
        // Create server lookup map
        const serverMap = new Map(servers.map(s => [parseInt(s.id), s.name]));

        if (backups.length === 0) {
            select.innerHTML = '<option value="">No completed backups available</option>';
            return;
        }

        select.innerHTML = backups.map(backup => {
            const id = parseInt(backup.id);
            const serverId = parseInt(backup.ldap_server_id);
            const serverName = serverMap.get(serverId) || 'Unknown Server';
            const date = new Date(backup.created_at).toLocaleString(undefined, { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            const label = `#${id} - ${serverName} - ${date} (${backup.backup_type})`;
            const isSelected = selectedId && id === parseInt(selectedId);
            return `<option value="${id}"${isSelected ? ' selected' : ''}>${label}</option>`;
        }).join('');
    } catch (error) {
        console.error('Error loading backup options:', error);
        select.innerHTML = '<option value="">Failed to load backups</option>';
    }
}

// Load feature flags
async function loadFeatureFlags() {
    try {
        const response = await fetch(`${API_URL}/config/features`, { headers: authHeaders() });
        if (response.ok) {
            featureFlags = await response.json();
        }
    } catch (error) {
        console.error('Error loading feature flags:', error);
        // Default to disabled if fetch fails
        featureFlags = { cloud_storage_enabled: false, cloud_provider: null };
    }
}

// Load backups
async function loadBackups() {
    paginationState.backups.skip = 0;
    paginationState.backups.allItems = [];
    
    // Show/hide cloud filter based on feature flag
    const cloudFilterGroup = document.querySelector('#filter-cloud')?.parentElement;
    if (cloudFilterGroup) {
        cloudFilterGroup.style.display = featureFlags.cloud_storage_enabled ? '' : 'none';
    }
    
    await loadBackupsPage();
}

async function loadBackupsPage() {
    try {
        const refreshStatus = document.getElementById('backups-refresh-status');
        if (refreshStatus && paginationState.backups.skip === 0) {
            refreshStatus.textContent = 'Refreshing...';
        }

        const [backupsResponse, serversResponse] = await Promise.all([
            fetch(`${API_URL}/backups/?skip=${paginationState.backups.skip}&limit=${paginationState.backups.limit}`, { headers: authHeaders() }),
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() })
        ]);

        if (!backupsResponse.ok) {
            throw new Error(`Failed to load backups: ${backupsResponse.status} ${backupsResponse.statusText}`);
        }

        const newBackups = await backupsResponse.json();
        const servers = serversResponse.ok ? await serversResponse.json() : [];

        const sensitiveCategories = ['acl', 'schema', 'config', 'certificates'];
        const visibleBackups = newBackups.filter(backup => !sensitiveCategories.includes(backup.category));
        
        // Add new items to the list
        paginationState.backups.allItems.push(...visibleBackups);
        
        // Check if there are more items
        paginationState.backups.hasMore = visibleBackups.length === paginationState.backups.limit;
        
        // Render backups
        renderBackups(paginationState.backups.allItems, servers);
        
        // Keep load more button hidden (using View All per-server buttons instead)
        const loadMoreBtn = document.getElementById('loadMoreBackupsBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
        
        if (refreshStatus && paginationState.backups.skip === 0) {
            refreshStatus.textContent = `Updated ${new Date().toLocaleTimeString()}`;
        }
    } catch (error) {
        console.error('Error loading backups:', error);
        const refreshStatus = document.getElementById('backups-refresh-status');
        if (refreshStatus) {
            refreshStatus.textContent = 'Refresh failed';
        }
    }
}

async function loadMoreBackups() {
    paginationState.backups.skip += paginationState.backups.limit;
    await loadBackupsPage();
}

function renderBackups(backups, servers) {
    const serverMap = new Map(servers.map(server => [parseInt(server.id), server.name]));
    const tbody = document.getElementById('backups-tbody');
    const ITEMS_PER_SERVER = 5;
    
    if (backups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No backups found</td></tr>';
        return;
    }
    
    const groupedBackups = new Map();
    backups.forEach(backup => {
        const serverName = serverMap.get(parseInt(backup.ldap_server_id)) || 'Unknown Server';
        if (!groupedBackups.has(serverName)) {
            groupedBackups.set(serverName, []);
        }
        groupedBackups.get(serverName).push(backup);
    });

    const backupRows = [];
    Array.from(groupedBackups.keys()).sort((a, b) => a.localeCompare(b)).forEach(serverName => {
        const serverBackups = groupedBackups.get(serverName);
        const showCount = Math.min(ITEMS_PER_SERVER, serverBackups.length);
        
        backupRows.push(`
            <tr class="group-row">
                <td colspan="8"><span class="group-label">${escapeHtml(serverName)}</span></td>
            </tr>
        `);

        backupRows.push(serverBackups.slice(0, showCount).map(backup => `
            <tr>
                <td>
                    <input type="checkbox" class="backup-checkbox" value="${parseInt(backup.id)}" onchange="updateBatchDeleteButton()">
                </td>
                <td>${escapeHtml(serverName)}</td>
                <td>${escapeHtml(backup.backup_type)}</td>
                <td>
                    <!-- Note: status is a backend enum value (pending|in_progress|completed|failed), safe for use in CSS class -->
                    <span class="status-badge status-${backup.status.replace('_', '-')}">
                        ${escapeHtml(backup.status)}
                    </span>
                    ${backup.retry_count > 0 ? `<br><small style="color: #856404;">🔄 Retry ${backup.retry_count}/${backup.max_retries}</small>` : ''}
                    ${backup.next_retry_at && backup.status === 'pending' ? `<br><small style="color: #2563eb;">Next: ${new Date(backup.next_retry_at).toLocaleTimeString()}</small>` : ''}
                    ${backup.verification_status ? `<br><small class="verification-badge verification-${backup.verification_status}">${getVerificationIcon(backup.verification_status)} ${backup.verification_status}</small>` : ''}
                    ${backup.cloud_uploaded ? `<br><small class="cloud-badge cloud-uploaded">☁️ Cloud: ${backup.cloud_provider || 'uploaded'}</small>` : ''}
                </td>
                <td>${backup.file_size ? formatBytes(backup.file_size) : 'N/A'}</td>
                <td>${backup.entry_count ? parseInt(backup.entry_count) : 'N/A'}</td>
                <td>${new Date(backup.created_at).toLocaleString()}</td>
                <td class="action-cell">
                    ${backup.status === 'completed'
                        ? `<button class="btn btn-secondary" onclick="showBackupContent(${parseInt(backup.id)})">View</button>
                           <button class="btn btn-secondary" onclick="showBackupDiffModal(${parseInt(backup.id)})">Diff</button>
                           <button class="btn btn-info" onclick="downloadBackupContent(${parseInt(backup.id)})">Download</button>
                           <button class="btn btn-success" onclick="restoreBackup(${parseInt(backup.id)})" ${backup.cloud_uploaded && !backup.file_path ? 'title="✨ Will auto-download from cloud storage"' : ''}>Restore${backup.cloud_uploaded && !backup.file_path ? ' ☁️' : ''}</button>
                           <button class="btn btn-secondary" onclick="verifyBackup(${parseInt(backup.id)})">Verify</button>
                           ${featureFlags.cloud_storage_enabled ? (
                               backup.cloud_uploaded 
                                   ? `<button class="btn btn-secondary" onclick="downloadFromCloud(${parseInt(backup.id)})" title="Manually download from cloud to local storage">⬇️ Cloud</button>`
                                   : `<button class="btn btn-secondary" onclick="uploadToCloud(${parseInt(backup.id)})" title="Upload to cloud storage">☁️ Upload</button>`
                           ) : ''}
                           <button class="btn btn-danger" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>`
                        : `<button class="btn btn-danger" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>`}
                </td>
            </tr>
        `).join(''));
        
        // Add "Load More" button row if there are more backups
        if (serverBackups.length > ITEMS_PER_SERVER) {
            backupRows.push(`
                <tr>
                    <td colspan="8" style="text-align: center; padding: 10px;">
                        <button class="btn btn-secondary" data-server-id="${serverBackups[0].ldap_server_id}" onclick="viewServerBackups(this.dataset.serverId, '${escapeHtml(serverName).replace(/'/g, "&#39;")}')">View All (${serverBackups.length} total)</button>
                    </td>
                </tr>
            `);
        }
    });

    tbody.innerHTML = backupRows.join('');

    const selectAll = document.getElementById('select-all-backups');
    if (selectAll) {
        selectAll.checked = false;
    }
    if (typeof updateBatchDeleteButton === 'function') {
        updateBatchDeleteButton();
    }
}

async function viewServerBackups(serverId, displayServerName) {
    // Parse serverId as integer
    serverId = parseInt(serverId);
    
    // Create and show modal with all backups for the selected server
    let modal = document.getElementById('serverBackupsModal');
    
    if (!modal) {
        // Create modal if it doesn't exist
        modal = document.createElement('div');
        modal.id = 'serverBackupsModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h2 id="serverBackupsTitle"></h2>
                    <span class="close" onclick="closeServerBackupsModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <table id="serverBackupsTable" class="data-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="select-all-server-backups" onchange="toggleAllServerBackups(this)"></th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Size</th>
                                <th>Entries</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="serverBackupsTbody"></tbody>
                    </table>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeServerBackupsModal()">Close</button>
                    <button class="btn btn-danger" id="serverBackupDeleteBtn" onclick="batchDeleteServerBackups()" style="display:none;">Delete Selected</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Show modal
    modal.style.display = 'block';
    modal.style.zIndex = '1500';  // Set z-index higher than default modals
    document.getElementById('serverBackupsTitle').textContent = `All Backups for ${escapeHtml(displayServerName)}`;
    
    // Show loading state
    const tbody = document.getElementById('serverBackupsTbody');
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Loading...</td></tr>';
    const selectAllCheckbox = document.getElementById('select-all-server-backups');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }
    
    // Fetch backups for this server
    try {
        const response = await fetch(`${API_URL}/backups/?skip=0&limit=1000`, {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch backups: ${response.status}`);
        }
        
        const backups = await response.json();
        
        // Filter backups for this server by ID
        const filteredBackups = backups.filter(backup => parseInt(backup.ldap_server_id) === serverId);
        
        console.log(`Loaded ${backups.length} backups total, ${filteredBackups.length} for server ${serverId}`);
        
        // Render backups in modal
        if (filteredBackups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--text-secondary);">No backups found for this server</td></tr>';
        } else {
            tbody.innerHTML = filteredBackups.map(backup => `
                <tr>
                    <td>
                        <input type="checkbox" class="server-backup-checkbox" value="${parseInt(backup.id)}" onchange="updateServerBackupDeleteButton()">
                    </td>
                    <td>${escapeHtml(backup.backup_type)}</td>
                    <td>
                        <span class="status-badge status-${backup.status.replace('_', '-')}">
                            ${escapeHtml(backup.status)}
                        </span>
                    </td>
                    <td>${backup.file_size ? formatBytes(backup.file_size) : 'N/A'}</td>
                    <td>${backup.entry_count ? parseInt(backup.entry_count) : 'N/A'}</td>
                    <td>${new Date(backup.created_at).toLocaleString()}</td>
                    <td class="action-cell">
                        ${backup.status === 'completed'
                            ? `<details class="action-menu">
                                <summary class="btn btn-secondary btn-sm">Actions</summary>
                                <div class="action-menu-list">
                                    <button class="btn btn-secondary btn-sm" onclick="showBackupContent(${parseInt(backup.id)})">View</button>
                                    <button class="btn btn-secondary btn-sm" onclick="showBackupDiffModal(${parseInt(backup.id)})">Diff</button>
                                    <button class="btn btn-info btn-sm" onclick="downloadBackupContent(${parseInt(backup.id)})">Download</button>
                                    <button class="btn btn-success btn-sm" onclick="restoreBackup(${parseInt(backup.id)})" ${backup.cloud_uploaded && !backup.file_path ? 'title="✨ Will auto-download from cloud storage"' : ''}>Restore${backup.cloud_uploaded && !backup.file_path ? ' ☁️' : ''}</button>
                                    <button class="btn btn-danger btn-sm" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>
                                </div>
                            </details>`
                            : `<button class="btn btn-danger btn-sm" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>`}
                    </td>
                </tr>
            `).join('');
        }
        
        updateServerBackupDeleteButton();
    } catch (error) {
        showError(`Error loading backups for ${escapeHtml(displayServerName)}: ${error.message}`);
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading backups: ${escapeHtml(error.message)}</td></tr>`;
        console.error('Error:', error);
    }
}

function closeServerBackupsModal() {
    const modal = document.getElementById('serverBackupsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const modal = document.getElementById('serverBackupsModal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
});

function toggleAllServerBackups(checkbox) {
    const checkboxes = document.querySelectorAll('.server-backup-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateServerBackupDeleteButton();
}

function updateServerBackupDeleteButton() {
    const checkboxes = document.querySelectorAll('.server-backup-checkbox:checked');
    const deleteBtn = document.getElementById('serverBackupDeleteBtn');
    deleteBtn.style.display = checkboxes.length > 0 ? 'block' : 'none';
}

async function batchDeleteServerBackups() {
    const checkboxes = document.querySelectorAll('.server-backup-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (ids.length === 0) {
        showError('No backups selected');
        return;
    }
    
    if (!confirm(`Delete ${ids.length} backup(s)? This cannot be undone.`)) {
        return;
    }
    
    try {
        for (const id of ids) {
            const response = await fetch(`${API_URL}/backups/${id}`, {
                method: 'DELETE',
                headers: authHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete backup ${id}`);
            }
        }
        
        showSuccess(`Deleted ${ids.length} backup(s)`);
        closeServerBackupsModal();
        loadBackups();
    } catch (error) {
        showError(`Error deleting backups: ${error.message}`);
        console.error('Error:', error);
    }
}

async function deleteBackup(backupId) {
    const id = parseInt(backupId);

    if (!Number.isFinite(id)) {
        showToast('error', 'Invalid backup id');
        return;
    }

    if (!confirm('Delete this backup? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/backups/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete backup');
        }

        showToast('success', 'Backup deleted successfully');

        const modal = document.getElementById('serverBackupsModal');
        if (modal && modal.style.display === 'block') {
            closeServerBackupsModal();
        }

        await loadBackups();
    } catch (error) {
        console.error('Delete backup error:', error);
        showToast('error', error.message || 'Failed to delete backup');
    }
}

function getVerificationIcon(status) {
    const icons = {
        'verified': '✅',
        'failed': '❌',
        'not_verified': '⚠️',
        'pending': '🔄'
    };
    return icons[status] || '❓';
}

async function verifyBackup(backupId) {
    const id = parseInt(backupId);

    if (!Number.isFinite(id)) {
        showToast('error', 'Invalid backup ID');
        return;
    }

    if (!confirm('Verify this backup? This will check file integrity, checksum, and LDIF syntax.')) {
        return;
    }

    try {
        showToast('info', 'Verifying backup... This may take a moment.');
        
        const response = await fetch(`${API_URL}/backups/verification/${id}`, {
            method: 'POST',
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Verification failed');
        }

        const result = await response.json();
        
        if (result.verified) {
            showToast('success', `✅ Backup verified successfully! ${result.message}`);
        } else {
            showToast('error', `❌ Verification failed: ${result.message}`);
        }

        // Reload backups to show updated verification status
        await loadBackups();
    } catch (error) {
        console.error('Verify backup error:', error);
        showToast('error', error.message || 'Failed to verify backup');
    }
}

async function uploadToCloud(backupId) {
    const id = parseInt(backupId);

    if (!Number.isFinite(id)) {
        showToast('error', 'Invalid backup ID');
        return;
    }

    if (!confirm('Upload this backup to cloud storage? This may take a few moments for large backups.')) {
        return;
    }

    try {
        showToast('info', 'Uploading backup to cloud storage...');
        
        const response = await fetch(`${API_URL}/backups/cloud/${id}/upload`, {
            method: 'POST',
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        
        showToast('success', `☁️ ${result.message}`);

        // Reload backups to show cloud upload status
        await loadBackups();
    } catch (error) {
        console.error('Upload to cloud error:', error);
        showToast('error', error.message || 'Failed to upload backup to cloud storage');
    }
}

async function downloadFromCloud(backupId) {
    const id = parseInt(backupId);

    if (!Number.isFinite(id)) {
        showToast('error', 'Invalid backup ID');
        return;
    }

    if (!confirm('Download this backup from cloud storage to local storage?')) {
        return;
    }

    try {
        showToast('info', 'Downloading backup from cloud storage...');
        
        const response = await fetch(`${API_URL}/backups/cloud/${id}/download`, {
            method: 'POST',
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }

        const result = await response.json();
        
        showToast('success', `⬇️ ${result.message}`);

        // Reload backups to show updated file path
        await loadBackups();
    } catch (error) {
        console.error('Download from cloud error:', error);
        showToast('error', error.message || 'Failed to download backup from cloud storage');
    }
}

// Toggle filter panel visibility
function toggleBackupFilters() {
    const filterPanel = document.getElementById('backup-filters');
    if (filterPanel) {
        filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
        
        // Load servers for filter dropdown if showing
        if (filterPanel.style.display === 'block') {
            populateFilterServers();
        }
    }
}

// Populate filter server  dropdown
async function populateFilterServers() {
    const select = document.getElementById('filter-server');
    if (!select) return;
    
    try {
        const response = await fetch(`${API_URL}/ldap-servers/`, {
            headers: authHeaders()
        });
        
        if (!response.ok) return;
        
        const servers = await response.json();
        
        // Clear existing options except "All Servers"
        select.innerHTML = '<option value="">All Servers</option>';
        
        // Add server options
        servers.forEach(server => {
            const option = document.createElement('option');
            option.value = server.id;
            option.textContent = server.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load servers for filter:', error);
    }
}

// Apply backup filters using advanced search
async function applyBackupFilters() {
    try {
        showToast('info', 'Applying filters...');
        
        // Build filter parameters
        const params = {
            skip: 0,
            limit: 100
        };
        
        // Text search
        const search = document.getElementById('backups-search')?.value;
        if (search) params.search = search;
        
        // Server filter
        const serverId = document.getElementById('filter-server')?.value;
        if (serverId) params.server_id = parseInt(serverId);
        
        // Status filter
        const status = document.getElementById('filter-status')?.value;
        if (status) params.status = status;
        
        // Type filter
        const type = document.getElementById('filter-type')?.value;
        if (type) params.backup_type = type;
        
        // Category filter
        const category = document.getElementById('filter-category')?.value;
        if (category) params.category = category;
        
        // Verification filter
        const verification = document.getElementById('filter-verification')?.value;
        if (verification) params.verification_status = verification;
        
        // Cloud upload filter
        const cloud = document.getElementById('filter-cloud')?.value;
        if (cloud) params.cloud_uploaded = cloud === 'true';
        
        // Date filters
        const createdAfter = document.getElementById('filter-created-after')?.value;
        if (createdAfter) params.created_after = createdAfter;
        
        const createdBefore = document.getElementById('filter-created-before')?.value;
        if (createdBefore) params.created_before = createdBefore;
        
        // Size filters (convert MB to bytes)
        const minSize = document.getElementById('filter-min-size')?.value;
        if (minSize) params.min_size = Math.floor(parseFloat(minSize) * 1024 * 1024);
        
        const maxSize = document.getElementById('filter-max-size')?.value;
        if (maxSize) params.max_size = Math.floor(parseFloat(maxSize) * 1024 * 1024);
        
        // Sort options
        const sortBy = document.getElementById('filter-sort-by')?.value || 'created_at';
        params.sort_by = sortBy;
        
        const sortOrder = document.getElementById('filter-sort-order')?.value || 'desc';
        params.sort_order = sortOrder;
        
        // Call advanced search API
        const response = await fetch(`${API_URL}/backups/catalog/search`, {
            method: 'POST',
            headers: {
                ...authHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error('Filter search failed');
        }
        
        const backups = await response.json();
        
        // Update count
        const countEl = document.getElementById('filter-results-count');
        if (countEl) {
            countEl.textContent = `Found ${backups.length} backup(s)`;
        }
        
        // Fetch servers for rendering
        const serversResponse = await fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() });
        const servers = serversResponse.ok ? await serversResponse.json() : [];
        
        // Render results
        renderBackups(backups, servers);
        
        showToast('success', `Found ${backups.length} backup(s)`);
        
    } catch (error) {
        console.error('Filter error:', error);
        showToast('error', 'Failed to apply filters');
    }
}

// Reset all filters
function resetBackupFilters() {
    // Reset all filter inputs
    document.getElementById('filter-server').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-verification').value = '';
    document.getElementById('filter-cloud').value = '';
    document.getElementById('filter-created-after').value = '';
    document.getElementById('filter-created-before').value = '';
    document.getElementById('filter-min-size').value = '';
    document.getElementById('filter-max-size').value = '';
    document.getElementById('filter-sort-by').value = 'created_at';
    document.getElementById('filter-sort-order').value = 'desc';
    
    const countEl = document.getElementById('filter-results-count');
    if (countEl) {
        countEl.textContent = '';
    }
    
    // Reset search box
    const searchBox = document.getElementById('backups-search');
    if (searchBox) {
        searchBox.value = '';
    }
    
    // Reload backups
    loadBackups();
    
    showToast('info', 'Filters reset');
}

// Export backups to CSV or JSON
async function exportBackups(format) {
    try {
        showToast('info', `Exporting backups as ${format.toUpperCase()}...`);
        
        // Build query parameters from current filters
        const params = new URLSearchParams();
        params.append('format', format);
        
        const serverId = document.getElementById('filter-server')?.value;
        if (serverId) params.append('server_id', serverId);
        
        const status = document.getElementById('filter-status')?.value;
        if (status) params.append('status', status);
        
        const createdAfter = document.getElementById('filter-created-after')?.value;
        if (createdAfter) params.append('created_after', createdAfter);
        
        const createdBefore = document.getElementById('filter-created-before')?.value;
        if (createdBefore) params.append('created_before', createdBefore);
        
        // Make request
        const response = await fetch(`${API_URL}/backups/catalog/export?${params.toString()}`, {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `ldapguard_backups_${new Date().getTime()}.${format}`;
        
        if (contentDisposition) {
            const matches = contentDisposition.match(/filename="?([^"]+)"?/);
            if (matches && matches[1]) {
                filename = matches[1];
            }
        }
        
        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('success', `✅ Exported ${filename}`);
        
    } catch (error) {
        console.error('Export error:', error);
        showToast('error', `Failed to export backups`);
    }
}

async function fetchServersForBackups() {
    try {
        const response = await fetch(`${API_URL}/ldap-servers`, {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch servers: ${response.status}`);
        }
        
        const data = await response.json();
        return data.items || [];
    } catch (error) {
        console.error('Error fetching servers:', error);
        return [];
    }
}

async function showBackupContent(backupId) {
    const modal = document.getElementById('backupContentModal');
    const contentEl = document.getElementById('backupContentBody');
    const metaEl = document.getElementById('backupContentMeta');
    const searchInput = document.getElementById('backupSearchInput');
    const searchResults = document.getElementById('backupSearchResults');
    const limitSelector = document.getElementById('backupLineLimit');

    if (!modal || !contentEl || !metaEl) return;

    contentEl.textContent = '';
    metaEl.textContent = 'Loading...';
    modal.style.display = 'block';
    modal.style.zIndex = '2000';  // Ensure it appears on top of other modals
    
    // Store backup ID for reload functionality
    window.currentBackupId = backupId;
    
    // Reset search
    if (searchInput) searchInput.value = '';
    if (searchResults) searchResults.textContent = '';
    
    // Reset limit selector to default
    if (limitSelector) limitSelector.value = '200';
    
    // Switch to Raw view by default
    switchBackupView('Raw');

    await loadBackupContentWithLimit(backupId, 200);
}

async function loadBackupContentWithLimit(backupId, maxLines) {
    const contentEl = document.getElementById('backupContentBody');
    const metaEl = document.getElementById('backupContentMeta');

    if (!contentEl || !metaEl) return;

    contentEl.textContent = '';
    metaEl.textContent = 'Loading...';

    try {
        // Always send max_lines parameter (0 = no limit)
        const url = `${API_URL}/backups/${parseInt(backupId)}/content?max_lines=${maxLines}`;

        const response = await fetch(url, {
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load backup content');
        }

        const data = await response.json();
        // Ensure content is a string
        if (typeof data.content !== 'string') {
            console.error('ERROR: content is not a string!', data.content);
            throw new Error('Invalid response format: content is not a string');
        }
        
        // Store original content for searching
        window.backupOriginalContent = data.content;
        contentEl.textContent = window.backupOriginalContent;
        
        // Update meta information
        if (maxLines === 0) {
            metaEl.textContent = `Showing all ${data.lines} lines`;
        } else {
            metaEl.textContent = data.truncated
                ? `Showing first ${data.lines} lines (truncated)`
                : `Showing ${data.lines} lines`;
        }
    } catch (error) {
        contentEl.textContent = '';
        metaEl.textContent = error.message || 'Failed to load backup content';
        window.backupOriginalContent = '';
    }
}

function reloadBackupContent() {
    const limitSelector = document.getElementById('backupLineLimit');
    if (!limitSelector || !window.currentBackupId) return;
    
    const limit = parseInt(limitSelector.value);
    loadBackupContentWithLimit(window.currentBackupId, limit);
}

function closeBackupContentModal() {
    const modal = document.getElementById('backupContentModal');
    if (modal) {
        modal.style.display = 'none';
    }
    window.backupOriginalContent = '';
    window.currentBackupId = null;
}

function searchBackupContent() {
    const searchInput = document.getElementById('backupSearchInput');
    const contentEl = document.getElementById('backupContentBody');
    const searchResults = document.getElementById('backupSearchResults');
    
    if (!searchInput || !contentEl || !window.backupOriginalContent) return;
    
    const searchTerm = searchInput.value.trim().toLowerCase();
    
    if (!searchTerm) {
        // Restore original content if search is cleared
        contentEl.textContent = window.backupOriginalContent;
        searchResults.textContent = '';
        return;
    }
    
    const content = window.backupOriginalContent;
    const lines = content.split('\n');
    const matchIndices = [];
    
    // Find all lines matching the search term
    lines.forEach((line, index) => {
        if (line.toLowerCase().includes(searchTerm)) {
            matchIndices.push(index);
        }
    });
    
    // Highlight matching lines
    const highlightedLines = lines.map((line, index) => {
        if (matchIndices.includes(index)) {
            // Highlight the matching part
            const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            return line.replace(regex, '<mark>$1</mark>');
        }
        return line;
    });
    
    // Display results
    contentEl.innerHTML = highlightedLines.join('\n');
    searchResults.textContent = `${matchIndices.length} match${matchIndices.length !== 1 ? 'es' : ''} found`;
    
    // Scroll to first match if there are any
    if (matchIndices.length > 0) {
        const firstMatchLine = lines[matchIndices[0]];
        setTimeout(() => {
            const marks = contentEl.querySelectorAll('mark');
            if (marks.length > 0) {
                marks[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }
}

function clearBackupSearch() {
    const searchInput = document.getElementById('backupSearchInput');
    const contentEl = document.getElementById('backupContentBody');
    const searchResults = document.getElementById('backupSearchResults');
    
    if (searchInput) searchInput.value = '';
    if (contentEl && window.backupOriginalContent) {
        contentEl.textContent = window.backupOriginalContent;
    }
    if (searchResults) searchResults.textContent = '';
}

// ===== LDIF Parser & Enhanced Viewer =====

function parseLDIF(ldifContent) {
    const entries = [];
    const lines = ldifContent.split('\n');
    let currentEntry = null;
    let currentAttr = null;
    let currentValue = '';

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Skip empty lines
        if (!line.trim()) {
            if (currentEntry && currentAttr) {
                currentEntry.attributes[currentAttr] = currentEntry.attributes[currentAttr] || [];
                currentEntry.attributes[currentAttr].push(currentValue.trim());
                currentAttr = null;
                currentValue = '';
            }
            if (currentEntry && Object.keys(currentEntry.attributes).length > 0) {
                entries.push(currentEntry);
                currentEntry = null;
            }
            continue;
        }
        
        // Skip comments
        if (line.startsWith('#')) continue;
        
        // Continuation line (starts with space)
        if (line.startsWith(' ') && currentAttr) {
            currentValue += line.substring(1);
            continue;
        }
        
        // Save previous attribute
        if (currentAttr) {
            currentEntry.attributes[currentAttr] = currentEntry.attributes[currentAttr] || [];
            currentEntry.attributes[currentAttr].push(currentValue.trim());
            currentValue = '';
        }
        
        // Parse attribute: value
        const colonIndex = line.indexOf(':');
        if (colonIndex === -1) continue;
        
        const attr = line.substring(0, colonIndex).trim();
        let value = line.substring(colonIndex + 1).trim();
        
        // Handle base64 encoded values (::)
        if (value.startsWith(':')) {
            value = value.substring(1).trim();
            value = `[base64: ${value.substring(0, 20)}...]`;
        }
        
        // Start new entry on 'dn:'
        if (attr.toLowerCase() === 'dn') {
            if (currentEntry && Object.keys(currentEntry.attributes).length > 0) {
                entries.push(currentEntry);
            }
            currentEntry = {
                dn: value,
                attributes: {}
            };
            currentAttr = null;
        } else {
            currentAttr = attr;
            currentValue = value;
        }
    }
    
    // Add last entry
    if (currentEntry) {
        if (currentAttr) {
            currentEntry.attributes[currentAttr] = currentEntry.attributes[currentAttr] || [];
            currentEntry.attributes[currentAttr].push(currentValue.trim());
        }
        if (Object.keys(currentEntry.attributes).length > 0) {
            entries.push(currentEntry);
        }
    }
    
    return entries;
}

function buildDNTree(entries) {
    if (!entries || entries.length === 0) {
        return { 
            rdn: 'Root', 
            dn: '', 
            children: new Map(), 
            entry: null,
            level: 0
        };
    }
    
    const root = { 
        rdn: 'Root', 
        dn: '', 
        children: new Map(), 
        entry: null,
        level: 0
    };
    
    entries.forEach(entry => {
        if (!entry || !entry.dn) return;
        
        // Split DN into RDN components (reverse for top-down tree)
        const rdnParts = entry.dn.split(',').map(s => s.trim()).reverse();
        let currentNode = root;
        let currentDN = '';
        
        rdnParts.forEach((rdn, index) => {
            if (!rdn) return;
            
            // Build full DN up to this point
            if (index === 0) {
                currentDN = rdn;
            } else {
                currentDN = rdn + ',' + currentDN;
            }
            
            // Check if this RDN node exists
            if (!currentNode.children.has(rdn)) {
                currentNode.children.set(rdn, {
                    rdn: rdn,
                    dn: currentDN,
                    children: new Map(),
                    entry: null,
                    level: index + 1
                });
            }
            
            currentNode = currentNode.children.get(rdn);
        });
        
        // Attach the full entry data to the leaf node
        currentNode.entry = entry;
    });
    
    return root;
}

function switchBackupView(viewType) {
    // Hide all views
    document.getElementById('backupRawView').style.display = 'none';
    document.getElementById('backupParsedView').style.display = 'none';
    document.getElementById('backupTreeView').style.display = 'none';
    
    // Remove active class from all tabs
    document.querySelectorAll('.backup-view-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected view and activate tab
    const viewElement = document.getElementById(`backup${viewType}View`);
    const tabElement = document.querySelector(`.backup-view-tab[data-view="${viewType}"]`);
    
    if (viewElement) viewElement.style.display = 'block';
    if (tabElement) tabElement.classList.add('active');
    
    // Render view content if needed
    if (viewType === 'Parsed' && window.backupOriginalContent) {
        renderParsedView();
    } else if (viewType === 'Tree' && window.backupOriginalContent) {
        renderTreeView();
    }
}

function renderParsedView() {
    const container = document.getElementById('backupParsedContent');
    const searchInput = document.getElementById('parsedSearchInput');
    
    if (!container || !window.backupOriginalContent) return;
    
    const entries = parseLDIF(window.backupOriginalContent);
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    // Filter entries based on search
    const filteredEntries = searchTerm
        ? entries.filter(entry => {
            const dnMatch = entry.dn.toLowerCase().includes(searchTerm);
            const attrMatch = Object.entries(entry.attributes).some(([key, values]) => {
                return key.toLowerCase().includes(searchTerm) ||
                       values.some(v => v.toLowerCase().includes(searchTerm));
            });
            return dnMatch || attrMatch;
        })
        : entries;
    
    // Render entries
    container.innerHTML = filteredEntries.map((entry, index) => {
        const objectClasses = entry.attributes.objectClass || [];
        const icon = getEntryIcon(objectClasses);
        
        const attributesHtml = Object.entries(entry.attributes)
            .map(([key, values]) => {
                const valuesHtml = values.map(v => 
                    `<div class="attr-value">${escapeHtml(v)}</div>`
                ).join('');
                return `
                    <div class="ldap-attribute">
                        <div class="attr-name">${escapeHtml(key)}</div>
                        <div class="attr-values">${valuesHtml}</div>
                    </div>
                `;
            })
            .join('');
        
        return `
            <div class="ldap-entry-card" id="entry-${index}">
                <div class="entry-header" onclick="toggleEntryCard(${index})">
                    <span class="entry-icon">${icon}</span>
                    <span class="entry-dn">${escapeHtml(entry.dn)}</span>
                    <span class="entry-toggle">▶</span>
                </div>
                <div class="entry-attributes" id="entry-attrs-${index}" style="display: none;">
                    ${attributesHtml}
                </div>
            </div>
        `;
    }).join('');
    
    // Update count
    const countElement = document.getElementById('parsedEntryCount');
    if (countElement) {
        countElement.textContent = `${filteredEntries.length} ${filteredEntries.length === 1 ? 'entry' : 'entries'}`;
    }
}

function renderTreeView() {
    const container = document.getElementById('backupTreeContent');
    if (!container || !window.backupOriginalContent) {
        if (container) container.innerHTML = '<div style="padding: 20px; color: var(--text-secondary);">No backup content loaded</div>';
        return;
    }
    
    try {
        const entries = parseLDIF(window.backupOriginalContent);
        
        if (!entries || entries.length === 0) {
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">No LDAP entries found in backup</div>';
            return;
        }
        
        const tree = buildDNTree(entries);
        if (!tree) {
            container.innerHTML = '<div style="padding: 20px; color: var(--text-secondary);">Error building tree structure</div>';
            return;
        }
        
        window.treeData = tree;  // Store for search/expand functionality
        
        let html = '<div class="tree-root">';
        // Render all root children
        if (tree.children && tree.children.size > 0) {
            tree.children.forEach((childNode) => {
                const nodeHtml = renderTreeNode(childNode);
                if (nodeHtml) {
                    html += nodeHtml;
                }
            });
        } else {
            // Fallback: display all entries as flat list
            html += entries.map((entry, idx) => `
                <div class="tree-node-item" data-dn="${escapeHtml(entry.dn)}">
                    <div class="tree-node-header" onclick="selectTreeEntry('${escapeHtml(entry.dn)}', event)" style="cursor: pointer; padding: 8px;">
                        <span class="tree-icon">📄</span>
                        <span class="tree-label">${escapeHtml(entry.dn)}</span>
                    </div>
                </div>
            `).join('');
        }
        html += '</div>';
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error rendering tree:', error);
        container.innerHTML = `<div style="padding: 20px; color: red; font-size: 12px;">Error: ${error.message}</div>`;
    }
}

function renderTreeNode(node) {
    if (!node) return '';
    
    const hasChildren = node.children && node.children.size > 0;
    const hasEntry = node.entry !== null && node.entry !== undefined;
    const nodeId = `tree-${(node.dn || 'root').replace(/[^a-zA-Z0-9]/g, '_')}-${Math.random()}`;
    
    // Determine icon based on entry type or if it's a container
    let icon = '📁';
    if (hasEntry && node.entry && node.entry.attributes && node.entry.attributes.objectClass) {
        icon = getEntryIcon(node.entry.attributes.objectClass);
    } else if (!hasChildren) {
        icon = '📄';
    }
    
    const indent = (node.level || 0) * 20;
    const displayRdn = node.rdn || node.dn || 'Unknown';
    const displayDn = node.dn || '';
    
    let html = `
        <div class="tree-node-item" data-dn="${escapeHtml(displayDn)}">
            <div class="tree-node-header" style="padding-left: ${indent}px;" onclick="toggleTreeNode('${nodeId}', event)">
                <span class="tree-toggle">${hasChildren ? '▶' : '&nbsp;&nbsp;'}</span>
                <span class="tree-icon">${icon}</span>
                <span class="tree-label" onclick="selectTreeEntry('${escapeHtml(displayDn)}', event)">${escapeHtml(displayRdn)}</span>
            </div>
    `;
    
    if (hasChildren) {
        html += `<div class="tree-children" id="${nodeId}" style="display: none;">`;
        
        try {
            // Sort children alphabetically
            const sortedChildren = Array.from(node.children.entries()).sort((a, b) => 
                a[0].localeCompare(b[0])
            );
            
            sortedChildren.forEach(([rdn, childNode]) => {
                if (childNode) {
                    html += renderTreeNode(childNode);
                }
            });
        } catch (e) {
            console.error('Error rendering child nodes:', e);
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    
    return html;
}

function getEntryIcon(objectClasses) {
    const classes = objectClasses.map(c => c.toLowerCase());
    
    if (classes.includes('person') || classes.includes('inetorgperson')) return '👤';
    if (classes.includes('groupofnames') || classes.includes('groupofuniquenames')) return '👥';
    if (classes.includes('organizationalunit') || classes.includes('organization')) return '🏢';
    if (classes.includes('domain')) return '🌐';
    if (classes.includes('device') || classes.includes('computer')) return '💻';
    if (classes.includes('applicationprocess')) return '⚙️';
    
    return '📄';
}

function toggleEntryCard(index) {
    const attrs = document.getElementById(`entry-attrs-${index}`);
    const card = document.getElementById(`entry-${index}`);
    
    if (!attrs || !card) return;
    
    const isHidden = attrs.style.display === 'none';
    attrs.style.display = isHidden ? 'block' : 'none';
    
    const toggle = card.querySelector('.entry-toggle');
    if (toggle) {
        toggle.textContent = isHidden ? '▼' : '▶';
    }
}

function toggleTreeNode(nodeId, event) {
    if (event) event.stopPropagation();
    
    const childrenDiv = document.getElementById(nodeId);
    if (!childrenDiv) return;
    
    const isExpanded = childrenDiv.style.display === 'block';
    childrenDiv.style.display = isExpanded ? 'none' : 'block';
    
    // Update toggle icon
    const header = childrenDiv.previousElementSibling;
    if (header && header.classList.contains('tree-node-header')) {
        const toggle = header.querySelector('.tree-toggle');
        if (toggle) {
            toggle.innerHTML = isExpanded ? '▶' : '▼';
        }
    }
}

function selectTreeEntry(dn, event) {
    if (event) event.stopPropagation();
    
    // Switch to parsed view and show this entry
    switchBackupView('Parsed');
    
    const searchInput = document.getElementById('parsedSearchInput');
    if (searchInput) {
        searchInput.value = dn;
        renderParsedView();
        
        // Scroll to the entry after a short delay
        setTimeout(() => {
            const firstCard = document.querySelector('.ldap-entry-card');
            if (firstCard) {
                firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
}

function expandAllTreeNodes() {
    const allChildren = document.querySelectorAll('.tree-children');
    allChildren.forEach(child => {
        child.style.display = 'block';
    });
    
    const allToggles = document.querySelectorAll('.tree-toggle');
    allToggles.forEach(toggle => {
        if (toggle.innerHTML.trim() === '▶') {
            toggle.innerHTML = '▼';
        }
    });
}

function collapseAllTreeNodes() {
    const allChildren = document.querySelectorAll('.tree-children');
    allChildren.forEach(child => {
        child.style.display = 'none';
    });
    
    const allToggles = document.querySelectorAll('.tree-toggle');
    allToggles.forEach(toggle => {
        if (toggle.innerHTML.trim() === '▼') {
            toggle.innerHTML = '▶';
        }
    });
}

function searchTreeView() {
    const searchInput = document.getElementById('treeSearchInput');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    const allNodes = document.querySelectorAll('.tree-node-item');
    
    if (!searchTerm) {
        // Show all nodes
        allNodes.forEach(node => {
            node.style.display = '';
        });
        return;
    }
    
    // Hide all first, then show matching ones and their parents
    allNodes.forEach(node => {
        const dn = node.getAttribute('data-dn') || '';
        if (dn.toLowerCase().includes(searchTerm)) {
            node.style.display = '';
            // Expand parents
            let parent = node.parentElement;
            while (parent) {
                if (parent.classList && parent.classList.contains('tree-children')) {
                    parent.style.display = 'block';
                    // Update toggle
                    const header = parent.previousElementSibling;
                    if (header) {
                        const toggle = header.querySelector('.tree-toggle');
                        if (toggle) toggle.innerHTML = '▼';
                    }
                }
                parent = parent.parentElement;
            }
        } else {
            node.style.display = 'none';
        }
    });
}

function searchParsedEntries() {
    renderParsedView();
}

function clearParsedSearch() {
    const searchInput = document.getElementById('parsedSearchInput');
    if (searchInput) {
        searchInput.value = '';
        renderParsedView();
    }
}

function jumpToSection(sectionName) {
    const contentEl = document.getElementById('backupContentBody');
    const searchInput = document.getElementById('backupSearchInput');
    
    if (!contentEl || !window.backupOriginalContent) return;
    
    const content = window.backupOriginalContent;
    const lines = content.split('\n');
    
    // Find lines that match the section (e.g., ou=users, ou=app, etc.)
    let foundIndex = -1;
    const searchPatterns = [
        `ou=${sectionName}`,
        `cn=${sectionName}`,
        sectionName // fallback to any mention
    ];
    
    for (const pattern of searchPatterns) {
        foundIndex = lines.findIndex(line => line.toLowerCase().includes(pattern.toLowerCase()));
        if (foundIndex !== -1) break;
    }
    
    if (foundIndex === -1) {
        showToast('info', `Section "${sectionName}" not found in backup`);
        return;
    }
    
    // Set search input and perform search
    searchInput.value = sectionName;
    searchBackupContent();
    
    // Scroll to the section
    setTimeout(() => {
        const marks = contentEl.querySelectorAll('mark');
        if (marks.length > 0) {
            marks[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

async function downloadBackupContent(backupId) {
    try {
        const response = await fetch(`${API_URL}/backups/${parseInt(backupId)}/download`, {
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to download backup');
        }

        const blob = await response.blob();
        const disposition = response.headers.get('content-disposition') || '';
        const match = disposition.match(/filename="([^"]+)"/i);
        const filename = match ? match[1] : `backup-${parseInt(backupId)}.ldif`;

        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        showToast('error', error.message || 'Failed to download backup');
    }
}

async function showBackupDiffModal(backupId) {
    const modal = document.getElementById('backupDiffModal');
    const metaEl = document.getElementById('backupDiffMeta');
    const bodyEl = document.getElementById('backupDiffBody');

    if (!modal || !metaEl || !bodyEl) return;

    window.currentDiffBaseId = parseInt(backupId);
    modal.style.display = 'block';
    modal.style.zIndex = '2000';
    metaEl.textContent = `Select a backup to compare with #${window.currentDiffBaseId}.`;
    bodyEl.innerHTML = '';

    await loadBackupDiffOptions(window.currentDiffBaseId);
}

async function loadBackupDiffOptions(baseId) {
    const select = document.getElementById('backupDiffTarget');
    if (!select) return;

    select.innerHTML = '<option value="">Loading...</option>';

    try {
        const response = await fetch(`${API_URL}/backups/?status=completed&limit=1000`, {
            headers: authHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to load backups: ${response.status}`);
        }

        const backups = await response.json();
        const options = backups
            .filter(backup => parseInt(backup.id) !== parseInt(baseId))
            .map(backup => {
                const createdAt = backup.created_at ? new Date(backup.created_at).toLocaleString() : 'Unknown time';
                const label = `#${parseInt(backup.id)} - ${backup.category || 'category'} - ${createdAt}`;
                return `<option value="${parseInt(backup.id)}">${label}</option>`;
            });

        select.innerHTML = '<option value="">Select a backup...</option>' + options.join('');
    } catch (error) {
        select.innerHTML = '<option value="">Failed to load backups</option>';
        showToast('error', error.message || 'Failed to load backups');
    }
}

async function runBackupDiff() {
    const targetSelect = document.getElementById('backupDiffTarget');
    const metaEl = document.getElementById('backupDiffMeta');
    const bodyEl = document.getElementById('backupDiffBody');

    if (!targetSelect || !metaEl || !bodyEl || !window.currentDiffBaseId) return;

    const targetId = parseInt(targetSelect.value);
    if (!Number.isFinite(targetId)) {
        showToast('error', 'Select a backup to compare');
        return;
    }

    metaEl.textContent = 'Loading diff...';
    bodyEl.innerHTML = '';

    try {
        const response = await fetch(
            `${API_URL}/backups/${window.currentDiffBaseId}/diff?against_id=${targetId}`,
            { headers: authHeaders() }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load diff');
        }

        const data = await response.json();
        const diffText = data.diff || '';

        if (diffText.length === 0) {
            bodyEl.innerHTML = '<tr class="diff-meta"><td colspan="4">No differences found.</td></tr>';
            metaEl.textContent = 'No differences found.';
            return;
        }

        bodyEl.innerHTML = renderSideBySideDiff(diffText);

        metaEl.textContent = data.truncated
            ? `Showing first ${data.lines} diff lines (truncated)`
            : `Showing ${data.lines} diff lines`;
    } catch (error) {
        metaEl.textContent = error.message || 'Failed to load diff';
        bodyEl.innerHTML = '';
    }
}

function closeBackupDiffModal() {
    const modal = document.getElementById('backupDiffModal');
    if (modal) {
        modal.style.display = 'none';
    }
    window.currentDiffBaseId = null;
    const bodyEl = document.getElementById('backupDiffBody');
    if (bodyEl) {
        bodyEl.innerHTML = '';
    }
}

function renderSideBySideDiff(diffText) {
    const lines = diffText.split('\n');
    let leftLine = 0;
    let rightLine = 0;
    const rows = [];

    for (const rawLine of lines) {
        if (rawLine.startsWith('@@')) {
            const match = rawLine.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
            if (match) {
                leftLine = parseInt(match[1], 10) - 1;
                rightLine = parseInt(match[2], 10) - 1;
            }
            rows.push(`<tr class="diff-hunk"><td colspan="4">${escapeHtml(rawLine)}</td></tr>`);
            continue;
        }

        if (rawLine.startsWith('---') || rawLine.startsWith('+++') || rawLine.startsWith('\\')) {
            rows.push(`<tr class="diff-meta"><td colspan="4">${escapeHtml(rawLine)}</td></tr>`);
            continue;
        }

        const prefix = rawLine.charAt(0);
        const content = rawLine.slice(1);

        if (prefix === ' ') {
            leftLine += 1;
            rightLine += 1;
            rows.push(
                `<tr class="diff-line diff-ctx">
                    <td class="diff-line-no">${leftLine}</td>
                    <td class="diff-text">${escapeHtml(content)}</td>
                    <td class="diff-line-no">${rightLine}</td>
                    <td class="diff-text">${escapeHtml(content)}</td>
                </tr>`
            );
            continue;
        }

        if (prefix === '-') {
            leftLine += 1;
            rows.push(
                `<tr class="diff-line diff-del">
                    <td class="diff-line-no">${leftLine}</td>
                    <td class="diff-text">${escapeHtml(content)}</td>
                    <td class="diff-line-no"></td>
                    <td class="diff-text"></td>
                </tr>`
            );
            continue;
        }

        if (prefix === '+') {
            rightLine += 1;
            rows.push(
                `<tr class="diff-line diff-add">
                    <td class="diff-line-no"></td>
                    <td class="diff-text"></td>
                    <td class="diff-line-no">${rightLine}</td>
                    <td class="diff-text">${escapeHtml(content)}</td>
                </tr>`
            );
            continue;
        }

        rows.push(`<tr class="diff-meta"><td colspan="4">${escapeHtml(rawLine)}</td></tr>`);
    }

    return rows.join('');
}

// Load restore jobs
async function loadRestores() {
    paginationState.restores.skip = 0;
    paginationState.restores.allItems = [];
    await loadRestoresPage();
}

async function loadRestoresPage() {
    try {
        const refreshStatus = document.getElementById('restores-refresh-status');
        if (refreshStatus && paginationState.restores.skip === 0) {
            refreshStatus.textContent = 'Refreshing...';
        }

        const [restoresResponse, serversResponse] = await Promise.all([
            fetch(`${API_URL}/restores/?skip=${paginationState.restores.skip}&limit=${paginationState.restores.limit}`, { headers: authHeaders() }),
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() })
        ]);

        if (!restoresResponse.ok) {
            throw new Error(`Failed to load restores: ${restoresResponse.status} ${restoresResponse.statusText}`);
        }

        const newRestores = await restoresResponse.json();
        const servers = serversResponse.ok ? await serversResponse.json() : [];
        
        // Add new items to the list
        paginationState.restores.allItems.push(...newRestores);
        
        // Check if there are more items
        paginationState.restores.hasMore = newRestores.length === paginationState.restores.limit;
        
        // Render restores
        renderRestores(paginationState.restores.allItems, servers);
        
        // Keep load more button hidden (using View All per-server buttons instead)
        const loadMoreBtn = document.getElementById('loadMoreRestoresBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
        
        if (refreshStatus && paginationState.restores.skip === 0) {
            refreshStatus.textContent = `Updated ${new Date().toLocaleTimeString()}`;
        }
    } catch (error) {
        console.error('Error loading restores:', error);
        const refreshStatus = document.getElementById('restores-refresh-status');
        if (refreshStatus) {
            refreshStatus.textContent = 'Refresh failed';
        }
    }
}

async function loadMoreRestores() {
    paginationState.restores.skip += paginationState.restores.limit;
    await loadRestoresPage();
}

function renderRestores(restores, servers) {
    const serverMap = new Map(servers.map(server => [parseInt(server.id), server.name]));
    const tbody = document.getElementById('restores-tbody');
    const ITEMS_PER_SERVER = 5;
    
    if (restores.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">No restore jobs found</td></tr>';
        return;
    }
    
    const groupedRestores = new Map();
    restores.forEach(restore => {
        const serverName = serverMap.get(parseInt(restore.ldap_server_id)) || 'Unknown Server';
        if (!groupedRestores.has(serverName)) {
            groupedRestores.set(serverName, []);
        }
        groupedRestores.get(serverName).push(restore);
    });

    const restoreRows = [];
    Array.from(groupedRestores.keys()).sort((a, b) => a.localeCompare(b)).forEach(serverName => {
        const serverRestores = groupedRestores.get(serverName);
        const showCount = Math.min(ITEMS_PER_SERVER, serverRestores.length);
        
        restoreRows.push(`
            <tr class="group-row">
                <td colspan="5"><span class="group-label">${escapeHtml(serverName)}</span></td>
            </tr>
        `);

        restoreRows.push(serverRestores.slice(0, showCount).map(restore => `
            <tr>
                <td>${escapeHtml(serverName)}</td>
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
        `).join(''));
        
        // Add "Load More" button row if there are more restores
        if (serverRestores.length > ITEMS_PER_SERVER) {
            restoreRows.push(`
                <tr>
                    <td colspan="5" style="text-align: center; padding: 10px;">
                        <button class="btn btn-secondary" data-server-id="${serverRestores[0].ldap_server_id}" onclick="viewServerRestores(this.dataset.serverId, '${escapeHtml(serverName).replace(/'/g, "&#39;")}')">View All (${serverRestores.length} total)</button>
                    </td>
                </tr>
            `);
        }
    });

    tbody.innerHTML = restoreRows.join('');
}

async function viewServerRestores(serverId, displayServerName) {
    // Parse serverId as integer
    serverId = parseInt(serverId);
    
    // Create and show modal with all restores for the selected server
    let modal = document.getElementById('serverRestoresModal');
    
    if (!modal) {
        // Create modal if it doesn't exist
        modal = document.createElement('div');
        modal.id = 'serverRestoresModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h2 id="serverRestoresTitle"></h2>
                    <span class="close" onclick="closeServerRestoresModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <table id="serverRestoresTable" class="data-table">
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Entries Restored</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody id="serverRestoresTbody"></tbody>
                    </table>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeServerRestoresModal()">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Show modal
    modal.style.display = 'block';
    modal.style.zIndex = '1500';  // Set z-index higher than default modals
    document.getElementById('serverRestoresTitle').textContent = `All Restore Jobs for ${escapeHtml(displayServerName)}`;
    
    // Show loading state
    const tbody = document.getElementById('serverRestoresTbody');
    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px;">Loading...</td></tr>';
    
    // Fetch restores for this server
    try {
        const response = await fetch(`${API_URL}/restores/?skip=0&limit=1000`, {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch restores: ${response.status}`);
        }
        
        const restores = await response.json();
        
        // Filter restores for this server by ID
        const filteredRestores = restores.filter(restore => parseInt(restore.ldap_server_id) === serverId);
        
        console.log(`Loaded ${restores.length} restores total, ${filteredRestores.length} for server ${serverId}`);
        
        // Render restores in modal
        if (filteredRestores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px; color: var(--text-secondary);">No restore jobs found for this server</td></tr>';
        } else {
            tbody.innerHTML = filteredRestores.map(restore => `
                <tr>
                    <td>
                        <span class="status-badge status-${restore.status.replace('_', '-')}">
                            ${escapeHtml(restore.status)}
                        </span>
                    </td>
                    <td>${restore.entries_restored ? parseInt(restore.entries_restored) : 'N/A'}</td>
                    <td>${new Date(restore.created_at).toLocaleString()}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading restores:', error);
        showError(`Error loading restores for ${escapeHtml(displayServerName)}: ${error.message}`);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading restores: ${escapeHtml(error.message)}</td></tr>`;
    }
}

function closeServerRestoresModal() {
    const modal = document.getElementById('serverRestoresModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const modal = document.getElementById('serverRestoresModal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
});

// Load scheduled backups
async function loadScheduled() {
    try {
        const [scheduled, servers] = await Promise.all([
            fetch(`${API_URL}/scheduled-backups/`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load scheduled backups: ${r.status} ${r.statusText}`);
                return r.json();
            }),
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() }).then(r => {
                if (!r.ok) throw new Error(`Failed to load servers: ${r.status} ${r.statusText}`);
                return r.json();
            })
        ]);

        const tbody = document.getElementById('scheduled-tbody');

        if (scheduled.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No scheduled backups</td></tr>';
            return;
        }

        const serverMap = new Map(servers.map(s => [parseInt(s.id), s.name]));

        tbody.innerHTML = scheduled.map(schedule => {
            const serverName = serverMap.get(parseInt(schedule.ldap_server_id)) || 'Unknown Server';
            return `
            <tr>
                <td>${escapeHtml(schedule.name)}</td>
                <td>${escapeHtml(serverName)}</td>
                <td>${escapeHtml(schedule.cron_expression)}</td>
                <td>${escapeHtml(schedule.backup_type)}</td>
                <td>${parseInt(schedule.retention_days)}</td>
                <td>
                    <span class="status-badge ${schedule.is_active ? 'status-completed' : 'status-failed'}">
                        ${schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="action-cell">
                    <button class="btn btn-secondary btn-sm" onclick="runScheduleNow(${parseInt(schedule.id)}, '${escapeHtml(schedule.name)}')">Run now</button>
                    <button class="btn btn-info btn-sm" onclick="showEditScheduleModal(${parseInt(schedule.id)})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteSchedule(${parseInt(schedule.id)}, '${escapeHtml(schedule.name)}')">Delete</button>
                </td>
            </tr>
            `;
        }).join('');
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

async function showEditServerModal(serverId) {
    try {
        const response = await fetch(`${API_URL}/ldap-servers/${serverId}`, {
            headers: authHeaders()
        });
        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            
            if (contentType.includes('application/json')) {
                try {
                    const data = await response.json();
                    errorMessage = data.detail || errorMessage;
                } catch (e) {
                    // JSON parse failed
                }
            }
            
            throw new Error(errorMessage);
        }
        const server = await response.json();
        
        // Populate form fields
        document.getElementById('editServerId').value = server.id;
        document.getElementById('editServerName').value = server.name;
        document.getElementById('editServerHost').value = server.host;
        document.getElementById('editServerPort').value = server.port;
        document.getElementById('editServerUseSSL').checked = server.use_ssl;
        document.getElementById('editServerBaseDN').value = server.base_dn;
        document.getElementById('editServerBindDN').value = server.bind_dn || '';
        // Don't populate password - leave empty for security
        document.getElementById('editServerPassword').value = '';
        document.getElementById('editServerActive').checked = server.is_active;
        document.getElementById('editServerDescription').value = server.description || '';
        
        // Show modal
        const modal = document.getElementById('editServerModal');
        if (modal) {
            modal.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading server:', error);
        showToast('error', `Failed to load server details: ${error.message}`);
    }
}

function closeEditServerModal() {
    const modal = document.getElementById('editServerModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function handleEditServer(event) {
    event.preventDefault();
    
    const serverId = document.getElementById('editServerId').value;
    const serverData = {
        name: document.getElementById('editServerName').value,
        host: document.getElementById('editServerHost').value,
        port: parseInt(document.getElementById('editServerPort').value),
        use_ssl: document.getElementById('editServerUseSSL').checked,
        base_dn: document.getElementById('editServerBaseDN').value,
        bind_dn: document.getElementById('editServerBindDN').value,
        is_active: document.getElementById('editServerActive').checked,
        description: document.getElementById('editServerDescription').value
    };
    
    // Only include password if it's not empty
    const password = document.getElementById('editServerPassword').value;
    if (password) {
        serverData.bind_password = password;
    }
    
    try {
        const response = await fetch(`${API_URL}/ldap-servers/${serverId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(serverData)
        });
        
        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let errorMessage = `Failed to update LDAP server (HTTP ${response.status})`;
            
            if (contentType.includes('application/json')) {
                try {
                    const data = await response.json();
                    errorMessage = data.detail || errorMessage;
                } catch (e) {
                    // If JSON parsing fails, use default message
                }
            }
            
            throw new Error(errorMessage);
        }
        
        showToast('success', 'LDAP server updated successfully');
        closeEditServerModal();
        await loadServers();
    } catch (error) {
        console.error('Edit server error:', error);
        showToast('error', error.message || 'Failed to update LDAP server');
    }
}

async function deleteServer(serverId, serverName) {
    if (!confirm(`Are you sure you want to delete the LDAP server "${serverName}"? This cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/ldap-servers/${serverId}`, {
            method: 'DELETE',
            headers: authHeaders()
        });

        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let errorMessage = `Failed to delete LDAP server (HTTP ${response.status})`;
            
            if (contentType.includes('application/json')) {
                try {
                    const data = await response.json();
                    errorMessage = data.detail || errorMessage;
                } catch (e) {
                    // If JSON parsing fails, use default message
                }
            }
            
            throw new Error(errorMessage);
        }

        showToast('success', `LDAP server "${serverName}" deleted successfully`);
        await loadServers();
    } catch (error) {
        console.error('Delete server error:', error);
        showToast('error', error.message || 'Failed to delete LDAP server');
    }
}

function showCreateBackupModal(defaultCategory = null) {
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
        category: 'directory',
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

async function showCreateRestoreModal() {
    const modal = document.getElementById('createRestoreModal');
    if (modal) {
        modal.style.display = 'block';
    }
    
    // Initialize calendar with current month
    window.restoreCurrentDate = new Date();
    window.restoreSelectedDate = null;
    window.restoreBackupsByDate = {};
    
    // Load server options
    await loadServerOptions('restoreServerId');
    
    // Auto-load calendar if a server is selected
    const serverId = document.getElementById('restoreServerId').value;
    if (serverId) {
        await updateRestoreBackupDates();
    }
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
    // Clear restore preview data
    window.restoreAllEntries = [];
    window.restoreSelectedEntries = new Set();
    document.getElementById('restoreEntriesPreview').innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Select a backup to preview entries</div>';
    document.getElementById('restoreFilter').value = '';
    document.getElementById('restoreSearchInput').value = '';
    document.getElementById('selectAllRestoreEntries').checked = false;
    document.getElementById('restoreBackupId').value = '';
    document.getElementById('restoreBackupInfo').style.display = 'none';
    toggleRestoreFilter();
}

async function updateRestoreBackupDates() {
    try {
        const response = await fetch(`${API_URL}/backups/?skip=0&limit=1000`, {
            headers: authHeaders()
        });
        const serversResponse = await fetch(`${API_URL}/ldap-servers/`, {
            headers: authHeaders()
        });

        if (!response.ok) throw new Error('Failed to fetch backups');
        const data = await response.json();
        const servers = serversResponse.ok ? await serversResponse.json() : [];
        
        // Create server name mapping
        const serverMap = new Map(servers.map(s => [parseInt(s.id), s.name]));
        
        // Group ALL backups by date (not filtered by server - allows restore to different server)
        window.restoreBackupsByDate = {};
        
        data.forEach(backup => {
            const date = new Date(backup.created_at);
            // Use local date format to avoid timezone issues
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const dateKey = `${year}-${month}-${day}`;
            
            if (!window.restoreBackupsByDate[dateKey]) {
                window.restoreBackupsByDate[dateKey] = [];
            }
            
            // Add server name to backup object
            backup.ldap_server_name = serverMap.get(parseInt(backup.ldap_server_id)) || 'Unknown';
            window.restoreBackupsByDate[dateKey].push(backup);
        });
        
        // Sort backups by time within each date
        Object.keys(window.restoreBackupsByDate).forEach(date => {
            window.restoreBackupsByDate[date].sort((a, b) =>
                new Date(a.created_at) - new Date(b.created_at)
            );
        });

        renderRestoreCalendar();
    } catch (error) {
        console.error('Error loading backup dates:', error);
        document.getElementById('restoreCalendar').innerHTML = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
    }
}

function renderRestoreCalendar() {
    const container = document.getElementById('restoreCalendar');
    const currentDate = window.restoreCurrentDate;
    
    // Calendar header with month/year and navigation
    let html = `
        <div class="calendar-header">
            <button type="button" onclick="previousRestoreMonth()">❮</button>
            <h3 id="restoreCalendarMonth">${currentDate.toLocaleDateString('en-US', {month: 'long', year: 'numeric'})}</h3>
            <button type="button" onclick="nextRestoreMonth()">❯</button>
        </div>
    `;
    
    // Weekday headers
    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    html += '<div class="calendar-weekdays">';
    weekdays.forEach(day => {
        html += `<div>${day}</div>`;
    });
    html += '</div>';
    
    // Calendar days
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    html += '<div class="calendar-days">';
    let currentCell = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
        // Use local date format to match backup date keys
        const cellYear = currentCell.getFullYear();
        const cellMonth = String(currentCell.getMonth() + 1).padStart(2, '0');
        const cellDay = String(currentCell.getDate()).padStart(2, '0');
        const dateKey = `${cellYear}-${cellMonth}-${cellDay}`;
        
        const hasBackup = window.restoreBackupsByDate[dateKey] && window.restoreBackupsByDate[dateKey].length > 0;
        const isCurrentMonth = currentCell.getMonth() === month;
        const isSelected = window.restoreSelectedDate && dateKey === window.restoreSelectedDate;
        
        let className = 'calendar-day';
        if (!isCurrentMonth) className += ' disabled';
        if (hasBackup && isCurrentMonth) className += ' has-backup';
        if (isSelected) className += ' selected';
        
        const dayNum = currentCell.getDate();
        html += `
            <div class="${className}" ${isCurrentMonth && hasBackup ? `onclick="selectRestoreBackupDate('${dateKey}')"` : ''}>
                ${dayNum}
            </div>
        `;
        
        currentCell.setDate(currentCell.getDate() + 1);
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function previousRestoreMonth() {
    window.restoreCurrentDate.setMonth(window.restoreCurrentDate.getMonth() - 1);
    renderRestoreCalendar();
}

function nextRestoreMonth() {
    window.restoreCurrentDate.setMonth(window.restoreCurrentDate.getMonth() + 1);
    renderRestoreCalendar();
}

function selectRestoreBackupDate(dateStr) {
    window.restoreSelectedDate = dateStr;
    
    // Show available backups for this date
    const backups = window.restoreBackupsByDate[dateStr] || [];
    const timesList = document.getElementById('restoreTimesList');
    
    if (backups.length === 0) {
        timesList.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">No backups for this date</div>';
        document.getElementById('restoreBackupId').value = '';
        document.getElementById('restoreBackupInfo').style.display = 'none';
        return;
    }
    
    // Group backups by server
    const backupsByServer = {};
    backups.forEach(backup => {
        const serverName = backup.ldap_server_name || 'Unknown Server';
        if (!backupsByServer[serverName]) {
            backupsByServer[serverName] = [];
        }
        backupsByServer[serverName].push(backup);
    });
    
    let html = '';
    Object.keys(backupsByServer).sort().forEach(serverName => {
        let serverHtml = '';
        
        backupsByServer[serverName].forEach((backup, index) => {
            try {
                const backupDate = new Date(backup.created_at);
                const time = backupDate.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'});
                const status = backup.status || 'pending';
                const verified = backup.verification_status ? `✓ ${backup.verification_status}` : '';
                
                serverHtml += `
                    <div class="restore-time-item" onclick="selectRestoreBackup(${backup.id}, this)">
                        <div class="restore-time-item-time">${time}</div>
                        <div class="restore-time-item-info">${status} ${verified}</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error parsing backup:', backup, error);
            }
        });
        
        // Wrap server's backups in a box
        html += `
            <div style="border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 16px; overflow: hidden; background: var(--bg-secondary);">
                <div style="padding: 12px 16px; background: var(--bg-tertiary); font-weight: 500; color: var(--text-primary); border-bottom: 1px solid var(--border-color);">${serverName}</div>
                <div style="padding: 8px 0;">${serverHtml}</div>
            </div>
        `;
    });
    
    if (html === '') {
        timesList.innerHTML = '<div style="padding: 20px; text-align: center; color: red;">Error loading backup times</div>';
    } else {
        timesList.innerHTML = html;
    }
    
    renderRestoreCalendar(); // Re-render to show selected date
}

function selectRestoreBackup(backupId, element) {
    console.log('selectRestoreBackup called with ID:', backupId);
    
    // Remove previous selection
    document.querySelectorAll('.restore-time-item.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Add selection to clicked element
    element.classList.add('selected');
    document.getElementById('restoreBackupId').value = backupId;
    
    // Show backup info
    const backup = window.restoreBackupsByDate[window.restoreSelectedDate].find(b => b.id === backupId);
    if (backup) {
        const time = new Date(backup.created_at).toLocaleString();
        document.getElementById('restoreBackupInfoText').textContent = `${backup.ldap_server_name} at ${time}`;
        document.getElementById('restoreBackupInfo').style.display = 'block';
        console.log('Selected backup:', backup);
    } else {
        console.warn('Backup not found in window.restoreBackupsByDate');
    }
    
    // Always load preview when a backup is selected
    console.log('About to load restore preview. Selective restore checked:', document.getElementById('restoreSelective').checked);
    loadRestorePreview();
}

function toggleRestoreFilter() {
    const filterGroup = document.getElementById('restoreFilterGroup');
    const selective = document.getElementById('restoreSelective');
    if (!filterGroup || !selective) return;

    filterGroup.style.display = selective.checked ? 'block' : 'none';
    if (selective.checked) {
        // Check if a backup is already selected
        const backupId = document.getElementById('restoreBackupId').value;
        if (backupId) {
            loadRestorePreview();
        } else {
            // Show message to select a backup first
            const previewContainer = document.getElementById('restoreEntriesPreview');
            if (previewContainer) {
                previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Select a backup to preview entries</div>';
            }
        }
    } else {
        // Clear preview when unchecked
        const previewContainer = document.getElementById('restoreEntriesPreview');
        if (previewContainer) {
            previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Select a backup to preview entries</div>';
        }
    }
}

// Load and parse backup content for restore preview
async function loadRestorePreview() {
    const backupId = document.getElementById('restoreBackupId').value;
    const previewContainer = document.getElementById('restoreEntriesPreview');
    
    console.log('loadRestorePreview called with backupId:', backupId);
    
    if (!backupId) {
        console.log('No backup ID provided');
        previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Select a backup to preview entries</div>';
        return;
    }

    previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Loading backup entries...</div>';

    try {
        console.log(`Fetching backup ${backupId} content...`);
        const response = await fetch(`${API_URL}/backups/${parseInt(backupId)}/content?max_lines=1000`, {
            headers: authHeaders()
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to load backup content`);
        }

        const data = await response.json();
        const content = data.content || '';
        
        console.log(`Backup content received, length: ${content.length}`);
        
        if (!content || content.trim() === '') {
            console.warn('Backup content is empty');
            previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Backup content is empty</div>';
            return;
        }
        
        // Parse LDIF format to extract DN entries and build tree
        const { entries, tree } = parseLdifContent(content);
        
        console.log(`Parsed ${entries.length} entries, tree structure:`, tree);
        
        if (entries.length === 0) {
            console.warn('No entries parsed from content');
            previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">No entries found in backup</div>';
            return;
        }

        // Store entries and tree for search/filter functions
        window.restoreAllEntries = entries;
        window.restoreTreeStructure = tree;
        window.restoreSelectedEntries = new Set();
        
        console.log('Calling renderRestoreTree...');
        renderRestoreTree(tree);
        console.log('renderRestoreTree completed');
    } catch (error) {
        console.error('Error loading restore preview:', error);
        previewContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--danger-color);">Error: ${escapeHtml(error.message)}</div>`;
    }
}

// Parse LDIF content to extract distinguished names and build a tree structure
function parseLdifContent(content) {
    try {
        const lines = content.split('\n');
        const allEntries = [];
        let currentEntry = null;

        // First pass: extract all entries
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            if (line.startsWith('dn:')) {
                if (currentEntry && currentEntry.dn) {
                    allEntries.push(currentEntry);
                }
                const dn = line.substring(3).trim();
                const displayName = extractDisplayName(dn);
                currentEntry = {
                    dn: dn,
                    displayName: displayName,
                    attributes: {},
                    level: (dn.match(/,/g) || []).length
                };
            } else if (currentEntry && line.includes(':') && line.trim() && !line.startsWith(' ')) {
                const colonIndex = line.indexOf(':');
                const key = line.substring(0, colonIndex).trim();
                const value = line.substring(colonIndex + 1).trim();
                if (key && !currentEntry.attributes[key]) {
                    currentEntry.attributes[key] = value;
                }
            }
        }

        if (currentEntry && currentEntry.dn) {
            allEntries.push(currentEntry);
        }

        console.log('Parsed LDIF entries:', allEntries.length);

        // Build tree structure
        const tree = { children: [], dn: 'root' };

        allEntries.forEach(entry => {
            insertIntoTree(tree, entry);
        });

        return { entries: allEntries, tree: tree };
    } catch (error) {
        console.error('Error parsing LDIF:', error);
        return { entries: [], tree: { children: [], dn: 'root' } };
    }
}

// Insert entry into tree structure
function insertIntoTree(tree, entry) {
    const dnParts = entry.dn.split(',').map(s => s.trim());
    let currentNode = tree;

    for (let i = dnParts.length - 1; i >= 0; i--) {
        const part = dnParts[i];
        let childNode = currentNode.children.find(c => c.dn === part);

        if (!childNode) {
            const fullDn = dnParts.slice(0, dnParts.length - i).reverse().join(',');
            childNode = {
                dn: part,
                fullDn: fullDn,
                children: [],
                entries: [],
                level: dnParts.length - 1 - i
            };
            currentNode.children.push(childNode);
            // Sort children by DN
            currentNode.children.sort((a, b) => a.dn.localeCompare(b.dn));
        }

        currentNode = childNode;
    }

    // Store the actual leaf entry
    currentNode.entries = currentNode.entries || [];
    currentNode.entries.push(entry);
}

// Extract a readable name from DN part
function extractDisplayName(dn) {
    const match = dn.match(/(?:^|,)([^=,]+)=([^,]+)/);
    if (match) {
        const [, type, value] = match;
        return value;
    }
    return dn.substring(0, 50) + (dn.length > 50 ? '...' : '');
}

// Render entries as a tree structure
function renderRestoreTree(tree) {
    const previewContainer = document.getElementById('restoreEntriesPreview');
    
    if (!tree || !tree.children || tree.children.length === 0) {
        console.log('No tree children to render');
        previewContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">No entries to display</div>';
        return;
    }
    
    // Render as hierarchical tree
    let html = '<div style="padding: 0; font-size: 0.9em; font-family: monospace;">';
    
    try {
        console.log('Building tree HTML from', tree.children.length, 'top-level nodes');
        tree.children.forEach((node, index) => {
            html += renderRestoreTreeNode(node, 0, index === tree.children.length - 1);
        });
    } catch (error) {
        console.error('Error rendering tree:', error);
        html += '<div style="padding: 20px; color: var(--danger-color);">Error rendering entries: ' + escapeHtml(error.message) + '</div>';
    }
    
    html += '</div>';
    console.log('Setting innerHTML, length:', html.length);
    previewContainer.innerHTML = html;
    
    // Add event listeners after rendering
    setTimeout(() => {
        console.log('Adding tree listeners');
        addRestoreTreeListeners();
    }, 50);
}

// Recursively render restore tree nodes
function renderRestoreTreeNode(node, depth, isLast) {
    let html = '';
    const nodeId = `restore-tree-node-${Date.now()}-${Math.random()}`;
    const hasChildren = node.children && node.children.length > 0;
    const hasEntries = node.entries && node.entries.length > 0;
    
    // Tree connector
    const indent = depth > 0 ? '  '.repeat(depth - 1) : '';
    const branch = isLast ? '└─ ' : '├─ ';
    const connector = depth === 0 ? '' : indent + branch;
    
    // Node row
    html += `<div class="tree-node" id="${nodeId}" style="padding: 2px 0; display: flex; align-items: center; user-select: none;">`;
    
    // Spacing
    if (depth > 0) {
        html += `<span style="width: ${depth * 14}px;"></span>`;
    }
    
    // Toggle button for parent nodes
    if (hasChildren) {
        const toggleId = `toggle-restore-${nodeId}`;
        html += `<button id="${toggleId}" class="tree-toggle" style="border: none; background: none; cursor: pointer; padding: 0 4px; width: 16px; color: var(--text-secondary); font-size: 0.85em;">▶</button>`;
    } else {
        html += `<span style="width: 16px;"></span>`;
    }
    
    // Checkbox for leaf entries
    if (hasEntries && !hasChildren) {
        const dnValues = node.entries.map(e => e.dn);
        const firstDn = dnValues[0];
        const isSelected = window.restoreSelectedEntries.has(firstDn);
        html += `
            <input 
                type="checkbox" 
                class="restore-entry-checkbox" 
                value="${escapeHtml(firstDn)}" 
                data-all-dns="${escapeHtml(JSON.stringify(dnValues))}"
                ${isSelected ? 'checked' : ''}
                onchange="toggleRestoreCheckbox()"
                style="margin: 0 4px; cursor: pointer; width: 16px;"
            >
        `;
    } else {
        html += `<span style="width: 20px;"></span>`;
    }
    
    // Label
    const label = extractNodeLabel(node.dn);
    html += `<span style="flex: 1; color: var(--text-primary); cursor: ${hasChildren ? 'pointer' : 'default'};">${escapeHtml(label)}</span>`;
    
    // Entry count badge
    if (hasEntries && node.entries.length > 0) {
        html += `<span style="margin-left: 8px; padding: 2px 6px; background: var(--primary-color); color: white; border-radius: 3px; font-size: 0.8em; white-space: nowrap;">${node.entries.length}</span>`;
    }
    
    html += `</div>`;
    
    // Children (initially hidden)
    if (hasChildren) {
        const childrenId = `children-restore-${nodeId}`;
        html += `<div id="${childrenId}" style="display: none;">`;
        node.children.forEach((child, idx) => {
            html += renderRestoreTreeNode(child, depth + 1, idx === node.children.length - 1);
        });
        html += `</div>`;
    }
    
    return html;
}

// Add expand/collapse listeners to tree nodes
function addRestoreTreeListeners() {
    const toggleButtons = document.querySelectorAll('[id^="toggle-restore-"]');
    toggleButtons.forEach(toggleBtn => {
        if (!toggleBtn.dataset.listenerAdded) {
            const nodeId = toggleBtn.id.replace('toggle-restore-', '');
            const childrenDiv = document.getElementById(`children-restore-${nodeId}`);
            if (childrenDiv) {
                toggleBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isHidden = childrenDiv.style.display === 'none';
                    childrenDiv.style.display = isHidden ? '' : 'none';
                    toggleBtn.textContent = isHidden ? '▼' : '▶';
                });
                toggleBtn.dataset.listenerAdded = 'true';
            }
        }
    });
}

// Recursively render restore tree nodes
function renderRestoreTreeNode(node, depth, isLast) {
    let html = '';
    const nodeId = `tree-node-${Date.now()}-${Math.random()}`;
    const isLeaf = node.entries.length > 0;
    const hasChildren = node.children.length > 0;
    
    // Tree lines
    const indent = depth > 0 ? '    '.repeat(depth - 1) : '';
    const branch = isLast ? '└── ' : '├── ';
    const connector = depth === 0 ? '' : indent + branch;
    
    // Node row
    html += `<div class="tree-node" id="${nodeId}" style="padding: 4px 0; display: flex; align-items: center;">`;
    html += `<span style="user-select: none; width: ${depth * 16}px;"></span>`;
    
    if (hasChildren) {
        const toggleId = `toggle-${nodeId}`;
        html += `<button id="${toggleId}" class="tree-toggle" style="border: none; background: none; cursor: pointer; padding: 0 4px; width: 20px; color: var(--text-secondary);">▶</button>`;
    } else {
        html += `<span style="width: 20px;"></span>`;
    }
    
    // Checkbox (only for leaf entries)
    if (isLeaf) {
        const dnValues = node.entries.map(e => e.dn);
        const firstDn = dnValues[0];
        const isSelected = window.restoreSelectedEntries.has(firstDn);
        html += `
            <input 
                type="checkbox" 
                class="restore-entry-checkbox" 
                value="${escapeHtml(firstDn)}" 
                data-all-dns="${escapeHtml(JSON.stringify(dnValues))}"
                ${isSelected ? 'checked' : ''}
                onchange="toggleRestoreCheckbox()"
                style="margin: 0 4px; cursor: pointer;"
            >
        `;
    } else {
        html += `<span style="width: 24px;"></span>`;
    }
    
    // Label
    const label = extractNodeLabel(node.dn);
    html += `<span style="flex: 1; cursor: ${isLeaf ? 'default' : 'pointer'};">${escapeHtml(label)}</span>`;
    
    // Entry count badge
    if (isLeaf && node.entries.length > 0) {
        html += `<span style="margin-left: 8px; padding: 2px 6px; background: var(--primary-color); color: white; border-radius: 3px; font-size: 0.8em;">${node.entries.length}</span>`;
    }
    
    html += `</div>`;
    
    // Children (initially hidden)
    if (hasChildren) {
        const childrenId = `children-${nodeId}`;
        html += `<div id="${childrenId}" style="display: none;">`;
        node.children.forEach((child, idx) => {
            html += renderRestoreTreeNode(child, depth + 1, idx === node.children.length - 1);
        });
        html += `</div>`;
        
        // Add expand/collapse handler after rendering initial structure
        setTimeout(() => {
            const toggleBtn = document.getElementById(`toggle-${nodeId}`);
            const childrenDiv = document.getElementById(childrenId);
            if (toggleBtn && childrenDiv) {
                toggleBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isHidden = childrenDiv.style.display === 'none';
                    childrenDiv.style.display = isHidden ? '' : 'none';
                    toggleBtn.textContent = isHidden ? '▼' : '▶';
                });
            }
        }, 0);
    }
    
    return html;
}

// Extract label from DN component (e.g., "cn=John" -> "John")
function extractNodeLabel(dn) {
    if (!dn) return 'root';
    const parts = dn.split('=');
    if (parts.length >= 2) {
        return parts.slice(1).join('=');
    }
    return dn;
}

// Filter tree based on search input
function filterRestoreEntries() {
    const searchInput = document.getElementById('restoreSearchInput').value.toLowerCase();
    const treeNodes = document.querySelectorAll('.tree-node');
    
    if (!window.restoreAllEntries) return;

    treeNodes.forEach(node => {
        const checkbox = node.querySelector('.restore-entry-checkbox');
        
        if (checkbox) {
            // Entry node - check if it matches search
            const dn = checkbox.value.toLowerCase();
            const entry = window.restoreAllEntries.find(e => e.dn === checkbox.value);
            
            const matches = !searchInput || 
                dn.includes(searchInput) ||
                (entry && entry.attributes.uid?.toLowerCase().includes(searchInput)) ||
                (entry && entry.attributes.mail?.toLowerCase().includes(searchInput));
            
            node.style.display = matches ? '' : 'none';
        } else {
            // Container node - show if any children are visible
            node.style.display = '';
        }
    });

    // Update select all checkbox
    updateSelectAllCheckbox();
}

// Toggle individual checkbox
function toggleRestoreCheckbox() {
    const checkboxes = document.querySelectorAll('.restore-entry-checkbox');
    
    window.restoreSelectedEntries.clear();
    checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
            window.restoreSelectedEntries.add(checkbox.value);
        }
    });

    updateRestoreFilter();
    updateSelectAllCheckbox();
}

// Update select all checkbox state
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAllRestoreEntries');
    const checkboxes = document.querySelectorAll('.restore-entry-checkbox');
    
    if (!selectAllCheckbox) return;

    const visibleCheckboxes = Array.from(checkboxes).filter(cb => 
        cb.closest('.tree-node').style.display !== 'none'
    );
    
    const allVisible = visibleCheckboxes.length > 0 && visibleCheckboxes.every(cb => cb.checked);
    selectAllCheckbox.checked = allVisible;
}

// Toggle all entries in current view
function toggleAllRestoreEntries() {
    const selectAllCheckbox = document.getElementById('selectAllRestoreEntries');
    const checkboxes = document.querySelectorAll('.restore-entry-checkbox');
    
    const visibleCheckboxes = Array.from(checkboxes).filter(cb => 
        cb.closest('.tree-node').style.display !== 'none'
    );

    visibleCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });

    toggleRestoreCheckbox();
}

// Update LDAP filter based on selections
function updateRestoreFilter() {
    const filterInput = document.getElementById('restoreFilter');
    const countEl = document.getElementById('restoreSelectionCount');
    
    if (!filterInput) return;

    const selectedCount = window.restoreSelectedEntries.size;
    countEl.textContent = `${selectedCount} selected`;

    if (selectedCount === 0) {
        filterInput.value = '';
        return;
    }

    if (selectedCount === 1) {
        // Single entry: match by DN using a wildcard or use (objectClass=*)
        const dn = Array.from(window.restoreSelectedEntries)[0];
        // Create a filter that matches entries by their DN
        filterInput.value = `(distinguishedName=${escapeLdapFilter(dn)})`;
    } else {
        // Multiple entries: build OR filter
        const dnFilters = Array.from(window.restoreSelectedEntries)
            .map(dn => `(distinguishedName=${escapeLdapFilter(dn)})`)
            .join('');
        filterInput.value = dnFilters.length > 0 ? `(|${dnFilters})` : '';
    }
}

// Escape special characters in LDAP filter strings
function escapeLdapFilter(str) {
    return str
        .replace(/\\/g, '\\5c')
        .replace(/\(/g, '\\28')
        .replace(/\)/g, '\\29')
        .replace(/\*/g, '\\2a')
        .replace(/\x00/g, '\\00');
}

// Clear all selections
function clearRestoreSelections() {
    window.restoreSelectedEntries.clear();
    document.querySelectorAll('.restore-entry-checkbox').forEach(cb => {
        cb.checked = false;
    });
    document.getElementById('selectAllRestoreEntries').checked = false;
    document.getElementById('restoreFilter').value = '';
    document.getElementById('restoreSearchInput').value = '';
    document.getElementById('restoreSelectionCount').textContent = '0 selected';
    if (window.restoreTreeStructure) {
        renderRestoreTree(window.restoreTreeStructure);
    }
}

async function handleCreateRestore(event) {
    event.preventDefault();

    const backupId = document.getElementById('restoreBackupId').value;
    const serverId = document.getElementById('restoreServerId').value;
    const selectiveRestore = document.getElementById('restoreSelective').checked;
    const restoreFilter = document.getElementById('restoreFilter').value.trim();

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
        restore_filter: selectiveRestore ? restoreFilter : null
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
    const statusGroup = document.getElementById('scheduleStatusGroup');
    if (statusGroup) {
        statusGroup.style.display = 'none';
    }
    const scheduleId = document.getElementById('scheduleId');
    if (scheduleId) {
        scheduleId.value = '';
    }
    const title = document.getElementById('scheduleModalTitle');
    if (title) {
        title.textContent = 'Schedule Backup';
    }
    const submit = document.getElementById('createScheduleSubmit');
    if (submit) {
        submit.textContent = 'Create Schedule';
    }
    const serverSelect = document.getElementById('scheduleServerId');
    if (serverSelect) {
        serverSelect.disabled = false;
    }
    loadServerOptions('scheduleServerId');
}

async function showEditScheduleModal(scheduleId) {
    try {
        const response = await fetch(`${API_URL}/scheduled-backups/${parseInt(scheduleId)}`, {
            headers: authHeaders()
        });

        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let errorMessage = `Failed to load schedule (HTTP ${response.status})`;

            if (contentType.includes('application/json')) {
                const data = await response.json();
                errorMessage = data.detail || errorMessage;
            }

            throw new Error(errorMessage);
        }

        const schedule = await response.json();
        const modal = document.getElementById('createScheduleModal');
        if (modal) {
            modal.style.display = 'block';
        }

        await loadServerOptions('scheduleServerId', schedule.ldap_server_id);
        document.getElementById('scheduleId').value = schedule.id;
        document.getElementById('scheduleName').value = schedule.name;
        document.getElementById('scheduleType').value = schedule.backup_type;
        document.getElementById('scheduleCron').value = schedule.cron_expression;
        document.getElementById('scheduleRetention').value = schedule.retention_days;
        document.getElementById('scheduleIsActive').checked = schedule.is_active;

        const statusGroup = document.getElementById('scheduleStatusGroup');
        if (statusGroup) {
            statusGroup.style.display = 'block';
        }
        const title = document.getElementById('scheduleModalTitle');
        if (title) {
            title.textContent = 'Edit Schedule';
        }
        const submit = document.getElementById('createScheduleSubmit');
        if (submit) {
            submit.textContent = 'Save Changes';
        }
        const serverSelect = document.getElementById('scheduleServerId');
        if (serverSelect) {
            serverSelect.disabled = true;
        }
    } catch (error) {
        console.error('Error loading schedule:', error);
        showToast('error', error.message || 'Failed to load schedule');
    }
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
    const statusGroup = document.getElementById('scheduleStatusGroup');
    if (statusGroup) {
        statusGroup.style.display = 'none';
    }
    const serverSelect = document.getElementById('scheduleServerId');
    if (serverSelect) {
        serverSelect.disabled = false;
    }
}

async function handleCreateSchedule(event) {
    event.preventDefault();

    const scheduleId = document.getElementById('scheduleId').value;
    const name = document.getElementById('scheduleName').value.trim();
    const serverId = document.getElementById('scheduleServerId').value;
    const backupType = document.getElementById('scheduleType').value;
    const cronExpression = document.getElementById('scheduleCron').value.trim();
    const retention = document.getElementById('scheduleRetention').value;
    const isActive = document.getElementById('scheduleIsActive').checked;

    if (!name || !serverId || !cronExpression) {
        showToast('error', 'Please fill in required fields (Name, Server, Cron)');
        return;
    }

    const payload = {
        name,
        backup_type: backupType,
        cron_expression: cronExpression,
        retention_days: parseInt(retention || '30')
    };

    if (scheduleId) {
        payload.is_active = isActive;
    } else {
        payload.ldap_server_id = parseInt(serverId);
    }

    try {
        const response = await fetch(
            scheduleId
                ? `${API_URL}/scheduled-backups/${parseInt(scheduleId)}`
                : `${API_URL}/scheduled-backups/`,
            {
                method: scheduleId ? 'PUT' : 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
            }
        );

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

        showToast('success', scheduleId ? 'Schedule updated successfully' : 'Schedule created successfully');
        closeCreateScheduleModal();
        await loadScheduled();
    } catch (error) {
        console.error('Create schedule error:', error);
        showToast('error', error.message || (scheduleId ? 'Failed to update schedule' : 'Failed to create schedule'));
    }
}

async function deleteSchedule(scheduleId, scheduleName) {
    if (!confirm(`Are you sure you want to delete the schedule "${scheduleName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/scheduled-backups/${parseInt(scheduleId)}`, {
            method: 'DELETE',
            headers: authHeaders()
        });

        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let errorMessage = `Failed to delete schedule (HTTP ${response.status})`;

            if (contentType.includes('application/json')) {
                const data = await response.json();
                errorMessage = data.detail || errorMessage;
            }

            throw new Error(errorMessage);
        }

        showToast('success', `Schedule "${scheduleName}" deleted successfully`);
        await loadScheduled();
    } catch (error) {
        console.error('Delete schedule error:', error);
        showToast('error', error.message || 'Failed to delete schedule');
    }
}

async function runScheduleNow(scheduleId, scheduleName) {
    try {
        const response = await fetch(`${API_URL}/scheduled-backups/${parseInt(scheduleId)}/run`, {
            method: 'POST',
            headers: authHeaders()
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
                    : 'Failed to run schedule');
            throw new Error(message);
        }

        showToast('success', `Scheduled backup "${scheduleName}" queued`);
        await loadBackups();
    } catch (error) {
        console.error('Run schedule error:', error);
        showToast('error', error.message || 'Failed to run schedule');
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
        modal.style.zIndex = '2000';  // Ensure it appears on top of other modals
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

// Sensitive Backups (ACL, Schema, Config, Certificates)
async function loadSensitiveBackups() {
    paginationState.sensitiveBackups.skip = 0;
    paginationState.sensitiveBackups.allItems = [];
    await loadSensitiveBackupsPage();
}

async function loadSensitiveBackupsPage() {
    try {
        const refreshStatus = document.getElementById('sensitive-refresh-status');
        if (refreshStatus && paginationState.sensitiveBackups.skip === 0) {
            refreshStatus.textContent = 'Refreshing...';
        }
        
        const [backupsResponse, serversResponse] = await Promise.all([
            fetch(`${API_URL}/backups/?skip=${paginationState.sensitiveBackups.skip}&limit=${paginationState.sensitiveBackups.limit}`, { headers: authHeaders() }),
            fetch(`${API_URL}/ldap-servers/`, { headers: authHeaders() })
        ]);
        
        if (!backupsResponse.ok) {
            throw new Error(`Failed to load backups: ${backupsResponse.status}`);
        }
        
        const allBackups = await backupsResponse.json();
        const servers = serversResponse.ok ? await serversResponse.json() : [];
        
        // Filter for sensitive backup categories
        const sensitiveCategories = ['acl', 'schema', 'config', 'certificates'];
        const sensitiveBackups = allBackups.filter(b => sensitiveCategories.includes(b.category));
        
        paginationState.sensitiveBackups.allItems.push(...sensitiveBackups);
        paginationState.sensitiveBackups.hasMore = sensitiveBackups.length === paginationState.sensitiveBackups.limit;
        
        renderSensitiveBackups(paginationState.sensitiveBackups.allItems, servers);

        if (refreshStatus && paginationState.sensitiveBackups.skip === 0) {
            refreshStatus.textContent = `Updated ${new Date().toLocaleTimeString()}`;
        }
        
        const loadMoreBtn = document.getElementById('loadMoreSensitiveBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = paginationState.sensitiveBackups.hasMore ? '' : 'none';
        }
    } catch (error) {
        console.error('Error loading sensitive backups:', error);
        alert('Error loading sensitive backups: ' + error.message);
    } finally {
        const refreshStatus = document.getElementById('sensitive-refresh-status');
        if (refreshStatus && paginationState.sensitiveBackups.skip !== 0) {
            refreshStatus.textContent = '';
        }
    }
}

async function loadMoreSensitiveBackups() {
    paginationState.sensitiveBackups.skip += paginationState.sensitiveBackups.limit;
    await loadSensitiveBackupsPage();
}

function renderSensitiveBackups(backups, servers) {
    const tbody = document.getElementById('sensitive-tbody');
    if (!tbody) return;
    
    if (backups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="no-data">No sensitive backups found</td></tr>';
        return;
    }
    
    tbody.innerHTML = backups.map(backup => {
        const server = servers.find(s => s.id === backup.ldap_server_id);
        const serverName = server?.name || `Server ${backup.ldap_server_id}`;
        const category = backup.category ? backup.category.charAt(0).toUpperCase() + backup.category.slice(1) : 'Unknown';
        const type = backup.backup_type ? backup.backup_type.charAt(0).toUpperCase() + backup.backup_type.slice(1) : 'Unknown';
        const status = backup.status ? backup.status.charAt(0).toUpperCase() + backup.status.slice(1) : 'Unknown';
        const size = backup.file_size ? (backup.file_size / 1024).toFixed(2) + ' KB' : 'N/A';
        const entries = backup.entry_count || 'N/A';
        const created = backup.created_at ? new Date(backup.created_at).toLocaleString() : 'N/A';
        
        return `<tr>
            <td>${backup.id}</td>
            <td>${serverName}</td>
            <td><span class="badge badge-info">${category}</span></td>
            <td>${type}</td>
            <td><span class="badge badge-${status.toLowerCase() === 'completed' ? 'success' : status.toLowerCase() === 'failed' ? 'danger' : 'warning'}">${status}</span></td>
            <td>${size}</td>
            <td>${entries}</td>
            <td>${created}</td>
            <td class="action-cell">
                ${backup.status === 'completed'
                    ? `<button class="btn btn-secondary btn-sm" onclick="showBackupContent(${parseInt(backup.id)})">View</button>
                       <button class="btn btn-info btn-sm" onclick="downloadBackupContent(${parseInt(backup.id)})">Download</button>
                       <button class="btn btn-success btn-sm" onclick="restoreBackup(${parseInt(backup.id)})">Restore</button>
                       <button class="btn btn-danger btn-sm" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>`
                    : `<button class="btn btn-danger btn-sm" onclick="deleteBackup(${parseInt(backup.id)})">Delete</button>`}
            </td>
        </tr>`;
    }).join('');
}

function showCreateSensitiveBackupModal() {
    showCreateBackupModal('schema');
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
    if (activeTab === 'backups' || activeTab === 'sensitive' || activeTab === 'restores') {
        loadTabData(activeTab);
    }
}, 10000);
