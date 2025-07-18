import os
import subprocess
import json

from pathlib import Path

from ...config import Config
from ...core import Logger
from ...adapters.Git import Git
from ...connectors.Gitlab import GitlabConnector


class Terraform:
    """
    Klasa wykonująca polecenia terraform - cli
    """

    __logger: Logger
    __cwd: Path
    __project_iac_id: str
    __enable_gitlab_state: bool
    __cmd: str = "terraform"
    __tfplan: str = ".terraform/.tfplan"
    __tfplanjson: str = ".tfplan.json"
    
    def __init__(self, logger: Logger, src_path: Path, enable_gitlab_state: bool = True) -> None:
        if logger == None:
            self.__logger = Logger()
        else:
            self.__logger = logger

        self.__cwd = src_path   
        
        if os.path.exists(self.__cwd):
            self.__logger.debug(f"✔️  Directory exist {self.__cwd}")
            
            git = Git(self.__logger, self.__cwd)
            full_path = git.get_remote_url()
            self.__logger.trace(f"    Set full_path repository: {full_path}")

            gl = GitlabConnector(self.__logger)
            project = gl.graphql_get_project(full_path)
            self.__project_iac_id = project['id']
            self.__logger.info(f"    Set repository id: {self.__project_iac_id}")

            self.__enable_gitlab_state = enable_gitlab_state
            self.__logger.info(f"    Enable gitlab state: {self.__enable_gitlab_state}")
            
        else: 
            raise FileNotFoundError(f"Repository path '{src_path}' does not exist.")
        
    def terraform_init(self, tf_state: str) -> None:
        """
        Initialize terraform in the current directory
        """
        if self.__enable_gitlab_state:
            gitlab_url = Config().gitlab_url
            username = Config().gitlab_username
            token = Config().gitlab_token.get_secret_value()

            cmd = f"{self.__cmd} init -backend-config=\"address={gitlab_url}/api/v4/projects/{self.__project_iac_id}/terraform/state/{tf_state}\" \
-backend-config=\"lock_address={gitlab_url}/api/v4/projects/{self.__project_iac_id}/terraform/state/{tf_state}/lock\" \
-backend-config=\"unlock_address={gitlab_url}/api/v4/projects/{self.__project_iac_id}/terraform/state/{tf_state}/lock\" \
-backend-config=\"username={username}\" \
-backend-config=\"password={token}\" \
-backend-config=\"lock_method=POST\" \
-backend-config=\"unlock_method=DELETE\" \
-backend-config=\"retry_wait_min=5\""
        else:
            tf_init_args = Config().tf_init_args
            cmd = f"{self.__cmd} init {tf_init_args}"
        
        self.__logger.debug("🚀  Terraform init has been started")
        self.__logger.debug(cmd)
        result = subprocess.run(
            cmd,
            cwd=self.__cwd,
            shell=True,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            print(cmd)
            print(result.stdout)
            print(result.stderr)
            self.__logger.error("❌   Terraform init failed!")
            exit(1)
        else:
            self.__logger.success("✔️   Terraform has been successfully initialized!")

    def terraform_plan(self) -> None:
        """
        Plan terraform in the current directory
        """
        tfplan_path = self.__cwd / self.__tfplan
        if os.path.exists(tfplan_path):
            os.remove(tfplan_path)
            self.__logger.info(f"    Remove {tfplan_path}")

        cmd = f"{self.__cmd} plan -out={tfplan_path}"

        self.__logger.debug("🚀  Terraform plan has been started")
        self.__logger.debug(cmd)
        result = subprocess.run(
            cmd,
            cwd=self.__cwd,
            shell=True,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            print(cmd)
            print(result.stdout)
            print(result.stderr)
            self.__logger.error("❌   Terraform plan failed!")
            exit(1)
        else:
            self.__logger.success("✔️   Terraform plan has been successfully executed!")

    def terraform_show(self) -> None:
        """
        Show terraform result
        """
        tfplan_path = self.__cwd / self.__tfplan
        tfplanjson_path = self.__cwd / self.__tfplanjson

        if os.path.exists(tfplanjson_path):
            os.remove(tfplanjson_path)
            self.__logger.info(f"    Remove {tfplanjson_path}")

        cmd = f"{self.__cmd} show -json {tfplan_path} > {tfplanjson_path}"

        self.__logger.debug("🚀  Terraform show has been started")
        self.__logger.debug(cmd)
        result = subprocess.run(
            cmd,
            cwd=self.__cwd,
            shell=True,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            print(cmd)
            print(result.stdout)
            print(result.stderr)
            self.__logger.error("❌   Terraform show failed!")
            exit(1)
        else:
            self.__logger.success("✔️   Terraform show has been successfully executed!")

    def terraform_import(self, to: str , id: str, dry: bool = False) -> None:
        """
        Import terraform resource
        """
        cmd = f"{self.__cmd} import '{to}' '{id}'"

        self.__logger.debug("🚀  Terraform import has been started")
        self.__logger.debug(cmd)
        if not dry:
            result = subprocess.run(
                cmd,
                cwd=self.__cwd,
                shell=True,
                text=True,
                capture_output=True,
            )

            if result.returncode != 0:
                print(cmd)
                print(result.stdout)
                print(result.stderr)
                self.__logger.error("❌   Terraform import failed!")
                exit(1)
            else:
                self.__logger.success(f"✔️   Terraform import {to} has been successfully executed!")

    def get_terraform_plan_json(self):
        """
        Analiza pliku json z terraform plan
        """

        tfplanjson_path = self.__cwd / self.__tfplanjson
        if not os.path.exists(tfplanjson_path):
            self.__logger.error(f"Plik {tfplanjson_path} nie istnieje!")
            exit(1)

        with open(tfplanjson_path, 'r') as f:
            data = json.load(f)

        return data