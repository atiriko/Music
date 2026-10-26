"""Seeded drum grooves. Styles define anchors; variation changes actual hits."""
import numpy as np
from Event import Event

DRUM_STYLES = ('Rock', 'Pop', 'Four on the floor', 'Funk', 'Hip hop', 'Shuffle', 'Half time', 'Breakbeat', 'Metal', 'Drum and bass', 'Techno')
DRUM_COMPLEXITIES = ('Follow complexity', 'Simple', 'Balanced', 'Intricate')
DRUM_FILLS = {'None': 0, 'Every 2 bars': 2, 'Every 4 bars': 4, 'Every 8 bars': 8}
KICKS = {
    'Metal': ((0, .5, 1, 1.5, 2, 2.5, 3, 3.5), (0, .25, 1, 1.5, 2, 2.25, 3, 3.5), (0, .5, .75, 2, 2.5, 2.75)),
    'Drum and bass': ((0, 1.75, 2.5), (0, .75, 2, 2.75), (0, 1.5, 2.5, 3.75)),
    'Techno': ((0, 1, 2, 3),),
    'Rock': ((0, 2), (0, 1.5, 2), (0, 2, 2.5), (0, .5, 2)),
    'Pop': ((0, 1.5, 2.5), (0, 2), (0, 2.5, 3.5), (0, .5, 2.5)),
    'Four on the floor': ((0, 1, 2, 3),),
    'Funk': ((0, .75, 1.5, 2.5), (0, 1.75, 2.5, 3.25), (0, .5, 2, 2.75), (0, 1.5, 2.25, 3.5)),
    'Hip hop': ((0, .75, 2.5), (0, 1.5, 2.75), (0, 1.75, 2.5), (0, .5, 2)),
    'Shuffle': ((0, 2), (0, 1.5, 2), (0, 2, 2.5), (0, .5, 2.5)),
    'Half time': ((0, 1.5, 3), (0, .75, 3.5), (0, 1, 2.75), (0, 1.75, 3)),
    'Breakbeat': ((0, 1.75, 2.5), (0, .5, 2.75, 3.5), (0, .75, 2.25, 3.5), (0, 1.5, 2.5, 3.75)),
}


def generate(scheduler, bars=8, complexity=1, rng=None, style='Rock', fill_every=4):
    if style not in DRUM_STYLES or complexity not in (0, 1, 2):
        raise ValueError('Choose a supported drum style and complexity.')
    rng = rng if rng is not None else np.random.default_rng()
    choose = lambda values: values[int(rng.integers(len(values)))]
    base_kicks = choose(KICKS[style])
    open_hat = choose((.5, 1.5, 2.5, 3.5))

    def hit(bar, beat, pitch, velocity, length=.2):
        if style == 'Shuffle' and abs(beat % 1 - .5) < 1e-8:
            beat += 1 / 6
        duration = min(length, 4 - beat) * scheduler.tempo.quarter
        scheduler.addEvent(Event(9, pitch, (bar * 4 + beat) * scheduler.tempo.quarter,
                                 duration, max(1, min(127, int(velocity)))))

    for bar in range(bars):
        kicks = choose(KICKS[style]) if bar % 2 and rng.random() < .65 else base_kicks
        if complexity == 0 and style not in ('Four on the floor', 'Techno', 'Metal'):
            kicks = (0, choose((1.5, 2, 2.5, 3)))
        for beat in kicks:
            hit(bar, beat, 36, rng.integers(90, 112))
        snares = (2,) if style == 'Half time' else (1, 3)
        for beat in snares:
            hit(bar, beat, 38, rng.integers(85, 106))
            if style in ('Pop', 'Four on the floor', 'Techno') and rng.random() < .6:
                hit(bar, beat, 39, rng.integers(48, 72))
        subdivisions = (4, 8, 16)[complexity]
        for step in range(subdivisions):
            beat = step * 4 / subdivisions
            if beat % 1 and rng.random() < .12:
                continue
            pitch = 46 if complexity > 0 and (abs(beat - open_hat) < 1e-8 or style == 'Techno' and beat % 1 == .5) else 42
            if style == 'Metal' and complexity > 0:
                pitch = 51 if bar % 4 < 2 else 49
            hit(bar, beat, pitch, rng.integers(48, 72), .4 if pitch == 46 else .15)
        # Optional offbeat hits vary even a sparse groove without moving its anchors.
        if complexity == 0:
            hit(bar, choose((.5, 1.5, 2.5, 3.5)), 42, rng.integers(40, 60))
        elif style in ('Funk', 'Hip hop', 'Breakbeat', 'Drum and bass'):
            hit(bar, choose((.75, 1.75, 2.75, 3.75)), 38, rng.integers(32, 50))
        elif rng.random() < .6:
            hit(bar, choose((.5, 1.5, 2.5, 3.5)), 54, rng.integers(40, 62))
        if fill_every and complexity > 0 and bar % fill_every == 0:
            hit(bar, 0, 49, 78, 1)
        if fill_every and complexity > 0 and (bar + 1) % fill_every == 0:
            pitches = choose(((38, 50, 47, 45), (50, 47, 38, 45), (38, 38, 47, 45)))
            beats = (3, 3.25, 3.5, 3.75) if complexity == 2 else (3, 3.5)
            for index, beat in enumerate(beats):
                hit(bar, beat, pitches[index], rng.integers(70, 96))
