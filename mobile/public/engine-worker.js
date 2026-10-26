let engine;
const ready = (async () => {
  const { loadPyodide } = await import('./runtime/pyodide/pyodide.mjs');
  const pyodide = await loadPyodide({ indexURL: new URL('./runtime/pyodide/', self.location.href).href });
  await pyodide.loadPackage('numpy');
  const response = await fetch('./engine.zip');
  if (!response.ok) throw new Error('Cannot load the bundled music engine.');
  pyodide.FS.mkdirTree('/music');
  pyodide.unpackArchive(await response.arrayBuffer(), 'zip', { extractDir: '/music' });
  pyodide.runPython("import sys; sys.path.insert(0, '/music'); import mobile_bridge");
  engine = pyodide;
})();
let requests = Promise.resolve();
self.onmessage = ({ data }) => {
  requests = requests.then(async () => {
    try {
      await ready;
      if (data.action === 'import_font') {
        engine.globals.set('_font_bytes', new Uint8Array(data.data.bytes));
        engine.globals.set('_font_name', data.data.name);
        engine.globals.set('_font_family', data.data.family);
        let output;
        try {
          output = engine.runPython('mobile_bridge.import_binary(bytes(_font_bytes.to_py()), _font_name, _font_family)');
          const metadata = JSON.parse(output.get(0));
          // The remapped copy gets private MIDI banks; this is what the synth must load.
          const bytes = output.get(1).toJs();
          const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
          self.postMessage({ id: data.id, result: { metadata, buffer } }, [buffer]);
        } finally {
          output?.destroy();
          engine.runPython('del _font_bytes, _font_name, _font_family');
        }
        return;
      }
      engine.globals.set('_mobile_request', JSON.stringify({ action: data.action, data: data.data }));
      const json = engine.runPython('mobile_bridge.handle(_mobile_request)');
      self.postMessage({ id: data.id, result: JSON.parse(json) });
    } catch (error) {
      const message = String(error.message || error).trim().split('\n').filter(Boolean).at(-1).replace(/^(ValueError|TypeError|RuntimeError):\s*/, '');
      self.postMessage({ id: data.id, error: message });
    }
  });
};
