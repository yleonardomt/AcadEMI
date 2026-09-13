// ============================================
// INTERACCIONES DE LA PORTADA (templates/academi/index.html)
// Todo se degrada con elegancia: si el navegador no soporta
// IntersectionObserver o el usuario pidió menos movimiento,
// el contenido simplemente aparece estático (sin animar).
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ===== Scroll suave para enlaces internos =====
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            var target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ===== Revelado al hacer scroll =====
    var revealEls = document.querySelectorAll('.reveal');
    if (prefersReducedMotion || typeof IntersectionObserver === 'undefined') {
        revealEls.forEach(function(el) { el.classList.add('in-view'); });
    } else {
        var revealObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
        revealEls.forEach(function(el) { revealObserver.observe(el); });
    }

    // ===== Contadores animados (estadísticas dinámicas) =====
    var counters = document.querySelectorAll('.counter');
    function animateCounter(el) {
        var target = parseFloat(el.getAttribute('data-count')) || 0;
        var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
        if (prefersReducedMotion) {
            el.textContent = target.toFixed(decimals);
            return;
        }
        var duration = 1400;
        var start = null;
        function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = (target * eased).toFixed(decimals);
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                el.textContent = target.toFixed(decimals);
            }
        }
        requestAnimationFrame(step);
    }

    if (counters.length && typeof IntersectionObserver !== 'undefined') {
        var counterObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach(function(el) { counterObserver.observe(el); });
    } else {
        counters.forEach(animateCounter);
    }

    // ===== Efecto 3D "tilt" al mover el mouse sobre tarjetas =====
    // Rota la tarjeta levemente según la posición del cursor para dar
    // sensación de profundidad. Se ignora en pantallas táctiles (no
    // hay hover real) y si el usuario prefiere menos movimiento.
    var isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;
    if (!prefersReducedMotion && !isCoarsePointer) {
        document.querySelectorAll('.tilt-card').forEach(function(card) {
            var maxTilt = 6;
            card.addEventListener('mousemove', function(e) {
                var rect = card.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width;
                var y = (e.clientY - rect.top) / rect.height;
                var rotateY = (x - 0.5) * maxTilt * 2;
                var rotateX = (0.5 - y) * maxTilt * 2;
                card.style.transform = 'perspective(900px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateY(-6px)';
            });
            card.addEventListener('mouseleave', function() {
                card.style.transform = '';
            });
        });
    }
});
