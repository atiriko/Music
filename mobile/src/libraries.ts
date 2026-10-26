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
      const transaction = db.transaction(STORE, mode);
      const request = run(transaction.objectStore(STORE));
      let result: T;
      request.onsuccess = () => { result = request.result; };
      transaction.oncomplete = () => resolve(result);
      transaction.onabort = transaction.onerror = () => reject(new Error(transaction.error?.name === 'QuotaExceededError' ? 'Not enough storage for this instrument library.' : 'Could not access instrument storage.'));
    });
  } finally { db.close(); }
}
export const saveLibrary = (entry: StoredLibrary) => transact('readwrite', store => store.put(entry));
export const deleteLibrary = (id: string) => transact('readwrite', store => store.delete(id));
export async function remapLibrary(metadata: Library) {
  const stored = await transact<StoredLibrary>('readonly', store => store.get(metadata.id));
  if (!stored) throw new Error('The imported instrument audio is missing.');
  const view = new DataView(stored.bytes);
  for (const preset of metadata.presets) {
    view.setUint16(preset.offset + 20, preset.program, true);
    view.setUint16(preset.offset + 22, preset.bank, true);
  }
  await saveLibrary({ metadata, bytes: stored.bytes });
}
export const storedLibraries = () => transact<StoredLibrary[]>('readonly', store => store.getAll() as IDBRequest<StoredLibrary[]>);
export async function storedMetadata() {
  // Walk one library at a time so startup does not retain every SF2 buffer.
  const db = await open();
  try {
    return await new Promise<Library[]>((resolve, reject) => {
      const entries: Library[] = [];
      const transaction = db.transaction(STORE, 'readonly');
      const request = transaction.objectStore(STORE).openCursor();
      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) { entries.push((cursor.value as StoredLibrary).metadata); cursor.continue(); }
      };
      transaction.oncomplete = () => resolve(entries);
      transaction.onerror = () => reject(new Error('Could not restore instrument libraries.'));
    });
  } finally { db.close(); }
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
