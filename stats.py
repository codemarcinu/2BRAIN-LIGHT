import os
import psycopg2
import json
from datetime import datetime
from dotenv import load_dotenv
from rich.table import Table
from rich.console import Console

load_dotenv()
console = Console()

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"), port=os.getenv("DB_PORT")
    )

def get_monthly_report():
    """Generuje raport wydatków za bieżący miesiąc"""
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Suma całkowita
    cur.execute("""
        SELECT SUM(total_amount), COUNT(*) 
        FROM receipts 
        WHERE date_part('month', date) = date_part('month', CURRENT_DATE)
        AND date_part('year', date) = date_part('year', CURRENT_DATE)
    """)
    total_spent, receipt_count = cur.fetchone()
    total_spent = total_spent or 0.0
    receipt_count = receipt_count or 0

    # 2. Wg Kategorii
    cur.execute("""
        SELECT category, SUM(total_amount) 
        FROM receipts 
        WHERE date_part('month', date) = date_part('month', CURRENT_DATE)
        GROUP BY category 
        ORDER BY SUM(total_amount) DESC
    """)
    by_category = cur.fetchall()

    # 3. Wg Sklepów (Top 5)
    cur.execute("""
        SELECT shop_name, SUM(total_amount) 
        FROM receipts 
        WHERE date_part('month', date) = date_part('month', CURRENT_DATE)
        GROUP BY shop_name 
        ORDER BY SUM(total_amount) DESC 
        LIMIT 5
    """)
    by_shop = cur.fetchall()

    conn.close()
    return {
        "total": total_spent,
        "count": receipt_count,
        "categories": by_category,
        "shops": by_shop
    }

def get_price_history(product_query):
    """Szuka historii cen dla danego produktu w JSONB"""
    conn = get_db()
    cur = conn.cursor()
    
    # Przeszukujemy JSONB. To zapytanie jest nieco wolne na dużej bazie, ale na domową OK.
    # Szukamy w tablicy 'items' obiektów, gdzie klucz 'name' zawiera nasz tekst
    search_term = f"%{product_query}%"
    
    # Uwaga: To wymaga, żeby items_json było listą obiektów {"name": "...", "price": ...}
    # Dla starych rekordów (gdzie to lista stringów) to może sypnąć błędami lub nic nie zwrócić.
    # Dlatego robimy proste pobranie wszystkiego i filtrowanie w Pythonie dla bezpieczeństwa danych mieszanych.
    
    cur.execute("SELECT date, shop_name, items_json FROM receipts ORDER BY date DESC")
    rows = cur.fetchall()
    
    conn.close()
    
    history = []
    
    for r in rows:
        r_date, r_shop, r_items = r
        if not r_items: continue
        
        # Obsługa różnych formatów (lista stringów vs lista dictów)
        for item in r_items:
            if isinstance(item, dict):
                name = item.get('name', '')
                price = item.get('price', 0)
                if product_query.lower() in name.lower():
                    history.append({
                        "date": r_date,
                        "shop": r_shop,
                        "name": name,
                        "price": price
                    })
            elif isinstance(item, str):
                # Stary format - brak ceny jednostkowej, ignorujemy dla wykresu cen
                pass
                
    return history

def print_analytics_menu():
    from rich.panel import Panel
    
    report = get_monthly_report()
    
    # 1. Dashboard Miesięczny
    console.print(Panel(f"[bold]RAPORT MIESIĘCZNY ({datetime.now().strftime('%B')})[/]", style="blue"))
    console.print(f"💰 Wydano łącznie: [bold green]{report['total']:.2f} PLN[/] (Paragonów: {report['count']})")
    
    # Tabela Kategorii
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column(justify="right")
    
    if report['categories']:
        console.print("\n[u]Wydatki wg Kategorii:[/]")
        for cat, amount in report['categories']:
            grid.add_row(cat, f"{amount:.2f} PLN")
        console.print(grid)
    
    # Tabela Sklepów
    if report['shops']:
        console.print("\n[u]Top Sklepy:[/]")
        shop_grid = Table.grid(expand=True)
        shop_grid.add_column()
        shop_grid.add_column(justify="right")
        for shop, amount in report['shops']:
            shop_grid.add_row(shop, f"{amount:.2f} PLN")
        console.print(shop_grid)
        
    console.print("\n------------------------------------------------")

def show_product_history_ui():
    import questionary
    product = questionary.text("Wpisz nazwę produktu do analizy (np. Masło):").ask()
    if not product: return
    
    history = get_price_history(product)
    
    if not history:
        console.print(f"[red]Nie znaleziono historii cen dla '{product}' (lub brak danych o cenach w bazie).[/]")
        return
        
    table = Table(title=f"📈 Historia cen: {product.upper()}")
    table.add_column("Data", style="cyan")
    table.add_column("Sklep", style="magenta")
    table.add_column("Produkt", style="white")
    table.add_column("Cena", style="green", justify="right")
    
    # Sortowanie chronologiczne do tabeli
    history.sort(key=lambda x: x['date'])
    
    prices = []
    
    for h in history:
        price_display = f"{h['price']:.2f} PLN" if h['price'] > 0 else "???"
        table.add_row(str(h['date']), h['shop'], h['name'], price_display)
        if h['price'] > 0:
            prices.append(h['price'])
            
    console.print(table)
    
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        console.print(f"\n📊 [bold]Średnia:[/]{avg_price:.2f} | [bold green]Min:[/]{min_price:.2f} | [bold red]Max:[/]{max_price:.2f}")
    
    input("\n[Enter] aby wrócić...")
