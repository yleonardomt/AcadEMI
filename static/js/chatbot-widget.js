// ============================================
// WIDGET FLOTANTE DEL ASISTENTE VIRTUAL
// Usa las funciones compartidas de static/js/chatbot.js
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    var fab = document.getElementById('chatbotFab');
    var panel = document.getElementById('chatbotPanel');
    if (!fab || !panel) return;

    var body = document.getElementById('chatbotWidgetBody');
    var input = document.getElementById('chatbotWidgetInput');
    var sendBtn = document.getElementById('chatbotWidgetSend');
    var isSending = false;

    function togglePanel() {
        var isOpen = panel.classList.toggle('open');
        fab.classList.toggle('open', isOpen);
        if (isOpen) {
            input.focus();
        }
    }

    function scrollToBottom() {
        body.scrollTop = body.scrollHeight;
    }

    function showTyping() {
        var typing = document.createElement('div');
        typing.className = 'chatbot-msg bot';
        typing.id = 'chatbotWidgetTyping';
        typing.innerHTML = '<div class="avatar"><i class="fas fa-robot"></i></div>' +
            '<div class="chatbot-typing"><span></span><span></span><span></span></div>';
        body.appendChild(typing);
        scrollToBottom();
    }

    function hideTyping() {
        var typing = document.getElementById('chatbotWidgetTyping');
        if (typing) typing.remove();
    }

    function send(message) {
        if (isSending || !message) return;
        isSending = true;

        body.appendChild(chatbotBuildMessageEl(message, 'user'));
        scrollToBottom();
        showTyping();

        chatbotSendMessage(message, function(response) {
            hideTyping();
            body.appendChild(chatbotBuildMessageEl(response, 'bot'));
            scrollToBottom();
            isSending = false;
        }, function(errorMessage) {
            hideTyping();
            body.appendChild(chatbotBuildMessageEl(errorMessage, 'bot'));
            scrollToBottom();
            isSending = false;
        });
    }

    fab.addEventListener('click', togglePanel);

    sendBtn.addEventListener('click', function() {
        var text = input.value.trim();
        input.value = '';
        send(text);
    });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            var text = input.value.trim();
            input.value = '';
            send(text);
        }
    });

    document.querySelectorAll('.chatbot-quick button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            send(btn.getAttribute('data-msg'));
        });
    });
});
