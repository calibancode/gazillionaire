import java.io.*;
import java.util.*;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.abc.ABC;
import com.jpexs.decompiler.flash.abc.types.*;
import com.jpexs.decompiler.flash.abc.types.traits.*;
import com.jpexs.decompiler.flash.abc.avm2.AVM2Code;
import com.jpexs.decompiler.flash.abc.avm2.instructions.AVM2Instruction;
import com.jpexs.decompiler.flash.tags.*;

/**
 * Restores the plain-namespace (kind-8) value references inside the methods the
 * original Flex MXML compiler generated for itself.
 *
 * The original application was built from an MXML document, so six of its
 * methods were synthesized by the MXML backend (the application and skin
 * instance initializers, Gazillionaire.initialize/moduleFactory and
 * _Gazillionaire_StylesInit).  The backend resolves package-level definitions
 * through freshly created, unregistered NamespaceValues, which XML writers
 * serialize as CONSTANT_Namespace (kind 8) multinames:
 *
 *     getlex            mn7(11:mx_internal8:7:mx.core)
 *     findpropstrict    mn7(12:CSSCondition8:9:mx.styles)
 *     constructprop     mn7(11:CSSSelector8:9:mx.styles)
 *
 * Sources compiled as plain ActionScript resolve the same definitions through
 * the package namespace (kind 22, CONSTANT_PackageNamespace), which is
 * indistinguishable at the source level and semantically equivalent at
 * runtime (AVM2 namespace lookup compares the namespace name).  This tool
 * repoints only those operand sites in the six generated methods to the
 * original kind-8 encoding, reusing an existing plain namespace when present
 * (e.g. mx.core from the bundled SDK skins) and appending one otherwise
 * (mx.styles).  Coerce sites, traits and every other method keep their
 * package-namespace entries.
 *
 * The tool is intentionally strict: it fails the build unless every expected
 * method and every expected site count is found, so a changed compiler output
 * cannot be patched silently.
 *
 * Usage: RestoreMxmlNamespaces <in.swf> <out.swf>
 */
public class RestoreMxmlNamespaces {

    /** A method synthesized by the MXML backend, with its exact site counts. */
    static final class Target {
        final String className;
        final String traitName; // null selects the instance initializer
        final int getlex, findpropstrict, constructprop;

        Target(String className, String traitName, int getlex, int findpropstrict, int constructprop) {
            this.className = className;
            this.traitName = traitName;
            this.getlex = getlex;
            this.findpropstrict = findpropstrict;
            this.constructprop = constructprop;
        }

        String label() {
            return className + "/" + (traitName == null ? "iinit" : traitName);
        }
    }

    static final List<Target> TARGETS = List.of(
            new Target("Gazillionaire", null, 2, 0, 0),
            new Target("Gazillionaire", "initialize", 2, 0, 0),
            new Target("Gazillionaire", "moduleFactory", 2, 1, 1),
            new Target("Gazillionaire", "_Gazillionaire_StylesInit", 4, 29, 29),
            new Target("GradientBarSkin", null, 2, 0, 0),
            new Target("GradientTrackSkin", null, 2, 0, 0));

    /** Plain-namespace QName sites per CSS class, for the whole application ABC. */
    static final Map<String, Integer> EXPECTED_CSS_SITES =
            Map.of("CSSCondition", 18, "CSSSelector", 20, "CSSStyleDeclaration", 22);

    static ABC abc;

    static String str(int i) {
        return abc.constants.getString(i);
    }

    static String className(int instanceIndex) {
        return abc.constants.getMultiname(abc.instance_info.get(instanceIndex).name_index)
                .getNameWithNamespace(new HashSet<>(), abc, abc.constants, true).toRawString();
    }

    /** Return an existing string index with this value, or append one. */
    static int stringId(String s) {
        for (int i = 1; i < abc.constants.getStringCount(); i++)
            if (s.equals(str(i))) return i;
        return abc.constants.addString(s);
    }

    /** Find or add a namespace with exact kind+uri, returning its index. */
    static int nsId(int kind, String uri) {
        for (int i = 1; i < abc.constants.getNamespaceCount(); i++) {
            Namespace n = abc.constants.getNamespace(i);
            if (!n.deleted && n.kind == kind && uri.equals(str(n.name_index))) return i;
        }
        return abc.constants.addNamespace(new Namespace(kind, stringId(uri)));
    }

