import os
import json

from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Union

from ...config import Config
from ...core import Logger

class GitlabGroup:
    """ 
    Klasa generująca pliki terraform dla grupy na podstawie zebranych danych z gitlab API.
    """

    __logger: Logger
    __group: dict = []
    __repository_path: Path
    __sanitized_group_name: str
    __template_path: Path
    __force: bool = False

    tf_module_gitlab_group_source: str

    def __init__(self, template_path: Path, group: dict, repository_path: Path, logger: Logger = None) -> None:

        if logger == None:
            self.__logger = Logger()
        else:
            self.__logger = logger

        self.__group = group
        self.__repository_path = repository_path      
        self.__logger.trace(f"  Set repository path: {self.__repository_path}")
        self.__template_path = template_path
        self.__logger.trace(f"  Set template dir path: {self.__template_path}")


        self.__sanitized_group_name = self.__group['name'].replace(".", "_")
        self.__logger.trace(f"  Sanitized group name: {self.__sanitized_group_name}")
        
        self.__group['avatar'] = str(os.path.basename(urlparse(self.__group['avatarUrl']).path)).replace(".png", "")
        self.__group['avatar'] = None if self.__group['avatar'] == "b''" else self.__group['avatar']
        self.__logger.trace(f"  Change avatar name: {self.__group['avatar']}")

        self.tf_module_gitlab_group_source = Config().tf_module_gitlab_group_source


    def __save_module(self, body: Union[str,dict], is_json: bool = False):
        dest_tf = self.__repository_path / f"{self.__group['fullPath']}.tf"
        dest_tf_json = self.__repository_path / f"{self.__group['fullPath']}.tf.json"

        if os.path.exists(dest_tf) and not self.__force:
            self.__logger.warning(f"⛔  File {dest_tf} already exists, skipping. Use --force to overwrite.")
        elif os.path.exists(dest_tf_json) and not self.__force:
            self.__logger.warning(f"⛔  File {dest_tf_json} already exists, skipping. Use --force to overwrite.")
        else:
            dest = dest_tf_json if is_json else dest_tf
            with open(dest, "w") as f:
                f.write(body) if isinstance(body, str) else json.dump(body, f, indent=2)
            self.__logger.success(f"📝  Generated: {dest} module definition.")

    def __save_another_files(self, dest: str, body: Union[str,dict], is_json: bool = False) -> None:
        dest_tf = dest if str(dest).endswith(".tf") else str(dest)[:-5]
        dest_tf_json = dest if str(dest).endswith(".json") else f"{dest}.json"

        if not os.path.isdir(dest.parent):
            os.makedirs(dest.parent)
            self.__logger.success(f"📁  Create directory: {dest.parent}")

        if os.path.exists(dest_tf) and not self.__force:
            self.__logger.warning(f"⛔  File {dest_tf} already exists, skipping. Use --force to overwrite.")
        elif os.path.exists(dest_tf_json) and not self.__force:
            self.__logger.warning(f"⛔  File {dest_tf_json} already exists, skipping. Use --force to overwrite.")
        else:
            with open(dest, "w") as f:
                f.write(body) if isinstance(body, str) else json.dump(body, f, indent=2)
            self.__logger.success(f"📝  Generated: {dest} module definition.")

    def generate_hcl(self, force: bool=False) -> None:
        self.__force = force

        template_env = Environment(
            loader = FileSystemLoader(self.__template_path),
            trim_blocks = True,
            lstrip_blocks = True
        )
        for j2_path in list(self.__template_path.glob("*.tf.j2")):
            template_name = j2_path.name
            
            template = template_env.get_template(name=template_name)
            rendered = template.render({
                "group": self.__group,
                "module_name": self.__sanitized_group_name,
                'source': self.tf_module_gitlab_group_source
            })

            if template_name == 'module.tf.j2':
                self.__save_module(body=rendered, is_json=False)
            else:
                dest = self.__repository_path / f"{self.__group['fullPath']}" / template_name.replace('.j2','')
                self.__save_another_files(dest=dest, body=rendered, is_json=False)
                    
    def generate_json(self, force: bool=False) -> None:
        self.__force = force
        
        template_env = Environment(
            loader = FileSystemLoader(self.__template_path),
            trim_blocks = True,
            lstrip_blocks = True
        )
        for j2_path in list(self.__template_path.glob("*.tf.json.j2")):
            template_name = j2_path.name
            
            template = template_env.get_template(name=template_name)
            rendered = template.render({
                "group": self.__group,
                "module_name": self.__sanitized_group_name,
                'source': self.tf_module_gitlab_group_source
            })

            if template_name == 'module.tf.json.j2':
                self.__save_module(body=json.loads(rendered), is_json=True)
            else:
                dest = self.__repository_path / f"{self.__group['fullPath']}" / template_name.replace('.j2','')
                self.__save_another_files(dest=dest, body=json.loads(rendered), is_json=False)