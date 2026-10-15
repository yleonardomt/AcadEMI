// ============================================
// INTERACCIONES DE LA PORTADA (templates/academi/index.html)
// Todo se degrada con elegancia: si el navegador no soporta
// IntersectionObserver o el usuario pidió menos movimiento,
// el contenido simplemente aparece estático (sin animar).
// El CSS solo oculta los .reveal cuando este script ya cargó
// (clase .landing-js), así que sin JS todo se ve normal.
// ============================================

document.documentElement.classList.add('landing-js');

document.addEventListener('DOMContentLoaded', function() {
    var reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    var prefersReducedMotion = reducedMotionQuery.matches;
    var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    // ===== Scroll suave para enlaces internos =====
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var href = this.getAttribute('href');
            if (href === '#') return;

            var target = document.querySelector(href);
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({
                behavior: prefersReducedMotion ? 'auto' : 'smooth',
                block: 'start'
            });
        });
    });

    // ===== Revelado al hacer scroll (con entrada escalonada) =====
    // Los hijos .reveal de un contenedor [data-stagger] reciben --i (0..5);
    // el CSS lo usa como retraso, así una fila de tarjetas entra en cascada
    // (70 ms entre una y otra) en vez de aparecer toda junta.
    document.querySelectorAll('[data-stagger]').forEach(function(group) {
        Array.prototype.filter.call(group.children, function(child) {
            return child.classList.contains('reveal');
        }).forEach(function(child, i) {
            child.style.setProperty('--i', Math.min(i, 5));
        });
    });

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
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        revealEls.forEach(function(el) { revealObserver.observe(el); });
    }

    // ===== Video del hero: botón de pausa (accesibilidad) =====
    // Un video que se mueve solo más de 5 segundos debe poder pausarse.
    // También arranca pausado si el usuario pidió menos movimiento.
    var heroVideo = document.querySelector('.hero-video-bg');
    var videoToggle = document.querySelector('.hero-video-toggle');
    if (heroVideo && videoToggle) {
        var toggleIcon = videoToggle.querySelector('i');

        function setVideoPaused(paused) {
            if (paused) { heroVideo.pause(); } else { heroVideo.play().catch(function() {}); }
            videoToggle.setAttribute('aria-pressed', paused ? 'true' : 'false');
            videoToggle.setAttribute('aria-label', paused ? 'Reanudar video de fondo' : 'Pausar video de fondo');
            toggleIcon.className = paused ? 'fas fa-play' : 'fas fa-pause';
        }

        videoToggle.addEventListener('click', function() {
            setVideoPaused(!heroVideo.paused);
        });
        if (prefersReducedMotion) setVideoPaused(true);
    }

    // ===== Brillo que sigue al cursor en las tarjetas del bento =====
    // Solo con mouse. Actualiza --mx/--my en la propia tarjeta (no en el
    // contenedor) para no recalcular estilos de toda la cuadrícula.
    var featuresGrid = document.querySelector('.features-grid');
    if (featuresGrid && finePointer && !prefersReducedMotion) {
        var glowFrame = null;
        featuresGrid.addEventListener('pointermove', function(e) {
            var card = e.target.closest('.feature-card');
            if (!card || glowFrame) return;
            var x = e.clientX, y = e.clientY;
            glowFrame = requestAnimationFrame(function() {
                var rect = card.getBoundingClientRect();
                card.style.setProperty('--mx', (x - rect.left) + 'px');
                card.style.setProperty('--my', (y - rect.top) + 'px');
                glowFrame = null;
            });
        });
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
});


// ===== Puntos indicadores del carrusel de cursos (solo se muestran en celular) =====
document.addEventListener('DOMContentLoaded', function() {
    var track = document.querySelector('.courses .row.g-4');
    if (!track) return;

    var items = Array.prototype.slice.call(track.querySelectorAll(':scope > [class*="col-"]'));
    if (items.length < 2) return;

    var nav = document.createElement('div');
    nav.className = 'carousel-dots';
    var dots = items.slice(0, 10).map(function(_, i) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'carousel-dot';
        dot.setAttribute('aria-label', 'Ir al curso ' + (i + 1));
        dot.addEventListener('click', function() {
            var item = items[i];
            track.scrollTo({
                left: item.offsetLeft - (track.clientWidth - item.offsetWidth) / 2,
                behavior: 'smooth'
            });
        });
        nav.appendChild(dot);
        return dot;
    });
    track.parentNode.insertBefore(nav, track.nextSibling);

    function update() {
        var center = track.scrollLeft + track.clientWidth / 2;
        var best = 0, bestDist = Infinity;
        items.forEach(function(item, i) {
            var d = Math.abs(item.offsetLeft + item.offsetWidth / 2 - center);
            if (d < bestDist) { bestDist = d; best = i; }
        });
        dots.forEach(function(dot, i) { dot.classList.toggle('is-active', i === Math.min(best, dots.length - 1)); });
    }

    var ticking = false;
    track.addEventListener('scroll', function() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function() { update(); ticking = false; });
    }, { passive: true });
    update();
});
