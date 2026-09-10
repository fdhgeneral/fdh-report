/* ============================================================
   FDH Hall of Fame — Core JavaScript
   ============================================================ */

'use strict';

/* ── Mobile Nav ── */
(function () {
  const burger = document.querySelector('.nav__burger');
  const links  = document.querySelector('.nav__links');
  if (!burger || !links) return;
  burger.addEventListener('click', () => links.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!burger.contains(e.target) && !links.contains(e.target))
      links.classList.remove('open');
  });
})();

/* ── Active Nav link ── */
(function () {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav__link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === path || (path === '' && href === 'index.html'))
      link.classList.add('active');
  });
})();

/* ── Tabs ── */
function initTabs(container) {
  const btns   = container.querySelectorAll('.tab-btn');
  const panels = container.querySelectorAll('.tab-panel');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = container.querySelector('#' + btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });
}
document.querySelectorAll('[data-tabs]').forEach(initTabs);

/* ── Sortable Tables ── */
function initSortableTable(table) {
  const headers = table.querySelectorAll('th[data-sort]');
  headers.forEach(th => {
    th.style.cursor = 'pointer';
    th.title = 'Click to sort';
    th.addEventListener('click', () => {
      const col  = parseInt(th.dataset.sort, 10);
      const asc  = th.dataset.asc !== 'true';
      th.dataset.asc = asc;
      headers.forEach(h => h.removeAttribute('data-asc'));
      th.dataset.asc = asc;

      const tbody = table.querySelector('tbody');
      const rows  = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {
        const av = a.cells[col]?.textContent.trim() || '';
        const bv = b.cells[col]?.textContent.trim() || '';
        const an = parseFloat(av.replace(/[^0-9.-]/g, ''));
        const bn = parseFloat(bv.replace(/[^0-9.-]/g, ''));
        const cmp = isNaN(an) || isNaN(bn)
          ? av.localeCompare(bv)
          : an - bn;
        return asc ? cmp : -cmp;
      });
      rows.forEach(r => tbody.appendChild(r));

      // Update rank column if present
      tbody.querySelectorAll('td.rank').forEach((cell, i) => {
        cell.textContent = i + 1;
      });
    });
  });
}
document.querySelectorAll('.fdh-table[data-sortable]').forEach(initSortableTable);

/* ── Animated counters ── */
function animateCounter(el) {
  const target = parseFloat(el.dataset.target);
  const isFloat = el.dataset.target.includes('.');
  const decimals = isFloat ? (el.dataset.target.split('.')[1]?.length || 1) : 0;
  const duration = 1200;
  const start = performance.now();
  function update(now) {
    const p = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    const val = target * ease;
    el.textContent = isFloat ? val.toFixed(decimals) : Math.round(val).toLocaleString();
    if (p < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

const counterObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });
document.querySelectorAll('[data-counter]').forEach(el => counterObserver.observe(el));

/* ── Search / Filter ── */
function initTableFilter(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;
  input.addEventListener('input', () => {
    const q = input.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}
// Auto-wire any filter inputs with data-filter-table attribute
document.querySelectorAll('[data-filter-table]').forEach(input => {
  initTableFilter(input.id, input.dataset.filterTable);
});

/* ── Smooth scroll for anchor links ── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

/* ── Progress bars ── */
const barObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const fill = entry.target.querySelector('.progress-bar__fill');
      if (fill) fill.style.width = fill.dataset.width;
      barObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.2 });
document.querySelectorAll('.progress-bar').forEach(bar => {
  const fill = bar.querySelector('.progress-bar__fill');
  if (fill) { fill.style.width = '0'; barObserver.observe(bar); }
});

/* ── Last-updated timestamp ── */
(function () {
  const el = document.getElementById('last-updated-ts');
  if (!el) return;
  const raw = el.dataset.ts;
  if (!raw) return;
  try {
    const d = new Date(raw);
    el.textContent = d.toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
    });
  } catch (_) {}
})();
