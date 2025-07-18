import click
import json as json1

from pathlib import Path

from ....connectors.Gitlab import GitlabConnector
from ....generators.terraform import GitlabGroup, GitlabProject

default_templates_for_group_dir = Path('terraform/modules/gitlab-group')
default_templates_for_project_dir = Path('terraform/modules/gitlab-project')

def generate_group(ctx, gl: GitlabConnector, full_path, repository_path, template_path, force, json) -> None:
    group = gl.graphql_get_group(full_path)

    # graphql nie ma możliwości pobrania badges grupy
    badges = gl.get_group_badges(group['fullPath'])
    group['badges'] = badges

    templates = ctx.obj.get_config().templates_dir
    template_path = templates / default_templates_for_group_dir if template_path is None else template_path

    gen = GitlabGroup(template_path, group, repository_path, ctx.obj.logger())
    if json:
        gen.generate_json(force)
    else:
        gen.generate_hcl(force)

def generate_project(ctx, gl, full_path, repository_path, template_path, force, json) -> None:
    project = gl.graphql_get_project(full_path)
    
    # graphql nie ma możliwości pobrania badges grupy
    badges = gl.get_project_badges(project['fullPath'])
    project['badges'] = badges

    protected_tags = gl.get_project_protected_tags(project['fullPath'])
    project['protected_tags'] = protected_tags

    templates = ctx.obj.get_config().templates_dir
    template_path = templates / default_templates_for_project_dir if template_path is None else template_path

    gen = GitlabProject(template_path, project, repository_path, ctx.obj.logger())
    if json:
        gen.generate_json(force)
    else:
        gen.generate_hcl(force)

@click.group()
@click.pass_context
def gitlab(ctx):
    """
    Generowanie plików hcl lug tf.json na podstawie terraform modules
    """
    ctx.obj.logger().trace("✔️  codebase-suite → terraform → generate → gitlab")


@gitlab.command()
@click.option('-p','--full-path', type=str, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.option('-r','--repository-path', type=Path, required=True, help="Set local path to repository with a IaC definitions")
@click.option('-t','--template-path', type=Path, required=False, help="Set path to template file definition gitlab group")
@click.option('-f', '--force', is_flag=True, default=False, help="Wymuś nadpisanie istniejących plików")
@click.option('--json', is_flag=True, default=False, help="Generuj konfiguracje w formacie json")
@click.pass_context
def group(ctx, full_path, repository_path, template_path, force, json):
    """
    Generowanie plików terraform dla grupy gitlab
    na podstawie modułu gitlab-group
    
    https://gitlab.com/pl.rachuna-net/infrastructure/terraform/modules/gitlab-group
    """
    gl = GitlabConnector(ctx.obj.logger())
    generate_group(ctx, gl, full_path, repository_path, template_path, force, json)

@gitlab.command()
@click.option('-p','--full-path', type=str, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.option('-r','--repository-path', type=Path, required=True, help="Set local path to repository with a IaC definitions")
@click.option('-t','--template-path', type=Path, required=False, help="Set path to template file definition gitlab group")
@click.option('-f', '--force', is_flag=True, default=False, help="Wymuś nadpisanie istniejących plików")
@click.option('--json', is_flag=True, default=False, help="Generuj konfiguracje w formacie json")
@click.pass_context
def project(ctx, full_path, repository_path, template_path, force, json):
    """
    Generowanie plików terraform dla projektu gitlab
    na podstawie modułu gitlab-project
    
    https://gitlab.com/pl.rachuna-net/infrastructure/terraform/modules/gitlab-project
    """
    gl = GitlabConnector(ctx.obj.logger())
    generate_project(ctx, gl, full_path, repository_path, template_path, force, json)
    

@gitlab.command()
@click.option('-p','--full-path', type=str, required=True, help="Set full path to group (eg. pl.rachuna-net/app)")
@click.option('-r','--repository-path', type=Path, required=True, help="Set local path to repository with a IaC definitions")
@click.option('-t','--template-path', type=Path, required=False, help="Set path to template file definition gitlab group")
@click.option('-f', '--force', is_flag=True, default=False, help="Wymuś nadpisanie istniejących plików")
@click.option('--json', is_flag=True, default=False, help="Generuj konfiguracje w formacie json")
@click.pass_context
def groups(ctx, full_path, repository_path, template_path, force, json):
    """
    Generowanie plików terraform dla grupy gitlab i ich dzieci
    """
    gl = GitlabConnector(ctx.obj.logger())

    # generate root
    generate_group(ctx, gl, full_path, repository_path, template_path, force, json)

    # children
    groups = gl.graphql_get_descendantGroups(full_path)
    projects = gl.graphql_get_group_projects(full_path)
    
    for group in groups:
        ctx.obj.logger().trace(f"Przygotowanie do generowania plików dla {group['fullPath']}")
        generate_group(ctx, gl, group['fullPath'], repository_path, template_path, force, json)

    for project in projects:
        ctx.obj.logger().trace(f"Przygotowanie do generowania plików dla {project['fullPath']}")
        generate_project(ctx, gl, project['fullPath'], repository_path, template_path, force, json)