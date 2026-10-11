"""CSS edits. Operates on text `s`, returns new text. Every replacement is asserted."""
import re

def apply(s):
    def rep(old, new, count=1):
        nonlocal s
        n = s.count(old)
        assert n == count, f'expected {count} got {n}: {old[:70]!r}'
        s = s.replace(old, new)

    def in_rule(sel, old, new, nth=0):
        """Replace a declaration inside the nth rule whose selector line is exactly `sel {`."""
        nonlocal s
        starts = [m.start() for m in re.finditer(r'(?m)^' + re.escape(sel) + r'\s*\{', s)]
        assert len(starts) > nth, f'rule not found: {sel}'
        a = starts[nth]; b = s.index('}', a)
        block = s[a:b]
        assert old in block, f'{old!r} not in rule {sel}'
        s = s[:a] + block.replace(old, new, 1) + s[b:]

    # ── 1. Fonts: render-blocking @import → <link> in <head> (see patch_html) ──
    rep("@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Montserrat:wght@200;300;400;500&display=swap');\n\n", "")

    # ── 2. Colour tokens: tertiary text was 2.6:1 on the dark background ──
    rep("  --gray:      #5a5550;\n  --gray2:     #888078;", "  --gray:      #857d74;\n  --gray2:     #9a9289;\n  --danger:    #e08a8a;")
    rep("  --gold:      #9e6f34;\n  --gold2:     #b8833e;\n  --gray:      #b8a898;\n  --gray2:     #7a6858;",
        "  --gold:      #875c28;\n  --gold2:     #a06f32;\n  --gray:      #6b5a4b;\n  --gray2:     #5c4c3e;\n  --danger:    #a33a3a;")

    # ── 3. Cursor: system cursor by default, custom one only when JS enables it on a mouse device ──
    rep("""  overflow-x: hidden;
  cursor: none;
}
/* Touch devices: restore cursor so taps work */
@media (pointer: coarse) {
  body, body * { cursor: auto !important; }
  .cursor, .cursor-ring { display: none !important; }
}

/* ── CUSTOM CURSOR ── */
/* Desktop custom cursor for non-touch */
@media (pointer: fine) {
  .use-custom-cursor { cursor: none; }
  .use-custom-cursor a,
  .use-custom-cursor button,
  .use-custom-cursor [onclick],
  .use-custom-cursor input,
  .use-custom-cursor textarea,
  .use-custom-cursor select { cursor: none; }
}
.cursor {""", """  overflow-x: hidden;
}

/* ── CUSTOM CURSOR ── */
/* The system cursor stays visible unless JS turns the custom one on (mouse devices only). */
.cursor, .cursor-ring { display: none; }
@media (hover: hover) and (pointer: fine) {
  .use-custom-cursor, .use-custom-cursor * { cursor: none !important; }
  .use-custom-cursor .cursor, .use-custom-cursor .cursor-ring { display: block; }
}
.cursor {""")
    # ── 4. Broken selector before the duplicated @media block (orig. line 1145) ──
    rep("""body.light-mode /* Desktop custom cursor for non-touch */
@media (pointer: fine) {
  .use-custom-cursor { cursor: none; }
  .use-custom-cursor a,
  .use-custom-cursor button,
  .use-custom-cursor [onclick],
  .use-custom-cursor input,
  .use-custom-cursor textarea,
  .use-custom-cursor select { cursor: none; }
}
.cursor { background: var(--gold); }
""", """/* Portfolio captions sit on a dark gradient over the photo in both themes */
body.light-mode .pi-label-name { color: #f5f0e8; }
body.light-mode .pi-label-type { color: #e2c38a; }
body.light-mode .lead-status.is-error { background: rgba(163,58,58,0.06); }
""")

    # stray "cursor:none" declarations elsewhere would hide the pointer when the custom cursor is off
    s = s.replace('cursor: none;', 'cursor: pointer;')
    rep("  cursor: pointer;\n}\n.portfolio-item > div:first-child", "}\n.portfolio-item > div:first-child")  # portfolio tiles are not links

    # ── 5. Orphaned media-query bodies with stray braces (orig. lines 1315–1326) ──
    rep("""/* ── RESPONSIVE ── */
.reviews-grid { grid-template-columns: 1fr 1fr; }
  .guarantee-section { margin: 0 40px; }
}
.counters-grid { grid-template-columns: repeat(2, 1fr); }
  .reviews-grid { grid-template-columns: 1fr; }
  .guarantee-section { grid-template-columns: 1fr; margin: 0 20px; }
  .guarantee-block, .materials-block { padding: 40px 28px; }
  .materials-grid { grid-template-columns: 1fr 1fr; }
}
.guarantee-section { margin: 0; }
}
""", """/* ── RESPONSIVE (guarantee / reviews / counters blocks) ── */
@media (max-width: 1024px) {
  .reviews-grid { grid-template-columns: 1fr 1fr; }
  .guarantee-section { margin: 0 40px; }
}
@media (max-width: 768px) {
  .counters-grid { grid-template-columns: repeat(2, 1fr); }
  .reviews-grid { grid-template-columns: 1fr; }
  .guarantee-section { grid-template-columns: 1fr; margin: 0 20px; }
  .guarantee-block, .materials-block { padding: 40px 28px; }
  .materials-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 430px) {
  .guarantee-section { margin: 0; }
}
""")
    rep("/* ── RESPONSIVE ── */\n\n/* ── MARQUEE ── */", "/* ── MARQUEE ── */")

    # ── 6. Type scale: nothing a visitor has to read is below 10px ──
    in_rule('.nav-links a', 'font-size: 10px;', 'font-size: 11px;')
    in_rule('.nav-cta', 'font-size: 10px;', 'font-size: 11px;')
    in_rule('.hero-eyebrow', 'font-size: 9px;\n  letter-spacing: 0.5em;', 'font-size: 11px;\n  letter-spacing: 0.42em;')
    in_rule('.hero-sub', 'font-size: 12px;', 'font-size: 13px;')
    in_rule('.btn-primary', 'font-size: 10px;', 'font-size: 11px;')
    in_rule('.btn-outline', 'font-size: 10px;', 'font-size: 11px;')
    in_rule('.hero-scroll span', 'font-size: 7.5px;', 'font-size: 10px;')
    in_rule('.section-label', 'font-size: 8.5px;\n  letter-spacing: 0.5em;', 'font-size: 11px;\n  letter-spacing: 0.4em;')
    in_rule('.service-num', 'font-size: 9px;', 'font-size: 11px;')
    in_rule('.service-desc', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.about-stat-label', 'font-size: 8px;\n  letter-spacing: 0.35em;', 'font-size: 10px;\n  letter-spacing: 0.25em;\n  text-align: center;')
    in_rule('.about-text p', 'font-size: 12px;\n  line-height: 2.1;', 'font-size: 14px;\n  line-height: 1.95;')
    in_rule('.feature-row', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.pi-label-type', 'font-size: 8px;\n  letter-spacing: 0.35em;', 'font-size: 10px;\n  letter-spacing: 0.26em;')
    in_rule('.step-name', 'font-size: 12px;', 'font-size: 13px;')
    in_rule('.step-desc', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.contact-item-label', 'font-size: 8px;\n  letter-spacing: 0.4em;', 'font-size: 10px;\n  letter-spacing: 0.32em;')
    in_rule('.form-label', 'font-size: 8px;\n  letter-spacing: 0.35em;', 'font-size: 11px;\n  letter-spacing: 0.22em;')
    in_rule('.form-input, .form-textarea', 'font-size: 12px;', 'font-size: 14px;')
    in_rule('.form-input, .form-textarea', 'letter-spacing: 0.08em;', 'letter-spacing: 0.04em;')
    in_rule('.form-input::placeholder, .form-textarea::placeholder', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.form-submit', 'font-size: 10px;', 'font-size: 11px;')
    in_rule('.footer-copy', 'font-size: 9px;', 'font-size: 11px;')
    in_rule('.footer-links a', 'font-size: 9px;', 'font-size: 11px;')
    in_rule('.car-label', 'font-size: 11px;', 'font-size: 12px;')
    in_rule('.adm-tab', 'font-size: 8.5px;\n  letter-spacing: 0.3em;', 'font-size: 10px;\n  letter-spacing: 0.18em;')
    in_rule('.adm-section-title', 'font-size: 8px;', 'font-size: 10px;')
    in_rule('.adm-label', 'font-size: 9px;', 'font-size: 10px;')
    in_rule('.adm-input, .adm-textarea', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.adm-photo-slot span', 'font-size: 8px; letter-spacing: 0.2em;', 'font-size: 10px; letter-spacing: 0.1em;')
    in_rule('.adm-btn-sm', 'font-size: 8px;\n  letter-spacing: 0.25em;', 'font-size: 10px;\n  letter-spacing: 0.18em;')
    in_rule('.adm-btn', 'font-size: 9px;', 'font-size: 11px;')
    in_rule('.adm-toast', 'font-size: 9px;\n  letter-spacing: 0.25em;', 'font-size: 11px;\n  letter-spacing: 0.16em;\n  max-width: calc(100vw - 32px);')
    in_rule('.adm-toggle-label', 'font-size: 11px;', 'font-size: 12px;')
    in_rule('.lock-sub', 'font-size: 9px;', 'font-size: 10px;')
    in_rule('.lock-err', 'font-size: 10px;\n  color: #c86e6e;', 'font-size: 12px;\n  color: var(--danger);\n  text-align: center;')
    in_rule('.guarantee-item-desc', 'font-size: 10px;', 'font-size: 12px;')
    in_rule('.material-tag-desc', 'font-size: 9px;', 'font-size: 11px;')
    in_rule('.file-drop-text', 'font-size: 11px;', 'font-size: 13px;')
    in_rule('.file-drop-hint', 'font-size: 9px;', 'font-size: 10.5px;')
    in_rule('.file-item', 'font-size: 10px;', 'font-size: 12px;')
    in_rule('.send-method', 'font-size: 9px;\n  letter-spacing: 0.2em;', 'font-size: 10.5px;\n  letter-spacing: 0.14em;')
    in_rule('.form-success-sub', 'font-size: 10px;\n  letter-spacing: 0.2em;', 'font-size: 11px;\n  letter-spacing: 0.14em;\n  line-height: 1.9;')
    in_rule('.file-item-remove', 'cursor: pointer; padding: 2px 4px;', 'cursor: pointer; padding: 6px 10px; margin: -6px -8px -6px 4px;')
    in_rule('.file-item-remove', 'font-size: 14px;', 'font-size: 18px;')

    # ── 7. Layout values that used to live in inline style="" (and so ignored every media query) ──
    rep("/* ── CAROUSEL ── */\n#carousel::-webkit-scrollbar { display: none; }\n", """/* ── CAROUSEL ── */
#categories { padding: 100px 0; overflow: hidden; background: var(--bg); }
.cat-head { padding: 0 60px; }
.cat-head-row { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 12px 24px; margin-bottom: 52px; }
.cat-link {
  font-size: 11px; letter-spacing: 0.3em; text-transform: uppercase;
  color: var(--gold); text-decoration: none; white-space: nowrap;
  border-bottom: 1px solid var(--border); padding-bottom: 3px;
}
.cat-link:hover { border-bottom-color: var(--gold); }
.car-wrap { position: relative; }
#carousel {
  display: flex; gap: 28px; padding: 0 60px 24px;
  overflow-x: auto; scroll-behavior: smooth; overscroll-behavior-x: contain;
  scrollbar-width: none; -ms-overflow-style: none;
}
#carousel::-webkit-scrollbar { display: none; }
.car-arrow {
  position: absolute; top: 50%; transform: translateY(-60%); z-index: 10;
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  background: rgba(12,10,8,0.85); border: 1px solid var(--border); color: var(--gold);
  cursor: pointer; transition: background 0.3s; backdrop-filter: blur(8px);
}
#carPrev { left: 24px; }
#carNext { right: 24px; }
#carDots { display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 32px; padding: 0 60px; }
""")
    in_rule('.car-dot', 'width: 6px; height: 6px;', 'width: 6px; height: 6px;\n  padding: 0; border: 9px solid transparent; margin: -9px; box-sizing: content-box;\n  background-clip: padding-box;\n  cursor: pointer;')

    in_rule('.car-dot.active', 'border-radius: 3px;', 'border-radius: 12px;')
    # floating buttons, calculator shell
    rep("/* ── SEND METHOD ── */", """/* ── FLOATING BUTTONS ── */
.fab {
  position: fixed; right: 28px; z-index: 1000;
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg2); border: 1px solid var(--border); color: var(--gray2);
  cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.fab:hover { border-color: var(--gold); color: var(--gold); }
#admin-open-btn { bottom: 136px; display: none; }
body.admin-entry #admin-open-btn { display: flex; }
#calc-btn { bottom: 84px; }
#calc-btn.is-open { border-color: var(--gold); color: var(--gold); background: rgba(200,169,110,0.08); }
#theme-toggle-btn { bottom: 28px; box-shadow: 0 4px 24px rgba(200,169,110,0.2); }
body.menu-open .fab { display: none !important; }

/* ── CALCULATOR SHELL ── */
.calc-head {
  padding: 28px 40px 22px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  position: sticky; top: 0; background: var(--bg2); z-index: 10; backdrop-filter: blur(8px);
}
.calc-steps { background: var(--bg2); padding: 40px; }
.calc-result {
  background: var(--bg3); padding: 36px 28px;
  display: flex; flex-direction: column; gap: 16px;
  position: sticky; top: 90px; align-self: start;
}
#pc-size { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
#pc-material { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

/* ── ACCESSIBILITY HELPERS ── */
.visually-hidden {
  position: absolute !important; width: 1px; height: 1px; margin: -1px; padding: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; border: 0;
}
.skip-link {
  position: fixed; top: -80px; left: 16px; z-index: 3000;
  background: var(--gold); color: var(--bg); padding: 12px 18px;
  font-size: 12px; letter-spacing: 0.12em; text-decoration: none;
}
.skip-link:focus { top: 12px; }
a:focus-visible, button:focus-visible, [tabindex]:focus-visible,
input:focus-visible, textarea:focus-visible, .send-method:focus-within {
  outline: 2px solid var(--gold2); outline-offset: 3px;
}
.form-input:focus-visible, .form-textarea:focus-visible,
.adm-input:focus-visible, .adm-textarea:focus-visible { outline-offset: 0; }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .marquee-track, .scroll-line { animation: none; }
  .reveal { transition: none; }
  #carousel { scroll-behavior: auto; }
}

/* ── FORM STATES ── */
.form-error { font-size: 12px; letter-spacing: 0.02em; color: var(--danger); min-height: 0; }
.form-error:empty { display: none; }
.form-input[aria-invalid="true"], .form-textarea[aria-invalid="true"] { border-color: var(--danger); }
.form-req { color: var(--gold); }
.form-hp { position: absolute !important; width: 1px; height: 1px; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); }
.lead-status {
  font-size: 13px; line-height: 1.7; letter-spacing: 0.02em;
  padding: 14px 16px; border: 1px solid var(--border); color: var(--gray2);
}
.lead-status[hidden] { display: none; }
.lead-status.is-error { border-color: var(--danger); color: var(--white); background: rgba(224,138,138,0.07); }
.lead-status a { color: var(--gold); }
.form-submit[disabled] { opacity: 0.55; cursor: progress; }
.form-actions { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.calc-chip {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  border: 1px solid var(--border); background: rgba(200,169,110,0.05);
  padding: 12px 14px; font-size: 12px; line-height: 1.7; color: var(--gray2); white-space: pre-line;
}
.calc-chip[hidden] { display: none; }
.calc-chip button { background: none; border: 0; color: var(--gray2); font-size: 18px; line-height: 1; padding: 4px 8px; cursor: pointer; }
.calc-chip button:hover { color: var(--danger); }
.form-success-id { font-size: 13px; letter-spacing: 0.06em; color: var(--white); }
.form-success-links { font-size: 12px; line-height: 1.9; color: var(--gray2); }
.form-success-links a { color: var(--gold); }
.btn-link {
  background: none; border: 0; border-bottom: 1px solid var(--border); padding: 0 0 3px;
  font-family: 'Montserrat', sans-serif; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--gold); cursor: pointer;
}
.btn-link:hover { border-bottom-color: var(--gold); }

/* ── ADMIN: messages, leads ── */
.adm-msg { font-size: 12px; line-height: 1.7; color: var(--gray2); padding: 12px 14px; border: 1px solid var(--border); margin-bottom: 16px; }
.adm-msg.is-error { border-color: var(--danger); color: var(--white); }
.adm-msg[hidden] { display: none; }
.adm-toast.is-error { background: var(--danger); color: #1a0d0d; }
.adm-field-err { font-size: 11px; color: var(--danger); margin-top: 4px; }
.adm-input[aria-invalid="true"] { border-color: var(--danger); }
.adm-head-actions { display: flex; align-items: center; gap: 8px; }
.adm-logout {
  background: none; border: 1px solid var(--border); color: var(--gray2); height: 36px; padding: 0 12px;
  font-family: 'Montserrat', sans-serif; font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; cursor: pointer;
}
.adm-logout:hover { border-color: var(--gold); color: var(--gold); }
.adm-logout[hidden] { display: none; }
.lead-card { border: 1px solid var(--border); padding: 14px 16px; margin-bottom: 12px; font-size: 12px; line-height: 1.75; color: var(--gray2); }
.lead-card-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 6px; }
.lead-card-name { font-size: 14px; color: var(--white); overflow-wrap: anywhere; }
.lead-card-date { font-size: 11px; color: var(--gray); white-space: nowrap; }
.lead-card dl { display: grid; grid-template-columns: auto 1fr; gap: 2px 12px; }
.lead-card dt { color: var(--gray); }
.lead-card dd { color: var(--white); overflow-wrap: anywhere; white-space: pre-line; }
.lead-card a { color: var(--gold); }
.lead-card-foot { display: flex; justify-content: flex-end; margin-top: 8px; }
.lead-card-del { background: none; border: 0; color: var(--danger); font-size: 11px; letter-spacing: 0.1em; cursor: pointer; padding: 6px 0; }

/* ── SEND METHOD ── */""")

    # radios must stay focusable for keyboard users
    rep(".send-method input[type=radio] { display: none; }", ".send-method input[type=radio] { position: absolute; opacity: 0; width: 1px; height: 1px; pointer-events: none; }")

    # nav above the mobile menu so the hamburger can close it; dynamic viewport units for iOS toolbars
    in_rule('nav', 'z-index: 100;', 'z-index: 999;')
    in_rule('#admin-panel', 'width: 480px; height: 100vh;', 'width: 480px; height: 100vh; height: 100dvh;\n  max-width: 100vw;\n  visibility: hidden;')
    in_rule('#admin-panel', 'transition: right 0.4s cubic-bezier(0.16,1,0.3,1);', 'transition: right 0.4s cubic-bezier(0.16,1,0.3,1), visibility 0s linear 0.4s;')
    rep("#admin-panel.open { right: 0; }", "#admin-panel.open { right: 0; visibility: visible; transition: right 0.4s cubic-bezier(0.16,1,0.3,1), visibility 0s; }")
    in_rule('.hero', 'min-height: 100vh;', 'min-height: 100vh;\n  min-height: 100svh;')

    # content hidden until scripted reveal: only when JS is actually running
    rep(".reveal {\n  opacity: 0;", ".js .reveal {\n  opacity: 0;")
    rep(".reveal.visible {", ".js .reveal.visible {")

    # hamburger → cross
    rep("/* ── HERO ── */", """/* ── MOBILE MENU ── */
#hamburger { width: 44px; height: 44px; margin-right: -8px; }
body.menu-open .ham-line:nth-child(1) { transform: translateY(6px) rotate(45deg); }
body.menu-open .ham-line:nth-child(2) { opacity: 0; }
body.menu-open .ham-line:nth-child(3) { width: 22px !important; align-self: center !important; transform: translateY(-6px) rotate(-45deg); }
#mobile-menu { overflow-y: auto; padding: 88px 20px 40px; }
.ig-icon-btn { min-width: 44px; min-height: 44px; justify-content: center; }

/* ── HERO ── */""")

    # ── 8. Media queries ──
    # 768
    rep("  #about, #process { padding: 64px 20px; }\n  .contact-section { padding: 64px 20px; gap: 44px; grid-template-columns: 1fr; }",
        "  .contact-section { padding: 64px 20px; gap: 44px; grid-template-columns: 1fr; }")
    rep("  .hero-sub { font-size: 11px; letter-spacing: 0.1em; max-width: 100%; }\n  .hero-eyebrow { font-size: 8px; letter-spacing: 0.28em; margin-bottom: 22px; }",
        "  .hero-sub { font-size: 13px; letter-spacing: 0.08em; max-width: 100%; }\n  .hero-eyebrow { font-size: 10px; letter-spacing: 0.26em; margin-bottom: 22px; }")
    rep("  #categories > div:first-child { padding: 0 20px; }\n  #carousel { padding: 0 16px 16px; gap: 12px; }",
        "  .cat-head { padding: 0 20px; }\n  .cat-head-row { margin-bottom: 32px; }\n  #carousel { padding: 0 16px 16px; gap: 12px; }\n  #carDots { padding: 0 20px; }\n  .cat-link { padding: 12px 0 8px; }\n  .car-arrow { width: 44px; height: 44px; }")
    rep("  .car-label { font-size: 9px; letter-spacing: 0.13em; }", "  .car-label { font-size: 11px; letter-spacing: 0.1em; }")
    rep("  .service-name { font-size: 18px; }\n  .service-desc { font-size: 10px; }", "  .service-name { font-size: 18px; }\n  .service-desc { font-size: 13px; line-height: 1.75; }")
    rep("""  .about-visual { display: none; }
  .about-text p { font-size: 11px; }
  .about-features { gap: 10px; }
  .feature-row { font-size: 10px; }""", """  /* decorative frame goes, the "5+ years" figure stays */
  .about-visual { height: auto; margin-bottom: 28px; }
  .about-box-1 { display: none; }
  .about-box-2 { position: static; width: auto; height: auto; flex-direction: row; justify-content: flex-start; align-items: baseline; gap: 14px; padding: 16px 20px; }
  .about-stat-num { font-size: 40px; }
  .about-stat-label { text-align: left; }
  .about-text p { font-size: 14px; line-height: 1.85; }
  .about-features { gap: 10px; }
  .feature-row { font-size: 13px; }""")
    rep("  .step-name { font-size: 11px; }\n  .step-desc { font-size: 10px; }", "  .step-name { font-size: 12px; }\n  .step-desc { font-size: 13px; line-height: 1.75; }")
    rep("  .send-method { padding: 12px 8px; font-size: 8.5px; }\n  .file-drop-inner { padding: 20px 16px; }\n  .file-drop-text { font-size: 10px; }",
        "  .send-method { padding: 14px 8px; font-size: 10.5px; }\n  .file-drop-inner { padding: 20px 16px; }\n  .file-drop-text { font-size: 13px; }\n  /* 16px stops iOS Safari from zooming the page when a field gets focus */\n  .form-input, .form-textarea, .adm-input, .adm-textarea { font-size: 16px; letter-spacing: 0.02em; }\n  .form-submit { align-self: stretch; text-align: center; padding: 18px 24px; }\n  .form-actions { flex-direction: column; align-items: stretch; }")
    rep("  .adm-tab { padding: 12px 6px; font-size: 8px; white-space: nowrap; }", "  .adm-tab { padding: 14px 12px; font-size: 10px; letter-spacing: 0.12em; white-space: nowrap; flex: 0 0 auto; }")
    rep("""  #calc-inner-grid { grid-template-columns: 1fr !important; }
  #calc-popup [style*="position:sticky"] { position: static !important; }
  #calc-popup > div:first-child { padding: 18px 20px 14px; }

  /* Fixed buttons */
  #calc-btn { bottom: 80px; right: 16px; width: 44px; height: 44px; }
  #theme-toggle-btn { bottom: 24px; right: 16px; width: 44px; height: 44px; }

  /* Cursor off on touch */
  .cursor, .cursor-ring { display: none !important; }
  body { cursor: auto !important; }
}""", """  #calc-inner-grid { grid-template-columns: 1fr !important; }
  .calc-result { position: static; }
  .calc-head { padding: 18px 20px 14px; }
  .calc-steps { padding: 28px 20px; }
  .calc-result { padding: 28px 20px; }

  /* Fixed buttons */
  .fab { right: 16px; width: 44px; height: 44px; }
  #admin-open-btn { bottom: 128px; }
  #calc-btn { bottom: 76px; }
  #theme-toggle-btn { bottom: 24px; }
  footer { padding-bottom: 84px; }
}""")
    rep("  footer { flex-direction: column; gap: 14px; text-align: center; padding: 28px 20px; }", "  footer { flex-direction: column; gap: 14px; text-align: center; padding: 28px 20px 84px; }")
    rep("  footer { padding-bottom: 84px; }\n}", "}")
    rep("  .footer-links { flex-wrap: wrap; justify-content: center; gap: 14px; }", "  .footer-links { flex-wrap: wrap; justify-content: center; gap: 6px 18px; }\n  .footer-links a { display: inline-block; padding: 12px 4px; }")

    rep("""  #carPrev { left: 4px; width: 36px; height: 36px; }
  #carNext { right: 4px; width: 36px; height: 36px; }""", "  #carPrev { left: 4px; }\n  #carNext { right: 4px; }")
    # 430
    rep("  section { padding: 56px 16px; }\n  #about, #process { padding: 56px 16px; }\n  .contact-section { padding: 56px 16px; }\n  .section-label { font-size: 8px; letter-spacing: 0.35em; }",
        "  section { padding: 56px 16px; }\n  .contact-section { padding: 56px 16px; }\n  .section-label { font-size: 10px; letter-spacing: 0.3em; }")
    rep("  .hero-eyebrow { font-size: 7.5px; letter-spacing: 0.22em; margin-bottom: 18px; }\n  .hero-sub { font-size: 10px; line-height: 1.85; }",
        "  .hero-eyebrow { font-size: 10px; letter-spacing: 0.18em; margin-bottom: 18px; }\n  .hero-sub { font-size: 13px; line-height: 1.8; letter-spacing: 0.04em; }\n  .hero-sub br { display: none; }")
    rep("  .btn-primary, .btn-outline { font-size: 9px; letter-spacing: 0.2em; padding: 13px 20px; }", "  .btn-primary, .btn-outline { font-size: 11px; letter-spacing: 0.2em; padding: 16px 20px; }")
    rep("""  #categories > div:first-child { padding: 0 16px; margin-bottom: 0; }
  #categories > div:first-child > div:last-child { display: none; }
  #carousel { padding: 0 12px 14px; gap: 10px; }""", """  .cat-head { padding: 0 16px; }
  .cat-head-row { margin-bottom: 26px; }
  #carousel { padding: 0 12px 14px; gap: 10px; }""")
    rep("  .car-label { font-size: 8.5px; letter-spacing: 0.1em; }", "  .car-label { font-size: 11px; letter-spacing: 0.06em; }")
    rep("  #carDots { margin-top: 14px; gap: 6px; }", "  #carDots { margin-top: 14px; gap: 6px; padding: 0 16px; }")
    rep("  .service-num { font-size: 8px; margin-bottom: 10px; }\n  .service-desc { font-size: 10px; line-height: 1.8; }", "  .service-num { font-size: 10px; margin-bottom: 10px; }")
    rep("  .feature-row { font-size: 10px; gap: 12px; }", "  .feature-row { gap: 12px; }")
    rep("  .contact-item-value { font-size: 16px; }", "  .contact-item-value { font-size: 18px; }")
    rep("""  .send-method { padding: 11px 6px; font-size: 8px; gap: 5px; }
  .form-input, .form-textarea { font-size: 11px; padding: 12px 14px; }
  .form-textarea { height: 100px; }
  .form-submit { font-size: 9px; padding: 14px 28px; }
  .file-drop-zone { min-height: 80px; }
  .file-drop-inner { padding: 16px 12px; gap: 6px; }
  .file-drop-text { font-size: 9.5px; }
  .file-drop-hint { font-size: 7.5px; }""", """  .send-method { padding: 14px 6px; gap: 6px; }
  .form-input, .form-textarea { padding: 13px 14px; }
  .form-textarea { height: 110px; }
  .file-drop-zone { min-height: 80px; }
  .file-drop-inner { padding: 18px 12px; gap: 6px; }
  .file-drop-hint { font-size: 10px; letter-spacing: 0.08em; text-align: center; }""")
    rep("  footer { padding: 22px 16px; gap: 12px; }", "  footer { padding: 22px 16px 80px; gap: 12px; }")
    rep("  .footer-copy { font-size: 8px; }\n  .footer-links { gap: 12px; }\n  .footer-links a { font-size: 8px; }", "  .footer-copy { font-size: 10px; }")
    rep("""  #calc-popup { width: 100vw; }
  #calc-popup > div:first-child { padding: 16px; }

  /* Fixed buttons */
  #calc-btn { bottom: 70px; right: 14px; width: 42px; height: 42px; }
  #theme-toggle-btn { bottom: 18px; right: 14px; width: 42px; height: 42px; }
  button[title="Адмін панель"] { bottom: 122px; right: 14px; width: 42px; height: 42px; }
}""", """  #calc-popup { width: 100vw; }
  .calc-head { padding: 16px; }
  .calc-steps, .calc-result { padding: 24px 16px; }
  #pc-size { grid-template-columns: repeat(2, 1fr); }
  #pc-material { grid-template-columns: 1fr; }

  /* Fixed buttons */
  .fab { right: 14px; }
  #admin-open-btn { bottom: 122px; }
  #calc-btn { bottom: 70px; }
  #theme-toggle-btn { bottom: 18px; }
}""")
    # 375
    rep("  section { padding: 48px 14px; }\n  #about, #process, .contact-section { padding: 48px 14px; }", "  section { padding: 48px 14px; }\n  .contact-section { padding: 48px 14px; }\n  .cat-head { padding: 0 14px; }")
    # 1440
    rep("  section { padding: 140px 80px; }\n  #about, #process { padding: 140px 80px; }\n  .contact-section { padding: 140px 80px; }\n  footer { padding: 48px 80px; }\n  #categories > div:first-child { padding: 0 80px; }\n  #carousel { padding: 0 80px 24px; }",
        "  section { padding: 140px 80px; }\n  .contact-section { padding: 140px 80px; }\n  footer { padding: 48px 80px; }\n  #categories { padding: 120px 0; }\n  .cat-head { padding: 0 80px; }\n  #carousel { padding: 0 80px 24px; }")
    return s

EXTRA_CSS = """
/* ── Additions that accompany the reworked form / admin markup ── */
.contact-form-body { display: flex; flex-direction: column; gap: 20px; }
.contact-form-body[hidden] { display: none; }
.file-list { padding: 0; margin-top: 8px; }
.file-list:empty { display: none; }
#lead-handle-group[hidden] { display: none; }
.lock-close { position: absolute; top: 18px; right: 18px; }
/* nothing behind the login screen is reachable by Tab or screen readers */
#admin-panel.locked .adm-header, #admin-panel.locked .adm-tabs, #admin-panel.locked .adm-content { visibility: hidden; }
/* the enlarged (transparent) hit area of a dot must not be painted */
.car-dot, .car-dot.active { background-clip: padding-box; }
"""
