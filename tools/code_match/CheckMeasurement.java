import java.io.*;
import java.nio.file.*;
import java.util.*;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.abc.types.*;
import com.jpexs.decompiler.flash.abc.avm2.instructions.*;
import static com.jpexs.decompiler.flash.abc.avm2.AVM2Code.*;

/** Negative controls using real game bytecode; never writes a SWF. */
public class CheckMeasurement {
    static void changed(String before, String after, String label) {
        if(before.equals(after)) throw new AssertionError("Missed mutation: "+label);
        System.out.println("PASS: "+label);
    }
    public static void main(String[] args) throws Exception {
        MeasureCode.includedClasses=new HashSet<>(Files.readAllLines(Path.of(args[1])));
        SWF swf=new SWF(new FileInputStream(args[0]),false);
        Set<String> tested=new HashSet<>();
        for(var tag:swf.getAbcList()) {
            MeasureCode c=new MeasureCode(tag.getABC());
            for(MethodBody b:c.abc.bodies) {
                if(!c.scopes.get(b.method_info).equals("game")) continue;
                String before=c.canonical(b);
                for(AVM2Instruction ins:c.codes.get(b.method_info).code) {
                    if(ins.definition.instructionName.equals("initproperty") && tested.add("opcode")) {
                        var def=ins.definition;
                        ins.definition=instructionSet[0x61]; // setproperty
                        changed(before,c.canonical(b),"initproperty versus setproperty");
                        ins.definition=def;
                    }
                    if(ins.definition.instructionName.equals("pushstring") && tested.add("constant")) {
                        int index=ins.operands[0]; String old=c.abc.constants.getString(index);
                        c.abc.constants.setString(index,old+"__measurement_control");
                        changed(before,c.canonical(b),"constant-pool value changed with identical instruction bytes");
                        c.abc.constants.setString(index,old);
                    }
                    if(ins.operands==null) continue;
                    for(int j=0;j<ins.definition.operands.length;j++) {
                        if(ins.definition.operands[j]!=DAT_MULTINAME_INDEX) continue;
                        Multiname m=c.abc.constants.getMultiname(ins.operands[j]);
                        if(!m.hasOwnNamespaceSet()) continue;
                        int[] namespaces=c.abc.constants.getNamespaceSet(m.namespace_set_index).namespaces;
                        if(namespaces.length<2 || !tested.add("namespace_set")) continue;
                        int old=namespaces[0]; namespaces[0]=namespaces[1]; namespaces[1]=old;
                        changed(before,c.canonical(b),"namespace-set ordering preserved");
                        namespaces[1]=namespaces[0]; namespaces[0]=old;
                    }
                }
                if(!before.equals(c.canonical(b))) throw new AssertionError("Mutation not restored");
                if(b.exceptions.length>0 && tested.add("exceptions")) {
                    ABCException e=b.exceptions[0]; int old=e.target;
                    e.target=old==0?c.rawCodes.get(b.method_info).length:0;
                    changed(before,c.canonical(b),"exception target changed"); e.target=old;
                }
            }
        }
        if(tested.size()!=4) throw new AssertionError("Missing controls: "+tested);
    }
}
