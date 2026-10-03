/* Slide-deck navigation for supplemental/slides/*.html (see assets/slides.css).
   Builds the dot strip from each <section class="slide" data-key="…" aria-label="…">
   (data-key "start" shows as "Start", "recap" as ★, anything else as written;
   data-dot="…" overrides the button label).
   ← → / PageUp PageDown / Home End, swipe, and #<data-key> in the URL all navigate.
   Optional: data-alias="e-1 x" on a slide lets #e-1 or #x open it.
   Needs #deck, #dots, #prevBtn, #nextBtn, #counter in the page. */
(function(){
  const slides = Array.from(document.querySelectorAll('.slide'));
  const dots = document.getElementById('dots');
  const prev = document.getElementById('prevBtn'), next = document.getElementById('nextBtn');
  const counter = document.getElementById('counter');
  let idx = 0;

  slides.forEach((s, i) => {
    const key = s.dataset.key;
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'dot';
    b.textContent = s.dataset.dot || (key === 'start' ? 'Start' : key === 'recap' ? '★' : key);
    b.title = s.getAttribute('aria-label');
    b.onclick = () => go(i, true);
    dots.appendChild(b);
  });

  function go(i, push){
    idx = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, j) => s.classList.toggle('active', j === idx));
    Array.from(dots.children).forEach((d, j) => { d.classList.toggle('on', j === idx); d.setAttribute('aria-selected', j === idx); });
    prev.disabled = idx === 0;
    next.disabled = idx === slides.length - 1;
    const label = slides[idx].getAttribute('aria-label');
    counter.textContent = `${idx + 1} / ${slides.length} — ${label}`;
    const hash = '#' + slides[idx].dataset.key;
    if(push && location.hash !== hash) history.replaceState(null, '', hash);
    const top = document.getElementById('deck').getBoundingClientRect().top;
    if(top < 0) window.scrollTo({top: window.scrollY + top - 8});
  }
  function fromHash(){
    const k = (location.hash || '').slice(1).toLowerCase();
    const i = slides.findIndex(s => s.dataset.key === k || (s.dataset.alias || '').split(' ').includes(k));
    go(i >= 0 ? i : 0, false);
  }

  prev.onclick = () => go(idx - 1, true);
  next.onclick = () => go(idx + 1, true);
  document.addEventListener('keydown', e => {
    if(e.target.closest('input, textarea, summary') || e.altKey || e.ctrlKey || e.metaKey) return;
    if(e.key === 'ArrowRight' || e.key === 'PageDown'){ go(idx + 1, true); e.preventDefault(); }
    else if(e.key === 'ArrowLeft' || e.key === 'PageUp'){ go(idx - 1, true); e.preventDefault(); }
    else if(e.key === 'Home'){ go(0, true); e.preventDefault(); }
    else if(e.key === 'End'){ go(slides.length - 1, true); e.preventDefault(); }
  });
  // swipe on touch screens (horizontal swipes only, so vertical scrolling still works)
  let sx = null, sy = null;
  const deck = document.getElementById('deck');
  deck.addEventListener('touchstart', e => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, {passive:true});
  deck.addEventListener('touchend', e => {
    if(sx === null) return;
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if(Math.abs(dx) > 60 && Math.abs(dx) > 1.5 * Math.abs(dy)) go(idx + (dx < 0 ? 1 : -1), true);
    sx = sy = null;
  }, {passive:true});
  // label each cell with its column heading (used by the stacked phone layout)
  document.querySelectorAll('table.recap').forEach(t => {
    const heads = Array.from(t.rows[0].cells).map(c => c.textContent.trim());
    Array.from(t.rows).slice(1).forEach(r => Array.from(r.cells).forEach((c, i) => { if(heads[i]) c.dataset.l = heads[i]; }));
  });
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
