import openai
from typing import Protocol, List
from dotenv import load_dotenv
import os
from type import EmbeddingVector
import glob
import tiktoken
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from modelconfig import OpenAIEmbeddingModel, LocalEmbeddingModel

# get api key
load_dotenv()
os.getenv("OPENAI_API_KEY")

# 토큰 수 세기
knowledge_base_path = "testdoc/**/*.md"
files = glob.glob(knowledge_base_path, recursive=True)
print(len(files))


def make_knowledge_text(files: List[str]) -> str:
    entire_knowlegde_base = ""

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            entire_knowlegde_base += f.read()
            entire_knowlegde_base += "\n\n"
    return entire_knowlegde_base


entire_knowledge_base = make_knowledge_text(files)


def return_knowledge_textlength(knowledge_base: str):
    return len(knowledge_base)


print(
    f"Total character in knowledge_base: {return_knowledge_textlength(entire_knowledge_base)}"
)


def count_token(
    knowledge_text: str, embedding_model: OpenAIEmbeddingModel | LocalEmbeddingModel
) -> int:
    encoding = tiktoken.encoding_for_model(embedding_model)
    tokens = encoding.encode(knowledge_text)
    token_count = len(tokens)
    return token_count


print(f"Total tokens: {count_token(entire_knowledge_base, 'text-embedding-3-large')}")


client = openai.OpenAI()
vectors = client.embeddings.create(model="text-embedding-3-small", input=["a", "b"])
# print(a)


class EmbeddingProvider(Protocol):
    def embed(self, texts: List[str]) -> EmbeddingVector: ...


print("끝")
