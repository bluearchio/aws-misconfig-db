"""Rich terminal progress display for the ingest pipeline."""

from __future__ import annotations

import sys
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn,
        TaskProgressColumn, TimeElapsedColumn,
    )
    from rich.table import Table
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class PipelineProgress:
    """Progress display for the ingest pipeline.

    Uses rich for styled output when available and stdout is a terminal.
    Falls back to plain text otherwise.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._use_rich = HAS_RICH and sys.stdout.isatty()
        self.console = Console() if self._use_rich else None
        self._source_results: list[tuple] = []
        self._progress: Any = None
        self._fetch_task: Any = None
        self._process_task: Any = None

    # ── Header ──────────────────────────────────────────────

    def show_header(self, version: str, mode: str, num_sources: int, threshold: float):
        if self._use_rich:
            lines = [
                f"[bold]Mode:[/bold]       {mode}",
                f"[bold]Sources:[/bold]    {num_sources} enabled",
                f"[bold]Threshold:[/bold]  {threshold}",
            ]
            self.console.print(Panel(
                "\n".join(lines),
                title=f"[bold blue]AWS Misconfig DB · Ingest Pipeline v{version}[/bold blue]",
                border_style="blue",
                padding=(0, 1),
            ))
        else:
            print(f"\n{'=' * 55}")
            print(f"  AWS Misconfig DB · Ingest Pipeline v{version}")
            print(f"  Mode: {mode} | Sources: {num_sources} | Threshold: {threshold}")
            print(f"{'=' * 55}")

    def show_dedup_loaded(self, count: int):
        if self._use_rich:
            self.console.print(
                f"  [dim]Loaded[/dim] [bold]{count}[/bold] "
                f"[dim]existing recommendations for dedup[/dim]"
            )
        else:
            print(f"  Loaded {count} existing recommendations for dedup")

    # ── Fetch phase ─────────────────────────────────────────

    def start_fetch_phase(self, total: int):
        self._source_results = []
        if self._use_rich:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TextColumn("·"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True,
            )
            self._progress.start()
            self._fetch_task = self._progress.add_task("Fetching sources", total=total)
        else:
            print(f"\n  Fetching from {total} sources...")

    def update_source_start(self, source_name: str, source_type: str):
        if self._use_rich and self._progress is not None:
            self._progress.update(
                self._fetch_task,
                description=f"Fetching [cyan]{source_name}[/cyan]",
            )

    def update_source_complete(
        self,
        source_name: str,
        source_type: str,
        items_parsed: int,
        items_novel: int,
        error: str | None = None,
        not_modified: bool = False,
    ):
        if error:
            self._source_results.append(("error", source_name, source_type, 0, 0, error))
        elif not_modified:
            self._source_results.append(("skip", source_name, source_type, 0, 0, "not modified"))
        else:
            self._source_results.append(("ok", source_name, source_type, items_parsed, items_novel, ""))

        if self._use_rich and self._progress is not None:
            self._progress.advance(self._fetch_task)

    def end_fetch_phase(self):
        if self._use_rich and self._progress is not None:
            self._progress.stop()
            self._progress = None
            self.console.print()

        for status, name, stype, parsed, novel, detail in self._source_results:
            stype_display = stype.upper() if len(stype) <= 3 else stype[:3].upper()
            if self._use_rich:
                if status == "ok":
                    self.console.print(
                        f"    [green]✓[/green] {name:<32} [dim]{stype_display:>4}[/dim]"
                        f"  {parsed:>3} items → [bold]{novel}[/bold] novel"
                    )
                elif status == "skip":
                    self.console.print(
                        f"    [yellow]○[/yellow] {name:<32} [dim]{stype_display:>4}  not modified[/dim]"
                    )
                else:
                    self.console.print(
                        f"    [red]✗[/red] {name:<32} [dim]{stype_display:>4}[/dim]  [red]{detail[:60]}[/red]"
                    )
            else:
                if status == "ok":
                    print(f"    ✓ {name:<32} {stype_display:>4}  {parsed:>3} items → {novel} novel")
                elif status == "skip":
                    print(f"    ○ {name:<32} {stype_display:>4}  not modified")
                else:
                    print(f"    ✗ {name:<32} {stype_display:>4}  {detail[:60]}")

        if self._use_rich:
            self.console.print()
        else:
            print()

    # ── Process phase ───────────────────────────────────────

    def start_process_phase(self, total: int):
        if self._use_rich:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TextColumn("·"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True,
            )
            self._progress.start()
            self._process_task = self._progress.add_task("Processing items", total=total)
        else:
            print(f"  Processing {total} items...")

    def update_item_progress(self, title: str, stage: str):
        if self._use_rich and self._progress is not None:
            short = title[:40] + "..." if len(title) > 40 else title
            self._progress.update(
                self._process_task,
                description=f"{stage} [cyan]{short}[/cyan]",
            )

    def advance_item(self):
        if self._use_rich and self._progress is not None:
            self._progress.advance(self._process_task)

    def end_process_phase(self):
        if self._use_rich and self._progress is not None:
            self._progress.stop()
            self._progress = None

    # ── Summary ─────────────────────────────────────────────

    def show_summary(self, metrics: dict):
        m = metrics
        errors = m.get("errors", [])

        if self._use_rich:
            lines = []
            src = m.get("sources_processed", 0)
            err_str = f" · [red]{len(errors)} errors[/red]" if errors else " · [green]0 errors[/green]"
            lines.append(f"[bold]Sources[/bold]      {src} processed{err_str}")
            lines.append(f"[bold]Fetched[/bold]      {m.get('items_fetched', 0)} items")

            seen = m.get("items_filtered_seen", 0)
            dedup = m.get("items_filtered_dedup", 0)
            if seen or dedup:
                lines.append(f"[bold]Filtered[/bold]     {seen} seen · {dedup} duplicates")

            converted = m.get("items_converted", 0)
            skipped = m.get("items_convert_skipped", 0)
            failed = m.get("items_convert_failed", 0)
            if converted or skipped or failed:
                parts = [f"{converted} items"]
                if skipped:
                    parts.append(f"{skipped} skipped")
                if failed:
                    parts.append(f"[red]{failed} failed[/red]")
                lines.append(f"[bold]Converted[/bold]    {' · '.join(parts)}")

            validated = m.get("items_validated", 0)
            val_failed = m.get("items_validation_failed", 0)
            if validated or val_failed:
                v_str = f" · [red]{val_failed} failed[/red]" if val_failed else ""
                lines.append(f"[bold]Validated[/bold]    {validated} passed{v_str}")

            staged = m.get("items_staged", 0)
            if staged:
                lines.append(f"[bold]Staged[/bold]       [green]{staged} new recommendations[/green]")

            elapsed = m.get("elapsed_seconds")
            if elapsed:
                lines.append(f"[bold]Time[/bold]         {elapsed}s")

            self.console.print(Panel(
                "\n".join(lines),
                title="[bold]Summary[/bold]",
                border_style="green" if not errors else "yellow",
                padding=(0, 1),
            ))

            if errors:
                self.console.print("\n[bold red]Errors:[/bold red]")
                for err in errors:
                    self.console.print(f"  [red]•[/red] {err}")
        else:
            print("=" * 55)
            print("  Summary")
            print("=" * 55)
            print(f"  Sources:    {m.get('sources_processed', 0)} processed ({len(errors)} errors)")
            print(f"  Fetched:    {m.get('items_fetched', 0)} items")
            seen = m.get("items_filtered_seen", 0)
            dedup = m.get("items_filtered_dedup", 0)
            if seen or dedup:
                print(f"  Filtered:   {seen} seen, {dedup} dedup")
            if m.get("items_converted"):
                print(f"  Converted:  {m['items_converted']} ({m.get('items_convert_skipped', 0)} skipped)")
            if m.get("items_staged"):
                print(f"  Staged:     {m['items_staged']} new recommendations")
            if m.get("elapsed_seconds"):
                print(f"  Time:       {m['elapsed_seconds']}s")
            print("=" * 55)
            if errors:
                print("\nErrors:")
                for err in errors:
                    print(f"  • {err}")

    def show_staged_table(self, staged_items: list[dict]):
        if not staged_items:
            return

        if self._use_rich:
            table = Table(
                title="New Staged Recommendations",
                box=box.ROUNDED,
                show_lines=True,
                padding=(0, 1),
            )
            table.add_column("Service", style="cyan", width=18)
            table.add_column("Scenario", width=48)
            table.add_column("Risk", style="yellow", width=22)
            table.add_column("Dedup", justify="right", width=6)

            for item in staged_items:
                scenario = item.get("scenario", "?")
                if len(scenario) > 46:
                    scenario = scenario[:46] + ".."
                table.add_row(
                    item.get("service_name", "?"),
                    scenario,
                    item.get("risk_detail", "?"),
                    f"{item.get('dedup_score', 0):.2f}",
                )
            self.console.print()
            self.console.print(table)
        else:
            print(f"\n  {'Service':<18} {'Scenario':<48} {'Risk':<22} {'Dedup':>6}")
            print("  " + "-" * 96)
            for item in staged_items:
                scenario = item.get("scenario", "?")[:46]
                print(
                    f"  {item.get('service_name', '?'):<18} {scenario:<48} "
                    f"{item.get('risk_detail', '?'):<22} {item.get('dedup_score', 0):>5.2f}"
                )
