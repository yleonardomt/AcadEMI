// ============================================
// MODALES SIN FONDO NEGRO (ver components/modals.css)
// ============================================

function openModalWithoutBackdrop(modalId) {
    document.querySelectorAll('.modal-backdrop').forEach(function(el) {
        el.remove();
    });
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';

    var modalElement = document.getElementById(modalId);
    if (!modalElement) {
        console.error('Modal no encontrado:', modalId);
        return;
    }

    var modal = new bootstrap.Modal(modalElement, {
        backdrop: false,
        keyboard: true
    });
    modal.show();
}

function closeModalWithoutBackdrop(modalId) {
    var modalElement = document.getElementById(modalId);
    if (!modalElement) return;

    var modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
    }

    document.querySelectorAll('.modal-backdrop').forEach(function(el) {
        el.remove();
    });
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
}

window.openModalWithoutBackdrop = openModalWithoutBackdrop;
window.closeModalWithoutBackdrop = closeModalWithoutBackdrop;

// Cerrar cualquier modal abierto con la tecla ESC
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(function(modal) {
                if (modal.id) {
                    closeModalWithoutBackdrop(modal.id);
                }
            });
        }
    });
});
