// Demo 錄影用：假游標、點擊波紋、逐字打字、底部字幕。
// run_demo.py 用 add_init_script 注入，每次換頁都會重新載入；速度由 window.DEMO_SPEED 控制。
(function () {
  if (window.demo) return;
  if (window.top !== window.self) { // 裝置預覽的 iframe 裡不放游標和字幕，由外層頁面操作；只藏記憶體模式橫幅
    const hide = () => document.querySelectorAll('.mem-banner').forEach(b => (b.style.display = 'none'));
    if (document.body) hide(); else document.addEventListener('DOMContentLoaded', hide);
    return;
  }
  const SPEED = window.DEMO_SPEED || 1;
  const sleep = ms => new Promise(r => setTimeout(r, ms / SPEED));
  const ease = t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  let c, cap, x, y;
  const HOT = [5, 2]; // 游標的點擊點：箭頭尖端

  function mount() {
    document.querySelectorAll('.mem-banner').forEach(b => (b.style.display = 'none'));
    // 字幕字體：Noto Sans TC（登入頁、老師端不一定有載入，這裡補上）
    const font = document.createElement('link');
    font.rel = 'stylesheet';
    font.href = 'https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@700&display=swap';
    document.head.appendChild(font);
    c = document.createElement('div');
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2l15 11.5-6.6.9 3.9 7.6-2.9 1.4-3.8-7.6L4 20.5z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>'; // 黑色箭頭游標
    c.popover = 'manual'; // 放進瀏覽器的最上層（top layer），彈出的 <dialog> 也蓋不住
    Object.assign(c.style, { position: 'fixed', inset: 'auto', left: '0', top: '0', margin: '0', padding: '0', border: '0', background: 'transparent', overflow: 'visible', zIndex: 2147483647, pointerEvents: 'none', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.35))' });
    cap = document.createElement('div');
    cap.popover = 'manual';
    Object.assign(cap.style, {
      position: 'fixed', inset: 'auto', left: '50%', bottom: '36px', margin: '0', border: '0', transform: 'translateX(-50%)', zIndex: 2147483647, pointerEvents: 'none',
      background: 'rgba(0,0,0,.5)', color: '#fff', padding: '16px 30px', borderRadius: '20px',
      font: '700 30px "Noto Sans TC",sans-serif', maxWidth: '90vw', textAlign: 'center', lineHeight: '1.45',
      textShadow: '0 1px 3px rgba(0,0,0,.6)',
      transition: 'opacity .3s', opacity: '0',
    });
    document.body.appendChild(cap);
    document.body.appendChild(c); // 游標最後加入，永遠在字幕上面
    raise();
    // 頁面打開 <dialog> 時，把字幕和游標重新拉到最上層
    new MutationObserver(raise).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['open'] });
    const st = document.createElement('style');
    st.textContent = '@keyframes demoRip{from{transform:translate(-50%,-50%) scale(.2);opacity:.9}to{transform:translate(-50%,-50%) scale(1);opacity:0}}';
    document.head.appendChild(st);
    let p = null;
    try { p = JSON.parse(sessionStorage.demoPos || 'null'); } catch (e) {}
    [x, y] = p || [innerWidth * .6, innerHeight * .4];
    c.style.transform = `translate(${x - HOT[0]}px,${y - HOT[1]}px)`;
  }

  // top layer 裡後顯示的在上面：先字幕、再游標
  function raise() {
    for (const el of [cap, c]) { if (!el) continue; try { if (el.matches(':popover-open')) el.hidePopover(); el.showPopover(); } catch (e) {} }
  }

  async function moveTo(tx, ty, ms = 750) {
    const sx = x, sy = y, t0 = performance.now(), dur = ms / SPEED;
    for (;;) {
      const t = Math.min(1, (performance.now() - t0) / dur), e = ease(t);
      x = sx + (tx - sx) * e; y = sy + (ty - sy) * e - Math.sin(Math.PI * t) * 30;
      c.style.transform = `translate(${x - HOT[0]}px,${y - HOT[1]}px)`;
      if (t >= 1) break;
      await new Promise(r => setTimeout(r, 16));
    }
    try { sessionStorage.demoPos = JSON.stringify([x, y]); } catch (e) {}
  }

  // "選擇器" 或 "text:選擇器|文字"（找第一個看得到、文字包含「文字」的元素）
  // 前面加 "frame:" 代表找裝置預覽 iframe 裡面的元素
  function $q(el) {
    if (typeof el !== 'string') return el;
    let doc = document;
    if (el.startsWith('frame:')) {
      const f = document.querySelector('.phone-view iframe');
      doc = f && f.contentDocument; el = el.slice(6);
      if (!doc || !doc.body) return null;
    }
    if (el.startsWith('text:')) {
      const [sel, txt] = el.slice(5).split('|');
      return [...doc.querySelectorAll(sel)].find(e => e.offsetParent && e.textContent.trim().includes(txt)) || null;
    }
    return doc.querySelector(el);
  }

  // 元素在外層畫面上的位置（iframe 裡的元素要加上 iframe 的位置和縮放）
  function rectOf(node) {
    const r = node.getBoundingClientRect();
    if (node.ownerDocument === document) return r;
    const f = [...document.querySelectorAll('iframe')].find(f => f.contentDocument === node.ownerDocument);
    const fr = f.getBoundingClientRect(), k = fr.width / (f.clientWidth || fr.width);
    return { left: fr.left + r.left * k, top: fr.top + r.top * k, width: r.width * k, height: r.height * k, bottom: fr.top + r.bottom * k };
  }

  async function to(el) {
    const node = typeof el === 'string' ? await until(() => $q(el), 3000) : el; // 等元素出現（對話框動畫等）
    if (!node) throw new Error('demo: 找不到 ' + el);
    const r0 = node.getBoundingClientRect(), vh = node.ownerDocument.defaultView.innerHeight;
    const inFrame = node.ownerDocument !== document;
    if (r0.top < (inFrame ? 0 : 70) || r0.bottom > vh - (inFrame ? 0 : 130)) { node.scrollIntoView({ behavior: 'smooth', block: 'center' }); await sleep(800); }
    const r = rectOf(node);
    await moveTo(r.left + Math.min(r.width / 2, 60), r.top + r.height / 2);
    return node;
  }

  function ripple() {
    const d = document.createElement('div');
    Object.assign(d.style, { position: 'fixed', left: x + 'px', top: y + 'px', width: '46px', height: '46px', borderRadius: '50%', background: 'rgba(26,115,232,.45)', zIndex: 2147483646, pointerEvents: 'none', animation: `demoRip ${.5 / SPEED}s ease-out forwards` });
    d.popover = 'manual'; Object.assign(d.style, { inset: 'auto', margin: '0', border: '0', padding: '0' });
    document.body.appendChild(d); try { d.showPopover(); } catch (e) {} raise();
    setTimeout(() => d.remove(), 600);
  }

  // 音效：全部用 Web Audio 現場合成，不需要音效檔
  // tick＝點擊、key＝打字、whoosh／whooshOut＝特寫放大／縮回、ding＝成功、buzz＝被擋下
  let audio = null;
  function ac() { audio = audio || new AudioContext(); return audio; }
  function noise(sec) {
    const a = ac(), len = Math.floor(a.sampleRate * sec), buf = a.createBuffer(1, len, a.sampleRate), ch = buf.getChannelData(0);
    for (let i = 0; i < len; i++) ch[i] = Math.random() * 2 - 1;
    const src = a.createBufferSource(); src.buffer = buf; return src;
  }
  function tone(type, f0, f1, at, dur, vol) {
    const a = ac(), o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.setValueAtTime(f0, at); if (f1) o.frequency.exponentialRampToValueAtTime(f1, at + dur);
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + .01); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g).connect(a.destination); o.start(at); o.stop(at + dur + .02);
  }
  function burst(sec, freq, q, vol, curve = 6) {
    const a = ac(), t = a.currentTime, src = noise(sec), bp = a.createBiquadFilter(), g = a.createGain();
    bp.type = 'bandpass'; bp.frequency.value = freq; bp.Q.value = q;
    const len = 64, env = new Float32Array(len); for (let i = 0; i < len; i++) env[i] = vol * Math.pow(1 - i / (len - 1), curve) + 0.0001;
    g.gain.setValueCurveAtTime(env, t, sec);
    src.connect(bp).connect(g).connect(a.destination); src.start(t);
  }
  function whoosh(up, vol) {
    const a = ac(), t = a.currentTime, dur = .55 / Math.max(1, SPEED / 2), src = noise(dur), bp = a.createBiquadFilter(), g = a.createGain();
    bp.type = 'bandpass'; bp.Q.value = .9;
    bp.frequency.setValueAtTime(up ? 300 : 2400, t); bp.frequency.exponentialRampToValueAtTime(up ? 2600 : 300, t + dur);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + dur * .55); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(bp).connect(g).connect(a.destination); src.start(t);
  }
  const SFX = {
    tick: () => burst(.03, 2600, 1.2, .9),
    key: () => burst(.02, 3800 + Math.random() * 800, 2, .25, 8),
    whoosh: () => whoosh(true, .55),
    whooshOut: () => whoosh(false, .3),
    ding: () => { const t = ac().currentTime; tone('sine', 880, 0, t, .35, .25); tone('sine', 1318.5, 0, t + .09, .5, .22); },
    buzz: () => { const t = ac().currentTime; tone('square', 150, 110, t, .22, .12); tone('square', 150, 110, t + .26, .22, .12); },
  };
  function sfx(name) { try { SFX[name](); } catch (e) {} }
  const tick = () => sfx('tick');
  async function click(el) { const n = await to(el); await sleep(180); ripple(); tick(); await sleep(120); n.click(); await sleep(600); return n; }
  async function press(el) { await to(el); await sleep(180); ripple(); tick(); await sleep(120); } // 只做動畫，真正的點擊交給 Playwright（會換頁的按鈕）

  // 打字前重新抓一次元素，避免頁面自動更新換掉輸入框
  async function type(sel, text, ms = 85) {
    await click(sel);
    const n = $q(sel); n.focus();
    for (const ch of text) { n.value += ch; n.dispatchEvent(new Event('input', { bubbles: true })); sfx('key'); await sleep(ms); }
    await sleep(400);
    return n;
  }
  async function clear(sel) { const n = $q(sel); while (n.value) { n.value = n.value.slice(0, -1); n.dispatchEvent(new Event('input', { bubbles: true })); await sleep(50); } }
  async function choose(sel, match) { // 下拉選單：游標移過去，選文字包含 match 的選項
    const s = await to(sel); await sleep(300);
    const o = [...s.options].find(o => o.textContent.includes(match));
    if (!o) throw new Error('demo: 選單沒有 ' + match);
    s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })); await sleep(700);
  }
  // 重點特寫：把目標移到畫面中間並放大，四周變暗、目標加外框；字幕講完再縮回來
  // el 可以是選擇器、元素，或回傳元素的函式（清單會重畫時用函式，每次重新找）
  async function spot(el, text, ms = 3000, zoom = 1.6) {
    const get = () => (typeof el === 'function' ? el() : typeof el === 'string' ? $q(el) : el);
    let node = await until(get, 3000);
    if (!node) throw new Error('demo: 找不到 ' + el);
    if (node.ownerDocument !== document) { await to(node); return say(text, ms); } // iframe 裡的元素不放大
    await to(node);
    node = get() || node;
    if (!node.isConnected) return say(text, ms);
    let box = node; while (box.parentElement && box.parentElement !== document.body) box = box.parentElement;
    const r = node.getBoundingClientRect(), b = box.getBoundingClientRect();
    const k = Math.max(1, Math.min(zoom, (innerWidth * .8) / r.width, (innerHeight * .55) / r.height));
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const dur = .6 / SPEED;
    Object.assign(box.style, { transformOrigin: `${cx - b.left}px ${cy - b.top}px`, transition: `transform ${dur}s cubic-bezier(.2,.8,.2,1)`, willChange: 'transform' });
    sfx('whoosh');
    box.style.transform = `translate(${innerWidth / 2 - cx}px,${innerHeight * .42 - cy}px) scale(${k})`;
    const tx = innerWidth / 2, ty = innerHeight * .42, w = r.width * k + 24, h = r.height * k + 24;
    const ring = document.createElement('div');
    ring.popover = 'manual';
    Object.assign(ring.style, { position: 'fixed', inset: 'auto', margin: '0', padding: '0', border: '0', background: 'transparent', pointerEvents: 'none',
      left: tx - w / 2 + 'px', top: ty - h / 2 + 'px', width: w + 'px', height: h + 'px', borderRadius: '18px',
      boxShadow: '0 0 0 4px rgba(255,255,255,.95), 0 0 0 200vmax rgba(10,14,22,.55)', opacity: '0', transition: `opacity ${dur}s` });
    document.body.appendChild(ring); try { ring.showPopover(); } catch (e) {} raise();
    moveTo(tx + w / 2 - 10, ty + h / 2 - 6, 600);
    await sleep(80); ring.style.opacity = '1';
    await sleep(650);
    await say(text, ms);
    sfx('whooshOut'); ring.style.opacity = '0'; box.style.transform = '';
    await sleep(650);
    ring.remove(); box.style.willChange = ''; box.style.transition = '';
  }

  // 字幕位置：預設在底部置中；手機預覽時改放到手機外框左邊，才不會遮住底部導覽列
  function capAt(where) {
    const ph = where === 'phone' && document.querySelector('.phone-view .phone');
    if (ph) {
      const r = ph.getBoundingClientRect();
      Object.assign(cap.style, { left: 'auto', right: (innerWidth - r.left + 48) + 'px', bottom: 'auto', top: '50%',
        transform: 'translateY(-50%)', maxWidth: Math.max(320, r.left - 96) + 'px', textAlign: 'left' });
    } else {
      Object.assign(cap.style, { left: '50%', right: 'auto', bottom: '36px', top: 'auto',
        transform: 'translateX(-50%)', maxWidth: '90vw', textAlign: 'center' });
    }
  }
  async function say(t, ms = 2200) { cap.innerHTML = t; cap.style.opacity = '1'; await sleep(ms); }
  function hush() { cap.style.opacity = '0'; }
  async function until(fn, ms = 30000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await new Promise(r => setTimeout(r, 250)); } return null; }
  async function top() { window.scrollTo({ top: 0, behavior: 'smooth' }); await sleep(900); }
  function credits() { return +(document.body.innerText.match(/本學期學分\s*(\d+)/) || [])[1]; }

  // 課程卡片：用課名找 #list 裡的 article.course
  function course(name) { return [...document.querySelectorAll('#list .course')].find(a => a.innerText.split('\n').some(l => l.trim() === name)) || null; }
  function courseBtn(name, re = /^(登記|加選)$/) { const a = course(name); return a && [...a.querySelectorAll('button')].find(b => re.test(b.textContent.trim())); }
  function block(name) { return [...document.querySelectorAll('#tt .blk')].find(b => b.textContent.includes(name)) || null; }

  window.demo = { sfx, spot, capAt, moveTo, to, click, press, type, clear, choose, say, hush, sleep, until, top, credits, course, courseBtn, block, $q };
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
