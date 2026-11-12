// 一片落叶，为什么让卡车急刹车？ — picture. Timeline comes from scripts/leaf-truck/build.py (inputProps).
import React from 'react';
import {AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, registerRoot, staticFile, useCurrentFrame} from 'remotion';

const W = 1920, H = 1080, FPS = 24;
const cyan = '#86f4ff', ice = '#e0faff', amber = '#ffcf8d', rose = '#ff8f9e', mint = '#86f7be', dim = '#8fb3c2';
const font = 'PingFang SC, Hiragino Sans GB, system-ui, sans-serif';
const mono = 'SFMono-Regular, Menlo, PingFang SC, monospace';
const clamp = (n: number) => Math.min(1, Math.max(0, n));
const ease = (n: number) => { const x = clamp(n); return x * x * (3 - 2 * x); };
const fade = (t: number, at: number, d = .5) => ease((t - at) / d);
const pos = (left: number, top: number, width?: number): React.CSSProperties => ({position: 'absolute', left, top, width});

type Shot = {from: number; dur: number; kind: string; [k: string]: any};
type Tag = {from: number; dur: number; en: string; zh: string};
export type Props = {frames: number; shots: Shot[]; tags: Tag[]};

function Bi({en, zh, size = 1, color}: {en: string; zh: string; size?: number; color?: string}) {
  return <span style={{color}}>{en}<span style={{display: 'block', fontSize: `${.66 * size}em`, opacity: .9, fontWeight: 620,
    marginTop: '.18em', letterSpacing: 0}}>{zh}</span></span>;
}

function Surface({children}: {children?: React.ReactNode}) {
  return <AbsoluteFill style={{background: 'radial-gradient(ellipse at 70% 45%, #183f55 0%, #0a2439 45%, #061323 100%)',
    color: ice, fontFamily: font}}>
    <AbsoluteFill style={{backgroundImage: 'linear-gradient(#81e5fa0b 1px,transparent 1px),linear-gradient(90deg,#81e5fa0b 1px,transparent 1px)',
      backgroundSize: '64px 64px'}}/>
    {children}
  </AbsoluteFill>;
}

function Heading({en, zh, t}: {en: string; zh: string; t: number}) {
  const a = fade(t, .1, .45);
  return <div style={{...pos(110, 84, 1700), fontSize: 64, fontWeight: 820, opacity: a, transform: `translateY(${(1 - a) * 10}px)`}}>
    <Bi en={en} zh={zh}/></div>;
}

function Badge({kind}: {kind?: string}) {
  if (!kind) return null;
  const label = kind === 'idea' ? ['THOUGHT EXPERIMENT', '设想'] : ['RECONSTRUCTION · AI-GENERATED', '情景重现 · AI 生成'];
  return <div style={{...pos(W - 960, 48, 910), textAlign: 'right', whiteSpace: 'nowrap', font: `700 22px ${mono}`, color: ice, letterSpacing: 2,
    textShadow: '0 1px 6px #000c'}}>{label[0]}<span style={{marginLeft: 14, letterSpacing: 0, fontFamily: font}}>{label[1]}</span></div>;
}

function Stamp({text}: {text?: string}) {
  if (!text) return null;
  return <div style={{...pos(60, H - 150), padding: '14px 22px', border: `3px dashed ${amber}`, color: amber, background: '#000a',
    font: `760 30px ${font}`, borderRadius: 8}}>{text}</div>;
}

// ------------------------------------------------------------------ footage
function Clip({s, t}: {s: Shot; t: number}) {
  const dur = s.dur / FPS;
  const z0 = s.zoom ? s.zoom[0] + (s.zoom[1] - s.zoom[0]) * ease(t / dur) : 1;
  const j = s.jolt != null && t > s.jolt ? Math.exp(-(t - s.jolt) * 5) : 0;   // hard brake: a lurch that dies away
  const jx = s.jolt != null && t > s.jolt ? j * 34 * Math.sin((t - s.jolt) * 34) : 0;
  const z = z0 * (1 + .05 * j);
  const [fx, fy] = s.focus ?? [50, 50];
  const style: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover',
    transform: `translateX(${jx}px) rotate(${jx * .02}deg) scale(${z})`,
    transformOrigin: `${fx}% ${fy}%`, filter: s.filter};
  return <AbsoluteFill style={{background: '#000'}}>
    {s.still ? <Img src={staticFile(s.still)} style={style}/> :
      <OffthreadVideo src={staticFile(s.src)} trimBefore={Math.round((s.start ?? 0) * FPS)} playbackRate={s.rate ?? 1} muted style={style}/>}
    {s.marks?.map((m: any, i: number) => <Mark key={i} m={m} t={t}/>)}
    {s.labels?.map((m: any, i: number) => <Label key={`l${i}`} m={m} t={t}/>)}
    <Badge kind={s.badge}/>
    <Stamp text={s.stamp}/>
  </AbsoluteFill>;
}

