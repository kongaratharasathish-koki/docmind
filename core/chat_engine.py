# core/chat_engine.py
#
# Owns the LangChain conversational chain.
# Decoupled from Streamlit so it can be tested independently or swapped
# for a different LLM without touching the UI layer.

from __future__ import annotations

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI

import config


# In-process cache: (vectorstore hash) -> chain. Re-using the same chain
# across chat turns avoids re-instantiating the Gemini client and the
# memory object on every request. Memory is rebuilt per request by the
# router from session history anyway, so a cached chain template is safe.
_chain_cache: "dict[str, ConversationalRetrievalChain]" = {}


def _chain_cache_key(vectorstore) -> str:
    """Deterministic key derived from the vectorstore's docmind hash.

    Falls back to object id() when the hash attribute is missing
    (e.g. in unit tests with fake vectorstores).
    """
    h = getattr(vectorstore, "_docmind_hash", None)
    if h:
        return f"hash:{h}"
    return f"id:{id(vectorstore)}"


def invalidate_chain_cache(vectorstore=None) -> None:
    """Drop cached chains. If vectorstore is given, only drop that one.

    Call from upload routes after they invalidate the vectorstore cache.
    Without an argument, clears the entire cache.
    """
    global _chain_cache
    if vectorstore is None:
        _chain_cache = {}
        return
    key = _chain_cache_key(vectorstore)
    _chain_cache.pop(key, None)


def build_chat_engine(retriever) -> ConversationalRetrievalChain:
    """
    Build a ConversationalRetrievalChain from a retriever.
    Legacy path — used when no collection is selected.
    """
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
    )
    return chain


def create_conversation_chain(vectorstore) -> ConversationalRetrievalChain:
    """
    Build a ConversationalRetrievalChain from an existing vector store.

    The chain template (LLM + retriever) is cached by vectorstore hash so
    successive chat turns on the same collection don't re-instantiate the
    Gemini client. The caller is expected to rebuild memory from session
    history before invoking, so the cached template's memory is unused.
    """
    key = _chain_cache_key(vectorstore)
    cached = _chain_cache.get(key)
    if cached is not None:
        return cached

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": config.TOP_K_DOCS},
    )

    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
    )

    _chain_cache[key] = chain
    # Bound the cache: a typical workload has tens of active collections,
    # so 256 is plenty of headroom. Each entry holds one LLM client.
    if len(_chain_cache) > 256:
        # Drop an arbitrary old entry. dicts preserve insertion order in
        # CPython 3.7+ so the first key is the oldest.
        _chain_cache.pop(next(iter(_chain_cache)))
    return chain


def ask(chain: ConversationalRetrievalChain, question: str) -> dict:
    """
    Send a question through the chain and return the full response dict.

    Response dict contains:
        "answer"           — the LLM's answer string
        "source_documents" — list of Document objects used as context

    Keeping this thin wrapper means we can add retry logic, logging, or
    latency tracking here without touching app.py.
    """
    return chain.invoke({"question": question})


def rebuild_memory_from_messages(chain: ConversationalRetrievalChain, messages: list) -> ConversationalRetrievalChain:
    """
    Clear existing memory and rebuild ConversationBufferMemory from stored messages.

    Args:
        chain: Existing ConversationalRetrievalChain with a ConversationBufferMemory
        messages: List of message dicts with "role" and "content" keys

    Returns:
        The same chain with memory rebuilt from the provided messages
    """
    if not chain or not chain.memory:
        return chain

    chain.memory.clear()

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            chain.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            chain.memory.chat_memory.add_ai_message(content)

    return chain
