"""Normalize native project metadata after Capacitor sync, including Windows-to-Mac paths."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
package=ROOT/'ios/App/CapApp-SPM/Package.swift'
if package.exists():
    source=package.read_text()
    source=re.sub(r'path: "([^"]+)"',lambda match:'path: "'+match[1].replace('\\','/')+'"',source)
    package.write_text(source)
print('Native project paths normalized for Android Studio and Xcode.')
