package latc;

import de.redsix.dmncheck.result.ValidationResult;
import de.redsix.dmncheck.util.ValidatorLoader;
import de.redsix.dmncheck.validators.core.Validator;
import org.camunda.bpm.model.dmn.Dmn;
import org.camunda.bpm.model.dmn.DmnModelInstance;
import org.camunda.bpm.model.xml.instance.ModelElementInstance;

import java.io.File;
import java.util.List;

/**
 * Runs every validator that dmn-check's ValidatorLoader discovers (the same set the
 * maven plugin / CLI run by default) on each DMN file given as argument, and prints
 * one JSON object per file (JSON Lines) to stdout.
 * Usage: java latc.RunDmnCheck --list | file1.dmn file2.dmn ...
 */
public class RunDmnCheck {

    static String esc(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int) c)); else b.append(c);
            }
        }
        return b.toString();
    }

    public static void main(String[] args) {
        List<Validator> validators = ValidatorLoader.getValidators();
        if (args.length > 0 && args[0].equals("--list")) {
            for (Validator v : validators) System.out.println(v.getClass().getName());
            return;
        }
        for (String path : args) {
            StringBuilder out = new StringBuilder();
            out.append("{\"file\":\"").append(esc(path)).append("\"");
            long t0 = System.nanoTime();
            try {
                DmnModelInstance model = Dmn.readModelFromFile(new File(path));
                long tParse = System.nanoTime();
                out.append(",\"parsed\":true,\"findings\":[");
                boolean first = true;
                for (Validator v : validators) {
                    List<ValidationResult> results;
                    try {
                        results = v.apply(model);
                    } catch (Throwable e) {
                        if (!first) out.append(",");
                        first = false;
                        out.append("{\"validator\":\"").append(v.getClass().getSimpleName())
                           .append("\",\"severity\":\"VALIDATOR_EXCEPTION\",\"message\":\"")
                           .append(esc(e.toString())).append("\",\"element\":\"\"}");
                        continue;
                    }
                    for (ValidationResult r : results) {
                        if (!first) out.append(",");
                        first = false;
                        ModelElementInstance el = r.getElement();
                        String elId = "";
                        try { elId = el == null ? "" : el.getElementType().getTypeName() + ":" + el.getAttributeValue("id"); } catch (Throwable ignored) { }
                        out.append("{\"validator\":\"").append(v.getClass().getSimpleName())
                           .append("\",\"severity\":\"").append(r.getSeverity())
                           .append("\",\"message\":\"").append(esc(r.getMessage()))
                           .append("\",\"element\":\"").append(esc(elId)).append("\"}");
                    }
                }
                long t1 = System.nanoTime();
                out.append("],\"parse_ms\":").append((tParse - t0) / 1e6)
                   .append(",\"validate_ms\":").append((t1 - tParse) / 1e6);
            } catch (Throwable e) {
                long t1 = System.nanoTime();
                out.append(",\"parsed\":false,\"error\":\"").append(esc(e.toString()));
                Throwable c = e.getCause();
                while (c != null) { out.append(" | cause: ").append(esc(c.toString())); c = c.getCause(); }
                out.append("\",\"findings\":[],\"total_ms\":").append((t1 - t0) / 1e6);
            }
            out.append("}");
            System.out.println(out);
        }
    }
}
