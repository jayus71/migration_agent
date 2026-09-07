# Experiment D parameter sweep

The literal document criterion is reported alongside the corrected paired-drift criterion. For `fault=none`, a clean candidate follows the learning reference, so requiring reference movement above 0.05 while requiring candidate loss peak-to-peak below 0.005 is internally inconsistent.

| Config | Min fixed-probe reference displacement | Max candidate P2P | Max fixed-probe residual P2P | Literal criterion | Corrected paired criterion |
|---|---:|---:|---:|:---:|:---:|
| 01_steps50_batch4_lr0.01 | 0.0023066998 | 0.20981503 | 7.6293945e-06 | no | no |
| 02_steps50_batch32_lr0.01 | 0.00051188469 | 0.21569633 | 7.6293945e-06 | no | no |
| 03_steps200_batch32_lr0.01 | 0.0012737513 | 0.82663774 | 7.8678131e-06 | no | no |
| 04_steps50_batch32_lr0.05 | 0.0022934675 | 1.0755453 | 7.6293945e-06 | no | no |
| 05_steps200_batch4_lr0.05 | 0.026796103 | 3.2700827 | 7.6293945e-06 | no | no |
| 06_steps400_batch4_lr0.05 | 0.062393546 | 3.3156731 | 7.6293945e-06 | no | yes |
| 07_steps200_batch4_lr0.10 | 0.050593734 | 3.3089615 | 7.390976e-06 | no | yes |

Per-model values are preserved in `parameter_sweep_summary.json`.
