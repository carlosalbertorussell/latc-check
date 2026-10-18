#!/bin/sh
# Builds the tiny runner (pom in scripts/dmncheck-runner, source RunDmnCheck.java) in the tools folder
# and runs dmn-check 1.1.6 on the original DMN 1.4 inputs, the DMN 1.3-namespace copies and the controls.
T=C:/Users/crussell/Downloads/repos/tools/dmncheck-dmnlint/dmncheck-runner
R=C:/Users/crussell/Downloads/repos/LATC/results/tools/dmncheck-dmnlint
I=C:/Users/crussell/Downloads/repos/LATC/results/tools/inputs
export JAVA_HOME=C:/Users/crussell/Downloads/repos/tools/jdk8u504-b01
export MAVEN_OPTS=-Xmx512m
mkdir -p $T/src/main/java/latc && cp $R/scripts/dmncheck-runner/pom.xml $T/ && cp $R/scripts/RunDmnCheck.java $T/src/main/java/latc/
(cd $T && /c/Users/crussell/Downloads/repos/tools/apache-maven-3.9.9/bin/mvn -q compile dependency:build-classpath -Dmdep.outputFile=cp.txt)
CP="$T/target/classes;$(cat $T/cp.txt)"
J="$JAVA_HOME/bin/java -Xmx1g -cp $CP latc.RunDmnCheck"
$J --list > $R/raw/dmncheck_validators_loaded.txt
$J $I/pension*.dmn $I/car*.dmn > $R/raw/dmncheck_original_dmn14.jsonl
$J $R/converted_dmn13/pension*.dmn $R/converted_dmn13/car*.dmn > $R/raw/dmncheck_converted_dmn13.jsonl   # ~2 min per Car file
$J $R/controls/*.dmn > $R/raw/dmncheck_controls.jsonl
