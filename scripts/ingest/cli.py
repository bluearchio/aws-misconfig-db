"""CLI entrypoint for the ingest pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.ingest import __version__
from scripts.ingest.config import load_sources, get_enabled_sources
from scripts.ingest.orchestrator import PipelineOrchestrator
from scripts.ingest.progress import PipelineProgress
from scripts.ingest.stage import list_staged, promote, reject
from scripts.ingest.state import load_state

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def _console():
    """Get a console instance if rich is available."""
    return Console() if HAS_RICH and sys.stdout.isatty() else None


def cmd_fetch(args):
    """Run the fetch pipeline."""
    progress = PipelineProgress(verbose=args.verbose)

    orchestrator = PipelineOrchestrator(
        source_ids=args.sources,
        source_type=args.source_type,
        dry_run=args.dry_run,
        skip_llm=args.skip_llm,
        max_items=args.max_items,
        similarity_threshold=args.similarity_threshold,
        model=args.model,
        verbose=args.verbose,
        progress=progress,
        auto_promote=args.auto_promote,
        auto_promote_threshold=args.auto_promote_threshold,
    )
    metrics = orchestrator.run()

    # Show auto-promoted summary if any
    auto_promoted = metrics.get("items_auto_promoted", 0)
    if auto_promoted > 0:
        console = _console()
        if console:
            console.print(f"\n  [bold green]{auto_promoted}[/bold green] item(s) auto-promoted to the main database")
        else:
            print(f"\n  {auto_promoted} item(s) auto-promoted to the main database")

    # Show staged items table if any were staged
    if metrics.get("items_staged", 0) > 0:
        staged = list_staged()
        progress.show_staged_table(staged)

    return 0 if not metrics.get("errors") else 1


def cmd_list_sources(args):
    """List configured sources."""
    try:
        config = load_sources()
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    sources = config["sources"]
    if args.enabled_only:
        sources = [s for s in sources if s.get("enabled", True)]

    if args.format == "json":
        print(json.dumps(sources, indent=2))
        return 0

    console = _console()
    if console:
        table = Table(
            title=f"Configured Sources ({len(sources)})",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        table.add_column("ID", style="cyan", width=32)
        table.add_column("Type", width=8)
        table.add_column("Enabled", width=8, justify="center")
        table.add_column("Categories", style="dim")

        for s in sources:
            enabled = "[green]yes[/green]" if s.get("enabled", True) else "[dim]no[/dim]"
            cats = ", ".join(s.get("categories", []))
            table.add_row(s["id"], s["type"], enabled, cats)

        console.print(table)
    else:
        print(f"{'ID':<35} {'Type':<8} {'Enabled':<8} {'Categories'}")
        print("-" * 80)
        for s in sources:
            enabled = "yes" if s.get("enabled", True) else "no"
            cats = ", ".join(s.get("categories", []))
            print(f"{s['id']:<35} {s['type']:<8} {enabled:<8} {cats}")

    enabled_count = sum(1 for s in config["sources"] if s.get("enabled", True))
    total = len(config["sources"])
    if console:
        console.print(f"\n  [bold]{enabled_count}[/bold] enabled / {total} total")
    else:
        print(f"\n  {enabled_count} enabled / {total} total")
    return 0


def cmd_health(args):
    """Run health checks."""
    from scripts.ingest.health import run_health_checks
    results = run_health_checks(checks=args.check)

    console = _console()
    has_errors = False

    if console:
        table = Table(box=box.SIMPLE_HEAVY, padding=(0, 1))
        table.add_column("Status", width=10, justify="center")
        table.add_column("Check", style="bold", width=24)
        table.add_column("Message")

        for result in results:
            severity = result["severity"]
            if severity == "OK":
                status = "[green]OK[/green]"
            elif severity == "WARNING":
                status = "[yellow]WARN[/yellow]"
            elif severity == "ERROR":
                status = "[red]ERROR[/red]"
                has_errors = True
            else:
                status = "[bold red]CRIT[/bold red]"
                has_errors = True

            table.add_row(status, result["check"], result["message"])

        console.print(Panel(table, title="[bold]Health Checks[/bold]", border_style="blue"))
    else:
        for result in results:
            severity = result["severity"]
            symbol = {"OK": "✓", "WARNING": "⚠", "ERROR": "✗", "CRITICAL": "✗✗"}
            print(f"  {symbol.get(severity, '?')} [{severity}] {result['check']}: {result['message']}")
            if severity in ("ERROR", "CRITICAL"):
                has_errors = True

    return 1 if has_errors else 0


def cmd_history(args):
    """Show pipeline run history."""
    state = load_state()
    runs = state.get("runs", [])

    if not runs:
        print("No pipeline runs recorded.")
        return 0

    last_n = args.last or 10
    runs = runs[-last_n:]

    if args.format == "json":
        print(json.dumps(runs, indent=2))
        return 0

    console = _console()
    if console:
        table = Table(
            title=f"Pipeline Run History (last {len(runs)})",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("Fetched", justify="right", width=8)
        table.add_column("Staged", justify="right", style="green", width=8)
        table.add_column("Dedup", justify="right", width=8)
        table.add_column("Errors", justify="right", width=8)

        for run in reversed(runs):
            ts = run.get("timestamp", "?")[:19]
            m = run.get("metrics", {})
            err_count = len(m.get("errors", []))
            err_style = f"[red]{err_count}[/red]" if err_count else str(err_count)
            table.add_row(
                ts,
                str(m.get("items_fetched", 0)),
                str(m.get("items_staged", 0)),
                str(m.get("items_filtered_dedup", 0)),
                err_style,
            )

        console.print(table)
    else:
        for run in reversed(runs):
            ts = run.get("timestamp", "?")
            m = run.get("metrics", {})
            print(f"  {ts}  fetched={m.get('items_fetched', 0)}  staged={m.get('items_staged', 0)}  "
                  f"dedup={m.get('items_filtered_dedup', 0)}  errors={len(m.get('errors', []))}")

    return 0


def cmd_show_staged(args):
    """Show staged recommendations."""
    staged = list_staged(service_filter=args.filter_service)

    if not staged:
        print("No staged recommendations.")
        return 0

    if args.format == "json":
        print(json.dumps(staged, indent=2))
        return 0

    console = _console()
    if console and args.format != "detail":
        table = Table(
            title=f"Staged Recommendations ({len(staged)})",
            box=box.ROUNDED,
            show_lines=True,
            padding=(0, 1),
        )
        table.add_column("Service", style="cyan", width=16)
        table.add_column("Scenario", width=44)
        table.add_column("Risk", style="yellow", width=20)
        table.add_column("Source", style="dim", width=16)
        table.add_column("Dedup", justify="right", width=6)

        for item in staged:
            scenario = item["scenario"]
            if len(scenario) > 42:
                scenario = scenario[:42] + ".."
            table.add_row(
                item["service_name"],
                scenario,
                item["risk_detail"],
                item["source_id"][:16],
                f"{item['dedup_score']:.2f}",
            )

        console.print(table)
    elif args.format == "detail":
        for item in staged:
            if console:
                lines = [
                    f"[bold]Service:[/bold]  {item['service_name']}",
                    f"[bold]Scenario:[/bold] {item['scenario']}",
                    f"[bold]Risk:[/bold]     {item['risk_detail']}",
                    f"[bold]Source:[/bold]   {item['source_id']}",
                    f"[bold]Dedup:[/bold]    {item['dedup_score']:.2f} (closest: {item['closest_existing'][:50]})",
                    f"[bold]Staged:[/bold]   {item['staged_at']}",
                ]
                console.print(Panel(
                    "\n".join(lines),
                    title=f"[cyan]{item['id']}[/cyan]",
                    border_style="dim",
                ))
            else:
                print(f"\n{'=' * 60}")
                print(f"ID:       {item['id']}")
                print(f"Service:  {item['service_name']}")
                print(f"Scenario: {item['scenario']}")
                print(f"Risk:     {item['risk_detail']}")
                print(f"Source:   {item['source_id']}")
                print(f"Dedup:    {item['dedup_score']:.2f} (closest: {item['closest_existing'][:50]})")
                print(f"Staged:   {item['staged_at']}")
    else:
        print(f"{'ID':<40} {'Service':<12} {'Scenario':<40} {'Dedup'}")
        print("-" * 100)
        for item in staged:
            scenario = item['scenario'][:38] + ".." if len(item['scenario']) > 40 else item['scenario']
            print(f"{item['id']:<40} {item['service_name']:<12} {scenario:<40} {item['dedup_score']:.2f}")

    if console:
        console.print(f"\n  [bold]{len(staged)}[/bold] staged recommendations")
    else:
        print(f"\nTotal: {len(staged)} staged recommendations")
    return 0


def cmd_promote(args):
    """Promote a staged recommendation."""
    success, message = promote(args.uuid)
    console = _console()
    if console:
        if success:
            console.print(f"  [green]✓[/green] {message}")
        else:
            console.print(f"  [red]✗[/red] {message}")
    else:
        print(message)
    return 0 if success else 1


def cmd_reject(args):
    """Reject a staged recommendation."""
    success, message = reject(args.uuid, reason=args.reason or "")
    console = _console()
    if console:
        if success:
            console.print(f"  [yellow]○[/yellow] {message}")
        else:
            console.print(f"  [red]✗[/red] {message}")
    else:
        print(message)
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        prog="ingest",
        description=f"AWS Misconfiguration DB Ingest Pipeline v{__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Run the fetch pipeline")
    fetch_parser.add_argument("--sources", nargs="*", help="Source IDs to fetch")
    fetch_parser.add_argument("--source-type", choices=["rss", "html", "github"], help="Filter by source type")
    fetch_parser.add_argument("--dry-run", action="store_true", help="Fetch and dedup without LLM or staging")
    fetch_parser.add_argument("--skip-llm", action="store_true", help="Skip LLM conversion")
    fetch_parser.add_argument("--max-items", type=int, help="Max items per source")
    fetch_parser.add_argument("--similarity-threshold", type=float, default=0.70, help="Dedup threshold (default: 0.70)")
    fetch_parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model for conversion")
    fetch_parser.add_argument("--auto-promote", action="store_true", help="Auto-promote high-confidence recommendations (dedup < 0.30)")
    fetch_parser.add_argument("--auto-promote-threshold", type=float, default=0.30, help="Auto-promote threshold (default: 0.30)")
    fetch_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    fetch_parser.set_defaults(func=cmd_fetch)

    # list-sources command
    ls_parser = subparsers.add_parser("list-sources", help="List configured sources")
    ls_parser.add_argument("--enabled-only", action="store_true")
    ls_parser.add_argument("--format", choices=["table", "json"], default="table")
    ls_parser.set_defaults(func=cmd_list_sources)

    # health command
    health_parser = subparsers.add_parser("health", help="Run health checks")
    health_parser.add_argument("--check", nargs="*", help="Specific checks to run")
    health_parser.set_defaults(func=cmd_health)

    # history command
    hist_parser = subparsers.add_parser("history", help="Show run history")
    hist_parser.add_argument("--last", type=int, default=10, help="Number of runs to show")
    hist_parser.add_argument("--format", choices=["table", "json"], default="table")
    hist_parser.set_defaults(func=cmd_history)

    # show-staged command
    ss_parser = subparsers.add_parser("show-staged", help="Show staged recommendations")
    ss_parser.add_argument("--format", choices=["table", "json", "detail"], default="table")
    ss_parser.add_argument("--filter-service", help="Filter by service name")
    ss_parser.set_defaults(func=cmd_show_staged)

    # promote command
    prom_parser = subparsers.add_parser("promote", help="Promote staged recommendation")
    prom_parser.add_argument("uuid", help="UUID of staged recommendation")
    prom_parser.set_defaults(func=cmd_promote)

    # reject command
    rej_parser = subparsers.add_parser("reject", help="Reject staged recommendation")
    rej_parser.add_argument("uuid", help="UUID of staged recommendation")
    rej_parser.add_argument("--reason", help="Rejection reason")
    rej_parser.set_defaults(func=cmd_reject)

    args = parser.parse_args()

    # Setup logging - quiet when rich is rendering progress
    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
