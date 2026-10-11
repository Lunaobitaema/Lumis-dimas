import sys, json
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
def newpage(b, w=1280, h=900, mobile=False):
    ctx = b.new_context(viewport={'width':w,'height':h}, has_touch=mobile, is_mobile=mobile, color_scheme='dark')
    pg = ctx.new_page(); pg.errs=[]; pg.reqs=[]
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.on('request', lambda r: pg.reqs.append(r.method+' '+r.url[:80]))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.add_init_script("window.__opened=[]; window.open=(u)=>{window.__opened.push(u); return null}; try{navigation.addEventListener('navigate',e=>{ if(!e.destination.url.startsWith('http')){window.__nav=e.destination.url; e.preventDefault();}})}catch(e){}")
    pg.goto(URL); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
    return ctx, pg
out = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1 mobile menu
    ctx, pg = newpage(b, 375, 800, True)
    pg.click('#hamburger'); pg.wait_for_timeout(500)
    out['menu_open_display'] = pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")
    out['hamburger_reachable_when_open'] = pg.evaluate("(()=>{const r=document.getElementById('hamburger').getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return e? (e.closest('#hamburger')?'hamburger':(e.id||e.tagName)) : null})()")
    out['fixed_btns_over_menu'] = pg.evaluate("(()=>{const r=document.getElementById('calc-btn').getBoundingClientRect(); const e=document.elementFromPoint(r.left+10,r.top+10); return !!e.closest('#calc-btn')})()")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    out['menu_closes_on_escape'] = pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")=='none'
    # carousel resize reset (mobile address-bar resize)
    pg.evaluate("document.getElementById('mobile-menu').style.display='none'; document.body.style.overflow=''")
    before = pg.evaluate("(()=>{const c=document.getElementById('carousel'); c.style.scrollBehavior='auto'; c.scrollLeft+=260; return c.scrollLeft})()")
    pg.set_viewport_size({'width':375,'height':740}); pg.wait_for_timeout(500)
    out['carousel_scroll_before_after_height_resize'] = [before, pg.evaluate("document.getElementById('carousel').scrollLeft")]
    out['carousel_gap_css_vs_js'] = pg.evaluate("getComputedStyle(document.getElementById('carousel')).gap")
    ctx.close()
    # 2 form
    ctx, pg = newpage(b)
    out['form_controls_hit_test'] = pg.evaluate("""(()=>{const o={}; document.querySelectorAll('.contact-form .form-input, .contact-form .form-textarea, .contact-form .send-method, .contact-form .form-submit').forEach(el=>{ el.scrollIntoView({block:'center',behavior:'instant'}); const r=el.getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); o[(el.placeholder||el.id||el.className).slice(0,22)] = e===el||el.contains(e) ? 'OK' : 'COVERED BY '+(e?(e.id||e.tagName):'null'); }); return o})()""")
    pg.evaluate("document.querySelector('.form-submit').click()"); pg.wait_for_timeout(300)
    out['empty_submit_toast'] = pg.inner_text('#adm-toast')
    pg.fill('.contact-form input[type=tel]', 'abc', force=True); pg.evaluate("document.querySelector('input[value=instagram]').click()")
    pg.set_input_files('#fileInput', [{'name':'<img src=x onerror=window.__xss=1>.png','mimeType':'image/png','buffer':b'\x89PNG123'},
                                      {'name':'virus.exe','mimeType':'application/octet-stream','buffer':b'MZ'}])
    pg.wait_for_timeout(400)
    out['xss_via_filename'] = pg.evaluate("window.__xss===1")
    out['exe_accepted_in_list'] = 'virus.exe' in pg.inner_text('#fileList')
    n = len(pg.reqs)
    pg.evaluate("document.querySelector('.form-submit').click()"); pg.wait_for_timeout(600)
    out['submit_phone_abc_result'] = pg.inner_text('.contact-form').strip().replace('\n',' | ')
    out['network_requests_on_submit'] = pg.reqs[n:]
    out['opened'] = pg.evaluate("window.__opened")
    ctx.close()
    # email link
    ctx, pg = newpage(b)
    out['email_link'] = pg.evaluate("(()=>{const a=document.querySelectorAll('.contact-item-value a')[1]; return [a.getAttribute('href'), a.textContent]})()")
    out['file_drop_zone_border'] = pg.evaluate("getComputedStyle(document.getElementById('fileDropZone')).borderTopStyle+' / minH '+getComputedStyle(document.getElementById('fileDropZone')).minHeight+' / pos '+getComputedStyle(document.getElementById('fileDropZone')).position")
    out['file_input_rect'] = pg.evaluate("(()=>{const r=document.getElementById('fileInput').getBoundingClientRect();return [Math.round(r.width),Math.round(r.height), getComputedStyle(document.getElementById('fileInput')).opacity]})()")
    out['body_cursor'] = pg.evaluate("getComputedStyle(document.body).cursor")
    # 4 calc
    pg.click('#calc-btn'); pg.wait_for_timeout(700)
    out['calc_initial_display'] = pg.inner_text('#pc-price')
    pg.click('#calc-popup button:has-text("Отримати")'); pg.wait_for_timeout(300)
    import urllib.parse
    nav = pg.evaluate("window.__nav||''"); out['calc_default_mail_price'] = urllib.parse.unquote(nav)[-40:]
    for t in ['Монтаж','Дизайн-макет','Доставка Київ']: pg.click(f'.pc-ext:has-text("{t}")')
    pg.wait_for_timeout(800)
    out['calc_3extras_display'] = pg.inner_text('#pc-price') + ' disc ' + pg.inner_text('#rv-disc2')
    pg.click('#calc-popup button:has-text("Отримати")'); pg.wait_for_timeout(300)
    out['calc_3extras_mail_price'] = urllib.parse.unquote(pg.evaluate("window.__nav||''"))[-30:]
    pg.click('#calc-popup button:has-text("Скинути")'); pg.wait_for_timeout(800)
    out['calc_after_reset'] = pg.inner_text('#pc-price') + ' | ext row: ' + pg.inner_text('#rv-ext2') + ' | disc: ' + pg.inner_text('#rv-disc2')
    out['calc_opt_focusable'] = pg.evaluate("document.querySelector('.pc-opt').tabIndex")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    out['calc_closes_on_escape'] = pg.evaluate("getComputedStyle(document.getElementById('calc-popup')).display")=='none'
    ctx.close()
    # 5 dots
    ctx, pg = newpage(b)
    res=[]
    for i in range(6):
        pg.evaluate(f"(()=>{{const c=document.getElementById('carousel'); c.style.scrollBehavior='auto'; const w=c.querySelector('.car-card:not(.car-clone)').offsetWidth+28; c.scrollLeft=6*w+{i}*w; }})()")
        pg.wait_for_timeout(200)
        res.append(pg.evaluate("document.querySelectorAll('.car-dot.active').length"))
    out['active_dots_per_card_position'] = res
    out['dots_total_vs_cards'] = pg.evaluate("[document.querySelectorAll('.car-dot').length, document.querySelectorAll('.car-card:not(.car-clone)').length]")
    out['car_card_focusable'] = pg.evaluate("document.querySelector('.car-card').tabIndex")
    # 6 admin
    out['admin_offscreen_inputs_tabbable'] = pg.evaluate("getComputedStyle(document.getElementById('admin-panel')).visibility")
    out['default_password_shown_on_page'] = 'lumis2024' in pg.content()
    pg.click('button[title="Адмін панель"]'); pg.wait_for_timeout(600)
    pg.fill('#lock-input','lumis2024'); pg.click('#admin-lock .adm-btn'); pg.wait_for_timeout(400)
    out['default_password_unlocks'] = pg.evaluate("document.getElementById('admin-lock').classList.contains('hidden')")
    pg.fill('#edit-eyebrow','ЗМІНЕНО'); pg.evaluate("(()=>{const e=document.getElementById('edit-email'); e.value='new@example.com'; e.dispatchEvent(new Event('input',{bubbles:true}))})()"); pg.fill('#edit-about-title','Новий заголовок')
    pg.fill('#edit-hero-sub','<img src=x onerror="window.__xss2=1">')
    pg.wait_for_timeout(300)
    out['liveUpdate_global'] = pg.evaluate("typeof window.liveUpdate")
    out['admin_xss_hero_sub'] = pg.evaluate("window.__xss2===1")
    out['email_edit_applied'] = pg.evaluate("document.querySelectorAll('.contact-item-value a')[1].textContent")
    out['about_title_edit_applied'] = pg.inner_text('.about-text .section-title')
    pg.evaluate("updateColor('gold','#ff0000'); document.getElementById('toggle-process').click()")
    pg.fill('#edit-hero-sub','ok'); pg.click('#pane-content .adm-btn'); pg.wait_for_timeout(300)
    out['localStorage_keys'] = pg.evaluate("Object.keys(localStorage)")
    pg.reload(); pg.wait_for_timeout(1200)
    out['after_reload_eyebrow(visitor)'] = pg.inner_text('.hero-eyebrow')
    out['after_reload_gold'] = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--gold').trim()")
    out['after_reload_process_visible'] = pg.evaluate("getComputedStyle(document.getElementById('process')).display")
    out['pageerrors'] = pg.errs
    ctx.close()
    # light theme contrast
    ctx, pg = newpage(b)
    out['contrast'] = pg.evaluate("""(()=>{
      const lum=c=>{const m=c.match(/[\\d.]+/g).map(Number); const f=v=>{v/=255; return v<=0.03928? v/12.92: Math.pow((v+0.055)/1.055,2.4)}; return 0.2126*f(m[0])+0.7152*f(m[1])+0.0722*f(m[2])};
      const cr=(a,b)=>{const x=lum(a),y=lum(b); return +((Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)).toFixed(2)};
      const t=document.createElement('span'); document.body.appendChild(t);
      const col=v=>{t.style.color='var(--'+v+')'; return getComputedStyle(t).color};
      const run=()=>({gray_on_bg:cr(col('gray'),col('bg')), gray_on_bg2:cr(col('gray'),col('bg2')), gray2_on_bg:cr(col('gray2'),col('bg')), gold_on_bg:cr(col('gold'),col('bg')), bg_on_gold:cr(col('bg'),col('gold')), white_on_bg:cr(col('white'),col('bg'))});
      const dark=run(); document.body.classList.add('light-mode'); const light=run();
      const pl=cr(getComputedStyle(document.querySelector('.pi-label-name')).color,'rgb(12,10,8)');
      return {dark, light, light_portfolio_label_on_dark_gradient: pl}; })()""")
    ctx.close(); b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))
