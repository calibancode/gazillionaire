# Verification

[Strict matching](CODE_MATCH.md): **100.00%** — **666,482 / 666,482 original code
bytes**, with **9,120 / 9,120 scoped bodies matching** and none missing or extra.
All 156 scoped script initializers and all six MXML-backend-generated bodies
match.
The older P-code comparison (`tools/verify.sh`) agrees: **4,822 / 4,822 methods
(100.00%)** bytecode-identical, with an empty worklist. These measure
code reconstruction, not gameplay coverage.

```bash
python3 tools/measure_code.py   # strict, index-resolved matching
tools/verify.sh               # normalized P-code comparison
tools/verify_runtime.sh       # AIR 32 fixtures via Wine
```

The normalized verifier also ignores selected opcode aliases, namespace-set
ordering, registers and labels. It reports no remaining method differences.

[Earlier comparison (2026-10-13)](reference/cleanup_verification_report.txt) ·
[Method worklist](reference/verification_diffs.tsv) ·
[Structural audit](reference/residual_audit.tsv)

The strict measurement, the P-code comparison and the AIR runtime fixtures were
rerun on 2026-10-15: the MXML-backend namespace restoration recovered the last
six bodies (2,279 original code bytes) without changing any other canonical
body, and the runtime fixtures still match. The build, nine Python tests and
shell syntax checks passed. Two out-of-scope SDK method bodies changed with the
earlier include-order fix; see [code matching](CODE_MATCH.md).
The saved residual audit was last regenerated on 2026-10-13.
The optional whole-class summary in `verify.sh` completed on 2026-10-15, but its
coarser file-level comparison is not claimed: it reports 36 differing class
files (the embed classes and the two big class files) whose constituent methods
the per-method comparator above matches.

`classify_diffs.py` and `audit_residuals.py` accept original/rebuilt P-code
folders. `align_methods.py` maps method indices to source declarations.
Generate P-code with `ffdec -format script:pcode -export script DIR FILE.swf`;
allow several GB per comparison. Explained differences remain differences.

Saved AIR fixtures cover serialization, localization, helpers, trading,
selection markers, deterministic travel ordering and AI facility payments.
The probe supplies Flex controls without initializing the full document UI.
The runner rejects failed launches and incomplete, duplicate or error reports.
The harness passed on 2026-10-13 after the source-shape recovery changes and
again on 2026-10-15 after the namespace restoration, using the dedicated Wine
prefix. All original/rebuilt fixture reports matched.

Rendered sessions, complete AI turns, random events, audio/video and persisted
save-slot loading remain unverified.
