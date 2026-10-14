# ASC codegen probes

Single-file ActionScript programs compiled with the project's `amxmlc`
(Flex 4.16.1 + AIR 32) and disassembled with `ffdec -format script:pcode`
to test **how a given source spelling compiles**, before rewriting the
decompiled game source to match the original bytecode.

Reproduce any probe with:

```bash
FLEX_HOME=$PWD/../../sdk AIR_HOME=$PWD/../../sdk ../../sdk/bin/amxmlc -source-path=. PROBE.as
ffdec -format script:pcode -export script OUT PROBE.swf
```

## Findings so far

### `use namespace mx_internal;` flips namespace-qualified codegen

`ProbeTest2.as` (no `use namespace`) vs `ProbeTest3.as` (with it), both
containing `mx_internal::_document = this;`:

| source | emitted P-code |
|--------|----------------|
| `import mx.core.mx_internal;` **only** | `getlex QName(PackageNamespace("mx.core"),"mx_internal")` / `coerce Namespace` / `findpropstrict RTQName("_document")` / … `setproperty RTQName("_document")` — the namespace **value** is loaded and the member is a runtime-qualified RTQName |
| same + `use namespace mx_internal;` | `findproperty QName(Namespace("http://www.adobe.com/2006/flex/mx/internal"),"_document")` / `setproperty QName(...)` — a static QName |

The original SWF shows the **RTQName** form everywhere `mx_internal::` is
used — i.e. the original source had **no `use namespace mx_internal;`**;
that directive is an ffdec addition (the 8-method `rtqname` diff category).
Removing it should restore the original codegen.

### Import spelling does not explain plain `Namespace("pkg")` QNames

The original sometimes refers to `mx.styles.CSSStyleDeclaration` /
`CSSCondition` / `CSSSelector` through a plain `Namespace("mx.styles")`
multiname (60 refs, all in the MXML-generated style-selector code inside
closures) where the rebuild emits `PackageNamespace("mx.styles")` — and it
uses *both* kinds in the same class, so it is per-site, not per-import.

Probed so far, **all of which still emit `PackageNamespace`**:

* `import mx.styles.CSSStyleDeclaration;` (`ProbeTest.as` `e()`)
* `import mx.styles.*;` (`ProbeW1.as`)
* `import mx.core.*;` + `import mx.styles.*;` (`ProbeW4.as`; also loses the
  RTQName form for `mx_internal::`, so the original cannot have used an
  `mx.core` wildcard)
* references inside `newfunction` closures (`ProbeC1.as`) — inconclusive:
  the closure body did not surface in the exported P-code as expected, so
  this case needs a better probe (ffdec appears to inline closure bodies
  elsewhere or the export layout differs).

**Open question:** what spelling/context makes ASC emit the plain
`Namespace` kind for these style-class references? (the `ns_kind` mystery,
see `docs/CODE_MATCH.md`)

## Source-shape recovery (2026-10-13)

Verified with the current `amxmlc` and the strict linear AVM2 decoder:

* `member = value` emits `initproperty`; `this.member = value` emits
  `setproperty`. The counted `tools/member_cleanup.json` worklist limits this
  recovery to measured writes, including compound assignments.
* `if((a >= 6))` emits `greaterequals; iffalse`, while `if(a >= 6)` emits
  `ifnge`. Extra parentheses recover the two insurance tests in
  `frm_Special_action` without changing comparison semantics.
* Restoring outer `else if`/`else` chains recovers unreachable jumps following
  returns in `commodity_sound` and the two travel event handlers. Inspect raw
  canonical dumps, not only JPEXS P-code: its unreachable jump labels can differ
  from the raw targets.
* Moving hoisted local declarations to their original lexical positions
  restores register allocation. For the six skin arrays, use a declaration
  followed by a separate assignment; an inline initialized declaration causes
  additional entry-time null writes for registers 7 and 8.
* Recovered resource sources already retain original key order, but SDK locale
  generation overrides them unless disabled. Force-link all ten bundles with
  `-locale=` and restore their typed return local to match the original bodies.

These repairs initially raised strict matching to 99.27% without modifying the
measurer. The subsequent script-initializer fix below raises it to **99.59%**.

## Script initializers: `findpropstrict` vs `getscopeobject 0` (2026-10-13, resolved)

