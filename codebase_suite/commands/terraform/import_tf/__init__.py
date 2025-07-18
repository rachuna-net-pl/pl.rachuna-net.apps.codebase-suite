import click
import json
import time
import sys

from pathlib import Path


from codebase_suite.adapters import Terraform
from codebase_suite.config import Config
from codebase_suite.connectors.Gitlab.GitlabConnector import GitlabConnector

gl: GitlabConnector


def print_progress_bar(ctx, index, size, width=60):
    percent = (index / size) * 100
    left = int(width * percent // 100)
    right = width - left
    
    ctx.obj.logger().trace(f"   Status import: {index} / {size}")
    if index == size:
        ctx.obj.logger().info(f"    [\033[2;32m { '█' * left}{' ' * right} \033[0m] {percent:.1f}%")
    else:
        ctx.obj.logger().info(f"    [\033[2;34m { '█' * left}{' ' * right} \033[0m] {percent:.1f}%")


def replan(tf: Terraform,ctx):
    ctx.obj.logger().info("    Refresh terraform plan json")
    tf.terraform_plan()
    tf.terraform_show()
    return tf.get_terraform_plan_json()


@click.group(name="import")
@click.pass_context
def import_tf(ctx):
    """
    Importowanie zasobów do terraform state
    """
    ctx.obj.logger().trace("✔️  codebase-suite → terraform → import")  # pragma: no cover


@import_tf.command()
@click.option('-r','--repository-path', type=Path, required=True, help="Set local path to repository with a IaC definitions")
@click.option('--dry', is_flag=True, default=False, help="Uruchom w trybie dry-run")
@click.option('--no-gitlab-state', is_flag=True, default=False, help="Disable use gitlab terraform states")
@click.option('-b','--progress', is_flag=True, default=False, help="Enable progress bar")
@click.pass_context
def gitlab(ctx, repository_path, dry, no_gitlab_state, progress):
    """
    Importowanie resources do terraform state dla iac-gitlab
    (eg. https://gitlab.com/pl.rachuna-net/infrastructure/terraform/iac-gitlab)
    """
    gl = GitlabConnector(ctx.obj.logger())
    tf = Terraform(ctx.obj.logger(), repository_path, not no_gitlab_state)

    tf_state_name_iac_gitlab = Config().tf_state_name_iac_gitlab
    tf.terraform_init(tf_state_name_iac_gitlab)
    plan = replan(tf, ctx)

    ## importujemy najpierw grupy, by po ponownym terraform plan podstawiły się rodzice
    resources_count = len(plan['resource_changes'])
    counter = 0
    ctx.obj.logger().info("🔼  Import gitlab groups ...")
    for resource in plan['resource_changes']:
        counter += 1
        if "create" in resource['change']['actions']:

            # GITLAB GROUP
            if resource['type'] == "gitlab_group":
                group_path = resource['change']['after']['path']
                
                if 'parent_id' in resource['change']['after']:
                    parent_id = resource['change']['after']['parent_id']
                    parent_group = gl.get_group_by_id(parent_id)
                    group = gl.graphql_get_group(parent_group.full_path+"/"+group_path)
                else:
                    group = gl.graphql_get_group(group_path)
                tf.terraform_import(resource['address'], group['id'], dry)

                if progress and counter < resources_count:
                    print_progress_bar(ctx, counter, resources_count)
    if progress:
        print_progress_bar(ctx, counter, resources_count)


    ## importujemy najpierw projekty, by po ponownym terraform plan podstawiły się id projektu
    plan = replan(tf, ctx)
    resources_count = len(plan['resource_changes'])
    counter = 0
    ctx.obj.logger().info("🔼  Import gitlab projects ...")
    for resource in plan['resource_changes']:
        counter += 1
        if "create" in resource['change']['actions']:

            # GITLAB PROJECT
            if resource['type'] == "gitlab_project":
                project_name = resource['change']['after']['name']
                
                if 'namespace_id' in resource['change']['after']:
                    parent_id = resource['change']['after']['namespace_id']
                    parent_group = gl.get_group_by_id(parent_id)
                    project = gl.graphql_get_project(parent_group.full_path+"/"+project_name)
                else:
                    project = gl.graphql_get_project(project_name)
                tf.terraform_import(resource['address'], project['id'], dry)
                
                if progress and counter < resources_count:
                    print_progress_bar(ctx, counter, resources_count)    # pragma: no cover
    if progress:
        print_progress_bar(ctx, counter, resources_count)

    plan = replan(tf, ctx)
    resources_count = len(plan['resource_changes'])
    counter = 0
    ctx.obj.logger().info("🔼  Import gitlab group and project settings ...")
    for resource in plan['resource_changes']:
        counter += 1
        if "create" in resource['change']['actions'] and "delete" not in resource['change']['actions']:

            # group parameters
            if 'group' in resource['change']['after']:
                group_id = resource['change']['after']['group']
                group = gl.get_group_by_id(group_id)

                if resource['type'] == "gitlab_group_badge":
                    for badge in gl.get_group_badges(group_id):
                        if badge['name'] == resource['change']['after']['name']:
                            tf.terraform_import(resource['address'], f"{group_id}:{badge['id']}", dry)

                if resource['type'] == "gitlab_group_label":
                    for g in gl.graphql_get_group(group.full_path)['labels']:
                        if g['title'] == resource['change']['after']['name']:
                            tf.terraform_import(resource['address'], f"{group_id}:{g['id']}", dry)
                
                if resource['type'] == "gitlab_group_variable":
                    for g in gl.graphql_get_group(group.full_path)['ciVariables']:
                        if g['key'] == resource['change']['after']['key']:
                            tf.terraform_import(resource['address'], f"{group_id}:{g['key']}:{g['environmentScope']}", dry)
            
                if progress and counter < resources_count:
                    print_progress_bar(ctx, counter, resources_count)

            # nie pobieraj tego samego
            if 'project' in resource['change']['after']:
                project_id = resource['change']['after']['project']
                project = gl.get_project_by_id(project_id)

                if resource['type'] == "gitlab_branch_protection":
                    for protected_branch in gl.graphql_get_project(project.path_with_namespace)['branchRules']:
                        if protected_branch['name'] == resource['change']['after']['branch']:
                            tf.terraform_import(resource['address'], f"{project_id}:{protected_branch['name']}", dry)
                
                if resource['type'] == "gitlab_tag_protection":
                    for protected_tag in gl.get_project_protected_tags(project_id):
                        if protected_tag['name'] == resource['change']['after']['tag']:
                            tf.terraform_import(resource['address'], f"{project_id}:{protected_tag['name']}", dry)

                if resource['type'] == "gitlab_project_badge":
                    for badge in gl.get_project_badges(project_id):
                        if badge['name'] == resource['change']['after']['name']:
                            tf.terraform_import(resource['address'], f"{project_id}:{badge['id']}", dry)

                if resource['type'] == "gitlab_project_mirror":
                    for mirror in gl.get_project_mirrors(project_id):
                        if mirror.url == resource['change']['after']['url']:
                            tf.terraform_import(resource['address'], f"{project_id}:{mirror.id}", dry)

                if resource['type'] == "gitlab_project_label":
                    for label in gl.graphql_get_project(project.path_with_namespace)['labels']:
                        if label['title'] == resource['change']['after']['name']:
                            tf.terraform_import(resource['address'], f"{project_id}:{label['id']}", dry)
                
                if resource['type'] == "gitlab_project_variable":
                    # print(resource)
                    for ci_var in gl.graphql_get_project(project.path_with_namespace)['ciVariables']:
                        if ci_var['key'] == resource['change']['after']['key']:
                            tf.terraform_import(resource['address'], f"{project_id}:{ci_var['key']}:{ci_var['environmentScope']}", dry)

                if progress and counter < resources_count:
                    print_progress_bar(ctx, counter, resources_count)    # pragma: no cover
    
    if progress:
        print_progress_bar(ctx, counter, resources_count)