import click

from .generate import generate
from .import_tf import import_tf

@click.group()
@click.pass_context
def terraform(ctx):
    """
    Zadanie związane z pracą z terraform
    """
    ctx.obj.logger().trace("✔️  codebase-suite → terraform")   # pragma: no cover


terraform.add_command(generate)
terraform.add_command(import_tf)
