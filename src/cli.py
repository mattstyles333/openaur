#!/usr/bin/env python3
"""
OpenAura CLI - A Typer-based command-line interface for OpenAura
"""
import json
import os
import subprocess
import sys
import time
from typing import Optional, List

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.rule import Rule
from rich.style import Style
from rich.syntax import Syntax
from rich.columns import Columns

app = typer.Typer(
    name="openaur",
    help="OpenAura CLI - Personal AI Assistant",
    add_completion=False,
)
console = Console()

# Configuration
BASE_URL = "http://localhost:8000"
CONTAINER_NAME = "openaura"


def print_banner():
    """Print the OpenAura banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗   ██╗██████╗  ║
║  ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║   ██║██╔══██╗ ║
║  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████║██║   ██║██████╔╝ ║
║  ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║   ██║██╔══██╗ ║
║  ╚██████╔╝██║     ███████╗██║ ╚████║██║  ██║╚██████╔╝██║  ██║ ║
║   ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ║
║                                                           ║
║         Personal AI Assistant with Arch Linux              ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(f"[cyan]{banner}[/cyan]")


def check_container() -> bool:
    """Check if the OpenAura container is running."""
    # Check if we're running inside a container (Docker environment)
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", False):
        # Running inside container, assume we're good
        return True
    
    # Running on host, check if container is running via docker
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except FileNotFoundError:
        # Docker not available, assume we're in development mode
        return True


def make_request(method: str, endpoint: str, **kwargs) -> dict:
    """Make an HTTP request to the OpenAura API."""
    url = f"{BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to OpenAura. Is the server running?[/red]")
        console.print("[yellow]Run: openaur start[/yellow]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP Error: {e.response.status_code}[/red]")
        try:
            error_data = e.response.json()
            console.print(f"[red]{error_data.get('detail', 'Unknown error')}[/red]")
        except:
            console.print(f"[red]{e.response.text}[/red]")
        raise typer.Exit(1)


# Server Commands
server_app = typer.Typer(help="Manage the OpenAura server")
app.add_typer(server_app, name="server")


@server_app.command("start")
def server_start():
    """Start the OpenAura server with progress indicator."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Starting OpenAura containers...", total=None)
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd="/home/laptop/Documents/code/openaur",
            capture_output=True
        )
        progress.update(task, completed=True)
    
    # Show nice success panel
    panel = Panel(
        "[bold green]✓ OpenAura started successfully![/bold green]\n\n"
        "[blue]API:[/blue] http://localhost:8000\n"
        "[blue]WebUI:[/blue] http://localhost:3000",
        title="🚀 Server Ready",
        border_style="green"
    )
    console.print(panel)


@server_app.command("stop")
def server_stop():
    """Stop the OpenAura server."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[yellow]Stopping OpenAura containers...", total=None)
        subprocess.run(
            ["docker-compose", "down"],
            cwd="/home/laptop/Documents/code/openaur",
            capture_output=True
        )
        progress.update(task, completed=True)
    
    console.print("[green]✓ OpenAura stopped[/green]")


@server_app.command("restart")
def server_restart():
    """Restart the OpenAura server."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Restarting OpenAura containers...", total=None)
        subprocess.run(
            ["docker-compose", "restart"],
            cwd="/home/laptop/Documents/code/openaur",
            capture_output=True
        )
        time.sleep(2)  # Give containers time to restart
        progress.update(task, completed=True)
    
    console.print("[green]✓ OpenAura restarted[/green]")


@server_app.command("status")
def server_status():
    """Show the OpenAura server status with rich formatting."""
    console.print("[bold blue]OpenAura Server Status[/bold blue]")
    console.print(Rule(style="blue"))
    subprocess.run(["docker-compose", "ps"], cwd="/home/laptop/Documents/code/openaur")


@server_app.command("logs")
def server_logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show")
):
    """Show OpenAura server logs."""
    cmd = ["docker-compose", "logs"]
    if follow:
        cmd.append("-f")
    if tail:
        cmd.extend(["--tail", str(tail)])
    subprocess.run(cmd, cwd="/home/laptop/Documents/code/openaur")


