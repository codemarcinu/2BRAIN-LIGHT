from .base import BaseReceiptAgent

class LidlAgent(BaseReceiptAgent):
    def __init__(self):
        super().__init__("Lidl")

    def preprocess(self, text: str) -> str:
        # Lidl ma specyficzny format, często produkty zaczynają się od dużej litery
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_clean = line.strip()
            # Ignoruj linie z samym kodem kreskowym (częste w Lidlu na dole) or reklamami
            if "LIDL PLUS" in line_clean.upper():
                continue
            cleaned_lines.append(line_clean)
            
        return "\n".join(cleaned_lines)
