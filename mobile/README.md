# Royalty Free Music Maker for Android and iOS

A shared mobile app with native Android/iOS projects, touch controls, offline sampled playback, song arrangement, MIDI preview, and exports. It uses the existing Python composition engine from the parent directory; there is no server and no separate mobile rewrite of its music rules.

## Install the Android test build

The locally built debug APK is `releases/Music-Studio-android-debug.apk`. Transfer it to an Android device and open it to install. This is a development build signed with the local debug key, not a Play Store release.

Physical Android/iPhone testing is still needed before a store release. A native build succeeding and browser tests passing do not substitute for device testing.

## Features

- Keys, scales, complexity, tempo, seeded variations, and chord-aware melodies.
- 128 sampled instrument programs and nine drum kits, using the same bundled GeneralUser GS library as the desktop app.
- Eight drum styles, independent drum complexity, fill frequency, and new rhythmic patterns with each variation.
- Up to 32 named sections; reuse/reorder sections and add drum-fill transitions.
- Full-song MIDI piano roll with track filters, zoom, horizontal scrolling, and playback cursor.
- MIDI/WAV exports using the native Android/iOS share sheet; project import/export uses the desktop `.song.json` format.
- Automatic draft persistence, multiple named projects saved locally, and an included example song.
- No microphone, accounts, or external synthesizer are needed. Native apps include AdMob banner advertising; music remains local. Generation and playback assets are bundled offline.

Playback and rendering pause/cancel when the app leaves the foreground. Background audio, lock-screen media controls, external MIDI hardware, cloud sync, and store publication are not implemented. The first startup initializes the local music engine; it may take a few seconds, especially on an older phone. Long WAV exports use additional memory.

## Development setup

Install Node.js 22+, Python with `numpy`, `mido`, and `packaging`, and run from this directory:

```powershell
python -m pip install numpy mido packaging
npm ci
npm run build
npm run preview
```

The preview is available at `http://127.0.0.1:4173`. The production build uses a strict local-assets CSP. `npm run dev` is intended for front-end development; use the production preview for the bundled Python runtime and CSP tests.

`npm run build` runs `scripts/prepare_engine.py`, which copies the original Python modules into `public/engine.zip`, bundles Pyodide/NumPy, copies the parent project's SoundFont and example song, and includes third-party licenses. The first build downloads the checksum-verified NumPy wheel matching the pinned Pyodide runtime; subsequent builds reuse it. No download occurs when the installed app generates or plays music.

Runtime/build assets, installed dependencies, SDK caches, and APKs are ignored by Git. Commit the mobile source, native projects, lockfile, and the parent project's SoundFont. Do not commit `node_modules`, `.tools`, `dist`, or generated `public` runtime files.

## Android build

Requirements: JDK 21, Android SDK API 36/build-tools 36.0.0, and Android SDK licenses accepted. Android Studio can install the SDK/JDK. Set `JAVA_HOME` and `ANDROID_HOME` for your installation.

```powershell
npm run build:android
```

This builds/syncs web assets, normalizes generated native paths, runs Gradle, and copies the debug APK to `releases/Music-Studio-android-debug.apk`. If assets are already synced, use `python scripts/build_android.py --skip-sync`.

For this workspace, local SDK/JDK tools were provisioned under `.tools` without replacing global Java settings. `build_android.py` can reuse `.tools/java-home.txt` and `.tools/android-sdk` when no environment overrides are set. `scripts/provision_android.py` downloads/extracts these tools; platform/build-tools installation and license acceptance are still needed when provisioning a fresh machine.

For a release, change `appId` in `capacitor.config.json` to your registered application identifier, configure your own signing key in Android Studio, and generate a signed release bundle. The debug APK is not a store submission artifact.

## iOS build on a Mac

The Xcode project is `ios/App/App.xcodeproj`, using Swift Package Manager. It includes native file sharing/preferences/status bar integration, the sampled library, app icons, an audio session configured for music playback, and an app privacy manifest.

A Mac with Xcode 26+ is required by Capacitor 8. This Windows workspace cannot compile, sign, install, or physically test an iOS app. No `.ipa` was produced here.

On a Mac, with the repository and its parent engine/assets available:

```bash
python3 -m pip install numpy mido packaging
npm ci
npm run sync
npx cap open ios
```

Select your Apple development team, use a unique bundle identifier, choose an iPhone/simulator, and run in Xcode. To distribute through TestFlight/App Store, configure signing/provisioning and archive through Xcode. `npm run sync` must be run after engine/UI changes; it also regenerates platform-correct Swift package paths.

An unsigned simulator compile can be run with:

```bash
xcodebuild -project ios/App/App.xcodeproj -scheme App -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO build
```

## Checks and limits of verification

```powershell
npm run build
npm test
npx playwright install chromium webkit
npm run test:e2e
```

The Node tests load the bundled Python code inside actual WebAssembly and compare its MIDI byte-for-byte with native desktop Python for representative keys/scales/drum styles and a full song. They also check variations, project validation, and audible/distinct sampled instruments.

Browser tests run at phone sizes in Chromium and WebKit: all assets with external requests blocked, controls, MIDI preview, section arrangement, persistence after reload, downloads, and WAV audio data. Playback tests inspect actual Web Audio sample levels, rather than only watching a playback cursor. The Windows WebKit binary does not expose `AudioContext`/`AudioWorkletNode`; its playback test is explicitly skipped. Run that test on macOS WebKit and verify on a physical iPhone before release. WebKit generation, arrangements, persistence and offline WAV rendering/export are tested on Windows.

