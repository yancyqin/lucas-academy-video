"""Keep the owner's words at native speed; add silence at verified punctuation.

These timings are editorial choices for this film, not fixed TTS punctuation
durations. Existing connected speech is never split to manufacture a pause.
"""
from pathlib import Path
import json
import re
import numpy as np
from scipy.signal import resample_poly

SR = 48000
PREVIOUS = Path(__file__).resolve().parents[2].parent / 'lucas-academy-video-data/why-build-together-20261122/english-owner-track-v05'

# Seconds added to existing pauses, after the specified punctuation-bearing word.
EXTRA = {
    'n001': {'bag.': .75},
    'n002': {'dollars.': .45, 'today.': .55},
    'n003': {'easier,': .50},
    'n004': {'clothing,': .08, 'belonging,': .08},
    'n005': {'Instagram,': .14},
    'n006': {'competitions,': .40, 'well,': .30, 'cello,': .60,
             'gear:': .70, 'question.': 1.20},
    'n008': {'pictures,': .15, 'videos:': .18},
    'n009': {'filling,': .16, 'nourishing.': .28, 'food,': .10},
    'n010': {'produce.': .75},
    'n011': {'step.': .30, 'revisions,': .18, 'judgment,': .12,
             'ownership,': .12, 'leadership,': .12},
}


def build_voice(audio, sr, alignment, plan, data):
    previous = json.loads((PREVIOUS / 'placements.json').read_text())
    gain = previous['gain']
    rows = alignment['rows']
    all_words = [{**w, 'id': row['id']} for row in rows for w in row['words']]
    inserts = []
    for i, left in enumerate(all_words[:-1]):
        extra = EXTRA.get(left['id'], {}).get(left['word'].strip(), 0)
        if not extra:
            continue
        right = all_words[i + 1]
        assert re.search(r'[,.:;?!]$', left['word'])
        center = (left['end'] + right['start']) / 2
        lo = round(max(left['start'] + .015, center - .20) * sr)
        hi = round(min(right['end'] - .015, center + .20) * sr)
        window = round(.008 * sr)
        assert hi - lo >= window
        energy = np.convolve(audio[lo:hi] ** 2, np.ones(window) / window, 'valid')
        quiet = lo + int(energy.argmin()) + window // 2
        rms = float(np.sqrt(energy.min()))
        # The low threshold excludes voiced/fricative bridges, even when the
        # written sentence has punctuation. Pick a near-zero sample in that gap.
        assert rms < .0002, (left['id'], left['word'], rms)
        radius = round(.002 * sr)
        cut = quiet - radius + int(np.abs(audio[quiet-radius:quiet+radius]).argmin())
        inserts.append({'after_id': left['id'], 'after_word': left['word'].strip(),
                        'before_word': right['word'].strip(),
                        'source_sample': cut, 'source_second': cut / sr,
                        'rms_8ms': rms, 'edge_amplitude': float(abs(audio[cut])),
                        'existing_gap_estimate': round(right['start'] - left['end'], 4),
                        'added_seconds': extra, 'added_samples_48k': round(extra * SR)})
    assert len(inserts) == sum(len(v) for v in EXTRA.values())
    voice = np.zeros(plan['intro_frames'] * 1600, dtype='float32')
    pieces = []
    group_plans = []
    mapped = {}
    quiet_cuts = list(previous['quiet_cuts'])
    for entry in inserts:
        quiet_cuts.append({'after': entry['after_id'] + ':' + entry['after_word'],
                           'source_second': entry['source_second'],
                           'rms_10ms': entry['rms_8ms'], 'rms_window_ms': 8})
    for group in previous['placements']:
        ids = group['ids']
        a, b = group['source_start_sample'], group['source_end_sample']
        start = group['start']
        if ids == ['n006']:
            start = 51.0
        elif ids == ['n007', 'n008', 'n009']:
            start = 65.1
        events = sorted([e for e in inserts if a < e['source_sample'] < b], key=lambda e: e['source_sample'])
        cuts = [a] + [e['source_sample'] for e in events] + [b]
        output_start = round(start * SR)
        added = 0
        for i, (p, q) in enumerate(zip(cuts, cuts[1:])):
            index = output_start + 2 * (p - a) + added
            chunk = resample_poly(audio[p:q], 2, 1).astype('float32') * gain
            assert len(chunk) == 2 * (q - p)
            voice[index:index+len(chunk)] = chunk
            pieces.append({'ids': ids, 'source_start_sample': p, 'source_end_sample': q,
                           'source_start': p/sr, 'source_end': q/sr,
                           'start': index/SR, 'end': (index+len(chunk))/SR,
                           'seconds': len(chunk)/SR, 'speech_speed': 1.0})
            if i < len(events):
                events[i]['output_start'] = (index + len(chunk)) / SR
                events[i]['output_end'] = events[i]['output_start'] + events[i]['added_seconds']
                added += events[i]['added_samples_48k']
        end = (output_start + 2*(b-a) + added) / SR
        last = next(s for s in plan['scenes'] if s['id'] == ids[-1])
        assert end <= (last['start_frame']+last['frames'])/30 + 1e-6, (ids, end)
        group_plans.append({'ids': ids, 'start': start, 'end': end,
                            'added_pause_seconds': added/SR, 'insertion_count': len(events)})

        def output_time(t):
            return start + t-a/sr + sum(e['added_samples_48k']/SR for e in events if e['source_sample'] <= round(t*sr))

        for row in rows:
            if row['id'] not in ids:
                continue
            words = []
            for word in row['words']:
                x = max(a/sr, min(word['start'], b/sr-.02))
                y = max(x+.02, min(word['end'], b/sr))
                words.append({'word': word['word'], 'start': output_time(x), 'end': output_time(y)})
            mapped[row['id']] = {'id': row['id'], 'text': row['text'], 'words': words,
                                 'source_start': row['start'], 'source_end': row['end']}
    assert all(p['source_end_sample'] == q['source_start_sample'] for p, q in zip(pieces, pieces[1:]))
    assert sum(p['source_end_sample']-p['source_start_sample'] for p in pieces) == len(audio)
    assert all(p['end'] <= q['start']+1e-7 for p, q in zip(pieces, pieces[1:]))
    assert all(p['end'] <= q['start'] for p, q in zip(group_plans, group_plans[1:]))
    before_rows = previous['rows']
    gaps = lambda rs: [{'after': p['id'], 'before': q['id'],
                       'seconds': round(q['words'][0]['start']-p['words'][-1]['end'],4)}
                      for p,q in zip(rs,rs[1:])]
    speech_cues = [{'speech': {'start': r['words'][0]['start'], 'end': r['words'][-1]['end']}}
                   for r in mapped.values()]
    report = {'mode': 'native speech with punctuation pause extension', 'speech_speed': 1.0,
              'source_samples_preserved_once': len(audio), 'no_speech_regenerated': True,
              'added_pause_seconds': round(sum(e['added_seconds'] for e in inserts),4),
              'insertions': inserts, 'groups': group_plans,
              'paragraph_gaps_before': gaps(before_rows), 'paragraph_gaps_after': gaps(list(mapped.values())),
              'connected_sentence_boundaries_preserved': ['n007→n008', 'n008 want.→But', 'n008→n009'],
              'guideline': 'Spend available time at natural punctuation; leave already adequate pauses and connected speech intact; prioritize sentence meaning and picture cues over uniform timing.'}
    (data/'pause-plan.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return voice, pieces, mapped, speech_cues, quiet_cuts, gain
