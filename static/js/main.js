/**
 * University Event Management System (UEMS)
 * Global Vanilla JavaScript
 * 
 * Provides base interactions without frontend libraries or frameworks.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alert messages after 6 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });

    console.log('UEMS Foundation initialized successfully.');
});
