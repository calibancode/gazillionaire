# Verification

[Strict matching](CODE_MATCH.md): **80.04%**, with all 9,120 scoped bodies present.
Normalized comparison: **4,804 / 4,822 methods (99.63%)**. These measure code
reconstruction, not gameplay coverage.

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
| 4 | Jumps to the next instruction |
| 1 | Boolean branch folding |
| 7 | Resource-object member order |

[Saved comparison](reference/cleanup_verification_report.txt) ·
[Method worklist](reference/verification_diffs.tsv) ·
[Structural audit](reference/residual_audit.tsv)

`classify_diffs.py` and `audit_residuals.py` accept original/rebuilt P-code
folders. `align_methods.py` maps method indices to source declarations.
Generate P-code with `ffdec -format script:pcode -export script DIR FILE.swf`;
allow several GB per comparison. Explained differences remain differences.

Saved AIR fixtures cover serialization, localization, helpers, trading,
selection markers, deterministic travel ordering and AI facility payments.
The probe supplies Flex controls without initializing the full document UI.
The runner rejects failed launches and incomplete, duplicate or error reports.
The harness has not been rerun since the data-path migration.

Rendered sessions, complete AI turns, random events, audio/video and persisted
save-slot loading remain unverified.
