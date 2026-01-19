from .base import BaseReceiptAgent
from .biedronka import BiedronkaAgent
from .lidl import LidlAgent

# Shop Mappings for canonical names
SHOP_MAPPINGS = {
    "BIEDRONKA": ["JERONIMO MARTINS", "BIEDRONKA", "BIEDR.", "JMP S.A."],
    "LIDL": ["LIDL", "LIDL SP. Z O.O.", "LIDL SKLEP"],
    "AUCHAN": ["AUCHAN", "AUCHAN POLSKA"],
    "ZABKA": ["ZABKA", "ŻABKA", "AJENT", "SKLEP SPOZYWCZY ZABKA"],
    "ROSSMANN": ["ROSSMANN", "ROSSMANN SDP"],
    "HEBE": ["JERONIMO MARTINS DROGERIE", "HEBE"],
    "CARREFOUR": ["CARREFOUR", "CARREFOUR EXPRESS", "CARREFOUR MARKET"],
    "KAUFLAND": ["KAUFLAND", "KAUFLAND POLSKA"],
    "DINO": ["DINO", "DINO POLSKA", "MARKET DINO"],
    "NETTO": ["NETTO", "NETTO SP. Z O.O."],
    "ALDI": ["ALDI", "ALDI SP. Z O.O."],
    "STOKROTKA": ["STOKROTKA", "STOKROTKA SP. Z O.O."],
    "LEWIATAN": ["LEWIATAN", "P.H.U.", "SKLEP SPOZYWCZY LEWIATAN"],
    "ORLEN": ["PKN ORLEN", "ORLEN", "STACJA PALIW ORLEN"],
    "BP": ["BP EUROPA", "STACJA PALIW BP"],
    "SHELL": ["SHELL", "SHELL POLSKA"],
    "CIRCLE_K": ["CIRCLE K", "STATOIL"],
    "MCDONALDS": ["MCDONALD'S", "MCDONALDS", "RESTAURACJA MCDONALDS"],
    "KFC": ["KFC", "AMREST"],
    "LEROY_MERLIN": ["LEROY MERLIN", "LEROY-MERLIN"],
    "CASTORAMA": ["CASTORAMA", "CASTORAMA POLSKA"],
    "IKEA": ["IKEA", "IKEA RETAIL"]
}

SHOP_AGENTS = {
    "BIEDRONKA": BiedronkaAgent,
    "LIDL": LidlAgent,
    # Add other specialized agents here if needed, otherwise fallback to base
}

def detect_shop(text: str) -> str:
    """
    Wykrywa sklep w tekście OCR używając mapowania.
    Zwraca kanoniczną nazwę sklepu (np. 'BIEDRONKA') lub 'Sklep' jeśli nie znaleziono.
    """
    text_upper = text.upper()
    
    for canonical_name, aliases in SHOP_MAPPINGS.items():
        for alias in aliases:
            if alias in text_upper:
                return canonical_name
                
    return "Sklep"

def get_agent(shop_name: str) -> BaseReceiptAgent:
    """Fabryka agentów dla sklepów."""
    agent_cls = SHOP_AGENTS.get(shop_name.upper()) # Normalize to upper key
    if agent_cls:
        return agent_cls()
    return BiedronkaAgent() # Default fallback, or could use a GenericAgent
