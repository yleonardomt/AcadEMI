// ============================================
// ESTADO GLOBAL
// ============================================
var cartState = {
    items: [],
    subtotal: 0,
    discount: 0,
    total: 0,
    couponCode: null,
    processing: false
};

// ============================================
// INICIALIZAR
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    updateCartState();
    loadCouponFromSession();
    initCardFields();
});

function initCardFields() {
    ['cardNumber', 'cardExpiry', 'cardCvc', 'cardHolder'].forEach(function(id) {
        var input = document.getElementById(id);
        if (!input) return;
        input.addEventListener('input', function() {
            if (id === 'cardNumber') {
                input.value = input.value.replace(/\D/g, '').slice(0, 16).replace(/(.{4})(?=.)/g, '$1 ');
            } else if (id === 'cardExpiry') {
                var digits = input.value.replace(/\D/g, '').slice(0, 4);
                input.value = digits.length > 2 ? digits.slice(0, 2) + '/' + digits.slice(2) : digits;
            } else if (id === 'cardCvc') {
                input.value = input.value.replace(/\D/g, '').slice(0, 3);
            }
            input.removeAttribute('aria-invalid');
            document.getElementById('cardError').hidden = true;
        });
    });
}

function validateCard() {
    var error = document.getElementById('cardError');
    function fail(id, message) {
        error.textContent = message;
        error.hidden = false;
        var field = document.getElementById(id);
        field.setAttribute('aria-invalid', 'true');
        field.focus();
        return null;
    }
    if (!document.getElementById('cardHolder').value.trim()) {
        return fail('cardHolder', 'Ingresa el nombre del titular de la tarjeta.');
    }
    var number = document.getElementById('cardNumber').value.replace(/\s/g, '');
    var cards = JSON.parse(document.getElementById('demoCards').textContent);
    var testCard = Object.keys(cards).find(function(key) { return cards[key].number === number; });
    if (!testCard) return fail('cardNumber', 'Usa una tarjeta de prueba para esta presentación: 4000 0566 5566 5556.');
    var expiry = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(document.getElementById('cardExpiry').value);
    if (!expiry) return fail('cardExpiry', 'Ingresa una fecha válida con formato MM/AA.');
    var now = new Date();
    if (2000 + Number(expiry[2]) < now.getFullYear() ||
            (2000 + Number(expiry[2]) === now.getFullYear() && Number(expiry[1]) < now.getMonth() + 1)) {
        return fail('cardExpiry', 'La tarjeta está vencida. Ingresa una fecha futura.');
    }
    if (!/^\d{3}$/.test(document.getElementById('cardCvc').value)) {
        return fail('cardCvc', 'El CVC debe tener 3 dígitos.');
    }
    return testCard;
}

