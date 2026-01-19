from abc import ABC, abstractmethod
import re
from typing import List

class BaseReceiptAgent(ABC):
    def __init__(self, shop_name: str = "Base"):
        self.shop_name = shop_name

    @abstractmethod
    def preprocess(self, text: str) -> str:
        """Czyszczenie specyficzne dla sklepu."""
        pass

    def detect_dates(self, text: str) -> List[str]:
        # Common date formats: YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY
        patterns = [
            r'\b(\d{4})[-./](\d{2})[-./](\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{2})[-./](\d{2})[-./](\d{4})\b',  # DD-MM-YYYY
        ]
        found = []
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                # Normalize to YYYY-MM-DD
                if len(m[0]) == 4: # YYYY-MM-DD
                    found.append(f"{m[0]}-{m[1]}-{m[2]}")
                else: # DD-MM-YYYY
                    found.append(f"{m[2]}-{m[1]}-{m[0]}")
        return sorted(list(set(found)))
