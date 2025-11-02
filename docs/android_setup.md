# Android 端 LLM 部署指南

本指南提供在 Android 手机上运行量化大模型的完整流程，涵盖环境准备、模型量化、工程集成、性能调优与常见问题。根据需要选择 `llama.cpp`（纯本地 CPU/GPU 推理）或 `MLC-LLM`（TVM Runtime，可调用 GPU/NNAPI）。

## 1. 环境准备

1. 安装 **Android Studio Electric Eel (2022.3)+**，在 `SDK Manager` 勾选：
   - Android SDK Platform 34
   - Android SDK Build-Tools 34
   - NDK r26b 及以上
   - CMake、LLDB
2. 安装 **JDK 17**，在 Android Studio `File > Settings > Build Tools > Gradle` 中指定。
3. 安装 **Python ≥ 3.9**，建议运行 `scripts/setup_env.ps1`（Windows）或 `scripts/setup_env.sh`（macOS/Linux）创建虚拟环境。
4. 安装 **Git** 和 **Hugging Face CLI**：`pip install huggingface_hub`，并执行 `huggingface-cli login`。
5. 手机开启开发者模式，打开 **USB 调试** / **通过 USB 安装** / **允许调试日志** 等选项。

环境验证命令：

```powershell
adb devices
python --version
cmake --version
```

均正常后继续下一步。

## 2. llama.cpp 方案

### 2.1 模型量化

1. 克隆仓库：`git clone https://github.com/ggerganov/llama.cpp`。
2. 安装依赖：`python -m pip install -r llama.cpp/requirements.txt`。
3. 使用仓库自带工具或本项目脚本量化（示例使用本仓 `scripts/convert_to_gguf.py`）：
   ```powershell
   python scripts\convert_to_gguf.py `
     --repo qwen/Qwen2.5-1.5B-Instruct `
     --llama-cpp-path D:\repo\llama.cpp `
     --dtype fp16 `
     --quant q4_K_M `
     --out models\qwen2.5-1.5b
   ```
   输出示例：`models/qwen2.5-1.5b/model-q4_K_M.gguf` 与 `tokenizer.model`。

### 2.2 编译 Android Demo

1. 在 Android Studio 打开 `llama.cpp/android` 工程。
2. 将 GGUF 模型与 tokenizer 复制到 `app/src/main/assets/models/`。
3. 修改 `MainActivity.kt` 指向模型路径、上下文长度：
   ```kotlin
   private val modelPath = "models/model-q4_K_M.gguf"
   private val promptTemplate = """
       A helpful assistant.
       User: %s
       Assistant:
   """.trimIndent()
   ```
4. 检查 `CMakeLists.txt` 与 `gradle.properties` 中的 NDK、CMake 版本是否正确。
5. 用真机运行（首启会将模型复制到 `/data/data/<pkg>/files/models`）。

### 2.3 性能调优

- 调整线程：`params.n_threads = Runtime.getRuntime().availableProcessors()` 或手动指定大核数量。
- 控制批量：`params.n_batch = 128~256`，避免内存溢出。
- 启用 GPU（OpenCL/Vulkan）：参考官方 `ggml-opencl` 或 `ggml-vulkan` 分支重新编译。
- 记录耗时：在 Kotlin 端使用 `SystemClock.elapsedRealtime()`；必要时写入日志文件。

## 3. MLC-LLM 方案

### 3.1 安装与打包

```powershell
pip install --upgrade mlc-llm-nightly mlc-llm-core

python scripts\package_with_mlc.py `
  --repo qwen/Qwen2.5-1.5B-Instruct `
  --quantization q4f16_1 `
  --target android `
  --out models\mlc_qwen15b `
  --conv-template qwen2
```

输出目录包含 `params`, `weights`, `metadata`, `model_library_generated.*`，以及 Java/Kotlin 绑定所需资源。

### 3.2 集成到 Android 项目

1. 克隆官方示例：`git clone https://github.com/mlc-ai/mlc-llm`，打开 `android/MLCChat`。
2. 将 `models/mlc_qwen15b` 复制到 `app/src/main/assets/models/qwen/`。
3. 在 Kotlin 代码中初始化：
   ```kotlin
   private lateinit var runtime: MLCChatModule

   private fun initRuntime(context: Context) {
       val config = RuntimeConfig(
           modelPath = "qwen",
           modelLib = "model_lib",
           modelType = "int4",
           maxNumTokens = 2048
       )
       runtime = MLCChatModule(context, config)
   }

   private fun runInference(prompt: String) {
       runtime.generateAsync(
           prompt = prompt,
           progressCallback = { token -> appendToken(token) },
           completionCallback = { result -> showResult(result) }
       )
   }
   ```
4. 如需 GPU / NNAPI 加速：
   ```kotlin
   runtime.updateConfig(
       deviceType = DeviceType.ANDROID,
       gpuDelegate = GPUDelegate.AUTO,
       useNNAPI = true
   )
   ```
5. 运行时模型会自动解压到沙盒目录，可通过 `Logcat` 观察加载状态。

## 4. 推理日志与 ADB 工具

- 将时间戳、生成 token 数、能耗等信息写入 `/sdcard/Android/data/<pkg>/files/logs/run_*.jsonl`。
- 导出日志：
  ```powershell
  adb shell run-as <pkg.name> ls files/logs
  adb pull /sdcard/Android/data/<pkg>/files/logs logs/android
  ```
- 获取耗电数据：
  ```powershell
  adb shell dumpsys batterystats --reset
  # 运行测试后
  adb shell dumpsys batterystats > logs/android/batterystats.txt
  ```

## 5. 推荐目录结构

```
MobileLLMDeploy/
  models/
    qwen2.5-1.5b/
      model-q4_K_M.gguf
      tokenizer.model
    mlc_qwen15b/
      params/
      weights/
  android/
    llama_cpp_demo/         # Android Studio 工程
    mlc_chat_app/           # MLC 官方模板拷贝
```

## 6. 常见问题

- **模型加载失败**：确认模型路径、读写权限，或将模型放入外部存储并动态复制。
- **内存不足崩溃**：使用更高的量化等级（q4_K_M → q4_0 → q3_K）或减小上下文长度。
- **推理速度慢**：确认运行在大核 / GPU / NNAPI；调低 `n_batch` 或在 `perf_tuning.md` 中进一步调优。
- **APK 体积过大**：考虑首次启动在线下载模型或使用 OBB/分包。

完成以上步骤后，即可在真机上验证推理效果，并与 `docs/perf_tuning.md`、`docs/edge_cloud_workflow.md` 一起开展端云协同实验。*** End Patch
