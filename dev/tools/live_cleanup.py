import sys
from playwright.sync_api import sync_playwright
URL = sys.argv[1]; IDS = sys.argv[2:]
CLEAN = """(async()=>{ const u=FB.user, db=FB.db, me=u.uid, id=(u.email||'').split('@')[0];
  try { await FB.setPond(0); } catch(e){}
  await new Promise(r => setTimeout(r, 1500));
  for (const f of Object.keys(NET.friends)) { try { await FB.removeFriend(f); } catch(e){} }
  for (const k of Object.keys(NET.requests)) { try { await FB.declineFriend(k); } catch(e){} }
  for (const p of ['leaderboard/'+me, 'online/'+me, 'users/'+me, 'ids/'+id, 'chatT/'+me, 'giftT/'+me]) { try { await db.ref(p).remove(); } catch(e) { return 'fail '+p+' '+e.code; } }
  await u.delete(); return 'deleted'; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader'])
    for id_ in IDS:
        pg = b.new_page(); pg.goto(URL)
        for _ in range(60):
            if pg.evaluate('titleScene.ready && FB.restored !== undefined'): break
            pg.wait_for_timeout(500)
        if pg.evaluate('!!FB.restored'): pg.evaluate('FB.auth.signOut()'); pg.wait_for_timeout(500)
        u = pg.evaluate(f"FB.login('{id_}', 'Test-123456').then(u => FB.start(u, null)).then(() => 'in', e => 'err ' + e.code)")
        pg.wait_for_timeout(2500)
        print(id_, u, pg.evaluate(CLEAN) if u == 'in' else '', flush=True)
        pg.close()
    b.close()
