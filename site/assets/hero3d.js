/**
 * hero3d.js — Live 3-D WebGL hero for awesome-mad-projects.
 * Requires Three.js r160 loaded before this script (assets/vendor/three.min.js).
 *
 * Scene:
 *   - Parametric Mobius strip with highlighted zero-curve midline
 *   - Torus encircling the scene
 *   - 14 geodesic-style curves converging toward a glowing "Gojo" singularity
 *   - Particle star field
 *
 * Features:
 *   - ~60 fps target; devicePixelRatio capped at 2
 *   - requestAnimationFrame loop, paused when tab is hidden
 *   - Hand-rolled mouse/touch orbit (drag-to-rotate)
 *   - Slow auto-rotation; orbit resets after drag
 *   - Graceful fallback: exits early when WebGL unavailable OR prefers-reduced-motion
 *   - Adds class "canvas-active" to #hero so CSS can hide the static poster
 */
(function () {
  'use strict';

  // ── Pre-flight checks ──────────────────────────────────────────────────
  if (!window.THREE) return;

  var prefersReduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return;

  var canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  // Test WebGL availability without allocating the main renderer yet
  try {
    var testCtx = document.createElement('canvas').getContext('webgl') ||
                  document.createElement('canvas').getContext('experimental-webgl');
    if (!testCtx) throw new Error('no-webgl');
    var ext = testCtx.getExtension('WEBGL_lose_context');
    if (ext) ext.loseContext();
  } catch (e) {
    return; // No WebGL → CSS static fallback (poster image)
  }

  var THREE = window.THREE;

  // ── Renderer ──────────────────────────────────────────────────────────
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x080b14, 1);

  function W() { return canvas.clientWidth; }
  function H() { return canvas.clientHeight; }
  renderer.setSize(W(), H(), false);

  // ── Scene & Camera ────────────────────────────────────────────────────
  var scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x080b14, 0.055);

  var camera = new THREE.PerspectiveCamera(55, W() / H(), 0.1, 80);
  camera.position.set(0, 2.2, 10);
  camera.lookAt(0, 0, 0);

  // ── Main group (orbit target) ──────────────────────────────────────────
  var group = new THREE.Group();
  group.rotation.x = 0.25;
  scene.add(group);

  // ── Helpers ───────────────────────────────────────────────────────────
  function glowLine(pts, color, opacity, lw) {
    var geom = new THREE.BufferGeometry().setFromPoints(pts);
    var mat  = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: opacity });
    return new THREE.Line(geom, mat);
  }

  function addGlowLine(target, pts, color, baseOpacity) {
    // Core line
    target.add(glowLine(pts, color, baseOpacity, 1));
    // Bloom imitation: wider, dimmer duplicate
    target.add(glowLine(pts, color, baseOpacity * 0.18, 4));
  }

  // ── Mobius Strip ──────────────────────────────────────────────────────
  var U_SEG = 80, V_SEG = 20;
  var R_MOBIUS = 1.8, HALF_W = 0.42;

  function buildMobiusGeom() {
    var pos = [];
    var idx = [];
    for (var i = 0; i <= U_SEG; i++) {
      var u = (i / U_SEG) * Math.PI * 2;
      for (var j = 0; j <= V_SEG; j++) {
        var v = (j / V_SEG) * 2 - 1;  // -1 → 1
        var x = (R_MOBIUS + HALF_W * v * Math.cos(u / 2)) * Math.cos(u);
        var y = (R_MOBIUS + HALF_W * v * Math.cos(u / 2)) * Math.sin(u);
        var z = HALF_W * v * Math.sin(u / 2);
        pos.push(x * 0.44, y * 0.44, z * 0.44); // scale to fit scene
      }
    }
    for (var ii = 0; ii < U_SEG; ii++) {
      for (var jj = 0; jj < V_SEG; jj++) {
        var a = ii * (V_SEG + 1) + jj;
        var b = a + 1;
        var c = (ii + 1) * (V_SEG + 1) + jj;
        var d = c + 1;
        idx.push(a, b, d, a, d, c);
      }
    }
    var geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
    geom.setIndex(idx);
    geom.computeVertexNormals();
    return geom;
  }

  // Surface mesh
  var mobiusGeom = buildMobiusGeom();
  var mobiusMesh = new THREE.Mesh(
    mobiusGeom,
    new THREE.MeshBasicMaterial({
      color: 0x7c9cff, side: THREE.DoubleSide,
      transparent: true, opacity: 0.22, wireframe: false
    })
  );
  group.add(mobiusMesh);

  // Wireframe overlay
  var mobiusWire = new THREE.Mesh(
    mobiusGeom,
    new THREE.MeshBasicMaterial({
      color: 0x4fc3ff, side: THREE.DoubleSide,
      transparent: true, opacity: 0.38, wireframe: true
    })
  );
  group.add(mobiusWire);

  // Zero-curve midline (v = 0 → simple circle in XY scaled)
  (function () {
    var pts = [];
    var N = 300;
    for (var i = 0; i <= N; i++) {
      var u = (i / N) * Math.PI * 2;
      // v=0: x = R*cos(u), y = R*sin(u), z = 0
      pts.push(new THREE.Vector3(
        R_MOBIUS * Math.cos(u) * 0.44,
        R_MOBIUS * Math.sin(u) * 0.44,
        0
      ));
    }
    addGlowLine(group, pts, 0x5be7c4, 0.9);
  }());

  // ── Torus ─────────────────────────────────────────────────────────────
  var torusGeom  = new THREE.TorusGeometry(3.2, 0.06, 6, 90);
  var torus = new THREE.Mesh(
    torusGeom,
    new THREE.MeshBasicMaterial({ color: 0xb98cff, transparent: true, opacity: 0.55 })
  );
  // Glow copy
  var torusGlow = new THREE.Mesh(
    torusGeom,
    new THREE.MeshBasicMaterial({ color: 0xb98cff, transparent: true, opacity: 0.10 })
  );
  torus.rotation.x = Math.PI * 0.35;
  torus.rotation.y = Math.PI * 0.15;
  torusGlow.rotation.copy(torus.rotation);
  group.add(torus);
  group.add(torusGlow);

  // ── Gojo Singularity Point ────────────────────────────────────────────
  // The geodesics converge to this point
  var GOJO = new THREE.Vector3(0.3, 0.1, 0);

  // Glow rings (layered sphere halos)
  var gojoGroup = new THREE.Group();
  gojoGroup.position.copy(GOJO);
  scene.add(gojoGroup); // Not inside `group` — stays near fixed position

  var haloSizes = [0.38, 0.22, 0.12, 0.055, 0.018];
  var haloAlpha = [0.06, 0.10, 0.18, 0.45, 0.95];
  haloSizes.forEach(function (r, i) {
    var m = new THREE.Mesh(
      new THREE.SphereGeometry(r, 12, 12),
      new THREE.MeshBasicMaterial({
        color: i === haloSizes.length - 1 ? 0xffffff : 0x5be7c4,
        transparent: true, opacity: haloAlpha[i]
      })
    );
    gojoGroup.add(m);
  });

  // ── Geodesic Curves ───────────────────────────────────────────────────
  (function () {
    var N_CURVES = 14;
    var colors = [0x4fc3ff, 0x7c9cff, 0xb98cff, 0x5be7c4];
    for (var i = 0; i < N_CURVES; i++) {
      var theta = (i / N_CURVES) * Math.PI * 2;
      var phi   = (0.2 + (i % 4) * 0.22) * Math.PI;
      var dist  = 4.8;
      var sx = dist * Math.sin(phi) * Math.cos(theta);
      var sy = dist * Math.sin(phi) * Math.sin(theta) * 0.7;
      var sz = dist * Math.cos(phi);

      // Midpoint with slight random offset for organic look
      var seed  = Math.sin(i * 137.5) * 0.5;
      var mx = (sx + GOJO.x) * 0.5 + seed * 0.6;
      var my = (sy + GOJO.y) * 0.5 + Math.cos(i * 89.3) * 0.4;
      var mz = (sz + GOJO.z) * 0.5 + Math.sin(i * 52.7) * 0.5;

      var curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(sx, sy, sz),
        new THREE.Vector3(mx, my, mz),
        new THREE.Vector3(
          mx * 0.35 + GOJO.x * 0.65,
          my * 0.35 + GOJO.y * 0.65,
          mz * 0.35 + GOJO.z * 0.65
        ),
        GOJO.clone()
      ]);

      var pts  = curve.getPoints(60);
      var col  = colors[i % colors.length];
      var fade = 0.25 + 0.15 * (i % 3);
      addGlowLine(group, pts, col, fade);
    }
  }());

  // ── Star field ────────────────────────────────────────────────────────
  (function () {
    var count = 280;
    var buf   = new Float32Array(count * 3);
    var rng   = function (a, b) { return a + Math.random() * (b - a); };
    for (var i = 0; i < count; i++) {
      buf[i * 3]     = rng(-22, 22);
      buf[i * 3 + 1] = rng(-14, 14);
      buf[i * 3 + 2] = rng(-18, 18);
    }
    var sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(buf, 3));
    var sm = new THREE.PointsMaterial({ color: 0xffffff, size: 0.055, transparent: true, opacity: 0.65 });
    scene.add(new THREE.Points(sg, sm));
  }());

  // ── Orbit control (hand-rolled) ───────────────────────────────────────
  var orbit = { rotY: 0.0, rotX: 0.25, dragging: false, prevX: 0, prevY: 0 };

  canvas.addEventListener('mousedown', function (e) {
    orbit.dragging = true;
    orbit.prevX = e.clientX;
    orbit.prevY = e.clientY;
    canvas.style.cursor = 'grabbing';
  });
  window.addEventListener('mouseup', function () {
    orbit.dragging = false;
    canvas.style.cursor = 'grab';
  });
  window.addEventListener('mousemove', function (e) {
    if (!orbit.dragging) return;
    orbit.rotY += (e.clientX - orbit.prevX) * 0.0045;
    orbit.rotX  = Math.max(-0.65, Math.min(0.65,
      orbit.rotX + (e.clientY - orbit.prevY) * 0.0045));
    orbit.prevX = e.clientX;
    orbit.prevY = e.clientY;
  });

  // Touch
  canvas.addEventListener('touchstart', function (e) {
    orbit.prevX = e.touches[0].clientX;
    orbit.prevY = e.touches[0].clientY;
  }, { passive: true });
  canvas.addEventListener('touchmove', function (e) {
    orbit.rotY += (e.touches[0].clientX - orbit.prevX) * 0.004;
    orbit.rotX  = Math.max(-0.65, Math.min(0.65,
      orbit.rotX + (e.touches[0].clientY - orbit.prevY) * 0.004));
    orbit.prevX = e.touches[0].clientX;
    orbit.prevY = e.touches[0].clientY;
  }, { passive: true });

  canvas.style.cursor = 'grab';

  // ── Resize ────────────────────────────────────────────────────────────
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      renderer.setSize(W(), H(), false);
      camera.aspect = W() / H();
      camera.updateProjectionMatrix();
    }, 100);
  });

  // ── Visibility pause ─────────────────────────────────────────────────
  var paused = false;
  document.addEventListener('visibilitychange', function () {
    paused = document.hidden;
  });

  // ── Animation loop ────────────────────────────────────────────────────
  var clock = 0;
  function animate() {
    requestAnimationFrame(animate);
    if (paused) return;
    clock += 0.014;

    // Auto-rotate (pauses when user is dragging)
    if (!orbit.dragging) {
      orbit.rotY += 0.0025;
    }

    group.rotation.y = orbit.rotY;
    group.rotation.x = orbit.rotX;

    // Torus own rotation
    torus.rotation.z     = clock * 0.12;
    torusGlow.rotation.z = torus.rotation.z;

    // Gojo pulse — the halo breathes
    var pulse = 0.85 + 0.15 * Math.sin(clock * 2.3);
    gojoGroup.scale.setScalar(pulse);

    renderer.render(scene, camera);
  }

  // ── Mark hero as active ───────────────────────────────────────────────
  var heroEl = document.getElementById('hero');
  if (heroEl) heroEl.classList.add('canvas-active');

  animate();
}());
