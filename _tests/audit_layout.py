"""Layout/responsive audit. Usage: audit_layout.py <url> <outdir>"""
import sys, json, os
from playwright.sync_api import sync_playwright
URL, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
WIDTHS = [320,360,375,390,430,768,1024,1280,1440,1920]
JS = r"""
() => {
  const vw = document.documentElement.clientWidth;
  const clipped = el => { let p = el.parentElement; while (p && p !== document.body) { const cs = getComputedStyle(p);
      if (['hidden','auto','scroll','clip'].includes(cs.overflowX) || cs.position==='fixed') return true; p = p.parentElement; } return false; };
  const vis = el => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
      return cs.display!=='none' && cs.visibility!=='hidden' && r.width>0 && r.height>0; };
  const offenders = [];
  document.querySelectorAll('body *').forEach(el => {
    if (!vis(el) || getComputedStyle(el).position==='fixed' || clipped(el)) return;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 || r.left < -1) offenders.push((el.id?'#'+el.id:'')+'.'+(el.className&&el.className.baseVal===undefined?el.className:'')+' <'+el.tagName+'> '+Math.round(r.left)+'..'+Math.round(r.right));
  });
  // text overflowing its own box
  const textOverflow = [];
  document.querySelectorAll('h1,h2,h3,p,a,button,span,div,label').forEach(el => {
    if (!vis(el) || clipped(el) && el.closest('#carousel,.marquee-section')) return;
    if (el.children.length===0 && el.textContent.trim() && el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).display!=='inline')
      textOverflow.push((el.className||el.tagName)+': '+el.textContent.trim().slice(0,30));
  });
  // small fonts
  const small = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue; const el = n.parentElement; if (!el || !vis(el)) continue;
    if (el.closest('#admin-panel,#calc-popup,script,style,.car-clone')) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 11) { const k = fs+'px '+(el.className||el.tagName).toString().slice(0,30); small[k]=(small[k]||0)+1; }
  }
  // tap targets
  const taps = [];
  document.querySelectorAll('a,button,input,textarea,label.send-method,[onclick]').forEach(el => {
    if (!vis(el) || el.closest('#admin-panel,#calc-popup,.car-clone,#mobile-menu')) return;
    const r = el.getBoundingClientRect();
    if (r.height < 40 || r.width < 40) taps.push((el.id||el.className||el.tagName).toString().slice(0,24)+' '+Math.round(r.width)+'x'+Math.round(r.height));
  });
  const pad = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).padding : null; };
  const shown = s => { const e = document.querySelector(s); return !!e && vis(e); };
  const g = document.querySelector;
  return { vw, docScrollW: document.documentElement.scrollWidth, bodyScrollW: document.body.scrollWidth,
    offenders: offenders.slice(0,12), textOverflow: textOverflow.slice(0,12), small, taps: taps.slice(0,20),
    pad: { about: pad('#about'), process: pad('#process'), categories: pad('#categories'), carousel: pad('#carousel'), contact: pad('#contact') },
    shown: { hamburger: shown('#hamburger'), navLinks: shown('.nav-links'), navCta: shown('.nav-cta'),
             catTitle: shown('#categories h2'), aboutStat: shown('.about-stat-num'), heroScroll: shown('.hero-scroll'),
             carArrows: shown('#carPrev'), adminBtn: shown('button[title="Адмін панель"]') },
    cols: { services: getComputedStyle(document.querySelector('.services-grid')).gridTemplateColumns.split(' ').length,
            portfolio: getComputedStyle(document.querySelector('.portfolio-grid')).gridTemplateColumns.split(' ').length,
            steps: getComputedStyle(document.querySelector('.process-steps')).gridTemplateColumns.split(' ').length },
    hero: (()=>{ const h=document.querySelector('.hero').getBoundingClientRect(); const t=document.querySelector('.hero-title').getBoundingClientRect();
            const b=document.querySelector('.hero-btns').getBoundingClientRect(); return {heroH:Math.round(h.height), titleL:Math.round(t.left), titleR:Math.round(t.right), btnBottom:Math.round(b.bottom), vh:innerHeight}; })(),
    fixedBtns: ['button[title="Адмін панель"]','#admin-open-btn','#calc-btn','#theme-toggle-btn'].map(s=>{const e=document.querySelector(s); if(!e||!vis(e)) return null; const r=e.getBoundingClientRect(); return s+': r'+Math.round(vw-r.right)+' b'+Math.round(innerHeight-r.bottom)+' '+Math.round(r.width)+'px';}).filter(Boolean),
    inputFont: (()=>{const e=document.querySelector('.form-input'); return e?getComputedStyle(e).fontSize:null})(),
  };
}
"""
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in WIDTHS:
        mobile = w <= 768
        ctx = b.new_context(viewport={'width': w, 'height': 800 if mobile else 900}, has_touch=mobile, is_mobile=mobile,
                            device_scale_factor=1, color_scheme='dark')
        pg = ctx.new_page()
        errs, ext = [], set()
        pg.on('console', lambda m: errs.append('console.'+m.type+': '+m.text[:160]) if m.type in ('error','warning') else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: '+str(e)[:200]))
        def route(r):
            u = r.request.url
            if u.startswith('http://127.0.0.1') or u.startswith('data:'): r.continue_()
            else: ext.add(u.split('?')[0][:70]); r.abort()
        pg.route('**/*', route)
        pg.goto(URL, wait_until='load'); pg.wait_for_timeout(2600)
        pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
        pg.wait_for_timeout(900)
        r = pg.evaluate(JS)
        r['errors'] = [e for e in errs if 'ERR_FAILED' not in e and 'net::' not in e]
        r['external'] = sorted(ext)
        res[w] = r
        pg.screenshot(path=f'{OUT}/full_{w}.png', full_page=True)
        ctx.close()
    b.close()
json.dump(res, open(f'{OUT}/layout.json','w'), ensure_ascii=False, indent=1)
for w, r in res.items():
    print(f"== {w}px  doc={r['docScrollW']} body={r['bodyScrollW']}  cols={r['cols']}  shown={ {k:v for k,v in r['shown'].items()} }")
    print('   pad', r['pad']); print('   hero', r['hero'], 'fixed', r['fixedBtns'], 'inputFont', r['inputFont'])
    if r['offenders']: print('   OFFSCREEN', r['offenders'])
    if r['textOverflow']: print('   TEXTOVF', r['textOverflow'])
    print('   small<11px:', sum(r['small'].values()), 'nodes;', list(r['small'].items())[:40])
    print('   taps<40:', len(r['taps']), r['taps'][:8])
    if r['errors']: print('   ERR', r['errors'][:5])
print('external:', res[1280]['external'])
