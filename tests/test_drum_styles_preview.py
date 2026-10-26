from dataclasses import replace
from collections import Counter
import tempfile
from pathlib import Path
import unittest
from mido import MidiFile
from generator import Settings, generate
from drum_patterns import DRUM_STYLES
from song import Song, Section, FILL, midi_preview, export_song_midi, compile_song


def rhythm(settings):
    return tuple((round(n.beat,6), n.pitch) for n in generate(replace(settings,feel='Tight')) if n.part=='Drums')


class DrumStyleTests(unittest.TestCase):
    def test_seeds_change_actual_hit_positions_or_drums_in_every_style(self):
        for style in DRUM_STYLES:
            for density in ['Simple','Balanced','Intricate']:
                with self.subTest(style=style,density=density):
                    patterns={rhythm(Settings(bars=1,seed=seed,drum_style=style,drum_complexity=density)) for seed in range(10)}
                    self.assertGreater(len(patterns),1)
        settings=Settings(seed=13,drum_style='Funk')
        self.assertEqual(generate(settings),generate(settings))

    def test_style_and_density_do_not_change_pitched_composition(self):
        settings=Settings(seed=4)
        pitched=lambda config:[n for n in generate(config) if n.part!='Drums']
        for style in DRUM_STYLES:
            self.assertEqual(pitched(settings),pitched(replace(settings,drum_style=style,drum_complexity='Intricate')))

    def test_four_on_floor_and_half_time_anchors(self):
        floor=generate(Settings(bars=4,feel='Tight',drum_style='Four on the floor',drum_fills='None'))
        self.assertEqual([n.beat for n in floor if n.part=='Drums' and n.pitch==36],list(range(16)))
        half=generate(Settings(bars=4,feel='Tight',drum_style='Half time',drum_fills='None'))
        self.assertEqual([n.beat for n in half if n.part=='Drums' and n.pitch==38],[2,6,10,14])

    def test_shuffle_timing_and_fill_controls(self):
        notes=generate(Settings(bars=4,feel='Tight',drum_style='Shuffle',drum_complexity='Balanced'))
        self.assertTrue(any(abs(n.beat%1-2/3)<1e-6 for n in notes if n.part=='Drums'))
        settings=Settings(bars=8,drum_complexity='Intricate',seed=8)
        no=generate(replace(settings,drum_fills='None'))
        fills=generate(replace(settings,drum_fills='Every 2 bars'))
        toms=lambda notes:[n for n in notes if n.part=='Drums' and n.pitch in (45,47,50)]
        self.assertFalse(toms(no))
        self.assertTrue(toms(fills))
        self.assertEqual({int(n.beat//4) for n in toms(fills)},{1,3,5,7})

    def test_settings_roundtrip_and_legacy_defaults(self):
        section=Section('Verse',Settings(drum_style='Hip hop',drum_complexity='Simple',drum_fills='Every 8 bars'),{'Drums':'Standard kit'})
        song=Song(110,{'Verse':section},['Verse'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'song.json';song.save(path);self.assertEqual(Song.load(path),song)
        self.assertEqual(Settings().drum_style,'Rock')
        for kwargs in [{'drum_style':'Invalid'},{'drum_complexity':'Invalid'},{'drum_fills':'Invalid'}]:
            with self.assertRaises(ValueError):Settings(**kwargs)

    def test_all_hit_times_and_lengths_fit_selected_length(self):
        for style in DRUM_STYLES:
            notes=generate(Settings(bars=3,drum_style=style,drum_complexity='Intricate'))
            for n in notes:
                if n.part=='Drums':
                    self.assertTrue(0<=n.beat<12)
                    self.assertTrue(0<n.duration<=12-n.beat+1e-8)

    def test_transition_fills_follow_the_preceding_sections_style_and_seed(self):
        section=Section('Verse',Settings(bars=1,seed=7,drum_style='Shuffle'),{'Drums':'Brush kit'})
        song=Song(110,{'Verse':section},['Verse',FILL])
        fill=compile_song(song)[1]
        self.assertEqual(fill.settings.drum_style,'Shuffle')
        self.assertEqual(fill.instruments['Drums'],'Brush kit')
        changed=Section('Verse',replace(section.settings,seed=8),section.instruments)
        other=compile_song(Song(110,{'Verse':changed},['Verse',FILL]))[1]
        self.assertNotEqual(fill.settings.seed,other.settings.seed)
        self.assertNotEqual(fill.notes,other.notes)


class MidiPreviewTests(unittest.TestCase):
    def test_preview_matches_full_export_including_fills_and_muting(self):
        a=Section('A',Settings(bars=1,drum_style='Funk'),{'Melody':'Piano','Drums':'Standard kit'})
        b=Section('B',Settings(bars=2,seed=16,drum_style='Shuffle'),{'Chords':'Strings','Drums':'Brush kit'})
        song=Song(110,{'A':a,'B':b},['A',FILL,'B','A'])
        notes,boundaries=midi_preview(song)
        self.assertEqual(boundaries,[(0,'A'),(4,FILL),(8,'B'),(16,'A')])
        self.assertTrue(any(n.beat>=16 for n in notes))
        self.assertFalse(any(n.part=='Bass' for n in notes))
        channels={'Melody':0,'Chords':1,'Bass':2,'Drums':9}
        expected=Counter((channels[n.part],round(n.beat*480),n.pitch) for n in notes)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'song.mid';export_song_midi(song,path);midi=MidiFile(path)
        actual=Counter()
        for track in midi.tracks:
            tick=0
            for message in track:
                tick+=message.time
                if message.type=='note_on' and message.velocity:
                    actual[(message.channel,tick,message.note)]+=1
        self.assertEqual(actual,expected)


if __name__=='__main__':unittest.main()
