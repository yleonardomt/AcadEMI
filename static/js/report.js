// ============================================
// REPORTAR CONTENIDO (RF-42)
// Rellena el modal compartido (partials/report_modal.html)
// y lo abre con el sistema de modales sin fondo negro.
// ============================================

function openReportModal(type, contentId) {
    var typeField = document.getElementById('reportContentType');
    var idField = document.getElementById('reportContentId');
    if (!typeField || !idField) {
        console.error('Modal de reporte no encontrado en esta página.');
        return;
    }
    typeField.value = type;
    idField.value = contentId;
    openModalWithoutBackdrop('reportContentModal');
}

window.openReportModal = openReportModal;
