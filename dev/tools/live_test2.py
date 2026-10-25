"""Live check of the v3 social features with two temporary accounts, then remove everything they wrote."""
import sys
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
log = []
def mk(b, tag):
    pg = b.new_page(viewport={'width': 405, 'height': 720})
    pg.on('pageerror', lambda e: log.append(f'[{tag}] PAGEERROR {e}'))
    pg.on('console', lambda m: log.append(f'[{tag}] {m.type}: {m.text}') if m.type == 'error' else None)
    pg.goto(URL); return pg
def until(pg, js, n=60):
    for _ in range(n):
        try:
            if pg.evaluate(js): return True
        except Exception as e: log.append(str(e)[:150])
        pg.wait_for_timeout(500)
    return False
def reg(pg, id_):
    until(pg, "titleScene.ready && FB.restored !== undefined")
    pg.evaluate("AUTH.set('register')"); pg.wait_for_timeout(300)
    pg.fill('#fId', id_); pg.fill('#fPw', 'Test-123456'); pg.fill('#fPw2', 'Test-123456'); pg.fill('#fMail', '')
    pg.evaluate('AUTH.doRegister()'); return until(pg, 'scene === lobbyScene')
CLEAN = """(async()=>{ const u=FB.user, db=FB.db, me=u.uid, id=(u.email||'').split('@')[0];
  try { await FB.setPond(0); } catch(e){}
  await new Promise(r => setTimeout(r, 1500));
  for (const f of Object.keys(NET.friends)) { try { await FB.removeFriend(f); } catch(e){} }
  for (const k of Object.keys(NET.requests)) { try { await FB.declineFriend(k); } catch(e){} }
  for (const p of ['leaderboard/'+me, 'online/'+me, 'users/'+me, 'ids/'+id, 'chatT/'+me, 'giftT/'+me]) { try { await db.ref(p).remove(); } catch(e) { return 'fail '+p+' '+e.code; } }
  await u.delete(); return 'deleted'; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    A = mk(b, 'A'); B = mk(b, 'B')
    print('reg', reg(A, 'zzt_a_claude'), reg(B, 'zzt_b_claude'), flush=True)
    for pg in (A, B): pg.evaluate('modals.length=0'); pg.wait_for_timeout(1500); pg.evaluate('modals.length=0')
    A.wait_for_timeout(2000)
    print('ids', A.evaluate("FB.findId('zzt_b_claude').then(u => !!u)"), flush=True)
    for pg in (A, B): pg.evaluate("enterPond(PONDS[0])")
    for pg in (A, B): until(pg, 'scene === pond && fade === 0'); pg.evaluate('modals.length=0')
    A.wait_for_timeout(5000)
    print('A sees', A.evaluate("pond.dockPeers().filter(d=>/zzt_/.test(d.pe.presence.n)).map(d=>[d.pe.presence.n, +d.x.toFixed(2)])"), 'A wx', A.evaluate('pond.wx'), 'B wx', B.evaluate('pond.wx'), flush=True)
    r = A.evaluate("FB.findId('zzt_b_claude').then(u => FB.requestFriend(u, 'zzt_b_claude'))"); B.wait_for_timeout(2500)
    print('request', r, 'B got', B.evaluate('Object.values(NET.requests).map(x=>x.n)'), flush=True)
    B.evaluate("(()=>{ const [u, r] = Object.entries(NET.requests)[0]; return FB.acceptFriend(u, r.n); })()"); A.wait_for_timeout(2500)
    print('friends', A.evaluate('Object.values(NET.friends).map(f=>f.n)'), B.evaluate('Object.values(NET.friends).map(f=>f.n)'), flush=True)
    s0 = B.evaluate('S.silver')
    print('gift', A.evaluate("FB.sendGift(Object.keys(NET.friends)[0], {k:'silver', id:'', q:100}).then(()=>'ok', e=>e.code)"), flush=True)
    B.wait_for_timeout(3000); print('B silver', s0, '->', B.evaluate('S.silver'), flush=True)
    print('stranger gift', B.evaluate("FB.sendGift('nobody123', {k:'silver', id:'', q:100}).then(()=>'ALLOWED', e=>'refused')"), flush=True)
    print('long chat', B.evaluate("FB.db.ref().update({['chat/world/'+FB.db.ref('chat/world').push().key]: {uid: FB.user.uid, n:'x', m:'a'.repeat(61), t: firebase.database.ServerValue.TIMESTAMP}, ['chatT/'+FB.user.uid]: firebase.database.ServerValue.TIMESTAMP}).then(()=>'ALLOWED', e=>'refused')"), flush=True)
    print('cleanup', A.evaluate(CLEAN), B.evaluate(CLEAN), flush=True)
    print('\n'.join(log[:15])); b.close()
