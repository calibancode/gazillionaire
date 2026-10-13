import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.abc.ABC;
import com.jpexs.decompiler.flash.abc.types.*;
import com.jpexs.decompiler.flash.abc.types.traits.*;
import com.jpexs.decompiler.flash.abc.avm2.instructions.*;
import static com.jpexs.decompiler.flash.abc.avm2.AVM2Code.*;

/** Conservative, index-resolved AVM2 measurement. Requires JPEXS 24.1.1. */
public class MeasureCode {
    ABC abc;
    Map<Integer,String> names = new HashMap<>();
    Map<Integer,MethodBody> bodies = new HashMap<>();
    Map<Integer,com.jpexs.decompiler.flash.abc.avm2.AVM2Code> codes = new HashMap<>();
    Map<Integer,byte[]> rawCodes = new HashMap<>();
    Map<Integer,String> privateOwners = new HashMap<>();
    Map<Integer,String> scopes = new HashMap<>();
    String currentScope;
    static Set<String> includedClasses;
    static String scope(String c) {
        if(!includedClasses.contains(c)) return "framework";
        if(c.startsWith("en_US$")||c.endsWith("Skin")) return "support";
        if(Set.of("Gazillionaire","GameType","PlayerType","OpponentType","GameStrings").contains(c)) return "game";
        return "generated";
    }
    static String atom(String s) { return s == null ? "null" : s.length()+":"+s; }
    String ns(int index) {
        if(index == 0) return "*";
        Namespace n=abc.constants.getNamespace(index);
        String value=abc.constants.getString(n.name_index);
        if(n.kind == Namespace.KIND_PRIVATE)
            return "private:"+atom(privateOwners.getOrDefault(index,"unresolved:"+index+":"+value));
        return n.kind+":"+atom(value);
    }
    String mn(int index) {
        if(index == 0) return "*";
        Multiname m=abc.constants.getMultiname(index);
        StringBuilder s=new StringBuilder("mn"+m.kind+"(");
        if(m.hasOwnName()) s.append(atom(abc.constants.getString(m.name_index)));
        if(m.hasOwnNamespace()) s.append(ns(m.namespace_index));
        if(m.hasOwnNamespaceSet()) {
            s.append('[');
            for(int n:abc.constants.getNamespaceSet(m.namespace_set_index).namespaces) s.append(atom(ns(n)));
            s.append(']');
        }
        if(m.kind == Multiname.TYPENAME) {
            s.append(mn(m.qname_index));
            for(int p:m.params) s.append(atom(mn(p)));
        }
        return s.append(')').toString();
    }
    String cls(int i) { return abc.constants.getMultiname(abc.instance_info.get(i).name_index).getNameWithNamespace(new HashSet<>(),abc,abc.constants,true).toRawString(); }
    void owner(Traits traits,String owner) {
        for(Trait t:traits.traits) {
            Multiname m=abc.constants.getMultiname(t.name_index);
            if(m.hasOwnNamespace() && abc.constants.getNamespace(m.namespace_index).kind==Namespace.KIND_PRIVATE) {
                privateOwners.putIfAbsent(m.namespace_index,owner);
                // A private namespace may be shared by activation traits; retain its first structural owner.
            }
        }
    }
    void assign(int id,String name) {
        String prev=names.putIfAbsent(id,name);
        scopes.putIfAbsent(id,currentScope);
        if(prev!=null) { if(!prev.equals(name)) throw new IllegalStateException("Ambiguous method "+prev+" / "+name); return; }
        MethodBody b=bodies.get(id);
        if(b==null) return;
        owner(b.traits,name+"/activation");
        traits(b.traits,name+"/activation");
        int closure=0;
        for(AVM2Instruction ins:codes.get(b.method_info).code)
            if(ins.definition.instructionName.equals("newfunction")) assign(ins.operands[0],name+"/closure:"+(closure++));
    }
    void traits(Traits ts,String prefix) {
        for(Trait t:ts.traits) {
            String key=prefix+"/"+t.kindType+":"+mn(t.name_index);
            if(t instanceof TraitMethodGetterSetter) assign(((TraitMethodGetterSetter)t).method_info,key);
            if(t instanceof TraitFunction) assign(((TraitFunction)t).method_info,key);
        }
    }
    MeasureCode(ABC a) {
        abc=a;
        for(MethodBody b:a.bodies) {
            bodies.put(b.method_info,b);
            byte[] raw=b.getCodeBytes();
            rawCodes.put(b.method_info,raw);
            try {
                var input=new com.jpexs.decompiler.flash.abc.ABCInputStream(new com.jpexs.helpers.MemoryInputStream(raw));
                var code=new com.jpexs.decompiler.flash.abc.avm2.AVM2Code();
                int position=0;
                while(position<raw.length) {
                    int opcode=input.readU8("opcode");
                    var definition=instructionSet[opcode];
                    if(definition==null) throw new IllegalStateException("Unknown opcode "+opcode);
                    List<Integer> operands=new ArrayList<>();
                    for(int type:definition.operands) {
                        switch(type & 0xff00) {
                            case OPT_U30: operands.add(input.readU30("operand")); break;
                            case OPT_S16: operands.add((int)input.readU32("operand")); break;
                            case OPT_U8: operands.add(input.readU8("operand")); break;
                            case OPT_S8: operands.add((int)(byte)input.readU8("operand")); break;
                            case OPT_S24: operands.add(input.readS24("operand")); break;
                            case OPT_CASE_OFFSETS:
                                int count=input.readU30("caseCount"); operands.add(count);
                                for(int j=0;j<=count;j++) operands.add(input.readS24("caseTarget"));
                                break;
                            default: throw new IllegalStateException("Unknown operand type "+type);
                        }
                    }
                    var instruction=new AVM2Instruction(position,definition,operands.stream().mapToInt(Integer::intValue).toArray());
                    code.code.add(instruction);
                    position+=instruction.getBytesLength();
                }
                if(position!=raw.length) throw new IllegalStateException("Invalid instruction extent");
                codes.put(b.method_info,code);
            } catch(IOException error) { throw new IllegalStateException(error); }
        }
        for(int i=0;i<a.instance_info.size();i++) {
            owner(a.instance_info.get(i).instance_traits,cls(i));
            owner(a.class_info.get(i).static_traits,cls(i));
        }
        // Lexical namespace sets carry protected class names. Use these to anchor
        // anonymous private namespaces without erasing their distinct identities.
        for(int i=1;i<a.constants.getNamespaceSetCount();i++) {
            int[] set=a.constants.getNamespaceSet(i).namespaces;
            TreeSet<String> anchors=new TreeSet<>();
            for(int n:set) {
                Namespace ns=a.constants.getNamespace(n);
                if(ns.kind==Namespace.KIND_PROTECTED || ns.kind==Namespace.KIND_STATIC_PROTECTED)
                    anchors.add(a.constants.getString(ns.name_index));
            }
            if(!anchors.isEmpty()) for(int j=0;j<set.length;j++)
                if(a.constants.getNamespace(set[j]).kind==Namespace.KIND_PRIVATE)
                    privateOwners.putIfAbsent(set[j],"lexical:"+anchors+":"+j);
        }
        for(int i=0;i<a.instance_info.size();i++) {
            String c=cls(i);
            currentScope=scope(c);
            assign(a.instance_info.get(i).iinit_index,c+"/iinit");
            assign(a.class_info.get(i).cinit_index,c+"/cinit");
            traits(a.instance_info.get(i).instance_traits,c+"/instance");
            traits(a.class_info.get(i).static_traits,c+"/static");
        }
        for(ScriptInfo script:a.script_info) {
            currentScope="framework";
            for(Trait t:script.traits.traits) if(t instanceof TraitClass) {
                String sc=scope(cls(((TraitClass)t).class_info));
                if(!sc.equals("framework")) currentScope=sc;
            }
            List<String> keys=new ArrayList<>();
            for(Trait t:script.traits.traits) keys.add(mn(t.name_index));
            Collections.sort(keys);
            String key="script:"+String.join(";",keys);
            assign(script.init_index,key);
            traits(script.traits,key);
        }
        Map<String,Integer> privateIds=new HashMap<>();
        for(var entry:privateOwners.entrySet()) {
            Integer previous=privateIds.putIfAbsent(entry.getValue(),entry.getKey());
            if(previous!=null) throw new IllegalStateException("Private namespace identity collision: "+entry.getValue()+" "+previous+" / "+entry.getKey());
        }
        for(MethodBody b:a.bodies) if(!names.containsKey(b.method_info)) throw new IllegalStateException("Unowned body "+b.method_info);
    }
    String value(ValueKind v) {
        if(v.isNamespace()) return ns(v.value_index);
        switch(v.value_kind) {
            case 1: return atom(abc.constants.getString(v.value_index));
            case 3: return "int:"+abc.constants.getInt(v.value_index);
            case 4: return "uint:"+abc.constants.getUInt(v.value_index);
            case 6: return "double:"+Long.toHexString(Double.doubleToRawLongBits(abc.constants.getDouble(v.value_index)));
            case 0: case 10: case 11: case 12: return "literal:"+v.value_kind;
            default: throw new IllegalStateException("Unsupported value kind "+v.value_kind);
        }
    }
    String canonical(MethodBody b) {
        MethodInfo m=abc.method_info.get(b.method_info);
        StringBuilder s=new StringBuilder();
        s.append("flags:").append(m.flags).append(" return:").append(mn(m.ret_type));
        for(int p:m.param_types) s.append(" param:").append(mn(p));
        if(m.optional!=null) for(ValueKind v:m.optional) s.append(" optional:").append(atom(value(v)));
        if(m.paramNames!=null) for(int p:m.paramNames) s.append(" paramName:").append(atom(abc.constants.getString(p)));
        s.append("\nlimits:").append(b.max_stack).append(',').append(b.max_regs).append(',').append(b.init_scope_depth).append(',').append(b.max_scope_depth).append('\n');
        Map<Long,Integer> offsets=new HashMap<>();
        List<AVM2Instruction> code=codes.get(b.method_info).code;
        for(int i=0;i<code.size();i++) offsets.put(code.get(i).getAddress(),i);
        offsets.put((long)rawCodes.get(b.method_info).length,code.size());
        for(AVM2Instruction ins:code) {
            s.append(ins.definition.instructionName);
            for(int j=0;j<(ins.operands==null?0:ins.operands.length);j++) {
                int v=ins.operands[j];
                int t=ins.definition.operands[Math.min(j,ins.definition.operands.length-1)];
                String out;
                switch(t) {
                    case DAT_MULTINAME_INDEX: out=mn(v); break;
                    case DAT_STRING_INDEX: out=atom(abc.constants.getString(v)); break;
                    case DAT_NAMESPACE_INDEX: out=ns(v); break;
                    case DAT_INT_INDEX: out="int:"+abc.constants.getInt(v); break;
                    case DAT_UINT_INDEX: out="uint:"+abc.constants.getUInt(v); break;
                    case DAT_DOUBLE_INDEX: out="double:"+Long.toHexString(Double.doubleToRawLongBits(abc.constants.getDouble(v))); break;
                    case DAT_METHOD_INDEX: out=names.get(v); if(out==null) throw new IllegalStateException("Unknown method reference "+v); break;
                    case DAT_CLASS_INDEX: out=cls(v); break;
                    case DAT_OFFSET: out="target:"+target(offsets,ins.getAddress()+ins.getBytesLength()+v); break;
                    case DAT_CASE_BASEOFFSET: out="target:"+target(offsets,ins.getAddress()+v); break;
                    case OPT_CASE_OFFSETS:
                        out="cases:"+v;
                        for(int k=0;k<=v;k++) out+=","+target(offsets,ins.getAddress()+ins.operands[++j]);
                        break;
                    case DAT_DECIMAL_INDEX: case DAT_FLOAT_INDEX: case DAT_FLOAT4_INDEX:
                        throw new IllegalStateException("Unsupported pool operand "+t);
                    default:
                        if(!Set.of(OPT_U30, OPT_U8, OPT_S8, OPT_S16, DAT_ARG_COUNT,
                                DAT_DEBUG_TYPE, DAT_REGISTER_INDEX, DAT_LINENUM,
                                DAT_LOCAL_REG_INDEX, DAT_SLOT_INDEX, DAT_SCOPE_INDEX,
                                DAT_EXCEPTION_INDEX, DAT_NUMBER_CONTEXT, DAT_DISPATCH_ID).contains(t))
                            throw new IllegalStateException("Unsupported operand semantics "+t);
                        out="raw:"+v;
                }
                s.append(' ').append(atom(out));
            }
            s.append('\n');
        }
        for(ABCException e:b.exceptions) s.append("exception:").append(target(offsets,e.start)).append(',').append(target(offsets,e.end)).append(',').append(target(offsets,e.target)).append(',').append(mn(e.type_index)).append(',').append(mn(e.name_index)).append('\n');
        for(Trait t:b.traits.traits) {
            s.append("trait:").append(t.kindType).append(':').append(mn(t.name_index));
            if(t instanceof TraitSlotConst) {
                TraitSlotConst slot=(TraitSlotConst)t;
                s.append(':').append(slot.slot_id).append(':').append(mn(slot.type_index));
                if(slot.value_index!=0) s.append(':').append(value(new ValueKind(slot.value_index,slot.value_kind)));
            } else throw new IllegalStateException("Unsupported activation trait "+t.getClass());
            s.append('\n');
        }
        return s.toString();
    }
    static String target(Map<Long,Integer> offsets,long address) {
        Integer n=offsets.get(address);
        if(n==null) return "non-instruction-byte:"+address;
        return "instruction:"+n;
    }
    public static void main(String[] args) throws Exception {
        includedClasses=new HashSet<>(Files.readAllLines(Path.of(args[2])));
        SWF swf=new SWF(new FileInputStream(args[0]),false);
        Path out=Path.of(args[1]); Files.createDirectories(out);
        Set<String> all=new HashSet<>();
        Set<String> foundClasses=new HashSet<>();
        try(PrintWriter w=new PrintWriter(Files.newBufferedWriter(out.resolve("inventory.tsv")))) {
            w.println("identity\tcode_bytes\tsha256\traw_sha256\tscope");
            for(var rawTag:swf.getTags()) {
                if(!(rawTag instanceof com.jpexs.decompiler.flash.tags.ABCContainerTag)) continue;
                var tag=(com.jpexs.decompiler.flash.tags.ABCContainerTag)rawTag;
                MeasureCode context=new MeasureCode(tag.getABC());
                for(int i=0;i<context.abc.instance_info.size();i++) foundClasses.add(context.cls(i));
                for(MethodBody b:context.abc.bodies) {
                    String key=context.names.get(b.method_info);
                    if(!all.add(key)) throw new IllegalStateException("Duplicate identity "+key);
                    String text=context.canonical(b);
                    if(!context.scopes.get(b.method_info).equals("framework") && text.contains("unresolved:"))
                        throw new IllegalStateException("Unresolved private namespace in scoped method "+key);
                    ByteArrayOutputStream decoded=new ByteArrayOutputStream();
                    for(AVM2Instruction instruction:context.codes.get(b.method_info).code) decoded.write(instruction.getBytes());
                    if(!Arrays.equals(context.rawCodes.get(b.method_info),decoded.toByteArray()))
                        throw new IllegalStateException("Instruction decoder changed bytes in "+key);
                    String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                    String raw=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(context.rawCodes.get(b.method_info)));
                    w.println(key+"\t"+context.rawCodes.get(b.method_info).length+"\t"+hash+"\t"+raw+"\t"+context.scopes.get(b.method_info));
                    if(args.length>3 && key.contains(args[3])) Files.writeString(out.resolve(hash+".txt"),key+"\n"+text);
                }
            }
        }
        if(!foundClasses.containsAll(includedClasses)) {
            Set<String> missing=new TreeSet<>(includedClasses); missing.removeAll(foundClasses);
            throw new IllegalStateException("Missing scoped classes: "+missing);
        }
    }
}
