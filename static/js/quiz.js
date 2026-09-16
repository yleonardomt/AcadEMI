// ============================================
// MODAL
// ============================================
function showModal(icon, title, message) {
    document.getElementById('modalIcon').innerHTML = icon;
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

// ============================================
// DATOS DE LA PÁGINA (ver data-* en #quizForm)
// ============================================
var quizForm = document.getElementById('quizForm');
var lessonId = quizForm ? parseInt(quizForm.dataset.lessonId, 10) : null;
var nextLessonUrl = quizForm ? quizForm.dataset.nextLessonUrl : '';
var courseUrl = quizForm ? quizForm.dataset.courseUrl : '';

// ============================================
// TEMPORIZADOR
// ============================================
var timeLimit = (quizForm ? parseInt(quizForm.dataset.timeLimit, 10) : 0) * 60;
var timerDisplay = document.getElementById('timerDisplay');
var timerContainer = document.getElementById('timerContainer');
var timer = null;
var timeExceeded = false;

function startTimer() {
    timer = setInterval(function() {
        var minutes = Math.floor(timeLimit / 60);
        var seconds = timeLimit % 60;
        timerDisplay.textContent = minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
        timeLimit--;

        if (timeLimit <= 60 && timeLimit > 0) {
            timerContainer.classList.add('warning');
        }

        if (timeLimit < 0) {
            clearInterval(timer);
            timeExceeded = true;
            timerDisplay.textContent = '00:00';
            timerContainer.classList.add('warning');
            showModal(
                '<i class="fas fa-clock" style="color: var(--danger); font-size: 48px;"></i>',
                'Tiempo agotado',
                'Se acabó el tiempo. El cuestionario se enviará automáticamente.'
            );
            setTimeout(function() {
                closeModal();
                submitQuiz();
            }, 2000);
        }
    }, 1000);
}

// ============================================
// BLOQUEAR COPIA Y PEGA
// ============================================
document.addEventListener('copy', function(e) {
    e.preventDefault();
    showToast('Copiar no esta permitido durante el cuestionario', 'warning');
});

document.addEventListener('paste', function(e) {
    e.preventDefault();
    showToast('Pegar no esta permitido durante el cuestionario', 'warning');
});

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    showToast('Clic derecho no permitido', 'warning');
});

// ============================================
// REPORTAR INCIDENTE AL SERVIDOR (RF-53)
// ============================================
function reportIncident(type, detail, count) {
    fetch('/quiz/alert/tab-switch/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            lesson_id: lessonId,
            type: type,
            detail: detail,
            count: count || 0
        })
    }).then(function(response) { return response.json(); })
      .then(function(data) {
          if (data.kicked) {
              clearInterval(timer);
              document.getElementById('submitBtn').disabled = true;
              showModal(
                  '<i class="fas fa-ban" style="color: var(--danger); font-size: 48px;"></i>',
                  'Cuestionario bloqueado',
                  'Se detectaron demasiadas irregularidades de seguridad. Este intento queda anulado y serás redirigido a la siguiente lección.'
              );
              setTimeout(function() {
                  window.location.href = nextLessonUrl || courseUrl || '/';
              }, 3000);
          }
      })
      .catch(function() {});
}

// ============================================
// BLOQUEAR TECLAS
// ============================================
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey && ['c', 'v', 'x', 'u'].includes(e.key.toLowerCase())) || e.key === 'F12') {
        e.preventDefault();
        showToast('Accion no permitida', 'warning');
        if (e.key === 'F12') {
            reportIncident('other', 'Intento de abrir herramientas de desarrollador (F12)');
        }
        return false;
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'I') {
        e.preventDefault();
        showToast('Inspeccionar no permitido', 'warning');
        reportIncident('other', 'Intento de abrir herramientas de desarrollador (Ctrl+Shift+I)');
        return false;
    }
    if (e.key === 'F11') {
        e.preventDefault();
        showToast('Pantalla completa no permitida', 'warning');
        return false;
    }
    if (e.key === 'PrintScreen') {
        showToast('Las capturas de pantalla quedan registradas', 'warning');
        reportIncident('other', 'Intento de captura de pantalla (Impr Pant)');
    }
});

// ============================================
// DETECTAR CAMBIO DE PESTAÑA / VENTANA
// visibilitychange cubre el cambio de pestaña; blur/focus cubre además
// cambiar de ventana (otra app) sin cambiar de pestaña, que
// visibilitychange no siempre dispara igual en todos los navegadores.
// Se usa una ventana de "enfriamiento" para no contar dos veces el
// mismo cambio cuando ambos eventos disparan juntos.
// ============================================
var tabSwitchCount = 0;
var lastSwitchReportedAt = 0;
var SWITCH_DEDUP_WINDOW_MS = 800;

function reportWindowSwitch(reason) {
    var now = Date.now();
    if (now - lastSwitchReportedAt < SWITCH_DEDUP_WINDOW_MS) {
        return;
    }
    lastSwitchReportedAt = now;
    tabSwitchCount++;
    showToast('Cambio de pestaña o ventana detectado', 'warning');
    reportIncident('tab_switch', reason, tabSwitchCount);
}

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        reportWindowSwitch('Cambio de pestaña detectado (visibilitychange)');
    }
});

window.addEventListener('blur', function() {
    reportWindowSwitch('El estudiante salió de la ventana del examen (blur)');
});

// ============================================
// ENVIAR CUESTIONARIO
// ============================================
function submitQuiz() {
    var answers = {};
    var totalQuestions = 0;
    var answeredQuestions = 0;

    // Recopilar respuestas
    document.querySelectorAll('.question-card').forEach(function(card) {
        totalQuestions++;
        var radio = card.querySelector('input[type="radio"]:checked');
        if (radio) {
            var qId = radio.name.split('_')[1];
            answers['q_' + qId] = radio.value;
            answeredQuestions++;
        }
    });

    // Verificar si hay respuestas
    if (Object.keys(answers).length === 0) {
        showToast('No has seleccionado ninguna respuesta', 'warning');
        return;
    }

    // Verificar si todas las preguntas están respondidas
    if (answeredQuestions < totalQuestions) {
        showConfirm(
            'Faltan ' + (totalQuestions - answeredQuestions) + ' preguntas por responder. ¿Deseas enviar de todos modos?',
            function () { doSubmitQuiz(answers); },
            { buttonLabel: '<i class="fas fa-paper-plane"></i> Enviar de todos modos' }
        );
        return;
    }

    doSubmitQuiz(answers);
}

function doSubmitQuiz(answers) {
    // Obtener el token del campo oculto
    var token = document.getElementById('quizToken').value;

    // Deshabilitar botón
    var btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

    // Enviar con fetch
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            token: token,
            answers: answers
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            // Redirigir al resultado
            window.location.href = '/quiz/result/' + data.result_id + '/';
        } else {
            showToast(data.error || 'Error al enviar el cuestionario', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check"></i> Enviar respuestas';
        }
    })
    .catch(function() {
        showToast('Error de conexión al servidor', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Enviar respuestas';
    });
}

// ============================================
// INICIALIZAR
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    startTimer();
});
