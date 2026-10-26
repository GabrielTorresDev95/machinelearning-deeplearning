
from app.database import (
    criar_tabelas,
    SessionLocal
)

from app.models import Produto, Venda


def popular_banco():

    criar_tabelas()

    db = SessionLocal()

    try:
        if db.query(Produto).first():
            print("Banco já possui produtos.")
            return

        produtos = [
            Produto(
                nome="Notebook",
                categoria="Informática",
                preco=3500,
                estoque=20
            ),
            Produto(
                nome="Mouse Gamer",
                categoria="Periféricos",
                preco=150,
                estoque=40
            ),
            Produto(
                nome="Teclado Mecânico",
                categoria="Periféricos",
                preco=300,
                estoque=12
            ),
            Produto(
                nome="Monitor 24",
                categoria="Informática",
                preco=950,
                estoque=8
            ),
            Produto(
                nome="Headset",
                categoria="Áudio",
                preco=250,
                estoque=5
            ),
            Produto(
                nome="Webcam",
                categoria="Acessórios",
                preco=200,
                estoque=3
            )
        ]

        db.add_all(produtos)
        db.flush()

        vendas_exemplo = [
            (0, 3),
            (1, 10),
            (2, 4),
            (3, 2),
            (4, 3),
            (1, 5),
            (0, 2),
            (2, 3)
        ]

        for indice, quantidade in vendas_exemplo:

            produto = produtos[indice]

            total = (
                produto.preco * quantidade
            )

            venda = Venda(
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=produto.preco,
                total=total
            )

            produto.estoque -= quantidade

            db.add(venda)

        db.commit()

        print("Banco populado com sucesso!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    popular_banco()
