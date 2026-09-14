// ============================================
// MIS CURSOS (templates/academi/courses/mis_cursos.html)
// ============================================

var deleteCourseId = null;

function openDeleteModal(courseTitle, courseId) {
    document.getElementById('deleteCourseTitle').textContent = courseTitle;
    deleteCourseId = courseId;
    document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteCourseId = null;
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
        if (deleteCourseId) {
            deleteCourse(deleteCourseId);
        }
    });

    document.getElementById('deleteModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeDeleteModal();
        }
    });
});

// ============================================
// ELIMINAR CURSO (vía AJAX)
// ============================================
function deleteCourse(courseId) {
    fetch('/course/delete/' + courseId + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        closeDeleteModal();
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(function() {
                location.reload();
            }, 1000);
        } else {
            showToast(data.message || 'Error al eliminar el curso', 'error');
        }
    })
    .catch(function() {
        closeDeleteModal();
        showToast('Error de conexión al servidor', 'error');
    });
}
