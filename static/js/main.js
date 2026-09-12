// ============================================
// MENSAJES DE NOTIFICACIÓN (SIN ALERT)
// ============================================

function showMessage(message, type) {
    document.querySelectorAll('.message').forEach(function(msg) {
        msg.remove();
    });
    
    var messageDiv = document.createElement('div');
    messageDiv.className = 'message message-' + type;
    
    var icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };
    
    messageDiv.innerHTML = 
        '<i class="fas ' + icons[type] + '"></i>' +
        '<span>' + message + '</span>' +
        '<button class="message-close">' +
            '<i class="fas fa-times"></i>' +
        '</button>';
    
    document.body.appendChild(messageDiv);
    
    messageDiv.querySelector('.message-close').addEventListener('click', function() {
        messageDiv.style.opacity = '0';
        messageDiv.style.transition = 'opacity 0.3s ease';
        setTimeout(function() {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 300);
    });
    
    setTimeout(function() {
        if (messageDiv.parentElement) {
            messageDiv.style.opacity = '0';
            messageDiv.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                if (messageDiv.parentElement) {
                    messageDiv.remove();
                }
            }, 500);
        }
    }, 4000);
}

// ============================================
// VALIDACIÓN DE EMAIL
// ============================================

function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ============================================
// TOAST - NOTIFICACIONES FLOTANTES
// ============================================