    /** Find or add a plain QName (kind 7) with the given name and namespace. */
    static int qname(String name, int nsIdx) {
        for (int i = 1; i < abc.constants.getMultinameCount(); i++) {
            Multiname m = abc.constants.getMultiname(i);
            if (!m.deleted && m.kind == Multiname.QNAME && m.namespace_index == nsIdx
                    && name.equals(str(m.name_index)) && m.namespace_set_index == 0
                    && m.qname_index == 0 && (m.params == null || m.params.length == 0)) return i;
        }
        return abc.constants.addMultiname(Multiname.createQName(false, stringId(name), nsIdx));
    }

    /** True when the multiname is a package-namespace QName with this name+uri. */
    static boolean isPackageQName(int mnIdx, String name, String uri) {
        Multiname m = abc.constants.getMultiname(mnIdx);
        if (m.kind != Multiname.QNAME || m.namespace_index == 0 || !name.equals(str(m.name_index)))
            return false;
        Namespace n = abc.constants.getNamespace(m.namespace_index);
        return n.kind == Namespace.KIND_PACKAGE && uri.equals(str(n.name_index));
    }

    static MethodBody body(int methodInfo) {
        for (MethodBody b : abc.bodies) if (b.method_info == methodInfo) return b;
        return null;
    }

    static List<MethodBody> targetBodies() {
        Map<String, List<MethodBody>> found = new HashMap<>();
        for (String t : List.of("Gazillionaire", "GradientBarSkin", "GradientTrackSkin"))
            found.put(t, new ArrayList<>());
        for (int i = 0; i < abc.instance_info.size(); i++) {
            String name = className(i);
            List<MethodBody> list = found.get(name);
            if (list == null) continue;
            InstanceInfo inst = abc.instance_info.get(i);
            list.add(body(inst.iinit_index));
            if (name.equals("Gazillionaire")) {
                for (Trait t : inst.instance_traits.traits) {
                    if (!(t instanceof TraitMethodGetterSetter)) continue;
                    String tn = str(abc.constants.getMultiname(t.name_index).name_index);
                    if (tn.equals("initialize") || tn.equals("moduleFactory")
                            || tn.equals("_Gazillionaire_StylesInit"))
                        list.add(body(((TraitMethodGetterSetter) t).method_info));
                }
            }
        }
        return found.values().stream().flatMap(List::stream).filter(Objects::nonNull).toList();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("usage: RestoreMxmlNamespaces <in.swf> <out.swf>");
            System.exit(2);
        }
        SWF swf;
        try (FileInputStream in = new FileInputStream(args[0])) {
            swf = new SWF(in, false);
        }
        ABCContainerTag targetTag = null;
        for (var tag : swf.getTags()) {
            if (!(tag instanceof ABCContainerTag)) continue;
            abc = ((ABCContainerTag) tag).getABC();
            if (targetTag == null && !targetBodies().isEmpty()) targetTag = (ABCContainerTag) tag;
            else if (targetTag != null && !targetBodies().isEmpty())
                throw new IllegalStateException("MXML-generated methods found in more than one ABC block");
        }
        if (targetTag == null) throw new IllegalStateException("MXML-generated methods not found");

        abc = targetTag.getABC();
        List<MethodBody> bodies = targetBodies();
        if (bodies.size() != TARGETS.size())
            throw new IllegalStateException("Found " + bodies.size() + " of "
                    + TARGETS.size() + " MXML-generated methods");

        int nsMxCore8 = nsId(Namespace.KIND_NAMESPACE, "mx.core");
        int nsMxStyles8 = nsId(Namespace.KIND_NAMESPACE, "mx.styles");
        int mnMxInternal8 = qname("mx_internal", nsMxCore8);
        Map<String, Integer> cssTo = new LinkedHashMap<>();
        for (String name : List.of("CSSCondition", "CSSSelector", "CSSStyleDeclaration"))
            cssTo.put(name, qname(name, nsMxStyles8));

