import unittest
from generator import Settings, build_scheduler, generate


class MelodyTheoryTests(unittest.TestCase):
    def test_strong_beats_are_in_the_current_chord(self):
        for scale in ['Major','Natural minor','Harmonic minor','Dorian','Minor pentatonic']:
            for seed in range(10):
                scheduler=build_scheduler(Settings(scale=scale,seed=seed))
                for note in scheduler.queue:
                    if note.channel!=0:
                        continue
                    beat=note.nominal_time/scheduler.tempo.quarter
                    local=beat%4
                    if min(abs(local),abs(local-2),abs(local-4))>1e-7:
                        continue
                    chord=next({p%12 for p in tones} for start, length, _, tones in scheduler.harmony
                               if start <= beat < start+length)
                    self.assertIn(note.note%12,chord)

    def test_rhythmic_motif_returns_and_final_note_resolves(self):
        for seed in range(10):
            notes=[n for n in generate(Settings(seed=seed,complexity='Intricate',feel='Tight')) if n.part=='Melody']
            rhythm=lambda bar:[(round(n.beat-bar*4,6),round(n.duration,6)) for n in notes if bar*4<=n.beat<(bar+1)*4]
            self.assertEqual(rhythm(0),rhythm(2))
            self.assertEqual(rhythm(1),rhythm(3))
            self.assertEqual(notes[-1].pitch%12,0)
            steps=[abs(b.pitch-a.pitch)<=2 for a,b in zip(notes,notes[1:])]
            self.assertGreater(sum(steps)/len(steps),.7)


if __name__=='__main__':unittest.main()
