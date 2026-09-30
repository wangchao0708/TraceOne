# 结果与证据账本

[简体中文](results.md) | [English](results.en.md)

## 八模型 v12 实验实现：网页条件确认未过门槛

本版本增加真实同环境登记、独立校准与一次全新八类确认，全部使用 Codex 订阅
CLI 0.159.2、Low reasoning；没有使用付费 API 或重置额度。仍是一问 315 数字。
新登记每类 48 次，共 384 次，380 次成功、4 次超时；连同此前同问题的 192 条开发数据，
三折选型共 576 个调用分母。96 个候选按最差逐类匹配数优先、总数其次选择，选出
bank + raw + repetition/order 的 ridge（alpha=1，group weights=1/1/0.5）。
开发结果 543/576，Astra 59/72、6.1 Sol 58/72，属于已经看过、用于选型的数据。

用于拟合的是 571 条：4 条超时和1条旧采集器的事件异常未参与拟合，均保留在开发分母。
该异常的 `completed_item_types` 包含 `error`，早期保守计数把它计入 `tool_item_count`，
不能据此称发生了真实工具执行；原记录没有改写。新版采集器分开记录 error 和工具事件。
独立网页条件校准为 128 次、每类16次，不附加 Schema；124 条满足容错分析输入规则，
4条无法分析。支持范围用独立校准距离的逐类最大值，没有 high-margin bypass。

冻结 [v12配置](../config/release-candidate-v12.json) 和提交 `5b70968` 后才采集
[confirmation-v12](../data/public/confirmation-v12.jsonl)。120 次全部成功，未出现工具执行事件；
网页、CLI 和确认使用相同自包含问题、不附加 Schema，结果如下：

- GPT-5.5：15/15（100%）；GPT-5.6 Luna：14/15（93.3%）。
- GPT-5.6 Terra：15/15（100%）；GPT-5.6 Sol：14/15（93.3%）。
- GPT-6 Astra：9/15（60%）；GPT-6 Sol：14/15（93.3%）。
- GPT-6 Luna：10/15（66.7%）；GPT-6.1 Sol：10/15（66.7%）。
- 合计101/120（84.2%），未达到逐类≥14/15；9次拒识全部计入未匹配。
- 严格JSON/形状/范围合规61/120（50.8%）；按预先冻结的容错规则可分析114/120。

Astra的6次错误都被归为6.1 Sol；6.1 Sol有3次被归为Astra、2次拒识。
6 Luna有2次明确拒绝“独立随机”要求、2次JSON结构错误、1次支持范围拒识。
因此不能把开发94.3%或页面能显示6.1 Sol当作“整体性能变好”，也不能将这些错误当作降智证明。
本次按已冻结配置发布可复核的八类实验源码，未将失败确认冒充性能提升。
按后续明确请求，在线站点也已同步八模型实验实现；仓库保留七类历史方法。
Python/JavaScript在全部120条响应上逐字段一致，最大差约3.4×10⁻¹³。

[开发数据](../data/public/eight-optimized-development-v1.jsonl)、[开发选型](../data/eight-optimized-development-v1.json)、
[确认评测](../data/confirmation-v12-evaluation.json) 保留完整分母和隐私字段白名单。
另外包含24次已放弃的数字范围试点；它们不进入最终分类器拟合、校准或确认。
尚未对新版做真实未见模型的独立OOD验证；合成均匀数压力测试不能替代这种验证。

## GPT-6.1 Sol 扩展开发：尚未通过发布门槛

以下为最早489次开发阶段的历史记录；其中“未启动最终确认”等决策仅指当时，
后续v12的失败确认已在上节单独记录，不修改或覆盖先前结果。

2026-09-30 在 Codex CLI 0.159.2、订阅账户、Low reasoning 和隔离 wrapper 下
完成 489 次真实调用，均只有一次提问、315 个数字。489 次调用均返回成功；473 条
附加 Schema 的响应全部严格合规，16 条网页问题响应只有 5 条严格合规。后者的
格式偏差与拒识保留在分母。公开数据已去除 `thread_id`、stderr 等私人日志：
[responses](../data/public/gpt61-development-v1.jsonl)、
[manifest](../data/public/gpt61-development-v1.manifest.json)、
[development evaluation](../data/gpt61-development-v1.json)。

原问题给 6.1 Sol 采集 113 条 enrollment，再对八类各采集 15 条开发响应。
旧七类的 113 条/类 enrollment 来自历史批次，运行时与新增类不同，不能冒充
八类同期参考库。固定的 16-model bank 只作特征提取器，并未伪造第 17 个中心。
八类 ridge + support 三折开发验证中，alpha=1、raw weight=0.25 的结果如下。
随后另测“允许独立重复选择”的 315 数字问题，对八类各采集 24 条，按时间分成
三个平衡 fold。其最佳候选为 bank 特征 + 原始频率 + 重复/顺序统计的 RBF kernel
ridge（alpha=1、gamma=1）。

