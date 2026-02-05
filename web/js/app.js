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

// Check authentication and initialize app
async function checkAuthAndInit() {
    const token = getAuthToken();
    
    if (!token) {
        // Show login modal
        document.getElementById('loginModal').style.display = 'block';
        return;
    }
    
    try {
        // Verify token by calling a protected endpoint
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const user = await response.json();
            // Show main app
            document.getElementById('mainApp').style.display = 'block';
            document.getElementById('loginModal').style.display = 'none';
            
            // Update auth status
            document.getElementById('auth-status').textContent = `${user.username} (${user.role})`;
            document.getElementById('login-button').textContent = 'Logout';
            document.getElementById('login-button').onclick = handleLogout;
            
            // Initialize theme
            initTheme();
            
            // Load initial data
            loadDashboard();
        } else {
            // Token invalid, show login
            clearAuthToken();
            document.getElementById('loginModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        clearAuthToken();
        document.getElementById('loginModal').style.display = 'block';
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
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        setAuthToken(data.access_token);
        
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
    document.getElementById('login-button').onclick = showLoginModal;
    document.getElementById('loginForm').reset();
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
                <td>
                    <button class="btn btn-primary" onclick="backupServer(${parseInt(server.id)})">Backup Now</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading servers:', error);
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
                <td>
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
                <td>-</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading restores:', error);
    }
}

// Load scheduled backups
async function loadScheduled() {
    // Placeholder - would need scheduled backups endpoint
    console.log('Loading scheduled backups...');
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
    alert('Add Server modal - to be implemented');
}

function showCreateBackupModal() {
    alert('Create Backup modal - to be implemented');
}

function showCreateRestoreModal() {
    alert('Create Restore modal - to be implemented');
}

function showScheduleModal() {
    alert('Schedule Backup modal - to be implemented');
}

function backupServer(serverId) {
    alert(`Backup server ${serverId} - to be implemented`);
}

function restoreBackup(backupId) {
    alert(`Restore backup ${backupId} - to be implemented`);
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
