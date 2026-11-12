(() => {
  'use strict';

  function progressAt(position, start, end) {
    return end > start ? Math.max(0, Math.min(1, (position - start) / (end - start))) : 0;
  }

  function chapterAt(position, offsets) {
    let current = 0;
    for (let i = 1; i < offsets.length; i += 1) {
      if (offsets[i] > position) break;
      current = i;
    }
    return current;
  }

  // Browser controller: the scroll calculations above have no DOM dependencies.
  const timeline = document.querySelector('#journey-timeline');
  if (!timeline) return;
  const chapters = [...timeline.querySelectorAll('.journey-chapter')];
  const track = timeline.querySelector('.journey-track');
  const progress = timeline.querySelector('.journey-progress');
  const links = [...document.querySelectorAll('[data-chapter-link]')];
  if (!chapters.length || !track || !progress) return;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const revealed = new Set();
  let observer = null;
  let frameId = 0;
  let offsets = [];
  let start = 0;
  let end = 0;
  let needsMeasure = true;
  let active = -1;

  function reveal(chapter, instant = false) {
    if (instant) chapter.classList.add('journey-instant');
    if (revealed.has(chapter)) return;
    revealed.add(chapter);
    chapter.classList.add('is-revealed');
    observer?.unobserve(chapter);
  }

  function finishReveals() {
    document.body.classList.remove('journey-motion');
    chapters.forEach(chapter => reveal(chapter, true));
    observer?.disconnect();
  }

  function measure() {
    const scroll = window.scrollY;
    const timelineTop = timeline.getBoundingClientRect().top + scroll;
    offsets = chapters.map(chapter => chapter.getBoundingClientRect().top + scroll);
    start = offsets[0] + 8;
    end = offsets[offsets.length - 1] + 8;
    // This is a layout measurement, never an animated height; only the child scales on scroll.
    track.style.top = `${start - timelineTop}px`;
    track.style.bottom = 'auto';
    track.style.height = `${Math.max(0, end - start)}px`;
    needsMeasure = false;
  }

  function update() {
    frameId = 0;
    if (document.hidden) return;
    if (needsMeasure) measure();
    const scroll = window.scrollY;
    progress.style.transform = `scaleY(${progressAt(scroll + window.innerHeight * .52, start, end)})`;
    const next = chapterAt(scroll + window.innerHeight * .35, offsets);
    if (next !== active) {
      active = next;
      chapters.forEach((chapter, index) => chapter.classList.toggle('is-current', index === active));
      links.forEach(link => {
        if (link.dataset.chapterLink === chapters[active].id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }
    chapters.forEach((chapter, index) => chapter.classList.toggle('is-reached', offsets[index] + 8 <= scroll + window.innerHeight * .52));
  }

  function schedule(measureAgain = false) {
    if (measureAgain) needsMeasure = true;
    if (!document.hidden && !frameId) frameId = requestAnimationFrame(update);
  }

  measure();
  if (!reduced.matches && 'IntersectionObserver' in window) {
    try {
      observer = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) reveal(entry.target); });
      }, { threshold: .08, rootMargin: '0px 0px -10% 0px' });
      chapters.forEach((chapter, index) => {
        if (offsets[index] < window.scrollY + window.innerHeight * .9) reveal(chapter, true);
        else observer.observe(chapter);
      });
      document.body.classList.add('journey-motion');
    } catch {
      finishReveals();
    }
  } else {
    finishReveals();
  }

  links.forEach(link => {
    const chapter = chapters.find(item => item.id === link.dataset.chapterLink);
    if (!chapter) return;
    link.addEventListener('click', () => reveal(chapter, true));
  });
  chapters.forEach(chapter => chapter.addEventListener('focusin', () => reveal(chapter, true)));
  document.addEventListener('keydown', event => {
    if (['Tab', 'PageDown', 'PageUp', 'Home', 'End', 'ArrowDown', 'ArrowUp', ' '].includes(event.key)) finishReveals();
  }, { capture: true });
  window.addEventListener('scroll', () => schedule(), { passive: true });
  window.addEventListener('resize', () => schedule(true));
  if ('ResizeObserver' in window) new ResizeObserver(() => schedule(true)).observe(timeline);
  document.querySelectorAll('img').forEach(image => {
    if (!image.complete) image.addEventListener('load', () => schedule(true), { once: true });
  });
  document.fonts?.ready.then(() => schedule(true));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      if (frameId) cancelAnimationFrame(frameId);
      frameId = 0;
    } else schedule(true);
  });
  reduced.addEventListener('change', () => {
    if (reduced.matches) finishReveals();
    schedule();
  });
  update();
})();
