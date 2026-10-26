"""Seeded phrase registers, informed by role and selected GM instrument.

Ranges are compositional comfort zones for this sample bank, not claims about
the physical limits of acoustic instruments. Whole phrases move by octaves so
scale membership, melodic contour, chord voicing, and bass approaches survive.
"""
from dataclasses import replace
import numpy as np
from Instruments import SOUNDFONT_PROGRAMS

ROLES = {'Melody': (48, 100, 72), 'Chords': (40, 88, 60), 'Bass': (24, 64, 40)}
# Low, high, central register; individual instruments override family defaults.
SPECIAL = {
    8: (60, 108, 84), 9: (72, 108, 90), 10: (60, 108, 84),
    13: (60, 108, 84), 40: (55, 103, 76), 41: (48, 91, 66),
    42: (36, 84, 54), 43: (28, 67, 43), 47: (36, 64, 48),
    56: (54, 91, 72), 57: (40, 79, 58), 58: (28, 65, 43),
    59: (54, 91, 72), 60: (41, 84, 62),
    64: (56, 91, 74), 65: (49, 84, 67), 66: (44, 79, 61),
    67: (36, 72, 53), 68: (58, 96, 77), 69: (52, 88, 69),
    70: (34, 79, 55), 71: (50, 94, 72), 72: (72, 108, 90),
    73: (60, 100, 82), 78: (72, 108, 90),
}


def comfort_zone(part, instrument=None):
    low, high, target = ROLES[part]
    program = SOUNDFONT_PROGRAMS.get(instrument)
    if program is None:
        return low, high, target
    profile = SPECIAL.get(program)
    if profile is None:
        if 24 <= program <= 31:
            profile = (40, 88, 62)
        elif 32 <= program <= 39:
            profile = (28, 67, 43)
        elif 48 <= program <= 55 or 88 <= program <= 95:
            profile = (36, 96, 64)
        elif 74 <= program <= 79:
            profile = (60, 100, 80)
    if profile is None:
        return low, high, target
    low, high, center = profile
    target = center + {'Melody': 8, 'Chords': -4, 'Bass': -24}[part]
    return low, high, min(high - 6, max(low + 6, target))


def arrange(notes, seed, instruments=None, score_beats=None):
    """Transpose four-bar phrases together; leave percussion completely intact."""
    instruments = instruments or {}
    arranged = list(notes)
    centers = {}
    for channel, part in enumerate(ROLES):
        rng = np.random.default_rng(np.random.SeedSequence([seed, 0x0C7, channel]))
        low, high, center = comfort_zone(part, instruments.get(part))
        target = center + int(rng.choice((-12, 0, 12)))
        previous = None
        phrases = {}
        for index, note in enumerate(notes):
            if note.part == part:
                beat = score_beats[index] if score_beats is not None else note.beat
                phrase = int(beat // 16)
                phrases.setdefault(phrase, []).append(index)
        for phrase, indices in sorted(phrases.items()):
            if phrase and rng.random() < .35:
                target = center + int(rng.choice((-12, 0, 12)))
            pitches = [notes[i].pitch for i in indices]
            average = sum(pitches) / len(pitches)
            shifts = [s for s in range(-96, 97, 12) if min(pitches) + s >= low and max(pitches) + s <= high]
            if shifts:
                ceiling = 128
                if part == 'Chords':
                    ceiling = centers.get(('Melody', phrase), 128) - 8
                elif part == 'Bass':
                    ceiling = min(centers.get(('Chords', phrase), 128) - 10,
                                  centers.get(('Melody', phrase), 128) - 20)
                # Prefer continuity at phrase boundaries; never scatter individual
                # notes between random octaves to achieve a register change.
                # Leave room below the lead and above the bass where the selected
                # instruments allow it; their own comfort zones take precedence.
                shift = min(shifts, key=lambda s: abs(average + s - target) +
                            4 * max(0, average + s - ceiling) +
                            (.25 * abs(pitches[0] + s - previous) if previous is not None else 0))
                for index in indices:
                    arranged[index] = replace(notes[index], pitch=notes[index].pitch + shift)
            else:
                # Very wide phrases can exceed a narrow instrument's comfort
                # zone. Octave-fold only those outliers into the same zone.
                for index in indices:
                    pitch = notes[index].pitch
                    while pitch < low:
                        pitch += 12
                    while pitch > high:
                        pitch -= 12
                    arranged[index] = replace(notes[index], pitch=pitch)
            previous = arranged[indices[-1]].pitch
            centers[(part, phrase)] = sum(arranged[i].pitch for i in indices) / len(indices)
    return arranged
