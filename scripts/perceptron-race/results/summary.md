# Perceptron race: is this a 7?

Same 10 new 20 × 20 pictures (5 sevens, 5 ones) for everyone. Language models get the picture as 20 lines of # and .
(the same 400 numbers the perceptron reads) and must answer YES or NO. Times are medians per picture.

| System | Setting | Right | End to end | Model only | Notes |
|---|---|---|---|---|---|
| Perceptron, 12 training pictures (the page) | trained on 12 pictures; Python 3.15.1 on arm64 | 6/10 | 4.2 µs | 4.2 µs | learned in 3 rounds, 361.9 µs |
| Perceptron, 419 training pictures | trained on 419 pictures; Python 3.15.1 on arm64 | 10/10 | 4.3 µs | 4.3 µs | learned in 27 rounds, 99 ms |
| Perceptron, 419 training pictures, plain JavaScript | trained on 419 pictures; Node v22.23.1 on arm64 | 10/10 | 374 ns | 374 ns | learned in 27 rounds, 10 ms |
| Perceptron in the web page (Brython) | perceptron.html, 20 × 20 | - | 311.0 µs | 311.0 µs | plain JavaScript: 184 ns |
| Qwen3 8B (local, Ollama), thinking off | qwen3:8b on this Mac, thinking off | 5/10 | 545 ms | 543 ms | cold start (loading the model) 5.84 s; wall 449 ms–723 ms |
| Qwen3 8B (local, Ollama), thinking on | qwen3:8b on this Mac, thinking on (stopped after 2 pictures, about 4 minutes each) | 1/2 | 246.42 s | 246.41 s | wall 238.28 s–254.56 s |
| Claude Fable 5.1 | claude-fable-5-1 via claude -p | 10/10 | 2.49 s | 1.15 s | wall 2.33 s–5.09 s |
| GPT-6-Astra, reasoning low | gpt-6-astra via codex exec, reasoning low | 10/10 | 5.88 s | 4.05 s | wall 4.94 s–6.66 s |
| GPT-6-Astra, reasoning xhigh (default) | gpt-6-astra via codex exec, reasoning xhigh | 3/3 | 6.61 s | 3.77 s | wall 5.47 s–8.54 s |
