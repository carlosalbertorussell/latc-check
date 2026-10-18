import java.io.*;
import org.camunda.bpm.model.dmn.*;
import de.unikoblenz.ps.core.dmn.domain.vdmn.parser.SimpleVDmnParser;
// Diagnostic: parse a DMN file the same way DmnService does, but print the exception.
public class ParseCheck {
  public static void main(String[] a) throws Exception {
    for (String f : a) {
      try (InputStream in = new FileInputStream(f)) {
        DmnModelInstance m = Dmn.readModelFromStream(in);
        new SimpleVDmnParser().getVDmnDefinition(m);
        System.out.println("OK " + f);
      } catch (Throwable t) { System.out.println("FAIL " + f); t.printStackTrace(System.out); }
    }
  }
}
