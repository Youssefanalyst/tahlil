from __future__ import annotations
import argparse
import os
import re
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from config import settings


def build_llm() -> ChatOpenAI:
    # Ensure OpenRouter env mapping exists (also done in config)
    if settings.openrouter_api_key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    if settings.openrouter_base_url:
        os.environ.setdefault("OPENAI_API_BASE", settings.openrouter_base_url)

    # langchain-openai accepts base_url or openai_api_base depending on version
    try:
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
            base_url=settings.openrouter_base_url,
        )
    except TypeError:
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
            openai_api_base=settings.openrouter_base_url,  # fallback for older versions
        )

def build_rag_pipeline():
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vs = FAISS.load_local(settings.index_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vs.as_retriever(search_kwargs={"k": settings.k_retrieval})

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful RAG assistant. Answer based ONLY on the provided context. If unsure, say you don't know. Keep answers concise and respond in English. Never include chain-of-thought or reasoning blocks."),
        ("human", "Question: {question}\n\nContext:\n{context}"),
    ])

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    llm = build_llm()

    def strip_think(text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"```(thought|think|reasoning)[\s\S]*?```", "", text, flags=re.IGNORECASE)
        return text.strip()
    def build_input(inp: dict) -> dict:
        q = inp.get("question", "")
        extra = inp.get("extra", "") or ""
        docs = retriever.invoke(q)
        ctx = format_docs(docs)
        if extra.strip():
            ctx = extra.strip() + "\n\n" + ctx
        return {"context": ctx, "question": q}

    chain = RunnableLambda(build_input) | prompt | llm | StrOutputParser() | RunnableLambda(strip_think)

    return chain, retriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions over your ingested data")
    parser.add_argument("-q", "--query", required=True, help="Your question")
    parser.add_argument("--extra", default="", help="Optional extra context text to prepend to retrieved context")
    args = parser.parse_args()

    chain, retriever = build_rag_pipeline()
    answer = chain.invoke({"question": args.query, "extra": args.extra})

    print("\n=== Answer ===\n")
    print(answer)

    # Show top-k sources for transparency (LCEL retrievers are Runnables)
    try:
        docs = retriever.invoke(args.query)
    except AttributeError:
        # Fallback for very old retriever interface
        docs = []
    print("\n=== Sources ===\n")
    for i, d in enumerate(docs, 1):
        print(f"[{i}] {d.metadata.get('source', 'unknown')}")


if __name__ == "__main__":
    main()
