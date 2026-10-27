import os
import re
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
PERSONA_FILE = Path(os.getenv("PERSONA_FILE", BASE / "personas" / "bill.txt"))
SYSTEM_PROMPT = PERSONA_FILE.read_text(encoding="utf-8").strip()

BACKENDS = [(os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
             os.getenv("MODEL", "qwen3:1.7b"))]
if os.getenv("FALLBACK_URL"):
    BACKENDS.append((os.getenv("FALLBACK_URL"),
                     os.getenv("FALLBACK_MODEL", "qwen3:1.7b")))

NUM_CTX = int(os.getenv("NUM_CTX", "4096"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "512"))
TIMEOUT = httpx.Timeout(120.0, connect=3.0)
ESTADO_RE = re.compile(r"^\s*\[estado:\s*([\w-]+)\]\s*", re.IGNORECASE)

app = FastAPI(title="Local Chatbot")


class MensagemHistorico(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=4000)
    historico: list[MensagemHistorico] = Field(default_factory=list, max_length=6)


@app.get("/health")
def health():
    return {"status": "ok", "persona": PERSONA_FILE.stem}


@app.post("/chat")
async def chat(dados: ChatRequest):
    mensagem = dados.mensagem.strip()
    if not mensagem:
        raise HTTPException(400, "Escreva uma mensagem.")
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT},
                 *[m.model_dump() for m in dados.historico],
                 {"role": "user", "content": mensagem}]
    erro = (503, "Não foi possível conectar ao Ollama.")
    for url, modelo in BACKENDS:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.post(f"{url}/api/chat", json={
                    "model": modelo, "messages": mensagens,
                    "stream": False, "think": False,
                    "options": {"num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}})
                r.raise_for_status()
            texto = r.json()["message"]["content"]
            break
        except httpx.TimeoutException:
            erro = (504, "O modelo demorou demais para responder.")
        except httpx.RequestError:
            erro = (503, "Não foi possível conectar ao Ollama.")
        except httpx.HTTPStatusError:
            erro = (502, "O Ollama retornou um erro.")
    else:
        raise HTTPException(*erro)

    estado = None
    m = ESTADO_RE.match(texto)
    if m:
        estado = m.group(1).lower()
        texto = texto[m.end():]
    return {"resposta": texto, "estado": estado}


@app.get("/", response_class=FileResponse)
def inicio():
    return FileResponse(BASE / "index.html")
