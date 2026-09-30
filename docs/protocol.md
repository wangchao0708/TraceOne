# 评测协议

[简体中文](protocol.md) | [English](protocol.en.md)

## 1. 目标与真值边界

目标是在记录 Codex runtime、固定 `reasoning_effort=low`、wrapper 和 prompt 的条件下，
从一次响应判断七个 `requested_model` route label，或返回 `unknown`。事件流没有
独立 `response_model` 或权重证明，因此结果叫 requested-label agreement，不能
解释为服务端实际权重的 ground truth accuracy。

身份识别必须只有一个模型调用和一个响应。9×35 个数字是同一响应内的 315 个
微选择；JSON Schema 是输出约束，不是额外问题。能力降质是另一个多题流程，
不计入身份识别的一问预算。

## 2. 冻结发布管线

七模型历史 v11 的 315 数字配置为
[release-candidate-v11.json](../config/release-candidate-v11.json)；
v9、v10 候选与失败确认保留在历史记录中。
五模型历史发布配置仍见
[release-candidate-v8.json](../config/release-candidate-v8.json)：

1. strict parser 要求对象只含 `numbers`，形状 9×35，值为 1–355 的 integer。
2. 复用 ModelTrace 的 16-model marginal Hellinger 与 ordered-block bank，并计算
   absolute JS similarity。不足 280 个可用值会拒识；非目标 top 只有在目标
   marginal 候选满足相似度、边际优势和 fused 差距 ≤0.20 的预设回退条件时才能通过。
3. 通过 outer guard 后，48 维 bank feature（16 fused、16 marginal、16 absolute
   similarity）加 355 维原始数字频率进入 alpha=1 的七类 ridge adapter；频率
   维度权重 0.25，margin <0.01 时拒识。support 仍只使用原 48 维。
4. 默认 `supported` 再检查 shrinkage Mahalanobis target-support envelope。
   每类 99% empirical distance 阈值；高于每类第 90 百分位的 adapter margin
   可 rescue。若 adapter margin <0.01，只有 outer 目标候选的 fused margin ≥0.25、
   相似度 ≥0.60 且支持距离达标时才允许 bank rescue。它是经验 support，
   不具 distribution-free OOD 保证。

七模型当前训练集共 791 条、每类 113 条：各类原有 83 条，加上失败后转为开发
数据的 `confirmation-v8` 与 `confirmation-v9` 各 15 条。每类 Codex runtime 均显式
记录，训练跨日期与 runtime，时间漂移仍是限制。0.1.0 的 415 条训练和
`confirmation-v7` 冻结结果保持为历史证据。

初版开发划分是各类 68 条训练 / 15 条测试，随后 v9 在新确认集上未过门槛。
只有记录失败后，`confirmation-v8` 与 `confirmation-v9` 才依次转作后续开发数据。
v11 对两批做整批留出开发检查，最终使用全部 791 条拟合，并在
[confirmation-v10.json](../config/confirmation-v10.json) 预登记新确认计划；
该批虽达 103/105，但 GPT-6 Sol 只有 13/15，未过预设门槛。

## 3. Operating profiles

- `supported`：默认；outer guard + ridge + target support，优先降低未见类误接收。
- `enrolled`：outer guard + ridge，优先已登记路由 sensitivity。
- `bank`：仅上游特征与 guard，用于消融，不是推荐发布模式。

必须同时报告 match rate、coverage 和 abstention；禁止只在已识别子集上报 accuracy。

## 4. 数据划分与调参纪律

- Development：选择 prompt、feature、guard、adapter 与 support；不能作最终结论。
- Group CV：完整 collection 留一，测试批次不参与 normalization、fit 或阈值。
- Confirmation：先固定配置、样本数、成功规则与 hash，再采集全新响应。
- Open world：完整 label 同时从 gallery、feature space 和 support fit 中移除。

旧 v7 配置的 confirmation-v6 为 71/75，未过预注册门槛；随后才允许作为 v8
development 数据。v8 的 confirmation-v7 是最终未见盲测，不能再用于修改 v8。
七模型 v9 的 confirmation-v8 为 101/105，Astra 和 6 Luna 各 13/15；它未过
每类 ≥14/15 门槛，所以后续仅作为 v10 开发数据，绝不能回写成 v9 成功。
v10 的 confirmation-v9 为 98/105；v11 的 confirmation-v10 为 103/105，
但 6 Sol 为 13/15。三次失败均保留完整分母，不能把已查看的批次重新称作
独立成功。
失败调用、格式错误、误判与 `unknown` 全部留在主分母。

