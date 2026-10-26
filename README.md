# Algorithmic Royalty Free Music Maker

The original algorithmic MIDI program, extended with sampled instruments, drums, desktop controls, and a song arranger. Composition remains in `main.py`, using the existing `Event`, `Tempo`, and `Sheduler` modules.

## Run

Use Python 3.10 or newer with Tkinter on Windows:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Or double-click **Start Music.bat**. Restart an already open app after code updates.

Select **Audio output** and press **Test sound** to check your device. The app remembers the selected device in local `audio_settings.json`, excluded from Git. **Refresh outputs** rescans devices. Playback and rendering run inside this program; no external synthesizer, plugins, virtual MIDI cables, or DAW are required.

## Generate sections

Choose a key, scale, complexity, tempo, length, and instruments for melody, chords, bass, and drums, then press **Play**. There are **128 General MIDI instruments and nine drum kits**. **Mute** omits a part. Instrument/kit/mute and drum-control changes apply during playback after a short render, retaining the current position. Other composition/output changes apply on the next Play. Chord pattern, bass pattern, and playing feel also update during playback. Volume and Loop affect playback immediately. The bar counter follows the audio position.

**New variation** chooses a new seed and a different drum groove, varying actual hit positions and drum choices as well as accents. The same seed/settings reproduce the notes. Simple uses spacious rhythms; Balanced adds activity; Intricate adds faster rhythms, four-note chords, and busier drums. All pitched parts stay in the selected scale; percussion uses General MIDI drum note assignments.

**Drum style** selects Rock, Pop, Four on the floor, Funk, Hip hop, Shuffle, Half time, or Breakbeat. **Drum complexity** can follow the overall complexity or independently use Simple, Balanced, or Intricate. **Drum fills** selects none, or fills every 2, 4, or 8 bars. Shuffle uses swung offbeats; four-on-the-floor keeps a kick on every beat; half time puts the main snare on beat three. Variations retain those stylistic anchors while changing the groove. Changing drum controls does not alter the pitched composition. All drum controls are saved with captured sections and song projects; older projects default to Rock with complexity following the composition and fills every four bars.

The melody develops a recurring two-bar rhythmic motif, follows chord tones on strong beats, favors scale steps, recovers from larger movements, and resolves at phrase endings. Harmony still follows the original chord-order algorithm, with a tonic resolution in the final part of the section. The melody follows the active harmony even when a bar contains two chords.

**Chord pattern** offers Sustained, Pulse, Syncopated, and Arpeggiated accompaniment. **Bass pattern** offers Root, Groove, Walking, and Melodic lines. **Varied** chooses a pattern from the seed, so new variations change accompaniment as well as melody and drums. Chords use inversions that minimize voice movement; bass anchors chord changes and can approach the next root using the selected scale. These controls are shared by desktop and mobile and saved in song sections. Older projects receive the defaults.

**Phrasing / space** selects Continuous, Balanced, or Spacious. Balanced and Spacious give the melody real rests, ease back during openings and response bars, and leave an ensemble break at each four-bar phrase ending and the section ending. Spacious leaves longer gaps. Notes stop before the break; natural sample releases and room ambience can still ring out. Continuous keeps the uninterrupted accompaniment available for styles that need it. The rests are part of the actual score and MIDI output.

**Pitch register** is chosen automatically from the seed, the part (melody/chords/bass), and the selected instrument. New variations can use different octaves; four-bar phrases move together to preserve melodic contour and chord inversions. Piccolo and other high instruments favor a higher register, while cello, tuba, and bass instruments favor lower registers. These are sample-bank comfort zones. Percussion pitches are unchanged. Desktop playback, the piano roll, song assembly, mobile, and MIDI export use the same placed notes.

**Playing feel** selects Tight (exact score timing), Natural, or Loose. Natural and Loose add small ensemble timing offsets, chord spreads, articulation changes, and phrase dynamics. The actual performed notes appear in the piano roll and MIDI export. Separate random streams keep drum edits from changing the pitched performance.

Parts are balanced and panned with subtle reverb/chorus sends in MIDI and mobile synthesis. Desktop audio adds a small stereo room, gentle tone shaping, and soft peak rounding because its sample renderer has no effects engine. WAV retains that sound; MIDI carries notes, dynamics, balance, pan, and effect sends, whose sound depends on the player. These are genre-neutral arrangement and mixing improvements; the bundled compact instrument bank still determines sample realism.

**Export WAV** saves the current arrangement as stereo audio. **Export MIDI** saves melody, chords, bass, and drums on separate tracks, with tempo, note lengths, and instrument programs. Muted parts are omitted. For drums-only MIDI, mute melody/chords/bass. Drums use MIDI channel 10 (zero-based channel 9). Another app may use its own instrument sounds when playing MIDI; WAV preserves the rendered sound.

The piano roll includes muted parts; drums are orange. WAVs have a one-second release tail; loops wrap at the exact musical length and carry tails across the boundary rather than inserting silence.

## Create a song

