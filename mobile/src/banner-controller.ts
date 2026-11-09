import { AdmobConsentStatus, BannerAdPluginEvents } from '@capacitor-community/admob';
import type { AdMobPlugin, BannerAdOptions } from '@capacitor-community/admob';
import type { PluginListenerHandle } from '@capacitor/core';

export type AdStatus = {
  phase: 'consent' | 'initializing' | 'loading' | 'loaded' | 'blocked' | 'error';
  message: string;
};

export function adErrorMessage(error: unknown): string {
  if (error && typeof error === 'object') {
    const value = error as { message?: unknown; code?: unknown };
    const message = typeof value.message === 'string' ? value.message : JSON.stringify(error);
    return (value.code !== undefined ? `Code ${value.code}: ` : '') + message;
  }
  return String(error);
}

// Serialize native requests: leaving a screen during consent must not create an
// orphan banner, and changing consent must destroy the previous ad request.
export function createBannerController(
  sdk: AdMobPlugin,
  options: BannerAdOptions,
  changed: (height: number, privacyRequired?: boolean) => void,
  status: (value: AdStatus) => void = () => {},
) {
  let disposed = false;
  let initialized = false;
  let requested = false;
  let listening = false;
  let chain = Promise.resolve();
  const handles: PluginListenerHandle[] = [];
  const enqueue = (job: () => Promise<void>) => {
    const result = chain.then(job);
    chain = result.catch(() => {});
    return result;
  };
  const remove = async () => {
    changed(0);
    if (requested) { requested = false; await sdk.removeBanner(); }
  };
  const load = async () => {
    if (disposed) return;
    status({ phase: 'consent', message: 'Checking Google ad consent…' });
    let consent;
    try { consent = await sdk.requestConsentInfo(); }
    catch (error) {
      if (!disposed) status({ phase: 'error', message: 'Consent check failed: ' + adErrorMessage(error) });
      throw error;
    }
    if (disposed) return;
    if (consent.status === AdmobConsentStatus.REQUIRED && consent.isConsentFormAvailable) {
      status({ phase: 'consent', message: 'Waiting for the Google privacy form…' });
      try { consent = await sdk.showConsentForm(); }
      catch (error) {
        if (!disposed) status({ phase: 'error', message: 'Consent form failed: ' + adErrorMessage(error) });
        throw error;
      }
    }
    if (disposed) return;
    changed(0, consent.privacyOptionsRequirementStatus === 'REQUIRED');
    if (!consent.canRequestAds) {
      status({ phase: 'blocked', message: `Google consent status: ${consent.status}; canRequestAds=false. No ad was requested.` });
      return;
    }
    if (!initialized) {
      status({ phase: 'initializing', message: 'Starting Google Mobile Ads…' });
      try { await sdk.initialize({ initializeForTesting: options.isTesting }); }
      catch (error) {
        if (!disposed) status({ phase: 'error', message: 'Ad SDK initialization failed: ' + adErrorMessage(error) });
        throw error;
      }
      initialized = true;
      await sdk.setApplicationMuted({ muted: true });
    }
    if (disposed) return;
    status({ phase: 'loading', message: options.isTesting ? 'Requesting a Google test banner…' : 'Requesting a banner…' });
    requested = true;
    try { await sdk.showBanner(options); }
    catch (error) {
      if (!disposed) {
        changed(0);
        status({ phase: 'error', message: 'Banner request failed: ' + adErrorMessage(error) });
      }
      throw error;
    }
  };
  return {
    start: () => enqueue(async () => {
      if (disposed) return;
      if (!listening) {
        handles.push(await sdk.addListener(BannerAdPluginEvents.SizeChanged, size => {
          if (!disposed) changed(Number.isFinite(size.height) ? Math.max(0, size.height) : 0);
        }));
        handles.push(await sdk.addListener(BannerAdPluginEvents.FailedToLoad, error => {
          if (!disposed) {
            changed(0);
            status({ phase: 'error', message: 'Banner failed to load: ' + adErrorMessage(error) });
          }
        }));
        handles.push(await sdk.addListener(BannerAdPluginEvents.Loaded, () => {
          if (!disposed) status({ phase: 'loaded', message: options.isTesting ? 'Google test banner loaded.' : 'Banner loaded.' });
        }));
        listening = true;
      }
      if (requested) await remove();
      await load();
    }),
    privacy: () => enqueue(async () => {
      if (disposed) return;
      await remove();
      await sdk.showPrivacyOptionsForm();
      await load();
    }),
    stop: () => {
      disposed = true;
      changed(0);
      return enqueue(async () => {
        try { await remove(); }
        finally { for (const handle of handles.splice(0)) await handle.remove(); }
      });
    },
  };
}
