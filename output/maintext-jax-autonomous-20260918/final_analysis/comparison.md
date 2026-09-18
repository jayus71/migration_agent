# 自主修复比较：完整结果

运行：`/media/main/whj/projects/torch4ms/experiments/maintext_jax_autonomous_20260918/formal_v5`

统计保留 manifest 的全部实例。健康输入与实际修复分别计数；费用包含失败条件，未知 usage 不按零补齐。

| 方法 | 完成/计划 | 接受 | 1/2/4 次内接受 | 初始失败修复 | 健康保留 | 已结束条件 token | 每次接受 token |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| autonomous_layered | 6/6 | 6 | 6/6/6 | 6/6 | 0/0 | 674,009 | 112,334.8 |
| direct_shared_tools | 6/6 | 6 | 6/6/6 | 6/6 | 0/0 | 353,311 | 58,885.2 |

逐例胜负、未完成状态、基础设施错误、未知用量和 manifest 哈希见同名 JSON。
