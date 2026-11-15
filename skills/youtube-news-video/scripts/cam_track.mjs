#!/usr/bin/env node
/* Camera track check (idea from stazdev/cutaway's cam_track, MIT).
 *
 * check_shotlist.py checks the PLAN; this checks what the 3D camera REALLY does, from the same code the
 * render uses. It prints azimuth, elevation, distance and fov at every beat (and every 0.5 s with --dense)
 * and flags beats that are "parked": the camera barely changed side, height or distance since the last beat.
 *
 * Contract (set up in step 3): every 3D scene's camera comes from a pure function in
 *   anim/src/three/cameraPaths.ts
 *   export const CAMERAS: Record<string, (frame: number, fps: number) =>
 *       {position: [number, number, number], target: [number, number, number], fov: number}>
 * keyed by scene id, frame local to the scene. CameraRig calls CAMERAS[id](frame, fps); nothing else moves the camera.
 *
 * Usage (from the project root; uses tsx through npx to load the TypeScript file):
 *   node <skill>/scripts/cam_track.mjs anim [--dense] [--min-az 10] [--min-el 5] [--min-dist 0.12]
 * Exit code 1 if any beat is parked. Every number printed is MEASURED from the camera functions.
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
if (process.env.CAM_TRACK_INNER) {
  // ---- inner run (inside tsx): load the camera functions and measure ----
  const [anim] = args;
  const opt = JSON.parse(process.env.CAM_TRACK_INNER);
  const tl = JSON.parse(readFileSync(join(anim, 'src/data/timeline.json'), 'utf8'));
  const { CAMERAS } = await import(pathToFileURL(resolve(anim, 'src/three/cameraPaths.ts')).href);
  const fps = tl.fps;
  const pose = (fn, f) => {
    const c = fn(f, fps), d = c.position.map((v, i) => v - c.target[i]);
    const dist = Math.hypot(...d);
    return { az: (Math.atan2(d[0], d[2]) * 180) / Math.PI, el: (Math.asin(d[1] / dist) * 180) / Math.PI, dist, fov: c.fov };
  };
  const angDiff = (a, b) => Math.abs(((a - b + 540) % 360) - 180);
  let parked = 0, checked = 0;
  for (const s of tl.scenes) {
    const fn = CAMERAS[s.id];
    if (!fn) continue;
    const marks = [['start', 0], ...Object.entries(s.beats || {}).sort((a, b) => a[1] - b[1])];
    if (opt.dense) for (let f = 0; f < s.durationInFrames; f += Math.round(fps / 2)) marks.push([`+${(f / fps).toFixed(1)}s`, f]);
    marks.sort((a, b) => a[1] - b[1]);
    console.log(`\n${s.id}  (${(s.startFrame / fps).toFixed(2)}s, ${(s.durationInFrames / fps).toFixed(1)}s)`);
    console.log('  mark            t(s)    az°    el°    dist    fov   change');
    let prev = null;
    for (const [name, f] of marks) {
      const p = pose(fn, f), isBeat = !name.startsWith('+');
      let note = '';
      if (prev && isBeat && name !== 'start') {
        checked++;
        const dAz = angDiff(p.az, prev.az), dEl = Math.abs(p.el - prev.el), dD = Math.abs(p.dist - prev.dist) / prev.dist;
        const dFov = Math.abs(p.fov - prev.fov) / prev.fov;
        const moved = dAz >= opt.minAz || dEl >= opt.minEl || dD >= opt.minDist || dFov >= opt.minDist;
        note = `Δaz ${dAz.toFixed(0)}° Δel ${dEl.toFixed(0)}° Δdist ${(dD * 100).toFixed(0)}%` + (moved ? '' : '  <-- PARKED');
        if (!moved) parked++;
      }
      console.log(`  ${name.padEnd(14)} ${((s.startFrame + f) / fps).toFixed(2).padStart(6)} ${p.az.toFixed(0).padStart(6)} ${p.el.toFixed(0).padStart(6)} ${p.dist.toFixed(2).padStart(7)} ${p.fov.toFixed(0).padStart(5)}   ${note}`);
      if (isBeat) prev = p;
    }
  }
  console.log(`\n${checked} beat changes checked, ${parked} parked (thresholds: az ${opt.minAz}°, el ${opt.minEl}°, distance/fov ${opt.minDist * 100}%).`);
  process.exit(parked ? 1 : 0);
} else {
  // ---- outer run: parse options, re-run this file under tsx ----
  const anim = args.find((a) => !a.startsWith('--')) || 'anim';
  const num = (k, d) => { const i = args.indexOf(k); return i >= 0 ? parseFloat(args[i + 1]) : d; };
  const opt = { dense: args.includes('--dense'), minAz: num('--min-az', 10), minEl: num('--min-el', 5), minDist: num('--min-dist', 0.12) };
  for (const f of ['src/data/timeline.json', 'src/three/cameraPaths.ts'])
    if (!existsSync(join(anim, f))) { console.error(`Missing ${join(anim, f)} (see the contract at the top of this script).`); process.exit(2); }
  const r = spawnSync('npx', ['--yes', 'tsx', new URL(import.meta.url).pathname, anim], {
    stdio: 'inherit', env: { ...process.env, CAM_TRACK_INNER: JSON.stringify(opt) }, cwd: process.cwd(),
  });
  process.exit(r.status ?? 1);
}
