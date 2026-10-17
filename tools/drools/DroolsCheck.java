import java.io.File;
import java.util.List;
import org.kie.dmn.api.core.DMNMessage;
import org.kie.dmn.validation.DMNValidator;
import org.kie.dmn.validation.DMNValidator.Validation;
import org.kie.dmn.validation.DMNValidatorFactory;

/** Runs the Drools DMN validator, including decision-table gap and overlap analysis, on each file. */
public class DroolsCheck {
    public static void main(String[] args) {
        DMNValidator v = DMNValidatorFactory.newValidator();
        for (String path : args) {
            List<DMNMessage> msgs = v.validate(new File(path), Validation.VALIDATE_SCHEMA,
                    Validation.VALIDATE_MODEL, Validation.ANALYZE_DECISION_TABLE);
            System.out.println("=== " + path + " : " + msgs.size() + " messages");
            for (DMNMessage m : msgs) {
                System.out.println(m.getLevel() + "\t" + m.getMessageType() + "\t" + m.getText().replace('\n', ' '));
            }
        }
        v.dispose();
    }
}
