"""A slower second melody: chord tones, consonance, and contrary motion."""
import numpy as np
from Event import Event


def generate(scheduler, key, scale, seed):
    rng = np.random.default_rng(np.random.SeedSequence([seed, 0xC017]))
    quarter = scheduler.tempo.quarter
    lead = sorted((e for e in scheduler.queue if e.channel == 0), key=lambda e: e.time)
    previous, previous_lead = key + 12, None
    for start, duration, _, tones in scheduler.harmony:
        for offset in (0, 2):
            if offset >= duration:
                continue
            beat = start + offset
            # Alternate held support and shorter answers; leave independent rests.
            if int(beat // 4) % 2 and offset == 0:
                continue
            current_lead = next((e.note for e in reversed(lead) if e.time <= beat * quarter + .01), key + 24)
            direction = 0 if previous_lead is None else np.sign(current_lead - previous_lead)
            target = previous - int(direction) * 2
            choices = [p + octave for p in tones for octave in (-12, 0, 12)
                       if 50 <= p + octave <= 84 and (abs(p + octave - current_lead) % 12) in (3, 4, 7, 8, 9)]
            if not choices:
                choices = [p + octave for p in tones for octave in (-12, 0) if 50 <= p + octave <= 84]
            if not choices:
                continue
            pitch = min(choices, key=lambda p: (abs(p - target), abs(p - 65)))
            length = min(duration - offset, 1.5 if offset else 1.8)
            scheduler.addEvent(Event(3, pitch, beat * quarter, length * quarter, int(rng.integers(57, 74))))
            previous, previous_lead = pitch, current_lead
