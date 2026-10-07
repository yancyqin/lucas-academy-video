// Record the Pixel Science Room for 「计算机怎么算 1+1=？」 (FUN-INFORMATICS-01.md §5.1).
//
// Drives the museum headlessly the way whole-person-01/record-chamber.cjs does: the
// dev server's `?debug&manual=1` hook steps the world with a synthetic clock, so
// every frame is exactly 1/30 s of world time; the avatar is hidden; frames go
// straight into ffmpeg (no frame files). Positions come from the museum's own
// model modules, not from numbers copied by hand.
//
//   (inception-space-ui dev server on :8110 — .claude/launch.json "inception-space-8110")
//   PLAYWRIGHT_DIR=/Users/yqin/repo/ai-testing node scripts/fun-informatics-01/record-room.cjs <take> [--seconds N] [--smoke] [--first-person]
//
// takes: entry | bits | pixels | games | nativity | readers | corridor
// --smoke   records 2 s and writes <take>.smoke.png (the first frame) for a look
// output:   public/fun-informatics-01/footage/<take>.mp4 + <take>.json (world seconds
//           at frame 0, so Remotion can map a frame to the painting's loop time)
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require(path.join(process.env.PLAYWRIGHT_DIR || '.', 'node_modules/playwright'));

const UI = process.env.INCEPTION_UI || '/Users/yqin/repo/playground/inception-space-ui';
const ROOM = 'mr-yancys-class-room';
const FPS = 30;
const OUT = path.resolve(__dirname, '../../public/fun-informatics-01/footage');
const args = process.argv.slice(2);
const take = args[0];
const opt = name => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
const flag = name => args.includes(name);
const smoke = flag('--smoke');
const firstPerson = flag('--first-person');
const close = flag('--close'); // painting takes: fill the frame's width with the panel (crops ~0.7 m top and bottom)
const secondsOpt = Number(opt('--seconds') || 0);
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const TAU = Math.PI * 2;
const wrapAngle = a => ((a + Math.PI) % TAU + TAU) % TAU - Math.PI;
/** Museum yaw: 0 faces -Z, heading = (-sin yaw, -cos yaw). */
const yawToward = (from, to) => Math.atan2(-(to.x - from.x), -(to.z - from.z));

async function geometry() {
  const M = await import(path.join(UI, 'src/inception/world/model/museum.js'));
  const H = await import(path.join(UI, 'src/inception/world/model/hallRing.js'));
  const slots = M.MUSEUM_MANIFEST.portalSlots;
  const index = slots.findIndex(s => s.id === ROOM);
  const slot = slots[index];
  const center = M.roomCenterFor(slot, index);
  const floor = M.roomFloorY(slot, index);
  const entry = M.roomEntryPoint(slot, index);
  const stand = M.MUSEUM_MANIFEST.spawn.y;
  const arc = u => H.ringLocalToWorld(u, 0, -H.TUBE_PROFILE.floorDrop + stand);
  return {
    center, floor, entry,
    nativity: { x: center.x + 0, z: center.z + 4 },
    nativityReader: { x: center.x, z: center.z + 3.25 },
    spawn: M.MUSEUM_MANIFEST.spawn,
    door: H.ringDoorReturnPoint(slot.ring.u, slot.ring.side, stand),
    // By the inner wall opposite the door (the door is on the outer wall, side -1): ~4 m back, so the
    // doorway and the nameplate above it both fit a 65-degree frame.
    doorView: H.ringLocalToWorld(slot.ring.u, 1.7, -H.TUBE_PROFILE.floorDrop + stand),
    arc: [0.5, 0.515, 0.53, 0.545, 0.56].map(arc),
    ringRadius: H.HALL_RING.radius,
  };
}

function url(params) {
  const base = 'http://localhost:8110/?world=museum&debug&manual=1&hud=0&fullscreen=0';
  return base + (params ? '&' + params : '');
}

