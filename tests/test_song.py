from dataclasses import replace
import io
from pathlib import Path
import tempfile
import threading
import unittest
import wave
from mido import MidiFile
from generator import Settings
from song import Song, Section, FILL, compile_song, render_song, export_song_midi
from Instruments import SOUNDFONT_PROGRAMS


class SongTests(unittest.TestCase):
    def test_more_than_two_named_sections(self):
        names=['Intro','Verse 1','Chorus','Bridge','Outro']
        sections={name:Section(name,Settings(bars=1,seed=index),{'Melody':'Piano'}) for index,name in enumerate(names)}
        song=Song(110,sections,['Intro','Verse 1','Chorus','Verse 1',FILL,'Bridge','Chorus','Outro'])
        clips=compile_song(song)
        self.assertEqual([clip.name for clip in clips],song.sequence)
        self.assertEqual(song.bars,8)

    def project(self):
        a=Section('A',Settings(bars=1,bpm=220,seed=8),{'Melody':'Piano','Drums':'Standard kit'})
        b=Section('B',Settings(bars=2,bpm=90,seed=9),{'Melody':'Flute','Drums':'Jazz kit'})
        return Song(220,{'A':a,'B':b},['A',FILL,'B','A'])

    def test_sequence_offsets_repeatability_and_fill(self):
        song=self.project();clips=compile_song(song)
        self.assertEqual([clip.start_beat for clip in clips],[0,4,8,16])
        self.assertEqual(song.bars,5)
        self.assertEqual(clips[0].notes,clips[3].notes)
        self.assertTrue(all(clip.settings.bpm==220 for clip in clips))
        self.assertEqual({note.part for note in clips[1].notes},{'Drums'})
        self.assertTrue(any(note.pitch in (45,47,50) for note in clips[1].notes))

    def test_project_roundtrip_and_draft(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'song.song.json';song=self.project();song.save(path)
            self.assertEqual(Song.load(path),song)
            song.sequence=[];song.save(path);self.assertEqual(Song.load(path),song)

    def test_song_wav_has_full_length_and_cancels(self):
        song=self.project();audio=render_song(song)
        with wave.open(io.BytesIO(audio),'rb') as wav:
            self.assertAlmostEqual(wav.getnframes()/wav.getframerate(),5*4*60/220+1,places=4)
        cancelled=threading.Event();cancelled.set()
        self.assertIsNone(render_song(song,cancelled))

    def test_midi_changes_instruments_and_keeps_all_sections(self):
        song=self.project()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'song.mid';export_song_midi(song,path);midi=MidiFile(path)
        track=next(track for track in midi.tracks if track.name.startswith('Melody'))
        tick=0;programs=[];note_times=[]
        for message in track:
            tick+=message.time
            if message.type=='program_change':programs.append((tick,message.program))
            if message.type=='note_on':note_times.append(tick)
        self.assertEqual(programs,[(0,SOUNDFONT_PROGRAMS['Piano']),(8*480,SOUNDFONT_PROGRAMS['Flute']),(16*480,SOUNDFONT_PROGRAMS['Piano'])])
        self.assertTrue(any(time>=16*480 for time in note_times))
        self.assertAlmostEqual(midi.length,5*4*60/220,places=4)
        drums=next(track for track in midi.tracks if track.name.startswith('Drums'))
        self.assertTrue(all(message.channel==9 for message in drums if not message.is_meta))

    def test_invalid_arrangements(self):
        for song in [Song(),Song(sequence=['Missing']),Song(bpm=0),Song(220,self.project().sections,['B']*129)]:
            with self.assertRaises(ValueError):song.validate()


if __name__=='__main__':unittest.main()