@server_app.command("shell")
def server_shell():
    """Open a shell in the OpenAura container."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "bash"])


# Heart Commands
@app.command()
def heart():
    """Check the heart of OpenAura with beautiful visualization."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    result = make_request("GET", "/heart/")
    
    heart_data = result.get("heart", {})
    physical = heart_data.get("physical", {})
    emotional = heart_data.get("emotional", {})
    vitals = heart_data.get("vitals", {})
    
    # Create heartbeat animation
    for i in range(3):
        console.clear()
        console.print(f"[red]{'💓' if i % 2 == 0 else '  '}[/red]", justify="center")
        time.sleep(0.3)
    
    console.clear()
    
    # Create a nice display with layout
    title = Text("OpenAura Heart Monitor", style="bold cyan")
    title.align("center")
    
    # Health metrics
    health_table = Table(show_header=False, box=box.SIMPLE)
    health_table.add_column("Metric", style="cyan", width=20)
    health_table.add_column("Value", style="green")
    
    health_table.add_row("Physical Health", f"[bold]{physical.get('status', 'unknown')}[/bold]")
    health_table.add_row("Database", physical.get('database', 'unknown'))
    health_table.add_row("Emotional State", f"[yellow]{emotional.get('state', 'unknown')}[/yellow]")
    health_table.add_row("Mood", f"[italic]{emotional.get('mood', 'unknown')}[/italic]")
    health_table.add_row("Intensity", f"{emotional.get('intensity', 0):.0%}")
    health_table.add_row("Version", vitals.get('version', 'unknown'))
    
    # Create panels
    health_panel = Panel(
        health_table,
        title="[bold]💓 Vitals[/bold]",
        border_style="green"
    )
    
    # Pulse indicator
    pulse_text = Text("♥ ♥ ♥", style="bold red")
    pulse_panel = Panel(
        Align.center(pulse_text),
        title="[bold]Pulse[/bold]",
        border_style="red"
    )
    
    console.print(title)
    console.print()
    console.print(Columns([health_panel, pulse_panel]))
    console.print()
    console.print(f"[dim]{result.get('message', '')}[/dim]", justify="center")


