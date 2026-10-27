import httpx
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Meu Chatbot")

class MensagemHistorico(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)

class ChatRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=4000)
    historico: list[MensagemHistorico] = Field(
        default_factory=list, max_length=6
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(dados: ChatRequest):
    mensagem = dados.mensagem.strip()
    if not mensagem:
        raise HTTPException(400, "Escreva uma mensagem.")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resposta = await client.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "qwen3:1.7b",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você se chama Le Skibidi Bill Resenha Master 1.0, ou Bill. Responda em português do Brasil, de forma direta, com tom neutro e linguagem simples. Não use emojis nem frases prontas de atendimento. Admita quando não souber. Exemplo de tom: Usuário: Qual é seu nome? Assistente: Sou o Le Skibidi Bill Resenha Master 1.0. Pode me chamar de Bill.",
                        },
                        *[item.model_dump() for item in dados.historico],{"role": "user", "content": mensagem},
                    ],
                    "stream": False,
                    "think": False,
                    "options": {
                        "num_ctx": 4096,
                        "num_predict": 512,
                    },
                },
            )
            resposta.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(504, "O modelo demorou demais para responder.")
    except httpx.RequestError:
        raise HTTPException(503, "Não foi possível conectar ao Ollama.")
    except httpx.HTTPStatusError:
        raise HTTPException(502, "O Ollama retornou um erro.")

    return {"resposta": resposta.json()["message"]["content"]}

from pathlib import Path
from fastapi.responses import FileResponse

@app.get("/", response_class=FileResponse)
def inicio():
    return FileResponse(Path(__file__).resolve().parent / "index.html")
