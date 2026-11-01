# On hold: not merged into main

**Decision (2026-10-31, the author):** this branch, with the replication kit and the human-coding packet in `replication/`, stays unmerged while Paper A ("Where Declared Domains Are Lost: LATC, DMN Analysers and Public DMN Models", submitted to *Data & Knowledge Engineering* on 2026-10-25, DATAK-D-26-02269) is under review.

**Why:** Paper A cites `latc_check` 0.1.0 (Zenodo DOI 10.5281/zenodo.23646699, commit 0330360) and links this repository. Its Section 10.3 says independent replication remains open. A `replication/` folder on `main`, dated after submission and not described in the paper, could confuse reviewers about what was submitted.

**When the review ends:** merge this branch if the review asks for replication or more reproducibility material, or once a decision is in; describe the kit in the revision if there is one, and archive it as a new Zenodo version (for example 0.1.1). The cited version 0.1.0 stays as it is.
