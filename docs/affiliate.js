/* Affiliate page: commission calculator. Standalone, so it works even if the shared script is stale or fails. */
(function () {
  'use strict';
  var RATE = 0.2;
  function init() {
    var calc = document.getElementById('aff-calc');
    if (!calc) return;
    var amt = document.getElementById('aff-amount');
    var out = document.getElementById('aff-out');
    var termEl = document.getElementById('aff-term');
    var label = document.getElementById('aff-label');
    var note = document.getElementById('aff-note');
    var buttons = calc.querySelectorAll('[data-term]');
    var term = 'annual';

    function parse() { return parseInt(String(amt.value).replace(/[^0-9]/g, ''), 10) || 0; }
    function money(n) { return 'Rs ' + Math.round(n).toLocaleString('en-US'); }

    function render() {
      var annual = term === 'annual';
      out.textContent = money(parse() * RATE);
      termEl.textContent = annual ? '12 months' : '1 month';
      label.textContent = annual ? 'What the customer pays for the year (Rs)' : 'What the customer pays per month (Rs)';
      note.textContent = annual ? "Paid once, on the customer's first annual payment."
        : "Paid once, on the customer's first monthly payment. Renewals aren't included.";
    }

    // keep the commas while typing, without throwing the cursor to the end
    function reformat() {
      var raw = String(amt.value);
      var caret = amt.selectionStart == null ? raw.length : amt.selectionStart;
      var digitsBefore = raw.slice(0, caret).replace(/[^0-9]/g, '').length;
      var v = parse();
      var formatted = v ? v.toLocaleString('en-US') : '';
      if (formatted !== raw) {
        amt.value = formatted;
        var pos = 0, seen = 0;
        while (pos < formatted.length && seen < digitsBefore) { if (/[0-9]/.test(formatted[pos])) seen++; pos++; }
        try { amt.setSelectionRange(pos, pos); } catch (e) { /* some mobile keyboards refuse; fine */ }
      }
      render();
    }

    ['input', 'change', 'keyup', 'paste'].forEach(function (ev) {
      amt.addEventListener(ev, function () { setTimeout(reformat, 0); });
    });

    Array.prototype.forEach.call(buttons, function (b) {
      b.addEventListener('click', function () {
        term = b.getAttribute('data-term');
        Array.prototype.forEach.call(buttons, function (x) { x.setAttribute('aria-checked', String(x === b)); });
        // swap the example value so the switch makes sense at a glance
        if (term === 'monthly' && parse() === 600000) amt.value = '50,000';
        if (term === 'annual' && parse() === 50000) amt.value = '600,000';
        render();
      });
    });

    render();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