function Mark({m, t}: {m: any; t: number}) {
  const a = fade(t, m.at ?? 0, .3);
  return <div style={{...pos(m.x, m.y), width: m.w, height: m.h, border: `5px ${m.dashed ? 'dashed' : 'solid'} ${m.color ?? rose}`,
    borderRadius: 10, opacity: a, boxShadow: `0 0 22px ${m.color ?? rose}88`}}>
    <div style={{...pos(0, -66), whiteSpace: 'nowrap', font: `800 34px ${font}`, color: m.color ?? rose, textShadow: '0 2px 8px #000'}}>
      {m.en}<span style={{fontSize: 26, marginLeft: 12}}>{m.zh}</span></div>
  </div>;
}

function Label({m, t}: {m: any; t: number}) {
  const a = fade(t, m.at ?? 0, .4);
  return <div style={{...pos(m.x - 400, m.y, 800), textAlign: 'center', opacity: a, transform: `translateY(${(1 - a) * 12}px)`,
    color: m.color ?? amber, textShadow: '0 2px 12px #000, 0 0 4px #000'}}>
    <div style={{font: `900 84px ${font}`, lineHeight: 1}}>{m.en}</div>
    <div style={{font: `800 40px ${font}`, marginTop: 8}}>{m.zh}</div>
    {m.arrow && <div style={{font: `900 56px ${font}`, marginTop: 4}}>↓</div>}
  </div>;
}

// ------------------------------------------------------------------ graphics
function Title({t}: {t: number}) {
  const a = fade(t, .2, .7);
  return <AbsoluteFill style={{background: '#050d14', fontFamily: font, color: ice}}>
    <Img src={staticFile('stills/g2-start.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover',
      filter: 'brightness(.38) saturate(.8) blur(3px)'}}/>
    <div style={{...pos(120, 360, 1680), opacity: a, transform: `translateY(${(1 - a) * 14}px)`}}>
      <div style={{fontSize: 92, fontWeight: 860, lineHeight: 1.08}}>Why did a leaf stop<br/>a self-driving truck?</div>
      <div style={{fontSize: 60, fontWeight: 760, color: amber, marginTop: 26}}>一片落叶，为什么让卡车急刹车？</div>
    </div>
  </AbsoluteFill>;
}

function Brake({on, color}: {on: number; color: string}) {
  return <div style={{width: 92, height: 92, borderRadius: 46, border: `6px solid ${color}`, display: 'grid', placeItems: 'center',
    opacity: on, transform: `scale(${.6 + .4 * on})`, font: `900 30px ${mono}`, color}}>!</div>;
}

function Counter({t}: {t: number}) {
  const n = Math.min(11, Math.floor(clamp((t - 1.4) / 3.6) * 11 + (t > 1.4 ? 1 : 0)));
  return <Surface>
    <Heading en="Hard stops on the same street" zh="同一条路上的急刹车次数" t={t}/>
    <div style={{...pos(110, 330), font: `760 40px ${font}`, color: dim}}><Bi en="Human drivers" zh="人类司机"/></div>
    <div style={{...pos(560, 320), display: 'flex', gap: 18}}><Brake on={fade(t, .8, .3)} color={mint}/></div>
    <div style={{...pos(110, 560), font: `760 40px ${font}`, color: ice}}><Bi en="Driverless truck" zh="无人驾驶卡车"/></div>
    <div style={{...pos(560, 550, 1300), display: 'flex', gap: 18, flexWrap: 'wrap'}}>
      {Array.from({length: 11}, (_, i) => <Brake key={i} on={i < n ? 1 : 0} color={rose}/>)}</div>
    <div style={{...pos(1500, 300), font: `900 150px ${font}`, color: rose, opacity: fade(t, 5.2, .4)}}>×11</div>
    <div style={{...pos(110, 900), font: `600 26px ${mono}`, color: dim}}>up to 11× · 最多十一倍 · AWARD D7.3 §4.8.2</div>
  </Surface>;
}

