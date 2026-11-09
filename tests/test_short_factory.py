import argparse
import tempfile
import unittest
from pathlib import Path

import short_factory as factory


class ShortFactoryTests(unittest.TestCase):
    def test_each_output_uses_its_matching_recording_even_in_later_batches(self):
        rows = factory.load_manifest('music')
        mapped = factory.map_sources(rows, 'music')
        self.assertEqual(len({r['source_file'] for r in mapped}), 100)
        self.assertEqual(mapped[0]['source_file'], 'music_01.mp4')
        self.assertEqual(mapped[1]['source_file'], 'music_02.mp4')
        self.assertEqual(mapped[24]['source_file'], 'music_25.mp4')
        self.assertEqual(mapped[-1]['source_file'], 'music_100.mp4')
        # Selecting a subset must not renumber its recordings from 01 again.
        subset = factory.map_sources(rows[24:27], 'music')
        self.assertEqual([r['source_file'] for r in subset],
                         ['music_25.mp4', 'music_26.mp4', 'music_27.mp4'])
        self.assertEqual(rows[1]['source_file'], 'music_01.mp4')

    def test_original_reuse_plan_is_available_explicitly(self):
        rows = factory.load_manifest('music')
        self.assertEqual(factory.map_sources(rows, 'music', 'manifest'), rows)
        self.assertEqual(factory.map_sources(rows, 'music', 'manifest')[4]['source_file'],
                         'music_01.mp4')

    def test_full_source_is_preserved_despite_old_manifest_cuts(self):
        for offset in (0, 3, 6, 9, 12):
            with self.subTest(offset=offset):
                row = {'duration_sec': '12', 'start_offset_sec': str(offset)}
                self.assertEqual(factory.clip_window(row, 35), (0, 35))
                self.assertEqual(factory.clip_window(row, 58.44), (0, 58.44))

    def test_explicit_cuts_keep_audio_and_video_inside_source(self):
        row = {'duration_sec': '12', 'start_offset_sec': '12'}
        self.assertEqual(factory.clip_window(row, 35, 'manifest'), (12, 12))
        self.assertEqual(factory.clip_window(row, 35, 20), (12, 20))
        self.assertEqual(factory.clip_window(row, 35, 30), (5, 30))
        self.assertEqual(factory.clip_window(row, 35, 50), (0, 35))

    def test_duration_argument_rejects_nonfinite_and_nonpositive_values(self):
        for value in ('0', '-1', 'nan', 'inf', 'oops'):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    factory.parse_duration(value)
        self.assertEqual(factory.parse_duration('35'), 35)
        self.assertEqual(factory.parse_duration('source'), 'source')
        self.assertEqual(factory.parse_duration('manifest'), 'manifest')

    def test_wrapped_lines_are_separate_utf8_files_without_newline_glyphs(self):
        row = {
            'video_filename': 'test.mp4',
            'hook': 'Can you make music in seconds?',
            'supporting_text': '100% original — keep the punctuation.',
            'on_screen_question': 'Which style should I try?'
        }
        with tempfile.TemporaryDirectory() as directory:
            groups = factory.write_overlay(Path(directory), row)
            self.assertEqual([p.read_text() for p in groups[0]],
                             ['Can you make music in', 'seconds?'])
            for paths in groups:
                for path in paths:
                    self.assertNotIn('\n', path.read_text())
                    self.assertNotIn('\r', path.read_text())
            self.assertIn('100% original —', groups[1][0].read_text())
            filters = factory.ffmpeg_filter(*groups, '/font.ttf')
            self.assertEqual(filters.count('drawtext='), sum(map(len, groups)))
            self.assertIn('expansion=none', filters)


if __name__ == '__main__':
    unittest.main()
