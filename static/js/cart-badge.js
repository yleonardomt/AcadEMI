// ============================================
// CONTADOR DE CARRITO EN EL NAV
// Fuente única para actualizar el badge del carrito
// en el navbar y en el menú lateral (partials/header.html).
// Los botones "agregar/quitar del carrito" de catálogo,
// búsqueda y detalle de curso llaman a refreshCartBadge(count)
// después de cada cambio en vez de manipular el DOM cada uno
// por su cuenta.
// ============================================

function refreshCartBadge(count) {
    document.querySelectorAll('.nav-cart-badge').forEach(function(badge) {
        badge.textContent = count;
        badge.hidden = count <= 0;
    });
}

window.refreshCartBadge = refreshCartBadge;
