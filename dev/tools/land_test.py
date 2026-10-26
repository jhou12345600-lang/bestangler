"""Landscape (desktop) and portrait layout screenshots on the emulator site."""
import time, sys
from playwright.sync_api import sync_playwright
URL = 'http://localhost:8770/index.html'; OUT = '/home/claude/shots/v5/'
import os; os.makedirs(OUT, exist_ok=True)
VW, VH, TAG = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': VW, 'height': VH}); log = []
    pg.on('pageerror', lambda e: log.append('PAGEERROR ' + str(e)))
    pg.set_default_timeout(60000)
    def ev(js):
        try: return pg.evaluate(js)
        except Exception as e: log.append('EVAL ' + str(e)[:200])
    def wait(c, n=60):
        for _ in range(n):
            if ev(c): return True
            pg.wait_for_timeout(500)
    def shot(n): pg.screenshot(path=OUT + TAG + '_' + n + '.png'); print('shot', n, flush=True)
    pg.goto(URL); wait('titleScene.ready && FB.restored !== undefined')
    print('LW', ev('[LW, PX]'), flush=True)
    shot('01_title')
    ev("AUTH.set('register')"); pg.wait_for_timeout(500); shot('02_register')
    pg.fill('#fId', 'land' + str(int(time.time()) % 100000)); pg.fill('#fPw', 'secret123'); pg.fill('#fPw2', 'secret123'); ev('AUTH.doRegister()')
    wait('scene === lobbyScene && fade === 0'); pg.wait_for_timeout(800); shot('03_lobby_msg'); ev('modals.length=0')
    # click the 休閒池 pin with the real mouse (tests input mapping through the map transform)
    pin = ev("(() => { const ms = lobbyScene.ms(); const p = PONDS[0]; return [(p.pin[0] * ms - lobbyScene.camX), (p.pin[1] * ms - lobbyScene.camY)]; })()")
    box = pg.locator('#cv').bounding_box(); L = ev('LW')
    def click(x, y): pg.mouse.click(box['x'] + x / L * box['width'], box['y'] + y / 1280 * box['height'])
    print('pin at', pin, flush=True)
    if pin[1] > 1200: ev('lobbyScene.camY += ' + str(pin[1] - 700)); pg.wait_for_timeout(300); pin = ev("(() => { const ms = lobbyScene.ms(); const p = PONDS[0]; return [(p.pin[0] * ms - lobbyScene.camX), (p.pin[1] * ms - lobbyScene.camY)]; })()")
    click(pin[0], pin[1]); pg.wait_for_timeout(900); print('pond board open', ev('modals.length'), flush=True); shot('04_pondboard')
    # click 進入 inside the centred popup (board coords 400,862 + PX)
    px = ev('PX'); click(px + 400, 862); pg.wait_for_timeout(500)
    wait('scene === pond && fade === 0'); ev('modals.length=0'); pg.wait_for_timeout(1500); shot('05_pond')
    # real mouse on the throw button: press-hold-release to cast
    ev("pond.setState('aim')"); pg.wait_for_timeout(300); shot('06_aim')
    ev("pond.startCast(.6)"); pg.wait_for_timeout(3000); shot('07_wait')
    ev("pond.hook('carp', {x:.4, z:7}, false)"); pg.wait_for_timeout(2500); shot('08_fight_surface')
    # click the 力 button with the mouse a few times
    for _ in range(3): click(L / 2, 1130); pg.wait_for_timeout(400)
    print('N after clicks', ev('pond.N'), flush=True)
    ev("S.owned.rod.push('18feet'); S.equip.rod='18feet'; pond.lose('runaway')"); pg.wait_for_timeout(2500); ev("pond.setState('idle')")
    ev("(() => { const R = Math.random; Math.random = () => .99; pond.hook('carp', {x:.4, z:7}, false); Math.random = R; })()")
    SIM = "(n, f) => { for (let i = 0; i < n; i++) { T += .05; if (f) f(); pond.update(.05); } }"
    ev(f"({SIM})(40, () => {{ pond.N = 2; pond.lastPress = T; }})"); print('under?', ev('[pond.st, pond.view, pond.fish && pond.fish.len]'), flush=True)
    pg.wait_for_timeout(800); shot('09_fight_under')
    ev("go(catchScene, {sp:'carp', len:49.9, kg:2.78, stars:4, silver:25, gold:1, ep:43, golden:true, record:49.9, newRecord:true, pond:1, secs:30})")
    wait('scene === catchScene && fade === 0'); pg.wait_for_timeout(2000); shot('10_catch')
    ev('catchScene.finish()'); wait('scene === pond && fade === 0'); ev('modals.length=0; openModal(shopModal())'); pg.wait_for_timeout(800); shot('11_shop')
    ev('modals.length=0; openModal(chatModal("world"))'); pg.wait_for_timeout(900); shot('12_chat')
    print('\n'.join(log[:10])); b.close()
