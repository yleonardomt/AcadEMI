// ============================================
// CATÁLOGO DE CURSOS (templates/academi/courses/catalogo.html)
// ============================================

    // ============================================
    // FAVORITOS
    // ============================================
    function toggleFavorite(courseId, btn) {
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
                btn.classList.toggle('active', data.is_favorite);
                var icon = btn.querySelector('i');
                icon.className = data.is_favorite ? 'fas fa-heart' : 'far fa-heart';
                showToast(data.message, 'success');
            } else {
                showToast(data.message || 'Error al actualizar favoritos', 'error');
            }
        })
        .catch(function() {
            showToast('Error de conexión al servidor', 'error');
        });
    }

    // ============================================
    // CARRITO - VARIABLES GLOBALES
    // ============================================
    var cartItems = [];

    // ============================================
    // AGREGAR AL CARRITO
    // ============================================
    function addToCart(courseId, courseTitle) {
        var btn = document.getElementById('cartBtn' + courseId);

        if (!btn) return;

        // Verificar si ya está en el carrito
        if (cartItems.includes(courseId)) {
            // Quitar del carrito (vía AJAX)
            fetch('/cart/remove/' + courseId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    cartItems = cartItems.filter(function(id) { return id !== courseId; });
                    btn.classList.remove('in-cart');
                    btn.innerHTML = '<i class="fas fa-shopping-cart"></i><span class="btn-text" id="cartText' + courseId + '">Carrito</span>';
                    showToast('Curso "' + courseTitle + '" eliminado del carrito', 'error');
                    updateCartCount();
                } else {
                    showToast(data.message || 'Error al quitar del carrito', 'error');
                }
            })
            .catch(function() {
                showToast('Error de conexión al servidor', 'error');
            });
            return;
        }

        // Agregar al carrito (vía AJAX)
        fetch('/cart/add/' + courseId + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ course_id: courseId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cartItems.push(courseId);
                btn.classList.add('in-cart');
                btn.innerHTML = '<i class="fas fa-check"></i><span class="btn-text" id="cartText' + courseId + '">En carrito</span>';
                showToast('Curso "' + courseTitle + '" agregado al carrito', 'success');
                updateCartCount();
            } else {
                showToast(data.message || 'Error al agregar al carrito', 'error');
            }
        })
        .catch(function() {
            showToast('Error de conexión al servidor', 'error');
        });
    }

    // ============================================
    // ACTUALIZAR CONTADOR DEL CARRITO
    // ============================================
    function updateCartCount() {
        refreshCartBadge(cartItems.length);
    }

    // ============================================
    // INICIALIZAR CARRITO
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        // Obtener items del carrito desde el servidor
        fetch('/cart/items/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    cartItems = data.items || [];
                    // Actualizar botones
                    cartItems.forEach(function(id) {
                        var btn = document.getElementById('cartBtn' + id);
                        if (btn) {
                            btn.classList.add('in-cart');
                            btn.innerHTML = '<i class="fas fa-check"></i><span class="btn-text" id="cartText' + id + '">En carrito</span>';
                        }
                    });
                    updateCartCount();
                }
            })
            .catch(function() {});
    });

    // ============================================
    // CIERRE AUTOMÁTICO DE TOAST
    // ============================================
    document.addEventListener('click', function(e) {
        if (e.target.closest('.toast-close')) {
            var toast = e.target.closest('.toast-custom');
            if (toast) {
                toast.classList.add('removing');
                setTimeout(function() {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }
    });
