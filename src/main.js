/* Interactions only: every piece of content is already in the HTML (build.py). */
const WORK = /*@WORK@*/{};
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
const seen = (el, fn, margin = '0px') => new IntersectionObserver(es => es.forEach(e => fn(e.isIntersecting, e)), {rootMargin: margin}).observe(el);
const soon = (el, fn, margin = '0px 0px 160px 0px') => new IntersectionObserver((es, o) => es.forEach(e => { if (e.isIntersecting) { fn(); o.disconnect(); } }), {rootMargin: margin}).observe(el);
const load = v => { if (!v.poster && v.dataset.poster) v.poster = v.dataset.poster; if (!v.src && v.dataset.src) v.src = v.dataset.src; };
const mmss = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;

/* one video at a time: starting one pauses every other */
let current = null;
function solo(v) {
  if (current && current !== v) current.pause();
  current = v; load(v);
  v.play().catch(() => {});
}
function stop(v) { v.pause(); if (current === v) current = null; }

/* ---------- hero reel ---------- */
const phone = $('#phone'), tag = $('#phoneTag'), dots = $$('#dots i');
const reelVids = $$('video', phone);
let ri = 0, heroOn = true, cardActive = false, started = false;
const reelOK = () => started && heroOn && !cardActive && !document.hidden && !$('dialog[open]');
function showReel(i) {
  ri = i;
  reelVids.forEach((v, j) => { v.classList.toggle('on', j === i); if (j !== i) v.pause(); });
  if (started) load(reelVids[(i + 1) % reelVids.length]);
  dots.forEach((d, j) => { d.classList.remove('on'); if (j === i) { void d.offsetWidth; d.classList.add('on'); } });
  tag.textContent = reelVids[i].dataset.label;
  phone.href = `media/full/${reelVids[i].dataset.k}.mp4`;
  phone.dataset.play = reelVids[i].dataset.k;
  const hp = $('#handphone');
  hp.classList.remove('pop'); void hp.offsetWidth; hp.classList.add('pop');
  reelVids[i].currentTime = 0;
  if (reelOK()) solo(reelVids[i]);
}
showReel(0);
/* the reel starts once the page has loaded, so its video never competes with the first paint */
const start = () => setTimeout(() => { started = true; if (reelOK()) solo(reelVids[ri]); load(reelVids[(ri + 1) % reelVids.length]); }, 400);
if (fine) { if (document.readyState === 'complete') start(); else addEventListener('load', start, {once: true}); }
else {
  /* phones: the poster shows first and the reel starts on the first touch or scroll (saves data, keeps the first paint still) */
  const go = () => { ['touchstart', 'scroll', 'pointerdown'].forEach(t => removeEventListener(t, go)); start(); };
  ['touchstart', 'scroll', 'pointerdown'].forEach(t => addEventListener(t, go, {passive: true, once: true}));
}
seen(phone, on => { heroOn = on; if (on && reelOK()) solo(reelVids[ri]); else stop(reelVids[ri]); });
if (!reduce) setInterval(() => { if (reelOK()) showReel((ri + 1) % reelVids.length); }, 3200);
document.addEventListener('visibilitychange', () => { if (document.hidden && current) current.pause(); });

