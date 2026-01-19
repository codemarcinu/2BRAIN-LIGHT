import json
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from config import ProjectConfig

logger = logging.getLogger("ReceiptCache")

@dataclass
class ProductMatch:
    name: str
    category: str
    unit: str
    confidence: float
    source: str

class ReceiptCache:
    def __init__(self, cache_file: str = None):
        self.cache_file = cache_file or str(ProjectConfig.CACHE_FILE)
        self.cache: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} items from cache")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def lookup(self, line: str, shop: Optional[str] = None) -> Optional[ProductMatch]:
        # Normalize key
        key = line.strip().upper()
        
        # Try exact match
        if key in self.cache:
            data = self.cache[key]
            return ProductMatch(**data)
            
        return None

    def update(self, line: str, match: ProductMatch, shop: Optional[str] = None):
        key = line.strip().upper()
        self.cache[key] = asdict(match)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.info("Cache saved")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
