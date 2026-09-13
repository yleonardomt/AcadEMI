// ============================================
// VALIDACIÓN DE EMAIL
// ============================================

function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ============================================
// REGISTRO INTERACTIVO (templates/academi/auth/register.html)
// ============================================

document.addEventListener('DOMContentLoaded', function() {

    // ===== Mostrar campos según tipo de usuario =====
    var roleSelect = document.getElementById('id_role');
    var studentFields = document.getElementById('studentFields');
    var teacherFields = document.getElementById('teacherFields');

    function toggleRoleFields() {
        if (roleSelect.value === 'student') {
            studentFields.style.display = 'block';
            teacherFields.style.display = 'none';
            studentFields.querySelectorAll('input, select').forEach(function(el) {
                if (el.name && ['full_name', 'university', 'career'].includes(el.name)) {
                    el.setAttribute('required', 'required');
                }
            });
            teacherFields.querySelectorAll('input, select').forEach(function(el) {
                el.removeAttribute('required');
            });
        } else if (roleSelect.value === 'teacher') {
            studentFields.style.display = 'none';
            teacherFields.style.display = 'block';
            teacherFields.querySelectorAll('input, select').forEach(function(el) {
                if (el.name && ['teacher_full_name', 'specialty', 'experience_years'].includes(el.name)) {
                    el.setAttribute('required', 'required');
                }
            });
            studentFields.querySelectorAll('input, select').forEach(function(el) {
                el.removeAttribute('required');
            });
        } else {
            studentFields.style.display = 'none';
            teacherFields.style.display = 'none';
        }
    }

    if (roleSelect) {
        roleSelect.addEventListener('change', toggleRoleFields);
        toggleRoleFields();
    }

    // ===== Selector visual de rol (tarjetas Estudiante/Docente) =====
    var roleCards = document.querySelectorAll('#rolePicker .role-card');
    if (roleCards.length && roleSelect) {
        roleCards.forEach(function(card) {
            if (card.getAttribute('data-role') === roleSelect.value) {
                card.classList.add('selected');
            }
            card.addEventListener('click', function() {
                roleCards.forEach(function(c) { c.classList.remove('selected'); });
                card.classList.add('selected');
                roleSelect.value = card.getAttribute('data-role');
                roleSelect.dispatchEvent(new Event('change'));
            });
        });
    }

    // ===== Barra de fortaleza de contraseña =====
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
                color = '#00b894';
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

    // ===== Validación de email en tiempo real =====
    var emailInput = document.querySelector('#id_email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            var email = this.value;
            if (email && !validateEmail(email)) {
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
});
