export const milestone2Question =
  '3d xyz plane like a funal shape spiraling down';

export const milestone2Steps = [
  {
    prompt: milestone2Question,
    eyebrow: 'FIRST PASS',
    title: 'Build a 3D funnel centerline',
    formula:
      'Curve((7 - 0.3t) cos(t), 8 - 0.42t, (7 - 0.3t) sin(t), t, 0, 6π)',
    note: 'A descending helix gives the first funnel-like motion.',
    speed: 8,
    kind: 'funnel',
  },
  {
    prompt: 'Use this Möbius Surface as a reference. Make the track a Fibonacci spiral.',
    eyebrow: 'SURFACE REFERENCE',
    title: 'Combine a Möbius ribbon with golden-spiral decay',
    formula:
      'Surface(C(u) + vN(u), u,0,6π, v,-0.45,0.45)   ·   radius ∝ φ⁻²ᵘ⁄π',
    note: 'The width parameter v turns the golden-spiral centerline into a rideable band.',
    speed: 12,
    kind: 'mobius',
  },
  {
    prompt: 'One Surface. Down the Y-axis. End at (0, 0, 0).',
    eyebrow: 'FINAL CONSTRAINTS',
    title: 'One Surface. Down the Y-axis. End at the origin.',
    formula: 'S(6π, v) = (0, 0, 0)',
    note: 'Both the centerline and ribbon width collapse cleanly at the finish.',
    speed: 18,
    kind: 'origin',
  },
] as const;

export const milestone2FinalSurface = [
  'Surface(',
  ' (7(1-u/(6π))((1+√5)/2)^(',
  '  -2(u-4π(1-e^(-u/(4π))))/π)',
  '  +v(1-u/(6π))cos(0.35sin(0.6u)))cos(u),',
  ' 8(1-u/(6π))+v(1-u/(6π))sin(0.35sin(0.6u)),',
  ' (7(1-u/(6π))((1+√5)/2)^(',
  '  -2(u-4π(1-e^(-u/(4π))))/π)',
  '  +v(1-u/(6π))cos(0.35sin(0.6u)))sin(u),',
  ' u,0,6π, v,-0.45,0.45 )',
].join('\n');

export const milestone2FinalSurfacePasteable =
  'Surface((7*(1-u/(6*pi))*((1+sqrt(5))/2)^(-2*(u-4*pi*(1-exp(-u/(4*pi))))/pi)+v*(1-u/(6*pi))*cos(0.35*sin(0.6*u)))*cos(u),8*(1-u/(6*pi))+v*(1-u/(6*pi))*sin(0.35*sin(0.6*u)),(7*(1-u/(6*pi))*((1+sqrt(5))/2)^(-2*(u-4*pi*(1-exp(-u/(4*pi))))/pi)+v*(1-u/(6*pi))*cos(0.35*sin(0.6*u)))*sin(u),u,0,6*pi,v,-0.45,0.45)';

export const milestone2GeoGebraImage =
  'images/roller-coaster/milestone2-geogebra-final.png';
