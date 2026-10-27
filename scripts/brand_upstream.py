#!/usr/bin/env python3
"""Apply a small, explicit branding patch to a checked-out Shizuku source tree."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: brand_upstream.py <upstream-directory>")

root = Path(sys.argv[1]).resolve()
gradle = root / "manager/build.gradle"
manifest = root / "manager/src/main/AndroidManifest.xml"
strings_root = root / "manager/src/main/res"
if not gradle.exists() or not manifest.exists() or not strings_root.exists():
    raise SystemExit("Not a recognized Shizuku source tree; expected manager/build.gradle and AndroidManifest.xml")

text = gradle.read_text(encoding="utf-8")
old_id = 'applicationId "moe.shizuku.privileged.api"'
new_id = 'applicationId "com.zoro.shizukupro"'
if old_id in text:
    text = text.replace(old_id, new_id, 1)
elif new_id not in text:
    raise SystemExit("Could not find expected applicationId; upstream layout may have changed.")
text = text.replace('outputFileName = "shizuku-v${variant.versionName}-${variant.name}.apk"',
                    'outputFileName = "ZORO-SHIZUKU-PRO-${variant.name}.apk"')
gradle.write_text(text, encoding="utf-8")

for base in [root / "manager", root / "api", root / "server", root / "common", root / "starter", root / "shell"]:
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".xml", ".kt", ".java", ".aidl", ".gradle", ".properties", ".txt"}:
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        s2 = s.replace("moe.shizuku.manager.permission-group.", "com.zoro.shizukupro.permission-group.")
        s2 = s2.replace("moe.shizuku.manager.permission.", "com.zoro.shizukupro.permission.")
        if s2 != s:
            p.write_text(s2, encoding="utf-8")

for p in strings_root.rglob("strings.xml"):
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    s2 = s.replace('<string name="app_name" translatable="false">Shizuku</string>',
                   '<string name="app_name" translatable="false">ZORO SHIZUKU PRO</string>')
    s2 = s2.replace('<string name="app_name">Shizuku</string>',
                    '<string name="app_name">ZORO SHIZUKU PRO</string>')
    if s2 != s:
        p.write_text(s2, encoding="utf-8")

drawable = root / "manager/src/main/res/drawable"
drawable.mkdir(parents=True, exist_ok=True)
(drawable / "zoro_launcher.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#101820" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#00E676" android:pathData="M22,25h64v10L39,73h47v10H22V73L69,35H22z"/>
    <path android:fillColor="#FFFFFF" android:pathData="M25,17h58v4H25zM25,87h58v4H25z"/>
</vector>
''', encoding="utf-8")
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:icon="@drawable/ic_launcher"', 'android:icon="@drawable/zoro_launcher"')
m = m.replace('android:banner="@drawable/ic_launcher"', 'android:banner="@drawable/zoro_launcher"')
m = m.replace('android:banner="@mipmap/banner"', 'android:banner="@drawable/zoro_launcher"')
manifest.write_text(m, encoding="utf-8")

print("Branding patch applied; app ID set to com.zoro.shizukupro.")
print("This script does not certify API-level drop-in compatibility; test the resulting APK on-device.")