/* ---------- goblin: parallax layers, blink, mouth opens on hover, bites on click ---------- */
const mascot = $('#mascot'), gob = $('#gob');
const lays = $$('.lay', gob), states = $$('.st', gob);
const show = st => states.forEach(i => i.classList.toggle('on', i.dataset.st === st));
let mouth = 'rest', hovering = false, biting = false;
const setMouth = m => { mouth = m; show(m); };
const parallax = e => {
  const r = gob.getBoundingClientRect();
  const nx = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / 420));
  const ny = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / 420));
  gob.style.transform = `rotateY(${(nx * 14).toFixed(2)}deg) rotateX(${(-ny * 10).toFixed(2)}deg)`;
  lays.forEach(l => { const d = +l.dataset.d; l.style.transform = `translate(${(nx * d).toFixed(2)}px, ${(ny * d * .6).toFixed(2)}px)`; });
};
mascot.addEventListener('pointerenter', () => { hovering = true; if (!biting) setMouth('open'); });
mascot.addEventListener('pointerleave', () => { hovering = false; if (!biting) setMouth('rest'); });
mascot.addEventListener('focus', () => { if (!biting) setMouth('open'); });
mascot.addEventListener('blur', () => { if (!biting) setMouth('rest'); });
/* bite sound: two real chomps (Mixkit, free license); the audio context starts inside the click */
let ac, bitesReady, biteN = 0;
function primeAudio() {
  try {
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    if (ac.state === 'suspended') ac.resume();
    bitesReady = bitesReady || Promise.all(['assets/bite1.mp3', 'assets/bite2.mp3'].map(u => fetch(u).then(r => r.arrayBuffer()).then(b => ac.decodeAudioData(b))));
  } catch (e) {}
}
async function chomp() {
  try {
    const bufs = await bitesReady, src = ac.createBufferSource(), g = ac.createGain();
    src.buffer = bufs[biteN++ % bufs.length];
    src.playbackRate.value = .96 + Math.random() * .08;
    g.gain.value = .8;
    src.connect(g).connect(ac.destination); src.start();
  } catch (e) {}
}
mascot.addEventListener('click', e => {
  e.preventDefault(); e.stopPropagation();
  if (biting) return;
  if (reduce) { openDialog('talk', mascot); return; }
  biting = true;
  primeAudio();
  mascot.classList.remove('chomp'); void mascot.offsetWidth; mascot.classList.add('chomp');
  [['open', 0], ['bite', 80], ['open', 250], ['bite', 330]].forEach(([m, t]) => setTimeout(() => { setMouth(m); if (m === 'bite') chomp(); }, t));
  setTimeout(() => { biting = false; mascot.classList.remove('chomp'); setMouth(hovering ? 'open' : 'rest'); openDialog('talk', mascot); }, 640);
});

/* ---------- counters ---------- */
function count(el) {
  const to = +el.dataset.to, dec = +el.dataset.dec, suf = el.dataset.suf || '', t0 = performance.now(), dur = 1400;
  (function step(t) {
    const p = Math.min(1, (t - t0) / dur), k = 1 - Math.pow(1 - p, 3);
    el.textContent = (to * k).toFixed(dec) + suf;
    if (p < 1) requestAnimationFrame(step);
  })(t0);
}
if (!reduce) $$('.num[data-to]').forEach(n => soon(n, () => count(n), '0px'));

/* ---------- work rows: endless, and they only move when the viewer moves them ----------
   Swipe on touch, drag or the arrows with a mouse, or scroll the page (see scroll-linked strips).
   Each row repeats its cards; when the position leaves the middle copy it jumps by exactly one copy, which looks the same.
   Mouse: the hovered card plays. Touch: the centred card plays. */
const lanes = $('#lanes'), rows = [$('#row1'), $('#row2')];
const cards = $$('.card', lanes);
let pick = null;
seen(lanes, on => { if (!on && pick) { stop(pick); pick = null; cardActive = false; } }, '100px');
/* a card's preview video only exists once it is needed (hovered or centred) */
const vidOf = c => {
  let v = $('video', c);
  if (!v) {
    v = document.createElement('video');
    Object.assign(v, {muted: true, loop: true, playsInline: true, preload: 'auto'});
    v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.setAttribute('aria-hidden', 'true');
    v.dataset.src = c.dataset.prev;
    $('.pv', c).after(v);
  }
  return v;
};
const hoverPlay = c => {
  c.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') { cardActive = true; solo(vidOf(c)); } });
  c.addEventListener('pointerleave', () => { const v = $('video', c); if (v) stop(v); cardActive = false; });
};
const ioSwipe = new IntersectionObserver(es => {
  es.forEach(e => { e.target._r = e.isIntersecting ? e.intersectionRatio : 0; });
  const best = $$('.card', lanes).filter(c => !c.hidden).reduce((a, c) => ((c._r || 0) > (a?._r || 0) ? c : a), null);
  const v = best && best._r >= .6 ? vidOf(best) : null;
  if (v === pick) return;
  if (pick) stop(pick);
  pick = v; cardActive = !!v;
  if (v) solo(v); else if (reelOK()) solo(reelVids[ri]);
}, {threshold: [0, .3, .6, .9]});
const wire = c => { if (fine) hoverPlay(c); else ioSwipe.observe(c); };
cards.forEach(wire);

/* move a scroller without breaking a drag in progress */
const shift = (el, d) => { el.scrollLeft += d; if (el._drag) el._drag.left += d; };

