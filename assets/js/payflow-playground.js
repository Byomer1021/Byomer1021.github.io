/* PayFlow playground — runs the real interpreter in the browser.

   Pyodide is ~10 MB, so nothing is fetched until the visitor actually
   presses RUN. Until then this file costs one script tag.

   The Python that runs here is the repository's own source, copied
   verbatim into /assets/payflow/ and pinned to one revision. A
   JavaScript re-implementation would eventually disagree with the repo
   it claims to demonstrate; this cannot.

   Turkish strings use double quotes throughout: a bare apostrophe in a
   single-quoted JS string ends it early, and the suffixes attach with
   one ("Play'de", "18'i"). */
(function () {
  'use strict';

  var PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/';
  var MODULES = ['lexer', 'parser', 'ast_nodes', 'type_checker', 'interpreter', '_runner'];

  var PRESETS = {
    basic: [
      '// The smallest useful PayFlow program.',
      '',
      'plan Pro {',
      '  price:  9.99 USD;',
      '  period: 1 month;',
      '  trial:  7 days;',
      '  tier:   2;',
      '}',
      '',
      'paywall Onboarding {',
      '  default {',
      '    show Pro;',
      '  }',
      '}'
    ].join('\n'),

    regional: [
      '// Change the region above and run again — the routing follows it.',
      '',
      'plan Pro {',
      '  price:  9.99 USD;',
      '  period: 1 month;',
      '  trial:  7 days;',
      '  tier:   2;',
      '}',
      '',
      'paywall Onboarding {',
      '  when region == "EU" {',
      '    show Pro at 8.99 EUR with trial 14 days;',
      '  }',
      '  when region == "TR" {',
      '    show Pro at 199.00 TRY with trial 7 days;',
      '  }',
      '  default {',
      '    show Pro;',
      '  }',
      '}'
    ].join('\n'),

    rounding: [
      '// 9.99 USD split 3% split 8%',
      '//',
      '//   per-step:      9.99 * 0.97 = 9.6903 -> 9.69',
      '//                  9.69 * 0.92 = 8.9148 -> 8.91',
      '//   once-at-end:   9.99 * 0.97 * 0.92   -> 8.92',
      '//',
      '// The answer below settles which rule this language implements.',
      '',
      'plan Pro {',
      '  price: 9.99 USD;',
      '  trial: 7 days;',
      '}',
      '',
      'fn netRevenue(p: money, platformCut: percent, vat: percent) -> money {',
      '  return p split platformCut split vat;',
      '}',
      '',
      'paywall Settlement {',
      '  default {',
      '    show Pro at netRevenue(9.99 USD, 3%, 8%);',
      '  }',
      '}'
    ].join('\n'),

    typeerr: [
      '// Name equivalence: two records with identical fields are still',
      '// different types, because they mean opposite things.',
      '',
      'record Plan {',
      '  name:  string;',
      '  price: money;',
      '}',
      '',
      'record RefundRule {',
      '  name:  string;',
      '  price: money;',
      '}',
      '',
      'fn applyTaxes(p: Plan, rate: percent) -> money {',
      '  return p.price split rate;',
      '}',
      '',
      'fn caller(r: RefundRule, rate: percent) -> money {',
      '  return applyTaxes(r, rate);',
      '}'
    ].join('\n'),

    currency: [
      '// Both currencies are known while type checking, so the program',
      '// is rejected before anything runs.',
      '',
      'plan Pro {',
      '  price: 9.99 USD;',
      '  trial: 0 days;',
      '}',
      '',
      'fn total() -> money {',
      '  return 9.99 USD + 2.50 EUR;',
      '}',
      '',
      'paywall W {',
      '  default {',
      '    show Pro at total();',
      '  }',
      '}'
    ].join('\n'),

    leak: [
      '// The same mistake, hidden behind a parameter.',
      '//',
      '// `money` is one type: the annotation carries no currency, so the',
      '// checker cannot see that these two arguments disagree. The error',
      '// arrives at run time instead, and says "internal:" because the',
      '// interpreter expects the checker to have caught it.',
      '//',
      '// Currency-parameterised types would close this gap.',
      '',
      'plan Pro {',
      '  price: 9.99 USD;',
      '  trial: 0 days;',
      '}',
      '',
      'fn add(a: money, b: money) -> money {',
      '  return a + b;',
      '}',
      '',
      'paywall W {',
      '  default {',
      '    show Pro at add(9.99 USD, 2.50 EUR);',
      '  }',
      '}'
    ].join('\n')
  };

  var els = {};
  var pyodide = null;
  var loading = null;

  function $(id) { return document.getElementById(id); }

  function bi(en, tr) {
    return '<span data-lang="en">' + en + '</span><span data-lang="tr">' + tr + '</span>';
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function status(html, tone) {
    if (!els.status) return;
    els.status.className =
      'font-label-code-sm text-label-code-sm tracking-wider uppercase ' +
      (tone === 'error' ? 'text-error'
        : tone === 'ok' ? 'text-tertiary-fixed-dim'
        : 'text-outline');
    els.status.innerHTML = html;
  }

  function setBusy(on) {
    if (!els.run) return;
    els.run.disabled = on;
    els.run.classList.toggle('opacity-50', on);
    els.run.classList.toggle('cursor-wait', on);
  }

  // ---- Pyodide, loaded once, on demand ------------------------------------

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error('could not load ' + src)); };
      document.head.appendChild(s);
    });
  }

  function boot() {
    if (pyodide) return Promise.resolve(pyodide);
    if (loading) return loading;

    status(bi('LOADING PYTHON RUNTIME — ABOUT 10 MB, ONCE',
              "PYTHON ÇALIŞMA ZAMANI YÜKLENİYOR — YAKLAŞIK 10 MB, BİR KEZ"));

    loading = loadScript(PYODIDE + 'pyodide.js')
      .then(function () {
        return window.loadPyodide({ indexURL: PYODIDE });
      })
      .then(function (py) {
        status(bi('LOADING THE PAYFLOW INTERPRETER',
                  "PAYFLOW YORUMLAYICISI YÜKLENİYOR"));
        return Promise.all(MODULES.map(function (m) {
          return fetch('/assets/payflow/' + m + '.py').then(function (r) {
            if (!r.ok) throw new Error(m + '.py: HTTP ' + r.status);
            return r.text();
          }).then(function (src) { return [m, src]; });
        })).then(function (pairs) {
          pairs.forEach(function (p) { py.FS.writeFile(p[0] + '.py', p[1]); });
          py.runPython('import sys; sys.path.insert(0, "")');
          py.runPython('import _runner');
          pyodide = py;
          return py;
        });
      });

    loading.catch(function () { loading = null; });
    return loading;
  }

  // ---- running ------------------------------------------------------------

  function show(panel) {
    document.querySelectorAll('[data-pf-panel]').forEach(function (p) {
      p.hidden = p.getAttribute('data-pf-panel') !== panel;
    });
    document.querySelectorAll('[data-pf-tab]').forEach(function (t) {
      var on = t.getAttribute('data-pf-tab') === panel;
      t.classList.toggle('text-primary', on);
      t.classList.toggle('bg-surface-container-high', on);
      t.classList.toggle('text-outline', !on);
      t.setAttribute('aria-selected', String(on));
    });
  }

  function render(res) {
    var out = els.output;
    var region = els.region ? els.region.value : 'US';

    if (res.error) {
      out.innerHTML =
        '<span class="text-outline">$ python payflow.py program.pf --region ' + esc(region) + '</span>\n' +
        '<span class="text-error">' + esc(res.error) + '</span>\n' +
        '<span class="text-outline">[exit 1]</span>';
      var label = res.phase === 'type' ? bi('TYPE ERROR — CAUGHT BEFORE EXECUTION', "TİP HATASI — ÇALIŞMADAN ÖNCE YAKALANDI")
        : res.phase === 'runtime' ? bi('RUNTIME ERROR', "ÇALIŞMA ZAMANI HATASI")
        : bi('REJECTED BY THE FRONT END', "ÖN UÇ TARAFINDAN REDDEDİLDİ");
      status(label, 'error');
    } else {
      var body = res.output ? esc(res.output.replace(/\n+$/, ''))
        : '(no output — the program declares things but shows nothing)';
      out.innerHTML =
        '<span class="text-outline">$ python payflow.py program.pf --region ' + esc(region) + '</span>\n' +
        '<span class="text-tertiary-fixed-dim">' + body + '</span>\n' +
        '<span class="text-outline">[exit 0]</span>';
      status(bi('ACCEPTED', "KABUL EDİLDİ"), 'ok');
    }

    els.tokens.textContent = res.tokens || '';
    els.ast.textContent = res.ast || '(not parsed)';
  }

  function run() {
    setBusy(true);
    boot().then(function (py) {
      status(bi('RUNNING', "ÇALIŞIYOR"));
      // Hand the source over as globals rather than splicing it into a
      // Python literal — the editor contains quotes and backslashes.
      py.globals.set('__pf_src', els.editor.value);
      py.globals.set('__pf_region', els.region ? els.region.value : 'US');
      var raw = py.runPython('_runner.run_source(__pf_src, __pf_region)');
      var res = JSON.parse(raw);
      render(res);
      show('output');
      setBusy(false);
    }).catch(function (err) {
      status(bi('COULD NOT START THE RUNTIME — ' + esc(err.message),
                "ÇALIŞMA ZAMANI BAŞLATILAMADI — " + esc(err.message)), 'error');
      setBusy(false);
    });
  }

  // ---- wiring -------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', function () {
    els.editor = $('pf-editor');
    if (!els.editor) return;          // not this page
    els.run = $('pf-run');
    els.region = $('pf-region');
    els.preset = $('pf-preset');
    els.status = $('pf-status');
    els.output = $('pf-output');
    els.tokens = $('pf-tokens');
    els.ast = $('pf-ast');

    els.editor.value = PRESETS.regional;

    if (els.preset) {
      els.preset.addEventListener('change', function () {
        var src = PRESETS[els.preset.value];
        if (src) {
          els.editor.value = src;
          status(bi('PRESS RUN', "ÇALIŞTIR'A BAS"));
        }
      });
    }

    if (els.run) els.run.addEventListener('click', run);

    document.addEventListener('click', function (e) {
      var tab = e.target.closest('[data-pf-tab]');
      if (tab) { e.preventDefault(); show(tab.getAttribute('data-pf-tab')); }
    });

    // Ctrl/Cmd+Enter runs, the way every other editor does.
    els.editor.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); }
    });

    show('output');
    status(bi('PRESS RUN — THE RUNTIME LOADS ON FIRST USE',
              "ÇALIŞTIR'A BAS — ÇALIŞMA ZAMANI İLK KULLANIMDA YÜKLENİR"));
  });
})();
