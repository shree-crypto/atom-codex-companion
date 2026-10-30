"""Build public downloads from an explicit project-file allowlist."""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'sites' / 'atom-expression-lab' / 'dist'
OUT = DIST / 'downloads'


def archive(path, files, prefix=''):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for file, name in sorted(files, key=lambda item: item[1]):
            z.write(file, prefix + name)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert not any(part in {'.runtime', '.git', '.venv', '.pio', '.pio-core', 'node_modules', '__pycache__'}
                       for name in z.namelist() for part in Path(name).parts)


def guide_html(markdown):
    blocks = []
    code = None
    listing = False
    def inline(line):
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', html.escape(line))
    for line in markdown.splitlines():
        if line.startswith('```'):
            if code is None:
                code = []
            else:
                blocks.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if not line.startswith('- ') and listing:
            blocks.append('</ul>')
            listing = False
        if line.startswith('# '):
            blocks.append('<h1>' + inline(line[2:]) + '</h1>')
        elif line.startswith('## '):
            blocks.append('<h2>' + inline(line[3:]) + '</h2>')
        elif line.startswith('- '):
            if not listing:
                blocks.append('<ul>')
                listing = True
            blocks.append('<li>' + inline(line[2:]) + '</li>')
        elif line.strip():
            blocks.append('<p>' + inline(line) + '</p>')
    if listing:
        blocks.append('</ul>')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atom — step-by-step setup</title><link rel="stylesheet" href="style.css"></head><body><header><a class="brand" href="./">← ATOM / EXPRESSION LAB</a><a href="downloads/atom-companion-source.zip" download>Download source kit</a></header><main class="guide">' + ''.join(blocks) + '<p><a href="https://learn.chatgpt.com/docs/hooks">Official Codex hook documentation</a> · <a href="downloads/GETTING_STARTED.md" download>Save this guide</a> · <a href="./#downloads">All downloads</a></p></main></body></html>'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('revision-2-front.png','revision-2-assembled.png','revision-2-exploded.png'):
        shutil.copyfile(ROOT/'assets'/name,DIST/name)
    for name in ['index.html', 'style.css', 'app.mjs', 'audio.mjs', 'anime.mjs', 'device-voices.mjs', 'face.mjs', 'definitions.mjs']:
        shutil.copyfile(ROOT / 'preview' / name, DIST / name)
    shutil.copytree(ROOT / 'preview/voices', DIST / 'voices', dirs_exist_ok=True)
    patterns = ['README.md', 'GETTING_STARTED.md', 'requirements*.txt',
                'companion/*.py', 'hooks/*.py', 'hooks/config.example.json',
                'assets/*.png', 'firmware/*.md', 'firmware/platformio.ini', 'firmware/src/*.cpp', 'firmware/include/*.h',
                'firmware/test/test_limits/*.cpp', 'expressions/*.py', 'expressions/definitions.json', 'expressions/device_voice_pack.json',
                'preview/*.mjs', 'preview/*.html', 'preview/*.css', 'preview/voices/*.md', 'preview/voices/*.txt', 'preview/voices/*.json',
                'preview/voices/*/*.wav', 'preview/voices/*/*.ogg', 'tests/*.py', 'tests/*.mjs',
                'checks/*.py', 'checks/ACCEPTANCE.md', 'checks/event-coverage.md', 'checks/CODEX_AVATAR_BACKEND.md', 'checks/HARDWARE_S3R_ECHO.md', 'checks/hardware-s3r-echo.json',
                'cad/*.py', 'cad/dimensions.json']
    sources = sorted({p for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()})
    assert sources and (ROOT / 'GETTING_STARTED.md') in sources
    archive(OUT / 'atom-companion-source.zip', [(p, p.relative_to(ROOT).as_posix()) for p in sources], 'robot-companion/')
    archive(OUT / 'recorded-voice-clips.zip', [(p, p.relative_to(ROOT / 'preview/voices').as_posix()) for p in (ROOT / 'preview/voices').rglob('*') if p.is_file()])
    models = []
    for kind in ['STL', 'STEP', '3MF']:
        for name in ['body', 'bezel', 'keeper', 'bezel_print'] + (['fit_coupons'] if kind == 'STL' else []):
            p = ROOT / 'cad' / kind / (name + '.' + kind.lower())
            assert p.is_file() and p.stat().st_size > 0
            models.append((p, kind + '/' + p.name))
    archive(OUT / 'classic-enclosure-models.zip', models + [(ROOT / 'GETTING_STARTED.md', 'GETTING_STARTED.md')])
    bezel_files=[(p,n) for p,n in models if Path(n).stem in ('bezel','bezel_print')]
    archive(OUT/'bezel-only-update.zip',bezel_files+[(ROOT/'GETTING_STARTED.md','GETTING_STARTED.md')])
    for name in ['body', 'bezel', 'keeper', 'bezel_print', 'fit_coupons']:
        shutil.copyfile(ROOT / 'cad' / 'STL' / (name + '.stl'), OUT / (name + '.stl'))
    shutil.copyfile(ROOT / 'outputs' / 'atom-s3r-echo-firmware.bin', OUT / 'atom-s3r-echo-firmware.bin')
    shutil.copyfile(ROOT / 'GETTING_STARTED.md', OUT / 'GETTING_STARTED.md')
    (DIST / 'setup.html').write_text(guide_html((ROOT / 'GETTING_STARTED.md').read_text(encoding='utf-8')), encoding='utf-8')
    manifest = [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'checksums.json']
    (OUT / 'checksums.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_files': len(sources), 'model_files': len(models), 'downloads': manifest}, indent=2))


if __name__ == '__main__':
    main()
