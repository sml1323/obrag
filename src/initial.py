import openai
from typing import Protocol, List
from dotenv import load_dotenv
import os
from type import EmbeddingVector
import glob
import tiktoken

# get api key
load_dotenv()
os.getenv("OPENAI_API_KEY")

# 토큰 수 세기
knowledge_base_path = "testdoc/**/*.md"
files = glob.glob(knowledge_base_path, recursive=True)
print(len(files))

entire_knowlegde_base = ""

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        entire_knowlegde_base += f.read()
        entire_knowlegde_base += "\n\n"

print(f"Total character in knowledge_base: {len(entire_knowlegde_base)}")
encoding = tiktoken.encoding_for_model("text-embedding-3-large")
tokens = encoding.encode(entire_knowlegde_base)
token_count = len(tokens)
print(f"Total tokens: {token_count}")


client = openai.OpenAI()
vectors = client.embeddings.create(model="text-embedding-3-small", input=["a", "b"])
# print(a)


class EmbeddingProvider(Protocol):
    def embed(self, texts: List[str]) -> EmbeddingVector: ...


print("끝")