| 请求路由 | 原问题八类 supported，15 条/类 | 新问题最佳 closed-set 候选，24 条/类 |
| --- | ---: | ---: |
| GPT-5.5 | 15/15 | 23/24 |
| GPT-5.6 Luna | 15/15 | 23/24 |
| GPT-5.6 Terra | 15/15 | 24/24 |
| GPT-5.6 Sol | 15/15 | 23/24 |
| GPT-6 Astra | 9/15 | 19/24 |
| GPT-6 Sol | 12/15 | 21/24 |
| GPT-6 Luna | 12/15 | 23/24 |
| GPT-6.1 Sol | 8/15 | 19/24 |
| 合计 | 101/120 | 175/192 |

**这两列不是同批 paired 比较，不能从差值推导统计显著提升。** 新问题的 kernel
候选还没有重新校准 target-support，也没有独立确认；套用既有 outer guard 后
降为 171/192，Astra 为 16/24。因此 175/192 不能宣传成完整开放集方法的准确率。
新问题的提示词、特征及 51 个分类器候选均经过开发数据选择，公开这些候选是为了
呈现选择过程，而不是把最优开发结果当作盲测。另一个九种数字偏好问题的小规模
双模型 pilot 同样只用于选题，没有进入线上默认流程。

冻结的七类 v11 在本轮原问题开发响应上为 98/105；新增的 15 条 6.1 Sol 则
0/15 匹配，均被识别为 Astra。网页问题的 16 条 compatibility pilot 为 12/16
路由匹配，其中 6.1 Sol 为 0/2。这是已知的区分失败，**不是替换模型或降智的证明**。
为保留用户选择的 315 数字默认版本，当前只发布研究数据、可选八类训练接口和
网页风险提示，不启用第八类预测，也没有启动最终八类确认批次。

复现无需 API，也不会触发新采样：

```text
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python3 scripts/evaluate_gpt61_development.py
```

本轮继续尊重并感谢 ModelTrace 的优秀参考语料与可复现特征。所用的上游 16-model
参考库未登记 6.1 Sol，不能把这个覆盖差异计为对照方法“准确率为零”来制造胜利。既有同响应
一问/三问比较保留在下方；本轮未作新的八类全面优越性声明。

## 历史 315 数字 v11：第三轮确认仍未过门槛

先冻结 [release-candidate-v11.json](../config/release-candidate-v11.json)，再按
[confirmation-v10.json](../config/confirmation-v10.json) 对七类各采集 15 条新响应。
105 次调用全部成功并严格符合 9×35 Schema。默认 `supported` 与请求路由标签
一致 103/105（98.10%）：GPT-5.5、5.6 Luna/Terra/Sol、6 Astra、6 Luna
均为 15/15，GPT-6 Sol 为 13/15。预设规则要求每类至少 14/15，因此确认失败。

同响应 ModelTrace closed-set 一问为 104/105，非重叠三问为 35/35；本批不能
支持 TraceOne 全面优于优秀的上游方法。它们共用 TraceOne 的响应与 Schema，
三问只有 35 个独立决定；请求路由标签也不是实际服务权重的独立证明。
逐样本记录见 [evaluation](../data/confirmation-v10-evaluation.json) 和
[head-to-head](../data/confirmation-v10-head-to-head.json)。新 791 条适配器
以及原始数字频率特征的开发过程见
[seven-model-development-v3.json](../data/seven-model-development-v3.json)；
该开发证据不能替代独立确认。

## 七模型第二轮冻结确认：再次未过门槛

`release-candidate-v10` 于 2026-09-23 17:06:12 UTC 冻结，随后登记
`confirmation-v9`。七类各 15 次，共 105 次调用全部成功、严格符合 Schema；
prompt、runtime、Low reasoning 与 wrapper 在批内一致。TraceOne `supported`
为 98/105：5.5 与 5.6 Luna 各 14/15，5.6 Terra、6 Astra、6 Luna 各 15/15，
5.6 Sol 为 13/15，6 Sol 为 12/15。低于事先固定的“每类至少 14/15”门槛，
因此 v10 不作为七模型通过的发布依据。

同响应的 ModelTrace 一问为 96/105，非重叠三问为 35/35；TraceOne 一问
整体多对两条，但这不足以证明七类全面优于上游。保存的逐样本证据见
[evaluation](../data/confirmation-v9-evaluation.json) 与
[head-to-head](../data/confirmation-v9-head-to-head.json)。v9 批次只有在这次
失败如实记录之后，才能作为下一版开发数据。

