// ============================================
// APRENDER CURSO (templates/academi/courses/curso_aprender.html)
// ============================================

function toggleModule(element) {
    var body = element.nextElementSibling;
    var icon = element.querySelector('.fa-chevron-down');
    if (body.style.display === 'none') {
        body.style.display = 'block';
        icon.style.transform = 'rotate(0deg)';
    } else {
        body.style.display = 'none';
        icon.style.transform = 'rotate(-90deg)';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.module-body').forEach(function(body) {
        body.style.display = 'block';
    });
});
