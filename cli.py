import sys
import os
import time
import psycopg2
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
import questionary

# Importujemy logikę z naszych modułów
import finanse
import wiedza
import pantry
import stats

load_dotenv()
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    title = """
    ██████╗ ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
    ╚════██╗██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
     █████╔╝██████╔╝██████╔╝███████║██║██╔██╗ ██║
    ██╔═══╝ ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
    ███████╗██████╔╝██║  ██║██║  ██║██║██║ ╚████║
    ╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
            LITE EDITION v1.0
    """
    console.print(Text(title, style="bold cyan"))
    console.print(Panel.fit("System: [bold green]ONLINE[/] | Database: [bold green]MIKR.US[/] | AI: [bold yellow]OLLAMA[/]", border_style="blue"))
    console.print("")

def show_stats():
    """Pobiera statystyki z bazy Postgres"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"), port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        # Ostatnie 5 paragonów
        cur.execute("SELECT date, shop_name, total_amount, category FROM receipts ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        
        # Suma wydatków w tym miesiącu
        cur.execute("SELECT SUM(total_amount) FROM receipts WHERE date_part('month', date) = date_part('month', CURRENT_DATE)")
        result = cur.fetchone()
        total_month = result[0] if result and result[0] else 0.0
        
        conn.close()
        
        # Tabela
        table = Table(title="💸 OSTATNIE TRANSAKCJE")
        table.add_column("Data", style="cyan")
        table.add_column("Sklep", style="magenta")
        table.add_column("Kwota", justify="right", style="green")
        table.add_column("Kategoria", style="yellow")
        
        for row in rows:
            table.add_row(str(row[0]), row[1], f"{row[2]} PLN", row[3])
            
        console.print(table)
        console.print(f"\n💰 Wydatki w tym miesiącu: [bold red]{total_month:.2f} PLN[/bold red]\n")
        
    except Exception as e:
        console.print(f"[bold red]Błąd połączenia z bazą:[/] {e}")

def run_processing(mode):
    """Uruchamia przetwarzanie z paskiem postępu"""
    with console.status(f"[bold green]Przetwarzanie {mode}...[/]", spinner="dots"):
        if mode == "FINANSE":
            count = finanse.process_batch()
            color = "green" if count > 0 else "yellow"
            console.print(f"[{color}]Zakończono. Przetworzono paragonów: {count}[/]")
        elif mode == "WIEDZA":
            count = wiedza.process_batch()
            color = "green" if count > 0 else "yellow"
            console.print(f"[{color}]Zakończono. Przetworzono notatek: {count}[/]")
    
    input("\nNaciśnij Enter, aby wrócić...")

def menu_pantry():
    while True:
        clear_screen()
        # 1. Pobierz stan
        expiring_soon, total_count = pantry.get_dashboard_stats()
        
        console.print(Panel(f"🥦 [bold green]SPIŻARNIA LITE[/] (Liczba produktów: {total_count})", style="green"))
        
        # 2. Wyświetl alerty
        candidates = pantry.get_expired_candidates() # To są te PO terminie (do wyjaśnienia)
        
        if candidates:
            console.print(f"[bold red]⚠️  MASZ {len(candidates)} PRODUKTÓW DO WERYFIKACJI (PO TERMINIE)[/]")
            table = Table(show_header=False, box=None)
            for c in candidates[:5]: # Pokaż max 5 dla czytelności w nagłówku
                table.add_row(f"[red]• {c['name']}[/]", f"(Termin minął: {c['expiry']})")
            console.print(table)
            console.print("[dim]Wejdź w 'Przegląd' aby zarządzać wszystkimi.[/]\n")
        elif expiring_soon:
             console.print("[yellow]Ostrzeżenie: Coś się niedługo zepsuje. Sprawdź 'Co na obiad'.[/]\n")
        else:
            console.print("[green]Stan idealny. Nic się nie psuje.[/]\n")

        # 3. Menu
        action = questionary.select(
            "Wybierz akcję:",
            choices=[
                "🧹 Przegląd / Sprzątanie (HITL)",
                "👨🍳 Co na obiad? (AI Chef)",
                "🔙 Wróć"
            ]
        ).ask()
        
        if "Przegląd" in action:
            if not candidates:
                console.print("[green]Brak produktów po terminie![/]")
                time.sleep(1.5)
                continue
                
            console.print("\n[bold yellow]Oto lista produktów, o które martwi się system:[/]")
            for c in candidates:
                console.print(f"🆔 [bold cyan]{c['id']}[/] | [white]{c['name']}[/] | [dim]{c['expiry']}[/]")
                
            console.print(Panel("Napisz co z nimi zrobić. Np:\n[italic]'Mleko i ser zjedzone, kurczaka wyrzuć, a ryż jest jeszcze dobry'[/]", title="💬 TWÓJ GŁOS"))
            
            user_input = questionary.text("Twoja komenda:").ask()
            
            if user_input:
                with console.status("[bold green]OpenAI przetwarza Twoją decyzję...[/]"):
                    stats = pantry.process_human_feedback(candidates, user_input)
                
                if stats:
                    console.print("\n✅ [bold]Raport wykonania:[/]")
                    console.print(f"😋 Zjedzone: [green]{stats['consumed']}[/]")
                    console.print(f"🗑️ Wyrzucone: [red]{stats['trashed']}[/]")
                    console.print(f"📅 Przedłużone: [blue]{stats['extended']}[/]")
                input("\n[Enter] aby kontynuować...")

        elif "Obiad" in action:
            with console.status("[bold magenta]Szef kuchni zagląda do lodówki...[/]"):
                recipe = pantry.suggest_recipe()
            console.print(Panel(recipe, title="👨🍳 Przepis Dnia", border_style="magenta"))
            input("\n[Enter] aby kontynuować...")
            
        elif "Wróć" in action:
            break

def main_menu():
    while True:
        print_banner()
        
        action = questionary.select(
            "Wybierz moduł:",
            choices=[
                "💰 Przetwórz Paragony (Vision + Ollama)",
                "🧠 Przetwórz Inbox (Ollama)",
                "🥦 Smart Pantry (Hybrid-Cloud)",
                "📊 Analityka / Statystyki",
                "👀 Uruchom Watcher (Tryb ciągły)",
                "❌ Wyjście"
            ],
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       
                ('question', 'bold'),               
                ('answer', 'fg:#f44336 bold'),      
                ('pointer', 'fg:#673ab7 bold'),     
                ('highlighted', 'fg:#673ab7 bold'), 
                ('selected', 'fg:#cc5454'),         
                ('separator', 'fg:#cc5454'),        
                ('instruction', ''),                
                ('text', ''),                       
                ('disabled', 'fg:#858585 italic')   
            ])
        ).ask()

        if not action or "Wyjście" in action:
            sys.exit()
        elif "Paragony" in action:
            run_processing("FINANSE")
        elif "Inbox" in action:
            run_processing("WIEDZA")
        elif "Smart Pantry" in action:
            menu_pantry()
        elif "Analityka" in action:
            clear_screen()
            stats.print_analytics_menu()
            
            sub_action = questionary.select(
                "Opcje:",
                choices=["📈 Sprawdź historię ceny produktu", "🔙 Wróć"]
            ).ask()
            
            if "historię" in sub_action:
                stats.show_product_history_ui()
            
        elif "Watcher" in action:
            console.print("[bold red]Uruchamiam tryb ciągły. CTRL+C aby przerwać.[/]")
            try:
                # Prosty watcher w jednym procesie (sekwencyjnie)
                while True:
                    finanse.process_batch()
                    wiedza.process_batch()
                    time.sleep(5)
            except KeyboardInterrupt:
                pass

if __name__ == "__main__":
    main_menu()
