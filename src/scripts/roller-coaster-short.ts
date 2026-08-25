export const shortVideoRefinementQuestion =
  'Can we make one continuous shape—faster than a funnel, but slower than a golden spiral?';

export const hybridTurns = 5;
export const hybridContraction = 0.25;

export const hybridSurfaceDisplay = [
  't = u / (10π)',
  'r(u) = 8(1−t)φ^(−0.25u/(2π))',
  'S(u,v) = (',
  ' (r + v(1−t)cosβ)cosu,',
  ' 12(1−t) + v(1−t)sinβ,',
  ' (r + v(1−t)cosβ)sinu )',
  '0 ≤ u ≤ 10π   ·   −0.45 ≤ v ≤ 0.45',
].join('\n');

export const hybridSurfacePasteable =
  'Surface((8*(1-u/(10*pi))*((1+sqrt(5))/2)^(-0.25*u/(2*pi))+v*(1-u/(10*pi))*cos(0.25*sin(0.5*u)))*cos(u),12*(1-u/(10*pi))+v*(1-u/(10*pi))*sin(0.25*sin(0.5*u)),(8*(1-u/(10*pi))*((1+sqrt(5))/2)^(-0.25*u/(2*pi))+v*(1-u/(10*pi))*cos(0.25*sin(0.5*u)))*sin(u),u,0,10*pi,v,-0.45,0.45)';

export const hybridRadius = (u: number) => {
  const phi = (1 + Math.sqrt(5)) / 2;
  const t = u / (hybridTurns * Math.PI * 2);
  return 8 * (1 - t) * Math.pow(phi, (-hybridContraction * u) / (2 * Math.PI));
};

export const hybridSurfacePoint = (u: number, v: number) => {
  const t = u / (hybridTurns * Math.PI * 2);
  const collapse = Math.max(0, 1 - t);
  const radius = hybridRadius(u);
  const beta = 0.25 * Math.sin(0.5 * u);
  const sideways = v * collapse;
  const radial = radius + sideways * Math.cos(beta);
  return {
    x: radial * Math.cos(u),
    y: 12 * collapse + sideways * Math.sin(beta),
    z: radial * Math.sin(u),
  };
};
