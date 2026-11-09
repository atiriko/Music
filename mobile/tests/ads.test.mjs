import test from 'node:test';
import assert from 'node:assert/strict';
import { createBannerController } from '../src/banner-controller.ts';

const allowed = { status: 'NOT_REQUIRED', canRequestAds: true, privacyOptionsRequirementStatus: 'NOT_REQUIRED' };
function fixture(consent = allowed) {
  const calls = [], listeners = new Map(), layout = [], states = [];
  const sdk = {
    addListener: async (name, fn) => { listeners.set(name, fn); return { remove: async () => { listeners.delete(name); } }; },
    requestConsentInfo: async () => { calls.push('consent'); return consent; },
    showConsentForm: async () => { calls.push('form'); return allowed; },
    initialize: async () => { calls.push('initialize'); },
    setApplicationMuted: async () => { calls.push('muted'); },
    showBanner: async () => { calls.push('banner'); listeners.get('bannerAdSizeChanged')?.({ width: 393, height: 50 }); },
    removeBanner: async () => { calls.push('remove'); },
    showPrivacyOptionsForm: async () => { calls.push('privacy'); },
  };
  const controller = createBannerController(sdk, { adId: 'demo', isTesting: true }, (...args) => layout.push(args), next => states.push(next));
  return { controller, sdk, calls, listeners, layout, states };
}

test('required consent is resolved before initialization and banner loading', async () => {
  const f = fixture({ ...allowed, status: 'REQUIRED', canRequestAds: false, isConsentFormAvailable: true });
  await f.controller.start();
  assert.deepEqual(f.calls, ['consent', 'form', 'initialize', 'muted', 'banner']);
  assert.deepEqual(f.layout.at(-1), [50]);
  await f.controller.stop();
  assert.equal(f.listeners.size, 0);
  assert.deepEqual(f.layout.at(-1), [0]);
});

test('denied or unavailable consent never initializes the advertising SDK', async () => {
  const f = fixture({ ...allowed, canRequestAds: false, privacyOptionsRequirementStatus: 'REQUIRED' });
  await f.controller.start();
  assert.deepEqual(f.calls, ['consent']);
  assert.deepEqual(f.layout.at(-1), [0, true]);
  await f.controller.stop();
});

test('leaving during consent cannot create an orphan banner', async () => {
  const f = fixture();
  let release;
  const pending = new Promise(resolve => { release = resolve; });
  f.sdk.requestConsentInfo = () => pending;
  const starting = f.controller.start();
  await new Promise(resolve => setImmediate(resolve));
  const stopping = f.controller.stop();
  release(allowed);
  await Promise.all([starting, stopping]);
  assert.equal(f.calls.includes('banner'), false);
  assert.equal(f.listeners.size, 0);
});

test('privacy withdrawal removes the old banner without requesting another', async () => {
  const f = fixture();
  await f.controller.start();
  f.sdk.requestConsentInfo = async () => ({ ...allowed, canRequestAds: false });
  await f.controller.privacy();
  assert.deepEqual(f.calls, ['consent', 'initialize', 'muted', 'banner', 'remove', 'privacy']);
  assert.deepEqual(f.layout.at(-1), [0, false]);
  await f.controller.stop();
});

test('no-fill clears the inset and offline consent errors are recoverable', async () => {
  const f = fixture();
  await f.controller.start();
  f.listeners.get('bannerAdFailedToLoad')({ code: 3 });
  assert.deepEqual(f.layout.at(-1), [0]);
  await f.controller.stop();
  const offline = fixture();
  offline.sdk.requestConsentInfo = async () => { throw new Error('offline'); };
  await assert.rejects(offline.controller.start(), /offline/);
  await offline.controller.stop();
  assert.equal(offline.listeners.size, 0);
  assert.equal(offline.calls.includes('initialize'), false);
});


test('a rejected native banner request clears space even without a failure event', async () => {
  const f = fixture();
  f.sdk.showBanner = async () => {
    f.listeners.get('bannerAdSizeChanged')({ width: 393, height: 50 });
    throw new Error('native load failed');
  };
  await assert.rejects(f.controller.start(), /native load failed/);
  assert.deepEqual(f.layout.at(-1), [0]);
  await f.controller.stop();
});


test('the test screen receives the exact consent error and can retry successfully', async () => {
  const f = fixture();
  f.sdk.requestConsentInfo = async () => { throw new Error("Publisher account configuration could not be loaded"); };
  await assert.rejects(f.controller.start(), /Publisher/);
  assert.equal(f.states.at(-1).phase, 'error');
  assert.match(f.states.at(-1).message, /Consent check failed: Publisher account configuration/);
  assert.equal(f.calls.includes('initialize'), false);
  f.sdk.requestConsentInfo = async () => allowed;
  await f.controller.start();
  f.listeners.get('bannerAdLoaded')();
  assert.equal(f.states.at(-1).phase, 'loaded');
  assert.equal(f.calls.filter(x => x === 'initialize').length, 1);
  assert.equal(f.listeners.size, 3);
  await f.controller.stop();
});

test('a no-fill retry removes the old banner and preserves SDK error details', async () => {
  const f = fixture();
  await f.controller.start();
  f.listeners.get('bannerAdFailedToLoad')({ code: 3, message: 'No ad inventory' });
  assert.equal(f.states.at(-1).message, 'Banner failed to load: Code 3: No ad inventory');
  await f.controller.start();
  assert.equal(f.calls.filter(x => x === 'remove').length, 1);
  assert.equal(f.calls.filter(x => x === 'initialize').length, 1);
  assert.equal(f.calls.filter(x => x === 'banner').length, 2);
  await f.controller.stop();
});

test('blocked consent reports the state without bypassing the consent gate', async () => {
  const f = fixture({ ...allowed, status: 'REQUIRED', isConsentFormAvailable: false, canRequestAds: false });
  await f.controller.start();
  assert.equal(f.states.at(-1).phase, 'blocked');
  assert.match(f.states.at(-1).message, /canRequestAds=false/);
  assert.deepEqual(f.calls, ['consent']);
  await f.controller.stop();
});
