// API base URL
const API_URL = window.location.protocol + '//' + window.location.hostname + ':8000';

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
            fetch(`${API_URL}/ldap-servers/`).then(r => r.json()),
            fetch(`${API_URL}/backups/`).then(r => r.json())
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
        const response = await fetch(`${API_URL}/ldap-servers/`);
        const servers = await response.json();
        
        const tbody = document.getElementById('servers-tbody');
        
        if (servers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No LDAP servers configured</td></tr>';
            return;
        }
        
        tbody.innerHTML = servers.map(server => `
            <tr>
                <td>${server.name}</td>
                <td>${server.host}</td>
                <td>${server.port}</td>
                <td>${server.base_dn}</td>
                <td>
                    <span class="status-badge ${server.is_active ? 'status-completed' : 'status-failed'}">
                        ${server.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-primary" onclick="backupServer(${server.id})">Backup Now</button>
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
        const response = await fetch(`${API_URL}/backups/`);
        const backups = await response.json();
        
        const tbody = document.getElementById('backups-tbody');
        
        if (backups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-data">No backups found</td></tr>';
            return;
        }
        
        tbody.innerHTML = backups.map(backup => `
            <tr>
                <td>${backup.id}</td>
                <td>Server #${backup.ldap_server_id}</td>
                <td>${backup.backup_type}</td>
                <td>
                    <span class="status-badge status-${backup.status.replace('_', '-')}">
                        ${backup.status}
                    </span>
                </td>
                <td>${backup.file_size ? formatBytes(backup.file_size) : 'N/A'}</td>
                <td>${backup.entry_count || 'N/A'}</td>
                <td>${new Date(backup.created_at).toLocaleString()}</td>
                <td>
                    ${backup.status === 'completed' ? 
                        `<button class="btn btn-success" onclick="restoreBackup(${backup.id})">Restore</button>` : 
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
        const response = await fetch(`${API_URL}/restores/`);
        const restores = await response.json();
        
        const tbody = document.getElementById('restores-tbody');
        
        if (restores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No restore jobs found</td></tr>';
            return;
        }
        
        tbody.innerHTML = restores.map(restore => `
            <tr>
                <td>${restore.id}</td>
                <td>${restore.backup_id}</td>
                <td>Server #${restore.ldap_server_id}</td>
                <td>
                    <span class="status-badge status-${restore.status.replace('_', '-')}">
                        ${restore.status}
                    </span>
                </td>
                <td>${restore.entries_restored || 'N/A'}</td>
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
    loadDashboard();
    loadAppVersion();
});

// Auto-refresh every 30 seconds
setInterval(() => {
    const activeTab = document.querySelector('.nav-tab.active').getAttribute('data-tab');
    loadTabData(activeTab);
}, 30000);
