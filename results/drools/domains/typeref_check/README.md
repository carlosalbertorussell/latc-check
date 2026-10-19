# Drools 7.74.1: inputValues without an inputExpression typeRef

`pension_Age_60-64_V1_with_typeRef.dmn` is the V1 pension case of `run_drools_domains.py`
(full inputValues on every input, Age 60-64 absent from the rules).
`pension_Age_60-64_V1_without_typeRef.dmn` is the same file with `typeRef="string"` removed
from every `inputExpression`; the inputValues are unchanged.

Run with the Drools 7.74.1 driver of `tools/drools/` (Java 8):

    java -cp "out;lib/*" DroolsCheck <file>

Outputs: `with_typeRef.txt` reports the gaps (8 gap messages); `without_typeRef.txt` reports
"Skipped Decision Table Analysis of table ... because: null" and no gaps. So inputValues alone
are not enough: without an inputExpression typeRef, Drools 7.74.1 skips the table's analysis.
`results/corpus/SUMMARY.md` ("Sensitivity of the measures") counts the corpus inputs affected.
