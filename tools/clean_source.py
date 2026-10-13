"""Recover measured source shapes from the decompiler output.

The fixed manifest comes from the baseline dbl_init classification and
string-validated method alignment. Never strip initializers globally: some
original methods intentionally contain an explicit default initializer.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

MANIFEST = Path(__file__).with_name("initializer_cleanup.json")
EVENT_ALIASES = (
    "process_load_online_game", "process_autosave", "doQuit_process_save",
    "doQuit_process_gamemake", "frm_NewOrContinue_process_check_online_saves",
    "frm_NewOrContinue_process_check_online_solo_saves",
    "frm_ChooseShip3_process_online_save_selection",
    "frm_File_process_check_online_saves", "frm_File_process_check_online_solo_saves",
    "frm_File_process_online_autosave_then_new", "frm_File_process_init_save",
    "frm_File_process_online_save", "frm_LoadGame_process_check_online_saves",
    "frm_LoadGame_process_online_resign", "frm_LoadGame_process_online_autosave",
)
DECL = re.compile(
    r"^(\s*var [\w$]+:([\w.$]+)) = (null|0|NaN|false);(\s*)$"
)


def clean_initializers(text: str) -> tuple[str, int]:
    plan = json.loads(MANIFEST.read_text())
    if hashlib.sha256(text.encode()).hexdigest() != plan["source_sha256"]:
        raise ValueError("initializer cleanup baseline changed; regenerate and validate alignment")
    lines = text.splitlines(keepends=True)
    count = 0
    for method in plan["methods"]:
        start = method["line"] - 1
        name = method["name"]
        if (name.startswith(("get_", "set_"))
                and "function " + name + "(" not in lines[start]):
            name = name[:3] + " " + name[4:]
        if "function " + name + "(" not in lines[start]:
            raise ValueError("initializer cleanup function mismatch: %s" % method)
        if lines[start + 1].strip() != "{":
            raise ValueError("unexpected function body: %s" % method)
        changed = 0
        # Only the leading local declarations belong to this method's init
        # sequence. Stop before executable statements or nested functions.
        for i in range(start + 2, len(lines)):
            if not lines[i].strip().startswith("var "):
                break
            match = DECL.fullmatch(lines[i])
            if not match:
                continue
            typ, value = match.group(2, 3)
            expected = {"int": "0", "uint": "0", "Number": "NaN",
                        "Boolean": "false"}.get(typ, "null")
            if value == expected:
                lines[i] = match.group(1) + ";" + match.group(4)
                changed += 1
        if not changed:
            raise ValueError("no initializers removed: %s" % method)
        count += changed
    return "".join(lines), count


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("cleanup expected one occurrence of %r" % old)
    return text.replace(old, new, 1)


def recover_parameter(text: str, declaration: str, alias: str, typ: str) -> str:
    """Recover a parameter name, keeping its uses and closure captures intact."""
    start = text.index(declaration)
    end = text.find("\n      }", start) + len("\n      }")
    body = text[start:end]
    if len(re.findall(r"\bparam1\b", body)) != 2:
        raise ValueError("unexpected parameter uses in " + declaration)
    body = replace_once(body, "param1:" + typ, alias + ":" + typ)
    body = replace_once(body, "         var %s:%s = param1;\n" % (alias, typ), "")
    return text[:start] + body + text[end:]


def clean_codegen(filename: str, text: str) -> str:
    if filename == "Gazillionaire.as":
        text = replace_once(text, "   use namespace mx_internal;\n", "")
        text = recover_parameter(text, "override public function set moduleFactory(",
                                 "factory", "IFlexModuleFactory")
        for name in EVENT_ALIASES:
            text = recover_parameter(text, "internal function " + name + "(", "event", "Event")
        text = clean_residuals(text)
    elif filename in ("_Gazillionaire_FlexInit.as", "_Gazillionaire_Styles.as"):
        text = recover_parameter(text, "public static function init(", "fbs", "IFlexModuleFactory")
    if filename == "_Gazillionaire_FlexInit.as":
        text = replace_once(text,
                            "         var styleNames:Array;\n         var i:int;\n         var styleManager:IStyleManager2 = null;",
                            "         var styleManager:IStyleManager2;\n         var styleNames:Array;\n         var i:int;")
        text = replace_once(text, "         var styleNames:Array;\n", "")
        text = replace_once(text, "         var i:int;\n", "")
        text = replace_once(text, "         styleNames = [", "         var styleNames:Array = [")
        text = replace_once(text, "         i = 0;", "         var i:int = 0;")
    if filename == "_Gazillionaire_Styles.as":
        text = replace_once(text,
                            "         var style:CSSStyleDeclaration = null;\n         var effects:Array = null;\n         var mergedStyle:CSSStyleDeclaration = null;\n",
                            "")
        text = replace_once(text, "         var selector:CSSSelector = null;\n",
                            "         var selector:CSSSelector = null;\n         var style:CSSStyleDeclaration;\n         var effects:Array;\n         var mergedStyle:CSSStyleDeclaration;\n")
    if filename == "_Gazillionaire_mx_managers_SystemManager.as":
        text = text.replace("Boolean(_loc2_.content)", "_loc2_.content")
        for name in ("_allowDomainParameters", "_allowInsecureDomainParameters"):
            text = replace_once(text, "Boolean(this." + name + ")", "this." + name)
    if filename == "CustomComboBoxSkin.as":
        text = replace_once(text, "Number(Math.max(_loc5_ - 1,0))", "Math.max(_loc5_ - 1,0)")
        text = replace_once(text, '               _loc3_ = getStyle("disabledIconColor");',
                            '               _loc3_ = getStyle("disabledIconColor");\n               break;')
    return text


def clean_residuals(text: str) -> str:
    """Apply measured source-shape repairs only to the residual worklist."""
    plan = json.loads(Path(__file__).with_name("codegen_cleanup.json").read_text())
    for method in plan:
        name = method["name"]
        declaration = re.search(r"^      .*function " + re.escape(name) + r"\(", text, re.M)
        if not declaration:
            raise ValueError("missing residual method: " + name)
        start = declaration.start()
        end = text.index("\n      }", start) + len("\n      }")
        body = text[start:end]
        if method.get("strip_defaults"):
            lines = body.splitlines(keepends=True)
            for i in range(2, len(lines)):
                if not lines[i].strip().startswith("var "):
                    break
                match = DECL.fullmatch(lines[i])
                if match:
                    typ, value = match.group(2, 3)
                    expected = {"int": "0", "uint": "0", "Number": "NaN",
                                "Boolean": "false"}.get(typ, "null")
                    if value == expected:
                        lines[i] = match.group(1) + ";" + match.group(4)
            body = "".join(lines)
        if method.get("assignment_casts"):
            # The target variable's declared type supplies the conversion.
            body = re.sub(r"^(\s*(?:_loc\d+_|param\d+) = )(?:Number|int|uint)\((.*)\);$",
                          r"\1\2;", body, flags=re.M)
        if method.get("postfix"):
            body = re.sub(r"^(\s*)(\+\+|--)(this\.[\w.]+(?:\[[^\n]+\])?);$",
                          r"\1\3\2;", body, flags=re.M)
        for old, new in method.get("replace", []):
            body = replace_once(body, old, new)
        for old, new in method.get("replace_all", {}).items():
            if old not in body:
                raise ValueError("missing repeated repair: " + old)
            body = body.replace(old, new)
        for old, new in method.get("empty_branches", []):
            pattern = r"^( +)(else )?if\(" + re.escape(old) + r"\)\n\1\{"
            body, changed = re.subn(pattern, lambda m: m[1] + (m[2] or "") + "if(" + new + ")\n" + m[1] + "{\n" + m[1] + "}\n" + m[1] + "else\n" + m[1] + "{", body, flags=re.M)
            if not changed:
                raise ValueError("empty-branch mismatch: " + name)
        text = text[:start] + body + text[end:]
    return text
