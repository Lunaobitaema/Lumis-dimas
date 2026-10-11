document.addEventListener('DOMContentLoaded', function() {
'use strict';

// ══════════════════════════════
//  HELPERS
// ══════════════════════════════
const API = 'api/';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  del(k) { try { localStorage.removeItem(k); } catch (e) {} }
};

// One place for every server call. Rejects with {network:true} when the server
// cannot be reached, or {status, code, message, fields} when it answered with an error.
async function apiCall(path, opts) {
  opts = opts || {};
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeout || 20000);
  const init = { method: opts.method || 'GET', credentials: 'same-origin', headers: { 'Accept': 'application/json' }, signal: ctrl.signal, cache: 'no-store' };
  if (opts.csrf) init.headers['X-CSRF-Token'] = opts.csrf;
  if (opts.json !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(opts.json); }
  if (opts.form) init.body = opts.form;
  let res;
  try {
    res = await fetch(API + path, init);
  } catch (e) {
    throw { network: true, timeout: e && e.name === 'AbortError' };
  } finally {
    clearTimeout(timer);
  }
  let data = null;
  try { data = await res.json(); } catch (e) { /* not JSON: static hosting, proxy error page… */ }
  if (!res.ok || !data || data.ok !== true) {
    throw { status: res.status, code: data && data.code, message: data && data.message, fields: (data && data.fields) || null, noBackend: !data };
  }
  return data;
}

// ══════════════════════════════
//  CAROUSEL
// ══════════════════════════════
const car = $('carousel');
const dotsEl = $('carDots');
const realCards = () => Array.from(car.querySelectorAll('.car-card:not(.car-clone)'));
const carGap = () => parseFloat(getComputedStyle(car).columnGap) || 0;
function getCardW() {
  const first = car.querySelector('.car-card:not(.car-clone)');
  return first ? first.offsetWidth + carGap() : 248;
}
let cardW = 248;
let carTeleporting = false;

function carIndex() {
  const n = realCards().length;
  if (!n || !cardW) return 0;
  return ((Math.round((car.scrollLeft - n * cardW) / cardW) % n) + n) % n;
}
function carJump(left) {
  car.style.scrollBehavior = 'auto';
  car.scrollLeft = left;
  requestAnimationFrame(() => { car.style.scrollBehavior = ''; });
}
function buildDots() {
  const n = realCards().length;
  dotsEl.textContent = '';
  for (let i = 0; i < n; i++) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'car-dot';
    b.setAttribute('aria-label', 'Слайд ' + (i + 1) + ' з ' + n);
    b.addEventListener('click', () => car.scrollTo({ left: (n + i) * cardW, behavior: 'smooth' }));
    dotsEl.appendChild(b);
  }
  updateDots();
}
function updateDots() {
  const idx = carIndex();
  dotsEl.querySelectorAll('.car-dot').forEach((d, i) => {
    d.classList.toggle('active', i === idx);
    if (i === idx) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current');
  });
}

// Layout: [one cloned set] [real cards] [as many cloned sets as it takes to fill the viewport].
function rebuildInfiniteClones(keepIndex) {
  const idx = keepIndex ? carIndex() : 0;
  car.querySelectorAll('.car-clone').forEach(el => el.remove());
  const cards = realCards();
  cardW = getCardW();
  if (!cards.length) { buildDots(); return; }
  const clone = orig => {
    const cl = orig.cloneNode(true);
    cl.classList.add('car-clone');
    cl.setAttribute('aria-hidden', 'true');
    cl.setAttribute('tabindex', '-1');
    return cl;
  };
  const setW = cards.length * cardW;
  const sets = Math.max(1, Math.ceil(car.clientWidth / setW) + 1);
  const firstReal = cards[0];
  cards.forEach(orig => car.insertBefore(clone(orig), firstReal));
  for (let k = 0; k < sets; k++) cards.forEach(orig => car.appendChild(clone(orig)));
  carJump(setW + idx * cardW);
  buildDots();
}

function carScroll(dir) {
  car.scrollBy({ left: dir * cardW * 2, behavior: 'smooth' });
}

car.addEventListener('scroll', () => {
  const n = realCards().length;
  if (!n || carTeleporting) return;
  const setW = n * cardW;
  if (car.scrollLeft >= setW * 2) {
    carTeleporting = true; carJump(car.scrollLeft - setW);
    requestAnimationFrame(() => { carTeleporting = false; });
  } else if (car.scrollLeft <= cardW * 0.5) {
    carTeleporting = true; carJump(car.scrollLeft + setW);
    requestAnimationFrame(() => { carTeleporting = false; });
  }
  updateDots();
}, { passive: true });

rebuildInfiniteClones(false);
// Card width depends on web fonts and images being laid out.
window.addEventListener('load', () => rebuildInfiniteClones(true));

// Rebuild only when the width really changes. Mobile browsers fire "resize" on every
// address-bar show/hide while scrolling, which used to throw the carousel back to the start.
let lastW = window.innerWidth, resizeTimer;
window.addEventListener('resize', () => {
  if (window.innerWidth === lastW) return;
  lastW = window.innerWidth;
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => rebuildInfiniteClones(true), 150);
});

// Drag to scroll (mouse). A drag must not count as a click on the card.
let isDown = false, dragged = false, startX = 0, startLeft = 0;
car.addEventListener('mousedown', e => { isDown = true; dragged = false; startX = e.pageX; startLeft = car.scrollLeft; });
window.addEventListener('mouseup', () => { if (isDown) { isDown = false; car.style.scrollBehavior = ''; } });
car.addEventListener('mousemove', e => {
  if (!isDown) return;
  const dx = e.pageX - startX;
  if (!dragged && Math.abs(dx) < 6) return;
  dragged = true;
  e.preventDefault();
  car.style.scrollBehavior = 'auto';
  car.scrollLeft = startLeft - dx;
});
car.addEventListener('click', e => { if (dragged) { e.preventDefault(); e.stopPropagation(); dragged = false; } }, true);
// Touch: native horizontal scrolling does the job; no extra handler.

function goToContact() {
  $('contact').scrollIntoView({ behavior: 'smooth' });
}

// ══════════════════════════════
//  CUSTOM CURSOR (mouse devices only)
// ══════════════════════════════
const cursor = $('cursor');
const ring = $('cursorRing');
const finePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
let cursorWanted = true;
function applyCursorMode() {
  document.body.classList.toggle('use-custom-cursor', finePointer && cursorWanted);
}
applyCursorMode();

if (finePointer) {
  let mx = -100, my = -100, rx = -100, ry = -100;
  cursor.style.left = ring.style.left = '-100px';
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cursor.style.left = mx + 'px';
    cursor.style.top  = my + 'px';
  });
  (function animRing() {
    rx += (mx - rx) * 0.12;
    ry += (my - ry) * 0.12;
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    requestAnimationFrame(animRing);
  })();
  // Delegated, so elements created later (file list, admin fields) react too.
  const HOT = 'a, button, label.send-method, [role="button"], [role="link"], [role="switch"], .pc-opt, .pc-opt-sz, .pc-opt-mat, .pc-ext';
  document.addEventListener('mouseover', e => {
    const hot = e.target.closest && e.target.closest(HOT);
    ring.style.width  = hot ? '50px' : '32px';
    ring.style.height = hot ? '50px' : '32px';
    ring.style.borderColor = hot ? 'rgba(200,169,110,0.7)' : 'rgba(200,169,110,0.4)';
  });
}

// Sticky nav
const nav = $('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 60);
}, { passive: true });

// Scroll reveal (content stays visible if the observer is unavailable)
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  reveals.forEach(r => obs.observe(r));
} else {
  reveals.forEach(r => r.classList.add('visible'));
}

// Keyboard: Enter/Space activates custom controls; Escape closes whatever is open.
function makeButtons(root) {
  (root || document).querySelectorAll('.pc-opt, .pc-opt-sz, .pc-opt-mat, .pc-ext').forEach(el => {
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-pressed', el.classList.contains('selected') ? 'true' : 'false');
  });
}
makeButtons();
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if ($('admin-panel').classList.contains('open')) closeAdmin();
    else if ($('calc-popup').style.display === 'block') toggleCalc();
    else if (document.body.classList.contains('menu-open')) closeMenu();
    return;
  }
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('[role="button"][tabindex], [role="link"][tabindex], [role="switch"][tabindex]')) {
    e.preventDefault();
    e.target.click();
  }
  if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) { e.preventDefault(); openAdmin(); }
});

