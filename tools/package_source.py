#!/usr/bin/env python3
"""Stage a source-only archive without relying on local Git metadata."""
import argparse
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
files = [ROOT / name for name in ('.gitignore', 'README.md', 'LICENSE')]
for directory in ('tools', 'docs'):
    files.extend(p for p in (ROOT / directory).rglob('*')
                 if p.is_file() and not p.is_symlink()
                 and '__pycache__' not in p.parts
                 and p.suffix in {'.py', '.sh', '.java', '.as', '.xml', '.json', '.txt', '.tsv', '.md'})
with tarfile.open(args.output, 'w:gz') as archive:
    for path in sorted(files):
        archive.add(path, arcname=str(Path('gazillionaire-reconstruction') / path.relative_to(ROOT)), recursive=False)
print(args.output)
