import type { Sequencer, WorkletSynthesizer } from 'spessasynth_lib';
import { GENERAL, loadLibrary } from './libraries';
import type { Library } from './types';
import { LiveBus } from './audio-bus';

export function decodeBase64(value: string): Uint8Array<ArrayBuffer> {
  const text = atob(value);
  return Uint8Array.from(text, character => character.charCodeAt(0));
}

class Player {
  private context?: AudioContext;
  private synth?: WorkletSynthesizer;
  private seq?: Sequencer;
  private gain?: GainNode;
  private bus?: LiveBus;
  private loading?: Promise<void>;
  private level = .8;
  private looping = true;
  private analyser?: AnalyserNode;
  private meter = new Float32Array(256);
  private serial = 0;
  private preparingPlayback = false;
  private queue: Promise<void> = Promise.resolve();
  private loaded = new Set<string>();
  /** Bundled library descriptors from the engine catalog (studio instruments). */
  bundled: Library[] = [];

  async unlock() {
    if (typeof AudioContext === 'undefined' || typeof AudioWorkletNode === 'undefined') throw new Error('Audio playback is unavailable in this browser. Use the installed app or a current Safari/Chrome browser.');
    this.context ??= new AudioContext({ latencyHint: 'interactive' });
    // This is called directly from the tap handler, before engine/network awaits.
    if (this.context.state !== 'running') await this.context.resume();
  }
  async ready() {
    await this.unlock();
    if (!this.loading) this.loading = (async () => {
      const { Sequencer, WorkletSynthesizer } = await import('spessasynth_lib');
      const context = this.context!;
      await context.audioWorklet.addModule(new URL('/audio/processor.js', location.href).href);
      this.synth = new WorkletSynthesizer(context);
      await this.synth.isReady;
      this.synth.setLogLevel(false, true, false);
      this.gain = context.createGain();
      this.gain.gain.value = this.level;
      this.bus = new LiveBus(context, this.gain);
      this.synth.connect(this.bus.input);
      this.analyser = context.createAnalyser();
      this.analyser.fftSize = 512;
      this.gain.connect(this.analyser);
      this.analyser.connect(context.destination);
      await this.synth.soundBankManager.addSoundBank(await loadLibrary(GENERAL, this.bundled), GENERAL);
      this.loaded = new Set([GENERAL]);
      this.seq = new Sequencer(this.synth);
      this.seq.skipToFirstNoteOn = false;
    })().catch(error => { this.loading = undefined; this.synth?.destroy(); this.synth = undefined; throw error; });
    return this.loading;
  }
  /** Load studio or imported libraries only when a composition uses them. */
  private async ensure(libraries: string[]) {
    for (const id of this.loaded) {
      if (id !== GENERAL && !libraries.includes(id)) {
        await this.synth!.soundBankManager.deleteSoundBank(id);
        this.loaded.delete(id);
      }
    }
    for (const id of libraries) {
      if (this.loaded.has(id)) continue;
      await this.synth!.soundBankManager.addSoundBank(await loadLibrary(id, this.bundled), id);
      this.loaded.add(id);
    }
  }
  play(midi: string, start = 0, libraries: string[] = [], profile = 'Balanced') {
    const ticket = ++this.serial;
    this.preparingPlayback = true;
    const task = this.queue.then(async () => {
      if (ticket !== this.serial) return;
      await this.playNow(midi, start, ticket, libraries, profile);
    });
    const finished = task.finally(() => { if (ticket === this.serial) this.preparingPlayback = false; });
    this.queue = finished.catch(() => {});
    return finished;
  }
  private async playNow(midi: string, start: number, ticket: number, libraries: string[], profile: string) {
    await this.ready();
    if (ticket !== this.serial) return;
    this.halt();
    await this.ensure(libraries);
    this.bus?.configure(profile);
    if (ticket !== this.serial) return;
    this.halt();
    const seq = this.seq!;
    await new Promise<void>((resolve, reject) => {
      const id = 'mobile-load-' + ticket;
      const clear = () => { clearTimeout(timer); seq.eventHandler.removeEvent('songChange', id); seq.eventHandler.removeEvent('midiError', id); };
      const timer = setTimeout(() => { clear(); reject(new Error('Loading the MIDI timed out. Try Play again.')); }, 30000);
      seq.eventHandler.addEvent('songChange', id, () => { clear(); resolve(); });
      seq.eventHandler.addEvent('midiError', id, event => { clear(); reject(new Error(String(event))); });
      seq.loadNewSongList([{ binary: decodeBase64(midi).buffer, fileName: 'composition.mid' }]);
    });
    // Loading also sends a pause event after songChange. Use a same-port
    // round trip so WebKit cannot deliver that stale pause after play().
    await seq.getMIDI();
    if (ticket !== this.serial) return;
    seq.loopCount = this.looping ? Infinity : 0;
    if (start > 0) seq.currentTime = Math.min(start, Math.max(0, seq.duration - .01));
    seq.play();
  }
  private halt() { this.seq?.pause(); this.synth?.stopAll(true); }
  stop() { ++this.serial; this.preparingPlayback = false; this.halt(); }
  get preparing() { return this.preparingPlayback; }
  async suspend() { this.stop(); if (this.context?.state === 'running') await this.context.suspend(); }
  set volume(value: number) { this.level = value; if (this.gain) this.gain.gain.setTargetAtTime(value, this.context!.currentTime, .02); }
  set loop(value: boolean) { this.looping = value; if (this.seq) this.seq.loopCount = value ? Infinity : 0; }
  get signalLevel() {
    if (!this.analyser) return 0;
    this.analyser.getFloatTimeDomainData(this.meter);
    return Math.min(1, this.meter.reduce((peak, sample) => Math.max(peak, Math.abs(sample)), 0));
  }
  get position() { return Math.max(0, this.seq?.currentHighResolutionTime ?? 0); }
  get playing() { return Boolean(this.seq && !this.seq.paused && !this.seq.isFinished); }
}
export const player = new Player();
