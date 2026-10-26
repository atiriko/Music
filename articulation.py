"""Turn score events into instrument-specific performances without plugins."""
from soundbanks import voice


def apply(scheduler, settings, instruments):
    quarter = scheduler.tempo.quarter
    for channel, part in ((0, 'Melody'), (1, 'Chords'), (2, 'Bass'), (3, 'Countermelody')):
        selected = instruments.get(part)
        if not selected:
            continue
        program = voice(selected)['gm_program']
        events = sorted((e for e in scheduler.queue if e.channel == channel), key=lambda e: (e.time, e.note))
        if 24 <= program <= 31 and channel == 1:
            groups = {}
            for event in events:
                groups.setdefault(round(event.time, 8), []).append(event)
            for group in groups.values():
                if len(group) < 2:
                    continue
                hit = group[0].time / quarter
                down = hit % 1 < .1 if settings.strum_pattern == 'Down-up' else int(hit) % 2 == 0
                spread = .003 if settings.strum_pattern == 'Chug' else .009
                for index, event in enumerate(sorted(group, key=lambda e: e.note, reverse=not down)):
                    offset = index * spread
                    event.time += offset
                    event.length = max(.025, event.length - offset)
                    event.velocity = max(1, event.velocity - index * 3)
        # Wind and bowed-string leads connect nearby notes, while respecting
        # intentional phrase rests. No legato is invented across a long gap.
        if channel in (0, 3) and (40 <= program <= 44 or 56 <= program <= 79):
            for event, following in zip(events, events[1:]):
                gap = following.time - event.time - event.length
                if 0 <= gap <= quarter * .22 and following.time - event.time <= quarter * 2:
                    event.length = following.time - event.time + min(.012, quarter * .02)
                event.velocity = max(1, min(112, event.velocity))
        if 32 <= program <= 37:
            for event in events:
                event.length *= .92
        # Piano and harp pedal-like sustain only in sustained accompaniment.
        if channel == 1 and (program < 8 or program == 46) and settings.chord_style == 'Sustained':
            for event in events:
                event.length *= 1.025

