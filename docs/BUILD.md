# Build

Requires Bash, Python 3, JDK 17+, JPEXS ffdec 24.1.1, curl and unzip.
`fetch_sdk.sh` installs Flex 4.16.1 and AIR 32 into `sdk/`.

```bash
tools/export_all.sh "/path/to/Gazillionaire"
tools/fetch_sdk.sh
tools/build.sh
tools/run.sh air               # Wine + AIR 32
# tools/run.sh                # optional Ruffle launcher
```

Game data defaults to ignored `.local-data/`. Set `GAZ_DATA_DIR` to an absolute
path to use another location; keep it consistent across commands.

| Path | Contents |
|---|---|
| `$GAZ_DATA_DIR/src/` | Local raw decompiler output |
| `$GAZ_DATA_DIR/original/` | Original SWFs and AIR metadata |
| `$GAZ_DATA_DIR/assets/` | Embedded images/data and runtime audio/images |
| `app/src/` | Generated buildable source |
| `build/` | Rebuilt SWF, recovered artwork and runtime directory |
| `sdk/` | Downloaded toolchain |

Edit `tools/prepare_build.py`, `tools/clean_source.py` and their manifests.
Preparation checks the baseline source hash, repairs decompiler artifacts and
recovers synthetic artwork embeds without copying executable code. The build
uses SDK framework classes and places the preloader/application on two frames.
The original has two ABC blocks; the rebuild has one. The ten recovered
`en_US$*_properties` classes are force-linked with SDK locale generation disabled,
preserving original resource literal order and return-local code generation.
The `-includes` order in `tools/build.sh` also preserves script-initializer
code generation: `GameType` analyzes before `PlayerType`/`OpponentType` generate,
while 37 other dependencies generate before their referrers inherit their slots.
The gradient skins' SDK inheritance/interface prerequisites are explicitly
included so they generate early enough. Keep this ordering when changing the
build invocation, and recheck with `python3 tools/measure_code.py`.

Launch through `run.sh`: it assembles the relative asset directories the game
loads. AIR is preferred for fidelity; Ruffle's AIR support is incomplete.

[Verification](VERIFICATION.md) · [Architecture](ARCHITECTURE.md)
