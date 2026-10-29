// 登入頁的六個方塊 logo：three.js 3D 入場動畫，播完後慢慢壓平，最後換回原本的 2D 方塊。
// 流程：飛入旋轉 → 炸開並整體轉一圈 → 壓平成 2D → 淡出 canvas、露出 CSS 方塊。
// 沒有 WebGL、three.js 沒載入、或使用者要求減少動態時，直接用原本的 CSS 方塊。
(function () {
  var canvas = document.getElementById("logo3d"), tiles = document.querySelector(".tiles");
  if (!canvas || !tiles || typeof THREE === "undefined") return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true }); } catch (e) { return; }
  var W = 132, H = 96;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(W, H, false);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.setClearColor(0x000000, 0);

  // 相機距離讓 1 單位剛好 10px：壓平時的方塊尺寸（26×20、間距 5）和 CSS 版一致
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 100);
  camera.position.set(0, 0, H / 10 / (2 * Math.tan(Math.PI / 12)));
  var ambient = new THREE.AmbientLight(0xffffff, 0.75); scene.add(ambient);
  var key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(3, 5, 8); scene.add(key);
  var rim = new THREE.DirectionalLight(0xffffff, 0.35); rim.position.set(-5, -3, 4); scene.add(rim);

  // 圓角方塊：圓角矩形擠出成厚度，邊緣再倒一圈斜角
  var TW = 2.6, TH = 2.0, GAP = 0.5, R = 0.5, D = 1.4;
  var shape = new THREE.Shape();
  shape.moveTo(-TW / 2 + R, -TH / 2);
  shape.lineTo(TW / 2 - R, -TH / 2); shape.quadraticCurveTo(TW / 2, -TH / 2, TW / 2, -TH / 2 + R);
  shape.lineTo(TW / 2, TH / 2 - R); shape.quadraticCurveTo(TW / 2, TH / 2, TW / 2 - R, TH / 2);
  shape.lineTo(-TW / 2 + R, TH / 2); shape.quadraticCurveTo(-TW / 2, TH / 2, -TW / 2, TH / 2 - R);
  shape.lineTo(-TW / 2, -TH / 2 + R); shape.quadraticCurveTo(-TW / 2, -TH / 2, -TW / 2 + R, -TH / 2);
  var geo = new THREE.ExtrudeGeometry(shape, { depth: D, bevelEnabled: true, bevelSize: 0.14, bevelThickness: 0.14, bevelSegments: 3, curveSegments: 8 });
  geo.translate(0, 0, -D / 2);

  var css = getComputedStyle(document.documentElement);
  var group = new THREE.Group(); scene.add(group);
  var P = Math.PI;
  var FROM = [[-9, 6, -16], [0, 10, -20], [9, 6, -16], [-9, -6, -16], [0, -10, -20], [9, -6, -16]];  // 飛入起點
  var SPIN = [[4 * P, -4 * P], [-4 * P, 6 * P], [4 * P, 4 * P], [-6 * P, -4 * P], [4 * P, -6 * P], [-4 * P, 4 * P]];  // 飛入時的旋轉量
  var meshes = [], mats = [];
  for (var i = 0; i < 6; i++) {
    var col = css.getPropertyValue("--t" + (i + 1)).trim() || "#1a73e8";
    var mat = new THREE.MeshStandardMaterial({ color: new THREE.Color(col).convertSRGBToLinear(), roughness: 0.3, metalness: 0.1 });  // r128：輸出是 sRGB，顏色要先轉成線性，不然會偏淡
    var m = new THREE.Mesh(geo, mat);
    m.userData.home = new THREE.Vector3((i % 3 - 1) * (TW + GAP), (0.5 - Math.floor(i / 3)) * (TH + GAP), 0);
    m.visible = false;
    group.add(m); meshes.push(m); mats.push(mat);
  }

  var px = 0, py = 0, tx = 0, ty = 0;  // 指標位置（-1～1）與平滑後的值
  window.addEventListener("pointermove", function (e) {
    tx = (e.clientX / innerWidth) * 2 - 1; ty = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });

  function clamp01(x) { return Math.min(Math.max(x, 0), 1); }
  function easeOutBack(t) { var c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); }
  function easeInOut(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function lerp(a, b, t) { return a + (b - a) * t; }

  var IN_DELAY = 0.12, IN_DUR = 1.0;                 // 飛入：每塊間隔 0.12 秒、各 1 秒
  var SHOW_AT = 1.8, SHOW_DUR = 1.8;                 // 炸開並整體轉一圈
  var FLAT_AT = SHOW_AT + SHOW_DUR, FLAT_DUR = 1.3;  // 壓平成 2D
  var END_AT = FLAT_AT + FLAT_DUR, FADE = 0.35;      // 換回 CSS 方塊
  var t0 = performance.now(), swapped = false;

  function frame(now) {
    var t = (now - t0) / 1000;
    px += (tx - px) * 0.06; py += (ty - py) * 0.06;
    var s = clamp01((t - SHOW_AT) / SHOW_DUR), f = easeInOut(clamp01((t - FLAT_AT) / FLAT_DUR));
    var ex = Math.sin(s * P);  // 炸開程度：0 → 1 → 0

    meshes.forEach(function (m, i) {
      var k = clamp01((t - 0.05 - i * IN_DELAY) / IN_DUR), e = easeOutBack(k), h = m.userData.home;
      m.visible = k > 0;
      m.scale.set(Math.max(e, 0.001), Math.max(e, 0.001), Math.max(e, 0.001) * lerp(1, 0.02, f));
      var fly = 1 - e;  // 飛入進度剩餘量
      var spread = 1 + 0.45 * ex;
      m.position.set(
        h.x * spread + FROM[i][0] * fly,
        h.y * spread + FROM[i][1] * fly,
        FROM[i][2] * fly + (i % 2 ? 1 : -1) * 2.2 * ex + Math.sin(t * 2 + i * 0.9) * 0.25 * (1 - f) * k);
      m.rotation.x = SPIN[i][0] * fly + Math.sin(s * P * 2 + i) * 0.6 * ex;
      m.rotation.y = SPIN[i][1] * fly + Math.cos(s * P * 2 + i * 1.3) * 0.8 * ex;
    });

    // 整體：炸開時轉一圈（2π 等於回到原位），壓平時指標視差與傾斜一起收回 0
    group.rotation.y = easeInOut(s) * 2 * P + px * 0.5 * (1 - f);
    group.rotation.x = (py * 0.35 - 0.12) * (1 - f) + Math.sin(s * P) * 0.25;

    // 光線與材質慢慢變成「平面上色」，壓平後看起來和 CSS 方塊一樣
    ambient.intensity = lerp(0.75, 1, f); key.intensity = lerp(0.9, 0, f); rim.intensity = lerp(0.35, 0, f);
    mats.forEach(function (mat) { mat.metalness = lerp(0.1, 0, f); });

    renderer.render(scene, camera);

    if (t < END_AT) { requestAnimationFrame(frame); return; }
    if (!swapped) {
      swapped = true;
      tiles.style.visibility = "visible";  // 位置與大小和壓平後的 3D 一致，淡出 canvas 就看不出換了
      canvas.style.transition = "opacity " + FADE + "s";
      canvas.style.opacity = "0";
      requestAnimationFrame(frame);
      return;
    }
    if (t < END_AT + FADE + 0.1) { requestAnimationFrame(frame); return; }
    canvas.hidden = true;
    renderer.dispose();
  }

  // CSS 方塊留在原位（版面不會跳動）但先藏起來，canvas 疊在它上面
  tiles.style.visibility = "hidden";
  canvas.hidden = false;
  requestAnimationFrame(frame);
})();
