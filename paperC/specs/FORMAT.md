# Paper C shared sample format

Protocol: `paperC/PROTOCOL.md`, registered at commit `ee7c527080e665df70b906f0cbf091098e84ad5f`.

Several sessions produce samples in this format in parallel. Do not change this text;
if something is unworkable, add a dated note under "Deviations" at the end.

## Folder

One sample per folder `paperC/specs/<ID>/`, containing exactly the files below.

### `spec.json`

```json
{
  "id": "<ID>",
  "title": "...",
  "source": {"repository": "...", "commit": "...", "entry_point": "...", "files": ["..."]},
  "attributes": [
    {
      "name": "...",
      "kind": "enum" | "bool" | "interval",
      "values": ["label", "..."],
      "representative": {"label": "concrete value passed to the encoding"},
      "source": "article or file:line"
    }
  ],
  "output": {"name": "...", "values": ["label", "..."], "source": "..."},
  "exclusions": [
    {"id": "...", "description": "...", "predicate": "<Python boolean expression>", "source": "..."}
  ],
  "fixed_inputs": {"<input>": {"value": "...", "why": "..."}},
  "notes": "..."
}
```

* `values`: labels as strings, in declared order.
* `representative`: for intervals and any label that is not itself a value, the concrete
  value passed to the encoding.
* `predicate`: a Python boolean expression over attribute names, comparing to labels as
  strings.

### `ground_truth.csv`

* Header: attribute names in spec order, then `output`.
* One row per element of the Cartesian product of declared values, in odometer order
  (last attribute varies fastest).
* `output` is a label from `output.values`, or `EXCLUDED` (an exclusion predicate
  holds), or `REJECTED` (the encoding raised an error or precondition failure; each such
  case explained in CONVERSION.md).
* UTF-8, LF line endings, no index column.

### `official_examples.csv`

* Header: `case_id`, attribute names, `output`.
* One row per official test case that maps onto the table; unmappable cases listed with
  reasons in CONVERSION.md.

### `oracle.py`

* `evaluate(row: dict[str, str]) -> str`.
* `python oracle.py --enumerate` writes `ground_truth.csv`.
* `python oracle.py --check-official` re-runs every official test through the original
  encoding and through the oracle and prints pass counts.

### Other files

* `ENVIRONMENT.md`: Python and package versions, install commands.
* `CONVERSION.md`: every interpretive choice with its source.
* `SHA256SUMS`: sha256 of every file in the folder.

## Size limit

The declared space must have at most 200,000 combinations; otherwise split into
sub-tables with IDs like `FR-AF-1`.

## Deviations

(none yet)
