"""Automatic song structure, hook reuse, candidate selection, and SF2 imports."""
from pathlib import Path
import struct
import unittest
from generator import Settings, generate
from auto_song import create, STYLES
from quality import assess, choose
from song import compile_song
import soundbanks

INSTRUMENTS = {'Melody': 'Studio Upright', 'Chords': 'Studio Clean Guitar', 'Bass': 'Finger Bass', 'Drums': 'Room kit'}


class AutoSongTests(unittest.TestCase):
    def test_standard_song_structure_and_shared_hook(self):
        song = create(Settings(seed=11), INSTRUMENTS, 'Standard', 'Pop', 2)
        self.assertEqual(song.sequence[0], 'Intro')
        self.assertEqual(song.sequence[-1], 'Outro')
        self.assertIn('Chorus', song.sequence)
        self.assertIn('Bridge', song.sequence)
        hooks = {section.settings.hook_seed for section in song.sections.values()}
        self.assertEqual(len(hooks), 1)
        roles = {section.settings.section_role for section in song.sections.values()}
        self.assertTrue({'Intro', 'Verse', 'Chorus', 'Bridge', 'Outro'} <= roles)
        self.assertGreater(song.sections['Final chorus'].settings.energy,
                           song.sections['Verse 1'].settings.energy)

    def test_lengths_and_styles(self):
        short = create(Settings(seed=3), INSTRUMENTS, 'Short', 'From generator', 1)
        extended = create(Settings(seed=3), INSTRUMENTS, 'Extended', 'Electronic', 1)
        self.assertLess(short.bars, extended.bars)
        self.assertIn('Breakdown', extended.sequence)
        self.assertEqual(extended.sections['Chorus'].settings.drum_style, 'Four on the floor')
        self.assertEqual(len(compile_song(short)), len(short.sequence))
        with self.assertRaises(ValueError):
            create(Settings(), INSTRUMENTS, 'Endless')
        with self.assertRaises(ValueError):
            create(Settings(), dict.fromkeys(INSTRUMENTS))
        self.assertIn('Ambient', STYLES)

    def test_intro_thins_out_lead(self):
        loop = generate(Settings(seed=8), INSTRUMENTS)
        intro = generate(Settings(seed=8, section_role='Intro', energy=35), INSTRUMENTS)
        first_half = lambda notes: [n for n in notes if n.part == 'Melody' and n.beat < 16]
        self.assertLess(len(first_half(intro)), len(first_half(loop)))

    def test_candidate_selection_is_deterministic_and_best(self):
        settings = Settings(seed=21)
        winner, report = choose(settings, INSTRUMENTS, 4)
        again, _ = choose(settings, INSTRUMENTS, 4)
        self.assertEqual(winner, again)
        self.assertEqual(report['score'], max(report['candidate_scores']))
        self.assertTrue(0 <= assess(generate(winner, INSTRUMENTS))['score'] <= 100)
        with self.assertRaises(ValueError):
            choose(settings, INSTRUMENTS, 9)


class ImportTests(unittest.TestCase):
    def test_categories_cover_every_instrument(self):
        groups = soundbanks.groups()
        self.assertIn('Studio Upright', groups['Pianos & keys'])
        self.assertIn('Studio Clean Guitar', groups['Guitars'])
        self.assertEqual(sum(map(len, groups.values())), len(soundbanks.SOUNDFONT_PROGRAMS))
        self.assertEqual(list(soundbanks.groups(True)), ['Drum kits'])

    def test_prepare_remaps_banks_and_rejects_bad_files(self):
        source = Path(soundbanks.LIBRARIES[next(iter(soundbanks.LIBRARIES))]['file']).read_bytes()
        # Make the content unique so it is not treated as the already-registered library.
        data = bytearray(source)
        offset = soundbanks.inspect(bytes(data))[0]['offset']
        struct.pack_into('<HH', data, offset + 20, 5, 0)
        metadata, modified = soundbanks.prepare(bytes(data), 'Test.sf2', 'Organs')
        preset = metadata['presets'][0]
        self.assertEqual(preset['category'], 'Organs')
        self.assertGreaterEqual(preset['bank'], 32)
        self.assertNotIn(preset['bank'], {p['bank'] for p in soundbanks.EXTRA.values()})
        self.assertEqual(soundbanks.inspect(modified)[0]['bank'], preset['bank'])
        with self.assertRaises(ValueError):
            soundbanks.prepare(b'RIFF' + b'\0' * 2000, 'bad.sf2')
        with self.assertRaises(ValueError):
            soundbanks.voice('Not an instrument')


if __name__ == '__main__':
    unittest.main()
