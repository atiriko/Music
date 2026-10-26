"""Section roles, ensemble interaction, and energy development."""
import numpy as np
from Event import Event


def shape(scheduler, settings):
    role = settings.section_role
    if role == 'Loop' and settings.energy == 65:
        return
    quarter = scheduler.tempo.quarter
    rng = np.random.default_rng(np.random.SeedSequence([settings.seed, 0xA22]))
    kicks = [e.time / quarter for e in scheduler.queue if e.channel == 9 and e.note == 36]
    melody = [e for e in scheduler.queue if e.channel == 0]
    kept = []
    for event in scheduler.queue:
        beat = event.time / quarter
        bar, local = int((beat + 1e-8) // 4), round(beat % 4, 6)
        progress = beat / (settings.bars * 4)
        if role == 'Intro':
            if event.channel == 0 and progress < .5:
                continue
            if event.channel == 9 and progress < .5 and event.note not in (42, 46):
                continue
        elif role == 'Breakdown':
            if event.channel == 9 and event.note not in (42, 46, 51):
                continue
            if event.channel == 2 and local not in (0, 2):
                continue
        elif role == 'Outro':
            if event.channel == 9 and progress > .5 and event.note not in (36, 42):
                continue
        if role in ('Verse', 'Bridge') and event.channel == 0 and bar % 2 and local >= 3:
            continue
        if role != 'Loop' and event.channel == 1 and local not in (0, 2):
            busy_lead = sum(abs(e.time - event.time) < quarter * .4 for e in melody) >= 2
            if busy_lead and rng.random() < .55:
                continue
        if role != 'Loop' and event.channel == 2 and local not in (0, 2) and kicks:
            # Move a nearby bass attack onto the drummer's kick, staying inside
            # the same half-bar harmony. Keep its previous note-off boundary.
            nearest = min(kicks, key=lambda kick: abs(kick - beat))
            if abs(nearest - beat) <= .25 and int(nearest // 2) == int((beat + 1e-8) // 2):
                end = event.time + event.length
                event.time = nearest * quarter
                event.length = max(.04 * quarter, end - event.time)
        level = .62 + settings.energy / 170
        if role == 'Intro':
            level *= .65 + .35 * progress
        elif role == 'Outro':
            level *= 1 - .48 * progress
        event.velocity = max(1, min(127, round(event.velocity * level)))
        kept.append(event)
    scheduler.queue[:] = kept

