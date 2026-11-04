// Demo 錄影用：假游標、點擊波紋、逐字打字、底部字幕。
// run_demo.py 用 add_init_script 注入，每次換頁都會重新載入；速度由 window.DEMO_SPEED 控制。
(function () {
  if (window.demo) return;
  const SPEED = window.DEMO_SPEED || 1;
  const sleep = ms => new Promise(r => setTimeout(r, ms / SPEED));
  const ease = t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  let c, cap, x, y;

  function mount() {
    document.querySelectorAll('.mem-banner').forEach(b => (b.style.display = 'none'));
    c = document.createElement('div');
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2l15 11.5-6.6.9 3.9 7.6-2.9 1.4-3.8-7.6L4 20.5z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, { position: 'fixed', left: '0', top: '0', zIndex: 2147483647, pointerEvents: 'none', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.35))' });
    document.body.appendChild(c);
    cap = document.createElement('div');
    Object.assign(cap.style, {
      position: 'fixed', left: '50%', bottom: '36px', transform: 'translateX(-50%)', zIndex: 2147483645, pointerEvents: 'none',
      background: 'rgba(20,24,32,.9)', color: '#fff', padding: '16px 30px', borderRadius: '20px',
      font: '700 30px "Noto Sans TC",system-ui,sans-serif', maxWidth: '90vw', textAlign: 'center', lineHeight: '1.45',
      transition: 'opacity .3s', opacity: '0',
    });
    document.body.appendChild(cap);
    const st = document.createElement('style');
    st.textContent = '@keyframes demoRip{from{transform:translate(-50%,-50%) scale(.2);opacity:.9}to{transform:translate(-50%,-50%) scale(1);opacity:0}}';
    document.head.appendChild(st);
    let p = null;
    try { p = JSON.parse(sessionStorage.demoPos || 'null'); } catch (e) {}
    [x, y] = p || [innerWidth * .6, innerHeight * .4];
    c.style.transform = `translate(${x}px,${y}px)`;
  }

  async function moveTo(tx, ty, ms = 750) {
    const sx = x, sy = y, t0 = performance.now(), dur = ms / SPEED;
    for (;;) {
      const t = Math.min(1, (performance.now() - t0) / dur), e = ease(t);
      x = sx + (tx - sx) * e; y = sy + (ty - sy) * e - Math.sin(Math.PI * t) * 30;
      c.style.transform = `translate(${x - 4}px,${y - 2}px)`;
      if (t >= 1) break;
      await new Promise(r => setTimeout(r, 16));
    }
    try { sessionStorage.demoPos = JSON.stringify([x, y]); } catch (e) {}
  }

  // "選擇器" 或 "text:選擇器|文字"（找第一個看得到、文字包含「文字」的元素）
  function $q(el) {
    if (typeof el !== 'string') return el;
    if (el.startsWith('text:')) {
      const [sel, txt] = el.slice(5).split('|');
      return [...document.querySelectorAll(sel)].find(e => e.offsetParent && e.textContent.trim().includes(txt)) || null;
    }
    return document.querySelector(el);
  }

  async function to(el) {
    const node = $q(el);
    if (!node) throw new Error('demo: 找不到 ' + el);
    const r0 = node.getBoundingClientRect();
    if (r0.top < 70 || r0.bottom > innerHeight - 130) { node.scrollIntoView({ behavior: 'smooth', block: 'center' }); await sleep(800); }
    const r = node.getBoundingClientRect();
    await moveTo(r.left + Math.min(r.width / 2, 60), r.top + r.height / 2);
    return node;
  }

  function ripple() {
    const d = document.createElement('div');
    Object.assign(d.style, { position: 'fixed', left: x + 'px', top: y + 'px', width: '46px', height: '46px', borderRadius: '50%', background: 'rgba(26,115,232,.45)', zIndex: 2147483646, pointerEvents: 'none', animation: `demoRip ${.5 / SPEED}s ease-out forwards` });
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 600);
  }

  async function click(el) { const n = await to(el); await sleep(180); ripple(); await sleep(120); n.click(); await sleep(600); return n; }
  async function press(el) { await to(el); await sleep(180); ripple(); await sleep(120); } // 只做動畫，真正的點擊交給 Playwright（會換頁的按鈕）

  // 打字前重新抓一次元素，避免頁面自動更新換掉輸入框
  async function type(sel, text, ms = 85) {
    await click(sel);
    const n = $q(sel); n.focus();
    for (const ch of text) { n.value += ch; n.dispatchEvent(new Event('input', { bubbles: true })); await sleep(ms); }
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
  async function say(t, ms = 2200) { cap.innerHTML = t; cap.style.opacity = '1'; await sleep(ms); }
  function hush() { cap.style.opacity = '0'; }
  async function until(fn, ms = 30000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await new Promise(r => setTimeout(r, 250)); } return null; }
  async function top() { window.scrollTo({ top: 0, behavior: 'smooth' }); await sleep(900); }
  function credits() { return +(document.body.innerText.match(/本學期學分\s*(\d+)/) || [])[1]; }

  // 課程卡片：用課名找 #list 裡的 article.course
  function course(name) { return [...document.querySelectorAll('#list .course')].find(a => a.innerText.split('\n').some(l => l.trim() === name)) || null; }
  function courseBtn(name, re = /^(登記|加選)$/) { const a = course(name); return a && [...a.querySelectorAll('button')].find(b => re.test(b.textContent.trim())); }
  function block(name) { return [...document.querySelectorAll('#tt .blk')].find(b => b.textContent.includes(name)) || null; }

  window.demo = { moveTo, to, click, press, type, clear, choose, say, hush, sleep, until, top, credits, course, courseBtn, block, $q };
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
