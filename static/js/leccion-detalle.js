function markComplete(lessonId) {
    var btn = document.getElementById('completeBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

    fetch('/lesson/' + lessonId + '/complete/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Lección completada correctamente', 'success');

            var progressBar = document.querySelector('.progress-bar');
            var progressText = document.querySelector('.progress-mini .fw-semibold + span');
            var progressSmall = document.querySelector('.progress-mini small');

            if (progressBar) {
                progressBar.style.width = data.progress + '%';
            }
            if (progressText) {
                progressText.textContent = data.progress + '%';
            }
            if (progressSmall) {
                progressSmall.innerHTML = `
                    <i class="fas fa-check-circle" style="color: var(--success);"></i>
                    ${data.completed_count} de ${data.total_lessons} lecciones completadas
                    ${data.progress == 100 ? '<span class="badge bg-success ms-2"><i class="fas fa-award"></i> Completado</span>' : ''}
                `;
            }

            btn.innerHTML = '<i class="fas fa-check-circle"></i> Completada';
            btn.className = 'btn btn-secondary';
            btn.disabled = true;

            if (data.progress == 100) {
                setTimeout(function() {
                    showToast('Felicidades, has completado el curso', 'success');
                }, 500);
            }

        } else {
            showToast(data.message || 'Error al marcar como completada', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check"></i> Marcar como completada';
        }
    })
    .catch(function() {
        showToast('Error de conexión al servidor', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Marcar como completada';
    });
}