/* drag to scroll with a mouse (rows, formats strip, stills carousels); a drag never counts as a click */
function draggable(el) {
  el.addEventListener('pointerdown', e => {
    if (e.pointerType !== 'mouse' || e.button !== 0 || el.scrollWidth <= el.clientWidth) return;
    el._drag = {x: e.clientX, left: el.scrollLeft, id: e.pointerId, moved: false};
  });
  el.addEventListener('pointermove', e => {
    const s = el._drag;
    if (!s || e.pointerId !== s.id) return;
    const dx = e.clientX - s.x;
    if (!s.moved && Math.abs(dx) < 6) return;
    if (!s.moved) { s.moved = true; el.classList.add('dragging'); try { el.setPointerCapture(e.pointerId); } catch (_) {} }
    el.scrollLeft = s.left - dx;
    el._wrap?.();
  });
  const end = e => {
    const s = el._drag;
    if (!s || e.pointerId !== s.id) return;
    if (s.moved) { el.classList.remove('dragging'); el._dragEnd = performance.now(); }
    el._drag = null;
  };
  el.addEventListener('pointerup', end);
  el.addEventListener('pointercancel', end);
  el.addEventListener('dragstart', e => e.preventDefault());
  el.addEventListener('click', e => { if (performance.now() - (el._dragEnd || 0) < 250) { e.preventDefault(); e.stopImmediatePropagation(); } }, true);
}

/* endless scroller: copies of the originals on both sides; the position is kept inside one band of width = one copy.
   Jumps happen instantly while dragging or page-scrolling, and only once a swipe/arrow glide has settled. */
function endless(lane, own, offset) {
  const row = lane.firstElementChild;
  $$('[data-clone]', row).forEach(k => { ioSwipe.unobserve(k); k.remove(); });
  if (!own.length) { lane._wrap = null; return; }
  const one = () => own[0].offsetWidth + parseFloat(getComputedStyle(row).columnGap || 16);
  const setW = one() * own.length;
  const room = lane.clientWidth * 1.5;
  const before = Math.ceil(room / setW), after = Math.ceil((lane.clientWidth + room) / setW); /* room on both sides of the middle copy */
  const copy = () => own.map(c => {
    const k = c.cloneNode(true);
    k.dataset.clone = ''; k.setAttribute('aria-hidden', 'true'); k.tabIndex = -1; k.hidden = false;
    $('video', k)?.remove();
    wire(k);
    return k;
  });
  for (let i = 0; i < before; i++) row.prepend(...copy());
  for (let i = 0; i < after; i++) row.append(...copy());
  const lo = before * setW, hi = lo + setW;
  lane._wrap = () => {
    if (lane.scrollLeft < lo) shift(lane, setW * Math.ceil((lo - lane.scrollLeft) / setW));
    else if (lane.scrollLeft >= hi) shift(lane, -setW * Math.ceil((lane.scrollLeft - hi + 1) / setW));
  };
  lane.scrollLeft = lo + offset * setW;
  if (!lane._idle) {
    let t = 0;
    lane.addEventListener('scroll', () => { clearTimeout(t); t = setTimeout(() => lane._wrap?.(), 140); }, {passive: true});
    lane._idle = true;
  }
}
$$('.lane, .sgal, .tgal').forEach(draggable);

/* arrows (mouse devices): most of a screen at a time */
$$('.lane-wrap').forEach(w => {
  const lane = $('.lane', w);
  $('.ln.prev', w).addEventListener('click', () => { lane._wrap?.(); lane.scrollBy({left: -lane.clientWidth * .7, behavior: reduce ? 'auto' : 'smooth'}); });
  $('.ln.next', w).addEventListener('click', () => { lane._wrap?.(); lane.scrollBy({left: lane.clientWidth * .7, behavior: reduce ? 'auto' : 'smooth'}); });
});

