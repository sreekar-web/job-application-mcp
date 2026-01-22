/**
 * Job Application Dashboard - Main JavaScript
 * Handles interactivity, AJAX calls, and real-time updates
 */

// Status badge color mapping
const STATUS_COLORS = {
    'SUBMITTED': '#667eea',
    'PENDING_USER_INPUT': '#f39c12',
    'VIEWED': '#16a085',
    'INTERVIEW': '#3498db',
    'OFFER': '#2ecc71',
    'ACCEPTED': '#27ae60',
    'REJECTED': '#e74c3c',
    'SAVED': '#95a5a6'
};

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    initializePopovers();
});

/**
 * Initialize Bootstrap popovers and tooltips
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Get color for status badge
 */
function getStatusColor(status) {
    return STATUS_COLORS[status] || '#95a5a6';
}

/**
 * Get CSS class for status badge
 */
function getStatusClass(status) {
    return 'status-' + status.toLowerCase();
}

/**
 * Show loading spinner
 */
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    element.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
}

/**
 * Show error message
 */
function showError(element, message) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    element.innerHTML = `<div class="alert alert-danger" role="alert"><i class="fas fa-exclamation-circle"></i> ${message}</div>`;
}

/**
 * Make API call with error handling
 */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            body: options.body ? JSON.stringify(options.body) : null
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Debounce function to prevent excessive API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Calculate days remaining until date
 */
function daysUntil(dateString) {
    const now = new Date();
    const target = new Date(dateString);
    const diff = target - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days;
}

/**
 * Calculate days since date
 */
function daysSince(dateString) {
    const now = new Date();
    const target = new Date(dateString);
    const diff = now - target;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days;
}

/**
 * Generate status badge HTML
 */
function generateStatusBadge(status) {
    return `<span class="badge badge-status ${getStatusClass(status)}">${status.replace(/_/g, ' ')}</span>`;
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone format
 */
function isValidPhone(phone) {
    const re = /^[\d\s\-\+\(\)]{10,}$/;
    return re.test(phone.replace(/\s/g, ''));
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('main') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    if (duration) {
        setTimeout(() => {
            alertDiv.remove();
        }, duration);
    }

    return alertDiv;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => showNotification('Copied to clipboard!', 'success'))
            .catch(() => fallbackCopy(text));
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showNotification('Copied to clipboard!', 'success');
}

/**
 * Animate number increment (for stats cards)
 */
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * Export data to CSV
 */
function exportToCSV(data, filename = 'data.csv') {
    if (!data || data.length === 0) {
        alert('No data to export');
        return;
    }

    const headers = Object.keys(data[0]);
    let csv = headers.join(',') + '\n';

    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header];
            // Escape quotes and wrap in quotes if contains comma
            const escaped = String(value || '').replace(/"/g, '""');
            return escaped.includes(',') ? `"${escaped}"` : escaped;
        });
        csv += values.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

/**
 * Clear all filters and search
 */
function clearAllFilters() {
    document.querySelectorAll('.form-control, .form-select').forEach(el => {
        if (el.type !== 'button' && el.type !== 'submit') {
            el.value = '';
        }
    });
    // Trigger change event to reload data
    document.dispatchEvent(new Event('filterChange'));
}

/**
 * Add keyboard shortcuts
 */
document.addEventListener('keydown', function(event) {
    // Ctrl+K: Focus search
    if (event.ctrlKey && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.focus();
    }

    // Escape: Close modals
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    }
});

/**
 * Log to console with timestamp
 */
function logDebug(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] ${message}`, data || '');
}

/**
 * Rate limiting for API calls
 */
class RateLimiter {
    constructor(maxCalls, timeWindow) {
        this.maxCalls = maxCalls;
        this.timeWindow = timeWindow;
        this.calls = [];
    }

    async call(fn) {
        const now = Date.now();
        this.calls = this.calls.filter(time => now - time < this.timeWindow);

        if (this.calls.length >= this.maxCalls) {
            const wait = this.calls[0] + this.timeWindow - now;
            await new Promise(resolve => setTimeout(resolve, wait));
            return this.call(fn);
        }

        this.calls.push(now);
        return fn();
    }
}

// Create a rate limiter instance (5 calls per 5 seconds)
const apiLimiter = new RateLimiter(5, 5000);

export {
    apiCall,
    debounce,
    formatDate,
    formatDateTime,
    getStatusColor,
    getStatusClass,
    showLoading,
    showError,
    showNotification,
    daysUntil,
    daysSince,
    generateStatusBadge,
    isValidEmail,
    isValidPhone,
    copyToClipboard,
    animateValue,
    exportToCSV,
    clearAllFilters,
    logDebug,
    RateLimiter,
    apiLimiter
};
