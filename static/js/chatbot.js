// ============================================
// ASISTENTE VIRTUAL - LÓGICA COMPARTIDA
// Usada por el widget flotante (partials/chatbot_widget.html)
// y por la página completa (academi/chatbot/chatbot.html).
// La respuesta siempre viene del backend (/chatbot/send/),
// nunca se duplica lógica de respuestas en el cliente.
// ============================================

function chatbotSendMessage(message, onResponse, onError) {
    fetch('/chatbot/send/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'message=' + encodeURIComponent(message),
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            onResponse(data.response);
        } else {
            onError(data.message || 'No se pudo procesar tu mensaje.');
        }
    })
    .catch(function() {
        onError('Error de conexión con el asistente.');
    });
}

function chatbotBuildMessageEl(text, sender) {
    var wrap = document.createElement('div');
    wrap.className = 'chatbot-msg ' + sender;

    var avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

    var bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    return wrap;
}
