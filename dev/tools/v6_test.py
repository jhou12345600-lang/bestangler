import sys
from playwright.sync_api import sync_playwright
W, H, TAG = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
OUT = '/home/claude/shots/v6/' + TAG + '_'
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': W, 'height': H}); pg.set_default_timeout(90000); log = []
    pg.on('pageerror', lambda e: log.append('PAGEERROR ' + str(e)))
    ev = pg.evaluate
    def wait(c, n=80):
        for _ in range(n):
            if ev(c): return True
            pg.wait_for_timeout(500)
    def shot(n): pg.screenshot(path=OUT + n + '.png'); print('shot', n, flush=True)
    pg.goto('http://localhost:8770/index.html'); wait('titleScene.ready && FB.restored !== undefined')
    ev("AUTH.enterWith(() => FB.guest(), true)"); wait('scene === lobbyScene && fade === 0')
    ev("modals.length=0; S.char='boy'; S.owned.rod.push('18feet'); S.equip.rod='18feet'; enterPond(PONDS[0])"); wait('scene === pond && fade === 0'); ev('modals.length=0')
    pg.wait_for_timeout(2500); shot('01_pond_boy')
    SIM = "(n, f) => { for (let i = 0; i < n; i++) { T += .05; if (f) f(); pond.update(.05); } }"
    sim = lambda n, f='null': ev(f"({SIM})({n}, {f})")
    ev("(() => { const R = Math.random; Math.random = () => .985; pond.hook('carp', {x:.4, z:7}, false); Math.random = R; })()")
    sim(10); pg.wait_for_timeout(600); shot('02_hook_surface')
    print('len', ev('pond.fish.len'), flush=True)
    sim(30, "() => { pond.N = 2; pond.lastPress = T; }"); sim(60, "() => { pond.N = 2; pond.lastPress = T; pond.fish.run = 0; pond.fish.rageT = 99; }")
    pg.wait_for_timeout(700); shot('03_under_bottom')
    sim(1, "() => { pond.fish.run = pond.fish.rageDur = 1.6; }"); sim(25, "() => { pond.N = 1; pond.lastPress = T; }")
    pg.wait_for_timeout(700); shot('04_under_sprint_left'); print('ux', ev('[pond.fish.ux, LW]'), flush=True)
    sim(1, "() => { pond.fish.U = 0; }"); sim(50, "() => { if (pond.fish) { pond.N = 2; pond.lastPress = T; } }"); pg.wait_for_timeout(700); shot('05_dragged_up_right')
    for _ in range(20):
        if ev("pond.st !== 'fight'"): break
        sim(20, "() => { if (pond.fish) { pond.N = 2; pond.lastPress = T; } }")
    sim(4); pg.wait_for_timeout(500); shot('06_surface_end')
    sim(18); pg.wait_for_timeout(400); shot('07_netting')
    print('\n'.join(log[:5])); b.close()
