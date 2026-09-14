// ============================================
// CREAR LECCIÓN DE TEXTO (templates/academi/courses/lecciones/crear_texto.html)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('form');
    var titleInput = document.getElementById('title');
    var submitBtn = document.getElementById('submitBtn');

    form.addEventListener('submit', function(e) {
        var valid = true;

        document.querySelectorAll('.is-invalid').forEach(function(el) { el.classList.remove('is-invalid'); });
        document.querySelectorAll('.invalid-feedback').forEach(function(el) { el.remove(); });

        function showError(input, message) {
            input.classList.add('is-invalid');
            var feedback = input.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                input.parentNode.insertBefore(feedback, input.nextSibling);
            }
            feedback.textContent = message;
            valid = false;
        }

        var title = titleInput.value.trim();
        if (!title) {
            showError(titleInput, 'El título es obligatorio.');
        } else if (title.length < 3) {
            showError(titleInput, 'El título debe tener al menos 3 caracteres.');
        }

        var contentInput = document.getElementById('content');
        var content = contentInput.value.trim();
        if (!content) {
            showError(contentInput, 'El contenido es obligatorio.');
        }

        if (!valid) {
            e.preventDefault();
            var firstError = form.querySelector('.is-invalid');
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
            var feedback = this.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        }
    });
});
