from .base import BaseReceiptAgent
import re

class BiedronkaAgent(BaseReceiptAgent):
    def __init__(self):
        super().__init__("Biedronka")

    def preprocess(self, text: str) -> str:
        # Usuwanie typowych śmieci z paragonów Biedronki
        lines = text.split('\n')
        cleaned_lines = []
        start_processing = False
        
        for line in lines:
            line = line.strip()
            # Szukamy początku listy zakupów (zazwyczaj po NIP lub 'PARAGON FISKALNY')
            if 'PARAGON FISKALNY' in line.upper():
                start_processing = True
                continue
            
            # Koniec listy zazwyczaj przy SUMA
            if 'SUMA PLN' in line.upper() or 'SPRZEDAZ OPODATKOWANA' in line.upper():
                break
                
            if start_processing and line:
                # Biedronka format: "NAZWA PRODUKTU   CENA" czasem z iloscią w nowej linii
                # Na razie proste czyszczenie
                cleaned_lines.append(line)
        
        # Jeśli nie znaleziono markerów, zwróć całość (fallback)
        if not cleaned_lines:
            return text
            
        return "\n".join(cleaned_lines)
