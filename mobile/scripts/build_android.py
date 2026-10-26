"""Build a local Android debug APK without changing global Java/SDK settings."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--skip-sync',action='store_true',help='Use already-synced web assets.')
args=parser.parse_args()
if not args.skip_sync:
    npm='npm.cmd' if os.name=='nt' else 'npm'
    subprocess.run([npm,'run','sync'],cwd=ROOT,check=True,shell=os.name=='nt')
env=dict(os.environ)
tools=ROOT/'.tools'
if not env.get('JAVA_HOME') and (tools/'java-home.txt').is_file():
    env['JAVA_HOME']=(tools/'java-home.txt').read_text().strip()
if not env.get('ANDROID_HOME') and (tools/'android-sdk').is_dir():
    env['ANDROID_HOME']=str(tools/'android-sdk')
    env['ANDROID_SDK_ROOT']=env['ANDROID_HOME']
if env.get('ANDROID_HOME'):
    (ROOT/'android/local.properties').write_text('sdk.dir='+env['ANDROID_HOME'].replace('\\','/')+'\n')
wrapper=ROOT/'android'/('gradlew.bat' if os.name=='nt' else 'gradlew')
if os.name!='nt':wrapper.chmod(wrapper.stat().st_mode|0o100)
tools.mkdir(exist_ok=True)
log=tools/'android-build.log'
with log.open('w') as output:
    print('Building Android debug APK. Log:',log,flush=True)
    result=subprocess.run([str(wrapper),'--no-daemon','--max-workers=1','-Dorg.gradle.jvmargs=-Xmx768m -XX:ActiveProcessorCount=2','assembleDebug'],cwd=ROOT/'android',stdout=output,stderr=subprocess.STDOUT,env=env,shell=os.name=='nt')
if result.returncode:
    print(log.read_text(errors='replace')[-8000:]);sys.exit(result.returncode)
release=ROOT/'releases';release.mkdir(exist_ok=True)
target=release/'Music-Studio-android-debug.apk'
shutil.copy2(ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',target)
print('Created:',target)
print('Size:',round(target.stat().st_size/1024/1024,1),'MiB')
