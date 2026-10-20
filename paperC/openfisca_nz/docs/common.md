## Conventions shared by the NZ samples

These points apply to NZ-SLP, NZ-AS and NZ-SPS (and the supplementary NZ-AS-1964). They are repeated in every CONVERSION.md so that each folder can be read on its own.

C1. **Ground truth is the encoding as written.** The output of every row is what OpenFisca Aotearoa at commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` computes for the entry variable in the fixed week. Where the encoding departs from the Act (missing provisions, coding defects), the table follows the encoding, and the departure is listed below under "Encoding behaviour reproduced".

C2. **Level of the attributes.** Every input variable read on the path from the entry variable is traced. Leaf inputs (variables without a formula) become attributes. Some variables that have their own formula are defined terms of the Act, encoded once and shared by many benefits, and the rule's official tests always set them directly as inputs: `social_security__residential_requirement` (SSA 2018 s 16), `social_security__in_a_relationship`, `social_security__dependent_children`, `social_security__financially_independent`, `basic_grant__entitled` (Student Allowances Regulations 1998), `immigration__resident`. These are attributes (or fixed inputs) at the level of the defined term, and their own sub-trees are listed in the sample's notes. Expanding them would have made almost every official case unmappable, because the tests override the defined term without setting its leaves. The variables of the benefit's own provisions (for example `sole_parent_support__requirement`, `accommodation_supplement__accommodation_costs`) are always expanded down to their leaves.

C3. **Numeric inputs** are split at every threshold that the formulas on the path compare against, with the parameter file, its value in the fixed week and its legislative reference cited in `spec.json`. Each band's representative is a value inside the band, usually its lower bound or the boundary value itself (for `<=` comparisons), so that the boundary semantics are exercised.

C4. **One OpenFisca simulation per row.** `social_security__dependent_children` (`interpretation/child.py:52-54`) uses Python's built-in `sum` over the whole population array. In a simulation that holds several households, every household's count becomes the total over all households. The official tests each simulate one household, so the encoding behaves as intended there. `oracle.py --enumerate` therefore simulates each row on its own (in parallel worker processes). `oracle.py --batch-diagnostic` shows the effect: with 300 random rows simulated together, NZ-SPS gets 1 row wrong; the other tables are unaffected because they set the count directly as an input.

C5. **REJECTED rows.** None. No simulation raised an error.

C6. **Official cases: how a case maps onto a row.** `oracle.py --check-official` loads every YAML file of the rule's test folder and, for each case:
1. builds the simulation exactly as `openfisca test` does (`SimulationBuilder.set_default_period(period)`, then `build_from_dict`), and computes the entry variable for every period the case asserts. This is the "directly through OpenFisca" count;
2. skips the case (UNMAPPABLE) when it asserts nothing about the entry variable;
3. otherwise, for each person whose value is asserted: rejects the person when the asserted week lies outside the range where the table's formula version and parameter values apply, or when the household differs from the table's fixed household (role, members);
4. reads every attribute from the case's own simulation, at the period the formula reads it (so an attribute that the case leaves unset takes the encoding's default, or the value its formula computes from what the case does set);
5. builds the oracle row, rejects it if it is EXCLUDED, and simulates it with tracing on. Every variable that the case sets as an input and that the oracle's computation reads (traced) is compared with the oracle's value at each traced period. A difference makes the person UNMAPPABLE (the case overrides an intermediate result with a value the attributes do not produce). Equal values are noted. Inputs that the oracle never reads are listed as such; their effect, if any, reaches the row through the attribute values of step 4;
6. compares the oracle output with the expected value.
Step 5 is what makes the mapping safe: a mapped person's output is determined by the row alone.

C7. **Verification.** `paperC/openfisca_nz/crosscheck.py` restates each formula in plain Python (no OpenFisca) and compares it with every row of `ground_truth.csv`, including the EXCLUDED labels. All rows agree for all four tables.