async function main() {
  if (!['entry', 'bits', 'pixels', 'games', 'nativity', 'readers', 'corridor'].includes(take)) {
    console.error('usage: record-room.cjs <entry|bits|pixels|games|nativity|readers|corridor> [--seconds N] [--smoke] [--first-person]');
    process.exit(2);
  }
  fs.mkdirSync(OUT, { recursive: true });
  const geo = await geometry();
  log('geometry', JSON.stringify({ entry: geo.entry, nativity: geo.nativity, door: geo.door }));

  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await ctx.addInitScript(() => {
    try {
      localStorage.setItem('inception.subtitles.v1', '{"shown":false}');
      localStorage.setItem('inception.gravity', 'off');
      localStorage.setItem('inception.quality', 'ultra');
    } catch {}
  });
  const page = await ctx.newPage();
  page.on('pageerror', e => log('pageerror', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') log('console', m.type(), m.text().slice(0, 160)); });

  const params = {
    entry: `inspect=${ROOM}`, nativity: `inspect=${ROOM}`, readers: `inspect=${ROOM}&orb=bits`,
    bits: `inspect=${ROOM}&orb=bits`, pixels: `inspect=${ROOM}&orb=pixels`, games: `inspect=${ROOM}&orb=games`,
    corridor: '',
  }[take];
  await page.goto(url(params), { timeout: 120000 });
  await page.waitForFunction(() => window.__museum?.world, null, { timeout: 120000 });

  // Arrive: in the room (or, for the corridor, in the hall) with no room work pending.
  const wantRoom = take === 'corridor' ? 'corridor' : ROOM;
  for (let i = 0; i < 900; i++) {
    const s = await page.evaluate(() => { const m = window.__museum; m.step(1000 / 30, 2); const p = m.probe(); return { room: p.room, pending: m.world.roomWorkPending(), x: p.x, z: p.z, yaw: p.yaw, t: p.worldSeconds }; });
    if (i % 30 === 0) log('arrive', JSON.stringify(s));
    if (s.room === wantRoom && s.pending === 0 && i > 15) break;
    await sleep(60);
  }
  if (firstPerson) { await page.keyboard.press('KeyV'); log('camera: first person'); }
  // Let the paintings and textures settle for a second of world time.
  await page.evaluate(() => window.__museum.step(1000 / 30, 30));

  // ---- the drive: one function per frame; returns {hold, forward, strafe, lookYaw, lookPitch, screenshot?} ----
  const step = async (intent = {}) => page.evaluate(({ hold, forward, strafe, lookYaw, lookPitch }) => {
    const m = window.__museum, w = m.world;
    const p = m.step(1000 / 30, 1, hold, forward, strafe, lookYaw, lookPitch);
    w.avatarRoot.visible = false;
    w.render();
    return { x: p.x, z: p.z, yaw: p.yaw, pitch: p.pitch, t: p.worldSeconds, bodyY: p.bodyY };
  }, { hold: false, forward: 0, strafe: 0, lookYaw: 0, lookPitch: 0, ...intent });
  // Render and read the canvas in ONE evaluate: a WebGL drawing buffer read in a later task may already
  // have been cleared by the compositor, which showed up as 10-25% random black frames.
  const grabCanvas = () => page.evaluate(() => {
    const w = window.__museum.world;
    w.avatarRoot.visible = false;
    w.render();
    return w.renderer.domElement.toDataURL('image/jpeg', 0.93);
  });
  // The "Press R" prompt and the manual-mode status line are museum UI; the film does not want them.
  // The prompt is re-created as the reader target changes, so it is hidden again before every page frame.
  const hideHud = () => page.evaluate(() => {
    const status = document.getElementById('inception-status'); if (status) status.style.display = 'none';
    for (const el of document.querySelectorAll('body *')) {
      const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
      if (/^Press R\b|^Mouse look|^Manual mode/.test(own)) el.style.setProperty('display', 'none', 'important');
    }
  });
  const grabPage = async () => { await hideHud(); return (await page.screenshot({ type: 'jpeg', quality: 93 })).toString('base64'); };
  // R opens the holographic panel's menu; "Read" opens the scrollable page.
  const openReader = async () => {
    await page.keyboard.press('KeyR');
    await page.evaluate(() => window.__museum.step(1000 / 30, 20));
    const read = page.getByRole('button', { name: /^Read/ });
    if (await read.count()) await read.first().click();
    await page.evaluate(() => window.__museum.step(1000 / 30, 20));
    await page.mouse.move(640, 420);
    await hideHud();
  };

  // Closed-loop controller: fly the body to (x, z) and/or turn to a yaw, over the frames given.
  let probe = await step();
  const toward = async (target, { yaw = null, frames = 90, speedCap = 1 } = {}, onFrame) => {
    for (let i = 0; i < frames; i++) {
      const dx = target.x - probe.x, dz = target.z - probe.z;
      const dist = Math.hypot(dx, dz);
      const heading = { x: -Math.sin(probe.yaw), z: -Math.cos(probe.yaw) };
      const right = { x: -heading.z, z: heading.x };
      const fwd = dx * heading.x + dz * heading.z, side = dx * right.x + dz * right.z;
      const gain = Math.min(1, dist / 2.5) * speedCap; // ease in over the last 2.5 m
      const want = yaw ?? probe.yaw;
      const dyaw = wrapAngle(want - probe.yaw);
      probe = await step({ forward: dist > 0.05 ? gain * fwd / dist : 0, strafe: dist > 0.05 ? gain * side / dist : 0, lookYaw: Math.max(-0.03, Math.min(0.03, dyaw * 0.25)) });
      if (onFrame) await onFrame(probe, i);
    }
    return probe;
  };
  const turnTo = async (yaw, frames, onFrame) => {
    const start = probe.yaw;
    const total = wrapAngle(yaw - start);
    for (let i = 0; i < frames; i++) {
      const eased = 0.5 - 0.5 * Math.cos(Math.PI * ((i + 1) / frames)); // smooth in/out
      const target = start + total * eased;
      probe = await step({ lookYaw: wrapAngle(target - probe.yaw) });
      if (onFrame) await onFrame(probe, i);
    }
  };

  // Rise (zero-g, Space = up thrust) until the body is at `targetY`; damping stops it.
  const riseTo = async (targetY, maxFrames = 300, onFrame) => {
    let prevY = probe.bodyY;
    for (let i = 0; i < maxFrames; i++) {
      const vy = (probe.bodyY - prevY) * FPS;          // m/s, from the last two probes
      const coast = Math.max(0, vy) / 2.2;              // FLIGHT_PARAMS.damping = 2.2 1/s
      prevY = probe.bodyY;
      probe = await step({ hold: probe.bodyY + coast < targetY });
      if (onFrame) await onFrame(probe, i);
      if (i > 30 && Math.abs(vy) < 0.02 && probe.bodyY + coast >= targetY - 0.1) break;
    }
  };
  // The three reader orbs stand exactly where a painting take looks; hide them (the Nativity stays).
  const hideOrbs = () => page.evaluate(() => {
    let n = 0;
    window.__museum.world.scene.traverse(o => { if (/-orb$/.test(o.userData?.propKey || '')) { o.visible = false; n++; } });
    return n;
  });

  // ---- recording sink: frames go to ffmpeg's stdin ----
  const outFile = path.join(OUT, `${take}${close ? '-close' : ''}${smoke ? '.smoke' : ''}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-an',
    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-g', '15', '-keyint_min', '15', '-sc_threshold', '0',
    '-movflags', '+faststart', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
  let frames = 0, firstT = null;
  const marks = [];
  let retried = 0;
  const record = async (grab = grabCanvas) => {
    let data = await grab();
    let buf = Buffer.from(data.includes(',') ? data.split(',')[1] : data, 'base64');
    // A frame that comes out (nearly) black is a glitch of the capture, not of the world: render again.
    for (let tries = 0; buf.length < 12000 && tries < 3; tries++) {
      await page.evaluate(() => { const w = window.__museum.world; w.avatarRoot.visible = false; w.render(); });
      data = await grab();
      buf = Buffer.from(data.includes(',') ? data.split(',')[1] : data, 'base64');
      retried++;
    }
    if (frames === 0) { firstT = probe.t; if (smoke) fs.writeFileSync(outFile.replace(/\.mp4$/, '.png'), buf); }
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    frames++;
    if (frames % 150 === 0) log('frame', frames, 'world t', probe.t.toFixed(2), 'pos', probe.x.toFixed(2), probe.z.toFixed(2), 'yaw', probe.yaw.toFixed(2));
  };
  const hold = async (seconds, grab) => { for (let i = 0; i < Math.round(seconds * FPS); i++) { probe = await step(); await record(grab); } };
  const mark = name => marks.push({ name, frame: frames, worldSeconds: probe.t });

  const limit = smoke ? 2 : secondsOpt || null; // seconds; null = the take's own length

  if (take === 'bits' || take === 'pixels' || take === 'games') {
    const loop = { bits: 181, pixels: 254, games: 88 }[take];
    log('orbs hidden', await hideOrbs());
    if (!firstPerson) { await page.keyboard.press('KeyV'); log('camera: first person'); }
    // The panel is 10.67 x 8 m on the wall at x = centre + 15.88. With a 65-degree vertical field of
    // view, 7.4 m back fills ~85% of the frame height; its centre is 4 m up, so rise to meet it.
    // --close: 5.4 m back fills ~90% of the width; the content sits in the lower middle, so the eye at 3.5 m.
    const stand = { x: geo.center.x + 15.88 - (close ? 5.4 : 7.4), z: probe.z };
    await toward(stand, { yaw: -Math.PI / 2, frames: 150 });
    await riseTo(geo.floor + (close ? 3.5 : 4.0));
    await turnTo(-Math.PI / 2, 20);
    await page.evaluate(() => window.__museum.step(1000 / 30, 30)); // settle
    probe = await step();
    log('standing', JSON.stringify(probe));
    // Step (without recording) to the painting's next loop start, so frame 0 is loop second 0 and a
    // frame number is the loop time x 30 — the seconds in FUN-INFORMATICS-01.md §3 read straight off.
    if (!smoke) {
      const t0 = probe.t;
      const wait = (loop - (t0 % loop)) % loop;
      const steps = Math.round(wait * FPS);
      log('aligning to loop start:', wait.toFixed(2), 's,', steps, 'steps');
      for (let done = 0; done < steps; done += 60) await page.evaluate(n => window.__museum.step(1000 / 30, n), Math.min(60, steps - done));
      probe = await step();
      log('loop-aligned at world t', probe.t.toFixed(3), '-> loop t', (probe.t % loop).toFixed(3));
    }
    await hold(limit ?? loop + 2);
  }
  if (take === 'entry') {
    await riseTo(geo.floor + 1.6);
    mark('arrive-facing-north');
    await hold(limit ?? 3);
    if (!limit) {
      mark('turn-right');
      await turnTo(probe.yaw - Math.PI / 2, 4 * FPS, () => record());
      mark('facing-east');
      await hold(4);
    }
  }
  if (take === 'nativity') {
    const n = geo.nativity, r = 6;
    // Walk (not recorded) from the entry to the orbit start, south of the model, looking at it.
    await toward({ x: n.x, z: n.z + r }, { yaw: yawToward({ x: n.x, z: n.z + r }, n), frames: 240 });
    await turnTo(yawToward(probe, n), 30);
    mark('orbit-start');
    const orbitFrames = limit ? Math.round(limit * FPS) : 20 * FPS;
    for (let i = 0; i < orbitFrames; i++) {
      const a = Math.PI / 2 + Math.PI * (i / (20 * FPS)); // from due south, half a turn
      const target = { x: n.x + r * Math.cos(a), z: n.z + r * Math.sin(a) };
      await toward(target, { yaw: yawToward(target, n), frames: 1, speedCap: 1 });
      await record();
    }
    if (!limit) {
      mark('to-reader');
      const rd = geo.nativityReader;
      await toward({ x: rd.x, z: rd.z + 4.0 }, { yaw: yawToward({ x: rd.x, z: rd.z + 4.0 }, rd), frames: 150 }, () => record());
      await turnTo(yawToward(probe, rd), 20, () => record());
      await hideHud();
      await hold(1, grabPage);
      await openReader();
      mark('reader-open');
      await hold(6, grabPage);
      await page.keyboard.press('KeyR');
      await hold(1, grabPage);
    }
  }
  if (take === 'readers') {
    // Standing at the bits orb (the URL put us there): R opens "From Bits to Meaning"; scroll it slowly.
    await hideHud();
    await hold(1, grabPage);
    await openReader();
    mark('reader-open');
    const seconds = limit ?? 16;
    for (let i = 0; i < Math.round(seconds * FPS); i++) {
      probe = await step();
      if (i > 2 * FPS && i % 2 === 0) { await page.mouse.wheel(0, 5); await hideHud(); }
      await record(grabPage);
    }
    await page.keyboard.press('KeyR');
    await hold(1, grabPage);
  }
  if (take === 'corridor') {
    // From the spawn, up the corridor to the south junction, round the ring to the room's door, face it, hold.
    mark('spawn');
    await hold(1);
    const first = { x: geo.spawn.x, z: geo.ringRadius - 2 };
    await turnTo(yawToward(probe, first), 2 * FPS, () => record());
    await toward(first, { yaw: yawToward(probe, first), frames: 6 * FPS }, () => record());
    // At the junction: turn until the doorway and its nameplate are in view down the ring, and hold.
    const doorOnWall = { x: geo.door.x - Math.sin(geo.door.yaw + Math.PI) * 2.2, z: geo.door.z - Math.cos(geo.door.yaw + Math.PI) * 2.2 };
    await turnTo(yawToward(probe, doorOnWall), 2 * FPS, () => record());
    mark('nameplate-in-view');
    await hold(3);
    // Walk the arc toward it, eyes on the door the whole way.
    for (const p of geo.arc.slice(1, 4)) await toward(p, { yaw: yawToward(probe, doorOnWall), frames: 3 * FPS }, () => record());
    await toward(geo.doorView, { yaw: yawToward(probe, doorOnWall), frames: 3 * FPS }, () => record());
    await turnTo(yawToward(probe, doorOnWall), 1 * FPS, () => record());
    mark('at-door');
    await hold(3);
    // Walk into the doorway; the membrane starts the museum's own transition (the transit tunnel).
    const faceDoor = yawToward(probe, doorOnWall);
    await toward({ x: doorOnWall.x - Math.sin(faceDoor) * 2, z: doorOnWall.z - Math.cos(faceDoor) * 2 }, { yaw: faceDoor, frames: 3 * FPS, speedCap: 0.7 }, () => record());
    mark('through');
    await hold(5);
  }

  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  fs.writeFileSync(outFile.replace(/\.mp4$/, '.json'), JSON.stringify({ take, fps: FPS, frames, firstWorldSeconds: firstT, marks, smoke, blackFrameRetries: retried }, null, 2));
  log('done', take, frames, 'frames ->', outFile, 'first world second', firstT);
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
