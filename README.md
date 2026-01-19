# 2brain_lite

Lekka wersja systemu "Drugi Mózg" do zarządzania finansami, spiżarnią i wiedzą osobistą.

## Funkcjonalności

*   **Spiżarnia (`pantry.py`)**: Zarządzanie stanem produktów, generowanie list zakupów.
*   **Finanse (`finanse.py`)**: Śledzenie wydatków, integracja z paragonami.
*   **Wiedza (`wiedza.py`)**: Zarządzanie notatkami w systemie Zettelkasten.
*   **Przetwarzanie Paragonów (`core/pipelines`)**: Automatyczna normalizacja danych z paragonów przy użyciu Fuzzy Matching i AI.
*   **CLI (`cli.py`)**: Interfejs wiersza poleceń do obsługi systemu.

## Nowość: Receipt Processing Pipeline

System teraz zawiera zaawansowany moduł przetwarzania paragonów, który:
1.  Wykrywa sklep i datę zakupu.
2.  Normalizuje nazwy produktów na podstawie bazy `product_taxonomy.json`.
3.  Uczy się nowych produktów (Cache).
4.  Wykorzystuje AI do analizy trudnych przypadków.

Dokumentacja techniczna potoku: [docs/RECEIPT_PIPELINE.md](docs/RECEIPT_PIPELINE.md).

## Instalacja

1.  Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
2.  Skonfiguruj `.env` (skopiuj z `.env.example` lub stwórz nowy):
    ```env
    GOOGLE_API_KEY=twoj_klucz
    RECEIPT_AI_PROVIDER=google
    ```

## Uruchomienie CLI

```bash
python cli.py
```
