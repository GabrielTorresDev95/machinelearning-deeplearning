
import logging
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import (
    get_db,
    criar_tabelas
)

from app.models import Produto, Venda

from app.schemas import (
    ProdutoCriar,
    ProdutoResposta,
    VendaCriar,
    PerguntaAgente
)

from app.analytics import (
    indicadores_vendas,
    analisar_estoque,
    ranking_produtos
)

from app.graph import executar_grafo


# ========================================
# INICIALIZAÇÃO
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    criar_tabelas()

    yield


app = FastAPI(
    title="SalesMind AI",
    description=(
        "Sistema Multiagente de Análise "
        "de Vendas com LangGraph, "
        "Pandas, SQL e Inteligência Artificial"
    ),
    version="1.0.0",
    lifespan=lifespan
)


# ========================================
# ROTA PRINCIPAL
# ========================================

@app.get("/")
def inicio():

    return {
        "sistema": "SalesMind AI",
        "status": "online",
        "documentacao": "/docs"
    }


# ========================================
# CADASTRAR PRODUTO
# ========================================

@app.post(
    "/produtos",
    response_model=ProdutoResposta,
    status_code=201
)
def cadastrar_produto(
    dados: ProdutoCriar,
    db: Session = Depends(get_db)
):

    produto = Produto(
        nome=dados.nome,
        categoria=dados.categoria,
        preco=dados.preco,
        estoque=dados.estoque
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    return produto


# ========================================
# LISTAR PRODUTOS
# ========================================

@app.get(
    "/produtos",
    response_model=list[ProdutoResposta]
)
def listar_produtos(
    db: Session = Depends(get_db)
):

    return db.query(Produto).all()


# ========================================
# CONSULTAR PRODUTO
# ========================================

@app.get(
    "/produtos/{produto_id}",
    response_model=ProdutoResposta
)
def consultar_produto(
    produto_id: int,
    db: Session = Depends(get_db)
):

    produto = db.get(
        Produto,
        produto_id
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    return produto


# ========================================
# REGISTRAR VENDA
# ========================================

@app.post(
    "/vendas",
    status_code=201
)
def registrar_venda(
    dados: VendaCriar,
    db: Session = Depends(get_db)
):

    produto = db.get(
        Produto,
        dados.produto_id
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    if produto.estoque < dados.quantidade:
        raise HTTPException(
            status_code=400,
            detail="Estoque insuficiente"
        )

    total = round(
        produto.preco * dados.quantidade,
        2
    )

    venda = Venda(
        produto_id=produto.id,
        quantidade=dados.quantidade,
        preco_unitario=produto.preco,
        total=total
    )

    produto.estoque -= dados.quantidade

    db.add(venda)
    db.commit()
    db.refresh(venda)

    return {
        "mensagem": "Venda registrada",
        "venda_id": venda.id,
        "produto": produto.nome,
        "quantidade": venda.quantidade,
        "total": venda.total,
        "estoque_restante": produto.estoque
    }


# ========================================
# INDICADORES DE VENDAS
# ========================================

@app.get("/indicadores")
def consultar_indicadores(
    db: Session = Depends(get_db)
):

    return indicadores_vendas(db)


# ========================================
# ESTOQUE
# ========================================

@app.get("/estoque")
def consultar_estoque(
    db: Session = Depends(get_db)
):

    return analisar_estoque(db)


# ========================================
# RANKING DE PRODUTOS
# ========================================

@app.get("/ranking")
def consultar_ranking(
    db: Session = Depends(get_db)
):

    return ranking_produtos(db)


# ========================================
# EXECUTAR AGENTES LANGGRAPH
# ========================================


# ==========================================
# EXECUTAR AGENTES COM LANGGRAPH
# ==========================================

logger = logging.getLogger(__name__)


@app.post("/agentes/perguntar")
def perguntar_agentes(dados: PerguntaAgente):

    try:
        resultado = executar_grafo(
            pergunta=dados.pergunta,
            thread_id=dados.thread_id
        )

        return resultado

    except Exception:
        logger.exception(
            "Erro interno ao executar LangGraph"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível processar "
                "a solicitação. Consulte os logs."
            )
        )

