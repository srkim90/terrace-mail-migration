from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MailMessage:
    folder_no: int
    uid_no: int
    full_path: str
    bytes_full_path: bytes
    email_file_coding: str
    msg_size: int
    msg_receive: int
    st_ctime: float
    st_ino: int
    st_size: int
    hardlink_count: int
    hardlinks: List[str]
