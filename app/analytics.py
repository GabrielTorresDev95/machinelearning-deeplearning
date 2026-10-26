
import pandas as pd

from sqlalchemy.orm import Session

from app.models import Produto, Venda


# ==========================================
# 1. TRANSFORMAR VENDAS EM DATAFRAME
# ==========================================

def dataframe_vendas(db: Session):

    vendas = db.query(Venda).all()

    registros = []

    for venda in vendas:

        registros.append({
            "id": venda.id,
            "produto": venda.produto.nome,
            "categoria": venda.produto.categoria,
            "quantidade": venda.quantidade,
            "preco_unitario": venda.preco_unitario,
            "total": venda.total,
            "data": venda.data
        })

    return pd.DataFrame(registros)


# ==========================================
# 2. INDICADORES DE VENDAS
# ==========================================

def indicadores_vendas(db: Session):

    df = dataframe_vendas(db)

    if df.empty:
        return {
            "faturamento_total": 0,
            "total_pedidos": 0,
            "unidades_vendidas": 0,
            "ticket_medio": 0,
            "produto_mais_vendido": None,
            "faturamento_por_categoria": {}
        }

    faturamento = float(
        df["total"].sum()
    )

    total_pedidos = len(df)

    unidades = int(
        df["quantidade"].sum()
    )

    ticket_medio = (
        faturamento / total_pedidos
        if total_pedidos > 0
        else 0
    )

    produtos = (
        df.groupby("produto")["quantidade"]
        .sum()
        .sort_values(ascending=False)
    )

    categorias = (
        df.groupby("categoria")["total"]
        .sum()
        .round(2)
        .to_dict()
    )

    return {
        "faturamento_total": round(
            faturamento, 2
        ),
        "total_pedidos": total_pedidos,
        "unidades_vendidas": unidades,
        "ticket_medio": round(
            ticket_medio, 2
        ),
        "produto_mais_vendido": str(
            produtos.index[0]
        ),
        "faturamento_por_categoria": categorias
    }


# ==========================================
# 3. ANÁLISE DE ESTOQUE
# ==========================================

def analisar_estoque(db: Session):

    produtos = db.query(Produto).all()

    resultado = []

    for produto in produtos:

        if produto.estoque == 0:
            status = "ESGOTADO"

        elif produto.estoque <= 5:
            status = "CRITICO"

        elif produto.estoque <= 15:
            status = "BAIXO"

        else:
            status = "NORMAL"

        resultado.append({
            "id": produto.id,
            "produto": produto.nome,
            "categoria": produto.categoria,
            "estoque": produto.estoque,
            "status": status
        })

    return resultado


# ==========================================
# 4. RANKING DE PRODUTOS
# ==========================================

def ranking_produtos(db: Session):

    df = dataframe_vendas(db)

    if df.empty:
        return []

    ranking = (
        df.groupby("produto")
        .agg(
            quantidade=("quantidade", "sum"),
            faturamento=("total", "sum")
        )
        .reset_index()
        .sort_values(
            "faturamento",
            ascending=False
        )
    )

    ranking["quantidade"] = (
        ranking["quantidade"].astype(int)
    )

    ranking["faturamento"] = (
        ranking["faturamento"].round(2)
    )

    return ranking.to_dict(
        orient="records"
    )
