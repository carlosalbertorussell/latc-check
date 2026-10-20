# Human coding of the exposed-table sample (for the study author)

This folder prepares a blinded human check of the 50-table sample of `results/corpus/EXPOSED_SAMPLE.md`
(Section 9.3, Appendix C.7), which so far was coded by two instances of a language model.

| File | Who gets it | Purpose |
|---|---|---|
| `HUMAN_CODER_GUIDE.md` | each coder | the task, the two judgements with the same classes and definitions the LLM coders had, one worked example per class, how to open the files |
| `coding_sheet_blank.csv` | each coder | the 50 tables (same rows and columns as `results/corpus/coding/blind_sheet.csv`), with a link to each model file at its recorded commit and four empty columns: `class`, `domain`, `justification`, `minutes` |
| `make_sheet.py` | nobody | rebuilds the blank sheet from `blind_sheet.csv` and `results/corpus/sources.json` |
| `score_human.py` | nobody | computes the agreement once the sheets are back |

## Sending the packet

1. Send each coder **only** `HUMAN_CODER_GUIDE.md` and `coding_sheet_blank.csv`, separately. Do
   not send the repository, a link to it, the paper, or this README: the repository holds the LLM
   labels (`results/corpus/exposed_sample_classes.json`, `exposed_sample_rater2.json`,
   `exposed_sample.csv`, `EXPOSED_SAMPLE.md`).
2. Coders need a web browser and a spreadsheet program. All 50 `model_url` links were checked to
   resolve (HTTP 200) on 2026-10-20. Coders who prefer local files can get the models with
   `python -I fetch_corpus.py` (network and git needed); `local_path` is relative to the folder
   it fills.
3. Expected effort: about 30 minutes of reading, then 3 to 6 minutes per table, so 3 to 5 hours
   per coder.
4. Ask each coder to return the filled sheet and a short note (hard cases, files they could not
   open, whether they saw anyone else's labels).

## Scoring

```bash
python -I replication/human_coding/score_human.py coding_sheet_AB.csv coding_sheet_CD.csv --out replication/human_coding/agreement.md
```

The script checks that each sheet has all 50 rows, unchanged `table` / `table_index` columns and
valid labels (case is ignored), and stops with a list of problems otherwise. It then prints, for
Human 1 / Human 2, each human against LLM 1 (first coder, `exposed_sample_classes.json`) and
LLM 2 (blinded second coder, `exposed_sample_rater2.json`), and LLM 1 / LLM 2:

* class counts and the OPEN share with its Wilson 95% interval, per coder;
* observed agreement, Cohen's kappa, PABAK and Gwet's AC1 on `class`, on `domain`, and on OPEN
  against the rest for each, using `cohen_kappa`, `pabak`, `gwet_ac1` and `wilson` from
  `latc_check/dmn_exposed_sample.py`;
* the class confusion tables of the two humans, and of each human against LLM 1;
* the minutes each coder recorded.

The LLM 1 / LLM 2 rows reproduce the agreement table of `results/corpus/EXPOSED_SAMPLE.md`
(class: 84%, kappa 0.42; OPEN against the rest: 98%, kappa 0.66), which checks that the labels
are matched correctly. With one sheet only, the script reports that coder against the two LLM
coders.

The script was tested with two synthetic sheets made from the LLM labels (one exact, one with
20% of the classes changed); no real human data is in this folder.
