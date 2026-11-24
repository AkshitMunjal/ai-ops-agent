import os

from dotenv import load_dotenv

load_dotenv()

# The embedding model turns text into a list of numbers.
# openai/text-embedding-3-small gives 1536 numbers per text.
EMBEDDING_SIZE = 1536

DEFAULT_VECTOR_URL = "postgresql://aiops:aiops@127.0.0.1:5433/aiops_vectors"


def get_vector_url():
    return os.getenv("VECTOR_DATABASE_URL", DEFAULT_VECTOR_URL)


def get_embedding_model():
    return os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
