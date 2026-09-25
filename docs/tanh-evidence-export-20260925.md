# Tanh案例证据导出

用户要求将五项【待核】的依据放到 `D:\705file\coworker`。本次从保存的正式运行记录导出材料，没有运行实验或修改论文。证据快照对应仓库提交 `4a9b9dde9ae97dc923a34e5accaf092322563922`，图形沿用已完成的独立预览。

## 交付文件

- `D:\705file\coworker\README_先读.md`：材料入口。
- `D:\705file\coworker\tanh-case-evidence\README_五项核对.md`：逐项答案、数字定义、调用节点、代码位置和原始文件路径。
- `D:\705file\coworker\tanh-case-evidence\`：源程序、任务配置、三种方法的完整已下载日志、初始/最终candidate与支持库、验收报告、关键事件、冻结汇总、当前图及相关TeX上下文。
- `D:\705file\coworker\tanh-case-evidence.zip`：完整证据目录的压缩包，18,258,272字节。
- `D:\705file\coworker\export_verification.json`：导出计数、大小及ZIP哈希。

包含1,231个原始证据文件，整理后的清单覆盖1,362个文件，连同MANIFEST.json共1,363个文件，总计78,754,368字节。ZIP的SHA-256为 `ccf7ac40475d7cf0698359706df84fb65441b93f3852602a5bbf14020d6d8115`。

## 五项证据结论

1. AutoencoderHead（task_008/I-08）属于表2(a)五个初始验收失败程序，也是LaDiM修好的四例之一。
2. 初始支持库已有低层aten.tanh实现，缺少高层functional_tanh及其注册。回退路径复制张量执行原生PyTorch函数，切断MindSpore求导图。唯一生产修改为torch4ms/ops/mtorch.py中四行注册和映射实现。
3. 公开seed 42中，encoder.0的weight/bias梯度范数为0，loss绝对差为1.430511474609375e-6；梯度向量差及更新检查失败。更新含AdamW权重衰减，不能把零梯度写成零更新。
4. 第17/22/23调用分别执行activation测试、增加高层映射、通过公开验收；共两次外部提交，最终24调用、1,488,495 token，不含初始翻译生成。
5. SWE-agent和MatchFixAgent均用满40调用，分别1,606,058和2,340,608 token，最终生产代码与初始版本相同。两者都分析到了Tanh根因；证据支持较少调用和token内完成修复，本例没有墙钟加速优势。

具体数值、逐参数观测、baseline记录节点和JSON路径详见交付README。原有审计清单涉及筛选备选task_009；本包只导出task_008，精确原始文件清单为 `provenance/raw_source_manifest.json`。

## 已执行的核查

导出前按原始大小/SHA-256清单验证1,231个文件，逐次复制后再次比对；交付的 `verify_manifest.py` 验证全部1,362个清单条目。ZIP经过CRC、成员数量及每个成员解压后的SHA-256核对。原始文件保留内容；ZIP遇到早于1980年的历史时间戳时按格式下限存储，不改变文件字节。

从D盘导出包重新累加104次响应的usage，与三份终态预算一致；复核相同的44个初始生产代码文件、初始观测、源程序和任务配置，以及实际生产补丁、两次LaDiM提交和42/1042/2042三seed验收。导出脚本通过Python语法编译。

导出脚本是 [scripts/export_tanh_case_evidence.py](../scripts/export_tanh_case_evidence.py)，输入为仓库内已下载证据及冻结审计材料。它要求新的目标目录，并生成带标准Python完整性校验器的材料包。图形生成器保留原仓库依赖，包内的PNG/PDF/SVG可直接查看。

本轮仅提交导出脚本与证据交接记录；大体积原始材料保留在用户指定的D盘目录，既有用户文件保持。