let workFilter = 'all';
function renderWork(f) {
  workFilter = f;
  const show = cards.filter(c => f === 'all' || c.dataset.f === f);
  cards.forEach(c => { c.hidden = !show.includes(c); });
  const wraps = rows.map(r => r.closest('.lane-wrap'));
  const half = Math.ceil(cards.length / 2);
  if (f === 'all') { cards.forEach((c, i) => rows[i < half ? 0 : 1].appendChild(c)); wraps[1].hidden = false; }
  else { show.forEach(c => rows[0].appendChild(c)); cards.filter(c => c.hidden).forEach(c => rows[1].appendChild(c)); wraps[1].hidden = true; }
  /* the second row starts half a copy along, so the two rows never line up */
  rows.forEach((r, i) => endless(r.parentElement, $$('.card:not([data-clone]):not([hidden])', r), i ? .5 : 0));
}
renderWork('all');
let rw = innerWidth;
addEventListener('resize', () => { if (Math.abs(innerWidth - rw) > 40) { rw = innerWidth; renderWork(workFilter); } });
$$('.chip').forEach(c => c.addEventListener('click', () => {
  $$('.chip').forEach(x => x.setAttribute('aria-pressed', x === c));
  renderWork(c.dataset.f);
}));

/* ---------- player: the full cut with sound and native controls ---------- */
const playerVid = $('#playerVid');
function openPlayer(k, opener) {
  if (current) current.pause();
  playerVid.poster = `assets/poster-${k}.webp`; playerVid.src = `media/full/${k}.mp4`; playerVid.muted = false;
  $('#playerTitle').textContent = (WORK[k] || {}).t || 'Video';
  openDialog('player', opener);
  playerVid.play().catch(() => {});
}
$('#player').addEventListener('close', () => {
  playerVid.pause(); playerVid.removeAttribute('src'); playerVid.load();
  if (reelOK()) solo(reelVids[ri]);
});

/* ---------- BeeCatalog: flow lights up while visible, bars grow when reached ---------- */
const nodes = $$('#flow .node');
let ni = 0, flowOn = false;
seen($('#flow'), on => { flowOn = on; });
if (!reduce) setInterval(() => { if (!flowOn) return; nodes.forEach((n, i) => n.classList.toggle('lit', i <= ni)); ni = (ni + 1) % (nodes.length + 1); }, 650);
else nodes.forEach(n => n.classList.add('lit'));
soon($('#bars'), () => { if (!reduce) $('#bars').classList.add('go'); });

/* ---------- process timeline: playhead follows scroll ---------- */
const tl = $('#tl'), tc = $('#tc'), steps = $$('#steps .step');
const pad = n => String(n).padStart(2, '0');
function scrub() {
  const r = tl.getBoundingClientRect();
  let p = reduce ? 1 : (innerHeight * .9 - r.top) / (innerHeight * .75);
  p = Math.max(0, Math.min(1, p));
  tl.style.setProperty('--p', p);
  const f = Math.round(p * 30 * 24);
  tc.textContent = `00:00:${pad(Math.floor(f / 24))}:${pad(f % 24)}`;
  steps.forEach((s, i) => s.classList.toggle('on', p >= i * .25 + .02 || p === 1));
}
let ticking = false;
addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { scrub(); ticking = false; }); } }, {passive: true});
addEventListener('resize', scrub);
scrub();

/* ---------- stack terminal types itself ---------- */
const typed = $('#typed'), tg = $('#tgrid');
soon(tg, () => {
  if (reduce) return;
  const full = typed.textContent; typed.textContent = '';
  [...full].forEach((ch, i) => setTimeout(() => { typed.textContent += ch; }, i * 35));
  setTimeout(() => tg.classList.add('print'), full.length * 35);
}, '0px 0px 80px 0px');

/* ---------- goblin cursor + click sparks (mouse only) ---------- */
const gc = $('#gc');
if (fine && !reduce) {
  document.documentElement.classList.add('has-gc');
  const HOT = {default: [3, 2], link: [14, 2], click: [20, 20]};
  const LINKY = 'a,button,summary,.tr,[data-play],details,.still';
  let x = -100, y = -100, state = 'default';
  const place = () => { const h = HOT[state]; gc.style.transform = `translate3d(${x - h[0]}px, ${y - h[1]}px, 0)`; };
  addEventListener('pointermove', e => {
    if (e.pointerType !== 'mouse') return;
    x = e.clientX; y = e.clientY; gc.classList.add('on');
    if (state !== 'click') { state = e.target.closest(LINKY) ? 'link' : 'default'; gc.dataset.s = state; }
    place();
  }, {passive: true});
  addEventListener('pointerdown', e => {
    if (e.pointerType !== 'mouse') return;
    state = 'click'; gc.dataset.s = 'click'; place();
    for (let i = 0; i < 5; i++) {
      const s = document.createElement('i'); s.className = 'spark';
      const a = Math.random() * Math.PI * 2, r = 18 + Math.random() * 18;
      s.style.left = (e.clientX - 3) + 'px'; s.style.top = (e.clientY - 3) + 'px';
      s.style.setProperty('--dx', Math.cos(a) * r + 'px'); s.style.setProperty('--dy', Math.sin(a) * r + 'px');
      document.body.appendChild(s); setTimeout(() => s.remove(), 520);
    }
  });
  addEventListener('pointerup', e => { state = e.target.closest(LINKY) ? 'link' : 'default'; gc.dataset.s = state; place(); });
  document.addEventListener('mouseleave', () => gc.classList.remove('on'));
}

