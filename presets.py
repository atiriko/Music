"""Editable starting points, using only sounds bundled with the application."""
SOUND_PRESETS = {
    'Studio band': {'instruments': {'Melody': 'Studio Upright', 'Chords': 'Studio Clean Guitar',
                    'Bass': 'Finger Bass', 'Countermelody': 'Flute', 'Drums': 'Room kit'},
                    'settings': {'drum_style': 'Pop', 'chord_voicing': 'Sevenths', 'strum_pattern': 'Pop'}},
    'Metal': {'instruments': {'Melody': 'Metal Lead', 'Chords': 'Studio Metal Guitar',
                    'Bass': 'Pick Bass', 'Countermelody': 'Overdrive Guitar', 'Drums': 'Power kit'},
             'settings': {'bpm': 150, 'drum_style': 'Metal', 'chord_voicing': 'Power',
                          'chord_style': 'Strummed', 'strum_pattern': 'Chug', 'melody_style': 'Angular', 'mix_profile': 'Punchy'}},
    'Drum and bass': {'instruments': {'Melody': 'Techno Stab', 'Chords': 'Dark Pad',
                    'Bass': 'Reese Bass', 'Countermelody': 'Metal Lead', 'Drums': 'Electronic kit'},
             'settings': {'bpm': 174, 'drum_style': 'Drum and bass', 'chord_voicing': 'Sevenths',
                          'strum_pattern': 'Auto', 'melody_style': 'Rhythmic', 'mix_profile': 'Punchy'}},
    'Techno': {'instruments': {'Melody': 'Techno Stab', 'Chords': 'Dark Pad',
                    'Bass': 'Acid Bass', 'Countermelody': 'Reese Bass', 'Drums': '808/909 kit'},
             'settings': {'bpm': 130, 'drum_style': 'Techno', 'chord_style': 'Arpeggiated',
                          'chord_voicing': 'Sus2', 'strum_pattern': 'Auto', 'melody_style': 'Rhythmic', 'mix_profile': 'Punchy'}},
}