## 5. 对照设计

0.1.0 的 head-to-head 对同一批 75 条响应运行；七模型 105 条确认批次也沿用
同一对照定义，并把三问划成每类五个互不重叠 triplet：

- TraceOne：每条响应作一次决定；
- ModelTrace-one：同一条响应的 closed-set mean fused argmax；
- ModelTrace-three：按模型和顺序划分三条一组；五模型批次有 25 组，七模型
  批次有 35 组，每组作一次决定。

比较复用同一 bank 与响应以减少数据差异，但 prompt/Schema 是 TraceOne 的，不是
ModelTrace 随机 challenge 原文；三问在七模型批次只有 35 个独立决定，置信区间
更宽。不同论文
或社区数据集的点估计只作背景。

## 6. Open-world 定义

完整 bank 中“excluded route 被拒绝”只是 registered-distractor 结果，因为该标签
参与了 bank 构建。真正 held-label 流程对每个 excluded label 重新构建 bank、
adapter feature space 和 support，再测试被删标签。ModelTrace closed-set 在这些
有效输入上没有 `unknown`，所以当前 324/324 必然被命名；这不是称其 0% accuracy，
而是 100% false identification under unknown truth。

open-world v5 在九个 excluded label、324 条上得到 `supported` 22 条误接收，
其中 GPT-5.4 为 13/36、Claude Opus 5.5 为 8/36。这些数据用于调参，
只能称 development estimate。独立 provider、
新日期和未见 wrapper 的盲测仍是缺口。

## 7. 降质协议

数字指纹漂移不能证明能力下降。Canary baseline/current 必须使用同一版本题目、
scorer、reasoning、wrapper、重试策略和时间预算，并逐题配对：

- 主检验：exact one-sided McNemar；baseline 对/current 错为 regression，反向为
  improvement。
- 结论：observed accuracy loss 达到预声明 minimum effect，且 p≤alpha，才报告
  `degraded`。
- 无效回答默认计错；题目集合不一致默认 `invalid_comparison`，不能静默取交集。
- overall 是预声明 primary test；题族是 secondary tests，用 Holm-Bonferroni。
- benchmark 题量先用预期 regression/improvement 概率做 exact power planning。

Canary v2 有四个题族、每族 48 题，共 192 题。题目或独立 session 是统计单元，
不能把同一长响应中的 token 当成独立样本。

## 8. 公开数据与隐私

`data/live/` 永不提交。`scripts/export_public_data.py` 删除本地 `thread_id` 和
`stderr_tail`，保留数字响应、route、runtime、reasoning、usage、时间与 hash；
manifest 记录源文件和公开文件 digest。发布前仍需人工检查未来 runtime 新字段。

## 9. 已知限制

- 行为指纹会随 system prompt、wrapper、reasoning 和时间漂移。
- 上游参考语料缺少完整 reasoning provenance。
- 0.1.0 五类各 15 条只能证明该批结果；75/75 的 Wilson 95% 区间仍为约 95.13%–100%。
- GPT-5.4 是当前最难未见类，七模型 development 中仍有 13/36 false accepts。
- 没有 routing log/attestation，不能区分 detector error、自然波动和真实换模。

## 10. GPT-6.1 Sol 首轮扩展开发（历史阶段）

本节记录最早489次开发的当时决策；0.3.0已登记第八类，后续实现和确认见第11节。

