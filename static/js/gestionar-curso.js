// ============================================
// GESTIONAR CURSO (templates/academi/courses/gestionar_curso.html)
// ============================================

var deleteUrl = '';

function showConfirmModal(title, message, url) {
    document.getElementById('confirmTitle').textContent = title || 'Confirmar eliminación';
    document.getElementById('confirmMessage').innerHTML = message || '¿Estás seguro de que deseas eliminar esto?';
    deleteUrl = url || '#';
    document.getElementById('confirmDeleteBtn').href = deleteUrl;
    new bootstrap.Modal(document.getElementById('confirmModal')).show();
}

function deleteItem() {
    if (deleteUrl && deleteUrl !== '#') {
        window.location.href = deleteUrl;
    }
    return false;
}

function closeModal() {
    var modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
    if (modal) modal.hide();
}

function confirmDeleteModule(moduleId, moduleTitle) {
    showConfirmModal(
        'Eliminar módulo',
        '¿Estás seguro de eliminar el módulo "<strong>' + moduleTitle + '</strong>"?<br>Las lecciones que contiene también se eliminarán.',
        '/module/delete/' + moduleId + '/'
    );
}

function confirmDeleteLesson(lessonId, lessonTitle) {
    showConfirmModal(
        'Eliminar lección',
        '¿Estás seguro de eliminar la lección "<strong>' + lessonTitle + '</strong>"?',
        '/lesson/delete/' + lessonId + '/'
    );
}

function reorderModule(moduleId, direction) {
    fetch('/module/reorder/' + moduleId + '/' + direction + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                showToast('Error al reordenar el módulo', 'danger');
            }
        })
        .catch(function() {
            showToast('Error de conexión al servidor', 'danger');
        });
}

function reorderLesson(lessonId, direction) {
    fetch('/lesson/reorder/' + lessonId + '/' + direction + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                showToast('Error al reordenar la lección', 'danger');
            }
        })
        .catch(function() {
            showToast('Error de conexión al servidor', 'danger');
        });
}

document.addEventListener('DOMContentLoaded', function() {
    var publishBtn = document.getElementById('publishBtn');
    if (publishBtn) {
        publishBtn.addEventListener('click', function(e) {
            e.preventDefault();
            new bootstrap.Modal(document.getElementById('publishModal')).show();
        });
    }

    document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
        deleteUrl = '';
        document.getElementById('confirmDeleteBtn').href = '#';
        document.getElementById('confirmMessage').innerHTML = '¿Estás seguro de que deseas eliminar esto?';
    });
});
