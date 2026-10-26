
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime
)

from sqlalchemy.orm import relationship

from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    categoria = Column(String(100), nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False, default=0)

    vendas = relationship(
        "Venda",
        back_populates="produto"
    )


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)

    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False
    )

    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    data = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    produto = relationship(
        "Produto",
        back_populates="vendas"
    )
