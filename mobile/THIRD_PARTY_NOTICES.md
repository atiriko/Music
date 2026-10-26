# Third-party software

The Python composition code remains in the desktop project and is bundled unchanged.

- react 19.3.1: MIT
- react-dom 19.3.1: MIT
- @capacitor/core 8.5.3: MIT
- @capacitor/app 8.1.2: MIT
- @capacitor/android 8.5.3: MIT
- @capacitor/ios 8.5.3: MIT
- @capacitor/filesystem 8.1.5: MIT
- @capacitor/preferences 8.0.1: MIT
- @capacitor/share 8.0.3: MIT
- @capacitor/status-bar 8.0.4: MIT
- stb-vorbis 0.0.6: Apache-2.0

- Pyodide 314.0.7: MPL-2.0, source: https://github.com/pyodide/pyodide
- CPython 3.14.2: PSF license, source: https://github.com/python/cpython
- NumPy 2.4.6: BSD-3-Clause; licenses included in the bundled wheel.
- Mido 1.3.3: MIT; source: https://github.com/mido/mido
- Packaging: BSD/Apache-2.0; source: https://github.com/pypa/packaging
- GeneralUser GS 2.0.3 by S. Christian Collins: license/source/hash in assets/soundfonts in the parent project and in the app soundfonts folder.

SpessaSynth core/library use Apache-2.0; their complete license files are included with the app. No Pyodide or third-party runtime source is modified.


## Additional instrument recordings

Studio Upright: FreePats Upright Piano KW, recorded by Gonzalo and Roberto, processed by Roberto. Version 2022-02-21, CC0 1.0. Source: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html

Studio Clean Guitar: FreePats FSBS Electric Guitar Clean, bridge small variant, version 2026-08-07, CC0 1.0. Studio Metal Guitar is a driven derivative of these recordings. Source: https://freepats.zenvoid.org/ElectricGuitar/clean-electric-guitar.html

Original credit and license files are included under `soundfonts/featured`. Preset bank/program headers are remapped for simultaneous playback. Studio Synths uses generated waveforms and contains no third-party recordings; it can be rebuilt with the parent project's `build_studio_sounds.py`.