/* ---------- dialogs: native modal (focus stays inside, Esc closes), focus returns to the opener ---------- */
let lenis = null;
function openDialog(id, opener) {
  const d = document.getElementById(id);
  d._opener = opener || document.activeElement;
  lenis?.stop();
  d.showModal();
  d.appendChild(gc);
  ($('.close', d) || d).focus();
}
$$('dialog').forEach(d => d.addEventListener('close', () => {
  lenis?.start();
  document.body.appendChild(gc);
  d._opener?.focus?.({preventScroll: true});
}));
document.addEventListener('click', e => {
  const o = e.target.closest('[data-open]');
  if (o) { e.preventDefault(); closeMenu(); openDialog(o.dataset.open, o); return; }
  const c = e.target.closest('[data-close]');
  if (c) { c.closest('dialog').close(); return; }
  const pl = e.target.closest('[data-play]');
  if (pl) { e.preventDefault(); openPlayer(pl.dataset.play, pl); return; }
  const st = e.target.closest('.still');
  if (st) { const im = $('#imgboxImg'); im.src = st.dataset.full; im.alt = st.getAttribute('aria-label').replace(/^Enlarge: /, ''); openDialog('imgbox', st); return; }
  const cp = e.target.closest('[data-copy]');
  if (cp) {
    e.preventDefault();
    const label = $('em', cp) || $('span', cp), was = label.textContent, text = cp.dataset.copy;
    navigator.clipboard.writeText(text).then(() => { label.textContent = 'Copied'; }).catch(() => {
      const r = document.createRange(); r.selectNodeContents($('small', cp) || label); const s = getSelection(); s.removeAllRanges(); s.addRange(r); label.textContent = 'Selected';
    });
    setTimeout(() => { label.textContent = was; }, 1600);
    return;
  }
  if (e.target.tagName === 'DIALOG') { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); }
});

/* ---------- smooth scroll: Lenis only with a mouse; anchors land below the sticky header ---------- */
if (fine && !reduce) {
  const sc = document.createElement('script');
  sc.src = 'https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js';
  sc.onload = () => {
    lenis = new Lenis({lerp: .085, smoothWheel: true, wheelMultiplier: .95});
    const raf = t => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf);
  };
  document.head.appendChild(sc);
}
/* sections render as they come near (content-visibility), so heights change mid-scroll:
   after each scroll ends, measure again and correct until the target sits under the header */
const goTo = (el, tries = 4) => {
  const off = -($('.top').offsetHeight + 8);
  const miss = () => el.getBoundingClientRect().top + off;
  const again = () => { if (tries > 1 && Math.abs(miss()) > 3) goTo(el, tries - 1); };
  if (lenis) { lenis.scrollTo(el, {offset: off, duration: tries === 4 ? 1.3 : .35, onComplete: again}); return; }
  scrollTo({top: scrollY + miss(), behavior: reduce || tries < 4 ? 'auto' : 'smooth'});
  let t = 0;
  const done = () => { clearTimeout(t); removeEventListener('scroll', wait); requestAnimationFrame(again); };
  const wait = () => { clearTimeout(t); t = setTimeout(done, 140); };
  addEventListener('scroll', wait, {passive: true});
  t = setTimeout(done, 140);
};
$$('a[href^="#"]:not([data-open])').forEach(a => a.addEventListener('click', e => {
  const t = $(a.getAttribute('href'));
  if (!t) return;
  e.preventDefault(); closeMenu(); goTo(t);
  t.setAttribute('tabindex', '-1'); t.focus({preventScroll: true});
}));

