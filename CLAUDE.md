# 北商選課系統

國立臺北商業大學 115-1 四技日間部的選課系統前端原型。整個系統是一個單檔 HTML：`course.html`（CSS、JS、字型、課程資料都內嵌在裡面）。介面文字以繁體中文為主，另有英文版。

## 檔案

| 路徑 | 說明 |
|---|---|
| `course.html` | **主程式，修改都改這個檔案。** 沒有 `<!doctype>`、`<html>`、`<head>`、`<body>`，因為它發布成 claude.ai Artifact 時會自動包上外框 |
| `preview.html` | 本機預覽用，由 `tools/build.py` 產生，不要直接改 |
| `data/ntub_115-1.txt` | 課程原始資料（748 筆，北商全校課程查詢 2026/10/08 擷取） |
| `tools/build_data.py` | 把 `data/ntub_115-1.txt` 轉成 `course.html` 裡的 `var RAW=[...]` |
| `tools/build.py` | 產生 `preview.html`，並把 `course.html` 複製到 `google-login/app/` |
| `django_app/` | **Django + Firebase + OpenAI 版本**（登入、存選課、AI 建議）。有自己的 README 與 CLAUDE.md；前端在 `courses/static/courses/app.js`，和 `course.html` 分開維護 |
| `google-login/` | 可部署版本：Express + Google 學校帳號登入（只收 @ntub.edu.tw），說明見其 README |
| `AI選課建議功能.md` | AI 選課建議的功能規格 |

## 常用指令

```bash
python tools/build.py        # 改完 course.html 後執行：更新 preview.html 與部署副本
python tools/build_data.py   # 改了 data/ntub_115-1.txt 後執行：重建課程資料
```

預覽：用瀏覽器開 `preview.html`。
JS 語法檢查：把 `<script>` 內容抽出來跑 `node --check`。

## course.html 的結構

依序是：

1. `<title>`、Google Fonts（Noto Sans TC）連結
2. `<style>`：開頭是內嵌的俐方體 11 號（Cubic 11）`@font-face`（base64，很長，搜尋時避開），接著是全部 CSS
3. HTML：登入閘門 `#gate` → 主畫面 `.wrap`（header、`#view-enroll`）→ `#toast` → 手機底部導覽 `nav.mnav` → AI 浮動按鈕 `#aiFab` 與面板 `#ai`
4. `<script>`：整段包在一個 IIFE 裡

### JS 主要區塊（依出現順序）

- **資料**：`RAW`（每筆 `[id,學系,src,班級,年級,課號,課名,老師,slots,教室,學分,名額,已選,課別,cat,icon]`，這一行很長）→ `COURSES`、`byId`
  - `src`：`dept` 本系課、`ge` 通識、`pe` 體育、`mil` 軍訓
  - `slots`：`[[星期, 起始節, 結束節], ...]`
  - `cat`：`req` 必修、`ele` 選修、`ge` 通識必修
- **圖示與學系**：`ICONS`、`icon()`、`colIdx()`、`DEPTS`、`DEPT_ZH`、`DEPTCOL`
- **多語系**：`STR={zh:{...},en:{...}}`、`t(key,...)`（`{0}` 佔位）、`tr()` 是 `t` 的別名。HTML 上用 `data-i18n`、`data-i18n-ph`、`data-i18n-aria`，由 `applyStatic()` 套用
- **狀態**：`var state={major,grade,cls,sel,auto,src,q,aiFilter,phase,...}`
- **規則**：`MIN=9`、`MAX=25`（超出 25 學分可以選但不計）、`forGrade()`（高年級可修低年級的本系課）、`autoReq()`（自動帶入本班必修）、`check()`（衝堂等檢查）、`countMap()`
- **動作**：`add()`、`drop()`、`setGrade()`、`resetFor()`（切換學系／年級／班級時重設，並提供「復原」）
- **畫面**：`render()` 依序呼叫 `renderAI`、`renderGrades`、`renderLottery`、`renderSummary`（學分＋畢業進度＋`basicPanel` 選課基本資料）、`renderChips`、`renderList`、`renderTT`（課表）
- **AI 選課建議**：`ai`、`aiCandidates`、`renderAI`、`aiOpen`。使用 claude.ai Artifact 的 `sample` 能力（`claude.use("sample")`），在 claude.ai 以外會自動隱藏
- **設定**：`ACCENTS`（主題色，含 `rainbow` 彩色）、`applyAccent()`、`THEMES`（系統／淺色／深色）、`applyFont()`（C = 俐方體、N = Noto）、語言切換
- **登入**：`gateText`、`showLogin`（片頭 2.6 秒後顯示登入卡）、`enterApp`、`setAcct`、`logout`。部署版會設定 `window.NTUB_SSO=true`，此時跳過預覽用的登入畫面

## 修改時的規則

- **新增文字一定要中英兩份**：同時加到 `STR.zh` 和 `STR.en`，不要把中文寫死在 JS 裡。
- **顏色只用 CSS 變數**（`--accent`、`--surface`、`--fg`、`--muted` 等），淺色與深色都要能看。深色模式定義在 `@media (prefers-color-scheme:dark)` 的 `:root:not([data-theme="light"])` 以及 `:root[data-theme="dark"]`。
- 不要用 1px 邊框；介面元素要跟著主題色變化。彩色主題不要用漸層，一個物件只用一種顏色（Google 色：藍 #1a73e8、紅 #d93025、黃 #f9ab00、綠 #188038）。
- **手機和平板版面相同**，媒體查詢統一用：`@media (max-width:720px), (max-width:1366px) and (pointer:coarse)`。桌機課表固定在側邊用 `(min-width:961px) and (pointer:fine)`。
- 外部資源只能用 Google Fonts，其他都要內嵌（claude.ai Artifact 的限制）。
- `localStorage`／`sessionStorage` 的讀寫都要包在 `try/catch` 裡。
- 改完記得執行 `python tools/build.py`。

## 已知限制

- 「已修學分」是範例數字（`EARNED`），沒有接學校的成績資料。
- 加選、退選不會寫回學校系統；名額與已選人數是 2026/10/08 的快照。
- `runLottery`、`leaveWait` 等抽籤與候補的程式碼目前沒有入口（抽籤是學校端的工作）。
