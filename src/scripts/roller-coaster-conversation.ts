export const rollerCoasterQuestions = [
  {
    id: 'formula-suggestions',
    text: "I'm making a roller coaster from formula in xy coordinate plane, any interesting formula suggestions?",
  },
  {
    id: 'make-a-loop',
    text: 'can we have something make a loop?',
  },
  {
    id: 'sketch',
    text: 'something like this',
    attachment: 'images/roller-coaster/user-spiral-sketch-enhanced.jpg',
  },
] as const;

export const firstAnswerFunctions = [
  {
    id: 'parabola',
    title: 'Parabola hill',
    formula: 'y = −0.15x²',
    note: 'one smooth hill',
  },
  {
    id: 'sine',
    title: 'Sine hills',
    formula: 'y = 2 sin(x)',
    note: 'rolling ups and downs',
  },
  {
    id: 'damped',
    title: 'Damped sine',
    formula: 'y = 4e⁻⁰·⁰⁸ˣ sin(x)',
    note: 'hills lose energy',
  },
  {
    id: 'gaussian',
    title: 'Gaussian bump',
    formula: 'y = 5e⁻ˣ²⁄⁴',
    note: 'a very smooth crest',
  },
] as const;

export const loopSummary = {
  title: 'A loop needs parametric equations',
  circle: 'x² + y² = 4',
  x: 'x = 2 sin(t)',
  y: 'y = 2(1 − cos(t))',
  note: 'The track can return through the same x-coordinate.',
} as const;

export const spiralSummary = {
  title: 'Spiral loop — like your sketch',
  x: 'x(t) = (2 + 0.3t) cos(t)',
  y: 'y(t) = (2 + 0.3t) sin(t) − 0.15t',
  note: 'The radius grows while the track gradually exits downward.',
  generatedImage: 'images/roller-coaster/spiral-loop-guide.jpg',
} as const;