// ============================================
// ACTUALIZAR ESTADO DEL CARRITO
// ============================================
function updateCartState() {
    var items = document.querySelectorAll('.cart-item');
    var subtotal = 0;
    var itemCount = items.length;

    items.forEach(function(item) {
        var price = parseFloat(item.dataset.price) || 0;
        var isFree = item.dataset.free === 'true';
        if (!isFree) {
            subtotal += price;
        }
    });

    cartState.items = items;
    cartState.subtotal = subtotal;
    cartState.total = Math.max(0, subtotal - cartState.discount);

    var subtotalDisplay = document.getElementById('subtotalDisplay');
    var totalDisplay = document.getElementById('totalDisplay');
    var cartBadge = document.getElementById('cartBadge');
    var discountRow = document.getElementById('discountRow');
    var discountDisplay = document.getElementById('discountDisplay');
    var checkoutBtn = document.getElementById('checkoutBtn');
    var cardFields = document.getElementById('debitCardFields');
    if (cardFields) {
        cardFields.hidden = cartState.total <= 0 || itemCount === 0;
        cardFields.disabled = cardFields.hidden;
    }

    if (subtotalDisplay) {
        subtotalDisplay.innerHTML = '<i class="fas fa-bolivian-sign"></i> ' + subtotal.toFixed(2);
    }
    if (totalDisplay) {
        totalDisplay.innerHTML = '<i class="fas fa-bolivian-sign"></i> ' + cartState.total.toFixed(2);
    }
    if (cartBadge) {
        cartBadge.innerHTML = '<i class="fas fa-book"></i> ' + itemCount + ' cursos';
    }

    if (cartState.discount > 0 && discountRow) {
        discountRow.style.display = 'flex';
        if (discountDisplay) {
            discountDisplay.innerHTML = '<i class="fas fa-bolivian-sign"></i> ' + cartState.discount.toFixed(2);
        }
    } else if (discountRow) {
        discountRow.style.display = 'none';
    }

    if (checkoutBtn) {
        checkoutBtn.disabled = cartState.processing || itemCount === 0 || (cartState.subtotal > 0 && checkoutBtn.dataset.demo !== 'true');
        checkoutBtn.innerHTML = cartState.subtotal > 0 && checkoutBtn.dataset.demo === 'true'
            ? '<i class="fas fa-bag-shopping"></i> Finalizar compra'
            : '<i class="fas fa-book-open"></i> Inscribirme gratis';
    }

}

// ============================================
// ELIMINAR DEL CARRITO
// ============================================
function removeFromCart(courseId) {
    fetch('/cart/remove/' + courseId + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Error en el servidor');
        }
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            if (typeof refreshCartBadge === 'function') {
                refreshCartBadge(data.items_count);
            }
            var item = document.getElementById('cart-item-' + courseId);
            if (item) {
                item.style.opacity = '0';
                item.style.transform = 'translateX(20px)';
                setTimeout(function() {
                    item.remove();
                    var remaining = document.querySelectorAll('.cart-item').length;
                    if (remaining === 0) {
                        location.reload();
                    } else {
                        updateCartState();
                        if (cartState.couponCode) {
                            removeCoupon();
                        }
                        showToast(data.message || 'Curso eliminado', 'success');
                    }
                }, 300);
            }
        } else {
            showToast(data.message || 'Error al eliminar', 'error');
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        showToast('Error de conexión al servidor', 'error');
    });
}

// ============================================
// CUPÓN - APLICAR
// ============================================
function applyCoupon() {
    var input = document.getElementById('couponInput');
    var code = input.value.trim().toUpperCase();
    var feedback = document.getElementById('couponFeedback');
    var btn = document.getElementById('applyCouponBtn');

    if (!code) {
        feedback.className = 'coupon-feedback error';
        feedback.innerHTML = '<i class="fas fa-exclamation-circle"></i> Ingresa un código de cupón.';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';

    fetch('/api/validate-coupon/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success && data.applied) {
            cartState.discount = data.discount_amount;
            cartState.couponCode = code;
            cartState.total = cartState.subtotal - cartState.discount;

            feedback.className = 'coupon-feedback success';
            feedback.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;

            document.getElementById('activeCouponCode').textContent = code;
            document.getElementById('activeCouponDisplay').style.display = 'block';
            input.value = '';
            input.disabled = true;

            updateCartState();
            showToast('Cupón aplicado: ' + data.message, 'success');
        } else {
            feedback.className = 'coupon-feedback error';
            feedback.textContent = data.message || 'No se pudo aplicar el cupón.';
        }
    })
    .catch(function() {
        feedback.className = 'coupon-feedback error';
        feedback.innerHTML = '<i class="fas fa-times-circle"></i> Error al verificar el cupón.';
    })
    .finally(function() {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Aplicar';
    });
}

