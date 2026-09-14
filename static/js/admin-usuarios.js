// ============================================
// GESTIÓN DE USUARIOS - ADMIN (templates/academi/users/admin_usuarios.html)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // ====== CONFIRMAR ELIMINACIÓN (SIN ALERT) ======
    var deleteButtons = document.querySelectorAll('.btn-delete-user');
    var modal = document.getElementById('confirmModal');
    var modalUsername = document.getElementById('modalUsername');
    var modalMessage = document.getElementById('modalMessage');
    var modalSubMessage = document.getElementById('modalSubMessage');
    var confirmBtn = document.getElementById('modalConfirmBtn');

    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var username = this.getAttribute('data-user');
            var url = this.getAttribute('data-url');

            modalUsername.textContent = username;
            modalMessage.innerHTML = '¿Estás seguro de eliminar a <span class="fw-bold" style="color: var(--danger);">' + username + '</span>?';
            modalSubMessage.textContent = 'Esta acción no se puede deshacer.';
            confirmBtn.href = url;

            var modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        });
    });

    // ====== ACTIVAR/DESACTIVAR CON CONFIRMACIÓN ======
    var toggleButtons = document.querySelectorAll('.btn-toggle-user');

    toggleButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var username = this.getAttribute('data-user');
            var url = this.getAttribute('data-url');
            var isActive = this.classList.contains('btn-outline-danger');

            modalUsername.textContent = username;
            if (isActive) {
                modalMessage.innerHTML = '¿Estás seguro de <span class="fw-bold" style="color: var(--danger);">desactivar</span> a ' + username + '?';
                modalSubMessage.textContent = 'El usuario no podrá iniciar sesión.';
                confirmBtn.className = 'btn btn-warning';
                confirmBtn.innerHTML = '<i class="fas fa-pause"></i> Desactivar';
            } else {
                modalMessage.innerHTML = '¿Estás seguro de <span class="fw-bold" style="color: var(--success);">activar</span> a ' + username + '?';
                modalSubMessage.textContent = 'El usuario podrá iniciar sesión nuevamente.';
                confirmBtn.className = 'btn btn-success';
                confirmBtn.innerHTML = '<i class="fas fa-play"></i> Activar';
            }
            confirmBtn.href = url;

            var modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        });
    });
});
