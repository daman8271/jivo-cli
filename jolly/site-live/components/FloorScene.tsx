"use client";

// The floor, in 3D. One block per machine — block height is the hours the plan
// puts on it that day, block colour is the oil on it, a beacon blinks where the
// oil is changed, and a green ring means that machine is filling RIGHT NOW.
// The godown is one box inside a wire shell: the shell is the limit (a guess),
// the solid part is what is in it, amber for the share already sold.
//
// Every figure arrives as a prop. Nothing is typed in this file.

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { IDLE_COLOR, SCENE, oilColor } from "../lib/webgl";

export type FloorMachine = {
  name: string;
  hours: number;      // hours the plan puts on it this day
  oilName: string | null;
  litres: number;
  runs: number;
  flushes: number;
  liveNow: boolean;   // on it right now, off the factory app
};

export type FloorProps = {
  machines: FloorMachine[];
  shiftHours: number;       // the longest planned day on any machine — the scale
  storagePct: number;       // physical vs the working limit
  storagePhysicalL: number;
  ceilingL: number;
  peakL: number;
  soldShare: number;        // 0..1 — the share of the godown already billed
  loadsReal: number;
  loadsForecast: number;
  onPick?: (name: string | null) => void;
};

const TRUCK_SLOTS = 5; // a drawing cap, not a figure
const PAD = 2.6;

