# Instructions given to the second coder

The exposed-table sample of Appendix C.7 was coded by two instances of the Claude language model (Anthropic; Claude Opus 5.5, October 2026), each run as an agent with file access. These are the instructions each one received, verbatim apart from local paths shortened to <repos> and <scratch>. It worked from blind_sheet.csv, which omits the first coder's labels.

---

You are the second, independent coder in an inter-rater reliability check for a research paper. Another coder has already classified the same 50 DMN decision tables. You must NOT see their labels. Classify every table yourself from the model files alone.

## Blinding rules (strict)
- Read ONLY these:
  - the sheet `<scratch>/blind2/blind_sheet.csv`;
  - the `.dmn` model files it names in `model_file`;
  - other files in the same repository folder as a model file (for example a README, a sibling test or an enum definition), when you need context.
- Do NOT open, list or search anything under `<repos>/LATC`. That covers its results/corpus folder (EXPOSED_SAMPLE.md, exposed_sample.csv, exposed_sample_classes.json), its README, the paper and its code.
- Do NOT open anything else in the scratchpad folder, and do NOT open any `.claude` folder or transcript.
- Do not search the web.
- If you accidentally see a prior label, say so in your report.

## Sheet columns
- **sample_no**
- **source** — the GitHub repo
- **kind** — the folder kind
  - `product-test` = an engine's or editor's test resources
  - `example` = example or tutorial repo
  - `analyser` = verifier/validator/linter fixtures
  - `other` = anything else
- **model_file** — absolute path
- **table** — the decision table's name, or its id, in that file
- **table_index** — 0-based index among the file's decision tables
- **hit_policy**
- **n_rules**
- **exposed_inputs** — the string input column(s) with no declared domain (no inputValues, no itemDefinition allowedValues)
- **mentioned_literals** — the string literals the rules use in that column
- **dash_in_column** — whether some rule has "-" in that column

Each table is "exposed": it is single-hit, it has such an undeclared string input, and no rule has "-" in that input and in every other input. So a value the rules never mention might reach no rule.

## Judgement 1: class (exactly one)
- **OPEN**: the input's real-world domain is open, or larger than the values the rules mention, so an unmentioned value can plausibly arrive and reach no rule.
- **CLOSED**: the domain is closed by convention or by the upstream model. Examples: yes/no; a fixed status set the rules enumerate; an enumeration fixed elsewhere. The risk is low.
- **PARTIAL**: the table is deliberately partial or a test fixture. Examples: a no-match test, a tutorial fragment, an analyser fixture with intentional gaps, or an engine or syntax test whose rules are not meant as a complete business rule.
- **UNCLEAR**: cannot be judged from the model.

Decide PARTIAL first if the table is a test fixture or deliberately incomplete. When the choice between OPEN and CLOSED is doubtful, choose UNCLEAR.

## Judgement 2: domain (exactly one)
This is what the exposed column's domain would be if the table were used for real. It applies to every table, fixtures included.
- **OPEN**: open, or larger than the mentioned values, in the real world.
- **CLOSED**: closed by convention or by the upstream model.
- **COVERED**: the column's entries already match every value through not(...) or other FEEL expressions, so nothing is missed.
- **SYNTHETIC**: placeholder values with no real-world domain, as in syntax and engine tests (for example "a", "b", "foo").
- **UNCLEAR**: cannot be judged from the model.

## Method
For each table:
1. Open the model file and find the table (by name/id, or by table_index).
2. Read:
   - the column label;
   - the input entries, including any not(...) or FEEL expressions beyond the listed literals;
   - the outputs;
   - names, descriptions and documentation nearby;
   - the file path (test folder names matter).
3. Decide both judgements.
4. Write a one-sentence justification.

## Output
Write `<scratch>/blind2/rater2.json`. It is a JSON object keyed by sample_no as a string:
`{"1": {"class": "...", "domain": "...", "justification": "..."}, ...}`
It must hold all 50 entries.

## Final report
Reply with:
- the counts per class and per domain;
- any table you could not open;
- any breach of blinding.

Keep it short.
