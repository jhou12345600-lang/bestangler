"""v3 features against the emulators: wide dock + walking, male character, chat, friends, gifts, underwater fight."""
import json, time, sys
from playwright.sync_api import sync_playwright
URL = 'http://localhost:8770/index.html'
OUT = '/home/claude/shots/v3/'
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
log = []
def page(b, tag):
    ctx = b.new_context(viewport={'width': 405, 'height': 720})
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: log.append(f'[{tag}] PAGEERROR {e}'))
    pg.on('console', lambda m: log.append(f'[{tag}] {m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    pg.goto(URL); return pg
def ev(pg, js):
    try: return pg.evaluate(js)
    except Exception as e: log.append('EVAL ' + str(e)[:300])
def shot(pg, n): pg.screenshot(path=OUT + n + '.png', timeout=180000); print('shot', n, flush=True)
def wait(pg, cond, n=60):
    for _ in range(n):
        if ev(pg, cond): return True
        pg.wait_for_timeout(500)
    return False
def register(pg, id_, pw):
    wait(pg, 'titleScene.ready && FB.restored !== undefined')
    ev(pg, "AUTH.set('register')"); pg.wait_for_timeout(300)
    pg.fill('#fId', id_); pg.fill('#fPw', pw); pg.fill('#fPw2', pw); pg.fill('#fMail', '')
    ev(pg, 'AUTH.doRegister()')
    return wait(pg, 'scene === lobbyScene')
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    A = page(b, 'A'); B = page(b, 'B')
    sfx = str(int(time.time()) % 100000)
    print('A reg', register(A, 'boyA' + sfx, 'secret123'), 'B reg', register(B, 'girlB' + sfx, 'secret123'), flush=True)
    for pg in (A, B): ev(pg, 'modals.length = 0'); pg.wait_for_timeout(800); ev(pg, 'modals.length = 0')
    # A picks the male character
    ev(A, 'openModal(charModal())'); A.wait_for_timeout(1500); shot(A, '01_charselect')
    ev(A, "S.char='boy'; save(); NET.lastJson=''; modals.length=0")
    shot(A, '02_lobby')
    # both to pond 1
    for pg in (A, B): ev(pg, 'enterPond(PONDS[0])')
    for pg in (A, B): print('in pond', wait(pg, "scene === pond && fade === 0"), flush=True)
    for pg in (A, B): ev(pg, 'modals.length = 0')
    A.wait_for_timeout(3000)
    print('A wx', ev(A, 'pond.wx'), 'B wx', ev(B, 'pond.wx'), 'A sees', ev(A, 'pond.dockPeers().map(d=>[d.pe.presence.n, d.x])'), flush=True)
    shot(A, '03_pond_A'); shot(B, '04_pond_B')
    # A walks right for 1.2s (hold key)
    A.keyboard.down('ArrowRight'); A.wait_for_timeout(400); shot(A, '05_walking'); A.wait_for_timeout(800); A.keyboard.up('ArrowRight')
    A.wait_for_timeout(1500)
    print('A wx after walk', ev(A, 'pond.wx'), 'B sees A at', ev(B, 'pond.dockPeers().map(d=>[d.pe.presence.n, d.x])'), flush=True)
    shot(B, '06_B_sees_A')
    # pan B's camera
    ev(B, 'pond.camW = pond.wx - 2.2; pond.follow = false'); B.wait_for_timeout(800); shot(B, '07_B_panned')
    ev(B, 'pond.follow = true')
    # chat in pond
    ev(A, "NET.sendChat('大家好！今天魚況如何？', 'pond')"); A.wait_for_timeout(2000)
    print('B pond chat', ev(B, 'NET.chat.pond.map(c=>c.n+":"+c.m)'), 'B says', ev(B, 'Object.keys(NET.says)'), flush=True)
    shot(B, '08_B_chat_bubble')
    ev(B, "openModal(chatModal('pond'))"); B.wait_for_timeout(1000); B.fill('#chatIn', '你好！鯉魚很多喔'); ev(B, 'modals[modals.length-1].send()'); B.wait_for_timeout(2500)
    shot(B, '09_chat_modal')
    ev(B, 'modals[modals.length-1].close()')
    ev(A, "NET.sendChat('世界頻道測試', 'world')"); A.wait_for_timeout(1500)
    print('B world', ev(B, 'NET.chat.world.map(c=>c.m)'), 'rate-limit:', ev(A, "NET.chatAt=0, FB.sendChat('太快', 'world')"), flush=True)
    A.wait_for_timeout(800)
    # friend request by account id
    ev(A, "openModal(friendsModal('add'))"); A.wait_for_timeout(800); A.fill('#fidIn', 'girlB' + sfx); ev(A, 'modals[modals.length-1].byId()'); A.wait_for_timeout(2500)
    print('A add msg', ev(A, 'modals[modals.length-1].msg'), flush=True); shot(A, '10_add_friend')
    ev(A, 'modals.length = 0'); B.wait_for_timeout(1000)
    print('B requests', ev(B, 'Object.values(NET.requests).map(r=>r.n)'), flush=True)
    ev(B, "modals.length=0; openModal(friendsModal('req'))"); B.wait_for_timeout(800); shot(B, '11_requests')
    ev(B, "FB.acceptFriend(Object.keys(NET.requests)[0], Object.values(NET.requests)[0].n)"); B.wait_for_timeout(2000)
    print('A friends', ev(A, 'Object.values(NET.friends).map(f=>f.n)'), 'B friends', ev(B, 'Object.values(NET.friends).map(f=>f.n)'), flush=True)
    ev(B, "modals.length=0; openModal(friendsModal('list'))"); B.wait_for_timeout(800); shot(B, '12_friend_list')
    ev(B, 'modals.length=0')
    # gifts A -> B: silver, bait, a rod
    ev(A, "S.owned.rod.push('15feet'); S.silver = 5000; save()")
    bid = ev(A, 'Object.keys(NET.friends)[0]')
    ev(A, f"openModal(giftModal('{bid}', 'B'))"); A.wait_for_timeout(600)
    ev(A, "(()=>{const m=modals[modals.length-1]; const it=m.items()[0]; m.sel=it; m.qty=500; m.send(it, 10)})()"); A.wait_for_timeout(3500)
    print('gift1 msg', ev(A, 'modals[modals.length-1].msg'), flush=True)
    ev(A, "(()=>{const m=modals[modals.length-1]; m.tab='bait'; const it=m.items()[0]; m.sel=it; m.qty=10; m.send(it, 10)})()"); A.wait_for_timeout(3500)
    print('gift2 msg', ev(A, 'modals[modals.length-1].msg'), flush=True)
    ev(A, "(()=>{const m=modals[modals.length-1]; m.tab='gear'; m.sel=null})()"); A.wait_for_timeout(400); shot(A, '13_gift_gear')
    ev(A, "(()=>{const m=modals[modals.length-1]; const it=m.items().find(i=>i.id==='15feet'); m.sel=it; m.send(it, 10)})()"); A.wait_for_timeout(3000)
    print('gift3 msg', ev(A, 'modals[modals.length-1].msg'), 'A owns', ev(A, 'S.owned.rod'), 'A silver', ev(A, 'S.silver'), flush=True)
    B.wait_for_timeout(2000)
    print('B silver', ev(B, 'S.silver'), 'B bait', ev(B, 'JSON.stringify(S.bait)'), 'B rods', ev(B, 'S.owned.rod'), 'B queue', ev(B, 'NET.giftQ.length'), 'B modal', ev(B, 'modals.length'), flush=True)
    shot(B, '14_B_gift_popup')
    ev(A, 'modals.length=0'); ev(B, 'modals.length=0; NET.giftQ.length=0')
    # A hooks a fish -> underwater fight
    ev(A, "pond.hook('carp', {x: .6, z: 9})"); A.wait_for_timeout(700); shot(A, '15_hookset')
    A.wait_for_timeout(2200); print('A view', ev(A, 'pond.view'), ev(A, 'pond.st'), flush=True)
    shot(A, '16_fight_under'); shot(B, '17_B_sees_fight')
    ev(A, 'pond.fish.depth = .9; pond.fish.run = 2; pond.line.T = .95; pond.line.Td=.95'); A.wait_for_timeout(500); shot(A, '18_fight_deep_tense')
    ev(A, 'pond.line.L = 3'); A.wait_for_timeout(1200); shot(A, '19_fight_close')
    # catch scene for the boy
    ev(A, "go(catchScene, {sp:'carp', len:72, kg:4.2, stars:4, silver:120, gold:1, ep:30, record:72, newRecord:true, pond:1})"); A.wait_for_timeout(2500); shot(A, '20_catch_boy')
    print('\n'.join(log[:40]))
    b.close()
