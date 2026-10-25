"""Wrap the game page into a standalone website.
usage: python -I make_site.py GAME_HTML OUT_DIR [CONFIG_JS]
Copies Firebase compat libs into OUT_DIR/lib, writes index.html, firebase-config.js
(a placeholder unless CONFIG_JS is given) and database.rules.json.
"""
import sys, os, shutil

src, out = sys.argv[1], sys.argv[2]
cfg = sys.argv[3] if len(sys.argv) > 3 else None
body = open(src, encoding='utf8').read()
# split off the head part (title/meta/links/style) that the artifact skeleton used to wrap
cut = body.index('<div id="wrap">')
head, rest = body[:cut], body[cut:]
head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
page = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#08221f">
<meta name="description" content="神釣手 Best Angler 2D 高畫質重製版：線上釣魚遊戲。">
<style>html,body{{margin:0}}:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}[hidden]{{display:none!important}}</style>
{head}<script src="lib/firebase-app-compat.js"></script>
<script src="lib/firebase-auth-compat.js"></script>
<script src="lib/firebase-database-compat.js"></script>
<script src="firebase-config.js"></script>
</head>
<body>
{rest}
</body>
</html>
"""
os.makedirs(out + '/lib', exist_ok=True)
open(out + '/index.html', 'w', encoding='utf8').write(page)
for f in os.listdir('/home/claude/web_emu/lib'):
    shutil.copy('/home/claude/web_emu/lib/' + f, out + '/lib/' + f)
shutil.copy('/home/claude/fbemu/database.rules.json', out + '/database.rules.json')
if cfg:
    shutil.copy(cfg, out + '/firebase-config.js')
elif not os.path.exists(out + '/firebase-config.js'):
    open(out + '/firebase-config.js', 'w', encoding='utf8').write(
        "// 把 Firebase 主控台「專案設定 → 一般 → 你的應用程式」裡的 firebaseConfig 貼在這裡。\n"
        "// 沒有填寫時，遊戲會以單機模式執行。\n"
        "window.FIREBASE_CONFIG = {\n"
        "  apiKey: 'YOUR_API_KEY',\n"
        "  authDomain: 'YOUR_PROJECT.firebaseapp.com',\n"
        "  databaseURL: 'https://YOUR_PROJECT-default-rtdb.asia-southeast1.firebasedatabase.app',\n"
        "  projectId: 'YOUR_PROJECT',\n"
        "  appId: 'YOUR_APP_ID',\n"
        "};\n")
open(out + '/.nojekyll', 'w').write('')
print('site written', out)
