/**
 * Sound library storage shared by live playback and the WAV export worker.
 *
 * The GM library and bundled studio instruments are fetched from the app
 * bundle. Imported SF2 files are stored in IndexedDB (already bank-remapped by
 * the engine), so they survive restarts and work fully offline.
 */
import type { Library } from './types';

const DB = 'music-studio-instruments';
const STORE = 'libraries';
export const GENERAL = 'general-user';
export interface StoredLibrary { metadata: Library; bytes: ArrayBuffer }

function open() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'metadata.id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error('Instrument storage is unavailable on this device.'));
  });
}
async function transact<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>) {
  const db = await open();
  try {
    return await new Promise<T>((resolve, reject) => {
      const request = run(db.transaction(STORE, mode).objectStore(STORE));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error(request.error?.name === 'QuotaExceededError' ? 'Not enough storage for this instrument library.' : 'Could not access instrument storage.'));
    });
  } finally { db.close(); }
}
export const saveLibrary = (entry: StoredLibrary) => transact('readwrite', store => store.put(entry));
export const deleteLibrary = (id: string) => transact('readwrite', store => store.delete(id));
export const storedLibraries = () => transact<StoredLibrary[]>('readonly', store => store.getAll() as IDBRequest<StoredLibrary[]>);
export async function storedMetadata() {
  return (await storedLibraries()).map(entry => entry.metadata);
}

/** Resolve a library identifier to SF2 bytes from the bundle or device storage. */
export async function loadLibrary(id: string, bundled: Library[]): Promise<ArrayBuffer> {
  if (id === GENERAL) return fetchBundled('/soundfonts/GeneralUser-GS.sf2');
  const featured = bundled.find(library => library.id === id && library.relative_file);
  if (featured) return fetchBundled('/soundfonts/featured/' + featured.relative_file!.split('/').pop());
  const stored = await transact<StoredLibrary | undefined>('readonly', store => store.get(id) as IDBRequest<StoredLibrary | undefined>);
  if (!stored) throw new Error('An imported instrument library is missing. Import its SF2 file again.');
  return stored.bytes;
}
async function fetchBundled(path: string) {
  const response = await fetch(new URL(path, self.location.href));
  if (!response.ok) throw new Error('A bundled instrument library is missing.');
  return response.arrayBuffer();
}
