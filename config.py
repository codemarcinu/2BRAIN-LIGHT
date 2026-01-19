import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class ProjectConfig:
    BASE_DIR = Path(__file__).parent
    
    # Paths
    INPUTS_DIR = BASE_DIR / "inputs"
    PARAGONY_DIR = INPUTS_DIR / "paragony"
    INBOX_DIR = INPUTS_DIR / "inbox"
    ARCHIVE_DIR = BASE_DIR / "archive"
    
    # Config Files
    PRODUCT_TAXONOMY_PATH = BASE_DIR / "config/product_taxonomy.json"
    
    # AI Config
    RECEIPT_AI_PROVIDER = os.getenv("RECEIPT_AI_PROVIDER", "google") # google or ollama
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OLLAMA_RECEIPT_MODEL = os.getenv("OLLAMA_RECEIPT_MODEL", "llama3")
    
    # Vault
    OBSIDIAN_VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", INPUTS_DIR)) # Fallback to inputs if not set

    # Cache
    CACHE_FILE = BASE_DIR / "receipt_cache.json"