1. Configure a generated section on **Generator**.
2. Open **Song creator**, enter a name such as `Intro`, `Verse`, `Chorus`, `Bridge`, or `A`, and click **Capture generator section**. Repeat for other sections. Capture stores settings, seed, and instrument selections. Reusing a name updates that saved section.
3. Select a saved section and click **Append section** as many times as needed. Append one-bar **drum fills**, then use **Move up**, **Move down**, and **Remove** to arrange everything.
4. Set the song tempo. All sections play at this common tempo while retaining their keys, motifs, and instruments.
5. **Play song**, **Export song WAV**, or **Export song MIDI**. MIDI includes program changes at section boundaries and a percussion track. WAV sections overlap release tails so transitions have no added silent padding.

The **MIDI output** tab shows the complete assembled song as a piano roll, including repeated sections and drum-fill transitions. It updates when you capture, reorder, remove, or load sections. Track filters show all parts or isolate melody, chords, bass, or drums. Fit the whole song or zoom to 4/8/16 bars, scroll horizontally, and click a note for its MIDI pitch, bar, beat, and duration. Muted parts are omitted, matching MIDI export. Play song opens this view and moves a playback cursor; Follow playback scrolls with it. Editing the playing song stops playback so the displayed notes stay consistent with the arrangement. Save project and export controls remain available below either song view.

You can save up to **32 named sections**, arrange up to **128 entries**, and create songs up to **256 bars**. **Load selected into Generator** lets you audition/edit a saved section; capture it under the same name to update its occurrences. Unused sections can be deleted.

**Save song project** and **Open song project** preserve the reusable sections and sequence in `.song.json` files. A draft without a sequence can also be saved. Try `examples/Example.song.json`, which contains Intro, Verse, Chorus, Bridge, and Outro sections with drum-fill transitions.

Playback, output selection, and volume are shared by both tabs. Starting one stops the other; Stop cancels pending rendering.

## Sample library and credits

The bundled `assets/soundfonts/GeneralUser-GS.sf2` is **GeneralUser GS 2.0.3 by S. Christian Collins**: https://www.schristiancollins.com/generaluser.php . It supplies recorded instrument samples and programmed drum/synth presets, replacing the former basic oscillator approximations. This compact GM bank improves instrument character; it is not a large specialist orchestral or piano library.

The original license, documentation, source commit, and SHA-256 are included alongside the bank. No library download is performed during playback. TinySoundFont renders the samples in-process: https://github.com/amberwhitehead/tinysoundfont-pybind .

## Existing MIDI workflow

```powershell
python main.py --midi
```

This retains the original first-port MIDI workflow (`r` restart, `s` save `.queueSave`, Ctrl+C stop), with generated drums added. It needs a MIDI destination/external synthesizer; desktop playback does not.

## Code layout

| File | Responsibility |
| --- | --- |
| `main.py` | Original scales, chord helpers/transitions, improved melody, progression, drums, MIDI CLI |
| `Event.py`, `Tempo.py`, `Sheduler.py` | Original events, tempo, event queue/save API, corrected MIDI scheduling |
| `Notes.py`, `Instruments.py`, `ProgressionStateMachine.py` | Original supporting modules; SoundFont/kit program maps added to `Instruments.py` |
| `generator.py` | Validated UI settings and adapter calling the original composition engine |
| `accompaniment.py` | Harmonic spans, chord inversions and patterns, bass motifs |
| `phrasing.py` | Musical rests, ensemble breaks, and changes in section activity |
| `registers.py` | Instrument-aware, seeded phrase register placement |
| `performance.py` | Seeded timing, articulation, phrase dynamics |
| `mix_settings.py`, `production.py` | Shared MIDI mix controls and desktop room/tone processing |
| `drum_patterns.py` | Seeded groove styles, independent drum density, and fill scheduling |
| `synth.py` | Offline sampled-instrument WAV rendering |
| `audio_output.py` | Audio devices, resampling, looping, volume, playback |
| `midi_export.py` | Standard MIDI export of sections and song clips |
| `song.py` | Named sections, sequence compilation, project files, assembled WAV/MIDI |
| `music_app.py`, `song_ui.py`, `piano_roll.py` | Generator/song controls, background rendering, and full-song MIDI visualization |

Minor/diminished intervals are corrected to 0/3/7 and 0/3/6. Progressions build chords from the selected scale instead of assuming major-key qualities. The original chord-order state transitions and weighted first chord remain, with a final cadence added.

The scheduler now handles note-off deadlines separately, releases notes on stop, and retains its queue for saving/replay. `Event.setBar` computes bar positions without debug prints. Audio resampling uses floating-point positions to avoid the Windows int32 overflow that previously replayed the beginning with silent gaps.

## Verify

```powershell
python -m unittest discover -s tests -v
```

Checks cover all keys/scales/complexities, all 128 instrument programs, drum kits and MIDI percussion, melody/harmony rules, original engine APIs, Windows resampling, looping, song sequences, project roundtrips, and assembled exports.


## Android and iOS

The mobile version lives in `mobile/` and shares this Python composition engine. It includes native Android/iOS projects, offline sampled playback, drum controls, arrangement, MIDI preview, native file sharing, and compatible song projects. See [mobile/README.md](mobile/README.md) for the Android test APK, build commands, iOS/Xcode signing handoff, and verification limits.
