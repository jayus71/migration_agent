# JAX 自然迁移正式比较

12 个冻结来源各初译一次：10 个返回非空候选，8 个初始通过，2 个进入四方法修复；另外2个空正文生成失败保留在来源流量和费用中。修复接受率的分母为2。

| 方法 | 修复接受 | 修复调用 | 输入 tokens | 输出 tokens | 修复总 tokens | 两任务端到端 tokens | 全12来源端到端 tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LaDiM | 1/2 | 35 | 1,710,061 | 130,005 | 1,840,066 | 1,871,493 | 1,979,790 |
| Direct LLM | 1/2 | 28 | 642,831 | 118,104 | 760,935 | 792,362 | 900,659 |
| MatchFixAgent | 1/2 | 23 | 225,734 | 33,180 | 258,914 | 290,341 | 398,638 |
| SWE-agent | 1/2 | 66 | 982,362 | 31,170 | 1,013,532 | 1,044,959 | 1,153,256 |

两任务端到端费用将对应的共同初译各计一次；全12来源费用包括8项初始通过与2项空生成的初译。四方法共享同一实际初译批次，跨方法合计实际消耗时只计这12次初译一次。

| 任务 | 方法 | 最终接受 | 状态 | 提交数 | 修复 tokens |
| --- | --- | --- | --- | ---: | ---: |
| time_sequence | LaDiM | True | completed / invalid_final | 1 | 143,224 |
| time_sequence | Direct LLM | True | completed / completed | 2 | 142,618 |
| time_sequence | MatchFixAgent | True | completed / completed | 1 | 240,504 |
| time_sequence | SWE-agent | True | completed / submitted | 1 | 274,292 |
| residual_cnn | LaDiM | False | completed / output_budget_exhausted | 3 | 1,696,842 |
| residual_cnn | Direct LLM | False | completed / completed | 4 | 618,317 |
| residual_cnn | MatchFixAgent | False | infrastructure_error / infrastructure_error | 1 | 18,410 |
| residual_cnn | SWE-agent | False | completed / call_budget_exhausted | 1 | 739,240 |

三种子最终复验、冻结文件、逐调用原始 usage 及独立数组验收的核查结果见 formal_report.json 与 independent_audit.json。源轨迹复验从公共 source.py 和冻结输入重新执行，没有模型API调用。
