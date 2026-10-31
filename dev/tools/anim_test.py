from playwright.sync_api import sync_playwright
import sys
CH = sys.argv[1] if len(sys.argv) > 1 else 'g'
ROD = sys.argv[2] if len(sys.argv) > 2 else '15feet'
OUT = f'/home/claude/shots/v7/A_{CH}_{ROD}_'
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': 540, 'height': 960}); pg.set_default_timeout(90000); log = []
    pg.on('pageerror', lambda e: log.append('PAGEERROR ' + str(e)))
    ev = pg.evaluate
    def wait(c, n=80):
        for _ in range(n):
            if ev(c): return True
            pg.wait_for_timeout(500)
    pg.goto('http://localhost:8771/index.html'); wait('titleScene.ready')
    ev(f"S.char='{CH}'; go(lobbyScene)"); wait('scene === lobbyScene && fade === 0')
    pid = 0 if ROD.endswith('feet') else (3 if ROD.startswith('C') else 2)
    ev(f"modals.length=0; if(!S.owned.rod.includes('{ROD}')) S.owned.rod.push('{ROD}'); S.equip.rod='{ROD}'; S.equip.line='2'; S.gold=99999; S.silver=99999; S.ep=9e6; S.room={{p:PONDS[{pid}].id, until:Date.now()+9e6}}; enterPond(PONDS[{pid}], true)"); wait('scene === pond && fade === 0'); ev('modals.length=0')
    ev(f"S.equip.rod='{ROD}'"); ev("ensure(['img:'+angKey(S.char, pond.rod().code)])"); pg.wait_for_timeout(2500)
    print('key', ev("angKey(S.char, pond.rod().code)"), ev("!!A.tex['img:'+angKey(S.char, pond.rod().code)]"))
    SIM = "(n, f) => { for (let i = 0; i < n; i++) { T += .05; if (f) f(); pond.update(.05); } }"
    sim = lambda n, f='null': ev(f"({SIM})({n}, {f})")
    shots = []
    def shot(name):
        pg.wait_for_timeout(250); pg.screenshot(path=OUT + name + '.png'); shots.append(OUT + name + '.png')
    shot('0idle')
    ev("pond.p.fee.per==='room' && (S.room = S.room||{}); pond.tackleOk = () => null; pond.candidates = () => [[pond.p.fish[0], 1]]; pond.startCast(.6)")
    for i, k in enumerate([4, 4, 3, 3, 6]):
        sim(k); shot(f'1cast{i}')
    sim(30); shot('2wait')
    ev("pond.hook(pond.p.fish[0], {x:.3, z:6}, false)"); sim(3); shot('3strike')
    sim(20, "() => { pond.N = 3; pond.lastPress = T; }"); shot('4fight')
    ev("pond.land()"); sim(1); pg.evaluate('pond.stT=.12'); shot('5land0'); ev('pond.stT=1.0'); print(ev('[pond.st, pond.stT, pond.landAt]')); sim(8); shot('6land1'); print(ev('[pond.st, pond.stT, pond.landAt, !!pond.fish]')); sim(10); print(ev('[pond.st, pond.stT, scene===pond]')); shot('7land2')
    print(log[:5]); b.close()
    from PIL import Image
    ims = [Image.open(f).resize((270, 480)) for f in shots]
    out = Image.new('RGB', (270 * 6, 480 * 2))
    for i, im in enumerate(ims): out.paste(im, ((i % 6) * 270, (i // 6) * 480))
    out.save(OUT + 'sheet.png')
