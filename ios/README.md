# iOS 示例工程说明

建议在此目录中按以下结构组织你的 iOS Demo：

- `coreml-demo/`：基于 CoreML 的 SwiftUI/Storyboard 项目。
- `mlc-chat-ios/`：引用 `MLC-LLM` 构建的聊天 Demo。
- `profiling/`：Instruments 采样脚本、MetricKit 报表。

使用流程：

1. 按照 `../docs/ios_setup.md` 准备模型（CoreML `.mlpackage` 或 MLC artifact）。
2. 将模型拖入 Xcode 工程并启用「Copy items if needed」。如模型较大，可改为首次启动下载。
3. 将采样、能耗数据导出到 `../docs` 对应记录中，便于与端云协同实验对比。
4. 如果需要共享给团队成员，请附上签名证书配置和测试设备列表，避免构建失败。

当前仓库未附带实际工程，可根据上述步骤创建并放置于此。*** End Patch
