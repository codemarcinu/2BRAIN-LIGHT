# 2brain_lite CLI Manual

Welcome to the **Glorious CLI** manual for `2brain_lite`. This tool is designed to be your command center for personal finance and knowledge management, utilizing local AI and cloud databases.

## 🚀 Installation & Setup

1.  **Prerequisites**:
    *   Python 3.10+
    *   PostgreSQL database (e.g., on Mikr.us)
    *   Google Cloud Vision API Key (JSON)
    *   Ollama installed locally (with `qwen2.5-coder:14b` and `bielik` models)

2.  **Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Ensure your `.env` file is populated with:
    *   `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_PORT`
    *   `GOOGLE_APPLICATION_CREDENTIALS` (path to JSON key)
    *   `OLLAMA_MODEL_LOGIC` (e.g., `qwen2.5-coder:14b`)
    *   `OLLAMA_MODEL_POLISH` (e.g., `bielik`)

## 🎮 Usage Guide

Run the CLI with:
```bash
python cli.py
```

Navigate the menu using **Arrow Keys** and **Enter**.

### 💰 Module: Przetwórz Paragony (Finance)
*   **Input**: Place image files (`.jpg`, `.png`) in `inputs/paragony`.
*   **Action**: Select "💰 Przetwórz Paragony".
*   **Process**:
    1.  **OCR**: Google Vision extracts text from the image.
    2.  **AI Parsing**: Ollama converts raw text into structured JSON (Date, Shop, Amount, Category, Items).
    3.  **Storage**: Finds are saved to your PostgreSQL database.
    4.  **Archival**: Original images are moved to `archive/` with a timestamp.

### 🧠 Module: Przetwórz Inbox (Knowledge)
*   **Input**: Place text files (`.txt`) in `inputs/inbox`.
*   **Action**: Select "🧠 Przetwórz Inbox".
*   **Process**:
    1.  **AI Analysis**: Ollama summarizes the text, extracts key insights, and suggests tags.
    2.  **Markdown Generation**: Creates a formatted `.md` file in your Obsidian Inbox (path defined in `wiedza.py`).
    3.  **Archival**: Original `.txt` files are moved to `archive/`.

### 📊 Module: Raport Finansowy
*   **Action**: Select "📊 Raport Finansowy".
*   **Process**: Fetches the last 5 transactions and the total sum for the current month directly from the database and displays them in a rich table.

### 👀 Module: Watcher (Tryb ciągły)
*   **Action**: Select "👀 Uruchom Watcher".
*   **Process**: Runs in an infinite loop, monitoring both input folders every 5 seconds. Use `CTRL+C` to stop.

## 🔧 Troubleshooting

*   **Database Error**: Ensure your VPN/Internet connection is active if using a remote DB. Check `.env` credentials.
*   **Ollama Error**: Ensure Ollama is running (`ollama serve`) and the specified models are pulled (`ollama pull <model_name>`).
*   **Google Vision Error**: Check if your service account key is valid and the path in `.env` is correct.
