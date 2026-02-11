/* Atelier Alami - Main JS */

// HTMX configuration
document.addEventListener('htmx:configRequest', function(event) {
  // Add any global headers if needed
});

// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
  // Close any alerts without Alpine
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(function(alert) {
    setTimeout(function() {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(2rem)';
      setTimeout(function() { alert.remove(); }, 300);
    }, 4000);
  });
});

// Confirm delete helper
function confirmDelete(name) {
  return confirm('Are you sure you want to delete "' + name + '"?');
}
