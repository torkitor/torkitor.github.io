'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Evaluate only the pure geometry; the browser controller and DOM are excluded.
const source = fs.readFileSync(path.join(__dirname, 'assets/knowledge-cloud.js'), 'utf8');
const boundary = source.indexOf('  // Browser controller:');
assert.ok(boundary > 0, 'Geometry/controller boundary must remain explicit');
const geometry = vm.runInNewContext(source.slice(0, boundary) + 'return { fields, createLandscape, rotatePoint, projectPoint, landscapeScale }; })();');
const points = geometry.createLandscape();
assert.equal(geometry.fields.length, 6);
assert.equal(new Set(geometry.fields.map(field => field.id)).size, 6);
assert.equal(points.length, 1188);
assert.equal(JSON.stringify(points), JSON.stringify(geometry.createLandscape()), 'Landscape must be stable across visits');

for (const [group, field] of geometry.fields.entries()) {
  const cluster = points.filter(point => !point.bridge && point.group === group);
  assert.equal(cluster.length, 174);
  for (const [axis, index] of [['x', 0], ['y', 1], ['z', 2]]) {
    const mean = cluster.reduce((total, point) => total + point[axis], 0) / cluster.length;
    assert.ok(Math.abs(mean - field.center[index]) < .015, `${field.id} must remain centred on its label`);
  }
}

for (const [width, height] of [[320, 360], [600, 400], [1180, 570]]) {
  const scale = geometry.landscapeScale(width, height);
  for (const yaw of [-Math.PI, -.22, 0, Math.PI / 2]) {
    for (const pitch of [-.65, -.12, .65]) {
      for (const point of points) {
        const rotated = geometry.rotatePoint(point, yaw, pitch);
        assert.ok(Math.abs(Math.hypot(point.x, point.y, point.z) - Math.hypot(rotated.x, rotated.y, rotated.z)) < 1e-10, 'Rotation must preserve distance');
        const projected = geometry.projectPoint(rotated, width, height, scale);
        assert.ok(Object.values(projected).every(Number.isFinite), 'Projection must remain finite');
        assert.ok(projected.x > 0 && projected.x < width && projected.y > 0 && projected.y < height, `Cloud outside ${width}x${height} at yaw ${yaw}, pitch ${pitch}: ${JSON.stringify(projected)}`);
      }
    }
  }
}

