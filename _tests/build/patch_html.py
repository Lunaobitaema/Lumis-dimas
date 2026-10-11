"""Markup edits (head, body, calculator, admin). Every replacement is asserted."""
import re

def apply(s):
    def rep(old, new, count=1):
        nonlocal s
        n = s.count(old)
        assert n == count, f'expected {count} got {n}: {old[:80]!r}'
        s = s.replace(old, new)
    def cut(start, end, new):
        """Replace everything from marker `start` up to (not including) marker `end`."""
        nonlocal s
        assert s.count(start) == 1 and s.count(end) == 1, (start[:50], s.count(start), end[:50], s.count(end))
        a = s.index(start); b = s.index(end)
        assert a < b
        s = s[:a] + new + s[b:]

    # ── HEAD ──
    rep('<html lang="uk">', '<html lang="uk" class="no-js">')
    rep('<title>LUMIS — Рекламна продукція</title>\n', '''<title>LUMIS — Рекламна продукція</title>
<meta name="description" content="LUMIS — студія рекламної продукції у Києві: фотозони, лайтбокси, наліпки, об'ємні літери, неонові вивіски та індивідуальні замовлення.">
<meta name="theme-color" content="#0c0a08">
<meta property="og:type" content="website">
<meta property="og:locale" content="uk_UA">
<meta property="og:title" content="LUMIS — Рекламна продукція">
<meta property="og:description" content="Фотозони, лайтбокси, наліпки, об'ємні літери, неонові вивіски та індивідуальні замовлення. Київ.">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://images.unsplash.com; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&amp;family=Montserrat:wght@200;300;400;500&amp;display=swap">
<script>document.documentElement.className = 'js';</script>
''')

    # a hidden <br> on phones must not glue two words together
    rep('лайтбокси, наліпки,<br>об\'ємні літери', 'лайтбокси, наліпки, <br>об\'ємні літери')
    # ── CURSOR / NAV ──
    rep('<div class="cursor" id="cursor"></div>\n<div class="cursor-ring" id="cursorRing"></div>',
        '<a class="skip-link" href="#main">Перейти до змісту</a>\n<div class="cursor" id="cursor" aria-hidden="true"></div>\n<div class="cursor-ring" id="cursorRing" aria-hidden="true"></div>')
    rep('<a href="#" class="nav-logo">', '<a href="#hero" class="nav-logo" aria-label="LUMIS — на початок сторінки">')
    rep('<a id="ig-nav-link" href="https://instagram.com/lumis.ua" target="_blank" class="ig-icon-btn" title="Instagram">',
        '<a id="ig-nav-link" href="https://instagram.com/lumis.ua" target="_blank" rel="noopener noreferrer" class="ig-icon-btn" title="Instagram" aria-label="Instagram LUMIS (відкриється в новій вкладці)">')
    rep('<a id="ig-footer-link" href="https://instagram.com/lumis.ua" target="_blank" class="ig-icon-btn" title="Наш Instagram">',
        '<a id="ig-footer-link" href="https://instagram.com/lumis.ua" target="_blank" rel="noopener noreferrer" class="ig-icon-btn" title="Наш Instagram" aria-label="Instagram LUMIS (відкриється в новій вкладці)">')
    rep('<button id="hamburger" onclick="toggleMenu()" aria-label="Меню" style="display:none;background:none;border:none;color:var(--gold);cursor:pointer;padding:4px;flex-direction:column;gap:5px;align-items:center;justify-content:center;width:32px;height:32px;">',
        '<button id="hamburger" type="button" onclick="toggleMenu()" aria-label="Меню" aria-expanded="false" aria-controls="mobile-menu" style="display:none;background:none;border:none;color:var(--gold);cursor:pointer;padding:4px;flex-direction:column;gap:5px;align-items:center;justify-content:center;">')
    rep('<div id="mobile-menu" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:var(--bg);z-index:998;flex-direction:column;align-items:center;justify-content:center;gap:32px;opacity:0;transition:opacity 0.3s;">',
        '<div id="mobile-menu" role="dialog" aria-modal="true" aria-label="Меню" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:var(--bg);z-index:998;flex-direction:column;align-items:center;justify-content:center;gap:32px;opacity:0;transition:opacity 0.3s;">')
    rep('font-family:\'Montserrat\',sans-serif;font-size:10px;letter-spacing:0.3em;text-transform:uppercase;padding:14px 36px;text-decoration:none;">Замовити</a>\n</div>',
        'font-family:\'Montserrat\',sans-serif;font-size:12px;letter-spacing:0.3em;text-transform:uppercase;padding:16px 36px;text-decoration:none;">Замовити</a>\n</div>')

    # ── MAIN landmark ──
    rep('<!-- HERO -->\n<section class="hero" id="hero">', '<main id="main">\n<!-- HERO -->\n<section class="hero" id="hero">')
    rep('<!-- FOOTER -->\n<footer>', '</main>\n\n<!-- FOOTER -->\n<footer>')

    # ── CATEGORIES: inline layout → classes (so media queries apply) ──
    rep('<section id="categories" style="padding: 100px 0; overflow:hidden; background: var(--bg);">\n  <div style="padding: 0 60px;" class="reveal">',
        '<section id="categories">\n  <div class="cat-head reveal">')
    rep('<div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom: 52px;">', '<div class="cat-head-row">')
    s2 = re.sub(r'<a href="#contact" style="font-size:10px; letter-spacing:0\.3em;[^>]*>Всі колекції →</a>', '<a href="#contact" class="cat-link">Всі колекції →</a>', s)
    assert s2 != s; s = s2
    rep('<!-- Track wrapper -->\n  <div style="position:relative;">', '<!-- Track wrapper -->\n  <div class="car-wrap">')
    s2 = re.sub(r'<button id="carPrev" onclick="carScroll\(-1\)" style="[^"]*">', '<button id="carPrev" class="car-arrow" type="button" onclick="carScroll(-1)" aria-label="Попередні категорії">', s)
    assert s2 != s; s = s2
    s2 = re.sub(r'<button id="carNext" onclick="carScroll\(1\)" style="[^"]*">', '<button id="carNext" class="car-arrow" type="button" onclick="carScroll(1)" aria-label="Наступні категорії">', s)
    assert s2 != s; s = s2
    s2 = re.sub(r'<div id="carousel" style="[^"]*">', '<div id="carousel">', s); assert s2 != s; s = s2
    rep('''  <div id="carDots" style="display:flex; justify-content:center; gap:8px; margin-top:32px; padding:0 60px;">
    <div class="car-dot active"></div>
    <div class="car-dot"></div>
    <div class="car-dot"></div>
  </div>''', '''  <div id="carDots" role="group" aria-label="Перемикання слайдів"></div>''')
    rep('''<div class="car-card" onclick="document.getElementById('contact').scrollIntoView({behavior:'smooth'})">''',
        '''<div class="car-card" role="link" tabindex="0" onclick="goToContact()">''', 6)

    # "135deg" is not valid inside radial-gradient(), so the browser dropped these backgrounds entirely
    assert s.count('radial-gradient(135deg at') == 10
    s = s.replace('radial-gradient(135deg at', 'radial-gradient(circle at')
    # ── SERVICES / PROCESS: real headings ──
    s, n = re.subn(r'<div class="service-name">(.*?)</div>', r'<h3 class="service-name">\1</h3>', s); assert n == 6
    s, n = re.subn(r'<div class="step-name">(.*?)</div>', r'<h3 class="step-name">\1</h3>', s); assert n == 4
    rep('<section id="about" style="padding: 120px 60px;">', '<section id="about">')
    rep('<section id="process" style="padding:120px 60px;">', '<section id="process">')

    # ── PORTFOLIO: background photos need a text alternative ──
    def port(m):
        return f'<div class="portfolio-item" role="img" aria-label="{m.group(2)} — {m.group(3)}" style="{m.group(1)}">' + m.group(0)[m.group(0).index('>')+1:]
    s, n = re.subn(r'<div class="portfolio-item" style="([^"]*)">\s*<div style="[^"]*"></div>\s*<div class="pi-label">\s*<div class="pi-label-name">([^<]*)</div>\s*<div class="pi-label-type">([^<]*)</div>', port, s)
    assert n == 6

    # ── CONTACTS ──
    rep('<div class="contact-item-value"><a href="tel:+380441234567">+38 (044) 123-45-67</a></div>',
        '<div class="contact-item-value"><a id="contact-phone-link" href="tel:+380441234567">+38 (044) 123-45-67</a></div>')
    # The saved page carried Cloudflare's obfuscated address ("[email protected]") without the script that decodes it.
    rep('<div class="contact-item-value"><a href="/cdn-cgi/l/email-protection#573f323b3b38173b223a3e24792236"><span class="__cf_email__" data-cfemail="a1c9c4cdcdcee1cdd4ccc8d28fd4c0">[email&#160;protected]</span></a></div>',
        '<div class="contact-item-value"><a id="contact-email-link" href="mailto:hello@lumis.ua">hello@lumis.ua</a></div>')
    rep('<div class="contact-item-value">Київ, вул. Хрещатик, 1</div>', '<div class="contact-item-value" id="contact-address">Київ, вул. Хрещатик, 1</div>')
    rep('<div class="contact-item-value">Пн–Пт, 9:00–18:00</div>', '<div class="contact-item-value" id="contact-hours">Пн–Пт, 9:00–18:00</div>')

    # ── FORM ──
    methods_a = s.index('        <label class="send-method" id="method-email">')
    methods_b = s.index('      </div>\n    </div>\n\n    <button class="form-submit" onclick="submitForm(event)">')
    methods = s[methods_a:methods_b]
    methods = methods.replace('<svg width="16"', '<svg aria-hidden="true" width="16"')
    cut('  <div class="contact-form reveal">', '</section>\n\n</main>', f'''  <form class="contact-form reveal" id="lead-form" novalidate aria-label="Заявка на замовлення">
   <div class="contact-form-body" id="lead-form-body">
    <div class="form-row">
      <div class="form-group">
        <label class="form-label" for="lead-name">Ім'я <span class="form-req" aria-hidden="true">*</span></label>
        <input class="form-input" id="lead-name" name="name" type="text" placeholder="Ваше ім'я" autocomplete="name" maxlength="100" required aria-describedby="err-name">
        <div class="form-error" id="err-name" role="alert"></div>
      </div>
      <div class="form-group">
        <label class="form-label" for="lead-phone">Телефон <span class="form-req" id="lead-phone-req" aria-hidden="true" hidden>*</span></label>
        <input class="form-input" id="lead-phone" name="phone" type="tel" inputmode="tel" placeholder="+38 (0__)" autocomplete="tel" maxlength="40" aria-describedby="err-phone">
        <div class="form-error" id="err-phone" role="alert"></div>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label" for="lead-order">Тип замовлення</label>
      <input class="form-input" id="lead-order" name="order" type="text" placeholder="Лайтбокс, неон, фотозона…" maxlength="150">
    </div>
    <div class="form-group">
      <label class="form-label" for="lead-message">Повідомлення</label>
      <textarea class="form-textarea" id="lead-message" name="message" placeholder="Опишіть ваш проєкт..." maxlength="3000"></textarea>
    </div>

    <!-- Розрахунок, переданий з калькулятора -->
    <div class="calc-chip" id="lead-calc" hidden>
      <span id="lead-calc-text"></span>
      <button type="button" onclick="clearCalcFromForm()" aria-label="Прибрати розрахунок із заявки">×</button>
    </div>

    <!-- FILE UPLOAD -->
    <div class="form-group">
      <label class="form-label" for="fileInput">Прикріпити файл <span style="color:var(--gray);font-size:10px;letter-spacing:0.1em;">(необов'язково)</span></label>
      <div class="file-drop-zone" id="fileDropZone">
        <input type="file" id="fileInput" multiple accept=".jpg,.jpeg,.png,.pdf,.ai,.eps,.svg,.zip" onchange="handleFiles(this.files); this.value='';" aria-describedby="file-hint err-files">
        <div class="file-drop-inner" id="fileDropInner">
          <svg aria-hidden="true" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <span class="file-drop-text">Перетягніть файли або <u>оберіть</u></span>
          <span class="file-drop-hint" id="file-hint">JPG, PNG, PDF, AI, EPS, SVG, ZIP · до 10MB · до 5 файлів</span>
        </div>
      </div>
      <div class="file-list" id="fileList"></div>
      <div class="form-error" id="err-files" role="alert"></div>
    </div>

    <!-- SEND METHOD -->
    <div class="form-group">
      <span class="form-label" id="lead-method-label">Як з вами зв'язатись</span>
      <div class="send-methods" role="radiogroup" aria-labelledby="lead-method-label">
{methods}      </div>
    </div>
    <div class="form-group" id="lead-handle-group">
      <label class="form-label" for="lead-handle"><span id="lead-handle-label">Ваш email</span> <span class="form-req" id="lead-handle-req" aria-hidden="true">*</span></label>
      <input class="form-input" id="lead-handle" name="handle" type="email" placeholder="name@example.com" autocomplete="email" maxlength="120" aria-describedby="err-handle">
      <div class="form-error" id="err-handle" role="alert"></div>
    </div>

    <div class="form-hp" aria-hidden="true">
      <label>Не заповнюйте це поле <input type="text" name="website" tabindex="-1" autocomplete="off"></label>
    </div>

    <div class="lead-status" id="lead-status" role="alert" hidden></div>
    <div class="form-actions">
      <button class="form-submit" type="submit" id="lead-submit">Надіслати запит</button>
    </div>
   </div>

   <div class="form-success" id="lead-success" tabindex="-1" role="status">
      <svg class="form-success-icon" aria-hidden="true" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="9 12 11 14 15 10"/>
      </svg>
      <div class="form-success-title">Заявку прийнято</div>
      <div class="form-success-id" id="lead-success-id"></div>
      <div class="form-success-sub">Ми зв'яжемось з вами найближчим часом</div>
      <div class="form-success-links" id="lead-success-links"></div>
      <button type="button" class="btn-link" onclick="resetLeadForm()">Надіслати ще одну заявку</button>
   </div>
  </form>
''')

    # ── FIXED BUTTONS ──
    s2 = re.sub(r'<button onclick="openAdmin\(\)" title="Адмін панель" style="[^"]*" onmouseenter="[^"]*" onmouseleave="[^"]*">',
                '<button id="admin-open-btn" class="fab" type="button" onclick="openAdmin()" title="Адмін панель" aria-label="Адмін панель">', s); assert s2 != s; s = s2
    s2 = re.sub(r'<button id="calc-btn" onclick="toggleCalc\(\)" title="Калькулятор вартості" style="[^"]*" onmouseenter="[^"]*" onmouseleave="[^"]*">',
                '<button id="calc-btn" class="fab" type="button" onclick="toggleCalc()" title="Калькулятор вартості" aria-label="Калькулятор вартості" aria-expanded="false" aria-controls="calc-popup">', s); assert s2 != s; s = s2
    rep('<button class="theme-toggle" id="theme-toggle-btn" onclick="toggleTheme()" title="Змінити тему" style="position:fixed;bottom:28px;right:28px;z-index:1000;cursor:pointer;width:48px;height:48px;box-shadow:0 4px 24px rgba(200,169,110,0.2);">',
        '<button class="theme-toggle fab" id="theme-toggle-btn" type="button" onclick="toggleTheme()" title="Змінити тему" aria-label="Змінити тему (світла / темна)">')
    s = s.replace('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/>',
                  '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/>')

    # ── CALCULATOR ──
    a = s.index('<!-- CALC PANEL (full) -->'); b = s.index('<!-- THEME TOGGLE (fixed) -->')
    c = s[a:b]
    def r1(old, new, count=1):
        nonlocal c
        assert c.count(old) == count, (old[:70], c.count(old)); c = c.replace(old, new)
    c2 = re.sub(r'<div id="calc-popup" style="', '<div id="calc-popup" role="dialog" aria-modal="true" aria-label="Калькулятор вартості" tabindex="-1" style="', c); assert c2 != c; c = c2
    r1('<div style="padding:28px 40px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg2);z-index:10;backdrop-filter:blur(8px);">', '<div class="calc-head">')
    r1('<button onclick="toggleCalc()" style="background:none;', '<button type="button" onclick="toggleCalc()" aria-label="Закрити калькулятор" style="background:none;')
    r1('<div style="background:var(--bg2);padding:40px;">', '<div class="calc-steps">')
    r1('<div style="background:var(--bg3);padding:36px 28px;display:flex;flex-direction:column;gap:16px;position:sticky;top:90px;align-self:start;">', '<div class="calc-result">')
    r1('<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;" id="pc-size">', '<div id="pc-size">')
    r1('<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;" id="pc-material">', '<div id="pc-material">')
    # type scale inside the calculator (all inline): 8→10, 8.5→11, 9→11, 10→12, 11→13
    c = re.sub(r'font-size:(8|8\.5|9|10|11)px', lambda m: 'font-size:' + {'8':'10','8.5':'11','9':'11','10':'12','11':'13'}[m.group(1)] + 'px', c)
    c = c.replace('letter-spacing:0.5em', 'letter-spacing:0.36em').replace('letter-spacing:0.45em', 'letter-spacing:0.3em')
    r1('<button onclick="pcSend()" style="width:100%;background:var(--gold);color:var(--bg);border:none;font-family:\'Montserrat\',sans-serif;font-size:11px;font-weight:500;letter-spacing:0.3em;',
       '<button type="button" onclick="pcSend()" style="width:100%;background:var(--gold);color:var(--bg);border:none;font-family:\'Montserrat\',sans-serif;font-size:11px;font-weight:500;letter-spacing:0.2em;')
    r1('<button onclick="pcReset()"', '<button type="button" onclick="pcReset()"')
    # the static figure contradicted the formula (neon 2800 × S 1.0 × silicone 1.0 = 2800)
    r1('>3 200 <span style="font-size:18px;color:var(--gray2);">₴</span></div>', ' aria-live="polite">2 800 <span style="font-size:18px;color:var(--gray2);">₴</span></div>')
    r1('<span id="rv-type2" style="font-size:11px;letter-spacing:0.08em;color:var(--white);text-align:right;">', '<span id="rv-type2" style="font-size:11px;letter-spacing:0.08em;color:var(--white);text-align:right;">')
    s = s[:a] + c + s[b:]

    # ── ADMIN ──
    rep('<div id="admin-overlay" onclick="closeAdmin()"></div>', '<div id="admin-overlay" onclick="closeAdmin()"></div>')
    rep('<!-- ADMIN PANEL -->\n<div id="admin-panel">', '<!-- ADMIN PANEL -->\n<div id="admin-panel" class="locked" role="dialog" aria-modal="true" aria-label="Адмін панель">')
    cut('  <!-- PASSWORD LOCK -->', '  <!-- HEADER -->', '''  <!-- PASSWORD LOCK -->
  <div id="admin-lock">
    <button class="adm-close lock-close" type="button" onclick="closeAdmin()" aria-label="Закрити панель">
      <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/></svg>
    </button>
    <div class="lock-logo">LUMIS</div>
    <div class="lock-sub">Адміністративна панель</div>
    <div class="adm-field" style="width:100%;max-width:280px;">
      <label class="adm-label" for="lock-input">Пароль</label>
      <input id="lock-input" class="adm-input" type="password" placeholder="••••••••" autocomplete="current-password" onkeydown="if(event.key==='Enter')checkPass()">
    </div>
    <div class="lock-err" id="lock-err" role="alert"></div>
    <button class="adm-btn" type="button" id="lock-submit" style="max-width:280px;" onclick="checkPass()">Увійти</button>
  </div>

  <!-- SET / CHANGE PASSWORD -->
  <div id="admin-setpass" class="hidden">
    <button class="adm-close lock-close" type="button" onclick="closeAdmin()" aria-label="Закрити панель">
      <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/></svg>
    </button>
    <div class="lock-logo">LUMIS</div>
    <div class="lock-sub" id="setpass-title">Задайте власний пароль</div>
    <div class="adm-field" style="width:100%;max-width:280px;">
      <label class="adm-label" for="setpass-current">Поточний пароль</label>
      <input id="setpass-current" class="adm-input" type="password" autocomplete="current-password">
    </div>
    <div class="adm-field" style="width:100%;max-width:280px;">
      <label class="adm-label" for="setpass-new">Новий пароль (від 10 символів)</label>
      <input id="setpass-new" class="adm-input" type="password" autocomplete="new-password" minlength="10">
    </div>
    <div class="adm-field" style="width:100%;max-width:280px;">
      <label class="adm-label" for="setpass-repeat">Повторіть новий пароль</label>
      <input id="setpass-repeat" class="adm-input" type="password" autocomplete="new-password" onkeydown="if(event.key==='Enter')submitNewPass()">
    </div>
    <div class="lock-err" id="setpass-err" role="alert"></div>
    <button class="adm-btn" type="button" id="setpass-submit" style="max-width:280px;" onclick="submitNewPass()">Зберегти пароль</button>
    <button class="adm-btn secondary" type="button" id="setpass-cancel" style="max-width:280px;" onclick="cancelNewPass()">Скасувати</button>
  </div>

''')
    rep('''    <button class="adm-close" onclick="closeAdmin()">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
        <line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/>
      </svg>
    </button>''', '''    <div class="adm-head-actions">
      <button class="adm-logout" type="button" id="adm-logout" onclick="logoutAdmin()">Вийти</button>
      <button class="adm-close" type="button" onclick="closeAdmin()" aria-label="Закрити панель">
        <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
          <line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/>
        </svg>
      </button>
    </div>''')
    rep('''    <button class="adm-tab active" onclick="switchTab('content')">Контент</button>
    <button class="adm-tab" onclick="switchTab('photos')">Фото</button>
    <button class="adm-tab" onclick="switchTab('contacts')">Контакти</button>
    <button class="adm-tab" onclick="switchTab('settings')">Налаштування</button>''',
        '''    <button class="adm-tab active" type="button" data-tab="content" onclick="switchTab('content')">Контент</button>
    <button class="adm-tab" type="button" data-tab="photos" onclick="switchTab('photos')">Фото</button>
    <button class="adm-tab" type="button" data-tab="contacts" onclick="switchTab('contacts')">Контакти</button>
    <button class="adm-tab" type="button" data-tab="leads" onclick="switchTab('leads')">Заявки</button>
    <button class="adm-tab" type="button" data-tab="settings" onclick="switchTab('settings')">Налаштування</button>''')
    rep('  <div class="adm-content">\n    <div class="adm-pane active" id="pane-content">', '  <div class="adm-content">\n    <div class="adm-msg" id="adm-msg" role="status" hidden></div>\n    <div class="adm-pane active" id="pane-content">')
    rep('    <!-- SETTINGS TAB -->', '''    <!-- LEADS TAB -->
    <div class="adm-pane" id="pane-leads">
      <div class="adm-section">
        <div class="adm-section-title">Заявки з сайту</div>
        <div class="adm-msg" id="leads-msg" role="status" hidden></div>
        <div id="leads-list"></div>
        <button class="adm-btn secondary" type="button" onclick="loadLeads()">Оновити список</button>
      </div>
    </div>

    <!-- SETTINGS TAB -->''')
    # labels ↔ fields
    def link_label(m):
        return f'<label class="adm-label" for="{m.group(2)}">{m.group(1)}</label>\n          <{m.group(3)} class="{m.group(4)}" id="{m.group(2)}"'
    s, n = re.subn(r'<label class="adm-label">([^<]*)</label>\n          <(input|textarea) class="(adm-input|adm-textarea)" id="([a-z-]+)"',
                   lambda m: f'<label class="adm-label" for="{m.group(4)}">{m.group(1)}</label>\n          <{m.group(2)} class="{m.group(3)}" id="{m.group(4)}"', s)
    assert n >= 12, n
    s, n = re.subn(r'<div class="adm-toggle on" id="(toggle-[a-z]+)" onclick="([^"]*)"></div>',
                   r'<div class="adm-toggle on" id="\1" role="switch" aria-checked="true" tabindex="0" onclick="\2"></div>', s); assert n == 4
    rep('<span class="adm-toggle-label">Показувати карусель категорій</span>', '<span class="adm-toggle-label" id="lbl-toggle-carousel">Показувати карусель категорій</span>')
    rep('<input type="color" id="color-gold" value="#c8a96e"', '<input type="color" id="color-gold" aria-label="Акцентний колір" value="#c8a96e"')
    rep('<input type="color" id="color-bg" value="#0c0a08"', '<input type="color" id="color-bg" aria-label="Фоновий колір" value="#0c0a08"')
    rep('<input class="adm-input" id="color-gold-hex" value="#c8a96e"', '<input class="adm-input" id="color-gold-hex" aria-label="Акцентний колір, hex" value="#c8a96e"')
    rep('<input class="adm-input" id="color-bg-hex" value="#0c0a08"', '<input class="adm-input" id="color-bg-hex" aria-label="Фоновий колір, hex" value="#0c0a08"')
    s = s.replace('<button class="adm-btn" onclick="saveAll()">', '<button class="adm-btn" type="button" onclick="saveAll()">')
    rep('<div class="adm-toast" id="adm-toast">Збережено</div>', '<div class="adm-toast" id="adm-toast" role="status" aria-live="polite"></div>')
    rep('Клікніть на слот щоб завантажити фото.<br>Формати: JPG, PNG, WEBP. Макс. 5MB.', 'Клікніть на слот, щоб завантажити фото.<br>Формати: JPG, PNG, WEBP. Макс. 5MB. Фото з\'явиться на сайті після «Зберегти».')

    return s