function Cargo({t}: {t: number}) {
  const jolt = ease((t - 1.0) / .35);
  return <Surface>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      <rect x="360" y="260" width="1200" height="560" rx="16" fill="#0f2c3d" stroke={cyan} strokeWidth="4"/>
      <rect x="1560" y="360" width="190" height="460" rx="18" fill="#123448" stroke={cyan} strokeWidth="4"/>
      {[0, 1, 2].map(i => <g key={i} transform={`translate(${520 + i * 250 + jolt * (180 - i * 30)} ${520 - (i === 2 ? jolt * 40 : 0)}) rotate(${i === 2 ? jolt * 14 : 0})`}>
        <rect width="210" height="210" rx="8" fill="#b8865a" stroke="#6b4a30" strokeWidth="6"/></g>)}
      <rect x="480" y="740" width="820" height="26" fill="#8a6a45"/>
      <text x="960" y="880" fill={amber} fontSize="40" fontWeight="800" textAnchor="middle" opacity={jolt}>cargo lurches forward · 货往前一冲</text>
    </svg>
    <Stamp text="G3 待生成：货箱里货物前冲（Muse）"/>
  </Surface>;
}

function Pallet({t, missed = false}: {t: number; missed?: boolean}) {
  const r = fade(t, .8, .8);
  return <Surface>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      <path d="M0 1080 L760 470 L1160 470 L1920 1080 Z" fill="#1b2a33"/>
      <path d="M958 480 L958 1080" stroke="#e8d27a" strokeWidth="8" strokeDasharray="60 50" opacity=".6"/>
      <g transform="translate(700 700)">
        <rect width="520" height="40" fill="#c49a62"/><rect y="72" width="520" height="40" fill="#b88d55"/>
        {[0, 1, 2].map(i => <rect key={i} x={i * 230} y="40" width="60" height="32" fill="#8d6a3e"/>)}
      </g>
      <g opacity={r}>
        <path d="M1270 700 V812" stroke={amber} strokeWidth="6"/><path d="M1250 700 H1290 M1250 812 H1290" stroke={amber} strokeWidth="6"/>
        <text x="1310" y="772" fill={amber} fontSize="56" fontWeight="900">14.4 cm</text>
      </g>
      <g transform="translate(905 410)" opacity=".8"><rect width="110" height="70" rx="6" fill="#e8eef2"/><rect x="18" y="70" width="74" height="10" fill="#333"/></g>
      {missed && <text x="960" y="980" textAnchor="middle" fill={rose} fontSize="44" fontWeight="900" opacity={fade(t, 1.2, .3)}>NOT DETECTED · 没看见</text>}
    </svg>
    <div style={{...pos(110, 90), font: `800 54px ${font}`}}><Bi en="A euro pallet on the lane" zh="车道上的欧标木托盘"/></div>
    <Stamp text="G4 待生成：车道上的矮木托盘（Muse）"/>
  </Surface>;
}

function Split({t}: {t: number}) {
  const a = fade(t, .6, .3), b = fade(t, 2.2, .3);
  const panel: React.CSSProperties = {...pos(0, 270, W / 2), height: 540, overflow: 'hidden'};
  return <AbsoluteFill style={{background: '#050d14', color: ice, fontFamily: font}}>
    <div style={{...pos(0, 0, W / 2), height: H}}>
      <div style={panel}><Img src={staticFile('stills/g2-start.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover'}}/></div>
      <div style={{...pos(24, 545), width: 860, height: 215, border: `6px solid ${rose}`, borderRadius: 10, opacity: a,
        boxShadow: `0 0 22px ${rose}88`}}/>
      <div style={{...pos(60, 110, 840), font: `900 56px ${font}`, color: rose, opacity: a}}>
        <Bi en="Leaves: obstacle!" zh="落叶：当成障碍"/></div>
    </div>
    <div style={{...pos(W / 2, 0, W / 2), height: H}}>
      <div style={panel}><Img src={staticFile('stills/g4-start.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover'}}/></div>
      <div style={{...pos(44, 562), width: 800, height: 150, border: `5px dashed ${amber}`, borderRadius: 10, opacity: b * .9}}/>
      <div style={{...pos(60, 110, 840), font: `900 56px ${font}`, color: amber, opacity: b}}>
        <Bi en="Pallet: not seen" zh="木托盘：没看见"/></div>
      <div style={{...pos(60, 850, 840), font: `800 40px ${font}`, color: amber, opacity: b}}>14.4 cm</div>
    </div>
    <div style={{...pos(W / 2 - 3, 0), width: 6, height: H, background: cyan}}/>
  </AbsoluteFill>;
}

