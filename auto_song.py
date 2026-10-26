"""Create an editable full song from related, scored section candidates."""
from dataclasses import replace
from generator import Settings
from quality import choose
from song import Song, Section

LENGTHS = ('Short', 'Standard', 'Extended')
STYLES = ('From generator', 'Pop', 'Electronic', 'Rock', 'Jazz', 'Hip hop', 'Ambient')
STYLE_RULES = {
    'Pop': ('Pop', 'Syncopated', 'Groove', 'Balanced'),
    'Electronic': ('Four on the floor', 'Arpeggiated', 'Groove', 'Punchy'),
    'Rock': ('Rock', 'Pulse', 'Groove', 'Punchy'),
    'Jazz': ('Shuffle', 'Syncopated', 'Walking', 'Warm'),
    'Hip hop': ('Hip hop', 'Syncopated', 'Groove', 'Warm'),
    'Ambient': ('Half time', 'Sustained', 'Root', 'Spacious'),
}


def create(settings, instruments, length='Standard', style='From generator', candidates=4):
    if length not in LENGTHS or style not in STYLES:
        raise ValueError('Choose a listed song length and style.')
    if not any(instruments.values()):
        raise ValueError('Choose at least one instrument before creating a song.')
    base = settings
    if style in STYLE_RULES:
        drum, chord, bass, mix = STYLE_RULES[style]
        base = replace(base, drum_style=drum, chord_style=chord, bass_style=bass, mix_profile=mix)
    chorus, selection = choose(replace(base, bars=8, section_role='Chorus', energy=max(72, base.energy)),
                               instruments, candidates, new_hook=True)
    hook = chorus.hook_seed
    definitions = [('Intro', 4, 'Intro', 35), ('Verse 1', 8, 'Verse', 52),
                   ('Chorus', 8, 'Chorus', 78), ('Verse 2', 8, 'Verse', 60),
                   ('Bridge', 8, 'Bridge', 48), ('Final chorus', 8, 'Chorus', 90),
                   ('Outro', 4, 'Outro', 30)]
    sections = {}
    reports = {}
    for index, (name, bars, role, energy) in enumerate(definitions):
        seed = (chorus.seed + index * 7919) % 1_000_000_000
        phrase = 'Spacious' if role in ('Intro', 'Bridge', 'Outro') else base.phrasing
        level = 'Simple' if role in ('Intro', 'Outro') else base.complexity
        candidate = replace(base, bars=bars, seed=seed, hook_seed=hook, section_role=role,
                            energy=min(100, max(0, energy + base.energy - 65)),
                            phrasing=phrase, complexity=level)
        if name == 'Chorus':
            selected, report = chorus, selection
        else:
            selected, report = choose(candidate, instruments, candidates)
        sections[name] = Section(name, selected, dict(instruments))
        reports[name] = report
    if length == 'Short':
        sequence = ['Intro', 'Verse 1', 'Chorus', 'Final chorus', 'Outro']
    else:
        sequence = ['Intro', 'Verse 1', 'Chorus', 'Verse 2', 'Chorus', 'Bridge', 'Final chorus', 'Outro']
    if length == 'Extended':
        breakdown = replace(sections['Bridge'].settings, section_role='Breakdown', energy=25)
        sections['Breakdown'] = Section('Breakdown', breakdown, dict(instruments))
        sequence[5:5] = ['Breakdown', 'Verse 2', 'Chorus']
    used = {name: sections[name] for name in dict.fromkeys(sequence)}
    song = Song(base.bpm, used, sequence, {'automatic': True, 'style': style,
                'hook_seed': hook, 'selection': {name: reports.get(name, {}) for name in used}})
    song.validate()
    return song
