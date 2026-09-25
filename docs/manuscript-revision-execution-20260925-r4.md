# 2026-09-25 r4执行记录

本轮按[用户批准的r4](manuscript-revision-plan-20260925-r4.md)及S60–S68后续要求修改。开始提交e615868，分支codex/iclr-2027-template。

## 实际改动

- 最新`figures/架构图0925终版.svg`原样转为`hierarchical_feedback_architecture.pdf`，裁到绘图边界，Times New Roman嵌入，无栅格图片。SVG SHA-256为279239cf2500da9813f1cbbc2974821722d9f23068c599d3bfb6f6b67dafa506。用户图源仍有Java目标示意；图注保留实验方向说明。图注依后续要求缩为5行。
- 算法与表格在caption后采用局部small；三算法逻辑保持，算法1/2保留55%左环绕，算法3全宽。3.4采用r4五段。
- cref输出Fig./Table/Algorithm，附录节与子节显式设置appendix别名，PDF不再出现Section A.1/A.6。
- Figure 3保留左右两面板、完整三种方法总成本、全部29输入、两负值及排序。右轴单位millions，数字1–29横排且Task仅一次。Figure 1按用户新要求只有左侧一个Acc.，下方只列100%/100%/88%。两图用量三位小数。
- 检测图移至A.6，补阴影、均值/个体首次越阈区别、两项loss工程实践来源和四阈值敏感性。均由保存轨迹分析，无实验重跑。
- 原Table 2/3最终合为Table 2(a,b)：10项初译修复与6项JAX研究分开报告。按S68移除(b)内部两行分组标题，将方法类型移到总表注；两个子表标题、表头、四行及底线对齐。消融表变为Table 3，所有引用同步。
- 当前全文成本单位统一为millions；所有预算和单次限制仍为准确整数，百分比保留原值。

## 同内容版面比较

算法A(55%)、B(50%)、C(全栏)分别在隔离目录编译。三种布局正文终点相同，采用计划的半栏优先规则；B把Algorithm 2的While条件拆行，最终保留A。

JAX表对比保持相同caption和数值。固定48%环绕为表格预留完整高度，第8页正文结束约615.5pt；全栏允许第8页正文延至732.3pt。全栏正文结束位置比固定半栏提前58.6pt，约5行。自由浮动半栏能进一步提前，但漂到消融节旁，未采用。随后按用户要求合并Table 2/3，正文终点再提前约6行。最终(b)分组文字移表注，使左右基线一致。详细坐标见[试排数据](review-evidence/manuscript-20260925-r4/table-comparison.json)。

## 核验与边界

15项figure测试、10项unified-result测试、3项manuscript-comparison测试通过。独立检查55个成本显示单元格与r4一致；四阈值检出数、首次越阈范围、均值越阈和正常对照误报逐格复算。数据及实验资料共947个文件字节保持，原始整数账本未改。三个algorithmic除引用命令外相同。

主稿latexmk成功，24页，正文结束第10页；无overfull、未定义引用及LaTeX/package警告。PDF逐页渲染，关键表格文字边界、基线、图形标签间距和页坐标已检验。图像工具本轮未返回可见图像，未声称完成全稿目视巡检；用户在过程中检查并反馈了图1、图2及第8/9页和表2。

最新SVG90%宽度下最小Candidate字约3.56pt，少数字为4.27pt；用户明确保留图内内容，本轮保持原样。九页压缩按最新用户要求暂停，没有执行r4删句清单或继续缩小架构图。范围外的摘要语法、引言80%概括、Fig.1 caption语法继续登记，未擅自改动。

官方包重新下载，SHA-256为0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e，四个样式文件逐字一致。官方例文仍写“do not change font sizes”；本轮9pt按r4授权采用，字号和页数均留作投稿前处理项，不宣称投稿合规。

## 新引用来源

TroubleShooter的[loss_compare文档](https://github.com/mindspore-ai/toolkits/blob/e0486eee96a1893b5e1b59f02669804a2d796030/troubleshooter/docs/api/widget/loss_compare.md)返回曲线、误差图、CSV及统计，没有自动判错阈值。所固定提交日期2025-09-15，引用年份由计划的2024修正为2025。

[MindSpore Transformers r1.7.0指南](https://www.mindspore.cn/mindformers/docs/en/r1.7.0/advanced_development/precision_optimization.html)实际标题是Large Model Precision Optimization Guide，依次讨论step-1 loss、local norm和更新权重。页面和对应源码未列出版日期，因此引用使用n.d.，版本及访问日期保留，未沿用未证实的2025。

## 交付与对照

主稿为`conference_101719.pdf`；固定2026-09-21基线未改，HTML逐词对照与LaTeX差异PDF随最终稿刷新。反馈登记本轮覆盖全部140个有效ID，详见[逐项记录](review-evidence/manuscript-20260925-r4/feedback-review.csv)和[验证JSON](review-evidence/manuscript-20260925-r4/verification.json)。用户PPT与其他个人文件保持，未push或同步Overleaf。
