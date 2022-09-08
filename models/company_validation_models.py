import os
from dataclasses import dataclass
from typing import List, Dict

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class HardLinkMails:
    inode: int
    file_size: int
    emails: List[str]


@dataclass_json
@dataclass
class CompanyValidationModels:
    hard_links: Dict[int, HardLinkMails]

    def __init__(self) -> None:
        super().__init__()
        self.hard_links = {}

    def add_mail(self, file_name: str) -> None:
        if os.path.exists(file_name) is False or os.path.isfile(file_name) is False:
            return
        stat: os.stat_result = os.stat(file_name)
        try:
            self.hard_links[stat.st_ino].emails.append(file_name)
        except KeyError as e:
            self.hard_links[stat.st_ino] = HardLinkMails(inode=stat.st_ino, file_size=stat.st_size, emails=[file_name])