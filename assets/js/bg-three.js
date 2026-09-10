/* Site background: a ground-plane grid receding into fog, with a point cloud
   drifting above it. The shape is deliberate — it is what a homography does to
   an image, which is the thing half these projects are about.

   Everything here is defensive: no WebGL, reduced-motion, or a hidden tab all
   end with the page looking fine and nothing running. */
(function () {
  'use strict';

  var canvas = document.getElementById('bg-canvas');
  if (!canvas || typeof THREE === 'undefined') return;

  // site.js has already resolved the OS setting and any explicit choice into
  // data-motion, so read that rather than the media query — otherwise the
  // visitor's opt-in would be ignored here.
  function motionOff() {
    return document.documentElement.getAttribute('data-motion') === 'off';
  }
  var GROUND = 0x0e0e12;   // matches surface-container-lowest
  var CYAN = 0x00f5ff;
  var VIOLET = 0xd0bcff;
  var EMERALD = 0x69f6b9;

  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'low-power'
    });
  } catch (e) {
    return; // no WebGL: the page keeps its flat background
  }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  renderer.setClearColor(GROUND, 0);

  var scene = new THREE.Scene();
  // Fog is what keeps this readable: the far half of the grid dissolves into
  // the page background instead of turning into visual noise behind text.
  scene.fog = new THREE.FogExp2(GROUND, 0.0092);

  var camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 500);
  camera.position.set(0, 6, 24);

  // ---- Ground plane grid -----------------------------------------------
  // Built by hand rather than GridHelper so the two axes can carry different
  // weights: the lines running away from the camera read as lane structure and
  // carry most of the motion, the cross ties just give them depth.
  var SPACING = 6;
  var HALF_X = 16;          // 16 * 6 = 96 units either side
  var DEPTH = 40;           // 40 * 6 = 240 units deep
  var gridGroup = new THREE.Group();

  function buildGrid(color, opacity, alongZ) {
    var positions = [];
    if (alongZ) {
      for (var i = -HALF_X; i <= HALF_X; i++) {
        positions.push(i * SPACING, 0, -DEPTH * SPACING, i * SPACING, 0, SPACING * 3);
      }
    } else {
      for (var j = -DEPTH; j <= 3; j++) {
        positions.push(-HALF_X * SPACING, 0, j * SPACING, HALF_X * SPACING, 0, j * SPACING);
      }
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    var mat = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      fog: true
    });
    return new THREE.LineSegments(geo, mat);
  }

  gridGroup.add(buildGrid(CYAN, 0.40, true));
  gridGroup.add(buildGrid(CYAN, 0.20, false));
  gridGroup.position.y = -5;
  scene.add(gridGroup);

  // A second grid overhead, dimmer and violet, so the field has a ceiling and
  // the middle of the screen is not an empty band.
  var ceiling = new THREE.Group();
  ceiling.add(buildGrid(VIOLET, 0.16, true));
  ceiling.add(buildGrid(VIOLET, 0.10, false));
  ceiling.position.y = 30;
  scene.add(ceiling);

  // ---- Point cloud ------------------------------------------------------
  // A soft round sprite, drawn once into a canvas: the default square points
  // read as dust specks rather than lights.
  function dotTexture() {
    var c = document.createElement('canvas');
    c.width = c.height = 64;
    var g = c.getContext('2d');
    var grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, 'rgba(255,255,255,1)');
    grd.addColorStop(0.25, 'rgba(255,255,255,0.75)');
    grd.addColorStop(0.55, 'rgba(255,255,255,0.22)');
    grd.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }

  var COUNT = 700;
  var pts = new Float32Array(COUNT * 3);
  var cols = new Float32Array(COUNT * 3);
  var drift = new Float32Array(COUNT);
  var palette = [new THREE.Color(CYAN), new THREE.Color(VIOLET), new THREE.Color(EMERALD)];

  function seed(k, far) {
    pts[k * 3] = (Math.random() - 0.5) * 190;
    pts[k * 3 + 1] = Math.random() * 34 - 4;
    pts[k * 3 + 2] = far ? -240 : -Math.random() * 240;
    drift[k] = 0.5 + Math.random() * 1.5;
  }

  for (var k = 0; k < COUNT; k++) {
    seed(k, false);
    var c = palette[(Math.random() * palette.length) | 0];
    var shade = 0.55 + Math.random() * 0.45;
    cols[k * 3] = c.r * shade;
    cols[k * 3 + 1] = c.g * shade;
    cols[k * 3 + 2] = c.b * shade;
  }

  var pointGeo = new THREE.BufferGeometry();
  pointGeo.setAttribute('position', new THREE.BufferAttribute(pts, 3));
  pointGeo.setAttribute('color', new THREE.BufferAttribute(cols, 3));

  var points = new THREE.Points(pointGeo, new THREE.PointsMaterial({
    size: 2.6,
    map: dotTexture(),
    vertexColors: true,
    transparent: true,
    opacity: 0.80,
    sizeAttenuation: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    fog: true
  }));
  scene.add(points);

  // ---- Interaction ------------------------------------------------------
  var pointer = { x: 0, y: 0 };
  var target = { x: 0, y: 0 };
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  if (fine) {
    window.addEventListener('mousemove', function (e) {
      if (motionOff()) return;
      target.x = (e.clientX / window.innerWidth - 0.5) * 2;
      target.y = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });
  }

  var scrollNorm = 0;
  window.addEventListener('scroll', function () {
    var max = document.body.scrollHeight - window.innerHeight;
    scrollNorm = max > 0 ? Math.min(1, window.scrollY / max) : 0;
  }, { passive: true });

  window.addEventListener('resize', function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight, false);
    if (motionOff()) renderer.render(scene, camera);
  }, { passive: true });

  // ---- Loop -------------------------------------------------------------
  var positionAttr = pointGeo.getAttribute('position');
  var start = performance.now();
  var running = false;
  var frame = 0;

  function render(now) {
    if (!running) return;
    var t = (now - start) / 1000;

    // Both grids scroll toward the camera and wrap by one cell, so the motion
    // is continuous without the geometry ever growing.
    gridGroup.position.z = (t * 9) % SPACING;
    ceiling.position.z = (t * 5.5) % SPACING;

    // Points drift forward at their own rates and recycle at the far plane.
    var arr = positionAttr.array;
    for (var i = 0; i < COUNT; i++) {
      arr[i * 3 + 2] += drift[i] * 0.32;
      if (arr[i * 3 + 2] > 20) {
        arr[i * 3] = (Math.random() - 0.5) * 190;
        arr[i * 3 + 1] = Math.random() * 34 - 4;
        arr[i * 3 + 2] = -240;
      }
    }
    positionAttr.needsUpdate = true;

    pointer.x += (target.x - pointer.x) * 0.035;
    pointer.y += (target.y - pointer.y) * 0.035;

    camera.position.x = pointer.x * 4;
    camera.position.y = 6 - pointer.y * 2 + scrollNorm * 6;
    camera.lookAt(pointer.x * 1.5, 4 - scrollNorm * 3, -40);

    renderer.render(scene, camera);
    frame = requestAnimationFrame(render);
  }

  function play() {
    if (running || motionOff()) return;
    running = true;
    frame = requestAnimationFrame(render);
  }

  function pause() {
    running = false;
    cancelAnimationFrame(frame);
  }

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) pause(); else play();
  });

  // Toggling the preference starts or stops the field without a reload.
  window.addEventListener('oca:motion', function (e) {
    if (e.detail === 'on') {
      start = performance.now();
      play();
    } else {
      pause();
      camera.lookAt(0, 4, -40);
      renderer.render(scene, camera);
    }
  });

  if (motionOff()) {
    // Still give the page its depth, just frozen.
    camera.lookAt(0, 4, -40);
    renderer.render(scene, camera);
  } else {
    play();
  }
})();
