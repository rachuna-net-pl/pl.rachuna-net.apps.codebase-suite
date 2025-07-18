from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from singleton_decorator import singleton

@singleton
class Config(BaseSettings):
    """
    klasa, która przechowuje ustawienia aplikacji.
    """
    model_config = SettingsConfigDict(env_file=".env")

    ### global
    templates_dir: Path = Field(validation_alias='CODEBASE_TEMPLATES_PATH', description="Path to templates directory", default=Path.cwd() / 'templates')

    ### gitlab
    gitlab_url: str = Field(validation_alias='GITLAB_FQDN', description="GitLab server URL", default="https://gitlab.com/")
    gitlab_token: SecretStr = Field(validation_alias='GITLAB_TOKEN', description="GitLab API token", validate_default=False)
    gitlab_username: str = Field(validation_alias='CI_USERNAME', description="GitLab username")
    ssl_verify: str = Field(validation_alias='GITLAB_SSL_VERIFY', description="Path SSL verify enabled", default="")
    api_version: str = Field(validation_alias='GITLAB_API_VERSION', description="Set gitlab api version", default="4")


    ## terraform
    tf_module_gitlab_group_source: str = Field(validation_alias='TF_MODULE_gitlab_group_source', description="Moduł terraform gitlab-group", default="git@gitlab.com:pl.rachuna-net/infrastructure/terraform/modules/gitlab-group.git")
    tf_module_gitlab_project_source: str = Field(validation_alias='TF_MODULE_gitlab_project_source', description="Moduł terraform gitlab-group", default="git@gitlab.com:pl.rachuna-net/infrastructure/terraform/modules/gitlab-project.git")
    tf_state_name_iac_gitlab: str = Field(validation_alias='TF_STATE_NAME_iac_gitlab', description="Nazwa TF STATE dla iac-gitlab", default="production")
    
    tf_init_args: str = Field(validation_alias='TF_INIT_ARG', description="Arguments to terraform init", default="")