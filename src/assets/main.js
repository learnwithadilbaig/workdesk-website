/* WorkDesk website interactions. Every feature checks that its elements exist, so one file serves all pages. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var TICK = function () { var t = $('.mt'); return t ? t.outerHTML : ''; };

  /* ---------- menus ---------- */
  var dds = $$('.dd');
  function closeAll(except) {
    dds.forEach(function (d) {
      if (d === except) return;
      var b = $('.dd-btn', d), m = $('.mega', d);
      m.hidden = true; b.setAttribute('aria-expanded', 'false');
    });
  }
  dds.forEach(function (d) {
    var b = $('.dd-btn', d), m = $('.mega', d);
    b.addEventListener('click', function (e) {
      e.stopPropagation(); closeAll(d);
      m.hidden = !m.hidden; b.setAttribute('aria-expanded', String(!m.hidden));
    });
  });
  document.addEventListener('click', function (e) { if (!e.target.closest('.dd')) closeAll(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAll(); });
  var mb = $('.menu-btn'), mn = $('#mobile-nav');
  if (mb && mn) mb.addEventListener('click', function () {
    mn.hidden = !mn.hidden; mb.setAttribute('aria-expanded', String(!mn.hidden));
    mb.setAttribute('aria-label', mn.hidden ? 'Open menu' : 'Close menu');
  });
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- reveal + tick draw (only for content that starts below the fold) ---------- */
  var io = 'IntersectionObserver' in window && !reduce ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      var el = en.target;
      el.classList.add('in');
      $$('.mt', el).forEach(function (t, i) { t.style.animationDelay = (i * 0.07) + 's'; t.classList.add('drawn'); });
      if (el.__onShow) el.__onShow();
      io.unobserve(el);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 }) : null;
  function onShow(el, fn) {
    if (!el) return;
    if (!io) { fn(); return; }
    var r = el.getBoundingClientRect();
    if (r.top < window.innerHeight && r.bottom > 0) { fn(); return; }
    el.__onShow = fn; io.observe(el);
  }
  if (io) {
    var fold = window.innerHeight;
    $$('[data-reveal] > *, .reveal').forEach(function (el, i, all) {
      if (el.getBoundingClientRect().top < fold * 0.95) return;
      var idx = Array.prototype.indexOf.call(el.parentNode.children, el);
      el.style.setProperty('--d', Math.min(idx, 5) * 0.07 + 's');
      el.classList.add('pre'); io.observe(el);
    });
  }

  /* ---------- spotlight on cards ---------- */
  $$('.spot').forEach(function (c) {
    c.addEventListener('pointermove', function (e) {
      var r = c.getBoundingClientRect();
      c.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      c.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  /* ---------- marquee: duplicate items for a seamless loop ---------- */
  $$('.marquee-track').forEach(function (t) { t.innerHTML += t.innerHTML; $$('span', t).slice(t.children.length / 2).forEach(function (s) { s.setAttribute('aria-hidden', 'true'); }); });

  /* ---------- hero leave approvals ---------- */
  var toast = $('#toast'), tt = $('#toast-text'), pc = $('#pending-count'), timer;
  function approve(row) {
    var act = $('.act', row); if (!act || !$('button', act)) return;
    act.innerHTML = '<span class="pill ok">' + TICK().replace('class="mt"', 'class="mt drawn"') + ' Approved</span>';
    var left = $$('.req .approve').length;
    if (pc) pc.textContent = left ? left + ' pending' : 'All done';
    if (toast) {
      tt.textContent = (row.getAttribute('data-msg') || 'Approved.');
      toast.classList.remove('hide'); clearTimeout(timer);
      timer = setTimeout(function () { toast.classList.add('hide'); }, 2800);
    }
  }
  $$('[data-req]').forEach(function (r) { var b = $('.approve', r); if (b) b.addEventListener('click', function () { approve(r); }); });
  var firstReq = $('[data-req][data-auto]');
  if (firstReq && !reduce) setTimeout(function () { approve(firstReq); }, 1800);

  /* ---------- attendance chart ---------- */
  var chart = $('#chart');
  if (chart) {
    var data = {
      all: { v: [92, 93, 91, 94, 95, 93, 92, 94, 96, 95, 97, 96], late: 38 },
      sales: { v: [88, 90, 89, 92, 91, 90, 93, 94, 92, 95, 96, 94], late: 21 },
      ops: { v: [95, 94, 96, 96, 97, 95, 94, 96, 97, 98, 98, 97], late: 9 }
    };
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for (var i = 0; i < 12; i++) chart.appendChild(document.createElement('i'));
    var draw = function (team) {
      var d = data[team], max = Math.max.apply(null, d.v), bars = chart.children;
      for (var i = 0; i < 12; i++) {
        bars[i].style.height = ((d.v[i] - 80) / 20 * 100) + '%'; /* axis runs 80% to 100% */
        bars[i].className = d.v[i] === max ? 'hi' : '';
        bars[i].title = months[i] + ': ' + d.v[i] + '%';
      }
      $('#avg').textContent = Math.round(d.v.reduce(function (a, b) { return a + b; }, 0) / 12) + '%';
      $('#best').textContent = months[d.v.indexOf(max)];
      $('#late').textContent = d.late;
    };
    onShow(chart, function () { draw('all'); });
    $$('[data-team]').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('[data-team]').forEach(function (x) { x.classList.toggle('on', x === b); });
        draw(b.getAttribute('data-team'));
      });
    });
  }

  /* ---------- export button toast (reports page) ---------- */
  $$('[data-export]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = $('#export-toast'); if (!t) return;
      t.classList.remove('hide'); setTimeout(function () { t.classList.add('hide'); }, 2400);
    });
  });

  /* ---------- bars that grow when shown ---------- */
  $$('[data-grow]').forEach(function (wrap) {
    var bars = $$('.bar i', wrap);
    bars.forEach(function (b) { b.dataset.w = b.style.width; b.style.width = '0%'; });
    onShow(wrap, function () { setTimeout(function () { bars.forEach(function (b) { b.style.width = b.dataset.w; }); }, 120); });
  });

  /* ---------- module hub: pulses travel from each module into the desk ---------- */
  var hub = $('.hub');
  if (hub && !reduce) {
    var nodes = $$('.node', hub), n = 0;
    setInterval(function () { nodes.forEach(function (x, i) { x.classList.toggle('lit', i === n % nodes.length); }); n++; }, 1400);
  }

  /* ---------- steps progress line follows scroll ---------- */
  var pl = $('.progress-line');
  if (pl && !reduce) {
    var steps = pl.parentNode;
    var upd = function () {
      var r = steps.getBoundingClientRect(), vh = window.innerHeight;
      var p = Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (r.height + vh * 0.35)));
      pl.style.setProperty('--p', (p * 100).toFixed(1) + '%');
    };
    window.addEventListener('scroll', upd, { passive: true }); upd();
  }

  /* ---------- attendance week grid ---------- */
  var att = $('#att-grid');
  if (att) {
    var cells = $$('.c[data-s]', att);
    cells.forEach(function (c) { c.dataset.final = c.getAttribute('data-s'); c.className = 'c'; c.textContent = ''; });
    var labels = { p: '', l: 'Late', v: 'Leave', o: 'Off' };
    var fill = function () {
      cells.forEach(function (c, i) {
        setTimeout(function () {
          c.className = 'c ' + c.dataset.final + ' pop'; c.textContent = labels[c.dataset.final];
          setTimeout(function () { c.classList.remove('pop'); }, 300);
        }, reduce ? 0 : i * 45);
      });
    };
    onShow(att, fill);
  }

  /* ---------- payslip count-up ---------- */
  var net = $('#net-pay');
  if (net) {
    var target = parseInt(net.getAttribute('data-value'), 10);
    var fmt = function (v) { return 'PKR ' + v.toLocaleString('en-PK'); };
    net.textContent = fmt(reduce ? target : 0);
    onShow(net, function () {
      if (reduce) return;
      var t0 = null;
      var step = function (ts) {
        if (!t0) t0 = ts;
        var k = Math.min(1, (ts - t0) / 1300), e = 1 - Math.pow(1 - k, 3);
        net.textContent = fmt(Math.round(target * e / 10) * 10);
        if (k < 1) requestAnimationFrame(step); else net.textContent = fmt(target);
      };
      requestAnimationFrame(step);
    });
  }

  /* ---------- kanban: a card moves to Done every few seconds ---------- */
  var kb = $('#kanban');
  if (kb && !reduce) {
    var cols = $$('.kb-col', kb);
    var count = function () { cols.forEach(function (c) { var s = $('b span', c); if (s) s.textContent = $$('.kb-card', c).length; }); };
    onShow(kb, function () {
      var due = ['Due Fri', 'Due Mon', 'Due today', 'Due Wed'], d = 0;
      var move = function (card, col, label, atTop) {
        card.remove(); card.classList.remove('enter'); void card.offsetWidth;
        var tag = $('.meta span', card); if (tag) tag.innerHTML = label;
        card.classList.add('enter');
        if (atTop) col.insertBefore(card, $('.kb-card', col)); else col.appendChild(card);
      };
      setInterval(function () {
        var todo = cols[0], doing = cols[1], done = cols[2];
        var c = $('.kb-card', doing); if (c) move(c, done, TICK() + ' Done', true);
        var n = $('.kb-card', todo); if (n) move(n, doing, due[d++ % due.length], false);
        var finished = $$('.kb-card', done);
        if (finished.length > 2) move(finished[finished.length - 1], todo, 'To do', false);
        count();
      }, 2600);
    });
  }

  /* ---------- profile tabs and role tabs ---------- */
  $$('[role="tablist"]').forEach(function (list) {
    var tabs = $$('[role="tab"]', list);
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        tabs.forEach(function (x) {
          var on = x === t; x.setAttribute('aria-selected', String(on)); x.tabIndex = on ? 0 : -1;
          var p = document.getElementById(x.getAttribute('aria-controls')); if (p) p.hidden = !on;
        });
      });
      t.addEventListener('keydown', function (e) {
        var i = tabs.indexOf(t);
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          var j = (i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length; tabs[j].focus(); tabs[j].click();
        }
      });
    });
  });

  /* ---------- score rings ---------- */
  $$('.ring[data-v]').forEach(function (r) {
    var v = parseFloat(r.getAttribute('data-v')), fg = $('.fg', r), lab = $('b', r);
    lab.textContent = v + '%';
    onShow(r, function () { fg.style.strokeDashoffset = String(289 - 289 * v / 100); });
  });

  /* ---------- pricing builder ---------- */
  var builder = $('#builder');
  if (builder) {
    var range = $('#team-size'), out = $('#team-out'), sum = $('#sum-text');
    var upd2 = function () {
      var picked = $$('input[type=checkbox]:checked', builder).map(function (c) { return c.getAttribute('data-name'); });
      var n = parseInt(range.value, 10);
      out.textContent = n >= 1000 ? '1,000+' : n;
      if (!picked.length) { sum.textContent = 'Pick at least one module to get a quote.'; return; }
      var list = picked.length === 1 ? picked[0] : picked.slice(0, -1).join(', ') + ' and ' + picked[picked.length - 1];
      sum.textContent = list + ' for ' + (n >= 1000 ? 'more than 1,000' : n) + ' employees. We will send you a written quote for exactly this.';
    };
    builder.addEventListener('input', upd2); upd2();
  }

  /* ---------- forms: post to the configured endpoint, or explain that none is set ---------- */
  $$('form[data-form]').forEach(function (f) {
    var note = $('.form-note', f);
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var bad = $$('[required]', f).filter(function (el) { return !el.value.trim(); });
      var email = $('input[type=email]', f);
      $$('[aria-invalid]', f).forEach(function (el) { el.removeAttribute('aria-invalid'); });
      if (bad.length) {
        bad.forEach(function (el) { el.setAttribute('aria-invalid', 'true'); });
        var first = ((f.querySelector('label[for="' + bad[0].id + '"]') || {}).textContent || '').replace(/[?:]$/, '');
        note.className = 'form-note err';
        note.textContent = bad.length === 1 ? 'Please fill in "' + first + '".'
          : 'Please fill in the ' + bad.length + ' highlighted fields, starting with "' + first + '".';
        bad[0].focus(); return;
      }
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value.trim())) { note.className = 'form-note err'; note.textContent = 'That email address looks incomplete. Try name@company.com.'; email.setAttribute('aria-invalid', 'true'); email.focus(); return; }
      var endpoint = f.getAttribute('data-endpoint');
      if (!endpoint) { note.className = 'form-note'; note.textContent = f.getAttribute('data-unset') || 'This form is not connected yet. Add a form endpoint in src/config.json before launch.'; return; }
      var btn = $('button[type=submit]', f); btn.disabled = true;
      fetch(endpoint, { method: 'POST', body: new FormData(f), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          note.className = 'form-note ok'; note.textContent = f.getAttribute('data-ok') || 'Thanks. We will be in touch soon.'; f.reset();
        })
        .catch(function () { note.className = 'form-note err'; note.textContent = 'Something went wrong sending the form. Please email us instead.'; })
        .then(function () { btn.disabled = false; });
    });
  });
})();
