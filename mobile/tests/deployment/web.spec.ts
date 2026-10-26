import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('the production server serves the complete app with correct caching and MIME types', async ({ request }) => {
  const health = await request.get('/healthz');
  expect(health.status()).toBe(200);
  expect(await health.text()).toBe('ok\n');
  expect(health.headers()['cache-control']).toBe('no-store');

  const response = await request.get('/');
  expect(response.status()).toBe(200);
  expect(response.headers()['cache-control']).toBe('no-cache');
  expect(response.headers()['cross-origin-opener-policy']).toBe('same-origin');
  expect(response.headers()['cross-origin-embedder-policy']).toBe('require-corp');
  const html = await response.text();
  const script = html.match(/src="(\/assets\/[^"\s]+\.js)"/);
  expect(script).not.toBeNull();
  const asset = await request.head(script![1]);
  expect(asset.headers()['cache-control']).toContain('immutable');

  const wasm = await request.head('/runtime/pyodide/pyodide.asm.wasm');
  expect(wasm.status()).toBe(200);
  expect(wasm.headers()['content-type']).toBe('application/wasm');
  const module = await request.head('/runtime/pyodide/pyodide.mjs');
  expect(module.status()).toBe(200);
  expect(module.headers()['content-type']).toBe('application/javascript');
  const bank = '/soundfonts/featured/upright.sf2';
  const compressed = await request.head(bank, { headers: { 'Accept-Encoding': 'gzip' } });
  const original = await request.head(bank, { headers: { 'Accept-Encoding': 'identity' } });
  expect(compressed.status()).toBe(200);
  expect(compressed.headers()['content-encoding']).toBe('gzip');
  expect(Number(compressed.headers()['content-length'])).toBeLessThan(Number(original.headers()['content-length']));
  const unchanged = await request.head(bank, { headers: { 'Accept-Encoding': 'identity', 'If-None-Match': original.headers().etag } });
  expect(unchanged.status()).toBe(304);

  const missing = await request.get('/runtime/not-a-real-file.wasm');
  expect(missing.status()).toBe(404);
  expect(missing.headers()['cache-control'] ?? '').not.toContain('immutable');
});

test('the web build runs the engine, sampled playback and MIDI/WAV exports in a browser', async ({ page }) => {
  // Direct SPA navigation also checks that web-build asset URLs are root-relative.
  await page.goto('/song/saved');
  await expect(page.getByRole('button', { name: 'Play current section' })).toBeVisible({ timeout: 60000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
  expect(await page.evaluate(() => isSecureContext && crossOriginIsolated && typeof AudioWorkletNode !== 'undefined')).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  await page.getByLabel('Sound preset', { exact: true }).selectOption('Techno');
  await page.getByLabel(/Length.*bars/).fill('1');
  await page.getByLabel(/Tempo.*BPM/).fill('220');
  for (const part of ['Chords', 'Bass', 'Drums']) await page.getByLabel(part, { exact: true }).selectOption('Mute');
  await page.getByRole('button', { name: 'Play current section' }).click();
  await expect.poll(async () => Number(await page.getByRole('meter').getAttribute('aria-valuenow')), { timeout: 60000 }).toBeGreaterThan(.001);
  await page.getByRole('button', { name: 'Stop', exact: true }).click();

  const midiDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export MIDI', exact: true }).click();
  const midi = await readFile((await (await midiDownload).path())!);
  expect(midi.subarray(0, 4).toString()).toBe('MThd');

  const wavDownload = page.waitForEvent('download', { timeout: 60000 });
  await page.getByRole('button', { name: 'Export WAV', exact: true }).click();
  const wav = await readFile((await (await wavDownload).path())!);
  expect(wav.subarray(0, 4).toString()).toBe('RIFF');
  let peak = 0;
  for (let i = 44; i + 1 < wav.length; i += 2) peak = Math.max(peak, Math.abs(wav.readInt16LE(i)));
  expect(peak).toBeGreaterThan(100);
  await expect(page.getByRole('alert')).toHaveCount(0);
});
