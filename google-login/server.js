// 選課系統：Google 學校帳號單一登入（只允許 @ntub.edu.tw）
// 啟動：GOOGLE_CLIENT_ID=xxx SESSION_SECRET=yyy node server.js
const express = require("express");
const session = require("express-session");
const { OAuth2Client } = require("google-auth-library");
const fs = require("fs");
const path = require("path");

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const SESSION_SECRET = process.env.SESSION_SECRET;
const DOMAIN = "ntub.edu.tw";
if (!CLIENT_ID || !SESSION_SECRET) {
  console.error("請先設定環境變數 GOOGLE_CLIENT_ID 與 SESSION_SECRET");
  process.exit(1);
}

const app = express();
const google = new OAuth2Client(CLIENT_ID);
app.set("trust proxy", 1);
app.use(express.json());
app.use(
  session({
    secret: SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production", // 正式環境必須是 HTTPS
      maxAge: 8 * 60 * 60 * 1000, // 8 小時
    },
  })
);

// 前端需要的 Client ID（Client ID 本來就是公開的，不是密碼）
app.get("/config.js", (req, res) => {
  res.type("js").send(`window.GOOGLE_CLIENT_ID=${JSON.stringify(CLIENT_ID)};`);
});

// 收到 Google 回傳的 ID token，在伺服器端驗證，再確認是學校帳號
app.post("/auth/google", async (req, res) => {
  try {
    const ticket = await google.verifyIdToken({ idToken: req.body.credential, audience: CLIENT_ID });
    const p = ticket.getPayload();
    const email = String(p.email || "").toLowerCase();
    // hd 是 Google Workspace 網域；三個條件都要成立，不能只看前端
    if (p.hd !== DOMAIN || !p.email_verified || !email.endsWith("@" + DOMAIN)) {
      return res.status(403).json({ error: "not_school_account", email });
    }
    req.session.regenerate((err) => {
      if (err) return res.status(500).json({ error: "session" });
      req.session.user = { sub: p.sub, email, name: p.name || "" };
      res.json({ ok: true, name: p.name || email });
    });
  } catch (e) {
    res.status(401).json({ error: "invalid_token" });
  }
});

app.post("/auth/logout", (req, res) => req.session.destroy(() => res.json({ ok: true })));

app.get("/api/me", (req, res) => {
  if (!req.session.user) return res.status(401).json({ error: "not_signed_in" });
  res.json(req.session.user);
});

// 選課系統本體只給已登入的學校帳號；檔案放在 app/，不在公開的 public/ 裡
const COURSE_HTML = fs.readFileSync(path.join(__dirname, "app", "course.html"), "utf8");
app.get("/app", (req, res) => {
  if (!req.session.user) return res.redirect("/");
  res.type("html").send(
    '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' +
      "<script>window.NTUB_SSO=true</script>" +
      "<style>body{margin:0}[hidden]{display:none!important}</style></head><body>" +
      COURSE_HTML +
      "</body></html>"
  );
});

// 已登入的人直接進選課系統
app.get("/", (req, res, next) => (req.session.user ? res.redirect("/app") : next()));
app.use(express.static(path.join(__dirname, "public"), { index: "login.html" }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`選課系統已啟動：http://localhost:${PORT}`));