function Sensor({t}: {t: number}) {
  const x = fade(t, 1.6, .4);
  return <Surface>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      <rect x="760" y="300" width="400" height="120" rx="24" fill="#1a3a4d" stroke={cyan} strokeWidth="5"/>
      <rect x="860" y="190" width="200" height="120" rx="20" fill="#0d1f2b" stroke={cyan} strokeWidth="5"/>
      {[0, 1, 2].map(i => <path key={i} d={`M1070 ${230 + i * 20} q ${120 + i * 60} ${-20} ${240 + i * 120} 0`} fill="none"
        stroke={cyan} strokeWidth="3" opacity={.5 + .5 * Math.sin(t * 4 - i)}/>)}
      <text x="960" y="560" textAnchor="middle" fill={ice} fontSize="56" fontWeight="800">Replace the sensor?</text>
      <text x="960" y="630" textAnchor="middle" fill={dim} fontSize="40" fontWeight="700">换掉传感器？</text>
      <path d="M720 520 L1200 660" stroke={rose} strokeWidth="10" opacity={x}/>
      <text x="960" y="800" textAnchor="middle" fill={mint} fontSize="48" fontWeight="800" opacity={x}>First, log every stop · 先把每次停车记下来</text>
    </svg>
  </Surface>;
}

const STOPS: [string, string, number][] = [
  ['Other vehicles', '别的车', 13], ['Lost localization', '定位丢了', 12], ['Weather', '天气', 9], ['Safety stops', '安全停车', 4],
  ['Other emergency stops', '其他紧急停车', 3], ['Obstacles near the path', '路边障碍', 3], ['Overtaking', '超车', 2], ['Container on the path', '路上有集装箱', 1],
];

function Stops({t}: {t: number}) {
  return <Surface>
    <Heading en="47 stops in 7.9 hours of driving" zh="7.9 小时实际行驶，47 次停车" t={t}/>
    {STOPS.map(([en, zh, n], i) => {
      const g = fade(t, .8 + i * .35, .5);
      return <div key={en} style={{...pos(110, 300 + i * 82, 1700), display: 'flex', alignItems: 'center', gap: 24, opacity: .25 + .75 * g}}>
        <div style={{width: 700, font: `700 32px ${font}`, textAlign: 'right', whiteSpace: 'nowrap'}}>{en}<span style={{fontSize: 26, color: dim, marginLeft: 12}}>{zh}</span></div>
        <div style={{height: 48, width: n * 64 * g, background: i < 3 ? cyan : '#5b8ea3', borderRadius: 6}}/>
        <div style={{font: `800 34px ${mono}`, opacity: g}}>{n}</div>
      </div>;
    })}
    <div style={{...pos(110, 980), font: `600 26px ${mono}`, color: dim}}>AWARD D7.3 §4.8.2 · 2023-08-07 – 09-20</div>
  </Surface>;
}

