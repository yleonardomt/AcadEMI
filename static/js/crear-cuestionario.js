(function() {
    // ============================================
    // DATOS DE LA PÁGINA (ver data-* en #quizForm)
    // ============================================
    const quizForm = document.getElementById('quizForm');
    const esEdicion = quizForm.dataset.esEdicion === 'true';
    let preguntasIniciales = [];
    try {
        preguntasIniciales = JSON.parse(quizForm.dataset.preguntas || '[]');
    } catch (e) {
        preguntasIniciales = [];
    }

    // ============================================
    // MODAL
    // ============================================
    function showModal(title, message, type) {
        const modal = new bootstrap.Modal(document.getElementById('alertModal'));
        const icon = document.getElementById('alertIcon');
        const titleEl = document.getElementById('alertTitle');
        const msgEl = document.getElementById('alertMessage');

        icon.className = 'modal-icon';

        if (type === 'warning') {
            icon.classList.add('warning');
            icon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        } else if (type === 'error') {
            icon.classList.add('error');
            icon.innerHTML = '<i class="fas fa-times-circle"></i>';
        } else if (type === 'success') {
            icon.classList.add('success');
            icon.innerHTML = '<i class="fas fa-check-circle"></i>';
        } else {
            icon.innerHTML = '<i class="fas fa-info-circle"></i>';
        }

        titleEl.textContent = title;
        msgEl.textContent = message;
        modal.show();
    }

    // ============================================
    // VARIABLES
    // ============================================
    let questionCounter = 0;
    const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

    // ============================================
    // AGREGAR PREGUNTA
    // ============================================
    window.addQuestion = function() {
        questionCounter++;
        const container = document.getElementById('questionsContainer');

        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-item';
        questionDiv.id = 'question-' + questionCounter;

        let optionsHtml = '';
        for (let i = 0; i < 4; i++) {
            const letter = letters[i];
            optionsHtml += `
                <div class="option-item">
                    <span class="option-letter">${letter}</span>
                    <input type="text"
                           name="question_${questionCounter}_option_${i}"
                           placeholder="Opción ${letter}"
                           required>
                    <input type="checkbox"
                           name="question_${questionCounter}_correct_${i}"
                           class="option-correct">
                    <span class="correct-label">Correcta</span>
                    <button type="button" class="option-remove" onclick="removeOption(${questionCounter}, ${i})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }

        questionDiv.innerHTML = `
            <div class="question-number">Pregunta ${questionCounter}</div>
            <button type="button" class="question-remove" onclick="removeQuestion(${questionCounter})" title="Eliminar pregunta">
                <i class="fas fa-times"></i>
            </button>

            <div class="mb-2">
                <input type="text"
                       name="question_${questionCounter}_text"
                       class="form-control question-text-input"
                       placeholder="Escribe la pregunta..."
                       required>
            </div>

            <div class="mb-2">
                <label class="fw-semibold" style="font-size: 13px; color: var(--gray-dark);">
                    <i class="fas fa-check-square"></i> Opciones (marca las correctas)
                </label>
                <div id="options-${questionCounter}">
                    ${optionsHtml}
                </div>

                <button type="button" class="btn-add-option" onclick="addOption(${questionCounter})">
                    <i class="fas fa-plus-circle"></i> Agregar opción
                </button>
            </div>

            <input type="hidden" name="question_${questionCounter}_options_count" value="4" class="options-count">
        `;

        container.appendChild(questionDiv);
        updateQuestionCount();
    };

    // ============================================
    // CARGAR PREGUNTAS EXISTENTES
    // ============================================
    function cargarPreguntas(preguntas) {
        if (!preguntas || preguntas.length === 0) {
            return;
        }

        const container = document.getElementById('questionsContainer');
        container.innerHTML = '';
        questionCounter = 0;

        preguntas.forEach(function(pregunta) {
            questionCounter++;
            const num = questionCounter;
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question-item';
            questionDiv.id = 'question-' + num;

            let optionsHtml = '';
            pregunta.options.forEach(function(opt, optIndex) {
                const letter = letters[optIndex] || '?';
                const isChecked = opt.is_correct ? 'checked' : '';
                optionsHtml += `
                    <div class="option-item">
                        <span class="option-letter">${letter}</span>
                        <input type="text"
                               name="question_${num}_option_${optIndex}"
                               placeholder="Opción ${letter}"
                               required
                               value="${opt.text.replace(/"/g, '&quot;')}">
                        <input type="checkbox"
                               name="question_${num}_correct_${optIndex}"
                               class="option-correct"
                               ${isChecked}>
                        <span class="correct-label">Correcta</span>
                        <button type="button" class="option-remove" onclick="removeOption(${num}, ${optIndex})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
            });

            questionDiv.innerHTML = `
                <div class="question-number">Pregunta ${num}</div>
                <button type="button" class="question-remove" onclick="removeQuestion(${num})" title="Eliminar pregunta">
                    <i class="fas fa-times"></i>
                </button>

                <div class="mb-2">
                    <input type="text"
                           name="question_${num}_text"
                           class="form-control question-text-input"
                           placeholder="Escribe la pregunta..."
                           required
                           value="${pregunta.text.replace(/"/g, '&quot;')}">
                </div>

                <div class="mb-2">
                    <label class="fw-semibold" style="font-size: 13px; color: var(--gray-dark);">
                        <i class="fas fa-check-square"></i> Opciones (marca las correctas)
                    </label>
                    <div id="options-${num}">
                        ${optionsHtml}
                    </div>

                    <button type="button" class="btn-add-option" onclick="addOption(${num})">
                        <i class="fas fa-plus-circle"></i> Agregar opción
                    </button>
                </div>

                <input type="hidden" name="question_${num}_options_count" value="${pregunta.options.length}" class="options-count">
            `;

            container.appendChild(questionDiv);
        });

        updateQuestionCount();
    }

    // ============================================
    // ELIMINAR PREGUNTA
    // ============================================
    window.removeQuestion = function(questionId) {
        const element = document.getElementById('question-' + questionId);
        if (element) {
            const totalQuestions = document.querySelectorAll('.question-item').length;
            if (totalQuestions <= 1) {
                showModal('No se puede eliminar', 'Debe haber al menos 1 pregunta.', 'warning');
                return;
            }
            element.remove();
            updateQuestionCount();
            renumberQuestions();
        }
    };

    // ============================================
    // RENUMERAR PREGUNTAS
    // ============================================
    function renumberQuestions() {
        const questions = document.querySelectorAll('.question-item');
        questions.forEach((q, index) => {
            const num = index + 1;
            const numberDiv = q.querySelector('.question-number');
            if (numberDiv) {
                numberDiv.textContent = 'Pregunta ' + num;
            }
            q.id = 'question-' + num;

            const inputs = q.querySelectorAll('input');
            inputs.forEach(input => {
                const name = input.name;
                if (name) {
                    const newName = name.replace(/question_\d+/, 'question_' + num);
                    input.name = newName;
                }
            });

            const removeBtn = q.querySelector('.question-remove');
            if (removeBtn) {
                removeBtn.setAttribute('onclick', 'removeQuestion(' + num + ')');
            }

            const optionContainer = q.querySelector('[id^="options-"]');
            if (optionContainer) {
                optionContainer.id = 'options-' + num;

                const addOptionBtn = q.querySelector('.btn-add-option');
                if (addOptionBtn) {
                    addOptionBtn.setAttribute('onclick', 'addOption(' + num + ')');
                }

                const options = optionContainer.querySelectorAll('.option-item');
                options.forEach((opt, optIdx) => {
                    const removeOptBtn = opt.querySelector('.option-remove');
                    if (removeOptBtn) {
                        removeOptBtn.setAttribute('onclick', 'removeOption(' + num + ', ' + optIdx + ')');
                    }
                });
            }
        });
    }

    // ============================================
    // AGREGAR OPCIÓN
    // ============================================
    window.addOption = function(questionId) {
        const optionsContainer = document.getElementById('options-' + questionId);
        if (!optionsContainer) return;

        const currentOptions = optionsContainer.querySelectorAll('.option-item');
        const optionCount = currentOptions.length;

        if (optionCount >= 8) {
            showModal('Límite alcanzado', 'Máximo 8 opciones por pregunta.', 'warning');
            return;
        }

        const letter = letters[optionCount] || '?';
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option-item';
        optionDiv.innerHTML = `
            <span class="option-letter">${letter}</span>
            <input type="text"
                   name="question_${questionId}_option_${optionCount}"
                   placeholder="Opción ${letter}"
                   required>
            <input type="checkbox"
                   name="question_${questionId}_correct_${optionCount}"
                   class="option-correct">
            <span class="correct-label">Correcta</span>
            <button type="button" class="option-remove" onclick="removeOption(${questionId}, ${optionCount})">
                <i class="fas fa-times"></i>
            </button>
        `;
        optionsContainer.appendChild(optionDiv);

        const countInput = document.querySelector(`#question-${questionId} .options-count`);
        if (countInput) {
            countInput.value = optionCount + 1;
        }
    };

    // ============================================
    // ELIMINAR OPCIÓN
    // ============================================
    window.removeOption = function(questionId, optionIndex) {
        const optionsContainer = document.getElementById('options-' + questionId);
        if (!optionsContainer) return;

        const options = optionsContainer.querySelectorAll('.option-item');

        if (options.length <= 2) {
            showModal('No se puede eliminar', 'Debe haber al menos 2 opciones.', 'warning');
            return;
        }

        const optionToRemove = options[optionIndex];
        if (optionToRemove) {
            optionToRemove.remove();
            const countInput = document.querySelector(`#question-${questionId} .options-count`);
            if (countInput) {
                countInput.value = optionsContainer.querySelectorAll('.option-item').length;
            }
            const remainingOptions = optionsContainer.querySelectorAll('.option-item');
            remainingOptions.forEach((opt, idx) => {
                const letterSpan = opt.querySelector('.option-letter');
                if (letterSpan) {
                    letterSpan.textContent = letters[idx] || '?';
                }
            });
        }
    };

    // ============================================
    // ACTUALIZAR CONTADOR
    // ============================================
    function updateQuestionCount() {
        const count = document.querySelectorAll('.question-item').length;
        document.getElementById('questionCount').textContent = count;
    }

    // ============================================
    // INICIALIZAR
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        if (preguntasIniciales && preguntasIniciales.length > 0) {
            cargarPreguntas(preguntasIniciales);
        } else {
            addQuestion();
            addQuestion();
        }

        document.getElementById('addQuestionBtn').addEventListener('click', function() {
            addQuestion();
        });

        // ============================================
        // VALIDAR Y ENVIAR FORMULARIO
        // ============================================
        const form = document.getElementById('quizForm');
        const submitBtn = document.getElementById('submitBtn');
        const submitLabel = esEdicion ? 'Actualizando...' : 'Creando...';

        form.addEventListener('submit', function(e) {
            let valid = true;
            const questions = document.querySelectorAll('.question-item');
            let errorMessages = [];

            if (questions.length === 0) {
                showModal('Error', 'Debes agregar al menos una pregunta.', 'error');
                e.preventDefault();
                return false;
            }

            questions.forEach((q, index) => {
                const qText = q.querySelector('input[name*="_text"]');
                if (qText && !qText.value.trim()) {
                    errorMessages.push('La pregunta ' + (index + 1) + ' no tiene texto.');
                    qText.focus();
                    valid = false;
                }

                const options = q.querySelectorAll('.option-item input[type="text"]');
                const corrects = q.querySelectorAll('.option-correct:checked');

                options.forEach(opt => {
                    if (!opt.value.trim()) {
                        errorMessages.push('La pregunta ' + (index + 1) + ' tiene una opción vacía.');
                        opt.focus();
                        valid = false;
                    }
                });

                if (corrects.length === 0) {
                    errorMessages.push('La pregunta ' + (index + 1) + ' no tiene ninguna opción correcta marcada.');
                    valid = false;
                }
            });

            if (!valid) {
                e.preventDefault();
                showModal('Error en el formulario', errorMessages.join('\n'), 'error');
                return false;
            }

            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + submitLabel;
            submitBtn.disabled = true;
            return true;
        });
    });

})();
