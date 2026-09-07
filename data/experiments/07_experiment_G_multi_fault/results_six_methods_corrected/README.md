# Experiment G: corrected six-method results

All six baselines contain the same 20 multi-fault instances, use seed 101, temperature 0.1, a four-attempt budget, and the same three-stage verifier.

The MatchFixAgent row uses declared PyTorch source fragments paired with faulty Torch4MS fragments by the currently observed public failing symbol. No clean Torch4MS target implementation is supplied.

| Method | Strict | Repair@1 | Repair@2 | Repair@4 | Calls | Prompt | Completion | Total tokens | Wall time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R-EXEC | 1/20 (5.0%) | 0.0% | 0.0% | 5.0% | 79 | 134,081 | 198,145 | 332,226 | 1756.6 |
| R-FLAT | 1/20 (5.0%) | 5.0% | 5.0% | 5.0% | 77 | 142,726 | 950,990 | 1,093,716 | 8512.8 |
| R-HIER | 15/20 (75.0%) | 15.0% | 70.0% | 75.0% | 48 | 722,652 | 370,398 | 1,093,050 | 3575.4 |
| Direct LLM Repair | 15/20 (75.0%) | 5.0% | 50.0% | 75.0% | 55 | 72,227 | 593,982 | 666,209 | 5186.4 |
| SWE-agent | 3/20 (15.0%) | 15.0% | 15.0% | 15.0% | 67 | 2,365,310 | 118,785 | 2,484,095 | 11924.9 |
| MatchFixAgent (PyTorch source) | 16/20 (80.0%) | 0.0% | 35.0% | 80.0% | 59 | 552,214 | 1,261,074 | 1,813,288 | 7160.3 |

## Failed instances

- R-EXEC: MF-01, MF-02, MF-03, MF-04, MF-05, MF-06, MF-07, MF-09, MF-10, MF-11, MF-12, MF-13, MF-14, MF-15, MF-16, MF-17, MF-18, MF-19, MF-20
- R-FLAT: MF-01, MF-02, MF-03, MF-04, MF-05, MF-06, MF-07, MF-09, MF-10, MF-11, MF-12, MF-13, MF-14, MF-15, MF-16, MF-17, MF-18, MF-19, MF-20
- R-HIER: MF-02, MF-06, MF-11, MF-16, MF-18
- Direct LLM Repair: MF-01, MF-02, MF-12, MF-15, MF-18
- SWE-agent: MF-01, MF-02, MF-03, MF-04, MF-05, MF-07, MF-10, MF-11, MF-12, MF-13, MF-14, MF-15, MF-16, MF-17, MF-18, MF-19, MF-20
- MatchFixAgent (PyTorch source): MF-05, MF-10, MF-17, MF-20

## Provenance

The baseline directories were preserved from their formal remote runs. `provenance.json` records the source commit and result directory for each method. R-FLAT combines its provider-valid MF-01--04 head with the provider-valid MF-05--20 resume fragment.
