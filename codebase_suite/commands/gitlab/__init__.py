import click

from .project import project
from .group import group

@click.group()
@click.pass_context
def gitlab(ctx: click.Context):
    """
    Zarządzanie obiektami w Gitlab.
    """
    ctx.obj.logger().trace("✔️  codebase-suite → gitlab")  # pragma: no cover

gitlab.add_command(project)
gitlab.add_command(group)
