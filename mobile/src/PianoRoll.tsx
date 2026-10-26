import { useEffect, useRef, useState } from 'react';
import type { Composition, Part } from './types';
import { COLORS } from './types';

export function PianoRoll({ music, beat = 0 }: { music?: Composition; beat?: number }) {
  const [part, setPart] = useState('All parts');
  const [zoom, setZoom] = useState('Fit');
  const scroll = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [viewport, setViewport] = useState(320);
  const [left, setLeft] = useState(0);
  const total = Math.max(4, (music?.bars ?? 1) * 4);
  const scale = (viewport - 24) / (zoom === 'Fit' ? total : Number(zoom) * 4);
  const width = Math.max(viewport, total * scale + 24);
  useEffect(() => {
    const observer = new ResizeObserver(entries => setViewport(entries[0].contentRect.width));
    if (scroll.current) observer.observe(scroll.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const ratio = devicePixelRatio || 1;
    element.width = Math.round(viewport * ratio); element.height = 224 * ratio;
    const ctx = element.getContext('2d')!;
    ctx.scale(ratio, ratio); ctx.fillStyle = '#0f0e0d'; ctx.fillRect(0, 0, viewport, 224);
    const notes = (music?.notes ?? []).filter(note => part === 'All parts' || note.part === part);
    if (!notes.length) { ctx.fillStyle = '#8f897f'; ctx.font = '13px system-ui'; ctx.fillText('No notes yet', 20, 110); return; }
    const low = Math.min(...notes.map(note => note.pitch)) - 2;
    const high = Math.max(...notes.map(note => note.pitch)) + 2;
    const row = 174 / (high - low + 1);
    ctx.font = '10px system-ui';
    for (let pitch = low; pitch <= high; pitch++) if (pitch % 12 === 0) {
      const y = 42 + (high - pitch) * row;
      ctx.strokeStyle = '#24221f'; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(viewport, y); ctx.stroke();
      ctx.fillStyle = '#6f6a62'; ctx.fillText('C' + (Math.floor(pitch / 12) - 1), 3, y - 3);
    }
    const firstBar = Math.max(0, Math.floor(left / (4 * scale)));
    for (let bar = firstBar; bar <= Math.min(total / 4, firstBar + viewport / (scale * 4) + 1); bar++) {
      const x = 16 + bar * 4 * scale - left;
      ctx.strokeStyle = '#24221f'; ctx.beginPath(); ctx.moveTo(x, 20); ctx.lineTo(x, 224); ctx.stroke();
      if (zoom !== 'Fit' || total / 4 <= 16 || bar % Math.ceil(total / 64) === 0) { ctx.fillStyle = '#8f897f'; ctx.fillText(String(bar + 1), x + 3, 30); }
    }
    for (const [index, [start, name]] of (music?.boundaries ?? []).entries()) {
      const end = music?.boundaries[index + 1]?.[0] ?? total;
      const x = 16 + start * scale - left;
      ctx.fillStyle = index % 2 ? '#2c2a27' : '#232120'; ctx.fillRect(x, 0, (end - start) * scale, 17);
      ctx.fillStyle = '#ebe6dd'; ctx.fillText(name === '[Drum fill]' ? 'Fill' : name, Math.max(4, x + 4), 12);
    }
    for (const note of notes) {
      const x = 16 + note.beat * scale - left;
      const size = Math.max(2, note.duration * scale);
      if (x + size < 0 || x > viewport) continue;
      ctx.fillStyle = COLORS[note.part]; ctx.fillRect(x, 42 + (high - note.pitch) * row - 1, size, Math.max(2, row * .65));
    }
    if (beat > 0) {
      const x = 16 + Math.min(beat, total) * scale - left;
      ctx.strokeStyle = '#ff6b1a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, 17); ctx.lineTo(x, 224); ctx.stroke();
    }
  }, [music, beat, part, zoom, viewport, left, scale, total]);
  useEffect(() => {
    if (beat <= 0 || !scroll.current) return;
    const x = beat * scale;
    if (x < scroll.current.scrollLeft || x > scroll.current.scrollLeft + viewport - 24) scroll.current.scrollLeft = Math.max(0, x - 24);
  }, [beat, scale, viewport]);
  return <section className="roll" aria-label="MIDI output">
    <header><h2 className="group-title">MIDI · {music?.notes.length ?? 0} notes</h2><div className="roll-controls">
      <select aria-label="MIDI track" value={part} onChange={event => setPart(event.target.value)}>{['All parts', 'Melody', 'Chords', 'Bass', 'Drums'].map(value => <option key={value}>{value}</option>)}</select>
      <select aria-label="MIDI zoom" value={zoom} onChange={event => { setZoom(event.target.value); scroll.current!.scrollLeft = 0; }}>{['Fit', '4', '8', '16'].map(value => <option key={value} value={value}>{value === 'Fit' ? 'Fit' : value + ' bars'}</option>)}</select>
    </div></header>
    <div className="roll-scroll" ref={scroll} onScroll={event => setLeft(event.currentTarget.scrollLeft)}><div style={{ width, height: 224 }}><canvas ref={canvas} style={{ width: viewport, height: 224 }} role="img" aria-label={`Piano roll with ${music?.notes.length ?? 0} MIDI notes`} /></div></div>
    <div className="legend">{(Object.keys(COLORS) as Part[]).map(name => <span key={name}><i style={{ background: COLORS[name] }} />{name}</span>)}</div>
  </section>;
}
