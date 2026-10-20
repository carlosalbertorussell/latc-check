# Coding guide: 50 DMN decision tables

Thank you for helping. You will read 50 decision tables taken from public DMN models on GitHub
and give each one two short labels and a one-sentence reason. Another person codes the same
tables on their own. Please work alone, and do not discuss the tables or your labels with
anyone until both of you have sent in your sheets.

**Time.** Plan on about 30 minutes to read this guide and look at the worked examples, then
3 to 6 minutes per table: roughly 3 to 5 hours in total. Most tables are small. Two or three
sittings work better than one long one. Please record the minutes you spend on each table in
the `minutes` column (a rough figure is fine).

**What you receive.** This guide and `coding_sheet_blank.csv`. Rename the sheet to
`coding_sheet_<your initials>.csv` before you start, fill in the last four columns, and send it
back. Open it in a spreadsheet program (Excel, LibreOffice Calc, Google Sheets) and save it as
CSV (UTF-8).

## 1. What a DMN decision table is

DMN (Decision Model and Notation) is a standard for writing business rules. A decision table has
input columns, output columns and one row per rule. Each cell in an input column is a test on
that input:

| Input entry | Meaning |
|---|---|
| `"Gold"` | the input equals the string Gold |
| `"Gold","Silver"` | the input is Gold or Silver |
| `not("Gold")` | the input is anything except Gold |
| `-` (or an empty cell) | any value matches |
| `< 18`, `[18..65]` | numeric tests |

A rule fires when every input entry in its row matches. The **hit policy** (a letter or word
at the top left of the table) says what happens when several rules match. All 50 tables have a
single-result hit policy (UNIQUE, ANY, FIRST or PRIORITY): the table returns the result of one
rule. If no rule matches, the table returns no result.

A model may **declare** the allowed values of an input, either directly on the column
(`inputValues`) or through a data type defined elsewhere in the model (`itemDefinition` with
`allowedValues`). In every table of this sample, at least one string input column has no such
declaration. That column is named in `exposed_inputs`. In addition, no rule has `-` in that
column together with `-` in every other column, so no rule is a "catch everything" rule. A
string value that no rule mentions in that column may therefore match no rule at all.

Your task is to judge whether that matters for each table.

## 2. The sheet

| Column | Meaning |
|---|---|
| `sample_no` | row number, 1 to 50 |
| `source` | the GitHub (or GitLab) repository |
| `kind` | the folder kind: `product-test` = an engine's or editor's test resources; `example` = an example or tutorial repository; `analyser` = fixtures of a verifier, validator or linter; `other` = anything else |
| `model_url` | the model file at the exact commit used, in your browser |
| `local_path` | the same file in a local download (see section 3), if you prefer local files |
| `table` | the decision table's name, or its id, in that file |
| `table_index` | its position among the file's decision tables, counting from 0 |
| `hit_policy`, `n_rules` | hit policy and number of rules |
| `exposed_inputs` | the undeclared string input column(s); several are separated by ` \| ` |
| `mentioned_literals` | the string values the rules use in that column, in the same order |
| `dash_in_column` | whether some rule has `-` in that column |
| **`class`** | your first judgement (section 4) |
| **`domain`** | your second judgement (section 5) |
| **`justification`** | one sentence: why |
| **`minutes`** | about how long the table took |

Some files appear in more than one row, sometimes with the same table. Judge every row as it
comes; you may reuse your reasoning.

## 3. How to open a model file

**In the browser (simplest).** Click the `model_url` link. GitHub shows the file as XML. Use
the browser's find function (Ctrl+F or Cmd+F):

1. Search for `decisionTable`. The tables appear in file order; `table_index` 0 is the first.
   The table sits inside a `<decision name="..." id="...">` element whose name or id matches
   the `table` column.
2. The `<input label="...">` elements are the columns, in order. Each `<rule>` has one
   `<inputEntry>` per input column (the `<text>` inside is the cell) and one `<outputEntry>`
   per output column.
3. `&quot;` in the XML is a double quote, so `&quot;Gold&quot;` is `"Gold"`.

**As a picture (optional).** Click "Raw" on GitHub, save the file, and drag it onto
<https://demo.bpmn.io/dmn/new>. That viewer shows the table as a grid. It may refuse some files
(newer DMN versions, engine-specific test files); then read the XML.