Before the scheduling fix, 39 script-initializer differences shared the *same single
instruction*: the object pushed as the `initproperty` target in a script
initializer that installs one public class.

```
getlocal0
pushscope
getscopeobject 0          <- or: findpropstrict Multiname("X",[PackageNamespace("")])
getlex Object
pushscope
getlex Object
newclass X
popscope
initproperty X
returnvoid
```

Both forms store the class object into the script's global, so they are
semantically identical. `measure_code.py` counts them as different bodies
(2,171 original bytes across 39 scripts).

### Original vs pre-fix rebuild

* Original uses `findpropstrict` (FP) for **39** of the 156 scoped scripts:
  `PlayerType`, `OpponentType`, all 34 `*_dataClass` embed carriers, and
  `CustomPreloader`, `LoadScreen`, `LoadScreen_LoadScreenGraphic`.
* The pre-fix rebuild emits FP for 74; **37 scripts flip GS->FP** (GameStrings,
  GradientBarSkin, GradientTrackSkin, the 22 SWF-embed host classes and the
  12 `_class_embed_css` SWF hosts) and **2 flip FP->GS**
  (`PlayerType`, `OpponentType`). The other 117 agree.

### The mechanism (ASC + flex2 sources)

1. `FlowAnalyzer.evaluate(ClassDefinitionNode)` (FA pass 1 = `As3Compiler.analyze1`)
   creates the class's slot on the unit's global via `Builder.ExplicitVar` +
   `ImplicitCall`/`ImplicitConstruct` and synthesizes `node.init`, the
   assignment `X = class`.
2. FA pass 2 (`As3Compiler.analyze2`) evaluates `node.init`, binding its
   LHS reference. CodeGenerator later chooses the emitted form in
   `CodeGenerator.evaluate(Context, SetExpressionNode)` from the cached
   binding: scope 0 + unresolved slot index -> `getscopeobject 0`;
   scope 0 + resolved slot -> `var_index = slot.getVarIndex()` (forced to -1
   unless the slot's `declaredBy` is the unit's own global); a non-method slot
   with `var_index < 0` -> `findpropstrict X`; a const slot with
   `var_index >= 0` -> `getscopeobject 0`.
3. **`FlowAnalyzer.inheritSlots`** (invoked from `As3Compiler.analyze2` for
   inheritance/namespace dependencies and from `analyze3` for
   type/namespace/expression dependencies) copies a dependency unit's global
   slots into the current unit's global and — for `VariableSlot`s — calls
   `slot.setVarIndex(-1)` **on the shared `Slot` object, mutating the
   dependency's own class slot**.

Therefore:

> **A class's script initializer is FP iff some other unit inherited its
> class slot (`setVarIndex(-1)`) before the class's own unit generated.**

Verified two ways:

* **Probes** (`P1/P2`, `R2/D1/D2`, `F1/A,B,C,D`, `G1/E1`): any unit that
  another unit references compiles its install with `findpropstrict`; a unit
  referenced by nobody (command-line root or `-includes`) uses
  `getscopeobject 0`. The reference kind (extends, type annotation, member
  initializer, in-method expression) did not change the outcome in isolation.
* **Historical full instrumented rebuild** (temporary shadow classes, not
  retained in this directory): for every
  sampled class, `first VHACK seq < GEN seq` exactly predicts FP:

  | class | GEN@ | first HACK@ | form |
  |---|---:|---:|---|
  | PlayerType | 367 | 384 | GS (orig wants FP) |
  | OpponentType | 360 | 383 | GS (orig wants FP) |
  | GameStrings | 349 | 276 | FP (orig wants GS) |
  | GameType | 412 | 469 | GS (agrees) |
  | Gazillionaire | 822 | none | GS (agrees) |
  | GradientBarSkin | 504 | 475 | FP (orig wants GS) |
  | GradientTrackSkin | 505 | 473 | FP (orig wants GS) |
  | CustomPreloader | 86 | 20 | FP (agrees) |
  | LoadScreen | 87 | 39 | FP (agrees) |
  | Gazillionaire_PlanetBass1Class | 846 | 470 | FP (orig wants GS) |
  | Gazillionaire_PlanetBass1Class_dataClass | 880 | 524 | FP (agrees) |
  | Gazillionaire__embed_mxml_TILO1_SWF_1460587624 | 828 | 474 | FP (orig wants GS) |
  | Gazillionaire_BoyIconClass | 363 | 472 | GS (agrees) |
  | Gazillionaire__embed_mxml_i_bank_png_875063226 | 378 | 471 | GS (agrees) |

  699/699 script bodies and every FP/GS form were identical to the reference
  rebuild, so the instrumentation does not perturb codegen.