# Chat Commands
@app.command()
def chat(
    message: Optional[str] = typer.Argument(None, help="Message to send (omit for interactive mode)"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID for continuity")
):
    """Chat with OpenAura with rich formatting."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    if message:
        # Single message mode with spinner
        data = {"message": message}
        if session_id:
            data["session_id"] = session_id
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]OpenAura is thinking..."),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            result = make_request("POST", "/chat/", json=data)
        
        # Format response nicely
        response_panel = Panel(
            result.get('response', ''),
            title="[bold green]🤖 OpenAura[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(response_panel)
        
        if result.get('tools_used'):
            tools_text = Text(
                f"🔧 Tools used: {', '.join(result['tools_used'])}",
                style="dim"
            )
            console.print(tools_text)
            
    else:
        # Interactive mode
        print_banner()
        console.print(Panel.fit(
            "[bold cyan]OpenAura Chat[/bold cyan]\n"
            "Type [bold red]'exit'[/bold red] or [bold red]'quit'[/bold red] to leave",
            border_style="cyan"
        ))
        console.print()
        
        current_session = session_id
        while True:
            user_input = console.input("[bold green]👤 You:[/bold green] ")
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break
            
            data = {"message": user_input}
            if current_session:
                data["session_id"] = current_session
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]Thinking..."),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("", total=None)
                    result = make_request("POST", "/chat/", json=data)
                
                current_session = result.get("session_id")
                
                response_panel = Panel(
                    result.get('response', ''),
                    title="[bold cyan]🤖 OpenAura[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                )
                console.print(response_panel)
                console.print()
            except:
                break


# Ingest Commands
ingest_app = typer.Typer(help="Ingest data into OpenAura")
app.add_typer(ingest_app, name="ingest")


@ingest_app.command("action")
def ingest_action(
    binary: str = typer.Argument(..., help="Binary name to ingest (e.g., git, docker)"),
    safety: int = typer.Option(2, "--safety", "-s", help="Safety level (1-3)"),
    max_depth: int = typer.Option(12, "--depth", "-d", help="Max crawl depth")
):
    """Ingest a CLI tool's documentation with progress spinner."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        task = progress.add_task(f"[cyan]Ingesting {binary}...", total=None)
        
        result = make_request(
            "POST",
            "/ingest/action",
            params={"binary": binary, "safety": safety, "max_depth": max_depth}
        )
        
        progress.update(task, completed=True)
    
    # Show result nicely
    status_color = "green" if result.get("status") == "created" else "yellow"
    console.print(f"\n[bold {status_color}]✓ {result.get('message', 'Done')}[/bold {status_color}]")
    
    details = Table(show_header=False, box=box.SIMPLE)
    details.add_column("Property", style="cyan")
    details.add_column("Value", style="white")
    details.add_row("Binary", binary)
    details.add_row("Path", result.get('path', 'N/A'))
    details.add_row("Commands", str(result.get('commands_count', 0)))
    details.add_row("Safety Level", str(safety))
    
    console.print(Panel(details, title="[bold]📥 Ingestion Details[/bold]"))


@ingest_app.command("memory")
def ingest_memory(
    content: str = typer.Argument(..., help="Content to remember"),
    source: str = typer.Option("manual", "--source", help="Memory source"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Tags for the memory")
):
    """Ingest a memory into OpenAura."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Storing memory..."),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("", total=None)
        result = make_request(
            "POST",
            "/ingest/memory",
            json={"content": content, "source": source, "tags": tags or []}
        )
    
    # Success animation
    console.print("[green]✨[/green]", end="")
    time.sleep(0.1)
    console.print(" [green]✨[/green]", end="")
    time.sleep(0.1)
    console.print(" [green]✨[/green]")
    console.print(f"\n[bold green]✓ {result.get('message', 'Memory stored')}[/bold green]")


@ingest_app.command("status")
def ingest_status():
    """Show ingestion status with rich formatting."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    result = make_request("GET", "/ingest/status")
    
    # Create dashboard
    console.print(Rule("[bold cyan]📥 Ingestion Status[/bold cyan]"))
    
    # Status indicator
    status = result.get("status", "unknown")
    status_emoji = "🟢" if status == "ready" else "🟡"
    console.print(f"{status_emoji} Status: [bold]{status}[/bold]")
    console.print()
    
    # Stats
    stats = Table(title="Statistics", box=box.ROUNDED)
    stats.add_column("Metric", style="cyan")
    stats.add_column("Value", style="white")
    stats.add_row("Ingested Actions", str(result.get("ingested_actions", 0)))
    
    if result.get("actions"):
        actions_list = ", ".join(result["actions"])
        stats.add_row("Actions", actions_list)
    
    console.print(stats)
    console.print()
    
    # Capabilities
    if result.get("capabilities"):
        console.print("[bold]Capabilities:[/bold]")
        for cap in result["capabilities"]:
            console.print(f"  ✓ {cap}")


# Actions Commands
@app.command()
def actions():
    """List registered actions with rich table."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    result = make_request("GET", "/actions/")
    
    if not result:
        console.print("[yellow]No actions registered yet[/yellow]")
        console.print("[dim]Register one with: openaur ingest action <binary>[/dim]")
        return
    
    # Create styled table
    table = Table(
        title="🔧 Registered Actions",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("ID", style="cyan", width=15)
    table.add_column("Description", style="white", width=50)
    table.add_column("Safety", style="yellow", width=8, justify="center")
    
    for action in result:
        safety = action.get("safety", "N/A")
        # Color code safety levels
        safety_style = {
            1: "[green]1[/green]",
            2: "[yellow]2[/yellow]",
            3: "[red]3[/red]"
        }.get(safety, str(safety))
        
        desc = action.get("description", "N/A")
        if len(desc) > 47:
            desc = desc[:47] + "..."
        
        table.add_row(
            action.get("id", "N/A"),
            desc,
            safety_style
        )
    
    console.print(table)


# Package Commands
packages_app = typer.Typer(help="Package management")
app.add_typer(packages_app, name="packages")


@packages_app.command("search")
def packages_search(
    query: str = typer.Argument(..., help="Package name to search for"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results")
):
    """Search for packages with progress indicator."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Searching packages..."),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("", total=None)
        result = make_request("GET", f"/packages/search?q={query}&limit={limit}")
    
    packages = result.get("packages", [])
    
    if not packages:
        console.print(f"[yellow]No packages found for '{query}'[/yellow]")
        return
    
    table = Table(
        title=f"📦 Search Results: '{query}'",
        box=box.ROUNDED
    )
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Description", style="white", width=40)
    
    for pkg in packages:
        desc = pkg.get("description", "N/A")
        if len(desc) > 37:
            desc = desc[:37] + "..."
        
        # Color code source
        source = pkg.get("source", "unknown")
        source_display = {
            "official": "[blue]official[/blue]",
            "aur": "[magenta]AUR[/magenta]"
        }.get(source, source)
        
        table.add_row(
            pkg.get("name", "N/A"),
            pkg.get("version", "N/A"),
            source_display,
            desc
        )
    
    console.print(table)
    console.print(f"\n[dim]Found {len(packages)} packages[/dim]")


@packages_app.command("install")
def packages_install(
    package: str = typer.Argument(..., help="Package name to install"),
    auto: bool = typer.Option(False, "--auto", help="Auto-install")
):
    """Install a package with progress bar."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    # Show installing animation
    console.print(f"[cyan]Installing {package}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", finished_style="green"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Installing {package}...", total=100)
        
        # Simulate progress (actual install happens on server)
        for i in range(0, 101, 10):
            time.sleep(0.1)
            progress.update(task, completed=i)
        
        result = make_request(
            "POST",
            "/packages/install",
            json={"package": package, "auto": auto}
        )
        
        progress.update(task, completed=100)
    
    if result.get("success"):
        console.print(f"\n[bold green]✓ {package} installed successfully[/bold green]")
    else:
        console.print(f"\n[bold red]✗ Failed to install {package}[/bold red]")
        console.print(f"[red]{result.get('error', 'Unknown error')}[/red]")


# Session Commands
@app.command()
def sessions():
    """List active sessions with rich formatting."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    result = make_request("GET", "/sessions/")
    
    if not result:
        console.print("[dim]No active sessions[/dim]")
        return
    
    table = Table(
        title="📋 Active Sessions",
        box=box.ROUNDED
    )
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Tmux Session", style="green")
    table.add_column("Command", style="white", width=40)
    table.add_column("Status", style="yellow", justify="center")
    
    for session in result:
        status = session.get("status", "N/A")
        status_style = {
            "running": "[green]● running[/green]",
            "completed": "[dim]✓ completed[/dim]",
            "failed": "[red]✗ failed[/red]"
        }.get(status, status)
        
        cmd = session.get("command", "N/A")
        if len(cmd) > 37:
            cmd = cmd[:37] + "..."
        
        table.add_row(
            session.get("id", "N/A")[:8],
            session.get("tmux_session", "N/A"),
            cmd,
            status_style
        )
    
    console.print(table)


# Test Command
@app.command()
def test():
    """Test OpenAura endpoints with visual feedback."""
    if not check_container():
        console.print("[red]Error: OpenAura container is not running[/red]")
        raise typer.Exit(1)
    
    print_banner()
    console.print(Rule("[bold blue]Running Tests[/bold blue]"))
    console.print()
    
    tests = [
        ("Health endpoint", "/health"),
        ("Heart endpoint", "/heart/"),
        ("Actions endpoint", "/actions/"),
        ("Ingest status", "/ingest/status"),
    ]
    
    results = []
    for name, endpoint in tests:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Testing {name}..."),
                console=console,
                transient=True
            ) as progress:
                progress.add_task("", total=None)
                make_request("GET", endpoint)
            results.append((name, "✓", "green"))
        except Exception as e:
            results.append((name, "✗", "red"))
    
    # Show results
    console.print()
    for name, status, color in results:
        console.print(f"  [{color}]{status}[/{color}] {name}")
    
    console.print()
    passed = sum(1 for _, status, _ in results if status == "✓")
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✓ All {total} tests passed![/bold green]")
    else:
        console.print(f"[bold yellow]⚠ {passed}/{total} tests passed[/bold yellow]")


# Callback for banner on CLI startup
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """OpenAura CLI with rich features."""
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n[bold]Welcome to OpenAura![/bold]")
        console.print("Run [cyan]openaur --help[/cyan] to see available commands\n")


if __name__ == "__main__":
    app()