[OpenAI 官方模型说明](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
确认模型 ID 为 `gpt-6.1-sol`，且支持 `low` reasoning。2026-09-30 的早期试调
曾返回“不支持该模型”；同日后续使用 Codex CLI 0.159.2 已验证可调用，并采集
了真实响应。现在训练函数可显式接收八类标签，support 从 adapter 读取类别；
默认采集、包内资产和网页预测仍保持七类，不把调用成功等同于识别通过。

本轮保持一问 315 数字、Low reasoning、隔离 wrapper 与完整 provenance。
全部 489 次调用均使用 Codex 订阅，没有使用付费 API 或账户重置额度。原问题给
6.1 Sol 采集 113 条 enrollment，对八类各采集 15 条开发响应；另测两种小规模
数字指令及一组八类各 24 条的改进问题。原问题的旧七类 enrollment 来自历史
运行时，而八类开发响应都使用同一 0.159.2 runtime。这是开发验证，不是八类
同期盲测；新增 enrollment 中也有晚于这批开发响应采集的记录。

对最初“直接重建 17-model bank”的计划作如下有记录调整：本轮缺少与上游匹配的
多环境 6.1 Sol 参考语料，因此保留 16-model bank 作为冻结的特征提取器，只训练
显式八类 adapter/support，不向原中心列表追加单独一个中心。未来若重建 17-model
outer bank，仍须从独立原始参考数据重新拟合归一化、环境方向与中心；不能与
enrollment、最终确认混用。原问题与改进问题的数据分别拟合，不能混成一个
单提示词训练集。

开发结果表明 Astra 与 6.1 Sol 尚不能稳定区分，详见
[结果](results.md#gpt-61-sol-扩展开发尚未通过发布门槛)。因此未启动最终八类确认，
也未上线新的预测模型。采集脚本用 `--allow-prospective` 明确允许经验证的新路由
参与多模型开发批次；不加该参数时，保留默认七类和新路由单独采集的保护。

所有规则与资产先冻结，再对八类各采集至少 15 条未见响应；沿用每类 ≥14/15
的预设识别门槛，失败、拒识和格式错误保留在分母。同响应 ModelTrace 一问及
互不重叠三问仍只作有边界的对照。网页自包含 prompt 的本轮 16 次 pilot 只作
兼容性检查，不能支持准确率声明；在重新冻结、独立确认与 Python/JavaScript
一致性证据到位前，不展示第八个预测选项。

冻结历史版本须在其原始 Git 提交上校验，不能修改旧 digest 来迁就新代码：

```text
python3 scripts/verify_frozen.py config/release-candidate-v11.json --revision 8d70a3b
```

本轮还把 raw-frequency 加权边界从写死的 48 改为 bank 模型数的三倍。对默认
16-model bank 数值不变；对删去一类的 held-label bank 则修正为 45。历史 OOD
开发结果仍属于当时实现，不能直接标成这个修正版或八类方法的 OOD 准确率。

复验前应重新检查所有目标是否能在同一账户、客户端和推理条件下调用；不能把历史
样本与不同日期、环境的新样本拼接成“同期盲测”。若可用模型集合改变，应重新登记
目标集合，并保留历史结果。

## 11. 0.3.0 八模型实验实现与发布边界

模型集为八条路由，包含 `gpt-6.1-sol`；采集不再要求该模型的 prospective opt-in。
CLI默认 `optimized` 使用 `identity-replacement-v1` 自包含问题；`supported` 和
`traceone prompt --legacy` 保留七类历史方法与问题。不要混用两版问题和分类器。

训练使用同一CLI 0.159.2、Low reasoning、同一问题的576次开发调用，571条参与拟合。
每次目标仍为315个整数。Schema约束用于登记；独立校准128次和全新确认120次均
不附加Schema，与网页条件相同。训练、校准、确认的ID分离，失败不从评测分母删除。

96个开发配置按最差逐类匹配数优先、总数其次、并列时简单ridge优先选择。
结果是alpha=1，48 bank特征、355原始频率和188重复/顺序统计；每组标准化后按
weight/sqrt(dim)加权，group weights为1、1、0.5。原16-model bank未添加伪造的6.1中心。
73维支持范围使用独立校准的逐类最大距离、covariance shrinkage=0.3；没有high-margin
bypass。它是经验检查，不提供身份概率或跨漂移的分布无关保证。

输入必须能读取为九个数组或唯一 `numbers` key 的对象。允许丢弃越界和非整数值，
每行需25–45个有效整数、总数280–350；不得补造或clamp整数。严格9×35、1–355格式
合规率另外报告；无法解析、输入不合格、工具执行、超时和拒识均计入未匹配。
支持距离比较使用1e-10相对浮点容差，margin使用1e-12绝对容差，以保持跨语言边界一致。

先冻结代码、数据和参数于 `5b70968`，再采集每类15次确认，规则仍是每类≥14/15。
实际101/120，Astra、6 Luna、6.1 Sol未过门槛；确认之后没有再调参或替换调用。
本次按已选择配置发布实验源码；随后按明确请求同步线上站点，不宣称整体性能改善。
完整失败证据见[结果](results.md)。网页降智线索中，Astra/6.1相互混淆一律为无法判断；
其他不一致也不能单独证明能力下降，能力降质仍需独立paired canary。
