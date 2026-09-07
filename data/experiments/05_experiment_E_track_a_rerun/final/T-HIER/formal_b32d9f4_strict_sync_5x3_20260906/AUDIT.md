# Experiment E T-HIER rerun audit

The rerun completed all 15 planned conditions: five models and seeds 642, 643, and 644.

| Gate | Result |
|---|---:|
| Compile | 15/15 |
| Execution | 15/15 |
| Training valid | 15/15 |
| Strict | 15/15 |
| Fixer calls | 0 |

The maximum observed differences were loss `3.337860107421875e-06`, gradient norm `4.76837158203125e-07`, and parameter-update relative L2 `0.002856338693775114`. They are below the unchanged limits 0.02, 0.05, and 0.03.

The previous normalized T-HIER `0/15` result was invalidated by the strict verifier's RNG-position bug. Its candidate path built a disposable execution model and then a second training model without reseeding, while the native reference path reset the seed and built only its training model. The old final comparison therefore used different random initializations. The paired diagnostic path already showed 14 near-identical trajectories, which led to this audit and fix.

This rerun did not simply reclassify the old rows. It made 15 fresh Translator calls with the same five-task, three-seed protocol. All initial candidates passed, including Tiny Causal LM seed 642, so no Fixer call was needed. The old `cross_entropy` failure remains a valid result for the old generated candidate but is not a persistent failure in this rerun.
