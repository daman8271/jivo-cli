"use client";

// Floor map — the September plan drawn on the factory floor. Ported from the
// August site's FloorScene (three.js + OrbitControls, canvas-sprite labels),
// with the September honesty rules kept: block colour = the oil on the
// machine, blinking beacons = oil changes, see-through trucks = expected
// orders nobody has placed yet, and the godown limit is marked as Daman's
// number (not measured) wherever it appears. Every figure comes through
// props from data/*.json — nothing is typed here. Words are plain by rule:
// see PLAIN-LANGUAGE.md.

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

/** Biggest run on one machine for one day (aggregated by the server page). */
export type OnLine = {
  sku: string; // product name
  head: string;
  oil: string | null; // oil NAME (mapped server-side from the RM code), or null
  pieces: number;
  litres: number;
  runs: number;
  flushes: number; // oil changes on this machine that day
} | null;

/** One plan day, flattened by the server page from data/days/day-NN.json. */
export type FloorDay = {
  n: number;
  date: string;
  weekday: string;
  working: boolean;
  hours: number[]; // hours planned on each machine, LINES order
  onLine: OnLine[];
  util: number; // machines busy %
  madeL: number;
  shippedL: number;
  pct: number; // storage.pct against the godown limit (Daman's number, not measured)
  physicalL: number;
  ceilingL: number;
  headroomL: number; // space left in the godown
  loadsReal: number; // dispatched_real.length — customer-ordered loads
  loadsFcst: number; // dispatched_forecast.length — expected, not ordered yet
  runs: number;
  oilChanges: number; // runs that day with flush_min > 0
  blocked: number; // products stuck for material that day (blocked.length)
  note: string | null;
};

export type OilLegendItem = { name: string; litres: number };

const LABELS = ["JP Machine", "Clear Pack", "10 Head", "6 Head", "Pouch", "Tin Head"];
const TRUCK_SLOTS = 5; // per kind (ordered / expected) — a drawing cap, not a figure
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/* ---------- formatting (hand-rolled so server and client agree) ---------- */

function inr(n: number) {
  const s = Math.round(Math.abs(n)).toString();
  const sign = n < 0 ? "-" : "";
  if (s.length <= 3) return sign + s;
  return sign + s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + s.slice(-3);
}
function shortDate(iso: string) {
  const p = iso.split("-");
  return `${Number(p[2])} ${MONTHS[Number(p[1]) - 1]}`;
}

/* ---------- godown tone (same thresholds for box and text) ---------- */

function tone(pct: number) {
  return pct >= 90 ? "red" : pct >= 75 ? "amber" : "green";
}
const TONE_HEX: Record<string, number> = { red: 0xef4444, amber: 0xf59e0b, green: 0x10b981 };
const TONE_TXT: Record<string, string> = { red: "text-red-400", amber: "text-amber-300", green: "text-emerald-400" };
const TONE_CSS: Record<string, string> = { red: "#f87171", amber: "#fbbf24", green: "#34d399" };

/* ---------- oil → colour (presentation only; keyed on the oil NAME) ---------- */

const OIL_KEY: [string, number][] = [
  ["MUSTARD", 0xeab308],
  ["SUNFLOWER", 0xf97316],
  ["GROUNDNUT", 0xb45309],
  ["SOYABEAN", 0x38bdf8],
  ["RICE BRAN", 0x14b8a6],
  ["SESAME", 0xa78bfa],
  ["SEASAME", 0xa78bfa],
  ["COTTON", 0x94a3b8],
  ["CANOLA", 0x84cc16],
  ["GOLD", 0xfbbf24],
  ["OLIVE", 0x22c55e],
];
const IDLE_HEX = 0x4a4a53;

export function oilColorHex(name: string | null | undefined): number {
  if (!name) return IDLE_HEX;
  const u = name.toUpperCase();
  for (const [k, c] of OIL_KEY) if (u.includes(k)) return c;
  let h = 0;
  for (let i = 0; i < u.length; i++) h = (h * 31 + u.charCodeAt(i)) % 360;
  const c = new THREE.Color();
  c.setHSL(h / 360, 0.55, 0.55);
  return c.getHex();
}
const cssOf = (hex: number) => `#${hex.toString(16).padStart(6, "0")}`;

const FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif";

/* ---------- canvas-texture labels ---------- */

type Label = { canvas: HTMLCanvasElement; tex: THREE.CanvasTexture; sprite: THREE.Sprite; key: string };

function makeLabel(w: number, h: number, worldW: number): Label {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
  sprite.scale.set(worldW, (worldW * h) / w, 1);
  return { canvas, tex, sprite, key: "" };
}

function ctxOf(l: Label) {
  const ctx = l.canvas.getContext("2d");
  if (ctx) {
    ctx.clearRect(0, 0, l.canvas.width, l.canvas.height);
    ctx.textAlign = "center";
  }
  return ctx;
}

/** The floating label over one machine: name, product, pieces and hours, oil, oil changes. */
function drawLineLabel(l: Label, name: string, hours: number, on: OnLine, working: boolean, blocked: number) {
  const idleWord = !working ? "closed" : blocked > 0 ? "waiting for material" : "not running";
  const key = `${name}|${hours.toFixed(1)}|${on && hours > 0 ? on.sku + on.pieces + (on.oil ?? "") + on.flushes : idleWord}`;
  if (l.key === key) return;
  l.key = key;
  const ctx = ctxOf(l);
  if (!ctx) return;
  const w = l.canvas.width / 2;
  ctx.font = `600 40px ${FONT}`;
  ctx.fillStyle = "#a1a1aa";
  ctx.fillText(name, w, 40);
  if (on && hours > 0) {
    const sku = on.sku.length > 26 ? on.sku.slice(0, 25) + "…" : on.sku;
    ctx.font = `700 44px ${FONT}`;
    ctx.fillStyle = on.head === "PREMIUM" ? "#fcd34d" : "#e4e4e7";
    ctx.fillText(sku, w, 90);
    ctx.font = `600 36px ${FONT}`;
    ctx.fillStyle = "#fbbf24";
    ctx.fillText(`${on.pieces.toLocaleString("en-IN")} pcs · ${hours.toFixed(1)} h`, w, 134);
    if (on.oil) {
      const oil = on.oil.length > 24 ? on.oil.slice(0, 23) + "…" : on.oil;
      ctx.font = `600 30px ${FONT}`;
      ctx.fillStyle = cssOf(oilColorHex(on.oil));
      ctx.fillText(`${oil}${on.runs > 1 ? `  +${on.runs - 1} more` : ""}`, w, 170);
    }
    if (on.flushes > 0) {
      ctx.font = `600 28px ${FONT}`;
      ctx.fillStyle = "#fbbf24";
      ctx.fillText(`⚑ ${on.flushes} oil change${on.flushes === 1 ? "" : "s"}`, w, 206);
    }
  } else {
    ctx.font = `700 ${idleWord.length > 12 ? 44 : 60}px ${FONT}`;
    ctx.fillStyle = "#52525b";
    ctx.fillText(idleWord, w, 120);
  }
  l.tex.needsUpdate = true;
}

/** The label over the godown: how full, out of the limit — and that the limit is not measured. */
function drawGodownLabel(l: Label, d: FloorDay, assumed: boolean) {
  const key = `${d.pct}|${d.physicalL}`;
  if (l.key === key) return;
  l.key = key;
  const ctx = ctxOf(l);
  if (!ctx) return;
  const w = l.canvas.width / 2;
  ctx.font = `600 42px ${FONT}`;
  ctx.fillStyle = "#a1a1aa";
  ctx.fillText("GODOWN", w, 50);
  ctx.font = `700 110px ${FONT}`;
  ctx.fillStyle = TONE_CSS[tone(d.pct)];
  ctx.fillText(`${d.pct}% full`, w, 160);
  ctx.font = `500 38px ${FONT}`;
  ctx.fillStyle = "#a1a1aa";
  ctx.fillText(`${inr(d.physicalL)} L of ${inr(d.ceilingL)} L`, w, 216);
  if (assumed) {
    ctx.font = `600 32px ${FONT}`;
    ctx.fillStyle = "#fbbf24";
    ctx.fillText("limit is Daman's number — not measured", w, 262);
  }
  l.tex.needsUpdate = true;
}