        Map<String, int[]> siteCounts = new LinkedHashMap<>(); // label -> {getlex, fs, cp}
        Map<String, Integer> cssSites = new LinkedHashMap<>();
        for (MethodBody b : bodies) {
            Target expected = TARGETS.stream()
                    .filter(t -> t.className.equals(ownerName(b)) && matchesTrait(t, b))
                    .findFirst().orElse(null);
            if (expected == null)
                throw new IllegalStateException("Unexpected method body " + b.method_info);
            int[] counts = countAndPatch(b, cssTo, cssSites);
            siteCounts.put(expected.label(), counts);
            int[] want = {expected.getlex, expected.findpropstrict, expected.constructprop};
            if (!Arrays.equals(counts, want))
                throw new IllegalStateException(expected.label() + ": found getlex=" + counts[0]
                        + " findpropstrict=" + counts[1] + " constructprop=" + counts[2]
                        + ", expected " + want[0] + "/" + want[1] + "/" + want[2]);
            b.setModified();
        }
        for (var e : EXPECTED_CSS_SITES.entrySet()) {
            int found = cssSites.getOrDefault(e.getKey(), 0);
            if (found != e.getValue())
                throw new IllegalStateException(e.getKey() + ": found " + found
                        + " namespace sites, expected " + e.getValue());
        }
        ((Tag) targetTag).setModified(true);

        try (FileOutputStream out = new FileOutputStream(args[1])) {
            swf.saveTo(out);
        }
        for (var e : siteCounts.entrySet()) {
            int[] c = e.getValue();
            System.out.println("  " + e.getKey() + " getlex=" + c[0]
                    + " findpropstrict=" + c[1] + " constructprop=" + c[2]);
        }
        System.out.println("  plain-namespace constants: mx.core ns=" + nsMxCore8
                + " mx.styles ns=" + nsMxStyles8 + " mx_internal mn=" + mnMxInternal8
                + " css=" + cssTo.values());
        System.out.println("restored " + TARGETS.size() + " MXML-generated methods");
    }

    static String ownerName(MethodBody body) {
        for (int i = 0; i < abc.instance_info.size(); i++) {
            InstanceInfo inst = abc.instance_info.get(i);
            if (inst.iinit_index == body.method_info) return className(i);
            for (Trait t : inst.instance_traits.traits)
                if (t instanceof TraitMethodGetterSetter
                        && ((TraitMethodGetterSetter) t).method_info == body.method_info)
                    return className(i);
        }
        return null;
    }

    static boolean matchesTrait(Target t, MethodBody b) {
        if (t.traitName == null) {
            for (int i = 0; i < abc.instance_info.size(); i++)
                if (abc.instance_info.get(i).iinit_index == b.method_info)
                    return t.className.equals(className(i));
            return false;
        }
        for (int i = 0; i < abc.instance_info.size(); i++) {
            if (!t.className.equals(className(i))) continue;
            for (Trait tr : abc.instance_info.get(i).instance_traits.traits)
                if (tr instanceof TraitMethodGetterSetter
                        && ((TraitMethodGetterSetter) tr).method_info == b.method_info
                        && t.traitName.equals(str(abc.constants.getMultiname(tr.name_index).name_index)))
                    return true;
        }
        return false;
    }

    /** Repoints the package-namespace sites in one body; returns getlex/fs/cp counts. */
    static int[] countAndPatch(MethodBody b, Map<String, Integer> cssTo, Map<String, Integer> cssSites) {
        int getlex = 0, fs = 0, cp = 0;
        List<AVM2Instruction> code = b.getCode().code;
        for (int pos = 0; pos < code.size(); pos++) {
            AVM2Instruction ins = code.get(pos);
            if (ins.operands == null || ins.operands.length == 0) continue;
            if (ins.definition.operands[0] != AVM2Code.DAT_MULTINAME_INDEX) continue;
            String op = ins.definition.instructionName;
            int to = 0;
            if (op.equals("getlex") && isPackageQName(ins.operands[0], "mx_internal", "mx.core")) {
                to = qname("mx_internal", nsId(Namespace.KIND_NAMESPACE, "mx.core"));
                getlex++;
            } else if (op.equals("findpropstrict") || op.equals("constructprop")) {
                int mn = ins.operands[0];
                for (var e : cssTo.entrySet())
                    if (isPackageQName(mn, e.getKey(), "mx.styles")) {
                        to = e.getValue();
                        cssSites.merge(e.getKey(), 1, Integer::sum);
                        if (op.equals("findpropstrict")) fs++; else cp++;
                        break;
                    }
            }
            if (to == 0) continue;
            int before = ins.getBytesLength();
            ins.operands[0] = to;
            int after = ins.getBytesLength();
            if (after != before)
                b.getCode().updateInstructionByteCount(pos, after - before, b);
        }
        return new int[] {getlex, fs, cp};
    }
}
