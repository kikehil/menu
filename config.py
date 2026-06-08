from dotenv import load_dotenv
import os

load_dotenv()

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "mi-instancia")

SAT_RFC = os.getenv("SAT_RFC", "")
SAT_EFIRMA_CER_PATH = os.getenv("SAT_EFIRMA_CER_PATH", "")
SAT_EFIRMA_KEY_PATH = os.getenv("SAT_EFIRMA_KEY_PATH", "")
SAT_EFIRMA_PASSWORD = os.getenv("SAT_EFIRMA_PASSWORD", "")

AUTHORIZED_NUMBERS = [
    n.strip() for n in os.getenv("AUTHORIZED_NUMBERS", "").split(",") if n.strip()
]

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")
