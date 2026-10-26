import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

chave = os.getenv("OPENAI_API_KEY")

if not chave:
    raise ValueError("Chave OpenAI não encontrada no .env")

print("Chave carregada com sucesso!")

modelo = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0.2
)

resposta = modelo.invoke(
    "Explique o que é LangGraph em duas frases."
)

print(resposta.content)