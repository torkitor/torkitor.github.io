'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, 'assets/journey.js'), 'utf8');
const boundary = source.indexOf('  // Browser controller:');
assert.ok(boundary > 0);
const calculations = vm.runInNewContext(source.slice(0, boundary) + 'return { progressAt, chapterAt }; })();');
assert.equal(calculations.progressAt(-50, 100, 900), 0);
assert.equal(calculations.progressAt(500, 100, 900), .5);
assert.equal(calculations.progressAt(1200, 100, 900), 1);
assert.equal(calculations.progressAt(500, 100, 100), 0);
assert.equal(calculations.chapterAt(0, [100, 500, 900]), 0);
assert.equal(calculations.chapterAt(500, [100, 500, 900]), 1);
assert.equal(calculations.chapterAt(1200, [100, 500, 900]), 2);

function harness({ reducedMotion = false, hasObserver = true, observerFails = false } = {}) {
  const frames = new Map();
  let frameNumber = 0;
  let intersection;
  const watched = new Set();
  let unobserved = 0;
  function element() {
    const listeners = new Map();
    const classes = new Set();
    return {
      style: {}, dataset: {}, attributes: {},
      classList: {
        add: value => classes.add(value), remove: value => classes.delete(value), contains: value => classes.has(value),
        toggle(value, force) { if (force) classes.add(value); else classes.delete(value); }
      },
      setAttribute(name, value) { this.attributes[name] = value; },
      removeAttribute(name) { delete this.attributes[name]; },
      addEventListener(type, callback) { if (!listeners.has(type)) listeners.set(type, []); listeners.get(type).push(callback); },
      emit(type, values = {}) {
        const event = { type, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, ...values };
        for (const callback of listeners.get(type) || []) callback(event);
        return event;
      }
    };
  }
  const window = Object.assign(element(), { scrollY: 0, innerHeight: 800 });
  const media = Object.assign(element(), { matches: reducedMotion });
  window.matchMedia = () => media;
  const chapters = [800, 1500, 2400].map((offset, index) => Object.assign(element(), {
    id: `chapter-${index}`, offset,
    getBoundingClientRect() { return { top: this.offset - window.scrollY, height: 400 }; }
  }));
  const links = chapters.map(chapter => Object.assign(element(), { dataset: { chapterLink: chapter.id } }));
  const image = Object.assign(element(), { complete: false });
  const track = element();
  const progress = element();
  const timeline = Object.assign(element(), {
    getBoundingClientRect: () => ({ top: 800 - window.scrollY }),
    querySelector: selector => selector === '.journey-track' ? track : progress,
    querySelectorAll: () => chapters
  });
  const document = Object.assign(element(), {
    hidden: false, body: element(), querySelector: () => timeline,
    querySelectorAll: selector => selector === 'img' ? [image] : links
  });
  class IntersectionObserver {
    constructor(callback) { if (observerFails) throw new Error('Observer unavailable'); intersection = callback; }
    observe(target) { watched.add(target); }
    unobserve(target) { watched.delete(target); unobserved += 1; }
    disconnect() { watched.clear(); }
  }
  if (hasObserver) window.IntersectionObserver = IntersectionObserver;
  vm.runInNewContext(source, {
    document, window, IntersectionObserver,
    requestAnimationFrame: callback => { frames.set(++frameNumber, callback); return frameNumber; },
    cancelAnimationFrame: id => frames.delete(id)
  });
  return {
    window, document, media, chapters, links, track, progress, image, frames, watched,
    get unobserved() { return unobserved; },
    intersect(index, visible) { intersection([{ target: chapters[index], isIntersecting: visible }]); },
    flush() { const pending = [...frames.values()]; frames.clear(); pending.forEach(callback => callback()); }
  };
}

const page = harness();
assert.equal(page.track.style.height, '1600px', 'Track must end at the last chapter marker');
assert.equal(page.progress.style.transform, 'scaleY(0)');
assert.equal(page.links[0].attributes['aria-current'], 'location');
assert.equal(page.frames.size, 0, 'Timeline must not run a perpetual animation loop');
assert.equal(page.watched.size, 3);
page.intersect(1, true);
assert.equal(page.chapters[1].classList.contains('is-revealed'), true);
assert.equal(page.watched.has(page.chapters[1]), false);
const firstRevealCount = page.unobserved;
page.intersect(1, false);
page.intersect(1, true);
assert.equal(page.unobserved, firstRevealCount, 'A photograph must reveal only once');

page.window.scrollY = 1300;
page.window.emit('scroll');
page.window.emit('scroll');
page.window.emit('scroll');
assert.equal(page.frames.size, 1, 'Scroll events must share one pending frame');
page.flush();
assert.equal(page.links[1].attributes['aria-current'], 'location');
assert.equal(page.links[0].attributes['aria-current'], undefined);
assert.equal(page.chapters[1].classList.contains('is-current'), true);
assert.equal(page.progress.style.transform, 'scaleY(0.5675)');
assert.equal(page.frames.size, 0);
const navigation = page.links[2].emit('click');
assert.equal(navigation.defaultPrevented, false, 'Fragment navigation must remain native');
assert.equal(page.chapters[2].classList.contains('journey-instant'), true);

page.chapters[2].offset += 200;
page.image.emit('load');
page.flush();
assert.equal(page.track.style.height, '1800px', 'Late images must trigger fresh layout measurement');
page.window.emit('scroll');
page.document.hidden = true;
page.document.emit('visibilitychange');
assert.equal(page.frames.size, 0, 'Hidden tabs must cancel pending work');
page.window.emit('resize');
assert.equal(page.frames.size, 0);
page.document.hidden = false;
page.document.emit('visibilitychange');
assert.equal(page.frames.size, 1);
page.flush();
page.document.emit('keydown', { key: 'Tab' });
assert.equal(page.document.body.classList.contains('journey-motion'), false);
assert.ok(page.chapters.every(chapter => chapter.classList.contains('is-revealed') && chapter.classList.contains('journey-instant')));
assert.equal(page.watched.size, 0);

for (const options of [{ reducedMotion: true }, { hasObserver: false }, { observerFails: true }]) {
  const fallback = harness(options);
  assert.equal(fallback.document.body.classList.contains('journey-motion'), false);
  assert.ok(fallback.chapters.every(chapter => chapter.classList.contains('is-revealed')));
}
const preference = harness();
preference.media.matches = true;
preference.media.emit('change');
assert.equal(preference.document.body.classList.contains('journey-motion'), false);
assert.ok(preference.chapters.every(chapter => chapter.classList.contains('journey-instant')));
preference.media.matches = false;
preference.media.emit('change');
assert.equal(preference.document.body.classList.contains('journey-motion'), false, 'Preference changes must never replay completed reveals');

console.log('PASS: bounded progress, active chapters, once-only reveals, native anchors, keyboard/reduced-motion fallback, layout updates and event-driven lifecycle.');
