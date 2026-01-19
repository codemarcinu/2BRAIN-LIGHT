import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("TaxonomyGuard")

class TaxonomyGuard:
    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = taxonomy_path
        self.ocr_map: Dict[str, Dict] = {}
        self.ocr_patterns: List[str] = []
        self._load_taxonomy()

    def _load_taxonomy(self):
        try:
            with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mappings = data.get('mappings', [])
                
                # Sort by length of OCR pattern descending to match longest execution first
                mappings.sort(key=lambda x: len(x['ocr']), reverse=True)
                
                for item in mappings:
                    ocr_key = item['ocr'].upper()
                    self.ocr_map[ocr_key] = item
                    self.ocr_patterns.append(ocr_key)
                    
            logger.info(f"Loaded {len(self.ocr_patterns)} taxonomy patterns")
        except Exception as e:
            logger.error(f"Failed to load taxonomy from {self.taxonomy_path}: {e}")
            self.ocr_map = {}
            self.ocr_patterns = []

    def get_metadata(self, ocr_text: str) -> Optional[Dict]:
        return self.ocr_map.get(ocr_text.upper())
