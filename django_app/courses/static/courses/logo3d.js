// 登入頁的六個方塊 logo：three.js 3D 版。
// 失敗（沒有 WebGL、three.js 沒載入）時保留原本的 CSS 方塊。
(function () {
  var canvas = document.getElementById("logo3d"), tiles = document.querySelector(".tiles");
  if (!canvas || !tiles || typeof THREE === "undefined") return;

  var renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true }); } catch (e) { return; }
  var W = 132, H = 96;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(W, H, false);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.setClearColor(0x000000, 0);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 100);
  camera.position.set(0, 0, 17);
  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  var key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(3, 5, 8); scene.add(key);
  var rim = new THREE.DirectionalLight(0xffffff, 0.35); rim.position.set(-5, -3, 4); scene.add(rim);

  // 圓角方塊：圓角矩形擠出成厚度，邊緣再倒一圈斜角
  var TW = 2.6, TH = 2.0, GAP = 0.5, R = 0.5, D = 0.8;
  var shape = new THREE.Shape();
  shape.moveTo(-TW / 2 + R, -TH / 2);
  shape.lineTo(TW / 2 - R, -TH / 2); shape.quadraticCurveTo(TW / 2, -TH / 2, TW / 2, -TH / 2 + R);
  shape.lineTo(TW / 2, TH / 2 - R); shape.quadraticCurveTo(TW / 2, TH / 2, TW / 2 - R, TH / 2);
  shape.lineTo(-TW / 2 + R, TH / 2); shape.quadraticCurveTo(-TW / 2, TH / 2, -TW / 2, TH / 2 - R);
  shape.lineTo(-TW / 2, -TH / 2 + R); shape.quadraticCurveTo(-TW / 2, -TH / 2, -TW / 2 + R, -TH / 2);
  var geo = new THREE.ExtrudeGeometry(shape, { depth: D, bevelEnabled: true, bevelSize: 0.12, bevelThickness: 0.12, bevelSegments: 3, curveSegments: 8 });
  geo.translate(0, 0, -D / 2);

  var css = getComputedStyle(document.documentElement);
  var group = new THREE.Group(); scene.add(group);
  var meshes = [];
  for (var i = 0; i < 6; i++) {
    var col = css.getPropertyValue("--t" + (i + 1)).trim() || "#1a73e8";
    var m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: new THREE.Color(col).convertSRGBToLinear(), roughness: 0.38, metalness: 0.08 }));
    m.userData.home = new THREE.Vector3((i % 3 - 1) * (TW + GAP), (0.5 - Math.floor(i / 3)) * (TH + GAP), 0);
    m.userData.delay = 0.05 + i * 0.1;  // 對應原本 CSS 的出場順序
    m.position.copy(m.userData.home);
    group.add(m); meshes.push(m);
  }

  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var px = 0, py = 0, tx = 0, ty = 0;  // 指標位置（-1～1）與平滑後的值
  window.addEventListener("pointermove", function (e) {
    tx = (e.clientX / innerWidth) * 2 - 1; ty = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });

  function easeOutBack(t) { var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); }
  var t0 = performance.now();
  function frame(now) {
    var t = (now - t0) / 1000;
    px += (tx - px) * 0.06; py += (ty - py) * 0.06;
    meshes.forEach(function (m, i) {
      var k = reduce ? 1 : Math.min(Math.max((t - m.userData.delay) / 0.7, 0), 1), e = easeOutBack(k);
      m.visible = k > 0;
      m.scale.setScalar(Math.max(e, 0.001));
      m.rotation.x = (1 - e) * -Math.PI;
      m.position.set(m.userData.home.x, m.userData.home.y + (1 - e) * 4,
        reduce ? 0 : Math.sin(t * 1.5 + i * 0.9) * 0.18 * k);
    });
    group.rotation.y = px * 0.5 + (reduce ? 0 : Math.sin(t * 0.7) * 0.18);
    group.rotation.x = py * 0.35 - 0.12;
    renderer.render(scene, camera);
    if (!reduce || t < 0.2) requestAnimationFrame(frame);
  }

  canvas.hidden = false;
  tiles.hidden = true;
  requestAnimationFrame(frame);
})();