function Lane({y, label, person, leaves, t, show, stop, verdict}: any) {
  const x = 140 + Math.min(t, 3) / 3 * 900;
  return <g transform={`translate(0 ${y})`}>
    <rect x="120" y="0" width="1680" height="190" rx="14" fill="#16303f" stroke="#2f5568" strokeWidth="3"/>
    <text x="150" y="-22" fill={ice} fontSize="40" fontWeight="800">{label}</text>
    {person && <g transform="translate(1260 40)"><circle cx="30" cy="20" r="20" fill={ice}/><rect x="14" y="44" width="32" height="70" rx="12" fill={ice}/></g>}
    {leaves && [0, 1, 2, 3, 4].map(i => <ellipse key={i} cx={1240 + i * 30} cy={110 + (i % 2) * 22} rx="16" ry="9" fill="#e07b2c" transform={`rotate(${i * 40} ${1240 + i * 30} ${110 + (i % 2) * 22})`}/>)}
    <g transform={`translate(${x} 60)`}><rect width="150" height="80" rx="16" fill="#e8eef2"/><rect x="110" y="14" width="30" height="50" rx="6" fill="#7fb7d6"/></g>
    {show && <text x="1500" y="118" fill={stop ? rose : mint} fontSize="58" fontWeight="900">{stop ? 'STOP' : 'GO'}</text>}
    {show && verdict && <text x="1720" y="118" fill={verdict === 'ok' ? mint : amber} fontSize="58">{verdict === 'ok' ? '✓' : '?!'}</text>}
  </g>;
}

function ABTest({t, reveal}: {t: number; reveal: boolean}) {
  return <Surface>
    <Heading en="Change one thing at a time" zh="每次只改一个地方" t={t}/>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      <Lane y={360} label="A · leaves removed — only the person · 只拿掉落叶" person t={t} show={reveal && t > .4} stop verdict="ok"/>
      <Lane y={690} label="B · person removed — only the leaves · 只拿掉人" leaves t={t} show={reveal && t > 1.2} stop verdict="bad"/>
    </svg>
    {!reveal && <div style={{...pos(0, 960, W), textAlign: 'center', font: `800 46px ${font}`, color: amber, opacity: fade(t, 2.5, .4)}}>
      Which one still stops? · 你猜，哪一次还会停？</div>}
    {reveal && <div style={{...pos(0, 960, W), textAlign: 'center', font: `800 46px ${font}`, color: amber, opacity: fade(t, 2.0, .4)}}>
      B still stops → the leaves are the trigger · 问题出在落叶上</div>}
    <Badge kind="idea"/>
  </Surface>;
}

function Lidar({t}: {t: number}) {
  const pts: React.ReactNode[] = [];
  for (let r = 0; r < 22; r++) for (let c = 0; c < 46; c++) {
    const y = 420 + r * r * 1.25, x = 960 + (c - 23) * (12 + r * 2.4);
    pts.push(<circle key={`${r}-${c}`} cx={x} cy={y} r={1.6 + r * .08} fill={cyan} opacity={.35 + .4 * Math.sin(t * 2 + c * .3 + r)}/>);
  }
  const hit = fade(t, 1.6, .3);
  const leaf = Array.from({length: 26}, (_, i) => [900 + (i * 37 % 140), 690 + (i * 53 % 70)]);
  return <Surface>
    <Heading en="What the lidar sees" zh="激光雷达看到的" t={t}/>
    <svg width={W} height={H} viewBox="0 0 1920 1080">{pts}
      {leaf.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="5" fill={hit > .5 ? rose : amber}/>)}
      <rect x="880" y="670" width="180" height="110" fill="none" stroke={rose} strokeWidth="5" opacity={hit}/>
      <text x="1090" y="720" fill={rose} fontSize="44" fontWeight="900" opacity={hit}>OBSTACLE · 障碍</text>
    </svg>
    <div style={{...pos(110, 930, 1700), font: `800 42px ${font}`, color: amber, opacity: fade(t, 3, .4)}}>
      <Bi en="A missing filter: leaves look like obstacles" zh="少了一道过滤，落叶也像障碍"/></div>
  </Surface>;
}

function Ripple({t}: {t: number}) {
  const items: [string, string, number, number][] = [
    ['The car behind: a near miss', '后车：差点追尾', 380, 330], ['Cargo shifts', '货物移位', 1380, 330], ['About 20% more energy', '多耗电约两成', 880, 820]];
  return <Surface>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      {[0, 1, 2].map(i => <circle key={i} cx="960" cy="560" r={80 + ((t * 120 + i * 140) % 420)} fill="none" stroke={cyan}
        strokeWidth="3" opacity={1 - ((t * 120 + i * 140) % 420) / 420}/>)}
      <circle cx="960" cy="560" r="80" fill="#2a1418" stroke={rose} strokeWidth="6"/>
      <text x="960" y="575" textAnchor="middle" fill={rose} fontSize="40" fontWeight="900">BRAKE</text>
    </svg>
    {items.map(([en, zh, x, y], i) => <div key={en} style={{...pos(x - 260, y - 60, 520), textAlign: 'center', font: `800 44px ${font}`,
      opacity: fade(t, .6 + i * 1.6, .4)}}><Bi en={en} zh={zh}/></div>)}
  </Surface>;
}

