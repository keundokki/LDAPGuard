// Batch operations for backups

// Toggle all backup checkboxes
function toggleAllBackups(checkbox) {
    const checkboxes = document.querySelectorAll('.backup-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBatchDeleteButton();
}

// Update batch delete button visibility
function updateBatchDeleteButton() {
    const checkboxes = document.querySelectorAll('.backup-checkbox:checked');
    const button = document.getElementById('batchDeleteBtn');
    
    if (checkboxes.length > 0) {
        button.style.display = 'block';
        button.textContent = `🗑️ Delete Selected (${checkboxes.length})`;
    } else {
        button.style.display = 'none';
    }
}

// Batch delete selected backups
async function batchDeleteBackups() {
    const checkboxes = document.querySelectorAll('.backup-checkbox:checked');
    const backupIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (backupIds.length === 0) {
        showToast('error', 'No backups selected');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${backupIds.length} backup(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/backups/batch-delete', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ backup_ids: backupIds })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete backups');
        }
        
        const result = await response.json();
        showToast('success', result.message || `Deleted ${result.deleted} backups`);
        
        // Uncheck select all
        document.getElementById('select-all-backups').checked = false;
        
        // Reload backups if function is available
        if (typeof loadBackups === 'function') {
            await loadBackups();
        } else {
            console.warn('loadBackups function is not available; skipping backups reload.');
        }
    } catch (error) {
        console.error('Batch delete error:', error);
        showToast('error', error.message || 'Failed to delete backups');
    }
}

// Test LDAP connection
async function testLDAPConnection() {
    const host = document.getElementById('serverHost').value;
    const port = document.getElementById('serverPort').value;
    const use_ssl = document.getElementById('serverSSL').checked;
    const base_dn = document.getElementById('serverBaseDN').value;
    const bind_dn = document.getElementById('serverBindDN').value || null;
    const bind_password = document.getElementById('serverBindPassword').value || null;
    
    if (!host || !port || !base_dn) {
        showToast('error', 'Please fill in required fields (Host, Port, Base DN)');
        return;
    }
    
    const testData = {
        host,
        port: parseInt(port),
        use_ssl,
        base_dn,
        bind_dn,
        bind_password
    };
    
    showToast('info', 'Testing LDAP connection...');
    
    try {
        const response = await fetch('/api/ldap-servers/test', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('success', `✅ Connection successful! ${result.message || ''}`);
        } else {
            showToast('error', `❌ Connection failed: ${result.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Test connection error:', error);
        showToast('error', 'Failed to test connection');
    }
}
