import type { Catalog, Composition, Instruments, Library, Project, Settings } from './types';

class MusicEngine {
  private worker = new Worker(new URL('/engine-worker.js', location.href), { type: 'module' });
  private serial = 0;
  private pending = new Map<number, { resolve: (result: unknown) => void; reject: (error: Error) => void }>();
  constructor() {
    this.worker.onmessage = ({ data }) => {
      const request = this.pending.get(data.id);
      if (!request) return;
      this.pending.delete(data.id);
      if (data.error) request.reject(new Error(data.error)); else request.resolve(data.result);
    };
    this.worker.onerror = (event) => {
      for (const request of this.pending.values()) request.reject(new Error(event.message || 'The music engine could not start.'));
      this.pending.clear();
    };
  }
  request<T>(action: string, data: unknown = {}, transfer: Transferable[] = []): Promise<T> {
    const id = ++this.serial;
    return new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve: value => resolve(value as T), reject });
      this.worker.postMessage({ id, action, data }, transfer);
    });
  }
  catalog() { return this.request<Catalog>('catalog'); }
  section(settings: Settings, instruments: Instruments) { return this.request<Composition>('section', { settings, instruments }); }
  variation(settings: Settings, instruments: Instruments, seed: number) { return this.request<Composition>('variation', { settings, instruments, seed }); }
  song(project: Project) { return this.request<Composition>('song', project); }
  validate(project: unknown) { return this.request<Project>('validate_project', project); }
  automaticSong(settings: Settings, instruments: Instruments, length: string, style: string, candidates: number, existing?: Project) {
    return this.request<Project>('automatic_song', { settings, instruments, length, style, candidates, existing });
  }
  registerLibrary(metadata: Library) { return this.request<Library>('register_library', metadata); }
  unregisterLibrary(id: string) { return this.request<{ removed: string }>('unregister_library', { id }); }
  importFont(bytes: ArrayBuffer, name: string, family: string) {
    return this.request<{ metadata: Library; buffer: ArrayBuffer }>('import_font', { bytes, name, family }, [bytes]);
  }
}
export const engine = new MusicEngine();
