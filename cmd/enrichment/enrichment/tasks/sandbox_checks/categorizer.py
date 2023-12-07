# Standard Libraries
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SandboxRegex:
    hostname: str
    username: str


class SandboxDetectorInterface(ABC):
    @abstractmethod
    async def check_sandbox(self, name: str) -> SandboxRegex:
        pass


class CsvSandboxDetector(SandboxDetectorInterface):
    sandboxRegexList: list[SandboxRegex] = []
    data_path: str
    _initialized: bool = False
    _category_files: Dict[str, str] = {
        "RegexChecks": "username_hostname_checks.csv",
    }

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            self.data_path = data_path
        else:
            self.data_path = os.path.join(os.path.dirname(__file__), "data")

        for check in self._category_files:
            self.__load_csv(check, os.path.join(self.data_path, self._category_files[check]))

    def __load_csv(self, category_name: str, filepath: str) -> None:
        csv = open(filepath, "r", encoding="utf-8")
        lines = csv.readlines()
        csv.close()

        for line in lines:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue

            parts = line.split(",", 1)

            username_regex = parts[0]
            hostname_regex = parts[1]

            regex = SandboxRegex(hostname_regex, username_regex)

            self.sandboxRegexList.append(regex)

    async def check_sandbox(self, username, hostname) -> bool:
        for r in self.sandboxRegexList:
            if re.match(r.username, username, re.IGNORECASE) and re.match(r.hostname, hostname, re.IGNORECASE):
                return True
        return False