// ============================================
// CUPÓN - QUITAR
// ============================================
function removeCoupon() {
    cartState.discount = 0;
    cartState.couponCode = null;
    cartState.total = cartState.subtotal;

    var activeCoupon = document.getElementById('activeCouponDisplay');
    var couponInput = document.getElementById('couponInput');
    var couponFeedback = document.getElementById('couponFeedback');

    if (activeCoupon) activeCoupon.style.display = 'none';
    if (couponInput) {
        couponInput.disabled = false;
        couponInput.value = '';
    }
    if (couponFeedback) {
        couponFeedback.className = 'coupon-feedback';
        couponFeedback.innerHTML = '';
    }

    updateCartState();
    showToast('Cupón eliminado', 'success');
}

// ============================================
// CARGAR CUPÓN DESDE SESIÓN
// ============================================
function loadCouponFromSession() {
    fetch('/api/get-active-coupon/?subtotal=' + encodeURIComponent(cartState.subtotal), {
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success && data.coupon) {
            cartState.discount = data.discount_amount;
            cartState.couponCode = data.code;
            cartState.total = cartState.subtotal - cartState.discount;

            document.getElementById('activeCouponCode').textContent = data.code;
            document.getElementById('activeCouponDisplay').style.display = 'block';
            document.getElementById('couponInput').disabled = true;

            updateCartState();
        }
    })
    .catch(function() {});
}

// ============================================
// PROCESAR COMPRA
// ============================================
function processCheckout() {
    var btn = document.getElementById('checkoutBtn');
    if (!btn || cartState.processing || !cartState.items.length) return;
    if (cartState.subtotal > 0 && btn.dataset.demo !== 'true') {
        showToast('Las compras de cursos pagos aún no están habilitadas.', 'error');
        return;
    }

    var form = document.getElementById('paymentForm');
    if (!form.reportValidity()) return;
    var testCard = null;
    if (cartState.total > 0) {
        testCard = validateCard();
        if (!testCard) return;
    }

    var fullName = document.getElementById('fullName');
    var email = document.getElementById('email');
    var phone = document.getElementById('phone');
    var address = document.getElementById('address');

    if (!fullName || !fullName.value.trim()) {
        showToast('Ingresa tu nombre completo', 'error');
        btn.disabled = false;
        updateCartState();
        return;
    }

    if (!email || !email.value.trim()) {
        showToast('Ingresa tu correo electrónico', 'error');
        btn.disabled = false;
        updateCartState();
        return;
    }

    var payload = {
        full_name: fullName.value.trim(),
        email: email.value.trim(),
        phone: phone ? phone.value.trim() : '',
        address: address ? address.value.trim() : '',
        payment_method: cartState.total > 0 ? 'debit_card' : 'free',
        test_card: testCard,
        coupon_code: cartState.couponCode
    };

    // Solo se envía el identificador público de la tarjeta de prueba.
    // Número, titular de tarjeta, fecha y CVC permanecen en el navegador.
    cartState.processing = true;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Procesando...';

    fetch('/checkout/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(function(response) {
        if (!response.ok) {
            return response.json().then(function(data) {
                throw new Error(data.message || 'Error en el servidor');
            });
        }
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            ['cardNumber', 'cardExpiry', 'cardCvc', 'cardHolder'].forEach(function(id) {
                var input = document.getElementById(id);
                if (input) input.value = '';
            });
            showToast(data.message || 'Inscripción realizada.', 'success');
            setTimeout(function() {
                window.location.href = '/my-courses/';
            }, 1500);
        } else {
            cartState.processing = false;
            showToast(data.message || 'Error al procesar la compra', 'error');
            btn.disabled = false;
            updateCartState();
        }
    })
    .catch(function(error) {
        cartState.processing = false;
        console.error('Error:', error);
        showToast(error.message || 'Error de conexión al servidor', 'error');
        btn.disabled = false;
        updateCartState();
    });
}

// Exponer funciones globalmente (usadas por atributos onclick del HTML)
window.removeFromCart = removeFromCart;
window.applyCoupon = applyCoupon;
window.removeCoupon = removeCoupon;
window.processCheckout = processCheckout;