/** The label over the truck gate: loads with a customer order, and loads only expected. */
function drawDockLabel(l: Label, real: number, fcst: number) {
  const key = `${real}|${fcst}`;
  if (l.key === key) return;
  l.key = key;
  const ctx = ctxOf(l);
  if (!ctx) return;
  const w = l.canvas.width / 2;
  ctx.font = `600 40px ${FONT}`;
  ctx.fillStyle = "#a1a1aa";
  ctx.fillText("TRUCKS OUT", w, 46);
  ctx.font = `700 44px ${FONT}`;
  ctx.fillStyle = real > 0 ? "#e4e4e7" : "#71717a";
  ctx.fillText(`${inr(real)} truck${real === 1 ? "" : "s"} — customer ordered`, w, 116);
  ctx.font = `600 40px ${FONT}`;
  ctx.fillStyle = fcst > 0 ? "#a78bfa" : "#52525b";
  ctx.fillText(`${inr(fcst)} expected — not ordered yet`, w, 172);
  l.tex.needsUpdate = true;
}

/* ---------- the scene ---------- */

type Handle = { setDay: (d: FloorDay) => void };

export default function FloorSepScene({
  days,
  shiftH,
  ceilingAssumed,
  oilLegend,
}: {
  days: FloorDay[];
  shiftH: number; // worked out server-side from the day files (max planned machine hours)
  ceilingAssumed: boolean; // the godown limit is Daman's number, not measured
  oilLegend: OilLegendItem[];
}) {
  const mountRef = useRef<HTMLDivElement>(null);
  const handleRef = useRef<Handle | null>(null);
  const daysRef = useRef(days);
  daysRef.current = days;

  const [day, setDay] = useState(1);
  const [playing, setPlaying] = useState(false);
  const [noWebGL, setNoWebGL] = useState(false);

  const d = days[day - 1] ?? days[0];

  /* build once */
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      setNoWebGL(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(mount.clientWidth || 800, mount.clientHeight || 500);
    renderer.setClearColor(0x09090b, 1);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x09090b, 150, 340);

    const camera = new THREE.PerspectiveCamera(40, 16 / 9, 0.5, 400);
    camera.position.set(0, 38, 47);

    const BASE_FOV = 40;
    const H_FOV = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(BASE_FOV) / 2) * (16 / 9));
    const applySize = () => {
      const w = mount.clientWidth,
        h = mount.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h;
      const wide = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(H_FOV / 2) / camera.aspect));
      camera.fov = THREE.MathUtils.clamp(Math.max(BASE_FOV, wide), BASE_FOV, 78);
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    };
    applySize();

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 3.5, -3);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 30;
    controls.maxDistance = 130;
    controls.minPolarAngle = 0.15;
    controls.maxPolarAngle = 1.45;
    controls.update();

    scene.add(new THREE.AmbientLight(0xffffff, 0.9));
    scene.add(new THREE.HemisphereLight(0x9ca3af, 0x09090b, 1.0));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.1);
    keyLight.position.set(22, 34, 26);
    scene.add(keyLight);
    const fill = new THREE.DirectionalLight(0xffffff, 0.6);
    fill.position.set(-26, 18, -20);
    scene.add(fill);

    /* floor + grid */
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(84, 56),
      new THREE.MeshStandardMaterial({ color: 0x101014, roughness: 1, metalness: 0 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.z = -8;
    scene.add(floor);

    const grid = new THREE.GridHelper(84, 42, 0x2a2a31, 0x1b1b20);
    grid.position.set(0, 0.02, -8);
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.55;
    scene.add(grid);

    /* six machine blocks — height = planned hours, colour = the oil on the machine */
    const GREY = new THREE.Color(IDLE_HEX);
    const blockGeo = new THREE.BoxGeometry(5.4, 1, 4.2);
    blockGeo.translate(0, 0.5, 0);
    const padGeo = new THREE.BoxGeometry(7, 0.4, 5.6);
    const cageBox = new THREE.BoxGeometry(5.8, 8, 4.6);
    const cageGeo = new THREE.EdgesGeometry(cageBox);
    cageBox.dispose();
    const cageMat = new THREE.LineBasicMaterial({ color: 0x232327 });

    const blocks: THREE.Mesh<THREE.BoxGeometry, THREE.MeshStandardMaterial>[] = [];
    const beacons: THREE.Mesh<THREE.OctahedronGeometry, THREE.MeshStandardMaterial>[] = [];
    const lineLabels: Label[] = [];
    const beaconGeo = new THREE.OctahedronGeometry(0.5);
    for (let i = 0; i < 6; i++) {
      const x = (i - 2.5) * 9;
      const pad = new THREE.Mesh(padGeo, new THREE.MeshStandardMaterial({ color: 0x232328, roughness: 0.9 }));
      pad.position.set(x, 0.2, 0);
      scene.add(pad);

      const cage = new THREE.LineSegments(cageGeo, cageMat); // the full shift, for scale
      cage.position.set(x, 4.4, 0);
      scene.add(cage);

      const block = new THREE.Mesh(
        blockGeo,
        new THREE.MeshStandardMaterial({
          color: GREY.clone(),
          emissive: GREY.clone(),
          emissiveIntensity: 0,
          roughness: 0.55,
          metalness: 0.08,
        })
      );
      block.position.set(x, 0.4, 0);
      block.scale.y = 1.1;
      scene.add(block);
      blocks.push(block);

      // oil-change beacon — blinks on days this machine changes oil
      const beacon = new THREE.Mesh(
        beaconGeo,
        new THREE.MeshStandardMaterial({
          color: 0xfbbf24,
          emissive: new THREE.Color(0xfbbf24),
          emissiveIntensity: 1.2,
          roughness: 0.4,
        })
      );
      beacon.position.set(x, 1.1, 2.9);
      beacon.visible = false;
      scene.add(beacon);
      beacons.push(beacon);

      const lab = makeLabel(512, 240, 8.6);
      lab.sprite.material.depthTest = false;
      lab.sprite.renderOrder = 10;
      lab.sprite.position.set(x, 6.4, -2.6);
      scene.add(lab.sprite);
      lineLabels.push(lab);
    }

    /* godown at the back — its limit is Daman's number, not measured (labelled so) */
    const G_W = 28,
      G_H = 9,
      G_D = 10,
      G_Z = -21;
    const shell = new THREE.Mesh(
      new THREE.BoxGeometry(G_W, G_H, G_D),
      new THREE.MeshStandardMaterial({ color: 0x18181b, transparent: true, opacity: 0.14, side: THREE.BackSide, roughness: 1 })
    );
    shell.position.set(0, G_H / 2, G_Z);
    scene.add(shell);

    const shellBox = new THREE.BoxGeometry(G_W, G_H, G_D);
    const shellEdges = new THREE.LineSegments(new THREE.EdgesGeometry(shellBox), new THREE.LineBasicMaterial({ color: 0x3f3f46 }));
    shellBox.dispose();
    shellEdges.position.copy(shell.position);
    scene.add(shellEdges);

    const fillGeo = new THREE.BoxGeometry(G_W - 0.6, 1, G_D - 0.6);
    fillGeo.translate(0, 0.5, 0);
    const godownFill = new THREE.Mesh(
      fillGeo,
      new THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: new THREE.Color(0x10b981),
        emissiveIntensity: 0.18,
        transparent: true,
        opacity: 0.5,
        roughness: 0.6,
      })
    );
    godownFill.position.set(0, 0.03, G_Z);
    godownFill.scale.y = 0.1;
    scene.add(godownFill);

    /* red line at the top of the godown limit */
    const ringMat = new THREE.MeshStandardMaterial({ color: 0xef4444, emissive: new THREE.Color(0xef4444), emissiveIntensity: 0.7, roughness: 0.6 });
    const ringX = new THREE.BoxGeometry(G_W + 0.5, 0.18, 0.18);
    const ringZ = new THREE.BoxGeometry(0.18, 0.18, G_D + 0.5);
    const ring = new THREE.Group();
    for (const z of [-(G_D / 2), G_D / 2]) {
      const b = new THREE.Mesh(ringX, ringMat);
      b.position.set(0, 0, z);
      ring.add(b);
    }
    for (const x of [-(G_W / 2), G_W / 2]) {
      const b = new THREE.Mesh(ringZ, ringMat);
      b.position.set(x, 0, 0);
      ring.add(b);
    }
    ring.position.set(0, G_H, G_Z);
    scene.add(ring);

    const godownLabel = makeLabel(720, 300, 13);
    godownLabel.sprite.material.depthTest = false;
    godownLabel.sprite.renderOrder = 10;
    godownLabel.sprite.position.set(0, G_H + 4.6, G_Z);
    scene.add(godownLabel.sprite);

    /* truck gate at the front — ordered loads solid, expected loads see-through */
    const DOCK_Z = 15;
    const dock = new THREE.Mesh(new THREE.BoxGeometry(40, 0.6, 6.5), new THREE.MeshStandardMaterial({ color: 0x141417, roughness: 1 }));
    dock.position.set(0, 0.3, DOCK_Z + 1.5);
    scene.add(dock);

    const cargoGeo = new THREE.BoxGeometry(2.6, 1.9, 3.6);
    const cabGeo = new THREE.BoxGeometry(2.3, 1.4, 1.5);
    const realCargoMat = new THREE.MeshStandardMaterial({ color: 0xa1a1aa, roughness: 0.75, metalness: 0.05 });
    const realCabMat = new THREE.MeshStandardMaterial({ color: 0x52525b, roughness: 0.75, metalness: 0.05 });
    const ghostCargoMat = new THREE.MeshStandardMaterial({ color: 0x8b5cf6, roughness: 0.85, transparent: true, opacity: 0.26, depthWrite: false });
    const ghostCabMat = new THREE.MeshStandardMaterial({ color: 0x6d28d9, roughness: 0.85, transparent: true, opacity: 0.2, depthWrite: false });

    const mkTruck = (cargoMat: THREE.Material, cabMat: THREE.Material, x: number) => {
      const g = new THREE.Group();
      const cargo = new THREE.Mesh(cargoGeo, cargoMat);
      cargo.position.y = 1.35;
      const cab = new THREE.Mesh(cabGeo, cabMat);
      cab.position.set(0, 1.1, -2.55);
      g.add(cargo, cab);
      g.position.set(x, 0, DOCK_Z - 3.6);
      g.scale.setScalar(0);
      g.visible = false;
      scene.add(g);
      return g;
    };
    const realTrucks: THREE.Group[] = [];
    const ghostTrucks: THREE.Group[] = [];
    for (let i = 0; i < TRUCK_SLOTS; i++) realTrucks.push(mkTruck(realCargoMat, realCabMat, -17.5 + i * 4.6));
    for (let i = 0; i < TRUCK_SLOTS; i++) ghostTrucks.push(mkTruck(ghostCargoMat, ghostCabMat, 17.5 - i * 4.6));

    const dockLabel = makeLabel(720, 240, 10);
    dockLabel.sprite.material.depthTest = false;
    dockLabel.sprite.renderOrder = 10;
    dockLabel.sprite.position.set(0, 2.6, DOCK_Z + 4.5);
    scene.add(dockLabel.sprite);

    /* animated state, lerped toward the selected day */
    const anim = { hours: new Array(6).fill(0) as number[], fill: 0, real: 0, fcst: 0 };
    const targetOil: THREE.Color[] = Array.from({ length: 6 }, () => GREY.clone());
    const flushes = new Array(6).fill(0) as number[];
    let target: FloorDay = daysRef.current[0];
    let snap = true;
    const fillColor = new THREE.Color(0x10b981);
    const tmp = new THREE.Color();

    handleRef.current = {
      setDay: (nd: FloorDay) => {
        target = nd;
        for (let i = 0; i < 6; i++) {
          const on = nd.onLine?.[i] ?? null;
          drawLineLabel(lineLabels[i], LABELS[i], nd.hours[i] ?? 0, on, nd.working, nd.blocked ?? 0);
          targetOil[i].setHex(on && (nd.hours[i] ?? 0) > 0 ? oilColorHex(on.oil) : IDLE_HEX);
          flushes[i] = on ? on.flushes : 0;
        }
        drawGodownLabel(godownLabel, nd, ceilingAssumed);
        drawDockLabel(dockLabel, nd.loadsReal, nd.loadsFcst);
      },
    };
    handleRef.current.setDay(daysRef.current[0]);

    const ro = new ResizeObserver(applySize);
    ro.observe(mount);

    /* loop */
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      raf = requestAnimationFrame(tick);
      const dt = Math.min((now - last) / 1000, 0.1);
      last = now;
      const k = snap ? 1 : 1 - Math.exp(-dt * 5);

      for (let i = 0; i < 6; i++) {
        const want = Math.max(0, Math.min(shiftH, target.hours[i] ?? 0));
        anim.hours[i] += (want - anim.hours[i]) * k;
        const h = anim.hours[i];
        const t = h / shiftH;
        const b = blocks[i];
        b.scale.y = 1.1 + t * 6.9;
        tmp.copy(GREY).lerp(targetOil[i], Math.min(1, t * 2.2));
        b.material.color.lerp(tmp, snap ? 1 : 0.2);
        b.material.emissive.copy(b.material.color);
        b.material.emissiveIntensity = 0.55 * t;
        lineLabels[i].sprite.position.y = Math.max(6.4, 0.4 + b.scale.y + 1.6);

        // oil-change beacon — blinks while this day has an oil change on the machine
        const bc = beacons[i];
        const on = target.working && flushes[i] > 0;
        bc.visible = on;
        if (on) {
          const p = Math.sin(now * 0.008 + i * 1.7);
          bc.scale.setScalar(0.85 + 0.3 * p);
          bc.material.emissiveIntensity = 1.2 + 0.9 * p;
          bc.rotation.y += dt * 2.2;
        }
      }

      anim.fill += (Math.max(0, Math.min(100, target.pct)) - anim.fill) * k;
      godownFill.scale.y = Math.max(0.05, (anim.fill / 100) * G_H);
      fillColor.setHex(TONE_HEX[tone(anim.fill)]);
      godownFill.material.color.lerp(fillColor, snap ? 1 : 0.15);
      godownFill.material.emissive.copy(godownFill.material.color);

      anim.real += (Math.min(target.loadsReal, TRUCK_SLOTS) - anim.real) * k;
      anim.fcst += (Math.min(target.loadsFcst, TRUCK_SLOTS) - anim.fcst) * k;
      for (let i = 0; i < TRUCK_SLOTS; i++) {
        const pr = Math.max(0, Math.min(1, anim.real - i));
        realTrucks[i].visible = pr > 0.01;
        realTrucks[i].scale.setScalar(pr);
        const pf = Math.max(0, Math.min(1, anim.fcst - i));
        ghostTrucks[i].visible = pf > 0.01;
        ghostTrucks[i].scale.setScalar(pf);
      }

      snap = false;
      controls.update();
      renderer.render(scene, camera);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      handleRef.current = null;
      controls.dispose();
      scene.traverse((obj) => {
        const o = obj as unknown as { geometry?: THREE.BufferGeometry; material?: THREE.Material | THREE.Material[] };
        o.geometry?.dispose();
        const mat = o.material;
        const list = Array.isArray(mat) ? mat : mat ? [mat] : [];
        for (const m of list) {
          (m as THREE.Material & { map?: THREE.Texture | null }).map?.dispose();
          m.dispose();
        }
      });
      scene.clear();
      renderer.dispose();
      renderer.forceContextLoss();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ?day=12 opens on that day */
  useEffect(() => {
    const q = Number(new URLSearchParams(window.location.search).get("day"));
    if (Number.isFinite(q) && q >= 1 && q <= days.length) setDay(Math.round(q));
  }, [days.length]);

  /* push the selected day into the scene */
  useEffect(() => {
    const h = handleRef.current;
    if (h && days[day - 1]) h.setDay(days[day - 1]);
  }, [day, days]);

  /* one day per second */
  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setDay((n) => (n >= days.length ? 1 : n + 1)), 1000);
    return () => window.clearInterval(id);
  }, [playing, days.length]);

  const t = tone(d.pct);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
        <button
          onClick={() => setPlaying((p) => !p)}
          className="w-24 shrink-0 rounded-md border border-violet-500/40 bg-violet-500/10 px-3 py-2 text-sm font-medium text-violet-300 hover:bg-violet-500/20"
        >
          {playing ? "Pause" : "Play"}
        </button>
        <div className="w-44 shrink-0">
          <div className="text-2xl font-semibold leading-tight tabular-nums">{shortDate(d.date)}</div>
          <div className="text-xs text-zinc-500">
            {d.weekday}
            {d.working ? "" : " — factory closed"}
          </div>
        </div>
        <input
          type="range"
          min={1}
          max={days.length}
          step={1}
          value={day}
          aria-label="Which day of September"
          onChange={(e) => {
            setPlaying(false);
            setDay(Number(e.target.value));
          }}
          className="min-w-[16rem] flex-1 accent-violet-500"
        />
        <div className="shrink-0 text-xs tabular-nums text-zinc-500">
          Day {day} of {days.length} — slide to change the day
        </div>
      </div>

      <div ref={mountRef} className="relative mt-4 h-[420px] w-full overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950 md:h-[560px]">
        <div className="pointer-events-none absolute left-3 top-3 z-10 rounded border border-violet-500/40 bg-violet-950/75 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-violet-300">
          THE COMPUTER&apos;S PLAN · nothing here has happened yet
        </div>
        {noWebGL && (
          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-zinc-500">
            This browser cannot draw the 3D map. The day&apos;s numbers are below.
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-1 text-sm tabular-nums">
        <span className="text-zinc-400">{shortDate(d.date)}</span>
        <span>
          makes <span className="font-semibold text-amber-300">{inr(d.madeL)} L</span>
        </span>
        <span>
          bills <span className="font-semibold text-zinc-100">{inr(d.shippedL)} L</span>
        </span>
        <span>
          machines busy <span className="font-semibold text-zinc-100">{d.util}%</span>{" "}
          <span className="text-zinc-500">of a {shiftH}-hour shift</span>
        </span>
        <span>
          godown <span className={`font-semibold ${TONE_TXT[t]}`}>{d.pct}% full</span>{" "}
          <span className="text-zinc-500">
            ({inr(d.headroomL)} L space left{ceilingAssumed ? " · limit not measured" : ""})
          </span>
        </span>
        <span>
          trucks <span className="font-semibold text-zinc-100">{inr(d.loadsReal)} customer ordered</span>
          <span className="text-violet-300"> + {inr(d.loadsFcst)} expected, not ordered yet</span>
        </span>
        <span>
          oil changes <span className="font-semibold text-amber-300">{d.oilChanges}</span>
        </span>
        <Link href={`/days/${d.n}`} className="text-violet-300 hover:underline">
          see day {d.n} →
        </Link>
      </div>

      {d.note && (
        <div className="mt-2 text-sm text-amber-300/90">
          <span className="text-zinc-500">What the plan decided that day — </span>
          {d.note}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-zinc-800 pt-3 text-xs text-zinc-500">
        <span className="text-zinc-400">Colour = the oil on that machine (its biggest run of the day):</span>
        {oilLegend.map((o) => (
          <span key={o.name} className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-sm align-middle" style={{ backgroundColor: cssOf(oilColorHex(o.name)) }} />
            {o.name}
          </span>
        ))}
      </div>

      <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-zinc-500">
        <span>block height = hours the machine runs that day, out of a {shiftH}-hour shift</span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-zinc-600 align-middle" />
          grey = not running (factory closed, or waiting for material)
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rotate-45 rounded-[2px] bg-amber-400 align-middle" />
          blinking yellow light = an oil change on that machine that day
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-violet-500/40 align-middle" />
          see-through purple truck = expected order — not ordered yet
        </span>
        <span>thin outline = a full {shiftH}-hour shift, for scale</span>
        <span>
          godown colour = how full it is, out of {inr(d.ceilingL)} L
          {ceilingAssumed ? " — Daman's number, not measured" : ""}. The red line is the top.
        </span>
        <span>one truck = one load (up to {TRUCK_SLOTS} of each drawn)</span>
        <span>drag to turn, scroll to zoom</span>
      </div>
    </div>
  );
}
