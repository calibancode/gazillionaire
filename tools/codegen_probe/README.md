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