### Why the pre-fix rebuild disagreed with the original

The form is decided by **unit processing order**: when the referrer's
`inheritSlots` runs relative to the referenced unit's `generate`.

* The 37 GS->FP flips are all hacked by one early burst (~seq 470-525), which
  is the force-included `Gazillionaire` unit's analyze2/3 inheriting the
  embed-host/skin class globals (`barSkin = GradientBarSkin`,
  `internal var PlanetBass1Class:Class = Gazillionaire_PlanetBass1Class`,
  ...). In the rebuild those hosts generate *after* that burst (seq 828-880);
  the original must have generated them *before* the referrer inherited them.
* `PlayerType`/`OpponentType` are hacked by `GameType`'s analyze3 (seq
  383/384) but generate earlier (seq 360/367). In the original SWF the script
  order shows `GameType` generated *before* `PlayerType`/`OpponentType`
  (`init` method indices 12426 < 12436/12454), i.e. the opposite order.

### Investigation plan (before resolution)

1. Model the scheduler: `flex2.compiler.CompilerAPI` (develop sources,
   `modules/compiler/src/java/flex2/compiler/CompilerAPI.java`) runs a
   phase-locked loop over a growing source list (`while (start < end)` at
   ~line 258 with `end = sources.size()` refreshes at ~282/312/342/383, and
   the `nextSource(...)` loop at ~line 433). Read this to derive how
   discovered dependencies interleave with the discovering unit's
   analyze2/analyze3 and other units' generate. (Fetched copy:
   `/tmp/opencode/CompilerAPI.java` if still present; otherwise re-fetch from
   GitHub `apache/flex-sdk` develop.)
2. Re-run the instrumented rebuild and attribute each `VHACK` to the
   inheriting unit (add the unit path to the `[VHACK]` print via the
   `SymbolTable`/current source, or correlate bursts with the surrounding
   `[REFBIND]` frames).
3. Experiment with build-invocation levers that change order without changing
   code shapes, measuring after each attempt
   (`python3 tools/measure_code.py` plus the `MeasureCode 'script:'` dump
   used for this work):
   * drop `Gazillionaire` from `-includes` (it should still be linked via
     `-frames.frame=Gazillionaire,Gazillionaire`; verify) so its analysis
     happens later;
   * reorder the `-includes` list;
   * check whether the original's entry point was the MXML root
     (`Gazillionaire.mxml` -> generated SystemManager), which would discover
     the document class differently than force-including it.
4. Constraint: any fix must keep the other 117 scoped scripts and all
   699 script bodies unchanged; the 39 target scripts each only need their
   third instruction flipped.

### Resolution: source scheduling via `-includes`

`CompilerAPI.batch2`'s `nextSource` scans from `sources.size() - 1` down to
zero, prioritizing `generate` over `analyze2`. `tools/build.sh` now explicitly
includes the 37 GS-target dependencies late in the list and `GameType` early.
This restores GS for those dependencies and FP for `PlayerType`/`OpponentType`.

The gradient skins require an additional scheduling prerequisite: explicitly
include their SDK inheritance/interface closure. Without it, their SDK
dependencies delay generation until after `Gazillionaire.analyze3`, regardless
of the tested application include orders. `CustomComboBoxSkin` is also explicit
to preserve its previously matching initializer. These SDK definitions were
already linked; no method identities were added or removed.

Verified with the unchanged strict measurer: exactly 39 of the 700 inventoried
script bodies change, all 39 now match, and all previously matching scoped bodies
remain matching. Application matching is **663,756 / 666,482 bytes (99.59%)**,
with **9,113 / 9,120 bodies** matching; generated application classes are 100%.
The scratch probe files and instrumentation directory are not retained here.
The planet selector repair subsequently raised strict matching to **99.66%**,
leaving six namespace-kind cases. See [the current report](../../docs/CODE_MATCH.md).
