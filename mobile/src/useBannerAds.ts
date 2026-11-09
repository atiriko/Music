import { useEffect, useRef, useState } from 'react';
import { Capacitor } from '@capacitor/core';
import { AdMob, BannerAdPosition, BannerAdSize } from '@capacitor-community/admob';
import config from '../admob.config.json';
import { adErrorMessage, createBannerController } from './banner-controller';
import type { AdStatus } from './banner-controller';

export function useBannerAds(ready: boolean) {
  const controller = useRef<ReturnType<typeof createBannerController> | null>(null);
  const [privacyRequired, setPrivacyRequired] = useState(false);
  const [status, setStatus] = useState<AdStatus>({ phase: 'consent', message: 'Waiting for the music app to finish loading…' });
  const [retrying, setRetrying] = useState(false);
  const platform = Capacitor.getPlatform();
  const native = Capacitor.isNativePlatform() && (platform === 'android' || platform === 'ios');
  const testing = native ? (config[platform as 'android' | 'ios'].testing ?? config.testing) : false;
  useEffect(() => {
    const platform = Capacitor.getPlatform();
    if (!ready || !config.enabled || !Capacitor.isNativePlatform() || (platform !== 'android' && platform !== 'ios')) return;
    let active = true;
    const ads = createBannerController(AdMob, {
      adId: config[platform].bannerId,
      adSize: BannerAdSize.ADAPTIVE_BANNER,
      position: BannerAdPosition.BOTTOM_CENTER,
      isTesting: config[platform].testing ?? config.testing,
      npa: true,
    }, (height, required) => {
      if (!active) return;
      // Include a 16px gap between ads and interactive navigation controls.
      document.documentElement.style.setProperty('--admob-inset', height > 0 ? `${height + 16}px` : '0px');
      if (required !== undefined) setPrivacyRequired(required);
    }, next => { if (active) setStatus(next); });
    controller.current = ads;
    // Ad failures/offline startup must never stop generation or playback.
    void ads.start().catch(error => {
      if (active) setStatus(current => current.phase === 'error' ? current : { phase: 'error', message: adErrorMessage(error) });
      console.warn('AdMob banner unavailable:', error);
    });
    return () => {
      active = false;
      controller.current = null;
      document.documentElement.style.removeProperty('--admob-inset');
      void ads.stop().catch(error => console.warn('AdMob cleanup:', error));
    };
  }, [ready]);
  const retry = async () => {
    if (!controller.current || retrying) return;
    setRetrying(true);
    try { await controller.current.start(); }
    catch (error) {
      setStatus(current => current.phase === 'error' ? current : { phase: 'error', message: adErrorMessage(error) });
    } finally { setRetrying(false); }
  };
  return {
    privacyRequired, openPrivacy: async () => { await controller.current?.privacy(); },
    diagnostic: native && config.enabled && testing ? status : null,
    retry, retrying,
  };
}