function showToast(message, type) {
    type = type || 'info';
    
    // Buscar contenedor existente
    var container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    var toast = document.createElement('div');
    toast.className = 'toast-custom ' + type;

    var iconMap = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    var icon = iconMap[type] || iconMap.info;

    toast.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove();">
            <i class="fas fa-times"></i>
        </button>
    `;
    container.appendChild(toast);

    setTimeout(function() {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(function() {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }
    }, 5000);
}

// ============================================
// FUNCIONES GLOBALES PARA MODALES SIN FONDO NEGRO
// ============================================

// Función para abrir cualquier modal sin fondo negro
function openModalWithoutBackdrop(modalId) {
    // Limpiar backdrops viejos
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

// Función para cerrar cualquier modal
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

// ============================================
// OBTENER CSRF TOKEN
// ============================================

function getCsrfToken() {
    var cookieValue = null;
    var name = 'csrftoken';
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ============================================
// EVENTOS AL CARGAR LA PÁGINA
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Botones de compra =====
    var btnComprar = document.querySelectorAll('.btn-comprar');
    for (var i = 0; i < btnComprar.length; i++) {
        btnComprar[i].addEventListener('click', function(e) {
            e.preventDefault();
            var curso = this.getAttribute('data-curso') || 'Curso';
            showToast('Curso "' + curso + '" agregado al carrito', 'success');
        });
    }
    
    // ===== Botón "Ver todos los cursos" =====
    var btnVerTodos = document.getElementById('btnVerTodos');
    if (btnVerTodos) {
        btnVerTodos.addEventListener('click', function(e) {
            e.preventDefault();
            showToast('Cargando todos los cursos...', 'info');
        });
    }
    
    // ===== Suscripción al newsletter =====
    var btnSubscribe = document.getElementById('btnSubscribe');
    var emailInput = document.getElementById('emailSubscribe');
    
    function handleSubscribe() {
        var email = emailInput.value.trim();
        
        if (!email) {
            showToast('Por favor, ingresa tu email', 'warning');
            return;
        }
        
        if (!validateEmail(email)) {
            showToast('Por favor, ingresa un email válido', 'error');
            return;
        }
        
        showToast('Te has suscrito correctamente', 'success');
        emailInput.value = '';
    }
    
    if (btnSubscribe) {
        btnSubscribe.addEventListener('click', handleSubscribe);
    }
    
    if (emailInput) {
        emailInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSubscribe();
            }
        });
    }
    
    // ===== Scroll suave para enlaces internos =====
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            var target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// ============================================
// REGISTRO INTERACTIVO
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Mostrar campos según rol =====
    var roleSelect = document.getElementById('id_role');
    var stepStudent = document.getElementById('stepStudent');
    var stepTeacher = document.getElementById('stepTeacher');
    
    function toggleRoleFields() {
        var role = roleSelect.value;
        
        if (role === 'student') {
            stepStudent.style.display = 'block';
            stepTeacher.style.display = 'none';
            // Hacer campos de estudiante requeridos
            document.querySelectorAll('#stepStudent input, #stepStudent select').forEach(function(input) {
                if (input.name && !input.name.includes('interests')) {
                    input.setAttribute('required', 'required');
                }
            });
            document.querySelectorAll('#stepTeacher input, #stepTeacher select').forEach(function(input) {
                input.removeAttribute('required');
            });
        } else if (role === 'teacher') {
            stepStudent.style.display = 'none';
            stepTeacher.style.display = 'block';
            // Hacer campos de docente requeridos
            document.querySelectorAll('#stepTeacher input, #stepTeacher select').forEach(function(input) {
                if (input.name && !input.name.includes('teaching_materials') && !input.name.includes('teaching_level')) {
                    input.setAttribute('required', 'required');
                }
            });
            document.querySelectorAll('#stepStudent input, #stepStudent select').forEach(function(input) {
                input.removeAttribute('required');
            });
        } else {
            stepStudent.style.display = 'none';
            stepTeacher.style.display = 'none';
        }
    }
    
    if (roleSelect) {
        roleSelect.addEventListener('change', toggleRoleFields);
        toggleRoleFields();
    }
    
    // ===== Validación de contraseña en tiempo real =====
    var passwordInput = document.querySelector('#id_password1');
    var strengthBar = document.querySelector('.strength-bar');
    var strengthText = document.querySelector('.strength-text');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            var password = this.value;
            var strength = 0;
            
            if (password.length >= 8) strength++;
            if (password.match(/[A-Z]/)) strength++;
            if (password.match(/[a-z]/)) strength++;
            if (password.match(/[0-9]/)) strength++;
            if (password.match(/[!@#$%^&*(),.?":{}|<>]/)) strength++;
            
            var width = (strength / 5) * 100;
            var color = '#dc3545';
            var text = 'Débil';
            
            if (strength >= 4) {
                color = '#28a745';
                text = 'Fuerte';
            } else if (strength >= 3) {
                color = '#ffc107';
                text = 'Media';
            } else if (strength >= 2) {
                color = '#fd7e14';
                text = 'Regular';
            }
            
            if (strengthBar) {
                strengthBar.style.width = width + '%';
                strengthBar.style.background = color;
            }
            if (strengthText) {
                strengthText.textContent = text + ' - ' + Math.round(width) + '%';
                strengthText.style.color = color;
            }
        });
    }
    
    // ===== Validación de email en tiempo real =====
    var emailInput = document.querySelector('#id_email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            var email = this.value;
            var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (email && !re.test(email)) {
                this.style.borderColor = '#dc3545';
                var errorDiv = this.parentElement.querySelector('.text-danger') || document.createElement('div');
                errorDiv.className = 'text-danger small mt-1';
                errorDiv.textContent = 'Ingresa un email válido';
                if (!this.parentElement.querySelector('.text-danger')) {
                    this.parentElement.appendChild(errorDiv);
                }
            } else {
                this.style.borderColor = '';
                var errorDiv = this.parentElement.querySelector('.text-danger');
                if (errorDiv) errorDiv.remove();
            }
        });
    }
    
    // ===== Confirmación de contraseña =====
    var password2Input = document.querySelector('#id_password2');
    if (password2Input && passwordInput) {
        password2Input.addEventListener('input', function() {
            if (this.value && this.value !== passwordInput.value) {
                this.style.borderColor = '#dc3545';
                var errorDiv = this.parentElement.querySelector('.text-danger') || document.createElement('div');
                errorDiv.className = 'text-danger small mt-1';
                errorDiv.textContent = 'Las contraseñas no coinciden';
                if (!this.parentElement.querySelector('.text-danger')) {
                    this.parentElement.appendChild(errorDiv);
                }
            } else {
                this.style.borderColor = '';
                var errorDiv = this.parentElement.querySelector('.text-danger');
                if (errorDiv) errorDiv.remove();
            }
        });
    }
    
    // Exponer funciones globalmente
    window.showToast = showToast;
    window.openModalWithoutBackdrop = openModalWithoutBackdrop;
    window.closeModalWithoutBackdrop = closeModalWithoutBackdrop;
    window.getCsrfToken = getCsrfToken;
});

// ============================================
// CERRAR MODALES CON ESC Y CLICK FUERA
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Cerrar con ESC - funciona globalmente
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Cerrar cualquier modal abierto
            var openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                var modalId = modal.id;
                if (modalId) {
                    closeModalWithoutBackdrop(modalId);
                }
            });
        }
    });
});

// ============================================
// INICIALIZAR TOOLTIPS DE BOOTSTRAP
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});