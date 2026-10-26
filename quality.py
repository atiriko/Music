"""Transparent musical heuristics for comparing generated candidates.

Scores rank measurable properties; they are not a promise of artistic quality.
"""
from dataclasses import replace
import math


def assess(notes):
    melody = sorted((n for n in notes if n.part == 'Melody'), key=lambda n: n.beat)
    if len(melody) < 2:
        return {'score': 0, 'motion': 0, 'breathing': 0, 'development': 0}
    moves = [abs(b.pitch - a.pitch) for a, b in zip(melody, melody[1:])]
    motion = sum(0 < move <= 7 for move in moves) / len(moves)
    repeated = sum(move == 0 for move in moves) / len(moves)
    gaps = [b.beat - a.beat - a.duration for a, b in zip(melody, melody[1:])]
    breathing = min(1, sum(gap > .3 for gap in gaps) / max(1, len(melody) / 8))
    spread = max(n.pitch for n in melody) - min(n.pitch for n in melody)
    development = max(0, 1 - abs(spread - 14) / 24)
    harmonies = {}
    for note in notes:
        if note.part == 'Chords':
            harmonies.setdefault(int((note.beat + .05) // 4), set()).add(note.pitch % 12)
    variety = min(1, len({tuple(sorted(v)) for v in harmonies.values()}) / 4)
    score = 100 * (.4 * motion + .2 * breathing + .2 * development + .2 * variety)
    score -= max(0, repeated - .35) * 25
    return {'score': round(max(0, min(100, score)), 1), 'motion': round(motion, 3),
            'breathing': round(breathing, 3), 'development': round(development, 3)}


def choose(settings, instruments, count=4, new_hook=False):
    from generator import generate
    if type(count) is not int or not 1 <= count <= 8:
        raise ValueError('Compare between one and eight candidates.')
    candidates = []
    for index in range(count):
        seed = (settings.seed + index * 104729) % 1_000_000_000
        candidate = replace(settings, seed=seed, hook_seed=seed if new_hook else settings.hook_seed)
        notes = generate(candidate, instruments)
        report = assess([n for n in notes if instruments.get(n.part)])
        candidates.append((report['score'], -index, candidate, report))
    winner = max(candidates, key=lambda value: value[:2])
    return winner[2], {**winner[3], 'candidates': count,
                       'candidate_scores': [value[0] for value in candidates]}

