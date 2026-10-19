# Instructions given to the first coder

The exposed-table sample of Appendix C.7 was coded by two instances of the Claude language model (Anthropic; Claude Opus 5.5, October 2026), each run as an agent with file access. These are the instructions each one received, verbatim apart from local paths shortened to <repos> and <scratch>. The first coder had also helped build the corpus measures and was not blind to the study's hypothesis.

---

Task: estimate how many "exposed" DMN decision tables are real risks, by classifying a random sample. Work in <repos>\LATC. Do NOT commit, do NOT push, do NOT download anything. Report progress about every 15 minutes (a short status line in your output). Use `uv run --no-project python -I` for Python; use the Bash tool (PowerShell is in constrained mode; do not bypass it).

Background: latc_check/dmn_corpus.py (runner run_dmn_corpus.py) parses .dmn files cloned under <repos>\corpus and <repos>\dmn-tck. results/corpus/SUMMARY.md reports 369 of 1,559 tables with string inputs (23.7%, counted over distinct files) as exposed: single-hit hit policy, a string input with no declared domain whose entries mention at least one string literal, and no catch-all rule (no rule with '-' in every input). Read dmn_corpus.py (functions exposed_column, _extra_measures etc.) and results/corpus/results.json / inputs.csv.

Do this:
1. Add a small deterministic sampler (e.g. a function in a new module latc_check/dmn_exposed_sample.py, with a unit test) that lists the exposed tables (by distinct table content, so near-duplicate copies are not over-sampled) and draws a simple random sample of 50 with seed 20210101. Save the list with source, path, table name, the exposed input column(s), the literals the rules mention, the hit policy, the number of rules, and whether some rule has '-' in that column.
2. Classify each sampled table by reading the model file (the column label, the literals, the output, nearby documentation/names), into exactly one class:
   - OPEN: the input's real-world domain is open or larger than the values the rules mention (e.g. country, product code, free-text category), so an unmentioned value can plausibly arrive and reach no rule;
   - CLOSED: the domain is closed by convention or by the upstream model (e.g. yes/no, a fixed status set that the rules enumerate completely, an enumeration fixed elsewhere in the model), so the risk is low;
   - PARTIAL: the table is deliberately partial or a test fixture (e.g. a test of no-match behaviour, a tutorial fragment, an analyser fixture with intentional gaps);
   - UNCLEAR: cannot be judged from the model.
   Give a one-line justification for each. Be conservative: when in doubt between OPEN and CLOSED, record UNCLEAR. Additionally record whether some rule with '-' in that column would still catch an unmentioned value in some states (partial protection).
3. Write results/corpus/exposed_sample.csv (one row per sampled table with class and justification) and results/corpus/EXPOSED_SAMPLE.md with the counts per class, Wilson 95% intervals for the OPEN share, and the implied estimate of tables at real risk among the 369 (state clearly that it is an estimate from one rater). Add a short README.md entry.
4. Run the full test suite (`uv run --no-project python -m unittest discover -s tests`) and report the count.

Final report: counts per class with intervals, 5 representative examples per class (path, column, literals, justification), and caveats (single rater, sampling unit). Do not use the constructions "not X but Y" or "X, not Y" in any prose you write.
