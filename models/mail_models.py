from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MailMessage:
    folder_no: int
    uid_no: int
    full_path: str
    bytes_full_path: str
    email_file_coding: str
    msg_size: int
    msg_receive: int
    st_ctime: float
    st_ino: int
    uniq_ino: str
    st_size: int
    hardlink_count: int
    is_webfolder: bool
    hardlinks: List[str]
