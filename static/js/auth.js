(function () {
    'use strict';
    document.body.classList.add('js-auth');

    document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
        var input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;
        button.addEventListener('click', function () {
            var showing = input.type === 'password';
            input.type = showing ? 'text' : 'password';
            button.setAttribute('aria-pressed', String(showing));
            button.setAttribute('aria-label', showing ? 'Ocultar contraseña' : 'Mostrar contraseña');
            button.querySelector('i').className = showing ? 'fas fa-eye-slash' : 'fas fa-eye';
            input.focus();
        });
    });

    var role = document.getElementById('id_role');
    var student = document.getElementById('studentFields');
    var teacher = document.getElementById('teacherFields');
    var cards = document.querySelectorAll('.role-card');
    function syncRole() {
        if (!role) return;
        var isTeacher = role.value === 'teacher';
        if (student && teacher) {
            student.hidden = isTeacher;
            teacher.hidden = !isTeacher;
            ['id_full_name'].forEach(function (id) { var el = document.getElementById(id); if (el) el.required = !isTeacher; });
            ['id_teacher_full_name', 'id_specialty'].forEach(function (id) { var el = document.getElementById(id); if (el) el.required = isTeacher; });
        }
        cards.forEach(function (card) {
            var selected = card.dataset.role === role.value;
            card.classList.toggle('selected', selected);
            card.setAttribute('aria-pressed', String(selected));
        });
    }
    if (role) {
        role.addEventListener('change', syncRole);
        cards.forEach(function (card) { card.addEventListener('click', function () { role.value = card.dataset.role; syncRole(); }); });
        syncRole();
    }

    var password = document.getElementById('id_password1');
    var confirmation = document.getElementById('id_password2');
    var match = document.getElementById('password-match');
    var rules = {
        length: function (v) { return v.length >= 8; },
        upper: function (v) { return /[A-Z]/.test(v); },
        lower: function (v) { return /[a-z]/.test(v); },
        digit: function (v) { return /[0-9]/.test(v); },
        symbol: function (v) { return /[!@#$%^&*(),.?":{}|<>]/.test(v); }
    };
    function checkPasswords() {
        if (!password) return;
        var passed = 0;
        Object.keys(rules).forEach(function (key) {
            var valid = rules[key](password.value);
            var item = document.querySelector('[data-rule="' + key + '"]');
            if (item) item.classList.toggle('valid', valid);
            if (valid) passed++;
        });
        var bar = document.querySelector('.strength-bar');
        if (bar) {
            bar.style.width = (passed * 20) + '%';
            bar.classList.toggle('strength-medium', passed >= 3 && passed < 5);
            bar.classList.toggle('strength-strong', passed === 5);
        }
        if (confirmation && match) {
            match.classList.remove('is-valid', 'is-error');
            if (!confirmation.value) { match.textContent = ''; }
            else if (confirmation.value === password.value) { match.textContent = 'Las contraseñas coinciden'; match.classList.add('is-valid'); }
            else { match.textContent = 'Las contraseñas no coinciden'; match.classList.add('is-error'); }
        }
    }
    if (password) password.addEventListener('input', checkPasswords);
    if (confirmation) confirmation.addEventListener('input', checkPasswords);
    checkPasswords();
})();
