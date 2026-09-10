/* Shared behaviour: language toggle, nav state, clock, scroll reveals. */
(function () {
  'use strict';

  // ---- 1. Language ---------------------------------------------------------
  // Both languages live in the markup as [data-lang] elements; CSS hides the
  // inactive one, so the page is readable before this script runs.
  var STORE_KEY = 'oca-lang';

  function applyLang(lang) {
    document.documentElement.setAttribute('lang', lang);
    try { localStorage.setItem(STORE_KEY, lang); } catch (e) { /* private mode */ }
    document.querySelectorAll('[data-lang-btn]').forEach(function (btn) {
      var on = btn.getAttribute('data-lang-btn') === lang;
      btn.classList.toggle('bg-surface-container-high', on);
      btn.classList.toggle('text-primary', on);
      btn.classList.toggle('text-outline', !on);
      btn.setAttribute('aria-pressed', String(on));
    });
    // Swap alt text and any attribute pairs the markup declares.
    document.querySelectorAll('[data-alt-en]').forEach(function (el) {
      el.setAttribute('alt', el.getAttribute('data-alt-' + lang) || el.getAttribute('data-alt-en'));
    });
  }

  var stored;
  try { stored = localStorage.getItem(STORE_KEY); } catch (e) { stored = null; }
  applyLang(stored === 'tr' || stored === 'en' ? stored : 'en');

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-lang-btn]');
    if (btn) { e.preventDefault(); applyLang(btn.getAttribute('data-lang-btn')); }
  });

  // ---- 2. Navigation active state -----------------------------------------
  // Match on the FIRST path segment, so a detail page like
  // /projects/otonomarac/ still lights up the Projects tab.
  var here = location.pathname.replace(/^\/+/, '').split('/')[0]
    .replace(/\.html$/, '')
    .toLowerCase() || 'index';
  document.querySelectorAll('[data-nav]').forEach(function (a) {
    if (a.getAttribute('data-nav') !== here) return;
    a.setAttribute('aria-current', 'page');
    a.classList.remove('text-on-surface-variant');
    a.classList.add('bg-surface-container-high', 'text-primary');
  });

  // ---- 3. Footer clock -----------------------------------------------------
  var clock = document.getElementById('local-clock');
  if (clock) {
    var tick = function () {
      // His local time, so a visitor can tell whether it is a sane hour to write.
      clock.textContent = new Date().toLocaleTimeString('tr-TR', {
        timeZone: 'Europe/Istanbul', hour12: false
      }) + ' İSTANBUL';
    };
    tick();
    setInterval(tick, 1000);
  }

  // ---- 4. Scroll reveals ---------------------------------------------------
  var targets = document.querySelectorAll('.reveal');
  if (targets.length && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add('is-visible'); });
  }

  // ---- 6. Motion preference --------------------------------------------
  // The OS setting is the default; an explicit choice by the visitor wins and
  // persists. Everything that moves reads data-motion rather than the media
  // query directly, so one switch covers the WebGL field and the CSS both.
  var MOTION_KEY = 'oca-motion';

  function resolveMotion() {
    var stored = null;
    try { stored = localStorage.getItem(MOTION_KEY); } catch (e) { /* private mode */ }
    if (stored === 'on' || stored === 'off') return stored;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'off' : 'on';
  }

  function applyMotion(state) {
    document.documentElement.setAttribute('data-motion', state);
    document.querySelectorAll('[data-motion-toggle]').forEach(function (btn) {
      var on = state === 'on';
      btn.setAttribute('aria-pressed', String(on));
      btn.classList.toggle('text-primary', on);
      btn.classList.toggle('text-outline', !on);
      var icon = btn.querySelector('.material-symbols-outlined');
      if (icon) icon.textContent = on ? 'motion_photos_on' : 'motion_photos_paused';
    });
    window.dispatchEvent(new CustomEvent('oca:motion', { detail: state }));
  }

  applyMotion(resolveMotion());

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-motion-toggle]');
    if (!btn) return;
    var next = document.documentElement.getAttribute('data-motion') === 'on' ? 'off' : 'on';
    try { localStorage.setItem(MOTION_KEY, next); } catch (err) { /* private mode */ }
    applyMotion(next);
  });

  // ---- 5. Mobile navigation ------------------------------------------------
  var burger = document.getElementById('nav-toggle');
  var drawer = document.getElementById('nav-drawer');
  if (burger && drawer) {
    burger.addEventListener('click', function () {
      var open = drawer.hasAttribute('hidden');
      if (open) { drawer.removeAttribute('hidden'); } else { drawer.setAttribute('hidden', ''); }
      burger.setAttribute('aria-expanded', String(open));
    });
  }
})();
