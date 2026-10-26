
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)


# ======================================
# SCHEMA PARA CADASTRAR PRODUTOS
# ======================================

class ProdutoCriar(BaseModel):

    nome: str = Field(min_length=2)

    categoria: str = Field(min_length=2)

    preco: float = Field(gt=0)

    estoque: int = Field(ge=0)


# ======================================
# SCHEMA PARA RETORNAR PRODUTOS
# ======================================

class ProdutoResposta(ProdutoCriar):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


# ======================================
# SCHEMA PARA REGISTRAR VENDAS
# ======================================

class VendaCriar(BaseModel):

    produto_id: int = Field(gt=0)

    quantidade: int = Field(gt=0)


# ======================================
# SCHEMA PARA PERGUNTAS DOS AGENTES
# ======================================

class PerguntaAgente(BaseModel):

    pergunta: str = Field(min_length=3)

    thread_id: str = "aluno-001"