/* ---------- mobile menu ---------- */
const burger = $('#burger'), mnav = $('#mnav');
function closeMenu() { burger.setAttribute('aria-expanded', 'false'); mnav.hidden = true; }
burger.addEventListener('click', () => { const open = burger.getAttribute('aria-expanded') !== 'true'; burger.setAttribute('aria-expanded', open); mnav.hidden = !open; });
addEventListener('keydown', e => { if (e.key === 'Escape' && !mnav.hidden) { closeMenu(); burger.focus(); } });

/* ---------- section reveals: only for blocks still below the fold at load ----------
   The trigger is the section, not each block: blocks inside a sideways carousel or a section that is not laid out
   yet (content-visibility) never report their own intersection, and must not stay hidden. */
if (!reduce) {
  const groups = ['.sec-head', '.feat', '.sgrid .sc', '.tl', '.steps', '.term', '.photo', '.about-grid > div', '.cta .wrap > *', 'details', '.stats .stat', '.sgal', '.tgal', '.case'];
  const pending = new Map();
  groups.forEach(sel => $$(sel).forEach((el, i) => {
    const sec = el.closest('section') || el;
    if (sec.getBoundingClientRect().top < innerHeight * .92 && el.getBoundingClientRect().top < innerHeight * .92) return;
    el.style.setProperty('--rd', (Math.min(i, 5) * .07) + 's');
    el.classList.add('rv');
    if (!pending.has(sec)) pending.set(sec, []);
    pending.get(sec).push(el);
  }));
  const show = el => { el.classList.add('rv-in'); el.classList.remove('rv'); };
  const io = new IntersectionObserver(es => es.forEach(e => {
    const list = pending.get(e.target);
    if (!list) return;
    /* blocks further down a tall section wait until they are close, the rest show now */
    const left = list.filter(el => { const r = el.getBoundingClientRect(); if (r.top < innerHeight * .95 || !r.height) { show(el); return false; } return true; });
    if (left.length) pending.set(e.target, left); else { pending.delete(e.target); io.unobserve(e.target); }
  }), {rootMargin: '0px 0px -8% 0px', threshold: [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1]});
  pending.forEach((_, sec) => io.observe(sec));
  /* safety net: anything still hidden once the user scrolled past it shows */
  addEventListener('scroll', () => pending.forEach(list => list.forEach(el => { if (el.classList.contains('rv') && el.getBoundingClientRect().top < innerHeight) show(el); })), {passive: true});
}

/* ---------- FAQ: answers slide open and closed ---------- */
$$('details').forEach(d => {
  const sum = $('summary', d), ans = $('.ans', d);
  sum.addEventListener('click', e => {
    if (reduce) return;
    e.preventDefault();
    if (d.open) {
      const h = ans.offsetHeight;
      ans.animate([{height: h + 'px', opacity: 1}, {height: '0px', opacity: 0}], {duration: 260, easing: 'ease-in'}).onfinish = () => { d.open = false; };
    } else {
      d.open = true;
      const h = ans.offsetHeight;
      ans.animate([{height: '0px', opacity: 0}, {height: h + 'px', opacity: 1}], {duration: 380, easing: 'cubic-bezier(.22,1,.36,1)'});
    }
  });
});

/* ---------- stills: 3D tilt toward the cursor ---------- */
if (fine && !reduce) $$('.still').forEach(c => {
  c.addEventListener('pointermove', e => {
    const r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
    c.style.transform = `rotateY(${(x * 12).toFixed(2)}deg) rotateX(${(-y * 12).toFixed(2)}deg) translateZ(8px)`;
  });
  c.addEventListener('pointerleave', () => { c.style.transform = ''; });
});

/* ---------- hero: goblin parallax + hand drift, mouse only, one frame per move ---------- */
const hpEl = $('#handphone');
const drift = e => {
  const r = hpEl.getBoundingClientRect();
  const nx = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / 600)), ny = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / 600));
  hpEl.style.setProperty('--hx', (nx * 10).toFixed(1) + 'px'); hpEl.style.setProperty('--hy', (ny * 6).toFixed(1) + 'px');
};
if (fine && !reduce) {
  let last = null, pending = false;
  addEventListener('pointermove', e => {
    if (e.pointerType !== 'mouse') return;
    last = e;
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; if (scrollY < innerHeight * 1.2) { parallax(last); drift(last); } });
  }, {passive: true});
}

/* ---------- decorative loops only run while their block is on screen ---------- */
$$('.hero, .marquee, .results, #systems, #stack').forEach(el => seen(el, on => el.classList.toggle('idle', !on), '50px'));