**Locally (optional).** If the person who sent you this guide gave you a download of the
models (made with `python -I fetch_corpus.py` in the study's repository), `local_path` is the
file's path inside that download folder.

**Context you may use.** The model file, and other files in the same repository: the README,
the folder names in the path (for example `src/test/resources`), the test class that loads
the model, or another model that defines a data type. **Do not** search the web for the table
or the study, and do not look at any other material about this sample. If you happen to see
anyone else's labels for these tables, note it in your justification for that row.

## 4. Judgement 1: `class` (exactly one)

| Class | Meaning |
|---|---|
| `OPEN` | the input's real-world domain is open, or larger than the values the rules mention, so an unmentioned value can plausibly arrive and reach no rule |
| `CLOSED` | the domain is closed by convention or by the upstream model, so the risk is low. Examples: yes/no; a fixed status set the rules enumerate; an enumeration fixed elsewhere (for example the outputs of an earlier decision that feeds this input) |
| `PARTIAL` | the table is deliberately partial or a test fixture. Examples: a no-match test, a tutorial fragment, an analyser fixture with intentional gaps, or an engine or syntax test whose rules are not meant as a complete business rule |
| `UNCLEAR` | cannot be judged from the model |

**Order of decisions.**

1. Decide `PARTIAL` first, if the table is a test fixture or deliberately incomplete.
2. Otherwise choose between `OPEN` and `CLOSED`.
3. When the choice between `OPEN` and `CLOSED` is doubtful, choose `UNCLEAR`.

If several columns are listed in `exposed_inputs`, consider all of them and give one label for
the table.

### Worked examples (made up for this guide; none is in the sample)

**OPEN.** An example shop repository, `src/main/resources/shipping.dmn`, table "Shipping fee",
hit policy UNIQUE. Input `Product category` (string, no declared values). Rules: `"Books"` →
2.00, `"Toys"` → 4.50, `"Games"` → 4.50. Nothing in the model restricts the category, and
shops add categories all the time. An order for "Garden" would match no rule.
`class = OPEN`, `domain = OPEN`. Justification: "Product categories form an open set and
nothing upstream limits them to the three the rules mention."

**CLOSED.** A tutorial repository, table "Report deadline", hit policy UNIQUE. Input `Quarter`
(string, no declared values). Rules: `"Q1"`, `"Q2"`, `"Q3"`, `"Q4"`, each with a date. The
input can only take these four values by convention, and all four have a rule.
`class = CLOSED`, `domain = CLOSED`. Justification: "Calendar quarters are a fixed set of four
and every one has a rule."

**PARTIAL.** An engine repository, `src/test/resources/org/example/engine/no-match.dmn`, table
"decision", hit policy FIRST, one rule: input `code` = `"X1"` → "found". The test class next to
it checks that the engine returns an empty result for the input "X2". The table is built to
miss values. `class = PARTIAL`, `domain = SYNTHETIC`. Justification: "Engine test of the
no-match case; X1 is a placeholder value."

**UNCLEAR.** An example repository with no README, table "Routing", hit policy UNIQUE. Input
`Region code` with rules `"R1"`, `"R2"`, `"R7"`. Nothing in the model or the repository says
whether R1 to R7 is a fixed list or whether R3 to R6 exist and were left out on purpose.
`class = UNCLEAR`, `domain = UNCLEAR`. Justification: "No way to tell from the repository
whether the region codes form a fixed set."

## 5. Judgement 2: `domain` (exactly one)

This is what the exposed column's domain would be **if the table were used for real**. Give it
for every table, test fixtures included.

| Domain | Meaning |
|---|---|
| `OPEN` | open, or larger than the mentioned values, in the real world |
| `CLOSED` | closed by convention or by the upstream model |
| `COVERED` | the column's entries already match every value through `not(...)` or other expressions, so nothing is missed |
| `SYNTHETIC` | placeholder values with no real-world domain, as in syntax and engine tests (for example "a", "b", "foo") |
| `UNCLEAR` | cannot be judged from the model |

The four worked examples above show `OPEN`, `CLOSED`, `SYNTHETIC` and `UNCLEAR`. An example of
`COVERED`: input `Currency` with two rules, `"EUR"` → "domestic" and `not("EUR")` → "foreign".
The `mentioned_literals` column lists only EUR, but the second rule matches every other value,
so no value is missed. (Check the actual entries in the file: `mentioned_literals` lists only
plain string values and does not show `not(...)` or other expressions.)

## 6. Writing the labels

* Use the words exactly as above, in capitals: `OPEN`, `CLOSED`, `PARTIAL`, `UNCLEAR` for
  `class`; `OPEN`, `CLOSED`, `COVERED`, `SYNTHETIC`, `UNCLEAR` for `domain`.
* One sentence of justification is enough. Say what the decisive evidence was (the folder, a
  test, the column's meaning, a `not(...)` entry).
* If you cannot open a file, write `UNCLEAR` in both columns and "could not open" as the
  justification.
* Do not change the other columns or the order of the rows.

When you are done, send the sheet back together with a short note: anything that was hard to
decide, any file you could not open, and whether you saw any other coder's labels.
