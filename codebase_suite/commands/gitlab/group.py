import sys
import click
from path import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from ...connectors.Gitlab import GitlabConnector


@click.group()
@click.pass_context
def group(ctx):
    """
    Zarządzanie grupami w gitlab
    """
    ctx.obj.logger().trace("✔️  codebase-suite → gitlab → group")


@group.command()
@click.option('-p','--full-path', type=Path, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.pass_context
def list_badges(ctx, full_path):
    """
    Lista badges zdefiniowana w grupie gitlab
    """
    gl = GitlabConnector(ctx.obj.logger())
    result = gl.get_group_badges(full_path)

    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("id", justify="left", no_wrap=True)
    table.add_column("name", justify="left", no_wrap=False, overflow="fold")
    table.add_column("link_url", justify="left", no_wrap=False, overflow="fold")
    table.add_column("image_url", justify="left", no_wrap=False, overflow="fold")

    for badge in result:
        table.add_row(
            str(badge['id']),
            badge['name'],
            badge['link_url'],
            badge['image_url']
        )

    console = Console()
    console.print(table)

    sys.exit(0)

@group.command()
@click.option('-p','--full-path', type=Path, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.pass_context
def list_ci(ctx, full_path):
    """
    Lista procesów CI/CD dla projektów w grupie
    """
    gl = GitlabConnector(ctx.obj.logger())
    result = gl.graphql_get_group_projects(full_path)

    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("id", justify="left", no_wrap=True)
    table.add_column("fullPath", justify="left", no_wrap=False, overflow="fold")
    table.add_column("ciConfigPathOrDefault", justify="left", no_wrap=False, overflow="fold")

    for project in sorted(result, key=lambda x: x.get("fullPath", "")):
        project_id = project.get("id", "").replace("gid://gitlab/Project/", "")
        table.add_row(
            project_id,
            project.get("fullPath", ""),
            project.get("ciConfigPathOrDefault", "")
        )

    console = Console()
    console.print(table)

    sys.exit(0)

@group.command()
@click.option('-p','--full-path', type=Path, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.pass_context
def list_labels(ctx, full_path):
    """
    Lista labels zdefiniowanych w grupie gitlab
    """
    gl = GitlabConnector(ctx.obj.logger())
    result = gl.graphql_get_group(full_path)

    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("id", justify="left", no_wrap=True)
    table.add_column("color", justify="left", no_wrap=False, overflow="fold")
    table.add_column("title", justify="left", no_wrap=False, overflow="fold")
    table.add_column("description", justify="left", no_wrap=False, overflow="fold")

    for var in sorted(result['labels'], key=lambda x: x.get("title", "")):

        table.add_row(
            var.get("id", ""),
            var.get("color", ""),
            var.get("title", ""),
            var.get("description", "")
        )

    console = Console()
    console.print(table)

    sys.exit(0)


@group.command()
@click.option('-p','--full-path', type=Path, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.pass_context
def list_vars(ctx, full_path):
    """
    Lista zmiennych w zdefiniowana w grupie gitlab
    """
    gl = GitlabConnector(ctx.obj.logger())
    result = gl.graphql_get_group(full_path)

    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("id", justify="left", no_wrap=True)
    table.add_column("key", justify="left", no_wrap=False, overflow="fold")
    table.add_column("value", justify="left", no_wrap=False, overflow="fold")
    table.add_column("protected", justify="left", no_wrap=False, overflow="fold")
    table.add_column("masked", justify="left", no_wrap=False, overflow="fold")
    table.add_column("scope", justify="left", no_wrap=False, overflow="fold")
    table.add_column("description", justify="left", no_wrap=False, overflow="fold")

    for var in sorted(result['ciVariables'], key=lambda x: x.get("key", "")):
        is_protected = var.get("protected", False)
        is_masked = var.get("masked", False)
        
        if is_protected:
            row_style = "bold red"
        elif is_masked:
            row_style = "bold green"
        else:
            row_style = ""

        table.add_row(
            Text(var.get("id", ""), style=row_style),
            Text(var.get("key", ""), style=row_style),
            Text(var.get("value", ""), style=row_style),
            Text("Yes" if is_protected else "No", style=row_style),
            Text("Yes" if is_masked else "No", style=row_style),
            Text(var.get("environmentScope", ""), style=row_style),
            Text(var.get("description", ""), style=row_style)
        )

    console = Console()
    console.print(table)

    sys.exit(0)
