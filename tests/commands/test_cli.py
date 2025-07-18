import pytest
import click
from click.testing import CliRunner
from codebase_suite.commands import commands  # zakładam, że tak importujesz ten moduł


def test_commands_help():
    runner = CliRunner()
    result = runner.invoke(commands, ['--help'])
    assert result.exit_code == 0
    
    subcommands = commands.commands
    assert "Narzędzie wspomagające devops" in result.output
    assert "gitlab" in subcommands
    assert "terraform" in subcommands


def invoke_and_check(verbose_count, no_color_flag):
    runner = CliRunner()
    args = []
    if verbose_count:
        args.extend(['-v'] * verbose_count)
    if no_color_flag:
        args.append('--no-color')

    @commands.command()
    @click.pass_context
    def dummy(ctx):
        context = ctx.obj
        logger_obj = context._Context__logger
        level = getattr(logger_obj, 'log_level', 'unknown')
        click.echo(f"log_level={level}")

    result = runner.invoke(commands, args + ['dummy'])
    commands.commands.pop('dummy')
    return result


def test_commands_verbose_and_no_color_flags_sets_context():
    res = invoke_and_check(verbose_count=0, no_color_flag=False)
    assert res.exit_code == 0
    assert "log_level=" in res.output

    res = invoke_and_check(verbose_count=1, no_color_flag=False)
    assert res.exit_code == 0

    res = invoke_and_check(verbose_count=2, no_color_flag=True)
    assert res.exit_code == 0