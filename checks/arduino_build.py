"""Build canonical firmware sources with Arduino CLI; upload only when requested."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cli', default='arduino-cli')
parser.add_argument('--port', help='Actual connected serial port; required for upload')
parser.add_argument('--upload', action='store_true')
args = parser.parse_args()
if args.upload and not args.port:
    parser.error('--upload requires an explicit --port')
sketch = ROOT / '.runtime/arduino/AtomCompanion'
sketch.mkdir(parents=True, exist_ok=True)
for folder in ('src', 'include'):
    for source in (ROOT / 'firmware' / folder).iterdir():
        if source.suffix in ('.cpp', '.h'):
            target=sketch / source.name
            if not target.exists() or source.read_bytes()!=target.read_bytes():
                shutil.copyfile(source,target)
stub='// setup() and loop() are in canonical main.cpp.\n#include <Arduino.h>\n'
if not (sketch/'AtomCompanion.ino').exists() or (sketch/'AtomCompanion.ino').read_text(encoding='utf-8')!=stub:
    (sketch/'AtomCompanion.ino').write_text(stub,encoding='utf-8')
fqbn = 'm5stack:esp32:m5stack_atoms3r'
out = ROOT / 'outputs/atoms3r-echo'
out.mkdir(parents=True, exist_ok=True)
subprocess.run([args.cli, 'compile', '--fqbn', fqbn, '--jobs', '2',
                '--build-path', str(ROOT / '.runtime/arduino/build'), '--output-dir', str(out), str(sketch)], check=True)
if args.upload:
    subprocess.run([args.cli, 'upload', '--fqbn', fqbn, '--port', args.port,
                    '--input-dir', str(out), str(sketch)], check=True)
print('Arduino build complete' + ('; upload complete on ' + args.port if args.upload else '; no upload requested'))
