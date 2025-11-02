# 安卓端验证与测试清单

在完成部署后，使用以下命令与步骤快速验证模型运行情况，确保系统稳定可靠。

## 1. 安装与启动
- 安装 Debug 包：`./gradlew installDebug`
- 启动 Activity：`adb shell am start -n com.example.llamacppdemo/.MainActivity`
- 查看 Logcat：`adb logcat -s llama.cpp MLC-LLM`（按需修改 TAG）

## 2. 模型文件
- 列出沙盒中的模型：`adb shell run-as com.example.llamacppdemo ls files/models`
- 检查大小：`adb shell run-as com.example.llamacppdemo du -h files/models`
- 若缺失，可执行脚本推送：`powershell -ExecutionPolicy Bypass -File scripts\android_push_model.ps1 -ModelFile ... -PackageName ...`

## 3. 推理验证
- 发送标准 Prompt 并观察输出：在 App 内执行或通过调试接口发送。
- 若支持命令行入口，可调用：`adb shell am broadcast -a com.example.llamacppdemo.TEST_PROMPT --es prompt "你好"`。
- 检查 Logcat 是否有 `"Inference finished"` 或类似结束标记。

## 4. 性能采集
- 重置并导出电量统计：  
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\android_collect_batterystats.ps1 `
      -PackageName com.example.llamacppdemo `
      -Output logs\android\batterystats.txt
  ```
- 记录 CPU/GPU 使用率：`adb shell top -d 1 | findstr com.example.llamacppdemo`
- 使用 Perfetto：`adb perfetto -c config.pbtxt -o trace.perfetto-trace`

## 5. 稳定性测试
- Monkey 测试（随机事件）：`adb shell monkey -p com.example.llamacppdemo -v 1000`
- 长时推理：编写脚本循环发送请求并监控内存/温度。
- 检查应用崩溃日志：`adb shell dumpsys crash`

## 6. 日志与指标对齐
- 导出推理日志：`adb pull /sdcard/Android/data/com.example.llamacppdemo/files/logs logs/android`
- 使用 `python` 脚本合并端侧日志与 PC 指标（可参照 `docs/logging_guidelines.md`）。
- 核对 `id` 是否一致，确认测试数据可用于分析。

完成上述验证后，即可进入端云联合评估或进一步的性能调优阶段。*** End Patch