Native share-sheet behavior, audio interruptions/routes, memory usage on older phones, and platform-specific WebView behavior require real-device verification. Automated tests here cover browser implementations of file export/persistence, not the native share-sheet UI.

## Maintainability

| Location | Purpose |
| --- | --- |
| Parent `main.py`, `generator.py`, `drum_patterns.py`, `song.py`, `midi_export.py` | Existing shared music logic; bundled each build |
| `python/mobile_bridge.py` | Small JSON adapter; validation, generation, MIDI and project exchange |
| `public/engine-worker.js` | Runs the packaged Python engine off the UI thread |
| `src/App.tsx` | Mobile controls, projects, song workflow and lifecycle |
| `src/player.ts` | Sampled audio-worklet playback of the generated MIDI |
| `src/wav-worker.ts` | Offline WAV rendering with the same SoundFont |
| `src/PianoRoll.tsx` | Virtualized/scrollable MIDI drawing suitable for long songs |
| `src/files.ts` | Native cache/share export and browser download fallback |
| `android`, `ios` | Editable native app projects |
| `scripts`, `tests` | Reproducible packaging/build commands and checks |

The only portability change to desktop song rendering is a lazy import of its native audio renderer. Desktop generation, project and MIDI APIs remain shared. Numeric settings also receive explicit whole-number validation for mobile input. The desktop UI and launch command remain available.

Credits and license copies are in `THIRD_PARTY_NOTICES.md`, `licenses`, and the installed app's `licenses`/`soundfonts` assets. GeneralUser GS is by S. Christian Collins. Pyodide is unmodified MPL-2.0; SpessaSynth core/library are Apache-2.0. No existing user code was relicensed.


## Song development and instrument libraries

Automatic generation appends related sections and preserves existing handmade sections and sequence entries. Names are made unique before the resulting project is validated. Musical controls include chord voicings, strum patterns, melody characters, and optional counterpoint. Metal, drum-and-bass, and techno sound presets use bundled samples and procedural synth patches.

SoundFont (.sf2) imports are limited to 64 MB per file. Imported presets are inspected and remapped into private banks by the same Python code as desktop. Normalized bytes live in IndexedDB, are restored before project validation, and are used by both the audio worklet and WAV worker. Pickers group sounds by instrument family. Project JSON contains references rather than embedding sample files, so moving a project between devices requires importing the same instrument libraries.

The original desktop engine functions remain available. Additional shared modules are `auto_song.py`, `quality.py`, `arrangement.py`, `articulation.py`, `counterpoint.py`, `soundbanks.py`, and `presets.py`. The build includes every shared module and the featured catalog; SF2 files and credits are bundled separately. Live playback loads the libraries a composition uses and unloads unused custom banks between compositions.


## AdMob banners

Android and iOS show an anchored adaptive banner below the navigation, with a
16px gap separating ads from controls. Banner size changes update the reserved
space; a failed/offline request leaves the app usable without a blank ad slot.
The website does not initialize AdMob or request ads.

`admob.config.json` is the single configuration file. Android is configured with your app/banner IDs, and iOS uses Google's demo IDs.
Both platforms have `testing: true`. Native
demo ads require a device/simulator build; browser preview does not display ads.
`npm run build` validates this configuration and writes the native app IDs to
AndroidManifest.xml and Info.plist. `npm run sync` includes the plugin in both
native projects. The plugin supplies the Google SDKs; do not add duplicate SDKs.

For your own ads:

1. Register separate Android and iOS apps in AdMob and create one banner unit for
   each. Set each platform's `appId` (`~` separator) and `bannerId` (`/` separator)
   in `admob.config.json`. Keep the platform’s `testing: true` during device development.
2. Configure and publish the applicable privacy messages in AdMob's Privacy &
   messaging area. Consent is refreshed on launch, and the required form is shown
   before SDK initialization/ad requests. Ads are requested only if UMP returns
   `canRequestAds`. An “Ad privacy choices” action appears when UMP requires it;
   updating choices removes the previous banner before a new request.
3. Set `android.testing: false` for an Android production release only after
   entering your real Android app and banner IDs. Leave `ios.testing: true` until
   iOS is ready. Platform flags override the top-level fallback `testing` value;
   the build rejects demo IDs for any platform configured in live mode. Requests currently use `npa: true`
   (non-personalized ads); the app does not independently prompt for ATT.
4. Run `npm run sync`, build the native apps, and test on physical devices.
   Confirm consent, banner layout in both orientations, no-fill/offline behavior,
   ad clicks, and uninterrupted music playback. Review the SDK data disclosures
   in Google Play Data safety and App Store App Privacy before submission.

Google's SKAdNetwork identifier is included. Add any further ad partner IDs from
Google's current iOS integration guide if enabling those partners/mediation.
Set `enabled: false` to stop banner requests without uninstalling the plugin.
This disables requests, but the SDK is still part of the native binary.

References: [plugin setup](https://github.com/capacitor-community/admob),
[Google Android setup](https://developers.google.com/admob/android/quick-start),
[Google iOS setup](https://developers.google.com/admob/ios/quick-start).


### Troubleshooting a missing banner on a test phone

Native builds with the platform's `testing: true` show an **Ad test status**
panel above Composition. It reports consent, initialization, loading, loaded,
or the exact SDK error. **Retry banner** checks consent again and removes the
previous request before retrying. The diagnostic panel is absent on the website
and in live-ad builds.

If the panel reports an account/configuration error during consent, check the
AdMob app ID and the privacy messages configured for that app in AdMob.
If it reports `canRequestAds=false`, no banner request has been made. If it
reports a banner error, keep its code and message for troubleshooting. This
panel does not bypass consent or change production ad settings.
