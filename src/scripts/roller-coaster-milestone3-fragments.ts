/**
 * The fragments the Milestone 3 build throws off while it works.
 *
 * They are grouped in the order the work actually happened — the formula
 * first, then the geometry it generates, then the runtime that flies a camera
 * through it, then the checks, then the deploy. The word cloud emits them in
 * that order, so the middle of the video reads as a build moving forward
 * rather than as a bag of technical words.
 *
 * Every string here is real: it is either a line from the Golden Funnel
 * sources, a command the repository actually runs, or a value that run
 * produced.
 */

export type FragmentStage = 'formula' | 'geometry' | 'runtime' | 'testing' | 'deploy';

export interface BuildFragment {
  text: string;
  stage: FragmentStage;
  /** 0 far, 1 middle, 2 near — depth layer for scale, blur and parallax. */
  layer: 0 | 1 | 2;
  /** Rendered as a terminal chip rather than as floating type. */
  chip?: '$' | '✓';
  /** Relative type size within its layer. */
  weight?: number;
}

export const STAGE_ORDER: FragmentStage[] = ['formula', 'geometry', 'runtime', 'testing', 'deploy'];

export const STAGE_LABEL: Record<FragmentStage, string> = {
  formula: 'FORMULA',
  geometry: 'GEOMETRY',
  runtime: 'RUNTIME',
  testing: 'TESTING',
  deploy: 'DEPLOYMENT',
};

export const STAGE_COLOR: Record<FragmentStage, string> = {
  formula: '#8ef0cf',
  geometry: '#9ec8ff',
  runtime: '#ffcf85',
  testing: '#eefff8',
  deploy: '#6fd6ff',
};

export const buildFragments: BuildFragment[] = [
  // --- the formula the ride is made of -------------------------------------
  {text: 'Surface(u, v)', stage: 'formula', layer: 2, weight: 1.32},
  {text: 'u ∈ [−4π, 10π]', stage: 'formula', layer: 1, weight: 1.05},
  {text: 'φ = (1 + √5) / 2', stage: 'formula', layer: 2, weight: 1.18},
  {text: 'taper(u) = 1 − u / 10π', stage: 'formula', layer: 1},
  {text: 'golden(u) = φ^(−u / 2π)', stage: 'formula', layer: 2, weight: 1.12},
  {text: 'r(u) = 8 · taper(u) · golden(u)', stage: 'formula', layer: 1, weight: 1.08},
  {text: 'h(u) = 12 · taper(u)', stage: 'formula', layer: 0},
  {text: 'goldenFunnelProfile(u)', stage: 'formula', layer: 0},

  // --- the geometry it generates -------------------------------------------
  {text: '∂S/∂u × ∂S/∂v', stage: 'geometry', layer: 2, weight: 1.22},
  {text: 'normalize(cross(tangent, localUp))', stage: 'geometry', layer: 1},
  {text: 'C¹ continuity', stage: 'geometry', layer: 2, weight: 1.1},
  {text: 'arc-length parameterization', stage: 'geometry', layer: 0},
  {text: 'CatmullRomCurve3', stage: 'geometry', layer: 1},
  {text: 'TBN frame', stage: 'geometry', layer: 2},
  {text: 'procedural surface sampling', stage: 'geometry', layer: 0},
  {text: 'BufferGeometry', stage: 'geometry', layer: 1},
  {text: 'Float32Array', stage: 'geometry', layer: 0},
  {text: 'DoubleSide', stage: 'geometry', layer: 1},

  // --- the runtime that flies a camera through it --------------------------
  {text: 'goldenFunnelCutsceneFrame(t)', stage: 'runtime', layer: 2, weight: 1.14},
  {text: 'manifoldBlackHoleFrame(t)', stage: 'runtime', layer: 2, weight: 1.12},
  {text: 'Quaternion.slerp()', stage: 'runtime', layer: 1},
  {text: 'camera.matrixWorld', stage: 'runtime', layer: 1},
  {text: 'projectionMatrixInverse', stage: 'runtime', layer: 0},
  {text: 'requestAnimationFrame()', stage: 'runtime', layer: 1},
  {text: 'WebGLRenderer', stage: 'runtime', layer: 2},
  {text: 'depthWrite: false', stage: 'runtime', layer: 0},
  {text: 'pointerlockchange', stage: 'runtime', layer: 1},
  {text: 'deltaTime', stage: 'runtime', layer: 0},
  {text: 'fixed timestep', stage: 'runtime', layer: 1},
  {text: 'frame interpolation', stage: 'runtime', layer: 0},
  {text: 'frustum culling', stage: 'runtime', layer: 1},
  {text: 'first-person camera lock', stage: 'runtime', layer: 2, weight: 1.06},
  {text: 'event horizon', stage: 'runtime', layer: 2, weight: 1.16},
  {text: 'accretion disk', stage: 'runtime', layer: 1, weight: 1.04},

  // --- the checks -----------------------------------------------------------
  {text: 'npm run check', stage: 'testing', layer: 2, chip: '$', weight: 1.1},
  {text: 'tsc --noEmit', stage: 'testing', layer: 1, chip: '$'},
  {text: 'vite build', stage: 'testing', layer: 1, chip: '$'},
  {text: '1153 tests passed', stage: 'testing', layer: 2, chip: '✓', weight: 1.2},
  {text: 'git diff --check', stage: 'testing', layer: 0, chip: '$'},
  {text: 'commit 0b62ae3', stage: 'testing', layer: 2, chip: '✓', weight: 1.08},
  {text: 'origin/main', stage: 'testing', layer: 1, chip: '✓'},

  // --- and out to the world -------------------------------------------------
  {text: 'CI pipeline', stage: 'deploy', layer: 1, chip: '✓'},
  {text: 'artifact SHA-256', stage: 'deploy', layer: 0, chip: '✓'},
  {text: 'content-addressed asset', stage: 'deploy', layer: 1},
  {text: 'cache-control: immutable', stage: 'deploy', layer: 0},
  {text: 'Render deploy', stage: 'deploy', layer: 2, chip: '✓', weight: 1.12},
  {text: 'healthcheck: HTTP 200', stage: 'deploy', layer: 2, chip: '✓', weight: 1.1},
  {text: 'is.lucasacademy.org', stage: 'deploy', layer: 2, weight: 1.26},
];

/**
 * The three lines the core keeps solving while the cloud spreads: the whole
 * surface as one parametric point, the constant it contracts by, and what the
 * finished ride measures — seven turns of curve, of which 4.75 carry a rider
 * and the last 2.25 belong to the cutscene that reaches the origin.
 */
export const coreLines = [
  'S(u, v) = \u27e8 r(u)\u00b7cos u,  h(u),  r(u)\u00b7sin u \u27e9',
  '\u03c6 = 1.6180339887',
  '7 turns \u00b7 4.75 ridden \u00b7 2.25 to the origin',
] as const;
