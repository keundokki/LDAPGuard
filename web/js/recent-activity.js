// Helper functions for graphical recent activity display

function getActivityColor(status) {
    const colorMap = {
        'completed': '#16a34a',
        'in_progress': '#f97316',
        'pending': '#3b82f6',
        'failed': '#dc2626'
    };
    return colorMap[status] || '#64748b';
}

function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    
    return date.toLocaleString(undefined, { month: 'short', day: 'numeric' });
}

function renderRecentActivityGraphical(backups, restores, servers) {
    const activityEl = document.getElementById('recent-activity');
    if (!activityEl) return;

    const serverMap = new Map(servers.map(server => [parseInt(server.id), server.name]));

    const activities = [
        ...backups.map(backup => ({
            type: 'Backup',
            id: parseInt(backup.id),
            serverId: parseInt(backup.ldap_server_id),
            status: backup.status,
            createdAt: backup.created_at,
            detail: backup.backup_type ? `${backup.backup_type}` : 'backup'
        })),
        ...restores.map(restore => ({
            type: 'Restore',
            id: parseInt(restore.id),
            serverId: parseInt(restore.ldap_server_id),
            status: restore.status,
            createdAt: restore.created_at,
            detail: `from #${parseInt(restore.backup_id)}`
        }))
    ];

    const recent = activities
        .filter(item => item.createdAt)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .slice(0, 8);

    if (recent.length === 0) {
        activityEl.innerHTML = '<p class="no-data">No recent activity</p>';
        return;
    }

    activityEl.innerHTML = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;">' +
        recent.map(item => {
            const serverName = serverMap.get(item.serverId) || 'Unknown Server';
            const icon = item.type === 'Backup' ? '💾' : '♻️';
            const color = getActivityColor(item.status);
            const timeAgo = formatTimeAgo(item.createdAt);
            const statusLabel = item.status ? item.status.replace('_', ' ') : 'pending';
            
            return `
                <div style="background: var(--surface); border: 2px solid ${color}; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: ${color};"></div>
                    <div style="display: flex; align-items: flex-start; gap: 8px;">
                        <div style="font-size: 28px; line-height: 1;">${icon}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 0.95em; color: var(--text-primary);">${escapeHtml(item.type)} #${item.id}</div>
                            <div style="font-size: 0.85em; color: var(--text-secondary); margin-top: 2px;">${escapeHtml(serverName)}</div>
                        </div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 6px 8px; border-radius: 4px; font-size: 0.85em; color: var(--text-secondary); font-weight: 500;">${escapeHtml(item.detail)}</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 4px;">
                        <span style="font-size: 0.8em; color: var(--text-secondary);">${timeAgo}</span>
                        <span style="padding: 2px 8px; background: ${color}; color: white; border-radius: 3px; font-size: 0.75em; font-weight: 600; text-transform: capitalize;">${statusLabel}</span>
                    </div>
                </div>
            `;
        }).join('') +
    '</div>';
}
