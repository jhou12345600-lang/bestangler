"""Re-render only boy-catch.png (+ boy.json 'catch') with final.py's CATCH_POSE."""
import json, re
src = open('/home/claude/char3d/final.py').read()
head = src.split('with sync_playwright() as p:')[0]
exec(head)
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); pg = b.new_page()
    pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
    pg.evaluate('o => setup(o)', {'model': MODEL, 'prefix': PREFIX})
    pg.evaluate('resetPose()'); pg.evaluate('p => pose(p)', CATCH_POSE); pg.evaluate('gripInFist(.5, .2, .15)')
    FW, FH = 900, 1500
    im = grade(shot(pg, {'w': FW, 'h': FH, 'az': 8, 'el': 4, 'dist': 1000, 'fov': 13.5, 'ty': .5}))
    tip = pg.evaluate(f'objScreen(R.gripTip, {FW}, {FH})')
    bb = im.getchannel('A').getbbox(); im = im.crop(bb); im.save(OUT + 'boy-catch.png')
    meta = json.load(open(OUT + 'boy.json'))
    meta['catch'] = {'tip': [round(tip[0] - bb[0], 1), round(tip[1] - bb[1], 1)], 'size': list(im.size)}
    json.dump(meta, open(OUT + 'boy.json', 'w'), indent=1); print(meta['catch'])
    b.close()
