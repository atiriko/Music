"""Ensemble breath points and changing activity over a section.

Silence is part of the score: these changes affect MIDI, previews, and audio.
They run before performance timing so each player respects the same break.
"""
PHRASINGS = ('Continuous', 'Balanced', 'Spacious')


def breath_points(bars, phrasing):
    if phrasing == 'Continuous':
        return []
    gap = 1 if phrasing == 'Spacious' else .5
    endings = sorted(set(range(16, bars * 4 + 1, 16)) | {bars * 4})
    return [(end - gap, end) for end in endings]


def apply(scheduler, bars, phrasing):
    if phrasing == 'Continuous':
        return
    quarter = scheduler.tempo.quarter
    breaks = breath_points(bars, phrasing)
    kept = []
    for event in scheduler.queue:
        beat, length = event.time / quarter, event.length / quarter
        # A quieter opening and response bars create entrances and contrast.
        # Keep harmony/bass downbeats and the lead's harmonic anchors intact.
        bar, local = int((beat + 1e-8) // 4), round(beat % 4, 8)
        sparse = (bars >= 4 and bar == 0) or (bar % 4 == 2)
        if sparse and event.channel in (1, 2) and local not in (0, 2):
            continue
        if sparse and event.channel == 9 and event.velocity < 80 and local % 1:
            continue
        for start, end in breaks:
            if start - 1e-8 <= beat < end - 1e-8:
                break
            if beat < start < beat + length:
                event.length = (start - beat) * quarter
        else:
            # Instruments ease back in the opening, then build into the phrase.
            if sparse:
                event.velocity = max(1, round(event.velocity * .86))
            kept.append(event)
    scheduler.queue[:] = kept


def protect_breaks(scheduler, bars, phrasing):
    """Players may vary their timing, but cannot play through a shared rest."""
    quarter = scheduler.tempo.quarter
    for start, end in breath_points(bars, phrasing):
        start, end = start * quarter, end * quarter
        for event in scheduler.queue:
            if event.nominal_time >= end - 1e-8 and start <= event.time < end:
                event.time = end
            if event.nominal_time < start - 1e-8 and event.time + event.length > start:
                event.length = max(.001, start - event.time)
