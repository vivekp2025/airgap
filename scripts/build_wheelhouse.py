"""GitHub Actions builder: resolved cross-platform binary wheel bundle."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone

PY = os.environ['TARGET_PYTHON']
PLATFORM = os.environ['TARGET_PLATFORM']
if PY not in {'3.10','3.11','3.12','3.13','3.14'}:
    raise SystemExit('Unsupported Python version')
if PLATFORM not in {'win_amd64','win32','win_arm64','manylinux2014_x86_64'}:
    raise SystemExit('Unsupported platform')
raw = os.environ['PACKAGES']
lines = [x.strip() for x in raw.splitlines() if x.strip() and not x.lstrip().startswith('#')]
if not lines or len(lines) > 50:
    raise SystemExit('Enter 1 to 50 package requirements')
# Deliberately permit only ordinary PyPI requirements, not URL/file/options/commands.
allowed = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9_,.-]+\])?(?:\s*(?:===|==|~=|!=|<=|>=|<|>)\s*[A-Za-z0-9*_.+!-]+(?:\s*,\s*(?:===|==|~=|!=|<=|>=|<|>)\s*[A-Za-z0-9*_.+!-]+)*)?$')
for x in lines:
    if not allowed.fullmatch(x):
        raise SystemExit(f'Invalid requirement {x!r}. Use plain PyPI package names with optional version constraints.')
root = Path('bundle')
wheelhouse = root / 'wheelhouse'
wheelhouse.mkdir(parents=True, exist_ok=True)
requirements = root / 'requirements.txt'
requirements.write_text('\n'.join(lines)+'\n', encoding='utf-8')
py_digits = PY.replace('.', '')
# abi3 wheels supported across CPython minor versions; none supports pure Python wheels.
cmd = [sys.executable, '-m', 'pip', 'download', '-r', str(requirements),
       '--dest', str(wheelhouse), '--only-binary=:all:',
       '--platform', PLATFORM, '--python-version', PY,
       '--implementation', 'cp', '--abi', f'cp{py_digits}', '--abi', 'abi3', '--abi', 'none',
       '--disable-pip-version-check']
print('Executing:', ' '.join(cmd), flush=True)
subprocess.run(cmd, check=True)
wheels = sorted(wheelhouse.glob('*.whl'))
if not wheels:
    raise SystemExit('Nothing was downloaded')
manifest = {
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'target_python': PY,
    'target_platform': PLATFORM,
    'requirements': lines,
    'wheels': [
        {'file': f.name, 'bytes': f.stat().st_size,
         'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
        for f in wheels
    ]
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
(root / 'INSTALL_OFFLINE.bat').write_text(
    '@echo off\nsetlocal\ncd /d "%~dp0"\n'
    'echo Installing using locally available wheel files only...\n'
    'python -m pip install --no-index --find-links="%~dp0wheelhouse" -r "%~dp0requirements.txt"\n'
    'if errorlevel 1 (echo INSTALLATION FAILED & pause & exit /b 1)\n'
    'python -m pip check\n'
    'pause\n', encoding='utf-8')
(root / 'VERIFY_OFFLINE.bat').write_text(
    '@echo off\nsetlocal\ncd /d "%~dp0"\n'
    'python -m pip --version\n'
    'python -c "import sys,platform; print(sys.version); print(platform.platform()); print(platform.architecture())"\n'
    'python -m pip check\n'
    'pause\n', encoding='utf-8')
(root / 'README_OFFLINE.txt').write_text(
    f'Target: CPython {PY}, {PLATFORM}\n\n'
    'Copy/extract entire bundle to the air-gapped Windows computer.\n'
    'Check Python version and CPU architecture match the target.\n'
    'Run INSTALL_OFFLINE.bat, or use your exact Python executable:\n'
    r'  "D:\path\to\python.exe" -m pip install --no-index --find-links=wheelhouse -r requirements.txt' + '\n'
    'Installation requires that pip is already installed and works on the offline Python environment.\n'
    'If another installed package conflicts with a dependency, use a clean virtual environment.\n'
    'Wheels with no binary release for the selected target cause the build to fail; see Actions logs.\n'
    'A Linux target requires manual installation (BAT files are for Windows).\n'
    'Review third-party code and licenses as per your organisation policy.\n', encoding='utf-8')
dist = Path('dist')
dist.mkdir(exist_ok=True)
out = dist / f'offline-wheels-cp{py_digits}-{PLATFORM}.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in root.rglob('*'):
        if f.is_file():
            z.write(f, f.relative_to(root))
print('Created', out, '| wheels:',len(wheels), '| bytes:', out.stat().st_size)
