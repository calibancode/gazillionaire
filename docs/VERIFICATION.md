# Verification

[Strict matching](CODE_MATCH.md): **99.59%** — **663,756 / 666,482 original code
bytes**, with **9,113 / 9,120 scoped bodies matching** and none missing or extra.
All 156 scoped script initializers now match; the seven remaining bodies differ
in namespace kind or the unreachable `planet_image_swf` jump.
The saved normalized comparison from the preceding source-shape recovery is
**4,815 / 4,822 methods (99.85%)**; it was not rerun after the include-order fix.
These measure code reconstruction, not gameplay coverage.

```bash
python3 tools/measure_code.py   # strict, index-resolved matching
tools/verify.sh               # normalized P-code comparison
tools/verify_runtime.sh       # AIR 32 fixtures via Wine
```

The normalized verifier also ignores selected opcode aliases, namespace-set
ordering, registers and labels. Its remaining differences are:

| Methods | Difference |
|---:|---|
| 6 | Namespace kind |
| 1 | Unreachable jump (rendered as a next-instruction jump by JPEXS) |

[Saved comparison](reference/cleanup_verification_report.txt) ·
[Method worklist](reference/verification_diffs.tsv) ·
[Structural audit](reference/residual_audit.tsv)

The strict measurement was rerun on 2026-10-13 after the include-order fix:
39 script bodies recovered 2,171 original code bytes, with no scoped regressions.
The build, eight Python tests and shell syntax checks passed. Two out-of-scope
SDK method bodies also changed; see [code matching](CODE_MATCH.md).
The saved normalized per-method comparison and residual audit were last rerun
on 2026-10-13 before that fix.
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
