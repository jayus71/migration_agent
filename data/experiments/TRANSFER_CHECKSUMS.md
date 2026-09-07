# 远端传输校验

Experiment I 由于包含 1,738 个文件，先在远端压缩，再传回本地并解压。

- 远端源目录：`/media/main/whj/projects/torch4ms/ascend-torch4ms-exp-i-core-8c5c635/experiments/experiment_request_20260820/09_experiment_I_real_translation/runs_real_core_v3`
- 压缩包：`09_experiment_I_real_translation/experiment_I_runs_real_core_v3_8c5c635.tar.gz`
- SHA-256：`76cd770fee5cf01e65445d0451e426eb85d755212d042b5574a206d8e9e467b2`
- 压缩包字节数：`7,685,103`
- 远端源文件数：`1,738`
- 本地解压文件数：`1,738`
- 远端源总字节数：`36,539,596`
- 本地解压总字节数：`36,539,596`
- 校验结果：通过。

Experiment E T-HIER 修复后结果也使用压缩传输：

- 压缩包：`05_experiment_E_track_a_rerun/T-HIER/experiment_E_T_HIER_b32d9f4_20260906.tar.gz`
- SHA-256：`e977e644d214e80f9e98b592c61d55105331a437bdf18911e30e542aa7543a0b`
- 压缩包字节数：`172,221`
- 远端/本地结果文件数：`157 / 157`
- 远端/本地结果总字节数：`928,714 / 928,714`
- 校验结果：通过。
