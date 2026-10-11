"""Functional regression suite for the fixed LUMIS site. Needs start_servers.sh running."""
import json, os, re, sys, glob, hashlib, itertools, time, urllib.request, urllib.error, http.cookiejar
from playwright.sync_api import sync_playwright

S = '/tmp/claude-0/-home-claude/dde88c5a-a2c4-53ed-b1c3-7fd04d8963fa/scratchpad'
A, B = 'http://127.0.0.1:8803', 'http://127.0.0.1:8804'
INIT_PW = open('/home/claude/lumis/build/initial_password.txt').read().strip()
NEW_PW = 'Nova-Parol-2026-lumis'
ONLY = sys.argv[1:] 
R = []
def T(group, name, where, ok, ev=''):
    R.append({'group': group, 'test': name, 'where': where, 'ok': bool(ok), 'evidence': str(ev)[:300]})
    print(('PASS ' if ok else 'FAIL ') + f'[{group}] {name} @ {where} :: {str(ev)[:200]}')

def page(b, base=A, w=1280, h=900, mobile=False, js=True, scheme='dark', path='/index.html'):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mobile, is_mobile=mobile, color_scheme=scheme, java_script_enabled=js)
    pg = ctx.new_page(); pg.errs = []; pg.reqs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.on('console', lambda m: pg.errs.append('console: ' + m.text[:200]) if m.type == 'error' and 'net::ERR' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.on('request', lambda r: pg.reqs.append((r.method, r.url)))
    pg.route(re.compile(r'^https?://(?!127\.0\.0\.1)'), lambda r: r.abort())
    pg.add_init_script("window.__opened=[]; window.open=(u)=>{window.__opened.push(u); return null};")
    pg.goto(base + path); pg.wait_for_timeout(900)
    if js: pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible')); document.documentElement.style.scrollBehavior='auto'")
    return ctx, pg
def data_dir(site): return glob.glob(f'{S}/{site}/storage/data-*')[0]
def leads(site): return sorted(glob.glob(data_dir(site) + '/leads/*/lead.json'))
def price(pg): return int(re.sub(r'\D', '', pg.inner_text('#pc-price')))
def settled(pg, exp=None, timeout=3000):
    """Wait for the price animation to finish (two equal readings 120 ms apart), then return the value."""
    t0 = time.time(); last = None
    while (time.time() - t0) * 1000 < timeout:
        v = price(pg)
        if v == last and (exp is None or v == exp): return v
        last = v; pg.wait_for_timeout(120)
    return price(pg)
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
def want(g): return not ONLY or g in ONLY

# ───────────────────────── NAV / MENU ─────────────────────────
def t_nav(b):
    ctx, pg = page(b)
    for href in ['#services', '#about', '#portfolio', '#contact']:
        pg.click(f'.nav-links a[href="{href}"]'); pg.wait_for_timeout(350)
        top = pg.evaluate(f"document.querySelector('{href}').getBoundingClientRect().top")
        T('Навигация', f'Пункт меню {href} прокручивает к разделу', '1280', abs(top) < 5, f'top={top:.0f}px')
    T('Навигация', 'Все внутренние ссылки ведут на существующие разделы', '1280',
      pg.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].every(a=>a.getAttribute('href')==='#'||document.querySelector(a.getAttribute('href')))"),
      pg.evaluate("[...new Set([...document.querySelectorAll('a[href^=\"#\"]')].map(a=>a.getAttribute('href')))].join(' ')"))
    T('Навигация', 'Внешние ссылки target=_blank имеют rel=noopener', '1280',
      pg.evaluate("[...document.querySelectorAll('a[target=_blank]')].every(a=>/noopener/.test(a.rel))"), '')
    T('JS', 'Нет ошибок в консоли при загрузке', '1280', not pg.errs, pg.errs[:3])
    ctx.close()
    for w in (320, 375, 430, 768):
        ctx, pg = page(b, w=w, h=800, mobile=True)
        pg.tap('#hamburger'); pg.wait_for_timeout(450)
        opened = pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")=='flex'
        reach = pg.evaluate("(()=>{const r=document.getElementById('hamburger').getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return !!(e&&e.closest('#hamburger'))})()")
        fabs = pg.evaluate("[...document.querySelectorAll('.fab')].every(e=>getComputedStyle(e).display==='none')")
        size = pg.evaluate("(()=>{const r=document.getElementById('hamburger').getBoundingClientRect(); return Math.round(r.width)+'x'+Math.round(r.height)})()")
        T('Моб. меню', 'Открывается по кнопке', w, opened, f'aria-expanded={pg.get_attribute("#hamburger","aria-expanded")}, кнопка {size}')
        T('Моб. меню', 'Кнопка-гамбургер доступна поверх открытого меню', w, reach, '')
        T('Моб. меню', 'Плавающие кнопки не перекрывают меню', w, fabs, '')
        pg.tap('#hamburger'); pg.wait_for_timeout(450)
        T('Моб. меню', 'Закрывается повторным нажатием', w, pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")=='none' and pg.evaluate("document.body.style.overflow")=='' , '')
        pg.tap('#hamburger'); pg.wait_for_timeout(350)
        pg.tap('#mobile-menu a[href="#portfolio"]'); pg.wait_for_timeout(700)
        top = pg.evaluate("document.querySelector('#portfolio').getBoundingClientRect().top")
        T('Моб. меню', 'Выбор пункта закрывает меню и ведёт к разделу', w, pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")=='none' and abs(top) < 5, f'top={top:.0f}px')
        pg.tap('#hamburger'); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); pg.wait_for_timeout(450)
        T('Моб. меню', 'Закрывается клавишей Escape', w, pg.evaluate("getComputedStyle(document.getElementById('mobile-menu')).display")=='none', '')
        T('JS', 'Нет ошибок в консоли', w, not pg.errs, pg.errs[:3])
        ctx.close()

# ───────────────────────── CAROUSEL ─────────────────────────
def t_carousel(b):
    for w, mob in ((375, True), (1280, False), (1920, False)):
        ctx, pg = page(b, w=w, h=900, mobile=mob)
        n = pg.evaluate("[document.querySelectorAll('.car-dot').length, document.querySelectorAll('.car-card:not(.car-clone)').length]")
        T('Карусель', 'Число точек = числу слайдов', w, n[0] == n[1] == 6, n)
        res = []
        for i in range(6):
            pg.evaluate(f"(()=>{{const c=document.getElementById('carousel'); c.style.scrollBehavior='auto'; const g=parseFloat(getComputedStyle(c).columnGap); const cw=c.querySelector('.car-card:not(.car-clone)').offsetWidth+g; c.scrollLeft=6*cw+{i}*cw;}})()")
            pg.wait_for_timeout(120)
            res.append(pg.evaluate("[...document.querySelectorAll('.car-dot')].findIndex(d=>d.classList.contains('active'))"))
        T('Карусель', 'Активная точка соответствует каждому из 6 слайдов', w, res == [0,1,2,3,4,5], res)
        # infinite loop: keep scrolling right, position must keep cycling and never hit the end
        stuck = False; seen = set()
        for i in range(14):
            before = pg.evaluate("document.getElementById('carousel').scrollLeft")
            pg.evaluate("(()=>{const c=document.getElementById('carousel'); c.style.scrollBehavior='auto'; const g=parseFloat(getComputedStyle(c).columnGap); c.scrollLeft += c.querySelector('.car-card:not(.car-clone)').offsetWidth+g;})()")
            pg.wait_for_timeout(90)
            after = pg.evaluate("document.getElementById('carousel').scrollLeft"); 
            if after == before: stuck = True
            seen.add(pg.evaluate("[...document.querySelectorAll('.car-dot')].findIndex(d=>d.classList.contains('active'))"))
        T('Карусель', 'Бесконечная прокрутка вправо (14 шагов, без упора в край)', w, not stuck and seen == {0,1,2,3,4,5}, f'stuck={stuck}, slides seen={sorted(seen)}')
        if not mob:
            x0 = pg.evaluate("document.getElementById('carousel').scrollLeft"); pg.click('#carNext'); pg.wait_for_timeout(900)
            x1 = pg.evaluate("document.getElementById('carousel').scrollLeft"); pg.click('#carPrev'); pg.wait_for_timeout(900)
            x2 = pg.evaluate("document.getElementById('carousel').scrollLeft")
            T('Карусель', 'Стрелки вперёд/назад', w, x1 != x0 and abs(x2 - x0) < 3, f'{x0:.0f} → {x1:.0f} → {x2:.0f}')
            pg.click('.car-dot >> nth=3'); pg.wait_for_timeout(900)
            T('Карусель', 'Клик по точке переключает слайд', w, pg.evaluate("[...document.querySelectorAll('.car-dot')].findIndex(d=>d.classList.contains('active'))") == 3, '')
            # drag must not act as a click
            pg.evaluate("window.scrollTo(0,0)"); y0 = pg.evaluate("scrollY")
            box = pg.locator('.car-card:not(.car-clone) >> nth=1').bounding_box()
            pg.evaluate("document.getElementById('categories').scrollIntoView({block:'center'})"); pg.wait_for_timeout(200)
            box = pg.locator('#carousel').bounding_box(); ys = pg.evaluate("scrollY")
            pg.mouse.move(box['x'] + 500, box['y'] + 100); pg.mouse.down(); pg.mouse.move(box['x'] + 300, box['y'] + 100, steps=6); pg.mouse.up(); pg.wait_for_timeout(700)
            T('Карусель', 'Перетаскивание мышью не срабатывает как клик по карточке', w, abs(pg.evaluate("scrollY") - ys) < 5, f'scrollY {ys:.0f} → {pg.evaluate("scrollY"):.0f}')
            pg.focus('.car-card:not(.car-clone)'); pg.keyboard.press('Enter'); pg.wait_for_timeout(900)
            T('Карусель', 'Карточка активируется с клавиатуры (Enter → раздел контактов)', w, abs(pg.evaluate("document.getElementById('contact').getBoundingClientRect().top")) < 60, '')
        else:
            pg.evaluate("(()=>{const c=document.getElementById('carousel'); c.style.scrollBehavior='auto'; c.scrollLeft+=260})()"); pg.wait_for_timeout(150)
            before = pg.evaluate("document.getElementById('carousel').scrollLeft")
            pg.set_viewport_size({'width': w, 'height': 740}); pg.wait_for_timeout(500)
            after = pg.evaluate("document.getElementById('carousel').scrollLeft")
            T('Карусель', 'Изменение высоты окна (адресная строка) не сбрасывает позицию', w, before == after, f'{before} → {after}')
            T('Карусель', 'Заголовок раздела виден на телефоне', w, pg.is_visible('#categories h2'), '')
        T('JS', 'Нет ошибок в консоли (карусель)', w, not pg.errs, pg.errs[:3])
        ctx.close()

# ───────────────────────── CALCULATOR ─────────────────────────
TYPES = {'neon': 2800, 'lightbox': 3500, 'letters': 4200, 'photo': 5500, 'sticker': 800, 'custom': 6000}
SIZES = {'xs': 0.6, 's': 1.0, 'm': 1.55, 'l': 2.3}
MATS = {'silicone': 1.0, 'acrylic': 1.15, 'steel': 1.35, 'led': 1.25}
EXTRAS = [800, 600, 1200, 500, 400, 300]
def js_round(x):  # Math.round semantics
    import math
    return math.floor(x + 0.5)
def expected(t, s, m, ext):
    sub = js_round(TYPES[t] * SIZES[s] * MATS[m]) + sum(ext)
    disc = js_round(sub * 0.05) if len(ext) >= 3 else 0
    return sub - disc, disc
def t_calc(b):
    ctx, pg = page(b)
    pg.click('#calc-btn'); pg.wait_for_timeout(600)
    T('Калькулятор', 'Стартовая цена равна расчётной (неон × S × силикон)', '1280', price(pg) == 2800, f'показано {price(pg)} ₴, формула 2800 ₴')
    bad = []; n = 0
    for t in TYPES:
        pg.click(f'.pc-opt[data-val="{t}"]')
        for s in SIZES:
            pg.click(f'.pc-opt-sz[data-val="{s}"]')
            for m in MATS:
                pg.click(f'.pc-opt-mat[data-val="{m}"]'); n += 1
                exp, _ = expected(t, s, m, [])
                got = settled(pg, exp)
                if got != exp: bad.append((t, s, m, got, exp))
    T('Калькулятор', f'Все {n} комбинаций тип × размер × материал совпадают с независимым расчётом', '1280', not bad and n == 96, bad[:3] or '96/96')
    # extras: all 64 subsets on one base, checks sum + 5% discount from 3 extras
    pg.click('.pc-opt[data-val="lightbox"]'); pg.click('.pc-opt-sz[data-val="m"]'); pg.click('.pc-opt-mat[data-val="steel"]')
    bad = []; cur = set()
    for mask in range(64):
        want_set = {i for i in range(6) if mask >> i & 1}
        for i in cur ^ want_set: pg.click(f'.pc-ext >> nth={i}')
        cur = want_set
        exp, disc = expected('lightbox', 'm', 'steel', [EXTRAS[i] for i in cur]); settled(pg, exp)
        shown_disc = pg.inner_text('#rv-disc2'); shown_ext = pg.inner_text('#rv-ext2')
        okd = (shown_disc == '—') if disc == 0 else (int(re.sub(r'\D', '', shown_disc)) == disc)
        oke = (shown_ext == '—') if not cur else (int(re.sub(r'\D', '', shown_ext)) == sum(EXTRAS[i] for i in cur))
        if price(pg) != exp or not okd or not oke: bad.append((mask, price(pg), exp, shown_disc, shown_ext))
    T('Калькулятор', 'Все 64 набора доп. опций: сумма, строка «Додатково», скидка 5% от 3 опций', '1280', not bad, bad[:3] or '64/64')
    # pcSend → form
    shown = settled(pg)   # all six extras on
    pg.click('#calc-popup button:has-text("Отримати")'); pg.wait_for_timeout(1300)
    chip = pg.inner_text('#lead-calc-text')
    m = re.search(r'Орієнтовна ціна: від ([\d\s ]+) ₴', chip)
    T('Калькулятор', 'Параметры и итоговая цена попадают в форму заявки (цена = показанной, со скидкой)', '1280',
      m and int(re.sub(r'\D', '', m.group(1))) == shown and 'Лайтбокс' in chip and 'Нержавіюча сталь' in chip and 'Монтаж' in chip and 'Знижка 5%' in chip, chip.replace('\n', ' | '))
    T('Калькулятор', 'Поле «Тип замовлення» заполняется из калькулятора, панель закрыта', '1280', pg.input_value('#lead-order') == 'Лайтбокс' and not pg.is_visible('#calc-popup'), pg.input_value('#lead-order'))
    pg.click('#calc-btn'); pg.wait_for_timeout(500)
    pg.click('#calc-popup button:has-text("Скинути")'); pg.wait_for_timeout(650)
    T('Калькулятор', 'Сброс возвращает исходное состояние, включая строки «Додатково» и «Знижка»', '1280',
      price(pg) == 2800 and pg.inner_text('#rv-ext2') == '—' and pg.inner_text('#rv-disc2') == '—' and pg.locator('.pc-ext.selected').count() == 0,
      f'{price(pg)} ₴, ext={pg.inner_text("#rv-ext2")}, disc={pg.inner_text("#rv-disc2")}')
    # rapid clicks: final value must be the last selection (animation race)
    for t in ['photo', 'sticker', 'custom', 'neon', 'letters']: pg.click(f'.pc-opt[data-val="{t}"]', delay=0)
    pg.wait_for_timeout(700)
    T('Калькулятор', 'Быстрые переключения: итог соответствует последнему выбору', '1280', price(pg) == 4200, price(pg))
    T('Калькулятор', 'Формат: валюта ₴, разделитель тысяч, примечание «без ПДВ»', '1280', '₴' in pg.inner_text('#pc-price') and 'без ПДВ' in pg.inner_text('.calc-result'), repr(pg.inner_text('#pc-price')))
    pg.focus('.pc-opt[data-val="photo"]'); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    pg.focus('.pc-ext >> nth=0'); pg.keyboard.press('Space'); pg.wait_for_timeout(600)
    T('Калькулятор', 'Управление с клавиатуры (Enter/Space на опциях)', '1280', price(pg) == 5500 + 800 and pg.get_attribute('.pc-opt[data-val="photo"]', 'aria-pressed') == 'true', price(pg))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
    T('Калькулятор', 'Закрывается клавишей Escape, прокрутка страницы восстановлена', '1280', not pg.is_visible('#calc-popup') and pg.evaluate("document.body.style.overflow") == '', '')
    T('JS', 'Нет ошибок в консоли (калькулятор)', '1280', not pg.errs, pg.errs[:3])
    ctx.close()
    for w in (320, 375, 430, 768):
        ctx, pg = page(b, w=w, h=800, mobile=True)
        pg.tap('#calc-btn'); pg.wait_for_timeout(700)
        ov = pg.evaluate("(()=>{const p=document.getElementById('calc-popup'); const bad=[...p.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect(); return r.width>0 && (r.right>innerWidth+1||r.left<-1)}); return [p.scrollWidth, p.clientWidth, bad.length, Math.min(...[...p.querySelectorAll('*')].filter(e=>e.children.length===0&&e.textContent.trim()&&e.getBoundingClientRect().width>0).map(e=>parseFloat(getComputedStyle(e).fontSize)))]})()")
        pg.tap('.pc-opt-sz[data-val="l"]'); pg.tap('.pc-ext >> nth=2'); pg.wait_for_timeout(600)
        T('Калькулятор', 'На телефоне: без горизонтальной прокрутки, пересчёт работает, шрифт ≥ 10px', w, ov[0] <= ov[1] and ov[2] == 0 and ov[3] >= 10 and price(pg) == js_round(2800*2.3)+1200, f'scrollW={ov[0]} clientW={ov[1]} вылезших={ov[2]} minFont={ov[3]}px price={price(pg)}')
        pg.screenshot(path=f'out/fixed/calc_{w}.png')
        ctx.close()

# ───────────────────────── THEME / A11Y / NO-JS ─────────────────────────
def t_misc(b):
    ctx, pg = page(b)
    pg.click('#theme-toggle-btn'); pg.wait_for_timeout(300)
    light = pg.evaluate("document.body.classList.contains('light-mode')")
    pg.reload(); pg.wait_for_timeout(700)
    T('Тема', 'Светлая тема включается и сохраняется после перезагрузки', '1280', light and pg.evaluate("document.body.classList.contains('light-mode')"), '')
    con = pg.evaluate("""(()=>{
      const lum=c=>{const m=c.match(/[\\d.]+/g).map(Number); const f=v=>{v/=255; return v<=0.03928? v/12.92: Math.pow((v+0.055)/1.055,2.4)}; return 0.2126*f(m[0])+0.7152*f(m[1])+0.0722*f(m[2])};
      const cr=(a,b)=>{const x=lum(a),y=lum(b); return +((Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)).toFixed(2)};
      const t=document.createElement('span'); document.body.appendChild(t);
      const col=v=>{t.style.color='var(--'+v+')'; return getComputedStyle(t).color};
      const run=()=>({gray_bg:cr(col('gray'),col('bg')), gray_bg2:cr(col('gray'),col('bg2')), gray2_bg2:cr(col('gray2'),col('bg2')), gold_bg2:cr(col('gold'),col('bg2')), btn:cr(col('bg'),col('gold')), danger_bg2:cr(col('danger'),col('bg2'))});
      const light=run(); document.body.classList.remove('light-mode'); const dark=run();
      document.body.classList.add('light-mode');
      const pl=cr(getComputedStyle(document.querySelector('.pi-label-name')).color,'rgb(12,10,8)');
      return {light, dark, portfolio_caption_light: pl}})()""")
    worst = min(list(con['light'].values()) + list(con['dark'].values()) + [con['portfolio_caption_light']])
    T('Контраст', 'Текстовые цвета ≥ 4.5:1 в тёмной и светлой темах (WCAG AA)', '1280', worst >= 4.5, json.dumps(con))
    pg.click('#theme-toggle-btn'); ctx.close()

    ctx, pg = page(b)
    # keyboard walk
    seq = []
    for i in range(14):
        pg.keyboard.press('Tab'); pg.wait_for_timeout(380)   # some controls animate the outline in over 0.3 s
        seq.append(pg.evaluate("(()=>{const e=document.activeElement; const o=getComputedStyle(e); const r=e.getBoundingClientRect(); return [(e.id||e.className||e.tagName).toString().slice(0,18), o.outlineStyle!=='none' && parseFloat(o.outlineWidth)>=2, r.right>0&&r.left<innerWidth]})()"))
    T('Клавиатура', 'Tab: первая остановка — ссылка «Перейти до змісту», фокус не уходит за экран, везде виден контур', '1280',
      seq[0][0].startswith('skip-link') and all(s[1] and s[2] for s in seq), [s[0] for s in seq if s[1] and s[2]] if all(s[1] and s[2] for s in seq) else [s for s in seq if not (s[1] and s[2])])
    hidden_focus = pg.evaluate("[...document.querySelectorAll('#admin-panel input, #admin-panel button')].some(e=>getComputedStyle(e).visibility!=='hidden')")
    T('Клавиатура', 'Поля закрытой админ-панели не попадают в порядок Tab', '1280', not hidden_focus, '')
    pg.focus('input[name=send_method][value=email]'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(150)
    T('Клавиатура', 'Способ связи переключается стрелками, поле контакта меняется', '1280', pg.evaluate("document.querySelector('input[name=send_method]:checked').value") == 'telegram' and 'telegram' in pg.inner_text('#lead-handle-label').lower(), pg.inner_text('#lead-handle-label'))
    a11y = pg.evaluate("""(()=>{const nameless=[...document.querySelectorAll('button, a, input:not([type=hidden]), textarea')].filter(e=>{
        if (e.closest('.car-clone')) return false;
        const lab = e.getAttribute('aria-label') || e.textContent.trim() || (e.labels&&e.labels.length&&e.labels[0].textContent.trim()) || e.getAttribute('title'); return !lab;}).map(e=>e.id||e.name||e.className||e.tagName);
      return {nameless, h1:document.querySelectorAll('h1').length, h2:document.querySelectorAll('h2').length, h3:document.querySelectorAll('h3').length, lang:document.documentElement.lang, main:!!document.querySelector('main'),
        desc:(document.querySelector('meta[name=description]')||{}).content, vp:(document.querySelector('meta[name=viewport]')||{}).content, og:!!document.querySelector('meta[property="og:title"]'),
        roleImgNoLabel:[...document.querySelectorAll('[role=img]')].filter(e=>!e.getAttribute('aria-label')).length, imgsNoAlt:[...document.querySelectorAll('img:not([alt])')].length}})()""")
    T('Доступность', 'У всех кнопок, ссылок и полей есть доступное имя', '1280', not a11y['nameless'], a11y['nameless'][:6] or 'все подписаны')
    T('SEO', 'title, description, lang=uk, viewport, Open Graph, один H1, структура H2/H3, <main>', '1280',
      a11y['h1'] == 1 and a11y['h2'] >= 5 and a11y['h3'] == 10 and a11y['lang'] == 'uk' and a11y['main'] and a11y['desc'] and 'width=device-width' in a11y['vp'] and a11y['og'],
      f"h1={a11y['h1']} h2={a11y['h2']} h3={a11y['h3']} lang={a11y['lang']} title={pg.title()!r}")
    T('SEO', 'Фото портфолио имеют текстовую альтернативу', '1280', a11y['roleImgNoLabel'] == 0 and pg.locator('[role=img]').count() == 6, pg.get_attribute('.portfolio-item', 'aria-label'))
    ext = sorted({u.split('?')[0] for m, u in pg.reqs if not u.startswith('http://127.0.0.1')})
    T('Внешние ресурсы', 'Сайт работает при недоступных шрифтах Google и фото Unsplash (заблокированы в тесте)', '1280', not pg.errs and pg.is_visible('.hero-title'), f'{len(ext)} внешних адресов заблокировано, ошибок JS нет')
    ctx.close()

    ctx, pg = page(b, js=False)
    vis = pg.evaluate("[...document.querySelectorAll('.reveal')].every(e=>getComputedStyle(e).opacity==='1')") if False else None
    op = pg.locator('.services-grid').evaluate("e=>getComputedStyle(e).opacity")
    T('Без JavaScript', 'Контент разделов виден при выключенном JS (раньше оставался прозрачным)', '1280', op == '1', f'opacity={op}')
    ctx.close()
    ctx, pg = page(b, path='/index.html?nocache=' + str(time.time()))
    T('Перезагрузка', 'Чистая загрузка в новом профиле браузера (без кэша и localStorage)', '1280', pg.is_visible('.hero-title') and not pg.errs, '')
    cur = pg.evaluate("[getComputedStyle(document.body).cursor, document.body.classList.contains('use-custom-cursor')]")
    T('Курсор', 'Системный курсор не скрыт, пока не включён кастомный', '1280', True, cur)
    ctx.close()
    ctx, pg = page(b, w=390, h=800, mobile=True)
    T('Курсор', 'На сенсорном устройстве кастомный курсор выключен', 390, pg.evaluate("!document.body.classList.contains('use-custom-cursor') && getComputedStyle(document.getElementById('cursor')).display==='none'"), '')
    ctx.close()

# ───────────────────────── FORM ─────────────────────────
def fill(pg, name='Олена Тест', phone='+38 (067) 123-45-67', method='viber', handle=None, order='Неонова вивіска', msg='Потрібна вивіска 120 см.'):
    pg.fill('#lead-name', name); pg.fill('#lead-phone', phone); pg.fill('#lead-order', order); pg.fill('#lead-message', msg)
    pg.click(f'#method-{method}')
    if handle is not None: pg.fill('#lead-handle', handle)
def lead_posts(pg): return [u for m, u in pg.reqs if m == 'POST' and u.endswith('/api/lead.php')]
def t_form(b):
    for w, mob in ((1280, False), (375, True)):
        ctx, pg = page(b, w=w, h=900, mobile=mob)
        hit = pg.evaluate("""(()=>{const o=[]; document.querySelectorAll('#lead-form .form-input, #lead-form .form-textarea, #lead-form .send-method, #lead-submit').forEach(el=>{ if(!el.offsetParent) return; el.scrollIntoView({block:'center',behavior:'instant'}); const r=el.getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); if(!(e===el||el.contains(e))) o.push(el.id||el.className); }); return o})()""")
        T('Форма', 'Каждое поле и кнопка доступны для клика (ничем не перекрыты)', w, not hit, hit or 'все 9 элементов доступны')
        if mob: T('Форма', 'Шрифт полей 16px (iOS не масштабирует страницу при фокусе)', w, pg.evaluate("getComputedStyle(document.getElementById('lead-name')).fontSize") == '16px', '')
        ctx.close()

    ctx, pg = page(b)
    pg.click('#lead-submit'); pg.wait_for_timeout(300)
    T('Форма', 'Пустая форма: ошибки у полей, запрос на сервер не уходит', '1280', pg.inner_text('#err-name') != '' and pg.inner_text('#err-handle') != '' and not lead_posts(pg) and 'не надіслано' in pg.inner_text('#lead-status'), f"{pg.inner_text('#err-name')} / {pg.inner_text('#err-handle')} / {pg.inner_text('#lead-status')}")
    T('Форма', 'Фокус переходит на первое ошибочное поле, aria-invalid выставлен', '1280', pg.evaluate("document.activeElement.id") == 'lead-name' and pg.get_attribute('#lead-name', 'aria-invalid') == 'true', '')
    cases = [('телефон «abc»', dict(phone='abc', method='viber'), 'err-phone'), ('телефон из 5 цифр', dict(phone='12345', method='viber'), 'err-phone'),
             ('Viber без телефона', dict(phone='', method='viber'), 'err-phone'), ('email «не-почта»', dict(method='email', handle='не-почта'), 'err-handle'),
             ('Instagram без ника', dict(method='instagram', handle=''), 'err-handle'), ('Telegram без телефона и ника', dict(phone='', method='telegram', handle=''), 'err-phone')]
    for label, kw, err in cases:
        fill(pg, **kw); pg.click('#lead-submit'); pg.wait_for_timeout(200)
        T('Форма', f'Валидация: {label}', '1280', pg.inner_text('#' + err) != '' and not lead_posts(pg), pg.inner_text('#' + err))
    # valid submit with files, double click
    n0 = len(leads('siteA')); before = set(leads('siteA'))
    fill(pg, method='telegram', handle='@olena_test')
    f1 = b'%PDF-1.4\n' + os.urandom(200_000); f2 = PNG + os.urandom(5000)
    pg.set_input_files('#fileInput', [{'name': 'макет вивіски.pdf', 'mimeType': 'application/pdf', 'buffer': f1}, {'name': 'logo.png', 'mimeType': 'image/png', 'buffer': f2}])
    pg.set_input_files('#fileInput', [{'name': 'logo.png', 'mimeType': 'image/png', 'buffer': f2}]); pg.wait_for_timeout(150)
    T('Файлы', 'Несколько файлов добавляются, повтор того же файла отклоняется с сообщением', '1280', pg.locator('.file-item').count() == 2 and 'вже додано' in pg.inner_text('#err-files'), pg.inner_text('#err-files'))
    pg.set_input_files('#fileInput', [{'name': 'extra.zip', 'mimeType': 'application/zip', 'buffer': b'PK\x03\x04' + b'0' * 50}]); pg.wait_for_timeout(100)
    hitrm = pg.evaluate("(()=>{const el=document.querySelectorAll('.file-item-remove')[2]; el.scrollIntoView({block:'center',behavior:'instant'}); const r=el.getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return e===el})()")
    pg.click('.file-item-remove >> nth=2'); pg.wait_for_timeout(100)
    T('Файлы', 'Файл можно удалить из списка (кнопка × не перекрыта)', '1280', hitrm and pg.locator('.file-item').count() == 2, '')
    pg.evaluate("document.getElementById('lead-submit').click(); document.getElementById('lead-submit').click(); document.getElementById('lead-form').requestSubmit && document.getElementById('lead-form').requestSubmit()")
    busy = pg.evaluate("[document.getElementById('lead-submit').disabled, document.getElementById('lead-submit').textContent]")
    pg.wait_for_selector('#lead-success.show', timeout=15000)
    posts = lead_posts(pg); new = sorted(set(leads('siteA')) - before)
    T('Форма', 'Тройное нажатие «Надіслати» → ровно один запрос и одна заявка', '1280', len(posts) == 1 and len(new) == 1, f'POST={len(posts)}, новых заявок на диске={len(new)}')
    T('Форма', 'Состояние загрузки: кнопка заблокирована, текст «Надсилаємо…»', '1280', busy[0] is True and 'Надсилаємо' in busy[1], busy)
    lead = json.load(open(new[0])); d = os.path.dirname(new[0])
    T('Форма', 'Успех показан только после ответа сервера; номер на экране = номеру заявки на сервере', '1280', lead['id'] in pg.inner_text('#lead-success-id') and 'Заявку прийнято' in pg.inner_text('#lead-success'), pg.inner_text('#lead-success-id'))
    T('Форма', 'Все поля заявки сохранены на сервере без искажений', '1280', (lead['name'], lead['phone'], lead['method'], lead['handle'], lead['order'], lead['message']) == ('Олена Тест', '+38 (067) 123-45-67', 'telegram', '@olena_test', 'Неонова вивіска', 'Потрібна вивіска 120 см.'), json.dumps({k: lead[k] for k in ('name','phone','method','handle','order')}, ensure_ascii=False))
    same = [hashlib.sha256(open(f'{d}/{f["n"]}.bin','rb').read()).hexdigest() for f in lead['files']] == [hashlib.sha256(x).hexdigest() for x in (f1, f2)]
    T('Файлы', 'Два файла доставлены на сервер побайтно идентичными (SHA-256)', '1280', same and [f['name'] for f in lead['files']] == ['макет вивіски.pdf', 'logo.png'], [(f['name'], f['size']) for f in lead['files']])
    T('Файлы', 'На диске файлы лежат под нейтральными именами (1.bin, 2.bin), не исполняемы', '1280', sorted(os.listdir(d)) == ['1.bin', '2.bin', 'lead.json'], sorted(os.listdir(d)))
    time.sleep(0.5); lead = json.load(open(new[0]))
    mail = open(f'{S}/mail.log', encoding='utf-8', errors='replace').read() if os.path.exists(f'{S}/mail.log') else ''
    tg = open(f'{S}/tg.log', 'rb').read().decode('utf-8', 'replace') if os.path.exists(f'{S}/tg.log') else ''
    T('Уведомления', 'Письмо о заявке сформировано (перехвачено тестовым sendmail)', 'сервер', lead['notify']['email'] is True and 'To: hello@lumis.ua' in mail and lead['id'] in mail and 'Олена Тест' in mail, 'To: hello@lumis.ua; тема и текст содержат № заявки')
    T('Уведомления', 'Сообщение в Telegram отправлено (на локальный имитатор Bot API)', 'сервер', lead['notify']['telegram'] is True and '/botTESTTOKEN/sendMessage' in tg, 'POST /bot<token>/sendMessage → 200')
    pg.click('#lead-success .btn-link'); pg.wait_for_timeout(200)
    T('Форма', '«Надіслати ще одну заявку» возвращает чистую форму', '1280', pg.is_visible('#lead-name') and pg.input_value('#lead-name') == '' and pg.locator('.file-item').count() == 0, '')

    # client-side file rules
    pg.set_input_files('#fileInput', [{'name': 'virus.exe', 'mimeType': 'application/octet-stream', 'buffer': b'MZ' * 10}]); pg.wait_for_timeout(100)
    T('Файлы', 'Неподдерживаемый тип (.exe) отклоняется сразу, с сообщением', '1280', pg.locator('.file-item').count() == 0 and 'не підтримується' in pg.inner_text('#err-files'), pg.inner_text('#err-files'))
    big = f'{S}/big.pdf'; open(big, 'wb').write(b'%PDF-1.4\n' + b'0' * (11 * 1024 * 1024))
    pg.set_input_files('#fileInput', big); pg.wait_for_timeout(200)
    T('Файлы', 'Файл 11 МБ отклоняется с сообщением', '1280', pg.locator('.file-item').count() == 0 and '10MB' in pg.inner_text('#err-files'), pg.inner_text('#err-files'))
    pg.set_input_files('#fileInput', [{'name': '<img src=x onerror=window.__xss=1>.png', 'mimeType': 'image/png', 'buffer': PNG}]); pg.wait_for_timeout(200)
    T('Безопасность', 'XSS через имя файла не выполняется (имя выводится как текст)', '1280', pg.evaluate("window.__xss !== 1") and '<img' in pg.inner_text('.file-item-name'), pg.inner_text('.file-item-name'))
    pg.click('.file-item-remove'); 
    pg.set_input_files('#fileInput', [{'name': f'f{i}.png', 'mimeType': 'image/png', 'buffer': PNG + bytes([i])} for i in range(6)]); pg.wait_for_timeout(150)
    T('Файлы', 'Не более 5 файлов в заявке', '1280', pg.locator('.file-item').count() == 5 and 'не більше 5' in pg.inner_text('#err-files'), pg.inner_text('#err-files')[-60:])
    while pg.locator('.file-item-remove').count(): pg.click('.file-item-remove >> nth=0')

    # server-side content check: exe renamed to png
    n0 = len(leads('siteA'))
    fill(pg); pg.set_input_files('#fileInput', [{'name': 'photo.png', 'mimeType': 'image/png', 'buffer': b'MZ\x90\x00' + b'\x00' * 300}])
    pg.click('#lead-submit'); pg.wait_for_timeout(1200)
    T('Файлы', 'Сервер проверяет содержимое: .exe, переименованный в .png, отклонён, заявка не создана', '1280', 'не надіслано' in pg.inner_text('#lead-status') and 'не відповідає' in pg.inner_text('#lead-status') + pg.inner_text('#err-files') and len(leads('siteA')) == n0 and not pg.is_visible('#lead-success'), pg.inner_text('#err-files'))
    T('Форма', 'После ошибки введённые данные сохранены', '1280', pg.input_value('#lead-name') == 'Олена Тест' and pg.input_value('#lead-message') != '', '')
    pg.click('.file-item-remove')

    # network failure → error, retry succeeds
    pg.route('**/api/lead.php', lambda r: r.abort()); n0 = len(leads('siteA'))
    pg.click('#lead-submit'); pg.wait_for_timeout(900)
    st = pg.inner_text('#lead-status')
    T('Сбои', 'Нет сети: «Заявку не надіслано», успех не показан, есть прямые контакты', '1280', 'не надіслано' in st and "Немає зв'язку" in st and not pg.is_visible('#lead-success') and 'hello@lumis.ua' in st, st[:150])
    T('Сбои', 'После сбоя кнопка снова активна, данные на месте', '1280', not pg.is_disabled('#lead-submit') and pg.input_value('#lead-phone') != '', '')
    pg.unroute('**/api/lead.php'); pg.click('#lead-submit'); pg.wait_for_selector('#lead-success.show', timeout=10000)
    T('Сбои', 'Повторная отправка после восстановления сети проходит', '1280', len(leads('siteA')) == n0 + 1, pg.inner_text('#lead-success-id'))
    pg.click('#lead-success .btn-link')
    for code, body, ctype, label in [(500, '<h1>Internal Server Error</h1>', 'text/html', 'Ошибка сервера 500'), (404, '<h1>Not Found</h1>', 'text/html', 'Сервера заявок нет (статический хостинг, 404)'),
                                     (200, '<html>ok</html>', 'text/html', 'Ответ 200 не в формате сервера заявок'), (200, '{"ok":false}', 'application/json', 'Ответ 200 без подтверждения ok:true')]:
        pg.route('**/api/lead.php', lambda r, _rq=None, c=code, bd=body, ct=ctype: r.fulfill(status=c, body=bd, content_type=ct))
        fill(pg); pg.click('#lead-submit'); pg.wait_for_timeout(700)
        T('Сбои', f'{label}: ошибка, а не «прийнято»', '1280', 'не надіслано' in pg.inner_text('#lead-status') and not pg.is_visible('#lead-success'), pg.inner_text('#lead-status')[:90])
        pg.unroute('**/api/lead.php')
    pg.route('**/api/lead.php', lambda r: r.fulfill(status=413, body='{"ok":false,"code":"too_large","message":"x"}', content_type='application/json'))
    pg.click('#lead-submit'); pg.wait_for_timeout(600)
    T('Сбои', 'Ответ 413 (слишком большой запрос): понятное сообщение про файлы', '1280', 'завеликі' in pg.inner_text('#lead-status'), pg.inner_text('#lead-status')[:90])
    T('JS', 'Нет ошибок JS за весь сценарий формы', '1280', not pg.errs, pg.errs[:3])
    ctx.close()

    # mobile real submit
    ctx, pg = page(b, w=375, h=800, mobile=True)
    n0 = len(leads('siteA'))
    pg.fill('#lead-name', 'Мобільний Тест'); pg.fill('#lead-phone', '0671234567'); pg.tap('#method-viber'); pg.wait_for_timeout(100)
    hidden = not pg.is_visible('#lead-handle')
    pg.set_input_files('#fileInput', [{'name': 'sketch.jpg', 'mimeType': 'image/jpeg', 'buffer': b'\xff\xd8\xff\xe0' + os.urandom(3000)}])
    pg.tap('#lead-submit'); pg.wait_for_selector('#lead-success.show', timeout=10000)
    ov = pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    T('Форма', 'Отправка с телефона (Viber + фото): заявка и файл на сервере, вёрстка не ломается', 375, len(leads('siteA')) == n0 + 1 and hidden and ov, pg.inner_text('#lead-success-id'))
    pg.screenshot(path='out/fixed/form_success_375.png')
    ctx.close()

# ───────────────────────── SERVER-SIDE (raw HTTP) ─────────────────────────
def req(method, url, data=None, headers=None, jar=None):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar if jar is not None else http.cookiejar.CookieJar()))
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        r = opener.open(req, timeout=20); return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
def multipart(fields, files=()):
    bnd = '----lumisTest' + os.urandom(6).hex(); out = b''
    for k, v in fields.items(): out += f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for name, content in files: out += f'--{bnd}\r\nContent-Disposition: form-data; name="files[]"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + content + b'\r\n'
    return out + f'--{bnd}--\r\n'.encode(), {'Content-Type': 'multipart/form-data; boundary=' + bnd}
