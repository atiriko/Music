export type Part = 'Melody' | 'Chords' | 'Bass' | 'Drums';
export interface Settings {
  key: string; scale: string; complexity: string; bpm: number; bars: number; seed: number;
  chord_style: string; bass_style: string; feel: string; phrasing: string;
  drum_style: string; drum_complexity: string; drum_fills: string;
  hook_seed?: number | null; section_role?: string; energy?: number; mix_profile?: string;
}
export type Instruments = Record<Part, string | null>;
export interface Note { part: Part; pitch: number; beat: number; duration: number; velocity: number }
export interface Section { settings: Settings; instruments: Instruments }
export interface Project { version: 1; bpm: number; sections: Record<string, Section>; sequence: string[]; metadata?: Record<string, unknown> }
export interface Composition {
  settings?: Settings; bpm: number; bars: number; notes: Note[]; midi: string; boundaries: [number, string][];
  libraries?: string[]; mixProfile?: string;
}
export interface LibraryPreset { label: string; name: string; category: string; program: number; bank: number; gm_program: number; drums: boolean; offset: number }
export interface Library { id: string; name: string; filename: string; sha256: string; presets: LibraryPreset[]; relative_file?: string }
export interface Catalog {
  keys: string[]; scales: string[]; complexities: string[]; instruments: string[]; kits: string[];
  chordStyles: string[]; bassStyles: string[]; feels: string[]; phrasings: string[];
  drumStyles: string[]; drumComplexities: string[]; drumFills: string[];
  defaults: Settings; defaultInstruments: Instruments;
  instrumentGroups: Record<string, string[]>; kitGroups: Record<string, string[]>; families: string[];
  libraries: Library[]; mixProfiles: string[]; songLengths: string[]; songStyles: string[];
}
export const PARTS: Part[] = ['Melody', 'Chords', 'Bass', 'Drums'];
export const COLORS: Record<Part, string> = { Melody: '#f0c36a', Chords: '#8ab4a0', Bass: '#d77f58', Drums: '#a7a39b' };
export const FILL = '[Drum fill]';
