// ============================================
// OBTENER CSRF TOKEN
// ============================================

function getCsrfToken() {
    // CSRF_COOKIE_HTTPONLY está en True en core/settings.py (a propósito,
    // para endurecer contra XSS), así que la cookie csrftoken NO es
    // legible desde JS. El valor real viene del input oculto que
    // partials/base.html renderiza con {% csrf_token %} (o del de
    // cualquier <form> visible en la página, como login/register que no
    // extienden base.html). Se deja la lectura de cookie como respaldo
    // por si algún día se desactiva ese endurecimiento.
    var input = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (input && input.value) {
        return input.value;
    }

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
