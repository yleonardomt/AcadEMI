// ============================================
// MODAL DE CONFIRMACIÓN COMPARTIDO (reemplaza confirm() nativo)
// Ver templates/partials/confirm_modal.html
// ============================================
//
// Uso declarativo (lo normal para "eliminar esto", "desactivar aquello"):
//   <form method="POST" data-confirm="¿Eliminar este curso?">...</form>
// Cualquier form con data-confirm se intercepta automáticamente: al
// enviarlo se muestra este modal, y solo si el usuario confirma se
// hace el submit real. data-confirm-icon/-button-class/-button-label
// son opcionales para personalizar el ícono y el botón de confirmar.
//
// Uso imperativo (cuando la acción no es un <form>, p. ej. un fetch):
//   showConfirm('¿Enviar de todos modos?', function() { ...continuar... });

document.addEventListener('DOMContentLoaded', function () {
    var modalEl = document.getElementById('globalConfirmModal');
    if (!modalEl) return;

    var messageEl = document.getElementById('globalConfirmMessage');
    var iconEl = document.getElementById('globalConfirmIcon');
    var confirmBtn = document.getElementById('globalConfirmBtn');
    var modal = new bootstrap.Modal(modalEl);
    var onConfirm = null;

    function openWith(message, options) {
        options = options || {};
        messageEl.textContent = message;
        iconEl.className = options.icon || 'fas fa-exclamation-circle';
        confirmBtn.className = 'btn ' + (options.buttonClass || 'btn-danger');
        confirmBtn.innerHTML = options.buttonLabel || '<i class="fas fa-check"></i> Confirmar';
        onConfirm = options.onConfirm || null;
        modal.show();
    }

    window.showConfirm = function (message, onConfirmCallback, options) {
        options = options || {};
        options.onConfirm = onConfirmCallback;
        openWith(message, options);
    };

    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (form.dataset.confirmed === 'true') return; // ya se confirmó, dejar pasar
            e.preventDefault();
            openWith(form.dataset.confirm, {
                icon: form.dataset.confirmIcon,
                buttonClass: form.dataset.confirmButtonClass,
                buttonLabel: form.dataset.confirmButtonLabel,
                onConfirm: function () {
                    form.dataset.confirmed = 'true';
                    if (form.requestSubmit) {
                        form.requestSubmit();
                    } else {
                        form.submit();
                    }
                }
            });
        });
    });

    confirmBtn.addEventListener('click', function () {
        modal.hide();
        var callback = onConfirm;
        onConfirm = null;
        if (callback) callback();
    });
});
