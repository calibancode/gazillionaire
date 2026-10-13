# Code matching

Measured on 2026-10-12 after rebuilding with the configurable local data paths:

| Scope | Matching original code bytes | Code matched | Matching method bodies |
|---|---:|---:|---:|
| Reconstructed application | 533,448 / 666,482 | **80.04%** | 8,962 / 9,120 |
| Five core game classes | 510,932 / 638,282 | 80.05% | 8,442 / 8,545 |
| Generated application classes | 21,666 / 24,356 | 88.96% | 471 / 511 |
| Resources and skins | 850 / 3,844 | 22.11% | 49 / 64 |

There are no missing or extra application method bodies in this comparison.
The scope is the fixed list of 156 reconstructed classes in
[`classes.txt`](../tools/code_match/classes.txt); bundled SDK classes are excluded.
The core comprises `Gazillionaire`, `GameType`, `PlayerType`, `OpponentType` and
`GameStrings`. Closures and script/class/instance initializers count separately,
so these counts exceed the older P-code comparator's top-level method counts.

## Definition

Code matched = original instruction bytes in matching method bodies / original
instruction bytes in all scoped method bodies. Each body receives all its
original byte weight or zero. Constant pools, assets and SWF container bytes
are not part of that weight. Missing bodies retain their denominator weight;
extra bodies earn no credit. A missing scoped class aborts the measurement.

Matching compares decoded opcodes and resolved operands, signatures, body limits,
activation slots and exception tables. Constant-pool indices are resolved to
values; class/method indices become structural identities. Branch offsets become
instruction targets. Non-instruction targets in unreachable original code retain
their literal byte addresses. Private namespaces retain distinct structural
identities anchored to their class/activation or lexical namespace set; identity
collisions or unresolved scoped namespaces abort. Methods are identified by class,
trait kind/name and static/instance role; closures use their enclosing method and
`newfunction` occurrence. Ambiguous ownership aborts.

Namespace kinds and complete ordered namespace sets, registers, property opcodes
and literal construction order remain significant. No opcode aliases or semantic
rewrites are applied. A linear decoder retains unreachable instructions and checks
byte-for-byte re-encoding against every original/rebuilt body.

The existing **99.63% normalized methods matched** is a separate diagnostic.
It tolerates distinctions this measurement preserves, including `initproperty`
versus `setproperty`. Some differing methods are large, so their full byte weights
substantially lower this score. Neither figure measures gameplay coverage or proves
semantic equivalence. This metric does not verify class layout or non-code data.

## Reproduce

Requires Python 3, a JDK with `javac` (17+), and JPEXS 24.1.1:

```bash
python3 tools/measure_code.py
# Other JPEXS installation:
python3 tools/measure_code.py --ffdec-jar /path/to/ffdec.jar
```

This measures the supplied SWFs; it does not rebuild them. Output is under
`build/code_match/`. The saved [report](reference/code_match_report.json) records
SWF, scope, measurer and JPEXS hashes. The [worklist](reference/code_match_differences.tsv)
contains all 158 differing application method bodies.

Validation: full original-versus-original comparison scored 100% in every scope;
negative controls detected opcode, string-pool value, namespace-set order and
exception-target changes. Coverage tests check missing and extra method weighting.
`CheckMeasurement.java` contains the bytecode controls; coverage tests run with
`python3 -m unittest discover -s tools/code_match -p 'test_*.py'`.
