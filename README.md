# Local Chatbot — Personas e inferência híbrida

Chatbot web experimental com **Python/FastAPI**, **Ollama** e uma interface que adapta sua identidade visual à persona carregada. O projeto começou como um assistente chamado Bill, executado em CPU, e evoluiu para uma arquitetura com modelos alternativos e personagens configuráveis.

> **Projeto independente e não oficial.** A persona Johnny Silverhand é inspirada em *Cyberpunk 2077*. Consulte a seção [Direitos autorais e atribuição](#direitos-autorais-e-atribuição) antes de reutilizar esse material.

## Etapa atual: personas e execução híbrida

O servidor Ubuntu hospeda a aplicação web e orquestra as consultas aos modelos:

~~~mermaid
flowchart TD
    A["Navegador · interface por persona"] --> B["FastAPI · /chat"]
    B -->|"Backend principal"| C["Ollama no Windows · Qwen3 14B · GPU"]
    B -->|"Fallback em caso de falha"| D["Ollama no Ubuntu · Qwen3 4B Instruct · CPU"]
~~~

Essa é a **configuração usada no desenvolvimento**, não uma exigência para instalar o projeto. É possível executar tudo em uma única máquina.

- **Persona:** texto de sistema carregado de um arquivo em `personas/` ou de outro caminho definido por `PERSONA_FILE`.
- **Interface:** tema, apresentação e sugestões de conversa adaptados à persona informada pelo endpoint `/health`.
- **Roteamento:** o backend tenta o Ollama principal; em caso de falha ou tempo excedido, tenta o modelo de fallback, quando configurado.
- **Transparência:** a resposta da API inclui o modelo que respondeu e, quando identificado, o estado da persona.
- **Histórico:** as últimas três trocas de mensagens ficam no navegador durante a sessão.

### Personas disponíveis

| Persona | Arquivo no repositório | Experiência visual |
| --- | --- | --- |
| Bill | `personas/bill.txt` | Estilo minimalista, tons frios |
| Johnny Silverhand | `personas/johnny.txt` | Estética inspirada em Night City, vermelho e contrastes fortes |

A persona ativa é escolhida no **backend**, pelo caminho de `PERSONA_FILE`. A interface acompanha essa escolha ao carregar a página; **não há, por enquanto, um seletor de personagens em tempo real**.

## Tecnologias

- Python 3.10+, FastAPI, Uvicorn, Pydantic e HTTPX
- HTML, CSS e JavaScript, sem framework de interface
- Ollama e modelos da família Qwen3
- Linux/Ubuntu e `systemd` para serviço contínuo
- Tailscale para conectividade privada entre servidor, Windows e clientes

## Organização do projeto

| Caminho | Papel |
| --- | --- |
| `main.py` | Rotas FastAPI, prompt de sistema, escolha do backend e fallback |
| `index.html` | Interface e apresentação por persona |
| `personas/bill.txt` | Instruções da persona Bill |
| `personas/johnny.txt` | Instruções da persona Johnny Silverhand |
| `requirements.txt` | Dependências Python |
| `deploy/` | Recursos de implantação |
| `docs/` | Documentação e registros visuais |

A imagem antiga em `docs/` registra uma etapa anterior da interface; a interface atual possui temas por persona.

## Executando localmente

Requisitos: **Python 3.10 ou superior** e **Ollama em execução**, com um modelo compatível instalado.

1. Instale um modelo leve para experimentar:

   ~~~bash
   ollama pull qwen3:4b-instruct
   ~~~

2. Na pasta do repositório, prepare o Python:

   ~~~bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ~~~

3. Configure as variáveis no terminal em que iniciará o backend:

   ~~~bash
   export OLLAMA_URL=http://127.0.0.1:11434
   export MODEL=qwen3:4b-instruct
   export PERSONA_FILE=personas/bill.txt
   ~~~

4. Inicie a aplicação:

   ~~~bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8001
   ~~~

5. Acesse a interface em http://127.0.0.1:8001 ou a documentação da API em http://127.0.0.1:8001/docs.

**Atenção:** o `main.py` lê variáveis de ambiente. Um arquivo `.env` isolado não é carregado automaticamente; use `export`, um gerenciador de ambiente ou a configuração `EnvironmentFile` do serviço `systemd`.

### Configuração com modelo principal e fallback

Exemplo conceitual para um servidor Ubuntu conectado ao Windows por uma rede privada:

~~~dotenv
PERSONA_FILE=/caminho/do/projeto/personas/johnny.txt
OLLAMA_URL=http://IP_PRIVADO_DO_WINDOWS:11434
MODEL=qwen3:14b
FALLBACK_URL=http://127.0.0.1:11434
FALLBACK_MODEL=qwen3:4b-instruct
NUM_CTX=4096
NUM_PREDICT=512
~~~

- O primeiro par, `OLLAMA_URL` e `MODEL`, define o **backend preferencial**.
- O segundo par, `FALLBACK_URL` e `FALLBACK_MODEL`, só é usado quando há uma falha no principal.
- A ausência de `FALLBACK_URL` desativa o fallback.
- O Ollama do Windows precisa estar disponível na rede privada para que o modelo 14B seja usado.
- A aplicação pode continuar respondendo com o 4B no Ubuntu quando o Ollama do Windows estiver indisponível, desde que o serviço local de Ollama esteja ativo.

Ao alterar arquivos, modelos ou variáveis de ambiente na implantação com `systemd`, reinicie o **serviço da aplicação correspondente** para que o processo carregue a nova configuração. Consulte os arquivos e instruções em `deploy/` para adequar os nomes e caminhos à sua instalação.

## Endpoints

| Método | Rota | Resultado |
| --- | --- | --- |
| `GET` | `/` | Interface web |
| `GET` | `/health` | Estado do serviço e nome da persona ativa |
| `POST` | `/chat` | Recebe mensagem/histórico e retorna resposta, estado e modelo |
| `GET` | `/docs` | Documentação interativa do FastAPI |

Exemplo de consulta:

~~~bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem":"Olá!"}'
~~~

A rota `/chat` **exige POST**. Abrir esse endereço diretamente na barra do navegador envia GET e, portanto, não inicia uma conversa.

## Histórico: primeira versão com Bill

A primeira etapa utilizava o **Qwen3 1.7B em CPU** numa VM ARM da Oracle Cloud, com quatro núcleos ARM Neoverse-N1 e aproximadamente 24 GB de RAM.

| Medida exploratória | Resultado da primeira etapa |
| --- | --- |
| Modelo | Qwen3 1.7B |
| Arquivo do modelo | Aproximadamente 1,4 GB |
| Tamanho carregado informado pelo Ollama | Aproximadamente 1,9 GB |
| Velocidade em dois testes curtos | 21–23 tokens/s |

Esses números são registros históricos, **não benchmarks da arquitetura atual**. A evolução do projeto acrescentou modelos maiores, fallback e apresentação orientada por persona.

## Limitações e segurança

- O histórico é temporário: atualizar ou fechar a página remove a conversa local.
- O backend recebe somente uma parte limitada do histórico recente; isso não garante que toda conversa caiba no contexto.
- As respostas chegam após a geração completa, sem streaming de tokens na interface.
- Os modelos podem alucinar, produzir texto de raciocínio em vez da resposta final ou desobedecer ao formato solicitado; modelos *instruct* podem ajudar, mas não eliminam esse risco.
- **A API não possui autenticação própria.** Mantenha o acesso restrito a uma rede privada ou acrescente autenticação e HTTPS antes de qualquer exposição pública.
- Não publique senhas, tokens, endereços sensíveis ou arquivos de ambiente reais no repositório.

A execução por Ollama não utiliza uma API externa cobrada por token; os custos de energia, hardware, hospedagem e rede dependem do ambiente escolhido.

## Direitos autorais e atribuição

> **AVISO DE PROPRIEDADE INTELECTUAL — JOHNNY SILVERHAND**
>
> **Johnny Silverhand, conforme representado em *Cyberpunk 2077*, integra propriedade intelectual protegida da CD PROJEKT RED e/ou dos respectivos titulares e licenciadores de direitos.** O personagem **não foi criado por este projeto**, e nenhum direito sobre ele é reivindicado aqui.
>
> *Cyberpunk 2077* e suas marcas, personagens, elementos narrativos e visuais pertencem aos respectivos detentores de direitos. **Este é um projeto de fã, independente, não oficial, sem afiliação, patrocínio ou endosso da CD PROJEKT RED.**

A utilização da persona Johnny Silverhand serve apenas para estudo e experimentação com interfaces e modelos de linguagem. Consulte as [diretrizes oficiais da CD PROJEKT RED para conteúdo de fãs](https://www.cdprojektred.com/pt-br/fan-content).

A licença do código deste repositório, quando aplicável, **não concede direitos sobre Johnny Silverhand, *Cyberpunk 2077* ou marcas e conteúdos de terceiros**.

## Próximos passos

- Seleção de personas sem reiniciar o serviço.
- Respostas progressivas (streaming).
- Testes automatizados do backend e do mecanismo de fallback.
- Melhor controle do tamanho do histórico e do contexto.
- Comparações reproduzíveis entre modelos, com métricas de qualidade e latência.