## 七模型首轮冻结确认：未过门槛

`release-candidate-v9` 于 2026-09-23 16:29:50 UTC 冻结，首条
`confirmation-v8` 于 16:32:05 UTC 采集。七类各 15 条，共 105 次调用全部成功、
严格符合 Schema，并使用相同的 Codex runtime、Low reasoning、prompt 与 wrapper。

TraceOne `supported` 是 101/105（96.19%）：5.5、5.6 Luna/Terra/Sol 和 6 Sol
各 15/15，6 Astra 与 6 Luna 各 13/15。因此没有达到预登记的“每类至少 14/15”
门槛。四条失败包括两条 outer guard 拒识和两条适配器误判；完整失败分母与逐条结果
见 [confirmation-v8-evaluation.json](../data/confirmation-v8-evaluation.json)。

同响应的新版 ModelTrace closed-set 一问也是 101/105，但逐类不同：5.6 Sol
14/15、6 Astra 13/15、6 Luna 14/15；非重叠三问为 35/35。它们不是模型服务
真实权重的证明，也不能凭这些点估计声称 TraceOne 已全面超过 ModelTrace。
对照见 [confirmation-v8-head-to-head.json](../data/confirmation-v8-head-to-head.json)。
这批失败确认只在冻结规则判定未通过后，才允许进入下一轮开发；不能把它重新称为
v9 的盲测成功。

## 0.2.0 七模型开发证据

首轮失败确认记录后，`confirmation-v8` 才转为 v10 开发数据。该批七类各 15 条
做三折留出，训练折使用旧 581 条和其余每类 10 条。最终规则在 105 条留出上
为 103/105，各类至少 14/15；这不是独立确认。最终拟合用 686 条、每类 98 条，
并于新确认采集前冻结在
[release-candidate-v10.json](../config/release-candidate-v10.json)。开发比较与逐条
错误见 [seven-model-development-v2.json](../data/seven-model-development-v2.json)。

同一九标签 held-label 压力测试中，新 `supported` 仍为 34/324 误接收，
`enrolled` 为 52/324；GPT-5.4 仍有 19/36、Claude Opus 5.5 仍有 10/36。
这是调参数据，不是新的独立 OOD 盲测；见
[open-world-v4-development.json](../data/open-world-v4-development.json)。
新确认计划是 [confirmation-v9.json](../config/confirmation-v9.json)，门槛仍为
七类每类至少 14/15。

ModelTrace 作者及时公开的新版 16-model bank（上游 commit
`55a2e4a55170423b484d701e9a82ab62b268c811`）包含 GPT-6 Sol 与 Luna 的
各 36 条 Low-reasoning 参考响应。TraceOne 在此优秀开放工作的基础上，用同一个
9×35 问题另外采集两款各 83 条独立 enrollment，与旧五款各 83 条组成平衡的
581 条训练集。两批 enrollment 的 Codex runtime 不同，已逐类记录。

冻结前的 68/15 开发划分共有 105 条测试响应：`supported` 为 100/105，
`enrolled` 为 102/105。新款 6 Sol 是 15/15；6 Luna 的 `supported` 是 13/15，
其中一条分类错、一条被支持域拒识。旧版 Astra 也为 13/15；这是需要保留的
失败证据，不能写成“七款开发集全对”。完整逐样本结果见
[seven-model-development-v1.json](../data/seven-model-development-v1.json)。

16-model held-label open-world 开发评测包含九个未登记标签各 36 条：
`supported` 误接收 34/324（10.49%），`enrolled` 51/324（15.74%）；
ModelTrace closed-set 按定义会给 324/324 个有效 unknown 输入命名。主要短板为
GPT-5.4 的 19/36 与 Claude Opus 5.5 的 10/36。数据仍来自上游参考语料，
并非独立 provider 盲测；它与旧版 24/288 使用的标签集合不同，不能直接比较
百分比。见 [open-world-development-v3.json](../data/open-world-development-v3.json)。

首轮 581 条训练配置先固定在
[release-candidate-v9.json](../config/release-candidate-v9.json)，随后按
[confirmation-v8.json](../config/confirmation-v8.json) 的七款各 15 条规则采集新
确认集，随后未过门槛。开发数据只用于选择配置，不能替代新确认结果。

## 0.1.0 五模型发布结论（历史）

0.1.0 发布使用 `release-candidate-v8` + `confirmation-v7`：先冻结、后采集、再揭盲。

- 75 次调用全部 `return_code=0`，75 个 sample ID 唯一。
- 75/75 严格 9×35 Schema 合规；prompt/schema hash、runtime、reasoning、wrapper
  在批内均一致。
