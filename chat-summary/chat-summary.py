"""
Chat history manager: Summary + Trimming + RAG context.

Flow:
    1. Load history từ Redis
    2. Summary nếu vượt ngưỡng (gọi API 1 lần)
    3. Trim xuống token limit
    4. Gộp history + RAG context + câu hỏi → gửi LLM
    5. Lưu history (chỉ lưu câu hỏi gốc, không lưu RAG)

Yêu cầu:
    pip install langchain-anthropic langchain-core redis
    ANTHROPIC_API_KEY=... trong .env
"""

import json
import os

import redis
import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL         = os.getenv("LLM_MODEL", "claude-haiku-4-5")
MAX_HISTORY_TOKEN = int(os.getenv("MAX_HISTORY_TOKEN", "4000"))
SESSION_TTL       = int(os.getenv("SESSION_TTL", "300"))   # 5 phút
REDIS_URL         = os.getenv("REDIS_URL", "redis://localhost:6379")
SUMMARY_THRESHOLD = int(os.getenv("SUMMARY_THRESHOLD", "10"))
MAX_RECENT        = int(os.getenv("MAX_RECENT", "6"))

SYSTEM_PROMPT = "Bạn là trợ lý hỗ trợ tra cứu tài liệu. Trả lời ngắn gọn, chính xác."

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=LLM_MODEL,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=2048,
    )

# ---------------------------------------------------------------------------
# Trim
# ---------------------------------------------------------------------------

def _trim(messages: list[BaseMessage], llm: ChatAnthropic) -> list[BaseMessage]:
    """Trim xuống MAX_HISTORY_TOKEN tokens, giữ tin mới nhất."""
    return trim_messages(
        messages,
        max_tokens=MAX_HISTORY_TOKEN,
        strategy="last",
        token_counter=llm,
        include_system=True,
        allow_partial=False,
    )

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _should_summarize(messages: list[BaseMessage]) -> bool:
    """Chỉ đếm non-system messages."""
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]
    return len(non_system) >= SUMMARY_THRESHOLD


def _compress(messages: list[BaseMessage], llm: ChatAnthropic) -> list[BaseMessage]:
    """
    Tóm tắt tin cũ, giữ lại MAX_RECENT tin gần nhất.
    Trả về: [system_msgs..., SystemMessage(summary), recent_msgs...]
    """
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    non_system  = [m for m in messages if not isinstance(m, SystemMessage)]

    to_summarize = non_system[:-MAX_RECENT]
    recent       = non_system[-MAX_RECENT:]

    if not to_summarize:
        return messages

    history_text = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in to_summarize
    )

    res = llm.invoke([HumanMessage(
        content=(
            "Tóm tắt ngắn gọn cuộc hội thoại sau, "
            "giữ thông tin quan trọng (tối đa 100 từ):\n\n"
            f"{history_text}"
        )
    )])

    log.info("history_summarized", summarized=len(to_summarize), kept=len(recent))

    summary_msg = SystemMessage(content=f"[Tóm tắt hội thoại trước]: {res.content}")
    return [*system_msgs, summary_msg, *recent]


def _prepare_history(
    messages: list[BaseMessage],
    llm: ChatAnthropic,
) -> list[BaseMessage]:
    """
    Bước 1: Summary nếu vượt ngưỡng
    Bước 2: Trim luôn chạy
    """
    if _should_summarize(messages):
        messages = _compress(messages, llm)
    return _trim(messages, llm)

# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------

def _get_redis() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)


def _redis_key(session_id: str) -> str:
    return f"chat_history:{session_id}"


def load_history(session_id: str) -> list[BaseMessage]:
    """Load history từ Redis. Trả về [] nếu chưa có hoặc hết TTL."""
    try:
        data = _get_redis().get(_redis_key(session_id))
        if not data:
            return []
        messages = []
        for m in json.loads(data):
            role, content = m["role"], m["content"]
            if role == "system":  messages.append(SystemMessage(content=content))
            elif role == "human": messages.append(HumanMessage(content=content))
            elif role == "ai":    messages.append(AIMessage(content=content))
        return messages
    except Exception as exc:
        log.warning("load_history_failed", session_id=session_id, error=str(exc))
        return []


def save_history(session_id: str, messages: list[BaseMessage]) -> None:
    """Lưu history vào Redis với TTL."""
    try:
        raw = []
        for m in messages:
            if isinstance(m, SystemMessage):  raw.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage): raw.append({"role": "human",  "content": m.content})
            elif isinstance(m, AIMessage):    raw.append({"role": "ai",     "content": m.content})
        _get_redis().setex(
            _redis_key(session_id),
            SESSION_TTL,
            json.dumps(raw, ensure_ascii=False),
        )
        log.info("history_saved", session_id=session_id, n_messages=len(raw))
    except Exception as exc:
        log.warning("save_history_failed", session_id=session_id, error=str(exc))


