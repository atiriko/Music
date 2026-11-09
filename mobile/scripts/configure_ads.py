"""Validate the shared AdMob IDs and write their native application metadata."""
import json
import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'admob.config.json').read_text())
for platform in ('android', 'ios'):
    ids = config[platform]
    for field, separator in [('appId', '~'), ('bannerId', '/')]:
        if not re.fullmatch(r'ca-app-pub-\d{16}' + re.escape(separator) + r'\d{10}', ids[field]):
            raise SystemExit(f'Invalid AdMob {platform} {field}')
        if not ids.get('testing', config['testing']) and ids[field].startswith('ca-app-pub-3940256099942544'):
            raise SystemExit('Live ads require your own app and banner IDs for that platform; keep testing=true for demo IDs.')

manifest = ROOT / 'android/app/src/main/AndroidManifest.xml'
text = manifest.read_text()
meta = ('<meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" '
        f'android:value="{config["android"]["appId"]}" />')
pattern = r'<meta-data\s+android:name="com.google.android.gms.ads.APPLICATION_ID"[^>]*?/>'
if re.search(pattern, text):
    text = re.sub(pattern, lambda _: meta, text)
else:
    text = text.replace('        <activity', '        ' + meta + '\n\n        <activity', 1)
manifest.write_text(text)

path = ROOT / 'ios/App/App/Info.plist'
with path.open('rb') as file:
    info = plistlib.load(file)
info['GADApplicationIdentifier'] = config['ios']['appId']
# Defer advertising SDK measurement until the JS consent gate initializes it.
info['GADDelayAppMeasurementInit'] = True
info['NSUserTrackingUsageDescription'] = 'Allow permission to use your device identifier for advertising measurement.'
items = info.setdefault('SKAdNetworkItems', [])
if not any(item.get('SKAdNetworkIdentifier') == 'cstr6suwn9.skadnetwork' for item in items):
    items.append({'SKAdNetworkIdentifier': 'cstr6suwn9.skadnetwork'})
with path.open('wb') as file:
    plistlib.dump(info, file, sort_keys=False)
print('AdMob IDs configured: ' + ', '.join(platform + '=' + ('test ads' if config[platform].get('testing', config['testing']) else 'live ads') for platform in ('android', 'ios')))
