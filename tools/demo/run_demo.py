"""自動跑一次完整 Demo（依「十分鐘簡報分工」的組員 2～6 流程），可錄成影片。

用法（在專案根目錄）：
    uv run --no-project --with playwright python tools/demo/run_demo.py            # 1 倍速，開視窗給你看
    uv run --no-project --with playwright python tools/demo/run_demo.py --speed 3  # 3 倍速
    uv run --no-project --with playwright python tools/demo/run_demo.py --record   # 另存影片到 tools/demo/out/
第一次使用前先裝瀏覽器：uv run --no-project --with playwright playwright install chromium

腳本會自己用 STORE=memory 啟動一個 Django（預設 8030 埠），資料每次都是全新的，不會寫進正式 Firestore。
登入用 DEBUG 才有的「本機測試登入」：學生 11446001、老師蒯思齊。AI 那段會真的呼叫 OpenAI（需要 django_app/.env 的金鑰）。
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DJANGO = ROOT / "django_app"
HERE = Path(__file__).resolve().parent
LIB = (HERE / "demo_lib.js").read_text(encoding="utf-8")
STUDENT = "11446001@ntub.edu.tw"
TEACHER = "sckuai@ntub.edu.tw"

# ---------- 每一段的瀏覽器動作（在頁面裡執行，回傳一行紀錄） ----------

SEG_OPEN = """async () => { const d = demo;
  await d.say('開場：git clone → start.bat → 網站自動開好', 3500);
  await d.say('登入與找課：只收 @ntub.edu.tw 學校帳號', 2600);
  await d.to('text:button|使用 Google'); await d.sleep(900);
  await d.say('Demo 用本機測試登入（學生 11446001）', 1800);
  await d.press('[data-dev="%s"]'); return 'open';
}""" % STUDENT

SEG_FIND = """async () => { const d = demo, log = [];
  await d.sleep(600);
  await d.to('#who'); await d.say('學號 11446001 → 114 入學・四技資管・大二，系統自動判斷', 3200);
  await d.to('#doneLine'); await d.say('本班必修已自動帶入課表，不需要可以自己退', 3000);
  await d.type('#q', '程式'); await d.say('搜尋課名、老師或課號', 1800);
  await d.click('#noClash'); await d.say('勾「只看不衝堂」，衝堂的課直接隱藏', 2600);
  await d.clear('#q'); await d.click('#noClash');
  await d.choose('#deptSel', '財務金融'); await d.say('切到外系（財金系）看課，你的選課和必修不會變', 3000);
  await d.choose('#deptSel', '資訊管理'); log.push('dept');
  return 'find ' + log + ' cr=' + d.credits();
}"""

SEG_PLAN = """async () => { const d = demo, log = [];
  await d.say('排課與檢查', 2000);
  await d.type('#q', '網站應用程式設計'); await d.sleep(500);
  await d.click(d.courseBtn('網站應用程式設計')); await d.say('加選成功，右下角提示目前名額', 2600); log.push('add');
  await d.clear('#q'); await d.type('#q', '程式設計(一)'); await d.sleep(500);
  const b = d.courseBtn('程式設計(一)'); await d.to(b); await d.say('這門課跟「資料結構」衝堂', 2200);
  await d.click(b); await d.say('系統直接擋下，並說明衝堂的是哪一門', 2800); log.push('clash');
  await d.clear('#q'); await d.sleep(300);
  await d.click('#tt .cell[data-slot="3,6"]'); await d.say('點課表的空堂（週三第 6 節）→ 清單只剩這個時段能選的課', 3200);
  await d.click('text:#chips button|時段'); log.push('slot');
  await d.click(d.block('網站應用程式設計')); await d.say('點課表上已選的課 → 保留、安全換課或退選', 2600);
  await d.click('text:#ttDlg button|退選'); log.push('drop');
  return 'plan ' + log + ' cr=' + d.credits();
}"""

SEG_CREDIT = """async () => { const d = demo, log = [];
  await d.top(); await d.say('學分與換課', 2000);
  await d.to('#summary'); await d.say('本學期學分：下限 9、上限 25，即時顯示「可再選幾學分」', 3200);
  const ph = d.$q('text:#summary *|階段一'); if (ph) { await d.to(ph); await d.say('選課階段：登記中可超額，截止後抽籤；加退選時剩餘名額先搶先贏', 3500); }
  const basic = d.$q('#basic summary') || d.$q('#basic');
  if (basic) { await d.click(basic); await d.say('選課基本資料：各類可加選的科目數', 2800); await d.click(basic); log.push('basic'); }
  await d.click(d.block('資料結構')); await d.click('text:#ttDlg button|安全換課');
  await d.say('安全換課：只列出時段相同、不衝堂、還有名額的替代課', 3000);
  await d.choose('#swapPick', '程式設計(一)');
  await d.to('#swapPreview'); await d.say('確認前先算好換課後的學分，必修也會另外提醒', 3000);
  await d.to('#swapConfirm'); await d.say('換成功前原本的課不會被退掉，不會兩頭落空', 2800);
  await d.click('#swapConfirm'); await d.sleep(1200); log.push('swap');
  return 'credit ' + log + ' blocks=' + [...document.querySelectorAll('#tt .blk b')].map(b => b.textContent).join('/');
}"""

SEG_AI = """async () => { const d = demo;
  await d.say('AI 選課建議', 2000);
  await d.click('#aiFab'); await d.sleep(600);
  await d.to('#aiDept'); await d.say('學系維持「自動判斷」，用平常講話的方式描述', 2600);
  await d.type('#aiText', '我想修財務相關的課，週二和週五不想排課', 100);
  for (let i = 0; i < 2; i++) {
    await d.click('#aiGo');
    d.$q('#aiStatus').textContent = '';
    await d.say('第一步：AI 判斷相關學系… 第二步：挑出不衝堂的課', 300);
    const r = await d.until(() => d.$q('#aiAll') || (/沒拿到|失敗|稍後|錯誤/.test(d.$q('#aiStatus').textContent) && 'fail'), 60000);
    if (r && r !== 'fail') break;
  }
  if (!d.$q('#aiAll')) return 'ai FAILED: ' + d.$q('#aiStatus').textContent;
  await d.to('#aiOut'); await d.say('AI 推薦 3–6 門課，每門附理由，而且彼此不衝堂', 3200);
  await d.click('#aiAll'); await d.say('按「全部加入」，課直接排進課表', 2600);
  await d.click('#aiClose'); await d.to('#tt'); await d.say('回到課表：新課已排進去', 2200);
  await d.top(); await d.click('#palBtn');
  await d.click('text:#langSeg button|English'); await d.say('切換英文：整個介面變英文，交換生也能用', 2600);
  await d.click('text:#langSeg button|中文');
  const th = document.querySelectorAll('#themeSeg button'); await d.click(th[th.length - 1]); await d.say('深色模式', 1800);
  const sw = [...document.querySelectorAll('#swatches button')]; await d.click(sw[sw.length - 1]); await d.say('主題色（含彩色主題）', 2000);
  await d.click(th[1]); await d.click(sw[0]); await d.click('#palBtn');
  return 'ai ok cr=' + d.credits();
}"""

SEG_APPLY = """async () => { const d = demo;
  // 「虛擬化技術」在週二 2–4 節；若 AI 剛好排了同時段的課，先退掉，老師核准時才不會衝堂
  const clash = [...document.querySelectorAll('#tt .blk')].filter(b => {
    const col = parseInt(b.style.gridColumn), [r1, r2] = b.style.gridRow.split('/').map(n => parseInt(n));
    return col === 3 && r1 <= 5 && (r2 || r1 + 1) > 3;   // 週二、和第 2–4 節重疊
  }).map(b => b.querySelector('b').textContent);
  for (const name of clash) { await d.click(d.block(name)); await d.click('text:#ttDlg button|退選'); }
  await d.top(); await d.say('特殊申請與老師端', 2200);
  const panel = d.$q('#applicationPanel'); await d.click(panel.querySelector('summary') || panel);
  await d.choose('#applicationCourse', '虛擬化技術'); await d.say('選一門四年級的課「虛擬化技術」（蒯思齊老師）', 2800);
  await d.to('#applicationKind'); await d.say('三種申請：加簽、跨系選修、豁免先修', 2600);
  const k = d.$q('#applicationKind'); k.value = 'add'; k.dispatchEvent(new Event('change', { bubbles: true }));
  await d.type('#applicationReason', '想提早修虛擬化技術，準備雲端相關的專題', 90);
  await d.click('#applicationSubmit'); await d.sleep(1200);
  await d.to('#applicationHistory'); await d.say('送出後狀態顯示「審核中」', 2600);
  await d.top(); await d.say('切換到老師端：登出 → 用老師帳號登入', 2000);
  await d.press('#logoutBtn');
  return 'apply ' + d.$q('#applicationMessage').innerText;
}"""

SEG_LOGIN_TEACHER = """async () => { const d = demo;
  await d.say('老師帳號登入（本機測試：蒯思齊）', 1600);
  await d.press('[data-dev="%s"]'); return 'teacher login';
}""" % TEACHER

SEG_TEACHER = """async () => { const d = demo;
  await d.sleep(500);
  await d.say('老師端：只看得到自己開的課和這些課的申請', 2600);
  const c = d.$q('text:h2,h3,b,strong|資訊網路'); if (c) { await d.to(c); await d.say('每門課的修課學生（學號、班級、信箱）', 2800); }
  const csv = d.$q('text:a,button|匯出全部名單'); if (csv) { await d.to(csv); await d.say('可匯出 CSV，Excel 直接開', 2400); }
  await d.top();
  await d.type('textarea[id^="review-note-"]', '同意加簽，請注意先修內容', 90);
  await d.click('[data-decision="approve"]'); await d.sleep(1500);
  await d.say('按「通過並加入課表」→ 學生的課表直接出現這門課', 2800);
  await d.top(); await d.say('切回學生帳號看結果', 1600);
  await d.press('#logout');
  return 'review ' + (document.body.innerText.match(/教師回覆：[^\\n]*/) || [''])[0];
}"""

SEG_LOGIN_STUDENT = """async () => { const d = demo; await d.press('[data-dev="%s"]'); return 'student login'; }""" % STUDENT

SEG_RESULT = """async () => { const d = demo;
  await d.sleep(600);
  const b = d.block('虛擬化'); if (b) { await d.to(b); await d.say('課表已出現「虛擬化技術」，標示「申請通過」', 3200); }
  await d.top(); await d.say('最後看手機版：登入頁右下角的「預覽裝置」按鈕', 2400);
  await d.press('#logoutBtn');
  return 'result approved=' + !!(b && /申請通過/.test(b.innerText));
}"""

SEG_MOBILE = """async () => { const d = demo;
  await d.until(() => d.$q('#card:not([hidden])'), 5000); await d.sleep(500);
  await d.click('#devbtn'); await d.say('右下角浮動按鈕：選擇預覽裝置（iPhone、Android、iPad）', 2600);
  await d.click('text:#devmenu button|iPhone 16'); d.$q('#devmenu').hidden = true;
  const login = await d.until(() => { const n = d.$q('frame:[data-dev="%s"]'); return n && n.offsetParent && n; }, 15000);
  await d.say('手機和平板版面相同，同一個網址直接切換', 2400);
  await d.click(login);
  const nav = await d.until(() => { const n = d.$q('frame:.mnav [data-mv="table"]'); return n && n.offsetParent && n; }, 15000);
  await d.sleep(800); await d.say('手機版：底部導覽列切換「課程／課表／進度」', 2600);
  await d.click(nav); await d.say('課表', 1800);
  await d.click('frame:.mnav [data-mv="me"]'); await d.say('學分與畢業進度', 1800);
  await d.click('frame:.mnav [data-mv="list"]'); await d.say('課程清單', 1600);
  await d.say('結語：一個畫面選完課；衝堂、學分、換課先幫你檢查；<br>AI 與線上加簽解決「不知道選什麼」和「選不到」', 4500);
  d.hush(); await d.sleep(800);
  return 'mobile ok';
}""" % STUDENT


def start_server(port):
    env = {**os.environ, "STORE": "memory", "DJANGO_DEBUG": "1", "PYTHONUTF8": "1"}
    proc = subprocess.Popen(
        ["uv", "run", "python", "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=DJANGO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(120):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                sys.exit(f"Django 啟動失敗（{port} 埠可能被占用）")
            time.sleep(0.5)
    stop_server(proc)
    sys.exit("等不到 Django 啟動")


def stop_server(proc):
    if proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        else:
            proc.terminate()


def screen_size():
    """主螢幕的實際解析度（例如 2560×1440），不受 Windows 顯示縮放影響。"""
    if os.name == "nt":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
        m = ctypes.windll.user32.GetSystemMetrics
        return m(0), m(1)
    return 2560, 1440


def main():
    ap = argparse.ArgumentParser(description="自動跑一次選課系統 Demo")
    ap.add_argument("--speed", type=float, default=1, help="播放速度倍數，例如 3 = 三倍速")
    ap.add_argument("--port", type=int, default=8030)
    ap.add_argument("--record", action="store_true", help="另存影片到 tools/demo/out/")
    ap.add_argument("--size", help="改用視窗模式並指定大小，例如 1440x810；不指定就是全螢幕")
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    if args.size:
        w, h = map(int, args.size.lower().split("x"))
        launch_args = [f"--window-size={w},{h + 90}"]
        view = {"viewport": {"width": w, "height": h}}
    else:  # 全螢幕：kiosk 模式不會跳出「按 F11 結束全螢幕」的提示
        w, h = screen_size()
        # 網頁縮放用預設的 100%（跟著 Windows 的顯示設定）
        launch_args = ["--kiosk", "--start-fullscreen"]
        view = {"no_viewport": True}

    print(f"畫面大小：{w}×{h}{'（全螢幕）' if not args.size else ''}")
    print(f"啟動 Django（記憶體模式）：{base}")
    server = start_server(args.port)
    t0 = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=launch_args)
            opts = {**view, "locale": "zh-TW"}
            out = HERE / "out"
            if args.record:
                out.mkdir(exist_ok=True)
                opts.update(record_video_dir=str(out), record_video_size={"width": w, "height": h})
            ctx = browser.new_context(**opts)
            ctx.add_init_script(f"window.DEMO_SPEED={args.speed};\n{LIB}")
            page = ctx.new_page()
            page.set_default_timeout(60000)

            def run(js):
                try:
                    print(" ", page.evaluate(js), f"({time.time() - t0:.0f}s)")
                except Exception:
                    out.mkdir(exist_ok=True)
                    shot = out / "error.png"
                    page.screenshot(path=str(shot))
                    print(f"出錯了，畫面存在 {shot}")
                    raise

            def run_then_nav(js, url_part):
                # 最後一個動作是 press()：游標動畫做完，再由 Playwright 真的點下去並等換頁
                selector = js.rsplit("d.press('", 1)[1].split("')", 1)[0]
                run(js)
                with page.expect_navigation(url=lambda u: url_part in u):
                    page.click(selector)
                page.wait_for_load_state("networkidle")

            page.goto(base + "/")
            page.wait_for_load_state("networkidle")
            run_then_nav(SEG_OPEN, "/app/")
            for seg in (SEG_FIND, SEG_PLAN, SEG_CREDIT, SEG_AI):
                run(seg)
            run_then_nav(SEG_APPLY, f"{base}/")
            run_then_nav(SEG_LOGIN_TEACHER, "/teacher/")
            run_then_nav(SEG_TEACHER, f"{base}/")
            run_then_nav(SEG_LOGIN_STUDENT, "/app/")
            run_then_nav(SEG_RESULT, f"{base}/")
            run(SEG_MOBILE)

            video = page.video
            ctx.close()
            browser.close()
            if video:
                dest = out / f"demo_{time.strftime('%Y%m%d_%H%M%S')}.webm"
                shutil.move(video.path(), dest)
                print(f"影片：{dest}")
    finally:
        stop_server(server)
    print(f"完成，共 {time.time() - t0:.0f} 秒（{args.speed:g} 倍速）")


if __name__ == "__main__":
    main()
