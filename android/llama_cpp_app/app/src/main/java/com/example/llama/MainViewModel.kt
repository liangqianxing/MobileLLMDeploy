package com.example.llama

import android.llama.cpp.LLamaAndroid
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch

class MainViewModel(
    private val llamaAndroid: LLamaAndroid = LLamaAndroid.instance(),
) : ViewModel() {

    companion object {
        @JvmStatic
        private val NANOS_PER_SECOND = 1_000_000_000.0
    }

    private val tag: String? = this::class.simpleName

    var messages by mutableStateOf(listOf("初始化完成，点击下方加载模型。"))
        private set

    var message by mutableStateOf("")
        private set

    private val conversation = mutableListOf<Pair<String, String>>() // Pair<user, assistant>

    private val systemPrompt = """
        <|im_start|>system
        你是一个友好且专业的中文助手，回答要简洁、准确，并且全程使用中文。
        <|im_end|>
    """.trimIndent()

    override fun onCleared() {
        super.onCleared()
        viewModelScope.launch {
            runCatching { llamaAndroid.unload() }
                .onFailure { exc -> messages += (exc.message ?: "模型卸载失败") }
        }
    }

    fun updateMessage(newMessage: String) {
        message = newMessage
    }

    fun clear() {
        conversation.clear()
        messages = listOf("对话记录已清空。")
    }

    fun log(msg: String) {
        messages += msg
    }

    fun load(pathToModel: String) {
        viewModelScope.launch {
            runCatching {
                llamaAndroid.load(pathToModel)
            }.onSuccess {
                messages += "模型已加载：$pathToModel"
            }.onFailure { exc ->
                Log.e(tag, "load() failed", exc)
                // 允许重复加载按钮，提示后继续
                if (exc.message?.contains("already loaded", ignoreCase = true) == true) {
                    messages += "模型已加载，无需重复操作。"
                } else {
                    messages += (exc.message ?: "加载失败")
                }
            }
        }
    }

    fun send() {
        val userText = message.trim()
        if (userText.isEmpty()) return
        message = ""

        messages += "用户：$userText"
        messages += "助手："
        val assistantIndex = messages.lastIndex

        val prompt = buildPrompt(userText)
        val buffer = StringBuilder()

        viewModelScope.launch {
            val result = runCatching {
                llamaAndroid.send(prompt)
                    .catch { exc ->
                        Log.e(tag, "send() failed", exc)
                        updateAssistantLine(assistantIndex, "发生错误：${exc.message}")
                        throw exc
                    }
                    .collect { token ->
                        buffer.append(token)
                        updateAssistantLine(assistantIndex, buffer.toString())
                    }
            }

            result.onFailure { exc ->
                Log.e(tag, "send coroutine failed", exc)
            }

            if (buffer.isNotEmpty()) {
                val reply = buffer.toString()
                updateAssistantLine(assistantIndex, reply)
                conversation += userText to reply
            } else {
                updateAssistantLine(assistantIndex, "(未获得内容)")
            }
        }
    }

    private fun buildPrompt(userText: String): String {
        val sb = StringBuilder()
        sb.appendLine(systemPrompt)
        for ((user, assistant) in conversation) {
            sb.appendLine("<|im_start|>user")
            sb.appendLine(user)
            sb.appendLine("<|im_end|>")
            sb.appendLine("<|im_start|>assistant")
            sb.appendLine(assistant)
            sb.appendLine("<|im_end|>")
        }
        sb.appendLine("<|im_start|>user")
        sb.appendLine(userText)
        sb.appendLine("<|im_end|>")
        sb.append("<|im_start|>assistant\n")
        return sb.toString()
    }

    private fun updateAssistantLine(index: Int, content: String) {
        if (index < 0) return
        val mutable = messages.toMutableList()
        if (index >= mutable.size) return
        mutable[index] = "助手：$content"
        messages = mutable
    }

    fun bench(pp: Int, tg: Int, pl: Int, nr: Int = 1) {
        viewModelScope.launch {
            try {
                val start = System.nanoTime()
                val warmupResult = llamaAndroid.bench(pp, tg, pl, nr)
                val end = System.nanoTime()

                messages += warmupResult

                val warmup = (end - start) / NANOS_PER_SECOND
                messages += "预热耗时：$warmup 秒"

                if (warmup <= 5.0) {
                    messages += llamaAndroid.bench(512, 128, 1, 3)
                } else {
                    messages += "预热耗时过长，跳过后续测试。"
                }
            } catch (exc: IllegalStateException) {
                Log.e(tag, "bench() failed", exc)
                messages += (exc.message ?: "Benchmark 失败")
            }
        }
    }
}
