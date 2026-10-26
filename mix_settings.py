"""Shared General MIDI balance and space for live playback and exports.

Bass stays centered and dry; the accompaniment sits behind the lead.
These controller values also work when the exported MIDI is opened elsewhere.
"""
PART_CONTROLLERS = {
    'Countermelody': {7: 82, 10: 87, 91: 36, 93: 8},
    'Melody': {7: 108, 10: 70, 91: 28, 93: 8},
    'Chords': {7: 86, 10: 49, 91: 40, 93: 16},
    'Bass': {7: 112, 10: 64, 91: 5, 93: 0},
    'Drums': {7: 104, 10: 64, 91: 18, 93: 0},
}

MIX_PROFILES = ('Balanced', 'Warm', 'Punchy', 'Spacious', 'Dry')


def controllers(part, profile='Balanced'):
    result = dict(PART_CONTROLLERS[part])
    if profile == 'Dry':
        result[91] = result[93] = 0
    elif profile == 'Spacious' and part != 'Bass':
        result[91] = min(80, result[91] + 25)
    elif profile == 'Punchy':
        result[91] = round(result[91] * .55)
        if part in ('Bass', 'Drums'):
            result[7] = min(127, result[7] + 6)
    elif profile == 'Warm':
        result[93] = min(30, result[93] + (8 if part == 'Chords' else 0))
    return result