function Dial({t}: {t: number}) {
  const a = -60 + 120 * ease((t - 1.0) / 3.5);
  return <Surface>
    <Heading en="Just make it less sensitive?" zh="让它别那么敏感？" t={t}/>
    <svg width={W} height={H} viewBox="0 0 1920 1080">
      <path d="M560 820 A400 400 0 0 1 1360 820" fill="none" stroke="#2f5568" strokeWidth="40"/>
      <path d="M560 820 A400 400 0 0 1 760 474" fill="none" stroke={rose} strokeWidth="40"/>
      <path d="M1160 474 A400 400 0 0 1 1360 820" fill="none" stroke={amber} strokeWidth="40"/>
      <line x1="960" y1="820" x2={960 + 360 * Math.sin(a * Math.PI / 180)} y2={820 - 360 * Math.cos(a * Math.PI / 180)} stroke={ice} strokeWidth="10"/>
      <circle cx="960" cy="820" r="22" fill={ice}/>
    </svg>
    <div style={{...pos(300, 880, 600), font: `800 40px ${font}`, color: rose}}><Bi en="Too sensitive: brakes for leaves" zh="太敏感：为落叶急刹"/></div>
    <div style={{...pos(1150, 880, 600), font: `800 40px ${font}`, color: amber, opacity: fade(t, 3.6, .4)}}><Bi en="Too dull: misses the pallet" zh="太迟钝：看不见托盘"/></div>
  </Surface>;
}

function Goal({t}: {t: number}) {
  const back = fade(t, 3.5, .6);
  return <Surface>
    <div style={{...pos(1060, 260, 760), padding: 40, border: `4px solid ${mint}`, borderRadius: 18, background: '#0d2a2a', font: `800 44px ${font}`,
      opacity: fade(t, .4, .5)}}>
      <div style={{color: mint, fontSize: 30, letterSpacing: 3, fontFamily: mono}}>GOAL · 目标</div>
      <div style={{marginTop: 20}}><Bi en="Leaves: ignore" zh="落叶：可以不管"/></div>
      <div style={{marginTop: 26, color: amber}}><Bi en="Pallets, people: never miss" zh="托盘、行人：一个都不能漏"/></div>
    </div>
    <svg width={W} height={H} viewBox="0 0 1920 1080" style={pos(0, 0)}>
      <path d="M1040 560 C 860 560 820 560 700 560" fill="none" stroke={cyan} strokeWidth="8" strokeDasharray="1000" strokeDashoffset={1000 * (1 - back)}/>
      <path d="M720 530 L690 560 L720 590" fill="none" stroke={cyan} strokeWidth="8" opacity={back}/>
    </svg>
    <div style={{...pos(110, 450, 560), font: `800 46px ${font}`, opacity: back}}><Bi en="What must the truck tell apart?" zh="车要分清哪些东西？"/></div>
  </Surface>;
}

function Fixes({t}: {t: number}) {
  const m = fade(t, 4.5, .8);
  const box = (x: number, en: string, zh: string, at: number) => <div style={{...pos(x, 330 + m * 80, 700), padding: 34, borderRadius: 16,
    border: `4px solid ${cyan}`, background: '#0f2c3d', font: `800 40px ${font}`, opacity: fade(t, at, .4),
    transform: `translateX(${(x < 900 ? 1 : -1) * m * 60}px)`}}><Bi en={en} zh={zh}/></div>;
  return <Surface>
    <Heading en="More than one fix" zh="办法不只一个" t={t}/>
    {box(160, 'Treat leaves and branches as non-obstacles', '把树叶、树枝当作「不是障碍」', .8)}
    {box(1060, 'Add cameras to see low objects', '加摄像头，看清低矮的东西', 2.6)}
    <div style={{...pos(0, 800, W), textAlign: 'center', font: `900 60px ${font}`, color: mint, opacity: m}}>
      <Bi en="Complementing each other" zh="互相补充"/></div>
    <div style={{...pos(110, 990), font: `600 24px ${mono}`, color: dim}}>AWARD D7.3 §4.8.2 (cameras) · §5.8.2.1 (leaves &amp; branches, forklift)</div>
  </Surface>;
}

