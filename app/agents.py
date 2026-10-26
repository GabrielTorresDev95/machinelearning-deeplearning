
import os
import json
import logging

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.database import SessionLocal
from app.analytics import (
    indicadores_vendas,
    analisar_estoque,
    ranking_produtos
)


# ==========================================
# 1. CONFIGURAÇÕES INICIAIS
# ==========================================

load_dotenv()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# ==========================================
# 2. CONFIGURAR O OLLAMA
# ==========================================

def obter_modelo():

    usar_llm = os.getenv(
        "USE_LLM", "false"
    ).strip().lower() == "true"

    if not usar_llm:
        print("[OLLAMA] IA desativada.")
        return None

    nome_modelo = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:1b"
    )

    endereco = os.getenv(
        "OLLAMA_BASE_URL",
        "http://127.0.0.1:11434"
    )

    print(f"[OLLAMA] Modelo: {nome_modelo}")

    return ChatOllama(
        model=nome_modelo,
        base_url=endereco,
        temperature=0.2,
        num_ctx=1024,
        num_predict=256,
        keep_alive="1m",
        client_kwargs={
            "timeout": 120
        }
    )


# ==========================================
# 3. GERAR RESPOSTA COM OLLAMA
# ==========================================

def gerar_resposta(
    pergunta: str,
    dados: dict,
    instrucao: str
) -> str:

    dados_json = json.dumps(
        dados,
        ensure_ascii=False,
        indent=2,
        default=str
    )

    try:
        modelo = obter_modelo()

        if modelo is None:
            return (
                "IA desativada no arquivo .env.\n\n"
                "Dados locais:\n"
                + dados_json
            )

        mensagens = [
            SystemMessage(
                content=(
                    instrucao
                    + "\nResponda em português brasileiro."
                    + "\nSeja claro e objetivo."
                    + "\nNão invente dados empresariais."
                    + "\nSe os dados forem insuficientes, "
                      "informe essa limitação."
                )
            ),
            HumanMessage(
                content=(
                    f"Pergunta:\n{pergunta}\n\n"
                    f"Dados disponíveis:\n{dados_json}"
                )
            )
        ]

        print("[OLLAMA] Enviando pergunta...")

        resposta = modelo.invoke(mensagens)

        conteudo = resposta.content

        if isinstance(conteudo, str):
            texto = conteudo.strip()
        else:
            texto = str(conteudo).strip()

        if not texto:
            raise ValueError(
                "O modelo Ollama retornou texto vazio."
            )

        print("[OLLAMA] Resposta recebida!")

        return texto

    except Exception as erro:

        tipo = type(erro).__name__

        logger.exception(
            "Falha na geração com Ollama"
        )

        status = getattr(
            erro,
            "status_code",
            None
        )

        if tipo == "ResponseError":

            if status == 404:
                motivo = (
                    "Modelo não encontrado no Ollama. "
                    "Confira OLLAMA_MODEL no .env."
                )

            elif status == 500:
                motivo = (
                    "Erro interno do Ollama. "
                    "O modelo pode não ter conseguido "
                    "carregar ou executar."
                )

            else:
                motivo = (
                    "O servidor Ollama rejeitou "
                    "ou não conseguiu concluir "
                    "a geração."
                )

        elif tipo in (
            "ConnectError",
            "ConnectionError"
        ):
            motivo = (
                "Não foi possível conectar "
                "ao Ollama na porta 11434."
            )

        elif tipo in (
            "ReadTimeout",
            "TimeoutException"
        ):
            motivo = (
                "O modelo excedeu o tempo "
                "limite de resposta."
            )

        else:
            motivo = (
                "Erro durante a execução "
                "do modelo local."
            )

        return (
            "Não foi possível gerar a resposta "
            "com o Ollama.\n\n"
            f"Tipo: {tipo}\n"
            f"Status Ollama: {status}\n"
            f"Motivo: {motivo}\n\n"
            "O erro detalhado está no terminal "
            "do FastAPI."
        )


# ==========================================
# 4. AGENTE DE VENDAS
# ==========================================

