
import re
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.agents import (
    agente_vendas,
    agente_estoque,
    agente_relatorios,
    agente_geral
)


# ========================================
# 1. ESTADO DO LANGGRAPH
# ========================================

class EstadoAgentes(TypedDict):
    pergunta: str
    categoria: str
    agente: str
    resposta: str
    dados: dict


# ========================================
# 2. CLASSIFICADOR
# ========================================

def classificador(estado: EstadoAgentes):

    pergunta = estado["pergunta"].lower()

    if re.search(
        r"relat[oó]rio|resumo executivo|"
        r"an[aá]lise geral|vis[aã]o geral",
        pergunta
    ):
        categoria = "relatorios"

    elif re.search(
        r"estoque|reposi[cç][aã]o|esgotado",
        pergunta
    ):
        categoria = "estoque"

    elif re.search(
        r"venda|faturamento|receita|"
        r"ticket m[eé]dio|ranking",
        pergunta
    ):
        categoria = "vendas"

    else:
        categoria = "geral"

    print(f"[CLASSIFICADOR] {categoria}")

    return {"categoria": categoria}


# ========================================
# 3. NÓS DOS AGENTES
# ========================================

def executar_vendas(estado: EstadoAgentes):
    return agente_vendas(estado["pergunta"])


def executar_estoque(estado: EstadoAgentes):
    return agente_estoque(estado["pergunta"])


def executar_relatorios(estado: EstadoAgentes):
    return agente_relatorios(estado["pergunta"])


def executar_geral(estado: EstadoAgentes):
    return agente_geral(estado["pergunta"])


# ========================================
# 4. SELECIONAR PRÓXIMO NÓ
# ========================================

def selecionar_agente(
    estado: EstadoAgentes
) -> Literal[
    "vendas", "estoque", "relatorios", "geral"
]:

    return estado["categoria"]


# ========================================
# 5. CONSTRUIR GRAFO
# ========================================

builder = StateGraph(EstadoAgentes)

builder.add_node("classificador", classificador)
builder.add_node("vendas", executar_vendas)
builder.add_node("estoque", executar_estoque)
builder.add_node("relatorios", executar_relatorios)
builder.add_node("geral", executar_geral)

# O classificador é sempre o primeiro nó
builder.add_edge(START, "classificador")

# Executa o agente escolhido pelo classificador
builder.add_conditional_edges(
    "classificador",
    selecionar_agente,
    {
        "vendas": "vendas",
        "estoque": "estoque",
        "relatorios": "relatorios",
        "geral": "geral"
    }
)

builder.add_edge("vendas", END)
builder.add_edge("estoque", END)
builder.add_edge("relatorios", END)
builder.add_edge("geral", END)

memoria = InMemorySaver()

aplicacao = builder.compile(
    checkpointer=memoria
)


# ========================================
# 6. EXECUTAR GRAFO
# ========================================

def executar_grafo(
    pergunta: str,
    thread_id: str = "aluno-001"
):

    configuracao = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    estado_inicial = {
        "pergunta": pergunta,
        "categoria": "",
        "agente": "",
        "resposta": "",
        "dados": {}
    }

    # Executa todos os nós até END.
    resultado = aplicacao.invoke(
        estado_inicial,
        config=configuracao
    )

    print("[LANGGRAPH] Estado final:", resultado)

    # Impede que um fluxo incompleto retorne
    # 200 OK com resposta vazia.
    if not resultado.get("agente") or not resultado.get("resposta"):
        raise RuntimeError(
            "O LangGraph terminou sem resposta do agente. "
            "Verifique o roteamento e as funções em agents.py."
        )

    return {
        "pergunta": pergunta,
        "categoria": resultado["categoria"],
        "agente": resultado["agente"],
        "resposta": resultado["resposta"],
        "dados": resultado["dados"],
        "thread_id": thread_id
    }
