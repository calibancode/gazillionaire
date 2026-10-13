"""Generate the implicit-member worklist from MeasureCode canonical dumps.

Run MeasureCode with an empty fourth argument to dump every body, then pass
the original/rebuilt output directories. This never copies executable code.
"""
import argparse
import csv
import json
import re
from pathlib import Path


def inventory(directory):
    with (directory / 'inventory.tsv').open() as stream:
        return {r['identity']: r for r in csv.DictReader(stream, delimiter='\t')}


def name(text):
    match = re.search(r'mn7\((\d+):', text)
    return text[match.end():match.end() + int(match[1])] if match else None


def generate(original, rebuilt, sources):
    before, after = inventory(original), inventory(rebuilt)
    plan = {}
    for identity, row in before.items():
        if (row['scope'] == 'framework' or identity not in after
                or row['sha256'] == after[identity]['sha256']
                or '/instance/' not in identity):
            continue
        a = (original / (row['sha256'] + '.txt')).read_text().splitlines()[1:]
        b = (rebuilt / (after[identity]['sha256'] + '.txt')).read_text().splitlines()[1:]
        if len(a) != len(b):
            continue
        targets = {name(x) for x, y in zip(a, b) if x.startswith('initproperty ')
                   and y == x.replace('initproperty ', 'setproperty ', 1)}
        if not targets:
            continue
        filename = identity.split('/')[0] + '.as'
        method = name(identity)
        text = (sources / filename).read_text()
        declaration = re.search(r'^      .*function (?:(?:get|set) )?'
                                + re.escape(method) + r'\(', text, re.M)
        if declaration is None:
            raise ValueError('missing method: ' + identity)
        start = declaration.start()
        body = text[start:text.index('\n      }', start)]
        properties = {}
        for prop in sorted(targets):
            instructions = [x for x in a if re.match(r'(?:setproperty|initproperty) ', x)
                            and name(x) == prop]
            matches = list(re.finditer(r'\bthis\.' + re.escape(prop)
                                      + r'\s*[+\-*/]?=(?!=)', body))
            if len(matches) != len(instructions):
                raise ValueError('assignment count mismatch: ' + identity + '/' + prop)
            # This baseline has no mixed explicit/implicit writes for a target.
            if not all(x.startswith('initproperty ') for x in instructions):
                raise ValueError('mixed writes require an occurrence worklist: ' + identity)
            properties[prop] = len(matches)
        plan.setdefault(filename, {})[method] = properties
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('rebuilt', type=Path)
    parser.add_argument('--sources', type=Path, default=Path('app/src'))
    parser.add_argument('--output', type=Path, default=Path('tools/member_cleanup.json'))
    args = parser.parse_args()
    args.output.write_text(json.dumps(generate(args.original, args.rebuilt, args.sources),
                                     indent=2) + '\n')
