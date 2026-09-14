// ============================================
// CREAR LECCIÓN (templates/academi/courses/crear_leccion.html)
// Sin IIFE a propósito: el template deja un <script> chico al final
// del body (bloque extra_js, después de este archivo) que restaura
// los valores del formulario si Django los devuelve por un error de
// validación — ese bloque necesita acceder a typeBtns/typeHidden/
// showGroupsByType de acá, por eso quedan en el scope global de la
// página en vez de encerrados en una función autoejecutable.
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // REGISTRAR PLUGINS DE FILEPOND E INICIALIZAR
    // ============================================
    FilePond.registerPlugin(FilePondPluginImagePreview);

    const videoFileInput = document.getElementById('videoFile');
    const documentFileInput = document.getElementById('documentFile');

    window.videoPond = FilePond.create(videoFileInput, {
        allowMultiple: false,
        maxFileSize: '500MB',
        labelIdle: `
            <i class="fas fa-cloud-upload-alt" style="font-size: 32px; color: var(--primary);"></i>
            <span style="font-weight: 500;">Arrastra o selecciona un video</span>
            <span style="font-size: 12px; color: var(--gray);">MP4, AVI, MOV, WMV, MKV</span>
        `,
        labelFileLoading: 'Cargando...',
        labelFileProcessing: 'Procesando...',
        labelTapToCancel: 'toca para cancelar',
        labelTapToRetry: 'toca para reintentar',
        labelTapToUndo: 'toca para deshacer',
        labelButtonRemoveItem: 'Eliminar',
        labelButtonAbortItemLoad: 'Cancelar',
        labelButtonRetryItemLoad: 'Reintentar',
    });

    window.documentPond = FilePond.create(documentFileInput, {
        allowMultiple: false,
        maxFileSize: '50MB',
        acceptedFileTypes: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/plain', 'application/zip'],
        labelIdle: `
            <i class="fas fa-file-upload" style="font-size: 32px; color: var(--primary);"></i>
            <span style="font-weight: 500;">Arrastra o selecciona un documento</span>
            <span style="font-size: 12px; color: var(--gray);">PDF, Word, PowerPoint, Excel, ZIP</span>
        `,
        labelFileLoading: 'Cargando...',
        labelFileProcessing: 'Procesando...',
        labelTapToCancel: 'toca para cancelar',
        labelTapToRetry: 'toca para reintentar',
        labelTapToUndo: 'toca para deshacer',
        labelButtonRemoveItem: 'Eliminar',
        labelButtonAbortItemLoad: 'Cancelar',
        labelButtonRetryItemLoad: 'Reintentar',
    });

    // ============================================
    // SELECTOR DE TIPO - DINÁMICO
    // ============================================
    window.typeBtns = document.querySelectorAll('.type-btn');
    window.typeHidden = document.getElementById('lessonType');
    const groups = {
        videoUrl: document.getElementById('videoUrlGroup'),
        videoFile: document.getElementById('videoFileGroup'),
        document: document.getElementById('documentGroup'),
        quiz: document.getElementById('quizGroup'),
        assignment: document.getElementById('assignmentGroup'),
    };

    function hideAllGroups() {
        Object.values(groups).forEach(g => g.classList.remove('active'));
    }

    window.showGroupsByType = function(type) {
        hideAllGroups();
        if (type === 'video') {
            groups.videoUrl.classList.add('active');
            groups.videoFile.classList.add('active');
        } else if (type === 'document') {
            groups.document.classList.add('active');
        } else if (type === 'quiz') {
            groups.quiz.classList.add('active');
        } else if (type === 'assignment') {
            groups.assignment.classList.add('active');
        }
        // text no muestra grupos adicionales
    };

    typeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.dataset.type;
            typeBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            typeHidden.value = type;
            showGroupsByType(type);
        });
    });

    const defaultType = 'text';
    typeHidden.value = defaultType;
    showGroupsByType(defaultType);

    // ============================================
    // PREVIEW DE URL DE VIDEO (YouTube)
    // ============================================
    const videoUrlInput = document.getElementById('video_url');
    const videoUrlPreview = document.getElementById('videoUrlPreview');

    videoUrlInput.addEventListener('input', function() {
        const url = this.value.trim();
        if (!url) {
            videoUrlPreview.innerHTML = '';
            return;
        }

        const youtubeRegex = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&]+)/;
        const match = url.match(youtubeRegex);

        if (match) {
            const videoId = match[1];
            videoUrlPreview.innerHTML = `
                <div class="preview-container">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <i class="fas fa-check-circle" style="color: var(--success);"></i>
                        <span class="fw-semibold">Vista previa del video</span>
                    </div>
                    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: var(--radius-sm);">
                        <iframe src="https://www.youtube.com/embed/${videoId}"
                                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                                frameborder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowfullscreen>
                        </iframe>
                    </div>
                </div>
            `;
        } else {
            videoUrlPreview.innerHTML = `
                <div class="preview-container">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fas fa-link" style="color: var(--primary);"></i>
                        <span>URL de video configurada: <a href="${url}" target="_blank" style="color: var(--primary);">${url}</a></span>
                    </div>
                </div>
            `;
        }
    });

    // ============================================
    // VALIDACIÓN DEL FORMULARIO
    // ============================================
    const form = document.getElementById('lessonForm');
    const titleInput = document.getElementById('title');

    function showError(input, message) {
        input.classList.add('is-invalid');
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
        feedback.textContent = message;
    }

    form.addEventListener('submit', function(e) {
        let valid = true;
        const type = typeHidden.value;

        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        const title = titleInput.value.trim();
        if (!title) {
            showError(titleInput, 'El título es obligatorio.');
            valid = false;
        } else if (title.length < 3) {
            showError(titleInput, 'El título debe tener al menos 3 caracteres.');
            valid = false;
        }

        if (type === 'video') {
            const hasUrl = videoUrlInput.value.trim() !== '';
            const hasFile = videoPond.getFiles().length > 0;
            if (!hasUrl && !hasFile) {
                showError(videoUrlInput, 'Debes proporcionar una URL de video o subir un archivo.');
                valid = false;
            }
        }

        if (type === 'document' && documentPond.getFiles().length === 0) {
            showError(documentFileInput, 'Debes subir un archivo de documento.');
            valid = false;
        }

        if (type === 'quiz') {
            const timeLimit = document.getElementById('quiz_time_limit').value;
            const passingScore = document.getElementById('quiz_passing_score').value;
            if (timeLimit && (isNaN(timeLimit) || parseInt(timeLimit) < 1)) {
                showError(document.getElementById('quiz_time_limit'), 'Ingresa un tiempo válido.');
                valid = false;
            }
            if (passingScore && (isNaN(passingScore) || parseInt(passingScore) < 0 || parseInt(passingScore) > 100)) {
                showError(document.getElementById('quiz_passing_score'), 'Ingresa un puntaje entre 0 y 100.');
                valid = false;
            }
        }

        if (!valid) {
            e.preventDefault();
            const firstError = form.querySelector('.is-invalid');
            if (firstError) firstError.focus();
            return false;
        }

        const submitBtn = document.getElementById('submitBtn');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';
        submitBtn.disabled = true;
        return true;
    });
});
