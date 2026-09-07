# 2026-09-06 实验结果本地汇总

本目录汇总 `EXPERIMENT_REQUEST_20260820.md` 中 Experiment A–K 的现有正式结果与诊断材料。它是独立的本地归档目录，不属于任何实验 Git 分支；本次没有执行分支合并，也没有改写源结果。

## 结论先行

- 多数实验的既定运行矩阵已经产生结果，但不能概括为“所有实验都通过”。
- A、B、C、G、H、I、J、K 已有可审计的正式结果包。
- D 的 24 个受控条件全部通过，但真实规模 10-step gate 失败，因此 6 个正式真实规模条件未启动，Experiment D 整体不支持论文正向主张。
- E 的 T-HIER 严格复验初始化 bug 已修复并完成全新 5×3 重跑：15/15 编译、执行、训练和严格通过。最新 T-MSA 仍是严格 0/15，T-X2MS 仍没有形成 15 个可测结果，因此 E 仍不能写成完整五方法比较完成。
- F 按实验要求并入 D 的真实规模验证和 I 的真实翻译验证，不单独运行。
- H 的 27 个条件齐全，但 DeepSeek 温度跨种子不完全一致，GLM 还是 5.2/5.3 混合版本；跨模型结论必须保守。
- I 的真实翻译矩阵已完成，但 R-HIER 对 5 个自然失败任务修复成功 0 个，Direct 修复成功 2 个；这暴露了算子 lowering、切片递归和梯度/参数更新桥接问题。
- J 的本地正式视图已采用第三轮 HIER/reverse 数据，两者均为 48/50；三轮结果分别为 44/49、47/46、48/48，reverse 优势没有稳定复现，因此“执行→数值→梯度/更新”与反序之间尚无确定优劣。

## 导航

- [EXPERIMENT_STATUS_REPORT.md](EXPERIMENT_STATUS_REPORT.md)：A–K 完成度、关键数字和论文口径。
- [CURRENT_ISSUES.md](CURRENT_ISSUES.md)：当前主要技术问题与证据边界。
- [SOURCE_INDEX.md](SOURCE_INDEX.md)：各结果包的来源 worktree、提交和远端位置。
- [PACKAGE_INVENTORY.csv](PACKAGE_INVENTORY.csv)：复制前后文件数和总字节数对账。
- [CONSOLIDATION_MANIFEST.json](CONSOLIDATION_MANIFEST.json)：机器可读汇总清单。
- [TRANSFER_CHECKSUMS.md](TRANSFER_CHECKSUMS.md)：Experiment I 压缩传输校验。

## 数据保全

Experiment D 原有 4,800 行历史数据没有被覆盖。汇总目录保留的是新的 commit-scoped 结果包及其原始日志、逐步指标、参数审计和 buffer 审计。所有复制均为只读源到新目录的复制。

归档包含 10,053 个源结果文件，共 551,836,313 字节；另保留 Experiment I 和 E T-HIER 的传输压缩包及本地汇总文档。完整目录当前约 535.92 MiB。

- [VALIDATION.md](VALIDATION.md)：关键行数、目录存在性和路径卫生检查。
