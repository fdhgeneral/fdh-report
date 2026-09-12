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

/* H2H interactive lookup */
(function(){
  var sA=document.getElementById("mgr-a");
  var sB=document.getElementById("mgr-b");
  var res=document.getElementById("h2h-result");
  if(!sA||!sB||!res)return;
  var H=window.FDH_H2H||{};
  function f(n){return(Math.round(Number(n)*10)/10).toFixed(1);}
  function go(){
    var a=sA.value.trim(),b=sB.value.trim();
    if(!a||!b){res.innerHTML="<p class=\"h2h-placeholder\">Select two managers to see their record.</p>";return;}
    if(a===b){res.innerHTML="<p class=\"h2h-placeholder\">Select two different managers.</p>";return;}
    var k=[a,b].sort().join("|"),d=H[k];
    if(!d){res.innerHTML="<p class=\"h2h-placeholder\">No matchups found between <strong>"+a+"</strong> and <strong>"+b+"</strong>.</p>";return;}
    var fl=(d.a!==a);
    var wA=fl?d.wins_b:d.wins_a,wB=fl?d.wins_a:d.wins_b;
    var pfA=fl?d.pf_b:d.pf_a,pfB=fl?d.pf_a:d.pf_b;
    var pgA=fl?d.ppg_b:d.ppg_a,pgB=fl?d.ppg_a:d.ppg_b;
    var cA=wA>wB?"win":wA<wB?"lose":"tied";
    var cB=wB>wA?"win":wB<wA?"lose":"tied";
    var bw=d.biggest_win||{},cl=d.closest_game||{},sk=d.streak||{};
    var bwCtx=(bw.score_w!==undefined)?"("+f(bw.score_w)+"\u2013"+f(bw.score_l)+", "+(bw.context||"")+")":"("+(bw.context||"")+")"
    var po=d.playoff_meetings>0?"<div class=\"h2h-center-meta\">&#9889; "+d.playoff_meetings+" playoff</div>":"";
    var sr="";
    if(d.seasons){Object.keys(d.seasons).sort().forEach(function(yr){
      var s=d.seasons[yr];
      var wa=fl?s.wins_b:s.wins_a,wb=fl?s.wins_a:s.wins_b;
      sr+="<tr><td>"+yr+"</td><td style=\"font-weight:600\">"+wa+"\u2013"+wb+"</td><td>"+s.meetings+" game"+(s.meetings!==1?"s":"")+"</td></tr>";
    });}
    var h="<div class=\"h2h-result-card\">"
      +"<div class=\"h2h-result-header\">"
        +"<div class=\"h2h-result-side\"><div class=\"h2h-result-name\">"+a+"</div><div class=\"h2h-wins "+cA+"\">"+wA+"</div><div class=\"h2h-pts\">"+f(pfA)+" pts &bull; "+pgA+" PPG</div></div>"
        +"<div class=\"h2h-center\"><div class=\"h2h-center-vs\">VS</div><div class=\"h2h-center-meta\">"+d.meetings+" meetings</div>"+po+"</div>"
        +"<div class=\"h2h-result-side\"><div class=\"h2h-result-name\">"+b+"</div><div class=\"h2h-wins "+cB+"\">"+wB+"</div><div class=\"h2h-pts\">"+f(pfB)+" pts &bull; "+pgB+" PPG</div></div>"
      +"</div>"
      +"<div class=\"h2h-facts\">"
        +"<div class=\"h2h-fact\">&#127942; <b>Biggest win:</b> "+(bw.winner||"?")+" +"+bw.margin+" pts "+bwCtx+"</div>"
        +"<div class=\"h2h-fact\">&#128293; <b>Streak:</b> "+(sk.holder||"?")+" &mdash; "+(sk.count||1)+"W in a row</div>"
        +"<div class=\"h2h-fact\">&#9203; <b>Closest game:</b> "+(cl.winner||"?")+" +"+(cl.margin||0)+" pts ("+(cl.context||"")+").</div>"
      +"</div>"
      +"<div class=\"h2h-breakdown\"><h4>Season Breakdown</h4>"
        +"<table><thead><tr><th>Season</th><th>"+a+"</th><th>Games</th></tr></thead><tbody>"+sr+"</tbody></table>"
      +"</div></div>";
    res.innerHTML=h;
  }
  sA.addEventListener("change",go);
  sB.addEventListener("change",go);
  try{
    var ks=Object.keys(H);
    if(ks.length){
      var ops=[].slice.call(sA.options).map(function(o){return o.value;});
      var top=ks.reduce(function(b,k){
        if(ops.indexOf(H[k].a)<0||ops.indexOf(H[k].b)<0)return b;
        return(!b||H[k].meetings>H[b].meetings)?k:b;
      },null);
      if(top){sA.value=H[top].a;sB.value=H[top].b;go();}
    }
  }catch(e){console.warn("FDH H2H auto-load:",e);}
})();
(function(){
  var inp=document.getElementById("h2h-search");
  var tbl=document.getElementById("h2h-table");
  if(!inp||!tbl)return;
  inp.addEventListener("input",function(){
    var q=this.value.trim().toLowerCase();
    var rows=tbl.tBodies[0].rows;
    for(var i=0;i<rows.length;i++){
      var m=(rows[i].cells[0]?rows[i].cells[0].textContent:"").toLowerCase();
      var o=(rows[i].cells[1]?rows[i].cells[1].textContent:"").toLowerCase();
      rows[i].style.display=(!q||m.indexOf(q)>-1||o.indexOf(q)>-1)?"":"none";
    }
  });
})();
