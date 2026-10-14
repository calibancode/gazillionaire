# Verification

[Strict matching](CODE_MATCH.md): **99.66%** — **664,203 / 666,482 original code
bytes**, with **9,114 / 9,120 scoped bodies matching** and none missing or extra.
All 156 scoped script initializers now match; the six remaining bodies differ
only in the namespace kind of `mx.core`/`mx.styles` QNames.
The older P-code comparison (`tools/verify.sh`) agrees: **4,816 / 4,822 methods
(99.88%)** bytecode-identical, differing in the same six bodies. These measure
code reconstruction, not gameplay coverage.

```bash
python3 tools/measure_code.py   # strict, index-resolved matching
tools/verify.sh               # normalized P-code comparison
tools/verify_runtime.sh       # AIR 32 fixtures via Wine
```

The normalized verifier also ignores selected opcode aliases, namespace-set
ordering, registers and labels. Its remaining differences are all six namespace
kinds.

[Earlier comparison (2026-10-13)](reference/cleanup_verification_report.txt) ·
[Method worklist](reference/verification_diffs.tsv) ·
[Structural audit](reference/residual_audit.tsv)

The strict measurement and the P-code comparison were rerun on 2026-10-14:
rebuilding `planet_image_swf`'s selector chains recovered one body (447 original
code bytes) with no scoped regressions. The build, nine Python tests and shell
syntax checks passed. Two out-of-scope SDK method bodies changed with the
earlier include-order fix; see [code matching](CODE_MATCH.md).
The saved residual audit was last regenerated on 2026-10-13.
The optional whole-class summary in `verify.sh` exceeded the 240-second run
budget after the per-method report completed; its result is not claimed.

`classify_diffs.py` and `audit_residuals.py` accept original/rebuilt P-code
folders. `align_methods.py` maps method indices to source declarations.
Generate P-code with `ffdec -format script:pcode -export script DIR FILE.swf`;
allow several GB per comparison. Explained differences remain differences.

Saved AIR fixtures cover serialization, localization, helpers, trading,
selection markers, deterministic travel ordering and AI facility payments.
The probe supplies Flex controls without initializing the full document UI.
The runner rejects failed launches and incomplete, duplicate or error reports.
The harness passed on 2026-10-13 after the source-shape recovery changes, using
a fresh dedicated Wine prefix. All original/rebuilt fixture reports matched.
Those runtime fixtures have not been rerun after the include-order fix.

Rendered sessions, complete AI turns, random events, audio/video and persisted
save-slot loading remain unverified.
