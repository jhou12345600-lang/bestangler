"""Official-spec gameplay checks against the emulators."""
import time, sys
from playwright.sync_api import sync_playwright
URL = 'http://localhost:8770/index.html'; OUT = '/home/claude/shots/v4/'
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
log = []
def ev(pg, js):
    try: return pg.evaluate(js)
    except Exception as e: log.append('EVAL ' + str(e)[:300])
def shot(pg, n): pg.screenshot(path=OUT + n + '.png', timeout=180000); print('shot', n, flush=True)
def wait(pg, cond, n=60):
    for _ in range(n):
        if ev(pg, cond): return True
        pg.wait_for_timeout(500)
    return False
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page(viewport={'width': 405, 'height': 720})
    pg.on('pageerror', lambda e: log.append('PAGEERROR ' + str(e)))
    pg.on('console', lambda m: log.append(m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto(URL); wait(pg, 'titleScene.ready && FB.restored !== undefined')
    ev(pg, "AUTH.set('register')"); pg.wait_for_timeout(300)
    pg.fill('#fId', 'spec' + str(int(time.time()) % 100000)); pg.fill('#fPw', 'secret123'); pg.fill('#fPw2', 'secret123'); ev(pg, 'AUTH.doRegister()')
    print('lobby', wait(pg, 'scene === lobbyScene'), flush=True); pg.wait_for_timeout(1500); None; ev(pg, 'modals.length=0')
    print('levels', ev(pg, '[LEVEL_EP[2], LEVEL_EP[4], LEVEL_EP[10], LEVEL_EP[50], LEVEL_EP[99], titleFor(1), titleFor(10), titleFor(99)]'))
    print('kg', ev(pg, "[fishKg('niloticus', 15), fishKg('carp', 72), fishKg('giantgrouper', 130), fishKg('tinfoil', 8)]"))
    print('bands', ev(pg, "[fishBand('carp', 45), fishBand('corvina', 115), FISH.giantgrouper.max, FISH.peacock.bands.length]"))
    ev(pg, 'openModal(missionsModal())'); pg.wait_for_timeout(700); None; ev(pg, 'modals.length=0')
    ev(pg, 'openModal(achievementModal())'); pg.wait_for_timeout(700); None; ev(pg, 'modals.length=0')
    ev(pg, 'openModal(leaderboardModal())'); pg.wait_for_timeout(700); None; ev(pg, 'modals.length=0')
    ev(pg, 'openModal(payModal())'); pg.wait_for_timeout(700); None; ev(pg, 'modals.length=0')
    ev(pg, 'openModal(lotteryModal())'); pg.wait_for_timeout(700); None; ev(pg, 'modals.length=0')
    ev(pg, 'openModal(shopModal())'); pg.wait_for_timeout(700); None; ev(pg, "modals[0].tab='rod'"); pg.wait_for_timeout(300); None; ev(pg, 'modals.length=0')
    # pond 1 with the basic kit: candidates & tackleOk
    ev(pg, 'enterPond(PONDS[0])'); wait(pg, 'scene === pond && fade === 0'); ev(pg, 'modals.length=0')
    print('pond1 cand', ev(pg, 'pond.candidates()'), 'ok?', ev(pg, 'pond.tackleOk()'), flush=True)
    ev(pg, "pond.setState('aim')"); pg.wait_for_timeout(600); None
    ev(pg, 'pond.startCast(.6)'); pg.wait_for_timeout(2500)
    print('after cast', ev(pg, '[pond.st, S.silver, S.bait["萬能餌"], pond.gold.casts]'), flush=True)
    # force a bite and strike many times to estimate the hook rate (logic only)
    print('hook rate', ev(pg, """(()=>{ let n=0; for (let i=0;i<2000;i++){ if (Math.random() < HOOK_RATE) n++; } return n/2000; })()"""))
    # fight a small fish on the surface
    ev(pg, "pond.retrieve(); pond.hook('niloticus', {x:.4, z:6}, false)"); pg.wait_for_timeout(2500)
    print('small fish', ev(pg, '[pond.st, pond.view, pond.fish.phase, pond.fish.len, pond.fish.U0, pond.fish.Fmax]'), flush=True)
    ev(pg, 'pond.N = 6; pond.lastPress = T'); pg.wait_for_timeout(1500); shot(pg, '10_fight_surface')
    print('U after reeling', ev(pg, '[pond.fish && Math.round(pond.fish.U), pond.P, Math.round(pond.line.L)]'))
    # line break: P + F > S
    ev(pg, 'pond.N = 10; pond.lastPress = T; pond.fish.F = 80; pond.fish.Fmax = 200'); pg.wait_for_timeout(1500)
    print('break test', ev(pg, '[pond.st, pond.loseWhy]'), flush=True)
    pg.wait_for_timeout(2500)
    # escape after 7 s idle
    ev(pg, "pond.hook('niloticus', {x:.4, z:6}, false)"); pg.wait_for_timeout(2500); ev(pg, 'pond.lastPress = T - 7.5'); pg.wait_for_timeout(800)
    print('idle escape', ev(pg, '[pond.st, pond.loseWhy]'), flush=True)
    pg.wait_for_timeout(2500)
    # a big golden carp with the 18 ft rod: goes under water after the surface thrash
    ev(pg, "S.owned.rod.push('18feet'); S.equip.rod='18feet'; Math.random = (r => () => r)(0.999)")
    ev(pg, "pond.hook('carp', {x:.4, z:7}, true)"); ev(pg, 'Math.random = (()=>{ const R = Math.random; return R; })()')
    pg.wait_for_timeout(600); shot(pg, '11_golden_hook')
    pg.wait_for_timeout(2500)
    print('big fish', ev(pg, '[pond.st, pond.view, pond.fish && pond.fish.phase, pond.fish && pond.fish.len]'), flush=True)
    ev(pg, 'pond.N = 2; pond.lastPress = T'); pg.wait_for_timeout(1500); shot(pg, '12_under_tired')
    ev(pg, 'pond.N = 0; pond.fish.run = 1.4; pond.fish.rageDur = 1.4; pond.lastPress = T'); pg.wait_for_timeout(1000); shot(pg, '13_under_rage')
    print('after rage', ev(pg, '[pond.st, pond.fish && Math.round(pond.fish.ux), pond.fish && pond.fish.uy.toFixed(2)]'), flush=True)
    # exhaust it: dragged to the upper right, then netted
    ev(pg, 'pond.fish.U = 0; pond.lastPress = T'); pg.wait_for_timeout(3500); shot(pg, '14_dragged')
    for _ in range(80):
        if ev(pg, "pond.st === 'land' || pond.st === 'idle'"): break
        ev(pg, 'pond.lastPress = T; pond.N = 0'); pg.wait_for_timeout(500)
    print('landing', ev(pg, '[pond.st, pond.view]'), flush=True)
    pg.wait_for_timeout(1200); shot(pg, '15_netting')
    wait(pg, 'scene === catchScene && fade === 0'); pg.wait_for_timeout(2000); shot(pg, '16_catch')
    print('catch result', ev(pg, 'JSON.stringify(catchScene.r)'), flush=True)
    s0 = ev(pg, '[S.silver, S.gold, S.ep]'); ev(pg, 'catchScene.finish()'); pg.wait_for_timeout(500)
    print('after sell', s0, '->', ev(pg, '[S.silver, S.gold, S.ep, S.stats.kg, S.firsts]'), flush=True)
    wait(pg, 'scene === pond && fade === 0'); ev(pg, 'modals.length=0')
    print('missions now', ev(pg, 'missionList().map(m=>m.id+":"+m.ok)'), flush=True)
    # room fee pond
    ev(pg, 'S.ep = LEVEL_EP[8]; S.gold = 150; go(lobbyScene)'); wait(pg, 'scene === lobbyScene && fade === 0'); ev(pg, 'modals.length=0')
    ev(pg, 'enterPond(PONDS[2])'); pg.wait_for_timeout(800); shot(pg, '17_room_fee')
    print('record rule check', ev(pg, "FB.db.ref('records/carp').get().then(s=>JSON.stringify(s.val()))"))
    print('\n'.join(log[:20])); b.close()
