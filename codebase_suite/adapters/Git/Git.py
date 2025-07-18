import os
import subprocess

from path import Path
from singleton_decorator import singleton

from ...core import Logger


@singleton
class Git:
    """
    Klasa wykonująca polecenia git - cli
    """

    __cwd: str
    __logger: Logger
    full_path: str

    def __init__(self, logger: Logger, src_path: Path) -> None:
        if logger == None:
            self.__logger = Logger()
        else:
            self.__logger = logger

        if os.path.isdir(src_path):
            self.__logger.debug(f"✔️  Directory exist {src_path}")
        else:
            raise FileNotFoundError(f"Repository path '{src_path}' does not exist.")
        
        self.__cwd = src_path

    def get_remote_url(self) -> str:
        self.__logger.trace(f"  Set cwd: {self.__cwd}")

        cmd = "git remote get-url origin"
        self.__logger.debug(f"📀  execute: {cmd}")

        result = subprocess.run(
            cmd,
            cwd=self.__cwd,
            shell=True,
            text=True,
            capture_output=True,
        )

        if result.returncode > 0:
            print(result.stdout)
            self.__logger.error("❌  Git init failed!")
            exit(1)

        if result.stdout.startswith("git@"):  # SSH
            self.full_path = result.stdout.split(":")[1].replace(".git", "").strip()
        elif result.stdout.startswith("http"):  # HTTPS
            parts = result.stdout.split("/")
            self.full_path = "/".join(parts[3:]).replace(".git", "").strip()
        else:
            self.__logger.error(f"❌  Unknown git remote format: {result.stdout}")
            exit(1)
        
        return self.full_path
