// ============================================
// DETALLE DE CURSO (templates/academi/courses/curso_detalle.html)
// ============================================

// ============================================
// MODAL DE VIDEO PROMOCIONAL
// ============================================
function openVideoModal() {
    var modal = new bootstrap.Modal(document.getElementById('videoModal'));
    modal.show();
}

function closeVideoModal() {
    var modalElement = document.getElementById('videoModal');
    var modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
    }
    var video = modalElement.querySelector('video');
    if (video) {
        video.pause();
    }
}

// ============================================
// CARRITO
// ============================================
var cartItems = [];

function addToCart(courseId, courseTitle) {
    var btn = document.getElementById('cartBtn' + courseId);
    var txt = document.getElementById('cartText' + courseId);

    if (!btn) return;

    if (cartItems.includes(courseId)) {
        fetch('/cart/remove/' + courseId + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cartItems = cartItems.filter(function(id) { return id !== courseId; });
                btn.classList.remove('in-cart');
                if (txt) txt.textContent = 'Agregar al carrito';
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
            if (txt) txt.textContent = 'En carrito';
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

function updateCartCount() {
    refreshCartBadge(cartItems.length);
}

document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // INICIALIZAR CARRITO
    // ============================================
    fetch('/cart/items/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cartItems = data.items || [];
                cartItems.forEach(function(id) {
                    var btn = document.getElementById('cartBtn' + id);
                    var txt = document.getElementById('cartText' + id);
                    if (btn) {
                        btn.classList.add('in-cart');
                        if (txt) txt.textContent = 'En carrito';
                    }
                });
                updateCartCount();
            }
        })
        .catch(function() {});

    // Pausar video al cerrar el modal
    document.getElementById('videoModal').addEventListener('hidden.bs.modal', function() {
        var video = this.querySelector('video');
        if (video) {
            video.pause();
        }
    });
});
