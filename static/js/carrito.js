// ============================================
// ESTADO GLOBAL
// ============================================
var cartState = {
    items: [],
    subtotal: 0,
    discount: 0,
    total: 0,
    couponCode: null,
    paymentMethod: 'qr'
};

// ============================================
// INICIALIZAR
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    updateCartState();
    loadCouponFromSession();
    generateQRCode(); // Generar QR al cargar
});

// ============================================
// GENERAR QR DINÁMICO
// ============================================
function generateQRCode() {
    var qrContainer = document.getElementById('qrContainer');
    if (!qrContainer) return;

    var total = document.getElementById('totalDisplay');
    if (!total) return;

    var totalText = total.textContent.replace(/[^0-9.]/g, '');
    var totalAmount = parseFloat(totalText) || 0;

    var user = qrContainer.dataset.username || 'Invitado';
    var paymentData = {
        user: user,
        amount: totalAmount,
        timestamp: new Date().toISOString(),
        method: 'QR',
        type: 'Pago AcadEMI'
    };

    var paymentString = encodeURIComponent(JSON.stringify(paymentData));
    var qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${paymentString}&bgcolor=ffffff&color=0033a0&margin=10`;

    // Buscar o crear imagen QR
    var existingImg = qrContainer.querySelector('.qr-image');
    if (existingImg) {
        existingImg.src = qrUrl;
    } else {
        var img = document.createElement('img');
        img.className = 'qr-image';
        img.src = qrUrl;
        img.alt = 'QR para pago';

        var infoDiv = qrContainer.querySelector('.qr-info');
        qrContainer.insertBefore(img, infoDiv);
    }

    // Actualizar información del QR
    var qrInfo = qrContainer.querySelector('.qr-amount');
    if (!qrInfo) {
        var amountInfo = document.createElement('div');
        amountInfo.className = 'qr-amount';
        qrContainer.appendChild(amountInfo);
    }
    document.querySelector('.qr-amount').innerHTML = `
        <i class="fas fa-bolivian-sign"></i> ${totalAmount.toFixed(2)}
        <span><i class="fas fa-user"></i> ${user}</span>
    `;

    // Botón para escanear QR (simulado)
    var scanBtn = qrContainer.querySelector('.qr-scan-btn');
    if (!scanBtn) {
        var btn = document.createElement('button');
        btn.className = 'qr-scan-btn';
        btn.innerHTML = '<i class="fas fa-camera"></i> Escanear QR y pagar';
        btn.onclick = function() {
            // Simular escaneo y pago
            showToast('QR escaneado. Procesando pago...', 'info');
            setTimeout(function() {
                processCheckout();
            }, 1500);
        };
        qrContainer.appendChild(btn);
    }
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
    cartState.total = subtotal - cartState.discount;

    var subtotalDisplay = document.getElementById('subtotalDisplay');
    var totalDisplay = document.getElementById('totalDisplay');
    var cartBadge = document.getElementById('cartBadge');
    var discountRow = document.getElementById('discountRow');
    var discountDisplay = document.getElementById('discountDisplay');
    var checkoutBtn = document.getElementById('checkoutBtn');

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
        checkoutBtn.disabled = itemCount === 0;
    }

    // Regenerar QR cuando cambia el total
    if (itemCount > 0) {
        setTimeout(generateQRCode, 100);
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
        body: JSON.stringify({ code: code, subtotal: cartState.subtotal })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
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
            feedback.innerHTML = '<i class="fas fa-times-circle"></i> ' + data.message;
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
// SELECCIONAR MÉTODO DE PAGO
// ============================================
function selectPayment(method) {
    cartState.paymentMethod = method;

    var options = document.querySelectorAll('.payment-option');
    options.forEach(function(opt) {
        opt.classList.remove('active');
        if (opt.dataset.method === method) {
            opt.classList.add('active');
        }
    });

    var qrContainer = document.getElementById('qrContainer');
    var cardContainer = document.getElementById('cardContainer');

    if (method === 'qr') {
        if (qrContainer) {
            qrContainer.style.display = 'block';
            setTimeout(generateQRCode, 100);
        }
        if (cardContainer) cardContainer.style.display = 'none';
    } else {
        if (qrContainer) qrContainer.style.display = 'none';
        if (cardContainer) cardContainer.style.display = 'block';
    }
}

// ============================================
// PROCESAR COMPRA
// ============================================
function processCheckout() {
    var btn = document.getElementById('checkoutBtn');
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Procesando...';

    var fullName = document.getElementById('fullName');
    var email = document.getElementById('email');
    var phone = document.getElementById('phone');
    var address = document.getElementById('address');

    if (!fullName || !fullName.value.trim()) {
        showToast('Ingresa tu nombre completo', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
        return;
    }

    if (!email || !email.value.trim()) {
        showToast('Ingresa tu correo electrónico', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
        return;
    }

    if (cartState.paymentMethod === 'card') {
        var cardNumber = document.getElementById('cardNumber');
        var cardExpiry = document.getElementById('cardExpiry');
        var cardCvc = document.getElementById('cardCvc');

        if (cardNumber && cardNumber.value.replace(/\s/g, '').length < 16) {
            showToast('Número de tarjeta inválido', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
            return;
        }

        if (cardExpiry && cardExpiry.value.length < 5) {
            showToast('Fecha de expiración inválida', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
            return;
        }

        if (cardCvc && cardCvc.value.length < 3) {
            showToast('CVC inválido', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
            return;
        }
    }

    var payload = {
        full_name: fullName.value.trim(),
        email: email.value.trim(),
        phone: phone ? phone.value.trim() : '',
        address: address ? address.value.trim() : '',
        payment_method: cartState.paymentMethod,
        coupon_code: cartState.couponCode,
        card_number: document.getElementById('cardNumber') ? document.getElementById('cardNumber').value.replace(/\s/g, '') : null,
        card_expiry: document.getElementById('cardExpiry') ? document.getElementById('cardExpiry').value : null,
        card_cvc: document.getElementById('cardCvc') ? document.getElementById('cardCvc').value : null
    };

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
            showToast('¡Compra realizada con éxito! Disfruta tus cursos.', 'success');
            setTimeout(function() {
                window.location.href = '/my-courses/';
            }, 1500);
        } else {
            showToast(data.message || 'Error al procesar la compra', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        showToast(error.message || 'Error de conexión al servidor', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-lock"></i> Comprar ahora';
    });
}

// ============================================
// FORMATO DE TARJETA
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    var cardInput = document.getElementById('cardNumber');
    if (cardInput) {
        cardInput.addEventListener('input', function(e) {
            var value = e.target.value.replace(/\D/g, '');
            var formatted = '';
            for (var i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formatted += ' ';
                }
                formatted += value[i];
            }
            e.target.value = formatted;
        });
    }

    var expiryInput = document.getElementById('cardExpiry');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            var value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                e.target.value = value.substring(0, 2) + '/' + value.substring(2, 4);
            } else {
                e.target.value = value;
            }
        });
    }
});

// Exponer funciones globalmente (usadas por atributos onclick del HTML)
window.removeFromCart = removeFromCart;
window.applyCoupon = applyCoupon;
window.removeCoupon = removeCoupon;
window.selectPayment = selectPayment;
window.processCheckout = processCheckout;
window.generateQRCode = generateQRCode;
