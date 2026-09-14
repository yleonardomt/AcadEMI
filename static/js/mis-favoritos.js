// ============================================
// MIS FAVORITOS (templates/academi/dashboard/mis_favoritos.html)
// ============================================

function removeFavorite(courseId, btn) {
    fetch('/course/' + courseId + '/favorite/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            showToast(data.message, 'success');
            var card = btn.closest('.col-md-6');
            if (card) card.remove();
        } else {
            showToast(data.message || 'Error al actualizar favoritos', 'error');
        }
    })
    .catch(function() {
        showToast('Error de conexión al servidor', 'error');
    });
}
