// ============================================
// PÁGINA COMPLETA DEL ASISTENTE (templates/academi/chatbot/chatbot.html)
// Usa chatbotSendMessage() de static/js/chatbot.js para la petición al
// backend; acá solo vive la interfaz de esta página (burbujas, typing).
// ============================================

var messagesContainer = document.getElementById('messagesContainer');
var chatEmpty = document.getElementById('chatEmpty');
var typingIndicator = document.getElementById('typingIndicator');
var chatInput = document.getElementById('chatInput');
var sendBtn = document.getElementById('sendBtn');
var isProcessing = false;

function addMessage(text, sender, time) {
    chatEmpty.style.display = 'none';

    var messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message ' + sender;

    var avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

    var bubble = document.createElement('div');
    bubble.className = 'bubble';

    var textSpan = document.createElement('span');
    textSpan.textContent = text;

    var timeSpan = document.createElement('span');
    timeSpan.className = 'time';
    timeSpan.textContent = time || new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

    bubble.appendChild(textSpan);
    bubble.appendChild(timeSpan);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);

    var container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    typingIndicator.style.display = 'block';
    var container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    typingIndicator.style.display = 'none';
}

function sendMessage() {
    if (isProcessing) return;
    var text = chatInput.value.trim();
    if (!text) return;

    isProcessing = true;
    sendBtn.disabled = true;
    chatInput.disabled = true;

    addMessage(text, 'user');
    chatInput.value = '';

    showTyping();

    chatbotSendMessage(text, function(response) {
        hideTyping();
        addMessage(response, 'bot');
        isProcessing = false;
        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }, function(errorMessage) {
        hideTyping();
        addMessage(errorMessage, 'bot');
        isProcessing = false;
        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    });
}

function sendQuickMessage(text) {
    chatInput.value = text;
    sendMessage();
}

document.addEventListener('DOMContentLoaded', function() {
    if (messagesContainer.children.length === 0) {
        chatEmpty.style.display = 'flex';
    }
    chatInput.focus();
});
