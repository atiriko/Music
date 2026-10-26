import { useEffect, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { Preferences } from '@capacitor/preferences';
import { Capacitor } from '@capacitor/core';
import { App as NativeApp } from '@capacitor/app';
import { engine } from './engine';
import { player } from './player';
import { renderWav, shareFile, shareMidi } from './files';
import { deleteLibrary, saveLibrary, storedMetadata, remapLibrary } from './libraries';
import { PianoRoll } from './PianoRoll';
import { FILL, PARTS, COLORS } from './types';
import type { Catalog, Composition, Instruments, Library, Part, Project, Settings } from './types';
import './style.css';

type Saved = { name: string; project: Project; updated: string };
type Mode = 'generate' | 'song' | 'projects';
const EMPTY: Project = { version: 1, bpm: 110, sections: {}, sequence: [] };
const STORAGE = 'music-studio-v1';
const MAX_FONT = 64 * 1024 * 1024;
const nextName = (sections: Project['sections']) => [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', ...Array.from({ length: 6 }, (_, i) => 'Section' + (27 + i))].find(name => !sections[name]) ?? 'Section';
const projectBars = (project: Project) => project.sequence.reduce((bars, name) => bars + (name === FILL ? 1 : project.sections[name]?.settings.bars ?? 0), 0);
const randomSeed = () => crypto.getRandomValues(new Uint32Array(1))[0] % 1_000_000_000;
// Imported presets carry a "[hash:index]" suffix to stay unique; hide it in lists.
const displayName = (name: string) => name.replace(/\s*\[[0-9a-f]{8}:\d+\]$/, '');
const pad = (value: number) => String(value).padStart(2, '0');

function Select({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  return <label className="row"><span>{label}</span><select value={value} aria-label={label} onChange={event => onChange(event.target.value)}>{values.map(option => <option key={option} value={option}>{option}</option>)}</select></label>;
}
function NumberField({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) {
  return <label className="row"><span>{label}</span><input type="number" inputMode="numeric" aria-label={label} min={min} max={max} value={Number.isFinite(value) ? value : ''} onChange={event => onChange(event.target.value === '' ? NaN : Number(event.target.value))} /></label>;
}
function Group({ title, aside, children }: { title: string; aside?: ReactNode; children: ReactNode }) {
  return <section className="group"><header><h2>{title}</h2>{aside !== undefined && <span>{aside}</span>}</header>{children}</section>;
}
function InstrumentPicker({ part, value, groups, onChange }: { part: Part; value: string | null; groups: Record<string, string[]>; onChange: (value: string | null) => void }) {
  const [type, setType] = useState('All types');
  const visible = type === 'All types' || !groups[type] ? groups : { [type]: groups[type] };
  const current = value ?? 'Mute';
  const listed = current === 'Mute' || Object.values(visible).some(names => names.includes(current));
  return <div className="instrument" style={{ '--part': COLORS[part] } as CSSProperties}>
    <div className="instrument-head"><span>{part}</span><select className="compact" aria-label={`${part} type`} value={type} onChange={event => setType(event.target.value)}>{['All types', ...Object.keys(groups)].map(option => <option key={option}>{option}</option>)}</select></div>
    <select aria-label={part} value={current} onChange={event => onChange(event.target.value === 'Mute' ? null : event.target.value)}>
      {!listed && <option value={current}>{displayName(current)}</option>}
      {Object.entries(visible).map(([group, names]) => <optgroup key={group} label={group}>{names.map(name => <option key={name} value={name}>{displayName(name)}</option>)}</optgroup>)}
      <option value="Mute">Mute</option>
    </select>
  </div>;
}

export default function App() {
  const [catalog, setCatalog] = useState<Catalog>();
  const [settings, setSettings] = useState<Settings>();
  const [instruments, setInstruments] = useState<Instruments>();
  const [mode, setMode] = useState<Mode>('generate');
  const [project, setProject] = useState<Project>(structuredClone(EMPTY));
  const [saved, setSaved] = useState<Saved[]>([]);
  const [imported, setImported] = useState<Library[]>([]);
  const [importFamily, setImportFamily] = useState('Auto');
  const [sectionName, setSectionName] = useState('A');
  const [projectName, setProjectName] = useState('My song');
  const [selected, setSelected] = useState('');
  const [section, setSection] = useState<Composition>();
  const [song, setSong] = useState<Composition>();
  const [auto, setAuto] = useState({ length: 'Standard', style: 'From generator', energy: 65, candidates: 4 });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const [playing, setPlaying] = useState<'generate' | 'song' | null>(null);
  const [position, setPosition] = useState(0);
  const [signalLevel, setSignalLevel] = useState(0);
  const [loop, setLoop] = useState(true);
  const [volume, setVolume] = useState(.8);
  const [ready, setReady] = useState(false);
  const [license, setLicense] = useState<{ title: string; text: string } | null>(null);
  const playingRef = useRef(playing);
  const operation = useRef(0);
  const sectionRequest = useRef(0);
  const songRequest = useRef(0);
  const lastSectionKey = useRef('');
  const exportAbort = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const fontInput = useRef<HTMLInputElement>(null);
  const latestSave = useRef('');
  const saveQueue = useRef(Promise.resolve());
  const currentKey = settings && instruments ? JSON.stringify([settings, instruments]) : '';
  const showError = (error: unknown) => setError(error instanceof Error ? error.message : String(error));
  const showLicense = async (title: string, path: string) => { try { const response = await fetch(path); if (!response.ok) throw new Error('Could not load the bundled license.'); setLicense({ title, text: await response.text() }); } catch (error) { showError(error); } };
  const stop = () => { operation.current++; exportAbort.current?.abort(); exportAbort.current = null; player.stop(); playingRef.current = null; setPlaying(null); setPosition(0); setBusy(''); };
  const updateProject = (next: Project) => { if (playingRef.current === 'song') stop(); setProject(next); };
  const refreshCatalog = async () => { const data = await engine.catalog(); player.bundled = data.libraries; setCatalog(data); return data; };

  useEffect(() => {
    let active = true;
    (async () => {
      // Imported libraries must be registered before the catalog lists them.
      const libraries = await storedMetadata().catch(() => [] as Library[]);
      const restored: Library[] = [];
      for (const library of libraries) {
        try {
          const updated = await engine.registerLibrary(library);
          if (updated.presets.some((preset, index) => preset.bank !== library.presets[index].bank)) await remapLibrary(updated);
          restored.push(updated);
        } catch { /* Keep stored data available for reimport if a library is damaged. */ }
      }
      const [data, stored] = await Promise.all([refreshCatalog(), Preferences.get({ key: STORAGE })]);
      if (!active) return;
      setImported(restored);
      let state: Record<string, unknown> = {};
      if (stored.value) { try { state = JSON.parse(stored.value); } catch { /* Start with safe defaults. */ } }
      setSettings({ ...data.defaults, ...((state.settings as Settings) ?? { seed: randomSeed() }) });
      setInstruments({ ...data.defaultInstruments, ...((state.instruments as Instruments) ?? {}) });
      if (state.project) { try { setProject(await engine.validate(state.project)); } catch { setError('The saved draft could not be restored. Import a saved song project if you have one.'); } }
      if (Array.isArray(state.saved)) setSaved(state.saved as Saved[]);
      if (typeof state.projectName === 'string') setProjectName(state.projectName);
      if (typeof state.volume === 'number') setVolume(Math.max(0, Math.min(1, state.volume)));
      setReady(true);
    })().catch(showError);
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!ready) return;
    latestSave.current = JSON.stringify({ settings, instruments, project, saved, projectName, volume });
    const timer = setTimeout(() => {
      const value = latestSave.current;
      saveQueue.current = saveQueue.current.catch(() => {}).then(() => Preferences.set({ key: STORAGE, value })).catch(showError);
    }, 500);
    return () => clearTimeout(timer);
  }, [ready, settings, instruments, project, saved, projectName, volume]);
  useEffect(() => { player.volume = volume; }, [volume]);
  useEffect(() => { player.loop = loop; }, [loop]);
  useEffect(() => {
    const pause = () => {
      stop(); void player.suspend();
      if (latestSave.current) { const value = latestSave.current; saveQueue.current = saveQueue.current.catch(() => {}).then(() => Preferences.set({ key: STORAGE, value })).catch(showError); }
    };
    const listener = Capacitor.isNativePlatform() ? NativeApp.addListener('appStateChange', state => { if (!state.isActive) pause(); }) : null;
    const onHidden = () => { if (document.hidden) pause(); };
    document.addEventListener('visibilitychange', onHidden);
    const timer = setInterval(() => {
      if (playingRef.current) {
        if (player.playing) { setPosition(player.position); setSignalLevel(player.signalLevel); }
        else if (!player.preparing) { playingRef.current = null; setPlaying(null); setPosition(0); setSignalLevel(0); }
      }
    }, 100);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', onHidden); if (listener) void listener.then(handle => handle.remove()); };
  }, []);
  useEffect(() => {
    const request = ++sectionRequest.current;
    if (!ready || !settings || !instruments) return;
    if (currentKey === lastSectionKey.current) { setError(''); return; }
    const timer = setTimeout(() => {
      engine.section(settings, instruments).then(async output => {
        if (request !== sectionRequest.current) return;
        lastSectionKey.current = currentKey;
        setSection(output); setError('');
        if (playingRef.current === 'generate') {
          const at = player.position;
          await player.play(output.midi, at, output.libraries, output.mixProfile);
        }
      }).catch(error => { if (request === sectionRequest.current) showError(error); });
    }, 220);
    return () => clearTimeout(timer);
  }, [ready, currentKey]);
  useEffect(() => {
    const request = ++songRequest.current;
    if (!ready || !project.sequence.length) { setSong(undefined); return; }
    const timer = setTimeout(() => {
      engine.song(project).then(output => { if (request === songRequest.current) { setSong(output); setError(''); } }).catch(error => { if (request === songRequest.current) { setSong(undefined); showError(error); } });
    }, 180);
    return () => clearTimeout(timer);
  }, [ready, project]);

  const resolveSection = async () => {
    if (!settings || !instruments) throw new Error('The studio is still loading.');
    if (section && currentKey === lastSectionKey.current) return section;
    const output = await engine.section(settings, instruments); lastSectionKey.current = currentKey; setSection(output); return output;
  };
  const play = async (target: 'generate' | 'song') => {
    stop(); const token = operation.current;
    setError(''); setBusy('Loading instruments…');
    try {
      await player.unlock();
      const output = target === 'generate' ? await resolveSection() : await engine.song(project);
      if (token !== operation.current) return;
      if (target === 'song') setSong(output);
      await player.play(output.midi, 0, output.libraries, output.mixProfile);
      if (token !== operation.current) return;
      playingRef.current = target; setPlaying(target); setPosition(0); setNotice('');
    } catch (error) { if (token === operation.current) showError(error); }
    finally { if (token === operation.current) setBusy(''); }
  };
  const vary = async () => {
    if (!settings || !instruments) return;
    stop(); const token = operation.current; setError(''); setBusy('Generating…');
    try {
      await player.unlock();
      const output = await engine.variation(settings, instruments, randomSeed());
      if (token !== operation.current) return;
      lastSectionKey.current = JSON.stringify([output.settings, instruments]);
      setSettings(output.settings); setSection(output);
      await player.play(output.midi, 0, output.libraries, output.mixProfile);
      if (token !== operation.current) return;
      playingRef.current = 'generate'; setPlaying('generate');
    } catch (error) { if (token === operation.current) showError(error); }
    finally { if (token === operation.current) setBusy(''); }
  };
  const generateSong = async () => {
    if (!settings || !instruments) return;
    stop(); const token = operation.current; setError(''); setBusy('Writing song…');
    try {
      if (!Number.isInteger(auto.energy) || auto.energy < 0 || auto.energy > 100) throw new Error('Energy must be a whole number from 0 to 100.');
      if (!Number.isInteger(auto.candidates) || auto.candidates < 1 || auto.candidates > 8) throw new Error('Takes must be a whole number from 1 to 8.');
      const output = await engine.automaticSong({ ...settings, energy: auto.energy }, instruments, auto.length, auto.style, auto.candidates, project);
      if (token !== operation.current) return;
      setProject(output); setSelected(Object.keys(output.sections)[0] ?? '');
      setNotice(`Song appended: ${output.sequence.length} entries, ${projectBars(output)} bars. Your saved sections are preserved.`);
    } catch (error) { if (token === operation.current) showError(error); }
    finally { if (token === operation.current) setBusy(''); }
  };
  const importFont = async (file?: File) => {
    if (fontInput.current) fontInput.current.value = '';
    if (!file || !catalog) return;
    setError(''); setBusy('Importing instruments…');
    try {
      if (!/\.sf2$/i.test(file.name)) throw new Error('Choose a SoundFont (.sf2) file.');
      if (file.size > MAX_FONT) throw new Error('SF2 imports are limited to 64 MB per file.');
      const known = new Set([...catalog.libraries.map(library => library.id)]);
      const { metadata, buffer } = await engine.importFont(await file.arrayBuffer(), file.name, importFamily);
      if (known.has(metadata.id)) { setNotice(`${metadata.name} is already installed.`); return; }
      try { await saveLibrary({ metadata, bytes: buffer }); }
      catch (error) { await engine.unregisterLibrary(metadata.id); throw error; }
      await refreshCatalog();
      setImported(list => [...list.filter(library => library.id !== metadata.id), metadata]);
      setNotice(`Added ${metadata.presets.length} instrument${metadata.presets.length === 1 ? '' : 's'} from ${metadata.name}.`);
    } catch (error) { showError(error); }
    finally { setBusy(''); }
  };
  const removeLibrary = async (library: Library) => {
    const labels = new Set(library.presets.map(preset => preset.label));
    const allInstruments: (string | null)[] = [
      ...Object.values(project.sections).flatMap(s => Object.values(s.instruments)),
      ...(instruments ? Object.values(instruments) : [])
    ];
    const used = allInstruments.some(name => name !== null && labels.has(name));
    if (used) { setError(`${library.name} is used by the current song or generator. Choose other instruments first.`); return; }
    try {
      await deleteLibrary(library.id); await engine.unregisterLibrary(library.id); await refreshCatalog();
      setImported(list => list.filter(item => item.id !== library.id)); setNotice(`Removed ${library.name}.`);
    } catch (error) { showError(error); }
  };
  const capture = async () => {
    if (!settings || !instruments) return;
    const name = sectionName.trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$/.test(name)) { setError('Use a section name of up to 32 letters, numbers, spaces, underscores, or hyphens.'); return; }
    if (!project.sections[name] && Object.keys(project.sections).length >= 32) { setError('A song can hold 32 saved sections. Update an existing section or remove an unused one.'); return; }
    try {
      await resolveSection();
      const sections = { ...project.sections, [name]: { settings: structuredClone(settings), instruments: structuredClone(instruments) } };
      updateProject({ ...project, sections }); setSelected(name); setSectionName(nextName(sections)); setNotice(`Saved section ${name}.`); setError('');
    } catch (error) { showError(error); }
  };
  const append = (name: string) => {
    if (!name) { setError('Save a section first.'); return; }
    const next = { ...project, sequence: [...project.sequence, name] };
    if (next.sequence.length > 128 || projectBars(next) > 256) { setError('A song can contain up to 128 entries and 256 bars.'); return; }
    updateProject(next); setError('');
  };
  const move = (index: number, direction: number) => {
    const sequence = [...project.sequence], other = index + direction;
    if (other < 0 || other >= sequence.length) return;
    [sequence[index], sequence[other]] = [sequence[other], sequence[index]];
    updateProject({ ...project, sequence });
  };
  const loadSection = (name: string) => {
    const value = project.sections[name]; stop(); setSettings(structuredClone(value.settings)); setInstruments(structuredClone(value.instruments)); setSectionName(name); setMode('generate'); setNotice(`Editing ${name}. Save under the same name to update it everywhere.`);
  };
  const exportMusic = async (format: 'midi' | 'wav') => {
    stop(); const token = operation.current; setError(''); setBusy(format === 'wav' ? 'Rendering WAV…' : 'Preparing MIDI…');
    try {
      const output = mode === 'song' ? await engine.song(project) : await resolveSection();
      if (token !== operation.current) return;
      const name = (mode === 'song' ? projectName : 'section-' + output.settings?.seed).replace(/[^a-zA-Z0-9 _-]/g, '').trim() || 'music';
      if (format === 'midi') await shareMidi(output, name);
      else {
        const controller = new AbortController(); exportAbort.current = controller;
        const blob = await renderWav(output, catalog?.libraries ?? [], value => setBusy(`Rendering WAV ${Math.round(value * 100)}%`), controller.signal);
        if (token !== operation.current) return;
        await shareFile(name + '.wav', blob, 'audio/wav');
      }
      setNotice('File ready.');
    } catch (error) { if (token === operation.current) showError(error); }
    finally { if (token === operation.current) { setBusy(''); exportAbort.current = null; } }
  };
  const saveProject = () => {
    const name = projectName.trim(); if (!name) { setError('Name the song first.'); return; }
    const record = { name, project: structuredClone(project), updated: new Date().toISOString() };
    setSaved([record, ...saved.filter(song => song.name !== name)]); setNotice(`Saved ${name} on this device.`); setError('');
  };
  const importProject = async (file?: File) => {
    if (!file) return;
    try {
      if (file.size > 2_000_000) throw new Error('Choose a Royalty Free Music Maker .song.json project, not an audio file.');
      const parsed = await engine.validate(JSON.parse(await file.text()));
      stop(); setProject(parsed); setProjectName(file.name.replace(/\.song\.json$|\.json$/i, '')); setSelected(Object.keys(parsed.sections)[0] ?? ''); setMode('song'); setNotice('Imported song project.'); setError('');
    } catch (error) { showError(error); }
    if (input.current) input.current.value = '';
  };

  if (!catalog || !settings || !instruments || !ready) return <main className="loading"><h1>Royalty Free Music Maker</h1>{error ? <><p role="alert">{error}</p><button onClick={() => location.reload()}>Try again</button></> : <><p>Loading the engine and instruments</p><div className="loading-bar"><i /></div></>}</main>;
  const set = <K extends keyof Settings>(key: K, value: Settings[K]) => setSettings({ ...settings, [key]: value });
  const active = playing === 'song' ? song : section;
  const activeBar = active ? Math.min(active.bars, Math.floor(position * active.bpm / 240) + 1) : 1;
  const selectedName = project.sections[selected] ? selected : Object.keys(project.sections)[0] ?? '';
  const scaleShort = settings.scale.replace('Natural minor', 'min').replace('Major', 'maj');
  const soundCount = catalog.instruments.length;
  return <div className="app-shell">
    {license && <div className="modal-backdrop"><section className="license-modal" role="dialog" aria-modal="true" aria-label={license.title} onKeyDown={event => { if (event.key === 'Escape') setLicense(null); }}><header><h2>{license.title}</h2><button autoFocus onClick={() => setLicense(null)}>Close</button></header><pre tabIndex={0}>{license.text}</pre></section></div>}
    <header className="topbar"><h1>Royalty Free Music Maker</h1><span className="readout">{settings.key.split(' ')[0]} {scaleShort} · {Number.isFinite(settings.bpm) ? settings.bpm : '—'} bpm</span></header>
    <main className="page">
      {error && <div className="message error" role="alert"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}
      {notice && <div className="message success" role="status"><span>{notice}</span><button aria-label="Dismiss message" onClick={() => setNotice('')}>×</button></div>}
      {mode === 'generate' && <>
        <Group title="Composition" aside="4/4">
          <div className="rows">
            <Select label="Key" value={settings.key} values={catalog.keys} onChange={value => set('key', value)} />
            <Select label="Scale" value={settings.scale} values={catalog.scales} onChange={value => set('scale', value)} />
            <Select label="Complexity" value={settings.complexity} values={catalog.complexities} onChange={value => set('complexity', value)} />
            <NumberField label="Tempo · BPM" value={settings.bpm} min={40} max={220} onChange={value => set('bpm', value)} />
            <NumberField label="Length · bars" value={settings.bars} min={1} max={32} onChange={value => set('bars', value)} />
            <NumberField label="Variation seed" value={settings.seed} min={0} max={999999999} onChange={value => set('seed', value)} />
          </div>
          {settings.section_role && settings.section_role !== 'Loop' && <p className="hint">Song part: {settings.section_role}, energy {settings.energy}. <button className="link" onClick={() => setSettings({ ...settings, section_role: 'Loop', energy: 65, hook_seed: null })}>Reset to a plain loop</button></p>}
        </Group>
        <Group title="Instruments" aside={`${soundCount} sounds`}>
          <label className="row"><span>Sound preset</span><select aria-label="Sound preset" defaultValue="" onChange={event => { const preset = catalog.soundPresets[event.target.value]; if (preset) { setInstruments(preset.instruments); setSettings({ ...settings, ...preset.settings }); } }}><option value="" disabled>Choose a starting sound</option>{Object.keys(catalog.soundPresets).map(name => <option key={name}>{name}</option>)}</select></label>
          <div className="instruments">{PARTS.filter(part => part !== 'Countermelody' || settings.countermelody).map(part => <InstrumentPicker key={part} part={part} value={instruments[part]} groups={part === 'Drums' ? catalog.kitGroups : catalog.instrumentGroups} onChange={value => setInstruments({ ...instruments, [part]: value })} />)}</div>
          <div className="import-row"><select className="compact" aria-label="Imported instrument type" value={importFamily} onChange={event => setImportFamily(event.target.value)}>{['Auto', ...catalog.families].map(option => <option key={option} value={option}>{option === 'Auto' ? 'Type: from file' : option}</option>)}</select><button disabled={Boolean(busy)} onClick={() => fontInput.current?.click()}>Import .sf2</button></div>
          <input className="file-input" type="file" accept=".sf2,audio/x-soundfont" ref={fontInput} onChange={event => importFont(event.target.files?.[0])} />
        </Group>
        <Group title="Playing">
          <div className="rows">
            <Select label="Chord pattern" value={settings.chord_style ?? catalog.defaults.chord_style} values={catalog.chordStyles} onChange={value => set('chord_style', value)} />
            <Select label="Bass pattern" value={settings.bass_style ?? catalog.defaults.bass_style} values={catalog.bassStyles} onChange={value => set('bass_style', value)} />
            <Select label="Playing feel" value={settings.feel ?? catalog.defaults.feel} values={catalog.feels} onChange={value => set('feel', value)} />
            <Select label="Phrasing / space" value={settings.phrasing ?? catalog.defaults.phrasing} values={catalog.phrasings} onChange={value => set('phrasing', value)} />
            <Select label="Chord voicing" value={settings.chord_voicing ?? 'Auto'} values={catalog.voicings} onChange={value => set('chord_voicing', value)} />
            <Select label="Strum pattern" value={settings.strum_pattern ?? 'Auto'} values={catalog.strums} onChange={value => set('strum_pattern', value)} />
            <Select label="Melody character" value={settings.melody_style ?? 'Motivic'} values={catalog.melodyStyles} onChange={value => set('melody_style', value)} />
            <label className="row"><span>Second melody / counterpoint</span><input aria-label="Second melody / counterpoint" type="checkbox" checked={settings.countermelody ?? false} onChange={event => set('countermelody', event.target.checked)} /></label>
            <Select label="Mix" value={settings.mix_profile ?? catalog.defaults.mix_profile ?? 'Balanced'} values={catalog.mixProfiles} onChange={value => set('mix_profile', value)} />
          </div>
        </Group>
        <Group title="Drums">
          <div className="rows">
            <Select label="Drum style" value={settings.drum_style} values={catalog.drumStyles} onChange={value => set('drum_style', value)} />
            <Select label="Drum complexity" value={settings.drum_complexity} values={catalog.drumComplexities} onChange={value => set('drum_complexity', value)} />
            <Select label="Drum fills" value={settings.drum_fills} values={catalog.drumFills} onChange={value => set('drum_fills', value)} />
          </div>
        </Group>
        <div className="actions"><button className="primary" disabled={Boolean(busy)} onClick={() => play('generate')}>Play</button><button disabled={Boolean(busy)} onClick={vary}>New variation</button></div>
        <PianoRoll music={section} beat={playing === 'generate' && section ? position * section.bpm / 60 : 0} />
        <Group title="Save section" aside={`${Object.keys(project.sections).length}/32`}>
          <div className="inline"><label className="field"><span>Section name</span><input value={sectionName} maxLength={32} aria-label="Section name" onChange={event => setSectionName(event.target.value)} placeholder="Verse, Chorus…" /></label><button onClick={capture} disabled={Boolean(busy)}>Save section</button></div>
        </Group>
      </>}
      {mode === 'song' && <fieldset className="song-controls" disabled={Boolean(busy)}>
        <Group title="Generate a full song">
          <p className="hint top">Intro, verses, choruses, bridge and outro around one hook. Uses the settings from Generate. Existing sections and arrangement entries stay in place; new sections are appended.</p>
          <div className="rows">
            <Select label="Length" value={auto.length} values={catalog.songLengths} onChange={length => setAuto({ ...auto, length })} />
            <Select label="Style" value={auto.style} values={catalog.songStyles} onChange={style => setAuto({ ...auto, style })} />
            <NumberField label="Energy · 0–100" value={auto.energy} min={0} max={100} onChange={energy => setAuto({ ...auto, energy })} />
            <NumberField label="Takes to compare" value={auto.candidates} min={1} max={8} onChange={candidates => setAuto({ ...auto, candidates })} />
          </div>
          <div className="actions"><button className="primary" disabled={Boolean(busy)} onClick={generateSong}>Generate and append song</button></div>
        </Group>
        <Group title="Sections" aside={`${Object.keys(project.sections).length}/32`}>{Object.keys(project.sections).length ? <>
          <div className="inline"><label className="field"><span>Saved section</span><select aria-label="Saved section" value={selectedName} onChange={event => setSelected(event.target.value)}>{Object.keys(project.sections).map(name => <option key={name}>{name}</option>)}</select></label><button onClick={() => append(selectedName)}>Add to song</button></div>
          <div className="chips">{Object.entries(project.sections).map(([name, value]) => <button key={name} onClick={() => loadSection(name)}><b>{name}</b><span>{value.settings.bars} bars · {value.settings.section_role && value.settings.section_role !== 'Loop' ? value.settings.section_role : `${value.settings.key} ${value.settings.scale}`}</span></button>)}</div>
          <button className="link" onClick={() => { if (project.sequence.includes(selectedName)) { setError('Remove this section from the arrangement before deleting it.'); return; } const sections = { ...project.sections }; delete sections[selectedName]; updateProject({ ...project, sections }); }}>Delete selected section</button>
        </> : <p className="empty">No sections yet. Generate a song above, or save sections from Generate.</p>}</Group>
        <Group title="Arrangement" aside={`${projectBars(project)} bars`}>
          <div className="rows"><NumberField label="Song tempo · BPM" value={project.bpm} min={40} max={220} onChange={bpm => updateProject({ ...project, bpm })} /></div>
          <ol className="sequence">{project.sequence.map((name, index) => <li key={index} className={name === FILL ? 'fill' : ''}><span className="step">{pad(index + 1)}</span><div><b>{name === FILL ? 'Drum fill' : name}</b><span>{name === FILL ? '1 bar' : `${project.sections[name].settings.bars} bars · ${project.sections[name].settings.drum_style}`}</span></div><div className="step-actions"><button aria-label={`Move entry ${index + 1} up`} disabled={index === 0} onClick={() => move(index, -1)}>↑</button><button aria-label={`Move entry ${index + 1} down`} disabled={index === project.sequence.length - 1} onClick={() => move(index, 1)}>↓</button><button aria-label={`Remove entry ${index + 1}`} onClick={() => updateProject({ ...project, sequence: project.sequence.filter((_, at) => at !== index) })}>×</button></div></li>)}</ol>
          <button className="ghost full" onClick={() => append(FILL)}>+ Drum fill</button>
        </Group>
        <div className="actions"><button className="primary" disabled={Boolean(busy) || !project.sequence.length} onClick={() => play('song')}>Play song</button><button onClick={() => setMode('projects')}>Save project</button></div>
        <PianoRoll music={song} beat={playing === 'song' && song ? position * song.bpm / 60 : 0} />
      </fieldset>}
      {mode === 'projects' && <>
        <Group title="Current song" aside="Autosaved">
          <label className="field"><span>Project name</span><input value={projectName} maxLength={64} aria-label="Project name" onChange={event => setProjectName(event.target.value)} /></label>
          <div className="actions"><button className="primary" onClick={saveProject}>Save on device</button><button onClick={() => shareFile(projectName.replace(/[^a-zA-Z0-9 _-]/g, '') + '.song.json', new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' }), 'application/json').catch(showError)}>Share project</button></div>
          <button className="ghost full" onClick={() => input.current?.click()}>Import a song project</button>
          <input className="file-input" type="file" accept=".json,.song.json,application/json" ref={input} onChange={event => importProject(event.target.files?.[0])} />
          <p className="hint">Projects open in both the phone and desktop apps.</p>
        </Group>
        <Group title="On this device" aside={saved.length}>{saved.length ? <ul className="list">{saved.map(record => <li key={record.name}><div><b>{record.name}</b><span>{record.project.sequence.length} entries · {projectBars(record.project)} bars</span></div><button onClick={() => { stop(); setProject(structuredClone(record.project)); setProjectName(record.name); setMode('song'); setNotice(`Opened ${record.name}.`); }}>Open</button><button aria-label={`Delete ${record.name}`} onClick={() => setSaved(saved.filter(song => song.name !== record.name))}>×</button></li>)}</ul> : <p className="empty">Nothing saved yet.</p>}<button className="ghost full" onClick={async () => { try { const data = await (await fetch('/Example.song.json')).json(); stop(); setProject(await engine.validate(data)); setProjectName('Example song'); setMode('song'); } catch (error) { showError(error); } }}>Open example song</button></Group>
        <Group title="Imported instruments" aside={imported.length}>{imported.length ? <ul className="list">{imported.map(library => <li key={library.id}><div><b>{library.name}</b><span>{library.presets.length} instrument{library.presets.length === 1 ? '' : 's'} · {library.presets[0]?.category}</span></div><button aria-label={`Remove ${library.name}`} onClick={() => removeLibrary(library)}>Remove</button></li>)}</ul> : <p className="empty">Add your own SoundFont (.sf2) instruments from Generate → Instruments.</p>}</Group>
        <Group title="Credits">
          <p className="hint top">Sounds: GeneralUser GS by S. Christian Collins. Studio Upright and Studio Clean Guitar are public-domain (CC0) recordings. Everything runs on this device.</p>
          <div className="links"><button className="link" onClick={() => showLicense('Sound library license', '/soundfonts/LICENSE.txt')}>Sound library license</button><button className="link" onClick={() => showLicense('Studio instruments', '/soundfonts/featured/SOURCES.md')}>Studio instruments</button><button className="link" onClick={() => showLicense('Third-party notices', '/THIRD_PARTY_NOTICES.md')}>Third-party notices</button></div>
        </Group>
      </>}
      {mode !== 'projects' && <Group title="Export"><div className="actions"><button onClick={() => exportMusic('midi')} disabled={Boolean(busy) || (mode === 'song' && !project.sequence.length)}>Export MIDI</button><button onClick={() => exportMusic('wav')} disabled={Boolean(busy) || (mode === 'song' && !project.sequence.length)}>Export WAV</button></div></Group>}
    </main>
    <aside className="transport" aria-label="Playback controls">
      <button className="transport-play" aria-label={mode === 'song' ? 'Play current song' : 'Play current section'} disabled={Boolean(busy) || (mode === 'song' && !project.sequence.length)} onClick={() => play(mode === 'song' ? 'song' : 'generate')}>▶</button>
      <button className="transport-stop" aria-label="Stop" onClick={stop} disabled={!playing && !busy}>■</button>
      <div className="transport-status"><span className={playing ? 'on' : ''}>{busy || (playing ? `Playing ${playing === 'song' ? 'song' : 'section'}` : 'Stopped')}</span><span className="counter">{playing ? `${pad(activeBar)}/${pad(active?.bars ?? 1)}` : '--/--'}</span></div>
      <span className="audio-meter" role="meter" aria-label="Audio output level" aria-valuemin={0} aria-valuemax={1} aria-valuenow={playing ? signalLevel : 0}><i style={{ transform: `scaleX(${Math.min(1, signalLevel * 4)})` }} /></span>
      <label className="loop"><input type="checkbox" checked={loop} onChange={event => setLoop(event.target.checked)} />Loop</label>
      <input className="volume" type="range" aria-label="Volume" min={0} max={1} step={.01} value={volume} onChange={event => setVolume(Number(event.target.value))} />
    </aside>
    <nav className="tabs" aria-label="Main navigation">{([['generate', 'Generate'], ['song', 'Song'], ['projects', 'Projects']] as const).map(([target, label]) => <button key={target} className={mode === target ? 'selected' : ''} aria-current={mode === target ? 'page' : undefined} onClick={() => setMode(target)}>{label}</button>)}</nav>
  </div>;
}
