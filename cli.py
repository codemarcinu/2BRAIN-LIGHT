import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

import questionary

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
import finanse
import wiedza
import psutil

console = Console()

def print_header():
    console.print(Panel.fit(
        "[bold green]2Brain Lite[/bold green] [cyan]Hacker Terminal[/cyan]\n"
        "[italic]v1.0 (Voice & Vision Edition)[/italic]",
        border_style="green"
    ))

def show_status():
    table = Table(title="System Status")
    table.add_column("Service", style="cyan")
    table.add_column("PID", style="magenta")
    table.add_column("Status", style="green")

    # Check for known processes (simple check by name)
    bg_processes = ["python", "python3"]
    
    found_bot = False
    found_watcher = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                full_cmd = " ".join(cmdline)
                if "bot.py" in full_cmd:
                    table.add_row("🤖 Telegram Bot", str(proc.info['pid']), "RUNNING")
                    found_bot = True
                if "watcher.py" in full_cmd:
                    table.add_row("👀 Watcher", str(proc.info['pid']), "RUNNING")
                    found_watcher = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not found_bot:
        table.add_row("🤖 Telegram Bot", "-", "[red]STOPPED[/red]")
    if not found_watcher:
        table.add_row("👀 Watcher", "-", "[red]STOPPED[/red]")

    console.print(table)
    input("\nNaciśnij ENTER aby wrócić...")

def process_finances():
    console.print("[yellow]💰 Przetwarzanie paragonów...[/yellow]")
    path = "./inputs/paragony"
    if not os.path.exists(path):
        console.print(f"[red]Brak katalogu {path}[/red]")
        return
        
    files = [f for f in os.listdir(path) if f.casefold().endswith(('.jpg', '.png', '.pdf'))]
    
    if not files:
        console.print("[bold red]Brak paragonów do przetworzenia![/bold red]")
    else:
        for f in files:
            full_path = os.path.join(path, f)
            console.print(f"Przetwarzam: {f}...", end="")
            try:
                result = finanse.process_receipt_image(full_path)
                console.print(f" [green]OK[/green]")
                console.print(Panel(result, title=f"Wynik: {f}", border_style="blue"))
            except Exception as e:
                console.print(f" [red]BŁĄD: {e}[/red]")
    
    input("\nNaciśnij ENTER, aby kontynuować...")

def process_knowledge():
    console.print("[cyan]🧠 Przetwarzanie inboxu (wiedza)...[/cyan]")
    count = wiedza.process_batch(verbose=True)
    if count == 0:
        console.print("[dim]Pusto...[/dim]")
    else:
        console.print(f"[bold green]Przetworzono {count} notatek![/bold green]")
    input("\nNaciśnij ENTER, aby kontynuować...")

def show_report():
    console.print("[bold cyan]📊 Raport Finansowy (Ostatnie 5)[/bold cyan]")
    # Używamy istniejącej logiki finanse (trzeba by dodać funkcję get_recent w finanse.py, 
    # ale tu założymy że po prostu wyświetlimy info że to demo, lub dodamy prosty query)
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST"),
            database=os.getenv("POSTGRES_DB") or os.getenv("DB_NAME"),
            user=os.getenv("POSTGRES_USER") or os.getenv("DB_USER"),
            password=os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASS"),
            port=os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute("SELECT date, shop_name, total_amount, category FROM receipts ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        
        table = Table()
        table.add_column("Data", style="cyan")
        table.add_column("Sklep", style="white")
        table.add_column("Kwota", justify="right", style="green")
        table.add_column("Kategoria", style="magenta")
        
        for row in rows:
            table.add_row(str(row[0]), row[1], f"{row[2]:.2f} PLN", row[3])
            
        console.print(table)
        conn.close()
    except Exception as e:
        console.print(f"[red]Błąd bazy danych: {e}[/red]")
        
    input("\nNaciśnij ENTER, aby wrócić...")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header()
        
        choice = questionary.select(
            "Wybierz moduł:",
            choices=[
                "💰 Przetwórz Paragony (Batch)",
                "🧠 Przetwórz Inbox (Wiedza)",
                "📊 Raport Finansowy",
                "⚙️ Status Systemu",
                "🚪 Wyjście"
            ]
        ).ask()
        
        if choice == "🚪 Wyjście":
            console.print("[bold red]Do widzenia![/bold red]")
            sys.exit(0)
        elif choice.startswith("💰"):
            process_finances()
        elif choice.startswith("🧠"):
            process_knowledge()
        elif choice.startswith("📊"):
            show_report()
        elif choice.startswith("⚙️"):
            show_status()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrzerwano.")