// ══════════════════════════════
//  FILE UPLOAD
// ══════════════════════════════
const MAX_FILE = 10 * 1024 * 1024;
const MAX_FILES = 5;
const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'pdf', 'ai', 'eps', 'svg', 'zip'];
let uploadedFiles = [];

function fmtSize(bytes) {
  return bytes >= 1048576 ? (bytes / 1048576).toFixed(1).replace('.', ',') + ' МБ' : Math.max(1, Math.round(bytes / 1024)) + ' КБ';
}

function handleFiles(files) {
  const problems = [];
  Array.from(files || []).forEach(file => {
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (file.name.indexOf('.') < 0 || ALLOWED_EXT.indexOf(ext) < 0) { problems.push('«' + file.name + '» — тип файлу не підтримується'); return; }
    if (file.size === 0) { problems.push('«' + file.name + '» — файл порожній'); return; }
    if (file.size > MAX_FILE) { problems.push('«' + file.name + '» перевищує 10MB'); return; }
    if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) { problems.push('«' + file.name + '» вже додано'); return; }
    if (uploadedFiles.length >= MAX_FILES) { problems.push('«' + file.name + '» — можна додати не більше ' + MAX_FILES + ' файлів'); return; }
    uploadedFiles.push(file);
  });
  $('err-files').textContent = problems.join('. ');
  renderFileList();
}

function renderFileList() {
  const list = $('fileList');
  if (!list) return;
  list.innerHTML = uploadedFiles.map((f, i) => `
    <div class="file-item">
      <div class="file-item-name">
        <svg aria-hidden="true" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
          <polyline points="13 2 13 9 20 9"/>
        </svg>
        <span>${esc(f.name)}</span>
      </div>
      <span class="file-item-size">${fmtSize(f.size)}</span>
      <button type="button" class="file-item-remove" onclick="removeFile(${i})" aria-label="Прибрати файл ${esc(f.name)}">×</button>
    </div>
  `).join('');
}

function removeFile(idx) {
  uploadedFiles.splice(idx, 1);
  $('err-files').textContent = '';
  renderFileList();
}

const dropZone = $('fileDropZone');
if (dropZone) {
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
  });
}

// ══════════════════════════════
//  LEAD FORM
// ══════════════════════════════
const leadForm = $('lead-form');
const METHODS = {
  email:     { label: 'Ваш email',                 type: 'email', ph: 'name@example.com', ac: 'email', handle: 'required', phone: false },
  telegram:  { label: 'Ваш Telegram (нік)',        type: 'text',  ph: '@username',        ac: 'off',   handle: 'optional', phone: 'or-handle' },
  viber:     { label: '',                          type: 'text',  ph: '',                 ac: 'off',   handle: 'none',     phone: true },
  instagram: { label: 'Ваш Instagram (нік)',       type: 'text',  ph: '@username',        ac: 'off',   handle: 'required', phone: false }
};
let leadSending = false;
let leadCalc = '';

function currentMethod() {
  const r = document.querySelector('input[name="send_method"]:checked');
  return r && METHODS[r.value] ? r.value : 'email';
}

function selectMethod(method) {
  if (!METHODS[method]) method = 'email';
  document.querySelectorAll('.send-method').forEach(el => el.classList.remove('active'));
  const target = $('method-' + method);
  if (target) target.classList.add('active');
  const m = METHODS[method];
  const group = $('lead-handle-group'), input = $('lead-handle');
  group.hidden = m.handle === 'none';
  $('lead-handle-label').textContent = m.label;
  $('lead-handle-req').hidden = m.handle !== 'required';
  if (input.type !== m.type) input.value = '';
  input.type = m.type;
  input.placeholder = m.ph;
  input.autocomplete = m.ac;
  input.required = m.handle === 'required';
  $('lead-phone-req').hidden = m.phone !== true;
  $('lead-phone').required = m.phone === true;
  setFieldError('handle', '');
  setFieldError('phone', '');
}

document.querySelectorAll('.send-method').forEach(label => {
  label.addEventListener('mouseenter', () => label.classList.add('hovered'));
  label.addEventListener('mouseleave', () => label.classList.remove('hovered'));
});