def clear_history(session_id: str) -> None:
    """Xóa history — dùng khi bắt đầu chat mới."""
    try:
        _get_redis().delete(_redis_key(session_id))
        log.info("history_cleared", session_id=session_id)
    except Exception as exc:
        log.warning("clear_history_failed", session_id=session_id, error=str(exc))

# ---------------------------------------------------------------------------
# Build messages: history + RAG + câu hỏi
# ---------------------------------------------------------------------------

def _build_messages(
    prepared_history: list[BaseMessage],
    user_message:     str,
    rag_chunks:       list[dict],
) -> list[BaseMessage]:
    """
    Gộp history đã chuẩn bị + RAG context + câu hỏi thành messages gửi LLM.

    Args:
        prepared_history: history đã qua summary + trim
        user_message:     câu hỏi gốc của user
        rag_chunks:       [{"page": int, "content": str}, ...]
                          truyền [] nếu không có RAG
    """
    if rag_chunks:
        rag_text = "\n\n".join(
            f"[Trang {c['page']}]: {c['content']}"
            for c in rag_chunks
        )
        final_content = (
            f"Dựa vào tài liệu sau:\n{rag_text}\n\n"
            f"Câu hỏi: {user_message}"
        )
    else:
        final_content = user_message

    return list(prepared_history) + [HumanMessage(content=final_content)]

# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------

def chat(
    session_id:   str,
    user_message: str,
    rag_chunks:   list[dict] | None = None,
) -> str:
    """
    Gửi tin nhắn và nhận phản hồi từ LLM.

    Args:
        session_id:   ID phiên hội thoại
        user_message: câu hỏi gốc của user
        rag_chunks:   [{"page": int, "content": str}] từ retriever
                      None nếu không dùng RAG
    """
    llm        = _get_llm()
    rag_chunks = rag_chunks or []

    # 1. Load history
    history = load_history(session_id)
    if not history or not isinstance(history[0], SystemMessage):
        history.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    # 2. Thêm câu hỏi gốc vào history (không kèm RAG)
    history.append(HumanMessage(content=user_message))

    # 3. Summary (nếu cần) → Trim
    prepared = _prepare_history(history, llm)

    # 4. Gộp history + RAG + câu hỏi
    messages = _build_messages(
        prepared_history=prepared,
        user_message=user_message,
        rag_chunks=rag_chunks,
    )

    log.info(
        "chat_request",
        session_id=session_id,
        history_msgs=len(prepared),
        rag_chunks=len(rag_chunks),
        summarized=_should_summarize(history),
    )

    # 5. Gọi LLM
    response   = llm.invoke(messages)
    ai_message = response.content

    # 6. Lưu history: prepared + response
    #    (lưu câu hỏi gốc, KHÔNG lưu RAG context)
    save_history(session_id, list(prepared) + [AIMessage(content=ai_message)])

    return ai_message


# ---------------------------------------------------------------------------
# Async version (FastAPI)
# ---------------------------------------------------------------------------

async def achat(
    session_id:   str,
    user_message: str,
    rag_chunks:   list[dict] | None = None,
) -> str:
    """Async version của chat()."""
    llm        = _get_llm()
    rag_chunks = rag_chunks or []

    history = load_history(session_id)
    if not history or not isinstance(history[0], SystemMessage):
        history.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    history.append(HumanMessage(content=user_message))
    prepared = _prepare_history(history, llm)
    messages = _build_messages(prepared, user_message, rag_chunks)

    response   = await llm.ainvoke(messages)
    ai_message = response.content

    save_history(session_id, list(prepared) + [AIMessage(content=ai_message)])
    return ai_message


# ---------------------------------------------------------------------------
# Agent version (tool calling + RAG)
# ---------------------------------------------------------------------------

def build_agent_with_history(tools: list, session_id: str):
    """Agent với tool calling + history + RAG."""
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate

    llm    = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_tool_calling_agent(llm.bind_tools(tools), tools, prompt)

    def run_agent(user_message: str, rag_chunks: list[dict] | None = None) -> str:
        rag_chunks = rag_chunks or []
        history    = load_history(session_id)

        if not history or not isinstance(history[0], SystemMessage):
            history.insert(0, SystemMessage(content=SYSTEM_PROMPT))

        history.append(HumanMessage(content=user_message))
        prepared = _prepare_history(history, llm)

        # Với agent: RAG context đưa vào input trực tiếp
        if rag_chunks:
            rag_text = "\n\n".join(
                f"[Trang {c['page']}]: {c['content']}" for c in rag_chunks
            )
            agent_input = f"Tài liệu tham khảo:\n{rag_text}\n\nCâu hỏi: {user_message}"
        else:
            agent_input = user_message

        result   = AgentExecutor(agent=agent, tools=tools, verbose=False).invoke({
            "input":        agent_input,
            "chat_history": prepared,
        })
        ai_reply = result["output"]

        save_history(session_id, list(prepared) + [AIMessage(content=ai_reply)])
        return ai_reply

    return run_agent