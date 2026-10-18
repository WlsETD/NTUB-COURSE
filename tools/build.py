"""產生本機預覽檔，並把最新的 course.html 同步到 google-login/app/。

用法（在專案根目錄）：python tools/build.py
- preview.html：在 course.html 外面包上 <!doctype html>，直接用瀏覽器打開就能預覽。
- google-login/app/course.html：部署版使用的副本，內容和 course.html 相同。
"""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "course.html")

HEAD = (
    '<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    "<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
)

body = open(SRC, encoding="utf8").read()
with open(os.path.join(ROOT, "preview.html"), "w", encoding="utf8", newline="\n") as f:
    f.write(HEAD.replace("<head>\n", "<head>\n<!-- 由 tools/build.py 產生，請改 course.html，不要直接改這個檔案 -->\n", 1) + body + "\n</body>\n</html>\n")

app_dir = os.path.join(ROOT, "google-login", "app")
if os.path.isdir(app_dir):
    shutil.copyfile(SRC, os.path.join(app_dir, "course.html"))
    print("已同步 google-login/app/course.html")
print("已產生 preview.html")
