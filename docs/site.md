# TraceOne Web

[简体中文](site.md) | [English](site.en.md)

在线地址：<https://traceone-model-check.nutmeg-basil-6747.chatgpt.site>

## 仓库源码与线上部署分开

本次只更新GitHub。仓库dist/和CLI包含八模型实验实现及GPT-6.1 Sol；在线站点
没有重新部署，仍使用此前七模型版本及Astra/6.1重叠提示。运行八模型源码：

```text
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

在同一机器打开http://127.0.0.1:8000。仅绑定loopback，不对外发布；Ctrl+C停止。

## 八模型源码的工作流

同一工作区切换模型识别和降智线索。识别模式复制一个自包含315数字问题，粘贴
回答后预测八条登记路由之一或unknown。降智线索模式先选择使用的模型，自动将
预测与所选标签比较，显示指纹一致、指纹异常或无法判断。

Astra和6.1 Sol互相混淆时，降智线索直接显示无法判断，不把困难分类当作路由异常。
任何指纹不一致都不能单独证明能力下降；严格能力降质仍需独立paired canary。

两种语言保持完整问题展示、不自动折行的输入、居中单行结果及简洁上游致谢。
格式偏差明确提示：越界值丢弃，不补造整数。容错为九行、每行25–45个有效整数、
总数280–350；完整回答仍应为9×35个1–355整数。不可读或不合格时返回未知。

## 当前源码实现与证据

1. 未改写的ModelTrace衍生16-model bank提供分布及ordered-block特征。
2. 48 bank + 355 raw-frequency + 188 repetition/order特征进入八类ridge。
3. 独立校准的73维目标支持范围及margin允许拒识，没有high-margin bypass。
4. 原bank外层结论仅作诊断，不用旧标签集合否决新登记的6.1 Sol。

登记、校准和确认使用Codex订阅CLI 0.159.2、Low reasoning。后两者不附加Schema，
与页面问题完全一致；其他平台、API wrapper和推理设置未获这批数据验证。

新确认101/120（84.2%）、严格格式61/120，未过每类≥14/15门槛，详见[结果](results.md)。
它不是八款全面优于上游或模型身份认证。旧七类Schema的103/105不能移作当前网页准确率。

test_eight_classifier.mjs核对120条新响应的标签、格式、有效数、分数、间隔、
支持距离、阈值和empirical p-value，最大误差约3.4×10⁻¹³，容差1e-9。
旧105条结果继续用历史资产复核。test_site_assets.mjs检查当前两份部署资产与
Python源资产逐字节一致、网页与CLI及采集问题相同。源码一致性不等于在线部署。

## 隐私、解释和致谢

应用无需API Key，计算留在当前浏览器标签页，应用代码不会上传回答。候选条形图
只是相对分数，不是实际权重身份概率；相似度与经验支持也不是可信attestation。
system prompt、reasoning、runtime及服务更新均可能使行为漂移。

页面简洁致谢[ModelTrace](https://github.com/xqy2006/ModelTrace)。仓库具体感谢作者
xqy2006的优秀开源贡献，并说明方法继承和MIT复用边界，见[研究说明](research.md)
和[third-party NOTICE](../third_party/NOTICE.md)。
