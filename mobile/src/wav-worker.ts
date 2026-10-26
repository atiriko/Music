import { BasicMIDI, SoundBankLoader, SpessaSynthProcessor, SpessaSynthSequencer } from 'spessasynth_core';
import { GENERAL, loadLibrary } from './libraries';
import { OfflineBus } from './audio-bus';

self.onmessage = async ({ data }) => {
  try {
    const rate = 22050;
    const synth = new SpessaSynthProcessor(rate, { maxBufferSize: 128 });
    // Load only the libraries this composition uses (GM, studio, or imported).
    for (const id of [GENERAL, ...(data.libraries ?? []).filter((id: string) => id !== GENERAL)]) {
      synth.soundBankManager.addSoundBank(SoundBankLoader.fromArrayBuffer(await loadLibrary(id, data.bundled ?? [])), id);
    }
    await synth.processorInitialized;
    const seq = new SpessaSynthSequencer(synth);
    seq.skipToFirstNoteOn = false;
    seq.loopCount = 0;
    seq.loadNewSongList([BasicMIDI.fromArrayBuffer(data.midi)]);
    seq.play();
    const bus = new OfflineBus(rate, data.mixProfile ?? 'Balanced');
    const frames = Math.ceil((data.seconds + 1) * rate);
    const buffer = new ArrayBuffer(44 + frames * 4);
    const view = new DataView(buffer);
    const ascii = (at: number, text: string) => [...text].forEach((letter, i) => view.setUint8(at + i, letter.charCodeAt(0)));
    ascii(0, 'RIFF'); view.setUint32(4, buffer.byteLength - 8, true); ascii(8, 'WAVEfmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 2, true);
    view.setUint32(24, rate, true); view.setUint32(28, rate * 4, true); view.setUint16(32, 4, true);
    view.setUint16(34, 16, true); ascii(36, 'data'); view.setUint32(40, frames * 4, true);
    const left = new Float32Array(128), right = new Float32Array(128);
    let peak = 0;
    for (let frame = 0; frame < frames; frame += 128) {
      seq.processTick();
      const count = Math.min(128, frames - frame);
      synth.process(left, right, 0, count);
      bus.process(left, right, count);
      for (let i = 0; i < count; i++) {
        const fade = Math.min(1, (frames - frame - i - 1) / (rate * .05));
        peak = Math.max(peak, Math.abs(left[i]), Math.abs(right[i]));
        view.setInt16(44 + (frame + i) * 4, Math.round(Math.max(-1, Math.min(1, left[i] * fade)) * 32767), true);
        view.setInt16(46 + (frame + i) * 4, Math.round(Math.max(-1, Math.min(1, right[i] * fade)) * 32767), true);
      }
      if (frame % (128 * 256) === 0) self.postMessage({ progress: frame / frames });
    }
    self.postMessage({ buffer, peak }, { transfer: [buffer] });
  } catch (error) { self.postMessage({ error: String(error instanceof Error ? error.message : error) }); }
};