function controllerHarness({ reducedMotion = false, canvasAvailable = true } = {}) {
  const frames = new Map();
  let nextFrame = 0;
  let intersect;
  const paint = { count: 0, arcs: [], labels: [] };
  const context = new Proxy({
    clearRect() { paint.count += 1; paint.arcs = []; paint.labels = []; },
    arc(...args) { paint.arcs.push(args); },
    fillText(text, x, y) { paint.labels.push({ text, x, y }); },
    measureText(text) { return { width: text.length * 6 }; }
  }, { get(target, key) { return target[key] || (() => {}); } });
  function element() {
    const listeners = new Map();
    const classes = new Set();
    const captures = new Set();
    return {
      hidden: false, attributes: {}, dataset: {}, style: { setProperty() {} },
      classList: { add: value => classes.add(value), remove: value => classes.delete(value), contains: value => classes.has(value) },
      addEventListener(type, callback) { if (!listeners.has(type)) listeners.set(type, []); listeners.get(type).push(callback); },
      emit(type, values = {}) {
        const event = { type, isPrimary: true, button: 0, pointerId: 1, pointerType: 'mouse', clientX: 300, clientY: 200, cancelable: true, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, ...values };
        for (const callback of listeners.get(type) || []) callback(event);
        return event;
      },
      setAttribute(name, value) { this.attributes[name] = value; if (name === 'hidden') this.hidden = true; },
      replaceChildren(...children) { this.children = children; },
      getBoundingClientRect() { return { width: 600, height: 400, left: 0, top: 0 }; },
      getContext() { return canvasAvailable ? context : null; },
      setPointerCapture(id) { captures.add(id); },
      hasPointerCapture(id) { return captures.has(id); },
      releasePointerCapture(id) { captures.delete(id); this.emit('lostpointercapture', { pointerId: id }); }
    };
  }
  const nodes = Object.fromEntries(['#knowledge-canvas', '.knowledge-stage', '.knowledge-fields', '.knowledge-selection', '#knowledge-detail', '#knowledge-link', '#knowledge-pause', '.knowledge-fallback'].map(id => [id, element()]));
  for (const key of ['.knowledge-stage', '.knowledge-fields', '.knowledge-selection']) nodes[key].hidden = true;
  const buttons = geometry.fields.map(field => Object.assign(element(), { dataset: { field: field.id } }));
  const root = Object.assign(element(), { querySelector: selector => nodes[selector], querySelectorAll: () => buttons });
  const document = Object.assign(element(), { hidden: false, querySelector: () => root, createElement: element });
  const media = Object.assign(element(), { matches: reducedMotion });
  class IntersectionObserver { constructor(callback) { intersect = callback; } observe() {} }
  class ResizeObserver { observe() {} }
  const window = Object.assign(element(), { devicePixelRatio: 3, matchMedia: () => media, IntersectionObserver, ResizeObserver });
  vm.runInNewContext(source, {
    document, window, IntersectionObserver, ResizeObserver,
    getComputedStyle: () => ({ getPropertyValue: key => key === '--paper' ? '#f5f3ee' : '#171b1d' }),
    requestAnimationFrame: callback => { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame: id => frames.delete(id)
  });
  return {
    ...nodes, buttons, document, window, media, frames, paint,
    visible(value) { intersect([{ isIntersecting: value }]); },
    step(time) { const pending = [...frames.values()]; frames.clear(); pending.forEach(callback => callback(time)); }
  };
}

const fallback = controllerHarness({ canvasAvailable: false });
assert.equal(fallback['.knowledge-fallback'].hidden, false);
assert.equal(fallback['.knowledge-stage'].hidden, true);
assert.equal(fallback.frames.size, 0);

const lifecycle = controllerHarness();
assert.equal(lifecycle['#knowledge-canvas'].width, 1200, 'DPR must be capped at two');
assert.equal(lifecycle.frames.size, 0, 'Offscreen initialization must not start a loop');
lifecycle.visible(true);
lifecycle.visible(true);
assert.equal(lifecycle.frames.size, 1, 'Observer notifications must not create duplicate loops');
lifecycle.step(100);
assert.equal(lifecycle.frames.size, 1);
lifecycle.visible(false);
assert.equal(lifecycle.frames.size, 0);
lifecycle.visible(true);
assert.equal(lifecycle.frames.size, 1);
lifecycle.document.hidden = true;
lifecycle.document.emit('visibilitychange');
assert.equal(lifecycle.frames.size, 0, 'Background tabs must cancel pending frames');
lifecycle.document.hidden = false;
lifecycle.document.emit('visibilitychange');
assert.equal(lifecycle.frames.size, 1);
lifecycle['#knowledge-pause'].emit('click');
assert.equal(lifecycle.frames.size, 0);
lifecycle.visible(false);
lifecycle.visible(true);
assert.equal(lifecycle.frames.size, 0, 'Visibility must not override an explicit pause');
lifecycle['#knowledge-pause'].emit('click');
assert.equal(lifecycle.frames.size, 1);
lifecycle.media.matches = true;
lifecycle.media.emit('change');
assert.equal(lifecycle.frames.size, 0, 'Changing to reduced motion must stop autoplay');
lifecycle.media.matches = false;
lifecycle.media.emit('change');
assert.equal(lifecycle.frames.size, 0, 'Changing a system preference must not implicitly resume');

const reduced = controllerHarness({ reducedMotion: true });
reduced.visible(true);
assert.equal(reduced.frames.size, 0, 'Reduced motion must start static');
const initialPoint = JSON.stringify(reduced.paint.arcs[0]);
assert.equal(reduced['#knowledge-canvas'].emit('keydown', { key: 'ArrowRight' }).defaultPrevented, true);
assert.notEqual(JSON.stringify(reduced.paint.arcs[0]), initialPoint, 'Keyboard input must update the view immediately');
reduced['#knowledge-canvas'].emit('keydown', { key: 'Home' });
assert.equal(JSON.stringify(reduced.paint.arcs[0]), initialPoint, 'Home must restore the initial view');
assert.equal(reduced['#knowledge-canvas'].emit('keydown', { key: 'Tab' }).defaultPrevented, false);
reduced.buttons[3].emit('click');
assert.equal(reduced['#knowledge-detail'].children[0].textContent, 'Medical AI');
assert.equal(reduced['#knowledge-link'].href, 'publications/?topic=Medical%20AI');
assert.equal(reduced.buttons.filter(button => button.attributes['aria-pressed'] === 'true').length, 1);
reduced.buttons[5].emit('click');
assert.equal(reduced['#knowledge-link'].href, 'software/');
reduced['#knowledge-pause'].emit('click');
assert.equal(reduced.frames.size, 1, 'Reduced motion allows an explicit user opt-in');
reduced['.knowledge-fields'].emit('focusin');
assert.equal(reduced.frames.size, 0, 'Reading field controls must pause motion');

const touch = controllerHarness();
touch.visible(true);
const target = touch.paint.labels.find(label => label.text === 'Medical AI');
const touchCanvas = touch['#knowledge-canvas'];
touchCanvas.emit('pointerdown', { pointerType: 'touch', clientX: target.x + 4, clientY: target.y - 45 });
const vertical = touchCanvas.emit('pointermove', { pointerType: 'touch', clientX: target.x + 4, clientY: target.y - 4 });
assert.equal(vertical.defaultPrevented, false, 'Vertical touch scrolling must remain native');
assert.equal(touchCanvas.hasPointerCapture(1), false);
touchCanvas.emit('pointerup', { pointerType: 'touch', clientX: target.x + 4, clientY: target.y - 4 });
assert.equal(touch.buttons[0].attributes['aria-pressed'], 'true', 'A scroll gesture must not become a label tap');
touchCanvas.emit('pointerdown', { pointerType: 'touch' });
assert.equal(touchCanvas.emit('pointermove', { pointerType: 'touch', clientX: 340, clientY: 202 }).defaultPrevented, true);
assert.equal(touchCanvas.hasPointerCapture(1), true);
assert.equal(touch.frames.size, 0, 'Dragging must stop automatic rotation');
touchCanvas.emit('pointercancel');
assert.equal(touchCanvas.hasPointerCapture(1), false);
assert.equal(touchCanvas.classList.contains('is-dragging'), false);
touchCanvas.emit('pointerdown');
touchCanvas.emit('pointermove', { clientX: 340 });
touch.window.emit('blur');
assert.equal(touchCanvas.hasPointerCapture(1), false, 'Window interruption must release a drag');
assert.equal(touchCanvas.classList.contains('is-dragging'), false);
touchCanvas.emit('pointerdown');
touchCanvas.emit('pointermove', { clientX: 340 });
touchCanvas.releasePointerCapture(1);
assert.equal(touchCanvas.classList.contains('is-dragging'), false, 'Lost capture must clear drag styling');
touchCanvas.emit('pointerdown');
touchCanvas.emit('pointermove', { clientX: 340 });
touch.document.hidden = true;
touch.document.emit('visibilitychange');
assert.equal(touchCanvas.hasPointerCapture(1), false, 'Hiding a tab must release a drag');
assert.equal(touchCanvas.classList.contains('is-dragging'), false);
assert.equal(touch.frames.size, 0);

console.log('PASS: geometry, projection bounds, fallback, DPR, animation lifecycle, reduced motion, keyboard, selection and touch cancellation.');
