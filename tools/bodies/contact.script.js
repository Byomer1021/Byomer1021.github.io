/* A small shell. Every answer below is a fact from the CV or a repository —
   nothing here is decorative filler. */
(function () {
  'use strict';

  var out = document.getElementById('cli-output');
  var form = document.getElementById('cli-form');
  var input = document.getElementById('cli-input');
  var history = [];
  var historyPos = -1;

  function lang() { return document.documentElement.getAttribute('lang') === 'tr' ? 'tr' : 'en'; }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  var COMMANDS = {
    help: {
      en: [
        'Available commands:',
        '  whoami      who I am, in one paragraph',
        '  contact     email and profile links',
        '  projects    the five open-source projects',
        '  private     the products behind closed repositories',
        '  stack       languages, frameworks, tools',
        '  education   university and school',
        '  experience  work experience',
        '  demo        open the live perception demo',
        '  cv          open the CV page',
        '  clear       clear this screen'
      ],
      tr: [
        'Kullanılabilir komutlar:',
        '  whoami      kim olduğum, tek paragrafta',
        '  contact     e-posta ve profil linkleri',
        '  projects    beş açık kaynak proje',
        '  private     kapalı repolardaki ürünler',
        '  stack       diller, frameworkler, araçlar',
        '  education   üniversite ve lise',
        '  experience  iş deneyimi',
        '  demo        canlı algı demosunu aç',
        '  cv          CV sayfasını aç',
        '  clear       ekranı temizle'
      ]
    },
    whoami: {
      en: [
        'Ömer Can Atlı — final-year Computer Engineering student at Gebze',
        'Technical University (expected 2027). I build backend systems, applied',
        'machine-learning pipelines, and the web and mobile apps on top of them.',
        'Four public repositories, each published with the measurements that say',
        'where it breaks. Two products with real users behind private repositories.'
      ],
      tr: [
        'Ömer Can Atlı — Gebze Teknik Üniversitesi Bilgisayar Mühendisliği son',
        'sınıf öğrencisi (beklenen mezuniyet 2027). Backend sistemler, uygulamalı',
        "makine öğrenmesi pipeline'ları ve bunların üzerindeki web ve mobil",
        'uygulamaları geliştiriyorum. Dört açık repo, her biri nerede kırıldığını',
        'söyleyen ölçümlerle yayımlanmış. Kapalı repolarda gerçek kullanıcılı iki ürün.'
      ]
    },
    contact: {
      en: [
        '{',
        '  "email"        : "atli.omercan_2001@hotmail.com",',
        '  "github"       : "github.com/Byomer1021",',
        '  "linkedin"     : "linkedin.com/in/ömer-can-atli",',
        '  "huggingface"  : "huggingface.co/byomer1021",',
        '  "location"     : "Maltepe, İstanbul, TR (UTC+03)",',
        '  "languages"    : ["Turkish — native", "English — C1"],',
        '  "looking_for"  : "internships and new-graduate roles"',
        '}'
      ],
      tr: [
        '{',
        '  "eposta"       : "atli.omercan_2001@hotmail.com",',
        '  "github"       : "github.com/Byomer1021",',
        '  "linkedin"     : "linkedin.com/in/ömer-can-atli",',
        '  "huggingface"  : "huggingface.co/byomer1021",',
        '  "konum"        : "Maltepe, İstanbul, TR (UTC+03)",',
        '  "diller"       : ["Türkçe — ana dil", "İngilizce — C1"],',
        '  "aranan"       : "staj ve yeni mezun pozisyonları"',
        '}'
      ]
    },
    projects: {
      en: [
        'otonomarac                 monocular driving perception + bird\'s-eye map',
        '                           8 weeks · live demo on Hugging Face Spaces',
        'trafikisaret               Turkish traffic-sign dataset + two-stage model',
        '                           717 boxes labelled by hand over 787 frames',
        'smart-city-traffic-analysis  38,310,226 NYC taxi trips as a graph',
        '                           removing JFK splits the network into 16 parts',
        'plakatanima                Turkish plate recognition, measured end to end',
        '                           18 of 34 plates fully automatic; TensorRT FP16 24.7x',
        'payflow                    a programming language for subscription billing',
        '                           lexer, parser, type checker, interpreter; runs in the browser',
        '',
        'Full write-ups: /projects/'
      ],
      tr: [
        'otonomarac                 tek kameradan sürüş algısı + kuşbakışı harita',
        '                           8 hafta · Hugging Face Spaces\'te canlı demo',
        'trafikisaret               Türk trafik işareti veri seti + iki aşamalı model',
        '                           787 karede elle etiketlenmiş 717 kutu',
        'smart-city-traffic-analysis  38.310.226 NYC taksi yolculuğu, graph olarak',
        '                           JFK çıkınca ağ 16 parçaya bölünüyor',
        'plakatanima                Türk plakası tanıma, uçtan uca ölçüldü',
        '                           18 / 34 plaka tam otomatik; TensorRT FP16 24.7x',
        'payflow                    abonelik faturalandırması için bir programlama dili',
        '                           lexer, ayrıştırıcı, tip denetleyicisi, yorumlayıcı; tarayıcıda çalışır',
        '',
        'Ayrıntılar: /projects/'
      ]
    },
    private: {
      en: [
        'respos          multi-tenant SaaS POS for restaurants — resposapp.com',
        '                Node.js/Express, React, Expo · JWT, per-tenant isolation',
        'Shorties        AI short-video exam prep — shorties.tr',
        '                three separate apps on one architecture:',
        '                  YKS  — live on the App Store and Google Play',
        '                  KPSS — in development',
        '                  ALES — in development',
        '                .NET Clean Architecture, React Native, Python video engine',
        'Fitness Tracker AI meal and workout recommendations (team project)',
        '                Flutter, .NET, MSSQL',
        '',
        'Code is closed because these have real users. Ask and I will walk you',
        'through the architecture.'
      ],
      tr: [
        'respos          restoranlar için multi-tenant SaaS POS — resposapp.com',
        '                Node.js/Express, React, Expo · JWT, tenant izolasyonu',
        'Shorties        yapay zekâ ile kısa video sınav hazırlık — shorties.tr',
        '                tek mimari üzerinde üç ayrı uygulama:',
        "                  YKS  — App Store ve Google Play'de yayında",
        '                  KPSS — geliştiriliyor',
        '                  ALES — geliştiriliyor',
        '                .NET Clean Architecture, React Native, Python video motoru',
        'Fitness Tracker yapay zekâ ile beslenme ve antrenman önerileri (ekip projesi)',
        '                Flutter, .NET, MSSQL',
        '',
        'Gerçek kullanıcıları olduğu için kod kapalı. İstersen mimarisini anlatırım.'
      ]
    },
    stack: {
      en: [
        'languages    Java · C++ · C · Python · C# · JavaScript · HTML/CSS · SQL',
        'frameworks   .NET · Spring Boot · Django · Flutter · React Native',
        '             Scikit-learn · TensorFlow (basic) · NumPy · Pandas',
        'tools        Git · Docker · Jira · Maven · Firebase · MySQL · SQL Server',
        'concepts     OOP · Data Structures · Machine Learning · Deep Learning'
      ],
      tr: [
        'diller       Java · C++ · C · Python · C# · JavaScript · HTML/CSS · SQL',
        'framework    .NET · Spring Boot · Django · Flutter · React Native',
        '             Scikit-learn · TensorFlow (temel) · NumPy · Pandas',
        'araçlar      Git · Docker · Jira · Maven · Firebase · MySQL · SQL Server',
        'kavramlar    OOP · Veri Yapıları · Makine Öğrenmesi · Derin Öğrenme'
      ]
    },
    education: {
      en: [
        'Gebze Technical University — B.Sc. Computer Engineering',
        '  expected 2027 · Kocaeli, Turkey',
        'Şehit Mustafa Serin Science High School',
        '  graduated 2019 · Balıkesir, Turkey'
      ],
      tr: [
        'Gebze Teknik Üniversitesi — Bilgisayar Mühendisliği Lisans',
        '  beklenen 2027 · Kocaeli, Türkiye',
        'Şehit Mustafa Serin Fen Lisesi',
        '  mezuniyet 2019 · Balıkesir, Türkiye'
      ]
    },
    experience: {
      en: [
        'Türk Telekom — Network Management Directorate, İstanbul',
        'Intern · July 2025 — August 2025',
        '',
        'A rotational internship across the Transmission, MPLS-IP, DSL, Mobile',
        'Core, Central Office and TTVPN units. Hands-on with xDSL/FTTH access',
        'technologies, MPLS, BNG, traffic monitoring and fault analysis.'
      ],
      tr: [
        'Türk Telekom — Ağ Yönetimi Direktörlüğü, İstanbul',
        'Stajyer · Temmuz 2025 — Ağustos 2025',
        '',
        'İletim, MPLS-IP, DSL, Mobil Çekirdek, Santral ve TTVPN birimlerinde',
        'rotasyonlu staj. xDSL/FTTH erişim teknolojileri, MPLS, BNG, trafik',
        'izleme ve arıza analizi üzerinde birebir çalışma.'
      ]
    }
  };

  var LINKS = {
    demo: 'https://huggingface.co/spaces/byomer1021/otonomarac',
    cv: '/cv/'
  };

  function println(text, cls) {
    var div = document.createElement('div');
    div.className = cls || 'text-on-surface-variant whitespace-pre-wrap';
    div.textContent = text;
    out.appendChild(div);
  }

  function printPrompt(cmd) {
    var div = document.createElement('div');
    div.className = 'mt-space-xs';
    div.innerHTML = '<span class="text-primary-fixed-dim">guest@oca.dev:~$</span> <span class="text-primary">' + esc(cmd) + '</span>';
    out.appendChild(div);
  }

  function printBlock(lines) {
    var pre = document.createElement('pre');
    pre.className = 'p-space-sm bg-surface-container-low/60 rounded text-primary-fixed text-[12px] leading-relaxed overflow-x-auto whitespace-pre-wrap';
    pre.style.border = '1px solid rgba(255,255,255,0.05)';
    pre.textContent = lines.join('\n');
    out.appendChild(pre);
  }

  function run(raw) {
    var cmd = raw.trim().toLowerCase();
    if (!cmd) return;
    printPrompt(raw.trim());

    if (cmd === 'clear') { out.innerHTML = ''; boot(); return; }

    if (cmd === 'ls') { cmd = 'projects'; }

    if (cmd === 'demo' || cmd === 'cv') {
      println(lang() === 'tr' ? 'Açılıyor: ' + LINKS[cmd] : 'Opening ' + LINKS[cmd], 'text-tertiary-fixed-dim');
      window.open(LINKS[cmd], cmd === 'demo' ? '_blank' : '_self');
      out.scrollTop = out.scrollHeight;
      return;
    }

    if (COMMANDS[cmd]) {
      printBlock(COMMANDS[cmd][lang()]);
    } else {
      println(
        lang() === 'tr'
          ? 'komut bulunamadı: ' + cmd + " — kullanılabilir komutlar için 'help' yaz"
          : 'command not found: ' + cmd + " — type 'help' for the list",
        'text-error'
      );
    }
    out.scrollTop = out.scrollHeight;
  }

  function boot() {
    var tr = lang() === 'tr';
    var wrap = document.createElement('div');
    wrap.className = 'text-on-surface-variant font-label-code-sm text-label-code-sm flex flex-col gap-space-3xs';
    wrap.innerHTML =
      '<div>• ' + (tr ? 'PROFİL YÜKLENİYOR [ÖMER CAN ATLI]...' : 'LOADING PROFILE [ÖMER CAN ATLI]...') + ' <span class="text-tertiary-fixed-dim">OK</span></div>' +
      '<div>• ' + (tr ? 'AÇIK DEPOLAR: 4' : 'PUBLIC REPOSITORIES: 4') + ' <span class="text-tertiary-fixed-dim">' + (tr ? 'İNDEKSLENDİ' : 'INDEXED') + '</span></div>' +
      '<div>• ' + (tr ? 'DURUM: ' : 'STATUS: ') + '<span class="text-primary-container">' + (tr ? 'STAJ VE YENİ MEZUN POZİSYONLARINA AÇIK' : 'OPEN TO INTERNSHIPS AND NEW-GRAD ROLES') + '</span></div>' +
      '<div>• ' + (tr ? 'YAZ ' : 'TYPE ') + '<span class="text-primary-fixed">help</span>' + (tr ? ' YA DA YUKARIDAKİ KISAYOLLARI KULLAN.' : ' OR USE THE SHORTCUTS ABOVE.') + '</div>';
    out.appendChild(wrap);
  }

  boot();
  run('whoami');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var value = input.value;
    if (value.trim()) { history.unshift(value.trim()); historyPos = -1; }
    run(value);
    input.value = '';
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyPos < history.length - 1) { historyPos++; input.value = history[historyPos]; }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyPos > 0) { historyPos--; input.value = history[historyPos]; }
      else { historyPos = -1; input.value = ''; }
    }
  });

  document.querySelectorAll('.cmd-shortcut').forEach(function (btn) {
    btn.addEventListener('click', function () { run(btn.getAttribute('data-cmd')); input.focus(); });
  });

  /* Local time in İstanbul, so a visitor can tell whether it is a sane hour. */
  var termClock = document.getElementById('term-clock');
  if (termClock) {
    var tick = function () {
      termClock.textContent = new Date().toLocaleTimeString('tr-TR', { timeZone: 'Europe/Istanbul', hour12: false }) + ' UTC+03';
    };
    tick();
    setInterval(tick, 1000);
  }

  /* Copy the email address. */
  var copyBtn = document.getElementById('copy-email');
  var copyIcon = document.getElementById('copy-icon');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var address = 'atli.omercan_2001@hotmail.com';
      var done = function () {
        copyIcon.textContent = 'check';
        copyBtn.classList.add('text-tertiary-fixed-dim');
        setTimeout(function () {
          copyIcon.textContent = 'content_copy';
          copyBtn.classList.remove('text-tertiary-fixed-dim');
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(address).then(done, function () {});
      }
    });
  }
})();
