// API base URL
const API_URL = (window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || window.API_URL || '/api';

// Pagination state
const paginationState = {
    backups: { skip: 0, limit: 50, hasMore: true, allItems: [], perServerLoaded: {} },
    serverBackups: { skip: 0, limit: 10, hasMore: true, allItems: [], selectedServerId: null },
    restores: { skip: 0, limit: 50, hasMore: true, allItems: [] }
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
    paginationState.backups.skip = 0;
    paginationState.backups.allItems = [];
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
        
        // Add new items to the list
        paginationState.backups.allItems.push(...newBackups);
        
        // Check if there are more items
        paginationState.backups.hasMore = newBackups.length === paginationState.backups.limit;
        
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
        tbody.innerHTML = '<tr><td colspan="9" class="no-data">No backups found</td></tr>';
        return;
    }
    
    const groupedBackups = new Map();
    backups.forEach(backup => {
        const serverName = serverMap.get(parseInt(backup.ldap_server_id)) || `Server #${parseInt(backup.ldap_server_id)}`;
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
                <td colspan="9"><span class="group-label">${escapeHtml(serverName)}</span></td>
            </tr>
        `);

        backupRows.push(serverBackups.slice(0, showCount).map(backup => `
            <tr>
                <td>
                    <input type="checkbox" class="backup-checkbox" value="${parseInt(backup.id)}" onchange="updateBatchDeleteButton()">
                </td>
                <td>${parseInt(backup.id)}</td>
                <td>${escapeHtml(serverName)}</td>
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
                        `<button class="btn btn-secondary" onclick="showBackupContent(${parseInt(backup.id)})">View</button>
                         <button class="btn btn-info" onclick="downloadBackupContent(${parseInt(backup.id)})">Download</button>
                         <button class="btn btn-success" onclick="restoreBackup(${parseInt(backup.id)})">Restore</button>` : 
                        ''}
                </td>
            </tr>
        `).join(''));
        
        // Add "Load More" button row if there are more backups
        if (serverBackups.length > ITEMS_PER_SERVER) {
            backupRows.push(`
                <tr>
                    <td colspan="9" style="text-align: center; padding: 10px;">
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
                                <th>ID</th>
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
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Loading...</td></tr>';
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
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px; color: var(--text-secondary);">No backups found for this server</td></tr>';
        } else {
            tbody.innerHTML = filteredBackups.map(backup => `
                <tr>
                    <td>
                        <input type="checkbox" class="server-backup-checkbox" value="${parseInt(backup.id)}" onchange="updateServerBackupDeleteButton()">
                    </td>
                    <td>${parseInt(backup.id)}</td>
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
                        ${backup.status === 'completed' ? 
                            `<details class="action-menu">
                                <summary class="btn btn-secondary btn-sm">Actions</summary>
                                <div class="action-menu-list">
                                    <button class="btn btn-secondary btn-sm" onclick="showBackupContent(${parseInt(backup.id)})">View</button>
                                    <button class="btn btn-info btn-sm" onclick="downloadBackupContent(${parseInt(backup.id)})">Download</button>
                                    <button class="btn btn-success btn-sm" onclick="restoreBackup(${parseInt(backup.id)})">Restore</button>
                                </div>
                            </details>` : 
                            ''}
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

    if (!modal || !contentEl || !metaEl) return;

    contentEl.textContent = '';
    metaEl.textContent = 'Loading...';
    modal.style.display = 'block';
    modal.style.zIndex = '2000';  // Ensure it appears on top of other modals

    try {
        const response = await fetch(`${API_URL}/backups/${parseInt(backupId)}/content?max_lines=200`, {
            headers: authHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load backup content');
        }

        const data = await response.json();
        contentEl.textContent = data.content || '';
        metaEl.textContent = data.truncated
            ? `Showing first ${data.lines} lines (truncated)`
            : `Showing ${data.lines} lines`;
    } catch (error) {
        contentEl.textContent = '';
        metaEl.textContent = error.message || 'Failed to load backup content';
    }
}

function closeBackupContentModal() {
    const modal = document.getElementById('backupContentModal');
    if (modal) {
        modal.style.display = 'none';
    }
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
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No restore jobs found</td></tr>';
        return;
    }
    
    const groupedRestores = new Map();
    restores.forEach(restore => {
        const serverName = serverMap.get(parseInt(restore.ldap_server_id)) || `Server #${parseInt(restore.ldap_server_id)}`;
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
                <td colspan="7"><span class="group-label">${escapeHtml(serverName)}</span></td>
            </tr>
        `);

        restoreRows.push(serverRestores.slice(0, showCount).map(restore => `
            <tr>
                <td>${parseInt(restore.id)}</td>
                <td>${parseInt(restore.backup_id)}</td>
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
                    <td colspan="7" style="text-align: center; padding: 10px;">
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
                                <th>ID</th>
                                <th>Backup ID</th>
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
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">Loading...</td></tr>';
    
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
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: var(--text-secondary);">No restore jobs found for this server</td></tr>';
        } else {
            tbody.innerHTML = filteredRestores.map(restore => `
                <tr>
                    <td>${parseInt(restore.id)}</td>
                    <td>${parseInt(restore.backup_id)}</td>
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
                <td class="action-cell">
                    <button class="btn btn-secondary btn-sm" onclick="runScheduleNow(${parseInt(schedule.id)}, '${escapeHtml(schedule.name)}')">Run now</button>
                    <button class="btn btn-info btn-sm" onclick="showEditScheduleModal(${parseInt(schedule.id)})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteSchedule(${parseInt(schedule.id)}, '${escapeHtml(schedule.name)}')">Delete</button>
                </td>
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
