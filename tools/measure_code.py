#!/usr/bin/env python3
"""Measure original-byte-weighted AVM2 matching (JPEXS 24.1.1, JDK 17+)."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from paths import DATA

ROOT = Path(__file__).resolve().parent.parent


def inventory(path):
    rows = {}
    with path.open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            key = row['identity']
            if key in rows:
                raise ValueError(f'Duplicate method identity: {key}')
            rows[key] = row
    return rows


def measure(original, rebuilt, scopes):
    rows = [r for r in original.values() if r['scope'] in scopes]
    matching = [r for r in rows if r['identity'] in rebuilt
                and r['sha256'] == rebuilt[r['identity']]['sha256']]
    total = sum(int(r['code_bytes']) for r in rows)
    matched = sum(int(r['code_bytes']) for r in matching)
    return dict(total_methods=len(rows), matched_methods=len(matching),
                total_code_bytes=total, matched_code_bytes=matched,
                code_matched_percent=100 * matched / total if total else None,
                missing_methods=sum(r['identity'] not in rebuilt for r in rows),
                extra_methods=sum(k not in original and r['scope'] in scopes
                                  for k, r in rebuilt.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=DATA/'original/Gazillionaire.swf')
    parser.add_argument('--rebuilt', type=Path, default=ROOT/'build/Gazillionaire.swf')
    parser.add_argument('--ffdec-jar', type=Path, default=Path('/usr/share/java/ffdec/ffdec.jar'))
    parser.add_argument('--output', type=Path, default=ROOT/'build/code_match')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = ROOT/'tools/code_match/MeasureCode.java'
    manifest = ROOT/'tools/code_match/classes.txt'
    with tempfile.TemporaryDirectory(prefix='gaz-code-match-') as temp:
        subprocess.run(['javac', '-cp', str(args.ffdec_jar), '-d', temp, str(source)], check=True)
        for label, swf in [('original', args.original), ('rebuilt', args.rebuilt)]:
            subprocess.run(['java', '-Djava.awt.headless=true', f'-Duser.home={temp}',
                            '-cp', f'{temp}:{args.ffdec_jar}', 'MeasureCode', str(swf),
                            str(args.output/label), str(manifest)], check=True)
    original = inventory(args.output/'original/inventory.tsv')
    rebuilt = inventory(args.output/'rebuilt/inventory.tsv')
    report = {
        'metric_version': 1,
        'description': 'Strict index-resolved method matching, weighted by original AVM2 code bytes',
        'original_sha256': hashlib.sha256(args.original.read_bytes()).hexdigest(),
        'rebuilt_sha256': hashlib.sha256(args.rebuilt.read_bytes()).hexdigest(),
        'scope_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'measurer_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'jpexs_jar_sha256': hashlib.sha256(args.ffdec_jar.read_bytes()).hexdigest(),
        'application': measure(original, rebuilt, {'game', 'generated', 'support'}),
        'core_game': measure(original, rebuilt, {'game'}),
        'generated_application': measure(original, rebuilt, {'generated'}),
        'resources_and_skins': measure(original, rebuilt, {'support'}),
    }
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    with (args.output/'differences.tsv').open('w') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['identity', 'scope', 'original_code_bytes', 'status'])
        for key, row in sorted(original.items()):
            if row['scope'] == 'framework':
                continue
            if key not in rebuilt or row['sha256'] != rebuilt[key]['sha256']:
                writer.writerow([key, row['scope'], row['code_bytes'],
                                 'missing' if key not in rebuilt else 'different'])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
