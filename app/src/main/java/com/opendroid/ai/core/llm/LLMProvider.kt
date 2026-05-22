package com.opendroid.ai.core.llm

import com.opendroid.ai.data.models.ChatMessage
import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.Serializable

interface LLMProvider {
    val name: String
    val availableModels: List<String>
    suspend fun complete(request: LLMRequest): LLMResponse
    fun streamComplete(request: LLMRequest): Flow<String>
    suspend fun isAvailable(): Boolean
}

@Serializable
data class LLMRequest(
    val systemPrompt: String,
    val messages: List<ChatMessage>,
    val temperature: Float = 0.7f,
    val maxTokens: Int = 2000,
    val responseFormat: ResponseFormat = ResponseFormat.JSON,
    val tools: List<Tool>? = null
)

enum class ResponseFormat {
    JSON, TEXT
}

@Serializable
data class Tool(
    val name: String,
    val description: String,
    val parameters: String // JSON Schema string representing parameters
)

@Serializable
data class LLMResponse(
    val content: String,
    val tokensUsed: Int,
    val model: String,
    val provider: String,
    val latencyMs: Long
)

fun List<ChatMessage>.toOpenAIMessages(systemPrompt: String): List<Map<String, Any>> {
    val messagesList = mutableListOf<Map<String, Any>>()
    messagesList.add(mapOf("role" to "system", "content" to systemPrompt))
    this.forEach { msg ->
        val role = if (msg.sender == ChatMessage.Sender.USER) "user" else "assistant"
        if (msg.imageBase64 != null && role == "user") {
            messagesList.add(
                mapOf(
                    "role" to role,
                    "content" to listOf(
                        mapOf("type" to "text", "text" to msg.text),
                        mapOf(
                            "type" to "image_url",
                            "image_url" to mapOf(
                                "url" to "data:image/jpeg;base64,${msg.imageBase64}"
                            )
                        )
                    )
                )
            )
        } else {
            messagesList.add(mapOf("role" to role, "content" to msg.text))
        }
    }
    return messagesList
}
