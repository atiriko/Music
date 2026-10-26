import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { loadPyodide } from 'pyodide';
import { BasicMIDI, SoundBankLoader, SpessaSynthProcessor, SpessaSynthSequencer } from 'spessasynth_core';

const runtime = resolve('public/runtime/pyodide') + '/';
const py = await loadPyodide({ indexURL: runtime });
await py.loadPackage('numpy');
py.FS.mkdirTree('/music');
py.unpackArchive(Uint8Array.from(readFileSync('public/engine.zip')), 'zip', { extractDir: '/music' });
py.runPython("import sys; sys.path.insert(0,'/music'); import mobile_bridge");
const run = request => { py.globals.set('_request', JSON.stringify(request)); return JSON.parse(py.runPython('mobile_bridge.handle(_request)')); };
const desktop = request => JSON.parse(execFileSync('python', ['-c', "import sys;sys.path.insert(0,'..');sys.path.insert(0,'python');import mobile_bridge;print(mobile_bridge.handle(sys.argv[1]))", JSON.stringify(request)], { encoding: 'utf8' }));
const catalog = run({ action: 'catalog' });
const roundNotes = notes => notes.map(note => ({ ...note, beat: +note.beat.toFixed(6), duration: +note.duration.toFixed(6), velocity: +note.velocity.toFixed(6) }));

test('the bundled engine has all 128 instruments and nine drum kits', () => {
  assert.equal(catalog.instruments.length, 137); assert.equal(catalog.kits.length, 9);
  assert.equal(catalog.drumStyles.length, 11);
});

test('mobile generation and MIDI match the existing desktop engine', () => {
  for (const [key, scale, style] of [['C','Major','Rock'], ['F# / Gb','Harmonic minor','Shuffle'], ['A','Natural minor','Funk'], ['D','Minor pentatonic','Four on the floor']]) {
    const request = { action: 'section', data: { settings: { ...catalog.defaults, seed: 6864, bars: 4, key, scale, drum_style: style, chord_style: 'Arpeggiated', bass_style: 'Walking', feel: 'Loose' }, instruments: catalog.defaultInstruments } };
    const mobile = run(request), native = desktop(request);
    assert.deepEqual(roundNotes(mobile.notes), roundNotes(native.notes));
    assert.equal(mobile.midi, native.midi, `MIDI mismatch for ${key} ${scale} ${style}`);
  }
});

test('instrument registers agree with desktop and change MIDI pitches', () => {
  const means = [];
  for (const instrument of ['Piccolo', 'Cello']) {
    const request = { action: 'section', data: { settings: { ...catalog.defaults, seed: 5 }, instruments: { ...catalog.defaultInstruments, Melody: instrument } } };
    const mobile = run(request), native = desktop(request);
    assert.deepEqual(roundNotes(mobile.notes), roundNotes(native.notes));
    assert.equal(mobile.midi, native.midi);
    const melody = mobile.notes.filter(note => note.part === 'Melody');
    means.push(melody.reduce((sum, note) => sum + note.pitch, 0) / melody.length);
  }
  assert.ok(means[0] > means[1] + 12);
});

test('phrasing leaves a real ensemble rest in mobile notes and MIDI', () => {
  const request = { action: 'section', data: { settings: { ...catalog.defaults, bars: 4, feel: 'Tight', phrasing: 'Spacious' }, instruments: catalog.defaultInstruments } };
  const result = run(request), native = desktop(request);
  assert.equal(result.midi, native.midi);
  assert.ok(result.notes.every(note => note.beat + note.duration <= 15));
  assert.deepEqual(roundNotes(result.notes), roundNotes(native.notes));
});

test('desktop song projects keep sections, fills, programs and MIDI on mobile', () => {
  const project = JSON.parse(readFileSync('../examples/Example.song.json', 'utf8'));
  const request = { action: 'song', data: project };
  const mobile = run(request), native = desktop(request);
  assert.equal(mobile.bars, 54); assert.equal(mobile.boundaries.length, 10);
  assert.deepEqual(roundNotes(mobile.notes), roundNotes(native.notes));
  assert.equal(mobile.midi, native.midi);
  assert.deepEqual(run({ action: 'validate_project', data: project }), desktop({ action: 'validate_project', data: project }));
});

test('new mobile variations change the real drum rhythm', () => {
  const data = { settings: { ...catalog.defaults, bars: 1, seed: 4, feel: 'Tight' }, instruments: catalog.defaultInstruments };
  const before = run({ action: 'section', data });
  const after = run({ action: 'variation', data: { ...data, seed: 4 } });
  const drums = result => result.notes.filter(note => note.part === 'Drums').map(note => [note.pitch, +note.beat.toFixed(6)]);
  assert.notDeepEqual(drums(before), drums(after));
});

