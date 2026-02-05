// Shared utility functions for LDAPGuard web interface

/**
 * Escapes HTML special characters to prevent XSS attacks.
 * This function converts potentially dangerous characters into their HTML entity equivalents.
 * 
 * @param {string|null|undefined} text - The text to escape
 * @returns {string} The escaped text safe for insertion into HTML, or empty string if input is null/undefined
 * 
 * @example
 * escapeHtml('<script>alert("XSS")</script>')
 * // Returns: '&lt;script&gt;alert("XSS")&lt;/script&gt;'
 */
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
