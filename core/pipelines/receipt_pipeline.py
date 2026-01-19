import asyncio
import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from rapidfuzz import process, fuzz
import time

# Lokalne importy
from config import ProjectConfig
from utils.receipt_cache import ReceiptCache, ProductMatch
from utils.taxonomy import TaxonomyGuard
from adapters.google.gemini_adapter import UniversalBrain
from utils.receipt_agents import detect_shop, get_agent

logger = logging.getLogger("AsyncReceiptPipeline")

class AsyncReceiptPipeline:
    """
    Asynchroniczny potok przetwarzania paragonów z inteligentnym cache'owaniem.
    
    Strategia:
    1. Cache (60-70% trafień -> natychmiastowy zwrot)
    2. Równoległe dopasowywanie rozmyte (Fuzzy Matching) dla braków w cache
    3. AI (LLM) tylko gdy powyższe zawiodą (pokrycie < 30%)
    """

    def __init__(self):
        self.cache = ReceiptCache()
        self.brain = UniversalBrain(provider=ProjectConfig.RECEIPT_AI_PROVIDER)
        
        self.taxonomy = TaxonomyGuard(str(ProjectConfig.PRODUCT_TAXONOMY_PATH))
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_receipt_async(self, ocr_text: str, shop: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        if not ocr_text or not ocr_text.strip():
            raise ValueError("OCR text is empty")

        # Krok 0: Wykrycie sklepu i wstępne czyszczenie
        if shop is None:
            shop = detect_shop(ocr_text)

        agent = get_agent(shop)
        cleaned_ocr = agent.preprocess(ocr_text)
        lines = [l.strip() for l in cleaned_ocr.split('\n') if l.strip()]

        # Krok 1: Sprawdzenie Cache
        cached_items = []
        cache_misses = []

        for line in lines:
            cached = self.cache.lookup(line, shop)
            if cached:
                cached_items.append((line, cached))
            else:
                cache_misses.append(line)

        cache_hit_rate = len(cached_items) / len(lines) if lines else 0

        # Krok 2: Równoległe dopasowywanie rozmyte (Fuzzy Matching)
        fuzzy_matches = []
        if cache_misses:
            fuzzy_matches = await self._fuzzy_match_batch(cache_misses)

        # Krok 3: Łączenie wyników
        all_items = []
        
        # Dodaj z cache
        for line, match in cached_items:
            all_items.append(self._match_to_item(line, match))

        # Dodaj z fuzzy match (jeśli pewność > 70%)
        for line, match_tuple in zip(cache_misses, fuzzy_matches):
            if match_tuple and match_tuple[1] >= 70:
                meta = self.taxonomy.get_metadata(match_tuple[0])
                if meta:
                    category = meta['cat'].upper() if meta['cat'] else 'INNE'
                    product_match = ProductMatch(
                        name=meta['name'],
                        category=category,
                        unit=meta['unit'],
                        confidence=match_tuple[1] / 100.0,
                        source="fuzzy"
                    )
                    all_items.append(self._match_to_item(line, product_match))
                    self.cache.update(line, product_match, shop)

        # Krok 4: Decyzja czy użyć AI (jeśli mało produktów rozpoznano)
        needs_ai = self._needs_ai_processing(all_items, len(lines), cache_hit_rate)

        if needs_ai:
            try:
                ai_result = await self._ai_process_async(ocr_text, shop, timeout=120.0)
                if ai_result and 'items' in ai_result:
                    all_items = ai_result['items']
                    self._update_cache_from_ai(ai_result['items'], shop)
            except Exception as e:
                logger.error(f"AI processing failed: {e}")

        # Krok 5: Ekstrakcja metadanych
        receipt_date = self._extract_date(ocr_text, shop)
        total_amount = sum(item.get('suma', 0) for item in all_items)

        if len(cached_items) + len(cache_misses) > 0:
            self.cache.save()

        elapsed = time.time() - start_time
        
        return {
            'items': all_items,
            'date': receipt_date,
            'total_amount': total_amount,
            'shop': shop,
            'stats': {
                'processing_time': elapsed,
                'cache_hit_rate': cache_hit_rate,
                'used_ai': needs_ai
            }
        }

    async def _fuzzy_match_batch(self, lines: List[str]) -> List[Optional[Tuple]]:
        if not lines: return []
        if len(lines) < 15: # Dla małych paragonów synchronicznie
            return [self._fuzzy_match_single(line) for line in lines]

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._fuzzy_match_single, line)
            for line in lines
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if not isinstance(r, Exception) else None for r in results]

    def _fuzzy_match_single(self, line: str) -> Optional[Tuple]:
        try:
            match = process.extractOne(
                line.upper(),
                self.taxonomy.ocr_patterns,
                scorer=fuzz.partial_ratio
            )
            return match
        except Exception:
            return None

    async def _ai_process_async(self, ocr_text: str, shop: str, timeout: float = 120.0) -> Optional[Dict]:
        system_prompt = self._build_system_prompt(shop)
        user_prompt = self._build_user_prompt(ocr_text, shop)

        try:
            response = await asyncio.wait_for(
                self.brain.generate_content_async(
                    user_prompt, system_prompt, "json"
                ),
                timeout=timeout
            )
            if response:
                cleaned = self._clean_json_response(response)
                return json.loads(cleaned)
        except Exception as e:
            logger.error(f"AI Error: {e}")
        return None

    def _match_to_item(self, line: str, match: ProductMatch) -> Dict:
        # Prosta logika regex do wyciągania cen z linii, która została dopasowana
        # To wymagałoby poprawy, bo cena może być w innym miejscu linii w zależności od OCR
        price_pattern = r'(\d+[.,]\d{2})'
        prices = re.findall(price_pattern, line)
        price = 0.0
        if prices:
            price = float(prices[-1].replace(',', '.'))
            
        return {
            'nazwa': match.name,
            'kategoria': match.category,
            'jednostka': match.unit,
            'ilosc': 1.0, # Uproszczenie, parser ilosci to osobny temat
            'cena_jedn': price,
            'suma': price
        }

    def _needs_ai_processing(self, items, total_lines, cache_hit_rate):
        if not items: return True
        coverage = len(items) / total_lines if total_lines > 0 else 0
        
        # Jeśli pokrycie jest bardzo niskie, użyj AI.
        # Możemy dostroić ten próg.
        if coverage < 0.3 or cache_hit_rate < 0.1: 
             return True
             
        return False

    def _extract_date(self, text, shop):
        agent = get_agent(shop)
        dates = agent.detect_dates(text)
        return dates[0] if dates else None

    def _clean_json_response(self, text):
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'```json\s*|\s*```', '', text)
        return text.strip()

    def _build_system_prompt(self, shop):
        return f"Extract items from {shop} receipt into JSON structure {{'items': [{{'nazwa':..., 'kategoria':..., 'ilosc':..., 'cena_jedn':..., 'suma':...}}]}}. Categories: SPOŻYWCZE, CHEMIA, ALKOHOL, INNE, NABIAŁ, OWOCE_WARZYWA, MIĘSO."

    def _build_user_prompt(self, ocr_text, shop):
        return f"Shop: {shop}\nOCR:\n{ocr_text}"

    def _update_cache_from_ai(self, items: List[Dict], shop: str):
        # Tutaj moglibyśmy dodawać do cache wyniki z AI
        # Ale to ryzykowne, bo AI może halucynować.
        # Na razie zostawiam puste albo tylko logowanie.
        pass

    def process_receipt_sync(self, ocr_text, shop=None):
        """Wrapper dla kodu synchronicznego"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.process_receipt_async(ocr_text, shop))
