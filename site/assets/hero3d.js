/**
 * hero3d.js — Live 3-D WebGL hero for awesome-mad-projects.
 * Requires Three.js r160 loaded before this script (assets/vendor/three.min.js).
 *
 * Aesthetic: ink-on-cream technical plate.
 *   - Cream background (#f6f2e9), near-black ink lines (#16150f)
 *   - Single vermilion accent (#d1341a) for the central singularity
 *   - No starfield, no glow/bloom, no neon — precision line-drawing
 *   - Möbius strip wireframe + torus + converging geodesic curves
 *   - Slow auto-rotation; drag to orbit; reduced-motion fallback
 */
(function () {
  'use strict';

  if (!window.THREE) return;

  var prefersReduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return;

  var canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  try {
    var testCtx = document.createElement('canvas').getContext('webgl') ||
                  document.createElement('canvas').getContext('experimental-webgl');
    if (!testCtx) throw new Error('no-webgl');
    var ext = testCtx.getExtension('WEBGL_lose_context');
    if (ext) ext.loseContext();
  } catch (e) { return; }

  var THREE = window.THREE;

  // ── Palette (ink on cream) ────────────────────────────────────────────────
  var C_BG      = 0xf6f2e9;   // cream
  var C_INK     = 0x16150f;   // near-black
  var C_INK_MID = 0x3d3b32;   // dark grey
  var C_MUTED   = 0x6b6760;   // mid grey
  var C_ACCENT  = 0xd1341a;   // vermilion

  // ── Renderer ──────────────────────────────────────────────────────────────
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(C_BG, 1);

  function W() { return canvas.clientWidth; }
  function H() { return canvas.clientHeight; }
  renderer.setSize(W(), H(), false);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  var scene  = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(52, W() / H(), 0.1, 80);
  camera.position.set(0, 2.0, 10.5);
  camera.lookAt(0, 0, 0);

  var group = new THREE.Group();
  group.rotation.x = 0.22;
  scene.add(group);

  // ── Line helper ───────────────────────────────────────────────────────────
  function inkLine(pts, color, opacity) {
    var geom = new THREE.BufferGeometry().setFromPoints(pts);
    var mat  = new THREE.LineBasicMaterial({
      color: color, transparent: true, opacity: opacity
    });
    return new THREE.Line(geom, mat);
  }

  // ── Möbius strip ──────────────────────────────────────────────────────────
  var U_SEG = 80, V_SEG = 20;
  var R_M = 1.8, HW = 0.42;

  function buildMobiusGeom() {
    var pos = [], idx = [];
    for (var i = 0; i <= U_SEG; i++) {
      var u = (i / U_SEG) * Math.PI * 2;
      for (var j = 0; j <= V_SEG; j++) {
        var v = (j / V_SEG) * 2 - 1;
        var x = (R_M + HW * v * Math.cos(u / 2)) * Math.cos(u);
        var y = (R_M + HW * v * Math.cos(u / 2)) * Math.sin(u);
        var z = HW * v * Math.sin(u / 2);
        pos.push(x * 0.44, y * 0.44, z * 0.44);
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

  var mobiusGeom = buildMobiusGeom();

  // Very subtle fill (cream tint, almost transparent)
  var mobiusMesh = new THREE.Mesh(mobiusGeom,
    new THREE.MeshBasicMaterial({
      color: 0xede9de, side: THREE.DoubleSide,
      transparent: true, opacity: 0.35, wireframe: false
    })
  );
  group.add(mobiusMesh);

  // Wireframe in ink
  var mobiusWire = new THREE.Mesh(mobiusGeom,
    new THREE.MeshBasicMaterial({
      color: C_INK_MID, side: THREE.DoubleSide,
      transparent: true, opacity: 0.22, wireframe: true
    })
  );
  group.add(mobiusWire);

  // Zero-curve midline (accent)
  (function () {
    var pts = [];
    for (var i = 0; i <= 300; i++) {
      var u = (i / 300) * Math.PI * 2;
      pts.push(new THREE.Vector3(
        R_M * Math.cos(u) * 0.44,
        R_M * Math.sin(u) * 0.44,
        0
      ));
    }
    group.add(inkLine(pts, C_ACCENT, 0.75));
  }());

  // ── Torus (hairline ink ring) ─────────────────────────────────────────────
  var torusGeom = new THREE.TorusGeometry(3.2, 0.04, 4, 90);
  var torus = new THREE.Mesh(torusGeom,
    new THREE.MeshBasicMaterial({ color: C_INK_MID, transparent: true, opacity: 0.30 })
  );
  torus.rotation.x = Math.PI * 0.35;
  torus.rotation.y = Math.PI * 0.15;
  group.add(torus);

  // ── Singularity point (small accent sphere) ───────────────────────────────
  var GOJO = new THREE.Vector3(0.3, 0.1, 0);
  var singularityGroup = new THREE.Group();
  singularityGroup.position.copy(GOJO);
  scene.add(singularityGroup);

  // Small solid accent dot — no halos/glow
  var singDot = new THREE.Mesh(
    new THREE.SphereGeometry(0.055, 8, 8),
    new THREE.MeshBasicMaterial({ color: C_ACCENT, transparent: true, opacity: 0.90 })
  );
  singularityGroup.add(singDot);

  // Thin accent ring around it
  var singRing = new THREE.Mesh(
    new THREE.TorusGeometry(0.14, 0.008, 4, 32),
    new THREE.MeshBasicMaterial({ color: C_ACCENT, transparent: true, opacity: 0.45 })
  );
  singularityGroup.add(singRing);

  // ── Geodesic curves (ink lines) ───────────────────────────────────────────
  (function () {
    var N = 14;
    for (var i = 0; i < N; i++) {
      var theta = (i / N) * Math.PI * 2;
      var phi   = (0.2 + (i % 4) * 0.22) * Math.PI;
      var dist  = 4.8;
      var sx = dist * Math.sin(phi) * Math.cos(theta);
      var sy = dist * Math.sin(phi) * Math.sin(theta) * 0.7;
      var sz = dist * Math.cos(phi);

      var seed = Math.sin(i * 137.5) * 0.5;
      var mx = (sx + GOJO.x) * 0.5 + seed * 0.5;
      var my = (sy + GOJO.y) * 0.5 + Math.cos(i * 89.3) * 0.35;
      var mz = (sz + GOJO.z) * 0.5 + Math.sin(i * 52.7) * 0.45;

      var curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(sx, sy, sz),
        new THREE.Vector3(mx, my, mz),
        new THREE.Vector3(mx * 0.35 + GOJO.x * 0.65, my * 0.35 + GOJO.y * 0.65, mz * 0.35 + GOJO.z * 0.65),
        GOJO.clone()
      ]);

      var pts = curve.getPoints(60);
      // Alternate between ink and muted for variety
      var col   = (i % 3 === 0) ? C_INK : ((i % 3 === 1) ? C_INK_MID : C_MUTED);
      var alpha = 0.18 + 0.18 * (i % 3);
      group.add(inkLine(pts, col, alpha));
    }
  }());

  // ── Orbit control (hand-rolled) ───────────────────────────────────────────
  var orbit = { rotY: 0.0, rotX: 0.22, dragging: false, prevX: 0, prevY: 0 };

  canvas.addEventListener('mousedown', function (e) {
    orbit.dragging = true; orbit.prevX = e.clientX; orbit.prevY = e.clientY;
    canvas.style.cursor = 'grabbing';
  });
  window.addEventListener('mouseup', function () {
    orbit.dragging = false; canvas.style.cursor = 'grab';
  });
  window.addEventListener('mousemove', function (e) {
    if (!orbit.dragging) return;
    orbit.rotY += (e.clientX - orbit.prevX) * 0.0042;
    orbit.rotX  = Math.max(-0.60, Math.min(0.60, orbit.rotX + (e.clientY - orbit.prevY) * 0.0042));
    orbit.prevX = e.clientX; orbit.prevY = e.clientY;
  });
  canvas.addEventListener('touchstart', function (e) {
    orbit.prevX = e.touches[0].clientX; orbit.prevY = e.touches[0].clientY;
  }, { passive: true });
  canvas.addEventListener('touchmove', function (e) {
    orbit.rotY += (e.touches[0].clientX - orbit.prevX) * 0.004;
    orbit.rotX  = Math.max(-0.60, Math.min(0.60, orbit.rotX + (e.touches[0].clientY - orbit.prevY) * 0.004));
    orbit.prevX = e.touches[0].clientX; orbit.prevY = e.touches[0].clientY;
  }, { passive: true });
  canvas.style.cursor = 'grab';

  // ── Resize ────────────────────────────────────────────────────────────────
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      renderer.setSize(W(), H(), false);
      camera.aspect = W() / H();
      camera.updateProjectionMatrix();
    }, 100);
  });

  // ── Visibility pause ──────────────────────────────────────────────────────
  var paused = false;
  document.addEventListener('visibilitychange', function () { paused = document.hidden; });

  // ── Animation loop ────────────────────────────────────────────────────────
  var clock = 0;
  function animate() {
    requestAnimationFrame(animate);
    if (paused) return;
    clock += 0.012;

    if (!orbit.dragging) orbit.rotY += 0.0020;

    group.rotation.y = orbit.rotY;
    group.rotation.x = orbit.rotX;

    torus.rotation.z = clock * 0.10;

    // Gentle singularity pulse (scale only — no glow)
    var pulse = 0.88 + 0.12 * Math.sin(clock * 2.0);
    singularityGroup.scale.setScalar(pulse);

    renderer.render(scene, camera);
  }

  var heroEl = document.getElementById('hero');
  if (heroEl) heroEl.classList.add('canvas-active');

  animate();
}());
