# iOS 端 LLM 部署指南

本指南介绍两种在 iOS 设备上运行本地大模型的主流方案：使用 CoreML 将 Transformer 模型转为 `.mlpackage`，以及通过 `MLC-LLM` 自动生成 TVM-runtime 的 Swift 接口。两者均支持 int4/int8 量化，可在 A17/M 系列芯片上达到秒级响应。

## 1. 前置条件

- macOS 14+，Xcode 15+（Command Line Tools 一并安装）
- Python ≥ 3.9，建议使用 `conda`/`pyenv` 独立环境
- `coremltools`、`mlc-llm`、`huggingface_hub`
- iOS 真机或模拟器（真机需要开发者账号签名）

安装依赖：

```bash
python -m pip install --upgrade coremltools mlc-llm-nightly huggingface_hub transformers accelerate
```

> 如需 int4 压缩，确保 `coremltools` 版本 ≥ 7.0。

## 2. CoreML 工作流

### 2.1 权重准备

1. 下载模型：`huggingface-cli download qwen/Qwen2.5-1.5B-Instruct --local-dir models/qwen2.5b`。
2. 合并权重（如遇自动分 shard）：`python scripts/merge_shards.py`（可选）。

### 2.2 转换为 CoreML

```python
import coremltools as ct
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "qwen/Qwen2.5-1.5B-Instruct", torch_dtype=torch.float16, device_map="cpu"
)
model.eval()

example = {
    "input_ids": torch.ones((1, 1), dtype=torch.int32),
    "attention_mask": torch.ones((1, 1), dtype=torch.int32),
}

mlmodel = ct.convert(
    model,
    convert_to="mlprogram",
    inputs=[ct.TensorType(name="input_ids", shape=example["input_ids"].shape, dtype=ct.int32),
            ct.TensorType(name="attention_mask", shape=example["attention_mask"].shape, dtype=ct.int32)],
    minimum_deployment_target=ct.target.iOS17,
)
mlmodel.save("models/Qwen15B.mlpackage")
```

### 2.3 量化压缩

```python
from coremltools.optimize.coreml import (
    quantization_utils as quant_utils,
    OptimizationConfig,
)

config = OptimizationConfig(global_config=quant_utils.LinearQuantizerConfig(bitwidth=4))
quantized = quant_utils.linear_quantize_weights(mlmodel, config)
quantized.save("models/Qwen15B-int4.mlpackage")
```

对于 3B 以上模型，考虑分块转换或使用 `MLC-LLM` 更加高效。

### 2.4 Swift 集成

1. 将 `.mlpackage` 拖入 Xcode 工程，勾选「Copy items if needed」。  
2. 生成接口：`let model = try! Qwen15B(configuration: MLModelConfiguration())`。
3. 推理示例：
   ```swift
   let promptTokens = tokenizer.encode("User: 你好\nAssistant:")
   let input = Qwen15BInput(input_ids: promptTokens.ids, attention_mask: promptTokens.mask)
   let output = try? model.prediction(input: input)
   let logits = output?.logits // 根据 tokenizer 解码
   ```
4. 设置计算单元：
   ```swift
   let config = MLModelConfiguration()
   config.computeUnits = .all // CPU + GPU + ANE
   ```
5. 利用 `MLShapedArray` 将输出 logits 转换为概率分布，再通过采样生成 token。

## 3. MLC-LLM 工作流

### 3.1 生成 iOS 包

```bash
python -m mlc_llm translate qwen/Qwen2.5-1.5B-Instruct \
    --quantization q4f16_1 \
    --target iphone \
    --artifact-path models/mlc_qwen_ios
```

### 3.2 Xcode 项目集成

1. 克隆官方示例：`git clone https://github.com/mlc-ai/mlc-llm`。
2. 打开 `mlc-llm/ios/MLCChat.xcodeproj`。
3. 将 `models/mlc_qwen_ios` 拷贝至 `MLCChat/Resources/models/qwen`。
4. 在 Swift 中加载：
   ```swift
   let runtime = try! MLCChatRuntime(
       modelConfig: .init(modelPath: "qwen", modelLib: "model_lib", modelType: "int4"),
       device: .appleGPU
   )

   runtime.generate(prompt: prompt, progressHandler: { token in
       DispatchQueue.main.async { append(token: token) }
   })
   ```
5. 支持的 `device`：`.appleGPU`, `.appleCPU`, `.appleANE`。ANE 只在支持的硬件上可用。
6. 若需推流 / 中断，调用 `runtime.abortGenerate()`。

## 4. 性能与能耗监测

- **Xcode Instruments – Energy Log**：查看能耗、温度、CPU/GPU 利用率。
- **MetricKit**：获取完整周期的能耗统计。
- 自定义日志：记录 token/s、推理延迟、上下行流量，与 PC 基准脚本对齐。
- 控制上下文长度 (`max_context`) 和批处理大小 (`maxTokens`) 以避免内存峰值。

## 5. 常见问题

- **内存耗尽**：1.5B 模型 int4 后仍约 1.2–1.5 GB，需确保真机有足够可用内存；可尝试更小模型或分段生成。
- **编译时间过长**：MLC-LLM 首次构建会产生 TVM 编译缓存，可开启 `--use-cache=1`。
- **运行崩溃**：检查模型路径是否复制到 Bundle，确认签名证书有效。
- **推理速度慢**：开启 `.all` computeUnits 或使用 `device: .appleANE`（支持的 iPhone/iPad）。

---

更多调参技巧参考 `perf_tuning.md`，端云协同应对方式见 `edge_cloud_workflow.md`。若需自动化转换脚本，可从 `scripts` 目录复制并补充。*** End Patch
