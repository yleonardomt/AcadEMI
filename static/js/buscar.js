// ============================================
// BUSCAR CURSOS (templates/academi/courses/buscar.html)
// ============================================

var cartItems = [];

function addToCart(courseId, courseTitle) {
    var btn = document.getElementById('cartBtn' + courseId);
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
                btn.innerHTML = '<i class="fas fa-shopping-cart"></i>';
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
            btn.innerHTML = '<i class="fas fa-check"></i>';
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
    var searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.focus();
        searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
    }

    fetch('/cart/items/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cartItems = data.items || [];
                cartItems.forEach(function(id) {
                    var btn = document.getElementById('cartBtn' + id);
                    if (btn) {
                        btn.classList.add('in-cart');
                        btn.innerHTML = '<i class="fas fa-check"></i>';
                    }
                });
            }
        })
        .catch(function() {});
});
