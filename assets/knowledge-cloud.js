(() => {
  'use strict';

  const fields = [
    { id: 'mri', name: 'Quantitative MRI', short: 'MRI', color: '#a0442c', center: [-.66, .3, .23], radii: [.43, .3, .34], description: 'Perfusion MRI and the interpretation of vascular and metabolic biomarkers in brain tumours. I study how acquisition and analytical choices affect the measurements we use.', topic: 'Neuroimaging' },
    { id: 'oncology', name: 'Neuro-oncology', short: 'Neuro-oncology', color: '#586d61', center: [-.72, -.42, -.21], radii: [.4, .3, .32], description: 'Brain tumour characterisation through imaging: connecting clinical questions, tumour biology and quantitative MRI, including presurgical differential diagnosis.', topic: 'Neuroimaging' },
    { id: 'radiomics', name: 'Radiomics', short: 'Radiomics', color: '#526c7a', center: [.05, .47, -.27], radii: [.4, .31, .35], description: 'The reliability of imaging features and the analyses built on them. My work examines preprocessing, information leakage, model multiplicity and patient-specific image surrogates.', topic: 'Radiomics & methods' },
    { id: 'ai', name: 'Medical AI', short: 'Medical AI', color: '#996b45', center: [.73, .18, .1], radii: [.41, .33, .35], description: 'Evaluation of machine learning and large language models in medicine, with an emphasis on construct validity, transparent benchmarks and the evidence behind performance claims.', topic: 'Medical AI' },
    { id: 'statistics', name: 'Biostatistics', short: 'Statistics', color: '#587b7c', center: [.6, -.49, -.24], radii: [.41, .29, .31], description: 'Study design, uncertainty and reproducible analysis. I investigate how validation, resampling and analytical decisions change the conclusions drawn from biomedical data.', topic: 'Radiomics & methods' },
    { id: 'software', name: 'Research software', short: 'Software', color: '#7b6372', center: [-.06, -.63, .27], radii: [.4, .27, .32], description: 'Inspectable tools that turn research methods into reproducible workflows, including imaging preprocessing checks and pixel-level de-identification of radiographs.', href: 'software/' }
  ];
  const connections = [[0, 1], [0, 2], [1, 2], [2, 3], [2, 4], [3, 4], [3, 5], [4, 5], [0, 5]];

  function createLandscape() {
    const points = [];
    const angle = Math.PI * (3 - Math.sqrt(5));
    fields.forEach((field, group) => {
      for (let i = 0; i < 174; i += 1) {
        const y = 1 - 2 * (i + .5) / 174;
        const radius = Math.sqrt(1 - y * y);
        const theta = i * angle;
        const shell = .83 + .13 * Math.sin(i * 2.17 + group);
        const x = radius * Math.cos(theta);
        const z = radius * Math.sin(theta);
        points.push({
          x: field.center[0] + field.radii[0] * x * shell,
          y: field.center[1] + field.radii[1] * y * shell,
          z: field.center[2] + field.radii[2] * z * shell + .04 * Math.sin(theta * 2),
          group, size: .8 + .65 * ((i * 37 % 101) / 101), bridge: false
        });
      }
    });
    connections.forEach(([a, b]) => {
      for (let i = 1; i < 17; i += 1) {
        const t = i / 17;
        const from = fields[a].center;
        const to = fields[b].center;
        points.push({
          x: from[0] + (to[0] - from[0]) * t,
          y: from[1] + (to[1] - from[1]) * t + Math.sin(t * Math.PI) * .09,
          z: from[2] + (to[2] - from[2]) * t + Math.sin(t * Math.PI) * .15,
          group: t < .5 ? a : b, size: .7, bridge: true
        });
      }
    });
    return points;
  }

  function rotatePoint(point, yaw, pitch) {
    const x = point.x * Math.cos(yaw) + point.z * Math.sin(yaw);
    const z = -point.x * Math.sin(yaw) + point.z * Math.cos(yaw);
    return { x, y: point.y * Math.cos(pitch) - z * Math.sin(pitch), z: point.y * Math.sin(pitch) + z * Math.cos(pitch) };
  }

  function projectPoint(point, width, height, scale) {
    const perspective = 3.8 / (3.8 + point.z);
    return { x: width / 2 + point.x * scale * perspective, y: height / 2 - point.y * scale * perspective, z: point.z, perspective };
  }

  function landscapeScale(width, height) {
    return Math.min(width * (width < 600 ? .31 : .34), height * .4);
  }

  // Browser controller: geometry above is deterministic and independently testable.
  const root = document.querySelector('#knowledge-map');
  if (!root) return;
  const canvas = root.querySelector('#knowledge-canvas');
  const stage = root.querySelector('.knowledge-stage');
  const controls = root.querySelector('.knowledge-fields');
  const selection = root.querySelector('.knowledge-selection');
  const detail = root.querySelector('#knowledge-detail');
  const link = root.querySelector('#knowledge-link');
  const pause = root.querySelector('#knowledge-pause');
  const buttons = [...root.querySelectorAll('[data-field]')];
  if (!canvas || !stage || !controls || !selection || !detail || !link || !pause || buttons.length !== fields.length) return;
  let context;
  try { context = canvas.getContext('2d'); } catch { return; }
  if (!context) return;

  const points = createLandscape();
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches;
  let inView = !('IntersectionObserver' in window);
  let selected = 0;
  let yaw = -.22;
  let pitch = -.12;
  let width = 0;
  let height = 0;
  let frameId = 0;
  let lastTime = 0;
  let lastPaint = 0;
  let pointer = null;
  let labelBounds = [];
  const paper = getComputedStyle(root).getPropertyValue('--paper').trim() || '#f5f3ee';
  const ink = getComputedStyle(root).getPropertyValue('--ink').trim() || '#171b1d';

  function updatePause() {
    pause.textContent = paused ? 'Resume rotation' : 'Pause rotation';
    pause.setAttribute('aria-label', paused ? 'Resume automatic map rotation' : 'Pause automatic map rotation');
  }

  function draw() {
    if (!width || !height) return;
    context.clearRect(0, 0, width, height);
    const scale = landscapeScale(width, height);
    const projected = points.map(point => ({ ...projectPoint(rotatePoint(point, yaw, pitch), width, height, scale), point }));
    projected.sort((a, b) => b.z - a.z);
    for (const item of projected) {
      const active = item.point.group === selected;
      const depth = Math.max(.2, Math.min(1, .65 - item.z * .34));
      context.globalAlpha = depth * (active ? .95 : .55) * (item.point.bridge ? .6 : 1);
      context.fillStyle = fields[item.point.group].color;
      context.beginPath();
      context.arc(item.x, item.y, (item.point.size + (active ? .45 : .1)) * item.perspective, 0, Math.PI * 2);
      context.fill();
    }
    context.globalAlpha = 1;
    const labels = fields.map((field, index) => {
      const center = { x: field.center[0], y: field.center[1], z: field.center[2] };
      return { ...projectPoint(rotatePoint(center, yaw, pitch), width, height, scale), field, index };
    });
    labelBounds = [];
    const fontSize = width < 600 ? 11 : 12;
    context.font = `${fontSize}px Helvetica, Arial, sans-serif`;
    for (const side of [-1, 1]) {
      const list = labels.filter(label => (label.x < width / 2 ? -1 : 1) === side).sort((a, b) => a.y - b.y);
      let previous = 14;
      list.forEach((label, position) => {
        const text = width < 600 ? label.field.short : label.field.name;
        const textWidth = context.measureText(text).width;
        const textX = side < 0 ? 14 : width - textWidth - 14;
        const maxY = height - 22 - (list.length - position - 1) * 30;
        const textY = Math.min(maxY, Math.max(previous + 30, label.y));
        previous = textY;
        const active = label.index === selected;
        const edgeX = side < 0 ? textX + textWidth + 7 : textX - 7;
        context.strokeStyle = label.field.color;
        context.globalAlpha = active ? .6 : .22;
        context.lineWidth = .7;
        context.beginPath();
        context.moveTo(label.x, label.y);
        context.lineTo(edgeX, textY - 4);
        context.stroke();
        context.globalAlpha = .94;
        context.fillStyle = paper;
        context.fillRect(textX - 5, textY - 15, textWidth + 10, 22);
        context.globalAlpha = active ? 1 : .72;
        context.fillStyle = active ? label.field.color : ink;
        context.fillText(text, textX, textY);
        if (active) {
          context.fillStyle = label.field.color;
          context.beginPath();
          context.arc(label.x, label.y, 3, 0, Math.PI * 2);
          context.fill();
        }
        labelBounds.push({ x: textX - 7, y: textY - 19, width: textWidth + 14, height: 28, index: label.index });
      });
    }
    context.globalAlpha = 1;
  }

  function shouldAnimate() { return !paused && inView && !document.hidden && !pointer?.dragging; }

  function frame(now) {
    frameId = 0;
    if (!shouldAnimate()) return;
    if (lastTime) yaw += Math.min((now - lastTime) / 1000, .05) * .065;
    lastTime = now;
    if (now - lastPaint >= 32) { draw(); lastPaint = now; }
    frameId = requestAnimationFrame(frame);
  }

  function syncAnimation() {
    if (shouldAnimate()) {
      if (!frameId) { lastTime = 0; frameId = requestAnimationFrame(frame); }
    } else if (frameId) {
      cancelAnimationFrame(frameId);
      frameId = 0;
      lastTime = 0;
    }
  }

  function stopRotation() {
    paused = true;
    updatePause();
    syncAnimation();
  }

  function selectField(index, userInitiated = true) {
    selected = index;
    const field = fields[index];
    buttons.forEach(button => {
      const active = button.dataset.field === field.id;
      button.setAttribute('aria-pressed', String(active));
    });
    const heading = document.createElement('h3');
    heading.textContent = field.name;
    const description = document.createElement('p');
    description.textContent = field.description;
    detail.replaceChildren(heading, description);
    link.href = field.href || `publications/?topic=${encodeURIComponent(field.topic)}`;
    link.textContent = field.href ? 'Explore research software' : 'Explore related publications';
    canvas.setAttribute('aria-label', `Research fields in three dimensions. ${field.name} selected. Use the field buttons below for descriptions and links.`);
    if (userInitiated) stopRotation();
    draw();
  }

  function resize() {
    const bounds = canvas.getBoundingClientRect();
    width = bounds.width;
    height = bounds.height;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function localPosition(event) {
    const bounds = canvas.getBoundingClientRect();
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  }

  function hitLabel(position) {
    return labelBounds.find(label => position.x >= label.x && position.x <= label.x + label.width && position.y >= label.y && position.y <= label.y + label.height);
  }

  buttons.forEach(button => {
    const index = fields.findIndex(field => field.id === button.dataset.field);
    if (index < 0) return;
    button.style.setProperty('--field-color', fields[index].color);
    button.setAttribute('aria-controls', 'knowledge-detail');
    button.addEventListener('click', () => selectField(index));
  });
  controls.addEventListener('focusin', stopRotation);
  canvas.addEventListener('focus', stopRotation);
  pause.addEventListener('click', () => {
    paused = !paused;
    updatePause();
    syncAnimation();
  });

  canvas.addEventListener('pointerdown', event => {
    if (!event.isPrimary || event.button !== 0) return;
    pointer = { id: event.pointerId, type: event.pointerType, startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, dragging: false, moved: false };
  });
  canvas.addEventListener('pointermove', event => {
    if (!pointer || event.pointerId !== pointer.id) {
      canvas.style.cursor = hitLabel(localPosition(event)) ? 'pointer' : 'grab';
      return;
    }
    const dx = event.clientX - pointer.startX;
    const dy = event.clientY - pointer.startY;
    if (Math.hypot(dx, dy) >= 8) pointer.moved = true;
    if (!pointer.dragging) {
      const horizontalTouch = pointer.type !== 'touch' || Math.abs(dx) > Math.abs(dy) * 1.25;
      if (Math.hypot(dx, dy) < 8 || !horizontalTouch) return;
      pointer.dragging = true;
      canvas.setPointerCapture(event.pointerId);
      canvas.classList.add('is-dragging');
      stopRotation();
    }
    if (event.cancelable) event.preventDefault();
    yaw += (event.clientX - pointer.x) * .007;
    if (pointer.type !== 'touch') pitch = Math.max(-.65, Math.min(.65, pitch + (event.clientY - pointer.y) * .005));
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    draw();
  }, { passive: false });

  function endPointer(event) {
    if (!pointer || event.pointerId !== pointer.id) return;
    const dragged = pointer.dragging;
    const moved = pointer.moved || (event.type === 'pointerup' && Math.hypot(event.clientX - pointer.startX, event.clientY - pointer.startY) >= 8);
    pointer = null;
    canvas.classList.remove('is-dragging');
    canvas.style.cursor = 'grab';
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (!dragged && !moved && event.type === 'pointerup') {
      const hit = hitLabel(localPosition(event));
      if (hit) selectField(hit.index);
    }
    syncAnimation();
  }
  function cancelPointer() {
    if (pointer) endPointer({ pointerId: pointer.id, type: 'pointercancel' });
  }
  canvas.addEventListener('pointerup', endPointer);
  canvas.addEventListener('pointercancel', endPointer);
  canvas.addEventListener('lostpointercapture', endPointer);
  canvas.addEventListener('pointerleave', event => {
    if (pointer && !pointer.dragging) endPointer(event);
  });
  canvas.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home'].includes(event.key)) return;
    event.preventDefault();
    stopRotation();
    if (event.key === 'ArrowLeft') yaw -= .12;
    if (event.key === 'ArrowRight') yaw += .12;
    if (event.key === 'ArrowUp') pitch = Math.min(.65, pitch + .1);
    if (event.key === 'ArrowDown') pitch = Math.max(-.65, pitch - .1);
    if (event.key === 'Home') { yaw = -.22; pitch = -.12; }
    draw();
  });

  stage.hidden = false;
  controls.hidden = false;
  selection.hidden = false;
  root.querySelector('.knowledge-fallback')?.setAttribute('hidden', '');
  root.classList.add('knowledge-ready');
  updatePause();
  resize();
  selectField(0, false);
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas);
  window.addEventListener('resize', resize);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      inView = entries[0].isIntersecting;
      syncAnimation();
    }, { threshold: .05 }).observe(stage);
  }
  window.addEventListener('blur', cancelPointer);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelPointer();
    syncAnimation();
  });
  reduced.addEventListener('change', () => {
    if (reduced.matches) stopRotation();
    draw();
  });
  syncAnimation();
})();
