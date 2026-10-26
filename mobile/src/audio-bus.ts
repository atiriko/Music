/** Shared profile settings for live Web Audio and offline sample processing. */
export function busProfile(name = 'Balanced') {
  return { highpass: 28, bass: name === 'Punchy' ? 1.5 : 0,
    treble: name === 'Warm' ? -3 : -.8, threshold: name === 'Punchy' ? -19 : -16,
    ratio: name === 'Punchy' ? 2.8 : 2, attack: .015, release: .18 };
}

export class LiveBus {
  private highpass: BiquadFilterNode;
  private bass: BiquadFilterNode;
  private treble: BiquadFilterNode;
  private compressor: DynamicsCompressorNode;
  constructor(context: AudioContext, output: AudioNode) {
    this.highpass = context.createBiquadFilter(); this.highpass.type = 'highpass';
    this.bass = context.createBiquadFilter(); this.bass.type = 'lowshelf'; this.bass.frequency.value = 160;
    this.treble = context.createBiquadFilter(); this.treble.type = 'highshelf'; this.treble.frequency.value = 4200;
    this.compressor = context.createDynamicsCompressor(); this.compressor.knee.value = 12;
    this.highpass.connect(this.bass).connect(this.treble).connect(this.compressor).connect(output);
    this.configure();
  }
  get input() { return this.highpass; }
  configure(name = 'Balanced') {
    const profile = busProfile(name);
    this.highpass.frequency.value = profile.highpass;
    this.bass.gain.value = profile.bass; this.treble.gain.value = profile.treble;
    this.compressor.threshold.value = profile.threshold; this.compressor.ratio.value = profile.ratio;
    this.compressor.attack.value = profile.attack; this.compressor.release.value = profile.release;
  }
}

/** Streaming tone shaping and smooth compression in the WAV worker. */
export class OfflineBus {
  private previous = [0, 0]; private hp = [0, 0]; private low = [0, 0]; private air = [0, 0];
  private envelope = 0;
  constructor(private rate: number, private name = 'Balanced') {}
  process(left: Float32Array, right: Float32Array, count: number) {
    const p = busProfile(this.name), threshold = 10 ** (p.threshold / 20);
    const hp = Math.exp(-2 * Math.PI * p.highpass / this.rate);
    const low = 1 - Math.exp(-2 * Math.PI * 160 / this.rate), air = 1 - Math.exp(-2 * Math.PI * 4200 / this.rate);
    const attack = Math.exp(-1 / (this.rate * p.attack)), release = Math.exp(-1 / (this.rate * p.release));
    const channels = [left, right];
    for (let i = 0; i < count; i++) {
      for (let channel = 0; channel < 2; channel++) {
        const sample = channels[channel][i];
        this.hp[channel] = hp * (this.hp[channel] + sample - this.previous[channel]); this.previous[channel] = sample;
        this.low[channel] += low * (this.hp[channel] - this.low[channel]);
        this.air[channel] += air * (this.hp[channel] - this.air[channel]);
        channels[channel][i] = this.air[channel] + (this.hp[channel] - this.air[channel]) * 10 ** (p.treble / 20) + this.low[channel] * (10 ** (p.bass / 20) - 1);
      }
      const peak = Math.max(Math.abs(left[i]), Math.abs(right[i]));
      const smooth = peak > this.envelope ? attack : release;
      this.envelope = smooth * this.envelope + (1 - smooth) * peak;
      const gain = this.envelope > threshold ? (threshold / this.envelope) ** (1 - 1 / p.ratio) : 1;
      left[i] = .95 * Math.tanh(left[i] * gain * 1.1 / .95);
      right[i] = .95 * Math.tanh(right[i] * gain * 1.1 / .95);
    }
  }
}