const WAYS: [string, string][] = [['Divergent', '发散思维'], ['Critical', '批判性思维'], ['Systems', '系统思维'], ['Backward', '逆向思维'], ['Integrative', '综合思维']];

function Together({t}: {t: number}) {
  return <Surface>
    <Heading en="Break it apart, let them complement each other" zh="把大问题拆开，让几种思维互相补充" t={t}/>
    <div style={{...pos(110, 380, 1700), display: 'flex', gap: 26, flexWrap: 'wrap'}}>
      {WAYS.map(([en, zh], i) => { const g = fade(t, .8 + i * .45, .4); return <div key={en} style={{flex: '0 0 300px', padding: '30px 28px',
        borderRadius: 12, border: `2px solid rgba(134,244,255,${.3 + .6 * g})`, background: `rgba(16,53,74,${.5 + .5 * g})`,
        boxShadow: `0 0 ${30 * g}px rgba(134,244,255,.3)`, font: `800 44px ${font}`, opacity: .25 + .75 * g}}><Bi en={en} zh={zh}/></div>; })}
    </div>
  </Surface>;
}

function EndCard({t}: {t: number}) {
  return <AbsoluteFill style={{background: '#050d14', color: ice, fontFamily: font, display: 'grid', placeItems: 'center'}}>
    <div style={{textAlign: 'center', opacity: fade(t, .3, .8)}}>
      <div style={{fontSize: 84, fontWeight: 820, letterSpacing: 2}}>Lucas Academy</div>
      <div style={{fontSize: 34, color: dim, marginTop: 24}}>By Yancy Qin · 作者 Yancy Qin</div>
    </div>
  </AbsoluteFill>;
}

function TagPill({tag, t}: {tag: Tag; t: number}) {
  const a = fade(t, 0, .35) * (1 - fade(t, tag.dur / FPS - .4, .4));
  return <div style={{position: 'absolute', right: 60, bottom: 50, padding: '12px 22px', borderRadius: 30, background: '#0b2533e6', border: `2px solid ${cyan}`,
    color: ice, font: `800 30px ${font}`, opacity: a}}>{tag.en}<span style={{marginLeft: 12, fontSize: 26, color: cyan}}>{tag.zh}</span></div>;
}

function ShotView({s}: {s: Shot}) {
  const t = useCurrentFrame() / FPS;
  switch (s.kind) {
    case 'clip': return <Clip s={s} t={t}/>;
    case 'title': return <Title t={t}/>;
    case 'counter': return <Counter t={t}/>;
    case 'cargo': return <Cargo t={t}/>;
    case 'pallet': return <Pallet t={t} missed={s.missed}/>;
    case 'split': return <Split t={t}/>;
    case 'sensor': return <Sensor t={t}/>;
    case 'stops': return <Stops t={t}/>;
    case 'ab': return <ABTest t={t} reveal={s.reveal}/>;
    case 'lidar': return <Lidar t={t}/>;
    case 'ripple': return <Ripple t={t}/>;
    case 'dial': return <Dial t={t}/>;
    case 'goal': return <Goal t={t}/>;
    case 'fixes': return <Fixes t={t}/>;
    case 'together': return <Together t={t}/>;
    case 'end': return <EndCard t={t}/>;
  }
  return null;
}

function TagView({tag}: {tag: Tag}) {
  return <TagPill tag={tag} t={useCurrentFrame() / FPS}/>;
}

export function LeafTruck({shots, tags}: Props) {
  return <AbsoluteFill style={{background: '#000'}}>
    {shots.map((s, i) => <Sequence key={i} from={s.from} durationInFrames={s.dur}><ShotView s={s}/></Sequence>)}
    {tags.map((g, i) => <Sequence key={`t${i}`} from={g.from} durationInFrames={g.dur}><TagView tag={g}/></Sequence>)}
  </AbsoluteFill>;
}

registerRoot(() => <Composition id="LeafTruck" component={LeafTruck as any} width={W} height={H} fps={FPS}
  durationInFrames={240} defaultProps={{frames: 240, shots: [], tags: []}}
  calculateMetadata={({props}: any) => ({durationInFrames: props.frames})}/>);
