import click

from .gitlab import gitlab

@click.group()
@click.pass_context
def generate(ctx):
    """
    Generowanie plików terraform
    """
    ctx.obj.logger().trace("✔️  codebase-suite → terraform → generate")  # pragma: no cover

generate.add_command(gitlab)
