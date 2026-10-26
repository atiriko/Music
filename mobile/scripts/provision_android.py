from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request
import zipfile

root=Path(__file__).resolve().parents[1]/'.tools'
root.mkdir(exist_ok=True)

def fetch(url,path,checksum=None):
    if not path.exists():
        print('Downloading',path.name,flush=True)
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})) as response,path.open('wb') as out:
            while chunk:=response.read(1024*1024):out.write(chunk)
    if checksum and hashlib.sha256(path.read_bytes()).hexdigest()!=checksum:
        raise RuntimeError('Checksum mismatch: '+str(path))
    return path

def jdk():
    if (root/'java-home.txt').exists() and Path((root/'java-home.txt').read_text()).is_dir():return
    archive=fetch('https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.zip',root/'jdk21.zip')
    with zipfile.ZipFile(archive) as z:
        prefix=z.namelist()[0].split('/')[0]
        z.extractall(root/'java')
    (root/'java'/prefix).resolve().relative_to(root.resolve())
    (root/'java-home.txt').write_text(str((root/'java'/prefix).resolve()))
    print('JDK 21 ready',flush=True)

def sdk():
    target=root/'android-sdk'/'cmdline-tools'/'latest'
    if target.exists():return
    archive=fetch('https://dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip',root/'android-tools.zip')
    with zipfile.ZipFile(archive) as z:z.extractall(root/'sdk-extract')
    target.parent.mkdir(parents=True,exist_ok=True)
    (root/'sdk-extract'/'cmdline-tools').resolve().relative_to(root.resolve())
    target.resolve().relative_to(root.resolve())
    (root/'sdk-extract'/'cmdline-tools').rename(target)
    print('Android command-line tools ready',flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(lambda function:function(),[jdk,sdk]):pass
