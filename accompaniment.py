"""Diatonic accompaniment: harmonic plans, voice leading, and bass motifs.

Times in the harmonic plan are beats; scheduled Events remain seconds.
The original engine supplies its progression and scale conversion function.
"""
from Event import Event

CHORD_STYLES = ('Varied', 'Sustained', 'Pulse', 'Syncopated', 'Arpeggiated')
BASS_STYLES = ('Varied', 'Root', 'Groove', 'Walking', 'Melodic')


def voice_lead(pitches, previous, rng):
    octave_shift = 12 * ((pitches[0] - 48) // 12)
    pitches = [p - octave_shift for p in pitches]
    candidates = []
    for inversion in range(len(pitches)):
        rotated = pitches[inversion:] + [p + 12 for p in pitches[:inversion]]
        for shift in (-24, -12, 0, 12):
            chord = [p + shift for p in rotated]
            if chord[0] >= 45 and chord[-1] <= 79:
                movement = (sum(abs(p - q) for p, q in zip(chord, previous)) if previous
                            else abs(sum(chord) / len(chord) - 60))
                candidates.append((movement, float(rng.random()), chord))
    return min(candidates)[2]


def generate(key, scale, scheduler, progression, level, rng, pitch,
             chord_style='Varied', bass_style='Varied'):
    quarter = scheduler.tempo.quarter
    bars = len(progression)
    spans = []
    previous = None
    for bar, degree in enumerate(progression):
        degree = int(degree) % len(scale)
        # Keep short variations distinct: resolve the final half-bar instead of
        # overwriting both bars of a two-bar idea with the same V-I cadence.
        changes = [(0, 4, degree)]
        if bar == bars - 1:
            changes = [(0, 2, degree), (2, 2, 0)] if degree else [(0, 4, 0)]
        elif level == 2 and bar % 4 == 3:
            changes = [(0, 2, degree), (2, 2, int(rng.choice((1, 3, 4, 5))) % len(scale))]
        for beat, duration, root in changes:
            tones = [pitch(key, scale, root + n * 2) for n in range(4 if level == 2 else 3)]
            voiced = voice_lead(tones, previous, rng)
            previous = voiced
            spans.append((bar * 4 + beat, duration, root, tuple(voiced)))
    scheduler.harmony = spans
    chosen_chord = chord_style
    if chosen_chord == 'Varied':
        choices = ('Sustained', 'Pulse') if level == 0 else ('Pulse', 'Syncopated', 'Arpeggiated', 'Sustained')
        chosen_chord = str(rng.choice(choices))
    chosen_bass = bass_style
    if chosen_bass == 'Varied':
        chosen_bass = str(rng.choice(('Root', 'Groove') if level == 0 else ('Groove', 'Walking', 'Melodic')))
    groove = ((0, 1.5, 2.5), (0, .75, 2, 3.5), (0, 1, 2.5, 3))[int(rng.integers(3))]
    direction = int(rng.choice((-1, 1)))
    for index, (start, duration, root, tones) in enumerate(spans):
        if chosen_chord == 'Sustained':
            hits = (0,)
        elif chosen_chord == 'Pulse':
            hits = (0, 2) if level == 0 else (0, 1, 2, 3)
        elif chosen_chord == 'Syncopated':
            hits = (0, 1.5, 3) if int(start // 4) % 2 == 0 else (0, .75, 2.5, 3.5)
        else:
            hits = tuple(i * (.5 if level else 1) for i in range(8 if level else 4))
        hits = [h for h in hits if h < duration]
        for i, hit in enumerate(hits):
            end = hits[i + 1] if i + 1 < len(hits) else duration
            gate = .94 if chosen_chord == 'Sustained' else .72
            notes = [tones[i % len(tones)]] if chosen_chord == 'Arpeggiated' else tones
            for n, note in enumerate(notes):
                velocity = int(rng.integers(60, 76)) + (5 if hit == 0 else 0) - n * 2
                scheduler.addEvent(Event(1, note, (start + hit) * quarter,
                                         (end - hit) * quarter * gate, velocity))
        hits = ((0,) if chosen_bass == 'Root' else (0, 1, 2, 3) if chosen_bass == 'Walking'
                else groove if chosen_bass == 'Groove' else (0, .5, 1.5, 2, 3, 3.5))
        if level == 0 and chosen_bass != 'Root':
            hits = (0, 2)
        hits = [h for h in hits if h < duration]
        next_root = spans[index + 1][2] if index + 1 < len(spans) else 0
        for i, hit in enumerate(hits):
            degree = root
            if i:
                if chosen_bass == 'Walking':
                    degree = root + direction * i
                elif chosen_bass == 'Melodic':
                    degree = root + (0, 4, 2, 4, 1, 2)[i % 6]
                elif chosen_bass == 'Groove':
                    degree = root + (4 if i % 2 else len(scale))
            if i == len(hits) - 1 and i and chosen_bass in ('Walking', 'Melodic'):
                degree = next_root + direction  # Diatonic approach to the next harmony.
            note = pitch(key - 12, scale, degree)
            while note > 55:
                note -= 12
            while note < 28:
                note += 12
            end = hits[i + 1] if i + 1 < len(hits) else duration
            velocity = int(rng.integers(79, 96)) + (5 if i == 0 else -4)
            scheduler.addEvent(Event(2, note, (start + hit) * quarter,
                                     (end - hit) * quarter * .82, velocity))