test('mobile rejects invalid projects rather than playing corrupt data', () => {
  assert.throws(() => run({ action: 'song', data: { version: 1, bpm: 110, sections: {}, sequence: ['Missing'] } }), /missing section/);
});

test('automatic songs append while preserving custom sections and MIDI counterpoint', () => {
  const custom = { settings: { ...catalog.defaults, bars: 1, seed: 444, countermelody: true }, instruments: catalog.defaultInstruments };
  const existing = { version: 1, bpm: 123, sections: { Chorus: custom }, sequence: ['Chorus'] };
  const request = { action: 'automatic_song', data: { settings: { ...catalog.defaults, seed: 11, countermelody: true }, instruments: catalog.defaultInstruments, existing, length: 'Short', style: 'Metal', candidates: 1 } };
  const project = run(request);
  assert.deepEqual(project.sections.Chorus, custom);
  assert.equal(project.sequence[0], 'Chorus');
  assert.ok(project.sections['Chorus 2']);
  assert.deepEqual(project, desktop(request));
  const song = run({ action: 'song', data: project });
  assert.ok(song.notes.some(note => note.part === 'Countermelody'));
  assert.ok(Buffer.from(song.midi, 'base64').includes(Buffer.from('Countermelody')));
});

test('bundled studio and electronic presets play their own private banks', async () => {
  for (const instrument of ['Studio Upright', 'Studio Metal Guitar', 'Reese Bass', 'Acid Bass']) {
    const library = catalog.libraries.find(item => item.presets.some(preset => preset.label === instrument));
    assert.ok(library, instrument);
    const preset = library.presets.find(item => item.label === instrument);
    const output = run({ action: 'section', data: { settings: { ...catalog.defaults, bars: 1 }, instruments: { Melody: instrument } } });
    const processor = new SpessaSynthProcessor(22050);
    const bank = readFileSync('../' + library.relative_file);
    processor.soundBankManager.addSoundBank(SoundBankLoader.fromArrayBuffer(Uint8Array.from(bank).buffer), library.id);
    await processor.processorInitialized;
    const sequencer = new SpessaSynthSequencer(processor);
    sequencer.loadNewSongList([BasicMIDI.fromArrayBuffer(Uint8Array.from(Buffer.from(output.midi, 'base64')).buffer)]);
    sequencer.loopCount = 0; sequencer.play();
    const left = new Float32Array(128), right = new Float32Array(128);
    let peak = 0;
    for (let i = 0; i < 200; i++) {
      sequencer.processTick(); processor.process(left, right);
      for (const value of left) peak = Math.max(peak, Math.abs(value));
    }
    assert.ok(peak > .001, `${instrument} private bank ${preset.bank} was silent`);
  }
});

test('the mobile SoundFont engine renders distinct, audible instrument samples', async () => {
  const bankBytes = readFileSync('../assets/soundfonts/GeneralUser-GS.sf2');
  const outputs = [];
  for (const instrument of ['Piano', 'Flute', 'Strings']) {
    const output = run({ action: 'section', data: { settings: { ...catalog.defaults, bars: 1 }, instruments: { ...catalog.defaultInstruments, Melody: instrument, Chords: null, Bass: null, Drums: null } } });
    const processor = new SpessaSynthProcessor(22050);
    const bytes = bankBytes.buffer.slice(bankBytes.byteOffset, bankBytes.byteOffset + bankBytes.byteLength);
    processor.soundBankManager.addSoundBank(SoundBankLoader.fromArrayBuffer(bytes), 'main');
    await processor.processorInitialized;
    const sequencer = new SpessaSynthSequencer(processor);
    const midi = Uint8Array.from(Buffer.from(output.midi, 'base64')).buffer;
    sequencer.loadNewSongList([BasicMIDI.fromArrayBuffer(midi)]);
    sequencer.loopCount = 0; sequencer.play();
    const left = new Float32Array(128), right = new Float32Array(128), samples = [];
    for (let i = 0; i < 200; i++) { sequencer.processTick(); processor.process(left, right); samples.push(...left); }
    const energy = samples.reduce((sum, value) => sum + value * value, 0) / samples.length;
    assert.ok(energy > .000001, `${instrument} is silent`);
    outputs.push(samples);
  }
  assert.notDeepEqual(outputs[0], outputs[1]); assert.notDeepEqual(outputs[0], outputs[2]);
});
