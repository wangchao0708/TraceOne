# 致谢

[简体中文](ACKNOWLEDGEMENTS.md) | [English](ACKNOWLEDGEMENTS_EN.md)

TraceOne 最重要的直接基础是 xqy2006 的
[ModelTrace](https://github.com/xqy2006/ModelTrace)。ModelTrace 将语言模型的
随机数字选择偏差发展为完整、可复现的黑盒指纹方法，公开了特征实现、参考库、
采集流程、验证结果与适用边界。这项工作富有原创性、工程完成度高，而且以开放
源码和数据的方式为社区提供了极具价值的研究起点。TraceOne 对此表示由衷敬意
与感谢。

TraceOne 复用并改造了 ModelTrace 的 marginal Hellinger、ordered-block 特征、
统一参考 bank 和参考语料。固定的上游 commit、许可证及改动边界记录在
[third_party/NOTICE.md](third_party/NOTICE.md)。本仓库中的 head-to-head 对照旨在
说明新增协议的行为，不应被解读为否定 ModelTrace 的首创性或贡献。

ModelTrace 还明确致谢了更早的
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker)；相关
[Linux Do 社区讨论](https://linux.do/t/topic/2472419/1) 推动了随机数分布方法的
传播。TraceOne 同样感谢这些先行探索。ModelTrace 作者的
[项目复盘](https://linux.do/t/topic/2827119?tl=en) 对实验边界的坦诚说明，也直接
帮助了本项目设计更严格的一问、OOD 与盲测协议。

本项目还受到 LLMmap、LLMPrint、Targeted Counterfactual Fingerprinting、
Conformal Inference for Open-Set and Imbalanced Classification、Do System Prompts
Leave Behavioral Fingerprints?、ICLR 2026 的 When LLMs get significantly worse
以及 Amazon Science LLM Accuracy Stats 的启发。每项工作的具体作用与原始链接见
[docs/research.md](docs/research.md)。

如果使用 TraceOne，请同时引用或链接 ModelTrace，并按实际使用的方法引用上述
相关工作。`CITATION.cff` 也明确保留了这一请求。
