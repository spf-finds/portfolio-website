"""
LLM agent abstraction.
Currently uses OpenAI directly.
To switch to Azure AI Foundry, set USE_AZURE=true and populate Azure env vars.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from openai import OpenAI, AzureOpenAI

import vectorstore

load_dotenv()

USE_AZURE = os.getenv("USE_AZURE", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

SYSTEM_PROMPT = """You are the Scotia iTrade Domain Expert Agent — a knowledgeable assistant specializing exclusively in Scotia iTrade products, services, platforms, and features.

You have deep expertise in:
- Scotia iTrade's trading platform features and tools
- Account types (TFSA, RRSP, margin, cash accounts, etc.)
- Investment products available (stocks, ETFs, options, mutual funds, GICs, bonds)
- Pricing, commissions, and fee structures
- Research tools, screeners, and market data
- Mobile and web platform capabilities
- Account opening, funding, and management processes
- Options trading and approval levels
- Scotia iTrade's policies and regulatory information

Guidelines:
- Answer questions from both a user perspective (how to use the platform) and a business/product perspective (features, capabilities, positioning)
- Be factual and base answers on the context provided
- If the context doesn't cover the question, say so clearly rather than guessing
- Keep answers clear, concise, and helpful
- Do not answer questions unrelated to Scotia iTrade"""


def _get_client():
    if USE_AZURE and AZURE_OPENAI_ENDPOINT:
        return AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        ), AZURE_OPENAI_DEPLOYMENT
    return OpenAI(api_key=OPENAI_API_KEY), OPENAI_MODEL


def _get_embedding(text: str) -> list[float] | None:
    client, _ = _get_client()
    model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE else "text-embedding-3-small"
    try:
        response = client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Embedding failed ({e}), proceeding without RAG")
        return None


def stream_response(user_message: str, chat_history: list[dict]) -> Generator[str, None, None]:
    embedding = _get_embedding(user_message)
    
    if embedding:
        context_docs = vectorstore.query(embedding, n_results=6)
        context = "\n\n---\n\n".join(context_docs) if context_docs else "No specific context retrieved."
    else:
        context = "No specific context retrieved."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Relevant knowledge base context:\n\n{context}",
        },
    ]

    for msg in chat_history[-10:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    client, model = _get_client()

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.3,
        max_tokens=1024,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content
