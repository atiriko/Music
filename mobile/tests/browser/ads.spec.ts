import { test, expect } from '@playwright/test';

test('native ad diagnostics show the consent error and retry successfully', async ({ page }) => {
  await page.addInitScript(() => {
    const host = window as unknown as Record<string, unknown>;
    const callbacks: Record<string, (value?: unknown) => void> = {};
    let attempts = 0;
    host.CapacitorCustomPlatform = { name: 'android' };
    host.Capacitor = {
      PluginHeaders: [{ name: 'AdMob', methods: [
        ...['requestConsentInfo', 'initialize', 'setApplicationMuted', 'showBanner', 'removeBanner', 'removeListener'].map(name => ({ name, rtype: 'promise' })),
        { name: 'addListener', rtype: 'callback' },
      ] }],
      nativeCallback: (_plugin: string, _method: string, options: { eventName: string }, callback: (value?: unknown) => void) => {
        callbacks[options.eventName] = callback;
        return options.eventName;
      },
      nativePromise: async (_plugin: string, method: string) => {
        if (method === 'requestConsentInfo') {
          if (++attempts === 1) throw new Error('Publisher account configuration could not be loaded');
          return { status: 'NOT_REQUIRED', canRequestAds: true, privacyOptionsRequirementStatus: 'NOT_REQUIRED' };
        }
        if (method === 'showBanner') setTimeout(() => {
          callbacks.bannerAdSizeChanged?.({ width: 393, height: 50 });
          callbacks.bannerAdLoaded?.();
        }, 50);
        if (method === 'removeBanner') callbacks.bannerAdSizeChanged?.({ width: 0, height: 0 });
        return {};
      },
    };
  });
  await page.goto('/');
  const status = page.getByRole('region', { name: 'Ad test status' });
  await expect(status).toContainText('Consent check failed: Publisher account configuration could not be loaded', { timeout: 60000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
  await status.getByRole('button', { name: 'Retry banner' }).click();
  await expect(status).toContainText('Google test banner loaded.');
  await expect.poll(() => page.evaluate(() => document.documentElement.style.getPropertyValue('--admob-inset'))).toBe('66px');
});
