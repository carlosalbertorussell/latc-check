# External check with Drools (KIE) DMN

`DroolsCheck.java` runs the Drools DMN validator, with schema and model validation and
decision-table analysis (gaps, overlaps, masked rules, subsumption, contraction), on each
DMN file it is given, and prints one line per message. `latc_check/drools_compare.py`
exports tables, runs this driver and compares its findings with the exhaustive oracle.

Reference setup (Drools 7.74.1.Final, which runs on Java 8):

* JDK: Eclipse Temurin 8 (jdk8u504-b01), from adoptium.net
* Maven 3.9.9, used only to download the libraries

```bash
mvn -B dependency:copy-dependencies -DoutputDirectory=lib
```

```bash
javac -cp "lib/*" -d out DroolsCheck.java
```

```bash
java -cp "out;lib/*" DroolsCheck ../../results/dmn/pension_t0.dmn
```

On Linux or macOS the classpath separator is `:` instead of `;`. The libraries (39 jars,
about 17 MB) and the JDK are not part of this repository.

Results: `results/drools/` (`pension.txt`, `random_tables.json`, `car.json`).
