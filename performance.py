"""Deterministic ensemble timing, articulation, and phrase dynamics."""
import numpy as np

FEELS = ('Tight', 'Natural', 'Loose')


def apply(scheduler, bars, seed, feel):
    streams = {channel: np.random.default_rng(np.random.SeedSequence([seed, 0xFEE, channel]))
               for channel in (0, 1, 2, 9)}
    amount = {'Tight': 0, 'Natural': .006, 'Loose': .012}[feel]
    end = bars * scheduler.tempo.whole
    groups = {}
    for event in sorted(scheduler.queue):
        event.nominal_time, event.nominal_length = event.time, event.length
        if not amount:
            continue
        rng = streams[event.channel]
        key = (event.channel, round(event.time, 8))
        if key not in groups:
            groups[key] = (float(rng.normal(0, amount)), 0)
        offset, voice = groups[key]
        # Shared onset per chord, with a very small spread between its voices.
        event.time = max(0, min(end - .001, event.time + offset + (voice * amount * .35 if event.channel == 1 else 0)))
        groups[key] = offset, voice + 1
        event.length = min(end - event.time, event.length * float(rng.uniform(.96, 1.025)))
        beat = event.nominal_time / scheduler.tempo.quarter
        phrase = 1 + .055 * np.sin(2 * np.pi * (beat % 16) / 16 - .6)
        event.velocity = max(1, min(127, round(event.velocity * phrase + rng.normal(0, 2))))
