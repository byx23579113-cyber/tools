"""常量定义模块"""

from enum import Enum


class EventType(str, Enum):
    """事件类型枚举"""

    CONTEXT_COMPRESSED = "context.compressed"
    CHAT_DELTA = "chat.delta"
    CHAT_FINAL = "chat.final"
    CHAT_ASK_USER_QUESTION = "chat.ask_user_question"
    CHAT_INVOCATION_PAUSED = "chat.invocation_paused"
    TASK_START = "task.start"
    TASK_COMPLETE = "task.complete"
    TOOL_CALL = "chat.tool_call"
    TOOL_RESULT = "chat.tool_result"


class FlowItemType(str, Enum):
    """流程项类型枚举"""

    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    COMPRESSION = "compression"
    ASSISTANT_RESPONSE = "assistant_response"
    ASK_USER_QUESTION = "ask_user_question"
    INVOCATION_PAUSED = "invocation_paused"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"


class Role(str, Enum):
    """角色枚举"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


BADGE_COLORS = {
    "high": "badge-red",
    "medium": "badge-orange",
    "low": "badge-blue",
}

SOURCE_CHUNK_TYPES = {
    "LLM_REASONING": "llm_reasoning",
    "ANSWER": "answer",
}
