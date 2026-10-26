"""Bundle original Python files, runtime, NumPy, and the existing SoundFont offline."""
from pathlib import Path
import hashlib
import importlib.util
import importlib.metadata
import json
import shutil
import urllib.request
import zipfile

MOBILE=Path(__file__).resolve().parents[1]
ROOT=MOBILE.parent
PUBLIC=MOBILE/'public'
RUNTIME=PUBLIC/'runtime'/'pyodide'
RUNTIME.mkdir(parents=True,exist_ok=True)
source=MOBILE/'node_modules'/'pyodide'
metadata=json.loads((source/'package.json').read_text(encoding='utf-8'))
for name in ['pyodide.js','pyodide.mjs','pyodide.asm.mjs','pyodide.asm.wasm','python_stdlib.zip','pyodide-lock.json']:
    shutil.copy2(source/name,RUNTIME/name)
lock=json.loads((source/'pyodide-lock.json').read_text())
needed=['numpy']
while needed:
    name=needed.pop()
    package=lock['packages'][name]
    target=RUNTIME/package['file_name']
    if not target.exists():
        url=f'https://cdn.jsdelivr.net/pyodide/v{metadata["version"]}/full/{package["file_name"]}'
        print('Bundling',package['file_name'],flush=True)
        urllib.request.urlretrieve(url,target)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=package['sha256']:
        raise RuntimeError('Runtime package checksum mismatch: '+name)
    needed.extend(package['depends'])
files=['counterpoint.py','presets.py','soundbanks.py','auto_song.py','arrangement.py','articulation.py','quality.py','phrasing.py','registers.py','accompaniment.py','performance.py','mix_settings.py','main.py','generator.py','drum_patterns.py','Event.py','Notes.py','Tempo.py','Sheduler.py',
       'Instruments.py','ProgressionStateMachine.py','song.py','midi_export.py']
with zipfile.ZipFile(PUBLIC/'engine.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in files:archive.write(ROOT/name,name)
    archive.write(MOBILE/'python'/'mobile_bridge.py','mobile_bridge.py')
    archive.write(ROOT/'assets/soundfonts/featured/catalog.json','assets/soundfonts/featured/catalog.json')
    for name in ['mido','packaging']:
        spec=importlib.util.find_spec(name)
        if not spec or not spec.origin:raise RuntimeError(f'Install {name} in your build Python environment.')
        package=Path(spec.origin).parent
        for path in package.rglob('*.py'):archive.write(path,str(Path(name)/path.relative_to(package)))
fonts=PUBLIC/'soundfonts';fonts.mkdir(exist_ok=True)
for name in ['GeneralUser-GS.sf2','LICENSE.txt','SOURCE.txt']:
    shutil.copy2(ROOT/'assets'/'soundfonts'/name,fonts/name)
featured=fonts/'featured';featured.mkdir(exist_ok=True)
for file in (ROOT/'assets/soundfonts/featured').rglob('*'):
    if file.is_file() and (file.suffix in ('.txt','.md','.json') or file.parent.name=='featured' and file.suffix=='.sf2'):
        target=featured/file.relative_to(ROOT/'assets/soundfonts/featured');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
synth=PUBLIC/'audio';synth.mkdir(exist_ok=True)
shutil.copy2(MOBILE/'node_modules'/'spessasynth_lib'/'dist'/'spessasynth_processor.min.js',synth/'processor.js')
shutil.copy2(ROOT/'examples'/'Example.song.json',PUBLIC/'Example.song.json')
licenses=PUBLIC/'licenses';licenses.mkdir(exist_ok=True)
for name in ['spessasynth_core','spessasynth_lib']:
    shutil.copy2(MOBILE/'node_modules'/name/'LICENSE',licenses/(name+'.txt'))
# License copies are generated on every clean build, not only on this machine.
for file in (MOBILE/'licenses').glob('*.txt'):
    shutil.copy2(file,licenses/file.name)
shutil.copy2(MOBILE/'THIRD_PARTY_NOTICES.md',PUBLIC/'THIRD_PARTY_NOTICES.md')
packages=['react','react-dom','@capacitor/core','@capacitor/app','@capacitor/android','@capacitor/ios',
          '@capacitor/filesystem','@capacitor/preferences','@capacitor/share','@capacitor/status-bar','stb-vorbis']
for name in packages:
    folder=MOBILE/'node_modules'/name
    for pattern in ('LICENSE*','LICENCE*'):
        for file in folder.glob(pattern):
            if file.is_file():
                shutil.copy2(file,licenses/(name.replace('@','').replace('/','-')+'-'+file.name+'.txt'))
for name in ('mido','packaging'):
    distribution=importlib.metadata.distribution(name)
    for file in distribution.files or ():
        if 'license' in str(file).lower() and not str(file).endswith('.py'):
            source=Path(distribution.locate_file(file))
            if source.is_file():shutil.copy2(source,licenses/(name+'-'+source.name+'.txt'))
print('Bundled the shared Python engine, offline runtime, NumPy, sampled instruments, and licenses.')