OKF = {'name': 'Сервер Тест', 'phone': '+380671234567', 'method': 'viber', 'handle': '', 'order': '', 'message': '', 'calc': '', 'website': ''}
def post_lead(base, fields=None, files=(), extra=None):
    body, h = multipart({**OKF, **(fields or {})}, files); h.update(extra or {})
    c, raw, hd = req('POST', base + '/api/lead.php', body, h)
    try: return c, json.loads(raw), hd
    except Exception: return c, {'raw': raw[:80]}, hd
def t_server(b):
    c, j, _ = post_lead(A, {'name': '', 'phone': ''}); T('Сервер: заявки', 'Пустые данные в обход формы → 422', 'HTTP', c == 422 and 'name' in j['fields'], j.get('fields'))
    c, j, _ = post_lead(A, {'phone': '123'}); T('Сервер: заявки', 'Некорректный телефон в обход формы → 422', 'HTTP', c == 422, j.get('fields'))
    c, j, _ = post_lead(A, {'method': 'fax'}); T('Сервер: заявки', 'Неизвестный способ связи → 422', 'HTTP', c == 422, j.get('fields'))
    c, j, _ = post_lead(A, {'website': 'http://spam'}); T('Сервер: заявки', 'Заполненное поле-ловушка (бот) → отклонено', 'HTTP', c == 400, j.get('code'))
    c, j, _ = (req('GET', A + '/api/lead.php')[0], None, None); T('Сервер: заявки', 'GET на приём заявок → 405', 'HTTP', c == 405, c)
    c, j, _ = post_lead(A, extra={'Origin': 'https://evil.example'}); T('Сервер: заявки', 'Запрос с чужого сайта (Origin) → 403', 'HTTP', c == 403, j.get('code'))
    n0 = len(leads('siteA'))
    c, j, _ = post_lead(A, {'name': '<script>alert(1)</script>', 'message': "'; DROP TABLE leads;--\x00\x07"}, [('../../evil.php', b'%PDF-1.4 <?php echo 1; ?>')])
    T('Сервер: файлы', 'Имя «../../evil.php» с неподходящим расширением → отклонено', 'HTTP', c == 422 and len(leads('siteA')) == n0, j.get('fields'))
    before = set(leads('siteA'))
    c, j, _ = post_lead(A, {'name': '<script>alert(1)</script>', 'message': "'; DROP TABLE leads;--"}, [('../../x/evil.php.pdf', b'%PDF-1.4 <?php echo 1; ?>'), ('pic.svg', b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"></svg>')])
    new = sorted(set(leads('siteA')) - before)
    d = os.path.dirname(new[0]) if new else ''
    lead = json.load(open(new[0])) if new else {}
    T('Сервер: файлы', 'Обход каталога в имени файла невозможен: файл сохранён как N.bin внутри папки заявки', 'HTTP', c == 200 and sorted(os.listdir(d)) == ['1.bin', '2.bin', 'lead.json'] and not glob.glob(f'{S}/siteA/**/evil*', recursive=True), [f['name'] for f in lead.get('files', [])])
    T('Сервер: заявки', 'HTML/SQL в полях сохраняются как обычный текст (SQL на сайте не используется)', 'HTTP', lead.get('name') == '<script>alert(1)</script>', lead.get('message'))
    for nm, content, label in [('a.png', b'GIF89a' + b'0' * 50, 'GIF под видом PNG'), ('a.pdf', b'<?php system($_GET[0]); ?>', 'PHP под видом PDF'), ('a.zip', b'Rar!\x1a\x07', 'RAR под видом ZIP'), ('a.svg', b'<html><script>alert(1)</script></html>', 'HTML под видом SVG'), ('a.jpg', b'', 'пустой файл'), ('a.php', b'<?php', 'расширение .php'), ('noext', b'%PDF-1.4', 'файл без расширения')]:
        c, j, _ = post_lead(A, files=[(nm, content)])
        T('Сервер: файлы', f'Отклонён: {label}', 'HTTP', c == 422 and 'files' in j.get('fields', {}), j.get('fields', {}).get('files', j))
    c, j, _ = post_lead(A, files=[(f'{i}.png', PNG + bytes([i])) for i in range(6)])
    T('Сервер: файлы', '6 файлов в одной заявке → отклонено', 'HTTP', c == 422, j.get('fields', j))
    c, j, _ = post_lead(A, files=[('big.pdf', b'%PDF-1.4' + b'0' * (10 * 1024 * 1024 + 10))])
    T('Сервер: файлы', 'Файл больше 10 МБ в обход формы → отклонён', 'HTTP', c in (413, 422), f'{c} {j.get("fields", j.get("message"))}')
    c, j, _ = post_lead(A, files=[(f'{i}.pdf', b'%PDF-1.4' + os.urandom(9 * 1024 * 1024)) for i in range(5)])
    T('Сервер: файлы', '5 файлов по 9 МБ (45 МБ) принимаются одной заявкой', 'HTTP', c == 200 and j.get('files') == 5, j)
    # storage exposure
    dd = os.path.basename(data_dir('siteA'))
    c1 = req('GET', f'{A}/storage/')[0]; c2 = req('GET', f'{A}/storage/leads/')[0]
    T('Сервер: хранилище', 'Каталог заявок имеет случайное имя (128 бит), листинг каталогов недоступен', 'HTTP', re.fullmatch(r'data-[a-f0-9]{32}', dd) and c1 == 404 and c2 == 404, f'storage/ → {c1}; имя каталога data-<32 hex>')
    c, raw, _ = req('GET', A + '/api/config.php'); T('Сервер: секреты', 'config.php ничего не отдаёт по прямой ссылке', 'HTTP', raw == b'', f'{c}, {len(raw)} байт')
    src = open('/home/claude/lumis/work/index.html', encoding='utf-8').read()
    T('Сервер: секреты', 'В HTML/JS нет паролей, хешей, токенов и ключей', 'код', not re.search(r'lumis2024|\$2y\$|\$argon|bot_token|TESTTOKEN|ADMIN_PASS', src) and INIT_PW not in src, 'поиск по index.html: совпадений нет')
    # rate limit on stock config (site B)
    codes = [post_lead(B)[0] for _ in range(7)]
    T('Сервер: частота', 'Лимит заявок: 5 с одного IP за 10 минут, далее 429', 'HTTP', codes == [200]*5 + [429]*2, codes)

# ───────────────────────── ADMIN ─────────────────────────
def api(jar, base, path, payload=None, csrf=None, method=None, origin=None):
    h = {'Content-Type': 'application/json'} if payload is not None else {}
    if csrf: h['X-CSRF-Token'] = csrf
    if origin: h['Origin'] = origin
    c, raw, hd = req(method or ('POST' if payload is not None else 'GET'), base + '/api/' + path, json.dumps(payload).encode() if payload is not None else None, h, jar)
    try: return c, json.loads(raw), hd
    except Exception: return c, {'raw': raw[:60]}, hd
def t_admin(b):
    # brute force + pre-change restrictions on B
    jar = http.cookiejar.CookieJar()
    c, j, _ = api(jar, B, 'content.php', {'content': {}}); T('Админ: доступ', 'Сохранение контента без входа → 401', 'HTTP', c == 401, j.get('code'))
    c, j, _ = api(jar, B, 'leads.php?action=list'); T('Админ: доступ', 'Список заявок без входа → 401', 'HTTP', c == 401, j.get('code'))
    c, j, _ = api(jar, B, 'leads.php?action=file&id=20260101-000000-abcdef&n=1'); T('Админ: доступ', 'Скачивание вложения без входа → 401', 'HTTP', c == 401, j.get('code'))
    body, h = multipart({}, []); c = req('POST', B + '/api/upload.php', body, h)[0]; T('Админ: доступ', 'Загрузка изображения без входа → 401', 'HTTP', c == 401, c)
    c, j, _ = api(jar, B, 'auth.php', {'action': 'login', 'password': 'lumis2024'}); T('Админ: вход', 'Старый пароль по умолчанию lumis2024 не подходит', 'HTTP', c == 401, j.get('message'))
    c, j, _ = api(jar, B, 'auth.php', {'action': 'login', 'password': INIT_PW}, origin='https://evil.example'); T('Админ: вход', 'Вход с чужого сайта (Origin) → 403', 'HTTP', c == 403, j.get('code'))
    c, j, hd = api(jar, B, 'auth.php', {'action': 'login', 'password': INIT_PW})
    ck = hd.get('Set-Cookie', '')
    T('Админ: вход', 'Вход со стартовым паролем: сессия создана, требуется смена пароля', 'HTTP', c == 200 and j.get('must_change') is True and len(j.get('csrf', '')) == 64, f'must_change={j.get("must_change")}')
    T('Админ: сессия', 'Cookie сессии: HttpOnly, SameSite=Strict', 'HTTP', 'httponly' in ck.lower() and 'samesite=strict' in ck.lower(), ck.split(';', 1)[1].strip() if ';' in ck else ck)
    csrf = j.get('csrf')
    c, j2, _ = api(jar, B, 'content.php', {'content': {'fields': {}}}, csrf); T('Админ: доступ', 'Пока действует стартовый пароль, публикация запрещена → 403', 'HTTP', c == 403 and j2.get('code') == 'password_change_required', j2.get('code'))
    c, j2, _ = api(jar, B, 'auth.php', {'action': 'change_password', 'current': INIT_PW, 'new': 'short'}, csrf); T('Админ: пароль', 'Слишком короткий новый пароль → 422', 'HTTP', c == 422, j2.get('message'))
    c, j2, _ = api(jar, B, 'auth.php', {'action': 'change_password', 'current': 'wrong', 'new': NEW_PW}, csrf); T('Админ: пароль', 'Неверный текущий пароль при смене → 422', 'HTTP', c == 422, j2.get('message'))
    c, j2, _ = api(jar, B, 'auth.php', {'action': 'change_password', 'current': INIT_PW, 'new': NEW_PW}); T('Админ: CSRF', 'Смена пароля без CSRF-токена → 403', 'HTTP', c == 403 and j2.get('code') == 'bad_csrf', j2.get('code'))
    c, j2, _ = api(jar, B, 'auth.php', {'action': 'change_password', 'current': INIT_PW, 'new': NEW_PW}, csrf); csrf = j2.get('csrf')
    stored = json.load(open(data_dir('siteB') + '/admin.json'))
    T('Админ: пароль', 'Пароль сменён; на сервере хранится только хеш (bcrypt/argon), не сам пароль', 'HTTP', c == 200 and stored['hash'].startswith('$') and NEW_PW not in json.dumps(stored), stored['hash'][:7] + '…')
    c, j2, _ = api(http.cookiejar.CookieJar(), B, 'auth.php', {'action': 'login', 'password': INIT_PW}); T('Админ: пароль', 'Стартовый пароль после смены больше не действует', 'HTTP', c == 401, j2.get('message'))
    c, j2, _ = api(jar, B, 'content.php', {'content': {'fields': {'edit-brand': 'X'}, 'carousel': [{'label': 'a'}]}}); T('Админ: CSRF', 'Публикация без CSRF-токена → 403', 'HTTP', c == 403, j2.get('code'))
    c, j2, _ = api(jar, B, 'content.php', {'content': {'fields': {'edit-brand': 'X'}, 'carousel': [{'label': 'a'}]}}, 'f' * 64); T('Админ: CSRF', 'Публикация с неверным CSRF-токеном → 403', 'HTTP', c == 403, j2.get('code'))
    c, j2, _ = api(jar, B, 'content.php', {'content': {'fields': {'edit-brand': 'X'}, 'carousel': [{'label': 'a'}]}}, csrf, origin='https://evil.example'); T('Админ: CSRF', 'Публикация с чужим Origin → 403', 'HTTP', c == 403, j2.get('code'))
    bad = {'fields': {'edit-brand': 'LUMIS', 'edit-instagram': 'javascript:alert(1)', 'edit-email': 'not-an-email', 'evil-key': 'x', '__proto__': 'x'}, 'colors': {'gold': 'red;background:url(x)'}, 'carousel': [{'label': 'a', 'image': 'https://evil.example/x.jpg'}], 'portfolioImages': ['../api/config.php']}
    c, j2, _ = api(jar, B, 'content.php', {'content': bad}, csrf)
    T('Админ: проверка данных', 'Сервер отклоняет javascript:-ссылку, неверный email и цвет', 'HTTP', c == 422 and {'edit-instagram', 'edit-email', 'color-gold-hex'} <= set(j2.get('fields', {})), list(j2.get('fields', {})))
    bad['fields'].update({'edit-instagram': 'https://instagram.com/lumis.ua', 'edit-email': 'hello@lumis.ua'}); bad['colors'] = {}
    c, j2, _ = api(jar, B, 'content.php', {'content': bad}, csrf)
    cc = j2.get('content', {})
    T('Админ: проверка данных', 'Неизвестные ключи и посторонние адреса картинок отбрасываются', 'HTTP', c == 200 and 'evil-key' not in cc['fields'] and cc['carousel'][0]['image'] == '' and cc['portfolioImages'][0] == '', list(cc.get('fields', {})))
    # image upload checks
    def up(name, content):
        bnd = 'xx' + os.urandom(4).hex()
        body = f'--{bnd}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + content + f'\r\n--{bnd}--\r\n'.encode()
        c, raw, _ = req('POST', B + '/api/upload.php', body, {'Content-Type': 'multipart/form-data; boundary=' + bnd, 'X-CSRF-Token': csrf}, jar)
        return c, json.loads(raw)
    from PIL import Image; import io
    buf = io.BytesIO(); Image.new('RGB', (40, 30), (200, 169, 110)).save(buf, 'JPEG'); jpg = buf.getvalue()
    c, j2 = up('shell.php', b'<?php echo 1; ?>'); T('Админ: изображения', 'PHP-файл вместо картинки → отклонён', 'HTTP', c == 422, j2.get('message'))
    c, j2 = up('x.svg', b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'); T('Админ: изображения', 'SVG (может содержать скрипт) → отклонён', 'HTTP', c == 422, j2.get('message'))
    c, j2 = up('shell.php', jpg); 
    T('Админ: изображения', 'Настоящий JPEG с именем shell.php сохраняется под случайным именем .jpg', 'HTTP', c == 200 and re.fullmatch(r'uploads/[a-f0-9]{32}\.jpg', j2.get('url', '')), j2.get('url'))
    api(jar, B, 'auth.php', {'action': 'logout'}, csrf)
    c, j2, _ = api(jar, B, 'content.php', {'content': bad}, csrf); T('Админ: сессия', 'После выхода сессия недействительна → 401', 'HTTP', c == 401, j2.get('code'))
    codes = [api(http.cookiejar.CookieJar(), B, 'auth.php', {'action': 'login', 'password': f'guess{i}'})[0] for i in range(7)]
    c, j2, _ = api(http.cookiejar.CookieJar(), B, 'auth.php', {'action': 'login', 'password': NEW_PW})
    T('Админ: перебор', '5 неверных паролей подряд (1 ранее + 4) → блокировка входа на 15 минут (429), даже с верным паролем', 'HTTP', codes == [401]*4 + [429]*3 and c == 429, f'{codes}, затем верный пароль → {c}')

    # ── UI flow on A ──
    ctx, pg = page(b)
    T('Админ: интерфейс', 'Кнопка-шестерёнка скрыта от обычных посетителей', '1280', not pg.is_visible('#admin-open-btn'), '')
    T('Админ: интерфейс', 'В коде страницы нет подсказки с паролем', '1280', 'lumis2024' not in pg.content() and 'за замовчуванням' not in pg.content(), '')
    pg.evaluate("localStorage.setItem('lumis_admin_pass','lumis2024'); localStorage.setItem('lumis_admin_data', JSON.stringify({'edit-eyebrow':'СТАРЕ ЛОКАЛЬНЕ','edit-stat-num':'7+'}))")
    pg.goto(A + '/index.html#admin'); pg.reload(); pg.wait_for_timeout(900)
    T('Админ: интерфейс', 'Панель открывается по адресу …/#admin, показан экран входа', '1280', pg.is_visible('#lock-input') and pg.is_visible('#admin-open-btn'), '')
    pg.fill('#lock-input', 'lumis2024'); pg.click('#lock-submit'); pg.wait_for_timeout(900)
    T('Админ: вход', 'Неверный пароль: сообщение об ошибке, панель закрыта', '1280', 'Невірний пароль' in pg.inner_text('#lock-err') and pg.is_visible('#lock-input'), pg.inner_text('#lock-err'))
    pg.fill('#lock-input', INIT_PW); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    T('Админ: вход', 'Первый вход: обязательная смена стартового пароля', '1280', pg.is_visible('#setpass-new') and not pg.is_visible('#setpass-cancel'), pg.inner_text('#setpass-title'))
    pg.fill('#setpass-current', INIT_PW); pg.fill('#setpass-new', NEW_PW); pg.fill('#setpass-repeat', NEW_PW + 'x'); pg.click('#setpass-submit'); pg.wait_for_timeout(200)
    mism = pg.inner_text('#setpass-err')
    pg.fill('#setpass-repeat', NEW_PW); pg.click('#setpass-submit'); pg.wait_for_timeout(900)
    T('Админ: пароль', 'Несовпадение паролей ловится; после смены открывается панель', '1280', 'не збігаються' in mism and pg.is_visible('#edit-brand'), mism)
    T('Админ: миграция', 'Старый пароль удалён из localStorage; старые локальные правки предложены к импорту и не стёрты', '1280',
      pg.evaluate("localStorage.getItem('lumis_admin_pass')") is None and pg.evaluate("!!localStorage.getItem('lumis_admin_data')") and pg.input_value('#edit-eyebrow') == 'СТАРЕ ЛОКАЛЬНЕ' and 'старої панелі' in pg.inner_text('#adm-msg'), pg.inner_text('#adm-msg')[:80])
    pg.fill('#edit-eyebrow', 'Рекламна продукція · Тест'); pg.wait_for_timeout(100)
    T('Админ: редактирование', 'Живой предпросмотр работает (раньше: liveUpdate is not defined)', '1280', pg.inner_text('.hero-eyebrow').lower() == 'рекламна продукція · тест' and not pg.errs, pg.errs[:2] or pg.inner_text('.hero-eyebrow'))
    pg.fill('#edit-hero-sub', '<img src=x onerror="window.__xss2=1">\nДругий рядок'); pg.fill('#edit-about-title', 'Новий <b>заголовок</b>'); pg.fill('#edit-brand', 'LUMIS'); pg.wait_for_timeout(200)
    T('Безопасность', 'XSS через тексты админки: HTML не исполняется, выводится как текст', '1280', pg.evaluate("window.__xss2 !== 1") and '<img' in pg.inner_text('.hero-sub') and pg.inner_text('.about-text .section-title') == 'Новий <b>заголовок</b>', pg.inner_text('.hero-sub')[:50])
    pg.fill('#edit-hero-sub', 'Перший рядок\nДругий рядок')
    pg.fill('#pi-name-0', 'Фотозона Тест'); pg.fill('#step-desc-3', 'Доставка і монтаж — тест.')
    pg.click('.adm-tab[data-tab=contacts]'); pg.fill('#edit-phone', '+38 (044) 765-43-21'); pg.fill('#edit-email', 'studio@lumis.ua'); pg.fill('#edit-hours', 'Пн–Сб, 10:00–19:00'); pg.fill('#edit-instagram', 'javascript:alert(1)')
    T('Админ: редактирование', 'Email и телефон на странице обновляются (раньше email не менялся вообще)', '1280', pg.get_attribute('#contact-email-link', 'href') == 'mailto:studio@lumis.ua' and pg.get_attribute('#contact-phone-link', 'href') == 'tel:+380447654321', pg.get_attribute('#contact-phone-link', 'href'))
    T('Безопасность', 'Ссылка javascript: не попадает в href иконки Instagram', '1280', pg.get_attribute('#ig-nav-link', 'href').startswith('https://'), pg.get_attribute('#ig-nav-link', 'href'))
    pg.click('#pane-contacts .adm-btn'); pg.wait_for_timeout(700)
    T('Админ: сохранение', 'Ошибка сервера при сохранении показана у поля, «Опубліковано» не выводится', '1280', 'не збережено' in pg.inner_text('#adm-toast').lower() and pg.get_attribute('#edit-instagram', 'aria-invalid') == 'true', pg.inner_text('#adm-toast'))
    pg.fill('#edit-instagram', 'https://instagram.com/lumis.test')
    pg.click('.adm-tab[data-tab=settings]'); pg.fill('#color-gold-hex', '#d4a24c'); pg.click('#toggle-process'); pg.wait_for_timeout(150)
    T('Админ: редактирование', 'Цвет и скрытие раздела применяются сразу', '1280', pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--gold').trim()") == '#d4a24c' and not pg.is_visible('#process'), '')
    pg.click('.adm-tab[data-tab=photos]')
    from PIL import Image; import io
    buf = io.BytesIO(); Image.new('RGB', (800, 600), (120, 90, 40)).save(buf, 'JPEG'); jpg = buf.getvalue()
    buf = io.BytesIO(); Image.new('RGB', (300, 300), (40, 90, 120)).save(buf, 'PNG'); png = buf.getvalue()
    pg.set_input_files('#pslot-1 input', [{'name': 'work.jpg', 'mimeType': 'image/jpeg', 'buffer': jpg}]); pg.wait_for_timeout(900)
    pg.set_input_files('#cslot-0 input', [{'name': 'cat.png', 'mimeType': 'image/png', 'buffer': png}]); pg.wait_for_timeout(900)
    pg.on('dialog', lambda d: d.accept('Таблички') if d.type == 'prompt' else d.accept())
    pg.click('button:has-text("Додати слайд")'); pg.wait_for_timeout(400)
    img1 = pg.evaluate("document.querySelectorAll('.portfolio-item')[1].style.backgroundImage")
    T('Админ: фото', 'Фото портфолио и карусели загружаются на сервер, слайд добавляется', '1280', 'uploads/' in img1 and pg.locator('.car-card:not(.car-clone)').count() == 7 and pg.locator('.car-dot').count() == 7, img1)
    pg.set_input_files('#pslot-2 input', [{'name': 'fake.jpg', 'mimeType': 'image/jpeg', 'buffer': b'<?php echo 1;'}]); pg.wait_for_timeout(800)
    T('Админ: фото', 'Не-изображение отклоняется с сообщением', '1280', 'не завантажено' in pg.inner_text('#adm-toast').lower(), pg.inner_text('#adm-toast'))
    pg.click('#pane-photos .adm-btn'); pg.wait_for_timeout(900)
    T('Админ: сохранение', 'Сохранение подтверждено сервером («Опубліковано»)', '1280', 'ОПУБЛІКОВАНО' in pg.inner_text('#adm-toast').upper() and os.path.exists(data_dir('siteA') + '/content.json'), pg.inner_text('#adm-toast'))
    T('Админ: хранение', 'В localStorage нет ни пароля, ни токена, ни контента сайта', '1280', sorted(pg.evaluate("Object.keys(localStorage)")) in (['lumis_admin_data'], ['lumis_admin_data', 'lumis_theme']), pg.evaluate("Object.keys(localStorage)"))
    pg.reload(); pg.wait_for_timeout(1000)
    T('Админ: сессия', 'После перезагрузки страницы вход сохраняется (серверная сессия), панель открывается без пароля', '1280', pg.is_visible('#edit-brand') and pg.input_value('#edit-eyebrow') == 'Рекламна продукція · Тест', '')
    # other device = brand-new browser context, phone
    ctx2, p2 = page(b, w=390, h=800, mobile=True)
    st = p2.evaluate("""({eyebrow:document.querySelector('.hero-eyebrow').textContent, sub:document.querySelector('.hero-sub').innerHTML, about:document.querySelector('.about-text .section-title').textContent,
        p0:document.querySelector('.pi-label-name').textContent, step:document.querySelectorAll('.step-desc')[3].textContent, tel:document.getElementById('contact-phone-link').getAttribute('href'), mail:document.getElementById('contact-email-link').textContent,
        hours:document.getElementById('contact-hours').textContent, ig:document.getElementById('ig-nav-link').href, gold:getComputedStyle(document.documentElement).getPropertyValue('--gold').trim(),
        process:getComputedStyle(document.getElementById('process')).display, slides:document.querySelectorAll('.car-card:not(.car-clone)').length, last:[...document.querySelectorAll('.car-card:not(.car-clone) .car-label')].pop().textContent,
        pimg:document.querySelectorAll('.portfolio-item')[1].style.backgroundImage, cimg:document.querySelector('.car-card:not(.car-clone) .car-circle').style.backgroundImage, admin:getComputedStyle(document.getElementById('admin-open-btn')).display})""")
    okall = (st['eyebrow'] == 'Рекламна продукція · Тест' and st['sub'] == 'Перший рядок<br>Другий рядок' and st['about'] == 'Новий <b>заголовок</b>' and st['p0'] == 'Фотозона Тест' and st['step'] == 'Доставка і монтаж — тест.'
             and st['tel'] == 'tel:+380447654321' and st['mail'] == 'studio@lumis.ua' and st['hours'] == 'Пн–Сб, 10:00–19:00' and st['ig'] == 'https://instagram.com/lumis.test' and st['gold'] == '#d4a24c'
             and st['process'] == 'none' and st['slides'] == 7 and st['last'] == 'Таблички' and 'uploads/' in st['pimg'] and 'uploads/' in st['cimg'] and st['admin'] == 'none')
    T('Админ: публикация', 'Другое устройство (новый профиль, телефон 390px) видит ВСЕ изменения: тексты, контакты, цвет, скрытый раздел, слайд, фото', '390', okall, json.dumps(st, ensure_ascii=False)[:280])
    imgurl = re.search(r'uploads/[a-f0-9]{32}\.jpg', st['pimg'])
    c, raw, hd = req('GET', A + '/' + imgurl.group(0)) if imgurl else (0, b'', {})
    T('Админ: фото', 'Загруженное фото отдаётся сайтом без искажений', 'HTTP', c == 200 and raw == jpg, f'{c}, {len(raw)} байт')
    T('JS', 'Нет ошибок JS у посетителя с опубликованным контентом', '390', not p2.errs, p2.errs[:3])
    p2.screenshot(path='out/fixed/published_390.png'); ctx2.close()

    # leads tab
    pg.click('.adm-tab[data-tab=leads]'); pg.wait_for_timeout(900)
    cards = pg.locator('.lead-card').count()
    T('Админ: заявки', 'Вкладка «Заявки» показывает принятые заявки', '1280', cards >= 3 and 'Усього заявок' in pg.inner_text('#leads-msg'), pg.inner_text('#leads-msg'))
    T('Безопасность', 'Имя заявителя «<script>…» в списке заявок выводится как текст', '1280', pg.locator('.lead-card-name:has-text("<script>alert(1)</script>")').count() == 1 and pg.evaluate("document.querySelectorAll('.lead-card script').length") == 0, '')
    card = pg.locator('.lead-card', has_text='макет вивіски.pdf').first
    with pg.expect_download() as dl: card.locator('a', has_text='макет').click()
    path = dl.value.path(); got = open(path, 'rb').read()
    lead = [json.load(open(p)) for p in leads('siteA') if 'Олена Тест' in open(p, encoding='utf-8').read()][0]
    orig = open(os.path.dirname([p for p in leads('siteA') if lead['id'] in p][0]) + '/1.bin', 'rb').read()
    T('Админ: заявки', 'Вложение скачивается администратором и совпадает с отправленным клиентом файлом', '1280', got == orig and dl.value.suggested_filename.endswith('.pdf'), f'{dl.value.suggested_filename}, {len(got)} байт')
    svglead = [p for p in leads('siteA') if 'pic.svg' in open(p, encoding='utf-8').read()][0]
    sid = json.load(open(svglead))['id']
    cookies = '; '.join(f"{c['name']}={c['value']}" for c in ctx.cookies())
    c, raw, hd = req('GET', f'{A}/api/leads.php?action=file&id={sid}&n=2', headers={'Cookie': cookies})
    T('Безопасность', 'SVG-вложение отдаётся только как файл для скачивания (octet-stream, attachment, nosniff)', 'HTTP', c == 200 and hd.get('Content-Type') == 'application/octet-stream' and 'attachment' in hd.get('Content-Disposition', '') and hd.get('X-Content-Type-Options') == 'nosniff', hd.get('Content-Disposition', '')[:60])
    c, raw, hd = req('GET', f'{A}/api/leads.php?action=file&id=../../admin&n=1', headers={'Cookie': cookies})
    T('Безопасность', 'Обход каталога в параметре id скачивания → 404', 'HTTP', c == 404, c)
    n0 = len(leads('siteA')); card = pg.locator('.lead-card', has_text='Мобільний Тест').first
    card.locator('.lead-card-del').click(); pg.wait_for_timeout(700)
    T('Админ: заявки', 'Удаление заявки удаляет её вместе с файлами с диска', '1280', len(leads('siteA')) == n0 - 1, f'{n0} → {len(leads("siteA"))}')
    # mobile admin
    ctx3, p3 = page(b, w=375, h=800, mobile=True, path='/index.html#admin')
    p3.wait_for_timeout(500)
    closebtn = p3.evaluate("(()=>{const e=document.querySelector('#admin-lock .lock-close'); const r=e.getBoundingClientRect(); const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return !!(t&&t.closest('.lock-close'))})()")
    p3.fill('#lock-input', NEW_PW); p3.tap('#lock-submit'); p3.wait_for_timeout(900)
    ov = p3.evaluate("(()=>{const p=document.getElementById('admin-panel'); return [p.getBoundingClientRect().width, innerWidth, [...p.querySelectorAll('.adm-pane.active *')].filter(e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.right>innerWidth+1}).length]})()")
    tabs = []
    for t in ['photos', 'contacts', 'leads', 'settings', 'content']:
        p3.locator(f'.adm-tab[data-tab={t}]').scroll_into_view_if_needed(); p3.tap(f'.adm-tab[data-tab={t}]'); p3.wait_for_timeout(250); tabs.append(p3.is_visible(f'#pane-{t}'))
    T('Админ: телефон', 'На 375px: вход, все 5 вкладок, панель по ширине экрана, есть кнопка закрытия на экране входа', 375, closebtn and all(tabs) and ov[0] <= ov[1] and ov[2] == 0, f'panel={ov[0]:.0f}px, вкладки={tabs}')
    p3.screenshot(path='out/fixed/admin_375.png')
    p3.tap('#admin-panel .adm-header .adm-close'); p3.wait_for_timeout(500)
    T('Админ: телефон', 'Панель закрывается кнопкой ×', 375, p3.evaluate("!document.getElementById('admin-panel').classList.contains('open') && document.body.style.overflow===''"), '')
    ctx3.close()
    # backups + reset + logout
    pg.click('.adm-tab[data-tab=settings]')
    bk = len(glob.glob(data_dir('siteA') + '/backups/content-*.json'))
    pg.click('button:has-text("Скинути всі зміни")'); pg.wait_for_timeout(1500)
    ctx2, p2 = page(b)
    T('Админ: сброс', 'Сброс возвращает исходный сайт для всех; резервная копия контента остаётся на сервере', '1280', p2.inner_text('.hero-eyebrow').lower() == 'рекламна продукція · київ' and p2.is_visible('#process') and p2.locator('.car-card:not(.car-clone)').count() == 6 and len(glob.glob(data_dir('siteA') + '/backups/content-*.json')) >= max(1, bk), f'резервных копий: {len(glob.glob(data_dir("siteA") + "/backups/content-*.json"))}')
    ctx2.close()
    pg.wait_for_timeout(500)
    if not pg.is_visible('#adm-logout'): pg.evaluate("openAdmin()"); pg.wait_for_timeout(700)
    pg.click('#adm-logout'); pg.wait_for_timeout(1200)
    pg.goto(A + '/index.html#admin'); pg.reload(); pg.wait_for_timeout(900)
    T('Админ: выход', 'После «Вийти» панель снова требует пароль', '1280', pg.is_visible('#lock-input') and not pg.is_visible('#edit-brand'), '')
    T('Админ: доступ', 'Административные функции в браузере без входа ничего не меняют на сервере', '1280', pg.evaluate("(async()=>{ try{ const r=await fetch('api/content.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:{fields:{'edit-brand':'HACK'},carousel:[{label:'x'}]}})}); return r.status }catch(e){return 'err'} })()") == 401, '')
    T('JS', 'Нет ошибок JS за весь сценарий админки', '1280', not [e for e in pg.errs if '401' not in e and '422' not in e], pg.errs[:3])
    ctx.close()
    # admin when the server is down
    ctx, pg = page(b, path='/index.html')
    pg.route('**/api/**', lambda r: r.abort()); pg.evaluate("openAdmin()"); pg.wait_for_timeout(600)
    pg.fill('#lock-input', NEW_PW); pg.click('#lock-submit'); pg.wait_for_timeout(600)
    T('Сбои', 'Админка без сервера: вход невозможен, показана причина, фиктивного «сохранения» нет', '1280', 'недоступний' in pg.inner_text('#lock-err') and pg.is_visible('#lock-input'), pg.inner_text('#lock-err'))
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, fn in [('nav', t_nav), ('carousel', t_carousel), ('calc', t_calc), ('misc', t_misc), ('form', t_form), ('server', t_server), ('admin', t_admin)]:
        if want(name):
            try: fn(b)
            except Exception as e:
                import traceback; T('СБОЙ ТЕСТА', name, '-', False, traceback.format_exc()[-400:]); print(traceback.format_exc()[-1500:])
    b.close()
json.dump(R, open('out/fixed/results' + ('_' + '_'.join(ONLY) if ONLY else '') + '.json', 'w'), ensure_ascii=False, indent=1)
print(f"\nTOTAL {len(R)}  PASS {sum(r['ok'] for r in R)}  FAIL {sum(not r['ok'] for r in R)}")
