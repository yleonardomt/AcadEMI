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
// EVENTOS AL CARGAR LA PÁGINA
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Botones de compra =====
    var btnComprar = document.querySelectorAll('.btn-comprar');
    for (var i = 0; i < btnComprar.length; i++) {
        btnComprar[i].addEventListener('click', function(e) {
            e.preventDefault();
            var curso = this.getAttribute('data-curso') || 'Curso';
            showMessage('Curso "' + curso + '" agregado al carrito', 'success');
        });
    }
    
    // ===== Botón "Ver todos los cursos" =====
    var btnVerTodos = document.getElementById('btnVerTodos');
    if (btnVerTodos) {
        btnVerTodos.addEventListener('click', function(e) {
            e.preventDefault();
            showMessage('Cargando todos los cursos...', 'info');
        });
    }
    
    // ===== Suscripción al newsletter =====
    var btnSubscribe = document.getElementById('btnSubscribe');
    var emailInput = document.getElementById('emailSubscribe');
    
    function handleSubscribe() {
        var email = emailInput.value.trim();
        
        if (!email) {
            showMessage('Por favor, ingresa tu email', 'warning');
            return;
        }
        
        if (!validateEmail(email)) {
            showMessage('Por favor, ingresa un email válido', 'error');
            return;
        }
        
        showMessage('Te has suscrito correctamente', 'success');
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
        toggleRoleFields(); // Ejecutar al cargar
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
    
    // ===== Mensajes de notificación (sin alert) =====
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
    
    // Exponer funciones globalmente
    window.showMessage = showMessage;
    
    // ===== Botones de compra =====
    document.querySelectorAll('.btn-comprar').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var curso = this.getAttribute('data-curso') || 'Curso';
            showMessage('Curso "' + curso + '" agregado al carrito', 'success');
        });
    });
    
    // ===== Suscripción =====
    var btnSubscribe = document.getElementById('btnSubscribe');
    var emailInputSubscribe = document.getElementById('emailSubscribe');
    
    function handleSubscribe() {
        var email = emailInputSubscribe.value.trim();
        var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!email) {
            showMessage('Por favor, ingresa tu email', 'warning');
            return;
        }
        
        if (!re.test(email)) {
            showMessage('Por favor, ingresa un email válido', 'error');
            return;
        }
        
        showMessage('Te has suscrito correctamente', 'success');
        emailInputSubscribe.value = '';
    }
    
    if (btnSubscribe) {
        btnSubscribe.addEventListener('click', handleSubscribe);
    }
    
    if (emailInputSubscribe) {
        emailInputSubscribe.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSubscribe();
            }
        });
    }
    
    // ===== Scroll suave =====
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