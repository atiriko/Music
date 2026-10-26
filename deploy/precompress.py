"""Precompress browser assets so nginx can serve large banks without CPU work."""
import gzip
from pathlib import Path
import shutil
import sys


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    required = ('index.html', 'engine.zip', 'runtime/pyodide/pyodide.asm.wasm',
                'soundfonts/GeneralUser-GS.sf2', 'soundfonts/featured/catalog.json')
    for name in required:
        if not (root / name).is_file():
            raise SystemExit('Missing production asset: ' + name)
    count = 0
    for source in root.rglob('*'):
        if not source.is_file() or source.suffix not in {'.html', '.js', '.mjs', '.css', '.json', '.wasm', '.sf2'}:
            continue
        target = source.with_name(source.name + '.gz')
        with source.open('rb') as original, target.open('wb') as output:
            with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as compressed:
                shutil.copyfileobj(original, compressed, length=128 * 1024)
        if target.stat().st_size >= source.stat().st_size * .95:
            target.unlink()
        else:
            count += 1
    print(f'Validated production assets and precompressed {count} files.')


if __name__ == '__main__':
    main()
