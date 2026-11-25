"""Stamp the site's index.html with a build id and write version.json (the page reloads itself once when a browser
served it an older cached copy).  python3 -I stamp_build.py SITE_DIR"""
import sys, hashlib, json
d = sys.argv[1].rstrip('/') + '/'
h = open(d + 'index.html', encoding='utf8').read()
b = hashlib.md5((h + open(d + 'assets.json', encoding='utf8').read()).encode()).hexdigest()[:10]
assert "const BUILD = '__BUILD__'" in h
open(d + 'index.html', 'w', encoding='utf8').write(h.replace("const BUILD = '__BUILD__'", f"const BUILD = '{b}'"))
json.dump({'build': b}, open(d + 'version.json', 'w'))
print('build', b)