export default function FloorScene(props: FloorProps) {
  const host = useRef<HTMLDivElement | null>(null);
  const latest = useRef(props);
  latest.current = props;

  useEffect(() => {
    const el = host.current;
    if (!el) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch {
      return; // the gate above should have caught this; never throw into render
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(SCENE.bg);
    scene.fog = new THREE.Fog(SCENE.bg, 34, 78);

    const camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 200);
    camera.position.set(16, 13, 20);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.maxPolarAngle = Math.PI / 2.15;
    controls.minDistance = 8;
    controls.maxDistance = 60;
    controls.target.set(0, 1.5, 0);

    scene.add(new THREE.AmbientLight(SCENE.white, 0.55));
    const key = new THREE.DirectionalLight(SCENE.white, 1.1);
    key.position.set(12, 20, 10);
    scene.add(key);

    // ground + grid
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 40),
      new THREE.MeshStandardMaterial({ color: SCENE.ground, roughness: 1 }),
    );
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);
    const grid = new THREE.GridHelper(60, 30, SCENE.gridMajor, SCENE.gridMinor);
    grid.position.y = 0.01;
    scene.add(grid);

    /* ── machines ─────────────────────────────────────────────── */
    const n = Math.max(1, props.machines.length);
    const blocks: THREE.Mesh[] = [];
    const rings: THREE.Mesh[] = [];
    const beacons: THREE.Mesh[] = [];
    const startX = -((n - 1) * PAD) / 2;

    props.machines.forEach((m, i) => {
      const x = startX + i * PAD;
      const pad = new THREE.Mesh(
        new THREE.BoxGeometry(1.9, 0.14, 3.4),
        new THREE.MeshStandardMaterial({ color: SCENE.pad, roughness: 0.9 }),
      );
      pad.position.set(x, 0.07, -4);
      scene.add(pad);

      const block = new THREE.Mesh(
        new THREE.BoxGeometry(1.5, 1, 2.6),
        new THREE.MeshStandardMaterial({ color: IDLE_COLOR, roughness: 0.55, metalness: 0.08 }),
      );
      block.userData.name = m.name;
      block.position.set(x, 0.5, -4);
      scene.add(block);
      blocks.push(block);

      const ring = new THREE.Mesh(
        new THREE.RingGeometry(1.15, 1.45, 32),
        new THREE.MeshBasicMaterial({ color: SCENE.live, side: THREE.DoubleSide, transparent: true, opacity: 0 }),
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(x, 0.16, -4);
      scene.add(ring);
      rings.push(ring);

      const beacon = new THREE.Mesh(
        new THREE.SphereGeometry(0.16, 12, 12),
        new THREE.MeshBasicMaterial({ color: SCENE.beacon, transparent: true, opacity: 0 }),
      );
      beacon.position.set(x, 2.4, -4);
      scene.add(beacon);
      beacons.push(beacon);
    });

    /* ── the godown ───────────────────────────────────────────── */
    const GW = 9, GD = 6, GH = 4.2;
    const shell = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(GW, GH, GD)),
      new THREE.LineBasicMaterial({ color: SCENE.shell }),
    );
    shell.position.set(9, GH / 2, 4);
    scene.add(shell);

    const limitLine = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(GW * 1.01, 0.01, GD * 1.01)),
      new THREE.LineBasicMaterial({ color: SCENE.limit }),
    );
    scene.add(limitLine);

    const fill = new THREE.Mesh(
      new THREE.BoxGeometry(GW - 0.25, 1, GD - 0.25),
      new THREE.MeshStandardMaterial({ color: SCENE.fillPlain, roughness: 0.9 }),
    );
    scene.add(fill);
    const sold = new THREE.Mesh(
      new THREE.BoxGeometry(GW - 0.2, 1, GD - 0.2),
      new THREE.MeshStandardMaterial({ color: SCENE.sold, roughness: 0.85, transparent: true, opacity: 0.85 }),
    );
    scene.add(sold);

    /* ── trucks at the gate ───────────────────────────────────── */
    const trucks: THREE.Mesh[] = [];
    for (let i = 0; i < TRUCK_SLOTS * 2; i++) {
      const real = i < TRUCK_SLOTS;
      const t = new THREE.Mesh(
        new THREE.BoxGeometry(1.5, 0.9, 0.85),
        new THREE.MeshStandardMaterial({
          color: real ? SCENE.truckReal : SCENE.truckForecast,
          transparent: true,
          opacity: real ? 0.95 : 0.35,
          roughness: 0.7,
        }),
      );
      const k = real ? i : i - TRUCK_SLOTS;
      t.position.set(-12, 0.45, -2 + k * 1.15 + (real ? 0 : 6.4));
      t.visible = false;
      scene.add(t);
      trucks.push(t);
    }

    /* ── picking ──────────────────────────────────────────────── */
    const ray = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const onMove = (e: PointerEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(pointer, camera);
      const hit = ray.intersectObjects(blocks, false)[0];
      renderer.domElement.style.cursor = hit ? "pointer" : "grab";
    };
    const onClick = (e: PointerEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(pointer, camera);
      const hit = ray.intersectObjects(blocks, false)[0];
      latest.current.onPick?.((hit?.object.userData.name as string) ?? null);
    };
    renderer.domElement.addEventListener("pointermove", onMove);
    renderer.domElement.addEventListener("click", onClick);

    /* ── apply the current props to the scene ─────────────────── */
    const apply = () => {
      const p = latest.current;
      const shiftH = Math.max(1, p.shiftHours);

      p.machines.forEach((m, i) => {
        const b = blocks[i];
        if (!b) return;
        const h = Math.max(0.18, (m.hours / shiftH) * 3.4);
        b.scale.y = h;
        b.position.y = (h * 1) / 2;
        (b.material as THREE.MeshStandardMaterial).color.set(m.hours > 0 ? oilColor(m.oilName) : IDLE_COLOR);
        (rings[i].material as THREE.MeshBasicMaterial).opacity = m.liveNow ? 0.9 : 0;
        beacons[i].position.y = h + 0.7;
        beacons[i].userData.on = m.flushes > 0;
      });

      const cap = Math.max(1, p.peakL);
      const fh = Math.max(0.05, Math.min(1.25, p.storagePhysicalL / cap)) * GH;
      const soldH = Math.max(0, Math.min(1, p.soldShare)) * fh;
      const freeH = Math.max(0.02, fh - soldH);

      fill.scale.y = freeH;
      fill.position.set(9, freeH / 2, 4);
      const overFull = p.storagePct >= 100;
      (fill.material as THREE.MeshStandardMaterial).color.set(
        overFull ? SCENE.fillOver : p.storagePct >= 95 ? SCENE.fillHot : p.storagePct >= 80 ? SCENE.fillWarm : SCENE.fillPlain,
      );
      sold.scale.y = Math.max(0.02, soldH);
      sold.position.set(9, freeH + soldH / 2, 4);

      limitLine.position.set(9, (Math.max(1, p.ceilingL) / cap) * GH, 4);

      const nReal = Math.min(TRUCK_SLOTS, p.loadsReal > 0 ? Math.max(1, Math.round((p.loadsReal / 20) + 0.4)) : 0);
      const nFcst = Math.min(TRUCK_SLOTS, p.loadsForecast > 0 ? Math.max(1, Math.round((p.loadsForecast / 20) + 0.4)) : 0);
      trucks.forEach((t, i) => {
        t.visible = i < TRUCK_SLOTS ? i < nReal : i - TRUCK_SLOTS < nFcst;
      });
    };
    apply();

    /* ── loop ─────────────────────────────────────────────────── */
    let raf = 0;
    const clock = new THREE.Clock();
    const tick = () => {
      raf = requestAnimationFrame(tick);
      const t = clock.getElapsedTime();
      beacons.forEach((b) => {
        const on = b.userData.on as boolean;
        (b.material as THREE.MeshBasicMaterial).opacity = on ? 0.35 + 0.55 * (0.5 + 0.5 * Math.sin(t * 5)) : 0;
      });
      controls.update();
      renderer.render(scene, camera);
    };
    tick();

    const onResize = () => {
      if (!el.clientWidth) return;
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
    };
    const ro = new ResizeObserver(onResize);
    ro.observe(el);

    // a lost GPU context is not a crash — stop the loop and leave the canvas
    const onLost = (e: Event) => {
      e.preventDefault();
      cancelAnimationFrame(raf);
    };
    renderer.domElement.addEventListener("webglcontextlost", onLost);

    const applyTimer = setInterval(apply, 400); // pick up prop changes cheaply

    return () => {
      clearInterval(applyTimer);
      cancelAnimationFrame(raf);
      ro.disconnect();
      renderer.domElement.removeEventListener("pointermove", onMove);
      renderer.domElement.removeEventListener("click", onClick);
      renderer.domElement.removeEventListener("webglcontextlost", onLost);
      controls.dispose();
      scene.traverse((o) => {
        const mesh = o as THREE.Mesh;
        mesh.geometry?.dispose?.();
        const mat = mesh.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
        else mat?.dispose?.();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
    // built once; every later change is pushed in by `apply`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.machines.length]);

  return <div ref={host} className="h-[26rem] w-full rounded-xl border border-zinc-800 bg-zinc-950 md:h-[32rem]" />;
}