- TraceOne `supported`：75/75，coverage 75/75，Wilson 95% CI
  95.13%–100%。
- 五类：5.5、Luna、Terra、Sol、Astra 均为 15/15。

这些是 requested-label agreement，不是独立的 served-weight 真值。

## 同响应 ModelTrace 对照

- TraceOne 一问：75/75。
- ModelTrace closed-set 一问：74/75；唯一错误在 Sol，因此 Sol 14/15，另四类
  15/15。
- ModelTrace 三问：25 个非重叠 triplet 全对，每类 5/5。

TraceOne 对 ModelTrace 一问的 paired discordance 只有 1 比 0；单侧 exact sign/
McNemar p=0.5，不足以证明准确率显著更高，也不是正式 non-inferiority 检验。
可以支持的结论是：本批五类逐类点估计未低于一问对照，Sol 多对一条；每次决定
从三次调用降到一次，且一问与三问 arm 的 accuracy 点估计均为 100%。三问只有
25 个决定，不能把 25/25 和 75/75 当作等样本量比较。

证据：

- [confirmation-v7 evaluation](../data/confirmation-v7-evaluation.json)
- [confirmation-v7 head-to-head](../data/confirmation-v7-head-to-head.json)
- [public confirmation responses](../data/public/confirmation-v7.jsonl)
- [release manifest](../config/release-v0.1.0.json)

## Open-world development

每个 fold 删除一个完整 excluded label 后再拟合，合计 8×36=288 个真正未见
label 样本：

- TraceOne `supported`：24/288 false accepts，8.33%，Wilson 95% CI
  5.66%–12.10%。
- TraceOne `enrolled`：59/288，20.49%，Wilson 95% CI 16.23%–25.52%。
- ModelTrace closed-set：288/288 false identifications；它在有效输入上没有
  `unknown` 分支。
- 同一 75 条 target holdout 在八个 gallery fold 中重复使用：`supported` 平均
  98.33%，最低 97.33%；不能把它当成 600 个独立样本。
- 主要失败集中于 GPT-5.4：`supported` 20/36 false accepts。

这是超参数已被查看的 development 结果，而且 unknown 来自上游语料，不是新
provider 盲测。它证明方法显著减少 closed-set 强制命名，但没有证明普适 OOD。
完整 decisions 在 [open-world-development-v2.json](../data/open-world-development-v2.json)。

旧 v6 的“完整 bank 内 excluded labels 2/288”只说明已登记 distractor rejection；
因为那些 labels 参与了 bank 构建，不再称为真正 open world。

## 开发过程中的失败

- 无 Schema 的 v2 曾出现 Luna 越界并截断，促成 strict 9×35 Schema。
- confirmation-v2 为 73/75，Sol 13/15；未过门槛。
- 190-row adapter 的真正盲测 confirmation-v3 为 71/75；未过门槛。
- confirmation-v4 为 73/75，Sol 13/15；未过门槛。
- v6 adapter 的 confirmation-v5 为 74/75；唯一失败是 Astra 240 秒 timeout，
  其余 74 个有效响应全部正确。
- v7 target-support 的 confirmation-v6 为 71/75：adapter 两错，support 又拒绝
  两个正确 Astra；未过每类 ≥14/15 门槛。这批随后才成为 v8 development。
- v8 选择 alpha=1：415-row whole-collection CV 为 412/415，优于 alpha=30 的
  411/415。KNN、LDA、RBF prototype 均未超过；见
  [adapter-model-exploration.json](../data/adapter-model-exploration.json)。

历史失败不与最终 confirmation 合并。为缩小公开发布面，原始失败批次不进入精简
主分支；其分母、关键结果和淘汰原因完整保留在本账本。

## Active probe 负结果

我们尝试把自由数字序列改成一次响应内 128 个成对二选一 bit：随机 pair v1 在
同数据选超参数的小样本 leave-one-out 为 24/25；按 340 条 enrollment 优化 pair
后的 v2 反而为 22/25，均低于主方法，因此没有进入发布 classifier。这项开发负
结果保留在账本中；其探索性 prompt、脚本和原始评测不进入精简发布主分支，也不
构成盲测结论。

## 降质检测状态

仓库提供完整方法，但没有捏造“已检测到服务端降质”的实测结论。

- 48-item canary 在假设 regression=0.10、improvement=0.02、minimum effect=0.05
  时 exact power 只有 29.06%。
- 192-item canary v2 的相应 power 为 89.76%。
- 实现报告 paired regressions/improvements、无效与缺失、exact one-sided McNemar，
  并对题族做 Holm-Bonferroni。

功效依赖预声明概率；实际监测必须重新记录 baseline/current 的 model、provider、
runtime、reasoning、wrapper、日期与重试策略。
