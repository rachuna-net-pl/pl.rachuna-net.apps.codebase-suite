import click
from path import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ...adapters.Git import Git
from ...connectors.Gitlab import GitlabConnector


console = Console()

@click.group()
@click.pass_context
def project(ctx: click.Context) -> None:
    """
    Zarządzanie projektami w GitLab
    """
    ctx.obj.logger().trace("✔️  codebase-suite → gitlab → project")

@project.command()
@click.option('--src', type=Path, required=False, help="Path to local project")
@click.option('-p','--full-path', type=Path, required=False, help="Set full path to repository (eg. pl.rachuna-net/app/codebase-suite)")
@click.pass_context
def info(ctx: click.Context, src: Path, full_path: Path) -> None:
    """
    Sprawdzanie projektu na podstawie lokalnej ścieżki do pobranego repozytorium lub po wskazaniu `full_path`
    """
    if full_path == None and src == None:
        ctx.obj.logger().error("❌   No arguments. Specify --src or --full-path")
        exit(1)

    ctx.obj.logger().trace("✔️  codebase-suite → gitlab → project → info")
    if src != None:
        try:
            git = Git(ctx.obj.logger(), src)
            full_path = git.get_remote_url()
            ctx.obj.logger().trace(f"  Set full_path repository: {full_path}")
        except FileNotFoundError:
            ctx.obj.logger().error(f"❌  Repository path '{src}' does not exist.")
            exit(1)

    gl = GitlabConnector(ctx.obj.logger())
    project = gl.graphql_get_project(full_path)
    if project == None:
        ctx.obj.logger().error(f"❌    Project '{full_path}' not found in gitlab.")
        exit(1)
    variables = gl.get_project_inherited_variables(project.get('fullPath', ''))

    table = Table(
        show_header=True, 
        header_style="bold",
        show_lines=True
    )
    table.add_column("Key", style="dim", no_wrap=True)
    table.add_column("Value")
     
    for key, value in project.items():
        if key in ['id', 'name', 'archived', 'description', 'visibility']:
            table.add_row(key, f"{value}")
        if key == "topics":
            table.add_row(key, ", ".join(value))
    
    console = Console()
    console.print(table)

    table = Table(
        show_header=True, 
        header_style="bold", 
        show_lines=True
    )
    table.add_column("id", justify="left", no_wrap=True)
    table.add_column("source", justify="left", no_wrap=False, overflow="fold")
    table.add_column("key", justify="left", no_wrap=True)
    table.add_column("value", justify="left", no_wrap=True)
    table.add_column("masked", justify="left", no_wrap=True)
    table.add_column("protected", justify="left", no_wrap=True)
    table.add_column("scope", justify="left", no_wrap=True)
    table.add_column("description", justify="left", no_wrap=False, overflow="fold")

    for val in sorted(variables.values(), key=lambda x: x.get('id', '')):
        is_protected = val.get("protected", False)
        is_masked = val.get("masked", False)
        description = val.get("description") or ""

        if is_protected:
            row_style = "bold red"  # pragma: no cover
        elif is_masked:
            row_style = "bold green"  # pragma: no cover
        else:
            row_style = ""

        table.add_row(
            Text(val.get('id', ""), style=row_style),
            Text(val.get('path', ""), style=row_style),
            Text(val.get('key', ""), style=row_style),
            Text(val.get("value", ""), style=row_style),
            Text("Yes" if is_protected else "No", style=row_style),
            Text("Yes" if is_masked else "No", style=row_style),
            Text(val.get("environmentScope", ""), style=row_style),
            Text(description, style=row_style),
        )
    console = Console()
    console.print(table)
