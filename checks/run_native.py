"""Compile and execute the actual firmware parser/motion tests on Windows."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    output = ROOT / '.runtime' / 'native-tests.exe'
    output.parent.mkdir(exist_ok=True)
    env = dict(os.environ)
    env['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT / '.runtime' / 'zig-cache')
    env['ZIG_LOCAL_CACHE_DIR'] = str(ROOT / '.runtime' / 'zig-local-cache')
    lib = ROOT / 'firmware' / '.pio' / 'libdeps' / 'atoms3' / 'ArduinoJson' / 'src'
    command = [sys.executable, '-m', 'ziglang', 'c++', '-std=c++17',
               '-I'+str(ROOT/'firmware'/'include'), '-I'+str(lib),
               str(ROOT/'firmware'/'test'/'test_limits'/'test_main.cpp'), '-o', str(output)]
    subprocess.run(command, env=env, check=True)
    subprocess.run([str(output)], check=True)
    print('Native parser and motion assertions passed.')
