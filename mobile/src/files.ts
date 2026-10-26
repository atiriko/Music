import { Capacitor } from '@capacitor/core';
import { Directory, Filesystem } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';
import { decodeBase64 } from './player';
import type { Composition, Library } from './types';

export async function shareFile(name: string, data: Blob | Uint8Array<ArrayBuffer>, type: string) {
  const blob = data instanceof Blob ? data : new Blob([data], { type });
  if (Capacitor.isNativePlatform()) {
    const encoded = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(',')[1]);
      reader.onerror = () => reject(new Error('Could not prepare this file.'));
      reader.readAsDataURL(blob);
    });
    const file = await Filesystem.writeFile({ path: 'exports/' + name, directory: Directory.Cache, data: encoded, recursive: true });
    await Share.share({ title: name, files: [file.uri], dialogTitle: 'Save or share your music' });
  } else {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
}
export function shareMidi(composition: Composition, name: string) { return shareFile(name + '.mid', decodeBase64(composition.midi), 'audio/midi'); }
export function renderWav(composition: Composition, bundled: Library[], onProgress: (value: number) => void, signal?: AbortSignal) {
  return new Promise<Blob>((resolve, reject) => {
    const worker = new Worker(new URL('./wav-worker.ts', import.meta.url), { type: 'module' });
    const close = () => { worker.terminate(); signal?.removeEventListener('abort', abort); };
    const abort = () => { close(); reject(new Error('WAV export cancelled.')); };
    signal?.addEventListener('abort', abort);
    worker.onerror = event => { close(); reject(new Error(event.message)); };
    worker.onmessage = ({ data }) => {
      if (data.error) { close(); reject(new Error(data.error)); }
      else if (data.buffer) { close(); resolve(new Blob([data.buffer], { type: 'audio/wav' })); }
      else if (typeof data.progress === 'number') onProgress(data.progress);
    };
    const midi = decodeBase64(composition.midi).buffer;
    worker.postMessage({ midi, seconds: composition.bars * 240 / composition.bpm, libraries: composition.libraries ?? [], mixProfile: composition.mixProfile, bundled }, [midi]);
  });
}
