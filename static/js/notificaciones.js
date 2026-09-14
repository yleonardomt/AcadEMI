// ============================================
// NOTIFICACIONES (templates/academi/pages/notificaciones.html)
// ============================================

function marcarTodasLeidas() {
    fetch('/notifications/marcar-todas/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        }
    })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                location.reload();
            }
        })
        .catch(function(error) { console.error('Error:', error); });
}
