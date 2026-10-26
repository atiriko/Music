import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

async function openStudio(page: import('@playwright/test').Page) {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Play current section' })).toBeVisible({ timeout: 60000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
}

test('all local assets initialize offline and the phone layout fits', async ({ page }) => {
  const external: string[] = [];
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.hostname !== '127.0.0.1') { external.push(url.href); return route.abort(); }
    return route.continue();
  });
  await openStudio(page);
  await expect(page.getByLabel('Melody', { exact: true }).locator('option')).toHaveCount(131);
  await expect(page.getByLabel('Drums', { exact: true }).locator('option')).toHaveCount(10);
  await expect(page.getByLabel('Drum style', { exact: true }).locator('option')).toHaveCount(8);
  await expect(page.getByLabel('Chord pattern').locator('option')).toHaveCount(5);
  await expect(page.getByLabel('Bass pattern').locator('option')).toHaveCount(5);
  await page.getByLabel('Chord pattern').selectOption('Arpeggiated');
  await page.getByLabel('Bass pattern').selectOption('Walking');
  await page.getByLabel('Playing feel').selectOption('Loose');
  await page.getByLabel('Phrasing / space').selectOption('Spacious');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.waitForTimeout(800);
  await page.reload();
  await expect(page.getByLabel('Chord pattern')).toHaveValue('Arpeggiated', { timeout: 60000 });
  await expect(page.getByLabel('Bass pattern')).toHaveValue('Walking');
  await expect(page.getByLabel('Playing feel')).toHaveValue('Loose');
  await expect(page.getByLabel('Phrasing / space')).toHaveValue('Spacious');
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(external).toEqual([]);
  await page.screenshot({ path: `test-results/${test.info().project.name}-generator.png` });
});

test('real sampled playback emits audio, changes instruments, loops, and stops', async ({ page }) => {
  await openStudio(page);
  const audioAvailable = await page.evaluate(() => typeof AudioContext !== 'undefined' && typeof AudioWorkletNode !== 'undefined');
  test.skip(!audioAvailable, 'The Windows WebKit test binary has no Web Audio implementation; run this playback test on macOS WebKit or a physical iPhone.');
  await page.getByLabel('Length · bars').fill('1');
  await page.getByLabel('Tempo · BPM').fill('220');
  await page.getByLabel('Chords', { exact: true }).selectOption('Mute');
  await page.getByLabel('Bass', { exact: true }).selectOption('Mute');
  await page.getByLabel('Drums', { exact: true }).selectOption('Mute');
  await page.getByRole('button', { name: 'Play current section' }).click();
  await expect(page.getByLabel('Playback controls')).toContainText('Playing section');
  await expect.poll(async () => Number(await page.getByRole('meter').getAttribute('aria-valuenow'))).toBeGreaterThan(.001);
  await page.getByLabel('Melody', { exact: true }).selectOption('Flute');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.waitForTimeout(1000);
  await expect.poll(async () => Number(await page.getByRole('meter').getAttribute('aria-valuenow'))).toBeGreaterThan(.001);
  await page.getByRole('button', { name: 'Stop' }).click();
  await expect(page.getByLabel('Playback controls')).toContainText('Stopped');
  await expect(page.getByRole('meter')).toHaveAttribute('aria-valuenow', '0');
});

test('sections arrange with fills, preview all MIDI, and survive app reload', async ({ page }) => {
  await openStudio(page);
  await page.getByLabel('Length · bars').fill('1');
  await page.getByLabel('Drum style', { exact: true }).selectOption('Funk');
  await page.getByLabel('Section name').fill('Verse');
  await page.getByRole('button', { name: 'Save section', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Saved section Verse');
  await page.getByLabel('Variation seed').fill('123');
  await page.getByLabel('Section name').fill('Chorus');
  await page.getByRole('button', { name: 'Save section', exact: true }).click();
  await page.getByRole('button', { name: 'Song', exact: true }).click();
  await page.getByLabel('Saved section').selectOption('Verse');
  await page.getByRole('button', { name: 'Add to song' }).click();
  await page.getByRole('button', { name: '+ Drum fill' }).click();
  await page.getByLabel('Saved section').selectOption('Chorus');
  await page.getByRole('button', { name: 'Add to song' }).click();
  await expect(page.getByRole('img', { name: /Piano roll with/ })).not.toHaveAttribute('aria-label', 'Piano roll with 0 MIDI notes');
  await page.getByRole('button', { name: 'Move entry 3 up' }).click();
  await page.getByRole('button', { name: 'Projects' }).click();
  await page.getByLabel('Project name').fill('Mobile song');
  await page.getByRole('button', { name: 'Save on device' }).click();
  await expect(page.getByText('Saved Mobile song on this device.')).toBeVisible();
  await page.waitForTimeout(800);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Play current section' })).toBeVisible({ timeout: 60000 });
  await page.getByRole('button', { name: 'Projects' }).click();
  await expect(page.getByText('Mobile song', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Open', exact: true }).click();
  await expect(page.getByText('3 bars', { exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export MIDI', exact: true }).click();
  const midi = await download;
  const bytes = await readFile((await midi.path())!);
  expect(bytes.subarray(0, 4).toString()).toBe('MThd');
  await page.screenshot({ path: `test-results/${test.info().project.name}-song.png`, fullPage: true });
});

test('WAV export contains actual audio samples', async ({ page }) => {
  await openStudio(page);
  await page.getByLabel('Length · bars').fill('1');
  await page.getByLabel('Tempo · BPM').fill('220');
  const download = page.waitForEvent('download', { timeout: 60000 });
  await page.getByRole('button', { name: 'Export WAV', exact: true }).click();
  const file = await download;
  const bytes = await readFile((await file.path())!);
  expect(bytes.subarray(0, 4).toString()).toBe('RIFF');
  expect(bytes.subarray(8, 12).toString()).toBe('WAVE');
  let peak = 0;
  for (let offset = 44; offset + 1 < bytes.length; offset += 2) peak = Math.max(peak, Math.abs(bytes.readInt16LE(offset)));
  expect(peak).toBeGreaterThan(100);
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('desktop projects import through the phone interface and validation recovers', async ({ page }) => {
  await openStudio(page);
  await expect(page.getByRole('img', { name: /Piano roll with/ })).not.toHaveAttribute('aria-label', 'Piano roll with 0 MIDI notes');
  const originalSeed = await page.getByLabel('Variation seed').inputValue();
  await page.getByLabel('Variation seed').fill('1.5');
  await expect(page.getByRole('alert')).toContainText('whole numbers');
  await page.getByLabel('Variation seed').fill(originalSeed);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.getByLabel('Variation seed').fill('123');
  await page.getByRole('button', { name: 'Projects', exact: true }).click();
  await page.locator('input[type=file]').setInputFiles('../examples/Example.song.json');
  await expect(page.getByText('54 bars', { exact: true })).toBeVisible();
  await expect(page.getByRole('img', { name: /Piano roll with/ })).not.toHaveAttribute('aria-label', 'Piano roll with 0 MIDI notes');
  await page.getByRole('button', { name: 'Projects', exact: true }).click();
  await page.getByRole('button', { name: 'Sound library license', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('GeneralUser GS');
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Import a song project' })).toBeVisible();
});
