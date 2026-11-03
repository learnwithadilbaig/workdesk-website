/* WorkDesk analytics. Pushes clean, named events to the Google Tag Manager dataLayer.
   Rules: one event per real action, params always present (empty string when not relevant),
   and never any personal data: no names, emails, phone numbers or free-text form answers. */
(function () {
  'use strict';
  var dl = window.dataLayer = window.dataLayer || [];
  var APP = window.WD_APP || {};

  function push(event, params) {
    var o = { event: event };
    for (var k in params) if (Object.prototype.hasOwnProperty.call(params, k)) o[k] = params[k] == null ? '' : params[k];
    dl.push(o);
  }
  window.wdTrack = push;

  var clean = function (s, n) { return String(s || '').replace(/\s+/g, ' ').trim().slice(0, n || 100); };
  var slug = function (s) { return clean(s, 60).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40); };
  var label = function (el) { return clean(el.getAttribute('aria-label') || el.textContent); };
  var abs = function (href) { try { return new URL(href, location.href).href.slice(0, 100); } catch (e) { return clean(href); } };
  var page = (location.pathname.split('/').pop() || 'index').replace(/\.html$/, '') || 'index';

  /* Where on the page an element sits: header, footer, hero, cta_band, or the section's own heading. */
  function where(el) {
    if (el.closest('#mobile-nav')) return 'mobile_menu';
    if (el.closest('.mega')) return 'header_menu';
    if (el.closest('header')) return 'header';
    if (el.closest('footer')) return 'footer';
    if (el.closest('.crumbs, nav[aria-label="Breadcrumb"]')) return 'breadcrumb';
    var s = el.closest('section');
    if (!s) return 'page';
    if (s.classList.contains('page-hero') || s.classList.contains('hero')) return 'hero';
    if (s.querySelector('.final')) return 'cta_band';
    if (s.querySelector('#builder')) return 'pricing_builder';
    if (s.querySelector('#aff-calc')) return 'commission_calculator';
    if (s.id) return slug(s.id);
    var h = s.querySelector('.eyebrow') || s.querySelector('h2');
    return h ? slug(h.textContent) : 'section';
  }

  /* What a link leads to, in plain words that make sense in reports. */
  var TYPES = {
    demo: 'book_demo', pricing: 'pricing', signup: 'sign_up', login: 'log_in', contact: 'contact',
    affiliate: 'affiliate', partners: 'partners', careers: 'careers', features: 'features', solutions: 'solutions',
    'people-management': 'feature_page', 'attendance-leave-management': 'feature_page', 'payroll-software': 'feature_page',
    'task-project-management': 'feature_page', 'performance-scorecards': 'feature_page', 'hr-reports-analytics': 'feature_page',
    blog: 'blog', help: 'help', faq: 'faq', security: 'security', about: 'about', privacy: 'legal', terms: 'legal', index: 'home'
  };
  function ctaType(el, href) {
    if (!href) return 'button';
    if (APP.login && href === APP.login) return 'log_in';
    if (APP.signup && href === APP.signup) return 'sign_up';
    var u; try { u = new URL(href, location.href); } catch (e) { return 'other'; }
    if (u.origin !== location.origin) return 'outbound';
    var p = (u.pathname.split('/').pop() || 'index').replace(/\.html$/, '') || 'index';
    if (u.hash && p === page) return u.hash === '#apply' ? 'affiliate_apply' : 'in_page';
    if (p.indexOf('blog-') === 0) return 'blog_post';
    return TYPES[p] || 'other';
  }

  function pricingState() {
    var b = document.getElementById('builder');
    if (!b) return null;
    var mods = Array.prototype.map.call(b.querySelectorAll('input[type=checkbox]:checked'), function (c) { return c.getAttribute('data-name'); });
    var r = document.getElementById('team-size');
    return { modules: mods.join(', '), module_count: mods.length, employee_count: r ? parseInt(r.value, 10) : '' };
  }

  /* ---------- every click on a link or button ---------- */
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('a[href], button');
    if (!el) return;
    if (el.closest('form') && (el.type === 'submit' || el.tagName === 'BUTTON' && !el.type)) return; /* form submits are tracked by the form code */
    var href = el.tagName === 'A' ? el.getAttribute('href') : '';

    if (/^(mailto:|tel:)|wa\.me\/|api\.whatsapp\.com|web\.whatsapp\.com/i.test(href || '')) {
      push('contact_click', { contact_method: /^mailto:/i.test(href) ? 'email' : /^tel:/i.test(href) ? 'phone' : 'whatsapp', link_location: where(el) });
      return;
    }
    if (el.matches('.dd-btn, .menu-btn')) {
      if (el.getAttribute('aria-expanded') !== 'true') push('menu_open', { menu_name: el.matches('.menu-btn') ? 'mobile' : slug(label(el)) });
      return;
    }
    if (el.getAttribute('role') === 'tab' || el.getAttribute('role') === 'radio' || el.hasAttribute('data-team')) {
      var grp = el.closest('[role=tablist], [role=radiogroup]');
      push('tab_select', { tab_name: label(el), tab_group: grp ? clean(grp.getAttribute('aria-label')) : 'chart_filter' });
      return;
    }
    if (el.closest('[data-req]') || el.hasAttribute('data-export')) {
      push('interactive_demo', { widget: el.hasAttribute('data-export') ? 'report_export' : 'leave_approval', link_location: where(el) });
      return;
    }

    var area = where(el);
    var isCta = el.matches('.btn, .text-link, .login') || el.tagName === 'BUTTON';
    if (!isCta && /^(mobile_menu|header_menu|header|footer|breadcrumb)$/.test(area)) {
      push('navigation_click', { nav_area: area, link_text: label(el) || 'logo', link_url: abs(href) });
      return;
    }
    if (!isCta) { /* a plain link inside page content, such as a link in a blog post */
      push('navigation_click', { nav_area: 'content', link_text: label(el), link_url: abs(href) });
      return;
    }
    push('cta_click', { cta_text: label(el), cta_type: ctaType(el, href), cta_location: area, cta_url: href ? abs(href) : '' });
    var ps = el.closest('#builder, .builder-aside') || (page === 'pricing' && /quote/i.test(label(el))) ? pricingState() : null;
    if (ps) push('quote_click', ps);
  }, true);

  /* ---------- FAQ answers opened ---------- */
  document.addEventListener('toggle', function (e) {
    var d = e.target;
    if (!d.matches || !d.matches('details') || !d.open) return;
    var s = d.querySelector('summary');
    push('faq_open', { faq_question: clean(s ? s.textContent : ''), faq_section: where(d) });
  }, true);

  /* ---------- pricing builder: one event once the visitor stops adjusting ---------- */
  var builder = document.getElementById('builder'), t1;
  if (builder) builder.addEventListener('input', function () {
    clearTimeout(t1);
    t1 = setTimeout(function () { var s = pricingState(); if (s) push('pricing_configure', s); }, 1500);
  });

  /* ---------- affiliate commission calculator ---------- */
  var calc = document.getElementById('aff-calc'), t2;
  if (calc) {
    var digits = function (id) { var el = document.getElementById(id); var n = el ? parseInt(String(el.value || el.textContent).replace(/[^0-9]/g, ''), 10) : NaN; return isNaN(n) ? 0 : n; };
    var report = function () {
      clearTimeout(t2);
      t2 = setTimeout(function () {
        var on = calc.querySelector('[data-term][aria-checked="true"]');
        push('calculator_use', { calculator: 'affiliate_commission', plan_term: on ? on.getAttribute('data-term') : '', plan_amount: digits('aff-amount'), commission: digits('aff-out') });
      }, 1500);
    };
    calc.addEventListener('input', report);
    calc.addEventListener('click', function (e) { if (e.target.closest('[data-term]')) report(); });
  }

  /* ---------- first interaction with a lead form ---------- */
  Array.prototype.forEach.call(document.querySelectorAll('form[data-form]'), function (f) {
    var name = f.querySelector('input[name=form]');
    if (!name) return; /* the log-in form is not a lead form */
    var started = false;
    var start = function () { if (started) return; started = true; push('lead_form_start', { form_name: name.value }); };
    f.addEventListener('focusin', start);
    f.addEventListener('input', start);
  });

  /* ---------- scroll depth: 25, 50, 75% of the page, once each, only after the visitor actually scrolls
     (short pages that fit the screen don't report fake depth on load). GA4 adds its own 90% "scroll" event. ---------- */
  var marks = [25, 50, 75], ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking || !marks.length) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var doc = document.documentElement, h = doc.scrollHeight - window.innerHeight;
      if (h < 200) return;
      var pct = Math.round(window.scrollY / h * 100);
      while (marks.length && pct >= marks[0]) push('scroll_depth', { percent_scrolled: marks.shift() });
    });
  }, { passive: true });

  /* ---------- 404 page ---------- */
  if (document.querySelector('main.page-404')) push('page_not_found', { missing_path: clean(location.pathname + location.search, 100) });
})();
