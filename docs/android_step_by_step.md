# Android 部署实操流程（Step-by-Step）

按照以下步骤即可在真机上完成一次完整的 LLM 部署与验证。所有命令默认在仓库根目录 `MobileLLMDeploy/` 下执行。

## 步骤 0：环境初始化
1. 创建虚拟环境并安装依赖（Windows PowerShell）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
   .\.venv\Scripts\Activate.ps1
   ```
   Linux/macOS：`bash scripts/setup_env.sh && source .venv/bin/activate`
2. 登录 Hugging Face：`huggingface-cli login`
3. 检查 ADB：`adb devices` 应显示已连接的手机。

## 步骤 1：下载与量化模型
1. 下载权重（示例：Qwen2.5-1.5B-Instruct）：
   ```powershell
   python scripts\download_model.py --repo qwen/Qwen2.5-1.5B-Instruct --output models\qwen2.5-1.5b\raw
   ```
2. 量化为 GGUF（llama.cpp）或 MLC artifact（二选一或都做）：
   - GGUF：
     ```powershell
     python scripts\convert_to_gguf.py `
       --repo qwen/Qwen2.5-1.5B-Instruct `
       --llama-cpp-path D:\repo\llama.cpp `
       --dtype fp16 `
       --quant q4_K_M `
       --out models\qwen2.5-1.5b\gguf
     ```
   - MLC：
     ```powershell
     python scripts\package_with_mlc.py `
       --repo qwen/Qwen2.5-1.5B-Instruct `
       --quantization q4f16_1 `
       --target android `
       --out models\qwen2.5-1.5b\mlc `
       --conv-template qwen2
     ```
3. 在 `models/qwen2.5-1.5b/README.md` 记录量化信息（可选）。

## 步骤 2：准备 Android 工程
1. 将 `llama.cpp/android` 或 `mlc-llm/android/MLCChat` 拷贝至本仓 `android/` 目录：
   ```powershell
   xcopy /E /I D:\repo\llama.cpp\android android\llama_cpp_demo
   ```
2. 在 Android Studio 打开对应工程，确认 Gradle 同步正常。
3. 将模型复制到 `app/src/main/assets/models/`：
   ```powershell
   Copy-Item models\qwen2.5-1.5b\gguf\model-q4_K_M.gguf android\llama_cpp_demo\app\src\main\assets\models\
   Copy-Item models\qwen2.5-1.5b\gguf\tokenizer.model android\llama_cpp_demo\app\src\main\assets\models\
   ```
   MLC 方案则复制整个 `models\qwen2.5-1.5b\mlc\` 目录到 `app/src/main/assets/models/qwen/`。
4. 修改 `MainActivity.kt` 或 `ChatModule` 中的模型路径与参数（见 `docs/android_setup.md`）。

## 步骤 3：推送/更新模型（可选）
若模型较大，不希望打包进 APK，可在安装后使用脚本推送：
```powershell
python -m pip install --upgrade colorama  # 可选
powershell -ExecutionPolicy Bypass -File scripts\android_push_model.ps1 `
  -ModelFile models\qwen2.5-1.5b\gguf\model-q4_K_M.gguf `
  -PackageName com.example.llamacppdemo
```
也可使用 `scripts/android_push_model.sh`（macOS/Linux）。

## 步骤 4：编译与运行
1. 在 Android Studio 选择目标设备，点击运行（或命令行执行 `./gradlew installDebug`）。
2. 首次运行时关注 Logcat，确认模型加载成功并开始生成文本。

## 步骤 5：记录日志与能耗
1. 应用内记录每次推理的开始/结束时间、token 数、能耗等，输出到 `files/logs/*.jsonl`（推荐格式见 `docs/perf_tuning.md`）。
2. 执行电量统计：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\android_collect_batterystats.ps1 `
     -PackageName com.example.llamacppdemo `
     -Output logs\android\batterystats.txt
   ```
3. 导出生成日志：`adb pull /sdcard/Android/data/com.example.llamacppdemo/files/logs logs/android`。

## 步骤 6：质量评估（与 PC 端联动）
1. 在 PC 端使用基准脚本生成指标（参考原仓 `experiments/mobile_benchmark/`）。
2. 将端侧日志与指标通过 `id` 合并，分析延迟/能耗 vs. 质量。

## 步骤 7：迭代与调优
- 调整线程数、批量大小、上下文长度。
- 尝试不同量化等级（q4_K_M vs q4_0 vs q5_K_M）。
- 评估 GPU/NNAPI 加速效果。
- 根据日志判断是否需要端云协同或进一步压缩模型。

执行完以上步骤，即完成一次完整的安卓端 LLM 部署与验证流程。*** End Patch
