document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const titleInput = document.getElementById('title');
    const submitBtn = document.getElementById('submitBtn');

    form.addEventListener('submit', function(e) {
        let valid = true;

        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        function showError(input, message) {
            input.classList.add('is-invalid');
            let feedback = input.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                input.parentNode.insertBefore(feedback, input.nextSibling);
            }
            feedback.textContent = message;
            valid = false;
        }

        const title = titleInput.value.trim();
        if (!title) {
            showError(titleInput, 'El título es obligatorio.');
        } else if (title.length < 3) {
            showError(titleInput, 'El título debe tener al menos 3 caracteres.');
        }

        const content = document.getElementById('content').value.trim();
        if (!content) {
            showError(document.getElementById('content'), 'La descripción de la tarea es obligatoria.');
        }

        const days = document.getElementById('assignment_deadline_days').value;
        const hours = document.getElementById('assignment_deadline_hours').value;

        if (!days || parseInt(days) < 1) {
            showError(document.getElementById('assignment_deadline_days'), 'Debes establecer al menos 1 día para entregar.');
        }

        if (hours && (parseInt(hours) < 0 || parseInt(hours) > 23)) {
            showError(document.getElementById('assignment_deadline_hours'), 'Las horas deben ser entre 0 y 23.');
        }

        if (!valid) {
            e.preventDefault();
            const firstError = form.querySelector('.is-invalid');
            if (firstError) firstError.focus();
            return false;
        }

        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';
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
