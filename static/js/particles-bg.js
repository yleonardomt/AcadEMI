// ============================================
// FONDO 3D DE PARTÍCULAS (Three.js/WebGL)
// Simple: esferas azules flotando suavemente en 3D
// (profundidad real vía cámara en perspectiva + niebla),
// sin líneas ni movimientos bruscos de cámara.
// Se degrada con elegancia: si Three.js no cargó, si el
// navegador no soporta WebGL, o si el usuario pidió menos
// movimiento, simplemente no se dibuja nada y queda el
// fondo con degradado normal.
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    if (typeof THREE === 'undefined') return;

    var canvas = document.getElementById('bg-particles');
    if (!canvas) return;

    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;
    var isSmallScreen = window.innerWidth < 769;
    var isLightweight = isCoarsePointer || isSmallScreen;

    var particleCount = isLightweight ? 60 : 140;

    var renderer;
    try {
        renderer = new THREE.WebGLRenderer({
            canvas: canvas,
            alpha: true,
            antialias: !isLightweight,
            powerPreference: 'low-power',
        });
    } catch (e) {
        return; // Sin WebGL disponible: se queda el degradado de fondo normal.
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isLightweight ? 1.5 : 2));
    renderer.setSize(window.innerWidth, window.innerHeight);

    var scene = new THREE.Scene();
    // El fondo de la página es claro (ver base.css); la niebla difumina
    // las esferas más lejanas hacia ese mismo tono para dar profundidad.
    scene.fog = new THREE.Fog(0xeef1f9, 400, 1400);
    var camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 1, 2000);
    camera.position.z = 600;

    // ===== Geometría: nube de esferas =====
    var geometry = new THREE.BufferGeometry();
    var positions = new Float32Array(particleCount * 3);
    var basePositions = new Float32Array(particleCount * 3);
    var colors = new Float32Array(particleCount * 3);
    var wavePhase = new Float32Array(particleCount);
    var waveSpeed = new Float32Array(particleCount);

    var colorDeep = new THREE.Color(0x0033a0);   // azul primario de la marca
    var colorBright = new THREE.Color(0x1a4db8); // azul medio
    var colorGlow = new THREE.Color(0x0ea5e9);   // celeste saturado

    for (var i = 0; i < particleCount; i++) {
        var x = (Math.random() - 0.5) * 1600;
        var y = (Math.random() - 0.5) * 1000;
        var z = (Math.random() - 0.5) * 800;

        basePositions[i * 3] = x;
        basePositions[i * 3 + 1] = y;
        basePositions[i * 3 + 2] = z;

        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;

        wavePhase[i] = Math.random() * Math.PI * 2;
        waveSpeed[i] = 0.25 + Math.random() * 0.35;

        var mix = Math.random();
        var mixed = mix < 0.5
            ? colorDeep.clone().lerp(colorBright, mix * 2)
            : colorBright.clone().lerp(colorGlow, (mix - 0.5) * 2);
        colors[i * 3] = mixed.r;
        colors[i * 3 + 1] = mixed.g;
        colors[i * 3 + 2] = mixed.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    var positionAttribute = geometry.getAttribute('position');

    // ===== Textura de esfera con sombreado (para que se vean como
    // bolitas con volumen, no puntos planos) =====
    function createSphereTexture() {
        var size = 64;
        var c = document.createElement('canvas');
        c.width = c.height = size;
        var ctx = c.getContext('2d');
        var gradient = ctx.createRadialGradient(
            size * 0.35, size * 0.35, 0,
            size * 0.5, size * 0.5, size * 0.5
        );
        gradient.addColorStop(0, 'rgba(255,255,255,1)');
        gradient.addColorStop(0.5, 'rgba(255,255,255,0.85)');
        gradient.addColorStop(0.85, 'rgba(255,255,255,0.35)');
        gradient.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);
        return new THREE.CanvasTexture(c);
    }

    var material = new THREE.PointsMaterial({
        size: isLightweight ? 8 : 11,
        map: createSphereTexture(),
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        opacity: 0.9,
        // Blending normal (no aditivo): sobre un fondo claro, el
        // aditivo suma hacia blanco y las partículas casi desaparecen.
        blending: THREE.NormalBlending,
        fog: true,
    });

    var points = new THREE.Points(geometry, material);
    scene.add(points);

    window.addEventListener('resize', function() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    var clock = new THREE.Clock();
    var waveAmplitude = isLightweight ? 12 : 18;

    function updateFloat(t) {
        var array = positionAttribute.array;
        for (var i = 0; i < particleCount; i++) {
            var idx = i * 3;
            array[idx + 1] = basePositions[idx + 1] + Math.sin(t * waveSpeed[i] + wavePhase[i]) * waveAmplitude;
            array[idx] = basePositions[idx] + Math.cos(t * waveSpeed[i] * 0.6 + wavePhase[i]) * (waveAmplitude * 0.5);
        }
        positionAttribute.needsUpdate = true;
    }

    function renderFrame() {
        var t = clock.getElapsedTime();
        updateFloat(t);
        // Rotación única y lenta de toda la nube: suficiente para que
        // se note que es un espacio 3D real, sin exagerar el movimiento.
        points.rotation.y = t * 0.025;
        renderer.render(scene, camera);
    }

    if (prefersReducedMotion) {
        renderer.render(scene, camera);
        return;
    }

    function animate() {
        requestAnimationFrame(animate);
        renderFrame();
    }
    animate();
});