const FIELD_INPUT = { name: 'lead-name', phone: 'lead-phone', handle: 'lead-handle' };
function setFieldError(field, msg) {
  const err = $('err-' + field);
  if (err) err.textContent = msg || '';
  const input = $(FIELD_INPUT[field]);
  if (input) { if (msg) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid'); }
}
Object.keys(FIELD_INPUT).forEach(f => $(FIELD_INPUT[f]).addEventListener('input', () => setFieldError(f, '')));
selectMethod(currentMethod());

function validateLead() {
  const method = currentMethod(), m = METHODS[method];
  const name = $('lead-name').value.trim();
  const phone = $('lead-phone').value.trim();
  const handle = $('lead-handle').value.trim();
  const errors = {};
  if (name.length < 2) errors.name = "Вкажіть ім'я";
  const digits = phone.replace(/\D/g, '');
  if (phone && (!/^[\d\s()+\-]+$/.test(phone) || digits.length < 10 || digits.length > 15)) errors.phone = 'Перевірте номер: потрібно 10–15 цифр';
  if (method === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(handle)) errors.handle = 'Вкажіть коректний email';
  if (method === 'instagram' && !/^@?[A-Za-z0-9._]{1,30}$/.test(handle)) errors.handle = 'Вкажіть нік в Instagram';
  if (method === 'telegram') {
    if (handle && !/^@?[A-Za-z0-9_]{4,32}$/.test(handle)) errors.handle = 'Перевірте нік у Telegram';
    if (!handle && !phone) errors.phone = 'Вкажіть телефон або нік у Telegram';
  }
  if (method === 'viber' && !phone) errors.phone = 'Для Viber потрібен номер телефону';
  return errors;
}

function showFieldErrors(errors) {
  ['name', 'phone', 'handle'].forEach(f => setFieldError(f, errors[f] || ''));
  if (errors.files) $('err-files').textContent = errors.files;
  const first = ['name', 'phone', 'handle'].find(f => errors[f]);
  if (first) $(FIELD_INPUT[first]).focus();
}

// Contacts as they currently stand on the page (the admin may have changed them).
function directContacts() {
  const tel = $('contact-phone-link'), mail = $('contact-email-link');
  const emailAddr = mail && mail.getAttribute('href').indexOf('mailto:') === 0 ? mail.getAttribute('href').slice(7) : '';
  return {
    telHref: tel ? tel.getAttribute('href') : '', telText: tel ? tel.textContent.trim() : '',
    email: emailAddr,
    instagram: $('ig-nav-link') ? $('ig-nav-link').href : ''
  };
}
function directLinksHtml(method) {
  const c = directContacts();
  const links = [];
  if (c.telHref) links.push(`<a href="${esc(c.telHref)}">${esc(c.telText)}</a>`);
  if (c.email) links.push(`<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`);
  if (method === 'telegram') links.push('<a href="https://t.me/lumisua" target="_blank" rel="noopener noreferrer">Telegram</a>');
  if (method === 'viber' && c.telHref) links.push(`<a href="viber://chat?number=${encodeURIComponent(c.telHref.replace('tel:', ''))}">Viber</a>`);
  if (method === 'instagram' && /^https:\/\//.test(c.instagram)) links.push(`<a href="${esc(c.instagram)}" target="_blank" rel="noopener noreferrer">Instagram</a>`);
  return links.join(' · ');
}

function setLeadStatus(html, isError) {
  const box = $('lead-status');
  box.hidden = !html;
  box.classList.toggle('is-error', !!isError);
  box.innerHTML = html || '';
}

function setSending(on) {
  leadSending = on;
  const btn = $('lead-submit');
  btn.disabled = on;
  btn.textContent = on ? 'Надсилаємо…' : 'Надіслати запит';
  leadForm.setAttribute('aria-busy', on ? 'true' : 'false');
}

async function submitForm(e) {
  if (e) e.preventDefault();
  if (leadSending) return;               // second click while the first request is still in flight

  $('err-files').textContent = '';
  const errors = validateLead();
  showFieldErrors(errors);
  if (Object.keys(errors).length) {
    setLeadStatus('Перевірте виділені поля — заявку ще не надіслано.', true);
    return;
  }

  const method = currentMethod();
  const fd = new FormData();
  fd.append('name', $('lead-name').value.trim());
  fd.append('phone', $('lead-phone').value.trim());
  fd.append('handle', METHODS[method].handle === 'none' ? '' : $('lead-handle').value.trim());
  fd.append('order', $('lead-order').value.trim());
  fd.append('message', $('lead-message').value.trim());
  fd.append('method', method);
  fd.append('calc', leadCalc);
  fd.append('website', leadForm.elements.website.value);
  uploadedFiles.forEach(f => fd.append('files[]', f, f.name));

  setSending(true);
  setLeadStatus(uploadedFiles.length ? 'Надсилаємо заявку та файли. Не закривайте сторінку…' : 'Надсилаємо заявку…', false);

  try {
    const res = await apiCall('lead.php', { method: 'POST', form: fd, timeout: 180000 });
    // Success is shown only after the server confirmed that the request is stored.
    showLeadSuccess(res, method);
  } catch (err) {
    const direct = directLinksHtml(method);
    const fallback = direct ? ' Або зв\'яжіться з нами напряму: ' + direct + '.' : '';
    if (err.network) {
      setLeadStatus('<strong>Заявку не надіслано.</strong> ' + (err.timeout ? 'Сервер не відповів вчасно.' : 'Немає зв\'язку із сервером.') + ' Перевірте інтернет і натисніть «Надіслати запит» ще раз — введені дані збережено.' + fallback, true);
    } else if (err.status === 422 && err.fields) {
      showFieldErrors(err.fields);
      setLeadStatus('<strong>Заявку не надіслано.</strong> ' + esc(err.fields.files || err.fields.method || 'Перевірте виділені поля.'), true);
    } else if (err.status === 413) {
      setLeadStatus('<strong>Заявку не надіслано.</strong> Файли завеликі для сервера. Зменште їх розмір або кількість і спробуйте ще раз.', true);
    } else if (err.status === 429) {
      setLeadStatus('<strong>Заявку не надіслано.</strong> ' + esc(err.message || 'Забагато спроб. Спробуйте за кілька хвилин.') + fallback, true);
    } else {
      setLeadStatus('<strong>Заявку не надіслано.</strong> Сталася помилка на сервері. Спробуйте ще раз трохи пізніше.' + fallback, true);
    }
  } finally {
    setSending(false);
  }
}
leadForm.addEventListener('submit', submitForm);

function showLeadSuccess(res, method) {
  setLeadStatus('', false);
  $('lead-form-body').hidden = true;
  $('lead-success-id').textContent = 'Номер заявки: ' + res.id + (res.files ? ' · файлів отримано: ' + res.files : '');
  const direct = directLinksHtml(method);
  $('lead-success-links').innerHTML = direct ? 'Потрібно швидше? ' + direct : '';
  const ok = $('lead-success');
  ok.classList.add('show');
  ok.focus({ preventScroll: true });
  ok.scrollIntoView({ block: 'nearest' });
}

function resetLeadForm() {
  leadForm.reset();
  uploadedFiles = [];
  renderFileList();
  clearCalcFromForm();
  ['name', 'phone', 'handle'].forEach(f => setFieldError(f, ''));
  $('err-files').textContent = '';
  setLeadStatus('', false);
  selectMethod(currentMethod());
  $('lead-success').classList.remove('show');
  $('lead-form-body').hidden = false;
  $('lead-name').focus();
}

function clearCalcFromForm() {
  leadCalc = '';
  $('lead-calc').hidden = true;
  $('lead-calc-text').textContent = '';
}

// ══════════════════════════════
//  CALCULATOR PANEL
// ══════════════════════════════
const pcPrices = {
  type: {
    neon:     { base:2800, label:'Неонова вивіска' },
    lightbox: { base:3500, label:'Лайтбокс' },
    letters:  { base:4200, label:"Об'ємні літери" },
    photo:    { base:5500, label:'Фотозона' },
    sticker:  { base:800,  label:'Наліпки / вініл' },
    custom:   { base:6000, label:'Індивідуальне' },
  },
  size: {
    xs: { mult:0.6,  label:'XS · до 50 см' },
    s:  { mult:1.0,  label:'S · 50–100 см' },
    m:  { mult:1.55, label:'M · 100–150 см' },
    l:  { mult:2.3,  label:'L · 150+ см' },
  }
};
const PC_DISCOUNT_FROM = 3;      // extras selected
const PC_DISCOUNT_RATE = 0.05;
let pcState = { type:'neon', size:'s', material:'silicone', matMult:1.0, extras:0 };
let pcAnimFrame, pcShown = null;
let calcReturnFocus = null;
const money = n => n.toLocaleString('uk');

// The single source of truth for the price: the panel and the request both use it.
function pcCompute() {
  const t = pcPrices.type[pcState.type] || pcPrices.type.neon;
  const s = pcPrices.size[pcState.size] || pcPrices.size.s;
  const mult = isFinite(pcState.matMult) && pcState.matMult > 0 ? pcState.matMult : 1;
  const selected = Array.from(document.querySelectorAll('.pc-ext.selected'));
  const extras = selected.reduce((sum, el) => sum + (parseInt(el.dataset.price, 10) || 0), 0);
  const subtotal = Math.round(t.base * s.mult * mult) + extras;
  const discount = selected.length >= PC_DISCOUNT_FROM ? Math.round(subtotal * PC_DISCOUNT_RATE) : 0;
  return { extras, extraCount: selected.length, subtotal, discount, total: subtotal - discount };
}

function toggleCalc() {
  const popup   = $('calc-popup');
  const overlay = $('calc-overlay');
  const btn     = $('calc-btn');
  const open    = popup.style.display === 'none' || popup.style.display === '';
  if (open) {
    calcReturnFocus = document.activeElement;
    popup.style.display = 'block';
    overlay.style.display = 'block';
    requestAnimationFrame(() => {
      popup.style.transform   = 'translateX(0)';
      overlay.style.opacity   = '1';
    });
    document.body.style.overflow = 'hidden';
    popup.focus({ preventScroll: true });
  } else {
    popup.style.transform  = 'translateX(100%)';
    overlay.style.opacity  = '0';
    setTimeout(() => { popup.style.display = 'none'; overlay.style.display = 'none'; }, 420);
    document.body.style.overflow = '';
    if (calcReturnFocus && calcReturnFocus.focus) calcReturnFocus.focus({ preventScroll: true });
  }
  btn.classList.toggle('is-open', open);
  btn.setAttribute('aria-expanded', open ? 'true' : 'false');
}

function pcMark(el, on) {
  el.classList.toggle('selected', on);
  el.setAttribute('aria-pressed', on ? 'true' : 'false');
}

function pcSelect(group, el) {
  $('pc-type').querySelectorAll('.pc-opt').forEach(o => {
    o.style.borderColor = 'var(--border)';
    o.style.color       = 'var(--gray2)';
    o.style.background  = 'transparent';
    pcMark(o, false);
  });
  el.style.borderColor = 'var(--gold)';
  el.style.color       = 'var(--gold)';
  el.style.background  = 'rgba(200,169,110,0.07)';
  pcMark(el, true);
  pcState.type = el.dataset.val;
  $('rv-type2').textContent = el.dataset.label || el.dataset.val;
  pcCalc();
}

function pcSelectSz(el) {
  document.querySelectorAll('.pc-opt-sz').forEach(o => {
    o.style.borderColor = 'var(--border)';
    o.style.background  = 'transparent';
    o.querySelector('div').style.color = 'var(--white)';
    pcMark(o, false);
  });
  el.style.borderColor = 'var(--gold)';
  el.style.background  = 'rgba(200,169,110,0.07)';
  el.querySelector('div').style.color = 'var(--gold)';
  pcMark(el, true);
  pcState.size = el.dataset.val;
  $('rv-size2').textContent = pcPrices.size[el.dataset.val].label;
  pcCalc();
}

function pcSelectMat(el) {
  document.querySelectorAll('.pc-opt-mat').forEach(o => {
    o.style.borderColor = 'var(--border)';
    o.style.background  = 'transparent';
    o.querySelector('div').style.color = 'var(--white)';
    pcMark(o, false);
  });
  el.style.borderColor = 'var(--gold)';
  el.style.background  = 'rgba(200,169,110,0.06)';
  el.querySelector('div').style.color = 'var(--gold)';
  pcMark(el, true);
  pcState.material = el.dataset.val;
  pcState.matMult  = parseFloat(el.dataset.mult);
  $('rv-mat2').textContent = el.querySelector('div').textContent;
  pcCalc();
}

function pcPaintExt(el, on) {
  pcMark(el, on);
  el.style.borderColor = on ? 'var(--gold)' : 'var(--border)';
  el.style.color       = on ? 'var(--gold)' : 'var(--gray2)';
  el.style.background  = on ? 'rgba(200,169,110,0.07)' : 'transparent';
  const check = el.querySelector('div');
  if (check) { check.style.background = on ? 'var(--gold)' : ''; check.style.color = on ? 'var(--bg)' : ''; }
}

function pcToggleExt(el) {
  pcPaintExt(el, !el.classList.contains('selected'));
  pcCalc();
}

function pcCalc(instant) {
  const r = pcCompute();
  pcState.extras = r.extras;
  const extRow = $('rv-ext-row'), extEl = $('rv-ext2');
  extRow.style.opacity = r.extras > 0 ? '1' : '0.4';
  extEl.textContent = r.extras > 0 ? '+' + money(r.extras) + ' ₴' : '—';
  const discRow = $('rv-disc-row'), discEl = $('rv-disc2');
  discRow.style.opacity = r.discount > 0 ? '1' : '0.4';
  discEl.textContent = r.discount > 0 ? '−' + money(r.discount) + ' ₴' : '—';
  pcAnimatePrice(r.total, instant);
}

function pcRenderPrice(v) {
  pcShown = v;
  $('pc-price').innerHTML = money(Math.round(v)) + ' <span style="font-size:18px;color:var(--gray2);">₴</span>';
}

function pcAnimatePrice(target, instant) {
  cancelAnimationFrame(pcAnimFrame);
  if (instant || pcShown === null) { pcRenderPrice(target); return; }
  const start = pcShown, diff = target - start, duration = 500;
  let startTime;
  function step(ts) {
    if (!startTime) startTime = ts;
    const p = Math.min((ts - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    pcRenderPrice(p < 1 ? start + diff * ease : target);
    if (p < 1) pcAnimFrame = requestAnimationFrame(step);
  }
  pcAnimFrame = requestAnimationFrame(step);
}

function pcReset() {
  document.querySelectorAll('.pc-ext').forEach(el => pcPaintExt(el, false));
  pcState = { type:'neon', size:'s', material:'silicone', matMult:1.0, extras:0 };
  pcSelect('type', document.querySelector('.pc-opt[data-val="neon"]'));
  pcSelectSz(document.querySelector('.pc-opt-sz[data-val="s"]'));
  pcSelectMat(document.querySelector('.pc-opt-mat[data-val="silicone"]'));
}

function pcSummary() {
  const typeEl = document.querySelector('.pc-opt.selected');
  const sizeEl = document.querySelector('.pc-opt-sz.selected');
  const matEl  = document.querySelector('.pc-opt-mat.selected');
  const r = pcCompute();
  const extras = Array.from(document.querySelectorAll('.pc-ext.selected')).map(e => e.lastChild.textContent.trim()).join(', ') || '—';
  const type = typeEl ? (typeEl.dataset.label || typeEl.dataset.val) : '';
  const lines = [
    'Розрахунок з калькулятора LUMIS',
    'Тип: ' + type,
    'Розмір: ' + (sizeEl ? pcPrices.size[sizeEl.dataset.val].label : ''),
    'Матеріал: ' + (matEl ? matEl.querySelector('div').textContent : ''),
    'Додатково: ' + extras + (r.extras ? ' (+' + money(r.extras) + ' ₴)' : '')
  ];
  if (r.discount) lines.push('Знижка 5%: −' + money(r.discount) + ' ₴');
  lines.push('Орієнтовна ціна: від ' + money(r.total) + ' ₴ (без ПДВ)');
  return { text: lines.join('\n'), type };
}

// "Отримати точний розрахунок": the selection travels into the request form,
// so it reaches the studio together with the contacts and files.
function pcSend() {
  const sum = pcSummary();
  if ($('lead-success').classList.contains('show')) resetLeadForm();
  leadCalc = sum.text;
  $('lead-calc-text').textContent = sum.text;
  $('lead-calc').hidden = false;
  if (!$('lead-order').value.trim()) $('lead-order').value = sum.type;
  calcReturnFocus = null;
  toggleCalc();
  $('lead-form').classList.add('visible');
  setTimeout(() => {
    $('contact').scrollIntoView({ behavior: 'smooth' });
    $('lead-name').focus({ preventScroll: true });
  }, 60);
}

pcCalc(true);

// ══════════════════════════════
//  THEME TOGGLE
// ══════════════════════════════
const THEME_KEY = 'lumis_theme';

function syncThemeMeta() {
  const light = document.body.classList.contains('light-mode');
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', light ? '#fdf6ed' : '#0c0a08');
  $('theme-toggle-btn').setAttribute('aria-pressed', light ? 'true' : 'false');
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('light-mode');
  store.set(THEME_KEY, isLight ? 'light' : 'dark');
  syncThemeMeta();
}

(function() {
  const saved = store.get(THEME_KEY);
  if (saved === 'light') {
    document.body.classList.add('light-mode');
  } else if (!saved) {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      document.body.classList.add('light-mode');
    }
  }
  syncThemeMeta();
})();

if (window.matchMedia) {
  const mq = window.matchMedia('(prefers-color-scheme: light)');
  const onScheme = e => {
    if (!store.get(THEME_KEY)) { document.body.classList.toggle('light-mode', e.matches); syncThemeMeta(); }
  };
  if (mq.addEventListener) mq.addEventListener('change', onScheme); else if (mq.addListener) mq.addListener(onScheme);
}

// ══════════════════════════════
//  SITE CONTENT (published by the admin, stored on the server)
// ══════════════════════════════
const TOGGLES = { carousel: 'toggle-carousel', process: 'toggle-process', instagram: 'toggle-ig', cursor: 'toggle-cursor' };
const aboutTitleEl = document.querySelector('.about-text .section-title');
const DEFAULT_ABOUT_TITLE_HTML = aboutTitleEl ? aboutTitleEl.innerHTML : '';
const heroSubEl = document.querySelector('.hero-sub');
const DEFAULT_HERO_SUB_HTML = heroSubEl ? heroSubEl.innerHTML : '';
const carouselDefaults = realCards().map(c => ({ html: c.querySelector('.car-circle').innerHTML, style: c.querySelector('.car-circle').getAttribute('style') || '' }));
const portfolioDefaults = Array.from(document.querySelectorAll('.portfolio-item')).map(el => el.style.backgroundImage);

const portfolioNames = Array.from(document.querySelectorAll('.pi-label-name')).map(el => el.textContent);
const portfolioTypes = Array.from(document.querySelectorAll('.pi-label-type')).map(el => el.textContent);
const stepNames = Array.from(document.querySelectorAll('.step-name')).map(el => el.textContent);
const stepDescs = Array.from(document.querySelectorAll('.step-desc')).map(el => el.textContent);

// Default SVG icons / backgrounds for slides added from the admin panel
const defaultIcons = [
  '<circle cx="55" cy="55" r="22" fill="none" stroke="#c8a96e" stroke-width="1.4"/><polygon points="55,33 60,48 76,48 63,58 68,73 55,63 42,73 47,58 34,48 50,48" fill="none" stroke="#c8a96e" stroke-width="1.3"/>',
  '<polygon points="55,28 80,55 55,82 30,55" fill="none" stroke="#c8a96e" stroke-width="1.4"/><polygon points="55,38 70,55 55,72 40,55" fill="none" stroke="#c8a96e" stroke-width="0.8" opacity="0.5"/>',
  '<polyline points="62,24 44,58 57,58 48,86 72,48 59,48 68,24" fill="none" stroke="#c8a96e" stroke-width="1.5" stroke-linejoin="round"/>',
  '<circle cx="55" cy="55" r="28" fill="none" stroke="#c8a96e" stroke-width="1.4"/><circle cx="55" cy="55" r="16" fill="none" stroke="#c8a96e" stroke-width="1"/><circle cx="55" cy="55" r="5" fill="#c8a96e" opacity="0.5"/>',
];
const defaultGradients = [
  'radial-gradient(circle at 40% 35%, #1e1a14, #0f0d0b)',
  'radial-gradient(circle at 60% 40%, #141820, #0a0c10)',
  'radial-gradient(circle at 35% 60%, #1a1820, #0c0a10)',
  'radial-gradient(circle at 50% 30%, #1a1410, #0d0b08)',
];

// Working state of everything that is not a plain text field.
const site = {
  colors: { gold: '', bg: '' },
  toggles: { carousel: true, process: true, instagram: true, cursor: true },
  carousel: realCards().map(c => ({ label: c.querySelector('.car-label').textContent, image: '' })),
  portfolioImages: ['', '', '', '', '', '']
};
const DEFAULT_SITE = JSON.parse(JSON.stringify(site));
const DEFAULT_FIELDS = {};
document.querySelectorAll('#admin-panel .adm-input[id^="edit-"], #admin-panel .adm-textarea[id^="edit-"]').forEach(el => { DEFAULT_FIELDS[el.id] = el.value; });
portfolioNames.forEach((n, i) => { DEFAULT_FIELDS['pi-name-' + i] = n; DEFAULT_FIELDS['pi-type-' + i] = portfolioTypes[i] || ''; });
stepNames.forEach((n, i) => { DEFAULT_FIELDS['step-name-' + i] = n; DEFAULT_FIELDS['step-desc-' + i] = stepDescs[i] || ''; });

const isUploadUrl = u => typeof u === 'string' && /^uploads\/[a-f0-9]{32}\.(jpg|png|webp)$/.test(u);
const isHttpsUrl = u => typeof u === 'string' && /^https:\/\/[A-Za-z0-9.\-]+(\/[^\s"'<>]*)?$/.test(u);

// Writes text fields to the page. Values are plain text: nothing is inserted as HTML.
function applyFields(f) {
  const has = k => typeof f[k] === 'string';
  if (has('edit-brand') && f['edit-brand'].trim()) {
    document.querySelectorAll('.nav-logo-text, .footer-logo').forEach(el => el.textContent = f['edit-brand']);
  }
  const eyebrow = document.querySelector('.hero-eyebrow');
  if (eyebrow && has('edit-eyebrow')) eyebrow.textContent = f['edit-eyebrow'];
  if (heroSubEl && has('edit-hero-sub')) {
    if (f['edit-hero-sub'] === DEFAULT_FIELDS['edit-hero-sub']) {
      heroSubEl.innerHTML = DEFAULT_HERO_SUB_HTML;      // the built-in copy with its own line break
    } else {
      heroSubEl.textContent = '';
      f['edit-hero-sub'].split('\n').forEach((line, i) => {
        if (i) heroSubEl.appendChild(document.createElement('br'));
        heroSubEl.appendChild(document.createTextNode(line));
      });
    }
  }
  if (aboutTitleEl && has('edit-about-title')) {
    if (f['edit-about-title'] === DEFAULT_FIELDS['edit-about-title']) aboutTitleEl.innerHTML = DEFAULT_ABOUT_TITLE_HTML;
    else aboutTitleEl.textContent = f['edit-about-title'];
  }
  const aboutPs = document.querySelectorAll('.about-text p');
  if (aboutPs[0] && has('edit-about-p1')) aboutPs[0].textContent = f['edit-about-p1'];
  if (aboutPs[1] && has('edit-about-p2')) aboutPs[1].textContent = f['edit-about-p2'];
  const statNum = document.querySelector('.about-stat-num'), statLbl = document.querySelector('.about-stat-label');
  if (statNum && has('edit-stat-num')) statNum.textContent = f['edit-stat-num'];
  if (statLbl && has('edit-stat-label')) statLbl.textContent = f['edit-stat-label'];

  const piNames = document.querySelectorAll('.pi-label-name'), piTypes = document.querySelectorAll('.pi-label-type');
  const items = document.querySelectorAll('.portfolio-item');
  for (let i = 0; i < 6; i++) {
    if (piNames[i] && has('pi-name-' + i)) piNames[i].textContent = f['pi-name-' + i];
    if (piTypes[i] && has('pi-type-' + i)) piTypes[i].textContent = f['pi-type-' + i];
    if (items[i] && piNames[i] && piTypes[i]) items[i].setAttribute('aria-label', piNames[i].textContent + ' — ' + piTypes[i].textContent);
  }
  const stepNameEls = document.querySelectorAll('.step-name'), stepDescEls = document.querySelectorAll('.step-desc');
  for (let i = 0; i < 4; i++) {
    if (stepNameEls[i] && has('step-name-' + i)) stepNameEls[i].textContent = f['step-name-' + i];
    if (stepDescEls[i] && has('step-desc-' + i)) stepDescEls[i].textContent = f['step-desc-' + i];
  }

  const phoneEl = $('contact-phone-link');
  if (phoneEl && has('edit-phone') && f['edit-phone'].trim()) { phoneEl.textContent = f['edit-phone']; phoneEl.setAttribute('href', 'tel:' + f['edit-phone'].replace(/[^+0-9]/g, '')); }
  const emailEl = $('contact-email-link');
  if (emailEl && has('edit-email') && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f['edit-email'])) { emailEl.textContent = f['edit-email']; emailEl.setAttribute('href', 'mailto:' + f['edit-email']); }
  if ($('contact-address') && has('edit-address')) $('contact-address').textContent = f['edit-address'];
  if ($('contact-hours') && has('edit-hours')) $('contact-hours').textContent = f['edit-hours'];
  const footCopy = document.querySelector('.footer-copy');
  if (footCopy && has('edit-copyright')) footCopy.textContent = f['edit-copyright'];
  // Only https links: a "javascript:" address must never reach an href.
  if (has('edit-instagram') && isHttpsUrl(f['edit-instagram'])) {
    document.querySelectorAll('.ig-icon-btn').forEach(a => a.setAttribute('href', f['edit-instagram']));
  }
}

function applyColors() {
  ['gold', 'bg'].forEach(name => {
    const v = site.colors[name];
    if (/^#[0-9a-fA-F]{6}$/.test(v || '')) document.documentElement.style.setProperty('--' + name, v);
    else document.documentElement.style.removeProperty('--' + name);
  });
}

function applyToggles() {
  $('categories').style.display = site.toggles.carousel ? '' : 'none';
  $('process').style.display = site.toggles.process ? '' : 'none';
  document.querySelectorAll('.ig-icon-btn').forEach(el => el.style.display = site.toggles.instagram ? '' : 'none');
  cursorWanted = site.toggles.cursor;
  applyCursorMode();
  Object.keys(TOGGLES).forEach(k => {
    const t = $(TOGGLES[k]);
    if (t) { t.classList.toggle('on', !!site.toggles[k]); t.setAttribute('aria-checked', site.toggles[k] ? 'true' : 'false'); }
  });
}

function paintCircle(circle, i, image) {
  const def = carouselDefaults[i];
  if (isUploadUrl(image)) {
    circle.textContent = '';
    circle.setAttribute('style', 'background-image:url("' + image + '");background-size:cover;background-position:center;');
  } else if (def) {
    circle.setAttribute('style', def.style);
    circle.innerHTML = def.html;
  } else {
    circle.setAttribute('style', 'background:' + defaultGradients[i % defaultGradients.length] + ';');
    circle.innerHTML = '<svg aria-hidden="true" viewBox="0 0 110 110" fill="none" width="80" height="80">' + defaultIcons[i % defaultIcons.length] + '</svg>';
  }
}

// Makes the real slides match site.carousel (count, labels, pictures).
function applyCarousel() {
  car.querySelectorAll('.car-clone').forEach(el => el.remove());
  let cards = realCards();
  while (cards.length > site.carousel.length) { cards.pop().remove(); }
  while (cards.length < site.carousel.length) {
    const card = document.createElement('div');
    card.className = 'car-card';
    card.setAttribute('role', 'link');
    card.setAttribute('tabindex', '0');
    card.addEventListener('click', goToContact);
    card.innerHTML = '<div class="car-circle"></div><div class="car-label"></div>';
    car.appendChild(card);
    cards.push(card);
  }
  cards.forEach((card, i) => {
    card.querySelector('.car-label').textContent = site.carousel[i].label;
    paintCircle(card.querySelector('.car-circle'), i, site.carousel[i].image);
  });
  rebuildInfiniteClones(false);
}

function applyPortfolioImages() {
  document.querySelectorAll('.portfolio-item').forEach((el, i) => {
    el.style.backgroundImage = isUploadUrl(site.portfolioImages[i]) ? 'url("' + site.portfolioImages[i] + '")' : (portfolioDefaults[i] || '');
  });
}

function applyContent(content) {
  if (!content || typeof content !== 'object') return;
  if (content.colors) { site.colors.gold = content.colors.gold || ''; site.colors.bg = content.colors.bg || ''; }
  if (content.toggles) Object.keys(site.toggles).forEach(k => { if (k in content.toggles) site.toggles[k] = !!content.toggles[k]; });
  if (Array.isArray(content.carousel) && content.carousel.length) {
    site.carousel = content.carousel.slice(0, 20).map(s => ({ label: String((s && s.label) || 'Слайд').slice(0, 60), image: isUploadUrl(s && s.image) ? s.image : '' }));
  }
  if (Array.isArray(content.portfolioImages)) site.portfolioImages = [0,1,2,3,4,5].map(i => isUploadUrl(content.portfolioImages[i]) ? content.portfolioImages[i] : '');
  applyFields(content.fields || {});
  applyColors();
  applyToggles();
  applyCarousel();
  applyPortfolioImages();
}

let publishedContent = null;
// Every visitor gets the published version. Without a server the page keeps its built-in content.
apiCall('content.php', { timeout: 8000 }).then(res => {
  publishedContent = res.content || null;
  if (publishedContent) applyContent(publishedContent);
}).catch(() => {});

// ══════════════════════════════
//  ADMIN PANEL
// ══════════════════════════════
const LEGACY_PASS_KEY = 'lumis_admin_pass';     // old client-side password, removed on first server login
const LEGACY_DATA_KEY = 'lumis_admin_data';     // old browser-only edits, offered for import
const admin = { authed: false, csrf: null, mustChange: false, built: false, returnFocus: null };

function showToast(msg, isError) {
  const t = $('adm-toast');
  t.textContent = msg;
  t.classList.toggle('is-error', !!isError);
  t.classList.add('show');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => t.classList.remove('show'), isError ? 5000 : 2600);
}
function adminMsg(text, isError) {
  const box = $('adm-msg');
  box.hidden = !text;
  box.textContent = text || '';
  box.classList.toggle('is-error', !!isError);
}
function apiErrorText(err, fallback) {
  if (err && err.network) return 'Сервер недоступний. Перевірте з\'єднання.';
  if (err && err.noBackend) return 'Серверна частина сайту не відповідає (api/ не встановлено або не працює PHP).';
  return (err && err.message) || fallback;
}
function sessionLost(err) {
  if (err && (err.status === 401 || err.code === 'bad_csrf')) {
    admin.authed = false; admin.csrf = null;
    showLock('Сесію завершено. Увійдіть знову.');
    return true;
  }
  return false;
}

function showLock(note) {
  $('admin-panel').classList.add('locked');
  $('admin-setpass').classList.add('hidden');
  $('admin-lock').classList.remove('hidden');
  $('adm-logout').hidden = true;
  $('lock-err').textContent = note || '';
  setTimeout(() => $('lock-input').focus(), 50);
}
function showSetPass(forced) {
  $('admin-panel').classList.add('locked');
  $('admin-lock').classList.add('hidden');
  $('admin-setpass').classList.remove('hidden');
  $('setpass-title').textContent = forced ? 'Задайте власний пароль замість стартового' : 'Зміна пароля';
  $('setpass-cancel').hidden = !!forced;
  ['setpass-current', 'setpass-new', 'setpass-repeat'].forEach(id => $(id).value = '');
  $('setpass-err').textContent = '';
  setTimeout(() => $('setpass-current').focus(), 50);
}
function enterAdmin() {
  $('admin-panel').classList.remove('locked');
  $('admin-lock').classList.add('hidden');
  $('admin-setpass').classList.add('hidden');
  $('adm-logout').hidden = false;
  if (!admin.built) { buildDynamicFields(); admin.built = true; }
  fillAdminForm();
  offerLegacyImport();
}

async function openAdmin() {
  admin.returnFocus = document.activeElement;
  document.body.classList.add('admin-entry');
  $('admin-overlay').classList.add('open');
  $('admin-panel').classList.add('open');
  document.body.style.overflow = 'hidden';
  if (admin.authed) { if (admin.mustChange) showSetPass(true); else enterAdmin(); return; }
  showLock('');
  try {
    const st = await apiCall('auth.php');
    if (st.authenticated) {
      admin.authed = true; admin.csrf = st.csrf; admin.mustChange = !!st.must_change;
      if (admin.mustChange) showSetPass(true); else enterAdmin();
    }
  } catch (err) {
    $('lock-err').textContent = apiErrorText(err, 'Сервер недоступний') + ' Вхід неможливий.';
  }
}
function closeAdmin() {
  $('admin-overlay').classList.remove('open');
  $('admin-panel').classList.remove('open');
  document.body.style.overflow = '';
  if (admin.returnFocus && admin.returnFocus.focus) admin.returnFocus.focus({ preventScroll: true });
}

async function checkPass() {
  const input = $('lock-input'), btn = $('lock-submit');
  if (!input.value) { $('lock-err').textContent = 'Введіть пароль'; return; }
  btn.disabled = true;
  try {
    const res = await apiCall('auth.php', { method: 'POST', json: { action: 'login', password: input.value } });
    admin.authed = true; admin.csrf = res.csrf; admin.mustChange = !!res.must_change;
    input.value = '';
    $('lock-err').textContent = '';
    store.del(LEGACY_PASS_KEY);
    if (admin.mustChange) showSetPass(true); else enterAdmin();
  } catch (err) {
    input.value = '';
    $('lock-err').textContent = apiErrorText(err, 'Не вдалося увійти');
    input.focus();
  } finally {
    btn.disabled = false;
  }
}

async function logoutAdmin() {
  try { await apiCall('auth.php', { method: 'POST', csrf: admin.csrf, json: { action: 'logout' } }); } catch (e) {}
  admin.authed = false; admin.csrf = null; admin.mustChange = false;
  // Unsaved previews must not linger on the public page.
  location.reload();
}

function changePass() { showSetPass(false); }
function cancelNewPass() { $('admin-setpass').classList.add('hidden'); $('admin-panel').classList.remove('locked'); }
async function submitNewPass() {
  const cur = $('setpass-current').value, nw = $('setpass-new').value, rep = $('setpass-repeat').value;
  const err = $('setpass-err'), btn = $('setpass-submit');
  if (!cur) { err.textContent = 'Введіть поточний пароль'; return; }
  if (nw.length < 10) { err.textContent = 'Новий пароль — щонайменше 10 символів'; return; }
  if (nw !== rep) { err.textContent = 'Паролі не збігаються'; return; }
  btn.disabled = true;
  try {
    const res = await apiCall('auth.php', { method: 'POST', csrf: admin.csrf, json: { action: 'change_password', current: cur, new: nw } });
    admin.csrf = res.csrf; admin.mustChange = false;
    enterAdmin();
    showToast('Пароль змінено');
  } catch (e) {
    if (!sessionLost(e)) err.textContent = apiErrorText(e, 'Не вдалося змінити пароль');
  } finally {
    btn.disabled = false;
  }
}

// ── Tabs ──
function switchTab(name) {
  document.querySelectorAll('.adm-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.adm-pane').forEach(p => p.classList.remove('active'));
  const pane = $('pane-' + name);
  if (pane) pane.classList.add('active');
  if (name === 'leads') loadLeads();
}

// ── Dynamic fields (built with DOM methods: values never pass through innerHTML) ──
function field(labelText, id, value, multiline) {
  const wrap = document.createElement('div');
  wrap.className = 'adm-field';
  const label = document.createElement('label');
  label.className = 'adm-label'; label.htmlFor = id; label.textContent = labelText;
  const input = document.createElement(multiline ? 'textarea' : 'input');
  input.className = multiline ? 'adm-textarea' : 'adm-input';
  input.id = id; input.value = value;
  input.maxLength = multiline ? 800 : 160;
  input.addEventListener('input', liveUpdate);
  wrap.appendChild(label); wrap.appendChild(input);
  return wrap;
}
const UPLOAD_ICON = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>';
function photoSlot(id, type, idx, caption, image) {
  const slot = document.createElement('div');
  slot.className = 'adm-photo-slot'; slot.id = id; slot.title = caption;
  const input = document.createElement('input');
  input.type = 'file'; input.accept = 'image/jpeg,image/png,image/webp';
  input.setAttribute('aria-label', 'Завантажити фото: ' + caption);
  input.addEventListener('change', () => loadPhoto(input, type, idx));
  slot.appendChild(input);
  slot.insertAdjacentHTML('beforeend', UPLOAD_ICON);
  const span = document.createElement('span');
  span.textContent = caption.split(' ')[0];
  slot.appendChild(span);
  if (isUploadUrl(image)) { const img = document.createElement('img'); img.src = image; img.alt = ''; slot.appendChild(img); }
  return slot;
}

function buildDynamicFields() {
  const pt = $('portfolio-titles');
  pt.textContent = '';
  portfolioNames.forEach((n, i) => {
    pt.appendChild(field('Проєкт ' + (i + 1) + ' — назва', 'pi-name-' + i, n));
    const t = field('Тип', 'pi-type-' + i, portfolioTypes[i] || '');
    t.style.marginTop = '-8px';
    pt.appendChild(t);
  });
  const ps = $('process-steps-edit');
  ps.textContent = '';
  stepNames.forEach((n, i) => {
    ps.appendChild(field('Крок ' + (i + 1) + ' — назва', 'step-name-' + i, n));
    const d = field('Опис', 'step-desc-' + i, stepDescs[i] || '', true);
    d.style.marginTop = '-8px';
    ps.appendChild(d);
  });
  rebuildPhotoAdmin();
}

function rebuildPhotoAdmin() {
  const pp = $('portfolio-photos');
  pp.textContent = '';
  portfolioNames.forEach((n, i) => pp.appendChild(photoSlot('pslot-' + i, 'portfolio', i, n, site.portfolioImages[i])));
  rebuildCarouselAdmin();
}

function rebuildCarouselAdmin() {
  const cp = $('carousel-photos');
  if (!cp) return;
  $('carousel-count').textContent = site.carousel.length;
  cp.textContent = '';
  site.carousel.forEach((s, i) => {
    const col = document.createElement('div');
    col.style.cssText = 'display:flex;flex-direction:column;gap:4px;';
    col.appendChild(photoSlot('cslot-' + i, 'carousel', i, s.label, s.image));
    const input = document.createElement('input');
    input.className = 'adm-input';
    input.style.cssText = 'font-size:12px;padding:7px 8px;';
    input.value = s.label; input.maxLength = 60; input.placeholder = 'Назва слайду';
    input.setAttribute('aria-label', 'Назва слайду ' + (i + 1));
    input.addEventListener('input', () => { site.carousel[i].label = input.value; updateCarouselLabel(i); });
    col.appendChild(input);
    cp.appendChild(col);
  });
}

function updateCarouselLabel(i) {
  const slides = realCards();
  if (slides[i]) slides[i].querySelector('.car-label').textContent = site.carousel[i].label;
  rebuildInfiniteClones(true);
}

function addCarouselSlide() {
  if (site.carousel.length >= 20) { showToast('Максимум 20 слайдів', true); return; }
  const name = (prompt('Назва нового слайду:', 'Новий слайд') || 'Новий слайд').slice(0, 60);
  site.carousel.push({ label: name, image: '' });
  applyCarousel();
  rebuildCarouselAdmin();
  showToast('Слайд додано — натисніть «Зберегти»');
}

function removeLastCarouselSlide() {
  if (site.carousel.length <= 1) { showToast('Мінімум 1 слайд', true); return; }
  if (!confirm('Видалити останній слайд?')) return;
  site.carousel.pop();
  applyCarousel();
  rebuildCarouselAdmin();
  showToast('Слайд видалено — натисніть «Зберегти»');
}

// ── Form ⇄ state ──
function collectFields() {
  const f = {};
  document.querySelectorAll('#admin-panel .adm-pane .adm-input[id], #admin-panel .adm-pane .adm-textarea[id]').forEach(el => {
    if (/^(edit-|pi-(name|type)-|step-(name|desc)-)/.test(el.id)) f[el.id] = el.value;
  });
  return f;
}
function fillAdminForm() {
  const f = Object.assign({}, DEFAULT_FIELDS, (publishedContent && publishedContent.fields) || {});
  Object.keys(f).forEach(id => { const el = $(id); if (el && typeof f[id] === 'string') el.value = f[id]; });
  [['gold', '#c8a96e'], ['bg', '#0c0a08']].forEach(([name, def]) => {
    const v = site.colors[name] || def;
    $('color-' + name).value = v; $('color-' + name + '-hex').value = v;
  });
  applyToggles();
  rebuildPhotoAdmin();
}

function liveUpdate() {
  applyFields(collectFields());
}

// ── Photos: uploaded to the server right away, published together with "Зберегти" ──
async function loadPhoto(input, type, idx) {
  const file = input.files[0];
  input.value = '';
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { showToast('Файл занадто великий (макс 5MB)', true); return; }
  const fd = new FormData();
  fd.append('image', file, file.name);
  showToast('Завантажуємо фото…');
  try {
    const res = await apiCall('upload.php', { method: 'POST', csrf: admin.csrf, form: fd, timeout: 120000 });
    if (type === 'portfolio') { site.portfolioImages[idx] = res.url; applyPortfolioImages(); }
    else { site.carousel[idx].image = res.url; applyCarousel(); }
    rebuildPhotoAdmin();
    showToast('Фото завантажено — натисніть «Зберегти»');
  } catch (err) {
    if (!sessionLost(err)) showToast('Фото не завантажено: ' + apiErrorText(err, 'помилка сервера'), true);
  }
}

// ── Colours ──
function updateColor(varName, val) {
  if (!(varName in site.colors) || !/^#[0-9a-fA-F]{6}$/.test(val)) return;
  site.colors[varName] = val;
  applyColors();
  const hexInput = $('color-' + varName + '-hex');
  if (hexInput) { hexInput.value = val; hexInput.removeAttribute('aria-invalid'); }
}
function updateColorFromHex(varName, val) {
  const hexInput = $('color-' + varName + '-hex');
  if (/^#[0-9a-fA-F]{6}$/.test(val)) {
    site.colors[varName] = val;
    applyColors();
    const picker = $('color-' + varName);
    if (picker) picker.value = val;
    if (hexInput) hexInput.removeAttribute('aria-invalid');
  } else if (hexInput) {
    hexInput.setAttribute('aria-invalid', 'true');
  }
}

// ── Section toggles ──
function flipToggle(key) {
  site.toggles[key] = !site.toggles[key];
  applyToggles();
}
function toggleSection(sectionId) { flipToggle(sectionId === 'categories' ? 'carousel' : 'process'); }
function toggleInstagram() { flipToggle('instagram'); }
function toggleCursor() { flipToggle('cursor'); }

// ── Save / Reset: the server is the only place where changes are kept ──
function clearAdminFieldErrors() {
  document.querySelectorAll('#admin-panel .adm-field-err').forEach(el => el.remove());
  document.querySelectorAll('#admin-panel [aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
}
function showAdminFieldErrors(fields) {
  let firstTab = null;
  Object.keys(fields || {}).forEach(id => {
    const el = $(id);
    if (!el) return;
    el.setAttribute('aria-invalid', 'true');
    const note = document.createElement('div');
    note.className = 'adm-field-err'; note.textContent = fields[id];
    (el.closest('.adm-field') || el.parentNode).appendChild(note);
    if (!firstTab) { const pane = el.closest('.adm-pane'); firstTab = pane ? pane.id.replace('pane-', '') : null; }
  });
  if (firstTab) switchTab(firstTab);
}

async function saveAll() {
  clearAdminFieldErrors();
  const content = {
    fields: collectFields(), colors: site.colors, toggles: site.toggles,
    carousel: site.carousel, portfolioImages: site.portfolioImages
  };
  try {
    const res = await apiCall('content.php', { method: 'POST', csrf: admin.csrf, json: { content } });
    publishedContent = res.content;
    adminMsg('', false);
    showToast('Опубліковано ✓');
  } catch (err) {
    if (sessionLost(err)) return;
    if (err.status === 422 && err.fields) showAdminFieldErrors(err.fields);
    showToast('Не збережено: ' + apiErrorText(err, 'помилка сервера'), true);
  }
}

async function resetAll() {
  if (!confirm('Повернути сайт до початкового вигляду? Опубліковані зміни буде скасовано (резервна копія залишиться на сервері).')) return;
  try {
    await apiCall('content.php', { method: 'POST', csrf: admin.csrf, json: { action: 'reset' } });
    location.reload();
  } catch (err) {
    if (!sessionLost(err)) showToast('Не скинуто: ' + apiErrorText(err, 'помилка сервера'), true);
  }
}

// Edits made with the old browser-only panel are still in this browser: offer them, never delete them.
function offerLegacyImport() {
  if (publishedContent) return;
  let legacy = null;
  try { legacy = JSON.parse(store.get(LEGACY_DATA_KEY) || 'null'); } catch (e) {}
  if (!legacy || typeof legacy !== 'object') return;
  let used = 0;
  Object.keys(legacy).forEach(id => {
    const el = $(id);
    if (el && typeof legacy[id] === 'string' && /^(edit-|pi-(name|type)-|step-(name|desc)-)/.test(id) && el.value !== legacy[id]) { el.value = legacy[id]; used++; }
  });
  if (used) {
    liveUpdate();
    adminMsg('Знайдено зміни зі старої панелі, збережені лише в цьому браузері. Їх підставлено у форму — перевірте та натисніть «Зберегти», щоб опублікувати для всіх.', false);
  }
}

// ── Leads ──
const METHOD_LABELS = { email: 'Email', telegram: 'Telegram', viber: 'Viber', instagram: 'Instagram' };
async function loadLeads() {
  const list = $('leads-list'), msg = $('leads-msg');
  msg.hidden = false; msg.classList.remove('is-error'); msg.textContent = 'Завантаження…';
  try {
    const res = await apiCall('leads.php?action=list');
    list.textContent = '';
    msg.textContent = res.total ? 'Усього заявок: ' + res.total + (res.total > res.leads.length ? ' (показано останні ' + res.leads.length + ')' : '') : 'Заявок поки немає.';
    res.leads.forEach(lead => list.appendChild(leadCard(lead)));
  } catch (err) {
    if (sessionLost(err)) return;
    msg.classList.add('is-error');
    msg.textContent = 'Не вдалося завантажити заявки: ' + apiErrorText(err, 'помилка сервера');
  }
}
function leadCard(lead) {
  const card = document.createElement('div');
  card.className = 'lead-card';
  const head = document.createElement('div'); head.className = 'lead-card-head';
  const name = document.createElement('div'); name.className = 'lead-card-name'; name.textContent = lead.name || '—';
  const date = document.createElement('div'); date.className = 'lead-card-date';
  const d = new Date(lead.created_at);
  date.textContent = isNaN(d) ? '' : d.toLocaleString('uk', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  head.appendChild(name); head.appendChild(date); card.appendChild(head);
  const dl = document.createElement('dl');
  const row = (k, v) => { if (!v) return; const dt = document.createElement('dt'); dt.textContent = k; const dd = document.createElement('dd'); dd.textContent = v; dl.appendChild(dt); dl.appendChild(dd); return dd; };
  row('№', lead.id);
  row('Телефон', lead.phone);
  row('Зв\'язок', (METHOD_LABELS[lead.method] || lead.method || '') + (lead.handle ? ' · ' + lead.handle : ''));
  row('Тип', lead.order);
  row('Текст', lead.message);
  row('Калькулятор', lead.calc);
  if (lead.files && lead.files.length) {
    const dd = row('Файли', ' ');
    dd.textContent = '';
    lead.files.forEach((f, i) => {
      if (i) dd.appendChild(document.createTextNode(', '));
      const a = document.createElement('a');
      a.href = API + 'leads.php?action=file&id=' + encodeURIComponent(lead.id) + '&n=' + encodeURIComponent(f.n);
      a.textContent = f.name + ' (' + fmtSize(f.size) + ')';
      a.setAttribute('download', f.name);
      dd.appendChild(a);
    });
  }
  const n = lead.notify || {};
  row('Сповіщення', [n.email === true ? 'email надіслано' : n.email === false ? 'email НЕ надіслано' : '', n.telegram === true ? 'Telegram надіслано' : n.telegram === false ? 'Telegram НЕ надіслано' : ''].filter(Boolean).join(', ') || 'не налаштовано');
  card.appendChild(dl);
  const foot = document.createElement('div'); foot.className = 'lead-card-foot';
  const del = document.createElement('button'); del.type = 'button'; del.className = 'lead-card-del'; del.textContent = 'Видалити заявку';
  del.addEventListener('click', async () => {
    if (!confirm('Видалити заявку № ' + lead.id + ' разом із файлами?')) return;
    try { await apiCall('leads.php', { method: 'POST', csrf: admin.csrf, json: { action: 'delete', id: lead.id } }); card.remove(); showToast('Заявку видалено'); }
    catch (err) { if (!sessionLost(err)) showToast('Не видалено: ' + apiErrorText(err, 'помилка сервера'), true); }
  });
  foot.appendChild(del); card.appendChild(foot);
  return card;
}

// The gear button is shown only to someone who came for the panel: …/#admin or Ctrl+Shift+A.
function checkAdminHash() {
  if (location.hash === '#admin') { document.body.classList.add('admin-entry'); openAdmin(); }
}
window.addEventListener('hashchange', checkAdminHash);
checkAdminHash();

// ══════════════════════════════
//  MOBILE MENU
// ══════════════════════════════
function toggleMenu() {
  const menu = $('mobile-menu');
  const open = menu.style.display === 'none' || menu.style.display === '';
  if (open) {
    menu.style.display = 'flex';
    requestAnimationFrame(() => { menu.style.opacity = '1'; });
    document.body.style.overflow = 'hidden';
    document.body.classList.add('menu-open');
    $('hamburger').setAttribute('aria-expanded', 'true');
    $('hamburger').setAttribute('aria-label', 'Закрити меню');
  } else {
    closeMenu();
  }
}
function closeMenu() {
  const menu = $('mobile-menu');
  if (!document.body.classList.contains('menu-open')) return;
  menu.style.opacity = '0';
  setTimeout(() => { if (!document.body.classList.contains('menu-open')) menu.style.display = 'none'; }, 300);
  document.body.style.overflow = '';
  document.body.classList.remove('menu-open');
  $('hamburger').setAttribute('aria-expanded', 'false');
  $('hamburger').setAttribute('aria-label', 'Меню');
}
// Leaving the phone layout (rotation, window resize) must not leave the page locked.
if (window.matchMedia) {
  const wide = window.matchMedia('(min-width: 769px)');
  const onWide = e => { if (e.matches) closeMenu(); };
  if (wide.addEventListener) wide.addEventListener('change', onWide); else if (wide.addListener) wide.addListener(onWide);
}

// Functions used by inline handlers in the markup
Object.assign(window, {
  carScroll, goToContact, toggleTheme, toggleCalc, toggleMenu, closeMenu,
  openAdmin, closeAdmin, checkPass, logoutAdmin, changePass, cancelNewPass, submitNewPass,
  switchTab, saveAll, resetAll, liveUpdate, loadLeads,
  toggleSection, toggleInstagram, toggleCursor, updateColor, updateColorFromHex,
  addCarouselSlide, removeLastCarouselSlide,
  selectMethod, submitForm, handleFiles, removeFile, resetLeadForm, clearCalcFromForm,
  pcSelect, pcSelectSz, pcSelectMat, pcToggleExt, pcReset, pcSend
});

}); // end DOMContentLoaded
