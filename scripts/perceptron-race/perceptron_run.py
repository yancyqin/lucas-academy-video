"""Race 1: the perceptron. Same predict()/train() as lucas-academy-ai perceptron.html, in plain CPython.
Writes results/perceptron.json."""
import json
import os
import platform
import statistics
import time
import timeit

from pictures import TEST, TRAIN, many_examples


def predict(picture, points):
    total = 0
    for i in range(len(picture)):
        if picture[i] == 1:            # a black square
            total = total + points[i]  # add its points
    return total > 0                   # more than 0: YES


def train(picture, answer, points):
    guess = predict(picture, points)
    if guess == answer:
        return                 # right: change nothing
    if answer == True:
        change = 1             # it is YES: add points
    else:
        change = -1            # it is NO: take points away
    for i in range(len(picture)):
        if picture[i] == 1:    # only the black squares
            points[i] = points[i] + change


def train_until_right(points, examples, max_rounds=200):
    for round_number in range(1, max_rounds + 1):
        mistakes = 0
        for picture, answer in examples:
            if predict(picture, points) != answer:
                mistakes += 1
            train(picture, answer, points)
        if mistakes == 0:
            return round_number
    return None


def race(label, examples, repeats):
    # training: how long it takes to learn from the examples (median of several fresh starts)
    train_times, rounds = [], None
    for _ in range(repeats):
        points = [0] * 400
        t0 = time.perf_counter()
        rounds = train_until_right(points, examples)
        train_times.append(time.perf_counter() - t0)
    points = [0] * 400
    train_until_right(points, examples)
    rows = []
    for name, picture, answer in TEST:
        loops = 20000
        per_call = min(timeit.repeat(lambda: predict(picture, points), number=loops, repeat=5)) / loops
        said = predict(picture, points)
        rows.append({'picture': name, 'answer': answer, 'said': said, 'right': said == answer, 'seconds': per_call})
    seconds = [r['seconds'] for r in rows]
    result = {
        'system': 'Perceptron (Rosenblatt rule), CPython',
        'setting': f'trained on {len(examples)} pictures; Python {platform.python_version()} on {platform.machine()}',
        'training': {'pictures': len(examples), 'rounds': rounds, 'median_seconds': statistics.median(train_times)},
        'right': sum(r['right'] for r in rows), 'n': len(rows),
        'median_seconds': statistics.median(seconds), 'min_seconds': min(seconds), 'max_seconds': max(seconds),
        'rows': rows,
    }
    print(f"{label}: trained on {len(examples)} pictures in {rounds} rounds, {result['training']['median_seconds'] * 1000:.1f} ms")
    for r in rows:
        print(f"  {r['picture']:8} answer {'YES' if r['answer'] else 'NO ':3} said {'YES' if r['said'] else 'NO ':3} "
              f"{'right' if r['right'] else 'WRONG'}  {r['seconds'] * 1e6:.1f} µs")
    print(f"  {result['right']}/{result['n']} right, median {result['median_seconds'] * 1e6:.1f} µs per picture")
    return result


def main():
    out = {'page_12_examples': race('the page (12 examples)', TRAIN, 50),
           'many_examples': race('many examples', many_examples(), 5),
           'machine': platform.platform()}
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(here, 'results', 'perceptron.json'), 'w'), indent=2)


if __name__ == '__main__':
    main()
