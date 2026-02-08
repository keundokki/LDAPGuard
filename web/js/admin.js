// Admin functionality for audit logs, API keys, settings, and config

// Track current admin section
let currentAdminSection = 'users';

// Show admin section
function showAdminSection(section, evt = null) {
    currentAdminSection = section;
    
    // Hide all admin sections
    document.querySelectorAll('.admin-section').forEach(sec => {
        sec.style.display = 'none';
    });
    
    // Show selected section
    document.getElementById(`admin-${section}`).style.display = 'block';
    
    // Update navigation buttons
    document.querySelectorAll('.admin-nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (evt && evt.target) {
        evt.target.classList.add('active');
    } else {
        const fallback = document.querySelector(`.admin-nav-btn[data-section="${section}"]`);
        if (fallback) {
            fallback.classList.add('active');
        }
    }
    
    // Load data for the section
    switch(section) {
        case 'users':
            loadUsers();
            break;
        case 'audit':
            loadAuditLogs();
            break;
        case 'api-keys':
            loadApiKeys();
            break;
        case 'notifications':
            loadSettings();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Load audit logs
async function loadAuditLogs() {
    try {
        const response = await fetch('/api/audit-logs/', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to load audit logs');
        }
        
        const logs = await response.json();
        const tbody = document.getElementById('audit-tbody');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No audit logs available</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${escapeHtml(new Date(log.created_at).toLocaleString())}</td>
                <td>User #${log.user_id ? parseInt(log.user_id) : 'System'}</td>
                <td>${escapeHtml(log.action)}</td>
                <td>${escapeHtml(log.resource_type) || '-'}</td>
                <td>${escapeHtml(log.details) || '-'}</td>
                <td>${escapeHtml(log.ip_address) || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading audit logs:', error);
        showToast('error', 'Failed to load audit logs');
    }
}

// Load API keys
async function loadApiKeys() {
    try {
        const response = await fetch('/api/api-keys/', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to load API keys');
        }
        
        const keys = await response.json();
        const tbody = document.getElementById('apikeys-tbody');
        
        if (keys.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No API keys configured</td></tr>';
            return;
        }
        
        tbody.innerHTML = keys.map(key => `
            <tr>
                <td>${escapeHtml(key.name)}</td>
                <td>${escapeHtml(key.key_prefix)}...</td>
                <td>${escapeHtml(key.permissions) || 'read,write'}</td>
                <td>${escapeHtml(new Date(key.created_at).toLocaleString())}</td>
                <td>${key.expires_at ? escapeHtml(new Date(key.expires_at).toLocaleString()) : 'Never'}</td>
                <td>${key.last_used_at ? escapeHtml(new Date(key.last_used_at).toLocaleString()) : 'Never'}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteApiKey(${parseInt(key.id)})">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading API keys:', error);
        showToast('error', 'Failed to load API keys');
    }
}

// Show create API key modal
function showCreateApiKeyModal() {
    document.getElementById('createApiKeyModal').style.display = 'block';
}

// Close create API key modal
function closeCreateApiKeyModal() {
    document.getElementById('createApiKeyModal').style.display = 'none';
    document.getElementById('createApiKeyForm').reset();
}

// Handle create API key
async function handleCreateApiKey(event) {
    event.preventDefault();
    
    const name = document.getElementById('apiKeyName').value;
    const permissions = document.getElementById('apiKeyPermissions').value;
    const expiresDays = document.getElementById('apiKeyExpires').value;
    
    try {
        const response = await fetch('/api/api-keys/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                permissions,
                expires_days: expiresDays ? parseInt(expiresDays) : null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create API key');
        }
        
        const result = await response.json();
        
        // Show the API key to the user (only shown once!)
        alert(`API Key Created!\n\nKey: ${result.api_key}\n\n⚠️ IMPORTANT: Save this key now! It will not be shown again.`);
        
        showToast('success', 'API key created successfully');
        closeCreateApiKeyModal();
        await loadApiKeys();
    } catch (error) {
        console.error('Error creating API key:', error);
        showToast('error', error.message || 'Failed to create API key');
    }
}

// Delete API key
async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete API key');
        }
        
        showToast('success', 'API key deleted successfully');
        await loadApiKeys();
    } catch (error) {
        console.error('Error deleting API key:', error);
        showToast('error', 'Failed to delete API key');
    }
}

// Save notification settings
async function saveNotificationSettings(event) {
    event.preventDefault();
    
    const settings = [
        {
            key: 'notification_email_enabled',
            value: document.getElementById('emailNotifications').checked.toString()
        },
        {
            key: 'notification_email',
            value: document.getElementById('notificationEmail').value
        },
        {
            key: 'notification_webhook_enabled',
            value: document.getElementById('webhookNotifications').checked.toString()
        },
        {
            key: 'notification_webhook_url',
            value: document.getElementById('webhookUrl').value
        },
        {
            key: 'notification_on_backup_success',
            value: document.getElementById('notifyBackupSuccess').checked.toString()
        },
        {
            key: 'notification_on_backup_failure',
            value: document.getElementById('notifyBackupFailure').checked.toString()
        },
        {
            key: 'notification_on_restore_complete',
            value: document.getElementById('notifyRestoreComplete').checked.toString()
        }
    ];
    
    try {
        const response = await fetch('/api/settings/batch', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save notification settings');
        }
        
        showToast('success', 'Notification settings saved successfully');
    } catch (error) {
        console.error('Error saving notification settings:', error);
        showToast('error', 'Failed to save notification settings');
    }
}

// Save system settings
async function saveSystemSettings(event) {
    event.preventDefault();
    
    const settings = [
        {
            key: 'backup_retention_days',
            value: document.getElementById('retentionDays').value
        },
        {
            key: 'backup_path',
            value: document.getElementById('backupPath').value
        },
        {
            key: 'session_timeout_minutes',
            value: document.getElementById('sessionTimeout').value
        },
        {
            key: 'require_2fa',
            value: document.getElementById('require2FA').checked.toString()
        }
    ];
    
    try {
        const response = await fetch('/api/settings/batch', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save system settings');
        }
        
        showToast('success', 'System settings saved successfully');
    } catch (error) {
        console.error('Error saving system settings:', error);
        showToast('error', 'Failed to save system settings');
    }
}

// Export configuration
async function exportConfiguration() {
    try {
        const response = await fetch('/api/config/export', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to export configuration');
        }
        
        const config = await response.json();
        
        // Download as JSON file
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ldapguard-config-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showToast('success', 'Configuration exported successfully');
    } catch (error) {
        console.error('Export failed:', error);
        showToast('error', 'Failed to export configuration');
    }
}

// Import configuration
async function importConfiguration(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const text = await file.text();
        const config = JSON.parse(text);
        
        const response = await fetch('/api/config/import', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Import failed');
        }
        
        const result = await response.json();
        
        showToast('success', 
            `Configuration imported: ${result.imported.servers} servers, ` +
            `${result.imported.scheduled_backups} schedules, ` +
            `${result.imported.users} users`
        );
        
        // Reload data
        await loadServers();
        if (typeof loadScheduledBackups === 'function') {
            await loadScheduledBackups();
        }
    } catch (error) {
        console.error('Import failed:', error);
        showToast('error', error.message || 'Failed to import configuration');
    }
    
    // Reset file input
    event.target.value = '';
}

// Load settings into forms
async function loadSettings() {
    try {
        const response = await fetch('/api/settings/', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            return; // Settings might not exist yet
        }
        
        const settings = await response.json();
        
        // Map settings to form fields
        settings.forEach(setting => {
            const element = document.getElementById(getElementIdForSetting(setting.key));
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = setting.value === 'true';
                } else {
                    element.value = setting.value;
                }
            }
        });
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Helper to map setting keys to element IDs
function getElementIdForSetting(key) {
    const mapping = {
        'notification_email_enabled': 'emailNotifications',
        'notification_email': 'notificationEmail',
        'notification_webhook_enabled': 'webhookNotifications',
        'notification_webhook_url': 'webhookUrl',
        'notification_on_backup_success': 'notifyBackupSuccess',
        'notification_on_backup_failure': 'notifyBackupFailure',
        'notification_on_restore_complete': 'notifyRestoreComplete',
        'backup_retention_days': 'retentionDays',
        'backup_path': 'backupPath',
        'session_timeout_minutes': 'sessionTimeout',
        'require_2fa': 'require2FA'
    };
    return mapping[key];
}

// ============================================
// User Management Functions
// ============================================

// Load users
async function loadUsers() {
    try {
        const response = await fetch('/api/auth/users/', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to load users');
        }
        
        const users = await response.json();
        const tbody = document.getElementById('users-tbody');
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${parseInt(user.id)}</td>
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.email)}</td>
                <!-- Note: role is a backend enum value (admin|operator|viewer), safe for use in CSS class -->
                <td><span class="badge badge-${user.role}">${escapeHtml(user.role)}</span></td>
                <td><span class="badge badge-${user.is_active ? 'success' : 'danger'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(user.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="showEditUserModal(${parseInt(user.id)})">Edit</button>
                    <button class="btn btn-secondary btn-sm" onclick="showResetPasswordModal(${parseInt(user.id)})">Reset Password</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteUser(${parseInt(user.id)})">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('error', 'Failed to load users');
    }
}

// Show create user modal
function showCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'block';
}

// Close create user modal
function closeCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'none';
    document.getElementById('createUserForm').reset();
}

// Handle create user
async function handleCreateUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('newUsername').value;
    const email = document.getElementById('newEmail').value;
    const password = document.getElementById('newPassword').value;
    const fullName = document.getElementById('newFullName').value;
    const role = document.getElementById('newRole').value;
    
    try {
        const response = await fetch('/api/auth/users/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName || null,
                role,
                ldap_auth: false
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
                    : 'Failed to create user');
            throw new Error(message);
        }

        showToast('success', 'User created successfully');
        closeCreateUserModal();
        await loadUsers();
    } catch (error) {
        console.error('Error creating user:', error);
        showToast('error', error.message || 'Failed to create user');
    }
}

// Show edit user modal
async function showEditUserModal(userId) {
    try {
        // Fetch user details
        const response = await fetch('/api/auth/users/', {
            headers: authHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to load user details');
        }
        
        const users = await response.json();
        const user = users.find(u => u.id === userId);
        
        if (!user) {
            throw new Error('User not found');
        }
        
        // Populate form
        document.getElementById('editUserId').value = user.id;
        document.getElementById('editUsername').value = user.username;
        document.getElementById('editEmail').value = user.email;
        document.getElementById('editFullName').value = user.full_name || '';
        document.getElementById('editRole').value = user.role;
        document.getElementById('editIsActive').value = user.is_active.toString();
        
        // Show modal
        document.getElementById('editUserModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading user details:', error);
        showToast('error', error.message || 'Failed to load user details');
    }
}

// Close edit user modal
function closeEditUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
    document.getElementById('editUserForm').reset();
}

// Show reset password modal
async function showResetPasswordModal(userId) {
    try {
        const response = await fetch('/api/auth/users/', {
            headers: authHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load user details');
        }

        const users = await response.json();
        const user = users.find(u => u.id === userId);

        if (!user) {
            throw new Error('User not found');
        }

        document.getElementById('resetUserId').value = user.id;
        document.getElementById('resetUsername').value = user.username;
        document.getElementById('resetNewPassword').value = '';
        document.getElementById('resetConfirmPassword').value = '';

        document.getElementById('resetPasswordModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading user details:', error);
        showToast('error', error.message || 'Failed to load user details');
    }
}

// Close reset password modal
function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').style.display = 'none';
    document.getElementById('resetPasswordForm').reset();
}

// Handle reset password
async function handleResetPassword(event) {
    event.preventDefault();

    const userId = document.getElementById('resetUserId').value;
    const newPassword = document.getElementById('resetNewPassword').value;
    const confirmPassword = document.getElementById('resetConfirmPassword').value;

    if (!newPassword || !confirmPassword) {
        showToast('error', 'Please fill in both password fields');
        return;
    }

    if (newPassword !== confirmPassword) {
        showToast('error', 'Passwords do not match');
        return;
    }

    try {
        const response = await fetch(`/api/auth/users/${userId}/reset-password`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ new_password: newPassword })
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
                    : 'Failed to reset password');
            throw new Error(message);
        }

        showToast('success', 'Password reset successfully');
        closeResetPasswordModal();
    } catch (error) {
        console.error('Reset password error:', error);
        showToast('error', error.message || 'Failed to reset password');
    }
}

// Handle edit user
async function handleEditUser(event) {
    event.preventDefault();
    
    const userId = document.getElementById('editUserId').value;
    const email = document.getElementById('editEmail').value;
    const fullName = document.getElementById('editFullName').value;
    const role = document.getElementById('editRole').value;
    const isActive = document.getElementById('editIsActive').value === 'true';
    
    try {
        const response = await fetch(`/api/auth/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                full_name: fullName || null,
                role,
                is_active: isActive
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }
        
        showToast('success', 'User updated successfully');
        closeEditUserModal();
        await loadUsers();
    } catch (error) {
        console.error('Error updating user:', error);
        showToast('error', error.message || 'Failed to update user');
    }
}

// Delete user
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/auth/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete user');
        }
        
        showToast('success', 'User deleted successfully');
        await loadUsers();
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('error', error.message || 'Failed to delete user');
    }
}