def agente_vendas(pergunta: str) -> dict:

    print("[AGENTE VENDAS] Iniciando")

    db = SessionLocal()

    try:
        indicadores = indicadores_vendas(db)
        ranking = ranking_produtos(db)

        dados = {
            "indicadores": indicadores,
            "ranking": ranking
        }

    finally:
        db.close()

    instrucao = """
    Você é especialista em análise de vendas.

    Analise os indicadores fornecidos.

    Considere:
    1. Faturamento total.
    2. Ticket médio.
    3. Produtos mais vendidos.
    4. Categorias de maior faturamento.
    5. Recomendações estratégicas.

    Não invente valores.
    """

    resposta = gerar_resposta(
        pergunta,
        dados,
        instrucao
    )

    return {
        "agente": "vendas",
        "resposta": resposta,
        "dados": dados
    }


# ==========================================
# 5. AGENTE DE ESTOQUE
# ==========================================

def agente_estoque(pergunta: str) -> dict:

    print("[AGENTE ESTOQUE] Iniciando")

    db = SessionLocal()

    try:
        produtos = analisar_estoque(db)

        criticos = [
            produto
            for produto in produtos
            if produto["status"] in (
                "CRITICO",
                "ESGOTADO"
            )
        ]

        baixos = [
            produto
            for produto in produtos
            if produto["status"] == "BAIXO"
        ]

        dados = {
            "produtos": produtos,
            "produtos_criticos": criticos,
            "produtos_baixos": baixos,
            "total_criticos": len(criticos),
            "total_baixos": len(baixos)
        }

    finally:
        db.close()

    instrucao = """
    Você é um especialista em estoque.

    Analise:
    1. Produtos esgotados.
    2. Produtos com estoque crítico.
    3. Produtos com estoque baixo.
    4. Prioridades de reposição.
    5. Recomendações operacionais.

    Não invente quantidades ou demandas.
    """

    resposta = gerar_resposta(
        pergunta,
        dados,
        instrucao
    )

    return {
        "agente": "estoque",
        "resposta": resposta,
        "dados": dados
    }


# ==========================================
# 6. AGENTE DE RELATÓRIOS
# ==========================================

def agente_relatorios(pergunta: str) -> dict:

    print("[AGENTE RELATÓRIOS] Iniciando")

    db = SessionLocal()

    try:
        indicadores = indicadores_vendas(db)
        estoque = analisar_estoque(db)
        ranking = ranking_produtos(db)

        dados = {
            "indicadores": indicadores,
            "estoque": estoque,
            "ranking": ranking
        }

    finally:
        db.close()

    instrucao = """
    Você é um analista de negócios.

    Gere um relatório gerencial com:

    1. Resumo executivo.
    2. Faturamento.
    3. Indicadores de desempenho.
    4. Produtos em destaque.
    5. Situação do estoque.
    6. Recomendações estratégicas.
    7. Conclusão.

    Utilize somente os dados recebidos.
    """

    resposta = gerar_resposta(
        pergunta,
        dados,
        instrucao
    )

    return {
        "agente": "relatorios",
        "resposta": resposta,
        "dados": dados
    }


# ==========================================
# 7. AGENTE GERAL
# ==========================================

def agente_geral(pergunta: str) -> dict:

    print("[AGENTE GERAL] Iniciando")

    dados = {
        "contexto": (
            "Assistente inteligente SalesMind AI."
        )
    }

    instrucao = """
    Você é um assistente de inteligência
    artificial com conhecimentos gerais.

    Responda perguntas sobre:
    - Matemática
    - Física
    - História
    - Ciência
    - Tecnologia
    - Programação
    - Python
    - Machine Learning
    - Deep Learning
    - LangChain
    - LangGraph
    - FastAPI
    - Banco de dados

    Explique conceitos de forma didática.

    Quando solicitado:
    - Resolva exercícios.
    - Gere códigos.
    - Apresente exemplos.
    - Explique passo a passo.

    Não afirme que executou ações
    que não foram realizadas.
    """

    resposta = gerar_resposta(
        pergunta,
        dados,
        instrucao
    )

    return {
        "agente": "geral",
        "resposta": resposta,
        "dados": dados
    }
