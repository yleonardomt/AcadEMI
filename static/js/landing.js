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
});


// ===== Puntos indicadores de los carruseles (solo se muestran en celular) =====
document.addEventListener('DOMContentLoaded', function() {
    function setupDots(track, itemSelector) {
        var items = Array.prototype.slice.call(track.querySelectorAll(itemSelector));
        if (items.length < 2) return;

        var nav = document.createElement('div');
        nav.className = 'carousel-dots';
        nav.setAttribute('role', 'tablist');
        var dots = items.slice(0, 10).map(function(_, i) {
            var dot = document.createElement('button');
            dot.type = 'button';
            dot.className = 'carousel-dot';
            dot.setAttribute('aria-label', 'Ir al elemento ' + (i + 1));
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
    }

    var courses = document.querySelector('.courses .row.g-4');
    if (courses) setupDots(courses, ':scope > [class*="col-"]');
    var testimonials = document.querySelector('.testimonials-grid');
    if (testimonials) setupDots(testimonials, ':scope > .testimonial-card');
});
