// ============================================
// MODO NOCHE / DÍA
// El tema real ya se aplica antes de este archivo
// (script inline en partials/base.html, para evitar
// el parpadeo del tema equivocado al cargar). Este
// archivo solo conecta el botón del navbar/menú
// lateral para cambiarlo y recordarlo.
// ============================================

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
        localStorage.setItem('academi-theme', theme);
    } catch (e) {
        // Almacenamiento no disponible (modo privado, etc.): el tema
        // igual se aplica para esta carga de página.
    }
    document.querySelectorAll('.theme-toggle-btn i').forEach(function(icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
    document.querySelectorAll('.theme-toggle-label').forEach(function(label) {
        label.textContent = theme === 'dark' ? 'Modo día' : 'Modo noche';
    });
}

function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', function() {
    var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    document.querySelectorAll('.theme-toggle-btn i').forEach(function(icon) {
        icon.className = current === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
    document.querySelectorAll('.theme-toggle-label').forEach(function(label) {
        label.textContent = current === 'dark' ? 'Modo día' : 'Modo noche';
    });

    document.querySelectorAll('.theme-toggle-btn').forEach(function(btn) {
        btn.addEventListener('click', toggleTheme);
    });
});

window.toggleTheme = toggleTheme;
