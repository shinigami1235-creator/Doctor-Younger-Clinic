/* Product showroom: the clinic's products stand on pedestals in a ring that turns.
   The product facing the viewer is lit and its details show in the card beside it.
   Drag, swipe, the arrow buttons or the keyboard arrows turn the ring. It turns on its own every 8 seconds when left alone.
   If WebGL or a product photo cannot load, the section hides and the product grid below stays. */
import * as THREE from "three";

const section = document.querySelector("[data-showroom]");
const stage = section && section.querySelector("[data-showroom-stage]");
const items = JSON.parse(document.getElementById("showroom-items")?.textContent || "[]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function fallback() { if (section) section.classList.add("is-fallback"); }

function supportsWebGL() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); }
  catch (e) { return false; }
}

if (!section || !items.length || !supportsWebGL()) {
  fallback();
} else {
  start();
}

function radialTexture(inner, outer, stops) {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(128, 128, inner, 128, 128, outer);
  stops.forEach(([at, col]) => grad.addColorStop(at, col));
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  return t;
}

function start() {
  const N = items.length;
  const STEP = (Math.PI * 2) / N;
  const RADIUS = 4.4;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  stage.prepend(renderer.domElement);
  renderer.domElement.setAttribute("aria-hidden", "true");

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  camera.position.set(0, 2.6, 14);
  camera.lookAt(0, 1.0, 0);

  scene.add(new THREE.HemisphereLight(0xfff8ee, 0xd9c9a3, 1.15));
  const key = new THREE.DirectionalLight(0xffffff, 1.4);
  key.position.set(3, 6, 6);
  scene.add(key);
  const spot = new THREE.SpotLight(0xfff1d6, 30, 20, Math.PI / 9, 0.6, 1.4);
  spot.position.set(0, 7, RADIUS + 1.5);
  spot.target.position.set(0, 0, RADIUS);
  scene.add(spot, spot.target);

  // Floor glow and the ring of pedestals
  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(9, 64),
    new THREE.MeshBasicMaterial({ map: radialTexture(10, 128, [[0, "rgba(255,255,255,0.9)"], [1, "rgba(255,255,255,0)"]]), transparent: true })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  scene.add(floor);

  const ring = new THREE.Group();
  scene.add(ring);

  const vignette = radialTexture(60, 126, [[0, "#ffffff"], [1, "#000000"]]);
  const shadowTex = radialTexture(0, 128, [[0, "rgba(42,34,29,0.35)"], [1, "rgba(42,34,29,0)"]]);
  const pedestalMat = new THREE.MeshStandardMaterial({ color: 0xf7f4ee, roughness: 0.55, metalness: 0.05 });
  const rimMat = new THREE.MeshStandardMaterial({ color: 0xb69e59, roughness: 0.3, metalness: 0.8 });
  const loader = new THREE.TextureLoader();
  loader.setCrossOrigin("anonymous");

  const slots = [];
  let failed = false;
  items.forEach((item, i) => {
    const g = new THREE.Group();
    const a = i * STEP;
    g.position.set(Math.sin(a) * RADIUS, 0, Math.cos(a) * RADIUS);

    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.4), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = 0.005;
    const pedestal = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.68, 0.42, 64), pedestalMat);
    pedestal.position.y = 0.21;
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.016, 12, 80), rimMat);
    rim.rotation.x = Math.PI / 2;
    rim.position.y = 0.42;

    const mat = new THREE.MeshBasicMaterial({ transparent: true, alphaMap: vignette, opacity: 1, depthWrite: false });
    const photo = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 1.7), mat);
    photo.position.y = 1.1;   // photo bottom rests on the pedestal top
    loader.load(item.img, (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 4;
      mat.map = tex;
      mat.needsUpdate = true;
    }, undefined, () => { if (!failed) { failed = true; fallback(); } });

    g.add(shadow, pedestal, rim, photo);
    g.userData = { index: i, photo };
    ring.add(g);
    slots.push(g);
  });

  // Card and controls
  const card = section.querySelector("[data-showroom-card]");
  const fields = {
    index: card.querySelector("[data-sr-index]"), name: card.querySelector("[data-sr-name]"),
    short: card.querySelector("[data-sr-short]"), size: card.querySelector("[data-sr-size]"),
    price: card.querySelector("[data-sr-price]"), link: card.querySelector("[data-sr-link]"),
    sizeRow: card.querySelector("[data-sr-size-row]"), priceRow: card.querySelector("[data-sr-price-row]"),
  };
  const dots = section.querySelector("[data-sr-dots]");
  items.forEach((item, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("aria-label", item.name);
    b.addEventListener("click", () => go(i, true));
    dots.appendChild(b);
  });

  let current = 0;
  let target = 0;        // target ring rotation
  let angle = 0;         // current ring rotation
  let lastInteract = 0;

  function show(i) {
    const item = items[i];
    fields.index.textContent = String(i + 1).padStart(2, "0");
    fields.name.textContent = item.name;
    fields.short.textContent = item.short;
    fields.size.textContent = item.size;
    fields.price.textContent = item.price;
    fields.sizeRow.hidden = !item.size;
    fields.priceRow.hidden = !item.price;
    fields.link.href = item.url;
    [fields.name, fields.short].forEach((el) => { el.classList.remove("is-swap"); void el.offsetWidth; el.classList.add("is-swap"); });
    [...dots.children].forEach((d, k) => d.setAttribute("aria-current", k === i ? "true" : "false"));
  }

  function go(i, user) {
    const delta = ((i - current) % N + N + N / 2) % N - N / 2;   // shortest way round
    current = (i + N) % N;
    target -= delta * STEP;
    if (user) lastInteract = performance.now();
    show(current);
  }

  section.querySelector("[data-sr-prev]").addEventListener("click", () => go(current - 1, true));
  section.querySelector("[data-sr-next]").addEventListener("click", () => go(current + 1, true));
  stage.tabIndex = 0;
  stage.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { go(current - 1, true); e.preventDefault(); }
    if (e.key === "ArrowRight") { go(current + 1, true); e.preventDefault(); }
    if (e.key === "Enter") window.location.href = items[current].url;
  });

  // Drag or swipe to turn; a tap on the front product opens it, a tap on another turns to it
  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let dragging = false, startX = 0, startTarget = 0, moved = 0;
  stage.addEventListener("pointerdown", (e) => {
    dragging = true; moved = 0; startX = e.clientX; startTarget = target;
    stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    moved = Math.max(moved, Math.abs(dx));
    target = startTarget + (dx / stage.clientWidth) * Math.PI * 1.2;
    lastInteract = performance.now();
  });
  stage.addEventListener("pointerup", (e) => {
    if (!dragging) return;
    dragging = false;
    if (moved < 6) {
      const r = stage.getBoundingClientRect();
      pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(pointer, camera);
      const hit = ray.intersectObjects(slots.map((s) => s.userData.photo))[0];
      if (hit) {
        const i = hit.object.parent.userData.index;
        if (i === current) window.location.href = items[i].url;
        else go(i, true);
      }
      return;
    }
    // Snap to the nearest product
    const nearest = Math.round(-target / STEP);
    current = ((nearest % N) + N) % N;
    target = -nearest * STEP;
    show(current);
  });

  function resize() {
    const w = stage.clientWidth, h = stage.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.position.z = w / h < 1 ? 18 : 14;
    camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  resize();

  let visible = true;
  new IntersectionObserver((en) => { visible = en[0].isIntersecting; }).observe(stage);

  const camPos = new THREE.Vector3();
  function frame(t) {
    requestAnimationFrame(frame);
    if (!visible) return;
    // Turn to the next product after 8 seconds without input
    if (!reduceMotion && !dragging && t - lastInteract > 8000) { go(current + 1, false); lastInteract = t; }
    angle += (target - angle) * (reduceMotion ? 1 : 0.05);
    ring.rotation.y = angle;
    camera.getWorldPosition(camPos);
    slots.forEach((g) => {
      const p = g.userData.photo;
      // Keep each photo facing the camera, and bring the front one forward
      const world = new THREE.Vector3();
      g.getWorldPosition(world);
      p.lookAt(camPos.x, p.getWorldPosition(new THREE.Vector3()).y, camPos.z);
      const front = (world.z + RADIUS) / (2 * RADIUS);       // 0 at the back, 1 at the front
      const s = 0.7 + 0.45 * Math.pow(front, 3);
      g.scale.setScalar(s);
      p.material.opacity = 0.35 + 0.65 * front;
    });
    renderer.render(scene, camera);
  }
  show(0);
  lastInteract = performance.now();
  requestAnimationFrame(frame);
}
