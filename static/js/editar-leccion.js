// ============================================
// EDITAR LECCIÓN (templates/academi/courses/editar_leccion.html)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const titleInput = document.getElementById('title');
    const submitBtn = document.getElementById('submitBtn');
    const deadlineDaysInput = document.getElementById('assignment_deadline_days');
    const deadlineHoursInput = document.getElementById('assignment_deadline_hours');

    function showError(input, message) {
        input.classList.add('is-invalid');
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
        feedback.textContent = message;
    }

    form.addEventListener('submit', function(e) {
        let valid = true;

        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        const title = titleInput.value.trim();
        if (!title) {
            showError(titleInput, 'El título es obligatorio.');
            valid = false;
        } else if (title.length < 3) {
            showError(titleInput, 'El título debe tener al menos 3 caracteres.');
            valid = false;
        }

        // Validar plazo de entrega si es tarea (solo presente en el DOM
        // cuando lesson.lesson_type == 'assignment')
        if (deadlineDaysInput) {
            const days = deadlineDaysInput.value;
            const hours = deadlineHoursInput.value;

            if (!days || parseInt(days) < 1) {
                showError(deadlineDaysInput, 'Debes establecer al menos 1 día para entregar.');
                valid = false;
            }

            if (hours && (parseInt(hours) < 0 || parseInt(hours) > 23)) {
                showError(deadlineHoursInput, 'Las horas deben ser entre 0 y 23.');
                valid = false;
            }
        }

        if (!valid) {
            e.preventDefault();
            const firstError = form.querySelector('.is-invalid');
            if (firstError) firstError.focus();
            return false;
        }

        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        submitBtn.disabled = true;
        return true;
    });

    titleInput.addEventListener('input', function() {
        if (this.value.trim().length >= 3) {
            this.classList.remove('is-invalid');
            const feedback = this.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        }
    });
});