/* ---------- scroll-linked strips: scrolling the page slides the work rows and the formats strip sideways ----------
   They never move on their own; dragging (mouse) or swiping (touch) moves them too. The formats strip loops. */
const mq = $('.marquee'), mtrack = $('#mtrack');
draggable(mq);
const loopW = () => { const half = mtrack.children[mtrack.children.length / 2]; return half ? half.offsetLeft - mtrack.firstElementChild.offsetLeft : 0; };
mq._wrap = () => { const w = loopW(); if (!w) return; if (mq.scrollLeft >= w * 1.5) shift(mq, -w); else if (mq.scrollLeft < w * .5) shift(mq, w); };
mq.scrollLeft = loopW() * .75;
mq.addEventListener('scroll', mq._wrap, {passive: true});
const linked = [[$('#lane-row1'), 1], [$('#lane-row2'), -1], [mq, 1]];
linked.forEach(l => seen(l[0], on => { l.on = on; }, '80px'));
if (!reduce) {
  let lastY = scrollY, queued = 0, raf = 0;
  addEventListener('scroll', () => {
    queued += scrollY - lastY; lastY = scrollY;
    if (raf) return;
    raf = requestAnimationFrame(() => {
      const dy = queued; queued = 0; raf = 0;
      linked.forEach(l => { if (l.on && !l[0].classList.contains('dragging') && !l[0].closest('[hidden]')) { l[0].scrollLeft += dy * .55 * l[1]; l[0]._wrap?.(); } });
    });
  }, {passive: true});
}

/* ---------- cursor bubble: follows the mouse, swaps purple and green under it, leaves a short trail of rings ----------
   Per frame it only writes transforms (no layout reads, no images redrawn), and it sleeps when the trail has settled.
   Over images and videos the colour swap fades out, so only text and backgrounds change. Mouse only, never with reduced motion. */
if (fine && !reduce && (CSS.supports('backdrop-filter', 'hue-rotate(1deg)') || CSS.supports('-webkit-backdrop-filter', 'hue-rotate(1deg)'))) {
  const cur = $('#cur'), lens = $('.lens', cur), head = $('.bub.head', cur), trail = $$('.bub:not(.head)', cur);
  const SIZE = [.62, .46, .33, .22];
  const pts = trail.map(() => ({x: 0, y: 0}));
  let mx = 0, my = 0, hx = 0, hy = 0, raf = 0, inside = false;
  const MEDIA = 'img, video, .still, .card .vid, .case-vid, .phone, .photo';
  const put = (el, x, y, s = 1, o = 1) => { el.style.transform = `translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,0) scale(${s})`; el.style.opacity = o; };
  function frame() {
    raf = 0;
    hx += (mx - hx) * .55; hy += (my - hy) * .55;            /* the head stays right on the pointer */
    put(lens, hx, hy, 1, ''); put(head, hx, hy);
    let px = hx, py = hy, moving = Math.abs(mx - hx) + Math.abs(my - hy) > .3;
    pts.forEach((p, i) => {
      p.x += (px - p.x) * .34; p.y += (py - p.y) * .34;       /* each ring chases the one in front */
      const d = Math.hypot(p.x - hx, p.y - hy);
      put(trail[i], p.x, p.y, SIZE[i] * 84 / 30, Math.min(1, d / 40));  /* rings fade out as they catch up */
      if (Math.abs(p.x - px) + Math.abs(p.y - py) > .3) moving = true;
      px = p.x; py = p.y;
    });
    if (moving) raf = requestAnimationFrame(frame);
  }
  addEventListener('pointermove', e => {
    if (e.pointerType !== 'mouse') return;
    mx = e.clientX; my = e.clientY;
    if (!inside) { inside = true; hx = mx; hy = my; pts.forEach(p => { p.x = mx; p.y = my; }); }
    cur.classList.toggle('on', !$('dialog[open]'));
    cur.classList.toggle('media', !!e.target.closest?.(MEDIA));
    if (!raf) raf = requestAnimationFrame(frame);
  }, {passive: true});
  document.addEventListener('mouseleave', () => { inside = false; cur.classList.remove('on'); });
  $$('dialog').forEach(d => d.addEventListener('close', () => { if (inside) cur.classList.add('on'); }));
  document.addEventListener('click', () => { if ($('dialog[open]')) cur.classList.remove('on'); });
}
